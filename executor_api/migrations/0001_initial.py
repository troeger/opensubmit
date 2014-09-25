# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TestMachine'
        db.create_table(u'executor_api_testmachine', (
            ('machine_user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')(null=True)),
            ('last_contact', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'executor_api', ['TestMachine'])

        # Adding model 'TestJob'
        db.create_table(u'executor_api_testjob', (
            ('submission', self.gf('django.db.models.fields.related.OneToOneField')(related_name='job', unique=True, primary_key=True, to=orm['submit.Submission'])),
            ('machine', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='jobs', null=True, to=orm['executor_api.TestMachine'])),
        ))
        db.send_create_signal(u'executor_api', ['TestJob'])

        # Adding model 'TestResult'
        db.create_table(u'executor_api_testresult', (
            ('job', self.gf('django.db.models.fields.related.OneToOneField')(related_name='_result', unique=True, primary_key=True, to=orm['executor_api.TestJob'])),
            ('success', self.gf('django.db.models.fields.BooleanField')()),
        ))
        db.send_create_signal(u'executor_api', ['TestResult'])

        # Adding model 'TestJobError'
        db.create_table(u'executor_api_testjoberror', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(related_name='errors', to=orm['executor_api.TestJob'])),
            ('machine', self.gf('django.db.models.fields.related.ForeignKey')(related_name='errors', to=orm['executor_api.TestMachine'])),
            ('occured', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('message', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'executor_api', ['TestJobError'])

        # Adding model 'AssignmentTest'
        db.create_table(u'executor_api_assignmenttest', (
            ('assignment', self.gf('django.db.models.fields.related.OneToOneField')(related_name='test', unique=True, primary_key=True, to=orm['submit.Assignment'])),
            ('puppet_config', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('test_script', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'executor_api', ['AssignmentTest'])

        # Adding M2M table for field machines on 'AssignmentTest'
        m2m_table_name = db.shorten_name(u'executor_api_assignmenttest_machines')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('assignmenttest', models.ForeignKey(orm[u'executor_api.assignmenttest'], null=False)),
            ('testmachine', models.ForeignKey(orm[u'executor_api.testmachine'], null=False))
        ))
        db.create_unique(m2m_table_name, ['assignmenttest_id', 'testmachine_id'])


    def backwards(self, orm):
        # Deleting model 'TestMachine'
        db.delete_table(u'executor_api_testmachine')

        # Deleting model 'TestJob'
        db.delete_table(u'executor_api_testjob')

        # Deleting model 'TestResult'
        db.delete_table(u'executor_api_testresult')

        # Deleting model 'TestJobError'
        db.delete_table(u'executor_api_testjoberror')

        # Deleting model 'AssignmentTest'
        db.delete_table(u'executor_api_assignmenttest')

        # Removing M2M table for field machines on 'AssignmentTest'
        db.delete_table(db.shorten_name(u'executor_api_assignmenttest_machines'))


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'executor_api.assignmenttest': {
            'Meta': {'object_name': 'AssignmentTest'},
            'assignment': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'test'", 'unique': 'True', 'primary_key': 'True', 'to': u"orm['submit.Assignment']"}),
            'machines': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'assignments'", 'symmetrical': 'False', 'to': u"orm['executor_api.TestMachine']"}),
            'puppet_config': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'test_script': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'executor_api.testjob': {
            'Meta': {'object_name': 'TestJob'},
            'machine': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'jobs'", 'null': 'True', 'to': u"orm['executor_api.TestMachine']"}),
            'submission': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'job'", 'unique': 'True', 'primary_key': 'True', 'to': u"orm['submit.Submission']"})
        },
        u'executor_api.testjoberror': {
            'Meta': {'object_name': 'TestJobError'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'errors'", 'to': u"orm['executor_api.TestJob']"}),
            'machine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'errors'", 'to': u"orm['executor_api.TestMachine']"}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'occured': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'executor_api.testmachine': {
            'Meta': {'object_name': 'TestMachine'},
            'last_contact': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'machine_user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        u'executor_api.testresult': {
            'Meta': {'object_name': 'TestResult'},
            'job': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'_result'", 'unique': 'True', 'primary_key': 'True', 'to': u"orm['executor_api.TestJob']"}),
            'success': ('django.db.models.fields.BooleanField', [], {})
        },
        u'submit.assignment': {
            'Meta': {'object_name': 'Assignment'},
            'attachment_test_compile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'attachment_test_full': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'attachment_test_timeout': ('django.db.models.fields.IntegerField', [], {'default': '30'}),
            'attachment_test_validity': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': u"orm['submit.Course']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'download': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'gradingScheme': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': u"orm['submit.GradingScheme']"}),
            'hard_deadline': ('django.db.models.fields.DateTimeField', [], {}),
            'has_attachment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'publish_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 9, 25, 0, 0)'}),
            'soft_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'test_machines': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['submit.TestMachine']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'validity_script_download': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'submit.course': {
            'Meta': {'object_name': 'Course'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_authors': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'courses'", 'to': u"orm['auth.User']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tutors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'courses_tutoring'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'submit.grading': {
            'Meta': {'object_name': 'Grading'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'means_passed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'submit.gradingscheme': {
            'Meta': {'object_name': 'GradingScheme'},
            'gradings': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'schemes'", 'symmetrical': 'False', 'to': u"orm['submit.Grading']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'submit.submission': {
            'Meta': {'object_name': 'Submission'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': u"orm['submit.Assignment']"}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'authored'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file_upload': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': u"orm['submit.SubmissionFile']"}),
            'grading': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['submit.Grading']", 'null': 'True', 'blank': 'True'}),
            'grading_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'grading_notes': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'max_length': '200', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'R'", 'max_length': '2'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted'", 'to': u"orm['auth.User']"})
        },
        u'submit.submissionfile': {
            'Meta': {'object_name': 'SubmissionFile'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'replaced_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['submit.SubmissionFile']", 'null': 'True', 'blank': 'True'})
        },
        u'submit.testmachine': {
            'Meta': {'object_name': 'TestMachine'},
            'config': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'host': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_contact': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['executor_api']