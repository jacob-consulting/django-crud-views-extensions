# Typeahead Widget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `crud_views_widget_typeahead`, a server-backed single-select typeahead (lookup registry, signed tokens, one JSON endpoint, `TypeaheadField`/`TypeaheadFilter`, vanilla-JS Bootstrap 5 frontend) plus an example app.

**Architecture:** A lookup class (registered by name) owns the allowed set, permission check, search and labels. `field.bind(request, **params)` sets the field's queryset from the lookup (validation = suggestions) and gives the widget a signed `{lookup, params}` token; the browser calls one generic endpoint with that token, which re-runs the lookup per request. The widget renders a nameless visible input + named hidden pk input + data attributes; a vanilla JS file (delivered page-globally through the crud_views asset registry) turns them into an ARIA combobox. A skin swaps the template and the JS, keeping the server core.

**Tech Stack:** Django 6 (supports ≥ 5.2 behaviour), django-crud-views 0.29 (asset registry, crispy, ViewSets), django-filter, pytest + pytest-django, vanilla ES2017 JS, Bootstrap 5 classes.

**Spec:** `docs/superpowers/specs/2026-10-15-typeahead-design.md`

## Global Constraints

- App package: `src/crud_views_widget_typeahead/`; app config `crud_views_widget_typeahead.apps.CrudViewsWidgetTypeaheadConfig`, `verbose_name = "CRUD Views Widget: Typeahead"`. Module names are public import paths.
- Settings key: `CRUD_VIEWS_TYPEAHEAD` with keys `EMIT` (default `True`), `TEMPLATE` (default `"crud_views_widget_typeahead/typeahead.html"`), `DEBOUNCE_MS` (default `250`). Only `conf.py` touches `django.conf.settings`.
- `assets.py` must import without Django.
- Asset registry key: `"typeahead"`. Static paths: `crud_views_widget_typeahead/typeahead.js`, `crud_views_widget_typeahead/typeahead.css`.
- URL namespace `crud_views_typeahead`, URL name `lookup`.
- Signing salt: `"crud_views.typeahead"`; token payload `{"l": name, "p": params}`; no expiry.
- Endpoint JSON: `{"results": [{"value": str, "label": str}], "count": int}`; errors `{"error": "bad_token"|"login_required"|"forbidden"|"not_found"}` with 400/403/403/404; 405 for non-GET.
- No `Media` classes; no inline scripts/styles; JS never uses `innerHTML`.
- Line length 120, double quotes (`uv run ruff check . && uv run ruff format .`).
- Root `uv run pytest` must stay green after every task; example app tests run from `examples/bootstrap5` with `uv run pytest`.
- Do not bump the package version.

## Review Focus

- A model **instance** (not a pk) as the field's initial value or passed straight to `widget.render()` must render the label → Task 4 `test_initial_instance_renders_label`.
- A search term of only whitespace must behave like an empty term (no query, empty result) → Task 3 `test_whitespace_only_term_is_empty`.
- `%` and `_` in the search term are literal characters, not SQL wildcards → Task 2 `test_like_wildcards_are_literal`.
- Labels containing HTML must be escaped in the server-rendered visible input (the JS side is safe by construction) → Task 4 `test_label_html_is_escaped`.
- A form built with `auto_id=False` must still render consistent ids (`aria-controls` matches the listbox id) → Task 4 `test_auto_id_false_still_consistent`.

---

## File Structure

```
src/crud_views_widget_typeahead/
  __init__.py                 empty
  apps.py                     ready(): register_assets + autodiscover_modules("typeahead")
  conf.py                     CRUD_VIEWS_TYPEAHEAD -> TypeaheadConfig
  assets.py                   Django-free static path lists
  lookups.py                  TypeaheadLookup, UserLookup, registry, LookupNotFound
  tokens.py                   make_token / read_token, BadToken
  views.py                    lookup_view (the endpoint)
  urls.py                     app_name="crud_views_typeahead", name="lookup"
  widgets.py                  TypeaheadBinding, TypeaheadInput
  fields.py                   TypeaheadField
  filters.py                  TypeaheadFilter
  templates/crud_views_widget_typeahead/typeahead.html
  static/crud_views_widget_typeahead/typeahead.js
  static/crud_views_widget_typeahead/typeahead.css
tests/
  conftest.py                 (modify) INSTALLED_APPS, ROOT_URLCONF
  urls.py                     includes the typeahead URLconf
  testapp/__init__.py, typeahead.py, templates/testapp/custom_typeahead.html
  test_typeahead_assets.py, test_typeahead_lookups.py, test_typeahead_tokens.py,
  test_typeahead_view.py, test_typeahead_fields.py, test_typeahead_widget.py,
  test_typeahead_filter.py, test_typeahead_js.py
examples/bootstrap5/typeahead/  example app (models, lookups, forms, views, urls, seed, tests, migrations)
examples/bootstrap5/project/    (modify) settings.py, urls.py, features.py, templatetags/*.py
pyproject.toml, .github/workflows/*.yml, README.md, CLAUDE.md   (modify)
```

---

### Task 1: App skeleton, settings, asset registration

**Files:**
- Create: `src/crud_views_widget_typeahead/__init__.py`, `apps.py`, `conf.py`, `assets.py`
- Modify: `pyproject.toml`, `tests/conftest.py`
- Test: `tests/test_typeahead_assets.py`

**Interfaces:**
- Produces: `conf.get_config() -> TypeaheadConfig(emit: bool, template: str, debounce_ms: int)`; `conf.DEFAULT_TEMPLATE`; `assets.APP_LABEL`, `assets.JS`, `assets.CSS`, `assets.source_files() -> {"js": [...], "css": [...]}`, `assets.bundle()` (same).

- [ ] **Step 1: Register the package with the build and coverage**

In `pyproject.toml` change

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/crud_views_widget_datetimepicker"]
```

to

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/crud_views_widget_datetimepicker", "src/crud_views_widget_typeahead"]
```

and

```toml
[tool.coverage.run]
source = ["crud_views_widget_datetimepicker"]
```

to

```toml
[tool.coverage.run]
source = ["crud_views_widget_datetimepicker", "crud_views_widget_typeahead"]
```

Create an empty `src/crud_views_widget_typeahead/__init__.py`. Then run `uv sync --extra dev` so the editable install picks up the new package.

- [ ] **Step 2: Write the failing tests**

`tests/test_typeahead_assets.py`:

```python
import subprocess
import sys

from django.apps import apps
from django.template import Context, Template

from crud_views_widget_typeahead.assets import APP_LABEL, CSS, JS, bundle, source_files
from crud_views_widget_typeahead.conf import DEFAULT_TEMPLATE, TypeaheadConfig, get_config


def _entry_path(entry) -> str:
    return getattr(entry, "path", entry)


def test_source_files():
    assert APP_LABEL == "crud_views_widget_typeahead"
    assert source_files() == {
        "js": ["crud_views_widget_typeahead/typeahead.js"],
        "css": ["crud_views_widget_typeahead/typeahead.css"],
    }
    assert JS == "crud_views_widget_typeahead/typeahead.js"
    assert CSS == "crud_views_widget_typeahead/typeahead.css"


def test_bundle_equals_source_files():
    assert bundle() == source_files()


def test_assets_module_is_django_free():
    code = "import sys, crud_views_widget_typeahead.assets; assert 'django' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True)


def test_app_is_installed():
    assert apps.get_app_config("crud_views_widget_typeahead").verbose_name == "CRUD Views Widget: Typeahead"


def test_bundle_registered_at_startup():
    from crud_views.lib.assets import get_registered

    bundle_ = {b.key: b for b in get_registered()}["typeahead"]
    assert [_entry_path(e) for e in bundle_.js] == [JS]
    assert [_entry_path(e) for e in bundle_.css] == [CSS]
    assert bundle_.emit is True


def test_cv_js_and_cv_css_include_typeahead():
    js = Template("{% load crud_views %}{% cv_js %}").render(Context({}))
    css = Template("{% load crud_views %}{% cv_css %}").render(Context({}))
    assert "/static/crud_views_widget_typeahead/typeahead.js" in js
    assert "/static/crud_views_widget_typeahead/typeahead.css" in css


def test_config_defaults():
    assert get_config() == TypeaheadConfig(emit=True, template=DEFAULT_TEMPLATE, debounce_ms=250)
    assert DEFAULT_TEMPLATE == "crud_views_widget_typeahead/typeahead.html"


def test_config_overrides(settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"EMIT": False, "TEMPLATE": "x/y.html", "DEBOUNCE_MS": 100}
    assert get_config() == TypeaheadConfig(emit=False, template="x/y.html", debounce_ms=100)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_typeahead_assets.py -v`
Expected: FAIL (`ModuleNotFoundError: crud_views_widget_typeahead.assets`).

- [ ] **Step 4: Implement**

`src/crud_views_widget_typeahead/assets.py`:

```python
"""Asset path definitions. Django-free by design: importable from settings.py,
so django-pipeline users can build bundles from the same single source of truth
that AppConfig.ready() feeds into the crud_views asset registry."""

APP_LABEL = "crud_views_widget_typeahead"
JS = f"{APP_LABEL}/typeahead.js"
CSS = f"{APP_LABEL}/typeahead.css"


def source_files() -> dict:
    """Static paths for pipeline source_filenames. No third-party plugin: nothing to vendor."""
    return {"js": [JS], "css": [CSS]}


def bundle() -> dict:
    """The js/css lists to register with the crud_views asset registry."""
    return source_files()
```

`src/crud_views_widget_typeahead/conf.py`:

```python
from dataclasses import dataclass

from django.conf import settings

DEFAULT_TEMPLATE = "crud_views_widget_typeahead/typeahead.html"


@dataclass(frozen=True)
class TypeaheadConfig:
    emit: bool = True
    template: str = DEFAULT_TEMPLATE
    debounce_ms: int = 250


def get_config() -> TypeaheadConfig:
    raw = getattr(settings, "CRUD_VIEWS_TYPEAHEAD", {}) or {}
    return TypeaheadConfig(
        emit=raw.get("EMIT", True),
        template=raw.get("TEMPLATE", DEFAULT_TEMPLATE),
        debounce_ms=int(raw.get("DEBOUNCE_MS", 250)),
    )
```

`src/crud_views_widget_typeahead/apps.py`:

```python
from django.apps import AppConfig


class CrudViewsWidgetTypeaheadConfig(AppConfig):
    name = "crud_views_widget_typeahead"
    verbose_name = "CRUD Views Widget: Typeahead"

    def ready(self):
        from crud_views.lib.assets import register_assets
        from django.utils.module_loading import autodiscover_modules

        from .assets import bundle
        from .conf import get_config

        b = bundle()
        register_assets(key="typeahead", js=b["js"], css=b["css"], emit=get_config().emit)
        # admin-style: import every installed app's typeahead.py so its lookups register
        autodiscover_modules("typeahead")
```

In `tests/conftest.py`, extend `INSTALLED_APPS` (after the datetimepicker entry):

