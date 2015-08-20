import base64
import uuid
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

import re
from django import forms

from botbot.apps.accounts import models as accounts_models
from . import models
from botbot.apps.bots.models import ChatBot


connection_regex = re.compile(r"^[\w\-\.]*\:\d*$")


class ChannelForm(forms.ModelForm):

    class Meta:
        model = models.Channel
        fields = ('chatbot', 'name', 'password', 'is_public', 'is_active')

    def save(self, *args, **kwargs):
        self.instance.slug = slugify(self.cleaned_data['name'])
        return super(ChannelForm, self).save(*args, **kwargs)


class ChannelRequestForm(forms.Form):
    channel_name = forms.CharField()
    server = forms.ChoiceField(choices=[],
                               label="IRC Server")
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
        self.fields['server'].choices = choices

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
