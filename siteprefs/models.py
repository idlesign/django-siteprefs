from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Preference(models.Model):

    app = models.CharField(_('Application'), max_length=100, null=True, blank=True, db_index=True)
    name = models.CharField(_('Name'), max_length=150)
    text = models.TextField(_('Value'), null=True, blank=True)

    class Meta(object):
        verbose_name = _('Preference')
        verbose_name_plural = _('Preferences')
        unique_together = ('app', 'name')

    def __str__(self):
        return '%s:%s' % (self.app, self.name)

    @classmethod
    def read_prefs(cls, mem_prefs):
        """Initializes preferences entries in DB according to currently discovered prefs."""
        db_prefs = {
            '%s__%s' % (pref['app'], pref['name']): pref for pref in
            cls.objects.values().order_by('app', 'name')
        }

        new_prefs = []
        for app, prefs in mem_prefs.items():
            for pref_name, pref_proxy in prefs.items():
                if not pref_proxy.static:  # Do not add static options to DB.
                    key = '%s__%s' % (app, pref_name)
                    if key in db_prefs:
                        # Entry already exists in DB. Let's get pref value from there.
                        pref_proxy.db_value = db_prefs[key]['text']
                    else:
                        new_prefs.append(cls(app=app, name=pref_name, text=pref_proxy.default))

        if new_prefs:
            try:
                cls.objects.bulk_create(new_prefs)
            except IntegrityError:  # Don't bother with duplicates.
                pass

    @classmethod
    def update_prefs(cls, *args, **kwargs):
        # TODO That could be more efficient.
        updated_prefs = kwargs['updated_prefs']
        for db_pref in cls.objects.filter(app=kwargs['app']):
            if db_pref.name in updated_prefs:
                db_pref.text = updated_prefs[db_pref.name]
                db_pref.save()
