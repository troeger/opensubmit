# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0002_auto_20141208_1122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='test_machines',
            field=models.ManyToManyField(help_text=b'The test machines that will take care of submissions for this assignment.', related_name='assignments', to='opensubmit.TestMachine', blank=True),
        ),
        migrations.AlterField(
            model_name='course',
            name='tutors',
            field=models.ManyToManyField(help_text=b'These users can edit / grade submissions for the course.', related_name='courses_tutoring', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='courses',
            field=models.ManyToManyField(related_name='participants', to='opensubmit.Course', blank=True),
        ),
    ]
