# MkDocs documentation on Read the Docs — design

Date: 2026-10-15

## Goal

Give `django-crud-views-extensions` a documentation site built with MkDocs and hosted on Read the Docs,
set up the same way as the sibling project `../django-crud-views`. All user documentation currently lives
in `README.md` (~250 lines); it moves into the docs and is expanded with reference material that today
exists only in code, `CLAUDE.md`, or git history. The README shrinks to an overview that links to the site.

Success criteria:

- `mkdocs build --strict` passes locally, in a new Docs CI workflow, and as a gate in the Publish workflow.
- Read the Docs builds the site from `.readthedocs.yaml` once the project is imported.
- Every fact in the README is present in the docs; nothing in the docs contradicts the code.
- The README is ~50–60 lines: badges, pitch, per-app summary with minimal install snippet, links to the site.

Out of scope: API autodoc (mkdocstrings), Material theme, FAQ page, screenshots, translated docs,
a `cv-sync` style snippet-sync check.

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Tooling | Copy of the sibling: `readthedocs` theme, `search` + `awesome-pages`, `admonition`, `.pages` nav files | User asked for the sibling's setup |
| Content scope | Migrate README and expand | User choice |
| README | Short overview + links | User choice; avoids writing settings/skins/endpoint docs twice |
| `docs/superpowers/` | Stays; excluded via `exclude_docs: superpowers/` | One line vs. moving 20+ files and breaking paths in old plans |
| Local preview | `uv run --no-project --with-requirements docs/requirements.txt mkdocs serve -a localhost:8001` | No root Taskfile in this repo; not adding one for a single command |
| RTD project | Imported manually by the user on readthedocs.org, slug `django-crud-views-extensions` | Cannot be done from the repo |

## Tooling and infrastructure

### `mkdocs.yml` (repo root)

```yaml
site_name: Django CRUD Views Extensions
theme: readthedocs
plugins:
    - search
    - awesome-pages
repo_url: https://github.com/jacob-consulting/django-crud-views-extensions
edit_uri: blob/main/docs/

exclude_docs: |
    superpowers/
    requirements.*

markdown_extensions:
    - admonition

validation:
    anchors: warn
```

Differences from the sibling: `edit_uri` uses `main` (the sibling's `master` is wrong for this repo's
default branch) and `exclude_docs` keeps the specs/plans and the docs requirements files out of the site.

### `docs/requirements.in` / `docs/requirements.txt`

`requirements.in` has the sibling's header comment and three pins:

```
mkdocs>=1.6.1
mkdocs-awesome-pages-plugin>=2.10.1
mkdocs-get-deps>=0.2.0
```

`requirements.txt` is the hash-locked output of
`uv pip compile --universal --generate-hashes --python-version 3.12 docs/requirements.in -o docs/requirements.txt`.

### `.readthedocs.yaml` (repo root)

Identical to the sibling: config version 2, `build.os: ubuntu-24.04`, `build.tools.python: "3.12"`,
`mkdocs.configuration: mkdocs.yml`, `python.install: [requirements: docs/requirements.txt]`.

### CI

The repo's existing workflows use `actions/checkout@v5` and `astral-sh/setup-uv`; the docs job follows that
style rather than the sibling's `setup-python` + `pip`:

```yaml
docs:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v5
    - uses: astral-sh/setup-uv@v8.3.2
      with:
        python-version: "3.13"
        enable-cache: true
    - run: uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict
```

uv verifies the hashes in `docs/requirements.txt` when installing from it.

- New `.github/workflows/docs.yml` (name `Docs`): triggers on `pull_request` to `main`, `push` to `main`,
  and `v*` tags; contains the job above.
- `.github/workflows/publish.yml`: add the same `docs` job; `publish.needs` becomes `[tests, docs, lint]`.

## Page structure

Nav order is set by `.pages` files (awesome-pages), as in the sibling.

