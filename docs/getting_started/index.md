# Getting started

## Install

```bash
pip install django-crud-views-extensions
# or
uv add django-crud-views-extensions
```

Add the apps you want after django-crud-views:

```python
INSTALLED_APPS = [
    # ...
    "crud_views.apps.CrudViewsConfig",
    "crud_views_widget_datetimepicker.apps.CrudViewsWidgetDatetimepickerConfig",
    "crud_views_widget_typeahead.apps.CrudViewsWidgetTypeaheadConfig",
]
```

The short forms `"crud_views_widget_datetimepicker"` and `"crud_views_widget_typeahead"` work as well.

## Assets

The widgets have no `Media` class. Both apps register their JavaScript and CSS with the django-crud-views asset
registry, so the `{% cv_css %}` and `{% cv_js %}` tags you already have in your base template deliver them on
every page, including content loaded into crud-views modals.

!!! note
    The datetimepicker is a jQuery plugin: load jQuery before `{% cv_js %}` (the same rule as django-crud-views
    core). The typeahead needs no jQuery.

## URLs

The typeahead needs its JSON endpoint mounted, under any prefix:

```python
urlpatterns += [path("_typeahead/", include("crud_views_widget_typeahead.urls"))]
```

See [Endpoint](../reference/typeahead/endpoint.md). The datetimepicker needs no URLs.

## Next

- [Your first datetimepicker](datetimepicker.md)
- [Your first typeahead](typeahead.md)
- [The example app](example_app.md) shows both in a running project
