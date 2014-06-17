"""Django admin configuration for the bot objects.
"""
from django.contrib import admin
from django.db import transaction
from django.forms.models import BaseInlineFormSet
import redis

from . import models
from botbot.apps.plugins.models import Plugin

class PluginFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        if not kwargs['instance'].pk:
            defaults = Plugin.objects.filter(
                slug__in=models.Channel.DEFAULT_PLUGINS)

            kwargs['initial'] = [{"plugin": obj.pk} for obj in defaults]
        super(PluginFormset, self).__init__(*args, **kwargs)


class ActivePluginInline(admin.StackedInline):
    model = models.Channel.plugins.through
    formset = PluginFormset

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None:
            return len(models.Channel.DEFAULT_PLUGINS)
        return 0


class MembershipInline(admin.TabularInline):
    model = models.Channel.users.through
    extra = 0


class ChatBotAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    readonly_fields = ('connection', 'server_identifier')

    # Disable bulk delete, because it doesn't call delete, so skips REFRESH
    actions = None

    def save_model(self, request, obj, form, change):
        super(ChatBotAdmin, self).save_model(request, form, form, change)
        transaction.commit()
        daemon_refresh()

    def delete_model(self, request, obj):
        super(ChatBotAdmin, self).delete_model(request, obj)
        transaction.commit()
        daemon_refresh()


class ChannelAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'name', 'chatbot', 'is_active',
                    'is_public', 'is_featured', 'is_pending', 'updated')
    list_filter = ('chatbot', 'is_active', 'is_public', 'is_featured', 'is_pending')
    list_editable = ('is_active',)
    readonly_fields = ('fingerprint', 'created', 'updated')
    search_fields = ('name', 'chatbot__server')
    inlines = [
            ActivePluginInline,
            MembershipInline
        ]

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        super(ChannelAdmin, self).save_model(request, obj, form, change)
        transaction.commit()
        daemon_refresh()

    def delete_model(self, request, obj):
        """
        Given a model instance delete it from the database.
        """
        super(ChannelAdmin, self).delete_model(request, obj)
        transaction.commit()
        daemon_refresh()
        

def daemon_refresh():
    """
    Ask daemon to reload configuration
    """
    queue = redis.Redis(db=0)
    queue.lpush('bot', 'REFRESH')


admin.site.register(models.ChatBot, ChatBotAdmin)
admin.site.register(models.Channel, ChannelAdmin)
admin.site.register(models.UserCount)
