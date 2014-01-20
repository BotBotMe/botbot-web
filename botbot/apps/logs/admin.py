from django.contrib import admin

from . import models


class LogAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'command', 'bot', 'timestamp']
    list_filter = ['bot', 'command']


admin.site.register(models.Log, LogAdmin)
