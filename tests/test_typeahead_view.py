import json

import pytest
from django.contrib.auth.models import AnonymousUser, Group, User
from django.test import RequestFactory
from django.urls import reverse

from crud_views_widget_typeahead.tokens import make_token
from crud_views_widget_typeahead.views import lookup_view

rf = RequestFactory()


def call(token, q="", user=None, method="get"):
    """Status and decoded JSON body of the endpoint; RequestFactory keeps auth query-free."""
    params = {"q": q} if token is None else {"t": token, "q": q}
    request = getattr(rf, method)("/typeahead/", params)
    request.user = user if user is not None else AnonymousUser()
    response = lookup_view(request)
    return response.status_code, (json.loads(response.content) if response.content else None)


@pytest.fixture
def team(db):
    group = Group.objects.create(name="team")
    member = User.objects.create_user("mmember", first_name="Mia", last_name="Member")
    User.objects.create_user("ooutsider", first_name="Mia", last_name="Outsider")
    group.user_set.add(member)
    return {"group": group, "member": member, "viewer": User.objects.create_user("viewer")}


def token_for(group):
    return make_token("testapp.group_members", {"group": str(group.pk)})


def test_results_are_scoped_to_the_lookup(team):
    status, body = call(token_for(team["group"]), "mia", team["viewer"])
    assert status == 200
    assert body == {"results": [{"value": str(team["member"].pk), "label": "Mia Member"}], "count": 1}


def test_count_is_taken_before_slicing(db):
    for name in ["alpha1", "alpha2", "alpha3", "beta"]:
        Group.objects.create(name=name)
    status, body = call(make_token("testapp.groups", {}), "alpha")
    assert status == 200
    assert body["count"] == 3
    assert [r["label"] for r in body["results"]] == ["alpha1", "alpha2"]  # max_results = 2, ordered by name


def test_short_term_runs_no_query(team, django_assert_num_queries):
    token = token_for(team["group"])
    with django_assert_num_queries(0):
        assert call(token, "m", team["viewer"]) == (200, {"results": [], "count": 0})


def test_whitespace_only_term_is_empty(team, django_assert_num_queries):
    token = token_for(team["group"])
    with django_assert_num_queries(0):
        assert call(token, "      ", team["viewer"]) == (200, {"results": [], "count": 0})


def test_term_is_stripped(team):
    status, body = call(token_for(team["group"]), "  mia  ", team["viewer"])
    assert body["count"] == 1


@pytest.mark.parametrize("token", [None, "", "garbage"])
def test_bad_token(db, token):
    assert call(token, "mia") == (400, {"error": "bad_token"})


def test_anonymous_gets_json_403_not_a_redirect(team):
    assert call(token_for(team["group"]), "mia") == (403, {"error": "login_required"})


def test_lookup_without_login_requirement_serves_anonymous(db):
    Group.objects.create(name="alpha")
    status, body = call(make_token("testapp.groups", {}), "alp")
    assert (status, body["count"]) == (200, 1)


def test_permission_denied_from_lookup(team):
    token = make_token("testapp.group_members", {"group": "forbidden"})
    assert call(token, "mia", team["viewer"]) == (403, {"error": "forbidden"})


def test_http404_from_lookup(team):
    token = make_token("testapp.group_members", {"group": "999999"})
    assert call(token, "mia", team["viewer"]) == (404, {"error": "not_found"})


def test_post_is_not_allowed(team):
    status, _ = call(token_for(team["group"]), "mia", team["viewer"], method="post")
    assert status == 405


def test_response_is_never_cached(team):
    request = rf.get("/typeahead/", {"t": token_for(team["group"]), "q": "mia"})
    request.user = team["viewer"]
    assert "no-store" in lookup_view(request)["Cache-Control"]


def test_url_is_routed(db, client):
    url = reverse("crud_views_typeahead:lookup")
    assert url == "/typeahead/"
    assert client.get(url, {"t": "garbage"}).status_code == 400
