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
    "datetimepicker",
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
