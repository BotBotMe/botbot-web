from django import http
from django.core.urlresolvers import reverse_lazy
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView

from . import models


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

    class LegacySlugUsage(Exception):

        def __init__(self, url):
            self.url = url

    def __init__(self, *args, **kwargs):
        super(ChannelMixin, self).__init__(*args, **kwargs)

        self._channel = None

    def dispatch(self, request, *args, **kwargs):
        """
        Add the channel as an attribute of the view.
        """
        try:
            self.channel = self.get_channel(user=request.user, **kwargs)
        except self.LegacySlugUsage, e:
            return http.HttpResponsePermanentRedirect(e.url)

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
                channel = get_object_or_404(self._channel_queryset(), pk=channel_pk)

            elif kwargs['bot_slug'] == 'private':
                channel = get_object_or_404(
                    self._channel_queryset(), private_slug=kwargs['channel_slug'])

            else:
                channel = self._get_identifiable_channel(
                    kwargs['bot_slug'], kwargs['channel_slug'])

            self._channel = channel

        return self._channel

    def _channel_queryset(self):
        return models.Channel.objects.filter(status__in=(models.Channel.ACTIVE, models.Channel.ARCHIVED))

    def _get_identifiable_channel(self, bot_slug, channel_slug):
        """
        Return the channel object for an identifiable channel URL.

        If no matching channel is found, raises 404.
        """
        candidates = self._channel_queryset()\
            .filter(slug=channel_slug, is_public=True)\
            .select_related('chatbot')

        # Return first channel that has a bot matching the current bot_slug.
        for channel in candidates:
            if channel.chatbot.slug == bot_slug:
                return channel
            elif channel.chatbot.legacy_slug == bot_slug:
                kwargs = self.request.resolver_match.kwargs.copy()
                kwargs['bot_slug'] = channel.chatbot.slug
                raise self.LegacySlugUsage(reverse_lazy(
                    self.request.resolver_match.url_name,
                    kwargs=kwargs
                ))

        raise http.Http404("No such channel / network combination")


class ChannelList(ListView):
    model = models.Channel
    template_name = "channel_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super(ChannelList, self).get_queryset(*args, **kwargs)
        return qs.filter(
            chatbot__slug=self.kwargs['network_slug'],
            is_public=True).active()

    def get_context_data(self, **kwargs):
        data = super(ChannelList, self).get_context_data(**kwargs)

        if not self.object_list:
            raise Http404()

        data['public_channels'] = self.object_list

        return data
