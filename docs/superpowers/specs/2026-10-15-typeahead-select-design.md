# Typeahead select popup (`TypeaheadSelect`) — design

Date: 2026-10-15
Status: approved in brainstorming, pending spec review
Builds on: `docs/superpowers/specs/2026-10-15-typeahead-design.md` (server core unchanged except paging)

## Goal

A second frontend for `crud_views_widget_typeahead` with a real dropdown/select feeling:
the closed widget looks like a Bootstrap `<select>`, opening it shows a popup with a
search field and a scrollable, server-paged list. It reuses the whole server core
(lookups, `bind()`, signed tokens, the one endpoint) and coexists with the existing
text typeahead, chosen per field.

Success criteria:

- Single-select with browse-on-open (for lookups that allow it), search, and
  scroll-to-load-more over thousands of rows.
- Works on crud_views pages, inside crud_views modals (Escape must not close the
  modal), in django-filter filters, and under a strict CSP (no `'unsafe-inline'`).
- No third-party JS (no jQuery, no Select2); no `innerHTML`; no `style` writes.
- The text typeahead's behaviour, template, JS and settings are untouched (only the
  endpoint's result order gains a `pk` tiebreaker, see §3).

## Background: why not django-autocomplete-light / Select2

A throwaway spike (DAL 5.0.0 `ModelSelect2` driven by our `binding`, Select2-format
endpoint over the lookup registry, example app) showed DAL can sit on our backend,
but:

- DAL 5 ships no Select2/jQuery: it loads Django admin's vendored Select2 4.0.13
  (`django.contrib.admin` required) and needs `django>=5.2` (crud_views allows `>=4.2`).
- In a crud_views (Bootstrap 5) modal the body-appended dropdown (`z-index: 1051`)
  sits under the modal (`1055`) and the modal's focus trap steals focus: unusable
  until `dropdownParent` is set via a custom init function. Escape in the open
  dropdown closes the whole modal.
- Select2 4.0.13 sets no `aria-activedescendant`, has no live region, and opens only on
  Enter/Space/Alt+↓ (`select2.full.js:5713`).
- The selected option re-rendered after reload used `str(obj)`, not `lookup.label`.
- Bootstrap 5 styling needed patching (double caret, clipped label).

