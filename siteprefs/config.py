from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from .settings import DISABLE_AUTODISCOVER


class SiteprefsConfig(AppConfig):
    """The default siteprefs configuration."""

    name = 'siteprefs'
    verbose_name = _('Site Preferences')

    def ready(self):

        if DISABLE_AUTODISCOVER:
            return

        from .toolbox import autodiscover_siteprefs
        autodiscover_siteprefs()
