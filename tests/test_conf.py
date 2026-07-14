from pathlib import Path

from crud_views_widget_datetimepicker.conf import DEFAULT_CDN_BASE, DEFAULT_VERSION, get_config


def test_defaults_with_no_setting(settings):
    if hasattr(settings, "CRUD_VIEWS_DATETIMEPICKER"):
        del settings.CRUD_VIEWS_DATETIMEPICKER
    cfg = get_config()
    assert cfg.source == "cdn"
    assert cfg.version == DEFAULT_VERSION
    assert cfg.cdn_base == DEFAULT_CDN_BASE
    assert cfg.vendor_dir is None
    assert cfg.emit is True
    assert cfg.lang == "de"  # derived from LANGUAGE_CODE="de-de" in conftest
    assert cfg.defaults == {}


def test_explicit_settings_win(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {
        "SOURCE": "vendored",
        "VERSION": "9.9.9",
        "VENDOR_DIR": "/tmp/vendored",
        "EMIT": False,
        "LANG": "en",
        "DEFAULTS": {"step": 15},
    }
    cfg = get_config()
    assert cfg.source == "vendored"
    assert cfg.version == "9.9.9"
    assert cfg.vendor_dir == Path("/tmp/vendored")
    assert cfg.emit is False
    assert cfg.lang == "en"
    assert cfg.defaults == {"step": 15}
