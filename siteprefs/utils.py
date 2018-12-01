import inspect
import os
from sys import version_info
from collections import OrderedDict
from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

try:
    from django.utils.module_loading import import_module as import_module_

except ImportError:
    # Django <=1.9.0
    from django.utils.importlib import import_module as import_module_

from django.contrib import admin
from etc.toolbox import import_app_module, import_project_modules

from .signals import prefs_save
from .settings import PREFS_MODULE_NAME


PY2 = (version_info.major == 2)


class Frame(object):
    """Represents a frame object at a definite level of hierarchy.

    To be used as context manager:

        with Frame as f:
            ...

    """

    def __init__(self, stepback=0):
        self.depth = stepback

    def __enter__(self):
        frame = inspect.currentframe().f_back

        for __ in range(self.depth):
            frame = frame.f_back

        self.frame = frame

        return self.frame

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.frame


class PatchedLocal(object):
    """Object of this class temporarily replace all module variables
    considered preferences."""

    def __init__(self, key, val):
        self.key = key
        self.val = val


class Mimic(object):
    """Mimics other types by implementation of various special methods.

    This one is deprecated if favor of setting module proxying (proxy_settings_module()).

    """

    value = None

    def __call__(self, *args, **kwargs):
        return self.value

    def __str__(self):
        return self.value.__str__()

    def __bool__(self):
        return bool(self.value)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __len__(self):
        return self.value.__len__()

    def __contains__(self, item):
        return self.value.__contains__(item)

    def __sub__(self, other):
        return self.value.__sub__(other)

    def __rsub__(self, other):
        return self.value.__rsub__(other)

    def __add__(self, other):
        return self.value.__add__(other)

    def __radd__(self, other):
        return self.value.__radd__(other)

    def __mul__(self, other):
        return self.value.__mul__(other)

    def __rmul__(self, other):
        return self.value.__rmul__(other)

    def __lt__(self, other):
        return self.value.__lt__(other)

    def __le__(self, other):
        return self.value.__le__(other)

    def __gt__(self, other):
        return self.value.__gt__(other)

    def __ge__(self, other):
        return self.value.__ge__(other)

    def __eq__(self, other):
        return self.value.__eq__(other)

    def __ne__(self, other):
        return self.value.__ne__(other)

    if PY2:

        def __cmp__(self, other):
            return self.value.__cmp__(other)

        def __nonzero__(self):
            return self.value.__nonzero__()

        def __lt__(self, other):
            return self.value < other

        def __le__(self, other):
            return self.value <= other

        def __gt__(self, other):
            return self.value > other

        def __ge__(self, other):
            return self.value >= other

        def __eq__(self, other):
            return self.value == other

        def __ne__(self, other):
            return self.value != other


class PrefProxy(Mimic):
    """Objects of this class replace app preferences."""

    def __init__(
            self, name, default, category=None, field=None, verbose_name=None, help_text='', static=True,
            readonly=False):
        """

        :param str|unicode name: Preference name.

        :param default: Default (initial) value.

        :param str|unicode category: Category name the preference belongs to.

        :param Field field: Django model field to represent this preference.

        :param str|unicode verbose_name: Field verbose name.

        :param str|unicode help_text: Field help text.

        :param bool static: Leave this preference static (do not store in DB).

        :param bool readonly: Make this field read only.

        """
        self.name = name
        self.category = category
        self.default = default
        self.static = static
        self.help_text = help_text

        if static:
            readonly = True

        self.readonly = readonly

        if verbose_name is None:
            verbose_name = name.replace('_', ' ').capitalize()

        self.verbose_name = verbose_name

        if field is None:
            self.field = get_field_for_proxy(self)

        else:
            self.field = field
            update_field_from_proxy(self.field, self)

    @property
    def value(self):

        if self.static:
            val = self.default

        else:
            try:
                val = getattr(self, 'db_value')

            except AttributeError:
                val = self.default

        return self.field.to_python(val)

    def get_value(self):
        # Deprecated: use .value directly.
        return self.value

    def __repr__(self):
        return '%s = %s' % (self.name, self.value)


def get_field_for_proxy(pref_proxy):
    """Returns a field object instance for a given PrefProxy object.

    :param PrefProxy pref_proxy:

    :rtype: models.Field

    """
    field = {
        bool: models.BooleanField,
        int:  models.IntegerField,
        float: models.FloatField,
        datetime: models.DateTimeField,

    }.get(type(pref_proxy.default), models.TextField)()

    update_field_from_proxy(field, pref_proxy)

    return field


