from pytest_djangoapp import configure_djangoapp_plugin

pytest_plugins = configure_djangoapp_plugin({
    'SITEPREFS_EXPOSE_MODEL_TO_ADMIN': True,
    'SITEPREFS_DISABLE_AUTODISCOVER': True,
})
