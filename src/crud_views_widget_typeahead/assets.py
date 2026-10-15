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
