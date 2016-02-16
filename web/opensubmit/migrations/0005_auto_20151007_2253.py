# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0004_auto_20150923_1356'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testmachine',
            name='host',
            field=models.TextField(help_text=b'UUID of the test machine, independent from IP address.', null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='student_id',
            field=models.CharField(max_length=30, null=True, blank=True),
        ),
    ]
