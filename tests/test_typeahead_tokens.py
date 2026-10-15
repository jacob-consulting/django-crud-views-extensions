import datetime
import uuid

import pytest
from django.core import signing
from django.core.exceptions import ImproperlyConfigured

from crud_views_widget_typeahead.lookups import LookupNotFound
from crud_views_widget_typeahead.tokens import SALT, BadToken, make_token, read_token


def test_round_trip():
    token = make_token("testapp.group_members", {"group": "1"})
    assert read_token(token) == ("testapp.group_members", {"group": "1"})


def test_salt():
    assert SALT == "crud_views.typeahead"


@pytest.mark.parametrize("token", ["", "garbage", "x" + make_token("testapp.groups", {})])
def test_bad_signature(token):
    with pytest.raises(BadToken):
        read_token(token)


def test_other_salt_is_rejected():
    with pytest.raises(BadToken):
        read_token(signing.dumps({"l": "testapp.groups", "p": {}}))


@pytest.mark.parametrize("payload", [["x"], {"l": "testapp.groups"}, {"l": "testapp.groups", "p": [1]}, {"p": {}}])
def test_wrong_shape(payload):
    with pytest.raises(BadToken):
        read_token(signing.dumps(payload, salt=SALT))


def test_unknown_lookup_in_token():
    with pytest.raises(BadToken):
        read_token(signing.dumps({"l": "nope.nope", "p": {}}, salt=SALT))


def test_make_token_unknown_lookup():
    with pytest.raises(LookupNotFound):
        make_token("nope.nope", {})


@pytest.mark.parametrize(
    "params", [{"id": uuid.uuid4()}, {"day": datetime.date(2026, 1, 1)}, {"ids": (1, 2)}, ["x"], None]
)
def test_make_token_rejects_non_json_params(params):
    with pytest.raises(ImproperlyConfigured):
        make_token("testapp.groups", params)
