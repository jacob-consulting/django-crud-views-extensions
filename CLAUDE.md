# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Incubator for **django-crud-views** extension apps. Apps are named as if they already
lived in django-crud-views itself (`crud_views_widget_*`) so a mature app can be lifted
into the main package with **no import changes** for consuming projects. Keep that
constraint in mind: public import paths and settings keys are part of the contract.

Currently ships two apps: `crud_views_widget_datetimepicker` (form widgets wrapping the
xdsoft jQuery DateTimePicker) and `crud_views_widget_typeahead` (server-backed type-ahead
select: lookup registry, signed tokens, one JSON endpoint, vanilla JS).

Depends on `django-crud-views >= 0.29` (the **asset registry** arrived in 0.11). There
is no `[tool.uv.sources]` override: local dev and CI both resolve django-crud-views from
PyPI via `uv.lock`. To test against an unreleased sibling checkout, temporarily install
it editable (`uv pip install -e ../django-crud-views`).

## Commands

```bash
uv run pytest                          # full suite (223 tests, ~0.46s)
uv run pytest tests/test_widgets.py    # one file
uv run pytest -k pipeline              # by keyword
uv run ruff check . && uv run ruff format .   # lint + format (line-length 120, double quotes)
uv run --no-project --with-requirements docs/requirements.txt mkdocs serve -a localhost:8001   # docs preview
uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict            # docs build (CI)
```

### Docs

MkDocs site on Read the Docs (`mkdocs.yml`, `.readthedocs.yaml`), `readthedocs` theme, nav order via
awesome-pages `.pages` files. User documentation lives in `docs/` (getting_started, reference per app,
development); the README is only an overview linking there. `docs/superpowers/` and `docs/requirements.*` are
excluded via `exclude_docs`. Build deps are hash-locked: edit `docs/requirements.in`, then
`uv pip compile --universal --generate-hashes --python-version 3.12 docs/requirements.in -o docs/requirements.txt`.
The definition-list extension is not enabled: use `###` subheadings, not `term\n:   text`.

### Example app

```bash
cd examples/bootstrap5 && task run     # migrate + seed (admin/admin) + runserver
cd examples/bootstrap5 && uv run pytest
```

Lives in the repo's uv env (no own pyproject). Root `uv run pytest` does **not** collect it
(`testpaths = ["tests"]`); CI runs it as a separate step. New `crud_views_widget_*` apps
add one example app plus `Feature` entries in `project/features.py` (matched to pages by
`Feature.viewset`). Each `Feature.docs` lists `DocRef`s rendered under "References to documentation" (a test checks
every page and anchor exists in `docs/`); the matching docs pages carry a `!!! example "Try it live"` box linking the
demo page. "The code behind this page" renders `SNIPPET_FILES` of `Feature.app` with pygments.

The public demo on Render runs this app with `project.settings_demo` (`render.yaml`, `requirements/demo.txt`,
`.github/workflows/demo.yml`; see `docs/development/demo.md`). Demo-only middleware (`boot.py`, `ratelimit.py`) is
installed by `settings_demo` only, so the example's tests never import gunicorn/whitenoise/django-ratelimit.

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
  falls back to the first segment of `LANGUAGE_CODE` (`lang_explicit` records whether it
  was set; widgets otherwise use the active request language). This is the only module that
  touches `django.conf.settings`.

- **`apps.py::ready()`** — the wiring point. Builds the bundle and calls
  `crud_views.lib.assets.register_assets(key="datetimepicker", ..., emit=cfg.emit)`.
  Assets are page-**global** via `{% cv_js %}`/`{% cv_css %}`, delivered on every page
  including crud-views modals. `emit=False` keeps assets registered but suppresses tag
  output so an external bundler (pipeline) can deliver them instead.