def update_field_from_proxy(field_obj, pref_proxy):
    """Updates field object with data from a PrefProxy object.

    :param models.Field field_obj:

    :param PrefProxy pref_proxy:

    """
    attr_names = ('verbose_name', 'help_text', 'default')

    for attr_name in attr_names:
        setattr(field_obj, attr_name, getattr(pref_proxy, attr_name))


def get_pref_model_class(app, prefs, get_prefs_func):
    """Returns preferences model class dynamically crated for a given app or None on conflict."""

    module = '%s.%s' % (app, PREFS_MODULE_NAME)

    model_dict = {
            '_prefs_app': app,
            '_get_prefs': staticmethod(get_prefs_func),
            '__module__': module,
            'Meta': type('Meta', (models.options.Options,), {
                'verbose_name': _('Preference'),
                'verbose_name_plural': _('Preferences'),
                'app_label': app,
                'managed': False,
            })
    }

    for field_name, val_proxy in prefs.items():
        model_dict[field_name] = val_proxy.field

    model = type('Preferences', (models.Model,), model_dict)

    def fake_save_base(self, *args, **kwargs):

        updated_prefs = {
            f.name: getattr(self, f.name) for f in self._meta.fields if not isinstance(f, models.fields.AutoField)
        }

        app_prefs = self._get_prefs(self._prefs_app)

        for pref in app_prefs.keys():
            if pref in updated_prefs:
                app_prefs[pref].db_value = updated_prefs[pref]

        self.pk = self._prefs_app  # Make Django 1.7 happy.
        prefs_save.send(sender=self, app=self._prefs_app, updated_prefs=updated_prefs)

        return True

    model.save_base = fake_save_base

    return model


def get_pref_model_admin_class(prefs):

    by_category = OrderedDict()
    readonly_fields = []

    for field_name, val_proxy in prefs.items():

        if val_proxy.readonly:
            readonly_fields.append(field_name)

        if val_proxy.category not in by_category:
            by_category[val_proxy.category] = []

        by_category[val_proxy.category].append(field_name)

    cl_model_admin_dict = {
        'has_add_permission': lambda *args: False,
        'has_delete_permission': lambda *args: False
    }

    if readonly_fields:
        cl_model_admin_dict['readonly_fields'] = readonly_fields

    fieldsets = []

    for category, cat_prefs in by_category.items():
        fieldsets.append((category, {'fields': cat_prefs}))

    if fieldsets:
        cl_model_admin_dict['fieldsets'] = fieldsets

    model = type('PreferencesAdmin', (admin.ModelAdmin,), cl_model_admin_dict)

    model.changelist_view = lambda self, request, **kwargs: self.change_view(request, '', **kwargs)

    model.get_object = lambda self, *args: (
        self.model(
            **{
                field_name: val_proxy.get_value() for field_name, val_proxy in
                self.model._get_prefs(self.model._prefs_app).items()
            }
        )
    )

    return model


def get_frame_locals(stepback=0):
    """Returns locals dictionary from a given frame.

    :param int stepback:

    :rtype: dict

    """
    with Frame(stepback=stepback) as frame:
        locals_dict = frame.f_locals

    return locals_dict


def traverse_local_prefs(stepback=0):
    """Generator to walk through variables considered as preferences
    in locals dict of a given frame.

    :param int stepback:

    :rtype: tuple

    """
    locals_dict = get_frame_locals(stepback+1)
    for k in locals_dict:
        if not k.startswith('_') and k.upper() == k:
            yield k, locals_dict


def import_module(package, module_name):
    """Imports a module from a given package.

    :param str|unicode package:
    :param str|unicode module_name:

    """
    import_app_module(package, module_name)


def import_prefs():
    """Imports preferences modules from packages (apps) and project root."""
    
    # settings.py locals if autodiscover_siteprefs() is in urls.py
    settings_locals = get_frame_locals(3)

    if 'self' not in settings_locals:  # If not SiteprefsConfig.ready()
        # Try to import project-wide prefs.

        project_package = settings_locals['__package__']  # Expected project layout introduced in Django 1.4
        if not project_package:
            # Fallback to old layout.
            project_package = os.path.split(os.path.dirname(settings_locals['__file__']))[-1]

        import_module(project_package, PREFS_MODULE_NAME)

    import_project_modules(PREFS_MODULE_NAME)
