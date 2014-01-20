from optparse import make_option

from django.core.management.base import NoArgsCommand

from botbot.apps.plugins import runner

class Command(NoArgsCommand):

    help = ("Starts up all plugins in the botbot.apps.bots.plugins module")
    option_list = NoArgsCommand.option_list + (
        make_option('--with-gevent',
            action='store_true',
            dest='with_gevent',
            default=False,
            help='Use gevent for concurrency'),
        )
    def handle_noargs(self, **options):
        runner.start_plugins(use_gevent=options['with_gevent'])
