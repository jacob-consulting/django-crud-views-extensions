# Adding an extension app

New apps follow the pattern of the existing two. The datetimepicker is the complete example, including a
third-party plugin with CDN and vendored modes.

## Naming

- Package: `crud_views_widget_<name>`.
- Settings: one dict, `CRUD_VIEWS_<NAME>`.
- Asset registry key: `<name>`.

Public import paths and settings keys are the contract: once an app is mature it moves into django-crud-views
under the same names, so consuming projects change nothing.

## Module roles

### `assets.py` — **Django-free** asset paths

The single source of truth for the app's static paths. It must import without Django, because one path
list feeds three consumers:

1. the runtime asset registry (`apps.py`),
2. the vendoring command and system check (only if there is a third-party plugin),
3. a project's django-pipeline config, which lives in `settings.py` and imports at settings-load time.

See [datetimepicker: django-pipeline](../reference/datetimepicker/pipeline.md) for the result.

### `conf.py` — settings

The only module that reads `django.conf.settings`: it turns the settings dict into a frozen dataclass.

### `apps.py` — wiring

`ready()` builds the bundle from `assets.py` and calls
`crud_views.lib.assets.register_assets(key=..., js=..., css=..., emit=cfg.emit)`. Assets are page-global
via `{% cv_js %}` / `{% cv_css %}`; `emit=False` keeps them registered but lets a bundler deliver them.

### Widgets

No `Media` class. Pass per-widget configuration to the JS through HTML attributes rendered per request.
The JS re-initialises on the `cv:modal:loaded` event so widgets work in crud-views modals.

### Vendoring and checks

Reuse `crud_views.lib.vendor` (`VendorSpec`, `vendor`, `check_vendored`) instead of writing your own.
System check IDs live in the `crud_views.*` namespace.

Before adding infrastructure, check what `crud_views.lib.*` already offers.

## Checklist

1. The package under `src/`, added to `[tool.hatch.build.targets.wheel] packages` and
   `[tool.coverage.run] source` in `pyproject.toml`, and to the `--cov` flags in `.github/workflows/tests.yml`
   and `.github/workflows/publish.yml`.
2. Tests under `tests/`.
3. An example app under `examples/bootstrap5/<app>/`, plus `Feature` entries in
   `examples/bootstrap5/project/features.py` (matched to pages by `Feature.viewset`).
4. Documentation: a getting-started walkthrough under `docs/getting_started/` and reference pages under
   `docs/reference/<app>/`, each listed in the `.pages` files and in `docs/reference/index.md`.
5. A section in the README linking to the documentation.
