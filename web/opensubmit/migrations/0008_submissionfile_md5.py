# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0007_auto_20151007_2322'),
    ]

    operations = [
        migrations.AddField(
            model_name='submissionfile',
            name='md5',
            field=models.CharField(max_length=36, null=True, blank=True),
        ),
    ]
