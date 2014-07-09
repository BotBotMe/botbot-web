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
    exclude = ('connection', )
    list_display = ('__unicode__', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    readonly_fields = ('server_identifier', )

    # Disable bulk delete, because it doesn't call delete, so skips REFRESH
    actions = None

    def save_related(self, request, form, formsets, change):
        super(ChatBotAdmin, self).save_related(request, form, formsets, change)
        daemon_refresh()

    def delete_model(self, request, obj):
        super(ChatBotAdmin, self).delete_model(request, obj)
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

    def save_related(self, request, form, formsets, change):
        super(ChannelAdmin, self).save_related(request, form, formsets, change)
        daemon_refresh()

    def delete_model(self, request, obj):
        super(ChannelAdmin, self).delete_model(request, obj)
        daemon_refresh()

def daemon_refresh():
    """
    Ask daemon to reload configuration
    """
    # Wait until the db transaction is done and then send the REFRESH command
    # so the Go bot part will update it.

    # THIS IS NO-OP SINCE DJANGO1.6 TRANSACTION REDESIGN
    # See https://django-transaction-hooks.readthedocs.org/ for a better
    # implementation.
    if transaction.is_managed():
        transaction.commit()

    from time import sleep
    sleep(1)

    queue = redis.Redis(db=0)
    queue.lpush('bot', 'REFRESH')


admin.site.register(models.ChatBot, ChatBotAdmin)
admin.site.register(models.Channel, ChannelAdmin)
admin.site.register(models.UserCount)
