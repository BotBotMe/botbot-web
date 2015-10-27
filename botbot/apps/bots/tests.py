# -*- coding: utf-8 -*-
import datetime

import pytz
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from botbot.apps.accounts import models as account_models
from botbot.apps.bots.models import pretty_slug
from botbot.apps.logs import models as logs_models
from . import models, utils


class BaseTestCase(TestCase):
    def setUp(self):
        self.member = account_models.User.objects.create_user(
            username="dupont éîïè",
            password="secret",
            email="dupont@botbot.local")
        self.member.is_superuser = True
        self.member.is_staff = True
        self.member.save()
        self.outsider = account_models.User.objects.create_user(
            username="Marie Thérèse",
            password="secret",
            email="m.therese@botbot.local")
        self.chatbot = models.ChatBot.objects.create(
                server='testserver',
                nick='botbot',
                is_active=True)
        self.public_channel = models.Channel.objects.create(
            chatbot=self.chatbot,
            name="#Test",
            slug="test",
            is_public=True)
        logs_models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            timestamp=pytz.utc.localize(datetime.datetime.now()))
        self.private_channel = models.Channel.objects.create(
            chatbot=self.chatbot,
            name="#test-internal",
            is_public=False)


class UrlTests(BaseTestCase):

    def assertFormError(self, response, form, field, error_str):
        """Override for Jinja2 templates"""
        self.assertIn(error_str,
                      response.context_data[form].errors[field])

    def test_help_channel(self):
        url = utils.reverse_channel(self.public_channel, "help_bot")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_log_current(self):
        url = utils.reverse_channel(self.public_channel, "log_current")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_show_channel_request_form(self):
        url = reverse('request_channel')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_request_channel_form_submission(self):
        url = reverse("request_channel")

        response = self.client.post(url, {
            "channel_name": "#test_channel_name",
            "server": self.chatbot.pk,
            "name": "test_name",
            "email": "test@example.com",
            "nick": "test_nick",
            "op": True,
            "description": "This is a test"
        })
        self.assertRedirects(response, reverse('request_channel_success'))
        channel = models.Channel.objects.get(name="#test_channel_name")
        self.assertFalse(channel.is_active)
        self.assertEqual(len(mail.outbox), 1)

    def test_request_channel_form_submission_channel_with_missing_pound_sign(self):
        url = reverse("request_channel")

        response = self.client.post(url, {
            "channel_name": "test_channel_name",
            "server": self.chatbot.pk,
            "name": "test_name",
            "email": "test@example.com",
            "nick": "test_nick",
            "op": True,
            "description": "This is a test"
        })
        self.assertRedirects(response, reverse('request_channel_success'))
        # make sure wer saved it with a pound sign.
        channel = models.Channel.objects.get(name="#test_channel_name")
        self.assertFalse(channel.is_active)
        self.assertEqual(len(mail.outbox), 1)

    def test_request_channel_form_invalid_submission(self):
        url = reverse("request_channel")

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "name",
                             "This field is required.")
        self.assertFormError(response, "form", "server",
                             "This field is required.")
        self.assertFormError(response, "form", "channel_name",
                             "This field is required.")
        self.assertFormError(response, "form", "email",
                             "This field is required.")
        self.assertFormError(response, "form", "nick",
                             "This field is required.")

    def test_request_channel_form_duplicate_channel_submission(self):
        url = reverse("request_channel")

        response = self.client.post(url, {
            "channel_name": self.public_channel.name,
            "server" : self.chatbot.pk,
            "name": "test_name",
            "email" : "test@example.com",
            "nick" : "test_nick",
            "op" : True
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "channel_name",
                             '<a href="{}">{}</a> is already being monitored.'.format(
                                self.public_channel.get_absolute_url(), self.public_channel.name))


class PrettySlugTestCase(TestCase):
    def test_pretty_slug(self):
        original = {
            "chat.freenode.net": "freenode",
            "morgan.freenode.net": "freenode",
            "dickson.freenode.net": "freenode",
            "irc.oftc.net": "oftc",
            "irc.mozilla.org": "mozilla",
            "irc.coldfront.net": "coldfront",
            "irc.synirc.net": "synirc",
        }

        for server, slug in original.iteritems():
            self.assertEqual(pretty_slug(server), slug)
