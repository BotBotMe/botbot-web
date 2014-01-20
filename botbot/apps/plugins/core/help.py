# pylint: disable=W0212
from botbot.apps.bots.utils import reverse_channel
from botbot_plugins.base import BasePlugin
from botbot_plugins.decorators import listens_to_mentions


SITE = "https://botbot.me"


class Plugin(BasePlugin):
    """
    Shows available plugins and descriptions.

    Simply ask for help and I'll gladly tell you what I'm capable of:

        {{ nick }}: help

    For further details, you can ask me about a specific plugin:

        {{ nick }}: help images
    """
    @listens_to_mentions(ur'^help$')
    def respond_to_help(self, line):
        plugins = [plgn.slug for plgn in line._channel.plugins.all()]
        help_url = get_help_url(line._channel)
        return u'Available plugins: {0} ({1})'.format(', '.join(plugins),
                                                      help_url)

    @listens_to_mentions(ur'^help (?P<command>.*)')
    def respond_to_plugin_help(self, line, command):
        """Returns first line of docstring and link to more"""
        slug = command.strip()
        try:
            plugin = line._channel.plugins.filter(slug=slug)[0]
            help_url = get_help_url(line._channel)
            response = [
                plugin.user_docs.strip().split('\n')[0],
                'More details: {0}#{1}'.format(help_url, command)
            ]
            return '\n'.join(response)
        except IndexError:
            return 'Sorry, that plugin is not available.'


def get_help_url(channel):
    return SITE + reverse_channel(channel, "help_bot")
