# Typeahead Select Popup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `TypeaheadSelect`, a select-style popup widget (trigger button + popup with search field and a server-paged, scroll-to-load list) to `crud_views_widget_typeahead`, reusing the existing server core and coexisting with the text typeahead per field.

**Architecture:** The endpoint gains an optional `page` parameter and a `pk` tiebreaker for total ordering. A new widget class `TypeaheadSelect(TypeaheadInput)` renders its own template; a self-contained vanilla `typeahead-select.js`/`.css` is registered as its own asset bundle (`typeahead_select`) with its own `SELECT_EMIT` switch. Fields, filters, `bind()`, tokens and lookups are unchanged.

**Tech Stack:** Python ≥ 3.12, Django (tests on 6.0), django-crud-views ≥ 0.29, django-filter, pytest + pytest-django, vanilla ES2017 JS, Bootstrap 5 CSS classes, Playwright (browser checklist only).

**Spec:** `docs/superpowers/specs/2026-10-15-typeahead-select-design.md`

## Global Constraints

- No new runtime dependencies; `pyproject.toml` `dependencies` stays `["django-crud-views>=0.29.0"]`.
- No third-party JS: no jQuery, no Select2, no DAL. JS never uses `innerHTML`, `insertAdjacentHTML`, `eval(`, `console.log`, or writes `.style.`.
- Public import paths and settings keys are contract: new keys are exactly `SELECT_EMIT` (default `True`) and `SELECT_TEMPLATE` (default `"crud_views_widget_typeahead/typeahead_select.html"`) inside `CRUD_VIEWS_TYPEAHEAD`.
- `assets.py` stays importable without Django; `source_files()` and `bundle()` keep returning exactly the text-typeahead files.
- Asset bundle key: `typeahead_select`; static paths `crud_views_widget_typeahead/typeahead-select.js` and `crud_views_widget_typeahead/typeahead-select.css`.
- The text typeahead's `typeahead.html`, `typeahead.js`, `typeahead.css`, `fields.py`, `filters.py`, `lookups.py`, `tokens.py`, `urls.py` are not modified.
- Endpoint response shape stays `{"results": [{"value", "label"}], "count": n}`; `page` is 1-based, page size = `lookup.max_results`.
- Lint/format: `uv run ruff check . && uv run ruff format .` (line length 120, double quotes) must be clean before each commit.
- Tests: `uv run pytest` (root, `tests/`) and `cd examples/bootstrap5 && uv run pytest` must both pass at the end of every task that touches them.

## Review Focus

1. **Absurd `page` values** (`page=1000000000000000000000000000000`, `page=1.5`, `page=-3`): a user editing the URL expects an empty page or page 1, never a 500 from a database OFFSET overflow. → Task 1, `test_page_far_past_the_end_runs_no_slice_query` and `test_garbage_page_means_page_one`.
2. **Browse with an empty or whitespace query on a `min_chars = 0` lookup**: expected to list the first page of the allowed set, and the next page to continue it. → Task 1, `test_browse_lookup_pages_through_everything_with_an_empty_query`.
3. **HTML in a label** (`<b>Mia</b>` as a first name): the trigger must show it as text, escaped by the template. → Task 3, `test_label_html_is_escaped`.
4. **Two popup widgets in one form**: ids (`popup_id`, `search_id`, `listbox_id`, hidden id) must not collide, or the second widget's JS drives the first one's popup. → Task 3, `test_two_widgets_have_distinct_ids`.
5. **`auto_id=False` forms**: the trigger, popup, search field and listbox ids must still reference each other consistently. → Task 3, `test_auto_id_false_still_consistent`.

---

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `src/crud_views_widget_typeahead/views.py` (modify) | `page` parsing, `_with_pk_tiebreaker()`, paged slicing | 1 |
| `tests/testapp/typeahead.py` (modify) | add `testapp.groups_browse` lookup (`min_chars = 0`) | 1 |
| `tests/test_typeahead_view.py` (modify) | paging + ordering tests | 1 |
| `src/crud_views_widget_typeahead/conf.py` (modify) | `select_emit`, `select_template` | 2 |
| `src/crud_views_widget_typeahead/assets.py` (modify) | `SELECT_JS`, `SELECT_CSS`, `select_source_files()`, `select_bundle()` | 2 |
| `src/crud_views_widget_typeahead/apps.py` (modify) | register `typeahead_select` bundle | 2 |
| `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.js` (create, stub in Task 2, full in Task 4) | popup frontend | 2, 4 |
| `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.css` (create, stub in Task 2, full in Task 4) | popup styles | 2, 4 |
| `tests/test_typeahead_assets.py` (modify) | select assets/conf/registration tests | 2 |
| `src/crud_views_widget_typeahead/widgets.py` (modify) | `TypeaheadSelect`, `_select_i18n()` | 3 |
| `src/crud_views_widget_typeahead/templates/crud_views_widget_typeahead/typeahead_select.html` (create) | popup markup | 3 |
| `tests/testapp/templates/testapp/custom_typeahead_select.html` (create) | template-override fixture | 3 |
| `tests/test_typeahead_select_widget.py` (create) | widget/template/field/filter tests | 3 |
| `tests/test_typeahead_select_js.py` (create) | static JS/CSS contract checks | 4 |
| `examples/bootstrap5/typeahead/typeahead.py`, `forms.py`, `views.py`, `tests.py`, `project/features.py` (modify) | example: browse lookup, pick-assignee modal, popup filter | 5 |
| `README.md`, `CLAUDE.md` (modify) | docs | 6 |

---

### Task 1: Endpoint paging and total ordering

**Files:**
- Modify: `src/crud_views_widget_typeahead/views.py`
- Modify: `tests/testapp/typeahead.py`
- Test: `tests/test_typeahead_view.py`

**Interfaces:**
- Consumes: `get_lookup(name)`, `lookup.filter(queryset, q)`, `lookup.get_queryset(request, **params)`, `lookup.max_results`, `lookup.min_chars` (existing, `lookups.py`).
- Produces: `GET ?t=&q=&page=` (optional `page`, 1-based); `_with_pk_tiebreaker(queryset) -> QuerySet` (module-private helper in `views.py`, tested directly); test lookup `testapp.groups_browse` (`GroupLookup` subclass, `min_chars = 0`, `max_results = 2`).

- [ ] **Step 1: Add the browse test lookup**

In `tests/testapp/typeahead.py`, append after `GroupLookup`:

```python
@register_lookup("testapp.groups_browse")
class GroupBrowseLookup(GroupLookup):
    """Like testapp.groups, but lists entries with an empty query (the select popup's browse-on-open)."""

    min_chars = 0
```

- [ ] **Step 2: Extend the test helper and write the failing tests**

In `tests/test_typeahead_view.py`, replace the `call` helper with a version that passes extra query params:

```python
def call(token, q="", user=None, method="get", **extra):
    """Status and decoded JSON body of the endpoint; RequestFactory keeps auth query-free."""
    params = {"q": q} if token is None else {"t": token, "q": q}
    params.update(extra)
    request = getattr(rf, method)("/typeahead/", params)
    request.user = user if user is not None else AnonymousUser()
    response = lookup_view(request)
    return response.status_code, (json.loads(response.content) if response.content else None)
```

Change the existing `from django.contrib.auth.models import AnonymousUser, Group, User` line to
`from django.contrib.auth.models import AnonymousUser, Group, Permission, User`, and add these imports:

```python
from django.db.models.functions import Lower

from crud_views_widget_typeahead.views import _with_pk_tiebreaker
```

Append the tests:

