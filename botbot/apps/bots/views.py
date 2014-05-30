import json

import redis
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import DeleteView, TemplateView, View, CreateView, FormView
from django import http
from django.db.models import Q

from botbot.apps.accounts import models as accounts_models
from botbot.apps.plugins import forms as plugins_forms
from . import forms, models, utils


class ChannelMixin(object):
    """
    View mixin used to identify the channel a view refers to. Adds
    :attr:`channel` to the view.

    Requires the view to be passed a ``channel_pk`` or both a ``channel_slug``
    and ``bot_slug`` urlconf arguments.

    Set :attr:`only_channel_owners` to ``True`` to restrict the view to owners
    of the channel.
    """
    only_channel_owners = False

    def __init__(self, *args, **kwargs):
        super(ChannelMixin, self).__init__(*args, **kwargs)

        self._channel = None

    def dispatch(self, request, *args, **kwargs):
        """
        Add the channel as an attribute of the view.
        """
        self.channel = self.get_channel(user=request.user, **kwargs)
        return super(ChannelMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Add the channel to the context.
        """
        data = super(ChannelMixin, self).get_context_data(**kwargs)
        data['channel'] = self.channel
        return data

    def get_channel(self, user, **kwargs):
        """
        Retrieve the channel from the url arguments, ensuring the user has
        permission.
        """
        if not self._channel:
            channel_pk = kwargs.get('channel_pk')
            if channel_pk:
                channel = get_object_or_404(models.Channel, pk=channel_pk)

            elif kwargs['bot_slug'] == 'private':
                channel = get_object_or_404(
                    models.Channel, slug=kwargs['channel_slug'])

            else:
                channel = self._get_identifiable_channel(
                    kwargs['bot_slug'], kwargs['channel_slug'])

            if not channel.user_can_access(
                    user, only_owners=self.only_channel_owners):
                raise http.Http404("No permission to access this channel")
            self._channel = channel

        return self._channel

    def _get_identifiable_channel(self, bot_slug, channel_slug):
        """
        Return the channel object for an identifiable channel URL.

        If no matching channel is found, raises 404.
        """
        # IRC channel names start with # or ##, check for all variants.
        names = (channel_slug, '#{}'.format(channel_slug),
                 '##{}'.format(channel_slug))
        # Need case insensitive lookup so '__in' won't work. This builds up a
        # Q filter: http://stackoverflow.com/a/897884/116042
        name_in_q = reduce(lambda q, name: q | Q(name__iexact=name),
                           names, Q())
        candidates = models.Channel.objects\
            .filter(name_in_q).filter(Q(is_public=True) | Q(slug=None))\
            .select_related('chatbot')

        # Return first channel that has a bot matching the current bot_slug.
        for channel in candidates:
            if channel.chatbot.slug == bot_slug:
                return channel

        raise http.Http404("No such channel / network combination")


class AddChannel(CreateView):
    template_name = 'bots/add_channel.html'
    form_class = forms.ChannelForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        Only staff and superuser should be able to add a new channel.
        """
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied
        return super(AddChannel, self).dispatch(request, *args, **kwargs)

    def form_valid(self, *args, **kwargs):
        """
        Also give the current user administrative membership to this new
        channel.
        """
        response = super(AddChannel, self).form_valid(*args, **kwargs)
        self.object.membership_set.create(user=self.request.user,
            is_admin=True, is_owner=True)
        self.object.create_default_plugins()
        return response

    def get_form_kwargs(self, *args, **kwargs):
        """
        Give the form the 'cb' prefix.
        """
        form_kwargs = super(AddChannel, self).get_form_kwargs(*args, **kwargs)
        form_kwargs['prefix'] = 'cb'
        return form_kwargs

    def get_success_url(self, *args, **kwargs):
        """
        Redirect to the management page of this channel.
        """
        return utils.reverse_channel(self.object, 'manage_channel')


class DeleteChannel(ChannelMixin, DeleteView):
    """
    Delete a channel.
    """
    template_name = 'bots/confirm_delete_channel.html'
    success_url = reverse_lazy("dashboard")
    only_channel_owners = True

    def get_object(self):
        """
        The ChannelMixin provides the channel as the ``channel`` attribute.
        """
        return self.channel


class ManageChannel(ChannelMixin, TemplateView):
    """
    Edit channel settings.
    """
    template_name = 'bots/manage_channel.html'
    only_channel_owners = True

    def build_forms(self):
        """
        Build the forms used for this hybrid view.
        """
        if hasattr(self, '_forms'):
            # Forms already built.
            return self._forms                          # pylint: disable=E0203
        if self.request.method == 'POST':
            data = self.request.POST
        else:
            data = None
        self._forms = {
            'form': forms.ChannelForm(data=data, instance=self.channel,
                prefix='cb'),
            'plugin_form': plugins_forms.PluginsForm(self.channel, data=data,
                prefix='plgn'),
            'users_form': forms.UsersForm(self.channel, data=data,
                prefix='usrs'),
        }
        return self._forms

    def get_context_data(self, **kwargs):
        """
        Add the forms and the current user's membership to the context.
        """
        data = super(ManageChannel, self).get_context_data(**kwargs)
        data.update(self.build_forms())
        data['membership'] = self.channel.membership_set\
            .get(user=self.request.user)
        return data

    def post(self, *args, **kwargs):
        """
        If everything is good, save the changes and redirect to the channel.
        """
        forms = self.build_forms()
        if not all([form.is_valid() for form in forms.values()]):
            # There were form errors, use the get view instead.
            return self.get(*args, **kwargs)
        for form in forms.values():
            form.save()
        queue = redis.StrictRedis.from_url(settings.REDIS_PLUGIN_QUEUE_URL)
        queue.lpush('bot', 'REFRESH')
        return redirect(self.channel.get_absolute_url())


class SuggestUsers(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """
        Only logged in users can view suggestions.
        """
        return super(SuggestUsers, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        """
        Returns a json list of emails and pks for suggested users, based on
        the ``term`` GET argument.
        """
        term = self.request.GET.get('term')
        if term:
            users = accounts_models.User.objects\
                .filter(username__icontains=term).values('email', 'pk')
            results = [{'label': u['email'], 'value': u['pk']} for u in users]
        else:
            results = []
        return http.HttpResponse(json.dumps(results),
            content_type='application/json')


class RequestChannel(FormView):
    template_name = "bots/request.html"
    form_class = forms.ChannelRequestForm
    success_url = reverse_lazy("request_channel_success")

    def form_valid(self, form):
        bot = form.cleaned_data['server']
        connection = form.cleaned_data['connection']
        if bot is None:
            bot, _ = models.ChatBot.objects.get_or_create(server=connection,
                                              defaults={"is_active" : False})
        channel = models.Channel.objects.create(name=form.cleaned_data['channel_name'],
                                      chatbot=bot, is_active=False, is_pending=True)
        channel.create_default_plugins()
        message = render_to_string('bots/emails/request.txt',
                                   {"data": form.cleaned_data})
        mail_admins("Channel Request", message)
        return super(RequestChannel, self).form_valid(form)
