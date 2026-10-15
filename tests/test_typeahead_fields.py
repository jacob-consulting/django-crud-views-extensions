import copy
import uuid

import pytest
from django import forms
from django.contrib.auth.models import Group, User
from django.core.exceptions import ImproperlyConfigured, PermissionDenied

from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.tokens import read_token
from crud_views_widget_typeahead.widgets import TypeaheadInput


class MemberForm(forms.Form):
    member = TypeaheadField(lookup="testapp.group_members")


@pytest.fixture
def team(db):
    group = Group.objects.create(name="team")
    member = User.objects.create_user("mmember", first_name="Mia", last_name="Member")
    outsider = User.objects.create_user("ooutsider", first_name="Mia", last_name="Outsider")
    group.user_set.add(member)
    return {"group": group, "member": member, "outsider": outsider}


def bound_form(team, data=None):
    form = MemberForm(data)
    form.fields["member"].bind(None, group=str(team["group"].pk))
    return form


def test_default_widget_is_typeahead_input():
    assert isinstance(MemberForm().fields["member"].widget, TypeaheadInput)


def test_bind_sets_queryset_and_binding(team):
    field = bound_form(team).fields["member"]
    assert list(field.queryset) == [team["member"]]
    binding = field.widget.binding
    assert binding.lookup_name == "testapp.group_members"
    assert read_token(binding.token) == ("testapp.group_members", {"group": str(team["group"].pk)})


def test_bind_returns_the_field(team):
    field = MemberForm().fields["member"]
    assert field.bind(None, group=str(team["group"].pk)) is field


def test_member_validates(team):
    form = bound_form(team, {"member": str(team["member"].pk)})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["member"] == team["member"]


def test_outsider_is_rejected(team):
    form = bound_form(team, {"member": str(team["outsider"].pk)})
    assert not form.is_valid()
    assert form.errors.as_data()["member"][0].code == "invalid_choice"


def test_required_empty_is_a_required_error(team):
    form = bound_form(team, {"member": ""})
    assert not form.is_valid()
    assert form.errors.as_data()["member"][0].code == "required"


def test_unbound_clean_raises(db):
    with pytest.raises(ImproperlyConfigured, match="bind"):
        MemberForm({"member": "1"}).is_valid()


def test_unbound_render_raises(db):
    with pytest.raises(ImproperlyConfigured, match="bind"):
        str(MemberForm()["member"])


def test_bind_rejects_non_json_params(team):
    with pytest.raises(ImproperlyConfigured):
        MemberForm().fields["member"].bind(None, group=uuid.uuid4())


def test_bind_propagates_permission_denied(db):
    with pytest.raises(PermissionDenied):
        MemberForm().fields["member"].bind(None, group="forbidden")


def test_binding_an_instance_field_leaves_the_class_field_unbound(team):
    bound_form(team)
    assert MemberForm.base_fields["member"].queryset is None
    assert MemberForm.base_fields["member"].widget.binding is None


def test_rebinding_a_copy_leaves_the_original_alone(team):
    other = Group.objects.create(name="other")
    field = bound_form(team).fields["member"]
    original_binding = field.widget.binding
    clone = copy.deepcopy(field)
    clone.bind(None, group=str(other.pk))
    assert field.widget.binding is original_binding
    assert list(field.queryset) == [team["member"]]
    assert list(clone.queryset) == []
