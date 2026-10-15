"""Typeahead widgets: TypeaheadInput (text input) and TypeaheadSelect (select-style popup).

Renders a visible text input without a name (the label), a hidden input carrying the name and the pk,
and data attributes for the frontend. No Media class on purpose: typeahead.js/.css are page-global via
cv_js/cv_css. The template (and with it the whole frontend) is swappable: see the README's skin contract.
"""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from django import forms
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.urls import reverse
from django.utils.translation import gettext, ngettext

from .conf import get_config
from .lookups import get_lookup


@dataclass(frozen=True)
class TypeaheadBinding:
    """What TypeaheadField.bind() hands the widget. Plain data without a reference back to the field:
    Widget.__deepcopy__ is shallow, so copies may share it, and re-binding a copy replaces only its own."""

    token: str
    lookup_name: str
    queryset: Any


def _i18n(min_chars: int) -> dict:
    return {
        "hint": ngettext(
            "Type at least %(count)d character, then choose with the arrow keys and Enter.",
            "Type at least %(count)d characters, then choose with the arrow keys and Enter.",
            min_chars,
        )
        % {"count": min_chars},
        "more": gettext("{n} more results – keep typing"),
        "none": gettext("No results"),
        "count": gettext("{n} results"),
        "error": gettext("Search failed"),
        "clear": gettext("Clear selection"),
        "listbox": gettext("Suggestions"),
    }


class TypeaheadInput(forms.Widget):
    def __init__(self, attrs=None, submit_on_clear: bool = False, template_name: str | None = None):
        super().__init__(attrs)
        self.submit_on_clear = submit_on_clear
        self._template_name = template_name
        self.binding: TypeaheadBinding | None = None

    @property
    def template_name(self) -> str:
        return self._template_name or get_config().template

    @template_name.setter
    def template_name(self, value: str | None):
        self._template_name = value

    def use_required_attribute(self, initial) -> bool:
        return False  # a required visible input would accept typed text without a pk

    def resolve(self, value):
        """The allowed object for a pk (or instance), or None for empty, garbage or out-of-scope values."""
        if self.binding is None or value in (None, ""):
            return None
        value = getattr(value, "pk", value)
        try:
            return self.binding.queryset.filter(pk=value).first()
        except (ValueError, TypeError, ValidationError):
            return None

    def get_context(self, name, value, attrs):
        if self.binding is None:
            raise ImproperlyConfigured(
                f"typeahead widget for {name!r} is not bound: call field.bind(request, ...) before rendering"
            )
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        lookup = get_lookup(self.binding.lookup_name)
        obj = self.resolve(value)
        text_attrs = widget["attrs"]
        text_id = text_attrs.get("id") or f"id_{name}"
        hint_id = f"{text_id}_hint"
        described_by = str(text_attrs.get("aria-describedby") or "").split()
        classes = str(text_attrs.get("class") or "").split()
        text_attrs.update(
            {
                "id": text_id,
                "class": " ".join(dict.fromkeys([*classes, "form-control"])),
                "autocomplete": "off",
                "role": "combobox",
                "aria-autocomplete": "list",
                "aria-expanded": "false",
                "aria-controls": f"{text_id}_listbox",
                # merge, never replace: Django adds <id>_helptext / <id>_error here
                "aria-describedby": " ".join(dict.fromkeys([*described_by, hint_id])),
            }
        )
        widget["typeahead"] = {
            "url": f"{reverse('crud_views_typeahead:lookup')}?{urlencode({'t': self.binding.token})}",
            "label": lookup.label(obj) if obj is not None else "",
            "value": str(obj.pk) if obj is not None else "",
            "hidden_name": name,
            "hidden_id": f"{text_id}_value",
            "listbox_id": f"{text_id}_listbox",
            "hint_id": hint_id,
            "min_chars": lookup.min_chars,
            "debounce": get_config().debounce_ms,
            "submit_on_clear": self.submit_on_clear,
            "i18n": _i18n(lookup.min_chars),
        }
        return context


def _select_i18n(min_chars: int) -> dict:
    return {
        "hint": gettext("Open with Enter or the arrow keys, type to search, choose with Enter."),
        "placeholder": gettext("Select…"),
        "search": gettext("Search"),
        "loading": gettext("Loading…"),
        "type_more": ngettext(
            "Type at least %(count)d character.",
            "Type at least %(count)d characters.",
            min_chars,
        )
        % {"count": min_chars},
    }


class TypeaheadSelect(TypeaheadInput):
    """Select-style popup: a trigger button that looks like a Bootstrap <select>, and a popup with a search field
    and a server-paged list. Same binding, hidden-input contract and endpoint as TypeaheadInput; its own template
    (SELECT_TEMPLATE) and its own frontend (typeahead-select.js, asset bundle "typeahead_select")."""

    @property
    def template_name(self) -> str:
        return self._template_name or get_config().select_template

    @template_name.setter
    def template_name(self, value: str | None):
        self._template_name = value

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        typeahead = widget["typeahead"]
        button = widget["attrs"]  # widget.attrs land on the trigger button
        text_id = button["id"]
        for key in ("role", "aria-autocomplete", "autocomplete"):  # text-input semantics, not a button's
            button.pop(key, None)
        classes = [c for c in str(button.get("class") or "").split() if c != "form-control"]
        button.update(
            {
                "class": " ".join(dict.fromkeys([*classes, "form-select", "text-start"])),
                "aria-haspopup": "listbox",
                "aria-expanded": "false",
                "aria-controls": f"{text_id}_popup",
                # <label for> would replace the button's content as its name: self-reference yields the label text,
                # then the value/placeholder span (APG select-only combobox pattern)
                "aria-labelledby": f"{text_id} {text_id}_label",
            }
        )
        lookup = get_lookup(self.binding.lookup_name)
        typeahead.update(
            {
                "popup_id": f"{text_id}_popup",
                "label_id": f"{text_id}_label",
                "search_id": f"{text_id}_search",
                "page_size": lookup.max_results,
                "i18n": {**typeahead["i18n"], **_select_i18n(lookup.min_chars)},
            }
        )
        return context
