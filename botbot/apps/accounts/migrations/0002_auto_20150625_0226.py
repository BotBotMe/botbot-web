# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0002_auto_20150625_0226'),
        ('auth', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='channel',
            field=models.ForeignKey(help_text='', to='bots.Channel'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(help_text='', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='membership',
            unique_together=set([('user', 'channel')]),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(verbose_name='groups', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', related_name='user_set', related_query_name='user', to='auth.Group'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(verbose_name='user permissions', blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission'),
            preserve_default=True,
        ),
    ]
