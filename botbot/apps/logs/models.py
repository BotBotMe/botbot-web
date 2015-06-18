import socket

from djorm_pgfulltext.models import SearchManager
from djorm_pgfulltext.fields import VectorField
from django.db import models
from django.conf import settings
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from botbot.apps.bots.utils import channel_url_kwargs


from . import utils

REDACTED_TEXT = '[redacted]'

MSG_TMPL = {
        u"JOIN": u"{nick} joined the channel",
        u"NICK": u"{nick} is now known as {text}",
        u"QUIT": u"{nick} has quit",
        u"PART": u"{nick} has left the channel",
        u"ACTION": u"{nick} {text}",
        u"SHUTDOWN": u"-- BotBot disconnected, possible missing messages --",
        }


class Log(models.Model):
    bot = models.ForeignKey('bots.ChatBot', null=True)
    channel = models.ForeignKey('bots.Channel', null=True)
    timestamp = models.DateTimeField(db_index=True)
    nick = models.CharField(max_length=255)
    text = models.TextField()
    action = models.BooleanField(default=False)

    command = models.CharField(max_length=50, null=True, blank=True)
    host = models.TextField(null=True, blank=True)
    raw = models.TextField(null=True, blank=True)

    # freenode chan name length limit is 50 chars, Campfire room ids are ints,
    #  so 100 should be enough
    room = models.CharField(max_length=100, null=True, blank=True)

    search_index = VectorField()

    objects = SearchManager(
        fields=('text',),
        config='pg_catalog.english',   # this is default
        search_field='search_index',   # this is default
        auto_update_search_field=True
    )

    class Meta:
        ordering = ('-timestamp',)
        index_together = [
            ['channel', 'timestamp'],
        ]

    def get_absolute_url(self):
        kwargs = channel_url_kwargs(self.channel)
        kwargs['msg_pk'] = self.pk

        return reverse('log_message_permalink', kwargs=kwargs)

    def as_html(self):
        return render_to_string("logs/log_display.html",
                                {'message_list': [self]})
    def get_cleaned_host(self):
        if self.host:
            if '@' in self.host:
                return self.host.split('@')[1]
            else:
                return self.host


    def notify(self):
        """Send update to Nginx to be sent out via SSE"""
        utils.send_event_with_id(
            "log",
            self.as_html(),
            self.timestamp.isoformat(),
            self.get_cleaned_host(),
            channel=self.channel_id)

    def get_nick_color(self):
        return hash(self.nick) % 32

    def __unicode__(self):
        if self.command == u"PRIVMSG":
            text = u''
            if self.nick:
                text += u'{0}: '.format(self.nick)
            text += self.text[:20]
        else:
            try:
                text = MSG_TMPL[self.command].format(nick=self.nick, text=self.text)
            except KeyError:
                text = u"{}: {}".format(self.command, self.text)

        return text

    def save(self, *args, **kwargs):
        is_new = False
        if not self.pk:
            is_new = True
        if self.nick in settings.EXCLUDE_NICKS:
            self.text = REDACTED_TEXT

        obj = super(Log, self).save(*args, **kwargs)
        if is_new:
            self.notify()
        return obj
