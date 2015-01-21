import logging
from botbot_plugins.base import PrivateMessage

LOG = logging.getLogger('botbot.plugin_runner')


class RealPluginMixin(object):
    """
    All the things that need to get added to botbot-plugins
    fake Plugin class to make it work with the bot and web.
    """

    def __init__(self, slug, channel, chatbot_id, app):
        self.slug = slug
        self.channel_id = channel.pk
        self.chatbot_id = chatbot_id
        self.app = app
        self.channel_name = channel.name
        # Configuration variables as a dictionary, from database
        if self.config_class:
            self.prod_config = self.config_class().fields
            plugin_config = channel.plugin_config(self.slug)
            self.prod_config.update(plugin_config)

    def unique_key(self, key):
        """A unique key for the chatbot, channel, plugin, key combination"""
        return u'{0}:{1}:{2}:{3}'.format(self.chatbot_id, self.channel_id,
                                         self.slug, key.strip())

    def store(self, key, value):
        """Saves a key,value to Redis"""
        ukey = self.unique_key(key)
        LOG.info('Storing: %s=%s', ukey, value)
        self.app.storage.set(ukey, value)

    def retrieve(self, key):
        """Retrieves the value for a key from Redis"""
        ukey = self.unique_key(key)
        value = self.app.storage.get(ukey)
        if value:
            value = unicode(value, 'utf-8')
            LOG.info('Retrieved: %s=%s', key, value)
        return value

    def delete(self, key):
        """ Delete the value from Redis"""
        ukey = self.unique_key(key)
        return self.app.storage.delete(ukey) == 1

    def greenlet_respond(self, grnlt):
        """Callback for gevent return values"""
        msg = grnlt.value
        self.respond(msg)

    def respond(self, msg):
        """Writes message back to the channel the line was received on"""
        # Internal method, not part of public API
        if msg:
            nick = self.channel_name
            if isinstance(msg, PrivateMessage):
                lines= msg.msg.split('\n')
                nick = msg.nick
            else:
                lines = msg.split('\n')
            for response_line in lines:
                LOG.info('Write to %s: %s', nick, response_line)
                response_cmd = u'WRITE {0} {1} {2}'.format(self.chatbot_id,
                                                           nick,
                                                           response_line)
                self.app.bot_bus.lpush('bot', response_cmd)
