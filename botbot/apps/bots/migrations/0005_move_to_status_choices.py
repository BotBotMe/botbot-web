# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def move_bools_to_status(apps, schema_editor):
    Channel = apps.get_model("bots", "Channel")

    for channel in Channel.objects.all():
        if channel.is_active:
            channel.status = "ACTIVE"
        else:
            channel.status = "PENDING"

        channel.save()



class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0004_channel_status'),
    ]

    operations = [
        migrations.RunPython(move_bools_to_status),

    ]
