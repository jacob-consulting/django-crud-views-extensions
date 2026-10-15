"""The one generic typeahead endpoint: GET ?t=<token>&q=<term> -> JSON.

Errors are JSON too (fetch() must never receive a login page), and never echo exception messages."""

from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .lookups import get_lookup
from .tokens import BadToken, read_token


def _error(code: str, status: int) -> JsonResponse:
    return JsonResponse({"error": code}, status=status)


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
    try:
        queryset = lookup.filter(lookup.get_queryset(request, **params), q)
        count = queryset.count()
        results = [{"value": lookup.value(obj), "label": lookup.label(obj)} for obj in queryset[: lookup.max_results]]
    except PermissionDenied:
        return _error("forbidden", 403)
    except Http404:
        return _error("not_found", 404)
    return JsonResponse({"results": results, "count": count})
