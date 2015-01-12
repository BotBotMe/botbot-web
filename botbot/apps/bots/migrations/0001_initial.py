# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text=b'IRC expects room name: #django', max_length=250)),
                ('slug', models.SlugField()),
                ('private_slug', models.SlugField(null=True, blank=True, help_text=b'Slug used for private rooms', unique=True)),
                ('password', models.CharField(help_text=b'Password (mode +k) if the channel requires one', max_length=250, null=True, blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_pending', models.BooleanField(default=False)),
                ('is_featured', models.BooleanField(default=False)),
                ('fingerprint', models.CharField(max_length=36, null=True, blank=True)),
                ('public_kudos', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChatBot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=False)),
                ('server', models.CharField(help_text=b'Format: irc.example.net:6697', max_length=100)),
                ('server_password', models.CharField(help_text=b'IRC server password - PASS command. Optional', max_length=100, null=True, blank=True)),
                ('server_identifier', models.CharField(max_length=164)),
                ('nick', models.CharField(max_length=64)),
                ('password', models.CharField(help_text=b'Password to identify with NickServ. Optional.', max_length=100, null=True, blank=True)),
                ('real_name', models.CharField(help_text=b'Usually a URL with information about this bot.', max_length=250)),
                ('slug', models.CharField(max_length=50, db_index=True)),
                ('max_channels', models.IntegerField(default=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dt', models.DateField()),
                ('counts', djorm_pgarray.fields.ArrayField(default=None, null=True, blank=True)),
                ('channel', models.ForeignKey(to='bots.Channel')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='channel',
            name='chatbot',
            field=models.ForeignKey(to='bots.ChatBot'),
            preserve_default=True,
        ),
    ]
