#!/usr/bin/env python
import sys

if __name__ == "__main__":
    if (len(sys.argv) > 1 and
            'run_plugins' in sys.argv and '--with-gevent' in sys.argv):
        # import gevent as soon as possible
        from gevent import monkey; monkey.patch_all()
        from psycogreen.gevent import patch_psycopg; patch_psycopg()

    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "botbot.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
