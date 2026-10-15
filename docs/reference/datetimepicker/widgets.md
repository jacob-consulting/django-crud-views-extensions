# Widgets

!!! example "Try it live"
    The [Datetimepicker: forms, modals & filters](https://django-crud-views-extensions-demo.onrender.com/datetimepicker/event/) example in the live demo shows this in action — log in as
    `admin` / `admin`. See [Live demo](../../getting_started/example_app.md#live-demo) for data resets and wake-up time.

`crud_views_widget_datetimepicker` ships three form widgets wrapping the
[xdsoft jQuery DateTimePicker](https://xdsoft.net/jqplugins/datetimepicker/):

| Widget | Form field | Class defaults |
|---|---|---|
| `DateTimePickerInput` | `DateTimeField` | — |
| `DatePickerInput` | `DateField` | `{"timepicker": False}` |
| `TimePickerInput` | `TimeField` | `{"timepicker": True, "datepicker": False}` |

```python
from crud_views.lib.crispy import CrispyModelForm
from crud_views_widget_datetimepicker.widgets import DateTimePickerInput, DatePickerInput, TimePickerInput

from appointments.models import Appointment


class AppointmentForm(CrispyModelForm):
    class Meta:
        model = Appointment
        fields = ["title", "starts_at"]
        widgets = {"starts_at": DateTimePickerInput()}
```

The widgets also work in django-filter filter forms, e.g.
`django_filters.DateFilter(field_name="day", lookup_expr="gte", widget=DatePickerInput())`.

## Options

### `config={...}`

Any [xdsoft option](https://xdsoft.net/jqplugins/datetimepicker/), passed to the picker as-is:

```python
widgets = {
    "quarter_hour": TimePickerInput(config={"step": 15}),
    "no_past": DatePickerInput(config={"minDate": 0}),  # 0 = today
    "weekdays_only": DatePickerInput(config={"disabledWeekDays": [0, 6]}),  # Sunday, Saturday
    "inline_calendar": DatePickerInput(config={"inline": True}),
    "fixed_times": TimePickerInput(config={"allowTimes": ["09:00", "12:00", "15:00"]}),
}
```

### `fix_year=2026` (`DateTimePickerInput` only)

Locks the picker to one calendar year: sets `minDate` to `2026-01-01`, `maxDate` to `2026-12-31`, and
`yearStart` / `yearEnd` to `2026`. The values are only defaults: an option you pass in `config` wins.

### `format=` (Django's own widget argument)

Pins the format the value is rendered and parsed with; see [Formats & language](formats.md).

## Config merge order

!!! example "Try it live"
    The [Datetimepicker: per-field config](https://django-crud-views-extensions-demo.onrender.com/datetimepicker/variant/) example in the live demo shows per-field options and settings `DEFAULTS` in action — log in as
    `admin` / `admin`. See [Live demo](../../getting_started/example_app.md#live-demo) for data resets and wake-up time.

The picker config is merged from these sources, lowest to highest priority:

1. the widget class defaults (table above),
2. `lang` (see [Formats & language](formats.md#language)),
3. `CRUD_VIEWS_DATETIMEPICKER["DEFAULTS"]` from your [settings](settings.md),
4. the per-field `config`.

```python
# settings.py: every week starts on Monday
CRUD_VIEWS_DATETIMEPICKER = {"DEFAULTS": {"dayOfWeekStart": 1}}

# forms.py: this field also gets 15-minute steps
widgets = {"starts_at": DateTimePickerInput(config={"step": 15})}
```

## How it works

The widgets have **no `Media` class**. The plugin and a small `init.js` are registered with the
django-crud-views asset registry, so `{% cv_css %}` / `{% cv_js %}` deliver them on every page.

At render time (per request) each widget serialises its merged config to JSON in an
`xdsoft-datetime-config` attribute. `init.js` activates every `input[xdsoft-datetime-config]` on document
ready, and again whenever django-crud-views dispatches `cv:modal:loaded` on `#cv-modal` after injecting
modal content, so pickers work inside crud-views modals.

!!! note
    jQuery must be loaded in your base template before `{% cv_js %}` — the same rule as django-crud-views core.
