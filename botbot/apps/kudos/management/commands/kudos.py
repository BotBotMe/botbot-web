from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max
from botbot.apps.bots.models import Channel

from botbot.apps.kudos import utils, models


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--force', '-f', action='store_true',
            help='Force full scan of kudos'),
        make_option(
            '--all', action='store_true', help='All channels'),
    )

    @transaction.atomic
    def handle(self, *args, **options):
        qs = Channel.objects.all()
        if args:
            qs = qs.filter(name__in=args)
        if (not options.get('all') and not args) or not qs:
            raise CommandError('No channels to parse')
        verbosity = int(options['verbosity'])
        if verbosity > 1:
            parse_stdout = self.stdout
        else:
            parse_stdout = None
        for channel in qs:
            if verbosity:
                self.stdout.write('Processing {}...'.format(channel))
                self.stdout.flush()
            qs = channel.log_set.all()
            if options['force']:
                self.stdout.write('(removing any kudos and doing full check)')
                self.stdout.flush()
                channel.kudos_set.all().delete()
                try:
                    channel.kudostotal.delete()
                except models.KudosTotal.DoesNotExist:
                    pass
            else:
                # Look up kudos for this channel, find max(recent), and limit
                # queryset to after that.
                recent = channel.kudos_set.aggregate(Max('recent')).values()[0]
                if recent:
                    qs = qs.filter(timestamp__gt=recent)
                    if verbosity:
                        self.stdout.write('(found existing kudos, updating)')
                        self.stdout.flush()
                else:
                    if verbosity:
                        self.stdout.write(
                            '(no existing kudos found, full check)')
                        self.stdout.flush()
            result = utils.parse_logs(qs, parse_stdout)
            if verbosity:
                self.stdout.write('Recording results...')
                self.stdout.flush()
            for person in result['kudos']:
                kudos, created = models.Kudos.objects.get_or_create(
                    nick=person['nick'],
                    channel=channel,
                    defaults={
                        'first': person['first'],
                        'recent': person['recent'],
                        'count': person['count'],
                    })
                if not created:
                    # if kudos.recent > person['first']:
                    #     kudos.first = person['first']
                    #     kudos.count = person['count']
                    # else:
                    kudos.count += person['count']
                    kudos.recent = person['recent']
                    kudos.save()
            kudos_total, created = (
                models.KudosTotal.objects.get_or_create(
                    channel=channel,
                    defaults={
                        'kudos_given': result['kudos_given'],
                        'message_count': result['message_count'],
                    }))
            if not created:
                kudos_total.kudos_given += result['kudos_given']
                kudos_total.message_count += result['message_count']
                kudos_total.save()
        if verbosity:
            self.stdout.write('Done!')
