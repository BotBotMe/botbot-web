# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.template.response import SimpleTemplateResponse
import pytz

from botbot.apps.accounts import models as account_models
from botbot.apps.bots import models as bot_models
from botbot.apps.logs import models as log_models
from .management.commands import redact as redact_cmd
from botbot.apps.bots.models import ChatBot, Channel
from botbot.apps.bots.utils import reverse_channel
from botbot.apps.kudos.models import Kudos, KudosTotal

class BaseTestCase(TestCase):
    def setUp(self):
        self.chatbot = ChatBot.objects.create(
            server='testserver',
            nick='botbot')
        self.public_channel = Channel.objects.create(
            chatbot=self.chatbot,
            name="#Test",
            slug="test",
            status=bot_models.Channel.ACTIVE,
            is_public=True)
        self.log = log_models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            timestamp=timezone.now())


class SmokeTests(BaseTestCase):

    def test_current_viewer(self):
        url = reverse_channel(self.public_channel, "log_current")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_day_log_viewer(self):
        url = reverse_channel(
            self.public_channel,
            "log_day",
            kwargs=dict(
            year=self.log.timestamp.year,
            month="%02d" % self.log.timestamp.month,
            day="%02d" % self.log.timestamp.day))
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_day_log_text_viewer(self):
        url = reverse_channel(
            self.public_channel,
            "log_day_text",
            kwargs=dict(
            year=self.log.timestamp.year,
            month="%02d" % self.log.timestamp.month,
            day="%02d" % self.log.timestamp.day))
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_missed_log(self):
        log_models.Log.objects.create(
            channel=self.public_channel,
            command='QUIT',
            nick="test",
            timestamp=timezone.now())
        log_models.Log.objects.create(
            channel=self.public_channel,
            nick="test",
            timestamp=timezone.now() + datetime.timedelta(seconds=1))
        url = "%smissed/test/" % reverse_channel(self.public_channel, "log_current")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_searched_log(self):
        log_models.Log.objects.create(
            channel=self.public_channel,
            nick="test",
            text="This is a test",
            timestamp=timezone.now() + datetime.timedelta(seconds=1))
        url = "%ssearch/?q=test" % reverse_channel(self.public_channel, "log_current")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)


class SearchTestCase(TestCase):
    def setUp(self):
        self.chatbot = bot_models.ChatBot.objects.create(
            server='testserver', nick='botbot', slug='botbot')

        self.public_channel = bot_models.Channel.objects.create(
            chatbot=self.chatbot, name="#Test", slug='test', status=bot_models.Channel.ACTIVE,
            is_public=True)

    def _add_log_line(self, text, nick="Nick"):
        obj = log_models.Log.objects.create(
            bot=self.chatbot, channel=self.public_channel,
            timestamp=timezone.now(), nick=nick, text=text, command='PRIVMSG')
        obj.update_search_field()
        return obj

    def test_simple_search(self):
        a = self._add_log_line("Hello World")
        b = self._add_log_line("Hello Europe")

        # Just search for "World"
        results = log_models.Log.objects.search("World")
        self.assertTrue(a in results)
        self.assertFalse(b in results)

        # Search for Hello which returns both results
        results = log_models.Log.objects.search("Hello")
        self.assertTrue(a in results)
        self.assertTrue(b in results)

    def test_nick_search_front(self):
        a = self._add_log_line("Hello World", nick="Foo")
        b = self._add_log_line("Hello World", nick="Bar")
        url = reverse('log_search', kwargs={
            'bot_slug': self.chatbot.slug,
            'channel_slug': self.public_channel.slug,
        }) + '?q=nick:Foo%20World'

        response = self.client.get(url)
        context = response.context_data['object_list']

        self.assertEqual(len(context), 1)
        self.assertTrue(a in context)
        self.assertFalse(b in context)

    def test_nick_search_end(self):
        a = self._add_log_line("Hello World", nick="Foo")
        b = self._add_log_line("Hello World", nick="Bar")
        url = reverse('log_search', kwargs={
            'bot_slug': self.chatbot.slug,
            'channel_slug': self.public_channel.slug,
        }) + '?q=World%20nick:Foo'

        response = self.client.get(url)
        context = response.context_data['object_list']

        self.assertEqual(len(context), 1)
        self.assertTrue(a in context)
        self.assertFalse(b in context)

    def test_nick_search_both(self):
        a = self._add_log_line("Hello World", nick="Foo")
        b = self._add_log_line("Hello World", nick="Bar")
        url = reverse('log_search', kwargs={
            'bot_slug': self.chatbot.slug,
            'channel_slug': self.public_channel.slug,
        }) + '?q=World%20nick:Foo%20Hello'

        response = self.client.get(url)
        context = response.context_data['object_list']

        self.assertEqual(len(context), 1)
        self.assertTrue(a in context)
        self.assertFalse(b in context)

