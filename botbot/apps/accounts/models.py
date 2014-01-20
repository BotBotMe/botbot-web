import json

from django.db import models
from django.contrib.auth import models as auth_models
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
import pytz

TIMEZONE_CHOICES = [(tz, tz.replace('_', ' ')) for tz in pytz.common_timezones]

class User(auth_models.AbstractUser):
    nick = models.CharField("Preferred nick", max_length=100, blank=True)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES,
                                blank=True)
    class Meta:
        db_table = 'auth_user'

@receiver(user_logged_in)
def set_user_timezone(sender, request, user, **kwargs):
    """Set the session timezone on login"""
    if user.timezone:
        request.session['django_timezone'] = user.timezone


class Membership(models.Model):
    user = models.ForeignKey(User)
    channel = models.ForeignKey('bots.Channel')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'channel')

    def to_json(self):
        return json.dumps(
            {
                'id': self.user.id,
                'admin': self.is_admin,
                'email': self.user.email
            })

    def save(self, *args, **kwargs):
        if self.is_owner:
            self.is_admin = True
        return super(Membership, self).save(*args, **kwargs)