```python
            "crud_views_widget_datetimepicker.apps.CrudViewsWidgetDatetimepickerConfig",
            "django_filters",
            "crud_views_widget_typeahead.apps.CrudViewsWidgetTypeaheadConfig",
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest -v`
Expected: all pass (existing 62 + 8 new).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock src/crud_views_widget_typeahead tests/conftest.py tests/test_typeahead_assets.py
git commit -m "feat(typeahead): app skeleton, settings and asset registration"
```

---

### Task 2: Lookups and registry

**Files:**
- Create: `src/crud_views_widget_typeahead/lookups.py`, `tests/testapp/__init__.py`, `tests/testapp/typeahead.py`
- Modify: `tests/conftest.py`
- Test: `tests/test_typeahead_lookups.py`

**Interfaces:**
- Consumes: `apps.py` autodiscovery (Task 1).
- Produces:
  - `class LookupNotFound(ImproperlyConfigured)`
  - `class TypeaheadLookup` with attributes `search_fields: list[str]`, `ordering: list`, `max_results: int = 10`, `min_chars: int = 2`, `login_required: bool = True` and methods `get_queryset(request, **params) -> QuerySet`, `label(obj) -> str`, `value(obj) -> str`, `filter(queryset, q: str) -> QuerySet`
  - `class UserLookup(TypeaheadLookup)`
  - `register_lookup(name: str)` (class decorator, returns the class), `register_user_lookup(name: str, base=UserLookup)` (function decorator, returns the function), `get_lookup(name: str) -> TypeaheadLookup`
  - module dict `_registry` (tests only)
  - Test lookups (autodiscovered): `"testapp.group_members"` (params `group`: str pk; `"forbidden"` → `PermissionDenied`; missing → `Http404`), `"testapp.groups"` (`search_fields=["name"]`, `ordering=["name"]`, `max_results=2`, `login_required=False`), `"testapp.all_users"` (no params).

- [ ] **Step 1: Add the test app**

`tests/testapp/__init__.py`: empty.

`tests/testapp/typeahead.py`:

```python
"""Lookups for the package tests. Imported by autodiscovery (CrudViewsWidgetTypeaheadConfig.ready)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from crud_views_widget_typeahead.lookups import TypeaheadLookup, register_lookup, register_user_lookup


@register_user_lookup("testapp.group_members")
def group_members(request, group):
    if group == "forbidden":
        raise PermissionDenied
    return get_object_or_404(Group, pk=group).user_set.all()


@register_user_lookup("testapp.all_users")
def all_users(request):
    return get_user_model().objects.all()


@register_lookup("testapp.groups")
class GroupLookup(TypeaheadLookup):
    search_fields = ["name"]
    ordering = ["name"]
    max_results = 2
    login_required = False

    def get_queryset(self, request, **params):
        return Group.objects.all()
```

In `tests/conftest.py` append `"tests.testapp",` to `INSTALLED_APPS` (after the typeahead app).

- [ ] **Step 2: Write the failing tests**

`tests/test_typeahead_lookups.py`:

```python
import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ImproperlyConfigured

from crud_views_widget_typeahead import lookups
from crud_views_widget_typeahead.lookups import (
    LookupNotFound,
    TypeaheadLookup,
    UserLookup,
    get_lookup,
    register_lookup,
    register_user_lookup,
)


@pytest.fixture
def registry():
    """Undo registrations made by a test."""
    saved = dict(lookups._registry)
    yield
    lookups._registry.clear()
    lookups._registry.update(saved)


@pytest.fixture
def people(db):
    make = User.objects.create_user
    return {
        "anna": make("amueller", first_name="Anna", last_name="Müller"),
        "andreas": make("aschmidt", first_name="Andreas", last_name="Schmidt"),
        "bert": make("bmueller", first_name="Bert", last_name="Müller"),
        "plain": make("zz_plain"),
    }


def search(q, lookup=None):
    return list((lookup or UserLookup()).filter(User.objects.all(), q))


def test_every_word_must_match(people):
    assert search("mül an") == [people["anna"]]


def test_words_may_match_different_fields(people):
    assert search("bert bmue") == [people["bert"]]


def test_case_insensitive(people):
    assert search("SCHMIDT") == [people["andreas"]]


def test_empty_term_returns_all_ordered(people):
    # Lower(last_name), Lower(first_name), Lower(username): the user without names sorts first
    assert search("   ") == [people["plain"], people["anna"], people["bert"], people["andreas"]]


def test_like_wildcards_are_literal(people):
    assert search("%") == []
    assert search("_") == [people["plain"]]


def test_results_are_distinct(people):
    people["anna"].groups.add(Group.objects.create(name="g1"), Group.objects.create(name="g2"))

    class ByGroup(UserLookup):
        search_fields = ["groups__name"]

    assert search("g", ByGroup()) == [people["anna"]]


def test_empty_search_fields_with_term_raises(db):
    with pytest.raises(ImproperlyConfigured):
        TypeaheadLookup().filter(User.objects.none(), "x")


def test_empty_search_fields_without_term_is_fine(db):
    assert list(TypeaheadLookup().filter(User.objects.none(), "")) == []


def test_get_queryset_must_be_implemented():
    with pytest.raises(NotImplementedError):
        TypeaheadLookup().get_queryset(None)


def test_user_label(people):
    assert UserLookup().label(people["anna"]) == "Anna Müller"
    assert UserLookup().label(people["plain"]) == "zz_plain"


def test_default_label_and_value(db):
    group = Group.objects.create(name="x")
    assert TypeaheadLookup().label(group) == "x"
    assert TypeaheadLookup().value(group) == str(group.pk)


def test_defaults():
    lookup = TypeaheadLookup()
    assert (lookup.max_results, lookup.min_chars, lookup.login_required) == (10, 2, True)


def test_register_and_get(registry):
    @register_lookup("t.groups")
    class L(TypeaheadLookup):
        search_fields = ["name"]

    assert isinstance(get_lookup("t.groups"), L)


def test_duplicate_registration_raises(registry):
    register_lookup("t.dup")(TypeaheadLookup)
    with pytest.raises(ImproperlyConfigured):
        register_lookup("t.dup")(TypeaheadLookup)


def test_unknown_lookup_raises():
    with pytest.raises(LookupNotFound):
        get_lookup("nope.nope")
    assert issubclass(LookupNotFound, ImproperlyConfigured)


def test_register_user_lookup(registry, people):
    @register_user_lookup("t.muellers")
    def muellers(request, **params):
        return User.objects.filter(last_name="Müller")

    lookup = get_lookup("t.muellers")
    assert isinstance(lookup, UserLookup)
    assert set(lookup.get_queryset(None)) == {people["anna"], people["bert"]}
    assert muellers(None).count() == 2  # the decorated function stays usable


def test_register_user_lookup_with_custom_base(registry):
    class Short(UserLookup):
        max_results = 3

    @register_user_lookup("t.short", base=Short)
    def short(request):
        return User.objects.none()

    assert isinstance(get_lookup("t.short"), Short)
    assert get_lookup("t.short").max_results == 3


def test_autodiscovery_registered_testapp_lookups():
    assert isinstance(get_lookup("testapp.group_members"), UserLookup)
    assert get_lookup("testapp.groups").search_fields == ["name"]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_typeahead_lookups.py -v`
Expected: FAIL. Collection or setup raises `ModuleNotFoundError: crud_views_widget_typeahead.lookups`, because autodiscovery imports `tests/testapp/typeahead.py` at startup.

- [ ] **Step 4: Implement**

`src/crud_views_widget_typeahead/lookups.py`:

```python
"""Typeahead lookups: one registered class per use case owns the allowed set (including the permission
check), the search and the labels. The endpoint and TypeaheadField both resolve lookups by name, so the
restriction is written once."""

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, QuerySet
from django.db.models.functions import Lower


class LookupNotFound(ImproperlyConfigured):
    pass


_registry: dict[str, "TypeaheadLookup"] = {}


class TypeaheadLookup:
    search_fields: list[str] = []  # icontains; every word must match some field
    ordering: list = []
    max_results = 10
    min_chars = 2
    login_required = True

    def get_queryset(self, request, **params) -> QuerySet:
        """The allowed set for this request and params. Raise PermissionDenied / Http404 to refuse."""
        raise NotImplementedError(f"{type(self).__name__} must implement get_queryset(request, **params)")

    def label(self, obj) -> str:
        return str(obj)

    def value(self, obj) -> str:
        return str(obj.pk)

    def filter(self, queryset: QuerySet, q: str) -> QuerySet:
        words = q.split()
        if words and not self.search_fields:
            raise ImproperlyConfigured(f"{type(self).__name__}.search_fields is empty, cannot search for {q!r}")
        for word in words:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f"{field}__icontains": word})
            queryset = queryset.filter(condition)
        queryset = queryset.distinct()
        if self.ordering:
            queryset = queryset.order_by(*self.ordering)
        return queryset


class UserLookup(TypeaheadLookup):
    search_fields = ["first_name", "last_name", "username"]
    ordering = [Lower("last_name"), Lower("first_name"), Lower("username")]

    def label(self, obj) -> str:
        return obj.get_full_name() or obj.get_username()


def register_lookup(name: str):
    """Class decorator: register an instance of the decorated TypeaheadLookup subclass under ``name``."""

    def decorator(cls):
        if name in _registry:
            raise ImproperlyConfigured(f"typeahead lookup {name!r} is already registered")
        _registry[name] = cls()
        return cls

    return decorator


def register_user_lookup(name: str, base: type[TypeaheadLookup] = UserLookup):
    """Function decorator: register ``func(request, **params) -> QuerySet`` as the get_queryset of a ``base``
    subclass. The function itself is returned unchanged."""

    def decorator(func):
        def get_queryset(self, request, **params):
            return func(request, **params)

        cls = type(f"{func.__name__}_lookup", (base,), {"get_queryset": get_queryset, "__module__": func.__module__})
        register_lookup(name)(cls)
        return func

    return decorator


def get_lookup(name: str) -> TypeaheadLookup:
    try:
        return _registry[name]
    except KeyError:
        raise LookupNotFound(f"typeahead lookup {name!r} is not registered") from None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/crud_views_widget_typeahead/lookups.py tests/testapp tests/conftest.py tests/test_typeahead_lookups.py
git commit -m "feat(typeahead): lookup classes and registry with autodiscovery"
```

---

### Task 3: Signed tokens and the endpoint

**Files:**
- Create: `src/crud_views_widget_typeahead/tokens.py`, `views.py`, `urls.py`, `tests/urls.py`
- Modify: `tests/conftest.py`
- Test: `tests/test_typeahead_tokens.py`, `tests/test_typeahead_view.py`

**Interfaces:**
- Consumes: `get_lookup`, `LookupNotFound`, test lookups (Task 2).
- Produces: `tokens.SALT`, `class BadToken(Exception)`, `make_token(name: str, params: dict) -> str`, `read_token(token: str) -> tuple[str, dict]`; `views.lookup_view(request) -> JsonResponse`; URL `crud_views_typeahead:lookup` (mounted at `/typeahead/` in tests).

- [ ] **Step 1: Write the failing token tests**

`tests/test_typeahead_tokens.py`:

```python
import datetime
import uuid

import pytest
from django.core import signing
from django.core.exceptions import ImproperlyConfigured

from crud_views_widget_typeahead.lookups import LookupNotFound
from crud_views_widget_typeahead.tokens import SALT, BadToken, make_token, read_token


def test_round_trip():
    token = make_token("testapp.group_members", {"group": "1"})
    assert read_token(token) == ("testapp.group_members", {"group": "1"})


def test_salt():
    assert SALT == "crud_views.typeahead"


@pytest.mark.parametrize("token", ["", "garbage", "x" + make_token("testapp.groups", {})])
def test_bad_signature(token):
    with pytest.raises(BadToken):
        read_token(token)


def test_other_salt_is_rejected():
    with pytest.raises(BadToken):
        read_token(signing.dumps({"l": "testapp.groups", "p": {}}))


@pytest.mark.parametrize("payload", [["x"], {"l": "testapp.groups"}, {"l": "testapp.groups", "p": [1]}, {"p": {}}])
def test_wrong_shape(payload):
    with pytest.raises(BadToken):
        read_token(signing.dumps(payload, salt=SALT))


def test_unknown_lookup_in_token():
    with pytest.raises(BadToken):
        read_token(signing.dumps({"l": "nope.nope", "p": {}}, salt=SALT))


def test_make_token_unknown_lookup():
    with pytest.raises(LookupNotFound):
        make_token("nope.nope", {})


@pytest.mark.parametrize(
    "params", [{"id": uuid.uuid4()}, {"day": datetime.date(2026, 1, 1)}, {"ids": (1, 2)}, ["x"], None]
)
def test_make_token_rejects_non_json_params(params):
    with pytest.raises(ImproperlyConfigured):
        make_token("testapp.groups", params)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_typeahead_tokens.py -v`
Expected: FAIL (`ModuleNotFoundError: crud_views_widget_typeahead.tokens`).

- [ ] **Step 3: Implement tokens**

`src/crud_views_widget_typeahead/tokens.py`:

```python
"""Signed widget tokens: the browser carries {lookup, params} but cannot change them.

