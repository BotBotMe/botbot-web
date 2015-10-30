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
            is_public=True,
            status=models.Channel.ACTIVE
        )
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
