from django import forms
from . import models

class PluginsForm(forms.Form):
    plugins = forms.ModelMultipleChoiceField(required=False,
        queryset=models.Plugin.objects.all(),
        widget=forms.CheckboxSelectMultiple())

    def __init__(self, channel, *args, **kwargs):
        super(PluginsForm, self).__init__(*args, **kwargs)
        self.channel = channel
        self.fields['plugins'].initial = [p.pk for p in channel.plugins.all()]

    def save(self):
        self.channel.plugins.clear()
        for plugin in self.cleaned_data['plugins']:
            models.ActivePlugin.objects.create(plugin=plugin,
                                               channel=self.channel)