class TemplateTestCase(TestCase):
    def setUp(self):
        self.chatbot = bot_models.ChatBot.objects.create(
            server='testserver', nick='botbot', slug='botbot')

        self.public_channel = bot_models.Channel.objects.create(
            chatbot=self.chatbot, name="#Test", slug='test',
            is_public=True)

    def test_logs_xss(self):
        log = log_models.Log.objects.create(
            bot=self.chatbot, channel=self.public_channel,
            timestamp=timezone.now(), nick='nick', text='<script>alert("hi")</script>',
            command='PRIVMSG')
        response = SimpleTemplateResponse('logs/log_display.html', {'message_list': [log]}).render()
        self.assertIn('&lt;script&gt;alert', response.content)


class TemplateTagTestCase(TestCase):
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

        self.assertEqual(
            urlize_impl(u'http://www.example.com\017'),
            u'<a href="http://www.example.com">http://www.example.com</a>'
        )

        # Test with a unicode char
        self.assertEqual(
            urlize_impl(u'https://forge.puppetlabs.com/modules?utf-8=✓&sort=latest_release&supported=yes'),
            u'<a href="https://forge.puppetlabs.com/modules?utf-8=%E2%9C%93&sort=latest_release&supported=yes">https://forge.puppetlabs.com/modules?utf-8=✓&sort=latest_release&supported=yes</a>'
        )

        # Test image
        self.assertEqual(
            urlize_impl(u'http://www.example.com/image.png'),
            u'<a data-src="http://www.example.com/image.png" href="http://www.example.com/image.png" data-type="image" class="image">http://www.example.com/image.png</a>'
        )

        # Test youtube video
        self.assertEqual(
            urlize_impl(u'https://www.youtube.com/watch?v=dQw4w9WgXcQ'),
            u'<a data-src="//www.youtube.com/embed/dQw4w9WgXcQ" href="https://www.youtube.com/watch?v=dQw4w9WgXcQ" data-type="youtube" class="image">https://www.youtube.com/watch?v=dQw4w9WgXcQ</a>'
        )

        # Test invalid youtube link
        self.assertEqual(
            urlize_impl(u'https://www.youtube.com/watch'),
            u'<a href="https://www.youtube.com/watch">https://www.youtube.com/watch</a>'
        )

        # Test dropbox
        self.assertEqual(
            urlize_impl(u'https://www.dropbox.com/s/1vbeuicgr18ialb/Screenshot%202014-06-09%2015.02.39.png'),
            u'<a data-src="https://dl.dropboxusercontent.com/s/1vbeuicgr18ialb/Screenshot%202014-06-09%2015.02.39.png" href="https://www.dropbox.com/s/1vbeuicgr18ialb/Screenshot%202014-06-09%2015.02.39.png" data-type="image" class="image">https://www.dropbox.com/s/1vbeuicgr18ialb/Screenshot%202014-06-09%2015.02.39.png</a>'
        )

        # Test cloudapp
        self.assertEqual(
            urlize_impl(u'http://cl.ly/image/1Y0A1C3l370z'),
            u'<a data-src="http://cl.ly/1Y0A1C3l370z/content" href="http://cl.ly/image/1Y0A1C3l370z" data-type="image" class="image">http://cl.ly/image/1Y0A1C3l370z</a>'
        )

        # Test cloudapp without image in url
        self.assertEqual(
            urlize_impl(u'http://cl.ly/1Y0A1C3l370z'),
            u'<a data-src="http://cl.ly/1Y0A1C3l370z/content" href="http://cl.ly/1Y0A1C3l370z" data-type="image" class="image">http://cl.ly/1Y0A1C3l370z</a>'
        )


