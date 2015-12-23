django-siteprefs
================
http://github.com/idlesign/django-siteprefs

.. image:: https://img.shields.io/pypi/v/django-siteprefs.svg
    :target: https://pypi.python.org/pypi/django-siteprefs

.. image:: https://img.shields.io/pypi/dm/django-siteprefs.svg
    :target: https://pypi.python.org/pypi/django-siteprefs

.. image:: https://img.shields.io/pypi/l/django-siteprefs.svg
    :target: https://pypi.python.org/pypi/django-siteprefs

.. image:: https://img.shields.io/coveralls/idlesign/django-siteprefs/master.svg
    :target: https://coveralls.io/r/idlesign/django-siteprefs

.. image:: https://img.shields.io/travis/idlesign/django-siteprefs/master.svg
    :target: https://travis-ci.org/idlesign/django-siteprefs

.. image:: https://landscape.io/github/idlesign/django-siteprefs/master/landscape.svg?style=flat
   :target: https://landscape.io/github/idlesign/django-siteprefs/master


What's that
-----------

*django-siteprefs allows Django applications settings to come alive*

Let's suppose you have your pretty settings.py file with you application::

    from django.conf import settings

    MY_OPTION_1 = getattr(settings, 'MY_APP_MY_OPTION_1', True)
    MY_OPTION_2 = getattr(settings, 'MY_APP_MY_OPTION_2', 'No alien utopia // Will long survive our bravery')
    MY_OPTION_42 = getattr(settings, 'MY_APP_MY_OPTION_42', 42)


Now you want these options to be exposed to Django Admin interface::

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

We're done with the app. Now to your settings.py of your project.

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
