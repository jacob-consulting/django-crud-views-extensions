import html
import re
from urllib.parse import parse_qs, urlsplit

import django_filters
import pytest
from django import forms
from django.contrib.auth.models import Group, User

from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.filters import TypeaheadFilter
from crud_views_widget_typeahead.tokens import read_token
from crud_views_widget_typeahead.widgets import TypeaheadSelect


class MemberForm(forms.Form):
    member = TypeaheadField(lookup="testapp.group_members", widget=TypeaheadSelect(), help_text="Pick a member")
    note = forms.CharField()


class PairForm(forms.Form):
    first = TypeaheadField(lookup="testapp.group_members", widget=TypeaheadSelect())
    second = TypeaheadField(lookup="testapp.group_members", widget=TypeaheadSelect())


@pytest.fixture
def team(db):
    group = Group.objects.create(name="team")
    member = User.objects.create_user("mmember", first_name="Mia", last_name="Member")
    outsider = User.objects.create_user("ooutsider", first_name="Mia", last_name="Outsider")
    group.user_set.add(member)
    return {"group": group, "member": member, "outsider": outsider}


def bound_form(team, form_class=MemberForm, **form_kwargs):
    form = form_class(**form_kwargs)
    for field in form.fields.values():
        if isinstance(field, TypeaheadField):
            field.bind(None, group=str(team["group"].pk))
    return form


def render(team, **form_kwargs) -> str:
    return str(bound_form(team, **form_kwargs)["member"])


def tag(markup: str, pattern: str) -> str:
    return re.search(pattern, markup).group(0)


def trigger(markup: str) -> str:
    return tag(markup, r'<button type="button"[^>]*aria-haspopup[^>]*>')


def test_search_field_is_not_inside_a_bootstrap_dropdown_menu(team):
    # Bootstrap's delegated keydown handler matches .dropdown-menu and throws on Escape
    markup = render(team)
    popup = tag(markup, r"<div[^>]*data-cv-typeahead-select-popup[^>]*>")
    assert "dropdown-menu" not in (attr(popup, "class") or "")
    listbox = tag(markup, r"<ul[^>]*>")
    assert "dropdown-menu" in (attr(listbox, "class") or "")
    between = markup[markup.index(popup) : markup.index(listbox)]
    assert "dropdown-menu" not in between
    assert 'type="search"' in between  # the search field sits in that dropdown-menu-free stretch


def label_text(markup: str) -> str:
    return html.unescape(
        re.search(r"<span[^>]*data-cv-typeahead-select-label[^>]*>(.*?)</span>", markup, re.S).group(1)
    )


def hidden_input(markup: str) -> str:
    return tag(markup, r'<input type="hidden"[^>]*>')


def search_input(markup: str) -> str:
    return tag(markup, r'<input type="search"[^>]*>')


def root(markup: str) -> str:
    return tag(markup, r'<div class="cv-typeahead-select"[^>]*>')


def attr(element: str, name: str):
    match = re.search(rf'\s{re.escape(name)}="([^"]*)"', element)
    return html.unescape(match.group(1)) if match else None


def test_structure_and_ids(team):
    markup = render(team)
    button = trigger(markup)
    assert attr(button, "id") == "id_member"
    assert attr(button, "name") is None
    assert attr(button, "aria-haspopup") == "listbox"
    assert attr(button, "aria-expanded") == "false"
    assert attr(button, "aria-controls") == "id_member_popup"
    assert {"form-select", "text-start"} <= set(attr(button, "class").split())
    assert "form-control" not in attr(button, "class").split()
    for dropped in ("role", "aria-autocomplete", "autocomplete"):
        assert attr(button, dropped) is None
    hidden = hidden_input(markup)
    assert (attr(hidden, "name"), attr(hidden, "id"), attr(hidden, "autocomplete")) == (
        "member",
        "id_member_value",
        "off",
    )
    popup = tag(markup, r"<div[^>]*data-cv-typeahead-select-popup[^>]*>")
    assert attr(popup, "id") == "id_member_popup"
    assert re.search(r"\shidden", popup)
    search = search_input(markup)
    assert attr(search, "id") == "id_member_search"
    assert attr(search, "role") == "combobox"
    assert attr(search, "aria-autocomplete") == "list"
    assert attr(search, "aria-expanded") == "false"
    assert attr(search, "aria-controls") == "id_member_listbox"
    assert attr(search, "aria-label")
    listbox = tag(markup, r"<ul[^>]*>")
    assert (attr(listbox, "id"), attr(listbox, "role")) == ("id_member_listbox", "listbox")
    assert attr(listbox, "aria-label")
    assert 'id="id_member_hint"' in markup
    assert "data-cv-typeahead-select-status" in markup and 'aria-live="polite"' in markup


