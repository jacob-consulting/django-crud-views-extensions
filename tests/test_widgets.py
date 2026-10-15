import datetime
import html
import json
import re

import pytest
from django import forms
from django.utils import timezone, translation

from crud_views_widget_datetimepicker.formats import php_to_strftime
from crud_views_widget_datetimepicker.widgets import (
    DatePickerInput,
    DateTimePickerInput,
    TimePickerInput,
)


def _rendered(widget, value=None, name="field") -> dict:
    """Value and picker config of the rendered <input>, as the browser receives them."""
    tag = widget.render(name, value)
    config = re.search(r'xdsoft-datetime-config="([^"]*)"', tag).group(1)
    rendered_value = re.search(r'value="([^"]*)"', tag)
    return {
        "config": json.loads(html.unescape(config)),
        "value": html.unescape(rendered_value.group(1)) if rendered_value else "",
    }


def _config(widget) -> dict:
    return _rendered(widget)["config"]


class EventForm(forms.Form):
    day = forms.DateField(widget=DatePickerInput())
    doors_open = forms.TimeField(widget=TimePickerInput())
    starts_at = forms.DateTimeField(widget=DateTimePickerInput())


DAY = datetime.date(2026, 10, 15)
DOORS = datetime.time(18, 30)
STARTS = datetime.datetime(2026, 10, 15, 19, 0, 0)


# --------------------------------------------------------------------------- defaults


def test_datetime_defaults():
    with translation.override("de"):
        cfg = _config(DateTimePickerInput())
    assert cfg["format"] == "d.m.Y H:i"  # prefers a format without seconds: the picker cannot set them
    assert cfg["lang"] == "de"


def test_date_defaults():
    with translation.override("de"):
        cfg = _config(DatePickerInput())
    assert cfg["format"] == "d.m.Y"
    assert cfg["timepicker"] is False


def test_time_defaults():
    with translation.override("de"):
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
    assert cfg["format"] == "Y-m-d"  # settings DEFAULTS beat the locale format
    assert cfg["step"] == 15  # per-field config beats settings DEFAULTS


def test_no_media_class():
    assert not hasattr(DateTimePickerInput, "Media")


def test_widgets_render_stock_input():
    tag = DateTimePickerInput().render("starts_at", None)
    assert "xdsoft-datetime-config" in tag
    assert "<input" in tag


# --------------------------------------------------------------------------- locale formats


@pytest.mark.parametrize(
    "lang, date_fmt, datetime_fmt",
    [
        ("en", "Y-m-d", "Y-m-d H:i"),
        ("de", "d.m.Y", "d.m.Y H:i"),
        ("fr", "d/m/Y", "d/m/Y H:i"),
    ],
)
def test_format_follows_active_locale(lang, date_fmt, datetime_fmt):
    with translation.override(lang):
        assert _config(DatePickerInput())["format"] == date_fmt
        assert _config(DateTimePickerInput())["format"] == datetime_fmt
        assert _config(TimePickerInput())["format"] == "H:i"  # prefers a format without seconds


def test_datetime_value_renders_without_seconds():
    with translation.override("de"):
        rendered = _rendered(DateTimePickerInput(), datetime.datetime(2026, 10, 15, 19, 0, 35))
    assert rendered["value"] == "15.10.2026 19:00"


def test_pinned_format_with_seconds_still_round_trips():
    class Form(forms.Form):
        starts_at = forms.DateTimeField(widget=DateTimePickerInput(config={"format": "Y-m-d H:i:s"}))

    with translation.override("de"):
        assert _rendered(Form().fields["starts_at"].widget, STARTS)["value"] == "2026-10-15 19:00:00"
        bound = Form(data={"starts_at": "2026-10-15 19:00:00"})
        assert bound.is_valid(), bound.errors
    assert timezone.make_naive(bound.cleaned_data["starts_at"]) == STARTS


def test_time_value_renders_without_seconds():
    with translation.override("de"):
        assert _rendered(TimePickerInput(), DOORS)["value"] == "18:30"


