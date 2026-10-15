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
that the picker can reproduce (time and datetime prefer a format without seconds — the
picker cannot set them) and renders the
value with that same format, so whatever the picker writes is accepted on submit —
e.g. `2026-10-15 19:00` under `en`, `15.10.2026 19:00` under `de`.

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

## crud_views_widget_typeahead

A server-backed type-ahead single select for large, permission-sensitive model choice sets (thousands of
users), for forms and django-filter filters. Vanilla JS, no jQuery, CSP-safe, ARIA combobox.

### Install

```python
INSTALLED_APPS = [
    # ...
    "crud_views.apps.CrudViewsConfig",
    "crud_views_widget_typeahead.apps.CrudViewsWidgetTypeaheadConfig",
]

# urls.py — any prefix
urlpatterns += [path("_typeahead/", include("crud_views_widget_typeahead.urls"))]
```

Assets reach every page through `{% cv_js %}` / `{% cv_css %}`.

### Define a lookup

Put lookups in your app's `typeahead.py`; it is imported automatically at startup.

```python
from crud_views_widget_typeahead.lookups import register_user_lookup

@register_user_lookup("projects.members")
def members(request, project):
    if not request.user.has_perm("projects.view_project"):
        raise PermissionDenied
    return get_object_or_404(Project, pk=project).members.all()
```

For other models, subclass `TypeaheadLookup` (`search_fields`, `ordering`, `max_results=10`, `min_chars=2`,
`login_required=True`, `get_queryset(request, **params)`, `label(obj)`) and decorate it with
`@register_lookup("app.name")`. Values are always the pk (`to_field_name` is not supported). Every word of the search term must match one of `search_fields`
(`icontains`). `register_user_lookup(name, base=...)` takes your own `UserLookup` subclass, e.g. to change
the label.

### Bind a form field / filter

```python
class TaskForm(forms.ModelForm):
    assignee = TypeaheadField(lookup="projects.members")

    def __init__(self, *args, request, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].bind(request, project=str(project.pk))


class TaskFilter(django_filters.FilterSet):
    assignee = TypeaheadFilter(lookup="projects.members")

    do_not_call_in_templates = True  # see below

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["assignee"].bind(self.request, project=str(self.project.pk))
```

`bind()` sets the field's queryset (save-time validation) and signs `{lookup, params}` into the widget, so
the endpoint serves exactly that set, re-checking permission on every request. Params must be JSON values
(pass UUIDs as `str`). An unbound field raises `ImproperlyConfigured`. With crud_views' `CrispyModelForm`,
use `self.cv_view.request` (see the example app).

**crud_views list views:** the list template tests `{% if view.filterset_class %}`, and Django templates
call callables — so the FilterSet class is instantiated there without a request. Set
`do_not_call_in_templates = True` on a FilterSet that binds in `__init__`.

### Settings

| Key in `CRUD_VIEWS_TYPEAHEAD` | Default | |
|---|---|---|
| `EMIT` | `True` | `False` suppresses our `cv_js`/`cv_css` output (skins, django-pipeline) |
| `TEMPLATE` | `"crud_views_widget_typeahead/typeahead.html"` | widget template |
| `DEBOUNCE_MS` | `250` | input debounce |

django-pipeline: `from crud_views_widget_typeahead.assets import source_files` (Django-free).

### Endpoint

`GET <mount>/?t=<token>&q=<term>` → `{"results": [{"value", "label"}], "count": n}` (`count` before
truncation to `max_results`). Errors are JSON: 400 `bad_token`, 403 `login_required` / `forbidden`,
404 `not_found`; 405 for non-GET. Terms shorter than `min_chars` return an empty result without a query.

### Skins

A design-system package replaces the frontend and keeps the server core:

1. Set `CRUD_VIEWS_TYPEAHEAD["TEMPLATE"]` (or a widget's `template_name`). The template gets `widget.attrs`
   (visible input: id, ARIA, merged `aria-describedby`) and `widget.typeahead`: `url`, `label`, `value`,
   `hidden_name`, `hidden_id`, `listbox_id`, `hint_id`, `min_chars`, `debounce`, `submit_on_clear`, `i18n`
   (`hint`, `more`, `none`, `count`, `error`, `clear`, `listbox`; `{n}` is the number placeholder).
2. Register your own JS/CSS with `crud_views.lib.assets.register_assets` and set `EMIT = False`.
3. Keep the hidden input contract (it has the `name`, carries the pk, `autocomplete="off"`, empty when
   nothing is selected) and these behaviours: visible text = label of the stored pk except while typing
   (restore on blur and submit; clear only via a clear button or fully emptied text); arrow keys preview text
   only; Enter never submits while the list is open; escape/highlight labels yourself; show "N more" from
   `count`; ARIA combobox/listbox with a live result count; re-init on `cv:modal:loaded`.

Dynamically added content (e.g. new formset rows) needs `window.cvTypeahead.init(container)`.

## Example app

`examples/bootstrap5/` is a local Django project with one page per use case
(datetimepicker: forms, modal, list filters, per-field config; typeahead: teams and tasks with 3,000 users). It runs against the code in `src/`.

```bash
cd examples/bootstrap5
task run        # migrate, seed, runserver on :8000 — log in as admin/admin
task test       # the example's own tests
```

Without [Task](https://taskfile.dev): `uv run manage.py migrate && uv run manage.py seed && uv run manage.py runserver`.
