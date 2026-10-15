import django_filters
from crispy_forms.layout import Layout, Row
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import Column6, CrispyModelForm
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.filters import TypeaheadFilter
from crud_views_widget_typeahead.widgets import TypeaheadSelect

from typeahead.models import Task


class TaskForm(CrispyModelForm):
    """The assignee choices are the team's members: bind() sets the queryset (validation) and the token
    (suggestions) from the same lookup and params."""

    assignee = TypeaheadField(lookup="typeahead.team_members", required=False, label=_("assignee"))

    class Meta:
        model = Task
        fields = ["title", "assignee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        team = self.cv_view.cv_get_parent_object()  # the team from the URL
        self.fields["assignee"].bind(self.cv_view.request, team=str(team.pk))

    def get_layout_fields(self):
        return [Row(Column6("title"), Column6("assignee"))]


class TaskPickForm(CrispyModelForm):
    """The select popup: browse the team's members on open, scroll to load more, or search."""

    assignee = TypeaheadField(
        lookup="typeahead.team_members_browse", widget=TypeaheadSelect(), required=False, label=_("assignee")
    )

    class Meta:
        model = Task
        fields = ["assignee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        team = self.cv_view.cv_get_parent_object()
        self.fields["assignee"].bind(self.cv_view.request, team=str(team.pk))

    def get_layout_fields(self):
        return [Row(Column6("assignee"))]


class TaskFilter(django_filters.FilterSet):
    """Filter by any team member with the select popup — the case the project this widget replaces solved with
    dal + Select2. min_chars stays 2 here, so the popup asks for two characters before searching."""

    assignee = TypeaheadFilter(
        lookup="typeahead.any_member", widget=TypeaheadSelect(submit_on_clear=True), label=_("assignee")
    )

    # crud_views' list template tests {% if view.filterset_class %}, and Django templates call callables:
    # without this the class would be instantiated there with request=None, and bind() would run without a user
    do_not_call_in_templates = True

    class Meta:
        model = Task
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["assignee"].bind(self.request)


class TaskFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column6("assignee")))
