import sys
from collections import OrderedDict

from django.contrib import admin

from .models import Preference
from .utils import import_prefs, get_frame_locals, traverse_local_prefs, get_pref_model_admin_class, \
    get_pref_model_class, PrefProxy, PatchedLocal, Frame
from .exceptions import SitePrefsException
from .signals import prefs_save
from .settings import MANAGE_SAFE_COMMANDS


__PATCHED_LOCALS_SENTINEL = '__siteprefs_locals_patched'

__PREFS_REGISTRY = None
__PREFS_DEFAULT_REGISTRY = OrderedDict()


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
    """Returns a dictionary with preferences for a certain app/module."""
    if app is None:
        with Frame(stepback=1) as frame:
            app = frame.f_globals['__name__'].split('.')[0]
    prefs = get_prefs()
    if app not in prefs:
        return None
    return prefs[app]


def bind_proxy(vals, category=None, **kwargs):
    """Binds PrefProxy objects to module variables used by apps as preferences."""
    addrs = OrderedDict()
    for local_name, locals_dict in traverse_local_prefs(3):
        addrs[id(locals_dict[local_name])] = local_name

    proxies = []
    locals_dict = get_frame_locals(3)
    for v in vals:  # Try to preserve fields order.
        id_val = id(v)
        if id_val in addrs:
            local_name = addrs[id_val]
            local_val = locals_dict[local_name]
            if isinstance(local_val, PatchedLocal) and not isinstance(local_val, PrefProxy):
                proxy = PrefProxy(local_name, v.val, category=category, **kwargs)

                app_name = locals_dict['__name__'].split('.')[0]
                prefs = get_prefs()
                if app_name not in prefs:
                    prefs[app_name] = OrderedDict()

                prefs[app_name][local_name.lower()] = proxy

                # Replace original pref variable with a proxy.
                locals_dict[local_name] = proxy
                proxies.append(proxy)

    return proxies


def register_admin_models(admin_site):
    """Registers dynamically created preferences models for Admin interface."""
    prefs = get_prefs()

    for app_label, prefs_items in prefs.items():
        model_class = get_pref_model_class(app_label, prefs_items, get_app_prefs)
        if model_class is not None:
            admin_site.register(model_class, get_pref_model_admin_class(prefs_items))


def autodiscover_siteprefs(admin_site=None):
    """Automatically discovers and registers all preferences available in all apps."""
    if admin_site is None:
        admin_site = admin.site
    with Frame(stepback=2) as frame:
        package = frame.f_globals['__package__']

    skip_packages = [
        'django.utils',
        'importlib',  # Since Django 1.9
    ]
    # Do not discover anything if called from manage.py (e.g. executing commands from cli).
    if package not in skip_packages or (len(sys.argv) > 1 and sys.argv[1] in MANAGE_SAFE_COMMANDS):
        import_prefs()
        Preference.read_prefs(get_prefs())
        register_admin_models(admin_site)


def patch_locals():
    """Temporarily (see unpatch_locals()) replaces all module variables
    considered preferences with PatchedLocal objects, so that every
    variable has different hash returned by id().

    """
    for k, ldict in traverse_local_prefs(2):
        ldict[k] = PatchedLocal(k, ldict[k])
    get_frame_locals(2)[__PATCHED_LOCALS_SENTINEL] = True  # Sentinel.


def unpatch_locals():
    """Restores the original values of module variables
    considered preferences if they are still PatchedLocal
    and not PrefProxy.

    """
    for k, ldict in traverse_local_prefs(3):
        if isinstance(ldict[k], PatchedLocal):
            ldict[k] = ldict[k].val
    del get_frame_locals(3)[__PATCHED_LOCALS_SENTINEL]


def register_prefs(*args, **kwargs):
    """Registers preferences whitch should be handled by siteprefs.
    Expects preferences as *args.

    Use keyword arguments to apply params supported by
    PrefProxy to all preferences not enclosed by `pref` and `pref_group`.

    """
    if __PATCHED_LOCALS_SENTINEL not in get_frame_locals(2):
        raise SitePrefsException('Please call `patch_locals()` right before the `register_prefs()`.')
    bind_proxy(args, **kwargs)
    unpatch_locals()


def pref_group(title, prefs, **kwargs):
    """Marks preferences group.
    Expects group title, and a set of preferences to group.

    Use keyword arguments to apply params supported by
    PrefProxy to all preferences in group not enclosed by `pref`.

    """
    bind_proxy(prefs, title, **kwargs)
    for proxy in prefs:  # For preferences already marked by pref().
        if isinstance(proxy, PrefProxy):
            proxy.category = title


def pref(preference, **kwargs):
    """Marks a preference.

    Use keyword arguments to apply params supported by
    PrefProxy to this preference.

    """
    try:
        return bind_proxy((preference,), **kwargs)[0]
    except IndexError:
        return