No expiry on purpose: the endpoint re-checks permission on every request via the lookup's
get_queryset(request, **params), so a form left open overnight keeps working and a leaked token grants
nothing beyond what the requesting user may see anyway."""

import json

from django.core import signing
from django.core.exceptions import ImproperlyConfigured

from .lookups import LookupNotFound, get_lookup

SALT = "crud_views.typeahead"


class BadToken(Exception):
    """Bad signature, wrong payload shape or unknown lookup."""


def make_token(name: str, params: dict) -> str:
    get_lookup(name)  # LookupNotFound for unregistered names, at bind time
    try:
        serialisable = isinstance(params, dict) and json.loads(json.dumps(params)) == params
    except (TypeError, ValueError):
        serialisable = False
    if not serialisable:
        raise ImproperlyConfigured(
            f"typeahead params for {name!r} must be a dict of JSON values (pass UUIDs, dates and model instances "
            f"as str): {params!r}"
        )
    return signing.dumps({"l": name, "p": params}, salt=SALT, compress=True)


def read_token(token: str) -> tuple[str, dict]:
    try:
        data = signing.loads(token, salt=SALT)
    except signing.BadSignature as e:
        raise BadToken("bad signature") from e
    if not isinstance(data, dict) or not isinstance(data.get("l"), str) or not isinstance(data.get("p"), dict):
        raise BadToken("wrong shape")
    try:
        get_lookup(data["l"])
    except LookupNotFound as e:
        raise BadToken("unknown lookup") from e
    return data["l"], data["p"]
```

- [ ] **Step 4: Run token tests to verify they pass**

Run: `uv run pytest tests/test_typeahead_tokens.py -v`
Expected: PASS.

- [ ] **Step 5: Write the failing endpoint tests**

`tests/urls.py`:

```python
from django.urls import include, path

urlpatterns = [path("typeahead/", include("crud_views_widget_typeahead.urls"))]
```

In `tests/conftest.py` add `ROOT_URLCONF="tests.urls",` to `settings.configure(...)` (next to `STATIC_URL`).

`tests/test_typeahead_view.py`:

```python
import json

import pytest
from django.contrib.auth.models import AnonymousUser, Group, User
from django.test import RequestFactory
from django.urls import reverse

from crud_views_widget_typeahead.tokens import make_token
from crud_views_widget_typeahead.views import lookup_view

rf = RequestFactory()


def call(token, q="", user=None, method="get"):
    """Status and decoded JSON body of the endpoint; RequestFactory keeps auth query-free."""
    params = {"q": q} if token is None else {"t": token, "q": q}
    request = getattr(rf, method)("/typeahead/", params)
    request.user = user if user is not None else AnonymousUser()
    response = lookup_view(request)
    return response.status_code, (json.loads(response.content) if response.content else None)


@pytest.fixture
def team(db):
    group = Group.objects.create(name="team")
    member = User.objects.create_user("mmember", first_name="Mia", last_name="Member")
    User.objects.create_user("ooutsider", first_name="Mia", last_name="Outsider")
    group.user_set.add(member)
    return {"group": group, "member": member, "viewer": User.objects.create_user("viewer")}


def token_for(group):
    return make_token("testapp.group_members", {"group": str(group.pk)})


def test_results_are_scoped_to_the_lookup(team):
    status, body = call(token_for(team["group"]), "mia", team["viewer"])
    assert status == 200
    assert body == {"results": [{"value": str(team["member"].pk), "label": "Mia Member"}], "count": 1}


def test_count_is_taken_before_slicing(db):
    for name in ["alpha1", "alpha2", "alpha3", "beta"]:
        Group.objects.create(name=name)
    status, body = call(make_token("testapp.groups", {}), "alpha")
    assert status == 200
    assert body["count"] == 3
    assert [r["label"] for r in body["results"]] == ["alpha1", "alpha2"]  # max_results = 2, ordered by name


def test_short_term_runs_no_query(team, django_assert_num_queries):
    token = token_for(team["group"])
    with django_assert_num_queries(0):
        assert call(token, "m", team["viewer"]) == (200, {"results": [], "count": 0})


def test_whitespace_only_term_is_empty(team, django_assert_num_queries):
    token = token_for(team["group"])
    with django_assert_num_queries(0):
        assert call(token, "      ", team["viewer"]) == (200, {"results": [], "count": 0})


def test_term_is_stripped(team):
    status, body = call(token_for(team["group"]), "  mia  ", team["viewer"])
    assert body["count"] == 1


@pytest.mark.parametrize("token", [None, "", "garbage"])
def test_bad_token(db, token):
    assert call(token, "mia") == (400, {"error": "bad_token"})


def test_anonymous_gets_json_403_not_a_redirect(team):
    assert call(token_for(team["group"]), "mia") == (403, {"error": "login_required"})


def test_lookup_without_login_requirement_serves_anonymous(db):
    Group.objects.create(name="alpha")
    status, body = call(make_token("testapp.groups", {}), "alp")
    assert (status, body["count"]) == (200, 1)


def test_permission_denied_from_lookup(team):
    token = make_token("testapp.group_members", {"group": "forbidden"})
    assert call(token, "mia", team["viewer"]) == (403, {"error": "forbidden"})


def test_http404_from_lookup(team):
    token = make_token("testapp.group_members", {"group": "999999"})
    assert call(token, "mia", team["viewer"]) == (404, {"error": "not_found"})


def test_post_is_not_allowed(team):
    status, _ = call(token_for(team["group"]), "mia", team["viewer"], method="post")
    assert status == 405


def test_response_is_never_cached(team):
    request = rf.get("/typeahead/", {"t": token_for(team["group"]), "q": "mia"})
    request.user = team["viewer"]
    assert "no-store" in lookup_view(request)["Cache-Control"]


def test_url_is_routed(db, client):
    url = reverse("crud_views_typeahead:lookup")
    assert url == "/typeahead/"
    assert client.get(url, {"t": "garbage"}).status_code == 400
```

- [ ] **Step 6: Run to verify failure**

Run: `uv run pytest tests/test_typeahead_view.py -v`
Expected: FAIL (`ModuleNotFoundError: crud_views_widget_typeahead.views`, or the URLconf import fails).

- [ ] **Step 7: Implement the endpoint**

`src/crud_views_widget_typeahead/views.py`:

```python
"""The one generic typeahead endpoint: GET ?t=<token>&q=<term> -> JSON.

