Getting started
===============

* Add the **siteprefs** application to INSTALLED_APPS in your settings file (usually 'settings.py').
* Use ``> python manage.py syncdb`` command to install apps tables int DB (``> python manage.py migrate`` for Django 1.7+)
* Add preferences ``autodiscover`` function call into settings (or urls; or `.ready()` in some application config on Django 1.9+) file::

    from siteprefs.toolbox import autodiscover_siteprefs

    autodiscover_siteprefs()


.. warning::

    Those, who are using South <1.0 for migrations, add this into settings file:

    .. code-block:: python

        SOUTH_MIGRATION_MODULES = {
            'siteprefs': 'siteprefs.south_migrations',
        }



Quick example
-------------

Let's suppose we created ``MYAPP`` application and now create ``settings.py`` file for it::

    from django.conf import settings

    ENABLE_GRAVATARS = getattr(settings, 'MYAPP_ENABLE_GRAVATARS', True)
    ENABLE_MAIL_RECOVERY = getattr(settings, 'MYAPP_ENABLE_MAIL_RECOVERY', True)
    ENABLE_MAIL_BOMBS = getattr(settings, 'MYAPP_ENABLE_MAIL_BOMBS', False)
    SLOGAN = "I'm short and I'm tall // I'm black and I'm white"
    PRIVATE_SETTING = 'Hidden'


    try:  # Respect those users who doesn't have siteprefs installed.
        from siteprefs.toolbox import patch_locals, register_prefs, pref, pref_group

        patch_locals()  # That's bootstrap.

        register_prefs(  # Now we register our settings to make them available as siteprefs.
            # First we define a group of related settings, and mark them non-static (editable).
            pref_group('Mail settings', (ENABLE_MAIL_RECOVERY, ENABLE_MAIL_BOMBS), static=False),
            SLOGAN,  # This setting stays static non-editable.
            # And finally we register a non-static setting with extended meta for Admin.
            pref(ENABLE_GRAVATAR_SUPPORT, verbose_name='Enable Gravatar service support', static=False, help_text='This enables Gravatar support.'),
        )
    except ImportError:
        pass


From now on you can view (and edit) your preferences with Django Admin interface.

Access your settings as usual, all changes made to preferences with Admin interface will be respected::

    from .settings import ENABLE_MAIL_BOMBS

    def bombing():
        if ENABLE_MAIL_BOMBS:
            print('booooom')


And mind that we've barely made a scratch of **siteprefs**.
