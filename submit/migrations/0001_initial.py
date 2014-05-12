# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Grading'
        db.create_table('submit_grading', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('submit', ['Grading'])

        # Adding model 'GradingScheme'
        db.create_table('submit_gradingscheme', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('submit', ['GradingScheme'])

        # Adding M2M table for field gradings on 'GradingScheme'
        db.create_table('submit_gradingscheme_gradings', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('gradingscheme', models.ForeignKey(orm['submit.gradingscheme'], null=False)),
            ('grading', models.ForeignKey(orm['submit.grading'], null=False))
        ))
        db.create_unique('submit_gradingscheme_gradings', ['gradingscheme_id', 'grading_id'])

        # Adding model 'Course'
        db.create_table('submit_course', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='courses', to=orm['auth.User'])),
            ('homepage', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('max_authors', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal('submit', ['Course'])

        # Adding model 'Assignment'
        db.create_table('submit_assignment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignments', to=orm['submit.Course'])),
            ('download', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('gradingScheme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['submit.GradingScheme'])),
            ('published', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('soft_deadline', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('hard_deadline', self.gf('django.db.models.fields.DateTimeField')()),
            ('has_attachment', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('test_attachment', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('submit', ['Assignment'])

        # Adding model 'Submission'
        db.create_table('submit_submission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assignment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['submit.Assignment'])),
            ('submitter', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submitted', to=orm['auth.User'])),
            ('notes', self.gf('django.db.models.fields.TextField')(max_length=200, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('grading', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['submit.Grading'], null=True, blank=True)),
            ('grading_notes', self.gf('django.db.models.fields.TextField')(max_length=1000, null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='R', max_length=2)),
        ))
        db.send_create_signal('submit', ['Submission'])

        # Adding M2M table for field authors on 'Submission'
        db.create_table('submit_submission_authors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('submission', models.ForeignKey(orm['submit.submission'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('submit_submission_authors', ['submission_id', 'user_id'])

        # Adding model 'SubmissionFile'
        db.create_table('submit_submissionfile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='files', to=orm['submit.Submission'])),
            ('attachment', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('fetched', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('output', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('error_code', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('replaced_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['submit.SubmissionFile'], null=True, blank=True)),
        ))
        db.send_create_signal('submit', ['SubmissionFile'])


    def backwards(self, orm):
        # Deleting model 'Grading'
        db.delete_table('submit_grading')

        # Deleting model 'GradingScheme'
        db.delete_table('submit_gradingscheme')

        # Removing M2M table for field gradings on 'GradingScheme'
        db.delete_table('submit_gradingscheme_gradings')

        # Deleting model 'Course'
        db.delete_table('submit_course')

        # Deleting model 'Assignment'
        db.delete_table('submit_assignment')

        # Deleting model 'Submission'
        db.delete_table('submit_submission')

        # Removing M2M table for field authors on 'Submission'
        db.delete_table('submit_submission_authors')

        # Deleting model 'SubmissionFile'
        db.delete_table('submit_submissionfile')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'submit.assignment': {
            'Meta': {'object_name': 'Assignment'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['submit.Course']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'download': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'gradingScheme': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['submit.GradingScheme']"}),
            'hard_deadline': ('django.db.models.fields.DateTimeField', [], {}),
            'has_attachment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'soft_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'test_attachment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'submit.course': {
            'Meta': {'object_name': 'Course'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_authors': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'courses'", 'to': "orm['auth.User']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'submit.grading': {
            'Meta': {'object_name': 'Grading'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'submit.gradingscheme': {
            'Meta': {'object_name': 'GradingScheme'},
            'gradings': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['submit.Grading']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'submit.submission': {
            'Meta': {'object_name': 'Submission'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['submit.Assignment']"}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'authored'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'grading': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['submit.Grading']", 'null': 'True', 'blank': 'True'}),
            'grading_notes': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'max_length': '200', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'R'", 'max_length': '2'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted'", 'to': "orm['auth.User']"})
        },
        'submit.submissionfile': {
            'Meta': {'object_name': 'SubmissionFile'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'error_code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'output': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'replaced_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['submit.SubmissionFile']", 'null': 'True', 'blank': 'True'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['submit.Submission']"})
        }
    }

    complete_apps = ['submit']