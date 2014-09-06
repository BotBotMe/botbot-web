from django.contrib import admin
from . import models

class ActivePluginAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'configuration')
    list_filter = ('channel', 'plugin')
    list_editable = ('configuration',)

admin.site.register(models.Plugin)
admin.site.register(models.ActivePlugin, ActivePluginAdmin)
