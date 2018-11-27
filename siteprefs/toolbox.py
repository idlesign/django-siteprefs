import sys
from collections import OrderedDict
from types import ModuleType

from django.contrib import admin

from .exceptions import SitePrefsException
from .models import Preference
from .settings import MANAGE_SAFE_COMMANDS
from .signals import prefs_save
from .utils import import_prefs, get_frame_locals, traverse_local_prefs, get_pref_model_admin_class, \
    get_pref_model_class, PrefProxy, PatchedLocal, Frame

__PATCHED_LOCALS_SENTINEL = '__siteprefs_locals_patched'

__PREFS_REGISTRY = None
__PREFS_DEFAULT_REGISTRY = OrderedDict()
__MODELS_REGISTRY = {}


def on_pref_update(*args, **kwargs):
    """Triggered on dynamic preferences model save.
     Issues DB save and reread.

    """
    Preference.update_prefs(*args, **kwargs)
    Preference.read_prefs(get_prefs())

prefs_save.connect(on_pref_update)


def get_prefs():
    """Returns a dictionary with all preferences discovered by siteprefs."""
    global __PREFS_REGISTRY

    if __PREFS_REGISTRY is None:
        __PREFS_REGISTRY = __PREFS_DEFAULT_REGISTRY

    return __PREFS_REGISTRY


def get_app_prefs(app=None):
    """Returns a dictionary with preferences for a certain app/module.

    :param str|unicode app:

    :rtype: dict

    """
    if app is None:

        with Frame(stepback=1) as frame:
            app = frame.f_globals['__name__'].split('.')[0]

    prefs = get_prefs()

    if app not in prefs:
        return {}

    return prefs[app]


def get_prefs_models():
    """Returns registered preferences models indexed by application names.

    :rtype: dict
    """
    return __MODELS_REGISTRY


def bind_proxy(values, category=None, field=None, verbose_name=None, help_text='', static=True, readonly=False):
    """Binds PrefProxy objects to module variables used by apps as preferences.

    :param list|tuple values: Preference values.

    :param str|unicode category: Category name the preference belongs to.

    :param Field field: Django model field to represent this preference.

    :param str|unicode verbose_name: Field verbose name.

    :param str|unicode help_text: Field help text.

    :param bool static: Leave this preference static (do not store in DB).

    :param bool readonly: Make this field read only.

    :rtype: list

    """
    addrs = OrderedDict()

    depth = 3

    for local_name, locals_dict in traverse_local_prefs(depth):
        addrs[id(locals_dict[local_name])] = local_name

    proxies = []
    locals_dict = get_frame_locals(depth)

    for value in values:  # Try to preserve fields order.

        id_val = id(value)

        if id_val in addrs:
            local_name = addrs[id_val]
            local_val = locals_dict[local_name]

            if isinstance(local_val, PatchedLocal) and not isinstance(local_val, PrefProxy):

                proxy = PrefProxy(
                    local_name, value.val,
                    category=category,
                    field=field,
                    verbose_name=verbose_name,
                    help_text=help_text,
                    static=static,
                    readonly=readonly,
                )

                app_name = locals_dict['__name__'].split('.')[-2]  # x.y.settings -> y
                prefs = get_prefs()

                if app_name not in prefs:
                    prefs[app_name] = OrderedDict()

                prefs[app_name][local_name.lower()] = proxy

                # Replace original pref variable with a proxy.
                locals_dict[local_name] = proxy
                proxies.append(proxy)

    return proxies


def register_admin_models(admin_site):
    """Registers dynamically created preferences models for Admin interface.

    :param admin.AdminSite admin_site: AdminSite object.

    """
    global __MODELS_REGISTRY

    prefs = get_prefs()

    for app_label, prefs_items in prefs.items():

        model_class = get_pref_model_class(app_label, prefs_items, get_app_prefs)

        if model_class is not None:
            __MODELS_REGISTRY[app_label] = model_class
            admin_site.register(model_class, get_pref_model_admin_class(prefs_items))


def autodiscover_siteprefs(admin_site=None):
    """Automatically discovers and registers all preferences available in all apps.

    :param admin.AdminSite admin_site: Custom AdminSite object.

    """
    if admin_site is None:
        admin_site = admin.site

    # Do not discover anything if called from manage.py (e.g. executing commands from cli).
    if 'manage' not in sys.argv[0] or (len(sys.argv) > 1 and sys.argv[1] in MANAGE_SAFE_COMMANDS):
        import_prefs()
        Preference.read_prefs(get_prefs())
        register_admin_models(admin_site)


