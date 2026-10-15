import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import CrispyDeleteForm, CrispyViewMixin
from crud_views.lib.table import LinkChildColumn, LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableFilterMixin,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from project.views import BreadcrumbMixin

from typeahead.forms import TaskFilter, TaskFilterFormHelper, TaskForm
from typeahead.models import Task, Team

# --------------------------------------------------------------------------- Team

cv_team = ViewSet(model=Team, name="team", icon_header="fa-solid fa-people-group")


class TeamTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    members = tables.Column(verbose_name=_("members"), accessor="pk", orderable=False)
    tasks = LinkChildColumn(name="task", verbose_name=_("tasks"))

    def render_members(self, record):
        return record.members.count()


class TeamListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_team
    table_class = TeamTable
    cv_list_actions = ["detail"]


class TeamDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_team
    cv_property_display = [{"title": _("Team"), "icon": "people-group", "properties": ["name"]}]


# --------------------------------------------------------------------------- Task (child of Team)

cv_task = ViewSet(model=Task, name="task", parent=ParentViewSet(name="team"), icon_header="fa-solid fa-list-check")


class TaskTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    assignee = tables.Column()


class TaskListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_task
    table_class = TaskTable
    filterset_class = TaskFilter
    formhelper_class = TaskFilterFormHelper
    cv_list_actions = ["detail", "update", "quick_assign", "delete"]


class TaskDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_task
    cv_property_display = [{"title": _("Task"), "icon": "list-check", "properties": ["title", "team", "assignee"]}]


class TaskCreateView(
    BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_task
    form_class = TaskForm
    cv_message_template_code = _("Created task “{{ object }}”")


class TaskUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_task
    form_class = TaskForm
    cv_message_template_code = _("Updated task “{{ object }}”")


class TaskQuickAssignView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    """The same TaskForm in a crud_views modal: typeahead.js re-initialises on cv:modal:loaded."""

    cv_viewset = cv_task
    cv_key = "quick_assign"
    cv_path = "quick-assign"
    cv_permission = "change"
    cv_modal = True
    cv_modal_size = "modal-lg"
    form_class = TaskForm
    cv_icon_action = "fa-solid fa-user-check"
    cv_action_label_template_code = _("Quick assign")
    cv_action_short_label_template_code = _("Quick assign")
    cv_header_template_code = _("Assign “{{ object }}”")
    cv_paragraph_template_code = _("The same form as the update page, opened in a modal.")
    cv_message_template_code = _("Updated task “{{ object }}”")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        return kwargs

    def cv_form_valid(self, context: dict):
        context["form"].save()


class TaskDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_task
    form_class = CrispyDeleteForm
    cv_modal = True
    cv_message_template_code = _("Deleted task “{{ object }}”")