def test_empty_shows_placeholder(team):
    markup = render(team)
    assert label_text(markup) == "Select…"
    assert "cv-typeahead-select-placeholder" in tag(markup, r"<span[^>]*data-cv-typeahead-select-label[^>]*>")
    assert attr(hidden_input(markup), "value") == ""


def test_initial_pk_renders_lookup_label(team):
    markup = render(team, initial={"member": team["member"].pk})
    assert label_text(markup) == "Mia Member"  # lookup.label (full name), not str(user) ("mmember")
    assert attr(hidden_input(markup), "value") == str(team["member"].pk)
    assert "cv-typeahead-select-placeholder" not in markup


def test_label_is_rerendered_after_a_validation_error(team):
    markup = render(team, data={"member": str(team["member"].pk), "note": ""})
    assert label_text(markup) == "Mia Member"


@pytest.mark.parametrize("value", ["abc", "999999", "1.5"])
def test_garbage_pk_renders_empty(team, value):
    markup = render(team, data={"member": value, "note": "x"})
    assert label_text(markup) == "Select…"
    assert attr(hidden_input(markup), "value") == ""


def test_out_of_scope_pk_renders_empty(team):
    markup = render(team, data={"member": str(team["outsider"].pk), "note": "x"})
    assert label_text(markup) == "Select…"
    assert attr(hidden_input(markup), "value") == ""


def test_label_html_is_escaped(team):
    team["member"].first_name = "<b>Mia</b>"
    team["member"].save()
    markup = render(team, initial={"member": team["member"].pk})
    assert "<b>Mia</b>" not in markup
    assert "&lt;b&gt;Mia&lt;/b&gt;" in markup


def test_unbound_widget_raises(team):
    from django.core.exceptions import ImproperlyConfigured

    with pytest.raises(ImproperlyConfigured, match="not bound"):
        str(MemberForm()["member"])


def test_aria_describedby_merges_django_ids_with_hint(team):
    assert attr(trigger(render(team)), "aria-describedby") == "id_member_helptext id_member_hint"
    invalid = render(team, data={"member": "", "note": "x"})
    assert attr(trigger(invalid), "aria-describedby") == "id_member_helptext id_member_error id_member_hint"


def test_no_required_attribute(team):
    assert re.search(r"\srequired", trigger(render(team))) is None


def test_auto_id_false_still_consistent(team):
    markup = render(team, auto_id=False)
    button = trigger(markup)
    popup = tag(markup, r"<div[^>]*data-cv-typeahead-select-popup[^>]*>")
    search = search_input(markup)
    listbox = tag(markup, r"<ul[^>]*>")
    assert attr(button, "aria-controls") == attr(popup, "id")
    assert attr(search, "aria-controls") == attr(listbox, "id")
    assert attr(hidden_input(markup), "id") == f"{attr(button, 'id')}_value"


def test_two_widgets_have_distinct_ids(team):
    form = bound_form(team, PairForm)
    ids = []
    for name in ("first", "second"):
        markup = str(form[name])
        ids += re.findall(r'\sid="([^"]*)"', markup)
    assert len(ids) == len(set(ids))


