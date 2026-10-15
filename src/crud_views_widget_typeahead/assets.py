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