class RedactTests(TestCase):
    def setUp(self):
        self.chatbot = bot_models.ChatBot.objects.create(
            server='testserver',
            nick='botbot')
        self.public_channel = bot_models.Channel.objects.create(
            chatbot=self.chatbot,
            slug="test",
            name="#Test",
            is_public=True)

    def test_command(self):
        log_models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            text='this is a test',
            nick='not-redact',
            timestamp=timezone.now())
        log_models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            text='this is a test',
            nick='redact',
            timestamp=timezone.now())
        redacted = log_models.Log.objects.filter(text=log_models.REDACTED_TEXT)
        self.assertFalse(redacted.exists())
        count = redact_cmd._redact_logs_for_nick('redact')
        self.assertEqual(count, 1)
        self.assertEqual(redacted.count(), 1)
        self.assertEqual(redacted[0].text, log_models.REDACTED_TEXT)

    @override_settings(EXCLUDE_NICKS=['redact'])
    def test_setting(self):
        not_redacted = log_models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            text='this is a test',
            nick='not-redact',
            timestamp=timezone.now())
        self.assertNotEqual(not_redacted.text, log_models.REDACTED_TEXT)
        redacted = log_models.Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            text='this is a test',
            nick='redact',
            timestamp=timezone.now())
        self.assertEqual(redacted.text, log_models.REDACTED_TEXT)


class KudosTests(BaseTestCase):

    def setUp(self):
        super(KudosTests, self).setUp()
        kudos = []
        for i, letter in enumerate('abcdefghijklmnopqrstuvwxyz'):
            kudos.append(Kudos(
                nick=letter*3, count=1+i+(i % 5), channel=self.public_channel,
                first=timezone.now()-datetime.timedelta(days=100),
                recent=timezone.now()))
        Kudos.objects.bulk_create(kudos)
        self.url = reverse_channel(self.public_channel, "kudos")

    def test_basic(self):
        response = self.client.get(self.url)
        self.assertIn('logs/kudos.html', response.template_name)

    def test_randomized_order(self):
        scoreboards = []
        for i in range(10):
            response = self.client.get(self.url)
            scoreboards.append(response.context_data['random_scoreboard'])
        same = True
        for scoreboard in scoreboards[1:]:
            if scoreboards[0] != scoreboard:
                same = False
                break
        self.assertFalse(same, 'Scoreboards were not shuffled')

    def test_no_kudos(self):
        self.public_channel.kudos_set.all().delete()
        response = self.client.get(self.url)
        self.assertIn('logs/kudos.html', response.template_name)

    def test_kudos_total(self):
        KudosTotal.objects.create(
            channel=self.public_channel, kudos_given=300,
            message_count=900)
        response = self.client.get(self.url)
        self.assertContains(response, ' 33.33%')

    def test_kudos_total_zero(self):
        KudosTotal.objects.create(
            channel=self.public_channel, kudos_given=0,
            message_count=0)
        response = self.client.get(self.url)
        self.assertIn('logs/kudos.html', response.template_name)
        self.assertNotIn('channel_kudos_perc', response.context_data)


    def test_not_public_kudos_admin(self):
        self.public_channel.public_kudos = False
        self.public_channel.save()
        admin = account_models.User.objects.create_user(
            username="admin",
            password="password",
            email="admin@botbot.local")

        self.assertTrue(self.client.login(
            username='admin', password='password'))
        response = self.client.get(self.url)
        self.assertIn('logs/kudos.html', response.template_name)


class KudosJSONTest(BaseTestCase):

    def setUp(self):
        super(KudosJSONTest, self).setUp()
        member = account_models.User.objects.create_user(
            username="member",
            password="password",
            email="member@botbot.local")
        admin = account_models.User.objects.create_user(
            username="admin",
            password="password",
            email="admin@botbot.local")
        self.url = reverse_channel(self.public_channel, "kudos_json")

    def test_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_basic(self):
        self.client.login(username='member', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/json')


    def test_not_public_kudos_admin(self):
        self.public_channel.public_kudos = False
        self.public_channel.save()

        self.assertTrue(self.client.login(
            username='admin', password='password'))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/json')
