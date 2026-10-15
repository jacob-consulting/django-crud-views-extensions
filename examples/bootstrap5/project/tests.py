from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape

from project.features import DEMO_URL, FEATURES


class ProjectTest(TestCase):
    def test_system_checks_pass(self):
        call_command("check", fail_level="WARNING")

    def test_home_renders_every_feature_card(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        for feature in FEATURES:
            self.assertContains(resp, escape(feature.title))  # card copy is autoescaped (e.g. "&")
            self.assertContains(resp, reverse(feature.url_name))

    def test_login_page_renders(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "admin/admin")

    def test_feature_pages_require_login(self):
        for feature in FEATURES:
            resp = self.client.get(reverse(feature.url_name))
            self.assertEqual(resp.status_code, 302, feature.url_name)

    def test_feature_pages_render_for_admin(self):
        admin = get_user_model().objects.create_superuser(username="t-admin", password="pw")
        self.client.force_login(admin)
        for feature in FEATURES:
            resp = self.client.get(reverse(feature.url_name))
            self.assertEqual(resp.status_code, 200, feature.url_name)

    def test_seed_is_idempotent(self):
        call_command("seed", verbosity=0)
        call_command("seed", verbosity=0)
        admin = get_user_model().objects.get(username="admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("admin"))

    def test_footer_links_the_live_demo(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, DEMO_URL)
        self.assertNotContains(resp, 'id="demo-banner"')

    @override_settings(DEMO_MODE=True)
    def test_demo_banner_in_demo_mode(self):
        resp = self.client.get(reverse("login"))
        self.assertContains(resp, 'id="demo-banner"')


@override_settings(ROOT_URLCONF="project.urls_demo")
class DemoUrlsTest(TestCase):
    def test_admin_is_not_mounted(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_login_still_mounted(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
