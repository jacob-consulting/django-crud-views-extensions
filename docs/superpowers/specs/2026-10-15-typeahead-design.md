# Typeahead widget (`crud_views_widget_typeahead`) — design

Date: 2026-10-15
Status: approved in brainstorming, pending spec review
Input: `docs/superpowers/prompts/2026-10-15-typeahead.md`

## Goal

A reusable type-ahead single select for large, context-dependent and
permission-sensitive model choice sets (motivating case: ~10,000 users, containers
with ~1,000 members), with suggestions loaded from the server, usable in Django forms
and django-filter filters. It replaces django-autocomplete-light/Select2 in
crud_views projects.

Success criteria:

- The endpoint never reveals more than the page itself would: the allowed set and
  the permission check live in one place (the lookup) and are re-checked per request.
- What the user can pick is exactly what the form accepts on save (one queryset
  feeds suggestions and validation).
- Works on plain Bootstrap 5 / crud_views pages, inside crud_views modals, under a
  strict CSP, and is accessible (ARIA combobox pattern).
- A design-system package can replace the frontend (template + JS) and reuse the
  whole server core unchanged.

## Decisions taken in brainstorming

| Topic | Decision |
|---|---|
| Consumers | crud_views projects only → one app `crud_views_widget_typeahead`, depends on django-crud-views like the datetimepicker, liftable into core without import changes |
| Default frontend | Own vanilla JS (no jQuery, no third-party plugin) |
| Skin boundary | Whole-frontend swap: skin provides template + its own JS; contract = widget context + endpoint JSON + hidden-input semantics |
| Scope | Single-select only |
| Binding API | Explicit `field.bind(request, **params)` (proven design); no form mixin, no thread-local magic |
| `UserTypeaheadField` | Dropped — user specifics live in `UserLookup` |
| Result item key | `label` (not the reference implementation's `term`) |
| JS testing | Scripted browser checklist against the example app; no JS test toolchain |

Deferred (each its own spec): multi-select, ViewSet-integrated lookups, migration of
the dal-based project, formset auto-init, automated JS tests.

## Package layout

`src/crud_views_widget_typeahead/` — module names are public import paths (contract):

| Module | Content |
|---|---|
| `apps.py` | `CrudViewsWidgetTypeaheadConfig.ready()`: `autodiscover_modules("typeahead")`, `register_assets(...)` |
| `conf.py` | `CRUD_VIEWS_TYPEAHEAD` → frozen `TypeaheadConfig` dataclass; only module touching `django.conf.settings` |
| `assets.py` | Django-free: `bundle()`, `source_files()` |
| `lookups.py` | `TypeaheadLookup`, `UserLookup`, `register_lookup`, `register_user_lookup`, `get_lookup` |
| `tokens.py` | `make_token(name, params)`, `read_token(token)` |
| `views.py` / `urls.py` | the endpoint; `app_name = "crud_views_typeahead"`, URL name `lookup` |
| `fields.py` | `TypeaheadField`, `TypeaheadBinding` |
| `filters.py` | `TypeaheadFilter` |
| `widgets.py` | `TypeaheadInput` |
| `templates/crud_views_widget_typeahead/typeahead.html` | default (Bootstrap 5) widget template |
| `static/crud_views_widget_typeahead/typeahead.js`, `typeahead.css` | default frontend |

## 1. Server core

### Settings (`CRUD_VIEWS_TYPEAHEAD`)

| Key | Default | Meaning |
|---|---|---|
| `EMIT` | `True` | emit our assets via `{% cv_js %}`/`{% cv_css %}`; `False` for skins or pipeline delivery |
| `TEMPLATE` | `"crud_views_widget_typeahead/typeahead.html"` | widget template (skin hook) |
| `DEBOUNCE_MS` | `250` | input debounce passed to the frontend |

Per-lookup knobs (`min_chars`, `max_results`, …) stay on the lookup class.

### Lookups

```python
class TypeaheadLookup:
    search_fields: list[str] = []   # icontains; every word must match some field
    ordering: list = []
    max_results = 10
    min_chars = 2
    login_required = True

    def get_queryset(self, request, **params) -> QuerySet: ...  # allowed set + permission check
    def label(self, obj) -> str: return str(obj)
    def filter(self, queryset, q) -> QuerySet: ...
```

- `filter()`: split `q` on whitespace; for each word build an OR of
  `<field>__icontains=word` over `search_fields`; AND the words; `distinct()`;
  `order_by(*ordering)` if set. Non-empty `q` with empty `search_fields` →
  `ImproperlyConfigured`.
- `UserLookup(TypeaheadLookup)`: `search_fields = ["first_name", "last_name",
  "username"]`, ordering `Lower("last_name"), Lower("first_name"), Lower("username")`,
  `label` = `get_full_name()` or `username`.
- `get_queryset` may raise `PermissionDenied` / `Http404`.

### Registry

- `@register_lookup("app.name")` — class decorator, registers an instance.
- `register_user_lookup("app.name", base=UserLookup)` — decorator for a function
  `(request, **params) -> QuerySet`; builds a `base` subclass whose `get_queryset`
  calls the function.
- `get_lookup(name)` → instance; unknown name → `LookupNotFound`
  (subclass of `ImproperlyConfigured`).
- Registering a name twice → `ImproperlyConfigured`.
- `ready()` runs `django.utils.module_loading.autodiscover_modules("typeahead")`, so
  each installed app's `typeahead.py` is imported (admin-style).

### Token

- `make_token(name, params)`: `signing.dumps({"l": name, "p": params},
  salt="crud_views.typeahead", compress=True)`. Validates at bind time: lookup is
  registered, `params` is a dict, `json.loads(json.dumps(params)) == params`
  (rejects UUIDs/dates/model instances → `ImproperlyConfigured` telling the
  developer to pass `str(...)`).
- `read_token(token)` → `(name, params)`; raises `BadToken` on bad signature,
  wrong shape, non-dict params or unknown lookup.
- **No expiry**: permission is re-checked on every request through
  `get_queryset(request, **params)`, so forms left open overnight keep working. A
  leaked token grants nothing beyond what the requesting user may see.

### Endpoint

`GET <mount>/?t=<token>&q=<term>` — project includes
`path("typeahead/", include("crud_views_widget_typeahead.urls"))` (any prefix);
widgets reverse `crud_views_typeahead:lookup`. View is `never_cache`, GET only.

| Case | Response |
|---|---|
| non-GET | 405 |
| bad/missing token, unknown lookup, non-dict params | 400 `{"error": "bad_token"}` |
| `login_required` and anonymous | 403 `{"error": "login_required"}` (JSON, **not** a redirect — `fetch` must not receive HTML) |
| `PermissionDenied` from the lookup | 403 `{"error": "forbidden"}` |
| `Http404` from the lookup | 404 `{"error": "not_found"}` |
| `len(q.strip()) < min_chars` | 200 `{"results": [], "count": 0}`, no query executed |
| otherwise | 200 `{"results": [{"value": "...", "label": "..."}], "count": n}` |

`count` is the filtered queryset's `count()` before slicing to `max_results`.
Error bodies never echo exception messages.

## 2. Field, filter, widget

### `TypeaheadField(ModelChoiceField)`

```python
assignee = TypeaheadField(lookup="app.team_members")

def __init__(self, *args, request, team, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields["assignee"].bind(request, team=str(team.pk))
```

- Constructed with `queryset=None`, default widget `TypeaheadInput`.
- `bind(request, **params)`: resolve lookup, `self.queryset =
  lookup.get_queryset(request, **params)`, set `self.widget.binding =
  TypeaheadBinding(token=make_token(...), lookup_name=..., queryset=self.queryset)`.
  Returns `self`.
- `TypeaheadBinding` is a frozen dataclass with no reference back to the field.
  `Widget.__deepcopy__` is shallow, so copies may share a binding object; re-binding
  a copy replaces only that copy's attribute (designs out the §6 bound-method
  gotcha).
