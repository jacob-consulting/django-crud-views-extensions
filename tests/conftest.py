from pathlib import Path

import django
from django.conf import settings


def pytest_configure():
    settings.configure(
        BASE_DIR=Path(__file__).resolve().parent,
        SECRET_KEY="django-testing",
        DEBUG=True,
        ALLOWED_HOSTS=[],
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django.contrib.staticfiles",
            "django_tables2",
            "django_object_detail",
            "crispy_forms",
            "crispy_bootstrap5",
            "crud_views.apps.CrudViewsConfig",
            "crud_views_widget_datetimepicker.apps.CrudViewsWidgetDatetimepickerConfig",
        ],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.request",
                    ],
                },
            }
        ],
        STATIC_URL="/static/",
        LANGUAGE_CODE="de-de",
        USE_TZ=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        CRUD_VIEWS_EXTENDS="base.html",
        CRISPY_ALLOWED_TEMPLATE_PACKS="bootstrap5",
        CRISPY_TEMPLATE_PACK="bootstrap5",
    )
    django.setup()
