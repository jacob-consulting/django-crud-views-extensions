from importlib.metadata import version

from django.conf import settings

from project.features import (
    CRUD_VIEWS_DEMO_URL,
    CRUD_VIEWS_DOCS_URL,
    CRUD_VIEWS_REPO_URL,
    DEMO_URL,
    DOCS_BASE,
    REPO_URL,
)


def project_info(request):  # Django context-processor signature
    return {
        "demo_mode": getattr(settings, "DEMO_MODE", False),
        "demo_url": DEMO_URL,
        "crud_views_version": version("django-crud-views"),
        "extensions_version": version("django-crud-views-extensions"),
        "repo_url": REPO_URL,
        "docs_url": f"{DOCS_BASE}/",
        "crud_views_docs_url": CRUD_VIEWS_DOCS_URL,
        "crud_views_repo_url": CRUD_VIEWS_REPO_URL,
        "crud_views_demo_url": CRUD_VIEWS_DEMO_URL,
    }
