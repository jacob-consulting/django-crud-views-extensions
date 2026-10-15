# django-crud-views-extensions

[![Tests](https://github.com/jacob-consulting/django-crud-views-extensions/actions/workflows/tests.yml/badge.svg)](https://github.com/jacob-consulting/django-crud-views-extensions/actions/workflows/tests.yml)
[![Lint](https://github.com/jacob-consulting/django-crud-views-extensions/actions/workflows/lint.yml/badge.svg)](https://github.com/jacob-consulting/django-crud-views-extensions/actions/workflows/lint.yml)
[![PyPI](https://img.shields.io/pypi/v/django-crud-views-extensions)](https://pypi.org/project/django-crud-views-extensions/)
[![Docs](https://readthedocs.org/projects/django-crud-views-extensions/badge/?version=stable)](https://django-crud-views-extensions.readthedocs.io/en/stable/)

Incubator for [django-crud-views](https://github.com/jacob-consulting/django-crud-views)
extension apps. Apps here are named as if they lived in django-crud-views itself
(`crud_views_widget_*`); once mature, an app may move into the main package with no
code changes for consuming projects.

Requires django-crud-views >= 0.29.

**Documentation:** <https://django-crud-views-extensions.readthedocs.io/en/stable/>

```bash
pip install django-crud-views-extensions
```

## crud_views_widget_datetimepicker

Form widgets wrapping the [xdsoft jQuery DateTimePicker](https://github.com/xdan/datetimepicker):
`DateTimePickerInput`, `DatePickerInput`, `TimePickerInput`. The plugin loads from a CDN or from vendored static
files; the picker format follows the request's locale.

```python
INSTALLED_APPS = [..., "crud_views", "crud_views_widget_datetimepicker"]

from crud_views_widget_datetimepicker.widgets import DateTimePickerInput

widgets = {"starts_at": DateTimePickerInput()}
```

[Getting started](https://django-crud-views-extensions.readthedocs.io/en/stable/getting_started/datetimepicker/) ·
[Reference](https://django-crud-views-extensions.readthedocs.io/en/stable/reference/datetimepicker/widgets/)

## crud_views_widget_typeahead

A server-backed type-ahead single select for large, permission-sensitive model choice sets (thousands of
users), for forms and django-filter filters — as a text typeahead or a select popup. Vanilla JS, no jQuery,
CSP-safe, ARIA combobox.

```python
INSTALLED_APPS = [..., "crud_views", "crud_views_widget_typeahead"]

urlpatterns += [path("_typeahead/", include("crud_views_widget_typeahead.urls"))]
```

[Getting started](https://django-crud-views-extensions.readthedocs.io/en/stable/getting_started/typeahead/) ·
[Reference](https://django-crud-views-extensions.readthedocs.io/en/stable/reference/typeahead/lookups/)

## Example app

`examples/bootstrap5/` is a local Django project with one page per use case, running against the code in `src/`:

```bash
cd examples/bootstrap5
task run        # migrate, seed, runserver on :8000 — log in as admin/admin
```

**Try it online:** the [live demo](https://django-crud-views-extensions-demo.onrender.com/) runs the example app (log in as `admin` / `admin`; data resets daily).

[More about the example app](https://django-crud-views-extensions.readthedocs.io/en/stable/getting_started/example_app/)

## Development

See [Development](https://django-crud-views-extensions.readthedocs.io/en/stable/development/).
