# Example App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local-only example Django project under `examples/bootstrap5/` that showcases the `crud_views_widget_datetimepicker` extension (forms, modals, list filters, per-field config) and doubles as a manual test harness for future `crud_views_widget_*` apps.

**Architecture:** A trimmed copy of `../django-crud-views/examples/bootstrap5`: a `project/` package (settings, URLs, feature-card registry, base templates, seed command) plus one feature app per extension (`datetimepicker/`). It runs in the repo's own uv environment, so it always exercises the editable `src/` code. The example's tests run separately from the root suite (own `pytest.ini`) and get their own CI step.

**Tech Stack:** Django, django-crud-views 0.29 (ViewSets, `crud_views_object_detail`, modals, asset registry), django-tables2, django-filter, crispy-forms/bootstrap5, pytest-django, Taskfile.

**Spec:** `docs/superpowers/specs/2026-10-15-example-app-design.md`

## Global Constraints

- **Prerequisite:** the datetimepicker locale/format fix (spec "Prerequisite") must be merged before Task 2's locale round-trip test can pass. If it is not merged yet, stop at Task 2 Step 1's locale test and report — do not weaken the test or work around it in the example.
- Location: everything example-specific lives under `examples/bootstrap5/`. Run all example commands from that directory.
- Run commands with `uv run` (repo root `pyproject.toml` env). No new dependencies; no `[tool.uv.sources]`.
- Asset delivery: package defaults (`SOURCE="cdn"`). `settings.py` sets only `CRUD_VIEWS_DATETIMEPICKER = {"DEFAULTS": {"dayOfWeekStart": 1}}`.
- Languages: `LANGUAGES = [("en", ...), ("de", ...)]` with `LocaleMiddleware`; `LANGUAGE_CODE = "en-us"`.
- Seeded login: `admin` / `admin` (superuser). No other demo users.
- Not carried over from upstream: `settings_demo.py`, `urls_demo.py`, `boot.py`, `ratelimit.py`, `render.yaml`, snippet panels, docs-sync / doc-link tests, `DocRef`.
- Ruff: line-length 120, double quotes; `uv run ruff check . && uv run ruff format --check .` from the repo root must pass (covers `examples/`, including migrations).
- Commits: conventional prefixes (`feat:`, `test:`, `docs:`, `ci:`, `chore:`). Never commit `db.sqlite3`. Do not touch the two staged files under `docs/superpowers/prompts/`; commit with explicit paths (`git commit -- <paths>`).

## Deviations from the spec (decided while planning)

- **Quick edit modal is a `CustomFormView`, not a second `UpdateView`.** In django-crud-views 0.29 `UpdateView.cv_modal_supported` is `False` (a system check rejects `cv_modal=True` on it); only custom-form, detail and delete views support modals. `EventQuickEditView` is a `CustomFormViewPermissionRequired` that edits the same instance with the same `EventForm`.
- **`crud_views_object_detail` is installed** (spec listed it as dropped): the Event detail view and the table's detail link column need it. It ships inside django-crud-views, so it adds no dependency.
- **`Feature` gains a `viewset` field.** Both datetimepicker cards live in one Django app, so the about panel / nav highlighting match a page to its card by the view's ViewSet name, not by app.

## Review Focus

1. **English locale round-trip** — under `en`, a date the picker writes must be accepted by the form and filter (the bug the prerequisite fixes). Pinned in Task 2 (`test_rendered_value_matches_picker_format_and_round_trips` for `en` and `de`).
2. **Modal request for quick edit** — the modal partial (`X-CV-Modal: true`) must contain the picker config attribute, and a valid modal POST must answer `204` + `X-CV-Redirect`, not a 302. Pinned in Task 2.
3. **Invalid filter input** — `?day_from=garbage` must render the list with a filter error, not a 500. Pinned in Task 2 (`test_garbage_filter_value_does_not_crash`).
4. **Two cards, one app** — each card's about panel must show *its* text on its pages (not the first card of the app). Pinned in Task 3 (`test_about_panel_matches_card`).
5. **Seeding twice** — `manage.py seed` must not duplicate events/variants or fail on an existing admin. Pinned in Tasks 1–3 (`test_seed_is_idempotent` per app).

---

## File Structure

```
examples/bootstrap5/
  manage.py                                   # Task 1
  pytest.ini                                  # Task 1
  taskfile.yaml                               # Task 1
  project/
    __init__.py                               # Task 1
    settings.py                               # Task 1 (Task 2 appends the app to INSTALLED_APPS)
    urls.py                                   # Task 1 (Task 2 appends an include)
    wsgi.py                                   # Task 1
    views.py                                  # Task 1: BreadcrumbMixin, HomeView
    features.py                               # Task 1: registry; Tasks 2/3 append entries
    context_processors.py                     # Task 1: versions for the footer
    seeding.py                                # Task 1: ensure_admin()
    management/__init__.py                    # Task 1
    management/commands/__init__.py           # Task 1
    management/commands/seed.py               # Task 1
    templatetags/__init__.py                  # Task 1
    templatetags/example_tags.py              # Task 1: get_feature_groups, example_about, feature_for
    templates/project/base.html               # Task 1
    templates/project/crud_views.html         # Task 1
    templates/project/nav.html                # Task 1
    templates/project/home.html               # Task 1
    templates/project/footer.html             # Task 1
    templates/project/example_about.html      # Task 1
    templates/registration/login.html         # Task 1
    tests.py                                  # Task 1
  datetimepicker/
    __init__.py apps.py                       # Task 2
    models.py                                 # Task 2: Event; Task 3: PickerVariant
    forms.py                                  # Task 2: EventForm, EventFilter; Task 3: PickerVariantForm
    views.py                                  # Task 2: cv_event views; Task 3: cv_variant views
    urls.py                                   # Task 2 (Task 3 extends)
    seed.py                                   # Task 2 (Task 3 extends)
    migrations/                               # Task 2 (0001), Task 3 (0002)
    tests.py                                  # Task 2 (Task 3 extends)
pyproject.toml                                # Task 1: [tool.pytest.ini_options] testpaths
.gitignore                                    # Task 1
README.md, CLAUDE.md                          # Task 4
.github/workflows/tests.yml                   # Task 4
```

---

### Task 1: Example project skeleton

**Files:**
- Create: everything under `examples/bootstrap5/` listed for Task 1 above
- Modify: `pyproject.toml` (add `[tool.pytest.ini_options]`), `.gitignore`
- Test: `examples/bootstrap5/project/tests.py`

**Interfaces:**
- Produces:
  - `project.features.FeatureGroup(key: str, title: str, icon: str)`
  - `project.features.Feature(app: str, viewset: str, group: str, title: str, description: str, about: str, look_at: str, url_name: str, icon: str)`
  - `project.features.GROUPS: list[FeatureGroup]` (one group, key `"widgets"`), `FEATURES: list[Feature]` (empty in Task 1), `feature_groups() -> list[tuple[FeatureGroup, list[Feature]]]`
  - `project.templatetags.example_tags.feature_for(view) -> Feature | None` — matches `view.cv_viewset.name` against `Feature.viewset`
  - `project.views.BreadcrumbMixin` — every example view inherits it first
  - `project.seeding.ensure_admin() -> User`
  - `manage.py seed` — calls `ensure_admin()`, then `import_module(f"{app}.seed").seed()` once per distinct `Feature.app`
  - `CRUD_VIEWS_EXTENDS = "project/crud_views.html"`

