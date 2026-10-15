# Vendored mode

By default the plugin files load from jsDelivr. In production you usually want them served from your own
static files instead: no third-party request from your users' browsers (GDPR), no CDN outage, and a simpler
Content Security Policy. Vendored mode is also required for [django-pipeline](pipeline.md).

## Setup

```python
# settings.py
CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored", "VENDOR_DIR": BASE_DIR / "vendored_static"}
STATICFILES_DIRS = [BASE_DIR / "vendored_static"]
```

```bash
python manage.py cv_vendor_datetimepicker
```

## The `cv_vendor_datetimepicker` command

The command takes no options; everything comes from the settings. It downloads all four file variants of the
pinned `VERSION` from `CDN_BASE`:

- `jquery.datetimepicker.full.js`
- `jquery.datetimepicker.full.min.js`
- `jquery.datetimepicker.css`
- `jquery.datetimepicker.min.css`

into `VENDOR_DIR/crud_views_widget_datetimepicker/<VERSION>/` and writes a `.vendored` version stamp next to
them. It fails with a `CommandError` when `VENDOR_DIR` is not set.

Re-run the command after changing `VERSION`. Either commit the vendored directory or run the command as part
of your deployment build, before `collectstatic`.

## Checks

On startup, [system checks](checks.md) report a missing `VENDOR_DIR` (`crud_views.E332`), missing vendored
files (`crud_views.W330`) and files that don't match the pinned `VERSION` (`crud_views.W331`).
