from django.dispatch import Signal


prefs_save = Signal()
"""Issued when dynamic preferences models are saved.
providing_args=['app', 'updated_prefs']

"""
