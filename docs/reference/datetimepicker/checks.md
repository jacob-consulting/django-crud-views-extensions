# System checks

The app registers a system check under the `crud_views` tag
(`python manage.py check --tag crud_views`).

| ID | Level | When | Fix |
|---|---|---|---|
| `crud_views.E333` | Error | `SOURCE` is neither `"cdn"` nor `"vendored"` | set `SOURCE` to `"cdn"` or `"vendored"` |
| `crud_views.E332` | Error | `SOURCE` is `"vendored"` but `VENDOR_DIR` is not set | set `VENDOR_DIR` and list it in `STATICFILES_DIRS` |
| `crud_views.W330` | Warning | vendored mode, but no vendored files found | run `python manage.py cv_vendor_datetimepicker` |
| `crud_views.W331` | Warning | the vendored files' version stamp doesn't match `VERSION` | re-run `python manage.py cv_vendor_datetimepicker` |

`E333` is checked in every mode; the others only in [vendored mode](vendored.md).

## crud_views.E333

> CRUD_VIEWS_DATETIMEPICKER['SOURCE'] must be 'cdn' or 'vendored'.

## crud_views.E332

> CRUD_VIEWS_DATETIMEPICKER: SOURCE is 'vendored' but VENDOR_DIR is not set.

Set `VENDOR_DIR` to a project directory that is listed in `STATICFILES_DIRS`.

## crud_views.W330

> crud_views asset bundle 'datetimepicker' is configured as vendored, but no vendored files were found at
> `<VENDOR_DIR>/crud_views_widget_datetimepicker/<VERSION>`.

The check looks for the `.vendored` stamp the command writes. Files live in a directory per version, so you
also see this warning right after changing `VERSION`. Run the vendor command.

## crud_views.W331

> crud_views asset bundle 'datetimepicker': vendored version '…' does not match configured version '…'.

The stamp in the version directory names another version, e.g. after files were copied in by hand. Re-run
the vendor command.

`W330` and `W331` come from django-crud-views core (`crud_views.lib.vendor.check_vendored`), which this app's
check calls; `E332` and `E333` are this app's own.
