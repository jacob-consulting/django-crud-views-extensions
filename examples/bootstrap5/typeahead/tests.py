import html
import re

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from typeahead.models import Task, Team


def typeahead(markup: str, name: str) -> dict:
    """data-url, visible text and hidden value of the rendered typeahead for field ``name``."""
    block = re.search(rf'<div class="cv-typeahead".*?name="{name}"[^>]*>', markup, re.S).group(0)

    def value(tag: str) -> str:
        match = re.search(r'value="([^"]*)"', tag)
        return html.unescape(match.group(1)) if match else ""

    return {
        "url": html.unescape(re.search(r'data-url="([^"]*)"', block).group(1)),
        "text": value(re.search(r'<input type="text"[^>]*>', block).group(0)),
        "value": value(re.search(rf'<input type="hidden" name="{name}"[^>]*>', block).group(0)),
    }


def typeahead_select(markup: str, name: str) -> dict:
    """data-url, trigger label and hidden value of the rendered select popup for field ``name``."""
    block = re.search(rf'<div class="cv-typeahead-select".*?name="{name}"[^>]*>', markup, re.S).group(0)
    label = re.search(r"<span[^>]*data-cv-typeahead-select-label[^>]*>(.*?)</span>", block, re.S).group(1)
    value = re.search(rf'<input type="hidden" name="{name}"[^>]*value="([^"]*)"', block).group(1)
    return {
        "url": html.unescape(re.search(r'data-url="([^"]*)"', block).group(1)),
        "label": html.unescape(label),
        "value": html.unescape(value),
    }


class TypeaheadTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(username="t-admin", password="pw")
        cls.team = Team.objects.create(name="Platform")
        cls.other_team = Team.objects.create(name="Payments")
        cls.member = User.objects.create_user("t-member", first_name="Mia", last_name="Member")
        cls.outsider = User.objects.create_user("t-outsider", first_name="Mia", last_name="Outsider")
        cls.team.members.add(cls.member)
        cls.other_team.members.add(cls.outsider)
        cls.task = Task.objects.create(team=cls.team, title="Fix login", assignee=cls.member)
        cls.other_task = Task.objects.create(team=cls.team, title="Write docs")

    def setUp(self):
        self.client.force_login(self.admin)

    def url(self, key, **kwargs):
        return reverse(f"task-{key}", kwargs={"team_pk": self.team.pk, **kwargs})


class TeamTest(TypeaheadTestCase):
    def test_team_list_links_to_tasks(self):
        resp = self.client.get(reverse("team-list"))
        self.assertContains(resp, self.url("list"))


