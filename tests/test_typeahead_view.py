import json

import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.db.models.functions import Lower
from django.test import RequestFactory
from django.urls import reverse

from crud_views_widget_typeahead.tokens import make_token
from crud_views_widget_typeahead.views import _with_pk_tiebreaker, lookup_view

rf = RequestFactory()


def call(token, q="", user=None, method="get", **extra):
    """Status and decoded JSON body of the endpoint; RequestFactory keeps auth query-free."""
    params = {"q": q} if token is None else {"t": token, "q": q}
    params.update(extra)
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


# --------------------------------------------------------------------------- paging


@pytest.fixture
def alphas(db):
    return [Group.objects.create(name=f"alpha{i}") for i in range(1, 6)]  # 5 matches, max_results = 2


def labels(body):
    return [r["label"] for r in body["results"]]


def test_page_one_equals_the_unpaged_response(alphas):
    token = make_token("testapp.groups", {})
    assert call(token, "alpha", page="1") == call(token, "alpha")


def test_pages_continue_without_overlap(alphas):
    token = make_token("testapp.groups", {})
    pages = [call(token, "alpha", page=str(n))[1] for n in (1, 2, 3)]
    assert [labels(p) for p in pages] == [["alpha1", "alpha2"], ["alpha3", "alpha4"], ["alpha5"]]
    assert {p["count"] for p in pages} == {5}


def test_page_past_the_end_is_empty_with_count(alphas):
    assert call(make_token("testapp.groups", {}), "alpha", page="4") == (200, {"results": [], "count": 5})


def test_page_far_past_the_end_runs_no_slice_query(alphas, django_assert_num_queries):
    token = make_token("testapp.groups", {})
    with django_assert_num_queries(1):  # the count only: an OFFSET this large would overflow the database
        assert call(token, "alpha", page="1" + "0" * 30) == (200, {"results": [], "count": 5})


@pytest.mark.parametrize("page", ["", "0", "-3", "1.5", "abc", " "])
def test_garbage_page_means_page_one(alphas, page):
    token = make_token("testapp.groups", {})
    assert call(token, "alpha", page=page) == call(token, "alpha")


def test_min_chars_is_enforced_on_every_page(team, django_assert_num_queries):
    token = token_for(team["group"])
    with django_assert_num_queries(0):
        assert call(token, "m", team["viewer"], page="2") == (200, {"results": [], "count": 0})


def test_permission_errors_on_every_page(db):
    token = make_token("testapp.group_members", {"group": "forbidden"})
    assert call(token, "mia", User.objects.create_user("v"), page="3") == (403, {"error": "forbidden"})


def test_browse_lookup_pages_through_everything_with_an_empty_query(alphas):
    token = make_token("testapp.groups_browse", {})
    seen = []
    for n in (1, 2, 3):
        status, body = call(token, "   ", page=str(n))
        assert (status, body["count"]) == (200, 5)
        seen += labels(body)
    assert seen == ["alpha1", "alpha2", "alpha3", "alpha4", "alpha5"]


def test_paging_a_scope_of_identical_names_neither_repeats_nor_skips_rows(db):
    # identical display names; the order is settled by username here, the pk tiebreaker is pinned by the
    # _with_pk_tiebreaker tests below
    group = Group.objects.create(name="twins")
    users = [User.objects.create_user(f"same{i:02d}", first_name="Sam", last_name="Same") for i in range(25)]
    group.user_set.add(*users)
    token = make_token("testapp.group_members", {"group": str(group.pk)})  # UserLookup: max_results = 10
    viewer = User.objects.create_user("viewer")
    pks = []
    for n in (1, 2, 3):
        pks += [r["value"] for r in call(token, "sam same", viewer, page=str(n))[1]["results"]]
    assert sorted(pks) == sorted(str(u.pk) for u in users)


# --------------------------------------------------------------------------- total ordering


def test_tiebreaker_on_an_unordered_queryset(db):
    assert _with_pk_tiebreaker(Group.objects.all()).query.order_by == ("pk",)


def test_tiebreaker_keeps_explicit_ordering(db):
    assert _with_pk_tiebreaker(User.objects.order_by("last_name", "-username")).query.order_by == (
        "last_name",
        "-username",
        "pk",
    )


def test_tiebreaker_keeps_expression_ordering(db):
    order_by = _with_pk_tiebreaker(User.objects.order_by(Lower("last_name"))).query.order_by
    assert len(order_by) == 2
    assert order_by[-1] == "pk"


def test_tiebreaker_keeps_meta_ordering(db):
    assert Permission._meta.ordering  # the fixture this test relies on
    assert _with_pk_tiebreaker(Permission.objects.all()).query.order_by == (*Permission._meta.ordering, "pk")
