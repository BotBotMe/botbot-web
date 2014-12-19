from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


class MembershipAdmin(admin.ModelAdmin):
    search_fields = (
        "user__username", "user__email", "channel__name", "channel__slug")
    list_display = ("user", "channel", "get_channel_is_active",
                    "get_channel_is_public", "kind")
    list_filter = ("kind", "is_admin", "is_owner", "channel__is_active")
    raw_id_fields = ("user",)

    def get_channel_is_active(self, obj):
        return obj.channel.is_active
    get_channel_is_active.short_description = "channel is actve"

    def get_channel_is_public(self, obj):
        return obj.channel.is_public
    get_channel_is_public.short_description = "channel is public"


class CustomUserAdmin(UserAdmin):
    list_display = (
    'username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')


admin.site.register(models.User, CustomUserAdmin)
admin.site.register(models.Membership, MembershipAdmin)
