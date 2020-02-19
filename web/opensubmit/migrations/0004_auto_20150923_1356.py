# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0003_auto_20150831_1900'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='student_id',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
