django-siteprefs
================
http://github.com/idlesign/django-siteprefs

.. image:: https://img.shields.io/pypi/v/django-siteprefs.svg
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

Let's suppose you have your pretty settings.py file with you application:

.. code:: python

    from django.conf import settings

    MY_OPTION_1 = getattr(settings, 'MY_APP_MY_OPTION_1', True)
    MY_OPTION_2 = getattr(settings, 'MY_APP_MY_OPTION_2', 'Some value')
    MY_OPTION_42 = getattr(settings, 'MY_APP_MY_OPTION_42', 42)


Now you want these options to be exposed to Django Admin interface. Just add the following:

.. code:: python

    # To be sure our app is still functional without django-siteprefs.
    if 'siteprefs' in settings.INSTALLED_APPS:
        from siteprefs.toolbox import patch_locals, register_prefs

        patch_locals()  # This bootstrap is required before `register_prefs` step.

        # And that's how we expose our options to Admin.
        register_prefs(MY_OPTION_1, MY_OPTION_2, MY_OPTION_42)


After that you can view your settings in Django Admin.

If you want those settings to be editable through the Admin - `siteprefs` allows that too, and even more.

Read the docs ;)


Documentation
-------------

http://django-siteprefs.readthedocs.org/