Multi-select/tags (Select2's main advantage) are not needed, so we build the popup.

## Decisions taken in brainstorming

| Topic | Decision |
|---|---|
| Frontend | Own vanilla JS, no DAL/Select2/jQuery |
| Scope | Single-select only |
| Interaction model | Select2-style popup: trigger button + popup with search field and list |
| Coexistence | Per field: new widget class `TypeaheadSelect` in `crud_views_widget_typeahead`; same field, filter, `bind()`, lookups, endpoint |
| More results | Scroll loads the next page; endpoint gains a `page` parameter |
| Browse on open | Decided by the lookup: `min_chars = 0` browses; otherwise "Type at least N characters" in the popup |
| JS structure | Approach A: self-contained `typeahead-select.js`/`.css`, own asset bundle and own `EMIT` switch; ~60 lines of helpers duplicated from `typeahead.js` rather than shared |
| Example filter | The task list filter switches to `TypeaheadSelect` |

Rejected: a shared JS core (B) and one JS file with two classes (C). Both modify the
shipped `typeahead.js` and couple the two widgets' asset delivery, so a skin setting
`EMIT = False` for the text typeahead would break or replace the popup too.

## Package changes

`src/crud_views_widget_typeahead/` (module names are public import paths):

| Module | Change |
|---|---|
| `widgets.py` | new `TypeaheadSelect(TypeaheadInput)` |
| `views.py` | optional `page` parameter; total ordering before slicing |
| `conf.py` | `SELECT_EMIT`, `SELECT_TEMPLATE` |
| `assets.py` | `SELECT_JS`, `SELECT_CSS`, `select_source_files()`, `select_bundle()` |
| `apps.py` | second `register_assets(key="typeahead_select", ...)` |
| `templates/crud_views_widget_typeahead/typeahead_select.html` | new default popup template |
| `static/crud_views_widget_typeahead/typeahead-select.js`, `typeahead-select.css` | new popup frontend |

Unchanged: `fields.py`, `filters.py`, `lookups.py`, `tokens.py`, `urls.py`,
`typeahead.html`, `typeahead.js`, `typeahead.css`.

## 1. Widget and template contract

### Python

`TypeaheadSelect(TypeaheadInput)` reuses `binding`, `resolve()` (pk or instance →
allowed object, `None` for empty/garbage/out-of-scope), the unbound-widget
`ImproperlyConfigured`, `use_required_attribute() -> False`, `submit_on_clear`, and the
`aria-describedby` merge (Django's `<id>_helptext` / `<id>_error` are kept; never set on
`widget.attrs`).

Usage:

```python
assignee = TypeaheadField(lookup="typeahead.team_members", widget=TypeaheadSelect())
user = TypeaheadFilter(lookup="typeahead.any_member", widget=TypeaheadSelect(submit_on_clear=True))
```

`TypeaheadFilter` already uses `kwargs.setdefault("widget", ...)`, so passing a widget
overrides the default.

Template: `template_name` argument, else `CRUD_VIEWS_TYPEAHEAD["SELECT_TEMPLATE"]`
(default `"crud_views_widget_typeahead/typeahead_select.html"`). It is independent of
`TEMPLATE`.

### Context

`widget.attrs` apply to the **trigger button** (it keeps the field id, so
`<label for>` labels it; buttons are labelable elements). The widget sets on it:
`class` merged with `form-select text-start`, `type="button"`,
`aria-haspopup="listbox"`, `aria-expanded="false"`, `aria-controls=<popup_id>`, and the
`aria-labelledby="<id> <id>_label"` (a `<label for>` would otherwise replace the button's content as its name;
the self-reference yields the label text, then the value/placeholder span, as in the APG select-only combobox),
and the merged `aria-describedby`. It drops the text typeahead's input-only attributes
(`role="combobox"`, `aria-autocomplete`, `autocomplete`).

`widget.typeahead` carries everything `TypeaheadInput` provides (`url`, `label`,
`value`, `hidden_name`, `hidden_id`, `listbox_id`, `hint_id`, `min_chars`, `debounce`,
`submit_on_clear`, `i18n`) plus:

| Key | Value |
|---|---|
| `popup_id` | `<id>_popup` |
| `search_id` | `<id>_search` |
| `page_size` | `lookup.max_results` |

`label` is `lookup.label(obj)`, never `str(obj)`.

Additional `i18n` keys:

| Key | Default text |
|---|---|
| `placeholder` | "Select…" |
| `search` | "Search" (accessible name of the search field) |
| `loading` | "Loading…" |
| `type_more` | "Type at least %(count)d character(s)." (ngettext, `min_chars`) |
| `hint` | "Open with Enter or the arrow keys, type to search, choose with Enter." |

`none`, `count`, `error`, `clear`, `listbox` are reused from `TypeaheadInput`; `more` is
not used.

### Markup (default template)

```
div.cv-typeahead-select [data-cv-typeahead-select, data-url, data-min-chars,
                         data-debounce, data-page-size, data-submit-on-clear, data-i18n-*]
├─ button.form-select.text-start     (widget.attrs)
│    └─ span#<label_id> [data-cv-typeahead-select-label]   label, or placeholder (muted)
├─ button [data-cv-typeahead-select-clear] ×    aria-label=i18n.clear; hidden when empty
├─ input type=hidden name=<name> id=<hidden_id> value=<pk> autocomplete=off
├─ div.cv-typeahead-select-popup#<popup_id> [hidden]   positioned inside the root; NOT .dropdown-menu
│                                               (Bootstrap's Escape handler throws on it)
│    ├─ input type=search id=<search_id> role=combobox aria-autocomplete=list
│    │        aria-expanded aria-controls=<listbox_id> aria-label=i18n.search
│    └─ ul#<listbox_id>.dropdown-menu.show tabindex=-1 role=listbox aria-label=i18n.listbox
│             (made static by our CSS; tabindex=-1 keeps the scroll container out of the Tab order)
├─ span#<hint_id>.visually-hidden               i18n.hint
└─ span.visually-hidden aria-live=polite [data-cv-typeahead-select-status]
```

Hidden-input contract (same as the text typeahead): it carries the `name` and the pk,
is empty when nothing is selected, and filter URLs stay `?user=<pk>`.

The popup lives **inside the widget root**, not in `<body>`. That is what failed in the
spike: a body-level dropdown under a Bootstrap 5 modal is covered by it and loses focus
to its focus trap. Known risk, covered by the browser checklist: clipping by ancestors
with `overflow: hidden` or a `modal-dialog-scrollable` modal.

ARIA: there is no WAI-ARIA Authoring Practices pattern for "button + search field in a
popup", so no compliance with one is claimed. The design combines a button with
`aria-haspopup`/`aria-expanded` and the APG editable-combobox semantics on the search
field (`role=combobox`, `aria-controls`, `aria-activedescendant`, live result count).
What screen readers announce is checked in the browser checklist and reported as found.

## 2. Frontend behaviour (`typeahead-select.js`)

- Vanilla JS, no globals except `window.cvTypeaheadSelect = {init(root)}`.
- Initialises `[data-cv-typeahead-select]` (once per element, marked with a data flag)
  on `DOMContentLoaded` and on the bubbling `cv:modal:loaded` event (dispatched by
  crud_views on `#cv-modal` after injecting content).
- Option text is built from text nodes and `<mark>` elements (search-word
  highlighting); never `innerHTML`. Never writes `element.style`; visibility via the
  `hidden` attribute and classes.
- After every selection or clear, the hidden input dispatches a bubbling `change` event.

### Closed (focus on the trigger)

| Input | Effect |
|---|---|
| click, Enter, Space, ↓, ↑, Alt+↓ | open |
| printable character (no Ctrl/Alt/Meta) | open with that character in the search field (then search) |
| clear button | hidden input `""`, label shows placeholder, `change`; with `submit_on_clear` `form.requestSubmit()`, else focus the trigger |

The trigger is `type="button"`: it never submits the form.

### Open (focus in the search field)

- On open: trigger and search field `aria-expanded="true"`; popup shown; focus moves to
  the search field. With `min_chars = 0`, page 1 is fetched with `q=""`. Otherwise the
  list shows one non-selectable info row with `i18n.type_more`.
- Typing: debounced by `DEBOUNCE_MS`. A new query aborts the request in flight
  (`AbortController`) and loads page 1. Below `min_chars`, the list shows
  `i18n.type_more`; nothing is fetched.
- ↓ / ↑: move the active option (wrapping only once every page is loaded; while more pages exist ↓ stays on the last loaded option and loads the next page, ↑ without an active option goes to the first). Sets `aria-activedescendant` on the search
  field, `.active` and `aria-selected="true"` on the option, scrolls it into view.
  The trigger keeps showing the committed label (no preview).
- Enter: always `preventDefault()` (never submits while open). With an active option:
  select it (hidden value, trigger label, close, focus trigger, `change`).
  Without one: nothing.
- Escape: `preventDefault()` and `stopPropagation()` (a surrounding Bootstrap modal
  must stay open), close, focus trigger; value unchanged.
- Tab: close; value unchanged; focus moves on naturally.
- Focus leaving the widget root (`focusout` whose `relatedTarget` is outside the root)
  or a click outside: close; value unchanged.
- Mouse: `mousedown` on the list is cancelled so focus stays in the search field;
  clicking an option selects it.
- Closing clears the search field and the list, so the next open starts fresh.

### Scroll paging

- State per open search: `query`, `page`, `loaded`, `count`, `pending`.
- On list `scroll`, when the remaining scroll distance is below one option height, and
  `loaded < count` and no request is pending: fetch `page + 1` with the same query and
  append. While it runs, a "Loading…" info row sits at the end of the list.
- Every response is matched against the current `query` and the requested `page`;
  stale responses are dropped.
- The live region announces `i18n.count` (with `{n}` = `count`) after page 1, and
  `i18n.none` for zero results. Later pages do not announce.
- Page 1 replaces the list and resets the active option; later pages append and keep it.

### Errors

A failed request (network, HTTP error, JSON `error`) shows an info row and announces
`i18n.error`; the committed value is never changed. Errors are logged with
`console.warn("cv-typeahead-select:", err)`.

## 3. Endpoint paging (`views.py`)

`GET ?t=<token>&q=<term>&page=<n>`; `page` is optional.

- `page`: 1-based. Missing, non-integer or `< 1` → 1. Lenient on purpose: it cannot
  widen the result set.
- Slice: `queryset[(page - 1) * size : page * size]` with `size = lookup.max_results`.
  A page past the end → `"results": []`, `count` unchanged.
- Response shape unchanged: `{"results": [{"value", "label"}], "count": n}`. Clients
  know there is more while `loaded < count`.
- Unchanged: token check (`bad_token` 400), `login_required` (403),
  `PermissionDenied` → 403, `Http404` → 404, the `min_chars` guard (short query →
  `{"results": [], "count": 0}` on every page), `never_cache`, GET only.

### Total ordering

OFFSET paging over a non-unique order can duplicate or skip rows between pages.
`TypeaheadLookup.ordering` defaults to `[]`, and `UserLookup`'s order (lower-cased
last name, first name, username) is not unique in practice (the example seeds
repeated names). Before slicing, the endpoint appends `pk` as the final order key,
preserving the lookup's ordering: the queryset's explicit `order_by`, else the
model's `Meta.ordering` (when default ordering applies), else nothing. This lives in
the view, not in `TypeaheadLookup.filter()`, because projects may override `filter()`.

