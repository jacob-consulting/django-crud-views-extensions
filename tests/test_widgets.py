import json

from crud_views_widget_datetimepicker.widgets import (
    DatePickerInput,
    DateTimePickerInput,
    TimePickerInput,
)


def _config(widget) -> dict:
    return json.loads(widget.attrs["xdsoft-datetime-config"])


def test_datetime_defaults():
    cfg = _config(DateTimePickerInput())
    assert cfg["format"] == "d.m.Y H:i:s"
    assert cfg["lang"] == "de"  # from LANGUAGE_CODE="de-de"


def test_date_defaults():
    cfg = _config(DatePickerInput())
    assert cfg["format"] == "d.m.Y"
    assert cfg["timepicker"] is False


def test_time_defaults():
    cfg = _config(TimePickerInput())
    assert cfg["format"] == "H:i"
    assert cfg["timepicker"] is True
    assert cfg["datepicker"] is False


def test_fix_year():
    cfg = _config(DateTimePickerInput(fix_year=2026))
    assert cfg["minDate"] == "2026-01-01"
    assert cfg["maxDate"] == "2026-12-31"
    assert cfg["yearStart"] == "2026"
    assert cfg["yearEnd"] == "2026"


def test_merge_precedence(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"DEFAULTS": {"step": 30, "format": "Y-m-d"}}
    cfg = _config(DateTimePickerInput(config={"step": 15}))
    assert cfg["format"] == "Y-m-d"  # settings DEFAULTS beat built-ins
    assert cfg["step"] == 15  # per-field config beats settings DEFAULTS


def test_no_media_class():
    assert not hasattr(DateTimePickerInput, "Media")


def test_widgets_render_stock_input():
    html = DateTimePickerInput().render("starts_at", None)
    assert "xdsoft-datetime-config" in html
    assert "<input" in html