- [ ] **Step 1: Root repo config**

Add to `pyproject.toml` (after `[tool.ruff]` sections, before `[tool.bumpversion]`):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

Append to `.gitignore`:

```
examples/**/db.sqlite3
```

Run from repo root: `uv run pytest -q`
Expected: `28 passed` (root suite unchanged).

- [ ] **Step 2: Write the failing project tests**

`examples/bootstrap5/project/tests.py`:

```python
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from project.features import FEATURES


class ProjectTest(TestCase):
    def test_system_checks_pass(self):
        call_command("check", fail_level="WARNING")

    def test_home_renders_every_feature_card(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        for feature in FEATURES:
            self.assertContains(resp, feature.title)
            self.assertContains(resp, reverse(feature.url_name))

    def test_login_page_renders(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "admin/admin")

    def test_feature_pages_require_login(self):
        for feature in FEATURES:
            resp = self.client.get(reverse(feature.url_name))
            self.assertEqual(resp.status_code, 302, feature.url_name)

    def test_feature_pages_render_for_admin(self):
        admin = get_user_model().objects.create_superuser(username="t-admin", password="pw")
        self.client.force_login(admin)
        for feature in FEATURES:
            resp = self.client.get(reverse(feature.url_name))
            self.assertEqual(resp.status_code, 200, feature.url_name)

    def test_seed_is_idempotent(self):
        call_command("seed", verbosity=0)
        call_command("seed", verbosity=0)
        admin = get_user_model().objects.get(username="admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("admin"))
```

`examples/bootstrap5/pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = project.settings
pythonpath = .
addopts = --strict-markers
python_files = test_*.py *_test.py tests.py
```

- [ ] **Step 3: Run to verify it fails**

Run: `cd examples/bootstrap5 && uv run pytest -q`
Expected: error — `No module named 'project'` / settings import failure.

- [ ] **Step 4: Project package — settings, URLs, wsgi, manage.py**

`examples/bootstrap5/manage.py`:

```python
#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
```

`examples/bootstrap5/project/__init__.py`: empty.

`examples/bootstrap5/project/wsgi.py`:

```python
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
application = get_wsgi_application()
```

`examples/bootstrap5/project/settings.py`:

```python
"""
Django settings for the django-crud-views-extensions example project.

Local use only. One example app per crud_views_widget_* extension — see the home page.
"""

from pathlib import Path

from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-example-project-do-not-use-in-production"
DEBUG = True  # local example only
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tables2",
    "django_filters",
    "crud_views_object_detail",
    "crud_views.apps.CrudViewsConfig",
    "crud_views_widget_datetimepicker.apps.CrudViewsWidgetDatetimepickerConfig",
    "project",
    # example feature apps (one per crud_views_widget_* extension)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "crud_views.lib.context_processor.crud_views_context",
                "project.context_processors.project_info",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en", _("English")),
    ("de", _("German")),
]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# django-crud-views
CRUD_VIEWS_EXTENDS = "project/crud_views.html"
CRUD_VIEWS_BREADCRUMB_PREFIX = [{"title": _("Home"), "url_name": "home"}]

# crispy forms
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# django-tables2
DJANGO_TABLES2_TEMPLATE = "crud_views/table/bootstrap5.html"

# crud_views_object_detail
CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "split-card"
CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "default"
CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY = "fontawesome"
CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE = "solid"

# crud_views_widget_datetimepicker — CDN delivery (package default); DEFAULTS apply to every picker
CRUD_VIEWS_DATETIMEPICKER = {
    "DEFAULTS": {"dayOfWeekStart": 1},  # weeks start on Monday
}
```

`examples/bootstrap5/project/urls.py`:

```python
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from project.views import HomeView


class CrispyAuthenticationForm(AuthenticationForm):
    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout("username", "password", FormActions(Submit("login", _("Log In"))))
        return helper


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("login/", LoginView.as_view(form_class=CrispyAuthenticationForm), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    # example feature apps append their include() here
]
```

- [ ] **Step 5: Feature registry, views, context processor, seeding, seed command**

`examples/bootstrap5/project/features.py`:

```python
"""Registry of example feature cards. Each feature task appends exactly one entry to FEATURES."""

from dataclasses import dataclass

from django.utils.translation import pgettext_lazy

#: GitHub page linked from the footer and the home page
REPO_URL = "https://github.com/jacob-consulting/django-crud-views-extensions"


@dataclass(frozen=True)
class FeatureGroup:
    key: str  # referenced by Feature.group
    title: str  # navbar dropdown and home page heading
    icon: str  # font-awesome classes


#: navbar dropdowns and home page sections, in display order
GROUPS: list[FeatureGroup] = [
    FeatureGroup(key="widgets", title=pgettext_lazy("feature group", "Widgets"), icon="fa-solid fa-puzzle-piece"),
]


@dataclass(frozen=True)
class Feature:
    app: str  # python package of the example app, e.g. "datetimepicker"; seed.py lives there
    viewset: str  # crud_views ViewSet name whose pages belong to this card, e.g. "event"
    group: str  # FeatureGroup.key
    title: str  # card / nav title (English, names a package feature)
    description: str  # one-liner on the home page card
    about: str  # 2-4 sentence teaching paragraph shown on every page of the card
    look_at: str  # one-sentence code pointer shown under the about paragraph
    url_name: str  # landing page URL name, e.g. "event-list"
    icon: str  # font-awesome classes


FEATURES: list[Feature] = [
    # example feature apps append their entries here
]


def feature_groups() -> list[tuple[FeatureGroup, list[Feature]]]:
    """FEATURES bucketed by GROUPS, in GROUPS order. Raises ValueError for an unknown group key."""
    buckets: dict[str, list[Feature]] = {group.key: [] for group in GROUPS}
    for feature in FEATURES:
        if feature.group not in buckets:
            raise ValueError(f"Feature {feature.title!r} names unknown group {feature.group!r}")
        buckets[feature.group].append(feature)
    return [(group, buckets[group.key]) for group in GROUPS]


# validate group keys at import time (the URLconf imports this via project.views)
feature_groups()
```

`examples/bootstrap5/project/views.py`:

```python
from django.views import generic

from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from project.features import feature_groups


class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    """Project-wide breadcrumb adoption point: every example view inherits this first."""


class HomeView(generic.TemplateView):
    template_name = "project/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature_groups"] = feature_groups()
        return context
```

`examples/bootstrap5/project/context_processors.py`:

```python
from importlib.metadata import version

from project.features import REPO_URL


def project_info(request):  # Django context-processor signature
    return {
        "crud_views_version": version("django-crud-views"),
        "extensions_version": version("django-crud-views-extensions"),
        "repo_url": REPO_URL,
    }
```

`examples/bootstrap5/project/seeding.py`:

```python
from django.contrib.auth import get_user_model

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"  # local example only — shown on the home and login pages


def ensure_admin():
    """Create the admin superuser, or reset its password. Idempotent."""
    user, _ = get_user_model().objects.get_or_create(
        username=ADMIN_USERNAME, defaults={"is_superuser": True, "is_staff": True}
    )
    user.is_superuser = user.is_staff = True
    user.set_password(ADMIN_PASSWORD)
    user.save()
    return user
```

`examples/bootstrap5/project/management/__init__.py` and `.../management/commands/__init__.py`: empty.

`examples/bootstrap5/project/management/commands/seed.py`:

```python
from importlib import import_module

from django.core.management.base import BaseCommand

from project.features import FEATURES
from project.seeding import ADMIN_PASSWORD, ADMIN_USERNAME, ensure_admin


class Command(BaseCommand):
    help = "Seed the admin user and demo data for all example apps. Idempotent."

    def handle(self, *args, **options):
        ensure_admin()
        self.stdout.write(f"user: {ADMIN_USERNAME}/{ADMIN_PASSWORD}")
        # several cards may share one app: seed each app once
        for app in dict.fromkeys(feature.app for feature in FEATURES):
            import_module(f"{app}.seed").seed()
            self.stdout.write(f"seeded {app}")
        self.stdout.write(self.style.SUCCESS("Done."))
```

- [ ] **Step 6: Template tags**

`examples/bootstrap5/project/templatetags/__init__.py`: empty.

`examples/bootstrap5/project/templatetags/example_tags.py`:

```python
from django import template

register = template.Library()


def feature_for(view):
    """The Feature card a view belongs to (matched by its ViewSet name), or None."""
    from project.features import FEATURES

    viewset = getattr(view, "cv_viewset", None)
    name = getattr(viewset, "name", None)
    return next((f for f in FEATURES if f.viewset == name), None) if name else None


@register.simple_tag(takes_context=True)
def get_feature_groups(context):
    """Navbar data: the feature groups plus the current page's card (or None)."""
    from project.features import feature_groups

    feature = feature_for(context.get("view"))
    return {
        "groups": feature_groups(),
        "active_group": feature.group if feature else None,
        "active_title": feature.title if feature else None,
    }


@register.inclusion_tag("project/example_about.html", takes_context=True)
def example_about(context):
    return {"feature": feature_for(context.get("view"))}
```

- [ ] **Step 7: Templates**

`examples/bootstrap5/project/templates/project/base.html`:

```django
{% load static %}
{% load django_bootstrap5 %}
{% load crud_views %}
{% load i18n %}

<!DOCTYPE html>
{% get_current_language as LANGUAGE_CODE %}
<html lang="{{ LANGUAGE_CODE }}">
<head>
    <meta charset="utf-8"/>
    <meta http-equiv="x-ua-compatible" content="ie=edge"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>{% block title %}{% translate "django-crud-views-extensions examples" %}{% endblock title %}</title>

    <!-- Bootstrap CSS and JS -->
    {% bootstrap_css %}
    {% bootstrap_javascript %}

    <!-- Font-Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css"
          integrity="sha512-Evv84Mr4kqVGRNSgIGL/F/aIDqQb7xQ2vcrdIwxfjThSH8CSR7PBEakCr51Ck+w+/U6swU2Im1vVX0SVk9ABhg=="
          crossorigin="anonymous" referrerpolicy="no-referrer"/>

    <!-- jquery: required by crud_views and by the datetimepicker plugin; must precede cv_js -->
    <script
            src="https://code.jquery.com/jquery-3.7.1.js"
            integrity="sha256-eKhayi8LEQwp4NKxN+CfCh+3qOVUtJn3QNZ0TciWLP4="
            crossorigin="anonymous"></script>

    <!-- crud_views: page-global assets, including every registered extension's (datetimepicker) -->
    {% cv_config %}
    {% cv_css %}
    {% cv_js %}

</head>

<body>

{% block nav %}
    {% include "project/nav.html" %}
{% endblock nav %}

<main class="container">

    {% bootstrap_messages %}

    {% block content %}
    {% endblock content %}

</main>

{% block footer %}
    {% include "project/footer.html" %}
{% endblock footer %}

</body>
</html>
```

`examples/bootstrap5/project/templates/project/crud_views.html`:

```django
{% extends "project/base.html" %}

{% load crud_views %}
{% load example_tags %}

{% block content %}

    {% example_about %}

    {% block cv_breadcrumb %}
        {% cv_breadcrumb %}
    {% endblock cv_breadcrumb %}

    <div class="card">
        <div class="card-header">
            <h5 class="d-flex justify-content-between align-items-center">
                <div>
                    <h3>
                        {% block cv_header_icon %}
                            {% cv_header_icon %}
                        {% endblock cv_header_icon %}
                        {% block cv_header %}
                            {% cv_header %}
                        {% endblock cv_header %}
                    </h3>
                </div>
                {% block cv_context %}
                    {% cv_context_actions object %}
                {% endblock cv_context %}
            </h5>
            {% block cv_paragraph %}
                {% cv_paragraph %}
            {% endblock cv_paragraph %}
        </div>
        <div class="card-body">
            {% block cv_filter %}
            {% endblock cv_filter %}

            {% block cv_content %}
            {% endblock cv_content %}
        </div>
    </div>

{% endblock content %}
```

`examples/bootstrap5/project/templates/project/nav.html`:

```django
{% load i18n crud_views %}
{% load example_tags %}
<nav class="navbar navbar-expand-xl navbar-dark bg-dark mb-4">
    <div class="container-fluid">
        <a class="navbar-brand" href="{% url "home" %}">django-crud-views-extensions</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarCollapse"
                aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarCollapse">
            <ul class="navbar-nav me-auto mb-2 mb-xl-0">
                {% get_feature_groups as nav_groups %}
                {% for group, features in nav_groups.groups %}
                    {% if features %}
                        <li class="nav-item dropdown">
                            <button type="button" id="nav-group-{{ group.key }}" class="nav-link dropdown-toggle{% if group.key == nav_groups.active_group %} active{% endif %}" data-bs-toggle="dropdown" aria-expanded="false"{% if group.key == nav_groups.active_group %} aria-current="true"{% endif %}>
                                <i class="{{ group.icon }}" aria-hidden="true"></i> {{ group.title }}
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="nav-group-{{ group.key }}">
                                {% for feature in features %}
                                    <li>
                                        <a class="dropdown-item{% if feature.title == nav_groups.active_title %} active{% endif %}"{% if feature.title == nav_groups.active_title %} aria-current="page"{% endif %} href="{% url feature.url_name %}">
                                            <i class="{{ feature.icon }} fa-fw" aria-hidden="true"></i> {{ feature.title }}
                                        </a>
                                    </li>
                                {% endfor %}
                            </ul>
                        </li>
                    {% endif %}
                {% endfor %}
            </ul>
            <div class="me-3">{% cv_language_selector %}</div>
            {% if request.user.is_authenticated %}
                <span class="navbar-text me-3">{{ request.user.username }}</span>
                <form class="d-flex" action="{% url "logout" %}" method="post">
                    {% csrf_token %}
                    <button class="btn btn-outline-success" type="submit">{% translate "Log Out" %}</button>
                </form>
            {% else %}
                <a class="btn btn-outline-success" href="{% url "login" %}">{% translate "Log In" %}</a>
            {% endif %}
        </div>
    </div>
</nav>
```

