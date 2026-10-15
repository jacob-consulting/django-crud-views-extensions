import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape

from project.features import CRUD_VIEWS_DOCS_URL, DEMO_URL, DOCS_BASE, FEATURES, DocRef, Feature
from project.templatetags.example_tags import snippet_panels
from project.views import HomeView

#: the repository's mkdocs sources, which DocRef.page is relative to
DOCS_DIR = Path(settings.BASE_DIR).parents[1] / "docs"


def _heading_slugs(markdown: str) -> set[str]:
    """Heading anchors as mkdocs' default toc slugify makes them; '#' lines inside code fences are not headings."""
    slugs, in_fence = set(), False
    for line in markdown.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and (match := re.match(r"#+\s+(.*)", line)):
            text = unicodedata.normalize("NFKD", match.group(1)).encode("ascii", "ignore").decode()
            text = re.sub(r"[^\w\s-]", "", text).strip().lower()
            slugs.add(re.sub(r"[-\s]+", "-", text))
    return slugs


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


class DocRefTest(SimpleTestCase):
    def test_url_plain_page(self):
        ref = DocRef(page="reference/typeahead/lookups.md", label="x")
        self.assertEqual(ref.url, f"{DOCS_BASE}/reference/typeahead/lookups/")

    def test_url_with_anchor(self):
        ref = DocRef(page="reference/datetimepicker/widgets.md", label="x", anchor="options")
        self.assertEqual(ref.url, f"{DOCS_BASE}/reference/datetimepicker/widgets/#options")

    def test_url_index_pages(self):
        self.assertEqual(DocRef(page="getting_started/index.md", label="x").url, f"{DOCS_BASE}/getting_started/")
        self.assertEqual(DocRef(page="index.md", label="x").url, f"{DOCS_BASE}/")

    def test_feature_docs_defaults_to_empty_tuple(self):
        feature = Feature(
            app="x", viewset="x", group="widgets", title="X", description="d", about="a", look_at="l",
            url_name="home", icon="fa-solid fa-x",
        )  # fmt: skip
        self.assertEqual(feature.docs, ())

    def test_every_feature_has_doc_refs(self):
        for feature in FEATURES:
            self.assertTrue(feature.docs, feature.title)

    def test_doc_refs_point_at_existing_pages_and_headings(self):
        for feature in FEATURES:
            for ref in feature.docs:
                with self.subTest(feature=feature.title, ref=ref.label):
                    page = DOCS_DIR / ref.page
                    self.assertTrue(page.is_file(), page)
                    if ref.anchor:
                        self.assertIn(ref.anchor, _heading_slugs(page.read_text()))


class SnippetPanelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="docs-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_every_feature_page_shows_code_and_doc_refs(self):
        for feature in FEATURES:
            with self.subTest(feature=feature.title):
                resp = self.client.get(reverse(feature.url_name))
                self.assertContains(resp, "The code behind this page")
                self.assertContains(resp, f"{feature.app}/views.py")
                self.assertContains(resp, f"{feature.app}/forms.py")
                self.assertContains(resp, "References to documentation")
                for ref in feature.docs:
                    self.assertContains(resp, f'<a href="{ref.url}" target="_blank" rel="noopener">')
                    self.assertContains(resp, escape(ref.label))

    def test_typeahead_shows_its_lookups_file(self):
        resp = self.client.get(reverse("team-list"))
        self.assertContains(resp, "typeahead/typeahead.py")

    def test_nothing_for_non_feature_view(self):
        self.assertEqual(snippet_panels({"view": HomeView()}), {"panels": [], "docs": ()})

    def test_home_has_no_code_panels(self):
        resp = self.client.get(reverse("home"))
        self.assertNotContains(resp, "The code behind this page")

    def test_no_doc_heading_when_docs_empty(self):
        html = render_to_string(
            "project/snippet_panels.html", {"panels": [{"id": "p", "title": "t", "html": "h"}], "docs": ()}
        )
        self.assertIn("snippet-panels", html)
        self.assertNotIn("References to documentation", html)


class CrossLinksTest(TestCase):
    def test_footer_links_the_docs(self):
        resp = self.client.get(reverse("login"))
        self.assertContains(resp, f'href="{DOCS_BASE}/"')
        self.assertContains(resp, f'href="{CRUD_VIEWS_DOCS_URL}"')

    def test_home_links_docs_and_crud_views(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, 'id="built-on-crud-views"')
        self.assertContains(resp, f'href="{CRUD_VIEWS_DOCS_URL}"', count=2)  # footer + home
        self.assertContains(resp, 'https://github.com/jacob-consulting/django-crud-views"')
        self.assertContains(resp, "https://django-crud-views-demo.onrender.com/")


@override_settings(ROOT_URLCONF="project.urls_demo")
class DemoUrlsTest(TestCase):
    def test_admin_is_not_mounted(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_login_still_mounted(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
