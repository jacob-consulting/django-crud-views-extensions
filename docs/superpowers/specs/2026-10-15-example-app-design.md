# Example app for django-crud-views-extensions — design

Date: 2026-10-15
Status: approved in brainstorming, pending spec review

## Goal

Add a local-only example Django project to this repo that shows real use cases for the
`crud_views_widget_*` extensions, modelled on `../django-crud-views/examples/bootstrap5`.

It serves two audiences:

- **Adopters** — a showcase with one feature card per use case, each with an "about"
  paragraph and a pointer to the code behind it.
- **Extension developers** — the place to click-test a widget in a real browser
  (forms, modals, filters, locales) while building it, including future extensions such
  as the typeahead widget.

Out of scope: any deployment (no Render, no `settings_demo.py`), JS/browser tests,
example-specific translation catalogs.

## Prerequisite (separate task, ships first)

The datetimepicker widgets hardcode the picker display format (`d.m.Y`,
`d.m.Y H:i:s`, `H:i`) while Django's render/parse formats follow the active locale.
Verified on 2026-10-15:

| Active language | Django renders | Picker writes | Form accepts picker value |
|---|---|---|---|
| `de` | `15.10.2026` | `15.10.2026` | yes |
| `en` | `2026-10-15` | `15.10.2026` | no ("Enter a valid date.") |

`TimePickerInput` mismatches in every language: Django renders `18:30:00`
(`TIME_INPUT_FORMATS[0]`), the picker format is `H:i`.

Also, `LANG` falls back to the `LANGUAGE_CODE` *setting* at widget construction, not to
the per-request active language.

A per-field `lang` is deliberately not demonstrated: the plugin's `setLocale` is
page-global, so one such field would switch every picker on the page.

This is fixed in `crud_views_widget_datetimepicker` as its own bounded task (short
design + approval, tests under `en-us` and `de-de`) before the example is built. The
example's tests include a regression check for it.

## Approach

**A — `examples/bootstrap5/` inside this repo, running in the repo's uv environment**
(chosen over a separate uv project and over a single flat project).

- The example's `taskfile.yaml` runs `uv run manage.py …`; uv resolves the root
  `pyproject.toml`, so the example always runs the editable `src/` code.
- django-crud-views already depends on django-filter, django-tables2,
  django-bootstrap5, django-crispy-forms and crispy-bootstrap5, so no new dependency
  is needed initially. An `example` optional extra is added only if a later
  dependency requires one.

## Layout

```
examples/bootstrap5/
  manage.py
  pytest.ini                 # DJANGO_SETTINGS_MODULE=project.settings, pythonpath=.
  taskfile.yaml              # run / seed / test / shell
  project/
    settings.py
    urls.py
    views.py                 # HomeView
    features.py              # FeatureGroup / Feature registry
    context_processors.py
    seeding.py
    management/commands/seed.py
    templates/project/       # base.html, crud_views.html, nav.html, home.html, example_about.html
    tests.py
  datetimepicker/            # one feature app per crud_views_widget_* extension
    models.py forms.py views.py urls.py seed.py tests.py apps.py migrations/
```

### `project/`

- **settings.py** — trimmed from upstream: no guardian, fsm, polymorphic,
  ordered_model or workflow apps; no demo mode. `crud_views_object_detail` *is*
  installed (ships inside django-crud-views; the Event detail view and the table's
  detail link need it). Installs `crud_views`,
  `crud_views_widget_datetimepicker`, `project`, `datetimepicker`. `LANGUAGES` = en, de
  with `LocaleMiddleware`. SQLite at `BASE_DIR / "db.sqlite3"`.
  `CRUD_VIEWS_DATETIMEPICKER = {"DEFAULTS": {"dayOfWeekStart": 1}}` (default CDN source).
- **urls.py** — home, `i18n/`, login/logout (crispy auth form as upstream), admin, then
  one `include()` per feature app.
- **features.py** — upstream's `FeatureGroup`/`Feature` dataclasses minus `DocRef`
  (no Read the Docs site for this package; cards link to the README instead).
- **templates/project/base.html** — from upstream: Bootstrap 5, jQuery 3.7.1 from
  code.jquery.com, Font Awesome, then `{% cv_css %}` / `{% cv_js %}` (the route by which
  the picker assets reach every page, modals included). Language switcher in the nav.
