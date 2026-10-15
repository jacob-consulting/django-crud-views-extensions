# Your first datetimepicker

Given a model with date, time and datetime fields:

```python
# events/models.py
from django.db import models


class Event(models.Model):
    title = models.CharField(max_length=100)
    day = models.DateField()
    doors_open = models.TimeField()
    starts_at = models.DateTimeField()
```

pick the matching widget per field:

```python
# events/forms.py
from crud_views.lib.crispy import CrispyModelForm
from crud_views_widget_datetimepicker.widgets import DatePickerInput, DateTimePickerInput, TimePickerInput

from events.models import Event


class EventForm(CrispyModelForm):
    class Meta:
        model = Event
        fields = ["title", "day", "doors_open", "starts_at"]
        widgets = {
            "day": DatePickerInput(),
            "doors_open": TimePickerInput(),
            "starts_at": DateTimePickerInput(),
        }
```

That is all: there is nothing else to configure. By default the plugin loads from jsDelivr, and the widget
renders an `<input>` carrying its picker config in an `xdsoft-datetime-config` attribute, which the app's
`init.js` turns into a picker. A plain Django `ModelForm` works the same way.

## The format follows the language

The picker writes dates in the format of the active request language — `15.10.2026 19:00` for German,
`2026-10-15 19:00` for English — and the form accepts exactly that format. See
[Formats & language](../reference/datetimepicker/formats.md) to pin a format instead.

## Per-field options

Any xdsoft option goes into `config`:

```python
widgets = {"doors_open": TimePickerInput(config={"step": 15})}  # 15-minute steps
```

See [Widgets](../reference/datetimepicker/widgets.md) for all options and how they merge with settings.

!!! tip "Production"
    For production — and if you'd rather not have your users' browsers contact a CDN (GDPR) — serve the
    plugin from your own static files: [Vendored mode](../reference/datetimepicker/vendored.md).