def patch_locals(depth=2):
    """Temporarily (see unpatch_locals()) replaces all module variables
    considered preferences with PatchedLocal objects, so that every
    variable has different hash returned by id().

    """
    for name, locals_dict in traverse_local_prefs(depth):
        locals_dict[name] = PatchedLocal(name, locals_dict[name])

    get_frame_locals(depth)[__PATCHED_LOCALS_SENTINEL] = True  # Sentinel.


def unpatch_locals(depth=3):
    """Restores the original values of module variables
    considered preferences if they are still PatchedLocal
    and not PrefProxy.

    """
    for name, locals_dict in traverse_local_prefs(depth):
        if isinstance(locals_dict[name], PatchedLocal):
            locals_dict[name] = locals_dict[name].val

    del get_frame_locals(depth)[__PATCHED_LOCALS_SENTINEL]


class ModuleProxy(object):
    """Proxy to handle module attributes access."""

    def __init__(self):
        self._module = None  # type: ModuleType
        self._prefs = []

    def bind(self, module, prefs):
        """
        :param ModuleType module:
        :param list prefs: Preference names. Just to speed up __getattr__.
        """
        self._module = module
        self._prefs = set(prefs)

    def __getattr__(self, name):

        value = getattr(self._module, name)

        if name in self._prefs:
            # It is a PrefProxy
            value = value.value

        return value


def proxy_settings_module(depth=3):
    """Replaces a settings module with a Module proxy to intercept
    an access to settings.

    :param int depth: Frame count to go backward.

    """
    proxies = []

    modules = sys.modules
    module_name = get_frame_locals(depth)['__name__']

    module_real = modules[module_name]

    for name, locals_dict in traverse_local_prefs(depth):

        value = locals_dict[name]

        if isinstance(value, PrefProxy):
            proxies.append(name)

    new_module = type(module_name, (ModuleType, ModuleProxy), {})(module_name)  # ModuleProxy
    new_module.bind(module_real, proxies)

    modules[module_name] = new_module


def register_prefs(*args, **kwargs):
    """Registers preferences that should be handled by siteprefs.

    Expects preferences as *args.

    Use keyword arguments to batch apply params supported by
    ``PrefProxy`` to all preferences not constructed by ``pref`` and ``pref_group``.

    Batch kwargs:

        :param str|unicode help_text: Field help text.

        :param bool static: Leave this preference static (do not store in DB).

        :param bool readonly: Make this field read only.

    :param bool swap_settings_module: Whether to automatically replace settings module
        with a special ``ProxyModule`` object to access dynamic values of settings
        transparently (so not to bother with calling ``.value`` of ``PrefProxy`` object).

    """
    swap_settings_module = bool(kwargs.get('swap_settings_module', True))

    if __PATCHED_LOCALS_SENTINEL not in get_frame_locals(2):
        raise SitePrefsException('Please call `patch_locals()` right before the `register_prefs()`.')

    bind_proxy(args, **kwargs)

    unpatch_locals()

    swap_settings_module and proxy_settings_module()


def pref_group(title, prefs, help_text='', static=True, readonly=False):
    """Marks preferences group.

    :param str|unicode title: Group title

    :param list|tuple prefs: Preferences to group.

    :param str|unicode help_text: Field help text.

    :param bool static: Leave this preference static (do not store in DB).

    :param bool readonly: Make this field read only.

    """
    bind_proxy(prefs, title, help_text=help_text, static=static, readonly=readonly)

    for proxy in prefs:  # For preferences already marked by pref().
        if isinstance(proxy, PrefProxy):
            proxy.category = title


def pref(preference, field=None, verbose_name=None, help_text='', static=True, readonly=False):
    """Marks a preference.

    :param preference: Preference variable.

    :param Field field: Django model field to represent this preference.

    :param str|unicode verbose_name: Field verbose name.

    :param str|unicode help_text: Field help text.

    :param bool static: Leave this preference static (do not store in DB).

    :param bool readonly: Make this field read only.

    :rtype: PrefProxy|None
    """
    try:
        bound = bind_proxy(
            (preference,),
            field=field,
            verbose_name=verbose_name,
            help_text=help_text,
            static=static,
            readonly=readonly,
        )
        return bound[0]

    except IndexError:
        return


class preferences(object):
    """Context manager - main entry point for siteprefs.

    .. code-block:: python

        from siteprefs.toolbox import preferences

        with preferences() as prefs:

            prefs(
                MY_OPTION_1,
                prefs.one(MY_OPTION_2, static=False),
                prefs.group('My Group', [prefs.one(MY_OPTION_42)]),
            )

    """

    one = staticmethod(pref)
    group = staticmethod(pref_group)

    __call__ = register_prefs

    def __enter__(self):
        patch_locals(3)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
