import html
import re
from urllib.parse import parse_qs, urlsplit

import pytest
from django import forms
from django.contrib.auth.models import Group, User

from crud_views_widget_typeahead.fields import TypeaheadField
from crud_views_widget_typeahead.tokens import read_token
from crud_views_widget_typeahead.widgets import TypeaheadInput


class MemberForm(forms.Form):
    member = TypeaheadField(lookup="testapp.group_members", help_text="Pick a member")
    note = forms.CharField()


@pytest.fixture
def team(db):
    group = Group.objects.create(name="team")
    member = User.objects.create_user("mmember", first_name="Mia", last_name="Member")
    outsider = User.objects.create_user("ooutsider", first_name="Mia", last_name="Outsider")
    group.user_set.add(member)
    return {"group": group, "member": member, "outsider": outsider}


def render(team, **form_kwargs) -> str:
    form = MemberForm(**form_kwargs)
    form.fields["member"].bind(None, group=str(team["group"].pk))
    return str(form["member"])


def tag(markup: str, pattern: str) -> str:
    return re.search(pattern, markup).group(0)


def text_input(markup: str) -> str:
    return tag(markup, r'<input type="text"[^>]*>')


def hidden_input(markup: str) -> str:
    return tag(markup, r'<input type="hidden"[^>]*>')


def attr(element: str, name: str):
    match = re.search(rf'\s{re.escape(name)}="([^"]*)"', element)
    return html.unescape(match.group(1)) if match else None


def test_visible_input_has_no_name_hidden_input_has(team):
    markup = render(team)
    assert attr(text_input(markup), "name") is None
    hidden = hidden_input(markup)
    assert attr(hidden, "name") == "member"
    assert attr(hidden, "id") == "id_member_value"
    assert attr(hidden, "autocomplete") == "off"


def test_initial_pk_renders_label(team):
    markup = render(team, initial={"member": team["member"].pk})
    assert attr(text_input(markup), "value") == "Mia Member"
    assert attr(hidden_input(markup), "value") == str(team["member"].pk)


def test_initial_instance_renders_label(team):
    markup = render(team, initial={"member": team["member"]})
    assert attr(text_input(markup), "value") == "Mia Member"
    form = MemberForm()
    form.fields["member"].bind(None, group=str(team["group"].pk))
    assert 'value="Mia Member"' in form.fields["member"].widget.render("member", team["member"])


def test_label_is_rerendered_after_a_validation_error(team):
    markup = render(team, data={"member": str(team["member"].pk), "note": ""})
    assert attr(text_input(markup), "value") == "Mia Member"
    assert attr(hidden_input(markup), "value") == str(team["member"].pk)


@pytest.mark.parametrize("value", ["abc", "999999", "1.5"])
def test_garbage_pk_renders_empty(team, value):
    markup = render(team, data={"member": value, "note": "x"})
    assert attr(text_input(markup), "value") == ""
    assert attr(hidden_input(markup), "value") == ""


def test_out_of_scope_pk_renders_empty(team):
    markup = render(team, data={"member": str(team["outsider"].pk), "note": "x"})
    assert attr(text_input(markup), "value") == ""
    assert attr(hidden_input(markup), "value") == ""


def test_label_html_is_escaped(team):
    team["member"].first_name = "<b>Mia</b>"
    team["member"].save()
    markup = render(team, initial={"member": team["member"].pk})
    assert "<b>Mia</b>" not in markup
    assert "&lt;b&gt;Mia&lt;/b&gt;" in markup


def test_aria_attributes(team):
    markup = render(team)
    text = text_input(markup)
    assert attr(text, "id") == "id_member"
    assert attr(text, "role") == "combobox"
    assert attr(text, "aria-autocomplete") == "list"
    assert attr(text, "aria-expanded") == "false"
    assert attr(text, "aria-controls") == "id_member_listbox"
    assert attr(text, "autocomplete") == "off"
    assert "form-control" in attr(text, "class").split()
    listbox = tag(markup, r"<ul[^>]*>")
    assert attr(listbox, "id") == "id_member_listbox"
    assert attr(listbox, "role") == "listbox"
    assert attr(listbox, "aria-label")
    assert 'id="id_member_hint"' in markup
    assert "aria-live" in markup


def test_aria_describedby_merges_django_ids_with_hint(team):
    assert attr(text_input(render(team)), "aria-describedby") == "id_member_helptext id_member_hint"
    invalid = render(team, data={"member": "", "note": "x"})
    assert attr(text_input(invalid), "aria-describedby") == "id_member_helptext id_member_error id_member_hint"


def test_no_required_attribute(team):
    assert re.search(r"\srequired", text_input(render(team))) is None


def test_auto_id_false_still_consistent(team):
    markup = render(team, auto_id=False)
    text = text_input(markup)
    listbox = tag(markup, r"<ul[^>]*>")
    assert attr(text, "aria-controls") == attr(listbox, "id")
    assert attr(hidden_input(markup), "id") == f"{attr(text, 'id')}_value"


def test_data_attributes(team):
    markup = render(team)
    root = tag(markup, r"<div class=\"cv-typeahead\"[^>]*>")
    assert "data-cv-typeahead" in root
    url = urlsplit(attr(root, "data-url"))
    assert url.path == "/typeahead/"
    assert read_token(parse_qs(url.query)["t"][0]) == ("testapp.group_members", {"group": str(team["group"].pk)})
    assert attr(root, "data-min-chars") == "2"
    assert attr(root, "data-debounce") == "250"
    assert attr(root, "data-submit-on-clear") == "false"
    assert "{n}" in attr(root, "data-i18n-more")
    assert "{n}" in attr(root, "data-i18n-count")
    assert attr(root, "data-i18n-none")
    assert attr(root, "data-i18n-error")


def test_debounce_from_settings(team, settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"DEBOUNCE_MS": 400}
    assert 'data-debounce="400"' in render(team)


def test_clear_button_hidden_without_value(team):
    button = tag(render(team), r"<button[^>]*data-cv-typeahead-clear[^>]*>")
    assert re.search(r"\shidden", button)
    with_value = tag(render(team, initial={"member": team["member"].pk}), r"<button[^>]*data-cv-typeahead-clear[^>]*>")
    assert not re.search(r"\shidden", with_value)


def test_template_from_settings(team, settings):
    settings.CRUD_VIEWS_TYPEAHEAD = {"TEMPLATE": "testapp/custom_typeahead.html"}
    assert render(team).startswith("<custom-typeahead")


def test_template_per_instance(team):
    form = MemberForm()
    field = form.fields["member"]
    field.widget.template_name = "testapp/custom_typeahead.html"
    field.bind(None, group=str(team["group"].pk))
    assert str(form["member"]).startswith("<custom-typeahead")
    assert TypeaheadInput(template_name="x.html").template_name == "x.html"


def test_skin_context_contract(team):
    form = MemberForm()
    form.fields["member"].bind(None, group=str(team["group"].pk))
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
    }
    assert set(context["widget"]["typeahead"]["i18n"]) == {"hint", "more", "none", "count", "error", "clear", "listbox"}
