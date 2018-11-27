from django.conf import settings


NOT_AN_OPTION = 'not-an-option'
MY_OPTION_1 = getattr(settings, 'MY_APP_MY_OPTION_1', True)
MY_OPTION_2 = getattr(settings, 'MY_APP_MY_OPTION_2', 'Some value')
MY_OPTION_42 = getattr(settings, 'MY_APP_MY_OPTION_42', 42)


if 'siteprefs' in settings.INSTALLED_APPS:

    from siteprefs.toolbox import preferences

    with preferences() as prefs:

        prefs(
            MY_OPTION_1,
            prefs.one(MY_OPTION_2, static=False),
            prefs.group('My Group', [prefs.one(MY_OPTION_42)]),
        )