- **`widgets.py`** — `DateTimePickerInput` / `DatePickerInput` / `TimePickerInput`.
  Deliberately **no `Media` class**: widgets only serialize a merged picker config into
  the `xdsoft-datetime-config` HTML attribute, **at render time** (per request). Config
  merge order (low→high): class `defaults` → `lang` → settings `DEFAULTS` → per-field
  `config`. Unless pinned, `format` is derived from the active locale's `*_INPUT_FORMATS`
  via `formats.py` (strftime ↔ PHP tokens `d m Y y H i s`), and the widget renders and
  parses values with that same format — the invariant is "what the picker writes, the
  form accepts" in every locale.

- **`static/.../init.js`** — reads `xdsoft-datetime-config` off matching inputs and
  activates pickers. Re-runs on the `cv:modal:loaded` event that crud-views fires after
  injecting modal content (so pickers work inside crud-views modals).

- **`checks.py` / `management/commands/cv_vendor_datetimepicker.py`** — both build a
  `crud_views.lib.vendor.VendorSpec` from config and call `check_vendored` / `vendor`.
  The system check (id namespace `crud_views.*` — E332/E333/W330/W331) warns when
  vendored files are missing or version-mismatched.

### crud_views_widget_typeahead

- **`lookups.py`** — `TypeaheadLookup` (allowed set + permission in `get_queryset(request, **params)`,
  multi-word `icontains` search, labels) and a name registry; `register_user_lookup` wraps a function.
  `apps.py::ready()` autodiscovers every app's `typeahead.py`.
- **`tokens.py`** — `signing.dumps({"l": name, "p": params})`, salt `crud_views.typeahead`, **no expiry**:
  permission is re-checked per request, so the browser can neither change scope nor needs fresh tokens.
- **`views.py`** — the single endpoint; JSON errors only (never a login redirect — `fetch` must get JSON). Optional
  1-based `page` (page size = `max_results`); `_with_pk_tiebreaker()` appends `pk` to the lookup's ordering so OFFSET
  paging never repeats or skips rows.
- **`fields.py` / `filters.py`** — `bind(request, **params)` is the single source of truth: it sets the
  queryset validation uses and the token the endpoint uses. `TypeaheadBinding` is frozen plain data
  because `Widget.__deepcopy__` is shallow. FilterSets that bind in `__init__` need
  `do_not_call_in_templates = True` under crud_views (its list template evaluates `view.filterset_class`).
- **`widgets.py`** — visible input has no `name`; hidden input carries the pk; `aria-describedby` is merged
  with Django's ids at render time (never set on `widget.attrs`, or Django drops its own).
- **`static/.../typeahead.js`** — vanilla, no `innerHTML`; the skin contract is documented in `docs/reference/typeahead/skins.md`.
  No CDN/vendor machinery: there is no third-party plugin.
- **`TypeaheadSelect`** (`widgets.py`) + `typeahead_select.html` + `static/.../typeahead-select.js`/`.css` — the
  select popup: trigger button, popup with search field and scroll-paged list, rendered inside the widget (a
  body-level dropdown breaks under crud_views' Bootstrap 5 modal). Own asset bundle `typeahead_select` and own
  settings `SELECT_EMIT`/`SELECT_TEMPLATE`, so a text-typeahead skin never touches it. Self-contained JS on purpose
  (helpers duplicated from `typeahead.js`, not shared).
- Tests: `tests/testapp/typeahead.py` holds the test lookups (autodiscovered); `tests/urls.py` mounts the
  endpoint at `/typeahead/`.

## Conventions

- New extension apps follow the `crud_views_widget_*` naming and the same three-consumer
  asset pattern; keep asset-path logic Django-free so it stays importable from
  `settings.py`.
- System-check and asset registry integration reuses `crud_views.lib.*` helpers rather
  than reimplementing them — check what the core package already offers before adding
  infrastructure here.
- A Claude Code skill for this package lives in the sibling marketplace repo
  `../skills/plugins/django-crud-views-extensions/` (released separately). A release that changes public API,
  settings or checks also updates that skill — see `docs/development/releasing.md#claude-code-skill`.
