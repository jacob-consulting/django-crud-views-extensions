"""Asset path definitions. Django-free by design: importable from settings.py,
so django-pipeline users can build bundles from the same single source of truth
that AppConfig.ready() feeds into the crud_views asset registry."""

APP_LABEL = "crud_views_widget_datetimepicker"
INIT_JS = f"{APP_LABEL}/init.js"

_FILES = {
    # minified: (js, css)
    True: ("jquery.datetimepicker.full.min.js", "jquery.datetimepicker.min.css"),
    False: ("jquery.datetimepicker.full.js", "jquery.datetimepicker.css"),
}

ALL_FILES = (
    "jquery.datetimepicker.full.js",
    "jquery.datetimepicker.full.min.js",
    "jquery.datetimepicker.css",
    "jquery.datetimepicker.min.css",
)


def source_files(version: str, minified: bool = True) -> dict:
    """Static paths for vendored mode / pipeline source_filenames.

    js order matters: the plugin must precede init.js (and jQuery precedes both,
    loaded by the project)."""
    base = f"{APP_LABEL}/{version}"
    js_file, css_file = _FILES[minified]
    return {"js": [f"{base}/{js_file}", INIT_JS], "css": [f"{base}/{css_file}"]}


def cdn_files(cdn_base: str, version: str, minified: bool = True) -> dict:
    """External URLs for CDN mode (plugin files only — init.js is always static)."""
    base = cdn_base.format(version=version).rstrip("/")
    js_file, css_file = _FILES[minified]
    return {"js": [f"{base}/{js_file}"], "css": [f"{base}/{css_file}"]}


def bundle(source: str, version: str, cdn_base: str, minified: bool = True) -> dict:
    """The js/css lists to register for a given SOURCE mode."""
    if source == "cdn":
        files = cdn_files(cdn_base, version, minified)
        return {"js": [*files["js"], INIT_JS], "css": files["css"]}
    return source_files(version, minified)
