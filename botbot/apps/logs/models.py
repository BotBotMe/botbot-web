from djorm_pgfulltext.models import SearchManager
from djorm_pgfulltext.fields import VectorField
from django.db import models
from django.conf import settings
from django.template.loader import render_to_string

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
    raw = models.TextField(null=True, blank=True)

    # freenode chan name length limit is 50 chars, Campfire room ids are ints,
    #  so 100 should be enough
    room = models.CharField(max_length=100, null=True, blank=True)

    search_index = VectorField()

    objects = SearchManager(
        fields=('text',),
        config='pg_catalog.english',   # this is default
        search_field='search_index',   # this is default
        auto_update_search_field=False    # We have a db trigger that does it
    )

    class Meta:
        ordering = ('-timestamp',)

    @models.permalink
    def get_absolute_url(self):

        if self.channel.is_public:
            bot_slug = self.channel.chatbot.slug
            chan_slug = self.channel.name.strip("#")
        else:
            bot_slug = 'private'
            chan_slug = self.channel.slug

        return ('log_message', [bot_slug, chan_slug, self.pk])

    def as_html(self):
        return render_to_string("logs/log_display.html",
                                {'message_list': [self], "highlight_pk": -1})

    def notify(self):
        """Send update to Redis queue to be picked up by SSE"""
        utils.send_event_with_id("log", self.as_html(),
            self.timestamp.isoformat(),
            channel="channel_update:{0}".format(self.channel_id))

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
