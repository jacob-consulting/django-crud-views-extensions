# django-pipeline

The typeahead has no third-party plugin, so there is nothing to vendor and no CDN mode. Add its static files
to your bundle and switch off the app's own tag output:

```python
from crud_views_widget_typeahead.assets import select_source_files, source_files

_ta = source_files()
_tas = select_source_files()  # only if you use TypeaheadSelect
PIPELINE = {
    "JAVASCRIPT": {"main": {"source_filenames": [..., *_ta["js"], *_tas["js"]], ...}},
    "STYLESHEETS": {"main": {"source_filenames": [..., *_ta["css"], *_tas["css"]], ...}},
}
CRUD_VIEWS_TYPEAHEAD = {"EMIT": False, "SELECT_EMIT": False}
```

`crud_views_widget_typeahead.assets` is Django-free, so it can be imported from `settings.py`.

| Function | Returns |
|---|---|
| `source_files()` | `{"js": ["crud_views_widget_typeahead/typeahead.js"], "css": ["crud_views_widget_typeahead/typeahead.css"]}` |
| `select_source_files()` | `{"js": ["crud_views_widget_typeahead/typeahead-select.js"], "css": ["crud_views_widget_typeahead/typeahead-select.css"]}` |
| `bundle()`, `select_bundle()` | what the app registers at startup (the same lists) |
