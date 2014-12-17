from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "kind")
    list_filter = ("kind", "is_admin", "is_owner")
    raw_id_fields = ("user",)


class CustomUserAdmin(UserAdmin):
    list_display = (
    'username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')


admin.site.register(models.User, CustomUserAdmin)
admin.site.register(models.Membership, MembershipAdmin)