@pytest.mark.parametrize("lang", ["en", "de", "fr"])
def test_rendered_value_matches_picker_format_and_round_trips(lang):
    """What Django renders is what the picker would write, and posting it back yields the same values."""
    with translation.override(lang):
        form = EventForm(initial={"day": DAY, "doors_open": DOORS, "starts_at": STARTS})
        data = {}
        for name, value in (("day", DAY), ("doors_open", DOORS), ("starts_at", STARTS)):
            rendered = _rendered(form.fields[name].widget, form[name].value(), name)
            assert rendered["value"] == value.strftime(php_to_strftime(rendered["config"]["format"]))
            data[name] = rendered["value"]
        bound = EventForm(data=data)
        assert bound.is_valid(), bound.errors
    assert bound.cleaned_data["day"] == DAY
    assert bound.cleaned_data["doors_open"] == DOORS
    assert timezone.make_naive(bound.cleaned_data["starts_at"]) == STARTS


def test_explicit_format_round_trips_in_any_locale():
    """A per-field format that the locale's input formats don't accept still renders and parses."""

    class Form(forms.Form):
        day = forms.DateField(widget=DatePickerInput(config={"format": "d.m.Y"}))

    with translation.override("en"):
        rendered = _rendered(Form().fields["day"].widget, DAY, "day")
        assert rendered["config"]["format"] == "d.m.Y"
        assert rendered["value"] == "15.10.2026"
        bound = Form(data={"day": "15.10.2026"})
        assert bound.is_valid(), bound.errors
    assert bound.cleaned_data["day"] == DAY


def test_django_format_kwarg_drives_picker_format():
    with translation.override("en"):
        widget = DatePickerInput(format="%d/%m/%Y")
        assert _config(widget)["format"] == "d/m/Y"
        assert _rendered(widget, DAY)["value"] == "15/10/2026"


def test_unparseable_input_falls_back_to_field_validation():
    with translation.override("en"):
        bound = EventForm(data={"day": "garbage", "doors_open": "18:30", "starts_at": "2026-10-15 19:00:00"})
        assert not bound.is_valid()
    assert "day" in bound.errors
    assert set(bound.errors) == {"day"}


def test_other_locale_input_format_still_accepted():
    """The widget's own parse is a convenience; Django's locale input formats keep working."""
    with translation.override("en"):
        bound = EventForm(data={"day": "10/15/2026", "doors_open": "18:30:00", "starts_at": "2026-10-15 19:00"})
        assert bound.is_valid(), bound.errors
    assert bound.cleaned_data["day"] == DAY


def test_invalid_submission_rerenders_submitted_text():
    with translation.override("en"):
        bound = EventForm(data={"day": "garbage", "doors_open": "18:30", "starts_at": "2026-10-15 19:00:00"})
        assert _rendered(bound.fields["day"].widget, bound["day"].value(), "day")["value"] == "garbage"


# --------------------------------------------------------------------------- language


@pytest.mark.parametrize("lang", ["en", "de", "fr"])
def test_lang_follows_active_language(lang):
    with translation.override(lang):
        assert _config(DatePickerInput())["lang"] == lang


def test_lang_uses_primary_subtag():
    with translation.override("en-gb"):
        assert _config(DatePickerInput())["lang"] == "en"


def test_explicit_lang_setting_wins(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"LANG": "fr"}
    with translation.override("de"):
        assert _config(DatePickerInput())["lang"] == "fr"


def test_per_field_lang_wins(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"LANG": "fr"}
    with translation.override("de"):
        assert _config(DatePickerInput(config={"lang": "en"}))["lang"] == "en"


def test_unconvertible_django_format_leaves_picker_default():
    """A Django format the picker cannot reproduce: no picker format, Django renders as usual."""
    with translation.override("en"):
        rendered = _rendered(DatePickerInput(format="%b %d, %Y"), DAY)
    assert "format" not in rendered["config"]
    assert rendered["value"] == "Oct 15, 2026"
