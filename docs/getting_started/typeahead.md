# Your first typeahead

This walkthrough builds what the [example app](example_app.md) shows: tasks belong to a team, and a task's
assignee must be one of the team's members — of which there may be thousands.

!!! example "Try it live"
    The [Typeahead: thousands of users](https://django-crud-views-extensions-demo.onrender.com/typeahead/team/) example in the live demo shows this in action — log in as
    `admin` / `admin`. See [Live demo](../getting_started/example_app.md#live-demo) for data resets and wake-up time.

## 1. Mount the endpoint

```python
# urls.py
urlpatterns += [path("_typeahead/", include("crud_views_widget_typeahead.urls"))]
```

## 2. Write a lookup

A lookup defines the allowed set, including the permission check. Put it in your app's `typeahead.py`; it is
imported automatically at startup.

```python
# teams/typeahead.py
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from crud_views_widget_typeahead.lookups import register_user_lookup

from teams.models import Team


@register_user_lookup("teams.members")
def team_members(request, team):
    # the endpoint must never reveal more than the pages do: same permission as the team pages
    if not request.user.has_perm("teams.view_team"):
        raise PermissionDenied
    return get_object_or_404(Team, pk=team).members.all()
```

`register_user_lookup` already knows how to search and label users. For other models, see
[Lookups](../reference/typeahead/lookups.md).

## 3. Bind a form field

```python
# teams/forms.py
from crud_views.lib.crispy import CrispyModelForm
from crud_views_widget_typeahead.fields import TypeaheadField

from teams.models import Task


class TaskForm(CrispyModelForm):
    assignee = TypeaheadField(lookup="teams.members", required=False)

    class Meta:
        model = Task
        fields = ["title", "assignee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        team = self.cv_view.cv_get_parent_object()  # the team from the URL
        self.fields["assignee"].bind(self.cv_view.request, team=str(team.pk))
```

`bind()` sets both the suggestions and the save-time validation from the same lookup and params. Params must
be JSON values, hence `str(team.pk)`. See [Fields & filters](../reference/typeahead/fields_filters.md).

## 4. Bind a filter

A filter over all tasks needs a lookup over every team member. Add it to `typeahead.py`:

```python
# teams/typeahead.py (continued)
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from crud_views_widget_typeahead.lookups import register_user_lookup


@register_user_lookup("teams.any_member")
def any_member(request):
    if not request.user.has_perm("teams.view_team"):
        raise PermissionDenied
    return get_user_model().objects.filter(teams__isnull=False).distinct()
```

and bind it in the FilterSet:

```python
# teams/filters.py
import django_filters

from crud_views_widget_typeahead.filters import TypeaheadFilter

from teams.models import Task


class TaskFilter(django_filters.FilterSet):
    assignee = TypeaheadFilter(lookup="teams.any_member")

    # crud_views' list template evaluates view.filterset_class: don't let it instantiate this without a request
    do_not_call_in_templates = True

    class Meta:
        model = Task
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["assignee"].bind(self.request)
```

## 5. Try the select popup

For browsing instead of typing, swap the widget:

```python
from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.widgets import TypeaheadSelect

assignee = TypeaheadField(lookup="teams.members", widget=TypeaheadSelect(), required=False)
```

With `min_chars = 0` on the lookup, the popup lists the first members as soon as it opens and loads more on
scroll. See [Widgets](../reference/typeahead/widgets.md).
