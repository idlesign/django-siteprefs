import sys

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SiteprefsConfig(AppConfig):
    """The default siteprefs configuration."""

    name = 'siteprefs'
    verbose_name = _('Site Preferences')

    def ready(self):

        # Shouldn't try to autodiscover in test as
        # DB probably won't be initialized in the moment.
        if 'test' in sys.argv[0]:
            return

        from .toolbox import autodiscover_siteprefs
        autodiscover_siteprefs()
