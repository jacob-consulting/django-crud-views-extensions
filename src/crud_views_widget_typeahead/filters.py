"""django-filter integration. Bind in the FilterSet's __init__:

    self.filters["user"].bind(self.request, team=str(team.pk))

Filter.field is cached and the filter form is built from it later, so the binding carries over.
URLs stay ?user=<pk>."""

import django_filters

from .fields import TypeaheadField
from .widgets import TypeaheadInput


class TypeaheadFilter(django_filters.ModelChoiceFilter):
    field_class = TypeaheadField

    def __init__(self, *args, lookup: str, **kwargs):
        kwargs.setdefault("widget", TypeaheadInput(submit_on_clear=True))
        kwargs["lookup"] = lookup  # passed through to TypeaheadField via Filter.extra
        super().__init__(*args, **kwargs)

    def bind(self, request, **params) -> "TypeaheadFilter":
        self.field.bind(request, **params)
        return self
