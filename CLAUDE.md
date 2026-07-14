# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Incubator for **django-crud-views** extension apps. Apps are named as if they already
lived in django-crud-views itself (`crud_views_widget_*`) so a mature app can be lifted
into the main package with **no import changes** for consuming projects. Keep that
constraint in mind: public import paths and settings keys are part of the contract.

Currently ships one app: `crud_views_widget_datetimepicker` (form widgets wrapping the
xdsoft jQuery DateTimePicker).

Depends on `django-crud-views >= 0.11` (the version that introduced the **asset
registry**). During local dev, `[tool.uv.sources]` points at a sibling editable checkout
at `../django-crud-views`; released builds use the PyPI pin in `dependencies`.

## Commands

```bash
uv run pytest                          # full suite (28 tests, ~0.05s)
uv run pytest tests/test_widgets.py    # one file
uv run pytest -k pipeline              # by keyword
uv run ruff check . && uv run ruff format .   # lint + format (line-length 120, double quotes)
```

Tests need **no** `DJANGO_SETTINGS_MODULE`: `tests/conftest.py::pytest_configure` calls
`settings.configure()` directly. It sets `LANGUAGE_CODE="de-de"` and seeds `PIPELINE={}`
(the empty dict matters — it keeps django-pipeline's global `setting_changed` receiver
from interfering; see commit history).

## Architecture

The core design principle is a **single source of truth for asset paths that is
importable without Django**, so the same path list feeds three consumers: the runtime
asset registry, the vendoring command/system-check, and a project's django-pipeline
bundle config (which lives in `settings.py` and must import cleanly at settings-load
time).

- **`assets.py`** — Django-free path logic. `bundle(source, version, cdn_base)` returns
  the `{"js": [...], "css": [...]}` lists to register; `source_files()` gives static
  paths (vendored/pipeline), `cdn_files()` gives CDN URLs. **JS order is load-bearing**:
  jQuery (project-provided) → plugin → `init.js`.

- **`conf.py`** — reads the `CRUD_VIEWS_DATETIMEPICKER` settings dict into a frozen
  `DatetimepickerConfig` dataclass. `SOURCE` is `"cdn"` (default) or `"vendored"`; `LANG`
  falls back to the first segment of `LANGUAGE_CODE`. This is the only module that
  touches `django.conf.settings`.

- **`apps.py::ready()`** — the wiring point. Builds the bundle and calls
  `crud_views.lib.assets.register_assets(key="datetimepicker", ..., emit=cfg.emit)`.
  Assets are page-**global** via `{% cv_js %}`/`{% cv_css %}`, delivered on every page
  including crud-views modals. `emit=False` keeps assets registered but suppresses tag
  output so an external bundler (pipeline) can deliver them instead.

- **`widgets.py`** — `DateTimePickerInput` / `DatePickerInput` / `TimePickerInput`.
  Deliberately **no `Media` class**: widgets only serialize a merged picker config into
  the `xdsoft-datetime-config` HTML attribute. Config merge order (low→high): class
  `defaults` → `lang` → settings `DEFAULTS` → per-field `config`.

- **`static/.../init.js`** — reads `xdsoft-datetime-config` off matching inputs and
  activates pickers. Re-runs on the `cv:modal:loaded` event that crud-views fires after
  injecting modal content (so pickers work inside crud-views modals).

- **`checks.py` / `management/commands/cv_vendor_datetimepicker.py`** — both build a
  `crud_views.lib.vendor.VendorSpec` from config and call `check_vendored` / `vendor`.
  The system check (id namespace `crud_views.*` — E332/E333/W330/W331) warns when
  vendored files are missing or version-mismatched.

## Conventions

- New extension apps follow the `crud_views_widget_*` naming and the same three-consumer
  asset pattern; keep asset-path logic Django-free so it stays importable from
  `settings.py`.
- System-check and asset registry integration reuses `crud_views.lib.*` helpers rather
  than reimplementing them — check what the core package already offers before adding
  infrastructure here.
