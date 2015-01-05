# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import botbot.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivePlugin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('configuration', botbot.core.fields.JSONField(default={}, help_text=b'User-specified attributes for this plugin {"username": "joe", "api-key": "foo"}', blank=True)),
                ('channel', models.ForeignKey(to='bots.Channel')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Plugin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='activeplugin',
            name='plugin',
            field=models.ForeignKey(to='plugins.Plugin'),
            preserve_default=True,
        ),
    ]