Errors are JSON too (fetch() must never receive a login page), and never echo exception messages."""

from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .lookups import get_lookup
from .tokens import BadToken, read_token


def _error(code: str, status: int) -> JsonResponse:
    return JsonResponse({"error": code}, status=status)


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
    try:
        queryset = lookup.filter(lookup.get_queryset(request, **params), q)
        count = queryset.count()
        results = [{"value": lookup.value(obj), "label": lookup.label(obj)} for obj in queryset[: lookup.max_results]]
    except PermissionDenied:
        return _error("forbidden", 403)
    except Http404:
        return _error("not_found", 404)
    return JsonResponse({"results": results, "count": count})
```

`src/crud_views_widget_typeahead/urls.py`:

```python
from django.urls import path

from . import views

app_name = "crud_views_typeahead"

urlpatterns = [path("", views.lookup_view, name="lookup")]
```

- [ ] **Step 8: Run all tests**

Run: `uv run pytest -v`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add src/crud_views_widget_typeahead/tokens.py src/crud_views_widget_typeahead/views.py \
  src/crud_views_widget_typeahead/urls.py tests/urls.py tests/conftest.py \
  tests/test_typeahead_tokens.py tests/test_typeahead_view.py
git commit -m "feat(typeahead): signed tokens and the JSON lookup endpoint"
```

---

### Task 4: Widget, field and template

**Files:**
- Create: `src/crud_views_widget_typeahead/widgets.py`, `fields.py`, `templates/crud_views_widget_typeahead/typeahead.html`, `tests/testapp/templates/testapp/custom_typeahead.html`
- Test: `tests/test_typeahead_fields.py`, `tests/test_typeahead_widget.py`

**Interfaces:**
- Consumes: `get_lookup` (Task 2), `make_token` (Task 3), `get_config` (Task 1), URL `crud_views_typeahead:lookup`.
- Produces:
  - `widgets.TypeaheadBinding(token: str, lookup_name: str, queryset)` (frozen dataclass)
  - `widgets.TypeaheadInput(attrs=None, submit_on_clear: bool = False, template_name: str | None = None)` with attributes `binding: TypeaheadBinding | None` and `submit_on_clear`, and a settable `template_name` property
  - `fields.TypeaheadField(lookup: str, queryset=None, **ModelChoiceField kwargs)` with attribute `lookup_name` and method `bind(request, **params) -> TypeaheadField`
  - The widget context contract for skins: `widget.attrs` (visible input) plus `widget.typeahead` with keys `url, label, value, hidden_name, hidden_id, listbox_id, hint_id, min_chars, debounce, submit_on_clear, i18n`; `i18n` has keys `hint, more, none, count, error, clear, listbox`, and `more`/`count` contain the placeholder `{n}`.

- [ ] **Step 1: Write the failing field tests**

`tests/test_typeahead_fields.py`:

```python
import copy
import uuid

import pytest
from django import forms
from django.contrib.auth.models import Group, User
from django.core.exceptions import ImproperlyConfigured, PermissionDenied

from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.tokens import read_token
from crud_views_widget_typeahead.widgets import TypeaheadInput


class MemberForm(forms.Form):
    member = TypeaheadField(lookup="testapp.group_members")


@pytest.fixture
def team(db):
    group = Group.objects.create(name="team")
    member = User.objects.create_user("mmember", first_name="Mia", last_name="Member")
    outsider = User.objects.create_user("ooutsider", first_name="Mia", last_name="Outsider")
    group.user_set.add(member)
    return {"group": group, "member": member, "outsider": outsider}


def bound_form(team, data=None):
    form = MemberForm(data)
    form.fields["member"].bind(None, group=str(team["group"].pk))
    return form


def test_default_widget_is_typeahead_input():
    assert isinstance(MemberForm().fields["member"].widget, TypeaheadInput)


def test_bind_sets_queryset_and_binding(team):
    field = bound_form(team).fields["member"]
    assert list(field.queryset) == [team["member"]]
    binding = field.widget.binding
    assert binding.lookup_name == "testapp.group_members"
    assert read_token(binding.token) == ("testapp.group_members", {"group": str(team["group"].pk)})


def test_bind_returns_the_field(team):
    field = MemberForm().fields["member"]
    assert field.bind(None, group=str(team["group"].pk)) is field


def test_member_validates(team):
    form = bound_form(team, {"member": str(team["member"].pk)})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["member"] == team["member"]


def test_outsider_is_rejected(team):
    form = bound_form(team, {"member": str(team["outsider"].pk)})
    assert not form.is_valid()
    assert form.errors.as_data()["member"][0].code == "invalid_choice"


def test_required_empty_is_a_required_error(team):
    form = bound_form(team, {"member": ""})
    assert not form.is_valid()
    assert form.errors.as_data()["member"][0].code == "required"


def test_unbound_clean_raises(db):
    with pytest.raises(ImproperlyConfigured, match="bind"):
        MemberForm({"member": "1"}).is_valid()


def test_unbound_render_raises(db):
    with pytest.raises(ImproperlyConfigured, match="bind"):
        str(MemberForm()["member"])


def test_bind_rejects_non_json_params(team):
    with pytest.raises(ImproperlyConfigured):
        MemberForm().fields["member"].bind(None, group=uuid.uuid4())


def test_bind_propagates_permission_denied(db):
    with pytest.raises(PermissionDenied):
        MemberForm().fields["member"].bind(None, group="forbidden")


def test_binding_an_instance_field_leaves_the_class_field_unbound(team):
    bound_form(team)
    assert MemberForm.base_fields["member"].queryset is None
    assert MemberForm.base_fields["member"].widget.binding is None


def test_rebinding_a_copy_leaves_the_original_alone(team):
    other = Group.objects.create(name="other")
    field = bound_form(team).fields["member"]
    original_binding = field.widget.binding
    clone = copy.deepcopy(field)
    clone.bind(None, group=str(other.pk))
    assert field.widget.binding is original_binding
    assert list(field.queryset) == [team["member"]]
    assert list(clone.queryset) == []
```

- [ ] **Step 2: Write the failing widget tests**

`tests/testapp/templates/testapp/custom_typeahead.html`:

```html
<custom-typeahead data-url="{{ widget.typeahead.url }}" data-value="{{ widget.typeahead.value }}"></custom-typeahead>
```

`tests/test_typeahead_widget.py`:

```python
import html
import re
from urllib.parse import parse_qs, urlsplit

import pytest
from django import forms
from django.contrib.auth.models import Group, User

from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.tokens import read_token
from crud_views_widget_typeahead.widgets import TypeaheadInput


class MemberForm(forms.Form):
    member = TypeaheadField(lookup="testapp.group_members", help_text="Pick a member")
    note = forms.CharField()


@pytest.fixture
def team(db):
    group = Group.objects.create(name="team")
    member = User.objects.create_user("mmember", first_name="Mia", last_name="Member")
    outsider = User.objects.create_user("ooutsider", first_name="Mia", last_name="Outsider")
    group.user_set.add(member)
    return {"group": group, "member": member, "outsider": outsider}


def render(team, **form_kwargs) -> str:
    form = MemberForm(**form_kwargs)
    form.fields["member"].bind(None, group=str(team["group"].pk))
    return str(form["member"])


def tag(markup: str, pattern: str) -> str:
    return re.search(pattern, markup).group(0)


def text_input(markup: str) -> str:
    return tag(markup, r'<input type="text"[^>]*>')


def hidden_input(markup: str) -> str:
    return tag(markup, r'<input type="hidden"[^>]*>')


def attr(element: str, name: str):
    match = re.search(rf'\s{re.escape(name)}="([^"]*)"', element)
    return html.unescape(match.group(1)) if match else None


def test_visible_input_has_no_name_hidden_input_has(team):
    markup = render(team)
    assert attr(text_input(markup), "name") is None
    hidden = hidden_input(markup)
    assert attr(hidden, "name") == "member"
    assert attr(hidden, "id") == "id_member_value"
    assert attr(hidden, "autocomplete") == "off"


def test_initial_pk_renders_label(team):
    markup = render(team, initial={"member": team["member"].pk})
    assert attr(text_input(markup), "value") == "Mia Member"
    assert attr(hidden_input(markup), "value") == str(team["member"].pk)


def test_initial_instance_renders_label(team):
    markup = render(team, initial={"member": team["member"]})
    assert attr(text_input(markup), "value") == "Mia Member"
    form = MemberForm()
    form.fields["member"].bind(None, group=str(team["group"].pk))
    assert 'value="Mia Member"' in form.fields["member"].widget.render("member", team["member"])


def test_label_is_rerendered_after_a_validation_error(team):
    markup = render(team, data={"member": str(team["member"].pk), "note": ""})
    assert attr(text_input(markup), "value") == "Mia Member"
    assert attr(hidden_input(markup), "value") == str(team["member"].pk)


@pytest.mark.parametrize("value", ["abc", "999999", "1.5"])
def test_garbage_pk_renders_empty(team, value):
    markup = render(team, data={"member": value, "note": "x"})
    assert attr(text_input(markup), "value") == ""
    assert attr(hidden_input(markup), "value") == ""


def test_out_of_scope_pk_renders_empty(team):
    markup = render(team, data={"member": str(team["outsider"].pk), "note": "x"})
    assert attr(text_input(markup), "value") == ""
    assert attr(hidden_input(markup), "value") == ""


def test_label_html_is_escaped(team):
    team["member"].first_name = "<b>Mia</b>"
    team["member"].save()
    markup = render(team, initial={"member": team["member"].pk})
    assert "<b>Mia</b>" not in markup
    assert "&lt;b&gt;Mia&lt;/b&gt;" in markup


def test_aria_attributes(team):
    markup = render(team)
    text = text_input(markup)
    assert attr(text, "id") == "id_member"
    assert attr(text, "role") == "combobox"
    assert attr(text, "aria-autocomplete") == "list"
    assert attr(text, "aria-expanded") == "false"
    assert attr(text, "aria-controls") == "id_member_listbox"
    assert attr(text, "autocomplete") == "off"
    assert "form-control" in attr(text, "class").split()
    listbox = tag(markup, r"<ul[^>]*>")
    assert attr(listbox, "id") == "id_member_listbox"
    assert attr(listbox, "role") == "listbox"
    assert attr(listbox, "aria-label")
    assert 'id="id_member_hint"' in markup
    assert "aria-live" in markup


def test_aria_describedby_merges_django_ids_with_hint(team):
    assert attr(text_input(render(team)), "aria-describedby") == "id_member_helptext id_member_hint"
    invalid = render(team, data={"member": "", "note": "x"})
    assert attr(text_input(invalid), "aria-describedby") == "id_member_helptext id_member_error id_member_hint"


def test_no_required_attribute(team):
    assert re.search(r"\srequired", text_input(render(team))) is None


def test_auto_id_false_still_consistent(team):
    markup = render(team, auto_id=False)
    text = text_input(markup)
    listbox = tag(markup, r"<ul[^>]*>")
    assert attr(text, "aria-controls") == attr(listbox, "id")
    assert attr(hidden_input(markup), "id") == f"{attr(text, 'id')}_value"


def test_data_attributes(team):
    markup = render(team)
    root = tag(markup, r"<div class=\"cv-typeahead\"[^>]*>")
    assert "data-cv-typeahead" in root
    url = urlsplit(attr(root, "data-url"))
    assert url.path == "/typeahead/"
    assert read_token(parse_qs(url.query)["t"][0]) == ("testapp.group_members", {"group": str(team["group"].pk)})
    assert attr(root, "data-min-chars") == "2"
    assert attr(root, "data-debounce") == "250"
    assert attr(root, "data-submit-on-clear") == "false"
    assert "{n}" in attr(root, "data-i18n-more")
    assert "{n}" in attr(root, "data-i18n-count")
    assert attr(root, "data-i18n-none")
    assert attr(root, "data-i18n-error")


def test_debounce_from_settings(team, settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"DEBOUNCE_MS": 400}
    assert 'data-debounce="400"' in render(team)


def test_clear_button_hidden_without_value(team):
    button = tag(render(team), r"<button[^>]*data-cv-typeahead-clear[^>]*>")
    assert re.search(r"\shidden", button)
    with_value = tag(render(team, initial={"member": team["member"].pk}), r"<button[^>]*data-cv-typeahead-clear[^>]*>")
    assert not re.search(r"\shidden", with_value)


def test_template_from_settings(team, settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"TEMPLATE": "testapp/custom_typeahead.html"}
    assert render(team).startswith("<custom-typeahead")


def test_template_per_instance(team):
    form = MemberForm()
    field = form.fields["member"]
    field.widget.template_name = "testapp/custom_typeahead.html"
    field.bind(None, group=str(team["group"].pk))
    assert str(form["member"]).startswith("<custom-typeahead")
    assert TypeaheadInput(template_name="x.html").template_name == "x.html"


def test_skin_context_contract(team):
    form = MemberForm()
    form.fields["member"].bind(None, group=str(team["group"].pk))
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
    }
    assert set(context["widget"]["typeahead"]["i18n"]) == {"hint", "more", "none", "count", "error", "clear", "listbox"}
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/test_typeahead_fields.py tests/test_typeahead_widget.py -v`
Expected: FAIL (`ModuleNotFoundError: crud_views_widget_typeahead.fields`).

- [ ] **Step 4: Implement the widget**

`src/crud_views_widget_typeahead/widgets.py`:

```python
"""Typeahead input widget.

Renders a visible text input without a name (the label), a hidden input carrying the name and the pk,
and data attributes for the frontend. No Media class on purpose: typeahead.js/.css are page-global via
cv_js/cv_css. The template (and with it the whole frontend) is swappable: see the README's skin contract.
"""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from django import forms
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.urls import reverse
from django.utils.translation import gettext, ngettext

from .conf import get_config
from .lookups import get_lookup


@dataclass(frozen=True)
class TypeaheadBinding:
    """What TypeaheadField.bind() hands the widget. Plain data without a reference back to the field:
    Widget.__deepcopy__ is shallow, so copies may share it, and re-binding a copy replaces only its own."""

    token: str
    lookup_name: str
    queryset: Any


def _i18n(min_chars: int) -> dict:
    return {
        "hint": ngettext(
            "Type at least %(count)d character, then choose with the arrow keys and Enter.",
            "Type at least %(count)d characters, then choose with the arrow keys and Enter.",
            min_chars,
        )
        % {"count": min_chars},
        "more": gettext("{n} more results – keep typing"),
        "none": gettext("No results"),
        "count": gettext("{n} results"),
        "error": gettext("Search failed"),
        "clear": gettext("Clear selection"),
        "listbox": gettext("Suggestions"),
    }


class TypeaheadInput(forms.Widget):
    def __init__(self, attrs=None, submit_on_clear: bool = False, template_name: str | None = None):
        super().__init__(attrs)
        self.submit_on_clear = submit_on_clear
        self._template_name = template_name
        self.binding: TypeaheadBinding | None = None

    @property
    def template_name(self) -> str:
        return self._template_name or get_config().template

    @template_name.setter
    def template_name(self, value: str | None):
        self._template_name = value

    def use_required_attribute(self, initial) -> bool:
        return False  # a required visible input would accept typed text without a pk

    def resolve(self, value):
        """The allowed object for a pk (or instance), or None for empty, garbage or out-of-scope values."""
        if self.binding is None or value in (None, ""):
            return None
        value = getattr(value, "pk", value)
        try:
            return self.binding.queryset.filter(pk=value).first()
        except (ValueError, TypeError, ValidationError):
            return None

    def get_context(self, name, value, attrs):
        if self.binding is None:
            raise ImproperlyConfigured(
                f"typeahead widget for {name!r} is not bound: call field.bind(request, ...) before rendering"
            )
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        lookup = get_lookup(self.binding.lookup_name)
        obj = self.resolve(value)
        text_attrs = widget["attrs"]
        text_id = text_attrs.get("id") or f"id_{name}"
        hint_id = f"{text_id}_hint"
        described_by = str(text_attrs.get("aria-describedby") or "").split()
        classes = str(text_attrs.get("class") or "").split()
        text_attrs.update(
            {
                "id": text_id,
                "class": " ".join(dict.fromkeys([*classes, "form-control"])),
                "autocomplete": "off",
                "role": "combobox",
                "aria-autocomplete": "list",
                "aria-expanded": "false",
                "aria-controls": f"{text_id}_listbox",
                # merge, never replace: Django adds <id>_helptext / <id>_error here
                "aria-describedby": " ".join(dict.fromkeys([*described_by, hint_id])),
            }
        )
        widget["typeahead"] = {
            "url": f"{reverse('crud_views_typeahead:lookup')}?{urlencode({'t': self.binding.token})}",
            "label": lookup.label(obj) if obj is not None else "",
            "value": lookup.value(obj) if obj is not None else "",
            "hidden_name": name,
            "hidden_id": f"{text_id}_value",
            "listbox_id": f"{text_id}_listbox",
            "hint_id": hint_id,
            "min_chars": lookup.min_chars,
            "debounce": get_config().debounce_ms,
            "submit_on_clear": self.submit_on_clear,
            "i18n": _i18n(lookup.min_chars),
        }
        return context
```

- [ ] **Step 5: Implement the template**

`src/crud_views_widget_typeahead/templates/crud_views_widget_typeahead/typeahead.html`:

```html
{% with ta=widget.typeahead %}<div class="cv-typeahead" data-cv-typeahead data-url="{{ ta.url }}" data-min-chars="{{ ta.min_chars }}" data-debounce="{{ ta.debounce }}" data-submit-on-clear="{{ ta.submit_on_clear|yesno:'true,false' }}" data-i18n-more="{{ ta.i18n.more }}" data-i18n-none="{{ ta.i18n.none }}" data-i18n-count="{{ ta.i18n.count }}" data-i18n-error="{{ ta.i18n.error }}">
  <div class="input-group">
    <input type="text" value="{{ ta.label }}"{% include "django/forms/widgets/attrs.html" %}>
    <button type="button" class="btn btn-outline-secondary" data-cv-typeahead-clear aria-label="{{ ta.i18n.clear }}"{% if not ta.value %} hidden{% endif %}><span aria-hidden="true">&times;</span></button>
  </div>
  <input type="hidden" name="{{ ta.hidden_name }}" id="{{ ta.hidden_id }}" value="{{ ta.value }}" autocomplete="off">
  <ul id="{{ ta.listbox_id }}" class="dropdown-menu cv-typeahead-menu" role="listbox" aria-label="{{ ta.i18n.listbox }}" hidden></ul>
  <span id="{{ ta.hint_id }}" class="visually-hidden">{{ ta.i18n.hint }}</span>
  <span class="visually-hidden" aria-live="polite" data-cv-typeahead-status></span>
</div>{% endwith %}
```

- [ ] **Step 6: Implement the field**

`src/crud_views_widget_typeahead/fields.py`:

```python
"""TypeaheadField: a ModelChoiceField whose queryset comes from a registered lookup.

