# Idea: a typeahead (remote autocomplete) widget for django-crud-views-extensions

Input for a brainstorm in `django-crud-views-extensions`: a reusable
type-ahead select for large model choice sets (thousands of users), with
suggestions loaded from the server, usable in forms and django-filter
filters.

A working implementation of this design already exists in another
Django project. There it was built on top of a design system's own typeahead
component. This document separates the parts of that design that are
framework-generic (candidates for this package) from the parts that were
specific to that design system.

---

## 1. Motivation and scope

- `<select>` stops working for model choices beyond a few hundred options
  (the motivating case: ~10,000 eligible users, containers with ~1,000
  members).
- The allowed set is usually context-dependent (»members of *this*
  container«, »users visible on *this* page«) and permission-sensitive — the
  endpoint must never reveal more than the page itself would.
- A generic version would let other projects drop
  django-autocomplete-light/Select2 (see section 2).

Considerations when placing it in this package:

1. **Dependency direction.** The generic core (registry, signing, one view, a
   form field) is plain Django and does not need django-crud-views. A
   `crud_views_widget_*` app requires `django-crud-views >= 0.11` (asset
   registry). Packages that use the widget but not crud_views would inherit
   that dependency.
2. **»Skins« need template *and* JS.** A design system that ships its own
   typeahead component defines a DOM contract and an init API. Overriding
   only the widget template is not enough; the JS adapter must be swappable
   too.
3. **The datetimepicker asset machinery** (CDN/vendored modes, vendor
   command, W330/W331 checks) exists to deliver a third-party plugin. Whether
   the typeahead needs it depends on the frontend choice (section 7).
4. **Consumers pinning with `exclude-newer`** (e.g. a 5-day rule) can't
   install a fresh release immediately — relevant if the package is iterated
   quickly while consumers adopt it.

---

## 2. Prior art in use: django-autocomplete-light + Select2

Observed in an existing project:

- Packages: `django-autocomplete-light>=3.12.1` (`dal`, `dal_select2` in
  `INSTALLED_APPS`), Select2 frontend, requires jQuery.
- Server: one view per lookup, `dal_select2.views.Select2QuerySetView`
  (`apps/<app>/views/auto_complete/{user,item}.py`), URLs
  `autocomplete-user` / `autocomplete-item`.
- Use: `widget=dal_select2.widgets.ModelSelect2(url="autocomplete-user")` on
  django-filter `ModelChoiceFilter`s (`apps/<app>/views/project.py`).
- Styling patch: `<app>/js/patch_select2_height.js` (Select2 doesn't fit
  plain Bootstrap without it).
- Problems found while reading it:
  - both autocomplete URLs carry `# todo: auth` — no login/permission check;
  - `UserAutocomplete.get_queryset` never builds its filter (`flt` starts as
    `None`, `if flt:` guards the OR-combination) → typing filters nothing;
  - the restriction (»users assigned to any Project«) is written twice:
    once in the filter's `queryset=`, once in the autocomplete view.

---

## 3. Anatomy of this repo (as of v0.1.2)

- Apps named as if they lived in django-crud-views (`crud_views_widget_*`)
  so they can move into the main package without import changes — **public
  import paths and settings keys are part of the contract**.
- Only app today: `crud_views_widget_datetimepicker` — widgets emit a JSON
  config attribute, `init.js` turns inputs into pickers; **no `Media`
  classes**: assets are page-global via `{% cv_js %}`/`{% cv_css %}` through
  the crud_views **asset registry** (`register_assets` in `AppConfig.ready()`).
- `assets.py` is Django-free (importable from `settings.py`) so the same path
  list feeds the registry, the vendoring command/checks and a project's
  django-pipeline bundle (`source_files()`).
- Settings dict `CRUD_VIEWS_DATETIMEPICKER` (`SOURCE` cdn|vendored, `VERSION`,
  `CDN_BASE`, `VENDOR_DIR`, `EMIT`, `LANG`, `DEFAULTS`).
- jQuery is a prerequisite (same rule as crud_views core).
- Tests: `settings.configure()` in `tests/conftest.py`, `PIPELINE={}` seeded.

---

## 4. The proven design (candidate generic core)

### Lookup registry (server)
```python
class TypeaheadLookup:
    search_fields: list[str] = []   # icontains; every word must match some field
    ordering: list = []
    max_results = 10
    min_chars = 2
    login_required = True
    def get_queryset(self, request, **params): ...  # the allowed set + permission check
    def label(self, obj) -> str: ...
    def value(self, obj) -> str: ...                # str(obj.pk)
    def filter(self, queryset, q): ...              # multi-word AND, distinct, ordering

@register_lookup("app.name")                         # class decorator
@register_user_lookup("app.name", base=UserLookup)   # function (request, **params) -> QuerySet
```
- `UserLookup`: `search_fields = first_name, last_name, username`, ordering
  `Lower(last_name), Lower(first_name), Lower(username)`, label = full name or
  username.
- Empty `search_fields` with a search term → `ImproperlyConfigured`.

