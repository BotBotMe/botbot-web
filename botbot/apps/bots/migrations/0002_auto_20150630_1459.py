# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150630_1459'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plugins', '0002_auto_20140912_1656'),
        ('bots', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonalChannels',
            fields=[
            ],
            options={
                'verbose_name': 'Pending Personal Channel',
                'proxy': True,
            },
            bases=('bots.channel',),
        ),
        migrations.CreateModel(
            name='PublicChannels',
            fields=[
            ],
            options={
                'verbose_name': 'Pending Public Channel',
                'proxy': True,
            },
            bases=('bots.channel',),
        ),
        migrations.AddField(
            model_name='channel',
            name='plugins',
            field=models.ManyToManyField(to='plugins.Plugin', through='plugins.ActivePlugin'),
        ),
        migrations.AddField(
            model_name='channel',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='accounts.Membership'),
        ),
        migrations.AlterUniqueTogether(
            name='channel',
            unique_together=set([('slug', 'chatbot'), ('name', 'chatbot')]),
        ),
    ]
