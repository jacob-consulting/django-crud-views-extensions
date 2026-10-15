from importlib.metadata import version

from project.features import REPO_URL


def project_info(request):  # Django context-processor signature
    return {
        "crud_views_version": version("django-crud-views"),
        "extensions_version": version("django-crud-views-extensions"),
        "repo_url": REPO_URL,
    }
