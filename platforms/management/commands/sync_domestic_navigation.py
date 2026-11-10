import json
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from platforms.models import Platform


class Command(BaseCommand):
    help = "Add three domestic platforms based on a dated standalone-app MAU reference, including manju."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        data = json.loads((Path(__file__).resolve().parents[2] / "data/domestic_navigation_20261110.json").read_text(encoding="utf-8"))
        self.stdout.write("Domestic selection: September 2026 standalone short-drama app MAU, including animated dramas; not a live ranking.")
        if not options["apply"]:
            self.stdout.write("Dry run: " + ", ".join(row["name"] for row in data["platforms"]))
            return
        with transaction.atomic():
            for row in data["platforms"]:
                by_slug = Platform.objects.filter(slug=row["slug"]).first()
                by_name = Platform.objects.filter(name=row["name"]).first()
                if by_slug and (by_slug.name != row["name"] or (by_name and by_name.pk != by_slug.pk)):
                    raise CommandError(f"Existing name/slug identify different platforms: {row['name']}; no records changed.")
                if by_name:
                    self.stdout.write(f"Preserved existing record and custom slug: {by_name.name}")
                    continue
                platform, created = Platform.objects.get_or_create(slug=row["slug"], defaults={"name": row["name"], "country": "China", "market": "China", "audience_region": "domestic", "rank": row["rank"], "status": "verified", "website": row["website"], "ios_url": row["ios_url"], "verification_url": row["ios_url"], "link_checked_at": timezone.make_aware(datetime(2026, 11, 10)), "source_note": f"QuestMobile Sep 2026 standalone app MAU incl. manju, #{row['rank']}. Reference: {data['ranking_source']}"[:255]})
                platform.full_clean()
                if not created:
                    self.stdout.write(f"Preserved existing record: {platform.name}")
        self.stdout.write(self.style.SUCCESS("Domestic navigation records synchronized; existing entries preserved."))
