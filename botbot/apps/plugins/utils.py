import datetime
from functools import wraps

from django.template import Template, Context
from django.template.defaultfilters import urlize
from django.utils.timezone import utc

import markdown

def plugin_docs_as_html(plugin, channel):
    tmpl = Template(plugin.user_docs)
    ctxt = Context({
        'nick': channel.chatbot.nick,
        'channel': channel,
        'SITE': 'https://botbot.me',
    })
    return markdown.markdown(urlize(tmpl.render(ctxt)))

def convert_nano_timestamp(nano_timestamp):
    """
    Takes a time string created by the bot (in Go using nanoseconds)
    and makes it a Python datetime using microseconds
    """
    # convert nanoseconds to microseconds
    # http://stackoverflow.com/a/10612166/116042
    rfc3339, nano_part = nano_timestamp.split('.')
    micro = nano_part[:-1] # strip trailing "Z"
    if len(nano_part) > 6: # trim to max size Python allows
        micro = micro[:6]
    rfc3339micro = ''.join([rfc3339, '.', micro, 'Z'])
    micro_timestamp = datetime.datetime.strptime(
        rfc3339micro, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=utc)
    return micro_timestamp


def log_on_error(Log, method):
    @wraps(method)
    def wrap(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception:
            Log.error("Plugin failed [%s]", method.__name__, exc_info=True)
    return wrap