- **seed** — idempotent; creates an `admin`/`admin` superuser and calls each feature
  app's `seed.py`.

Not carried over from upstream: `settings_demo.py`, `urls_demo.py`, `boot.py`,
`ratelimit.py`, `render.yaml`, docs-sync and doc-link tests.

### `datetimepicker/` feature app

All views use the `PermissionRequired` view variants; the seeded superuser can do
everything.

**`Event`** — everyday use cases. Fields: `title`, `day` (DateField), `doors_open`
(TimeField), `starts_at` (DateTimeField), `ends_at` (DateTimeField, optional).

- `EventForm` — `DatePickerInput`, `TimePickerInput`, `DateTimePickerInput`.
  `clean()` rejects `ends_at <= starts_at` to demonstrate re-rendering after a
  validation error.
- ViewSet `event`: list (table + filter), detail, create, update (full page), a
  "Quick edit" view with `cv_modal = True` reached from the list row actions, and
  delete (modal). Quick edit is a `CustomFormViewPermissionRequired` editing the
  instance with `EventForm`: in django-crud-views 0.29 `UpdateView` does not support
  modals (`cv_modal_supported = False`).
- `EventFilter` — `day_from` / `day_to` (`DateFilter`, `gte`/`lte`,
  `widget=DatePickerInput()`) and `starts_after` (`DateTimeFilter`,
  `DateTimePickerInput`).
- Seed: ~12 events spread over a few months.

**`PickerVariant`** — per-field config, one field per variant:

| Field | Widget |
|---|---|
| `this_year` | `DateTimePickerInput(fix_year=<current year>)` |
| `quarter_hour` | `TimePickerInput(config={"step": 15})` |
| `no_past` | `DatePickerInput(config={"minDate": 0})` |
| `weekdays_only` | `DatePickerInput(config={"disabledWeekDays": [0, 6]})` |
| `inline_calendar` | `DatePickerInput(config={"inline": True})` |
| `fixed_times` | `TimePickerInput(config={"allowTimes": ["09:00", "12:00", "15:00"]})` |

ViewSet `variant`: list, create, update, delete. The about panel explains the merge
order: class defaults → `LANG` → settings `DEFAULTS` → per-field `config`.

**features.py entries** — group "Widgets" with two cards:
"Datetimepicker: forms, modals & filters" (landing: event list) and
"Datetimepicker: per-field config" (landing: variant list).

## Root repo changes

- `pyproject.toml`: `[tool.pytest.ini_options] testpaths = ["tests"]` so the root
  suite does not collect the example.
- `.gitignore`: `examples/**/db.sqlite3`.
- `README.md` and `CLAUDE.md`: an "Example app" section (`cd examples/bootstrap5 &&
  task run`, login admin/admin).
- `.github/workflows/tests.yml`: an extra step
  `cd examples/bootstrap5 && uv run --no-sources --extra dev pytest`. Coverage upload
  stays with the root suite. Lint already covers `examples/`.

## Testing

Example tests (pytest-django, run via `task test` from `examples/bootstrap5`):

- `project/tests.py` — home renders all feature cards; every `Feature.url_name` resolves
  and returns 200 logged in, redirects to login when anonymous; `seed` is idempotent.
- `datetimepicker/tests.py`:
  - `{% cv_js %}` output contains the xdsoft CDN script and `init.js`;
  - event create/update pages and the quick-edit modal fragment render inputs with
    `xdsoft-datetime-config`;
  - a POST in the picker's format is accepted under both `en` and `de` (regression check
    for the prerequisite);
  - `ends_at <= starts_at` re-renders with an error and submitted values intact;
  - the filter narrows by `day_from` / `day_to`;
  - each `PickerVariant` field's JSON config contains its override, and
    `dayOfWeekStart` from the settings `DEFAULTS`.

Manual: one click-through in a real browser before declaring done — every page, picker
opens, modal, filters, language switch.

## Order of work

1. Prerequisite: datetimepicker locale/format fix (separate bounded task).
2. Example skeleton + root repo changes.
3. `datetimepicker` feature app + tests.
4. CI step + manual browser pass.
