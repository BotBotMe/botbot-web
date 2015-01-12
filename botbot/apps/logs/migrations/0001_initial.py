# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgfulltext.fields


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(db_index=True)),
                ('nick', models.CharField(max_length=255)),
                ('text', models.TextField()),
                ('action', models.BooleanField(default=False)),
                ('command', models.CharField(max_length=50, null=True, blank=True)),
                ('raw', models.TextField(null=True, blank=True)),
                ('room', models.CharField(max_length=100, null=True, blank=True)),
                ('search_index', djorm_pgfulltext.fields.VectorField(default=b'', serialize=False, null=True, editable=False, db_index=True)),
                ('bot', models.ForeignKey(to='bots.ChatBot', null=True)),
                ('channel', models.ForeignKey(to='bots.Channel', null=True)),
            ],
            options={
                'ordering': ('-timestamp',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='log',
            index_together=set([('channel', 'timestamp')]),
        ),
    ]
