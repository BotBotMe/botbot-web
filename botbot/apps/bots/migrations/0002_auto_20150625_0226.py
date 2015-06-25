# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
        ('bots', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='plugins',
            field=models.ManyToManyField(help_text='', to='plugins.Plugin', through='plugins.ActivePlugin'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='channel',
            name='users',
            field=models.ManyToManyField(help_text='', to=settings.AUTH_USER_MODEL, through='accounts.Membership'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='channel',
            unique_together=set([('slug', 'chatbot'), ('name', 'chatbot')]),
        ),
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
    ]
