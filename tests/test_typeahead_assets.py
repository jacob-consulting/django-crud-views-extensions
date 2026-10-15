import subprocess
import sys

from django.apps import apps
from django.template import Context, Template

from crud_views_widget_typeahead.assets import (
    APP_LABEL,
    CSS,
    JS,
    SELECT_CSS,
    SELECT_JS,
    bundle,
    select_bundle,
    select_source_files,
    source_files,
)
from crud_views_widget_typeahead.conf import DEFAULT_SELECT_TEMPLATE, DEFAULT_TEMPLATE, TypeaheadConfig, get_config


def _entry_path(entry) -> str:
    return getattr(entry, "path", entry)


def test_source_files():
    assert APP_LABEL == "crud_views_widget_typeahead"
    assert source_files() == {
        "js": ["crud_views_widget_typeahead/typeahead.js"],
        "css": ["crud_views_widget_typeahead/typeahead.css"],
    }
    assert JS == "crud_views_widget_typeahead/typeahead.js"
    assert CSS == "crud_views_widget_typeahead/typeahead.css"


def test_bundle_equals_source_files():
    assert bundle() == source_files()


def test_assets_module_is_django_free():
    code = "import sys, crud_views_widget_typeahead.assets; assert 'django' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True)


def test_app_is_installed():
    assert apps.get_app_config("crud_views_widget_typeahead").verbose_name == "CRUD Views Widget: Typeahead"


def test_bundle_registered_at_startup():
    from crud_views.lib.assets import get_registered

    bundle_ = {b.key: b for b in get_registered()}["typeahead"]
    assert [_entry_path(e) for e in bundle_.js] == [JS]
    assert [_entry_path(e) for e in bundle_.css] == [CSS]
    assert bundle_.emit is True


def test_cv_js_and_cv_css_include_typeahead():
    js = Template("{% load crud_views %}{% cv_js %}").render(Context({}))
    css = Template("{% load crud_views %}{% cv_css %}").render(Context({}))
    assert "/static/crud_views_widget_typeahead/typeahead.js" in js
    assert "/static/crud_views_widget_typeahead/typeahead.css" in css


def test_config_defaults():
    assert get_config() == TypeaheadConfig(emit=True, template=DEFAULT_TEMPLATE, debounce_ms=250)
    assert DEFAULT_TEMPLATE == "crud_views_widget_typeahead/typeahead.html"


def test_config_overrides(settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"EMIT": False, "TEMPLATE": "x/y.html", "DEBOUNCE_MS": 100}
    assert get_config() == TypeaheadConfig(emit=False, template="x/y.html", debounce_ms=100)


def test_select_source_files():
    assert select_source_files() == {
        "js": ["crud_views_widget_typeahead/typeahead-select.js"],
        "css": ["crud_views_widget_typeahead/typeahead-select.css"],
    }
    assert SELECT_JS == "crud_views_widget_typeahead/typeahead-select.js"
    assert SELECT_CSS == "crud_views_widget_typeahead/typeahead-select.css"
    assert select_bundle() == select_source_files()


def test_source_files_do_not_include_the_select_popup():
    # contract: pipeline configs call source_files(); the popup is opt-in via select_source_files()
    assert SELECT_JS not in source_files()["js"]
    assert SELECT_CSS not in source_files()["css"]


def test_select_bundle_registered_at_startup():
    from crud_views.lib.assets import get_registered

    bundles = {b.key: b for b in get_registered()}
    select = bundles["typeahead_select"]
    assert [_entry_path(e) for e in select.js] == [SELECT_JS]
    assert [_entry_path(e) for e in select.css] == [SELECT_CSS]
    assert select.emit is get_config().select_emit is True
    keys = list(bundles)
    assert keys.index("typeahead") < keys.index("typeahead_select")


def test_cv_js_and_cv_css_include_the_select_popup():
    js = Template("{% load crud_views %}{% cv_js %}").render(Context({}))
    css = Template("{% load crud_views %}{% cv_css %}").render(Context({}))
    assert "/static/crud_views_widget_typeahead/typeahead-select.js" in js
    assert "/static/crud_views_widget_typeahead/typeahead-select.css" in css


def test_select_static_files_exist():
    from django.contrib.staticfiles import finders

    assert finders.find(SELECT_JS)
    assert finders.find(SELECT_CSS)


def test_select_config_defaults():
    config = get_config()
    assert (config.select_emit, config.select_template) == (True, DEFAULT_SELECT_TEMPLATE)
    assert DEFAULT_SELECT_TEMPLATE == "crud_views_widget_typeahead/typeahead_select.html"


def test_select_config_overrides(settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"SELECT_EMIT": False, "SELECT_TEMPLATE": "x/select.html"}
    config = get_config()
    assert (config.select_emit, config.select_template) == (False, "x/select.html")
    assert (config.emit, config.template) == (True, DEFAULT_TEMPLATE)  # the text typeahead's keys are independent


def test_select_emit_false_is_passed_to_the_registry(settings, monkeypatch):
    from crud_views.lib import assets as core_assets
    from django.apps import apps

    settings.CRUD_VIEWS_TYPEAHEAD = {"SELECT_EMIT": False}
    monkeypatch.setattr(core_assets, "_REGISTRY", {})  # isolated: ready() would otherwise collide
    apps.get_app_config("crud_views_widget_typeahead").ready()
    bundles = {b.key: b for b in core_assets.get_registered()}
    assert bundles["typeahead_select"].emit is False
    assert bundles["typeahead"].emit is True
    assert core_assets.get_registered(only_emitting=True) is not None
    assert "typeahead_select" not in {b.key for b in core_assets.get_registered(only_emitting=True)}
