import datetime

from django.core.cache import cache
from django.db import models
from django.db.models import Max, Min
from django.utils.datastructures import SortedDict
from django_hstore import hstore
from djorm_pgarray.fields import ArrayField
from botbot.apps.plugins import models as plugins_models

PRETTY_SLUG = {
    "chat.freenode.net": "freenode",
    "irc.oftc.net": "oftc",
    "irc.mozilla.org": "mozilla",
    "irc.coldfront.net": "coldfront",
    "irc.synirc.net": "synirc",
}


class ChatBot(models.Model):
    is_active = models.BooleanField(default=False)
    connection = hstore.DictionaryField(
        default={"is": "not used"},
        help_text="Not used")

    server = models.CharField(
            max_length=100, help_text="Format: irc.example.net:6697")
    server_password = models.CharField(
            max_length=100,
            blank=True,
            null=True,
            help_text="IRC server password - PASS command. Optional")

    nick = models.CharField(max_length=64)
    password = models.CharField(
            max_length=100,
            blank=True,
            null=True,
            help_text="Password to identify with NickServ. Optional.")
    real_name = models.CharField(
            max_length=250,
            help_text="Usually a URL with information about this bot.")

    objects = hstore.HStoreManager()

    @property
    def slug(self):

        server = self.server.split(':')[0]
        return PRETTY_SLUG.get(server, server)

    def __unicode__(self):
        return u'{server} ({nick})'.format(server=self.server, nick=self.nick)

    @property
    def date_cache_key(self):
        return 'dc:{0}'.format(self.pk)


class Channel(models.Model):
    chatbot = models.ForeignKey(ChatBot)
    name = models.CharField(max_length=250,
                            help_text="IRC expects room name: #django")
    slug = models.SlugField(unique=True, blank=True, null=True)
    password = models.CharField(max_length=250, blank=True, null=True,
                                help_text="Password (mode +k) if the channel requires one")
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    plugins = models.ManyToManyField('plugins.Plugin',
                                     through='plugins.ActivePlugin')

    users = models.ManyToManyField('accounts.User',
                                   through='accounts.Membership')
    is_featured = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)

    def get_absolute_url(self):
        from botbot.apps.bots.utils import reverse_channel
        return reverse_channel(self, 'log_current')

    @property
    def active_plugin_slugs_cache_key(self):
        return 'channel:{0}:plugins'.format(self.name)

    def plugin_config_cache_key(self, slug):
        return 'channel:{0}:{1}:config'.format(self.name, slug)

    @property
    def active_plugin_slugs(self):
        """A cached set of the active plugins for the channel"""
        cache_key = self.active_plugin_slugs_cache_key
        cached_plugins = cache.get(cache_key)
        if not cached_plugins:
            plugins = self.activeplugin_set.all().select_related('plugin')
            slug_set = set([actv.plugin.slug for actv in plugins])
            cache.set(cache_key, slug_set)
            cached_plugins = slug_set
        return cached_plugins

    def plugin_config(self, plugin_slug):
        """A cached configuration for an active plugin"""
        cache_key = self.plugin_config_cache_key(plugin_slug)
        cached_config = cache.get(cache_key)
        if not cached_config:
            try:
                active_plugin = self.activeplugin_set.get(
                    plugin__slug=plugin_slug)
                cached_config = active_plugin.variables
            except plugins_models.ActivePlugin.DoesNotExist:
                cached_config = {}
            cache.set(cache_key, cached_config)
        return cached_config


    def user_can_access(self, user, only_owners=False):
        if only_owners:
            if not user.is_authenticated():
                return False
            return self.membership_set.filter(user=user, is_owner=True)\
                .exists()
        if self.is_public:
            return True
        if self.users.filter(pk=user.id).exists():
            return True
        return False

    @property
    def visible_commands_filter(self):
        """
        Provide Q object useful for limiting the logs to those that matter.

        Limits to certain IRC commands (including some more for
        private channels).
        """
        qfilter = models.Q(command__in=['PRIVMSG', 'NICK', 'NOTICE',
                                        'TOPIC', 'ACTION', 'SHUTDOWN'])
        if not self.is_public:
            # Private channels we want to see people arrive and leave too.
            qfilter = (qfilter |
                        models.Q(command__in=['JOIN', 'QUIT',
                                                'PART', 'AWAY']))
        else:
            qfilter = (qfilter |
                        models.Q(command__in=['JOIN', 'QUIT'],
                                nick=self.chatbot.nick))
        return qfilter

    def filtered_logs(self):
        return (self.log_set.filter(self.visible_commands_filter)
                            .exclude(command="NOTICE", nick="NickServ")
                            .exclude(command="NOTICE",
                                     text__startswith="*** "))

    def get_months_active(self):
        """
        Creates a SortedDict of the format:
        {
            ...
            '2010': {
                first_day_of_month_datetime: pk_of_first_log,
                ...
            },
        }
        """
        current_month = datetime.datetime.today().month
        # Added the current month to the key to automatically update
        minmax_dict_key = "minmax_dict_%s_%s" % (self.id, current_month)
        minmax_dict = cache.get(minmax_dict_key, None)
        if minmax_dict is None:
            minmax_dict = self.log_set.all().aggregate(
                last_log=Max("timestamp"),
                first_log=Min("timestamp"))
            if not minmax_dict['first_log']:
                return SortedDict()
            # cache for 10 days
            cache.set(minmax_dict_key, minmax_dict, 864000)
        first_log = minmax_dict['first_log'].date()
        last_log = minmax_dict['last_log'].date()
        last_log = datetime.date(last_log.year, last_log.month, 1)
        current = datetime.date(first_log.year, first_log.month, 1)
        months_active = SortedDict()
        while current <= last_log:
            months_active.setdefault(current.year, []).append(current)
            if current.month == 12:
                current = datetime.date(current.year + 1, 1, 1)
            else:
                current = datetime.date(current.year, current.month + 1, 1)
        return months_active

    def current_size(self):
        """Number of users in this channel.
        We only log hourly, so can be a bit off.
        None if we don't have a record yet.
        """
        try:
            usercount = UserCount.objects.get(channel=self,
                                              dt=datetime.date.today())
        except UserCount.DoesNotExist:
            return None

        hour = datetime.datetime.now().hour

        try:
            # Postgres arrays are 1 based, but here become 0 based, so shift
            count = usercount.counts[hour - 2]
            if not count:
                # Try one hour ago in case not logged this hour yet
                count = usercount.counts[hour - 3]
        except IndexError:
            return None
        return count

    def save(self, *args, **kwargs):
        """
        Ensure that an empty slug is converted to a null slug so that it
        doesn't trip up on multiple slugs being empty.
        """
        if not self.slug:
            self.slug = None
        super(Channel, self).save(*args, **kwargs)


class UserCount(models.Model):
    """Number of users in a channel, per hour."""

    channel = models.ForeignKey(Channel)
    dt = models.DateField()
    counts = ArrayField(dbtype="int")

    def __unicode__(self):
        return "{} on {}: {}".format(self.channel, self.dt, self.counts)
