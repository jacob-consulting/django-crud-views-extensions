import django_filters
from crispy_forms.layout import Layout, Row
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import Column3, Column4, Column6, CrispyModelForm
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views_widget_datetimepicker.widgets import DatePickerInput, DateTimePickerInput, TimePickerInput

from datetimepicker.models import Event, PickerVariant


class EventForm(CrispyModelForm):
    """The everyday case: one widget per field type, nothing else to configure."""

    class Meta:
        model = Event
        fields = ["title", "day", "doors_open", "starts_at", "ends_at"]
        widgets = {
            "day": DatePickerInput(),
            "doors_open": TimePickerInput(),
            "starts_at": DateTimePickerInput(),
            "ends_at": DateTimePickerInput(),
        }

    def get_layout_fields(self):
        return [
            Row(Column6("title"), Column3("day"), Column3("doors_open")),
            Row(Column6("starts_at"), Column6("ends_at")),
        ]

    def clean(self):
        cleaned = super().clean()
        starts_at, ends_at = cleaned.get("starts_at"), cleaned.get("ends_at")
        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error("ends_at", _("The end must be after the start."))
        return cleaned


class EventFilter(django_filters.FilterSet):
    """Date range filters: the picker widgets work on GET filter forms too."""

    day_from = django_filters.DateFilter(
        field_name="day", lookup_expr="gte", label=_("day from"), widget=DatePickerInput()
    )
    day_to = django_filters.DateFilter(field_name="day", lookup_expr="lte", label=_("day to"), widget=DatePickerInput())
    starts_after = django_filters.DateTimeFilter(
        field_name="starts_at", lookup_expr="gte", label=_("starts after"), widget=DateTimePickerInput()
    )

    class Meta:
        model = Event
        fields = ["day_from", "day_to", "starts_after"]


class EventFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("day_from"), Column4("day_to"), Column4("starts_after")))


class PickerVariantForm(CrispyModelForm):
    """Per-field config. Merge order, lowest to highest: widget class defaults → LANG → settings DEFAULTS →
    the config passed here. dayOfWeekStart=1 on every picker comes from CRUD_VIEWS_DATETIMEPICKER["DEFAULTS"]."""

    class Meta:
        model = PickerVariant
        fields = ["name", "this_year", "quarter_hour", "no_past", "weekdays_only", "inline_calendar", "fixed_times"]
        widgets = {
            # fix_year limits min/max date and the year dropdown to one year
            "this_year": DateTimePickerInput(fix_year=timezone.localdate().year),
            "quarter_hour": TimePickerInput(config={"step": 15}),
            "no_past": DatePickerInput(config={"minDate": 0}),  # 0 = today
            "weekdays_only": DatePickerInput(config={"disabledWeekDays": [0, 6]}),  # Sunday, Saturday
            "inline_calendar": DatePickerInput(config={"inline": True}),
            "fixed_times": TimePickerInput(config={"allowTimes": ["09:00", "12:00", "15:00"]}),
        }

    def get_layout_fields(self):
        return [
            Row(Column6("name"), Column6("this_year")),
            Row(Column4("quarter_hour"), Column4("no_past"), Column4("weekdays_only")),
            Row(Column6("inline_calendar"), Column6("fixed_times")),
        ]
