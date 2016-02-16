# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
from opensubmit.models.submissionfile import upload_path


class Migration(migrations.Migration):

    dependencies = [
        ('opensubmit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='attachment_test_compile',
            field=models.BooleanField(default=False, help_text=b"If activated, the student upload is uncompressed and 'make' is executed on one of the test machines.", verbose_name=b'Compile test ?'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='attachment_test_full',
            field=models.FileField(help_text=b'Same as the validation script, but executed AFTER the hard deadline to determine final grading criterias for the submission. Results are not shown to students.', upload_to=b'testscripts', null=True, verbose_name=b'Full test script', blank=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='attachment_test_timeout',
            field=models.IntegerField(default=30, help_text=b'Timeout (in seconds) after which the compilation / validation test / full test is cancelled. The submission is marked as invalid in this case. Intended for student code with deadlocks.', verbose_name=b'Timout for tests'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='attachment_test_validity',
            field=models.FileField(help_text=b'If given, the student upload is uncompressed, compiled and the script is executed for it on a test machine. Student submissions are marked as valid if this script was successful.', upload_to=b'testscripts', null=True, verbose_name=b'Validation script', blank=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='download',
            field=models.URLField(verbose_name=b'Link for assignment description'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='gradingScheme',
            field=models.ForeignKey(related_name=b'assignments', verbose_name=b'grading scheme', to='opensubmit.GradingScheme'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='hard_deadline',
            field=models.DateTimeField(help_text=b'Deadline after which submissions are no longer possible.'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='has_attachment',
            field=models.BooleanField(default=False, help_text=b'Activate this if the students must upload a (document / ZIP /TGZ) file as solution. Otherwise, they can only fill the notes field.', verbose_name=b'Student file upload ?'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='soft_deadline',
            field=models.DateTimeField(help_text=b'Deadline shown to students. After this point in time, submissions are still possible. Leave empty for only using a hard deadline.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='test_machines',
            field=models.ManyToManyField(help_text=b'The test machines that will take care of submissions for this assignment.', related_name=b'assignments', null=True, to=b'opensubmit.TestMachine', blank=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='validity_script_download',
            field=models.BooleanField(default=False, help_text=b'If activated, the students can download the validation script for offline analysis.', verbose_name=b'Download of validation script ?'),
        ),
        migrations.AlterField(
            model_name='course',
            name='active',
            field=models.BooleanField(default=True, help_text=b'Only assignments and submissions of active courses are shown to students and tutors. Use this flag for archiving past courses.'),
        ),
        migrations.AlterField(
            model_name='course',
            name='homepage',
            field=models.URLField(verbose_name=b'Course description link'),
        ),
        migrations.AlterField(
            model_name='course',
            name='max_authors',
            field=models.PositiveSmallIntegerField(default=1, help_text=b'Maximum number of authors (= group size) for assignments in this course.'),
        ),
        migrations.AlterField(
            model_name='course',
            name='owner',
            field=models.ForeignKey(related_name=b'courses', to=settings.AUTH_USER_MODEL, help_text=b'Only this user can change the course details and create new assignments.'),
        ),
        migrations.AlterField(
            model_name='course',
            name='tutors',
            field=models.ManyToManyField(help_text=b'These users can edit / grade submissions for the course.', related_name=b'courses_tutoring', null=True, to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='grading',
            name='means_passed',
            field=models.BooleanField(default=True, help_text=b'Students are informed about their pass or fail in the assignment, based on this flag in their given grade.'),
        ),
        migrations.AlterField(
            model_name='grading',
            name='title',
            field=models.CharField(help_text=b"The title of the grade, such as 'A', 'B', 'Pass', or 'Fail'.", max_length=20),
        ),
        migrations.AlterField(
            model_name='gradingscheme',
            name='gradings',
            field=models.ManyToManyField(help_text=b'The list of gradings that form this grading scheme.', related_name=b'schemes', to=b'opensubmit.Grading'),
        ),
        migrations.AlterField(
            model_name='gradingscheme',
            name='title',
            field=models.CharField(help_text=b"Choose a directly understandable name, such as 'ECTS' or 'Pass / Fail'.", max_length=200),
        ),
        migrations.AlterField(
            model_name='submission',
            name='authors',
            field=models.ManyToManyField(related_name=b'authored', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='submission',
            name='file_upload',
            field=models.ForeignKey(related_name=b'submissions', verbose_name=b'New upload', blank=True, to='opensubmit.SubmissionFile', null=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='grading_file',
            field=models.FileField(help_text=b'Additional information about the grading as file.', null=True, upload_to=upload_path, blank=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='grading_notes',
            field=models.TextField(help_text=b'Specific notes about the grading for this submission.', max_length=1000, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='submissionfile',
            name='attachment',
            field=models.FileField(upload_to=upload_path, verbose_name=b'File upload'),
        ),
        migrations.AlterField(
            model_name='submissionfile',
            name='replaced_by',
            field=models.ForeignKey(blank=True, editable=False, to='opensubmit.SubmissionFile', null=True),
        ),
        migrations.AlterField(
            model_name='testmachine',
            name='config',
            field=models.TextField(help_text=b'Host configuration, as shown to the students, in JSON format.', null=True),
        ),
        migrations.AlterField(
            model_name='testmachine',
            name='host',
            field=models.TextField(help_text=b"IP address of the test machine, as given in the HTTP REMOTE_ADDR header information.<br/>We recommend to run the executor script on the test machine with the 'register' parameter instead.", null=True),
        ),
        migrations.AlterField(
            model_name='testmachine',
            name='last_contact',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]
