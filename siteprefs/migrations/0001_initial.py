# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Preference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('app', models.CharField(blank=True, max_length=100, verbose_name='Application', db_index=True, null=True)),
                ('name', models.CharField(max_length=150, verbose_name='Name')),
                ('text', models.TextField(blank=True, verbose_name='Value', null=True)),
            ],
            options={
                'verbose_name_plural': 'Preferences',
                'verbose_name': 'Preference',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='preference',
            unique_together=set([('app', 'name')]),
        ),
    ]
