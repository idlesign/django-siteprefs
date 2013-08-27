django-siteprefs
================
http://github.com/idlesign/django-siteprefs


.. image:: https://pypip.in/d/django-siteprefs/badge.png
        :target: https://crate.io/packages/django-siteprefs


What's that
-----------

*django-siteprefs allows Django applications settings to come alive*

Let's suppose you have your pretty settings.py file with you application::

    from django.conf import settings

    MY_OPTION_1 = getattr(settings, 'MY_APP_MY_OPTION_1', True)
    MY_OPTION_2 = getattr(settings, 'MY_APP_MY_OPTION_2', 'No alien utopia // Will long survive our bravery')
    MY_OPTION_42 = getattr(settings, 'MY_APP_MY_OPTION_42', 42)


Now you want some of those options to be exposed to the Django Admin interface.

Let's say we expose `MY_OPTION_1`, `MY_OPTION_2`, `MY_OPTION_42` options::

    from django.conf import settings

    MY_OPTION_1 = getattr(settings, 'MY_APP_MY_OPTION_1', True)
    MY_OPTION_2 = getattr(settings, 'MY_APP_MY_OPTION_2', 'No alien utopia // Will long survive our bravery')
    MY_OPTION_42 = getattr(settings, 'MY_APP_MY_OPTION_42', 42)


    # To be sure our app is still functional without django-siteprefs
    # we use this try-except block.
    try:
        from siteprefs.toolbox import patch_locals, register_prefs

        patch_locals()  # This bootstrap is required before `register_prefs` step.

        # And that's how we expose our options to Admin.
        register_prefs(MY_OPTION_1, MY_OPTION_2, MY_OPTION_42)

    except ImportError:
        pass

We're done with the app. Now to your projects' settings.py.

* Add `siteprefs` into `INSTALLED_APPS`;
* Use siteprefs `autodiscover_siteprefs` function to locate all the options exposed by apps in your project::

    from siteprefs.toolbox import autodiscover_siteprefs

    autodiscover_siteprefs()


Now you can view your settings in Django Admin.

If you want those settings to be editable through the Admin - `siteprefs` allows that too, and even more.

Read the docs ;)


Documentation
-------------

http://django-siteprefs.readthedocs.org/
