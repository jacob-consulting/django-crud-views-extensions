"""Form widgets wrapping the xdsoft jQuery DateTimePicker.

The widgets only emit a JSON config in the ``xdsoft-datetime-config`` attribute;
``init.js`` (delivered via the crud_views asset registry) turns matching inputs
into pickers. No Media classes on purpose: assets are page-global via cv_js/cv_css.
"""

import json
from copy import copy

from django.forms import DateInput, DateTimeInput
from django.forms.widgets import TimeInput

from .conf import get_config


class XdsoftConfigMixin:
    """Merge order (lowest to highest): class defaults, lang from settings,
    settings DEFAULTS, per-field config."""

    defaults: dict = {}

    def __init__(self, *args, config=None, **kwargs):
        cfg = get_config()
        merged = copy(self.defaults)
        merged["lang"] = cfg.lang
        merged.update(cfg.defaults)
        merged.update(config or {})
        super().__init__(*args, **kwargs)
        self.attrs["xdsoft-datetime-config"] = json.dumps(merged)


class DateTimePickerInput(XdsoftConfigMixin, DateTimeInput):
    """https://xdsoft.net/jqplugins/datetimepicker/ — for DateTimeField."""

    defaults = {"format": "d.m.Y H:i:s"}

    def __init__(self, *args, fix_year=None, config=None, **kwargs):
        config = dict(config or {})
        if fix_year is not None:
            config.setdefault("minDate", f"{fix_year}-01-01")
            config.setdefault("maxDate", f"{fix_year}-12-31")
            config.setdefault("yearStart", f"{fix_year}")
            config.setdefault("yearEnd", f"{fix_year}")
        super().__init__(*args, config=config, **kwargs)


class DatePickerInput(XdsoftConfigMixin, DateInput):
    """For DateField."""

    defaults = {"format": "d.m.Y", "timepicker": False}


class TimePickerInput(XdsoftConfigMixin, TimeInput):
    """For TimeField."""

    defaults = {"format": "H:i", "timepicker": True, "datepicker": False}
