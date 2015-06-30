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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, help_text='', auto_created=True)),
                ('created', models.DateTimeField(help_text='', auto_now_add=True)),
                ('updated', models.DateTimeField(help_text='', auto_now=True)),
                ('name', models.CharField(max_length=250, help_text=b'IRC expects room name: #django')),
                ('slug', models.SlugField(help_text='')),
                ('private_slug', models.SlugField(unique=True, blank=True, null=True, help_text=b'Slug used for private rooms')),
                ('password', models.CharField(max_length=250, blank=True, null=True, help_text=b'Password (mode +k) if the channel requires one')),
                ('is_public', models.BooleanField(default=False, help_text='')),
                ('is_active', models.BooleanField(default=True, help_text='')),
                ('is_pending', models.BooleanField(default=False, help_text='')),
                ('is_featured', models.BooleanField(default=False, help_text='')),
                ('fingerprint', models.CharField(max_length=36, blank=True, null=True, help_text='')),
                ('public_kudos', models.BooleanField(default=True, help_text='')),
                ('notes', models.TextField(blank=True, help_text='')),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChatBot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, help_text='', auto_created=True)),
                ('is_active', models.BooleanField(default=False, help_text='')),
                ('server', models.CharField(max_length=100, help_text=b'Format: irc.example.net:6697')),
                ('server_password', models.CharField(max_length=100, blank=True, null=True, help_text=b'IRC server password - PASS command. Optional')),
                ('server_identifier', models.CharField(max_length=164, help_text='')),
                ('nick', models.CharField(max_length=64, help_text='')),
                ('password', models.CharField(max_length=100, blank=True, null=True, help_text=b'Password to identify with NickServ. Optional.')),
                ('real_name', models.CharField(max_length=250, help_text=b'Usually a URL with information about this bot.')),
                ('slug', models.CharField(max_length=50, db_index=True, help_text='')),
                ('max_channels', models.IntegerField(default=200, help_text='')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, help_text='', auto_created=True)),
                ('dt', models.DateField(help_text='')),
                ('counts', djorm_pgarray.fields.ArrayField(blank=True, null=True, default=None, help_text='')),
                ('channel', models.ForeignKey(help_text='', to='bots.Channel')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='channel',
            name='chatbot',
            field=models.ForeignKey(help_text='', to='bots.ChatBot'),
            preserve_default=True,
        ),
    ]
