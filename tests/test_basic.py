import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from django.contrib import admin
from django.db import models
from django.db import DatabaseError

from siteprefs.models import Preference
from siteprefs.toolbox import autodiscover_siteprefs, get_app_prefs, get_prefs_models
from siteprefs.utils import Frame, PatchedLocal, PrefProxy, get_field_for_proxy, get_pref_model_class, \
    get_pref_model_admin_class, get_frame_locals, import_module, PREFS_MODULE_NAME


def test_many():
    __package__ = 'tests.testapp'

    autodiscover_siteprefs()

    prefs = list(Preference.objects.all())
    assert len(prefs) == 1

    pref = prefs[0]
    assert pref.name == 'my_option_2'
    assert pref.text == 'Some value'

    prefs = get_app_prefs('testapp')
    assert len(prefs) == 3

    prefs = get_app_prefs('buggy')
    assert len(prefs) == 0

    def update_option_2(new_value):
        # Test update prefs triggering.
        model_cls = get_prefs_models()['testapp']
        model = model_cls()
        model.my_option_2 = new_value
        model.save()

    update_option_2('other_value')

    pref = Preference.objects.first()
    assert pref.text == 'other_value'
    assert '%s' % pref == 'testapp:my_option_2'

    from tests.testapp import testmodule

    assert testmodule.read_option_2() == 'other_value'
    assert testmodule.read_not_an_option() == 'not-an-option'

    update_option_2(44)

    assert testmodule.read_option_2() == '44'


def test_admin():
    from siteprefs.admin import PreferenceAdmin
    return PreferenceAdmin  # not too loose unused import


class TestUtils:

    def test_frame(self):
        with Frame() as f:
            assert f.f_locals['self'] is self

    def test_patched_local(self):
        pl = PatchedLocal('k', 'v')
        assert pl.key == 'k'
        assert pl.val == 'v'

    def test_pref_poxy(self):
        pp = PrefProxy('proxy_name', 'default')
        assert pp.name == 'proxy_name'
        assert pp.default == 'default'
        assert pp.category is None
        assert isinstance(pp.field, models.TextField)
        assert pp.verbose_name == 'Proxy name'
        assert pp.help_text == ''
        assert pp.static
        assert pp.readonly
        assert pp.get_value() == 'default'

        pp = PrefProxy(
            'proxy_name_2', 2,
            category='cat',
            field=models.IntegerField(),
            verbose_name='verbose name',
            help_text='help text',
            static=False,
            readonly=True)

        assert pp.name == 'proxy_name_2'
        assert pp.default == 2
        assert pp.category == 'cat'
        assert isinstance(pp.field, models.IntegerField)
        assert pp.verbose_name == 'verbose name'
        assert pp.help_text == 'help text'
        assert not pp.static
        assert pp.readonly
        assert pp.get_value() == 2

        pp.db_value = 42
        assert pp.get_value() == 42
        assert pp() == 42
        assert pp() < 43
        assert pp() > 41

        pp = PrefProxy('proxy_name_3', 10, static=False)
        assert not pp.readonly

    def test_get_field_for_proxy(self):
        pp = PrefProxy('proxy_name', 10)
        assert isinstance(get_field_for_proxy(pp), models.IntegerField)

        pp = PrefProxy('proxy_name', True)
        assert isinstance(get_field_for_proxy(pp), models.BooleanField)

        pp = PrefProxy('proxy_name', 13.4)
        assert isinstance(get_field_for_proxy(pp), models.FloatField)

        pp = PrefProxy('proxy_name', 'abc')
        assert isinstance(get_field_for_proxy(pp), models.TextField)

    def test_get_pref_model_class(self):
        p1 = PrefProxy('pp1', 10)
        p2 = PrefProxy('pp2', 20)
        p3 = PrefProxy('pp3', 'admin', field=models.CharField(max_length=10))
        p4 = PrefProxy('pp4', 'another', verbose_name='verbosed', static=False, field=models.CharField(max_length=10))

        def my_prefs_func():
            return 'yes'

        cl = get_pref_model_class('testapp', {'pp1': p1, 'pp2': p2, 'pp3': p3, 'pp4': p4}, my_prefs_func)

        model = cl()

        assert issubclass(cl, models.Model)
        assert isinstance(model._meta.fields[3], models.CharField)
        assert model._meta.fields[4].verbose_name == 'verbosed'
        assert repr(cl) == "<dynamic preferences model for 'testapp'>"

    def test_get_pref_model_admin_class(self):

        p1 = PrefProxy('pp1', 10)
        p2 = PrefProxy('pp2', 20)

        cl = get_pref_model_admin_class({'pp1': p1, 'pp2': p2})
        assert issubclass(cl, admin.ModelAdmin)

    def test_get_frame_locals(self):
        a = 'a'
        b = 'b'
        local = get_frame_locals(1)
        assert 'a' in local
        assert 'b' in local

    @pytest.mark.xfail(strict=True)
    def test_import_module(self):
        import_module('dummy', PREFS_MODULE_NAME[0])


def test_autodiscover_db_unavailable(monkeypatch):
    def raise_db_error(prefs):
        raise DatabaseError("simulated")

    monkeypatch.setattr(Preference, "read_prefs", staticmethod(raise_db_error))
    monkeypatch.setattr("siteprefs.toolbox.__MODELS_REGISTRY", {})

    __package__ = "tests.testapp"

    autodiscover_siteprefs()

    assert "testapp" in get_prefs_models()


def test_register_project_prefs():
    """Project-wide preferences can be declared in a project settings module."""

    proj = Path(tempfile.mkdtemp())
    (proj / "myproj").mkdir()
    (proj / "myproj" / "__init__.py").write_text("")
    (proj / "myproj" / "urls.py").write_text("urlpatterns = []\n")
    (proj / "myproj" / "settings.py").write_text(
        "DEBUG = True\n"
        'DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}\n'
        'INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.auth", "django.contrib.admin",'
        ' "django.contrib.messages", "django.contrib.sessions", "siteprefs"]\n'
        'SECRET_KEY = "x"\n'
        "\n"
        'PROJECT_WIDE_PREF = "initial"\n'
        "\n"
        "from siteprefs.toolbox import register_project_prefs\n"
        "\n"
        "register_project_prefs(PROJECT_WIDE_PREF=PROJECT_WIDE_PREF)\n"
    )

    code = (
        f"import sys; sys.path.insert(0, {str(proj)!r})\n"
        'import os; os.environ["DJANGO_SETTINGS_MODULE"] = "myproj.settings"\n'
        "import django; django.setup()\n"
        "from siteprefs.toolbox import get_prefs\n"
        "prefs = get_prefs()\n"
        'assert "myproj" in prefs, prefs.keys()\n'
        'assert prefs["myproj"]["project_wide_pref"].value == "initial"\n'
        'print("project-prefs-ok")\n'
    )

    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    assert "project-prefs-ok" in result.stdout
