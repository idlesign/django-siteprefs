from django.conf import settings


MY_OPTION_1 = getattr(settings, 'MY_APP_MY_OPTION_1', True)
MY_OPTION_2 = getattr(settings, 'MY_APP_MY_OPTION_2', 'Some value')
MY_OPTION_42 = getattr(settings, 'MY_APP_MY_OPTION_42', 42)


if 'siteprefs' in settings.INSTALLED_APPS:

    from siteprefs.toolbox import patch_locals, register_prefs, pref, pref_group

    patch_locals()

    register_prefs(
        MY_OPTION_1,
        pref(MY_OPTION_2, static=False),
        pref_group('My Group', [pref(MY_OPTION_42)]),
    )