bind(request, **params) is the single source of truth: it sets the queryset save-time validation uses
and hands the widget the signed token the endpoint uses, both from the same lookup and params."""

from django.core.exceptions import ImproperlyConfigured
from django.forms import ModelChoiceField

from .lookups import get_lookup
from .tokens import make_token
from .widgets import TypeaheadBinding, TypeaheadInput


class TypeaheadField(ModelChoiceField):
    widget = TypeaheadInput

    def __init__(self, lookup: str, queryset=None, **kwargs):
        self.lookup_name = lookup
        super().__init__(queryset, **kwargs)

    def bind(self, request, **params) -> "TypeaheadField":
        token = make_token(self.lookup_name, params)  # fails fast on unknown lookups and non-JSON params
        self.queryset = get_lookup(self.lookup_name).get_queryset(request, **params)
        self.widget.binding = TypeaheadBinding(token=token, lookup_name=self.lookup_name, queryset=self.queryset)
        return self

    def clean(self, value):
        if self.queryset is None:
            raise ImproperlyConfigured(
                f"TypeaheadField (lookup {self.lookup_name!r}) is not bound: call field.bind(request, ...)"
            )
        return super().clean(value)
```

- [ ] **Step 7: Run tests**

Run: `uv run pytest -v`
Expected: all pass. If `test_aria_describedby_merges_django_ids_with_hint` fails, print `text_input(...)` and check that Django passed its ids via `attrs` (they must not be set on `widget.attrs` at construction, or Django skips its own ids).

- [ ] **Step 8: Commit**

```bash
git add src/crud_views_widget_typeahead/widgets.py src/crud_views_widget_typeahead/fields.py \
  src/crud_views_widget_typeahead/templates tests/testapp/templates \
  tests/test_typeahead_fields.py tests/test_typeahead_widget.py
git commit -m "feat(typeahead): TypeaheadField, TypeaheadInput and default template"
```

---

### Task 5: django-filter integration

**Files:**
- Create: `src/crud_views_widget_typeahead/filters.py`
- Test: `tests/test_typeahead_filter.py`

**Interfaces:**
- Consumes: `TypeaheadField`, `TypeaheadInput` (Task 4); test lookup `testapp.all_users` (Task 2).
- Produces: `filters.TypeaheadFilter(*args, lookup: str, **ModelChoiceFilter kwargs)` with `bind(request, **params) -> TypeaheadFilter`. The default widget is `TypeaheadInput(submit_on_clear=True)`.

- [ ] **Step 1: Write the failing tests**

`tests/test_typeahead_filter.py`:

```python
import django_filters
import pytest
from django.contrib.auth.models import Group, User

from crud_views_widget_typeahead.filters import TypeaheadFilter
from crud_views_widget_typeahead.widgets import TypeaheadInput


class GroupFilter(django_filters.FilterSet):
    member = TypeaheadFilter(field_name="user", lookup="testapp.all_users")

    class Meta:
        model = Group
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["member"].bind(self.request)


@pytest.fixture
def groups(db):
    anna = User.objects.create_user("anna", first_name="Anna")
    bert = User.objects.create_user("bert", first_name="Bert")
    red, blue = Group.objects.create(name="red"), Group.objects.create(name="blue")
    red.user_set.add(anna)
    blue.user_set.add(bert)
    return {"anna": anna, "bert": bert, "red": red, "blue": blue}


def make(data=None):
    return GroupFilter(data, queryset=Group.objects.order_by("name"), request=None)


def test_filters_by_pk(groups):
    assert list(make({"member": str(groups["anna"].pk)}).qs) == [groups["red"]]


def test_empty_value_does_not_filter(groups):
    assert list(make({"member": ""}).qs) == [groups["blue"], groups["red"]]


def test_binding_survives_the_filter_form_copy(groups):
    field = make().form.fields["member"]
    assert field.widget.binding is not None
    assert set(field.queryset) == {groups["anna"], groups["bert"]}


def test_garbage_value_is_invalid_not_a_crash(groups):
    filterset = make({"member": "abc"})
    assert not filterset.is_valid()


def test_submit_on_clear_by_default(groups):
    assert 'data-submit-on-clear="true"' in str(make().form["member"])


def test_explicit_widget_is_kept(groups):
    class Plain(GroupFilter):
        member = TypeaheadFilter(field_name="user", lookup="testapp.all_users", widget=TypeaheadInput())

    filterset = Plain(None, queryset=Group.objects.all(), request=None)
    assert 'data-submit-on-clear="false"' in str(filterset.form["member"])


def test_bind_returns_the_filter(groups):
    filterset = make()
    assert filterset.filters["member"].bind(None) is filterset.filters["member"]
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_typeahead_filter.py -v`
Expected: FAIL (`ModuleNotFoundError: crud_views_widget_typeahead.filters`).

- [ ] **Step 3: Implement**

`src/crud_views_widget_typeahead/filters.py`:

```python
"""django-filter integration. Bind in the FilterSet's __init__:

    self.filters["user"].bind(self.request, team=str(team.pk))

