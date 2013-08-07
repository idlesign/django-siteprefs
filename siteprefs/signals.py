from django.dispatch import Signal


# Issued when dynamic preferences models are saved.
prefs_save = Signal(providing_args=['app', 'updated_prefs'])
