# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0008_submissionfile_md5'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submissionfile',
            name='md5',
            field=models.CharField(max_length=36, null=True, editable=False, blank=True),
        ),
    ]
