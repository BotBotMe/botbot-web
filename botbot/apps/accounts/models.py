import pytz
from django.contrib.auth import models as auth_models
from django.db import models

TIMEZONE_CHOICES = [(tz, tz.replace('_', ' ')) for tz in pytz.common_timezones]


class User(auth_models.AbstractUser):
    nick = models.CharField("Preferred nick", max_length=100, blank=True)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES,
                                blank=True)

    class Meta:
        db_table = 'auth_user'