```python
# --------------------------------------------------------------------------- paging


@pytest.fixture
def alphas(db):
    return [Group.objects.create(name=f"alpha{i}") for i in range(1, 6)]  # 5 matches, max_results = 2


def labels(body):
    return [r["label"] for r in body["results"]]


def test_page_one_equals_the_unpaged_response(alphas):
    token = make_token("testapp.groups", {})
    assert call(token, "alpha", page="1") == call(token, "alpha")


def test_pages_continue_without_overlap(alphas):
    token = make_token("testapp.groups", {})
    pages = [call(token, "alpha", page=str(n))[1] for n in (1, 2, 3)]
    assert [labels(p) for p in pages] == [["alpha1", "alpha2"], ["alpha3", "alpha4"], ["alpha5"]]
    assert {p["count"] for p in pages} == {5}


def test_page_past_the_end_is_empty_with_count(alphas):
    assert call(make_token("testapp.groups", {}), "alpha", page="4") == (200, {"results": [], "count": 5})


def test_page_far_past_the_end_runs_no_slice_query(alphas, django_assert_num_queries):
    token = make_token("testapp.groups", {})
    with django_assert_num_queries(1):  # the count only: an OFFSET this large would overflow the database
        assert call(token, "alpha", page="1" + "0" * 30) == (200, {"results": [], "count": 5})


@pytest.mark.parametrize("page", ["", "0", "-3", "1.5", "abc", " "])
def test_garbage_page_means_page_one(alphas, page):
    token = make_token("testapp.groups", {})
    assert call(token, "alpha", page=page) == call(token, "alpha")


def test_min_chars_is_enforced_on_every_page(team, django_assert_num_queries):
    token = token_for(team["group"])
    with django_assert_num_queries(0):
        assert call(token, "m", team["viewer"], page="2") == (200, {"results": [], "count": 0})


def test_permission_errors_on_every_page(db):
    token = make_token("testapp.group_members", {"group": "forbidden"})
    assert call(token, "mia", User.objects.create_user("v"), page="3") == (403, {"error": "forbidden"})


def test_browse_lookup_pages_through_everything_with_an_empty_query(alphas):
    token = make_token("testapp.groups_browse", {})
    seen = []
    for n in (1, 2, 3):
        status, body = call(token, "   ", page=str(n))
        assert (status, body["count"]) == (200, 5)
        seen += labels(body)
    assert seen == ["alpha1", "alpha2", "alpha3", "alpha4", "alpha5"]


def test_paging_a_scope_of_identical_names_neither_repeats_nor_skips_rows(db):
    # identical display names; the order is settled by username here, the pk tiebreaker is pinned by the
    # _with_pk_tiebreaker tests below
    group = Group.objects.create(name="twins")
    users = [User.objects.create_user(f"same{i:02d}", first_name="Sam", last_name="Same") for i in range(25)]
    group.user_set.add(*users)
    token = make_token("testapp.group_members", {"group": str(group.pk)})  # UserLookup: max_results = 10
    viewer = User.objects.create_user("viewer")
    pks = []
    for n in (1, 2, 3):
        pks += [r["value"] for r in call(token, "sam same", viewer, page=str(n))[1]["results"]]
    assert sorted(pks) == sorted(str(u.pk) for u in users)


# --------------------------------------------------------------------------- total ordering


def test_tiebreaker_on_an_unordered_queryset(db):
    assert _with_pk_tiebreaker(Group.objects.all()).query.order_by == ("pk",)


def test_tiebreaker_keeps_explicit_ordering(db):
    assert _with_pk_tiebreaker(User.objects.order_by("last_name", "-username")).query.order_by == (
        "last_name",
        "-username",
        "pk",
    )


def test_tiebreaker_keeps_expression_ordering(db):
    order_by = _with_pk_tiebreaker(User.objects.order_by(Lower("last_name"))).query.order_by
    assert len(order_by) == 2
    assert order_by[-1] == "pk"


def test_tiebreaker_keeps_meta_ordering(db):
    assert Permission._meta.ordering  # the fixture this test relies on
    assert _with_pk_tiebreaker(Permission.objects.all()).query.order_by == (*Permission._meta.ordering, "pk")
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_typeahead_view.py -q`
Expected: collection error `ImportError: cannot import name '_with_pk_tiebreaker'`.

- [ ] **Step 4: Implement paging and the tiebreaker**

Replace `src/crud_views_widget_typeahead/views.py` with:

```python
"""The one generic typeahead endpoint: GET ?t=<token>&q=<term>[&page=<n>] -> JSON.

Errors are JSON too (fetch() must never receive a login page), and never echo exception messages.
``page`` (1-based, page size = the lookup's max_results) serves the select popup's scroll paging; the text
typeahead never sends it."""

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import Http404, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .lookups import get_lookup
from .tokens import BadToken, read_token


def _error(code: str, status: int) -> JsonResponse:
    return JsonResponse({"error": code}, status=status)


def _page(request) -> int:
    """Lenient on purpose: a bad page cannot widen the result set, so it falls back to page 1."""
    try:
        page = int(request.GET.get("page", "1"))
    except ValueError:
        return 1
    return page if page >= 1 else 1


def _with_pk_tiebreaker(queryset: QuerySet) -> QuerySet:
    """Append pk as the last order key so OFFSET paging neither repeats nor skips rows that tie on the lookup's
    keys. Keeps the queryset's own ordering: explicit order_by, else the model's Meta.ordering."""
    query = queryset.query
    if query.order_by:
        keys = list(query.order_by)
    elif query.default_ordering:
        keys = list(query.get_meta().ordering)
    else:
        keys = []
    return queryset.order_by(*keys, "pk")


@never_cache
@require_GET
def lookup_view(request):
    try:
        name, params = read_token(request.GET.get("t", ""))
    except BadToken:
        return _error("bad_token", 400)
    lookup = get_lookup(name)
    user = getattr(request, "user", None)
    if lookup.login_required and not (user is not None and user.is_authenticated):
        return _error("login_required", 403)
    q = request.GET.get("q", "").strip()
    if len(q) < lookup.min_chars:
        return JsonResponse({"results": [], "count": 0})
    page = _page(request)
    try:
        queryset = _with_pk_tiebreaker(lookup.filter(lookup.get_queryset(request, **params), q))
        count = queryset.count()
        start = (page - 1) * lookup.max_results
        rows = queryset[start : start + lookup.max_results] if start < count else []
        results = [{"value": str(obj.pk), "label": lookup.label(obj)} for obj in rows]
    except PermissionDenied:
        return _error("forbidden", 403)
    except Http404:
        return _error("not_found", 404)
    return JsonResponse({"results": results, "count": count})
```

- [ ] **Step 5: Run the view tests, then the full suite**

Run: `uv run pytest tests/test_typeahead_view.py -q`
Expected: all pass (existing tests such as `test_count_is_taken_before_slicing` still pass: `GroupLookup` orders by `name`, the tiebreaker only appends `pk`).

Run: `uv run pytest -q`
Expected: all pass.

- [ ] **Step 6: Lint and commit**

```bash
uv run ruff check . && uv run ruff format .
git add src/crud_views_widget_typeahead/views.py tests/testapp/typeahead.py tests/test_typeahead_view.py
git commit -m "feat(typeahead): optional page parameter and pk tiebreaker on the endpoint"
```

---

### Task 2: Select settings, assets and registration

**Files:**
- Modify: `src/crud_views_widget_typeahead/conf.py`
- Modify: `src/crud_views_widget_typeahead/assets.py`
- Modify: `src/crud_views_widget_typeahead/apps.py`
- Create: `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.js` (stub, replaced in Task 4)
- Create: `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.css` (stub, replaced in Task 4)
- Test: `tests/test_typeahead_assets.py`

**Interfaces:**
- Consumes: `crud_views.lib.assets.register_assets(key, js, css, emit)`.
- Produces: `conf.DEFAULT_SELECT_TEMPLATE = "crud_views_widget_typeahead/typeahead_select.html"`; `TypeaheadConfig.select_emit: bool` (default `True`), `TypeaheadConfig.select_template: str` (default `DEFAULT_SELECT_TEMPLATE`); `assets.SELECT_JS`, `assets.SELECT_CSS`, `assets.select_source_files() -> {"js": [SELECT_JS], "css": [SELECT_CSS]}`, `assets.select_bundle()` (same value); registry bundle `typeahead_select`.

- [ ] **Step 1: Write the failing tests**

In `tests/test_typeahead_assets.py`, change the two import lines to:

```python
from crud_views_widget_typeahead.assets import (
    APP_LABEL,
    CSS,
    JS,
    SELECT_CSS,
    SELECT_JS,
    bundle,
    select_bundle,
    select_source_files,
    source_files,
)
from crud_views_widget_typeahead.conf import DEFAULT_SELECT_TEMPLATE, DEFAULT_TEMPLATE, TypeaheadConfig, get_config
```

Append:

```python
def test_select_source_files():
    assert select_source_files() == {
        "js": ["crud_views_widget_typeahead/typeahead-select.js"],
        "css": ["crud_views_widget_typeahead/typeahead-select.css"],
    }
    assert SELECT_JS == "crud_views_widget_typeahead/typeahead-select.js"
    assert SELECT_CSS == "crud_views_widget_typeahead/typeahead-select.css"
    assert select_bundle() == select_source_files()


def test_source_files_do_not_include_the_select_popup():
    # contract: pipeline configs call source_files(); the popup is opt-in via select_source_files()
    assert SELECT_JS not in source_files()["js"]
    assert SELECT_CSS not in source_files()["css"]


def test_select_bundle_registered_at_startup():
    from crud_views.lib.assets import get_registered

    bundles = {b.key: b for b in get_registered()}
    select = bundles["typeahead_select"]
    assert [_entry_path(e) for e in select.js] == [SELECT_JS]
    assert [_entry_path(e) for e in select.css] == [SELECT_CSS]
    assert select.emit is get_config().select_emit is True
    keys = list(bundles)
    assert keys.index("typeahead") < keys.index("typeahead_select")


def test_cv_js_and_cv_css_include_the_select_popup():
    js = Template("{% load crud_views %}{% cv_js %}").render(Context({}))
    css = Template("{% load crud_views %}{% cv_css %}").render(Context({}))
    assert "/static/crud_views_widget_typeahead/typeahead-select.js" in js
    assert "/static/crud_views_widget_typeahead/typeahead-select.css" in css


def test_select_static_files_exist():
    from django.contrib.staticfiles import finders

    assert finders.find(SELECT_JS)
    assert finders.find(SELECT_CSS)


def test_select_config_defaults():
    config = get_config()
    assert (config.select_emit, config.select_template) == (True, DEFAULT_SELECT_TEMPLATE)
    assert DEFAULT_SELECT_TEMPLATE == "crud_views_widget_typeahead/typeahead_select.html"


def test_select_config_overrides(settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"SELECT_EMIT": False, "SELECT_TEMPLATE": "x/select.html"}
    config = get_config()
    assert (config.select_emit, config.select_template) == (False, "x/select.html")
    assert (config.emit, config.template) == (True, DEFAULT_TEMPLATE)  # the text typeahead's keys are independent
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_typeahead_assets.py -q`
Expected: collection error `ImportError: cannot import name 'SELECT_CSS'`.

- [ ] **Step 3: Implement conf, assets, apps and the static stubs**

Replace `src/crud_views_widget_typeahead/conf.py` with:

