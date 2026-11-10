from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from drama.models import Drama, DramaLink
from platforms.models import Platform
from operations.models import Site, ContentSource, Publication


class OperationsTests(TestCase):
    def setUp(self):
        Site.objects.all().delete()
        self.a = Site.objects.create(name="Alpha", domain="alpha.test", is_default=True)
        self.b = Site.objects.create(name="Beta", domain="beta.test")
        self.source = ContentSource.objects.create(name="Licensed", domain="licensed.example", rights_holder="Studio", evidence="Contract ABC", is_verified=True)
        self.drama = Drama.objects.create(title="A real drama", slug="real-drama", description="Original description", status="published")
        self.link = DramaLink.objects.create(drama=self.drama, platform_name="Licensed", url="https://licensed.example/watch/1", is_official=True, source=self.source)
        self.pub = Publication.objects.create(site=self.a, drama=self.drama, summary="Original editorial summary. " * 6, originality_confirmed=True, status="published")
        self.staff = get_user_model().objects.create_superuser("editor", "editor@example.com", "test-password")

    def test_site_isolation(self):
        self.assertContains(self.client.get("/", HTTP_HOST="alpha.test"), "A real drama")
        self.assertNotContains(self.client.get("/", HTTP_HOST="beta.test"), "A real drama")
        self.assertEqual(self.client.get("/drama/real-drama/", HTTP_HOST="beta.test").status_code, 404)
        self.assertEqual(self.client.get("/", HTTP_HOST="unknown.test").status_code, 404)

    def test_unverified_or_expired_source_blocks_page_and_redirect(self):
        self.source.is_verified = False
        self.source.save()
        self.assertEqual(self.client.get("/drama/real-drama/", HTTP_HOST="alpha.test").status_code, 404)
        self.assertEqual(self.client.get(f"/go/{self.link.pk}/", HTTP_HOST="alpha.test").status_code, 404)
        self.source.is_verified = True
        self.source.expires_at = timezone.localdate() - timedelta(days=1)
        self.source.save()
        self.assertEqual(self.client.get(f"/go/{self.link.pk}/", HTTP_HOST="alpha.test").status_code, 404)

    def test_redirect_scoped_and_tracked(self):
        from analytics.models import OutboundClick
        response = self.client.get(f"/go/{self.link.pk}/?utm_campaign=spring", HTTP_HOST="alpha.test")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.link.url)
        click = OutboundClick.objects.get()
        self.assertEqual(click.site, self.a)
        self.assertEqual(click.campaign, "spring")
        self.assertEqual(self.client.get(f"/go/{self.link.pk}/", HTTP_HOST="beta.test").status_code, 404)

    def test_publication_requires_original_text_and_source(self):
        self.pub.originality_confirmed = False
        with self.assertRaises(ValidationError):
            self.pub.full_clean()
        self.pub.originality_confirmed = True
        self.source.is_verified = False
        self.source.save()
        with self.assertRaises(ValidationError):
            self.pub.full_clean()

    def test_metadata_and_sitemap_only_for_current_site(self):
        response = self.client.get("/drama/real-drama/", HTTP_HOST="alpha.test")
        self.assertContains(response, 'rel="canonical"')
        self.assertContains(response, "https://alpha.test/drama/real-drama/")
        self.assertContains(self.client.get("/sitemap.xml", HTTP_HOST="alpha.test"), "real-drama")
        self.assertNotContains(self.client.get("/sitemap.xml", HTTP_HOST="beta.test"), "real-drama")

    def test_cms_auth_and_model_permissions(self):
        self.assertEqual(self.client.get("/cms/").status_code, 302)
        user = get_user_model().objects.create_user("limited", password="test", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get("/cms/publications/").status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/cms/").status_code, 200)
        self.assertEqual(self.client.get("/cms/publications/").status_code, 200)

    def test_platforms_preserved_and_default_site_only(self):
        Platform.objects.create(name="Catalog entry", slug="catalog-entry")
        self.assertContains(self.client.get("/", HTTP_HOST="alpha.test"), "Catalog entry")
        self.assertNotContains(self.client.get("/", HTTP_HOST="beta.test"), "Catalog entry")

    def test_public_page_views_exclude_cms_and_errors(self):
        from analytics.models import PageView
        self.client.get("/", HTTP_HOST="alpha.test")
        self.client.get("/not-found", HTTP_HOST="alpha.test")
        self.client.get("/cms/", HTTP_HOST="alpha.test")
        self.assertEqual(PageView.objects.count(), 1)
        self.assertEqual(PageView.objects.get().site, self.a)

    def test_source_domain_and_site_scope_are_enforced(self):
        self.link.url = "https://unlicensed.example/watch"
        self.link.save()
        self.assertEqual(self.client.get(f"/go/{self.link.pk}/", HTTP_HOST="alpha.test").status_code, 404)
        self.link.url = "https://licensed.example/watch"
        self.link.save()
        self.source.allowed_sites.add(self.b)
        self.assertEqual(self.client.get("/drama/real-drama/", HTTP_HOST="alpha.test").status_code, 404)

    def test_seo_generates_metadata_without_claiming_originality(self):
        self.client.force_login(self.staff)
        self.pub.status = "draft"
        self.pub.save()
        self.client.post("/cms/bulk/", {"selected": [self.pub.pk], "action": "seo"})
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.meta_title, "A real drama | Alpha")
        self.assertEqual(self.pub.status, "draft")
        self.pub.originality_confirmed = False
        self.pub.save()
        self.client.post("/cms/bulk/", {"selected": [self.pub.pk], "action": "publish"})
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.status, "draft")

    def test_csv_import_is_atomic_and_creates_only_drafts(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.staff)
        invalid = b'title,slug,description\nValid,new-drama,Original summary\nInvalid,,\n'
        response = self.client.post("/cms/import/", {"site": self.a.pk, "file": SimpleUploadedFile("dramas.csv", invalid)})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Drama.objects.filter(slug="new-drama").exists())
        valid = b'title,slug,description\nValid,new-drama,Original summary\n'
        self.client.post("/cms/import/", {"site": self.a.pk, "file": SimpleUploadedFile("dramas.csv", valid)})
        pub = Publication.objects.get(drama__slug="new-drama")
        self.assertEqual(pub.status, "draft")
        self.assertFalse(pub.originality_confirmed)

    def test_unauthorized_mutations_and_csrf_are_rejected(self):
        user = get_user_model().objects.create_user("viewer", password="test", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.post("/cms/bulk/", {"selected": [self.pub.pk], "action": "unpublish"}).status_code, 403)
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.staff)
        self.assertEqual(browser.post("/cms/bulk/", {"selected": [self.pub.pk], "action": "unpublish"}).status_code, 403)

    def test_jsonld_is_valid_and_cannot_close_script(self):
        import json, re
        self.drama.title = 'A </script><script>alert("x")</script>'
        self.drama.save()
        html = self.client.get("/drama/real-drama/", HTTP_HOST="alpha.test").content.decode()
        data = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1)
        self.assertEqual(json.loads(data)["name"], self.drama.title)
        self.assertNotIn("</script>", data)

    def test_ad_schedule_site_and_click_tracking(self):
        from advertising.models import AdPosition
        from analytics.models import AdEvent
        ad = AdPosition.objects.create(site=self.a, name="Banner", code="alpha-banner", headline="A sponsor", target_url="https://sponsor.example", is_active=True, ad_code="<script>alert(1)</script>")
        home = self.client.get("/", HTTP_HOST="alpha.test")
        self.assertContains(home, "A sponsor")
        self.assertNotContains(home, "alert(1)")
        self.assertEqual(AdEvent.objects.filter(kind="impression").count(), 1)
        self.assertEqual(self.client.get(f"/ad-click/{ad.pk}/", HTTP_HOST="beta.test").status_code, 404)
        self.assertEqual(self.client.get(f"/ad-click/{ad.pk}/", HTTP_HOST="alpha.test").status_code, 302)
        self.assertEqual(AdEvent.objects.filter(kind="click").count(), 1)
        ad.ends_at = timezone.now() - timedelta(hours=1)
        ad.save()
        self.assertEqual(self.client.get(f"/ad-click/{ad.pk}/", HTTP_HOST="alpha.test").status_code, 404)

    def test_dashboard_counts_are_site_scoped(self):
        from analytics.models import PageView
        PageView.objects.create(site=self.a, path="/alpha-only")
        PageView.objects.create(site=self.b, path="/beta-only")
        self.client.force_login(self.staff)
        response = self.client.get(f"/cms/?site={self.a.pk}")
        self.assertContains(response, "/alpha-only")
        self.assertNotContains(response, "/beta-only")

    def test_all_cms_forms_and_lists_render(self):
        self.client.force_login(self.staff)
        for entity in ("sites", "dramas", "publications", "sources", "links", "ads", "platforms", "categories"):
            self.assertEqual(self.client.get(f"/cms/{entity}/").status_code, 200, entity)
            self.assertEqual(self.client.get(f"/cms/{entity}/new/").status_code, 200, entity)

    def test_host_header_with_port_and_source_expiry_today(self):
        self.source.expires_at = timezone.localdate()
        self.source.save()
        self.assertEqual(self.client.get("/drama/real-drama/", HTTP_HOST="alpha.test:8000").status_code, 200)

    def test_prepare_pages_is_idempotent_and_preserves_site_copy(self):
        self.client.force_login(self.staff)
        for _ in range(2):
            self.client.post("/cms/prepare/", {"selected": [self.drama.pk], "site": self.b.pk})
        pub = Publication.objects.get(site=self.b, drama=self.drama)
        self.assertEqual(pub.status, "draft")
        self.assertFalse(pub.originality_confirmed)
        self.assertEqual(Publication.objects.filter(site=self.b).count(), 1)
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.status, "published")

    def test_malformed_referrer_does_not_break_public_pages(self):
        self.assertEqual(self.client.get("/", HTTP_HOST="alpha.test", HTTP_REFERER="http://[").status_code, 200)
        self.assertEqual(self.client.get(f"/go/{self.link.pk}/", HTTP_HOST="alpha.test", HTTP_REFERER="http://[").status_code, 302)

    def test_truncated_csv_row_is_validation_error(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.staff)
        response = self.client.post("/cms/import/", {"site": self.a.pk, "file": SimpleUploadedFile("bad.csv", b'title,slug,description\nBroken,broken\n')})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Drama.objects.filter(slug="broken").exists())

    def test_dashboard_requires_permissions_for_all_reported_models(self):
        from django.contrib.auth.models import Permission
        user = get_user_model().objects.create_user("pv-only", password="test", is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename="view_pageview"))
        self.client.force_login(user)
        self.assertEqual(self.client.get("/cms/").status_code, 403)

    def test_hidden_drama_is_suppressed_everywhere(self):
        self.drama.status = "hidden"
        self.drama.save()
        self.assertEqual(self.client.get("/drama/real-drama/", HTTP_HOST="alpha.test").status_code, 404)
        self.assertEqual(self.client.get(f"/go/{self.link.pk}/", HTTP_HOST="alpha.test").status_code, 404)
        self.assertNotContains(self.client.get("/sitemap.xml", HTTP_HOST="alpha.test"), "real-drama")

    def test_daily_chart_has_actual_local_day_count(self):
        from analytics.models import PageView
        PageView.objects.create(site=self.a, path="/")
        self.client.force_login(self.staff)
        response = self.client.get(f"/cms/?site={self.a.pk}")
        today = response.context["chart"][-1]
        self.assertEqual(today["count"], 1)

    def test_detail_queries_do_not_scale_with_catalogue(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        for number in range(30):
            drama = Drama.objects.create(title=f"Drama {number}", slug=f"drama-{number}", description="Original draft")
            DramaLink.objects.create(drama=drama, source=self.source, platform_name="Licensed", url="https://licensed.example/watch", is_official=True)
            Publication.objects.create(site=self.a, drama=drama, summary="Original summary. " * 10, originality_confirmed=True, status="published")
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/drama/real-drama/", HTTP_HOST="alpha.test")
        self.assertEqual(response.status_code, 200)
        self.assertLess(len(queries), 20)

    def test_report_total_and_chart_use_same_calendar_window(self):
        from analytics.models import PageView
        from datetime import datetime, time
        old = PageView.objects.create(site=self.a, path="/outside-window")
        outside = timezone.make_aware(datetime.combine(timezone.localdate() - timedelta(days=7), time(23, 59)))
        PageView.objects.filter(pk=old.pk).update(created_at=outside)
        PageView.objects.create(site=self.a, path="/today")
        self.client.force_login(self.staff)
        response = self.client.get(f"/cms/?site={self.a.pk}&days=7")
        self.assertEqual(response.context["metrics"][0][1], 1)
        self.assertEqual(sum(row["count"] for row in response.context["chart"]), 1)
