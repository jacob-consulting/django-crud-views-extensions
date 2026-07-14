from django.template import Context, Template

from crud_views_widget_datetimepicker.checks import check_datetimepicker


def test_bundle_registered_at_startup():
    # conftest has no CRUD_VIEWS_DATETIMEPICKER -> CDN mode defaults applied in ready()
    from crud_views.lib.assets import get_registered

    bundles = {b.key: b for b in get_registered()}
    assert "datetimepicker" in bundles
    b = bundles["datetimepicker"]
    assert b.js[0].startswith("https://cdn.jsdelivr.net/npm/jquery-datetimepicker@")
    assert b.js[-1] == "crud_views_widget_datetimepicker/init.js"
    assert b.emit is True


def test_cv_js_includes_picker_assets():
    html = Template("{% load crud_views %}{% cv_js %}").render(Context({}))
    assert "jquery.datetimepicker.full.min.js" in html
    assert "/static/crud_views_widget_datetimepicker/init.js" in html
    # ordering: core viewset.js before the picker plugin
    assert html.index("crud_views/js/viewset.js") < html.index("jquery.datetimepicker")


def test_check_vendored_without_vendor_dir_errors(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored"}
    messages = check_datetimepicker()
    assert [m.id for m in messages] == ["crud_views.E332"]


def test_check_vendored_missing_files_warns(settings, tmp_path):
    settings.CRUD_VIEWS_DATETIMEPICKER = {
        "SOURCE": "vendored",
        "VENDOR_DIR": str(tmp_path),
    }
    messages = check_datetimepicker()
    assert [m.id for m in messages] == ["crud_views.W330"]


def test_check_cdn_is_silent(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "cdn"}
    assert check_datetimepicker() == []


def test_init_js_content():
    from pathlib import Path

    import crud_views_widget_datetimepicker as pkg

    init = (
        Path(pkg.__file__).parent
        / "static"
        / "crud_views_widget_datetimepicker"
        / "init.js"
    ).read_text()
    assert "xdsoft-datetime-config" in init
    assert "cv:modal:loaded" in init
    assert "console.log" not in init


def test_check_invalid_source_errors(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "nonsense"}
    messages = check_datetimepicker()
    assert [m.id for m in messages] == ["crud_views.E333"]
