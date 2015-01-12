# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db.models.loading import get_model


def initial_plugins(*args):
    Plugin = get_model('plugins', 'Plugin')

    intial = [
        {
            "name": "Logger",
            "slug": "logger"
        },
        {
            "name": "Ping",
            "slug": "ping"
        },
        {
            "name": "Wolfram|Alpha",
            "slug": "wolfram"
        },
        {
            "name": "Help",
            "slug": "help"
        },
        {
            "name": "Images",
            "slug": "images"
        },
        {
            "name": "Memory",
            "slug": "brain"
        },
        {
            "name": "Last Seen",
            "slug": "last_seen"
        },
        {
            "name": "GitHub",
            "slug": "github"
        },
        {
            "name": "!m",
            "slug": "bangmotivate"
        }
    ]

    for i in intial:
        Plugin(**i).save()


class Migration(migrations.Migration):
    dependencies = [
        ('plugins', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(initial_plugins)
    ]
