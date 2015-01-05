from django import forms

from . import models


class AccountForm(forms.ModelForm):

    class Meta:
        model = models.User
        exclude = ('first_name', 'last_name', 'password', 'is_staff',
                   'is_active', 'is_superuser', 'last_login', 'date_joined',
                   'groups', 'user_permissions', 'email')

class TimezoneForm(forms.Form):
    CHOICES = [('', '')]
    CHOICES.extend(models.TIMEZONE_CHOICES)
    timezone = forms.ChoiceField(choices=CHOICES, required=False)

    def __init__(self, request, *args, **kwargs):
        super(TimezoneForm, self).__init__(*args, **kwargs)
        self.request = request
        self.fields['timezone'].initial = request.session.get('django_timezone',
                                                              "")
    def save(self):
        tz = self.cleaned_data['timezone']
        self.request.session['django_timezone'] = tz
        if self.request.user.is_authenticated():
            self.request.user.timezone = tz
            self.request.user.save()
