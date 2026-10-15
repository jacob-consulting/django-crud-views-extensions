import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ImproperlyConfigured

from crud_views_widget_typeahead import lookups
from crud_views_widget_typeahead.lookups import (
    LookupNotFound,
    TypeaheadLookup,
    UserLookup,
    get_lookup,
    register_lookup,
    register_user_lookup,
)


@pytest.fixture
def registry():
    """Undo registrations made by a test."""
    saved = dict(lookups._registry)
    yield
    lookups._registry.clear()
    lookups._registry.update(saved)


@pytest.fixture
def people(db):
    make = User.objects.create_user
    return {
        "anna": make("amueller", first_name="Anna", last_name="Müller"),
        "andreas": make("aschmidt", first_name="Andreas", last_name="Schmidt"),
        "bert": make("bmueller", first_name="Bert", last_name="Müller"),
        "plain": make("zz_plain"),
    }


def search(q, lookup=None):
    return list((lookup or UserLookup()).filter(User.objects.all(), q))


def test_every_word_must_match(people):
    assert search("mül an") == [people["anna"]]


def test_words_may_match_different_fields(people):
    assert search("bert bmue") == [people["bert"]]


def test_case_insensitive(people):
    assert search("SCHMIDT") == [people["andreas"]]


def test_empty_term_returns_all_ordered(people):
    # Lower(last_name), Lower(first_name), Lower(username): the user without names sorts first
    assert search("   ") == [people["plain"], people["anna"], people["bert"], people["andreas"]]


def test_like_wildcards_are_literal(people):
    assert search("%") == []
    assert search("_") == [people["plain"]]


def test_results_are_distinct(people):
    people["anna"].groups.add(Group.objects.create(name="g1"), Group.objects.create(name="g2"))

    class ByGroup(UserLookup):
        search_fields = ["groups__name"]

    assert search("g", ByGroup()) == [people["anna"]]


def test_empty_search_fields_with_term_raises(db):
    with pytest.raises(ImproperlyConfigured):
        TypeaheadLookup().filter(User.objects.none(), "x")


def test_empty_search_fields_without_term_is_fine(db):
    assert list(TypeaheadLookup().filter(User.objects.none(), "")) == []


def test_get_queryset_must_be_implemented():
    with pytest.raises(NotImplementedError):
        TypeaheadLookup().get_queryset(None)


def test_user_label(people):
    assert UserLookup().label(people["anna"]) == "Anna Müller"
    assert UserLookup().label(people["plain"]) == "zz_plain"


def test_default_label(db):
    group = Group.objects.create(name="x")
    assert TypeaheadLookup().label(group) == "x"


def test_defaults():
    lookup = TypeaheadLookup()
    assert (lookup.max_results, lookup.min_chars, lookup.login_required) == (10, 2, True)


def test_register_and_get(registry):
    @register_lookup("t.groups")
    class L(TypeaheadLookup):
        search_fields = ["name"]

    assert isinstance(get_lookup("t.groups"), L)


def test_duplicate_registration_raises(registry):
    register_lookup("t.dup")(TypeaheadLookup)
    with pytest.raises(ImproperlyConfigured):
        register_lookup("t.dup")(TypeaheadLookup)


def test_unknown_lookup_raises():
    with pytest.raises(LookupNotFound):
        get_lookup("nope.nope")
    assert issubclass(LookupNotFound, ImproperlyConfigured)


def test_register_user_lookup(registry, people):
    @register_user_lookup("t.muellers")
    def muellers(request, **params):
        return User.objects.filter(last_name="Müller")

    lookup = get_lookup("t.muellers")
    assert isinstance(lookup, UserLookup)
    assert set(lookup.get_queryset(None)) == {people["anna"], people["bert"]}
    assert muellers(None).count() == 2  # the decorated function stays usable


def test_register_user_lookup_with_custom_base(registry):
    class Short(UserLookup):
        max_results = 3

    @register_user_lookup("t.short", base=Short)
    def short(request):
        return User.objects.none()

    assert isinstance(get_lookup("t.short"), Short)
    assert get_lookup("t.short").max_results == 3


def test_autodiscovery_registered_testapp_lookups():
    assert isinstance(get_lookup("testapp.group_members"), UserLookup)
    assert get_lookup("testapp.groups").search_fields == ["name"]


def test_value_is_always_the_pk_not_a_hook():
    # narrowed API: value() was overridable but the field validates by pk, so an override broke saving
    assert not hasattr(TypeaheadLookup(), "value")
