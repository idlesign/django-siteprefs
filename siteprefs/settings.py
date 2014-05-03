from django.conf import settings


# Toggles internal preferences model showing up in the Admin.
EXPOSE_MODEL_TO_ADMIN = getattr(settings, 'SITEPREFS_EXPOSE_MODEL_TO_ADMIN', False)

# Module name used by siteprefs.toolbox.autodiscover_siteprefs() to find preferences in application packages.
PREFS_MODULE_NAME = getattr(settings, 'SITEPREFS_MODULE_NAME', 'settings')

# List of commands called by manage.py where autodiscover is enabled
ENABLED_COMMANDS = getattr(settings, "SITEPREFS_ENABLED_COMMANDS",
                           ['runserver', 'runserver_plus', 'run_gunicorn', 'celeryd'])
