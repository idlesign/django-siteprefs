Settings
========

Some aspects of **siteprefs** could be tuned in `settings.py` of your project.


SITEPREFS_EXPOSE_MODEL_TO_ADMIN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Toggles internal preferences model showing up in the Admin. Default: true.


SITEPREFS_DISABLE_AUTODISCOVER
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Disables preferences autodiscovery on Django apps registry ready. Default: false.


SITEPREFS_MODULE_NAME
~~~~~~~~~~~~~~~~~~~~~

Module name used by siteprefs.toolbox.autodiscover_siteprefs() to find preferences in application packages.