```
docs/
├── .pages                      # Home: index.md · getting_started · reference · development
├── index.md
├── getting_started/
│   ├── .pages
│   ├── index.md
│   ├── datetimepicker.md
│   ├── typeahead.md
│   └── example_app.md
├── reference/
│   ├── .pages                  # index.md · Datetimepicker: datetimepicker · Typeahead: typeahead
│   ├── index.md
│   ├── datetimepicker/
│   │   ├── .pages
│   │   ├── widgets.md
│   │   ├── formats.md
│   │   ├── settings.md
│   │   ├── vendored.md
│   │   ├── pipeline.md
│   │   └── checks.md
│   └── typeahead/
│       ├── .pages
│       ├── lookups.md
│       ├── fields_filters.md
│       ├── widgets.md
│       ├── endpoint.md
│       ├── security.md
│       ├── settings.md
│       ├── skins.md
│       └── pipeline.md
└── development/
    ├── .pages
    ├── index.md
    ├── new_extension.md
    └── releasing.md
```

## Page content

Each page is written from the code (`src/`, `examples/bootstrap5/`), using the README as a starting point.
Source references in parentheses.

### `index.md`

Incubator pitch; the naming contract (`crud_views_widget_*`, public import paths and settings keys are
stable so an app can move into django-crud-views without import changes); requirements (Python ≥ 3.12,
django-crud-views ≥ 0.29); one paragraph + link per app; link to the example app.

### Getting started

- `index.md` — `pip install django-crud-views-extensions`; `INSTALLED_APPS` for each app; assets arrive via
  `{% cv_js %}` / `{% cv_css %}` (asset registry, page-global, works in crud-views modals); jQuery
  prerequisite for the datetimepicker only.
- `datetimepicker.md` — a model form with `DateTimePickerInput`, rendering, submitting; points to formats
  and vendored mode for production.
- `typeahead.md` — mount the URL; write a lookup in `typeahead.py`; bind a form field and a filter;
  switch to `TypeaheadSelect`. Mirrors the example app's teams/tasks pages.
- `example_app.md` — what `examples/bootstrap5/` contains (one page per `Feature` in
  `project/features.py`), `task run` / `task test`, the no-Task fallback commands, login `admin/admin`.

### Reference — datetimepicker

- `widgets.md` — `DateTimePickerInput`, `DatePickerInput`, `TimePickerInput`; `config=`, `fix_year=`,
  Django `format=`; no `Media` class, config serialised into the `xdsoft-datetime-config` attribute at
  render time; merge order class defaults → `lang` → settings `DEFAULTS` → per-field `config`
  (`widgets.py`); `init.js` re-runs on `cv:modal:loaded`.
- `formats.md` — locale-derived formats from `*_INPUT_FORMATS`, preference for formats without seconds,
  the "what the picker writes, the form accepts" invariant, pinning a format, token table strftime ↔ PHP
  (`d m Y y H i s`, from `formats.py`), picker language and its page-global nature.
- `settings.md` — table of every `CRUD_VIEWS_DATETIMEPICKER` key with default and meaning (`conf.py`).
- `vendored.md` — CDN vs vendored, `VENDOR_DIR` + `STATICFILES_DIRS`, `cv_vendor_datetimepicker` command
  (no options; downloads the pinned `VERSION` into `VENDOR_DIR`), GDPR rationale.
- `pipeline.md` — `source_files()` / `cdn_files()` / `bundle()` (`assets.py`, Django-free, importable from
  `settings.py`), `EMIT=False`, load order jQuery → plugin → `init.js`.
- `checks.md` — `crud_views.E333` (bad `SOURCE`) and `E332` (vendored without `VENDOR_DIR`) from
  `checks.py`; `W330` (files missing) and `W331` (version mismatch) from core's
  `crud_views.lib.vendor.check_vendored`: message, cause, fix.

### Reference — typeahead