Filter.field is cached and the filter form is built from it later, so the binding carries over.
URLs stay ?user=<pk>."""

import django_filters

from .fields import TypeaheadField
from .widgets import TypeaheadInput


class TypeaheadFilter(django_filters.ModelChoiceFilter):
    field_class = TypeaheadField

    def __init__(self, *args, lookup: str, **kwargs):
        kwargs.setdefault("widget", TypeaheadInput(submit_on_clear=True))
        kwargs["lookup"] = lookup  # passed through to TypeaheadField via Filter.extra
        super().__init__(*args, **kwargs)

    def bind(self, request, **params) -> "TypeaheadFilter":
        self.field.bind(request, **params)
        return self
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_widget_typeahead/filters.py tests/test_typeahead_filter.py
git commit -m "feat(typeahead): TypeaheadFilter for django-filter"
```

---

### Task 6: Default frontend (JS + CSS)

**Files:**
- Create: `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead.js`, `typeahead.css`
- Test: `tests/test_typeahead_js.py`

**Interfaces:**
- Consumes: the DOM the default template renders (Task 4): `[data-cv-typeahead]` root with `data-url`, `data-min-chars`, `data-debounce`, `data-submit-on-clear`, `data-i18n-{more,none,count,error}`; children `input[role=combobox]`, `input[type=hidden]`, `[role=listbox]`, `[data-cv-typeahead-status]`, `[data-cv-typeahead-clear]`.
- Produces: `window.cvTypeahead.init(root)`; re-init on the `cv:modal:loaded` event; a bubbling `change` event on the hidden input after selection or clearing.

- [ ] **Step 1: Write the failing static-content test**

`tests/test_typeahead_js.py`:

```python
from pathlib import Path

import crud_views_widget_typeahead as pkg

STATIC = Path(pkg.__file__).parent / "static" / "crud_views_widget_typeahead"


def test_js_contract():
    js = (STATIC / "typeahead.js").read_text()
    assert "[data-cv-typeahead]" in js
    assert "cv:modal:loaded" in js
    assert "window.cvTypeahead" in js
    assert "AbortController" in js
    assert "requestSubmit" in js
    assert "aria-activedescendant" in js


def test_js_is_csp_and_xss_safe():
    js = (STATIC / "typeahead.js").read_text()
    assert "innerHTML" not in js
    assert "insertAdjacentHTML" not in js
    assert ".style." not in js
    assert "eval(" not in js
    assert "console.log" not in js
    assert "jQuery" not in js and "$(" not in js


def test_css_exists():
    css = (STATIC / "typeahead.css").read_text()
    assert ".cv-typeahead-menu" in css
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_typeahead_js.py -v`
Expected: FAIL (`FileNotFoundError`).

- [ ] **Step 3: Write `typeahead.css`**

```css
/* crud_views_widget_typeahead — default Bootstrap 5 skin. Show/hide uses [hidden] + .show, never inline styles. */
.cv-typeahead {
    position: relative;
}

.cv-typeahead-menu {
    top: 100%;
    left: 0;
    width: 100%;
    max-height: 20rem;
    overflow-y: auto;
}

.cv-typeahead-menu.show {
    display: block;
}

.cv-typeahead-menu .dropdown-item {
    cursor: pointer;
    white-space: normal;
}

.cv-typeahead-menu .dropdown-item mark {
    padding: 0;
    color: inherit;
    background-color: var(--bs-highlight-bg, #fff3cd);
}

.cv-typeahead-menu .dropdown-item.active mark {
    color: inherit;
    background-color: transparent;
    text-decoration: underline;
}

.cv-typeahead-menu .cv-typeahead-info {
    cursor: default;
    color: var(--bs-secondary-color);
    font-size: 0.875em;
}
```

- [ ] **Step 4: Write `typeahead.js`**

```javascript
/*
 * crud_views_widget_typeahead — default frontend (vanilla JS, Bootstrap 5 markup).
 *
 * Contract (see README "Skins"): the visible input shows the label of the pk in the hidden input, except
 * while typing. Arrow keys preview text only; Enter selects when the list is open and never submits then.
 * Option text is built with textContent + <mark>, never innerHTML.
 *
 * Activates on DOMContentLoaded and on "cv:modal:loaded" (dispatched by crud_views after injecting modal
 * content). Call window.cvTypeahead.init(root) for other dynamically added content.
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

    class Typeahead {
        constructor(root) {
            this.root = root;
            this.input = root.querySelector('input[role="combobox"]');
            this.hidden = root.querySelector('input[type="hidden"]');
            this.list = root.querySelector('[role="listbox"]');
            this.status = root.querySelector("[data-cv-typeahead-status]");
            this.clearButton = root.querySelector("[data-cv-typeahead-clear]");
            this.url = root.dataset.url;
            this.minChars = parseInt(root.dataset.minChars, 10) || 0;
            this.debounce = parseInt(root.dataset.debounce, 10) || 0;
            this.submitOnClear = root.dataset.submitOnClear === "true";
            this.committed = this.input.value; // label of the stored pk
            this.options = []; // [{value, label, el}]
            this.active = -1;
            this.timer = null;
            this.controller = null;
            this.listen();
        }

        listen() {
            this.input.addEventListener("input", () => this.onInput());
            this.input.addEventListener("keydown", (e) => this.onKeydown(e));
            this.input.addEventListener("focusout", () => this.settle());
            // keep focus in the input while clicking an option, so focusout does not close the list first
            this.list.addEventListener("mousedown", (e) => e.preventDefault());
            if (this.clearButton) this.clearButton.addEventListener("click", () => this.clear(true));
            if (this.input.form) this.input.form.addEventListener("submit", () => this.settle(), true);
        }

        isOpen() {
            return !this.list.hidden;
        }

        onInput() {
            this.cancelPending();
            if (this.input.value.trim().length < this.minChars) {
                this.close();
                return;
            }
            this.timer = setTimeout(() => this.fetch(), this.debounce);
        }

        onKeydown(e) {
            const open = this.isOpen();
            switch (e.key) {
                case "ArrowDown":
                case "ArrowUp":
                    e.preventDefault();
                    if (open) {
                        this.move(e.key === "ArrowDown" ? 1 : -1);
                    } else if (e.key === "ArrowDown") {
                        this.cancelPending();
                        this.fetch();
                    }
                    break;
                case "Enter":
                    if (open) {
                        e.preventDefault(); // never submit while the list is open
                        if (this.active >= 0) this.select(this.active);
                    }
                    break;
                case "Escape":
                    if (open) {
                        e.preventDefault();
                        this.close();
                        this.input.value = this.committed;
                    }
                    break;
                case "Tab":
                    this.close();
                    break;
            }
        }

        /* Blur and submit: cancel pending work, then restore the invariant. Emptied text clears the pk. */
        settle() {
            this.cancelPending();
            this.close();
            if (this.input.value.trim() === "") {
                if (this.hidden.value !== "") this.clear(false);
            } else {
                this.input.value = this.committed;
            }
        }

        cancelPending() {
            clearTimeout(this.timer);
            this.timer = null;
            if (this.controller) {
                this.controller.abort();
                this.controller = null;
            }
        }

        fetch() {
            const q = this.input.value.trim();
            if (q.length < this.minChars) {
                this.close();
                return;
            }
            const controller = new AbortController();
            this.controller = controller;
            const url = this.url + (this.url.indexOf("?") === -1 ? "?" : "&") + "q=" + encodeURIComponent(q);
            fetch(url, {signal: controller.signal, credentials: "same-origin", headers: {Accept: "application/json"}})
                .then((response) => {
                    if (!response.ok) throw new Error("HTTP " + response.status);
                    return response.json();
                })
                .then((data) => {
                    if (this.controller !== controller) return; // superseded
                    this.controller = null;
                    if (document.activeElement !== this.input) return; // focus left meanwhile
                    this.render(data, q);
                })
                .catch((err) => {
                    if (err.name === "AbortError" || this.controller !== controller) return;
                    this.controller = null;
                    this.close();
                    this.announce(this.root.dataset.i18nError);
                    console.warn("cv-typeahead:", err);
                });
        }

        render(data, q) {
            const words = q.split(/\s+/).filter(Boolean);
            const results = data.results || [];
            const count = data.count || 0;
            this.list.replaceChildren();
            this.options = [];
            this.active = -1;
            this.input.removeAttribute("aria-activedescendant");
            results.forEach((item, i) => {
                const li = document.createElement("li");
                li.id = this.list.id + "_" + i;
                li.className = "dropdown-item";
                li.setAttribute("role", "option");
                li.setAttribute("aria-selected", "false");
                highlight(li, String(item.label), words);
                li.addEventListener("click", () => this.select(i));
                this.list.appendChild(li);
                this.options.push({value: String(item.value), label: String(item.label), el: li});
            });
            if (!results.length) {
                this.info(this.root.dataset.i18nNone);
            } else if (count > results.length) {
                this.info(fmt(this.root.dataset.i18nMore, count - results.length));
            }
            this.open();
            this.announce(fmt(this.root.dataset.i18nCount, count));
        }

        info(text) {
            const li = document.createElement("li");
            li.className = "dropdown-item-text cv-typeahead-info";
            li.setAttribute("role", "option");
            li.setAttribute("aria-disabled", "true");
            li.textContent = text;
            this.list.appendChild(li);
        }

        move(delta) {
            const n = this.options.length;
            if (!n) return;
            let next = this.active + delta;
            if (next < 0) next = n - 1;
            if (next >= n) next = 0;
            this.setActive(next);
            this.input.value = this.options[next].label; // preview only: the pk does not change
        }

        setActive(index) {
            this.options.forEach((opt, i) => {
                const on = i === index;
                opt.el.classList.toggle("active", on);
                opt.el.setAttribute("aria-selected", on ? "true" : "false");
            });
            this.active = index;
            const el = this.options[index].el;
            this.input.setAttribute("aria-activedescendant", el.id);
            el.scrollIntoView({block: "nearest"});
        }

        select(index) {
            const opt = this.options[index];
            this.hidden.value = opt.value;
            this.input.value = opt.label;
            this.committed = opt.label;
            this.close();
            this.changed();
        }

        clear(fromButton) {
            this.cancelPending();
            this.hidden.value = "";
            this.input.value = "";
            this.committed = "";
            this.close();
            this.changed();
            if (!fromButton) return;
            if (this.submitOnClear && this.input.form) {
                this.input.form.requestSubmit();
            } else {
                this.input.focus();
            }
        }

        changed() {
            if (this.clearButton) this.clearButton.hidden = this.hidden.value === "";
            this.hidden.dispatchEvent(new Event("change", {bubbles: true}));
        }

        open() {
            this.list.hidden = false;
            this.list.classList.add("show");
            this.input.setAttribute("aria-expanded", "true");
        }

        close() {
            this.list.hidden = true;
            this.list.classList.remove("show");
            this.input.setAttribute("aria-expanded", "false");
            this.input.removeAttribute("aria-activedescendant");
            this.active = -1;
        }

        announce(text) {
            if (this.status) this.status.textContent = text || "";
        }
    }

    function init(root) {
        (root || document).querySelectorAll("[data-cv-typeahead]").forEach(function (el) {
            if (el.dataset.cvTypeaheadReady) return;
            el.dataset.cvTypeaheadReady = "1";
            new Typeahead(el);
        });
    }

    window.cvTypeahead = {init: init};

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

- [ ] **Step 5: Run tests**

Run: `uv run pytest -v`
Expected: all pass.

- [ ] **Step 6: Syntax check**

Run: `node --check src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead.js` (skip this step if `node` is not installed).
Expected: no output, exit 0.

- [ ] **Step 7: Commit**

```bash
git add src/crud_views_widget_typeahead/static tests/test_typeahead_js.py
git commit -m "feat(typeahead): vanilla JS frontend and Bootstrap 5 styles"
```

---

### Task 7: Example app

**Files:**
- Create: `examples/bootstrap5/typeahead/__init__.py`, `apps.py`, `models.py`, `typeahead.py`, `forms.py`, `views.py`, `urls.py`, `seed.py`, `tests.py`, `migrations/__init__.py`, `migrations/0001_initial.py` (generated)
- Modify: `examples/bootstrap5/project/settings.py`, `project/urls.py`, `project/features.py`, `project/templatetags/<the module with feature_for>.py`

**Interfaces:**
- Consumes: `register_user_lookup`, `UserLookup`, `TypeaheadField`, `TypeaheadFilter`, URLconf `crud_views_widget_typeahead.urls`.
- Produces: ViewSets `team` (list, detail) and `task` (child of team: list with filter, detail, create, update, quick_assign modal, delete); lookups `typeahead.team_members` (param `team`) and `typeahead.any_member`; a Feature card with viewset `team`.

- [ ] **Step 1: Write the failing example tests**

`examples/bootstrap5/typeahead/tests.py`:

```python
import html
import re

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from typeahead.models import Task, Team


def typeahead(markup: str, name: str) -> dict:
    """data-url, visible text and hidden value of the rendered typeahead for field ``name``."""
    block = re.search(rf'<div class="cv-typeahead".*?name="{name}"[^>]*>', markup, re.S).group(0)

    def value(tag: str) -> str:
        match = re.search(r'value="([^"]*)"', tag)
        return html.unescape(match.group(1)) if match else ""

    return {
        "url": html.unescape(re.search(r'data-url="([^"]*)"', block).group(1)),
        "text": value(re.search(r'<input type="text"[^>]*>', block).group(0)),
        "value": value(re.search(rf'<input type="hidden" name="{name}"[^>]*>', block).group(0)),
    }


class TypeaheadTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(username="t-admin", password="pw")
        cls.team = Team.objects.create(name="Platform")
        cls.other_team = Team.objects.create(name="Payments")
        cls.member = User.objects.create_user("t-member", first_name="Mia", last_name="Member")
        cls.outsider = User.objects.create_user("t-outsider", first_name="Mia", last_name="Outsider")
        cls.team.members.add(cls.member)
        cls.other_team.members.add(cls.outsider)
        cls.task = Task.objects.create(team=cls.team, title="Fix login", assignee=cls.member)
        cls.other_task = Task.objects.create(team=cls.team, title="Write docs")

    def setUp(self):
        self.client.force_login(self.admin)

    def url(self, key, **kwargs):
        return reverse(f"task-{key}", kwargs={"team_pk": self.team.pk, **kwargs})


class TeamTest(TypeaheadTestCase):
    def test_team_list_links_to_tasks(self):
        resp = self.client.get(reverse("team-list"))
        self.assertContains(resp, self.url("list"))


class TaskFormTest(TypeaheadTestCase):
    def test_create_page_renders_typeahead(self):
        resp = self.client.get(self.url("create"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(typeahead(resp.content.decode(), "assignee")["url"].startswith("/_typeahead/?t="))
        self.assertContains(resp, "crud_views_widget_typeahead/typeahead.js")

    def test_endpoint_is_scoped_to_the_team(self):
        url = typeahead(self.client.get(self.url("create")).content.decode(), "assignee")["url"]
        body = self.client.get(url, {"q": "mia"}).json()
        self.assertEqual([r["label"] for r in body["results"]], ["Mia Member (t-member)"])

    def test_endpoint_requires_login(self):
        url = typeahead(self.client.get(self.url("create")).content.decode(), "assignee")["url"]
        self.client.logout()
        resp = self.client.get(url, {"q": "mia"})
        self.assertEqual((resp.status_code, resp.json()), (403, {"error": "login_required"}))

    def test_create_with_member(self):
        resp = self.client.post(self.url("create"), {"title": "New", "assignee": self.member.pk})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Task.objects.get(title="New").assignee, self.member)

    def test_create_with_outsider_is_rejected(self):
        resp = self.client.post(self.url("create"), {"title": "New", "assignee": self.outsider.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Task.objects.filter(title="New").exists())

    def test_update_shows_the_label(self):
        found = typeahead(self.client.get(self.url("update", pk=self.task.pk)).content.decode(), "assignee")
        self.assertEqual(found["text"], "Mia Member (t-member)")
        self.assertEqual(found["value"], str(self.member.pk))


class TaskModalTest(TypeaheadTestCase):
    def test_list_offers_quick_assign(self):
        self.assertContains(self.client.get(self.url("list")), self.url("quick_assign", pk=self.task.pk))

    def test_modal_partial_contains_typeahead(self):
        resp = self.client.get(self.url("quick_assign", pk=self.task.pk), HTTP_X_CV_MODAL="true")
        self.assertEqual(resp.status_code, 200)
        markup = resp.content.decode()
        self.assertNotIn("<html", markup)
        self.assertIn("data-cv-typeahead", markup)

    def test_valid_modal_post_answers_204(self):
        resp = self.client.post(
            self.url("quick_assign", pk=self.other_task.pk),
            {"title": "Write docs", "assignee": self.member.pk},
            HTTP_X_CV_MODAL="true",
        )
        self.assertEqual(resp.status_code, 204)
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.assignee, self.member)


class TaskFilterTest(TypeaheadTestCase):
    def test_filter_by_assignee(self):
        resp = self.client.get(self.url("list"), {"assignee": self.member.pk})
        self.assertContains(resp, "Fix login")
        self.assertNotContains(resp, "Write docs")

    def test_filter_offers_members_of_any_team(self):
        markup = self.client.get(self.url("list"), follow=True).content.decode()
        body = self.client.get(typeahead(markup, "assignee")["url"], {"q": "mia"}).json()
        self.assertEqual(
            sorted(r["label"] for r in body["results"]), ["Mia Member (t-member)", "Mia Outsider (t-outsider)"]
        )


class AboutTest(TypeaheadTestCase):
    def test_card_shows_on_team_and_task_pages(self):
        from project.features import FEATURES

        about = escape(next(f for f in FEATURES if f.viewset == "team").about)
        self.assertContains(self.client.get(reverse("team-list")), about)
        self.assertContains(self.client.get(self.url("list")), about)


class SeedTest(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed", verbosity=0)
        users, teams, tasks = get_user_model().objects.count(), Team.objects.count(), Task.objects.count()
        self.assertGreaterEqual(users, 3000)
        self.assertGreaterEqual(Team.objects.first().members.count(), 500)
        call_command("seed", verbosity=0)
        self.assertEqual(
            (get_user_model().objects.count(), Team.objects.count(), Task.objects.count()), (users, teams, tasks)
        )
```

- [ ] **Step 2: Models, app config, lookups**

`examples/bootstrap5/typeahead/__init__.py` and `migrations/__init__.py`: empty.

`examples/bootstrap5/typeahead/apps.py`:

```python
from django.apps import AppConfig


class TypeaheadExampleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "typeahead"
    label = "typeahead_example"  # distinct from the crud_views_widget_typeahead app label
```

`examples/bootstrap5/typeahead/models.py`:

```python
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Team(models.Model):
    name = models.CharField(_("name"), max_length=100, unique=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="teams", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("team")
        verbose_name_plural = _("teams")

    def __str__(self):
        return self.name


class Task(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(_("title"), max_length=100)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="typeahead_tasks",
        verbose_name=_("assignee"),
    )

    class Meta:
        ordering = ["title"]
        verbose_name = _("task")
        verbose_name_plural = _("tasks")

    def __str__(self):
        return self.title
```

`examples/bootstrap5/typeahead/typeahead.py`:

```python
"""Lookups for the example. CrudViewsWidgetTypeaheadConfig.ready() imports every app's typeahead.py."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from crud_views_widget_typeahead.lookups import UserLookup, register_user_lookup
from typeahead.models import Team


