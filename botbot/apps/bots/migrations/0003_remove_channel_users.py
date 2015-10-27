# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0002_auto_20150630_1459'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='channel',
            name='users',
        ),
    ]
