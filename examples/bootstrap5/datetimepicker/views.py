import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableFilterMixin,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from project.views import BreadcrumbMixin

from datetimepicker.forms import EventFilter, EventFilterFormHelper, EventForm, PickerVariantForm
from datetimepicker.models import Event, PickerVariant

# --------------------------------------------------------------------------- Event

cv_event = ViewSet(model=Event, name="event", icon_header="fa-regular fa-calendar")


class EventTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    day = tables.Column()
    doors_open = tables.Column()
    starts_at = tables.Column()
    ends_at = tables.Column()


class EventListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_event
    table_class = EventTable
    filterset_class = EventFilter
    formhelper_class = EventFilterFormHelper
    cv_list_actions = ["detail", "update", "quick_edit", "delete"]


class EventDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_event
    cv_property_display = [
        {"title": _("Event"), "icon": "calendar", "properties": ["title", "day", "doors_open", "starts_at", "ends_at"]},
    ]


class EventCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_message_template_code = _("Created event “{{ object }}”")


class EventUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_event
    form_class = EventForm
    cv_message_template_code = _("Updated event “{{ object }}”")


class EventQuickEditView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    """The same EventForm in a crud_views modal. Pickers activate because init.js re-runs on cv:modal:loaded.

    UpdateView does not support modals in django-crud-views 0.29, so this is a custom form view editing the instance.
    """

    cv_viewset = cv_event
    cv_key = "quick_edit"
    cv_path = "quick-edit"
    cv_permission = "change"
    cv_modal = True
    cv_modal_size = "modal-lg"
    form_class = EventForm
    cv_icon_action = "fa-solid fa-bolt"
    cv_action_label_template_code = _("Quick edit")
    cv_action_short_label_template_code = _("Quick edit")
    cv_header_template_code = _("Quick edit “{{ object }}”")
    cv_paragraph_template_code = _("The same form as the update page, opened in a modal.")
    cv_message_template_code = _("Updated event “{{ object }}”")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        return kwargs

    def cv_form_valid(self, context: dict):
        context["form"].save()


class EventDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_event
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted event “{{ object }}”")


# --------------------------------------------------------------------------- PickerVariant

cv_variant = ViewSet(model=PickerVariant, name="variant", icon_header="fa-solid fa-sliders")


class PickerVariantTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    this_year = tables.Column()
    quarter_hour = tables.Column()
    no_past = tables.Column()
    weekdays_only = tables.Column()
    fixed_times = tables.Column()


class PickerVariantListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_variant
    table_class = PickerVariantTable


class PickerVariantDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_variant
    cv_property_display = [
        {
            "title": _("Picker variant"),
            "icon": "sliders",
            "properties": [
                "name",
                "this_year",
                "quarter_hour",
                "no_past",
                "weekdays_only",
                "inline_calendar",
                "fixed_times",
            ],
        },
    ]


class PickerVariantCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_variant
    form_class = PickerVariantForm
    cv_message_template_code = _("Created picker variant “{{ object }}”")


class PickerVariantUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_variant
    form_class = PickerVariantForm
    cv_message_template_code = _("Updated picker variant “{{ object }}”")


class PickerVariantDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_variant
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted picker variant “{{ object }}”")