class DemoUserLookup(UserLookup):
    """Thousands of seeded users share names: show the username too."""

    def label(self, obj) -> str:
        return f"{obj.get_full_name() or obj.get_username()} ({obj.get_username()})"


def _check(request):
    # the endpoint must never reveal more than the pages do: same permission as the team pages
    if not request.user.has_perm("typeahead_example.view_team"):
        raise PermissionDenied


@register_user_lookup("typeahead.team_members", base=DemoUserLookup)
def team_members(request, team):
    _check(request)
    return get_object_or_404(Team, pk=team).members.all()


@register_user_lookup("typeahead.any_member", base=DemoUserLookup)
def any_member(request):
    _check(request)
    return get_user_model().objects.filter(teams__isnull=False).distinct()
```

- [ ] **Step 3: Forms**

`examples/bootstrap5/typeahead/forms.py`:

```python
import django_filters
from crispy_forms.layout import Layout, Row
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import Column6, CrispyModelForm
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.filters import TypeaheadFilter

from typeahead.models import Task


class TaskForm(CrispyModelForm):
    """The assignee choices are the team's members: bind() sets the queryset (validation) and the token
    (suggestions) from the same lookup and params."""

    assignee = TypeaheadField(lookup="typeahead.team_members", required=False, label=_("assignee"))

    class Meta:
        model = Task
        fields = ["title", "assignee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        team = self.cv_view.cv_get_parent_object()  # the team from the URL
        self.fields["assignee"].bind(self.cv_view.request, team=str(team.pk))

    def get_layout_fields(self):
        return [Row(Column6("title"), Column6("assignee"))]


class TaskFilter(django_filters.FilterSet):
    """Filter by any team member — the case the project this widget replaces solved with dal + Select2."""

    assignee = TypeaheadFilter(lookup="typeahead.any_member", label=_("assignee"))

    class Meta:
        model = Task
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["assignee"].bind(self.request)


class TaskFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column6("assignee")))
```

- [ ] **Step 4: Views and URLs**

`examples/bootstrap5/typeahead/views.py`:

```python
import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.table import LinkChildColumn, LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableFilterMixin,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from project.views import BreadcrumbMixin

from typeahead.forms import TaskFilter, TaskFilterFormHelper, TaskForm
from typeahead.models import Task, Team

# --------------------------------------------------------------------------- Team

cv_team = ViewSet(model=Team, name="team", icon_header="fa-solid fa-people-group")


class TeamTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    members = tables.Column(verbose_name=_("members"), accessor="pk", orderable=False)
    tasks = LinkChildColumn(name="task", verbose_name=_("tasks"))

    def render_members(self, record):
        return record.members.count()


class TeamListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_team
    table_class = TeamTable
    cv_list_actions = ["detail"]


class TeamDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_team
    cv_property_display = [{"title": _("Team"), "icon": "people-group", "properties": ["name"]}]


# --------------------------------------------------------------------------- Task (child of Team)

cv_task = ViewSet(model=Task, name="task", parent=ParentViewSet(name="team"), icon_header="fa-solid fa-list-check")


class TaskTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    assignee = tables.Column()


class TaskListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_task
    table_class = TaskTable
    filterset_class = TaskFilter
    formhelper_class = TaskFilterFormHelper
    cv_list_actions = ["detail", "update", "quick_assign", "delete"]


class TaskDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_task
    cv_property_display = [{"title": _("Task"), "icon": "list-check", "properties": ["title", "team", "assignee"]}]


class TaskCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_task
    form_class = TaskForm
    cv_message_template_code = _("Created task “{{ object }}”")


class TaskUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_task
    form_class = TaskForm
    cv_message_template_code = _("Updated task “{{ object }}”")


class TaskQuickAssignView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    """The same TaskForm in a crud_views modal: typeahead.js re-initialises on cv:modal:loaded."""

    cv_viewset = cv_task
    cv_key = "quick_assign"
    cv_path = "quick-assign"
    cv_permission = "change"
    cv_modal = True
    cv_modal_size = "modal-lg"
    form_class = TaskForm
    cv_icon_action = "fa-solid fa-user-check"
    cv_action_label_template_code = _("Quick assign")
    cv_action_short_label_template_code = _("Quick assign")
    cv_header_template_code = _("Assign “{{ object }}”")
    cv_paragraph_template_code = _("The same form as the update page, opened in a modal.")
    cv_message_template_code = _("Updated task “{{ object }}”")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        return kwargs

    def cv_form_valid(self, context: dict):
        context["form"].save()


class TaskDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_task
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted task “{{ object }}”")
```

Reformat with `uv run ruff format examples/bootstrap5/typeahead` (the `TaskCreateView` class line exceeds 120 characters).

`examples/bootstrap5/typeahead/urls.py`:

```python
from typeahead.views import cv_task, cv_team

urlpatterns = cv_team.urlpatterns + cv_task.urlpatterns
```

- [ ] **Step 5: Seed**

`examples/bootstrap5/typeahead/seed.py`:

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from typeahead.models import Task, Team

FIRST = [
    "Anna", "Ben", "Clara", "David", "Emma", "Felix", "Greta", "Hannah", "Jonas", "Lea",
    "Lukas", "Marie", "Noah", "Paul", "Sophie", "Tim", "Julia", "Max", "Laura", "Finn",
    "Mia", "Elias", "Lina", "Leon", "Ida", "Emil", "Nora", "Theo", "Ella", "Oskar",
]  # fmt: skip
LAST = [
    "Becker", "Braun", "Fischer", "Hartmann", "Hoffmann", "Koch", "Krüger", "Lange", "Meyer", "Müller",
    "Neumann", "Richter", "Schmidt", "Schneider", "Schröder", "Schulz", "Schwarz", "Wagner", "Weber", "Wolf",
    "Zimmermann", "Krause", "Lehmann", "Werner", "Schmitt", "Schmid", "Köhler", "Maier", "Herrmann", "König",
    "Walter", "Mayer", "Huber", "Kaiser", "Fuchs", "Peters", "Lang", "Scholz", "Möller", "Weiß",
    "Jung", "Hahn", "Schubert", "Vogel", "Friedrich", "Keller", "Günther", "Frank", "Berger", "Winkler",
]  # fmt: skip
USERS = 3000
TEAMS = ["Data", "Mobile", "Payments", "Platform"]
TEAM_SIZE = 500
TEAM_STRIDE = 400  # overlapping slices: some users are in two teams
TASKS = ["Fix login", "Write docs", "Review release", "Update dependencies", "Plan sprint"]


def seed():
    users = seed_users()
    seed_teams(users)


def seed_users() -> list[int]:
    User = get_user_model()
    if not User.objects.filter(username__startswith="demo-").exists():
        password = make_password(None)  # unusable: demo users cannot log in
        User.objects.bulk_create(
            User(
                username=f"demo-{i:04d}",
                first_name=FIRST[i % len(FIRST)],
                last_name=LAST[(i // len(FIRST)) % len(LAST)],
                password=password,
            )
            for i in range(USERS)
        )
    return list(User.objects.filter(username__startswith="demo-").order_by("username").values_list("pk", flat=True))


def seed_teams(users: list[int]):
    if Team.objects.exists():
        return
    for n, name in enumerate(TEAMS):
        team = Team.objects.create(name=name)
        members = users[n * TEAM_STRIDE : n * TEAM_STRIDE + TEAM_SIZE]
        team.members.add(*members)
        for j, title in enumerate(TASKS):
            Task.objects.create(team=team, title=title, assignee_id=members[j * 37] if j % 2 == 0 else None)
```

- [ ] **Step 6: Wire into the project**

`examples/bootstrap5/project/settings.py`, in `INSTALLED_APPS`:

```python
    "crud_views_widget_datetimepicker.apps.CrudViewsWidgetDatetimepickerConfig",
    "crud_views_widget_typeahead.apps.CrudViewsWidgetTypeaheadConfig",
    "project",
    # example feature apps (one per crud_views_widget_* extension)
    "datetimepicker",
    "typeahead.apps.TypeaheadExampleConfig",
]
```

Append to the end of `settings.py`:

```python
# crud_views_widget_typeahead — package defaults (EMIT=True, DEBOUNCE_MS=250); the endpoint is mounted in urls.py
```

`examples/bootstrap5/project/urls.py`, append:

```python
urlpatterns += [
    path("_typeahead/", include("crud_views_widget_typeahead.urls")),
    path("typeahead/", include("typeahead.urls")),
]
```

`examples/bootstrap5/project/features.py`, append to `FEATURES`:

```python
    Feature(
        app="typeahead",
        viewset="team",
        group="widgets",
        title="Typeahead: thousands of users",
        description="A server-backed type-ahead select, scoped per team, in forms, a modal and a list filter.",
        about=(
            "Each team has about 500 of 3,000 seeded users: too many for a <select>. The task form's assignee is a "
            "TypeaheadField bound to the 'typeahead.team_members' lookup with the team from the URL, so the "
            "suggestions and the save-time validation are the same set. The task list filters by any team member "
            "with a TypeaheadFilter. Open “Quick assign” on a task to use it inside a crud_views modal."
        ),
        look_at=(
            "typeahead.py (the lookups); TaskForm.__init__ and TaskFilter.__init__ (bind) in forms.py; the "
            "'_typeahead/' include in project/urls.py."
        ),
        url_name="team-list",
        icon="fa-solid fa-magnifying-glass",
    ),
```

