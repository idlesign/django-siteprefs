from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SiteprefsConfig(AppConfig):
    """The default siteprefs configuration."""

    name = 'siteprefs'
    verbose_name = _('Site Preferences')
