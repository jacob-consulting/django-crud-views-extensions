"""The one generic typeahead endpoint: GET ?t=<token>&q=<term>[&page=<n>] -> JSON.

Errors are JSON too (fetch() must never receive a login page), and never echo exception messages.
``page`` (1-based, page size = the lookup's max_results) serves the select popup's scroll paging; the text
typeahead never sends it."""

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import Http404, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .lookups import get_lookup
from .tokens import BadToken, read_token


def _error(code: str, status: int) -> JsonResponse:
    return JsonResponse({"error": code}, status=status)


def _page(request) -> int:
    """Lenient on purpose: a bad page cannot widen the result set, so it falls back to page 1."""
    try:
        page = int(request.GET.get("page", "1"))
    except ValueError:
        return 1
    return page if page >= 1 else 1


def _with_pk_tiebreaker(queryset: QuerySet) -> QuerySet:
    """Append pk as the last order key so OFFSET paging neither repeats nor skips rows that tie on the lookup's
    keys. Keeps the queryset's own ordering: explicit order_by, else the model's Meta.ordering."""
    query = queryset.query
    if query.order_by:
        keys = list(query.order_by)
    elif query.default_ordering:
        keys = list(query.get_meta().ordering)
    else:
        keys = []
    return queryset.order_by(*keys, "pk")


@never_cache
@require_GET
def lookup_view(request):
    try:
        name, params = read_token(request.GET.get("t", ""))
    except BadToken:
        return _error("bad_token", 400)
    lookup = get_lookup(name)
    user = getattr(request, "user", None)
    if lookup.login_required and not (user is not None and user.is_authenticated):
        return _error("login_required", 403)
    q = request.GET.get("q", "").strip()
    if len(q) < lookup.min_chars:
        return JsonResponse({"results": [], "count": 0})
    page = _page(request)
    try:
        queryset = _with_pk_tiebreaker(lookup.filter(lookup.get_queryset(request, **params), q))
        count = queryset.count()
        start = (page - 1) * lookup.max_results
        rows = queryset[start : start + lookup.max_results] if start < count else []
        results = [{"value": str(obj.pk), "label": lookup.label(obj)} for obj in rows]
    except PermissionDenied:
        return _error("forbidden", 403)
    except Http404:
        return _error("not_found", 404)
    return JsonResponse({"results": results, "count": count})
