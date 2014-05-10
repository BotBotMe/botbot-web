from django.contrib import admin

from . import models
from botbot.core.paginator import PostgresLargeTablePaginator


class LogAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'command', 'bot', 'timestamp']
    list_filter = ['bot', 'command']
    paginator = PostgresLargeTablePaginator


admin.site.register(models.Log, LogAdmin)