def test_data_attributes(team):
    markup = render(team)
    element = root(markup)
    assert "data-cv-typeahead-select" in element
    url = urlsplit(attr(element, "data-url"))
    assert url.path == "/typeahead/"
    assert read_token(parse_qs(url.query)["t"][0]) == ("testapp.group_members", {"group": str(team["group"].pk)})
    assert attr(element, "data-min-chars") == "2"
    assert attr(element, "data-debounce") == "250"
    assert attr(element, "data-page-size") == "10"
    assert attr(element, "data-submit-on-clear") == "false"
    assert "{n}" in attr(element, "data-i18n-count")
    for key in ("none", "error", "loading", "type-more", "placeholder"):
        assert attr(element, f"data-i18n-{key}"), key
    assert "2" in attr(element, "data-i18n-type-more")


def test_clear_button_hidden_without_value(team):
    button = tag(render(team), r"<button[^>]*data-cv-typeahead-select-clear[^>]*>")
    assert re.search(r"\shidden", button)
    assert attr(button, "aria-label")
    with_value = render(team, initial={"member": team["member"].pk})
    assert not re.search(r"\shidden", tag(with_value, r"<button[^>]*data-cv-typeahead-select-clear[^>]*>"))


def test_template_from_settings(team, settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"SELECT_TEMPLATE": "testapp/custom_typeahead_select.html"}
    assert render(team).startswith("<custom-typeahead-select")


def test_text_typeahead_template_setting_does_not_affect_the_popup(team, settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"TEMPLATE": "testapp/custom_typeahead.html"}
    assert "data-cv-typeahead-select" in render(team)


def test_template_per_instance(team):
    form = MemberForm()
    form.fields["member"].widget.template_name = "testapp/custom_typeahead_select.html"
    form.fields["member"].bind(None, group=str(team["group"].pk))
    assert str(form["member"]).startswith("<custom-typeahead-select")
    assert TypeaheadSelect(template_name="x.html").template_name == "x.html"


def test_skin_context_contract(team):
    form = bound_form(team)
    context = form.fields["member"].widget.get_context("member", team["member"].pk, {"id": "id_member"})
    assert set(context["widget"]["typeahead"]) == {
        "url",
        "label",
        "value",
        "hidden_name",
        "hidden_id",
        "listbox_id",
        "hint_id",
        "min_chars",
        "debounce",
        "submit_on_clear",
        "i18n",
        "popup_id",
        "search_id",
        "page_size",
    }
    assert set(context["widget"]["typeahead"]["i18n"]) == {
        "hint",
        "more",
        "none",
        "count",
        "error",
        "clear",
        "listbox",
        "placeholder",
        "search",
        "loading",
        "type_more",
    }


def test_form_round_trip_validates_against_the_bound_queryset(team):
    ok = bound_form(team, data={"member": str(team["member"].pk), "note": "x"})
    assert ok.is_valid(), ok.errors
    assert ok.cleaned_data["member"] == team["member"]
    outsider = bound_form(team, data={"member": str(team["outsider"].pk), "note": "x"})
    assert not outsider.is_valid()


class GroupFilter(django_filters.FilterSet):
    member = TypeaheadFilter(
        field_name="user", lookup="testapp.all_users", widget=TypeaheadSelect(submit_on_clear=True)
    )

    class Meta:
        model = Group
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["member"].bind(self.request)


def test_filter_with_the_popup_filters_by_pk(team):
    blue = Group.objects.create(name="blue")
    filterset = GroupFilter({"member": str(team["member"].pk)}, queryset=Group.objects.order_by("name"), request=None)
    assert list(filterset.qs) == [team["group"]]
    assert blue not in filterset.qs
    markup = str(filterset.form["member"])
    assert "data-cv-typeahead-select" in markup
    assert attr(root(markup), "data-submit-on-clear") == "true"
    assert attr(hidden_input(markup), "name") == "member"