```python
from dataclasses import dataclass

from django.conf import settings

DEFAULT_TEMPLATE = "crud_views_widget_typeahead/typeahead.html"
DEFAULT_SELECT_TEMPLATE = "crud_views_widget_typeahead/typeahead_select.html"


@dataclass(frozen=True)
class TypeaheadConfig:
    emit: bool = True
    template: str = DEFAULT_TEMPLATE
    debounce_ms: int = 250
    select_emit: bool = True
    select_template: str = DEFAULT_SELECT_TEMPLATE


def get_config() -> TypeaheadConfig:
    raw = getattr(settings, "CRUD_VIEWS_TYPEAHEAD", {}) or {}
    return TypeaheadConfig(
        emit=raw.get("EMIT", True),
        template=raw.get("TEMPLATE", DEFAULT_TEMPLATE),
        debounce_ms=int(raw.get("DEBOUNCE_MS", 250)),
        select_emit=raw.get("SELECT_EMIT", True),
        select_template=raw.get("SELECT_TEMPLATE", DEFAULT_SELECT_TEMPLATE),
    )
```

Replace `src/crud_views_widget_typeahead/assets.py` with:

```python
"""Asset path definitions. Django-free by design: importable from settings.py,
so django-pipeline users can build bundles from the same single source of truth
that AppConfig.ready() feeds into the crud_views asset registry.

Two bundles: the text typeahead (source_files/bundle) and the select popup
(select_source_files/select_bundle). They are separate so a skin or a pipeline
config can replace or deliver one without the other."""

APP_LABEL = "crud_views_widget_typeahead"
JS = f"{APP_LABEL}/typeahead.js"
CSS = f"{APP_LABEL}/typeahead.css"
SELECT_JS = f"{APP_LABEL}/typeahead-select.js"
SELECT_CSS = f"{APP_LABEL}/typeahead-select.css"


def source_files() -> dict:
    """Static paths for pipeline source_filenames. No third-party plugin: nothing to vendor."""
    return {"js": [JS], "css": [CSS]}


def bundle() -> dict:
    """The js/css lists to register with the crud_views asset registry."""
    return source_files()


def select_source_files() -> dict:
    """Static paths of the select popup for pipeline source_filenames."""
    return {"js": [SELECT_JS], "css": [SELECT_CSS]}


def select_bundle() -> dict:
    """The select popup's js/css lists to register with the crud_views asset registry."""
    return select_source_files()
```

Replace `src/crud_views_widget_typeahead/apps.py` with:

```python
from django.apps import AppConfig


class CrudViewsWidgetTypeaheadConfig(AppConfig):
    name = "crud_views_widget_typeahead"
    verbose_name = "CRUD Views Widget: Typeahead"

    def ready(self):
        from crud_views.lib.assets import register_assets
        from django.utils.module_loading import autodiscover_modules

        from .assets import bundle, select_bundle
        from .conf import get_config

        cfg = get_config()
        b = bundle()
        register_assets(key="typeahead", js=b["js"], css=b["css"], emit=cfg.emit)
        sb = select_bundle()
        register_assets(key="typeahead_select", js=sb["js"], css=sb["css"], emit=cfg.select_emit)
        # admin-style: import every installed app's typeahead.py so its lookups register
        autodiscover_modules("typeahead")
```

Create `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.js` (stub; Task 4 replaces it):

```js
/* crud_views_widget_typeahead — select popup frontend (implemented in the next task). */
```

Create `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.css` (stub; Task 4 replaces it):

```css
/* crud_views_widget_typeahead — select popup styles (implemented in the next task). */
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_typeahead_assets.py -q`
Expected: all pass, including the unchanged `test_config_defaults` (new dataclass fields have defaults, so `TypeaheadConfig(emit=True, template=..., debounce_ms=250)` still compares equal).

Run: `uv run pytest -q`
Expected: all pass.

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check . && uv run ruff format .
git add src/crud_views_widget_typeahead/conf.py src/crud_views_widget_typeahead/assets.py \
  src/crud_views_widget_typeahead/apps.py src/crud_views_widget_typeahead/static tests/test_typeahead_assets.py
git commit -m "feat(typeahead): select popup settings and its own asset bundle"
```

---

### Task 3: `TypeaheadSelect` widget and template

**Files:**
- Modify: `src/crud_views_widget_typeahead/widgets.py`
- Create: `src/crud_views_widget_typeahead/templates/crud_views_widget_typeahead/typeahead_select.html`
- Create: `tests/testapp/templates/testapp/custom_typeahead_select.html`
- Test: `tests/test_typeahead_select_widget.py`

**Interfaces:**
- Consumes: `TypeaheadInput` (`binding`, `resolve()`, `get_context()`, `use_required_attribute()`, `submit_on_clear`, `_template_name`), `_i18n(min_chars)`, `get_lookup()`, `get_config().select_template` (Task 2), `TypeaheadField`, `TypeaheadFilter`.
- Produces: `crud_views_widget_typeahead.widgets.TypeaheadSelect(attrs=None, submit_on_clear=False, template_name=None)`. Template context `widget.typeahead` = all `TypeaheadInput` keys plus `popup_id` (`<id>_popup`), `search_id` (`<id>_search`), `page_size` (`lookup.max_results`); `i18n` additionally has `placeholder`, `search`, `loading`, `type_more`, and a popup-specific `hint`. DOM contract used by Task 4: root `[data-cv-typeahead-select]` with `data-url`, `data-min-chars`, `data-debounce`, `data-page-size`, `data-submit-on-clear`, `data-i18n-none`, `data-i18n-count`, `data-i18n-error`, `data-i18n-loading`, `data-i18n-type-more`, `data-i18n-placeholder`; trigger `button[aria-haspopup="listbox"]`; label `[data-cv-typeahead-select-label]`; clear `[data-cv-typeahead-select-clear]`; `input[type=hidden]`; popup `[data-cv-typeahead-select-popup]` containing `input[type=search]` and `ul[role=listbox]`; status `[data-cv-typeahead-select-status]`.

- [ ] **Step 1: Create the template-override fixture**

Create `tests/testapp/templates/testapp/custom_typeahead_select.html` with exactly:

```html
<custom-typeahead-select>{{ widget.typeahead.label }}</custom-typeahead-select>
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_typeahead_select_widget.py`:

```python
import html
import re
from urllib.parse import parse_qs, urlsplit

import django_filters
import pytest
from django import forms
from django.contrib.auth.models import Group, User

from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.filters import TypeaheadFilter
from crud_views_widget_typeahead.tokens import read_token
from crud_views_widget_typeahead.widgets import TypeaheadSelect


class MemberForm(forms.Form):
    member = TypeaheadField(lookup="testapp.group_members", widget=TypeaheadSelect(), help_text="Pick a member")
    note = forms.CharField()


class PairForm(forms.Form):
    first = TypeaheadField(lookup="testapp.group_members", widget=TypeaheadSelect())
    second = TypeaheadField(lookup="testapp.group_members", widget=TypeaheadSelect())


@pytest.fixture
def team(db):
    group = Group.objects.create(name="team")
    member = User.objects.create_user("mmember", first_name="Mia", last_name="Member")
    outsider = User.objects.create_user("ooutsider", first_name="Mia", last_name="Outsider")
    group.user_set.add(member)
    return {"group": group, "member": member, "outsider": outsider}


def bound_form(team, form_class=MemberForm, **form_kwargs):
    form = form_class(**form_kwargs)
    for field in form.fields.values():
        if isinstance(field, TypeaheadField):
            field.bind(None, group=str(team["group"].pk))
    return form


def render(team, **form_kwargs) -> str:
    return str(bound_form(team, **form_kwargs)["member"])


def tag(markup: str, pattern: str) -> str:
    return re.search(pattern, markup).group(0)


def trigger(markup: str) -> str:
    return tag(markup, r'<button type="button"[^>]*aria-haspopup[^>]*>')


def label_text(markup: str) -> str:
    return html.unescape(re.search(r"<span[^>]*data-cv-typeahead-select-label[^>]*>(.*?)</span>", markup, re.S).group(1))


def hidden_input(markup: str) -> str:
    return tag(markup, r'<input type="hidden"[^>]*>')


def search_input(markup: str) -> str:
    return tag(markup, r'<input type="search"[^>]*>')


def root(markup: str) -> str:
    return tag(markup, r'<div class="cv-typeahead-select"[^>]*>')


def attr(element: str, name: str):
    match = re.search(rf'\s{re.escape(name)}="([^"]*)"', element)
    return html.unescape(match.group(1)) if match else None


def test_structure_and_ids(team):
    markup = render(team)
    button = trigger(markup)
    assert attr(button, "id") == "id_member"
    assert attr(button, "name") is None
    assert attr(button, "aria-haspopup") == "listbox"
    assert attr(button, "aria-expanded") == "false"
    assert attr(button, "aria-controls") == "id_member_popup"
    assert {"form-select", "text-start"} <= set(attr(button, "class").split())
    assert "form-control" not in attr(button, "class").split()
    for dropped in ("role", "aria-autocomplete", "autocomplete"):
        assert attr(button, dropped) is None
    hidden = hidden_input(markup)
    assert (attr(hidden, "name"), attr(hidden, "id"), attr(hidden, "autocomplete")) == ("member", "id_member_value", "off")
    popup = tag(markup, r"<div[^>]*data-cv-typeahead-select-popup[^>]*>")
    assert attr(popup, "id") == "id_member_popup"
    assert re.search(r"\shidden", popup)
    search = search_input(markup)
    assert attr(search, "id") == "id_member_search"
    assert attr(search, "role") == "combobox"
    assert attr(search, "aria-autocomplete") == "list"
    assert attr(search, "aria-expanded") == "false"
    assert attr(search, "aria-controls") == "id_member_listbox"
    assert attr(search, "aria-label")
    listbox = tag(markup, r"<ul[^>]*>")
    assert (attr(listbox, "id"), attr(listbox, "role")) == ("id_member_listbox", "listbox")
    assert attr(listbox, "aria-label")
    assert 'id="id_member_hint"' in markup
    assert "data-cv-typeahead-select-status" in markup and 'aria-live="polite"' in markup


