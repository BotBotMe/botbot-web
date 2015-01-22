from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView, View

from botbot.apps.bots import models as bots_models
from . import forms


class ManageAccount(FormView):
    """
    Let a user manage their account details.
    """
    form_class = forms.AccountForm
    template_name = 'accounts/manage.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """
        Only authenticated users can manage their details, obviously.
        """
        return super(ManageAccount, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.password_form = self.get_password_form()
        return super(ManageAccount, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('change_password_toggle'):
            """
            Since we're dealing with multiple forms in the template,
            check the password form here, and if it is invalid,
            return to the template
            """
            self.password_form = self.get_password_form()
            if not self.password_form.is_valid():
                form = self.get_form(self.get_form_class())
                return self.form_invalid(form)
        return super(ManageAccount, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ManageAccount, self).get_context_data(**kwargs)
        context['breadcrumb'] = 'account'
        context['password_form'] = self.password_form
        return context

    def get_success_url(self):
        return reverse('settings_account')

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super(ManageAccount, self).get_form_kwargs(*args,
            **kwargs)
        form_kwargs['instance'] = self.request.user
        return form_kwargs

    def get_password_form(self):
        return SetPasswordForm(user=self.request.user,
            data=self.request.POST or None, prefix='password-form')

    def form_valid(self, form, *args, **kwargs):
        response = super(ManageAccount, self).form_valid(form, *args, **kwargs)
        form.save()

        if self.request.POST.get('change_password_toggle'):
            # the password form is already instantiated in ``post``
            self.password_form.save()

        self.request.session['django_timezone'] = form.instance.timezone
        messages.success(self.request, 'Account details updated.')
        return response


class Channels(TemplateView):
    """
    The channels page, for both anonymous and authenticated users.
    """
    template_name = 'accounts/user_channels.html'

    def get_context_data(self, **kwargs):
        """
        Add the channels to the context.
        """
        data = super(Channels, self).get_context_data(**kwargs)
        data['public_channels'] = bots_models.Channel.objects \
            .filter(is_public=True) \
            .select_related('chatbot')
        if self.request.user.is_authenticated():
            data['admin_channels'] = bots_models.Channel.objects \
                .filter(membership__user=self.request.user,
                        membership__is_admin=True) \
                .select_related('chatbot')
            data['private_channels'] = bots_models.Channel.objects \
                .filter(is_public=False, membership__user=self.request.user) \
                .select_related('chatbot')
        return data


class Dashboard(TemplateView):
    """
    The channels page, for both anonymous and authenticated users.
    """

    def get_template_names(self):
        """
        Use the user or anonymous dashboard template.
        """
        if self.request.user.is_authenticated():
            return 'accounts/user_dashboard.html'
        return 'accounts/anon_dashboard.html'

    def get_context_data(self, **kwargs):
        """
        Add the channels to the context.
        """
        data = super(Dashboard, self).get_context_data(**kwargs)
        data['public_channels'] = bots_models.Channel.objects \
            .filter(is_public=True)\
            .select_related('chatbot')
        if self.request.user.is_authenticated():
            data['admin_channels'] = bots_models.Channel.objects \
                .filter(membership__user=self.request.user,
                        membership__is_admin=True)\
                .select_related('chatbot')
            data['private_channels'] = bots_models.Channel.objects \
                .filter(is_public=False, membership__user=self.request.user)\
                .select_related('chatbot')
        return data


class SetTimezone(View):
    """
    Set the current timezone.
    """

    def post(self, request, *args, **kwargs):
        """
        If the form is valid, set the timezone.

        In either case, only an empty response is returned (with either a 400
        or 202 status code).
        """
        form = forms.TimezoneForm(self.request, self.request.POST)
        if not form.is_valid():
            return HttpResponse(status=400)
        form.save()
        return HttpResponse(status=202)
