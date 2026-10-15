# Fields & filters

```python
import django_filters
from django import forms

from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.filters import TypeaheadFilter


class TaskForm(forms.ModelForm):
    assignee = TypeaheadField(lookup="projects.members")

    def __init__(self, *args, request, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].bind(request, project=str(project.pk))


class TaskFilter(django_filters.FilterSet):
    assignee = TypeaheadFilter(lookup="projects.members")

    do_not_call_in_templates = True  # see below

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["assignee"].bind(self.request, project=str(self.project.pk))
```

`TypeaheadField` is a `ModelChoiceField` whose queryset comes from a [lookup](lookups.md);
`TypeaheadFilter` is a django-filter `ModelChoiceFilter` using it. Filter URLs stay `?assignee=<pk>`.

## bind()

`bind(request, **params)` is the single source of truth for a field. From the same lookup and params it

- sets the field's queryset to `lookup.get_queryset(request, **params)`, which save-time validation uses, and
- signs `{lookup, params}` into a token for the widget, which the [endpoint](endpoint.md) uses.

So the suggestions and the validation are always the same set. `bind()` returns the field (or filter).

Params must be a dict of JSON values: pass UUIDs, dates and model instances as `str`
(`project=str(project.pk)`). Anything else raises `ImproperlyConfigured` when binding.

A field that was never bound raises `ImproperlyConfigured` when it renders or validates.

## With crud_views forms

crud_views' `CrispyModelForm` has the view at `self.cv_view`, so take the request from there:

```python
from crud_views.lib.crispy import CrispyModelForm
from crud_views_widget_typeahead.fields import TypeaheadField


class TaskForm(CrispyModelForm):
    assignee = TypeaheadField(lookup="typeahead.team_members", required=False)

    class Meta:
        model = Task
        fields = ["title", "assignee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        team = self.cv_view.cv_get_parent_object()  # the team from the URL
        self.fields["assignee"].bind(self.cv_view.request, team=str(team.pk))
```

## Filters

Bind in the FilterSet's `__init__`. `TypeaheadFilter` uses `TypeaheadInput(submit_on_clear=True)` by default,
so clearing the filter submits the filter form; pass `widget=` to change that.

!!! warning "crud_views list views: `do_not_call_in_templates`"
    The crud_views list template tests `{% if view.filterset_class %}`, and Django templates call callables —
    so the FilterSet class is instantiated there, without a request. Set `do_not_call_in_templates = True` on
    every FilterSet that binds in `__init__`.

## Duplicate rows

If a lookup's queryset is not distinct (e.g. it follows a many-to-many relation), the same object can appear
in several rows. The field tolerates that: the primary key is unique, so any row is the object.