In the template-tag module under `examples/bootstrap5/project/templatetags/`, replace `feature_for` so that child ViewSet pages (tasks) show their parent's card (teams):

```python
def feature_for(view):
    """The Feature card a view belongs to (matched by its ViewSet name, then its parents'), or None."""
    from project.features import FEATURES

    viewset = getattr(view, "cv_viewset", None)
    while viewset is not None:
        feature = next((f for f in FEATURES if f.viewset == viewset.name), None)
        if feature:
            return feature
        viewset = viewset.parent.viewset if viewset.parent else None
    return None
```

- [ ] **Step 7: Generate the migration**

Run (in `examples/bootstrap5`): `uv run manage.py makemigrations typeahead_example`
Expected: `typeahead/migrations/0001_initial.py` created with `Team` and `Task`.

- [ ] **Step 8: Run the example tests**

Run (in `examples/bootstrap5`): `uv run pytest -v`
Expected: all pass, including the existing datetimepicker tests. Fixes for likely failures:
- Crispy raises on the custom widget: check that the template renders without crispy-specific attributes. The widget only needs `widget.attrs`.
- `TaskCreateView` cannot find the parent: check that the URL kwarg is `team_pk` (`ParentViewSet(name="team")`).
- `test_filter_by_assignee` gets a 302: crud_views' filter session memory redirects only on a GET without parameters, so the request must carry the filter parameters as written.

- [ ] **Step 9: Run the root suite and lint**

Run (repo root): `uv run pytest && uv run ruff check . && uv run ruff format --check .`
Expected: all pass, no lint errors.

- [ ] **Step 10: Commit**

```bash
git add examples/bootstrap5/typeahead examples/bootstrap5/project
git commit -m "feat(example): typeahead example app with teams, tasks, modal and filter"
```

---

### Task 8: Docs and CI

**Files:**
- Modify: `README.md`, `CLAUDE.md`, `.github/workflows/*.yml` (the two pytest `--cov` lines)

**Interfaces:**
- Consumes: everything above. Produces documentation only.

- [ ] **Step 1: CI coverage**

In every workflow line `uv run --no-sources --extra dev pytest --cov=crud_views_widget_datetimepicker --cov-report=xml` (two occurrences), add `--cov=crud_views_widget_typeahead`:

```yaml
      - run: uv run --no-sources --extra dev pytest --cov=crud_views_widget_datetimepicker --cov=crud_views_widget_typeahead --cov-report=xml
```

Verify: `grep -rn "cov=crud_views_widget_typeahead" .github/workflows` shows 2 lines.

- [ ] **Step 2: README section**

Insert a `## crud_views_widget_typeahead` section before `## Example app` in `README.md`, with these subsections and content:

````markdown
## crud_views_widget_typeahead

A server-backed type-ahead single select for large, permission-sensitive model choice sets (thousands of
users), for forms and django-filter filters. Vanilla JS, no jQuery, CSP-safe, ARIA combobox.

### Install

```python
INSTALLED_APPS = [
    # ...
    "crud_views.apps.CrudViewsConfig",
    "crud_views_widget_typeahead.apps.CrudViewsWidgetTypeaheadConfig",
]

# urls.py — any prefix
urlpatterns += [path("_typeahead/", include("crud_views_widget_typeahead.urls"))]
```

Assets reach every page through `{% cv_js %}` / `{% cv_css %}`.

### Define a lookup

Put lookups in your app's `typeahead.py`; it is imported automatically at startup.

```python
from crud_views_widget_typeahead.lookups import register_user_lookup

@register_user_lookup("projects.members")
def members(request, project):
    if not request.user.has_perm("projects.view_project"):
        raise PermissionDenied
    return get_object_or_404(Project, pk=project).members.all()
```

For other models, subclass `TypeaheadLookup` (`search_fields`, `ordering`, `max_results=10`, `min_chars=2`,
`login_required=True`, `get_queryset(request, **params)`, `label(obj)`, `value(obj)`) and decorate it with
`@register_lookup("app.name")`. Every word of the search term must match one of `search_fields`
(`icontains`).

### Bind a form field / filter

```python
class TaskForm(forms.ModelForm):
    assignee = TypeaheadField(lookup="projects.members")

    def __init__(self, *args, request, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].bind(request, project=str(project.pk))


class TaskFilter(django_filters.FilterSet):
    assignee = TypeaheadFilter(lookup="projects.members")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["assignee"].bind(self.request, project=str(self.project.pk))
```

`bind()` sets the field's queryset (save-time validation) and signs `{lookup, params}` into the widget, so
the endpoint serves exactly that set, re-checking permission on every request. Params must be JSON values
(pass UUIDs as `str`). An unbound field raises `ImproperlyConfigured`. With crud_views' `CrispyModelForm`,
use `self.cv_view.request` (see the example app).

### Settings

| Key in `CRUD_VIEWS_TYPEAHEAD` | Default | |
|---|---|---|
| `EMIT` | `True` | `False` suppresses our `cv_js`/`cv_css` output (skins, django-pipeline) |
| `TEMPLATE` | `"crud_views_widget_typeahead/typeahead.html"` | widget template |
| `DEBOUNCE_MS` | `250` | input debounce |

django-pipeline: `from crud_views_widget_typeahead.assets import source_files` (Django-free).

### Endpoint

`GET <mount>/?t=<token>&q=<term>` → `{"results": [{"value", "label"}], "count": n}` (`count` before
truncation to `max_results`). Errors are JSON: 400 `bad_token`, 403 `login_required` / `forbidden`,
404 `not_found`; 405 for non-GET. Terms shorter than `min_chars` return an empty result without a query.

### Skins

A design-system package replaces the frontend and keeps the server core:

1. Set `CRUD_VIEWS_TYPEAHEAD["TEMPLATE"]` (or a widget's `template_name`). The template gets `widget.attrs`
   (visible input: id, ARIA, merged `aria-describedby`) and `widget.typeahead`: `url`, `label`, `value`,
   `hidden_name`, `hidden_id`, `listbox_id`, `hint_id`, `min_chars`, `debounce`, `submit_on_clear`, `i18n`
   (`hint`, `more`, `none`, `count`, `error`, `clear`, `listbox`; `{n}` is the number placeholder).
2. Register your own JS/CSS with `crud_views.lib.assets.register_assets` and set `EMIT = False`.
3. Keep the hidden input contract (it has the `name`, carries the pk, `autocomplete="off"`, empty when
   nothing is selected) and these behaviours: visible text = label of the stored pk except while typing
   (restore on blur and submit; clear only via a clear button or fully emptied text); arrow keys preview text
   only; Enter never submits while the list is open; escape/highlight labels yourself; show "N more" from
   `count`; ARIA combobox/listbox with a live result count; re-init on `cv:modal:loaded`.

Dynamically added content (e.g. new formset rows) needs `window.cvTypeahead.init(container)`.
````

- [ ] **Step 3: CLAUDE.md**

In `CLAUDE.md`:
- Change "Currently ships one app: `crud_views_widget_datetimepicker` (…)" to list both apps and add "`crud_views_widget_typeahead` (server-backed type-ahead select: lookup registry, signed tokens, one JSON endpoint, vanilla JS)".
- Replace the test-count comment `# full suite (62 tests, ~0.1s)` with the actual count from `uv run pytest -q | tail -1`.
- Add a `### crud_views_widget_typeahead` architecture subsection under `## Architecture`:

```markdown
### crud_views_widget_typeahead

- **`lookups.py`** — `TypeaheadLookup` (allowed set + permission in `get_queryset(request, **params)`,
  multi-word `icontains` search, labels) and a name registry; `register_user_lookup` wraps a function.
  `apps.py::ready()` autodiscovers every app's `typeahead.py`.
- **`tokens.py`** — `signing.dumps({"l": name, "p": params})`, salt `crud_views.typeahead`, **no expiry**:
  permission is re-checked per request, so the browser can neither change scope nor needs fresh tokens.
- **`views.py`** — the single endpoint; JSON errors only (never a login redirect — `fetch` must get JSON).
- **`fields.py` / `filters.py`** — `bind(request, **params)` is the single source of truth: it sets the
  queryset validation uses and the token the endpoint uses. `TypeaheadBinding` is frozen plain data
  because `Widget.__deepcopy__` is shallow.
- **`widgets.py`** — visible input has no `name`; hidden input carries the pk; `aria-describedby` is merged
  with Django's ids at render time (never set on `widget.attrs`, or Django drops its own).
- **`static/.../typeahead.js`** — vanilla, no `innerHTML`; the skin contract is documented in the README.
  No CDN/vendor machinery: there is no third-party plugin.
```

- [ ] **Step 4: Verify and commit**

Run: `uv run pytest -q && (cd examples/bootstrap5 && uv run pytest -q) && uv run ruff check . && uv run ruff format --check .`
Expected: all green.

```bash
git add README.md CLAUDE.md .github/workflows
git commit -m "docs(typeahead): README section, CLAUDE.md architecture, CI coverage"
```

---

### Task 9: Browser verification of the frontend contract

**Files:** none, unless a defect is found. Fix defects in `typeahead.js`/`typeahead.css` and commit them as `fix(typeahead): …`.

**Interfaces:**
- Consumes: the running example app (`cd examples/bootstrap5 && task run`, then log in as admin/admin at http://127.0.0.1:8000).

- [ ] **Step 1: Start the app**

Run in the background: `cd examples/bootstrap5 && task run`. Open Teams → "Platform" → tasks → "Create".

- [ ] **Step 2: Walk the checklist with a browser tool (Playwright or Chrome MCP)**

Record pass/fail for each item:

1. Typing 1 character opens nothing; typing "an" opens the list after about 250 ms, with matches wrapped in `<mark>`.
2. Typing fast ("anna becker") sends at most one request that renders; the network tab shows the earlier ones aborted (cancelled), and no stale list flashes.
3. A term with more than 10 matches shows a "N more results – keep typing" row, which is not selectable.
4. A term with no matches shows "No results".
5. ↓/↑ move the highlight and change only the visible text; the hidden input's value is unchanged (check with `document.getElementById("id_assignee_value").value`).
6. Enter with the list open selects the active option and does **not** submit the form; Enter with the list closed submits.
7. Escape closes the list and restores the committed label.
8. Typing a partial term and then clicking elsewhere restores the committed label; the pk is unchanged.
9. Clicking away within the debounce window (type, then click away immediately) does not reopen the list.
10. Fully emptying the text and blurring clears the pk; the clear button (×) clears the pk and refocuses the input.
11. Saving with a selected member works, and the update page shows "Name (username)".
12. Task list filter: selecting a member filters; the × button clears the filter and submits immediately (`submit_on_clear`); the URL stays `?assignee=<pk>`.
13. "Quick assign" modal: the typeahead works inside the modal, and saving closes the modal.
14. DOM check: `role="combobox"`, `aria-expanded` toggles, `aria-activedescendant` follows the highlight, and the live region text updates with the result count.
15. Logged out in another tab, then typing: the list closes and "Search failed" is announced; the console shows one `cv-typeahead:` warning and no uncaught errors.
16. Console: no errors on page load; there are no inline-style or CSP warnings.

- [ ] **Step 3: Fix any defect test-first, if possible**

For a server-side defect, add a failing pytest first. For a pure JS defect, fix it, re-run the affected checklist items, and commit:

```bash
git add src/crud_views_widget_typeahead/static
git commit -m "fix(typeahead): <what the checklist found>"
```

- [ ] **Step 4: Report**

Report the 16 results (pass/fail plus notes) in the hand-off message.
