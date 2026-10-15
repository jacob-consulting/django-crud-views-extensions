# Settings

All settings live in one optional dict:

```python
CRUD_VIEWS_TYPEAHEAD = {
    "EMIT": True,
    "TEMPLATE": "crud_views_widget_typeahead/typeahead.html",
    "DEBOUNCE_MS": 250,
    "SELECT_EMIT": True,
    "SELECT_TEMPLATE": "crud_views_widget_typeahead/typeahead_select.html",
}
```

| Key | Default | Meaning |
|---|---|---|
| `EMIT` | `True` | `False` suppresses the text typeahead's `{% cv_js %}` / `{% cv_css %}` output ([skins](skins.md), [django-pipeline](pipeline.md)) |
| `TEMPLATE` | `"crud_views_widget_typeahead/typeahead.html"` | text typeahead template |
| `DEBOUNCE_MS` | `250` | input debounce in milliseconds; applies to both widgets |
| `SELECT_EMIT` | `True` | `False` suppresses the select popup's `{% cv_js %}` / `{% cv_css %}` output |
| `SELECT_TEMPLATE` | `"crud_views_widget_typeahead/typeahead_select.html"` | select popup template |

The two widgets are separate asset bundles (`typeahead` and `typeahead_select`), so a skin can replace one
without touching the other. `EMIT` and `SELECT_EMIT` are read once at startup; the templates and
`DEBOUNCE_MS` every time a widget renders.
