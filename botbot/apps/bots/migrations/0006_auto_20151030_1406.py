# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0005_move_to_status_choices'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='channel',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='channel',
            name='is_pending',
        ),
    ]
