# django-crud-views-extensions

Incubator for [django-crud-views](https://github.com/jacob-consulting/django-crud-views)
extension apps. Apps here are named as if they lived in django-crud-views itself
(`crud_views_widget_*`); once mature, an app may move into the main package with no
code changes for consuming projects.

Requires django-crud-views >= 0.29.

## crud_views_widget_datetimepicker

Form widgets wrapping the [xdsoft jQuery DateTimePicker](https://github.com/xdan/datetimepicker):
`DateTimePickerInput`, `DatePickerInput`, `TimePickerInput`.

Prerequisite: jQuery loaded in your base template before `{% cv_js %}` (same rule as
django-crud-views core).

### Install

    pip install django-crud-views-extensions

    INSTALLED_APPS = [
        ...
        "crud_views",
        "crud_views_widget_datetimepicker",
    ]

That's it — the widget's JS/CSS are delivered through `{% cv_js %}`/`{% cv_css %}` on
every page (including crud-views modals) via the asset registry. By default the plugin
files load from jsDelivr (CDN mode).

### Use

    from crud_views_widget_datetimepicker.widgets import DateTimePickerInput

    class AppointmentForm(CrispyModelForm):
        class Meta:
            model = Appointment
            fields = ["title", "starts_at"]
            widgets = {"starts_at": DateTimePickerInput()}

Options: `config={...}` (any xdsoft option, e.g. `step`, `minTime`), and
`DateTimePickerInput(fix_year=2026)` to lock the picker to one calendar year.

### Formats and language

The picker format follows the active request language: the widget takes the first
of the locale's `DATE_INPUT_FORMATS` / `DATETIME_INPUT_FORMATS` / `TIME_INPUT_FORMATS`
that the picker can reproduce (time prefers a format without seconds) and renders the
value with that same format, so whatever the picker writes is accepted on submit —
e.g. `2026-10-15` under `en`, `15.10.2026` under `de`.

To pin a format, pass it to the picker (`config={"format": "d.m.Y"}` or settings
`DEFAULTS`) or to Django (`DatePickerInput(format="%d.%m.%Y")`). The widget renders and
parses a pinned format itself, so it works in every locale. Supported tokens:
`d m Y y H i s`; a picker format with other tokens is passed to the picker unchanged and
must then be accepted by the field's `input_formats`.

The picker language is the active request language unless `LANG` (settings) or
`config={"lang": ...}` sets one. The plugin's language is page-global: one field with
its own `lang` switches every picker on that page.

### Settings

    CRUD_VIEWS_DATETIMEPICKER = {
        "SOURCE": "cdn",        # "cdn" (default) | "vendored"
        "VERSION": "2.5.21",    # pinned upstream version, used by both modes
        "CDN_BASE": "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/",
        "VENDOR_DIR": None,     # required for vendored mode; must be on STATICFILES_DIRS
        "EMIT": True,           # False: keep registered but let a bundler deliver the files
        "LANG": None,           # None: the active request language
        "DEFAULTS": {},         # merged into every widget's picker config
    }

### Vendored mode (recommended for production / GDPR)

    CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored", "VENDOR_DIR": BASE_DIR / "vendored_static"}
    STATICFILES_DIRS = [BASE_DIR / "vendored_static"]

    python manage.py cv_vendor_datetimepicker

A system check warns on startup when the vendored files are missing (`crud_views.W330`)
or don't match the pinned `VERSION` (`crud_views.W331`).

### django-pipeline

CDN mode cannot be bundled. For pipeline, use vendored mode and build your bundle from
the same path list the app uses internally — then switch off tag emission:

    from crud_views_widget_datetimepicker.assets import source_files

    _dtp = source_files("2.5.21", minified=False)   # pipeline minifies itself
    PIPELINE = {
        "JAVASCRIPT": {"main": {"source_filenames": [..., *_dtp["js"]], ...}},
        "STYLESHEETS": {"main": {"source_filenames": [..., *_dtp["css"]], ...}},
    }
    CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored", "VENDOR_DIR": ..., "EMIT": False}

Keep the order jQuery → plugin → init.js in your bundle (`source_files()` already
returns plugin before init.js).
