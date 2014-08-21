from django.contrib import admin

from . import models
from botbot.core.paginator import PostgresLargeTablePaginator


class CommandListFilter(admin.SimpleListFilter):
    title = "Command"
    parameter_name = "command"

    def lookups(self, request, model_admin):
        return (
            ('ACTION', 'ACTION'),
            ('ERROR', 'ERROR'),
            ('JOIN', 'JOIN'),
            ('KICK', 'KICK'),
            ('MODE', 'MODE'),
            ('NICK', 'NICK'),
            ('NOTICE', 'NOTICE'),
            ('PART', 'PART'),
            ('PING', 'PING'),
            ('PRIVMSG', 'PRIVMSG'),
            ('QUIT', 'QUIT'),
            ('SHUTDOWN', 'SHUTDOWN'),
            ('TOPIC', 'TOPIC'),
            ('VERSION', 'VERSION'),
        )

    def queryset(self, request, queryset):
        return queryset.filter(command=self.value())


class LogAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'command', 'bot', 'timestamp']
    list_filter = ['bot', CommandListFilter]
    paginator = PostgresLargeTablePaginator


admin.site.register(models.Log, LogAdmin)
