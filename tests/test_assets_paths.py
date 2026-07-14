# Deliberately no Django imports: this module must work at settings-time.
from crud_views_widget_datetimepicker.assets import (
    ALL_FILES,
    APP_LABEL,
    INIT_JS,
    bundle,
    cdn_files,
    source_files,
)

CDN = "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/"


def test_source_files_minified():
    files = source_files("2.5.21")
    assert files["js"] == [
        "crud_views_widget_datetimepicker/2.5.21/jquery.datetimepicker.full.min.js",
        "crud_views_widget_datetimepicker/init.js",
    ]
    assert files["css"] == ["crud_views_widget_datetimepicker/2.5.21/jquery.datetimepicker.min.css"]


def test_source_files_unminified_for_pipeline():
    files = source_files("2.5.21", minified=False)
    assert files["js"][0].endswith("/jquery.datetimepicker.full.js")
    assert files["js"][1] == INIT_JS  # init.js last: plugin must load first
    assert files["css"] == ["crud_views_widget_datetimepicker/2.5.21/jquery.datetimepicker.css"]


def test_cdn_files():
    files = cdn_files(CDN, "2.5.21")
    assert files["js"] == [
        "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@2.5.21/build/jquery.datetimepicker.full.min.js"
    ]
    assert files["css"] == [
        "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@2.5.21/build/jquery.datetimepicker.min.css"
    ]


def test_bundle_cdn_appends_static_init_js():
    b = bundle("cdn", "2.5.21", CDN)
    assert b["js"][0].startswith("https://")
    assert b["js"][1] == INIT_JS


def test_bundle_vendored_equals_source_files():
    assert bundle("vendored", "2.5.21", CDN) == source_files("2.5.21")


def test_all_files_covers_both_variants():
    assert set(ALL_FILES) == {
        "jquery.datetimepicker.full.js",
        "jquery.datetimepicker.full.min.js",
        "jquery.datetimepicker.css",
        "jquery.datetimepicker.min.css",
    }
    assert APP_LABEL == "crud_views_widget_datetimepicker"
