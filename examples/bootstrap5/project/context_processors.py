from importlib.metadata import version

from django.conf import settings

from project.features import DEMO_URL, REPO_URL


def project_info(request):  # Django context-processor signature
    return {
        "demo_mode": getattr(settings, "DEMO_MODE", False),
        "demo_url": DEMO_URL,
        "crud_views_version": version("django-crud-views"),
        "extensions_version": version("django-crud-views-extensions"),
        "repo_url": REPO_URL,
    }
