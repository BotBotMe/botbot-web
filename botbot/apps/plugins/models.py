from django.core.cache import cache
from django.contrib.admindocs.utils import trim_docstring
from django.db import models
from django.utils.importlib import import_module

from botbot.core.fields import JSONField


class Plugin(models.Model):
    """A global plugin registered in botbot"""
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    @property
    def user_docs(self):
        for mod_prefix in ('botbot_plugins.plugins.',
                           'botbot.apps.plugins.core.'):
            try:
                docs = import_module(mod_prefix + self.slug).Plugin.__doc__
                return trim_docstring(docs)
            except (ImportError, AttributeError):
                continue
        return ''

    def __unicode__(self):
        return self.name


class ActivePlugin(models.Model):
    """An active plugin for a ChatBot"""
    plugin = models.ForeignKey('plugins.Plugin')
    channel = models.ForeignKey('bots.Channel')
    configuration =  JSONField(
            blank=True, default={},
            help_text="User-specified attributes for this plugin " +
            '{"username": "joe", "api-key": "foo"}')

    def save(self, *args, **kwargs):
        obj = super(ActivePlugin, self).save(*args, **kwargs)
        # Let the plugin_runner auto-reload the new values
        cache.delete(self.channel.plugin_config_cache_key(self.plugin.slug))
        cache.delete(self.channel.active_plugin_slugs_cache_key)
        return obj

    def __unicode__(self):
        return u'{0} for {1}'.format(self.plugin.name, self.channel.name)