- Unbound `clean()` or render → `ImproperlyConfigured("TypeaheadField 'x' is not
  bound — call field.bind(request, ...)")`.
- `PermissionDenied`/`Http404` from `get_queryset` during `bind()` propagate (the
  page would deny anyway).

### `TypeaheadFilter(django_filters.ModelChoiceFilter)`

- `field_class = TypeaheadField`; `lookup=` passed through to the field; widget
  defaults to `submit_on_clear=True`.
- `bind(request, **params)` → `self.field.bind(...)`. Called in the FilterSet's
  `__init__`; `Filter.field` is cached and the filter form deep-copies it later, so
  the binding survives.
- URLs stay `?assignee=<pk>`. django-filter is a transitive dependency of
  django-crud-views; no new dependency.

### `TypeaheadInput(forms.Widget)`

- `template_name` = `conf.TEMPLATE` unless overridden per instance.
- `submit_on_clear` constructor kwarg (default `False`).
- `use_required_attribute()` → `False` (required is enforced server-side; a
  `required` visible input would accept text without a pk).
- No `Media` class — assets are page-global via the registry.
- `value_from_datadict`: default (`data.get(name)` from the hidden input).

Rendered structure (default template):

```html
<div class="cv-typeahead" data-cv-typeahead
     data-url="/typeahead/?t=..." data-min-chars="2" data-debounce="250"
     data-submit-on-clear="false"
     data-i18n-more="…" data-i18n-none="…" data-i18n-count="…" data-i18n-error="…">
  <div class="input-group">
    <input type="text" id="id_assignee" class="form-control" autocomplete="off"
           role="combobox" aria-autocomplete="list" aria-expanded="false"
           aria-controls="id_assignee_listbox"
           aria-describedby="[django's ids] id_assignee_hint" value="Jane Doe">
    <button type="button" class="btn btn-outline-secondary" data-cv-typeahead-clear
            aria-label="…" hidden>×</button>
  </div>
  <input type="hidden" name="assignee" id="id_assignee_value" value="42" autocomplete="off">
  <ul id="id_assignee_listbox" class="dropdown-menu" role="listbox" aria-label="…" hidden></ul>
  <span id="id_assignee_hint" class="visually-hidden">…keyboard hint…</span>
  <span class="visually-hidden" aria-live="polite" data-cv-typeahead-status></span>
</div>
```

