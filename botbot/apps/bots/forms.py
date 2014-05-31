import base64
import uuid
from django.utils.safestring import mark_safe

import re
from django import forms

from botbot.apps.accounts import models as accounts_models
from . import models
from botbot.apps.bots.models import ChatBot


connection_regex = re.compile(r"^[\w\-\.]*\:\d*$")


class ChannelForm(forms.ModelForm):
    identifiable_url = forms.BooleanField(
        required=False, initial=True, help_text="Identifiable URLs may leak "
                                                "channel information as part of the referrer details if when URL "
                                                "is clicked from the logs")

    class Meta:
        model = models.Channel
        fields = ('chatbot', 'name', 'password', 'is_public', 'is_active')

    def save(self, *args, **kwargs):
        """
        If it's an identifiable url, set the slug to ``None``.

        If it's not an identifiable url, set the slug to a random value if it
        is not already set.
        """
        if self.cleaned_data['identifiable_url']:
            self.instance.slug = None
        elif not self.instance.slug:
            channels = models.Channel.objects.all()
            while not self.instance.slug or \
                    channels.filter(slug=self.instance.slug).exists():
                self.instance.slug = base64.b32encode(uuid.uuid4().bytes)[:4] \
                    .lower()
        return super(ChannelForm, self).save(*args, **kwargs)


class ChannelRequestForm(forms.Form):
    channel_name = forms.CharField()
    server = forms.ChoiceField(choices=[],
                               label="IRC Server")
    connection = forms.CharField(required=False, label="New IRC Server",
                                 help_text="IRC Server should be specified as <url>:<port>.")
    github = forms.URLField(label="GitHub Repo URL",
                            help_text="If the channel supports a github repo, the url to the repo.",
                            required=False)

    name = forms.CharField(label="Your name")
    email = forms.EmailField(label="Your e-mail")
    nick = forms.CharField(label="Your IRC Nick")
    op = forms.BooleanField(label="Are you a channel op?", required=False,
                            help_text=mark_safe("""
        I am an operator (op) for this channel and agree to the
        <a href="https://botbot.me/terms/">terms of service</a>. I will follow
        any server guidelines for logging, eg.
        <a href="https://freenode.net/channel_guidelines.shtml">Freenode</a>
        requires a link to the logs in the channel topic.
    """))

    description = forms.CharField(label="What is this channel for?",
                                  widget=forms.Textarea, required=True)

    def __init__(self, *args, **kwargs):
        super(ChannelRequestForm, self).__init__(*args, **kwargs)
        self._set_server_choices()

    def _set_server_choices(self):
        choices = [(c.pk, c.server) for c in ChatBot.objects.filter(is_active=True)]
        choices.insert(0, ('', '---------'))
        choices.append(("new", "Don't see mine, let me add it."))
        self.fields['server'].choices = choices

    def clean_channel_name(self):
        channel_name = self.cleaned_data['channel_name']
        if models.Channel.objects.filter(name=channel_name).exists():
            raise forms.ValidationError(
                "Sorry, this channel is already being monitored.")

        if not channel_name.startswith("#"):
            channel_name = "#" + channel_name

        return channel_name

    def clean_connection(self):
        connection = self.cleaned_data['connection']
        if connection and not connection_regex.match(connection):
            raise forms.ValidationError(
                "Incorrect format, should be <url>:<port>")

        return connection

    def clean_server(self):
        """
        Make sure server data is clean.

        :return: ChatBot if it was selected, None if the user should have gave
        us input to create a new one. Validation error if ChatBot was not found.
        """
        pk = self.cleaned_data['server']
        if pk == "new":
            return None

        try:
            return ChatBot.objects.get(pk=pk)
        except ChatBot.DoesNotExist:
            raise forms.ValidationError("Server doesn't exist.")

    def clean(self):
        cleaned_data = super(ChannelRequestForm, self).clean()
        server = cleaned_data.get('server')
        connection = cleaned_data.get('connection')
        if not self._errors.get('connection'):
            if server is None and not connection:
                self._errors["connection"] = self.error_class([
                    "This field is required."
                ])

        return cleaned_data


class UsersForm(forms.Form):
    users = forms.ModelMultipleChoiceField(required=False,
                                           queryset=accounts_models.User.objects.all())

    def __init__(self, channel, *args, **kwargs):
        super(UsersForm, self).__init__(*args, **kwargs)
        self.channel = channel
        if channel:
            self.fields['users'].initial = [p.pk for p in channel.users.all()]

    def save(self):
        users = self.cleaned_data['users']
        self.channel.membership_set.exclude(user__in=users).delete()
        for user in users:
            self.channel.membership_set.get_or_create(user=user)
