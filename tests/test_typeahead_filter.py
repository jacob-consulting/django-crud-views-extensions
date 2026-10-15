import django_filters
import pytest
from django.contrib.auth.models import Group, User

from crud_views_widget_typeahead.filters import TypeaheadFilter
from crud_views_widget_typeahead.widgets import TypeaheadInput


class GroupFilter(django_filters.FilterSet):
    member = TypeaheadFilter(field_name="user", lookup="testapp.all_users")

    class Meta:
        model = Group
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["member"].bind(self.request)


@pytest.fixture
def groups(db):
    anna = User.objects.create_user("anna", first_name="Anna")
    bert = User.objects.create_user("bert", first_name="Bert")
    red, blue = Group.objects.create(name="red"), Group.objects.create(name="blue")
    red.user_set.add(anna)
    blue.user_set.add(bert)
    return {"anna": anna, "bert": bert, "red": red, "blue": blue}


def make(data=None):
    return GroupFilter(data, queryset=Group.objects.order_by("name"), request=None)


def test_filters_by_pk(groups):
    assert list(make({"member": str(groups["anna"].pk)}).qs) == [groups["red"]]


def test_empty_value_does_not_filter(groups):
    assert list(make({"member": ""}).qs) == [groups["blue"], groups["red"]]


def test_binding_survives_the_filter_form_copy(groups):
    field = make().form.fields["member"]
    assert field.widget.binding is not None
    assert set(field.queryset) == {groups["anna"], groups["bert"]}


def test_garbage_value_is_invalid_not_a_crash(groups):
    filterset = make({"member": "abc"})
    assert not filterset.is_valid()


def test_submit_on_clear_by_default(groups):
    assert 'data-submit-on-clear="true"' in str(make().form["member"])


def test_explicit_widget_is_kept(groups):
    class Plain(GroupFilter):
        member = TypeaheadFilter(field_name="user", lookup="testapp.all_users", widget=TypeaheadInput())

    filterset = Plain(None, queryset=Group.objects.all(), request=None)
    assert 'data-submit-on-clear="false"' in str(filterset.form["member"])


def test_bind_returns_the_filter(groups):
    filterset = make()
    assert filterset.filters["member"].bind(None) is filterset.filters["member"]
