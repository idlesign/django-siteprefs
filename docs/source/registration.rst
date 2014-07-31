Preferences registration
========================

**siteprefs** has several helpers to ease application settings registration.

All of them reside in `siteprefs.toolbox` module. Let's go one by one:


* `register_prefs(*args, **kwargs )`

  The main way to register your settings. Expects preferences as **args** and their options as **kwargs**::

        register_prefs(
            MY_OPT_1,
            MY_OPT_2,
            MY_OPT_3,
            category='All the settings'  # This will group all the settings into one category in Admin.
        )


* `pref_group(group_title, prefs, **kwargs)`

  This allows preferences grouping. Expects a group title, a list of preferences and their options as **kwargs**::

        register_prefs(
            MY_OPT_1, MY_OPT_2,
            pref_group('My options group 1', (MY_OPT_3, MY_OPT_4), static=False),
            pref_group('My options group 2', (MY_OPT_5, pref(MY_OPT_6, verbose_name='My 6'))),
        )


* `pref(preference, **kwargs)`

  Used to mark a preference. Expects a preference and its options as **kwargs**::

        register_prefs(
            MY_OPT_1, MY_OPT_2,
            pref(MY_OPT_3, verbose_name='My third option', static=False),
            pref(MY_OPT_4, verbose_name='Fourth', help_text='My fourth option.'),
        )


Options accepted by prefs
-------------------------

These are the options accepted as **kwargs** by **siteprefs** helpers:


* `static`

  Flag to mark a preference editable from Admin - static are not editable. True by default.

* `readonly`

  Flag to mark an [editable] preference read only for Admin. False by default.

* `field`

  Field instance (from django.db.models, e.g. ``BooleanField()``) to represent a sitepref in Admin.

  None by default. If None, **siteprefs** will try to determine an appropriate field type for a given
  preference value type.

* `category`

  Category name to group a sitepref under. None by default.


* `verbose_name`

  Preference name to render in Admin.

  None by default. If None, a name will be deduces from preference variable name.

* `help_text`

  Hint text to render for a preference in Admin. Empty by default.