class TaskFormTest(TypeaheadTestCase):
    def test_create_page_renders_typeahead(self):
        resp = self.client.get(self.url("create"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(typeahead(resp.content.decode(), "assignee")["url"].startswith("/_typeahead/?t="))
        self.assertContains(resp, "crud_views_widget_typeahead/typeahead.js")

    def test_endpoint_is_scoped_to_the_team(self):
        url = typeahead(self.client.get(self.url("create")).content.decode(), "assignee")["url"]
        body = self.client.get(f"{url}&q=mia").json()
        self.assertEqual([r["label"] for r in body["results"]], ["Mia Member (t-member)"])

    def test_endpoint_requires_login(self):
        url = typeahead(self.client.get(self.url("create")).content.decode(), "assignee")["url"]
        self.client.logout()
        resp = self.client.get(f"{url}&q=mia")
        self.assertEqual((resp.status_code, resp.json()), (403, {"error": "login_required"}))

    def test_create_with_member(self):
        resp = self.client.post(self.url("create"), {"title": "New", "assignee": self.member.pk})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Task.objects.get(title="New").assignee, self.member)

    def test_create_with_outsider_is_rejected(self):
        resp = self.client.post(self.url("create"), {"title": "New", "assignee": self.outsider.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Task.objects.filter(title="New").exists())

    def test_update_shows_the_label(self):
        found = typeahead(self.client.get(self.url("update", pk=self.task.pk)).content.decode(), "assignee")
        self.assertEqual(found["text"], "Mia Member (t-member)")
        self.assertEqual(found["value"], str(self.member.pk))


class TaskModalTest(TypeaheadTestCase):
    def test_list_offers_quick_assign(self):
        self.assertContains(self.client.get(self.url("list")), self.url("quick_assign", pk=self.task.pk))

    def test_modal_partial_contains_typeahead(self):
        resp = self.client.get(self.url("quick_assign", pk=self.task.pk), HTTP_X_CV_MODAL="true")
        self.assertEqual(resp.status_code, 200)
        markup = resp.content.decode()
        self.assertNotIn("<html", markup)
        self.assertIn("data-cv-typeahead", markup)

    def test_valid_modal_post_answers_204(self):
        resp = self.client.post(
            self.url("quick_assign", pk=self.other_task.pk),
            {"title": "Write docs", "assignee": self.member.pk},
            HTTP_X_CV_MODAL="true",
        )
        self.assertEqual(resp.status_code, 204)
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.assignee, self.member)


class TaskFilterTest(TypeaheadTestCase):
    def test_filter_by_assignee(self):
        resp = self.client.get(self.url("list"), {"assignee": self.member.pk})
        self.assertContains(resp, "Fix login")
        self.assertNotContains(resp, "Write docs")

    def test_filter_renders_the_popup_with_the_label(self):
        markup = self.client.get(self.url("list"), {"assignee": self.member.pk}).content.decode()
        found = typeahead_select(markup, "assignee")
        self.assertEqual((found["label"], found["value"]), ("Mia Member (t-member)", str(self.member.pk)))
        self.assertIn('data-submit-on-clear="true"', markup)
        self.assertIn("crud_views_widget_typeahead/typeahead-select.js", markup)

    def test_filter_offers_members_of_any_team(self):
        markup = self.client.get(self.url("list"), follow=True).content.decode()
        body = self.client.get(typeahead_select(markup, "assignee")["url"] + "&q=mia").json()
        self.assertEqual(
            sorted(r["label"] for r in body["results"]), ["Mia Member (t-member)", "Mia Outsider (t-outsider)"]
        )

    def test_filter_needs_two_characters(self):
        markup = self.client.get(self.url("list"), follow=True).content.decode()
        self.assertEqual(self.client.get(typeahead_select(markup, "assignee")["url"] + "&q=m").json()["count"], 0)


class TaskPickModalTest(TypeaheadTestCase):
    def test_list_offers_pick_assignee(self):
        self.assertContains(self.client.get(self.url("list")), self.url("pick_assignee", pk=self.task.pk))

    def test_modal_partial_contains_the_popup(self):
        resp = self.client.get(self.url("pick_assignee", pk=self.task.pk), HTTP_X_CV_MODAL="true")
        self.assertEqual(resp.status_code, 200)
        markup = resp.content.decode()
        self.assertNotIn("<html", markup)
        found = typeahead_select(markup, "assignee")
        self.assertEqual((found["label"], found["value"]), ("Mia Member (t-member)", str(self.member.pk)))

    def test_popup_browses_team_members_without_a_query(self):
        markup = self.client.get(self.url("pick_assignee", pk=self.task.pk), HTTP_X_CV_MODAL="true").content.decode()
        url = typeahead_select(markup, "assignee")["url"]
        body = self.client.get(f"{url}&q=&page=1").json()
        self.assertEqual([r["label"] for r in body["results"]], ["Mia Member (t-member)"])
        self.assertEqual(body["count"], 1)

    def test_valid_modal_post_answers_204(self):
        resp = self.client.post(
            self.url("pick_assignee", pk=self.other_task.pk), {"assignee": self.member.pk}, HTTP_X_CV_MODAL="true"
        )
        self.assertEqual(resp.status_code, 204)
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.assignee, self.member)

    def test_outsider_is_rejected(self):
        resp = self.client.post(
            self.url("pick_assignee", pk=self.other_task.pk), {"assignee": self.outsider.pk}, HTTP_X_CV_MODAL="true"
        )
        self.assertEqual(resp.status_code, 422)  # crud_views re-renders an invalid modal form as 422
        self.other_task.refresh_from_db()
        self.assertIsNone(self.other_task.assignee)


class AboutTest(TypeaheadTestCase):
    def test_card_shows_on_team_and_task_pages(self):
        from project.features import FEATURES

        about = escape(next(f for f in FEATURES if f.viewset == "team").about)
        self.assertContains(self.client.get(reverse("team-list")), about)
        self.assertContains(self.client.get(self.url("list")), about)


class SeedTest(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed", verbosity=0)
        users, teams, tasks = get_user_model().objects.count(), Team.objects.count(), Task.objects.count()
        self.assertGreaterEqual(users, 3000)
        self.assertGreaterEqual(Team.objects.first().members.count(), 500)
        call_command("seed", verbosity=0)
        self.assertEqual(
            (get_user_model().objects.count(), Team.objects.count(), Task.objects.count()), (users, teams, tasks)
        )
