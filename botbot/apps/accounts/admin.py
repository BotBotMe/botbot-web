from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models

class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "kind")
    list_filter = ("kind", "is_admin", "is_owner")

admin.site.register(models.User, UserAdmin)
admin.site.register(models.Membership, MembershipAdmin)
