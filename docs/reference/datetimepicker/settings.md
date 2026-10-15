# Settings

All settings live in one optional dict:

```python
CRUD_VIEWS_DATETIMEPICKER = {
    "SOURCE": "cdn",        # "cdn" (default) | "vendored"
    "VERSION": "2.5.21",    # pinned upstream version, used by both modes
    "CDN_BASE": "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/",
    "VENDOR_DIR": None,     # required for vendored mode; must be on STATICFILES_DIRS
    "EMIT": True,           # False: keep registered but let a bundler deliver the files
    "LANG": None,           # None: the active request language
    "DEFAULTS": {},         # merged into every widget's picker config
}
```

| Key | Default | Meaning |
|---|---|---|
| `SOURCE` | `"cdn"` | `"cdn"` or `"vendored"` ([vendored mode](vendored.md)); anything else raises [`crud_views.E333`](checks.md) |
| `VERSION` | `"2.5.21"` | pinned upstream jquery-datetimepicker version, used by both modes |
| `CDN_BASE` | `"https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/"` | CDN URL template; `{version}` is replaced with `VERSION`. Also the download source of [vendored mode](vendored.md) |
| `VENDOR_DIR` | `None` | required for vendored mode; must be listed in `STATICFILES_DIRS` |
| `EMIT` | `True` | `False` keeps the assets registered but suppresses their `{% cv_js %}` / `{% cv_css %}` output, so a bundler can deliver them ([django-pipeline](pipeline.md)) |
| `LANG` | `None` | picker language; `None` means the active request language ([language](formats.md#language)) |
| `DEFAULTS` | `{}` | merged into every widget's picker config ([merge order](widgets.md#config-merge-order)) |

`SOURCE`, `VERSION`, `CDN_BASE` and `EMIT` are read once at startup, when the app registers its assets.
`LANG` and `DEFAULTS` are read every time a widget renders.
