from django.test import TestCase, Client
from operations.models import Site
from platforms.models import Platform


class LanguageTests(TestCase):
    def setUp(self):
        Site.objects.all().delete()
        self.site = Site.objects.create(name="Drama Discover", domain="alpha.test", is_default=True)
        self.platform = Platform.objects.create(name="ReelShort", slug="reelshort", website="https://www.reelshort.com/", status="verified", market="North America; Europe; global")

    def test_chinese_and_english_homepage(self):
        self.client.cookies["django_language"] = "zh-hans"
        response = self.client.get("/", HTTP_HOST="alpha.test")
        self.assertContains(response, 'lang="zh-hans"')
        self.assertContains(response, "浏览平台")
        self.assertContains(response, "访问官网")
        self.assertContains(response, "北美")
        self.assertContains(response, "ReelShort")
        self.client.cookies["django_language"] = "en"
        response = self.client.get("/", HTTP_HOST="alpha.test")
        self.assertContains(response, 'lang="en"')
        self.assertContains(response, "Explore platforms")
        self.assertContains(response, "Visit website")
        self.assertNotContains(response, "浏览平台")

    def test_switch_preserves_search_and_campaign_and_cookie(self):
        path = "/?q=ReelShort&kind=website&utm_campaign=launch#platforms"
        response = self.client.post("/i18n/setlang/", {"language": "zh-hans", "next": path}, HTTP_HOST="alpha.test")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, path)
        self.assertEqual(response.cookies["django_language"].value, "zh-hans")
        response = self.client.get(path.split('#')[0], HTTP_HOST="alpha.test")
        self.assertContains(response, "访问官网")
        self.assertContains(response, "utm_campaign=launch")

    def test_switch_rejects_external_return_and_requires_csrf(self):
        response = self.client.post("/i18n/setlang/", {"language": "en", "next": "https://attacker.example/"}, HTTP_HOST="alpha.test")
        self.assertEqual(response.url, "/")
        browser = Client(enforce_csrf_checks=True)
        self.assertEqual(browser.post("/i18n/setlang/", {"language": "en"}, HTTP_HOST="alpha.test").status_code, 403)

    def test_invalid_language_does_not_replace_preference(self):
        self.client.cookies["django_language"] = "en"
        response = self.client.post("/i18n/setlang/", {"language": "not-a-language", "next": "/"}, HTTP_HOST="alpha.test")
        self.assertNotIn("django_language", response.cookies)
        self.assertContains(self.client.get("/", HTTP_HOST="alpha.test"), "Explore platforms")

    def test_browser_preference_and_legacy_public_pages(self):
        self.assertContains(self.client.get("/", HTTP_HOST="alpha.test", HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9"), 'lang="en"')
        self.client.cookies["django_language"] = "zh-hans"
        self.assertContains(self.client.get("/drama/", HTTP_HOST="alpha.test"), "暂未发布短剧")
        self.assertContains(self.client.get("/search/?q=anything", HTTP_HOST="alpha.test"), "搜索结果")

    def test_country_and_audience_region_are_independent(self):
        self.platform.country = "United States"
        self.platform.save()
        Platform.objects.create(name="红果短剧", slug="hongguo", country="China", audience_region="domestic", ios_url="https://apps.apple.com/cn/app/id6451407032", status="verified")
        Platform.objects.create(name="Overseas China-based", slug="overseas-cn", country="China", audience_region="overseas")
        response = self.client.get("/?region=domestic&country=cn", HTTP_HOST="alpha.test")
        self.assertContains(response, "红果短剧")
        self.assertNotContains(response, "Overseas China-based")
        response = self.client.get("/?region=overseas&country=us", HTTP_HOST="alpha.test")
        self.assertContains(response, "ReelShort")
        self.assertNotContains(response, "红果短剧")

    def test_domestic_sync_reuses_custom_identity_and_is_idempotent(self):
        from django.core.management import call_command
        from io import StringIO
        old = Platform.objects.create(name="红果短剧", slug="custom-hongguo", country="China", audience_region="domestic", website="https://custom.example/", status="needs_review")
        for _ in range(2):
            call_command("sync_domestic_navigation", apply=True, stdout=StringIO())
        old.refresh_from_db()
        self.assertEqual(old.slug, "custom-hongguo")
        self.assertEqual(old.website, "https://custom.example/")
        self.assertEqual(old.status, "needs_review")
        self.assertEqual(Platform.objects.filter(audience_region="domestic").count(), 3)

    def test_domestic_sync_identity_collision_rolls_back(self):
        from django.core.management import call_command, CommandError
        from io import StringIO
        Platform.objects.create(name="Existing custom platform", slug="hongguo-manju")
        with self.assertRaises(CommandError):
            call_command("sync_domestic_navigation", apply=True, stdout=StringIO())
        self.assertFalse(Platform.objects.filter(name="红果短剧").exists())
