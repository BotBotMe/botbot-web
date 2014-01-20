import datetime

from django.db import transaction
from django.utils.timezone import utc

from botbot.apps.logs.models import Log
from botbot_plugins.base import BasePlugin


class Plugin(BasePlugin):
    """
    Logs all activity.

    I keep extensive logs on all the activity in `{{ channel.name }}`.
    You can read and search them at {{ SITE }}{{ channel.get_absolute_url }}.
    """
    def logit(self, line):
        """Log a message to the database"""
        # If the Channel do not startswtih "#" that means the message
        # is part of a /query
        if line._channel_name.startswith("#"):
            # convert nanoseconds to microseconds
            # http://stackoverflow.com/a/10612166/116042
            rfc3339, nano_part = line._received.split('.')
            micro = nano_part[0:5]
            rfc3339micro = ''.join([rfc3339, '.', micro, 'Z'])
            timestamp = datetime.datetime.strptime(
                rfc3339micro, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=utc)
            with transaction.commit_on_success():
                Log.objects.create(
                    channel_id=line._channel.pk,
                    timestamp=timestamp,
                    nick=line.user,
                    text=line.full_text,
                    room=line._channel,
                    command=line._command,
                    raw=line._raw)

    logit.route_rule = ('firehose', ur'(.*)')
