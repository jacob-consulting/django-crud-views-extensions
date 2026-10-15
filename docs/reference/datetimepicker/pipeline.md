# django-pipeline

CDN mode cannot be bundled. For [django-pipeline](https://django-pipeline.readthedocs.io/), use
[vendored mode](vendored.md), build your bundle from the same path list the app uses internally, and switch off
the app's own tag output with `EMIT: False`:

```python
# settings.py (BASE_DIR as defined by Django's project template)
from crud_views_widget_datetimepicker.assets import source_files

_dtp = source_files("2.5.21", minified=False)   # pipeline minifies itself
PIPELINE = {
    "JAVASCRIPT": {
        "main": {
            "source_filenames": ["js/jquery.min.js", *_dtp["js"]],  # jQuery first
            "output_filename": "js/main.js",
        }
    },
    "STYLESHEETS": {"main": {"source_filenames": [*_dtp["css"]], "output_filename": "css/main.css"}},
}
CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored", "VENDOR_DIR": BASE_DIR / "vendored_static", "EMIT": False}
```

## Path functions

`crud_views_widget_datetimepicker.assets` is Django-free, so it can be imported from `settings.py`. It is the
single source of truth for the asset paths: the app's own asset registration, the vendoring command and
your pipeline config all use it.

### `source_files(version, minified=True)`

Static paths for vendored mode / pipeline `source_filenames`:

```python
{
    "js": [
        "crud_views_widget_datetimepicker/2.5.21/jquery.datetimepicker.full.min.js",
        "crud_views_widget_datetimepicker/init.js",
    ],
    "css": ["crud_views_widget_datetimepicker/2.5.21/jquery.datetimepicker.min.css"],
}
```

With `minified=False`: `jquery.datetimepicker.full.js` and `jquery.datetimepicker.css`.

### `cdn_files(cdn_base, version, minified=True)`

The CDN URLs of the plugin files only (`init.js` is always a static file).

### `bundle(source, version, cdn_base, minified=True)`

What the app registers at startup: the CDN plugin files plus the static `init.js` for `"cdn"`, otherwise
`source_files(...)`.

!!! note "Load order"
    Keep the order jQuery → plugin → `init.js` in your bundle. `source_files()` already returns the plugin
    before `init.js`; jQuery is yours to include first.
