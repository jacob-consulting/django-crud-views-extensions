# Django CRUD Views Extensions

An incubator for [django-crud-views](https://github.com/jacob-consulting/django-crud-views) extension apps.
The apps are named as if they already lived in django-crud-views itself (`crud_views_widget_*`): once an app is
mature, it can move into the main package with no code changes for consuming projects.

## The naming contract

Public import paths (`crud_views_widget_<name>.<module>`) and settings keys (`CRUD_VIEWS_<NAME>`, for example
`CRUD_VIEWS_DATETIMEPICKER`) are part of the contract. They stay stable when an app moves into django-crud-views.

## Requirements

- Python 3.12 or newer
- django-crud-views 0.29 or newer
- jQuery, for the datetimepicker only

## Apps

### crud_views_widget_datetimepicker

Form widgets wrapping the [xdsoft jQuery DateTimePicker](https://github.com/xdan/datetimepicker):
`DateTimePickerInput`, `DatePickerInput` and `TimePickerInput`. The plugin loads from a CDN or from vendored
static files, and the picker format follows the locale of the current request.

[Get started](getting_started/datetimepicker.md) · [Reference](reference/datetimepicker/widgets.md)

### crud_views_widget_typeahead

A server-backed type-ahead single select for large, permission-sensitive model choice sets (thousands of
users), for forms and django-filter filters. It comes as a text typeahead and as a select-style popup. Vanilla
JS, no jQuery, CSP-safe, ARIA combobox.

[Get started](getting_started/typeahead.md) · [Reference](reference/typeahead/lookups.md)

## Install

```bash
pip install django-crud-views-extensions
```

Then follow [Getting started](getting_started/index.md). The [example app](getting_started/example_app.md) shows
every feature in a running project — or try the [live demo](https://django-crud-views-extensions-demo.onrender.com/) (log in as `admin` / `admin`); [Development](development/index.md) covers contributing.
