# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Kudos',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, help_text='', auto_created=True)),
                ('nick', models.CharField(max_length=255, help_text='')),
                ('count', models.PositiveIntegerField(help_text='')),
                ('first', models.DateTimeField(help_text='')),
                ('recent', models.DateTimeField(help_text='')),
                ('channel', models.ForeignKey(help_text='', to='bots.Channel')),
            ],
            options={
                'verbose_name_plural': 'kudos',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='KudosTotal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, help_text='', auto_created=True)),
                ('kudos_given', models.PositiveIntegerField(help_text='')),
                ('message_count', models.PositiveIntegerField(help_text='')),
                ('channel', models.OneToOneField(help_text='', to='bots.Channel')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='kudos',
            unique_together=set([('nick', 'channel')]),
        ),
    ]
