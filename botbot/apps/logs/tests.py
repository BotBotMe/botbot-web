 # -*- coding: utf-8 -*-

from django.utils.timezone import now
from django.test import TestCase
from django.test.utils import override_settings

from botbot.apps.bots import models as bot_models
from .management.commands import redact as redact_cmd
from . import models

class BestTestEver(TestCase):
    def test_urlize_impl_handling_with_control_chars(self):
        """
        The Github IRC bot puts a 'shift up' control character at the
        end of the link, which was not removed before transforming a link
        to a clickable HTML link.

        https://github.com/BotBotMe/botbot-web/issues/8 %0F
        """
        from botbot.apps.logs.templatetags.logs_tags import urlize_impl

        # Simple link with no control characters
        self.assertEqual(
            urlize_impl(u'http://www.example.com'),
            u'<a href="http://www.example.com">http://www.example.com</a>'
        )

        # Simple link with no control characters
        self.assertEqual(
            urlize_impl(u'http://www.example.com\017'),
            u'<a href="http://www.example.com">http://www.example.com</a>'
        )

class RedactTests(TestCase):
    def setUp(self):
        self.chatbot = bot_models.ChatBot.objects.create(
                server='testserver',
                nick='botbot')
        self.public_channel = bot_models.Channel.objects.create(
            chatbot=self.chatbot,
            name="#Test",
            is_public=True)

    def test_command(self):
        models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            text='this is a test',
            nick='not-redact',
            timestamp=now())
        models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            text='this is a test',
            nick='redact',
            timestamp=now())
        redacted = models.Log.objects.filter(text=models.REDACTED_TEXT)
        self.assertFalse(redacted.exists())
        count = redact_cmd._redact_logs_for_nick('redact')
        self.assertEqual(count, 1)
        self.assertEqual(redacted.count(), 1)
        self.assertEqual(redacted[0].text, models.REDACTED_TEXT)

    @override_settings(EXCLUDE_NICKS=['redact'])
    def test_setting(self):
        not_redacted = models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            text='this is a test',
            nick='not-redact',
            timestamp=now())
        self.assertNotEqual(not_redacted.text, models.REDACTED_TEXT)
        redacted = models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            text='this is a test',
            nick='redact',
            timestamp=now())
        self.assertEqual(redacted.text, models.REDACTED_TEXT)

