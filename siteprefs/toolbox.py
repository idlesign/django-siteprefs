import sys
from collections import OrderedDict

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

    for local_name, locals_dict in traverse_local_prefs(3):
        addrs[id(locals_dict[local_name])] = local_name

    proxies = []
    locals_dict = get_frame_locals(3)

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
    if ('manage' in sys.argv[0] and sys.argv[1] in MANAGE_SAFE_COMMANDS) or 'manage' not in sys.argv[0]:
        import_prefs()
        Preference.read_prefs(get_prefs())
        register_admin_models(admin_site)


def patch_locals():
    """Temporarily (see unpatch_locals()) replaces all module variables
    considered preferences with PatchedLocal objects, so that every
    variable has different hash returned by id().

    """
    for name, locals_dict in traverse_local_prefs(2):
        locals_dict[name] = PatchedLocal(name, locals_dict[name])

    get_frame_locals(2)[__PATCHED_LOCALS_SENTINEL] = True  # Sentinel.


def unpatch_locals():
    """Restores the original values of module variables
    considered preferences if they are still PatchedLocal
    and not PrefProxy.

    """
    for name, locals_dict in traverse_local_prefs(3):

        if isinstance(locals_dict[name], PatchedLocal):
            locals_dict[name] = locals_dict[name].val

    del get_frame_locals(3)[__PATCHED_LOCALS_SENTINEL]


def register_prefs(*args, **kwargs):
    """Registers preferences whitch should be handled by siteprefs.
    Expects preferences as *args.

    Use keyword arguments to apply params supported by
    PrefProxy to all preferences not enclosed by `pref` and `pref_group`.

    Accepted kwargs:

    :param str|unicode help_text: Field help text.

    :param bool static: Leave this preference static (do not store in DB).

    :param bool readonly: Make this field read only.

    """
    if __PATCHED_LOCALS_SENTINEL not in get_frame_locals(2):
        raise SitePrefsException('Please call `patch_locals()` right before the `register_prefs()`.')

    bind_proxy(args, **kwargs)

    unpatch_locals()


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
        return bind_proxy(
            (preference,),
            field=field,
            verbose_name=verbose_name,
            help_text=help_text,
            static=static,
            readonly=readonly,
        )[0]

    except IndexError:
        return
