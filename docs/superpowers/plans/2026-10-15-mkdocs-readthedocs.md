# MkDocs documentation on Read the Docs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the extensions' documentation as an MkDocs site on Read the Docs, migrating and expanding the README, set up like `../django-crud-views`.

**Architecture:** `mkdocs.yml` + `.readthedocs.yaml` at the repo root, pages under `docs/` with awesome-pages `.pages` nav files, a hash-locked `docs/requirements.txt`. `mkdocs build --strict` is the test: it fails on broken internal links, broken anchors, and missing nav targets. A Docs workflow runs it on PRs/main/tags and Publish gates PyPI releases on it.

**Tech Stack:** MkDocs ≥ 1.6.1 (`readthedocs` theme), mkdocs-awesome-pages-plugin ≥ 2.10.1, uv, GitHub Actions, Read the Docs config v2.

**Spec:** `docs/superpowers/specs/2026-10-15-mkdocs-readthedocs-design.md`

## Global Constraints

- Build/test command (used in every task): `uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict` — must end with `Documentation built` and no `WARNING`.
- Theme `readthedocs`; plugins `search`, `awesome-pages`; markdown extension `admonition`; `validation.anchors: warn`.
- `edit_uri: blob/main/docs/`; `repo_url: https://github.com/jacob-consulting/django-crud-views-extensions`.
- `docs/superpowers/` and `docs/requirements.*` are never published (`exclude_docs`).
- RTD site base URL: `https://django-crud-views-extensions.readthedocs.io/en/latest/`; RTD build: ubuntu-24.04, Python 3.12.
- Requirements lock: `uv pip compile --universal --generate-hashes --python-version 3.12 docs/requirements.in -o docs/requirements.txt`.
- CI style of this repo: `actions/checkout@v5`, `astral-sh/setup-uv@v8.3.2` with `python-version: "3.13"`, `enable-cache: true`.
- Out of scope: mkdocstrings/API autodoc, Material theme, FAQ page, screenshots, translations, snippet-sync checks.
- Facts in pages come from the code under `src/` and `examples/bootstrap5/`, not only from the README. Every value quoted in this plan was read from the code on 2026-10-15; if the code disagrees, the code wins and the page follows it.
- A page may only link to pages that exist by the end of its own task (strict build). Cross-links to later sections are added in Task 6.
- Work on branch `docs/mkdocs`; one commit per task.

## Review Focus

1. **Doc snippets that no longer import** — a reader copies `from crud_views_widget_typeahead.widgets import TypeaheadSelect` and it fails. Pinned by the import-check step in Task 6.
2. **Settings defaults that drift from `conf.py`** — a table says `DEBOUNCE_MS` 300 while code says 250. Pinned by the default-values grep step in Tasks 2 and 3.
3. **Internal files published on RTD** — specs, plans or `requirements.txt` showing up as pages. Pinned by the `site/` listing step in Task 1.
4. **README links to RTD paths that don't exist** — strict mode does not check absolute URLs. Pinned by the README-URL step in Task 6.
5. **Sibling-section ordering / missing nav** — a page exists but is not in any `.pages`, so it is unreachable from the menu. Pinned by the orphan-page step in Task 6.

---

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `mkdocs.yml` | Site config | 1 |
| `.readthedocs.yaml` | RTD build config | 1 |
| `docs/requirements.in`, `docs/requirements.txt` | Docs build deps (hash-locked) | 1 |
| `.github/workflows/docs.yml`, `.github/workflows/publish.yml` | CI build + release gate | 1 |
| `.gitignore` | ignore `site/` | 1 |
| `docs/.pages`, `docs/index.md` | Root nav + home | 1 (links added in 6) |
| `docs/reference/{.pages,index.md}` + `docs/reference/datetimepicker/*` | Datetimepicker reference | 2 |
| `docs/reference/typeahead/*` | Typeahead reference | 3 |
| `docs/getting_started/*` | Walkthroughs + example app | 4 |
| `docs/development/*` | Contributor docs | 5 |
| `README.md`, `CLAUDE.md`, `src/crud_views_widget_typeahead/widgets.py` (docstring) | Shrink README, point at docs | 6 |

---

### Task 1: Docs infrastructure and home page

**Files:**
- Create: `mkdocs.yml`, `.readthedocs.yaml`, `docs/requirements.in`, `docs/requirements.txt` (generated), `docs/.pages`, `docs/index.md`, `.github/workflows/docs.yml`
- Modify: `.github/workflows/publish.yml` (add `docs` job, extend `needs`), `.gitignore` (add `site/`)

**Interfaces:**
- Produces: the build command from Global Constraints; root `docs/.pages` whose `nav:` later tasks extend — Task 2 adds `reference`, Task 4 inserts `getting_started` before it, Task 5 appends `development` (final order: Home, getting_started, reference, development).

- [ ] **Step 1: Create branch**

```bash
git checkout -b docs/mkdocs
```

- [ ] **Step 2: Write `docs/requirements.in` and lock it**

```
# Docs build dependencies. Edit this file, then regenerate the hashed lock:
#   uv pip compile --universal --generate-hashes --python-version 3.12 docs/requirements.in -o docs/requirements.txt
mkdocs>=1.6.1
mkdocs-awesome-pages-plugin>=2.10.1
mkdocs-get-deps>=0.2.0
```

Run: `uv pip compile --universal --generate-hashes --python-version 3.12 docs/requirements.in -o docs/requirements.txt`
Expected: `docs/requirements.txt` exists and `grep -c sha256 docs/requirements.txt` prints a number > 0.

- [ ] **Step 3: Run the build to see it fail**

Run: `uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict`
Expected: FAIL — `Config file 'mkdocs.yml' does not exist`.

- [ ] **Step 4: Write `mkdocs.yml`**

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

- [ ] **Step 5: Write `docs/.pages`**

```yaml
nav:
    - Home: index.md
```

- [ ] **Step 6: Write `docs/index.md`**

Content (no internal links yet — Task 6 adds them):

