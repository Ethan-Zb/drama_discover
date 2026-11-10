from django.test import TestCase
from django.core.exceptions import ValidationError
from operations.models import Site
from platforms.models import Platform
from analytics.models import PlatformClick


class PlatformNavigationTests(TestCase):
    def setUp(self):
        Site.objects.all().delete()
        self.site = Site.objects.create(name="Alpha", domain="alpha.test", is_default=True)
        self.other = Site.objects.create(name="Beta", domain="beta.test")
        self.platform = Platform.objects.create(name="Verified streaming", slug="verified-streaming", website="https://video.example/", ios_url="https://apps.apple.com/us/app/example/id123", status="verified")

    def test_navigation_without_drama_or_license_record(self):
        response = self.client.get(f"/platform-go/{self.platform.pk}/?utm_campaign=launch", HTTP_HOST="alpha.test")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://video.example/")
        click = PlatformClick.objects.get()
        self.assertEqual(click.site, self.site)
        self.assertEqual(click.platform, self.platform)
        self.assertEqual(click.campaign, "launch")
        self.assertEqual(click.destination_kind, "website")

    def test_only_configured_target_can_be_selected(self):
        response = self.client.get(f"/platform-go/{self.platform.pk}/?target=ios&url=https://attacker.example", HTTP_HOST="alpha.test")
        self.assertEqual(response.url, self.platform.ios_url)
        self.assertEqual(self.client.get(f"/platform-go/{self.platform.pk}/?target=android", HTTP_HOST="alpha.test").status_code, 404)
        self.assertEqual(self.client.get(f"/platform-go/{self.platform.pk}/?target=bad", HTTP_HOST="alpha.test").status_code, 404)

    def test_site_scope_status_and_safe_url(self):
        route = f"/platform-go/{self.platform.pk}/"
        self.assertEqual(self.client.get(route, HTTP_HOST="beta.test").status_code, 404)
        self.other.platforms.add(self.platform)
        self.assertEqual(self.client.get(route, HTTP_HOST="beta.test").status_code, 302)
        for state, url in [("needs_review", "https://video.example/"), ("inactive", "https://video.example/"), ("verified", "javascript:alert(1)"), ("verified", "http://127.0.0.1/")]:
            self.platform.status, self.platform.website, self.platform.ios_url = state, url, ""
            self.platform.save()
            self.assertEqual(self.client.get(route, HTTP_HOST="alpha.test").status_code, 404)

    def test_search_and_unverified_entry_visibility(self):
        Platform.objects.create(name="Awaiting verification", slug="awaiting")
        response = self.client.get("/", HTTP_HOST="alpha.test")
        self.assertContains(response, f'/platform-go/{self.platform.pk}/')
        self.assertContains(response, "Awaiting verification")
        self.assertNotContains(response, "Featured dramas")
        response = self.client.get("/?q=Verified", HTTP_HOST="alpha.test")
        self.assertContains(response, "Verified streaming")
        self.assertNotContains(response, "Awaiting verification")

    def test_no_body_or_head_counted_as_click(self):
        self.client.head(f"/platform-go/{self.platform.pk}/", HTTP_HOST="alpha.test")
        self.assertEqual(PlatformClick.objects.count(), 0)

    def test_official_store_labels_cannot_point_to_other_domains(self):
        self.platform.website = ""
        self.platform.ios_url = "https://lookalike.example/"
        self.platform.android_url = "https://play.google.com.attacker.example/"
        self.platform.save()
        self.assertEqual(self.client.get(f"/platform-go/{self.platform.pk}/", HTTP_HOST="alpha.test").status_code, 404)

    def test_platform_report_is_scoped_and_permission_protected(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        user = get_user_model().objects.create_superuser("report-admin", "a@example.com", "test")
        PlatformClick.objects.create(platform=self.platform, site=self.site, destination_kind="website", campaign="alpha-only")
        PlatformClick.objects.create(platform=self.platform, site=self.other, destination_kind="website", campaign="beta-only")
        self.client.force_login(user)
        response = self.client.get(f"/cms/?site={self.site.pk}")
        self.assertContains(response, "alpha-only")
        self.assertNotContains(response, "beta-only")
        user.is_superuser = False
        user.save()
        user.user_permissions.set(Permission.objects.exclude(codename="view_platformclick"))
        self.assertEqual(self.client.get("/cms/").status_code, 403)

    def test_curated_catalogue_has_fifty_distinct_identities(self):
        import json
        from pathlib import Path
        from platforms.services import destinations
        path = Path(__file__).parent / "platforms/data/navigation_links_20261110.json"
        rows = json.loads(path.read_text(encoding="utf-8"))["platforms"]
        self.assertEqual(len(rows), 50)
        self.assertEqual(len({row["ios_url"] or row["android_url"] for row in rows}), 50)
        for row in rows:
            platform = Platform(status="verified", **{field:row.get(field, "") for field in ("name", "website", "ios_url", "android_url")})
            self.assertTrue(destinations(platform), row["name"])

    def test_sync_directory_is_idempotent_and_preserves_custom_urls(self):
        from django.core.management import call_command
        from io import StringIO
        custom = Platform.objects.create(name="ReelShort", slug="reelshort", website="https://custom.example/", status="needs_review")
        alias = Platform.objects.create(name="DramaReels", slug="dramareels")
        for _ in range(2):
            call_command("sync_platform_navigation", apply=True, stdout=StringIO())
        custom.refresh_from_db()
        self.assertEqual(custom.website, "https://custom.example/")
        self.assertEqual(custom.status, "needs_review")
        alias.refresh_from_db()
        self.assertEqual(alias.status, "inactive")
        self.assertEqual(Platform.objects.filter(name="SnackShort").count(), 1)
        self.assertEqual(Platform.objects.filter(name="Drama Pops").count(), 1)

    def test_malformed_configured_url_cannot_crash_redirect(self):
        self.platform.website = "https://["
        self.platform.ios_url = ""
        self.platform.save()
        self.assertEqual(self.client.get(f"/platform-go/{self.platform.pk}/", HTTP_HOST="alpha.test").status_code, 404)

    def test_incoming_campaign_survives_actual_homepage_link(self):
        import html, re
        page = self.client.get("/?utm_campaign=launch", HTTP_HOST="alpha.test").content.decode()
        route = html.unescape(re.search(r'href="(/platform-go/[^\"]+)"', page).group(1))
        self.client.get(route, HTTP_HOST="alpha.test")
        self.assertEqual(PlatformClick.objects.get().campaign, "launch")
        self.assertIn('name="utm_campaign" value="launch"', page)

    def test_sync_preserves_editorial_evidence_and_research_date(self):
        from django.core.management import call_command
        from io import StringIO
        from django.utils import timezone
        platform = Platform.objects.create(name="ReelShort", slug="reelshort", source_note="Manual editorial evidence", verification_url="https://www.reelshort.com/about")
        call_command("sync_platform_navigation", apply=True, stdout=StringIO())
        platform.refresh_from_db()
        self.assertEqual(platform.source_note, "Manual editorial evidence")
        self.assertEqual(platform.verification_url, "https://www.reelshort.com/about")
        self.assertEqual(str(timezone.localdate(platform.link_checked_at)), "2026-11-10")
        stamp = platform.link_checked_at
        call_command("sync_platform_navigation", apply=True, stdout=StringIO())
        platform.refresh_from_db()
        self.assertEqual(platform.link_checked_at, stamp)