def test_empty_shows_placeholder(team):
    markup = render(team)
    assert label_text(markup) == "Select…"
    assert "cv-typeahead-select-placeholder" in tag(markup, r"<span[^>]*data-cv-typeahead-select-label[^>]*>")
    assert attr(hidden_input(markup), "value") == ""


def test_initial_pk_renders_lookup_label(team):
    markup = render(team, initial={"member": team["member"].pk})
    assert label_text(markup) == "Mia Member"  # lookup.label (full name), not str(user) ("mmember")
    assert attr(hidden_input(markup), "value") == str(team["member"].pk)
    assert "cv-typeahead-select-placeholder" not in markup


def test_label_is_rerendered_after_a_validation_error(team):
    markup = render(team, data={"member": str(team["member"].pk), "note": ""})
    assert label_text(markup) == "Mia Member"


@pytest.mark.parametrize("value", ["abc", "999999", "1.5"])
def test_garbage_pk_renders_empty(team, value):
    markup = render(team, data={"member": value, "note": "x"})
    assert label_text(markup) == "Select…"
    assert attr(hidden_input(markup), "value") == ""


def test_out_of_scope_pk_renders_empty(team):
    markup = render(team, data={"member": str(team["outsider"].pk), "note": "x"})
    assert label_text(markup) == "Select…"
    assert attr(hidden_input(markup), "value") == ""


def test_label_html_is_escaped(team):
    team["member"].first_name = "<b>Mia</b>"
    team["member"].save()
    markup = render(team, initial={"member": team["member"].pk})
    assert "<b>Mia</b>" not in markup
    assert "&lt;b&gt;Mia&lt;/b&gt;" in markup


def test_unbound_widget_raises(team):
    from django.core.exceptions import ImproperlyConfigured

    with pytest.raises(ImproperlyConfigured, match="not bound"):
        str(MemberForm()["member"])


def test_aria_describedby_merges_django_ids_with_hint(team):
    assert attr(trigger(render(team)), "aria-describedby") == "id_member_helptext id_member_hint"
    invalid = render(team, data={"member": "", "note": "x"})
    assert attr(trigger(invalid), "aria-describedby") == "id_member_helptext id_member_error id_member_hint"


def test_no_required_attribute(team):
    assert re.search(r"\srequired", trigger(render(team))) is None


def test_auto_id_false_still_consistent(team):
    markup = render(team, auto_id=False)
    button = trigger(markup)
    popup = tag(markup, r"<div[^>]*data-cv-typeahead-select-popup[^>]*>")
    search = search_input(markup)
    listbox = tag(markup, r"<ul[^>]*>")
    assert attr(button, "aria-controls") == attr(popup, "id")
    assert attr(search, "aria-controls") == attr(listbox, "id")
    assert attr(hidden_input(markup), "id") == f"{attr(button, 'id')}_value"


def test_two_widgets_have_distinct_ids(team):
    form = bound_form(team, PairForm)
    ids = []
    for name in ("first", "second"):
        markup = str(form[name])
        ids += re.findall(r'\sid="([^"]*)"', markup)
    assert len(ids) == len(set(ids))


def test_data_attributes(team):
    markup = render(team)
    element = root(markup)
    assert "data-cv-typeahead-select" in element
    url = urlsplit(attr(element, "data-url"))
    assert url.path == "/typeahead/"
    assert read_token(parse_qs(url.query)["t"][0]) == ("testapp.group_members", {"group": str(team["group"].pk)})
    assert attr(element, "data-min-chars") == "2"
    assert attr(element, "data-debounce") == "250"
    assert attr(element, "data-page-size") == "10"
    assert attr(element, "data-submit-on-clear") == "false"
    assert "{n}" in attr(element, "data-i18n-count")
    for key in ("none", "error", "loading", "type-more", "placeholder"):
        assert attr(element, f"data-i18n-{key}"), key
    assert "2" in attr(element, "data-i18n-type-more")


def test_clear_button_hidden_without_value(team):
    button = tag(render(team), r"<button[^>]*data-cv-typeahead-select-clear[^>]*>")
    assert re.search(r"\shidden", button)
    assert attr(button, "aria-label")
    with_value = render(team, initial={"member": team["member"].pk})
    assert not re.search(r"\shidden", tag(with_value, r"<button[^>]*data-cv-typeahead-select-clear[^>]*>"))


def test_template_from_settings(team, settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"SELECT_TEMPLATE": "testapp/custom_typeahead_select.html"}
    assert render(team).startswith("<custom-typeahead-select")


def test_text_typeahead_template_setting_does_not_affect_the_popup(team, settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"TEMPLATE": "testapp/custom_typeahead.html"}
    assert "data-cv-typeahead-select" in render(team)


def test_template_per_instance(team):
    form = MemberForm()
    form.fields["member"].widget.template_name = "testapp/custom_typeahead_select.html"
    form.fields["member"].bind(None, group=str(team["group"].pk))
    assert str(form["member"]).startswith("<custom-typeahead-select")
    assert TypeaheadSelect(template_name="x.html").template_name == "x.html"


def test_skin_context_contract(team):
    form = bound_form(team)
    context = form.fields["member"].widget.get_context("member", team["member"].pk, {"id": "id_member"})
    assert set(context["widget"]["typeahead"]) == {
        "url",
        "label",
        "value",
        "hidden_name",
        "hidden_id",
        "listbox_id",
        "hint_id",
        "min_chars",
        "debounce",
        "submit_on_clear",
        "i18n",
        "popup_id",
        "search_id",
        "page_size",
    }
    assert set(context["widget"]["typeahead"]["i18n"]) == {
        "hint",
        "more",
        "none",
        "count",
        "error",
        "clear",
        "listbox",
        "placeholder",
        "search",
        "loading",
        "type_more",
    }


def test_form_round_trip_validates_against_the_bound_queryset(team):
    ok = bound_form(team, data={"member": str(team["member"].pk), "note": "x"})
    assert ok.is_valid(), ok.errors
    assert ok.cleaned_data["member"] == team["member"]
    outsider = bound_form(team, data={"member": str(team["outsider"].pk), "note": "x"})
    assert not outsider.is_valid()


class GroupFilter(django_filters.FilterSet):
    member = TypeaheadFilter(field_name="user", lookup="testapp.all_users", widget=TypeaheadSelect(submit_on_clear=True))

    class Meta:
        model = Group
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["member"].bind(self.request)


