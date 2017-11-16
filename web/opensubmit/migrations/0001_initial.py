# -*- coding: utf-8 -*-


from django.db import models, migrations
from opensubmit.models.submissionfile import upload_path
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('download', models.URLField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('publish_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('soft_deadline', models.DateTimeField(null=True, blank=True)),
                ('hard_deadline', models.DateTimeField()),
                ('has_attachment', models.BooleanField(default=False)),
                ('attachment_test_timeout', models.IntegerField(default=30)),
                ('attachment_test_compile', models.BooleanField(default=False)),
                ('attachment_test_validity', models.FileField(null=True, upload_to=b'testscripts', blank=True)),
                ('validity_script_download', models.BooleanField(default=False)),
                ('attachment_test_full', models.FileField(null=True, upload_to=b'testscripts', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('homepage', models.URLField()),
                ('active', models.BooleanField(default=True)),
                ('max_authors', models.PositiveSmallIntegerField(default=1)),
                ('owner', models.ForeignKey(related_name=b'courses', to=settings.AUTH_USER_MODEL)),
                ('tutors', models.ManyToManyField(related_name=b'courses_tutoring', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Grading',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=20)),
                ('means_passed', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GradingScheme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('gradings', models.ManyToManyField(related_name=b'schemes', to='opensubmit.Grading')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notes', models.TextField(max_length=200, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, null=True)),
                ('grading_notes', models.TextField(max_length=1000, null=True, blank=True)),
                ('grading_file', models.FileField(null=True, upload_to=upload_path, blank=True)),
                ('state', models.CharField(default=b'R', max_length=2, choices=[(b'R', b'Received'), (b'W', b'Withdrawn'), (b'S', b'Submitted'), (b'PC', b'Compilation test pending'), (b'FC', b'Compilation test failed'), (b'PV', b'Validity test pending'), (b'FV', b'Validity test failed'), (b'PF', b'Full test pending'), (b'FF', b'All but full test passed, grading pending'), (b'ST', b'All tests passed, grading pending'), (b'GP', b'Grading not finished'), (b'G', b'Grading finished'), (b'C', b'Closed, student notified'), (b'CT', b'Closed, full test pending')])),
                ('assignment', models.ForeignKey(related_name=b'submissions', to='opensubmit.Assignment')),
                ('authors', models.ManyToManyField(help_text=b'', related_name=b'authored', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubmissionFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment', models.FileField(upload_to=upload_path)),
                ('fetched', models.DateTimeField(null=True, editable=False)),
                ('replaced_by', models.ForeignKey(blank=True, to='opensubmit.SubmissionFile', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubmissionTestResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('result', models.TextField(null=True, blank=True)),
                ('kind', models.CharField(max_length=2, choices=[(b'c', b'Compilation test'), (b'v', b'Validation test'), (b'f', b'Full test')])),
                ('perf_data', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestMachine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('host', models.TextField(null=True)),
                ('last_contact', models.DateTimeField(editable=False)),
                ('config', models.TextField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('courses', models.ManyToManyField(related_name=b'participants', null=True, to='opensubmit.Course', blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='submissiontestresult',
            name='machine',
            field=models.ForeignKey(related_name=b'test_results', to='opensubmit.TestMachine'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='submissiontestresult',
            name='submission_file',
            field=models.ForeignKey(related_name=b'test_results', to='opensubmit.SubmissionFile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='submission',
            name='file_upload',
            field=models.ForeignKey(related_name=b'submissions', blank=True, to='opensubmit.SubmissionFile', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='submission',
            name='grading',
            field=models.ForeignKey(blank=True, to='opensubmit.Grading', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='submission',
            name='submitter',
            field=models.ForeignKey(related_name=b'submitted', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignment',
            name='course',
            field=models.ForeignKey(related_name=b'assignments', to='opensubmit.Course'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignment',
            name='gradingScheme',
            field=models.ForeignKey(related_name=b'assignments', to='opensubmit.GradingScheme'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignment',
            name='test_machines',
            field=models.ManyToManyField(to='opensubmit.TestMachine', null=True, blank=True),
            preserve_default=True,
        ),
    ]
