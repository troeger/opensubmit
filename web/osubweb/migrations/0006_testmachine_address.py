# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0005_auto_20151007_2253'),
    ]

    operations = [
        migrations.AddField(
            model_name='testmachine',
            name='address',
            field=models.TextField(help_text=b'Internal IP address of the test machine at the time of registration.', null=True),
        ),
    ]
