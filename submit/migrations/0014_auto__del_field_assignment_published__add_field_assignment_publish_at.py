# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Assignment.published'
        db.delete_column('submit_assignment', 'published')

        # Adding field 'Assignment.publish_at'
        db.add_column('submit_assignment', 'publish_at',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 1, 17, 0, 0)),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Assignment.published'
        db.add_column('submit_assignment', 'published',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Deleting field 'Assignment.publish_at'
        db.delete_column('submit_assignment', 'publish_at')


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
            'attachment_test_compile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'attachment_test_full': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'attachment_test_timeout': ('django.db.models.fields.IntegerField', [], {'default': '30'}),
            'attachment_test_validity': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['submit.Course']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'download': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'gradingScheme': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['submit.GradingScheme']"}),
            'hard_deadline': ('django.db.models.fields.DateTimeField', [], {}),
            'has_attachment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'publish_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 1, 17, 0, 0)'}),
            'soft_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'validity_script_download': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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
            'means_passed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'submit.gradingscheme': {
            'Meta': {'object_name': 'GradingScheme'},
            'gradings': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'schemes'", 'symmetrical': 'False', 'to': "orm['submit.Grading']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'submit.submission': {
            'Meta': {'object_name': 'Submission'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['submit.Assignment']"}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'authored'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file_upload': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': "orm['submit.SubmissionFile']"}),
            'grading': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['submit.Grading']", 'null': 'True', 'blank': 'True'}),
            'grading_notes': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'max_length': '200', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'R'", 'max_length': '2'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted'", 'to': "orm['auth.User']"})
        },
        'submit.submissionfile': {
            'Meta': {'object_name': 'SubmissionFile'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'perf_data': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'replaced_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['submit.SubmissionFile']", 'null': 'True', 'blank': 'True'}),
            'test_compile': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'test_full': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'test_validity': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'submit.testmachine': {
            'Meta': {'object_name': 'TestMachine'},
            'config': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'host': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_contact': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['submit']