`examples/bootstrap5/project/templates/project/home.html`:

```django
{% extends "project/base.html" %}

{% load i18n %}

{% block content %}

    <div class="bg-body-tertiary p-4 rounded mb-4">
        <h1>{% translate "django-crud-views-extensions examples" %}</h1>
        <p class="lead">
            {% blocktranslate trimmed %}One example per use case of the crud_views_widget_* extensions.
            Every page explains what it shows and where the code is.{% endblocktranslate %}
        </p>
        <a class="btn btn-primary" href="{{ repo_url }}#readme">README &raquo;</a>
    </div>

    {% for group, features in feature_groups %}
        {% if features %}
            <h2 id="group-{{ group.key }}" class="h4 mt-4 mb-3"><i class="{{ group.icon }}" aria-hidden="true"></i> {{ group.title }}</h2>
            <div class="row row-cols-1 row-cols-md-3 g-3">
                {% for feature in features %}
                    <div class="col">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title"><i class="{{ feature.icon }}" aria-hidden="true"></i> {{ feature.title }}</h5>
                                <p class="card-text">{{ feature.description }}</p>
                            </div>
                            <div class="card-footer">
                                <a class="btn btn-sm btn-outline-primary" href="{% url feature.url_name %}">{% translate "Open" %}</a>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endfor %}

    <div class="alert alert-info mt-4">
        {% blocktranslate trimmed %}Log in as <code>admin/admin</code> (created by <code>manage.py seed</code>).{% endblocktranslate %}
    </div>

{% endblock content %}
```

`examples/bootstrap5/project/templates/project/footer.html`:

```django
{% load i18n %}
<footer class="container border-top mt-5 py-3 text-muted small" id="site-footer">
    <span>django-crud-views-extensions {{ extensions_version }}</span>
    &middot;
    <span>django-crud-views {{ crud_views_version }}</span>
    &middot;
    <a href="{{ repo_url }}" class="link-secondary" target="_blank" rel="noopener">
        <i class="fa-brands fa-github" aria-hidden="true"></i> GitHub</a>
</footer>
```

`examples/bootstrap5/project/templates/project/example_about.html`:

```django
{% load i18n %}
{% if feature %}
    <div class="alert alert-light border d-flex gap-3 mb-4" id="example-about">
        <i class="fa-solid fa-circle-info fs-4 text-secondary mt-1" aria-hidden="true"></i>
        <div>
            <h6 class="mb-1">{% blocktranslate with title=feature.title %}About this example — {{ title }}{% endblocktranslate %}</h6>
            <p class="mb-2">{{ feature.about }}</p>
            <p class="mb-0 small text-muted" id="example-look-at">
                <i class="fa-solid fa-code" aria-hidden="true"></i>
                {% translate "Look at" %}: <code>examples/bootstrap5/{{ feature.app }}/</code> — {{ feature.look_at }}
            </p>
        </div>
    </div>
{% endif %}
```

`examples/bootstrap5/project/templates/registration/login.html`:

```django
{% extends "project/base.html" %}
{% load crispy_forms_tags %}
{% load i18n %}

{% block title %}{% translate "Log in" %} — {% translate "django-crud-views-extensions examples" %}{% endblock title %}

{% block content %}
    <div class="row justify-content-center">
        <div class="col-md-5">
            <div class="card">
                <div class="card-header"><h4>{% translate "Log in" %}</h4></div>
                <div class="card-body">
                    {% crispy form %}
                    <div class="alert alert-info mb-0 mt-3">
                        Demo user: <code>admin/admin</code> — run <code>manage.py seed</code> first.
                    </div>
                </div>
            </div>
        </div>
    </div>
{% endblock content %}
```

- [ ] **Step 8: Taskfile**

`examples/bootstrap5/taskfile.yaml`:

```yaml
version: '3'

tasks:

  run:
    desc: Migrate, seed and start the example server
    cmds:
      - uv run manage.py migrate
      - uv run manage.py seed
      - uv run manage.py runserver 0.0.0.0:8000

  seed:
    desc: Migrate and (re)seed demo data — idempotent
    cmds:
      - uv run manage.py migrate
      - uv run manage.py seed

  test:
    cmds:
      - uv run pytest

  migrations:
    cmds:
      - uv run manage.py makemigrations

  shell:
    cmds:
      - uv run manage.py shell
```

- [ ] **Step 9: Run tests to verify they pass**

Run: `cd examples/bootstrap5 && uv run pytest -q`
Expected: `6 passed`. (The FEATURES loops are empty for now; they gain teeth in Tasks 2–3.)

Also run: `cd examples/bootstrap5 && uv run manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 10: Lint and commit**

Run from repo root: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`
Expected: all checks pass, `28 passed`.

```bash
git add pyproject.toml .gitignore examples/bootstrap5
git commit -m "feat(example): example project skeleton" -- pyproject.toml .gitignore examples/bootstrap5
```

---

### Task 2: `datetimepicker` app — Event (forms, modal, filters)

**Files:**
- Create: `examples/bootstrap5/datetimepicker/{__init__,apps,models,forms,views,urls,seed,tests}.py`, `migrations/__init__.py`, `migrations/0001_initial.py` (generated)
- Modify: `examples/bootstrap5/project/settings.py` (INSTALLED_APPS), `project/urls.py`, `project/features.py`

**Interfaces:**
- Consumes: `BreadcrumbMixin`, `Feature`, `FEATURES`, `feature_for` from Task 1; `DateTimePickerInput`, `DatePickerInput`, `TimePickerInput` from `crud_views_widget_datetimepicker.widgets`.
- Produces:
  - `datetimepicker.models.Event(title, day, doors_open, starts_at, ends_at)`
  - `datetimepicker.forms.EventForm`, `EventFilter`
  - `datetimepicker.views.cv_event` (ViewSet name `"event"`); URL names `event-list`, `event-detail`, `event-create`, `event-update`, `event-quick_edit`, `event-delete` (crud_views names URLs `<viewset>-<cv_key>`)
  - `datetimepicker.seed.seed()`
  - `datetimepicker/tests.py` helper `php_date(value, fmt) -> str`

- [ ] **Step 1: Write the failing tests**

`examples/bootstrap5/datetimepicker/__init__.py` and `migrations/__init__.py`: empty.

`examples/bootstrap5/datetimepicker/tests.py`:

```python
import datetime
import json
import re

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from datetimepicker.models import Event

#: the xdsoft (PHP-style) format tokens the widgets use, mapped to strftime
_PHP_TOKENS = {"d": "%d", "m": "%m", "Y": "%Y", "H": "%H", "i": "%M", "s": "%S"}


def php_date(value, fmt: str) -> str:
    """Format a date/time the way the xdsoft picker would for a PHP-style format string."""
    return value.strftime("".join(_PHP_TOKENS.get(ch, ch) for ch in fmt))


def picker_input(html: str, name: str) -> dict:
    """Value and parsed xdsoft config of the rendered <input name=...>."""
    tag = re.search(rf'<input[^>]*name="{name}"[^>]*>', html).group(0)
    config = re.search(r'xdsoft-datetime-config="([^"]*)"', tag).group(1)
    value = re.search(r'value="([^"]*)"', tag)
    return {
        "config": json.loads(config.replace("&quot;", '"')),
        "value": value.group(1) if value else "",
    }


class EventTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="t-admin", password="pw")
        tz = timezone.get_current_timezone()
        cls.event = Event.objects.create(
            title="Autumn meetup",
            day=datetime.date(2026, 10, 15),
            doors_open=datetime.time(18, 30),
            starts_at=datetime.datetime(2026, 10, 15, 19, 0, tzinfo=tz),
            ends_at=datetime.datetime(2026, 10, 15, 22, 0, tzinfo=tz),
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def payload(self, **overrides):
        data = {
            "title": "Winter meetup",
            "day": "",
            "doors_open": "",
            "starts_at": "",
            "ends_at": "",
        }
        data.update(overrides)
        return data


class AssetsTest(EventTestCase):
    def test_cv_js_delivers_plugin_and_init(self):
        resp = self.client.get(reverse("event-list"))
        self.assertContains(resp, "cdn.jsdelivr.net/npm/jquery-datetimepicker@")
        self.assertContains(resp, "crud_views_widget_datetimepicker/init.js")


class EventFormTest(EventTestCase):
    def test_create_page_renders_pickers(self):
        resp = self.client.get(reverse("event-create"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertFalse(picker_input(html, "day")["config"]["timepicker"])
        self.assertFalse(picker_input(html, "doors_open")["config"]["datepicker"])
        self.assertIn("format", picker_input(html, "starts_at")["config"])

    def test_settings_defaults_reach_the_widget(self):
        html = self.client.get(reverse("event-create")).content.decode()
        self.assertEqual(picker_input(html, "day")["config"]["dayOfWeekStart"], 1)

    def test_rendered_value_matches_picker_format_and_round_trips(self):
        """Regression check for the locale/format prerequisite: under every language the value Django renders is
        what the picker would write, and posting it back unchanged saves the same values."""
        url = reverse("event-update", kwargs={"pk": self.event.pk})
        local_starts = timezone.localtime(self.event.starts_at)
        for lang in ("en", "de"):
            with self.subTest(lang=lang):
                html = self.client.get(url, HTTP_ACCEPT_LANGUAGE=lang).content.decode()
                day = picker_input(html, "day")
                doors = picker_input(html, "doors_open")
                starts = picker_input(html, "starts_at")
                ends = picker_input(html, "ends_at")
                self.assertEqual(day["value"], php_date(self.event.day, day["config"]["format"]))
                self.assertEqual(doors["value"], php_date(self.event.doors_open, doors["config"]["format"]))
                self.assertEqual(starts["value"], php_date(local_starts, starts["config"]["format"]))
                data = self.payload(
                    title="Autumn meetup",
                    day=day["value"],
                    doors_open=doors["value"],
                    starts_at=starts["value"],
                    ends_at=ends["value"],
                )
                resp = self.client.post(url, data, HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(resp.status_code, 302, resp.content.decode()[:2000])
                self.event.refresh_from_db()
                self.assertEqual(self.event.day, datetime.date(2026, 10, 15))
                self.assertEqual(self.event.doors_open, datetime.time(18, 30))
                self.assertEqual(timezone.localtime(self.event.starts_at), local_starts)

    def test_end_before_start_rerenders_with_error_and_values(self):
        url = reverse("event-update", kwargs={"pk": self.event.pk})
        html = self.client.get(url, HTTP_ACCEPT_LANGUAGE="de").content.decode()
        starts = picker_input(html, "starts_at")["value"]
        data = self.payload(
            title="Autumn meetup",
            day=picker_input(html, "day")["value"],
            doors_open=picker_input(html, "doors_open")["value"],
            starts_at=starts,
            ends_at=starts,  # equal to start: invalid
        )
        resp = self.client.post(url, data, HTTP_ACCEPT_LANGUAGE="de")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "must be after the start")
        rerendered = resp.content.decode()
        self.assertEqual(picker_input(rerendered, "starts_at")["value"], starts)
        self.assertIn("xdsoft-datetime-config", rerendered)


class EventModalTest(EventTestCase):
    def test_list_offers_quick_edit(self):
        resp = self.client.get(reverse("event-list"))
        self.assertContains(resp, reverse("event-quick_edit", kwargs={"pk": self.event.pk}))

    def test_modal_partial_contains_pickers(self):
        url = reverse("event-quick_edit", kwargs={"pk": self.event.pk})
        resp = self.client.get(url, HTTP_X_CV_MODAL="true")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertNotIn("<html", html)  # partial, not a full page
        self.assertIn("format", picker_input(html, "starts_at")["config"])

    def test_valid_modal_post_answers_204_with_redirect(self):
        url = reverse("event-quick_edit", kwargs={"pk": self.event.pk})
        html = self.client.get(url, HTTP_X_CV_MODAL="true", HTTP_ACCEPT_LANGUAGE="de").content.decode()
        data = self.payload(
            title="Renamed in modal",
            day=picker_input(html, "day")["value"],
            doors_open=picker_input(html, "doors_open")["value"],
            starts_at=picker_input(html, "starts_at")["value"],
            ends_at=picker_input(html, "ends_at")["value"],
        )
        resp = self.client.post(url, data, HTTP_X_CV_MODAL="true", HTTP_ACCEPT_LANGUAGE="de")
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(resp["X-CV-Redirect"])
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Renamed in modal")


class EventFilterTest(EventTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        tz = timezone.get_current_timezone()
        Event.objects.create(
            title="Spring meetup",
            day=datetime.date(2026, 3, 1),
            doors_open=datetime.time(18, 0),
            starts_at=datetime.datetime(2026, 3, 1, 19, 0, tzinfo=tz),
        )

    def test_day_range_narrows_list(self):
        list_url = reverse("event-list")
        for lang in ("en", "de"):
            with self.subTest(lang=lang):
                html = self.client.get(list_url, HTTP_ACCEPT_LANGUAGE=lang).content.decode()
                fmt = picker_input(html, "day_from")["config"]["format"]
                params = {
                    "day_from": php_date(datetime.date(2026, 10, 1), fmt),
                    "day_to": php_date(datetime.date(2026, 10, 31), fmt),
                }
                resp = self.client.get(list_url, params, HTTP_ACCEPT_LANGUAGE=lang)
                self.assertContains(resp, "Autumn meetup")
                self.assertNotContains(resp, "Spring meetup")

    def test_garbage_filter_value_does_not_crash(self):
        resp = self.client.get(reverse("event-list"), {"day_from": "garbage"})
        self.assertEqual(resp.status_code, 200)


class EventSeedTest(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed", verbosity=0)
        count = Event.objects.count()
        self.assertGreaterEqual(count, 10)
        call_command("seed", verbosity=0)
        self.assertEqual(Event.objects.count(), count)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd examples/bootstrap5 && uv run pytest datetimepicker -q`
