from django.dispatch import Signal


prefs_save = Signal(providing_args=['app', 'updated_prefs'])
"""Issued when dynamic preferences models are saved."""
