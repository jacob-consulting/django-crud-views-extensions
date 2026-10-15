import datetime
import json
import re

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape  # noqa: F401 — used by the Task 3 tests appended below

from datetimepicker.models import Event

#: the xdsoft (PHP-style) format tokens the widgets use, mapped to strftime
_PHP_TOKENS = {"d": "%d", "m": "%m", "Y": "%Y", "H": "%H", "i": "%M", "s": "%S"}


def php_date(value, fmt: str) -> str:
    """Format a date/time the way the xdsoft picker would for a PHP-style format string."""
    return value.strftime("".join(_PHP_TOKENS.get(ch, ch) for ch in fmt))


def picker_input(html: str, name: str) -> dict:
    """Value and parsed xdsoft config of the rendered <input name=...>."""
    tag = re.search(rf'<input[^>]*name="{name}"[^>]*>', html).group(0)
    config = re.search(r'xdsoft-datetime-config="([^"]*)"', tag).group(1)
    value = re.search(r'value="([^"]*)"', tag)
    return {
        "config": json.loads(config.replace("&quot;", '"')),
        "value": value.group(1) if value else "",
    }


class EventTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="t-admin", password="pw")
        tz = timezone.get_current_timezone()
        cls.event = Event.objects.create(
            title="Autumn meetup",
            day=datetime.date(2026, 10, 15),
            doors_open=datetime.time(18, 30),
            starts_at=datetime.datetime(2026, 10, 15, 19, 0, tzinfo=tz),
            ends_at=datetime.datetime(2026, 10, 15, 22, 0, tzinfo=tz),
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def payload(self, **overrides):
        data = {
            "title": "Winter meetup",
            "day": "",
            "doors_open": "",
            "starts_at": "",
            "ends_at": "",
        }
        data.update(overrides)
        return data


class AssetsTest(EventTestCase):
    def test_cv_js_delivers_plugin_and_init(self):
        resp = self.client.get(reverse("event-list"))
        self.assertContains(resp, "cdn.jsdelivr.net/npm/jquery-datetimepicker@")
        self.assertContains(resp, "crud_views_widget_datetimepicker/init.js")


class EventFormTest(EventTestCase):
    def test_create_page_renders_pickers(self):
        resp = self.client.get(reverse("event-create"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertFalse(picker_input(html, "day")["config"]["timepicker"])
        self.assertFalse(picker_input(html, "doors_open")["config"]["datepicker"])
        self.assertIn("format", picker_input(html, "starts_at")["config"])

    def test_settings_defaults_reach_the_widget(self):
        html = self.client.get(reverse("event-create")).content.decode()
        self.assertEqual(picker_input(html, "day")["config"]["dayOfWeekStart"], 1)

    def test_rendered_value_matches_picker_format_and_round_trips(self):
        """Regression check for the locale/format prerequisite: under every language the value Django renders is
        what the picker would write, and posting it back unchanged saves the same values."""
        url = reverse("event-update", kwargs={"pk": self.event.pk})
        local_starts = timezone.localtime(self.event.starts_at)
        for lang in ("en", "de"):
            with self.subTest(lang=lang):
                html = self.client.get(url, HTTP_ACCEPT_LANGUAGE=lang).content.decode()
                day = picker_input(html, "day")
                doors = picker_input(html, "doors_open")
                starts = picker_input(html, "starts_at")
                ends = picker_input(html, "ends_at")
                self.assertEqual(day["value"], php_date(self.event.day, day["config"]["format"]))
                self.assertEqual(doors["value"], php_date(self.event.doors_open, doors["config"]["format"]))
                self.assertEqual(starts["value"], php_date(local_starts, starts["config"]["format"]))
                data = self.payload(
                    title="Autumn meetup",
                    day=day["value"],
                    doors_open=doors["value"],
                    starts_at=starts["value"],
                    ends_at=ends["value"],
                )
                resp = self.client.post(url, data, HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(resp.status_code, 302, resp.content.decode()[:2000])
                self.event.refresh_from_db()
                self.assertEqual(self.event.day, datetime.date(2026, 10, 15))
                self.assertEqual(self.event.doors_open, datetime.time(18, 30))
                self.assertEqual(timezone.localtime(self.event.starts_at), local_starts)

    def test_end_before_start_rerenders_with_error_and_values(self):
        url = reverse("event-update", kwargs={"pk": self.event.pk})
        html = self.client.get(url, HTTP_ACCEPT_LANGUAGE="de").content.decode()
        starts = picker_input(html, "starts_at")["value"]
        data = self.payload(
            title="Autumn meetup",
            day=picker_input(html, "day")["value"],
            doors_open=picker_input(html, "doors_open")["value"],
            starts_at=starts,
            ends_at=starts,  # equal to start: invalid
        )
        resp = self.client.post(url, data, HTTP_ACCEPT_LANGUAGE="de")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "must be after the start")
        rerendered = resp.content.decode()
        self.assertEqual(picker_input(rerendered, "starts_at")["value"], starts)
        self.assertIn("xdsoft-datetime-config", rerendered)


class EventModalTest(EventTestCase):
    def test_list_offers_quick_edit(self):
        resp = self.client.get(reverse("event-list"))
        self.assertContains(resp, reverse("event-quick_edit", kwargs={"pk": self.event.pk}))

    def test_modal_partial_contains_pickers(self):
        url = reverse("event-quick_edit", kwargs={"pk": self.event.pk})
        resp = self.client.get(url, HTTP_X_CV_MODAL="true")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertNotIn("<html", html)  # partial, not a full page
        self.assertIn("format", picker_input(html, "starts_at")["config"])

    def test_valid_modal_post_answers_204_with_redirect(self):
        url = reverse("event-quick_edit", kwargs={"pk": self.event.pk})
        html = self.client.get(url, HTTP_X_CV_MODAL="true", HTTP_ACCEPT_LANGUAGE="de").content.decode()
        data = self.payload(
            title="Renamed in modal",
            day=picker_input(html, "day")["value"],
            doors_open=picker_input(html, "doors_open")["value"],
            starts_at=picker_input(html, "starts_at")["value"],
            ends_at=picker_input(html, "ends_at")["value"],
        )
        resp = self.client.post(url, data, HTTP_X_CV_MODAL="true", HTTP_ACCEPT_LANGUAGE="de")
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(resp["X-CV-Redirect"])
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Renamed in modal")


class EventFilterTest(EventTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        tz = timezone.get_current_timezone()
        Event.objects.create(
            title="Spring meetup",
            day=datetime.date(2026, 3, 1),
            doors_open=datetime.time(18, 0),
            starts_at=datetime.datetime(2026, 3, 1, 19, 0, tzinfo=tz),
        )

    def test_day_range_narrows_list(self):
        list_url = reverse("event-list")
        for lang in ("en", "de"):
            with self.subTest(lang=lang):
                # follow: crud_views remembers the last filter in the session and redirects back to it
                html = self.client.get(list_url, HTTP_ACCEPT_LANGUAGE=lang, follow=True).content.decode()
                fmt = picker_input(html, "day_from")["config"]["format"]
                params = {
                    "day_from": php_date(datetime.date(2026, 10, 1), fmt),
                    "day_to": php_date(datetime.date(2026, 10, 31), fmt),
                }
                resp = self.client.get(list_url, params, HTTP_ACCEPT_LANGUAGE=lang)
                self.assertContains(resp, "Autumn meetup")
                self.assertNotContains(resp, "Spring meetup")

    def test_garbage_filter_value_does_not_crash(self):
        resp = self.client.get(reverse("event-list"), {"day_from": "garbage"})
        self.assertEqual(resp.status_code, 200)


class EventSeedTest(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed", verbosity=0)
        count = Event.objects.count()
        self.assertGreaterEqual(count, 10)
        call_command("seed", verbosity=0)
        self.assertEqual(Event.objects.count(), count)
