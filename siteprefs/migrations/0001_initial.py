# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Preference'
        db.create_table('siteprefs_preference', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('app', self.gf('django.db.models.fields.CharField')(null=True, db_index=True, blank=True, max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('siteprefs', ['Preference'])

        # Adding unique constraint on 'Preference', fields ['app', 'name']
        db.create_unique('siteprefs_preference', ['app', 'name'])


    def backwards(self, orm):
        # Removing unique constraint on 'Preference', fields ['app', 'name']
        db.delete_unique('siteprefs_preference', ['app', 'name'])

        # Deleting model 'Preference'
        db.delete_table('siteprefs_preference')


    models = {
        'siteprefs.preference': {
            'Meta': {'object_name': 'Preference', 'unique_together': "(('app', 'name'),)"},
            'app': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'blank': 'True', 'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['siteprefs']