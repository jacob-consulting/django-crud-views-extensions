"""TypeaheadField: a ModelChoiceField whose queryset comes from a registered lookup.

bind(request, **params) is the single source of truth: it sets the queryset save-time validation uses
and hands the widget the signed token the endpoint uses, both from the same lookup and params."""

from django.core.exceptions import ImproperlyConfigured
from django.forms import ModelChoiceField

from .lookups import get_lookup
from .tokens import make_token
from .widgets import TypeaheadBinding, TypeaheadInput


class TypeaheadField(ModelChoiceField):
    widget = TypeaheadInput

    def __init__(self, lookup: str, queryset=None, **kwargs):
        self.lookup_name = lookup
        super().__init__(queryset, **kwargs)

    def bind(self, request, **params) -> "TypeaheadField":
        token = make_token(self.lookup_name, params)  # fails fast on unknown lookups and non-JSON params
        self.queryset = get_lookup(self.lookup_name).get_queryset(request, **params)
        self.widget.binding = TypeaheadBinding(token=token, lookup_name=self.lookup_name, queryset=self.queryset)
        return self

    def clean(self, value):
        if self.queryset is None:
            raise ImproperlyConfigured(
                f"TypeaheadField (lookup {self.lookup_name!r}) is not bound: call field.bind(request, ...)"
            )
        return super().clean(value)
