from optparse import make_option

from django.core.management.base import BaseCommand

from botbot.apps.logs import models

def _redact_logs_for_nick(nick):
    redacted_count = models.Log.objects.filter(nick=nick).update(
        text=models.REDACTED_TEXT)
    return redacted_count


class Command(BaseCommand):
    args = "<nick>"
    help = "Redact logs for the given nick"

    def handle(self, *args, **options):
        if len(args) != 1:
            self.stderr.write(
                "One argument (the nick to be redacted) is required.")
        nick = args[0]
        self.stdout.write("Redacting logs for '{0}'".format(nick))
        count = _redact_logs_for_nick(nick)
        self.stdout.write("{0} log lines redacted".format(count))