Expected: collection error — `No module named 'datetimepicker.models'`.

- [ ] **Step 3: App config, model, migration**

`examples/bootstrap5/datetimepicker/apps.py`:

```python
from django.apps import AppConfig


class DatetimepickerExampleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datetimepicker"
    label = "datetimepicker_example"  # distinct from the crud_views_widget_datetimepicker app label
```

`examples/bootstrap5/datetimepicker/models.py`:

```python
from django.db import models
from django.utils.translation import gettext_lazy as _


class Event(models.Model):
    title = models.CharField(_("title"), max_length=100)
    day = models.DateField(_("day"))
    doors_open = models.TimeField(_("doors open"))
    starts_at = models.DateTimeField(_("starts at"))
    ends_at = models.DateTimeField(_("ends at"), null=True, blank=True)

    class Meta:
        ordering = ["day", "starts_at"]
        verbose_name = _("event")
        verbose_name_plural = _("events")

    def __str__(self):
        return self.title
```

Add `"datetimepicker",` to `INSTALLED_APPS` in `project/settings.py` under the `# example feature apps` comment.

Run: `cd examples/bootstrap5 && uv run manage.py makemigrations datetimepicker_example && uv run ruff format datetimepicker/migrations`
Expected: `datetimepicker/migrations/0001_initial.py` with `- Create model Event`.

- [ ] **Step 4: Form and filter**

`examples/bootstrap5/datetimepicker/forms.py`:

```python
import django_filters
from crispy_forms.layout import Layout, Row
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import Column3, Column4, Column6, CrispyModelForm
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views_widget_datetimepicker.widgets import DatePickerInput, DateTimePickerInput, TimePickerInput

from datetimepicker.models import Event


class EventForm(CrispyModelForm):
    """The everyday case: one widget per field type, nothing else to configure."""

    class Meta:
        model = Event
        fields = ["title", "day", "doors_open", "starts_at", "ends_at"]
        widgets = {
            "day": DatePickerInput(),
            "doors_open": TimePickerInput(),
            "starts_at": DateTimePickerInput(),
            "ends_at": DateTimePickerInput(),
        }

    def get_layout_fields(self):
        return [
            Row(Column6("title"), Column3("day"), Column3("doors_open")),
            Row(Column6("starts_at"), Column6("ends_at")),
        ]

    def clean(self):
        cleaned = super().clean()
        starts_at, ends_at = cleaned.get("starts_at"), cleaned.get("ends_at")
        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error("ends_at", _("The end must be after the start."))
        return cleaned


class EventFilter(django_filters.FilterSet):
    """Date range filters: the picker widgets work on GET filter forms too."""

    day_from = django_filters.DateFilter(
        field_name="day", lookup_expr="gte", label=_("day from"), widget=DatePickerInput()
    )
    day_to = django_filters.DateFilter(field_name="day", lookup_expr="lte", label=_("day to"), widget=DatePickerInput())
    starts_after = django_filters.DateTimeFilter(
        field_name="starts_at", lookup_expr="gte", label=_("starts after"), widget=DateTimePickerInput()
    )

    class Meta:
        model = Event
        fields = ["day_from", "day_to", "starts_after"]


class EventFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("day_from"), Column4("day_to"), Column4("starts_after")))
```

`CrispyModelForm.get_layout_fields` may return a list of layout objects (see `crud_views/lib/crispy/form.py`).

- [ ] **Step 5: Views, URLs, project wiring, feature card**

`examples/bootstrap5/datetimepicker/views.py`:

```python
import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableFilterMixin,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from project.views import BreadcrumbMixin

from datetimepicker.forms import EventFilter, EventFilterFormHelper, EventForm
from datetimepicker.models import Event

# --------------------------------------------------------------------------- Event

cv_event = ViewSet(model=Event, name="event", icon_header="fa-regular fa-calendar")


class EventTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    day = tables.Column()
    doors_open = tables.Column()
    starts_at = tables.Column()
    ends_at = tables.Column()


class EventListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_event
    table_class = EventTable
    filterset_class = EventFilter
    formhelper_class = EventFilterFormHelper
    cv_list_actions = ["detail", "update", "quick_edit", "delete"]


class EventDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_event
    cv_property_display = [
        {"title": _("Event"), "icon": "calendar", "properties": ["title", "day", "doors_open", "starts_at", "ends_at"]},
    ]


class EventCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_message_template_code = _("Created event “{{ object }}”")


class EventUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_message_template_code = _("Updated event “{{ object }}”")


class EventQuickEditView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    """The same EventForm in a crud_views modal. Pickers activate because init.js re-runs on cv:modal:loaded.

    UpdateView does not support modals in django-crud-views 0.29, so this is a custom form view editing the instance.
    """

    cv_viewset = cv_event
    cv_key = "quick_edit"
    cv_path = "quick-edit"
    cv_permission = "change"
    cv_modal = True
    cv_modal_size = "modal-lg"
    form_class = EventForm
    cv_icon_action = "fa-solid fa-bolt"
    cv_action_label_template_code = _("Quick edit")
    cv_action_short_label_template_code = _("Quick edit")
    cv_header_template_code = _("Quick edit “{{ object }}”")
    cv_paragraph_template_code = _("The same form as the update page, opened in a modal.")
    cv_message_template_code = _("Updated event “{{ object }}”")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        return kwargs

    def cv_form_valid(self, context: dict):
        context["form"].save()


class EventDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_event
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted event “{{ object }}”")
```

`examples/bootstrap5/datetimepicker/urls.py`:

```python
from datetimepicker.views import cv_event

urlpatterns = cv_event.urlpatterns
```

Append to `project/urls.py`:

```python
urlpatterns += [path("datetimepicker/", include("datetimepicker.urls"))]
```

Append to `FEATURES` in `project/features.py`:

```python
    Feature(
        app="datetimepicker",
        viewset="event",
        group="widgets",
        title="Datetimepicker: forms, modals & filters",
        description="Date, time and datetime pickers on create/update forms, in a modal, and as list filters.",
        about=(
            "The everyday use of crud_views_widget_datetimepicker. The event form uses DatePickerInput, "
            "TimePickerInput and DateTimePickerInput; nothing else is configured — the plugin and init.js reach "
            "every page through {% cv_js %} / {% cv_css %}. Open “Quick edit” on a row to see the same form in a "
            "crud_views modal, and use the day range above the table to filter with the same widgets."
        ),
        look_at=(
            "EventForm.Meta.widgets and EventFilter in forms.py; EventQuickEditView (cv_modal = True) in views.py; "
            "CRUD_VIEWS_DATETIMEPICKER in project/settings.py."
        ),
        url_name="event-list",
        icon="fa-regular fa-calendar",
    ),
```

- [ ] **Step 6: Seed data**

`examples/bootstrap5/datetimepicker/seed.py`:

