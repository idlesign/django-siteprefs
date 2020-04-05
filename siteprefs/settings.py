from django.conf import settings


EXPOSE_MODEL_TO_ADMIN = getattr(settings, 'SITEPREFS_EXPOSE_MODEL_TO_ADMIN', False)
"""Toggles internal preferences model showing up in the Admin."""

DISABLE_AUTODISCOVER = getattr(settings, 'SITEPREFS_DISABLE_AUTODISCOVER', False)
"""Disables preferences autodiscovery on Django apps registry ready."""

PREFS_MODULE_NAME = getattr(settings, 'SITEPREFS_MODULE_NAME', 'settings')
"""Module name used by siteprefs.toolbox.autodiscover_siteprefs() to find preferences in application packages."""

MANAGE_SAFE_COMMANDS = getattr(
    settings, 'SITEPREFS_MANAGE_SAFE_COMMANDS', ['runserver', 'runserver_plus', 'run_gunicorn', 'celeryd'])
"""List of commands called by manage.py where autodiscover is enabled"""
