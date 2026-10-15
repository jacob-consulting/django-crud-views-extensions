"""TypeaheadField: a ModelChoiceField whose queryset comes from a registered lookup.

bind(request, **params) is the single source of truth: it sets the queryset save-time validation uses
and hands the widget the signed token the endpoint uses, both from the same lookup and params."""

from django.core.exceptions import ImproperlyConfigured, MultipleObjectsReturned
from django.forms import ModelChoiceField

from .lookups import get_lookup
from .tokens import make_token
from .widgets import TypeaheadBinding, TypeaheadInput


class TypeaheadField(ModelChoiceField):
    widget = TypeaheadInput

    def __init__(self, lookup: str, queryset=None, **kwargs):
        if kwargs.get("to_field_name"):
            # the hidden input, the endpoint's "value" and validation all key on the pk
            raise ImproperlyConfigured("TypeaheadField does not support to_field_name: values are always the pk")
        self.lookup_name = lookup
        super().__init__(queryset, **kwargs)

    def bind(self, request, **params) -> "TypeaheadField":
        token = make_token(self.lookup_name, params)  # fails fast on unknown lookups and non-JSON params
        self.queryset = get_lookup(self.lookup_name).get_queryset(request, **params)
        self.widget.binding = TypeaheadBinding(token=token, lookup_name=self.lookup_name, queryset=self.queryset)
        return self

    def to_python(self, value):
        try:
            return super().to_python(value)
        except MultipleObjectsReturned:
            # join artifacts of an un-distinct lookup queryset: the pk is unique, so any row is the object
            return self.queryset.filter(pk=value).first()

    def clean(self, value):
        if self.queryset is None:
            raise ImproperlyConfigured(
                f"TypeaheadField (lookup {self.lookup_name!r}) is not bound: call field.bind(request, ...)"
            )
        return super().clean(value)