Effect on the text typeahead: its first `max_results` results become deterministic;
rows that tie on the lookup's keys may come back in a different order than today. No
row is added or removed.

Not done (YAGNI): keyset/cursor paging, a separate page-size setting, a `more` flag.

## 4. Assets and settings

### `assets.py` (Django-free)

```python
SELECT_JS = f"{APP_LABEL}/typeahead-select.js"
SELECT_CSS = f"{APP_LABEL}/typeahead-select.css"

def select_source_files() -> dict:  # {"js": [SELECT_JS], "css": [SELECT_CSS]}
def select_bundle() -> dict:        # == select_source_files()
```

`source_files()` and `bundle()` keep returning exactly the text-typeahead files (their
output is contract: pipeline configs call them). django-pipeline users add
`select_source_files()` to their bundle explicitly; the README shows it.

### `apps.py`

```python
sb = select_bundle()
register_assets(key="typeahead_select", js=sb["js"], css=sb["css"], emit=cfg.select_emit)
```

Page-global via `{% cv_js %}`/`{% cv_css %}` like every bundle in this repo, so the files
also load on pages without a popup widget. No vendoring, no CDN mode, no system
checks: there is no third-party code.

### Settings (`CRUD_VIEWS_TYPEAHEAD`, keys are contract)

| Key | Default | Meaning |
|---|---|---|
| `SELECT_EMIT` | `True` | `False` suppresses the popup bundle (pipeline delivery, or a skin replacing the popup) |
| `SELECT_TEMPLATE` | `"crud_views_widget_typeahead/typeahead_select.html"` | popup template |

