import json

from django.db import models
from django.contrib.auth import models as auth_models
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
import pytz

TIMEZONE_CHOICES = [(tz, tz.replace('_', ' ')) for tz in pytz.common_timezones]


class User(auth_models.AbstractUser):
    nick = models.CharField("Preferred nick", max_length=100, blank=True)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES,
                                blank=True)

    class Meta:
        db_table = 'auth_user'

    def get_quantity_per_membership_kind(self):
        """
        Group the membership per kind and count them
        The result is a list of dict:
            [
                {'kind': u'public', 'quantity': 1},
                {'kind': u'personal', 'quantity': 2}
            ]
        """
        return (
            self.membership_set
                .filter(channel__is_active=True)
                .filter(
                    models.Q(kind=Membership.KIND_PERSONAL, channel__is_public=False) | 
                    models.Q(kind=Membership.KIND_PUBLIC))
                .values("kind")
                .annotate(quantity=models.Count("kind"))
            )


@receiver(user_logged_in)
def set_user_timezone(sender, request, user, **kwargs):
    """Set the session timezone on login"""
    if user.timezone:
        request.session['django_timezone'] = user.timezone


class Membership(models.Model):
    KIND_PERSONAL = "personal"
    KIND_PUBLIC = "public"
    KIND_CHOICES = (
        (KIND_PERSONAL, KIND_PERSONAL.title()),
        (KIND_PUBLIC, KIND_PUBLIC.title()),
    )

    user = models.ForeignKey(User)
    channel = models.ForeignKey('bots.Channel')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    kind = models.CharField(
        max_length=30, choices=KIND_CHOICES, default=KIND_PERSONAL)

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
