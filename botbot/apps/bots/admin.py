"""Django admin configuration for the bot objects.
"""
import redis
from django import forms
from django.conf import settings
from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from . import models


class PluginFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(PluginFormset, self).__init__(*args, **kwargs)


class ActivePluginInline(admin.StackedInline):
    model = models.Channel.plugins.through
    formset = PluginFormset

    def get_extra(self, request, obj=None, **kwargs):
        return 0



class ChatBotAdmin(admin.ModelAdmin):
    exclude = ('connection', 'server_identifier')
    list_display = ('__unicode__', 'is_active', 'usage')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    readonly_fields = ('server_identifier',)

    # Disable bulk delete, because it doesn't call delete, so skips REFRESH
    actions = None

    def usage(self, obj):
        return "%d%%" % (
            (obj.channel_set.filter(status=models.Channel.ACTIVE).count() / float(obj.max_channels)) * 100)


def botbot_refresh(modeladmin, request, queryset):
    """
    Ask daemon to reload configuration
    """
    queue = redis.from_url(settings.REDIS_PLUGIN_QUEUE_URL)
    queue.lpush('bot', 'REFRESH')
botbot_refresh.short_description = "Reload botbot-bot configuration"


class ChannelForm(forms.ModelForm):
    class Meta:
        model = models.Channel
        exclude = []

    def clean_private_slug(self):
        return self.cleaned_data['private_slug'] or None


class ChannelAdmin(admin.ModelAdmin):
    form = ChannelForm
    list_display = ('name', 'chatbot', 'status', 'is_featured', 'created', 'updated')
    list_filter = ('status', 'is_featured', 'is_public', 'chatbot')
    prepopulated_fields = {
        'slug': ('name',)
    }
    list_editable = ('chatbot','status',)
    readonly_fields = ('fingerprint', 'created', 'updated')
    search_fields = ('name', 'chatbot__server')
    inlines = [ActivePluginInline]
    actions = [botbot_refresh]


class PublicChannelApproval(ChannelAdmin):
    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        qs = super(PublicChannelApproval, self).get_queryset(request)
        return qs.filter(status=self.model.ACTIVE, is_public=True)


class PublicChannels(models.Channel):
    class Meta:
        proxy = True
        verbose_name = "Pending Public Channel"

admin.site.register(PublicChannels, PublicChannelApproval)

admin.site.register(models.ChatBot, ChatBotAdmin)
admin.site.register(models.Channel, ChannelAdmin)
admin.site.register(models.UserCount)
