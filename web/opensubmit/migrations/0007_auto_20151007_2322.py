# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0006_testmachine_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testmachine',
            name='address',
            field=models.CharField(help_text=b'Internal IP address of the test machine, at the time of registration.', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='testmachine',
            name='host',
            field=models.CharField(help_text=b'UUID of the test machine, independent from IP address.', max_length=50, null=True),
        ),
    ]
