"""Typeahead lookups: one registered class per use case owns the allowed set (including the permission
check), the search and the labels. The endpoint and TypeaheadField both resolve lookups by name, so the
restriction is written once."""

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, QuerySet
from django.db.models.functions import Lower


class LookupNotFound(ImproperlyConfigured):
    pass


_registry: dict[str, "TypeaheadLookup"] = {}


class TypeaheadLookup:
    search_fields: list[str] = []  # icontains; every word must match some field
    ordering: list = []
    max_results = 10
    min_chars = 2
    login_required = True

    def get_queryset(self, request, **params) -> QuerySet:
        """The allowed set for this request and params. Raise PermissionDenied / Http404 to refuse."""
        raise NotImplementedError(f"{type(self).__name__} must implement get_queryset(request, **params)")

    def label(self, obj) -> str:
        return str(obj)

    def filter(self, queryset: QuerySet, q: str) -> QuerySet:
        words = q.split()
        if words and not self.search_fields:
            raise ImproperlyConfigured(f"{type(self).__name__}.search_fields is empty, cannot search for {q!r}")
        for word in words:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f"{field}__icontains": word})
            queryset = queryset.filter(condition)
        queryset = queryset.distinct()
        if self.ordering:
            queryset = queryset.order_by(*self.ordering)
        return queryset


class UserLookup(TypeaheadLookup):
    search_fields = ["first_name", "last_name", "username"]
    ordering = [Lower("last_name"), Lower("first_name"), Lower("username")]

    def label(self, obj) -> str:
        return obj.get_full_name() or obj.get_username()


def register_lookup(name: str):
    """Class decorator: register an instance of the decorated TypeaheadLookup subclass under ``name``."""

    def decorator(cls):
        if name in _registry:
            raise ImproperlyConfigured(f"typeahead lookup {name!r} is already registered")
        _registry[name] = cls()
        return cls

    return decorator


def register_user_lookup(name: str, base: type[TypeaheadLookup] = UserLookup):
    """Function decorator: register ``func(request, **params) -> QuerySet`` as the get_queryset of a ``base``
    subclass. The function itself is returned unchanged."""

    def decorator(func):
        def get_queryset(self, request, **params):
            return func(request, **params)

        cls = type(f"{func.__name__}_lookup", (base,), {"get_queryset": get_queryset, "__module__": func.__module__})
        register_lookup(name)(cls)
        return func

    return decorator


def get_lookup(name: str) -> TypeaheadLookup:
    try:
        return _registry[name]
    except KeyError:
        raise LookupNotFound(f"typeahead lookup {name!r} is not registered") from None
