# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0003_remove_channel_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='status',
            field=models.CharField(default=b'PENDING', max_length=20, choices=[(b'PENDING', b'Pending'), (b'ACTIVE', b'Active'), (b'ARCHIVED', b'Archived')]),
        ),
    ]
