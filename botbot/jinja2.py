from __future__ import absolute_import  # Python 2 only

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.urlresolvers import reverse
from django.utils.timezone import now

from jinja2 import Environment

from botbot.apps.bots.utils import reverse_channel
from botbot.apps.logs.templatetags.logs_tags import bbme_urlizetrunc


def environment(**options):
    options['extensions'] = [
        'pipeline.templatetags.ext.PipelineExtension',
    ]
    env = Environment(**options)
    env.globals.update({
        # django
        'static': staticfiles_storage.url,
        'url': reverse,
        'now': now,
        # bots
        'channel_url': reverse_channel,
        # logs
        'bbme_urlizetrunc': bbme_urlizetrunc
    })
    return env
