# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import botbot.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivePlugin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, help_text='', auto_created=True)),
                ('configuration', botbot.core.fields.JSONField(blank=True, default={}, help_text=b'User-specified attributes for this plugin {"username": "joe", "api-key": "foo"}')),
                ('channel', models.ForeignKey(help_text='', to='bots.Channel')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Plugin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, help_text='', auto_created=True)),
                ('name', models.CharField(max_length=100, help_text='')),
                ('slug', models.SlugField(help_text='')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='activeplugin',
            name='plugin',
            field=models.ForeignKey(help_text='', to='plugins.Plugin'),
            preserve_default=True,
        ),
    ]
