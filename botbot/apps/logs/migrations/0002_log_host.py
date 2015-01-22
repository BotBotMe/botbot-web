# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='log',
            name='host',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
