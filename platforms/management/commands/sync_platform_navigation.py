import json
from datetime import datetime, date, time
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from platforms.models import Platform
from platforms.services import destinations


class Command(BaseCommand):
    help = "Review/apply the dated official platform-navigation directory. Existing custom URLs are preserved."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Apply reviewed records; default is a read-only summary.")

    def handle(self, *args, **options):
        path = Path(__file__).resolve().parents[2] / "data" / "navigation_links_20261110.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.stdout.write(f"Reviewed directory: {len(data['platforms'])} entries; dated {data['checked_on']}. Not a market-share ranking.")
        if not options["apply"]:
            self.stdout.write("Dry run. Use --apply to update blank/matching destinations and retain alias records privately.")
            return
        changed = archived = skipped = 0
        with transaction.atomic():
            for row in data["platforms"]:
                platform, created = Platform.objects.get_or_create(name=row["name"], defaults={"slug": slugify(row["name"]), "market": "International", "rank": {"Drama Pops": 30, "SnackShort": 47}.get(row["name"], 99)})
                fields = ("website", "ios_url", "android_url")
                if any(getattr(platform, field) and getattr(platform, field) != row.get(field, "") for field in fields):
                    skipped += 1
                    self.stdout.write(f"Preserved custom URLs: {platform.name}")
                    continue
                if not created and platform.status == Platform.Status.INACTIVE:
                    skipped += 1
                    self.stdout.write(f"Preserved inactive status: {platform.name}")
                    continue
                for field in fields:
                    setattr(platform, field, row.get(field, ""))
                platform.verification_url = platform.verification_url or row["verification_url"]
                platform.link_checked_at = platform.link_checked_at or timezone.make_aware(datetime.combine(date.fromisoformat(data["checked_on"]), time.min))
                if not platform.source_note or platform.source_note.startswith(("Industry app rankings and public platform directories; initial entry requires editorial verification.", "Entry identity checked ")):
                    platform.source_note = f"Entry identity checked {data['checked_on']}; publisher: {row['publisher']}. Official listing in verification_url; not a content-license audit."[:255]
                platform.status = Platform.Status.VERIFIED
                platform.full_clean()
                if not destinations(platform):
                    raise ValueError(f"No safe official destination: {platform.name}")
                platform.save()
                changed += 1
            for name, reason in data["archived"].items():
                platform = Platform.objects.filter(name=name).first()
                if platform and not any((platform.website, platform.ios_url, platform.android_url)):
                    platform.status = Platform.Status.INACTIVE
                    platform.source_note = reason[:255]
                    platform.save(update_fields=["status", "source_note", "updated_at"])
                    archived += 1
        self.stdout.write(self.style.SUCCESS(f"Applied {changed}; retained {archived} aliases privately; preserved {skipped} customized records."))