- The visible input keeps the field's `id` (so `<label for>` and Django 5.2's own
  `aria-describedby` target it) and has **no `name`**.
- `get_context` **appends** the hint id to any existing `aria-describedby` from
  `attrs` (never hardcoded; no duplicates).
- Value → text: resolve the pk via `binding.queryset.filter(pk=value).first()`,
  catching `ValueError`/`ValidationError`/`TypeError` for garbage. Resolved →
  visible text `lookup.label(obj)`, hidden value `str(obj.pk)`. Unresolved →
  **both** empty (a garbage or out-of-scope pk is never round-tripped). This also
  re-renders the label after a validation error.
- All user-visible strings (hint, "N more – keep typing", "No results",
  "N results", "Search failed", clear button label) are translatable and passed as
  data attributes / template text; the JS has no i18n of its own.

Documented widget context for skins: `widget.attrs` (the visible input's attributes:
id, ARIA, merged `aria-describedby`) and `widget.typeahead` with `url`, `label`, `value`,
`hidden_name`, `hidden_id`, `listbox_id`, `hint_id`, `min_chars`, `debounce`,
`submit_on_clear`, `i18n` (dict: `hint`, `more`, `none`, `count`, `error`, `clear`,
`listbox`; `{n}` is the number placeholder).

## 3. Frontend, skins, asset delivery

### Default frontend (`typeahead.js`, vanilla, ~350 lines)

Initialisation:

- `init(root)` processes every `[data-cv-typeahead]` under `root`; idempotent via
  `data-cv-typeahead-ready`.
- Runs on `DOMContentLoaded` and on the `cv:modal:loaded` CustomEvent dispatched on
  `#cv-modal` by crud_views.
- Public API: `window.cvTypeahead.init(root)` only (for dynamically added content;
  crud_views' `formset.js` fires no event, so added formset rows need a manual call —
  documented, auto-init deferred).

Behaviour contract (§5 of the input):

- **Fetching**: debounce `data-debounce` ms; each request has an `AbortController`;
  a new keystroke aborts the previous request; stale responses never render. Below
  `min_chars`: no request, list closed.
- **Selection**: sets hidden pk, visible text = label, remembers the label as the
  *committed text*, dispatches a bubbling `change` event on the hidden input.
- **Invariant**: visible text = committed label except while typing. Restored on
  `focusout` and on form `submit` (capture listener). The pk is cleared only by the
  clear button or by blurring with fully emptied text.
- **Keyboard**: ↑/↓ move `aria-activedescendant` and preview the text only (pk
  unchanged); Enter with the list open selects the active option (or does nothing if
  none) and always `preventDefault()`s; with the list closed Enter submits normally;
  Escape closes and restores; Tab closes.
- **Blur**: closes the list, clears the debounce timer, aborts in-flight requests.
  Option list uses `mousedown` + `preventDefault` so clicking does not blur first.
- **Rendering**: options built with `textContent` + `<mark>` nodes; never
  `innerHTML` (escaping by construction, Trusted-Types friendly). Highlighting per
  word, case-insensitive. `count > results.length` → a non-selectable "N more –
  keep typing" row. Zero results → "No results" row.
- **Clear button**: visible only while a pk is set; clears text and pk, dispatches
  `change`; with `data-submit-on-clear="true"` calls `form.requestSubmit()`.
- **ARIA**: `aria-expanded` kept in sync; options have `role="option"` and ids;
  polite live region announces the result count; keyboard hint via
  `aria-describedby`.
- **Errors**: non-2xx or network error → close list, announce "Search failed" in
  the live region, `console.warn`; no retry.

### CSP

No inline scripts or styles; configuration in data attributes; show/hide via the
`hidden` attribute and classes, never `style=`. The script tag comes from
`{% cv_js %}`, which carries the CSP nonce.

### Asset delivery

- `assets.py` (Django-free): `bundle()` → `{"js": ["crud_views_widget_typeahead/typeahead.js"],
  "css": ["crud_views_widget_typeahead/typeahead.css"]}`; `source_files()` returns
  the same static paths for a project's django-pipeline bundle in `settings.py`.
