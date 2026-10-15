# Security

## Signed tokens

`bind()` puts the lookup name and the params into a token:

```python
signing.dumps({"l": lookup_name, "p": params}, salt="crud_views.typeahead", compress=True)
```

The browser sends the token with every search. It can read it but not change it: the signature (Django's
`SECRET_KEY`, salt `crud_views.typeahead`) makes the [endpoint](endpoint.md) reject any modified token with
`400 bad_token`. So a user cannot widen the search to another lookup or other params.

Tokens are signed, **not encrypted**: params are visible in the page source. Don't put secrets in them.
Rotating `SECRET_KEY` invalidates the tokens in forms that are already open.

## No expiry

Tokens never expire, on purpose. The endpoint re-checks permission on **every** request by calling the
lookup's `get_queryset(request, **params)` with the current user. Therefore

- a form left open overnight keeps working, and
- a leaked token grants nothing beyond what the requesting user may see anyway.

## Validation uses the same set

The field's queryset comes from the same `bind()` call as the token. A pk outside the allowed set — for
example a hand-edited hidden input — fails form validation like any invalid `ModelChoiceField` choice.

## JSON errors

Refusals are JSON with a status code (`403 login_required`, `403 forbidden`, `404 not_found`), never a redirect
to the login page, and never contain exception messages.