```python
import datetime

from django.utils import timezone

from datetimepicker.models import Event

#: (title, days from the first of this month, doors open, start, duration in hours or None)
EVENTS = [
    ("Kick-off", 2, "17:30", "18:00", 2),
    ("Django meetup", 9, "18:30", "19:00", 3),
    ("Code review clinic", 16, "16:45", "17:00", 1),
    ("Release party", 23, "19:00", "20:00", None),
    ("Sprint planning", 33, "08:45", "09:00", 2),
    ("Accessibility workshop", 40, "09:30", "10:00", 6),
    ("Django meetup", 47, "18:30", "19:00", 3),
    ("Hack night", 54, "19:30", "20:00", 4),
    ("Quarterly review", 64, "13:45", "14:00", 2),
    ("Django meetup", 75, "18:30", "19:00", 3),
    ("Year-end retro", 86, "15:30", "16:00", 2),
    ("Holiday dinner", 92, "18:00", "19:00", None),
]


def _time(text: str) -> datetime.time:
    return datetime.time.fromisoformat(text)


def seed():
    tz = timezone.get_current_timezone()
    first = timezone.localdate().replace(day=1)
    for title, offset, doors, start, hours in EVENTS:
        day = first + datetime.timedelta(days=offset)
        starts_at = datetime.datetime.combine(day, _time(start), tzinfo=tz)
        Event.objects.get_or_create(
            title=title,
            day=day,
            defaults={
                "doors_open": _time(doors),
                "starts_at": starts_at,
                "ends_at": starts_at + datetime.timedelta(hours=hours) if hours else None,
            },
        )
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd examples/bootstrap5 && uv run pytest -q`
Expected: `17 passed` (Task 1's 6 + Task 2's 11). If `test_rendered_value_matches_picker_format_and_round_trips[en]` or `test_day_range_narrows_list[en]` fails with "Enter a valid date", the prerequisite is not merged — stop and report (see Global Constraints). If a URL name differs (e.g. `event-quick-edit`), print `[p.name for p in cv_event.urlpatterns]` and align the tests and nothing else.

Also run: `cd examples/bootstrap5 && uv run manage.py check`
Expected: no issues (this catches `cv_modal` misuse and unregistered `cv_list_actions` keys).

- [ ] **Step 8: Lint and commit**

Run from repo root: `uv run ruff check . && uv run ruff format --check .`

```bash
git add examples/bootstrap5
git commit -m "feat(example): datetimepicker forms, modal quick edit and list filters" -- examples/bootstrap5
```

---

### Task 3: `datetimepicker` app — PickerVariant (per-field config)

**Files:**
- Modify: `examples/bootstrap5/datetimepicker/{models,forms,views,urls,seed,tests}.py`, `project/features.py`
- Create: `examples/bootstrap5/datetimepicker/migrations/0002_pickervariant.py` (generated)

**Interfaces:**
- Consumes: Task 2's `datetimepicker` app, `picker_input()` test helper, `EventTestCase`-style setup.
- Produces: `PickerVariant` model; `cv_variant` ViewSet (name `"variant"`), URL names `variant-list`, `variant-create`, `variant-update`, `variant-delete`; second `Feature` entry with `viewset="variant"`.

- [ ] **Step 1: Write the failing tests**

Append to `examples/bootstrap5/datetimepicker/tests.py`:

```python
from datetimepicker.models import PickerVariant  # noqa: E402 — appended section


class VariantTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="t-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)

    def configs(self) -> dict:
        html = self.client.get(reverse("variant-create")).content.decode()
        names = ["this_year", "quarter_hour", "no_past", "weekdays_only", "inline_calendar", "german"]
        return {name: picker_input(html, name)["config"] for name in names}

    def test_each_field_carries_its_override(self):
        configs = self.configs()
        year = timezone.localdate().year
        self.assertEqual(configs["this_year"]["minDate"], f"{year}-01-01")
        self.assertEqual(configs["this_year"]["maxDate"], f"{year}-12-31")
        self.assertEqual(configs["quarter_hour"]["step"], 15)
        self.assertEqual(configs["no_past"]["minDate"], 0)
        self.assertEqual(configs["weekdays_only"]["disabledWeekDays"], [0, 6])
        self.assertTrue(configs["inline_calendar"]["inline"])
        self.assertEqual(configs["german"]["lang"], "de")

    def test_settings_defaults_apply_to_every_variant(self):
        for name, config in self.configs().items():
            self.assertEqual(config["dayOfWeekStart"], 1, name)

    def test_create_with_empty_fields(self):
        resp = self.client.post(reverse("variant-create"), {"name": "Empty"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(PickerVariant.objects.filter(name="Empty").exists())

    def test_about_panel_matches_card(self):
        from project.features import FEATURES

        by_viewset = {f.viewset: f for f in FEATURES}
        variant_page = self.client.get(reverse("variant-list"))
        event_page = self.client.get(reverse("event-list"))
        self.assertContains(variant_page, by_viewset["variant"].title)
        self.assertNotContains(variant_page, by_viewset["event"].about)
        self.assertContains(event_page, by_viewset["event"].title)
        self.assertNotContains(event_page, by_viewset["variant"].about)


class VariantSeedTest(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed", verbosity=0)
        count = PickerVariant.objects.count()
        self.assertGreaterEqual(count, 1)
        call_command("seed", verbosity=0)
        self.assertEqual(PickerVariant.objects.count(), count)
```

Then move the `from datetimepicker.models import PickerVariant` import up into the existing import block (`from datetimepicker.models import Event, PickerVariant`) and drop the `noqa` line, so ruff's import sorting passes.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd examples/bootstrap5 && uv run pytest datetimepicker -q`
Expected: `ImportError: cannot import name 'PickerVariant'`.

- [ ] **Step 3: Model and migration**

Append to `examples/bootstrap5/datetimepicker/models.py`:

```python
class PickerVariant(models.Model):
    """One field per per-field config example; all optional so any subset can be tried."""

    name = models.CharField(_("name"), max_length=100)
    this_year = models.DateTimeField(_("this year only"), null=True, blank=True)
    quarter_hour = models.TimeField(_("quarter-hour steps"), null=True, blank=True)
    no_past = models.DateField(_("today or later"), null=True, blank=True)
    weekdays_only = models.DateField(_("weekdays only"), null=True, blank=True)
    inline_calendar = models.DateField(_("inline calendar"), null=True, blank=True)
    german = models.DateField(_("German picker"), null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("picker variant")
        verbose_name_plural = _("picker variants")

    def __str__(self):
        return self.name
```

Run: `cd examples/bootstrap5 && uv run manage.py makemigrations datetimepicker_example && uv run ruff format datetimepicker/migrations`
Expected: `0002_pickervariant.py` with `- Create model PickerVariant`.

- [ ] **Step 4: Form**

Append to `examples/bootstrap5/datetimepicker/forms.py` (change the models import to `from datetimepicker.models import Event, PickerVariant` and add `from django.utils import timezone`):

