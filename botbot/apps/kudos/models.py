from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible


class KudosManager(models.Manager):
    use_for_related_fields = True

    def ranks(self, debug=False):
        """
        Return an ordered list of nicks for the current top ranks.

        The nicks are the first element in a list, the second being the nick's
        alltime score. If in debug mode, a dictionary of more information is
        also appended.
        """
        kudos_set = self.all()
        current_scores = reversed(sorted((k.score, k) for k in kudos_set))
        alltime_scores = reversed(sorted((k.count, k.nick) for k in kudos_set))
        alltime_kudos = {}
        for i, (count, nick) in enumerate(alltime_scores):
            alltime_kudos[nick] = i+1
        ranks = []
        for i, (score, k) in enumerate(current_scores):
            current = [
                k.nick,
                alltime_kudos[k.nick],
            ]
            if debug:
                current.append({
                    'current_rank': i+1,
                    'first': k.first.strftime('%d %b %Y'),
                    'recent': k.recent.strftime('%d %b %Y'),
                    'active_weight': k.active_weight(),
                    'kudos_per_day': k.kudos_per_day(),
                })
            ranks.append(current)
        return ranks


@python_2_unicode_compatible
class Kudos(models.Model):
    """
    Kudos given to a person (by being thanked by other people).

    Dates are kept of their very first kudos, and their most recent.
    """
    nick = models.CharField(max_length=255)
    channel = models.ForeignKey('bots.Channel')
    count = models.PositiveIntegerField()
    first = models.DateTimeField()
    recent = models.DateTimeField()

    objects = KudosManager()

    class Meta:
        verbose_name_plural = 'kudos'
        unique_together = ('nick', 'channel')

    def __str__(self):
        return self.nick

    def save(self, *args, **kwargs):
        """
        Always lowercase the nick, and set the first/recent dates if required.
        """
        self.nick = self.nick.lower()
        now = timezone.now()
        if not self.first:
            self.first = now
        if not self.recent:
            self.recent = now
        return super(Kudos, self).save(*args, **kwargs)

    def active_weight(self, min_days=31, max_days=365, now=None):
        now = now or timezone.now()
        age = (now - self.recent).days
        if age > max_days:
            return 0
        return min_days / float(max(age, min_days))

    def kudos_per_day(self, minimum=31):
        days = max((self.recent - self.first).days, minimum)
        return self.count / float(days)

    @property
    def score(self):
        return self.kudos_per_day() * self.active_weight()


@python_2_unicode_compatible
class KudosTotal(models.Model):
    channel = models.OneToOneField('bots.Channel')
    kudos_given = models.PositiveIntegerField()
    message_count = models.PositiveIntegerField()

    def __str__(self):
        return '{} kudos given to {}'.format(self.kudos_given, self.channel)

    @property
    def appreciation(self):
        if not self.message_count:
            return 0
        return self.kudos_given / float(self.message_count)