`DEBOUNCE_MS` is shared by both widgets. `EMIT` and `TEMPLATE` keep meaning the text
typeahead only. `TypeaheadConfig` gains `select_emit` and `select_template`.

### CSS (`typeahead-select.css`)

- Root `position: relative`; popup `position: absolute`, full root width, opens below
  the trigger.
- The list has its own `max-height` and `overflow-y: auto` (the scroll-paging element).
- Trigger label truncated with `text-overflow: ellipsis`; placeholder in Bootstrap's
  muted text colour; the clear button sits inside the trigger area, right of the label
  and left of the caret.
- No inline styles anywhere; Bootstrap's `.form-select` and `.dropdown-item` carry the look; the popup
  `div` is skinned by our own CSS (border, background, shadow-less card) and only the inner `<ul>` is a
  (static) `.dropdown-menu`. No theme dependency.

## 5. Testing, example app, docs

### Python tests (`uv run pytest`)

- `tests/test_typeahead_select_widget.py`: renders trigger + clear + hidden + popup
  structure and ids; label via `lookup.label` (not `str`); placeholder when empty;
  garbage and out-of-scope pk → empty; unbound → `ImproperlyConfigured`;
  `aria-describedby` merged with Django's ids; `SELECT_TEMPLATE` and per-widget
  `template_name`; `submit_on_clear` reaches the template; field + widget round-trip
  validates against the bound queryset; `TypeaheadFilter(widget=TypeaheadSelect())`
  keeps `?user=<pk>`.