- `ready()`: `register_assets(key="typeahead", js=..., css=..., emit=cfg.emit)`.
- No CDN/vendored mode, vendor command or W330-style checks — there is no
  third-party plugin.

### Skin contract

A skin (e.g. a design-system package) provides:

1. a template via `CRUD_VIEWS_TYPEAHEAD["TEMPLATE"]` (or per-widget
   `template_name`) consuming the documented widget context;
2. its own JS (and CSS) registered under its own asset key, with
   `CRUD_VIEWS_TYPEAHEAD["EMIT"] = False` to suppress ours.

It must keep the hidden-input semantics (has `name`, carries the pk,
`autocomplete="off"`, empty when nothing is selected) and consume the endpoint JSON
(`results[].value`, `results[].label`, `count`). The README documents the §5
behaviours as the expected contract for skins.

## 4. Testing

### Package tests (`tests/`)

`conftest.py` additions: `django_filters` and
`crud_views_widget_typeahead.apps.CrudViewsWidgetTypeaheadConfig` in
`INSTALLED_APPS`, `ROOT_URLCONF="tests.urls"` (new module including the typeahead
URLconf). Test data uses only `auth.User` and `auth.Group` (a group is the
"container", lookups scoped by `group=<id>`); no test models or migrations.

| File | Covers |
|---|---|
| `test_typeahead_lookups.py` | multi-word AND across fields, distinct, ordering, `ImproperlyConfigured` on empty `search_fields`, duplicate registration, `register_user_lookup`, `UserLookup` label fallback, autodiscovery |
| `test_typeahead_tokens.py` | round-trip, tampered signature, wrong shape, unknown lookup and non-JSON params rejected at `make_token` |
| `test_typeahead_view.py` | the full status table, anonymous → JSON 403 (no redirect), below `min_chars` → no query (`django_assert_num_queries(0)`), `count` before slicing, scope enforced (user outside the group never returned) |
| `test_typeahead_fields.py` | `bind()` sets queryset, unbound render/clean → `ImproperlyConfigured`, out-of-scope pk → validation error, re-binding a deep copy leaves the original untouched |
| `test_typeahead_widget.py` | rendered HTML: visible input without name, hidden `autocomplete="off"`, label re-rendered from pk, garbage/unknown pk → empty text and empty hidden, `aria-describedby` merged without duplicates, template override via setting and `template_name`, `use_required_attribute` false |
| `test_typeahead_filter.py` | `TypeaheadFilter.bind` survives the filter form's deep copy, `?user=<pk>` filters, `submit_on_clear` default |
| `test_typeahead_assets.py` | `assets.py` importable without Django, registry registration, `EMIT=False` |

### JS verification

A scripted browser checklist against the example app is an explicit plan task:
typing/debounce, abort on fast typing, keyboard navigation and preview, Enter with
list open vs. closed, Escape/Tab, blur within the debounce window, restore on
focusout and submit, clear button and submit-on-clear, "N more" row, zero results,
error state (e.g. logged out), inside a crud_views modal, ARIA attributes in the
DOM, no CSP/console errors.

## 5. Example app (`examples/bootstrap5/typeahead/`)

- Models: `Team` (`name`, `members` M2M to `User`), `Task` (`title`, `team` FK,
  `assignee` FK to `User`).
- Seed (`seed.py`): ~3,000 users via `bulk_create`, a few teams with ~500 members
  each, some tasks.
- `typeahead/typeahead.py`: `register_user_lookup("typeahead.team_members")` →
  `Team.objects.get(pk=team).members.all()` (`Http404` on missing team) and
  `register_user_lookup("typeahead.any_member")` → users that are a member of any
  team (`distinct()`); both autodiscovered.
- Team ViewSet (list/detail) and a Task ViewSet as its child (team fixed by URL): create/update form binds
  `assignee` with `team=str(team.pk)`; works as page and in a crud_views modal.
- Task list filter: `TypeaheadFilter(lookup="typeahead.any_member")` on `assignee`.
- One `Feature` entry (viewset `task`) with about / look-at texts.
- `project/settings.py`: add the app, `django_filters` already present; URL
  include of `crud_views_widget_typeahead.urls`.
- `typeahead/tests.py`: pages render, endpoint scoped to the team, non-member pk
  rejected on save, filter URL round-trip, edit form shows the label.

## 6. Wiring and docs

- CI: add `--cov=crud_views_widget_typeahead` to the pytest invocations.
- README: typeahead section — quickstart (install app, include URLs, define a
  lookup, bind a field/filter), lookup API, settings, skin contract.
- CLAUDE.md: architecture entry for the new app, updated test count.
- Version bump (0.3.0) happens at release, not in this work.