### Signed token instead of per-lookup URLs
- The widget carries `signing.dumps({"l": name, "p": params}, salt=...)`.
  The browser cannot change lookup or params (e.g. another container id).
- **No expiry**: permission is re-checked on every request via
  `get_queryset(request, **params)` — forms left open overnight still work.
- Params must be JSON-serialisable (UUIDs as `str`).

### One generic endpoint
`GET …/typeahead/?t=<token>&q=<term>` →
`{"results": [{"term", "value"}], "count": n}`:
400 bad/unknown token or non-dict params · 403 JSON when `login_required` and
anonymous (**not** `@login_required` — a redirect would make `fetch` receive
HTML) · 403/404 from `PermissionDenied`/`Http404` in the lookup · empty result
without a query when `len(q) < min_chars` · `GET` only.

### Field binding = single source of truth
```python
user = UserTypeaheadField(lookup="app.candidates")
# in the form's / FilterSet's __init__:
self.fields["user"].bind(request, container=str(pk))
```
`bind()` sets the field's `queryset` from the lookup (so save-time validation
uses exactly the suggestion set) and gives the widget the token URL. Unbound
field → `ImproperlyConfigured` on render and on `clean()`.
For django-filter: a `ModelChoiceFilter` subclass with
`field_class = UserTypeaheadField`, bound via
`self.filters["user"].field.bind(self.request, …)` in the FilterSet's
`__init__` — `Filter.field` is cached, the filter form is built later and
deep-copies the fields. Filters default to `submit_on_clear=True`.

### Widget contract
Visible text input **without `name`** + hidden input with `name` and the pk
(filter URLs stay `?user=<pk>`), text re-rendered from the pk after a
validation error, unknown/garbage pk → empty text.

### Approaches considered for "how does the endpoint know the scope"
- **A — named lookup + signed params** (chosen).
- B — queryset pickled into the cache (django-select2 style): breaks with
  per-process LocMem cache across gunicorn workers and with forms open longer
  than the cache TTL.
- C — one view per use case (dal style): restriction written twice, auth per
  view (forgotten in the prior art above).

---

## 5. Frontend behaviour any skin must provide

The reference implementation adapted a design system's typeahead component
(markup per its pattern, JS adapter calling the component's `setOptions`
after it initialised). Independent of the component, these behaviours had to
be added on top and belong to the widget's contract:

- hidden-pk sync on selection; invariant »visible text = label of the stored
  pk, except while typing« (restore on `focusout` and on `submit`, clear only
  via a clear button or fully emptied text);
- arrow-key preview changes only the text, never the pk;
- Enter must not submit the form while the suggestion list is open; with the
  list closed it submits as usual;
- own HTML escaping + highlighting of the search term (don't trust a
  component's pre-built highlight HTML);
- »N more results – keep typing« needs the server's total `count`;
- a clear button (`submit_on_clear` for filters);
- ARIA: `role="combobox"`, `aria-expanded`, `aria-autocomplete="list"`,
  listbox with `aria-label`, a screen-reader hint for keyboard use, live
  region with the result count.

---

## 6. Gotchas found during the reference implementation

- A component whose `setOptions()` immediately refreshes the list will fetch
  and open it on page load when the input is prefilled (edit forms). Blank
  the input around the call.
- A component's own »block Enter« logic may only check the input's direct
  parent; wrapping the input (e.g. in an `input-group` for a clear button)
  defeats it.
- Django 5.2's `attrs.html` emits its own `aria-describedby`
  (`…_helptext`/`…_error`); a hardcoded one in the widget template duplicates
  it and screen readers lose help text and errors → merge in `get_context`.
- Firefox restores script-changed hidden inputs on reload while the visible
  input (`autocomplete="off"`) is not restored → give the hidden input
  `autocomplete="off"` too.
- Clicking away within the debounce window could reopen the list on an
  unfocused field → close/cancel pending requests on blur.
- `Widget.__deepcopy__` is shallow: a bound method stored on the widget still
  points at the original field after copying (harmless in the form/filter
  flow, wrong if a copied bound field is re-bound).
- `distinct()` + `order_by(Lower(...))` is fine on Postgres (Django adds the
  expressions to the SELECT list).

---

## 7. Open questions for the brainstorm

- **Default frontend** for plain Bootstrap 5 / crud_views pages: which
  library (or own vanilla JS)? Not evaluated yet — research accessibility,
  no-jQuery, CSP compatibility, size.
- **Asset delivery:** asset registry (`cv_js`) like the datetimepicker vs.
  `Widget.media` (CSP nonce via middleware).
- **Skin mechanism:** how does a design-system package replace template *and*
  JS while reusing the server core? (e.g. widget `template_name` +
  frontend-agnostic data attributes + swappable init script.)
- **Package placement:** the generic core does not need crud_views at all —
  does it belong in a `crud_views_*` app, or in a standalone app that
  crud_views apps build on?
- **ViewSet integration:** a real crud_views fit would be a lookup view key
  on a ViewSet reusing its permission checks — bigger, but the only part that
  genuinely needs crud_views.
- **Migration path for the dal-based project:** replace `dal` widgets/views
  with lookups; fix the auth gap and the broken multi-token search on the way.
