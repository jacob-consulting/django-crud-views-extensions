"""Signed widget tokens: the browser carries {lookup, params} but cannot change them.

No expiry on purpose: the endpoint re-checks permission on every request via the lookup's
get_queryset(request, **params), so a form left open overnight keeps working and a leaked token grants
nothing beyond what the requesting user may see anyway."""

import json

from django.core import signing
from django.core.exceptions import ImproperlyConfigured

from .lookups import LookupNotFound, get_lookup

SALT = "crud_views.typeahead"


class BadToken(Exception):
    """Bad signature, wrong payload shape or unknown lookup."""


def make_token(name: str, params: dict) -> str:
    get_lookup(name)  # LookupNotFound for unregistered names, at bind time
    try:
        serialisable = isinstance(params, dict) and json.loads(json.dumps(params)) == params
    except (TypeError, ValueError):
        serialisable = False
    if not serialisable:
        raise ImproperlyConfigured(
            f"typeahead params for {name!r} must be a dict of JSON values (pass UUIDs, dates and model instances "
            f"as str): {params!r}"
        )
    return signing.dumps({"l": name, "p": params}, salt=SALT, compress=True)


def read_token(token: str) -> tuple[str, dict]:
    try:
        data = signing.loads(token, salt=SALT)
    except signing.BadSignature as e:
        raise BadToken("bad signature") from e
    if not isinstance(data, dict) or not isinstance(data.get("l"), str) or not isinstance(data.get("p"), dict):
        raise BadToken("wrong shape")
    try:
        get_lookup(data["l"])
    except LookupNotFound as e:
        raise BadToken("unknown lookup") from e
    return data["l"], data["p"]