def test_filter_with_the_popup_filters_by_pk(team):
    blue = Group.objects.create(name="blue")
    filterset = GroupFilter({"member": str(team["member"].pk)}, queryset=Group.objects.order_by("name"), request=None)
    assert list(filterset.qs) == [team["group"]]
    assert blue not in filterset.qs
    markup = str(filterset.form["member"])
    assert "data-cv-typeahead-select" in markup
    assert attr(root(markup), "data-submit-on-clear") == "true"
    assert attr(hidden_input(markup), "name") == "member"
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_typeahead_select_widget.py -q`
Expected: collection error `ImportError: cannot import name 'TypeaheadSelect'`.

- [ ] **Step 4: Implement the widget**

In `src/crud_views_widget_typeahead/widgets.py`, update the module docstring's first line to mention both widgets:

```python
"""Typeahead widgets: TypeaheadInput (text input) and TypeaheadSelect (select-style popup).
```

(keep the rest of the docstring), and append at the end of the file:

```python
def _select_i18n(min_chars: int) -> dict:
    return {
        "hint": gettext("Open with Enter or the arrow keys, type to search, choose with Enter."),
        "placeholder": gettext("Select…"),
        "search": gettext("Search"),
        "loading": gettext("Loading…"),
        "type_more": ngettext(
            "Type at least %(count)d character.",
            "Type at least %(count)d characters.",
            min_chars,
        )
        % {"count": min_chars},
    }


class TypeaheadSelect(TypeaheadInput):
    """Select-style popup: a trigger button that looks like a Bootstrap <select>, and a popup with a search field
    and a server-paged list. Same binding, hidden-input contract and endpoint as TypeaheadInput; its own template
    (SELECT_TEMPLATE) and its own frontend (typeahead-select.js, asset bundle "typeahead_select")."""

    @property
    def template_name(self) -> str:
        return self._template_name or get_config().select_template

    @template_name.setter
    def template_name(self, value: str | None):
        self._template_name = value

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        typeahead = widget["typeahead"]
        button = widget["attrs"]  # widget.attrs land on the trigger button
        text_id = button["id"]
        for key in ("role", "aria-autocomplete", "autocomplete"):  # text-input semantics, not a button's
            button.pop(key, None)
        classes = [c for c in str(button.get("class") or "").split() if c != "form-control"]
        button.update(
            {
                "class": " ".join(dict.fromkeys([*classes, "form-select", "text-start"])),
                "aria-haspopup": "listbox",
                "aria-expanded": "false",
                "aria-controls": f"{text_id}_popup",
            }
        )
        lookup = get_lookup(self.binding.lookup_name)
        typeahead.update(
            {
                "popup_id": f"{text_id}_popup",
                "search_id": f"{text_id}_search",
                "page_size": lookup.max_results,
                "i18n": {**typeahead["i18n"], **_select_i18n(lookup.min_chars)},
            }
        )
        return context
```

- [ ] **Step 5: Create the template**

Create `src/crud_views_widget_typeahead/templates/crud_views_widget_typeahead/typeahead_select.html`:

```html
{% with ta=widget.typeahead %}<div class="cv-typeahead-select" data-cv-typeahead-select data-url="{{ ta.url }}" data-min-chars="{{ ta.min_chars }}" data-debounce="{{ ta.debounce }}" data-page-size="{{ ta.page_size }}" data-submit-on-clear="{{ ta.submit_on_clear|yesno:'true,false' }}" data-i18n-none="{{ ta.i18n.none }}" data-i18n-count="{{ ta.i18n.count }}" data-i18n-error="{{ ta.i18n.error }}" data-i18n-loading="{{ ta.i18n.loading }}" data-i18n-type-more="{{ ta.i18n.type_more }}" data-i18n-placeholder="{{ ta.i18n.placeholder }}">
  <button type="button"{% include "django/forms/widgets/attrs.html" %}><span class="cv-typeahead-select-label{% if not ta.value %} cv-typeahead-select-placeholder{% endif %}" data-cv-typeahead-select-label>{% if ta.value %}{{ ta.label }}{% else %}{{ ta.i18n.placeholder }}{% endif %}</span></button>
  <button type="button" class="btn-close cv-typeahead-select-clear" data-cv-typeahead-select-clear aria-label="{{ ta.i18n.clear }}"{% if not ta.value %} hidden{% endif %}></button>
  <input type="hidden" name="{{ ta.hidden_name }}" id="{{ ta.hidden_id }}" value="{{ ta.value }}" autocomplete="off">
  <div id="{{ ta.popup_id }}" class="dropdown-menu cv-typeahead-select-popup" data-cv-typeahead-select-popup hidden>
    <div class="px-2 pb-2"><input type="search" id="{{ ta.search_id }}" class="form-control form-control-sm" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="{{ ta.listbox_id }}" aria-label="{{ ta.i18n.search }}" autocomplete="off"></div>
    <ul id="{{ ta.listbox_id }}" class="list-unstyled mb-0 cv-typeahead-select-list" role="listbox" aria-label="{{ ta.i18n.listbox }}"></ul>
  </div>
  <span id="{{ ta.hint_id }}" class="visually-hidden">{{ ta.i18n.hint }}</span>
  <span class="visually-hidden" aria-live="polite" data-cv-typeahead-select-status></span>
</div>{% endwith %}
```

- [ ] **Step 6: Run the tests**

Run: `uv run pytest tests/test_typeahead_select_widget.py -q`
Expected: all pass.

Run: `uv run pytest -q`
Expected: all pass (the text typeahead's widget tests are untouched).

- [ ] **Step 7: Lint and commit**

```bash
uv run ruff check . && uv run ruff format .
git add src/crud_views_widget_typeahead/widgets.py \
  src/crud_views_widget_typeahead/templates/crud_views_widget_typeahead/typeahead_select.html \
  tests/testapp/templates/testapp/custom_typeahead_select.html tests/test_typeahead_select_widget.py
git commit -m "feat(typeahead): TypeaheadSelect widget and popup template"
```

---

### Task 4: Popup frontend (`typeahead-select.js` / `.css`)

**Files:**
- Modify (replace stub): `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.js`
- Modify (replace stub): `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.css`
- Test: `tests/test_typeahead_select_js.py`

**Interfaces:**
- Consumes: the DOM contract from Task 3 (root data attributes and `data-cv-typeahead-select-*` hooks); endpoint `GET <data-url>&q=<term>&page=<n>` → `{results: [{value, label}], count}` (Task 1); event `cv:modal:loaded` (crud_views, bubbling from `#cv-modal`).
- Produces: `window.cvTypeaheadSelect = {init(root)}`; a bubbling `change` event on the hidden input after every selection or clear.

- [ ] **Step 1: Write the failing static checks**

Create `tests/test_typeahead_select_js.py`:

```python
from pathlib import Path

import crud_views_widget_typeahead as pkg

STATIC = Path(pkg.__file__).parent / "static" / "crud_views_widget_typeahead"


def test_js_contract():
    js = (STATIC / "typeahead-select.js").read_text()
    assert "[data-cv-typeahead-select]" in js
    assert "cv:modal:loaded" in js
    assert "window.cvTypeaheadSelect" in js
    assert "AbortController" in js
    assert "requestSubmit" in js
    assert "aria-activedescendant" in js
    assert "stopPropagation" in js  # Escape must not close a surrounding Bootstrap modal
    assert "page=" in js


def test_js_is_csp_and_xss_safe():
    js = (STATIC / "typeahead-select.js").read_text()
    assert "innerHTML" not in js
    assert "insertAdjacentHTML" not in js
    assert ".style." not in js
    assert "eval(" not in js
    assert "console.log" not in js
    assert "jQuery" not in js and "$(" not in js


def test_js_does_not_touch_the_text_typeahead():
    js = (STATIC / "typeahead-select.js").read_text()
    assert "window.cvTypeahead " not in js and "window.cvTypeahead=" not in js
    assert "[data-cv-typeahead]" not in js


def test_css():
    css = (STATIC / "typeahead-select.css").read_text()
    for selector in (
        ".cv-typeahead-select",
        ".cv-typeahead-select-popup",
        ".cv-typeahead-select-list",
        ".cv-typeahead-select-placeholder",
        ".cv-typeahead-select-clear",
    ):
        assert selector in css, selector
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_typeahead_select_js.py -q`
Expected: FAIL (`assert "[data-cv-typeahead-select]" in js`, and the CSS selectors) against the Task 2 stubs.

- [ ] **Step 3: Implement the JS**

Replace `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.js` with:

```js
/*
 * crud_views_widget_typeahead — select popup frontend (vanilla JS, Bootstrap 5 markup).
 *
 * A trigger button shows the label of the pk in the hidden input. Opening it shows a popup with a search field and
 * a server-paged list; scrolling to the end loads the next page. Enter never submits while the popup is open; Escape
 * closes only the popup (a surrounding Bootstrap modal stays open). Option text is built from text nodes and <mark>
 * elements, never parsed from HTML strings; no inline styles are written.
 *
 * Activates on DOMContentLoaded and on "cv:modal:loaded" (dispatched by crud_views after injecting modal content).
 * Call window.cvTypeaheadSelect.init(root) for other dynamically added content.
 */
(function () {
    "use strict";

    function fmt(template, n) {
        return (template || "").replace("{n}", String(n));
    }

    /* Append text to el, wrapping case-insensitive matches of any word in <mark>. */
    function highlight(el, text, words) {
        const lower = text.toLowerCase();
        const ranges = [];
        words.forEach(function (word) {
            const w = word.toLowerCase();
            let i = w ? lower.indexOf(w) : -1;
            while (i !== -1) {
                ranges.push([i, i + w.length]);
                i = lower.indexOf(w, i + w.length);
            }
        });
        ranges.sort(function (a, b) {
            return a[0] - b[0];
        });
        const merged = [];
        ranges.forEach(function (r) {
            const last = merged[merged.length - 1];
            if (last && r[0] <= last[1]) {
                last[1] = Math.max(last[1], r[1]);
            } else {
                merged.push([r[0], r[1]]);
            }
        });
        let pos = 0;
        merged.forEach(function (r) {
            if (r[0] > pos) el.appendChild(document.createTextNode(text.slice(pos, r[0])));
            const mark = document.createElement("mark");
            mark.textContent = text.slice(r[0], r[1]);
            el.appendChild(mark);
            pos = r[1];
        });
        if (pos < text.length) el.appendChild(document.createTextNode(text.slice(pos)));
    }

    class TypeaheadSelect {
        constructor(root) {
            this.root = root;
            this.trigger = root.querySelector('button[aria-haspopup="listbox"]');
            this.labelEl = root.querySelector("[data-cv-typeahead-select-label]");
            this.clearButton = root.querySelector("[data-cv-typeahead-select-clear]");
            this.hidden = root.querySelector('input[type="hidden"]');
            this.popup = root.querySelector("[data-cv-typeahead-select-popup]");
            this.search = this.popup.querySelector('input[type="search"]');
            this.list = this.popup.querySelector('[role="listbox"]');
            this.status = root.querySelector("[data-cv-typeahead-select-status]");
            this.url = root.dataset.url;
            this.minChars = parseInt(root.dataset.minChars, 10) || 0;
            this.debounce = parseInt(root.dataset.debounce, 10) || 0;
            this.submitOnClear = root.dataset.submitOnClear === "true";
            this.options = []; // [{value, label, el}]
            this.active = -1;
            this.timer = null;
            this.controller = null;
            this.loadingEl = null;
            this.query = "";
            this.page = 0; // last page rendered for this.query; 0 = none
            this.count = 0;
            this.listen();
        }

        listen() {
            this.trigger.addEventListener("click", () => (this.isOpen() ? this.close(true) : this.open("")));
            this.trigger.addEventListener("keydown", (e) => this.onTriggerKeydown(e));
            // while open, a click on the trigger must not move focus out of the popup first (focusout would close,
            // then the click would reopen)
            this.trigger.addEventListener("mousedown", (e) => {
                if (this.isOpen()) e.preventDefault();
            });
            this.search.addEventListener("input", () => this.onInput());
            this.search.addEventListener("keydown", (e) => this.onSearchKeydown(e));
            // keep focus in the search field while clicking options or popup padding
            this.popup.addEventListener("mousedown", (e) => {
                if (e.target !== this.search) e.preventDefault();
            });
            this.popup.addEventListener("focusout", (e) => {
                if (!this.popup.contains(e.relatedTarget)) this.close(false);
            });
            this.list.addEventListener("scroll", () => this.maybeLoadMore());
            if (this.clearButton) this.clearButton.addEventListener("click", () => this.clear());
        }

        isOpen() {
            return !this.popup.hidden;
        }

        onTriggerKeydown(e) {
            // Enter and Space activate the button natively (click -> open); the button is type="button"
            if (e.key === "ArrowDown" || e.key === "ArrowUp") {
                e.preventDefault();
                if (!this.isOpen()) this.open("");
            } else if (e.key.length === 1 && e.key !== " " && !e.ctrlKey && !e.altKey && !e.metaKey) {
                e.preventDefault();
                if (!this.isOpen()) this.open(e.key);
            }
        }

        onSearchKeydown(e) {
            switch (e.key) {
                case "ArrowDown":
                case "ArrowUp":
                    e.preventDefault();
                    this.move(e.key === "ArrowDown" ? 1 : -1);
                    break;
                case "Enter":
                    e.preventDefault(); // never submit while the popup is open
                    if (this.active >= 0) this.select(this.active);
                    break;
                case "Escape":
                    e.preventDefault();
                    e.stopPropagation(); // a surrounding Bootstrap modal must stay open
                    this.close(true);
                    break;
                // Tab: focus leaves the popup, the focusout handler closes it
            }
        }

        open(seed) {
            this.popup.hidden = false;
            this.popup.classList.add("show");
            this.setExpanded(true);
            this.search.value = seed;
            this.search.focus();
            this.load();
        }

        close(focusTrigger) {
            if (!this.isOpen()) return;
            this.cancelPending();
            this.popup.hidden = true;
            this.popup.classList.remove("show");
            this.setExpanded(false);
            this.search.value = "";
            this.resetList();
            this.query = "";
            this.page = 0;
            this.count = 0;
            this.announce("");
            if (focusTrigger) this.trigger.focus();
        }

        setExpanded(on) {
            const value = on ? "true" : "false";
            this.trigger.setAttribute("aria-expanded", value);
            this.search.setAttribute("aria-expanded", value);
        }

        onInput() {
            clearTimeout(this.timer);
            this.timer = setTimeout(() => this.load(), this.debounce);
        }

        /* Start over for the search field's current text: page 1, or the "type more" hint. */
        load() {
            this.cancelPending();
            const q = this.search.value.trim();
            this.query = q;
            this.page = 0;
            this.count = 0;
            if (q.length < this.minChars) {
                this.resetList();
                this.info(this.root.dataset.i18nTypeMore);
                this.announce(this.root.dataset.i18nTypeMore);
                return;
            }
            this.fetchPage(1);
        }

        cancelPending() {
            clearTimeout(this.timer);
            this.timer = null;
            if (this.controller) {
                this.controller.abort();
                this.controller = null;
            }
            this.removeLoading();
        }

        fetchPage(page) {
            const q = this.query;
            const controller = new AbortController();
            this.controller = controller;
            if (page > 1) this.loadingEl = this.info(this.root.dataset.i18nLoading);
            const sep = this.url.indexOf("?") === -1 ? "?" : "&";
            const url = this.url + sep + "q=" + encodeURIComponent(q) + "&page=" + page;
            fetch(url, {signal: controller.signal, credentials: "same-origin", headers: {Accept: "application/json"}})
                .then((response) => {
                    if (!response.ok) throw new Error("HTTP " + response.status);
                    return response.json();
                })
                .then((data) => {
                    if (this.controller !== controller || q !== this.query || !this.isOpen()) return; // stale
                    this.controller = null;
                    this.render(data, page);
                })
                .catch((err) => {
                    if (err.name === "AbortError" || this.controller !== controller) return;
                    this.controller = null;
                    this.removeLoading();
                    this.info(this.root.dataset.i18nError);
                    this.announce(this.root.dataset.i18nError);
                    console.warn("cv-typeahead-select:", err);
                });
        }

        render(data, page) {
            const results = data.results || [];
            this.removeLoading();
            if (page === 1) this.resetList();
            this.count = data.count || 0;
            this.page = page;
            const words = this.query.split(/\s+/).filter(Boolean);
            results.forEach((item) => {
                const index = this.options.length;
                const li = document.createElement("li");
                li.id = this.list.id + "_" + index;
                li.className = "dropdown-item";
                li.setAttribute("role", "option");
                li.setAttribute("aria-selected", "false");
                highlight(li, String(item.label), words);
                li.addEventListener("click", () => this.select(index));
                this.list.appendChild(li);
                this.options.push({value: String(item.value), label: String(item.label), el: li});
            });
            if (page === 1) {
                if (!this.options.length) this.info(this.root.dataset.i18nNone);
                this.announce(
                    this.options.length ? fmt(this.root.dataset.i18nCount, this.count) : this.root.dataset.i18nNone
                );
            }
            this.maybeLoadMore(); // a short first page leaves nothing to scroll: keep filling
        }

        /* Load the next page when the list is scrolled (or filled) to within one row of its end. */
        maybeLoadMore() {
            if (this.controller || this.page === 0 || this.options.length >= this.count) return;
            const list = this.list;
            const row = this.options.length ? this.options[this.options.length - 1].el.offsetHeight : 0;
            if (list.scrollHeight - list.scrollTop - list.clientHeight <= row) this.fetchPage(this.page + 1);
        }

        resetList() {
            this.list.replaceChildren();
            this.options = [];
            this.active = -1;
            this.loadingEl = null;
            this.search.removeAttribute("aria-activedescendant");
        }

        info(text) {
            const li = document.createElement("li");
            li.className = "dropdown-item-text cv-typeahead-select-info";
            li.setAttribute("role", "option");
            li.setAttribute("aria-disabled", "true");
            li.textContent = text || "";
            this.list.appendChild(li);
            return li;
        }

        removeLoading() {
            if (this.loadingEl) {
                this.loadingEl.remove();
                this.loadingEl = null;
            }
        }

        move(delta) {
            const n = this.options.length;
            if (!n) return;
            let next = this.active + delta;
            if (next < 0) next = n - 1;
            if (next >= n) next = 0;
            this.setActive(next);
        }

        setActive(index) {
            this.options.forEach((opt, i) => {
                const on = i === index;
                opt.el.classList.toggle("active", on);
                opt.el.setAttribute("aria-selected", on ? "true" : "false");
            });
            this.active = index;
            const el = this.options[index].el;
            this.search.setAttribute("aria-activedescendant", el.id);
            el.scrollIntoView({block: "nearest"});
        }

        select(index) {
            const opt = this.options[index];
            this.hidden.value = opt.value;
            this.setLabel(opt.label, false);
            this.close(true);
            this.changed();
        }

        clear() {
            this.close(false);
            this.hidden.value = "";
            this.setLabel(this.root.dataset.i18nPlaceholder, true);
            this.changed();
            if (this.submitOnClear && this.hidden.form) {
                this.hidden.form.requestSubmit();
            } else {
                this.trigger.focus();
            }
        }

        setLabel(text, isPlaceholder) {
            this.labelEl.textContent = text || "";
            this.labelEl.classList.toggle("cv-typeahead-select-placeholder", isPlaceholder);
        }

        changed() {
            if (this.clearButton) this.clearButton.hidden = this.hidden.value === "";
            this.hidden.dispatchEvent(new Event("change", {bubbles: true}));
        }

        announce(text) {
            if (this.status) this.status.textContent = text || "";
        }
    }

    function init(root) {
        (root || document).querySelectorAll("[data-cv-typeahead-select]").forEach(function (el) {
            if (el.dataset.cvTypeaheadSelectReady) return;
            el.dataset.cvTypeaheadSelectReady = "1";
            new TypeaheadSelect(el);
        });
    }

    window.cvTypeaheadSelect = {init: init};

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            init(document);
        });
    } else {
        init(document);
    }
    // crud_views dispatches this (bubbling) on #cv-modal after injecting modal content
    document.addEventListener("cv:modal:loaded", function (e) {
        init(e.target);
    });
})();
```

- [ ] **Step 4: Implement the CSS**

Replace `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.css` with:

```css
/* crud_views_widget_typeahead — select popup, Bootstrap 5 skin. Show/hide uses [hidden] + .show, never inline styles. */
.cv-typeahead-select {
    position: relative;
}

/* the trigger: a <button class="form-select"> that keeps room for the clear button and the caret */
.cv-typeahead-select > .form-select {
    display: block;
    width: 100%;
    padding-right: 4rem;
}

.cv-typeahead-select-label {
    display: block;
    min-height: 1.5em;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.cv-typeahead-select-placeholder {
    color: var(--bs-secondary-color);
}

.cv-typeahead-select-clear {
    position: absolute;
    top: 50%;
    right: 2.25rem;
    transform: translateY(-50%);
    font-size: 0.65rem;
}

.cv-typeahead-select-popup {
    top: 100%;
    left: 0;
    width: 100%;
}

.cv-typeahead-select-popup.show {
    display: block;
}

.cv-typeahead-select-list {
    max-height: 20rem;
    overflow-y: auto;
}

.cv-typeahead-select-list .dropdown-item {
    cursor: pointer;
    white-space: normal;
}

.cv-typeahead-select-list .dropdown-item mark {
    padding: 0;
    color: inherit;
    background-color: var(--bs-highlight-bg, #fff3cd);
}

.cv-typeahead-select-list .dropdown-item.active mark {
    color: inherit;
    background-color: transparent;
    text-decoration: underline;
}

.cv-typeahead-select-list .cv-typeahead-select-info {
    cursor: default;
    color: var(--bs-secondary-color);
    font-size: 0.875em;
}
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_typeahead_select_js.py -q`
Expected: all pass.

Run: `uv run pytest -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
uv run ruff check . && uv run ruff format .
git add src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.js \
  src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.css \
  tests/test_typeahead_select_js.py
git commit -m "feat(typeahead): select popup frontend with scroll paging"
```

---

### Task 5: Example app — pick-assignee modal and popup filter

**Files:**
- Modify: `examples/bootstrap5/typeahead/typeahead.py`
- Modify: `examples/bootstrap5/typeahead/forms.py`
- Modify: `examples/bootstrap5/typeahead/views.py`
- Modify: `examples/bootstrap5/project/features.py`
- Test: `examples/bootstrap5/typeahead/tests.py`

**Interfaces:**
- Consumes: `TypeaheadSelect` (Task 3), `TypeaheadField`, `TypeaheadFilter`, `register_user_lookup`, `DemoUserLookup` (example), endpoint `page` (Task 1).
- Produces: lookup `typeahead.team_members_browse`; `TaskPickForm`; `TaskPickAssigneeView` (`cv_key = "pick_assignee"`, URL name `task-pick_assignee`); `TaskFilter.assignee` rendered as the popup.

- [ ] **Step 1: Write the failing example tests**

In `examples/bootstrap5/typeahead/tests.py`, add a helper after `typeahead()`:

```python
def typeahead_select(markup: str, name: str) -> dict:
    """data-url, trigger label and hidden value of the rendered select popup for field ``name``."""
    block = re.search(rf'<div class="cv-typeahead-select".*?name="{name}"[^>]*>', markup, re.S).group(0)
    label = re.search(r"<span[^>]*data-cv-typeahead-select-label[^>]*>(.*?)</span>", block, re.S).group(1)
    value = re.search(rf'<input type="hidden" name="{name}"[^>]*value="([^"]*)"', block).group(1)
    return {
        "url": html.unescape(re.search(r'data-url="([^"]*)"', block).group(1)),
        "label": html.unescape(label),
        "value": html.unescape(value),
    }
```

Replace the class `TaskFilterTest` with:

```python
class TaskFilterTest(TypeaheadTestCase):
    def test_filter_by_assignee(self):
        resp = self.client.get(self.url("list"), {"assignee": self.member.pk})
        self.assertContains(resp, "Fix login")
        self.assertNotContains(resp, "Write docs")

    def test_filter_renders_the_popup_with_the_label(self):
        markup = self.client.get(self.url("list"), {"assignee": self.member.pk}).content.decode()
        found = typeahead_select(markup, "assignee")
        self.assertEqual((found["label"], found["value"]), ("Mia Member (t-member)", str(self.member.pk)))
        self.assertIn('data-submit-on-clear="true"', markup)
        self.assertIn("crud_views_widget_typeahead/typeahead-select.js", markup)

    def test_filter_offers_members_of_any_team(self):
        markup = self.client.get(self.url("list"), follow=True).content.decode()
        body = self.client.get(typeahead_select(markup, "assignee")["url"] + "&q=mia").json()
        self.assertEqual(
            sorted(r["label"] for r in body["results"]), ["Mia Member (t-member)", "Mia Outsider (t-outsider)"]
        )

    def test_filter_needs_two_characters(self):
        markup = self.client.get(self.url("list"), follow=True).content.decode()
        self.assertEqual(self.client.get(typeahead_select(markup, "assignee")["url"] + "&q=m").json()["count"], 0)
```

Append a new class:

```python
class TaskPickModalTest(TypeaheadTestCase):
    def test_list_offers_pick_assignee(self):
        self.assertContains(self.client.get(self.url("list")), self.url("pick_assignee", pk=self.task.pk))

    def test_modal_partial_contains_the_popup(self):
        resp = self.client.get(self.url("pick_assignee", pk=self.task.pk), HTTP_X_CV_MODAL="true")
        self.assertEqual(resp.status_code, 200)
        markup = resp.content.decode()
        self.assertNotIn("<html", markup)
        found = typeahead_select(markup, "assignee")
        self.assertEqual((found["label"], found["value"]), ("Mia Member (t-member)", str(self.member.pk)))

    def test_popup_browses_team_members_without_a_query(self):
        markup = self.client.get(self.url("pick_assignee", pk=self.task.pk), HTTP_X_CV_MODAL="true").content.decode()
        url = typeahead_select(markup, "assignee")["url"]
        body = self.client.get(f"{url}&q=&page=1").json()
        self.assertEqual([r["label"] for r in body["results"]], ["Mia Member (t-member)"])
        self.assertEqual(body["count"], 1)

    def test_valid_modal_post_answers_204(self):
        resp = self.client.post(
            self.url("pick_assignee", pk=self.other_task.pk), {"assignee": self.member.pk}, HTTP_X_CV_MODAL="true"
        )
        self.assertEqual(resp.status_code, 204)
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.assignee, self.member)

    def test_outsider_is_rejected(self):
        resp = self.client.post(
            self.url("pick_assignee", pk=self.other_task.pk), {"assignee": self.outsider.pk}, HTTP_X_CV_MODAL="true"
        )
        self.assertEqual(resp.status_code, 200)
        self.other_task.refresh_from_db()
        self.assertIsNone(self.other_task.assignee)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd examples/bootstrap5 && uv run pytest typeahead/tests.py -q`
Expected: FAIL — `NoReverseMatch` for `task-pick_assignee`, and `AttributeError: 'NoneType' object has no attribute 'group'` in `typeahead_select` (the filter still renders the text typeahead).

- [ ] **Step 3: Add the browse lookup**

In `examples/bootstrap5/typeahead/typeahead.py`, append:

```python
class DemoBrowseLookup(DemoUserLookup):
    """The select popup lists the first members on open (min_chars = 0) and loads more on scroll."""

    min_chars = 0


@register_user_lookup("typeahead.team_members_browse", base=DemoBrowseLookup)
def team_members_browse(request, team):
    _check(request)
    return get_object_or_404(Team, pk=team).members.all()
```

- [ ] **Step 4: Add the form and switch the filter**

In `examples/bootstrap5/typeahead/forms.py`, add the import:

```python
from crud_views_widget_typeahead.widgets import TypeaheadSelect
```

Add after `TaskForm`:

```python
class TaskPickForm(CrispyModelForm):
    """The select popup: browse the team's members on open, scroll to load more, or search."""

    assignee = TypeaheadField(
        lookup="typeahead.team_members_browse", widget=TypeaheadSelect(), required=False, label=_("assignee")
    )

    class Meta:
        model = Task
        fields = ["assignee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        team = self.cv_view.cv_get_parent_object()
        self.fields["assignee"].bind(self.cv_view.request, team=str(team.pk))

    def get_layout_fields(self):
        return [Row(Column6("assignee"))]
```

In `TaskFilter`, replace the `assignee` line and its docstring with:

```python
class TaskFilter(django_filters.FilterSet):
    """Filter by any team member with the select popup — the case the project this widget replaces solved with
    dal + Select2. min_chars stays 2 here, so the popup asks for two characters before searching."""

    assignee = TypeaheadFilter(
        lookup="typeahead.any_member", widget=TypeaheadSelect(submit_on_clear=True), label=_("assignee")
    )
```

(keep `do_not_call_in_templates`, `Meta` and `__init__` unchanged).

- [ ] **Step 5: Add the modal view**

In `examples/bootstrap5/typeahead/views.py`, change the forms import to:

```python
from typeahead.forms import TaskFilter, TaskFilterFormHelper, TaskForm, TaskPickForm
```

In `TaskListView`, set:

```python
    cv_list_actions = ["detail", "update", "quick_assign", "pick_assignee", "delete"]
```

Add after `TaskQuickAssignView`:

```python
class TaskPickAssigneeView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    """TypeaheadSelect in a crud_views modal: typeahead-select.js initialises on cv:modal:loaded, the popup lives
    inside the widget (not in <body>), and Escape closes only the popup."""

    cv_viewset = cv_task
    cv_key = "pick_assignee"
    cv_path = "pick-assignee"
    cv_permission = "change"
    cv_modal = True
    form_class = TaskPickForm
    cv_icon_action = "fa-solid fa-hand-pointer"
    cv_action_label_template_code = _("Pick assignee")
    cv_action_short_label_template_code = _("Pick assignee")
    cv_header_template_code = _("Pick an assignee for “{{ object }}”")
    cv_paragraph_template_code = _("The select popup: browse the team's members, scroll for more, or search.")
    cv_message_template_code = _("Updated task “{{ object }}”")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        return kwargs

    def cv_form_valid(self, context: dict):
        context["form"].save()
```

- [ ] **Step 6: Update the feature card**

In `examples/bootstrap5/project/features.py`, replace the typeahead `Feature`'s `title`, `description`, `about` and `look_at` with:

```python
        title="Typeahead: thousands of users",
        description="Server-backed type-ahead and select popup, scoped per team, in forms, modals and a list filter.",
        about=(
            "Each team has about 500 of 3,000 seeded users: too many for a <select>. The task form's assignee is a "
            "TypeaheadField bound to the 'typeahead.team_members' lookup with the team from the URL, so the "
            "suggestions and the save-time validation are the same set. “Quick assign” shows the text typeahead "
            "in a crud_views modal; “Pick assignee” shows the TypeaheadSelect popup, which browses the team on "
            "open and loads more on scroll. The task list filter uses the popup over any team member."
        ),
        look_at=(
            "typeahead.py (the lookups); TaskForm, TaskPickForm and TaskFilter (bind in __init__) in forms.py; the "
            "'_typeahead/' include in project/urls.py."
        ),
```

- [ ] **Step 7: Run the example tests and the root suite**

Run: `cd examples/bootstrap5 && uv run pytest -q`
Expected: all pass (including the unchanged `AboutTest`, which reads `about` from `FEATURES`).

Run (repo root): `uv run pytest -q`
Expected: all pass.

- [ ] **Step 8: Lint and commit**

```bash
uv run ruff check . && uv run ruff format .
git add examples/bootstrap5/typeahead examples/bootstrap5/project/features.py
git commit -m "feat(example): pick-assignee modal and list filter with the select popup"
```

---

### Task 6: Documentation

**Files:**
- Modify: `README.md` (section `## crud_views_widget_typeahead`, before `## Example app`)
- Modify: `CLAUDE.md` (`### crud_views_widget_typeahead` and the test-count line)

**Interfaces:**
- Consumes: the public names from Tasks 1–5.
- Produces: user-facing docs; no code.

- [ ] **Step 1: README — settings table, endpoint, new section**

In `README.md`, extend the `### Settings` table of the typeahead section with two rows (after `DEBOUNCE_MS`):

```markdown
| `SELECT_EMIT` | `True` | `False` suppresses the select popup's `cv_js`/`cv_css` output (skins, django-pipeline) |
| `SELECT_TEMPLATE` | `"crud_views_widget_typeahead/typeahead_select.html"` | select popup template |
```

and replace the line `django-pipeline: \`from crud_views_widget_typeahead.assets import source_files\` (Django-free).` with:

```markdown
django-pipeline: `from crud_views_widget_typeahead.assets import source_files, select_source_files`
(Django-free). `source_files()` is the text typeahead only; add `select_source_files()` if you use the popup.
`DEBOUNCE_MS` applies to both widgets.
```

In `### Endpoint`, replace the first sentence with:

```markdown
`GET <mount>/?t=<token>&q=<term>[&page=<n>]` → `{"results": [{"value", "label"}], "count": n}` (`count` before
truncation). `page` is 1-based with `max_results` rows per page (missing or invalid → 1); results are ordered by
the lookup's ordering with the pk as final tiebreaker, so pages never repeat or skip rows.
```

Insert a new subsection before `### Skins`:

````markdown
### Select popup

`TypeaheadSelect` is a second widget for the same fields and filters: a trigger that looks like a Bootstrap
`<select>`, opening a popup with a search field and a list that loads the next page when scrolled to the end.
Choose it per field; both widgets can appear on one page.

```python
from crud_views_widget_typeahead.widgets import TypeaheadSelect

assignee = TypeaheadField(lookup="projects.members", widget=TypeaheadSelect())
assignee = TypeaheadFilter(lookup="projects.members", widget=TypeaheadSelect(submit_on_clear=True))
```

`bind()` works exactly as above. A lookup with `min_chars = 0` lists its first page as soon as the popup opens;
otherwise the popup asks for `min_chars` characters first. Keyboard: Enter, Space or ↑/↓ (or typing) opens;
↑/↓ move, Enter selects, Escape closes only the popup (a surrounding crud_views modal stays open); Enter never
submits while it is open. The popup is rendered inside the widget, so it works in crud_views modals; it can be
clipped by an ancestor with `overflow: hidden`.

Its skin contract mirrors the one below: `SELECT_TEMPLATE` (or the widget's `template_name`) gets
`widget.typeahead` with every key listed under Skins plus `popup_id`, `search_id`, `page_size`, and i18n keys
`placeholder`, `search`, `loading`, `type_more`; register your own JS/CSS and set `SELECT_EMIT = False`; keep the
hidden-input contract and the behaviours above. Dynamically added content needs
`window.cvTypeaheadSelect.init(container)`.
````

- [ ] **Step 2: CLAUDE.md — architecture bullets and test count**

In `CLAUDE.md` under `### crud_views_widget_typeahead`, replace the `views.py` bullet with:

```markdown
- **`views.py`** — the single endpoint; JSON errors only (never a login redirect — `fetch` must get JSON). Optional
  1-based `page` (page size = `max_results`); `_with_pk_tiebreaker()` appends `pk` to the lookup's ordering so OFFSET
  paging never repeats or skips rows.
```

and after the `static/.../typeahead.js` bullet add:

```markdown
- **`TypeaheadSelect`** (`widgets.py`) + `typeahead_select.html` + `static/.../typeahead-select.js`/`.css` — the
  select popup: trigger button, popup with search field and scroll-paged list, rendered inside the widget (a
  body-level dropdown breaks under crud_views' Bootstrap 5 modal). Own asset bundle `typeahead_select` and own
  settings `SELECT_EMIT`/`SELECT_TEMPLATE`, so a text-typeahead skin never touches it. Self-contained JS on purpose
  (helpers duplicated from `typeahead.js`, not shared).
```

Run `uv run pytest -q` and replace `(161 tests, ~0.3s)` in the commands block with the actual count and time from its last line, e.g. `(NNN tests, ~0.4s)`.

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs(typeahead): select popup usage, settings, paging and skin contract"
```

---

### Task 7: Browser checklist and final verification

**Files:** none committed unless a defect is found (then fix test-first in the owning task's files and commit separately).

**Interfaces:**
- Consumes: everything above, running in the example app.
- Produces: a written checklist result in the final report.

- [ ] **Step 1: Run both suites and lint**

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest -q
cd examples/bootstrap5 && uv run pytest -q
```

Expected: clean lint, all tests pass in both suites.

- [ ] **Step 2: Start the example server**

```bash
cd examples/bootstrap5 && uv run manage.py migrate && uv run manage.py seed && uv run manage.py runserver 8000
```

(run in the background; log in as `admin` / `admin`). Team and task ids: open `/typeahead/team/`, pick a team, open its task list.

- [ ] **Step 3: Drive the checklist with Playwright and record each result**

1. Open via click, Enter, Space, ↓ and a typed character on the "Pick assignee" modal's trigger; focus lands in the search field (`document.activeElement` is `input[type=search]`).
2. Browse on open; scroll the list to its end repeatedly across ≥ 3 pages: collect all option labels and pks, assert no duplicate pks and that the count reaches `min(30, count)`.
3. Search ("luk"), select by keyboard (↓, Enter) and, on reopen, by mouse; the trigger shows the label; a `change` listener on the hidden input fires each time.
4. In the modal: popup is visible above the modal content (`document.elementFromPoint` on an option returns the option) and receives focus; Escape closes only the popup (`#cv-modal.show` still present); select + Save closes the modal and the list row shows the new assignee.
5. Enter in the open popup never submits (URL and modal unchanged); Enter on the closed trigger opens it.
6. Clear button on the list filter submits the form (`submit_on_clear`) and the URL drops `assignee`.
7. Filter: typing one character shows "Type at least 2 characters."; choosing a user submits `?assignee=<pk>`; after reload the trigger shows the lookup label (`Name (username)`), not the username.
8. Strict CSP: start a second server with `django.middleware.csp.ContentSecurityPolicyMiddleware` and `SECURE_CSP` = `default-src 'self'`; `script-src`/`style-src` `'self'` + nonce + `https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com`; `font-src` same hosts; `img-src 'self' data:`; `connect-src 'self'` (a scratch settings module importing `project.settings`, never committed). Run a full cycle (open, scroll-load, search, select, clear) and collect console messages: zero CSP violations. Positive control: inject `<span style="color: rgb(255, 0, 0)">` via a `div.innerHTML` in `page.evaluate` and confirm a violation is reported.
9. Clipping: in DevTools add `modal-dialog-scrollable` to `#cv-modal .modal-dialog`, and separately wrap a widget's parent with `overflow: hidden`; record whether the popup is clipped (expected for `overflow: hidden`, documented in the README).
10. German locale (switch language to Deutsch in the navbar): the popup strings render (they are English: the package ships no translation catalog, same as the text typeahead); record this.
11. Accessibility tree (`browser_snapshot`): trigger exposes a button with `expanded` state and the field label; the search field is a combobox with `aria-activedescendant` following ↑/↓; the live region text equals the result count after page 1. Record as found; do not claim screen-reader compliance.
12. Both widgets on one page: on the task list page with "Quick assign" open (text typeahead) after using the filter popup, both work and neither's events affect the other.

- [ ] **Step 4: Fix defects test-first, if any**

For each failing item: add a failing pytest (or a JS static check, where the defect is in markup/contract) in the owning task's test file, fix, rerun both suites, commit with `fix(typeahead): <what>`.

- [ ] **Step 5: Stop the servers and report**

Stop all servers started in this task. Report each checklist item as passed / failed-and-fixed / observed (items 9–11), with the evidence (assertion values, screenshots paths).
