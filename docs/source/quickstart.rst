Getting started
===============

* Add the **siteprefs** application to INSTALLED_APPS in your settings file (usually 'settings.py').
* Use ``> python manage.py migrate`` command to install apps tables int DB.


Quick example
-------------

Let's suppose we created ``MYAPP`` application and now create ``settings.py`` file for it:

.. code-block:: python

    from django.conf import settings

    ENABLE_GRAVATARS = getattr(settings, 'MYAPP_ENABLE_GRAVATARS', True)
    ENABLE_MAIL_RECOVERY = getattr(settings, 'MYAPP_ENABLE_MAIL_RECOVERY', True)
    ENABLE_MAIL_BOMBS = getattr(settings, 'MYAPP_ENABLE_MAIL_BOMBS', False)
    SLOGAN = "I'm short and I'm tall // I'm black and I'm white"
    PRIVATE_SETTING = 'Hidden'


    if 'siteprefs' in settings.INSTALLED_APPS:  # Respect those users who doesn't have siteprefs installed.

        from siteprefs.toolbox import preferences

        with preferences() as prefs:

            prefs(  # Now we register our settings to make them available as siteprefs.
                # First we define a group of related settings, and mark them non-static (editable).
                prefs.group('Mail settings', (ENABLE_MAIL_RECOVERY, ENABLE_MAIL_BOMBS), static=False),
                SLOGAN,  # This setting stays static non-editable.
                # And finally we register a non-static setting with extended meta for Admin.
                prefs.one(
                    ENABLE_GRAVATARS,
                    verbose_name='Enable Gravatar service support', static=False,
                    help_text='This enables Gravatar support.'),
            )


From now on you can view (and edit) your preferences with Django Admin interface.

Access your settings as usual, all changes made to preferences with Admin interface will be respected:

.. code-block:: python

    from .settings import ENABLE_MAIL_BOMBS

    def bombing():
        if ENABLE_MAIL_BOMBS:
            print('booooom')


And mind that we've barely made a scratch of **siteprefs**.
