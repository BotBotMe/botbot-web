 # -*- coding: utf-8 -*-
from django.test import TestCase

from .models import Log
from botbot.apps.bots.models import ChatBot, Channel
from botbot.apps.bots.utils import reverse_channel

import pytz
import datetime


class BaseTestCase(TestCase):
    def setUp(self):
        self.chatbot = ChatBot.objects.create(
                server='testserver',
                nick='botbot')
        self.public_channel = Channel.objects.create(
            chatbot=self.chatbot,
            name="#Test",
            is_public=True)
        self.log = Log.objects.create(
            channel=self.public_channel,
            command='PRIVMSG',
            timestamp=pytz.utc.localize(datetime.datetime.now()))

class UrlTests(BaseTestCase):

    def test_current_redirects_to_today(self):
        url = reverse_channel(self.public_channel, "log_current")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)
        self.assertTrue('/%s-%s-%s' % (self.log.timestamp.year,self.log.timestamp.month,self.log.timestamp.day) in res.url)

    def test_day_log_viewer(self):
        url = reverse_channel(self.public_channel, "log_current")
        day_url = self.client.get(url).url
        res = self.client.get(day_url)
        self.assertEqual(res.status_code, 200)

    def test_missed_log(self):
        Log.objects.create(
            channel=self.public_channel,
            command='QUIT',
            nick="test",
            timestamp=pytz.utc.localize(datetime.datetime.now()))
        Log.objects.create(
            channel=self.public_channel,
            nick="test",
            timestamp=pytz.utc.localize(datetime.datetime.now()+ datetime.timedelta(seconds=1)))
        url = "%smissed/test/" % reverse_channel(self.public_channel, "log_current")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_searched_log(self):
        Log.objects.create(
            channel=self.public_channel,
            nick="test",
            text="This is a test",
            timestamp=pytz.utc.localize(datetime.datetime.now()+ datetime.timedelta(seconds=1)))
        url = "%ssearch/?q=test" % reverse_channel(self.public_channel, "log_current")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)