- H1 `Django CRUD Views Extensions`.
- Pitch, from the README intro: incubator for [django-crud-views](https://github.com/jacob-consulting/django-crud-views) extension apps; named as if they lived in django-crud-views (`crud_views_widget_*`) so a mature app can move into the main package with no code changes for consuming projects.
- `## The naming contract` — public import paths (`crud_views_widget_<name>.<module>`) and settings keys (`CRUD_VIEWS_<NAME>`) are part of the contract and stay stable when an app moves into django-crud-views.
- `## Requirements` — Python ≥ 3.12; django-crud-views ≥ 0.29; jQuery only for the datetimepicker.
- `## Apps` — two subsections:
  - `### crud_views_widget_datetimepicker` — form widgets `DateTimePickerInput`, `DatePickerInput`, `TimePickerInput` wrapping the [xdsoft jQuery DateTimePicker](https://github.com/xdan/datetimepicker); CDN or vendored assets; picker format follows the request locale.
  - `### crud_views_widget_typeahead` — server-backed type-ahead single select for large, permission-sensitive model choice sets, for forms and django-filter filters; text typeahead and select popup; vanilla JS, no jQuery, CSP-safe, ARIA combobox.
- `## Install` — `pip install django-crud-views-extensions`.

- [ ] **Step 7: Write `.readthedocs.yaml`**

```yaml
# .readthedocs.yaml
# Read the Docs configuration file
# See https://docs.readthedocs.io/en/stable/config-file/v2.html for details

# Required
version: 2

# Set the version of Python and other tools you might need
build:
  os: ubuntu-24.04
  tools:
    python: "3.12"

mkdocs:
  configuration: mkdocs.yml

# Optionally declare the Python requirements required to build your docs
python:
   install:
   - requirements: docs/requirements.txt
```

- [ ] **Step 8: Add `site/` to `.gitignore`**

Append a line `site/`.

- [ ] **Step 9: Run the build to verify it passes**

Run: `uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict`
Expected: PASS, output ends with `Documentation built in …`, no `WARNING`.

- [ ] **Step 10: Verify nothing internal is published (Review Focus 3)**

Run: `ls site; find site -path '*superpowers*' -o -name 'requirements*' | head`
Expected: `ls` shows `index.html`, `search.html`, `sitemap.xml`, asset dirs; `find` prints nothing.

- [ ] **Step 11: Write `.github/workflows/docs.yml`**

```yaml
name: Docs

on:
  push:
    branches: [main]
    tags:
      - "v*"
  pull_request:
    branches: [main]

jobs:
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

- [ ] **Step 12: Gate publishing on the docs build**

In `.github/workflows/publish.yml`, insert this job between `tests` and `lint` (same indentation as `lint:`):

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

and change `needs: [tests, lint]` to `needs: [tests, docs, lint]`.

Run: `python3 -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]" .github/workflows/docs.yml .github/workflows/publish.yml .readthedocs.yaml mkdocs.yml && grep -n 'needs:' .github/workflows/publish.yml`
Expected: no exception; `needs: [tests, docs, lint]`. (If PyYAML is missing: `uv run --with pyyaml python …`.)

- [ ] **Step 13: Commit**

```bash
git add mkdocs.yml .readthedocs.yaml docs/requirements.in docs/requirements.txt docs/.pages docs/index.md .github/workflows/docs.yml .github/workflows/publish.yml .gitignore
git commit -m "docs: mkdocs + Read the Docs scaffolding, docs CI and release gate"
```

---

### Task 2: Reference — datetimepicker

**Files:**
- Create: `docs/reference/.pages`, `docs/reference/index.md`, `docs/reference/datetimepicker/{.pages,widgets.md,formats.md,settings.md,vendored.md,pipeline.md,checks.md}`
- Modify: `docs/.pages`

**Interfaces:**
- Consumes: build command, `docs/.pages` (Task 1).
- Produces: `docs/reference/.pages` with a `Datetimepicker` entry Task 3 appends `Typeahead` after; `docs/reference/index.md` with a `## Datetimepicker` list Task 3 appends `## Typeahead` after. Page paths `reference/datetimepicker/<name>.md` linked by Tasks 4 and 6.

Read first: `src/crud_views_widget_datetimepicker/{apps,assets,checks,conf,formats,widgets}.py`, `management/commands/cv_vendor_datetimepicker.py`, `static/crud_views_widget_datetimepicker/init.js`, and the README section `## crud_views_widget_datetimepicker`.

- [ ] **Step 1: Add the section to the root nav and run the build to see it fail**

`docs/.pages`:

```yaml
nav:
    - Home: index.md
    - reference
```

Run the build command. Expected: FAIL with `NavEntryNotFound: Nav entry "reference" not found. [.pages]`.

- [ ] **Step 2: Write the nav files**

`docs/reference/.pages`:

```yaml
nav:
    - index.md
    - Datetimepicker: datetimepicker
```

`docs/reference/datetimepicker/.pages`:

```yaml
nav:
    - widgets.md
    - Formats & language: formats.md
    - settings.md
    - Vendored mode: vendored.md
    - django-pipeline: pipeline.md
    - System checks: checks.md
```

- [ ] **Step 3: Write `docs/reference/index.md`**

H1 `Reference`, then `## Datetimepicker` with one bullet per page, sibling style: `- [Widgets](datetimepicker/widgets.md) — DateTimePickerInput, DatePickerInput, TimePickerInput and their options`, likewise for formats, settings, vendored, pipeline, checks (one-line description each).

- [ ] **Step 4: Write `docs/reference/datetimepicker/widgets.md`**

Must contain:
- The three widgets and the field each belongs to: `DateTimePickerInput` (DateTimeField), `DatePickerInput` (DateField, class defaults `{"timepicker": False}`), `TimePickerInput` (TimeField, class defaults `{"timepicker": True, "datepicker": False}`). Import: `from crud_views_widget_datetimepicker.widgets import DateTimePickerInput, DatePickerInput, TimePickerInput`.
- The README's `AppointmentForm` example.
- `config={...}`: any xdsoft option (e.g. `step`, `minTime`), link to https://xdsoft.net/jqplugins/datetimepicker/.
- `fix_year=2026` (DateTimePickerInput only): sets `minDate` `2026-01-01`, `maxDate` `2026-12-31`, `yearStart`, `yearEnd` via `setdefault` — an explicit `config` value wins.
- `## Config merge order` (lowest → highest): widget class defaults → `lang` → settings `DEFAULTS` → per-field `config`. Example: settings `DEFAULTS = {"dayOfWeekStart": 1}` plus `config={"step": 15}`.
- `## How it works`: no `Media` class; at render time (per request) the merged config is JSON-serialised into the `xdsoft-datetime-config` attribute; `init.js` activates every `input[xdsoft-datetime-config]` on document ready and again on the `cv:modal:loaded` event that crud-views dispatches on `#cv-modal`; assets are page-global via `{% cv_js %}` / `{% cv_css %}`; jQuery must load before `{% cv_js %}`.
- Link to `formats.md` for `format`.

- [ ] **Step 5: Write `docs/reference/datetimepicker/formats.md`**

Must contain (README `### Formats and language` plus):
- Format resolution order (highest first), from `XdsoftConfigMixin` docstring: explicit picker `format` (settings `DEFAULTS` or per-field `config`) → Django `format=` widget argument → first of the active locale's `DATE_INPUT_FORMATS` / `DATETIME_INPUT_FORMATS` / `TIME_INPUT_FORMATS` the picker can reproduce → fallback (`%Y-%m-%d %H:%M`, `%Y-%m-%d`, `%H:%M`).
- Datetime and time prefer a locale format without `%S` (the picker offers hours and minutes only).
- The invariant: the widget renders and parses the value with the picker's format, so what the picker writes the form accepts — examples `2026-10-15 19:00` (`en`), `15.10.2026 19:00` (`de`).
- `## Token table` — table strftime | PHP (picker): `%d`|`d`, `%m`|`m`, `%Y`|`Y`, `%y`|`y`, `%H`|`H`, `%M`|`i`, `%S`|`s`. Any other token (e.g. `%f`, `%b`, `%p`) or a letter in a literal makes a format unreproducible: the locale format is skipped; a pinned picker format with other tokens is passed to the picker unchanged and must be accepted by the field's `input_formats`; a Django `format=` the picker cannot reproduce leaves the picker on its own default.
- Pinning: `config={"format": "d.m.Y"}` or `DatePickerInput(format="%d.%m.%Y")`.
- `## Language` — active request language (first segment, `de-at` → `de`) unless settings `LANG` or `config={"lang": ...}`; `LANG` unset falls back to the first segment of `LANGUAGE_CODE` when no language is active. `!!! warning` admonition: the plugin locale is page-global (`jQuery.datetimepicker.setLocale`), so one field with its own `lang` switches every picker on the page.

- [ ] **Step 6: Write `docs/reference/datetimepicker/settings.md`**

`CRUD_VIEWS_DATETIMEPICKER` dict, table Key | Default | Meaning:

| Key | Default | Meaning |
|---|---|---|
| `SOURCE` | `"cdn"` | `"cdn"` or `"vendored"`; anything else → `crud_views.E333` |
| `VERSION` | `"2.5.21"` | pinned upstream jquery-datetimepicker version, used by both modes |
| `CDN_BASE` | `"https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/"` | CDN URL template; `{version}` is replaced |
| `VENDOR_DIR` | `None` | required for vendored mode; must be listed in `STATICFILES_DIRS` |
| `EMIT` | `True` | `False` keeps the assets registered but suppresses `{% cv_js %}`/`{% cv_css %}` output (bundler delivers them) |
| `LANG` | `None` | picker language; `None` = the active request language |
| `DEFAULTS` | `{}` | merged into every widget's picker config (see merge order) |

Plus the README's full settings code block. Settings are read at startup (`AppConfig.ready()`) for asset registration and at render time for `LANG`/`DEFAULTS`.

- [ ] **Step 7: Write `docs/reference/datetimepicker/vendored.md`**

Must contain: why (no third-party CDN request — GDPR, offline, CSP); the README settings block and `python manage.py cv_vendor_datetimepicker`; the command takes no options, downloads all four file variants (`jquery.datetimepicker.full.js`, `.full.min.js`, `jquery.datetimepicker.css`, `.min.css`) of `VERSION` from `CDN_BASE` into `VENDOR_DIR/crud_views_widget_datetimepicker/<VERSION>/`, and fails with `CommandError` when `VENDOR_DIR` is unset; re-run after changing `VERSION`; commit the vendored files or run the command in your deployment build; link to `checks.md`.

- [ ] **Step 8: Write `docs/reference/datetimepicker/pipeline.md`**

Must contain: CDN mode cannot be bundled; the README pipeline example; the three Django-free functions in `crud_views_widget_datetimepicker.assets`, importable from `settings.py`:
- `source_files(version, minified=True)` → `{"js": ["crud_views_widget_datetimepicker/<version>/jquery.datetimepicker.full.min.js", "crud_views_widget_datetimepicker/init.js"], "css": ["crud_views_widget_datetimepicker/<version>/jquery.datetimepicker.min.css"]}` (non-minified names with `minified=False`);
- `cdn_files(cdn_base, version, minified=True)` → plugin URLs only;
- `bundle(source, version, cdn_base, minified=True)` → what `AppConfig.ready()` registers (CDN plugin + static `init.js`, or `source_files`).
- `!!! note` load order jQuery → plugin → `init.js`; `source_files()` already returns plugin before `init.js`; jQuery is yours. Set `EMIT: False`.

- [ ] **Step 9: Write `docs/reference/datetimepicker/checks.md`**

Table ID | Level | When | Fix, then one `###` per ID (anchors `#crud_viewse333` etc. are whatever MkDocs generates — do not hand-link anchors):
- `crud_views.E333` Error — `SOURCE` is not `"cdn"`/`"vendored"` → set `SOURCE`. (`checks.py`)
- `crud_views.E332` Error — `SOURCE` is `"vendored"` but `VENDOR_DIR` unset → set `VENDOR_DIR`, list it in `STATICFILES_DIRS`. (`checks.py`)
- `crud_views.W330` Warning — vendored files missing → run `cv_vendor_datetimepicker`. (core `crud_views.lib.vendor.check_vendored`)
- `crud_views.W331` Warning — vendored files don't match `VERSION` → re-run the command. (core)
Checks run only in vendored mode (except E333) and are registered under the `crud_views` tag (`manage.py check --tag crud_views`).

Verify W330/W331 wording against the installed core: `grep -n -B4 -A4 'W33[01]' .venv/lib/python*/site-packages/crud_views/lib/vendor.py` and quote the messages from there.

- [ ] **Step 10: Run the build to verify it passes**

Run the build command. Expected: PASS, no `WARNING`.

- [ ] **Step 11: Verify defaults against code (Review Focus 2)**

Run: `grep -n '2.5.21\|jquery-datetimepicker@{version}' src/crud_views_widget_datetimepicker/conf.py docs/reference/datetimepicker/settings.md`
Expected: both values appear in both files.

- [ ] **Step 12: Commit**

```bash
git add docs/.pages docs/reference
git commit -m "docs: datetimepicker reference"
```

---

### Task 3: Reference — typeahead

**Files:**
- Create: `docs/reference/typeahead/{.pages,lookups.md,fields_filters.md,widgets.md,endpoint.md,security.md,settings.md,skins.md,pipeline.md}`
- Modify: `docs/reference/.pages`, `docs/reference/index.md`

**Interfaces:**
- Consumes: `docs/reference/.pages`, `docs/reference/index.md` (Task 2).
- Produces: page paths `reference/typeahead/<name>.md` linked by Tasks 4 and 6.

Read first: `src/crud_views_widget_typeahead/{apps,assets,conf,fields,filters,lookups,tokens,urls,views,widgets}.py`, the two templates under `templates/crud_views_widget_typeahead/`, the header comments of `static/crud_views_widget_typeahead/typeahead.js` and `typeahead-select.js`, `examples/bootstrap5/typeahead/{typeahead.py,forms.py}`, and README `## crud_views_widget_typeahead`.

- [ ] **Step 1: Extend the reference nav and run the build to see it fail**

Append to `docs/reference/.pages` nav: `    - Typeahead: typeahead`.
Run the build command. Expected: FAIL (nav entry `typeahead` not found).

- [ ] **Step 2: Write `docs/reference/typeahead/.pages`**

```yaml
nav:
    - lookups.md
    - Fields & filters: fields_filters.md
    - widgets.md
    - endpoint.md
    - security.md
    - settings.md
    - skins.md
    - django-pipeline: pipeline.md
```

- [ ] **Step 3: Append `## Typeahead` to `docs/reference/index.md`**

One bullet per page with a one-line description, same style as Task 2.

- [ ] **Step 4: Write `lookups.md`**

Must contain:
- A lookup owns the allowed set (including the permission check), the search and the labels; endpoint and field both resolve it by name, so the restriction is written once.
- `## Autodiscovery` — put lookups in `<app>/typeahead.py`; `AppConfig.ready()` imports every installed app's `typeahead.py` (`autodiscover_modules("typeahead")`). Registering a name twice → `ImproperlyConfigured`; an unknown name → `LookupNotFound` (subclass of `ImproperlyConfigured`) at `bind()` time.
- `## TypeaheadLookup` — table Attribute | Default | Meaning: `search_fields` `[]` (`icontains`; every word must match some field; searching with empty `search_fields` → `ImproperlyConfigured`), `ordering` `[]`, `max_results` `10` (also the select popup's page size), `min_chars` `2` (shorter terms return an empty result without a query; `0` lets the select popup list on open), `login_required` `True` (anonymous → 403 `login_required`). Methods: `get_queryset(self, request, **params)` (required; raise `PermissionDenied` / `Http404` to refuse), `label(self, obj)` (default `str(obj)`). Results are `.distinct()`.
- Class example with `@register_lookup("app.name")` (e.g. a `Project` lookup with `search_fields = ["name", "code"]`, `ordering = ["name"]`).
- `## Users: register_user_lookup` — the README `projects.members` example; it builds a `UserLookup` subclass: `search_fields = ["first_name", "last_name", "username"]`, ordering by lower-cased last name, first name, username, label `get_full_name()` or username; `base=` takes your own `UserLookup` subclass (example changing `label`). The decorated function is returned unchanged.
- Values are always the pk (`to_field_name` → `ImproperlyConfigured`).
- Import paths: `from crud_views_widget_typeahead.lookups import TypeaheadLookup, UserLookup, register_lookup, register_user_lookup`.

- [ ] **Step 5: Write `fields_filters.md`**

Must contain:
- README `TaskForm` / `TaskFilter` example with imports `from crud_views_widget_typeahead.fields import TypeaheadField` and `from crud_views_widget_typeahead.filters import TypeaheadFilter`.
- `bind(request, **params)` is the single source of truth: sets the field's queryset (save-time validation) from `lookup.get_queryset(request, **params)` and signs `{lookup, params}` into the widget token; returns the field/filter (chainable).
- Params must be a dict of JSON values — pass UUIDs, dates, model instances as `str`, else `ImproperlyConfigured` at bind time.
- Unbound field: `clean()` and rendering raise `ImproperlyConfigured`.
- `TypeaheadFilter` defaults its widget to `TypeaheadInput(submit_on_clear=True)`; URLs stay `?assignee=<pk>`; bind in the FilterSet's `__init__`.
- With crud_views' `CrispyModelForm` the request is `self.cv_view.request` — show the example app's form (`examples/bootstrap5/typeahead/forms.py`, `TaskForm.__init__`) trimmed to the bind call.
- `!!! warning "crud_views list views"` — the list template evaluates `{% if view.filterset_class %}` and Django templates call callables, instantiating the FilterSet without a request; set `do_not_call_in_templates = True` on a FilterSet that binds in `__init__`.
- Duplicate rows from an un-distinct lookup queryset are tolerated (pk is unique).

- [ ] **Step 6: Write `widgets.md`**

Must contain:
- Two widgets in `crud_views_widget_typeahead.widgets`: `TypeaheadInput` (default, text input + suggestion list) and `TypeaheadSelect` (trigger looking like a Bootstrap `<select>`, popup with search field and list that loads the next page on scroll). Per field; both can share a page. README examples for both.
- Constructor args: `attrs`, `submit_on_clear=False` (submit the form when the selection is cleared — default `True` for filters), `template_name=None` (overrides the settings template).
- Rendering: visible input/button has no `name`; a hidden input carries the name and the pk; the `required` attribute is never rendered (a required visible input would accept typed text without a pk); `aria-describedby` is merged with Django's help/error ids.
- `## Text typeahead keyboard` — from `typeahead.js` header comment and README skin behaviours: arrows preview, Enter selects, Enter never submits while the list is open or while typed text is not yet a selection, Escape, blur restores the label; "N more results" from `count`.
- `## Select popup` — README `### Select popup` paragraph: opens on Enter/Space/↑/↓/typing; ↑/↓ move, Enter selects; Escape closes only the popup (a surrounding crud_views modal stays open); Enter never submits while open; `min_chars = 0` lists the first page on open, otherwise asks for `min_chars` characters; page size = `max_results`.
- `## Modals and dynamic content` — both activate on `DOMContentLoaded` and on `cv:modal:loaded`; call `window.cvTypeahead.init(container)` / `window.cvTypeaheadSelect.init(container)` for other dynamic content (e.g. new formset rows). `!!! note` the popup renders inside the widget (works in modals) and can be clipped by an ancestor with `overflow: hidden`; inside `modal-dialog-scrollable` modals it scrolls within the modal body.

- [ ] **Step 7: Write `endpoint.md`**

Must contain:
- Mounting: `path("_typeahead/", include("crud_views_widget_typeahead.urls"))` — any prefix; URL name `crud_views_typeahead:lookup`.
- `GET <mount>/?t=<token>&q=<term>[&page=<n>]`; never cached (`never_cache`); non-GET → 405.
- Response example:

```json
{"results": [{"value": "42", "label": "Ada Lovelace"}, {"value": "7", "label": "Grace Hopper"}], "count": 57}
```

  `value` is the pk as string; `count` is the total before paging.
- Paging: `page` 1-based, page size `max_results`; missing/invalid/< 1 → 1; a page past the end returns `results: []`; ordering is the lookup's ordering (else the model's `Meta.ordering`) with pk as final tiebreaker, so pages never repeat or skip rows. The text typeahead never sends `page`.
- Terms shorter than `min_chars` → `{"results": [], "count": 0}` without a query.
- Errors table Status | Body | When: 400 `{"error": "bad_token"}` (bad signature, wrong shape, unknown lookup); 403 `{"error": "login_required"}` (`login_required` and anonymous); 403 `{"error": "forbidden"}` (`get_queryset` raised `PermissionDenied`); 404 `{"error": "not_found"}` (`Http404`); 405 (non-GET). Errors never redirect to a login page and never echo exception messages.

- [ ] **Step 8: Write `security.md`**

Must contain: token = `django.core.signing.dumps({"l": <lookup name>, "p": <params>}, salt="crud_views.typeahead", compress=True)` — the browser carries lookup and params but cannot change them; signed with `SECRET_KEY` (rotating it invalidates open forms' tokens). No expiry on purpose: permission is re-checked on every request through `get_queryset(request, **params)`, so a form left open overnight keeps working and a leaked token grants nothing beyond what the requesting user may see. Tokens are signed, not encrypted — params are readable in the page source; don't put secrets in them. Save-time validation uses the same `bind()` queryset, so a forged pk in the hidden input is rejected. JSON errors only (see endpoint).

- [ ] **Step 9: Write `settings.md`**

`CRUD_VIEWS_TYPEAHEAD` table Key | Default | Meaning:

| Key | Default | Meaning |
|---|---|---|
| `EMIT` | `True` | `False` suppresses the text typeahead's `{% cv_js %}`/`{% cv_css %}` output (skins, django-pipeline) |
| `TEMPLATE` | `"crud_views_widget_typeahead/typeahead.html"` | text typeahead template |
| `DEBOUNCE_MS` | `250` | input debounce in ms; applies to both widgets |
| `SELECT_EMIT` | `True` | `False` suppresses the select popup's `{% cv_js %}`/`{% cv_css %}` output |
| `SELECT_TEMPLATE` | `"crud_views_widget_typeahead/typeahead_select.html"` | select popup template |

Note: the two widgets are separate asset bundles (`typeahead`, `typeahead_select`), so a skin can replace one without touching the other.

- [ ] **Step 10: Write `skins.md`**

Structure as checklists (`- [ ]` is not rendered by the theme — use plain numbered/bulleted lists):
- `## Text typeahead` — README `### Skins` items 1–3, with the template context spelled out: `widget.attrs` (visible input: `id`, `class` incl. `form-control`, `autocomplete="off"`, `role="combobox"`, `aria-autocomplete="list"`, `aria-expanded`, `aria-controls`, merged `aria-describedby`) and `widget.typeahead` keys `url`, `label`, `value`, `hidden_name`, `hidden_id`, `listbox_id`, `hint_id`, `min_chars`, `debounce`, `submit_on_clear`, `i18n` with keys `hint`, `more`, `none`, `count`, `error`, `clear`, `listbox` (`{n}` is the number placeholder). Hidden-input contract and required behaviours as a bullet list (copy the README item 3 content, one behaviour per bullet).
- `## Select popup` — README `### Select popup` skin paragraph: extra keys `popup_id`, `label_id`, `search_id`, `page_size`; extra i18n keys `placeholder`, `search`, `loading`, `type_more`; `widget.attrs` land on the trigger button (`form-select text-start`, `aria-haspopup="listbox"`, `aria-expanded`, `aria-controls`, `aria-labelledby="<id> <id>_label"`); set `SELECT_EMIT = False`.
- `## Registering your assets` — `crud_views.lib.assets.register_assets(key="my_typeahead_skin", js=[...], css=[...])` in your `AppConfig.ready()`, plus `EMIT`/`SELECT_EMIT = False`. Check the exact `register_assets` signature: `grep -n 'def register_assets' -A12 .venv/lib/python*/site-packages/crud_views/lib/assets.py`.
- `## JavaScript API` — `window.cvTypeahead.init(root)`, `window.cvTypeaheadSelect.init(root)`, re-init on `cv:modal:loaded`.
- Link the default templates on GitHub: `https://github.com/jacob-consulting/django-crud-views-extensions/tree/main/src/crud_views_widget_typeahead/templates/crud_views_widget_typeahead`.

- [ ] **Step 11: Write `pipeline.md`**

`from crud_views_widget_typeahead.assets import source_files, select_source_files` (Django-free, importable from `settings.py`): `source_files()` → `{"js": ["crud_views_widget_typeahead/typeahead.js"], "css": ["crud_views_widget_typeahead/typeahead.css"]}`; `select_source_files()` → `{"js": ["crud_views_widget_typeahead/typeahead-select.js"], "css": ["crud_views_widget_typeahead/typeahead-select.css"]}`; `bundle()` / `select_bundle()` are what `AppConfig.ready()` registers (same lists). No CDN/vendoring — no third-party plugin. A `PIPELINE` example adding both, with `CRUD_VIEWS_TYPEAHEAD = {"EMIT": False, "SELECT_EMIT": False}`.

- [ ] **Step 12: Run the build to verify it passes**

Run the build command. Expected: PASS, no `WARNING`.

- [ ] **Step 13: Verify defaults against code (Review Focus 2)**

Run: `grep -c 'typeahead.html\|typeahead_select.html\|250' docs/reference/typeahead/settings.md; grep -n 'max_results = \|min_chars = ' src/crud_views_widget_typeahead/lookups.py; grep -n '`10`\|`2`' docs/reference/typeahead/lookups.md`
Expected: settings page count ≥ 3; lookups page shows the same `10` and `2` as the code.

- [ ] **Step 14: Commit**

```bash
git add docs/reference
git commit -m "docs: typeahead reference"
```

---

### Task 4: Getting started

**Files:**
- Create: `docs/getting_started/{.pages,index.md,datetimepicker.md,typeahead.md,example_app.md}`
- Modify: `docs/.pages`

**Interfaces:**
- Consumes: reference pages from Tasks 2–3 (link targets).
- Produces: `getting_started/<name>.md` paths linked by Task 6.

Read first: `examples/bootstrap5/project/{settings.py,urls.py,features.py}`, `examples/bootstrap5/datetimepicker/forms.py`, `examples/bootstrap5/typeahead/{typeahead.py,forms.py}`, `examples/bootstrap5/taskfile.yaml`.

- [ ] **Step 1: Add the section before `reference` and run the build to see it fail**

`docs/.pages`:

```yaml
nav:
    - Home: index.md
    - getting_started
    - reference
```

Run the build command. Expected: FAIL (nav entry `getting_started` not found).

- [ ] **Step 2: Write `docs/getting_started/.pages`**

```yaml
nav:
    - index.md
    - First datetimepicker: datetimepicker.md
    - First typeahead: typeahead.md
    - Example app: example_app.md
```

- [ ] **Step 3: Write `index.md` (Installation)**

H1 `Getting started`. `pip install django-crud-views-extensions` (or `uv add`). `INSTALLED_APPS` showing both forms used in the codebase: `"crud_views_widget_datetimepicker"` and `"crud_views_widget_typeahead.apps.CrudViewsWidgetTypeaheadConfig"` after `crud_views`. Assets: no `Media`; both apps register with the crud_views asset registry, so `{% cv_css %}` / `{% cv_js %}` in your base template deliver them on every page including crud-views modals. `!!! note` the datetimepicker needs jQuery loaded before `{% cv_js %}` (same rule as django-crud-views core); the typeahead needs none. Typeahead also needs the URL include (link `../reference/typeahead/endpoint.md`). Links to the two walkthroughs.

- [ ] **Step 4: Write `datetimepicker.md`**

Walkthrough: a model with `starts_at = models.DateTimeField()`, `day = models.DateField()`; a `CrispyModelForm` (or plain `ModelForm`) with `widgets = {"starts_at": DateTimePickerInput(), "day": DatePickerInput()}`; nothing else to configure — CDN mode by default; what renders (input with `xdsoft-datetime-config`); format follows the active language (link `../reference/datetimepicker/formats.md`); a per-field option `DateTimePickerInput(config={"step": 15})`; `!!! tip` production / GDPR → vendored mode (link `../reference/datetimepicker/vendored.md`). Base the snippet on `examples/bootstrap5/datetimepicker/forms.py`.

- [ ] **Step 5: Write `typeahead.md`**

Walkthrough mirroring the example app's teams/tasks, using the real code from `examples/bootstrap5/typeahead/typeahead.py` and `forms.py`: (1) mount the URL; (2) write the lookup in `typeahead.py` with `register_user_lookup`, including the permission check; (3) `TypeaheadField` + `bind()` in a form's `__init__`; (4) `TypeaheadFilter` + `bind()` in a FilterSet with `do_not_call_in_templates = True`; (5) swap in `TypeaheadSelect()`. Each step links its reference page (`../reference/typeahead/lookups.md`, `fields_filters.md`, `widgets.md`).

- [ ] **Step 6: Write `example_app.md`**

`examples/bootstrap5/` is a local Django project running against `src/`. One card per `Feature` in `project/features.py` — list the three by title with their one-line description: "Datetimepicker: forms, modals & filters", "Datetimepicker: per-field config", "Typeahead: thousands of users" (3,000 seeded users, ~500 per team). Commands: `cd examples/bootstrap5 && task run` (migrate, seed, runserver on 127.0.0.1:8000, log in `admin`/`admin`), `task seed`, `task test`; without [Task](https://taskfile.dev): `uv run manage.py migrate && uv run manage.py seed && uv run manage.py runserver`. `!!! warning` local only: DEBUG and a published admin/admin login. Each feature card names the code to look at (`look_at`) — mention that.

- [ ] **Step 7: Run the build to verify it passes**

Run the build command. Expected: PASS, no `WARNING`.

- [ ] **Step 8: Commit**

```bash
git add docs/.pages docs/getting_started
git commit -m "docs: getting started and example app"
```

---

### Task 5: Development

**Files:**
- Create: `docs/development/{.pages,index.md,new_extension.md,releasing.md}`
- Modify: `docs/.pages`

**Interfaces:**
- Consumes: reference pages (link targets for the asset pattern).
- Produces: `development/index.md` linked by Task 6 (README).

Read first: `CLAUDE.md`, `tests/conftest.py`, `pyproject.toml`, `.github/workflows/{tests,lint,publish}.yml`.

- [ ] **Step 1: Add the section and run the build to see it fail**

Append `    - development` to `docs/.pages` nav. Run the build command. Expected: FAIL (nav entry not found).

- [ ] **Step 2: Write `docs/development/.pages`**

```yaml
nav:
    - index.md
    - Adding an extension app: new_extension.md
    - Releasing: releasing.md
```

- [ ] **Step 3: Write `index.md`**

Requirements: [uv](https://docs.astral.sh/uv/), optionally [Task](https://taskfile.dev) for the example app. Setup: `git clone git@github.com:jacob-consulting/django-crud-views-extensions.git`, `cd django-crud-views-extensions`, `uv sync --extra dev`. Commands block: `uv run pytest`, `uv run pytest tests/test_widgets.py`, `uv run pytest -k pipeline`, `uv run ruff check . && uv run ruff format .` (line length 120, double quotes). Tests need no `DJANGO_SETTINGS_MODULE` — `tests/conftest.py` calls `settings.configure()` (`LANGUAGE_CODE="de-de"`, `PIPELINE={}`). Example app tests: `cd examples/bootstrap5 && uv run pytest` — not collected by the root run (`testpaths = ["tests"]`), CI runs them separately. django-crud-views comes from PyPI via `uv.lock`; to test an unreleased sibling checkout: `uv pip install -e ../django-crud-views`. `## Documentation` — preview `uv run --no-project --with-requirements docs/requirements.txt mkdocs serve -a localhost:8001`; build `… mkdocs build --strict`; update deps by editing `docs/requirements.in` and re-running the compile command (Global Constraints); `docs/superpowers/` holds design specs and plans and is not published.

- [ ] **Step 4: Write `new_extension.md`**

Must contain:
- Naming: package `crud_views_widget_<name>`, settings dict `CRUD_VIEWS_<NAME>`, asset key `<name>`; public import paths and settings keys are the contract.
- Module roles, using the datetimepicker as the model: `assets.py` — Django-free path logic, importable from `settings.py`; one path list feeds three consumers: the runtime asset registry (`apps.py`), vendoring command + system check (if there is a third-party plugin), and a project's django-pipeline config. `conf.py` — the only module reading `django.conf.settings`, into a frozen dataclass. `apps.py::ready()` — `register_assets(key=..., js=..., css=..., emit=cfg.emit)`. Widgets without `Media`. JS re-inits on `cv:modal:loaded`. Checks/vendoring reuse `crud_views.lib.vendor` (`VendorSpec`, `vendor`, `check_vendored`); check IDs in the `crud_views.*` namespace.
- Rule: check what `crud_views.lib.*` offers before adding infrastructure.
- Checklist: add the package to `[tool.hatch.build.targets.wheel] packages` and `[tool.coverage.run] source` in `pyproject.toml` and the `--cov` flags in `.github/workflows/tests.yml` and `publish.yml`; tests under `tests/`; one example app under `examples/bootstrap5/<app>/` plus `Feature` entries in `project/features.py` (matched to pages by `Feature.viewset`); reference pages under `docs/reference/<app>/` and a getting-started walkthrough; README section.
- Link `../reference/datetimepicker/pipeline.md` as the worked example of the three-consumer pattern.

- [ ] **Step 5: Write `releasing.md`**

Steps: on `main` with green CI → `uv run bump-my-version bump minor --no-commit --no-tag` (or `patch`/`major`) → `uv lock` → `uv run pytest` → `git commit -am "Bump version: X → Y"` (pyproject.toml + uv.lock together) → `git tag -a vY -m "Bump version: X → Y"` → `git push origin main vY`. The `Publish` workflow runs on `v*` tags: tests (3.12–3.15), docs (`mkdocs build --strict`), lint, then builds and publishes to PyPI via trusted publishing (OIDC, no API token; provenance attestations). Read the Docs builds `latest` from `main`; tagged versions can be activated in the RTD project settings. Verify the exact bump/publish details against `pyproject.toml [tool.bumpversion]` and `.github/workflows/publish.yml` before writing.

- [ ] **Step 6: Run the build to verify it passes**

Run the build command. Expected: PASS, no `WARNING`.

- [ ] **Step 7: Commit**

```bash
git add docs/.pages docs/development
git commit -m "docs: development, new extension app, releasing"
```

---

### Task 6: README, cross-links, repo housekeeping, final verification

**Files:**
- Modify: `README.md` (rewrite), `docs/index.md` (add links), `CLAUDE.md`, `src/crud_views_widget_typeahead/widgets.py:4` (docstring)

**Interfaces:**
- Consumes: every page path from Tasks 1–5.

- [ ] **Step 1: Add internal links to `docs/index.md`**

Under each app subsection: links to its getting-started page and reference pages (`getting_started/datetimepicker.md`, `reference/datetimepicker/widgets.md`, `getting_started/typeahead.md`, `reference/typeahead/lookups.md`); under Install: link `getting_started/index.md`; a line linking `getting_started/example_app.md` and `development/index.md`.

- [ ] **Step 2: Rewrite `README.md` (~50–60 lines)**

```markdown
# django-crud-views-extensions

[![Tests](https://github.com/jacob-consulting/django-crud-views-extensions/actions/workflows/tests.yml/badge.svg)](https://github.com/jacob-consulting/django-crud-views-extensions/actions/workflows/tests.yml)
[![Lint](https://github.com/jacob-consulting/django-crud-views-extensions/actions/workflows/lint.yml/badge.svg)](https://github.com/jacob-consulting/django-crud-views-extensions/actions/workflows/lint.yml)
[![PyPI](https://img.shields.io/pypi/v/django-crud-views-extensions)](https://pypi.org/project/django-crud-views-extensions/)
[![Docs](https://readthedocs.org/projects/django-crud-views-extensions/badge/?version=latest)](https://django-crud-views-extensions.readthedocs.io/en/latest/)
```

Then: the current intro paragraph + "Requires django-crud-views >= 0.29."; **Documentation:** link to the site root. `## crud_views_widget_datetimepicker` — two lines (what it is; CDN or vendored), the install snippet (`pip install`, `INSTALLED_APPS`), the 3-line `widgets = {"starts_at": DateTimePickerInput()}` snippet, links: Getting started `…/en/latest/getting_started/datetimepicker/`, Reference `…/en/latest/reference/datetimepicker/widgets/`. `## crud_views_widget_typeahead` — two lines, `INSTALLED_APPS` + URL include snippet, links `…/getting_started/typeahead/`, `…/reference/typeahead/lookups/`. `## Example app` — two lines + `cd examples/bootstrap5 && task run`, link `…/getting_started/example_app/`. `## Development` — link `…/development/`. Use fenced code blocks (the current README mixes indented ones).

- [ ] **Step 3: Point code and CLAUDE.md at the docs**

- `src/crud_views_widget_typeahead/widgets.py` module docstring: replace `see the README's skin contract` with `see the skin contract in docs/reference/typeahead/skins.md`.
- `CLAUDE.md`: in `## Commands` add
  ```bash
  uv run --no-project --with-requirements docs/requirements.txt mkdocs serve -a localhost:8001   # docs preview
  uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict            # docs build (CI)
  ```
  and a short `### Docs` paragraph: MkDocs on Read the Docs, `readthedocs` theme, nav via awesome-pages `.pages` files, `docs/superpowers/` and `docs/requirements.*` excluded via `exclude_docs`, deps locked in `docs/requirements.txt` (compile command). Replace "the skin contract is documented in the README" with "…in `docs/reference/typeahead/skins.md`". Keep the test-count line accurate (`uv run pytest -q | tail -1`).

- [ ] **Step 4: Run the build, tests and lint**

Run: the build command; `uv run pytest -q`; `uv run ruff check . && uv run ruff format --check .`
Expected: build PASS with no `WARNING`; all tests pass; ruff clean.

- [ ] **Step 5: Verify README URLs resolve to built pages (Review Focus 4)**

```bash
grep -o 'readthedocs.io/en/latest/[^)]*' README.md | sed 's#readthedocs.io/en/latest/##' | while read p; do
  test -f "site/${p}index.html" && echo "ok   $p" || echo "MISS $p"; done
```

Expected: every line `ok` (the empty path checks `site/index.html`).

- [ ] **Step 6: Verify every page is in the nav (Review Focus 5)**

```bash
uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict 2>&1 | grep -i 'not included in the "nav"' ; \
find docs -name '*.md' -not -path 'docs/superpowers/*' | sed 's#^docs/##; s#\.md$#/#; s#index/$##' | while read p; do test -f "site/${p}index.html" || echo "MISSING $p"; done
```

Expected: no output.

- [ ] **Step 7: Verify documented imports resolve (Review Focus 1)**

```bash
grep -rhoE '^\s*from crud_views_widget_[a-z_.]+ import [A-Za-z_, ]+' docs README.md --exclude-dir=superpowers | sed 's/^ *//' | sort -u > /tmp/doc_imports.py
uv run python -c "
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','crud_views','crud_views_widget_datetimepicker','crud_views_widget_typeahead'], LANGUAGE_CODE='en', PIPELINE={})
django.setup()
exec(open('/tmp/doc_imports.py').read())
print('imports ok:', sum(1 for _ in open('/tmp/doc_imports.py')))
"
```

Expected: `imports ok: N` with N ≥ 6. (Use the session scratchpad instead of `/tmp` when running as an agent.) If `crud_views` needs more apps to set up, copy `INSTALLED_APPS` from `tests/conftest.py`.

- [ ] **Step 8: Verify the README lost nothing**

Read the old README (`git show main:README.md`) section by section and confirm each fact appears on a docs page (grep a distinctive phrase per section, e.g. `do_not_call_in_templates`, `minified=False`, `submit_on_clear`, `bad_token`, `W331`, `cvTypeaheadSelect`, `modal-dialog-scrollable`):

```bash
for s in do_not_call_in_templates 'minified=False' submit_on_clear bad_token W331 cvTypeaheadSelect modal-dialog-scrollable fix_year 'register_user_lookup' 'type_more'; do
  printf '%-28s %s\n' "$s" "$(grep -rl -- "$s" docs --exclude-dir=superpowers | head -1)"; done
```

Expected: every phrase has a file.

- [ ] **Step 9: Commit**

```bash
git add README.md docs/index.md CLAUDE.md src/crud_views_widget_typeahead/widgets.py
git commit -m "docs: slim README to overview + Read the Docs links; cross-link docs"
```

- [ ] **Step 10: Push and open the PR**

```bash
git push -u origin docs/mkdocs
gh pr create --title "MkDocs documentation on Read the Docs" --body "Implements docs/superpowers/specs/2026-10-15-mkdocs-readthedocs-design.md: mkdocs + RTD config, docs CI and release gate, README content migrated and expanded into docs/, README slimmed to an overview. After merge: import the repo on readthedocs.org (slug django-crud-views-extensions)."
gh pr checks --watch
```

Expected: Docs, Tests, Lint green. (Ask the user before pushing if not already authorized.)

- [ ] **Step 11: Hand the RTD import to the user**

Tell the user: import `jacob-consulting/django-crud-views-extensions` at https://app.readthedocs.org/dashboard/import/, slug `django-crud-views-extensions`; the first build should pass with the committed `.readthedocs.yaml`, and the README badge resolves once it has.
