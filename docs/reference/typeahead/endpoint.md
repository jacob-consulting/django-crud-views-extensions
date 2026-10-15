# Endpoint

One generic JSON endpoint serves every lookup. Mount it under any prefix:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    # ...
    path("_typeahead/", include("crud_views_widget_typeahead.urls")),
]
```

The URL name is `crud_views_typeahead:lookup`. The widgets build their URL from it, so you never write it
yourself.

## Request

```
GET <mount>/?t=<token>&q=<term>[&page=<n>]
```

| Parameter | Meaning |
|---|---|
| `t` | the signed token the widget got from [`bind()`](fields_filters.md#bind) |
| `q` | the search term |
| `page` | 1-based page number (select popup only); missing, invalid or below 1 means 1 |

Responses are never cached. Other methods than `GET` get `405`.

## Response

```json
{"results": [{"value": "42", "label": "Ada Lovelace"}, {"value": "7", "label": "Grace Hopper"}], "count": 57}
```

- `value` is the primary key as a string, `label` the lookup's `label(obj)`.
- `count` is the number of all matches, before paging.
- A page holds `max_results` rows; a page past the end returns `"results": []`.
- Results are ordered by the lookup's `ordering` (else the queryset's own `order_by()`, else the model's `Meta.ordering`) with the primary key as the
  final tiebreaker, so pages never repeat or skip rows.
- Terms shorter than `min_chars` return `{"results": [], "count": 0}` without a database query.

## Errors

Errors are JSON too — `fetch()` must never receive a login page — and never echo exception messages. The one
exception is `405`, Django's standard empty response for a wrong method.

| Status | Body | When |
|---|---|---|
| 400 | `{"error": "bad_token"}` | bad signature, wrong payload shape, or a lookup that is no longer registered |
| 403 | `{"error": "login_required"}` | the lookup has `login_required = True` and the user is anonymous |
| 403 | `{"error": "forbidden"}` | the lookup's `get_queryset` raised `PermissionDenied` |
| 404 | `{"error": "not_found"}` | the lookup's `get_queryset` raised `Http404` |
| 405 | — | not a `GET` request |
