"""Form widgets wrapping the xdsoft jQuery DateTimePicker.

The widgets only emit a JSON config in the ``xdsoft-datetime-config`` attribute;
``init.js`` (delivered via the crud_views asset registry) turns matching inputs
into pickers. No Media classes on purpose: assets are page-global via cv_js/cv_css.

The config is built at render time, so the picker format and language follow the
active request language. The value is rendered and parsed with that same format, so
whatever the picker writes round-trips in every locale.
"""

import datetime
import json
from copy import copy

from django.forms import DateInput, DateTimeInput
from django.forms.widgets import TimeInput
from django.utils import formats
from django.utils.translation import get_language

from .conf import get_config
from .formats import php_to_strftime, strftime_to_php


class XdsoftConfigMixin:
    """Merge order (lowest to highest): class defaults, lang, settings DEFAULTS,
    per-field config.

    ``format`` comes from (highest first): an explicit picker ``format`` (settings
    DEFAULTS or per-field config), the Django ``format=`` widget argument, the active
    locale's input formats (``format_key``), ``fallback_format``. A Django ``format=``
    the picker cannot reproduce leaves the picker on its own default."""

    defaults: dict = {}
    fallback_format: str = ""  # strftime; every Django locale accepts it

    def __init__(self, *args, config=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.picker_config = dict(config or {})

    def prefers(self, fmt: str) -> bool:
        """Among the locale's input formats, pick the first one this returns True for."""
        return True

    def locale_format(self) -> str:
        candidates = [f for f in formats.get_format(self.format_key) if strftime_to_php(f)]
        preferred = [f for f in candidates if self.prefers(f)]
        return (preferred or candidates or [self.fallback_format])[0]

    def get_picker_config(self) -> dict:
        cfg = get_config()
        merged = copy(self.defaults)
        merged["lang"] = cfg.lang if cfg.lang_explicit else (get_language() or cfg.lang).split("-")[0]
        merged.update(cfg.defaults)
        merged.update(self.picker_config)
        if "format" not in merged:
            picker_format = strftime_to_php(self.format or self.locale_format())
            if picker_format:  # else: picker default; Django renders with self.format, the field's input_formats parse
                merged["format"] = picker_format
        return merged

    def strftime_format(self, config: dict) -> str | None:
        """The Python format matching the picker's, or None if the picker format has no equivalent."""
        return php_to_strftime(config["format"]) if config.get("format") else None

    def get_context(self, name, value, attrs):
        config = self.get_picker_config()
        context = super().get_context(name, value, attrs)
        fmt = self.strftime_format(config)
        if fmt and isinstance(value, (datetime.date, datetime.time)):
            context["widget"]["value"] = value.strftime(fmt)
        context["widget"]["attrs"]["xdsoft-datetime-config"] = json.dumps(config)
        return context

    def value_from_datadict(self, data, files, name):
        """Parse what the picker wrote; anything else goes to the field's own validation unchanged."""
        value = super().value_from_datadict(data, files, name)
        fmt = self.strftime_format(self.get_picker_config())
        if fmt and isinstance(value, str) and value.strip():
            try:
                return self.from_datetime(datetime.datetime.strptime(value.strip(), fmt))
            except ValueError:
                pass
        return value

    def from_datetime(self, value: datetime.datetime):
        return value


class DateTimePickerInput(XdsoftConfigMixin, DateTimeInput):
    """https://xdsoft.net/jqplugins/datetimepicker/ — for DateTimeField."""

    fallback_format = "%Y-%m-%d %H:%M"

    def __init__(self, *args, fix_year=None, config=None, **kwargs):
        config = dict(config or {})
        if fix_year is not None:
            config.setdefault("minDate", f"{fix_year}-01-01")
            config.setdefault("maxDate", f"{fix_year}-12-31")
            config.setdefault("yearStart", f"{fix_year}")
            config.setdefault("yearEnd", f"{fix_year}")
        super().__init__(*args, config=config, **kwargs)

    def prefers(self, fmt: str) -> bool:
        return "%S" not in fmt  # the picker offers hours and minutes only; it would fill in the current seconds


class DatePickerInput(XdsoftConfigMixin, DateInput):
    """For DateField."""

    defaults = {"timepicker": False}
    fallback_format = "%Y-%m-%d"

    def from_datetime(self, value: datetime.datetime):
        return value.date()


class TimePickerInput(XdsoftConfigMixin, TimeInput):
    """For TimeField."""

    defaults = {"timepicker": True, "datepicker": False}
    fallback_format = "%H:%M"

    def prefers(self, fmt: str) -> bool:
        return "%S" not in fmt  # the picker offers hours and minutes only

    def from_datetime(self, value: datetime.datetime):
        return value.time()
