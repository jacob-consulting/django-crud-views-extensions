# Lookups

A lookup is one registered class per use case. It owns the **allowed set** (including the permission check),
the **search** and the **labels**. The endpoint and the form field both resolve the lookup by name, so the
restriction is written once.

!!! example "Try it live"
    The [Typeahead: thousands of users](https://django-crud-views-extensions-demo.onrender.com/typeahead/team/) example in the live demo shows this in action — log in as
    `admin` / `admin`. See [Live demo](../../getting_started/example_app.md#live-demo) for data resets and wake-up time.

## Autodiscovery

Put lookups in your app's `typeahead.py`. When Django starts, the typeahead app imports the `typeahead.py` of
every installed app (like the admin's `admin.py`), which registers its lookups.

Registering a name twice raises `ImproperlyConfigured`. Using a name that is not registered raises
`LookupNotFound` (a subclass of `ImproperlyConfigured`) as soon as a field is bound to it.

## TypeaheadLookup

```python
from django.core.exceptions import PermissionDenied

from crud_views_widget_typeahead.lookups import TypeaheadLookup, register_lookup

from projects.models import Project


@register_lookup("projects.projects")
class ProjectLookup(TypeaheadLookup):
    search_fields = ["name", "code"]
    ordering = ["name"]

    def get_queryset(self, request, **params):
        if not request.user.has_perm("projects.view_project"):
            raise PermissionDenied
        return Project.objects.filter(archived=False)

    def label(self, obj):
        return f"{obj.code} – {obj.name}"
```

| Attribute | Default | Meaning |
|---|---|---|
| `search_fields` | `[]` | fields searched with `icontains`; **every word** of the search term must match one of them. Searching with no `search_fields` raises `ImproperlyConfigured` |
| `ordering` | `[]` | `order_by()` arguments for the results; empty keeps the queryset's own ordering |
| `max_results` | `10` | results per response; also the page size of the select popup |
| `min_chars` | `2` | shorter terms return an empty result without a query. `0` lets the [select popup](widgets.md#select-popup) list the first page as soon as it opens |
| `login_required` | `True` | anonymous requests get `403 login_required` |

| Method | Meaning |
|---|---|
| `get_queryset(self, request, **params)` | **required.** The allowed set for this request and these params. Raise `PermissionDenied` or `Http404` to refuse (the endpoint answers `403 forbidden` / `404 not_found`) |
| `label(self, obj)` | the text shown for an object; default `str(obj)` |

`params` are the keyword arguments passed to [`bind()`](fields_filters.md). Search results are made
`.distinct()`, so joins in `get_queryset` don't produce duplicates.

Values are always the primary key: `TypeaheadField(to_field_name=...)` raises `ImproperlyConfigured`.

## Users: register_user_lookup

User choices are the common case, so there is a shortcut: decorate a function returning the allowed set.

```python
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from crud_views_widget_typeahead.lookups import register_user_lookup

from projects.models import Project


@register_user_lookup("projects.members")
def members(request, project):
    if not request.user.has_perm("projects.view_project"):
        raise PermissionDenied
    return get_object_or_404(Project, pk=project).members.all()
```

This registers a subclass of `UserLookup`, whose `get_queryset` calls your function. `UserLookup` searches
`first_name`, `last_name` and `username`, orders by last name, first name and username (case-insensitive),
and labels a user with `get_full_name()`, falling back to the username. The decorated function is returned
unchanged.

To change any of that, pass your own `UserLookup` subclass as `base`:

```python
from crud_views_widget_typeahead.lookups import UserLookup, register_user_lookup


class UserWithUsernameLookup(UserLookup):
    """Many users share names: show the username too."""

    def label(self, obj):
        return f"{obj.get_full_name() or obj.get_username()} ({obj.get_username()})"


@register_user_lookup("projects.members_with_username", base=UserWithUsernameLookup)
def members_with_username(request, project): ...
```

!!! warning
    The endpoint must never reveal more than your pages do: check the same permission in `get_queryset`
    that the page using the field checks.
