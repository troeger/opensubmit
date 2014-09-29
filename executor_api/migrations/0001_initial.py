# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import executor_api.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('submit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignmentTest',
            fields=[
                ('assignment', models.OneToOneField(related_name=b'test', primary_key=True, serialize=False, to='submit.Assignment')),
                ('puppet_config', models.TextField(blank=True)),
                ('test_script', models.FileField(null=True, upload_to=executor_api.models.upload_path, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestJob',
            fields=[
                ('submission', models.OneToOneField(related_name=b'job', primary_key=True, serialize=False, to='submit.Submission')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestJobError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('occured', models.DateTimeField(auto_now=True)),
                ('message', models.TextField(editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestMachine',
            fields=[
                ('machine_user', models.OneToOneField(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('name', models.TextField(null=True)),
                ('last_contact', models.DateTimeField(null=True, editable=False, blank=True)),
            ],
            options={
                'permissions': (('api_usage', 'The user is allowed to use the API.'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('job', models.OneToOneField(related_name=b'_result', primary_key=True, serialize=False, to='executor_api.TestJob')),
                ('success', models.BooleanField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='testjoberror',
            name='job',
            field=models.ForeignKey(related_name=b'errors', editable=False, to='executor_api.TestJob'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='testjoberror',
            name='machine',
            field=models.ForeignKey(related_name=b'errors', editable=False, to='executor_api.TestMachine'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='testjob',
            name='machine',
            field=models.ForeignKey(related_name=b'jobs', blank=True, to='executor_api.TestMachine', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignmenttest',
            name='machines',
            field=models.ManyToManyField(related_name=b'assignments', to='executor_api.TestMachine'),
            preserve_default=True,
        ),
    ]
