"""This file contains tests for siteprefs."""
import sys
import unittest

from django.contrib import admin
from django.db import models

from .utils import Frame, PatchedLocal, PrefProxy, get_field_for_proxy, get_pref_model_class, \
    get_pref_model_admin_class, get_frame_locals, import_module, PREFS_MODULE_NAME
from .toolbox import autodiscover_siteprefs


class FakeSettingsModule(object):

    __name__ = 'siteprefs.settings'


class ToolboxTest(unittest.TestCase):

    def test_autodiscover(self):
        __package__ = 'siteprefs'
        autodiscover_siteprefs()


class UtilsTest(unittest.TestCase):

    def test_frame(self):
        with Frame() as f:
            self.assertEqual(f.f_locals['self'], self)

    def test_patched_local(self):
        pl = PatchedLocal('k', 'v')
        self.assertEqual(pl.key, 'k')
        self.assertEqual(pl.val, 'v')

    def test_pref_poxy(self):
        pp = PrefProxy('proxy_name', 'default')
        self.assertEqual(pp.name, 'proxy_name')
        self.assertEqual(pp.default, 'default')
        self.assertIsNone(pp.category)
        self.assertIsInstance(pp.field, models.TextField)
        self.assertEqual(pp.verbose_name, 'Proxy name')
        self.assertEqual(pp.help_text, '')
        self.assertTrue(pp.static)
        self.assertTrue(pp.readonly)
        self.assertEqual(pp.get_value(), 'default')

        pp = PrefProxy('proxy_name_2', 2, category='cat', field=models.IntegerField(), verbose_name='verbose name', help_text='help text', static=False, readonly=True)
        self.assertEqual(pp.name, 'proxy_name_2')
        self.assertEqual(pp.default, 2)
        self.assertEqual(pp.category, 'cat')
        self.assertIsInstance(pp.field, models.IntegerField)
        self.assertEqual(pp.verbose_name, 'verbose name')
        self.assertEqual(pp.help_text, 'help text')
        self.assertFalse(pp.static)
        self.assertTrue(pp.readonly)
        self.assertEqual(pp.get_value(), 2)

        pp.db_value = 42
        self.assertEqual(pp.get_value(), 42)
        self.assertEqual(pp(), 42)
        self.assertTrue(pp() < 43)
        self.assertTrue(pp() > 41)

        pp = PrefProxy('proxy_name_3', 10, static=False)
        self.assertFalse(pp.readonly)

    def test_get_field_for_proxy(self):
        pp = PrefProxy('proxy_name', 10)
        self.assertIsInstance(get_field_for_proxy(pp), models.IntegerField)

        pp = PrefProxy('proxy_name', True)
        self.assertIsInstance(get_field_for_proxy(pp), models.BooleanField)

        pp = PrefProxy('proxy_name', 13.4)
        self.assertIsInstance(get_field_for_proxy(pp), models.FloatField)

        pp = PrefProxy('proxy_name', 'abc')
        self.assertIsInstance(get_field_for_proxy(pp), models.TextField)

    def test_get_pref_model_class(self):
        p1 = PrefProxy('pp1', 10)
        p2 = PrefProxy('pp2', 20)
        p3 = PrefProxy('pp3', 'admin', field=models.CharField(max_length=10))
        p4 = PrefProxy('pp4', 'another', verbose_name='verbosed', static=False, field=models.CharField(max_length=10))

        my_prefs_func = lambda: 'yes'

        sys.modules['siteprefs.settings'] = FakeSettingsModule()

        cl = get_pref_model_class('siteprefs', {'pp1': p1, 'pp2': p2, 'pp3': p3, 'pp4': p4}, my_prefs_func)
        model = cl()
        self.assertTrue(issubclass(cl, models.Model))
        self.assertIsInstance(model._meta.fields[3], models.CharField)
        self.assertEquals(model._meta.fields[4].verbose_name, 'verbosed')

    def test_get_pref_model_admin_class(self):

        p1 = PrefProxy('pp1', 10)
        p2 = PrefProxy('pp2', 20)

        cl = get_pref_model_admin_class({'pp1': p1, 'pp2': p2})
        self.assertTrue(issubclass(cl, admin.ModelAdmin))

    def test_get_frame_locals(self):
        a = 'a'
        b = 'b'
        l = get_frame_locals(1)
        self.assertIn('a', l)
        self.assertIn('b', l)

    def test_import_module(self):
        try:
            import_module('siteprefs', PREFS_MODULE_NAME)
        except Exception:
            self.fail('test_import_module failed')