- `tests/test_typeahead_view.py`: page 1 equals the un-paged response; page 2
  continues without overlap, including across ties in the lookup's order keys; past
  the end → empty with `count`; garbage/`0`/negative `page` → page 1; `min_chars` is
  enforced with `page`; permission errors on any page; ordering appends `pk` while
  keeping explicit and `Meta.ordering`.
- `tests/test_typeahead_assets.py`: `select_source_files()`/`select_bundle()` paths;
  `source_files()`/`bundle()` unchanged; `assets.py` stays importable without Django.
- Registration: `typeahead_select` registered, respecting `SELECT_EMIT`.
- `tests/test_conf.py`: defaults and overrides of `SELECT_EMIT`, `SELECT_TEMPLATE`.
- Static checks on `typeahead-select.js` (in the style of `tests/test_typeahead_js.py`):
  no `innerHTML`, no `.style` assignment, listens for `cv:modal:loaded`, exposes
  `cvTypeaheadSelect`, calls `stopPropagation` for Escape. No JS test toolchain.

### Example app (`examples/bootstrap5/typeahead/`)

- `typeahead.py`: new lookup `typeahead.team_members_browse` (`min_chars = 0`; same scope
  and permission check as `team_members`).
- New modal action **"Pick assignee"** (`cv_key = "pick_assignee"`, `cv_modal = True`):
  `TaskPickForm` with `TypeaheadField(lookup="typeahead.team_members_browse",
  widget=TypeaheadSelect())`. Shows the popup in a crud_views modal, browse-on-open
  and scroll paging (~500 members per team). Added to `TaskListView.cv_list_actions`.
- `TaskFilter.assignee` switches to `TypeaheadSelect(submit_on_clear=True)` on
  `typeahead.any_member` (`min_chars = 2`): popup in a filter and the
  "type at least N characters" path.
- The text typeahead stays on create/update and in the existing "Quick assign" modal,
  so both widgets appear side by side on the task viewset.
- The existing typeahead `Feature` card (`viewset="team"`) gets updated `description`,
  `about` and `look_at` text naming both widgets. No new card: cards are matched to
  pages by viewset, and both widgets live on the same viewsets.
- Example tests: the pick-assignee modal fragment renders the popup; a valid modal
  POST answers 204; the filter renders the popup and `?assignee=<pk>` filters.

### Browser checklist (Playwright against the example, before merge)

1. Open via click, Enter, Space, ↓ and a typed character; focus lands in the search field.
2. Browse on open (pick assignee); scroll to the end of several pages: no duplicates, no gaps.
3. Search, then select by keyboard and by mouse; trigger shows the label; `change` fires.
4. In the modal: popup is above the modal content and receives focus; Escape closes only
   the popup; selecting and saving closes the modal and updates the row.
5. Enter never submits while the popup is open; Enter on the closed trigger opens it.
6. Clear button; in the filter it submits (`submit_on_clear`).
7. Filter: below 2 characters shows "Type at least 2 characters"; result submits `?assignee=<pk>`
   and the label renders after reload.
8. Strict CSP (Django 6 CSP middleware, `style-src` without `'unsafe-inline'`): zero
   violations across a full cycle, with a positive control proving violations are reported.
9. Clipping: popup inside a `modal-dialog-scrollable` modal and inside an
   `overflow: hidden` container; record the result.
10. German locale (`de`): i18n strings.
11. Accessibility tree: what the trigger, search field, active option and live region
    expose; reported as found.
12. Both widgets on one page (task update page + filter on the list) do not interfere.

### Docs

- README: "Select popup" section: usage, `min_chars = 0` to browse, `SELECT_EMIT` /
  `SELECT_TEMPLATE`, pipeline `select_source_files()`, and the popup's skin contract
  (context keys, hidden-input contract, required behaviours from §2).
- CLAUDE.md: architecture bullets for `TypeaheadSelect`, `typeahead-select.js` and
  endpoint paging; update the test count.

## Out of scope

Multi-select, tags/create-on-the-fly, a shared JS core, automated JS tests, changes to
the text typeahead's behaviour (apart from the `pk` tiebreaker in §3), DAL/Select2
compatibility.
