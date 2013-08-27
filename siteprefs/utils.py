import inspect
from collections import OrderedDict

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.importlib import import_module as import_module_
from django.utils.module_loading import module_has_submodule
from django.contrib import admin

from .signals import prefs_save
from .settings import PREFS_MODULE_NAME


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
        for step in range(self.depth):
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


class PrefProxy(object):
    """Objects of this class replace app preferences."""

    def __init__(self, name, default, category=None, field=None, verbose_name=None, help_text='', static=True, readonly=False):
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

    def get_value(self):
        if self.static:
            val = self.default
        else:
            try:
                val = getattr(self, 'db_value')
            except AttributeError:
                val = self.default
        return self.field.to_python(val)

    def __cmp__(self, other):
        if self.get_value() < other:
            return -1
        elif self.get_value() > other:
            return 1
        return 0

    def __call__(self, *args, **kwargs):
        return self.get_value()

    def __str__(self):
        return '%s = %s' % (self.name, self.get_value())


def get_field_for_proxy(val_proxy):
    """Returns a field object instance for a given PrefProxy object."""
    field_kwargs = {
        'verbose_name': val_proxy.verbose_name,
        'help_text': val_proxy.help_text,
        'default': val_proxy.default,
    }

    field = {
        bool: models.BooleanField,
        int:  models.IntegerField,
        float: models.FloatField,
    }.get(type(val_proxy.default), models.TextField)(**field_kwargs)
    return field


def get_pref_model_class(app, prefs, get_prefs_func):
    """Returns preferences model class dynamically crated for a given app."""

    model_dict = {
            '_prefs_app': app,
            '_get_prefs': staticmethod(get_prefs_func),
            '__module__': '%s.%s' % (app, PREFS_MODULE_NAME),
            'Meta': type('Meta', (models.options.Options,), {
                'verbose_name': _('Preference'),
                'verbose_name_plural': _('Preferences')
            })
    }

    for field_name, val_proxy in prefs.items():
        model_dict[field_name] = get_field_for_proxy(val_proxy)

    model = type('Preferences', (models.Model,), model_dict)

    def fake_save_base(self, *args, **kwargs):
        updated_prefs = {f.name: getattr(self, f.name) for f in self._meta.fields if not isinstance(f, models.fields.AutoField)}
        app_prefs = self._get_prefs(self._prefs_app)
        for pref in app_prefs.keys():
            if pref in updated_prefs:
                app_prefs[pref].db_value = updated_prefs[pref]
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
    model.get_object = lambda self, *args: self.model(**{field_name: val_proxy.get_value() for field_name, val_proxy in self.model._get_prefs(self.model._prefs_app).items()})

    return model


def get_frame_locals(stepback=0):
    """Returns locals dictionary from a given frame."""
    with Frame(stepback=stepback) as frame:
        locals_dict = frame.f_locals
    return locals_dict


def traverse_local_prefs(stepback=0):
    """Generator to walk through variables considered as preferences
    in locals dict of a given frame.

    """
    locals_dict = get_frame_locals(stepback+1)
    for k in locals_dict:
        if not k.startswith('_') and k.upper() == k:
            yield k, locals_dict


def import_module(package, module_name):
    """Imports a module from a given package."""
    module = import_module_(package)
    try:
        import_module_('%s.%s' % (package, module_name))
    except:
        if module_has_submodule(module, module_name):
            raise


def import_prefs():
    """Imports preferences modules from packages (apps)."""

    import_module(get_frame_locals(3)['__package__'], PREFS_MODULE_NAME)

    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        import_module(app, PREFS_MODULE_NAME)