```python
class PickerVariantForm(CrispyModelForm):
    """Per-field config. Merge order, lowest to highest: widget class defaults → LANG → settings DEFAULTS →
    the config passed here. dayOfWeekStart=1 on every picker comes from CRUD_VIEWS_DATETIMEPICKER["DEFAULTS"]."""

    class Meta:
        model = PickerVariant
        fields = ["name", "this_year", "quarter_hour", "no_past", "weekdays_only", "inline_calendar", "german"]
        widgets = {
            # fix_year limits min/max date and the year dropdown to one year
            "this_year": DateTimePickerInput(fix_year=timezone.localdate().year),
            "quarter_hour": TimePickerInput(config={"step": 15}),
            "no_past": DatePickerInput(config={"minDate": 0}),  # 0 = today
            "weekdays_only": DatePickerInput(config={"disabledWeekDays": [0, 6]}),  # Sunday, Saturday
            "inline_calendar": DatePickerInput(config={"inline": True}),
            "german": DatePickerInput(config={"lang": "de"}),  # overrides the LANG fallback
        }

    def get_layout_fields(self):
        return [
            Row(Column6("name"), Column6("this_year")),
            Row(Column4("quarter_hour"), Column4("no_past"), Column4("weekdays_only")),
            Row(Column6("inline_calendar"), Column6("german")),
        ]
```

`fix_year=timezone.localdate().year` is evaluated at import time; that is fine for a local example (restart the server on New Year).

- [ ] **Step 5: Views, URLs, feature card, seed**

Append to `examples/bootstrap5/datetimepicker/views.py` (add `PickerVariantForm` and `PickerVariant` to the imports):

```python
# --------------------------------------------------------------------------- PickerVariant

cv_variant = ViewSet(model=PickerVariant, name="variant", icon_header="fa-solid fa-sliders")


class PickerVariantTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    this_year = tables.Column()
    quarter_hour = tables.Column()
    no_past = tables.Column()
    weekdays_only = tables.Column()
    german = tables.Column()


class PickerVariantListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_variant
    table_class = PickerVariantTable


class PickerVariantDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_variant
    cv_property_display = [
        {
            "title": _("Picker variant"),
            "icon": "sliders",
            "properties": [
                "name",
                "this_year",
                "quarter_hour",
                "no_past",
                "weekdays_only",
                "inline_calendar",
                "german",
            ],
        },
    ]


class PickerVariantCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_variant
    form_class = PickerVariantForm
    cv_message_template_code = _("Created picker variant “{{ object }}”")


class PickerVariantUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_variant
    form_class = PickerVariantForm
    cv_message_template_code = _("Updated picker variant “{{ object }}”")


class PickerVariantDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_variant
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted picker variant “{{ object }}”")
```

`examples/bootstrap5/datetimepicker/urls.py`:

```python
from datetimepicker.views import cv_event, cv_variant

urlpatterns = cv_event.urlpatterns + cv_variant.urlpatterns
```

Append to `FEATURES`:

```python
    Feature(
        app="datetimepicker",
        viewset="variant",
        group="widgets",
        title="Datetimepicker: per-field config",
        description="Per-field picker options: one year only, 15-minute steps, no past dates, inline, language.",
        about=(
            "Each field passes its own xdsoft options through the widget's config argument. Options merge from "
            "lowest to highest: the widget class defaults, LANG, CRUD_VIEWS_DATETIMEPICKER['DEFAULTS'] (here "
            "dayOfWeekStart=1, so every week starts on Monday), then the per-field config. fix_year is a shortcut "
            "that sets minDate, maxDate, yearStart and yearEnd."
        ),
        look_at="PickerVariantForm.Meta.widgets in forms.py; CRUD_VIEWS_DATETIMEPICKER in project/settings.py.",
        url_name="variant-list",
        icon="fa-solid fa-sliders",
    ),
```

Append to `examples/bootstrap5/datetimepicker/seed.py` (add `PickerVariant` to the models import):

```python
def seed_variants():
    PickerVariant.objects.get_or_create(name="Example", defaults={"quarter_hour": datetime.time(9, 15)})
```

and call `seed_variants()` at the end of `seed()`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd examples/bootstrap5 && uv run pytest -q && uv run manage.py check`
Expected: all pass (Task 1's project tests now loop over both cards); no system-check issues.

- [ ] **Step 7: Lint and commit**

Run from repo root: `uv run ruff check . && uv run ruff format --check .`

```bash
git add examples/bootstrap5
git commit -m "feat(example): datetimepicker per-field config variants" -- examples/bootstrap5
```

---

### Task 4: CI, docs and manual browser pass

**Files:**
- Modify: `.github/workflows/tests.yml`, `README.md`, `CLAUDE.md`

- [ ] **Step 1: CI step**

In `.github/workflows/tests.yml`, after the root `pytest` step and before the codecov step, add:

```yaml
      - name: Example app tests
        working-directory: examples/bootstrap5
        run: uv run --no-sources --extra dev pytest
```

- [ ] **Step 2: README section**

Append to `README.md`:

````markdown
## Example app

`examples/bootstrap5/` is a local Django project with one page per use case
(forms, modal, list filters, per-field config). It runs against the code in `src/`.

```bash
cd examples/bootstrap5
task run        # migrate, seed, runserver on :8000 — log in as admin/admin
task test       # the example's own tests
```

Without [Task](https://taskfile.dev): `uv run manage.py migrate && uv run manage.py seed && uv run manage.py runserver`.
````

- [ ] **Step 3: CLAUDE.md section**

In `CLAUDE.md`, add after the `## Commands` code block:

````markdown
### Example app

```bash
cd examples/bootstrap5 && task run     # migrate + seed (admin/admin) + runserver
cd examples/bootstrap5 && uv run pytest
```

Lives in the repo's uv env (no own pyproject). Root `uv run pytest` does **not** collect it
(`testpaths = ["tests"]`); CI runs it as a separate step. New `crud_views_widget_*` apps
add one example app plus `Feature` entries in `project/features.py` (matched to pages by
`Feature.viewset`).
````

- [ ] **Step 4: Verify everything**

Run from repo root:
```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest -q
(cd examples/bootstrap5 && uv run --no-sources --extra dev pytest -q)
```
Expected: lint clean, `28 passed` at root, all example tests pass.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/tests.yml README.md CLAUDE.md
git commit -m "ci: run example app tests; docs: example app" -- .github/workflows/tests.yml README.md CLAUDE.md
```

- [ ] **Step 6: Manual browser pass**

Run: `cd examples/bootstrap5 && task run` (or the uv commands), open http://localhost:8000, log in as `admin/admin`, and check — in English, then switch to Deutsch and repeat:
- Home shows both cards; nav "Widgets" dropdown lists both.
- Event list: day-range pickers open; choosing a range filters the table.
- Event create/update: date, time and datetime pickers open; picking values and saving works; end ≤ start shows the error and the pickers still open afterwards.
- Quick edit (row action): modal opens, pickers open inside it, saving closes the modal and shows the success message.
- Delete opens a modal.
- Per-field config create: year limited to this year, 15-minute steps, past days disabled, weekends disabled, inline calendar visible without clicking, German month names on the last field; weeks start on Monday everywhere.
- Browser console: no JS errors.

Report anything that fails with a screenshot; do not mark the plan done until this pass is clean.