- `lookups.md` — `TypeaheadLookup` attributes (`search_fields`, `ordering`, `max_results`, `min_chars`,
  `login_required`), `get_queryset(request, **params)`, `label(obj)`; `register_lookup`,
  `register_user_lookup` (incl. `base=`); multi-word `icontains` search; pk-only values;
  autodiscovery of `typeahead.py` (`lookups.py`, `apps.py`).
- `fields_filters.md` — `TypeaheadField`, `TypeaheadFilter`, `bind(request, **params)` as the single source
  of truth for queryset and token, JSON-only params, unbound → `ImproperlyConfigured`, `cv_view.request`
  with `CrispyModelForm`, `do_not_call_in_templates = True` and why (`fields.py`, `filters.py`).
- `widgets.md` — text typeahead vs `TypeaheadSelect`; `submit_on_clear`; keyboard behaviour of each;
  `min_chars = 0` behaviour; modals, clipping by `overflow: hidden` / `modal-dialog-scrollable`;
  `window.cvTypeahead.init(container)` / `window.cvTypeaheadSelect.init(container)` for dynamic content
  (`widgets.py`, static JS).
- `endpoint.md` — `GET <mount>/?t=&q=&page=`, response shape with example JSON, `count` before
  truncation, 1-based paging with pk tiebreaker, error codes 400/403/404/405 with example bodies,
  short terms (`views.py`).
- `security.md` — signed tokens (salt `crud_views.typeahead`, payload `{l, p}`), no expiry and why
  (permission re-checked on every request; the browser cannot change scope), JSON errors instead of login
  redirects (`tokens.py`, `views.py`).
- `settings.md` — table of the five `CRUD_VIEWS_TYPEAHEAD` keys (`conf.py`).
- `skins.md` — text typeahead and select popup skin contracts: template context keys, i18n keys,
  registering own assets with `EMIT` / `SELECT_EMIT = False`, the hidden-input contract and required
  behaviours as checklists.
- `pipeline.md` — `source_files()` / `select_source_files()` (Django-free `assets.py`; `bundle()` /
  `select_bundle()` are what `apps.py` registers), `EMIT` / `SELECT_EMIT`.

### Development

- `index.md` — clone, `uv sync --extra dev`, `uv run pytest`, `ruff`, example app tests (not collected by
  the root run), test settings via `tests/conftest.py`, local docs preview command.
- `new_extension.md` — adding a `crud_views_widget_*` app: naming contract; Django-free `assets.py`
  feeding three consumers (asset registry, vendoring/checks, pipeline); `conf.py` as the only settings
  reader; `register_assets` in `apps.py::ready()`; reuse `crud_views.lib.*` helpers; add an example page
  plus `Feature` entries; add the package to `[tool.hatch.build.targets.wheel]` and coverage sources.
- `releasing.md` — `bump-my-version` with `--no-commit --no-tag`, `uv lock`, one commit for
  `pyproject.toml` + `uv.lock`, annotated `v*` tag, Publish workflow (tests + docs + lint gate, PyPI
  trusted publishing).

## README

Replaced by (~50–60 lines):

1. Title, badges: Tests, Lint, PyPI, Docs (`https://readthedocs.org/projects/django-crud-views-extensions/badge/?version=latest`).
2. Incubator pitch (current intro paragraph) + requirements.
3. Per app: two-line description, minimal install snippet, link to its getting-started and reference pages
   on `https://django-crud-views-extensions.readthedocs.io/en/latest/`.
4. Example app: two lines + `task run`, link to the docs page.
5. Link to the development docs.

## Repo housekeeping

- `CLAUDE.md`: add the docs build/preview command to Commands and a short note on the docs layout;
  `exclude_docs` keeps `docs/superpowers/` out of the site.
- `.gitignore`: add `site/`.

## Verification

- `uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict` passes (broken
  internal links and nav entries fail the build).
- The built site contains no `superpowers/` pages.
- `uv run pytest` and `ruff` unaffected.
- Docs workflow green on the PR.
- After merge, the user imports the project on readthedocs.org; the RTD build passes and the README badge
  resolves.
