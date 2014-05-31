# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.urlresolvers import reverse
import pytz

from botbot.apps.accounts import models as account_models
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
            is_public=True)
        logs_models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            timestamp=pytz.utc.localize(datetime.datetime.now()))
        self.private_channel = models.Channel.objects.create(
            chatbot=self.chatbot,
            name="#test-internal",
            is_public=False)

        account_models.Membership.objects.create(
            user=self.member, channel=self.private_channel, is_owner=True,
            is_admin=True)

        for plugin in models.Channel.DEFAULT_PLUGINS:
            models.Plugin.objects.create(name=plugin, slug=plugin)


class ModelTests(BaseTestCase):

    def test_user_can_access(self):
        self.assertTrue(self.private_channel.user_can_access(self.member))
        self.assertTrue(self.public_channel.user_can_access(self.outsider))
        self.assertFalse(self.private_channel.user_can_access(self.outsider))
        self.assertFalse(self.private_channel.user_can_access(AnonymousUser))


class UrlTests(BaseTestCase):

    def test_help_channel(self):
        url = utils.reverse_channel(self.public_channel, "help_bot")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_log_current(self):
        url = utils.reverse_channel(self.public_channel, "log_current")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_channel_get(self):
        self.client.login(username=self.member.username, password="secret")
        url = reverse("add_channel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_channel(self):
        channel_count = models.Channel.objects.count()
        self.client.login(username=self.member.username, password="secret")
        url = reverse("add_channel")
        response = self.client.post(url, {
            "cb-is_public": True,
            "cb-is_active": True,
            "cb-chatbot": self.chatbot.pk,
            "cb-name": "#newchannel",
            "cb-plugins": [],
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.Channel.objects.count(), channel_count + 1)
        channel = models.Channel.objects.get(name="#newchannel")
        self.assertEqual(self.member in channel.users.all(), True)

    def test_add_private_channel(self):
        channel_count = models.Channel.objects.count()
        self.client.login(username=self.member.username, password="secret")
        url = reverse("add_channel")
        response = self.client.post(url, {
            "cb-is_public": False,
            "cb-is_active": True,
            "cb-chatbot": self.chatbot.pk,
            "cb-name": "#newchannel2",
            "cb-plugins": [],
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.Channel.objects.count(), channel_count + 1)
        channel = models.Channel.objects.get(name="#newchannel2")
        self.assertEqual(self.member in channel.users.all(), True)

    def test_add_channel_identifiable_url(self):
        self.client.login(username=self.member.username, password="secret")
        url = reverse("add_channel")

        for public, identifiable, name in (
                    (True, True, 'open'),
                    (True, False, 'obfuscated'),
                    (False, True, 'members_only'),
                    (False, False, 'top_secret'),
                ):

            response = self.client.post(url, {
                "cb-is_public": public,
                "cb-is_active": True,
                "cb-chatbot": self.chatbot.pk,
                "cb-name": "#{}".format(name),
                "cb-plugins": [],
                "cb-identifiable_url": identifiable,
            })
            self.assertEqual(response.status_code, 302)
            channel = models.Channel.objects.get(name="#{}".format(name))
            # Non-identifiable channel, channel name shouldn't be in url.
            channel_url = utils.reverse_channel(channel, "log_current")
            if identifiable:
                self.assertIn(name, channel_url)
            else:
                self.assertNotIn(name, channel_url)

    def test_dashboard_annonymous_get(self):
        url = reverse("dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_authenticated_get(self):
        self.client.login(username=self.member.username, password="secret")
        url = reverse("dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_channel_annonymous_get(self):
        url = utils.reverse_channel(self.public_channel, "delete_channel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_channel_owner_get(self):
        channel_count = models.Channel.objects.count()
        self.client.login(username=self.member.username, password="secret")
        url = utils.reverse_channel(self.private_channel, "delete_channel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.Channel.objects.count(), channel_count)

    def test_delete_channel_owner_post(self):
        channel_count = models.Channel.objects.count()
        self.client.login(username=self.member.username, password="secret")
        url = utils.reverse_channel(self.private_channel, "delete_channel")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(models.Channel.objects.count(), channel_count - 1)
        with self.assertRaises(models.Channel.DoesNotExist):
            models.Channel.objects.get(id=self.private_channel.id)

    def test_save_empty_slugs(self):
        self.chatbot.channel_set.create(name="#test1", slug="")
        self.chatbot.channel_set.create(name="#test2", slug="")

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
                             "Sorry, this channel is already being monitored.")

    def test_request_channel_form_invalid_formatted_server(self):
        url = reverse("request_channel")

        response = self.client.post(url, {
            "channel_name": "test_channel_name",
            "server": "new",
            "connection": "irc.freenode.net",
            "name": "test_name",
            "email": "test@example.com",
            "nick": "test_nick",
            "op": True
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "connection",
                             "Incorrect format, should be <url>:<port>")

    def test_request_channel_form_require_connect_if_server_set_to_new(self):
        url = reverse("request_channel")

        response = self.client.post(url, {
            "channel_name": "test_channel_name",
            "server": "new",
            "connection": "",
            "name": "test_name",
            "email": "test@example.com",
            "nick": "test_nick",
            "op": True
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "connection",
                             "This field is required.")

