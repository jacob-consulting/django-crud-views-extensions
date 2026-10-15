from dataclasses import dataclass

from django.conf import settings

DEFAULT_TEMPLATE = "crud_views_widget_typeahead/typeahead.html"


@dataclass(frozen=True)
class TypeaheadConfig:
    emit: bool = True
    template: str = DEFAULT_TEMPLATE
    debounce_ms: int = 250


def get_config() -> TypeaheadConfig:
    raw = getattr(settings, "CRUD_VIEWS_TYPEAHEAD", {}) or {}
    return TypeaheadConfig(
        emit=raw.get("EMIT", True),
        template=raw.get("TEMPLATE", DEFAULT_TEMPLATE),
        debounce_ms=int(raw.get("DEBOUNCE_MS", 250)),
    )
