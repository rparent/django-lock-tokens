# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import lock_tokens.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LockToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token_str', models.CharField(default=lock_tokens.models.get_random_token, unique=True, max_length=32, editable=False)),
                ('locked_object_id', models.PositiveIntegerField()),
                ('locked_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('locked_object_content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='locktoken',
            unique_together=set([('locked_object_content_type', 'locked_object_id')]),
        ),
    ]
