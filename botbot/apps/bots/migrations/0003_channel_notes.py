# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0002_auto_20150112_1908'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='notes',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
    ]
