from django.core.management.base import BaseCommand
from django.utils.text import slugify
from platforms.models import Platform

# Initial discovery directory, not an audited market-share ranking.
# Official URLs are deliberately left blank unless confirmed; review before publishing.
DATA = [
    ("ReelShort", "United States", "North America; Europe; global", "app_web"),
    ("DramaBox", "Singapore", "Global; Southeast Asia", "app_web"),
    ("NetShort", "Singapore", "Global", "app"),
    ("GoodShort", "Singapore", "Global", "app"),
    ("DramaWave", "Singapore", "Global; Southeast Asia", "app"),
    ("ShortMax", "United States", "Global", "app_web"),
    ("FlickReels", "United States", "Global", "app"),
    ("Kuku TV", "India", "India; global", "app"),
    ("RapidTV", "United States", "Global", "app"),
    ("StardustTV", "United States", "Global", "app"),
    ("FreeReels", "China", "Global; emerging markets", "app"),
    ("Melolo", "China", "Indonesia; Thailand; Philippines", "app"),
    ("Story TV", "India", "India; global", "app"),
    ("QuickTV", "India", "India; global", "app"),
    ("My Drama", "Ukraine", "Global", "app"),
    ("FlareFlow", "Singapore", "Global", "app"),
    ("PineDrama", "China", "Global", "app"),
    ("MoboReels", "United States", "Global", "app"),
    ("JoyReels", "Unknown", "Global", "app"),
    ("FlexTV", "Singapore", "Global; Türkiye", "app_web"),
    ("KalosTV", "United States", "North America; Türkiye", "app"),
    ("Sereal+", "Unknown", "Global", "app"),
    ("Vigloo", "South Korea", "South Korea; global", "app_web"),
    ("Shortical", "Israel", "Global", "app"),
    ("CandyJarTV", "Germany / United States", "Global", "app"),
    ("HotMiniDrama", "Unknown", "Global", "app"),
    ("LuckyDrama", "Unknown", "Global", "app"),
    ("AnyReel", "Unknown", "Global", "app"),
    ("BonusTV", "Unknown", "Global", "app"),
    ("DramaReels", "Unknown", "Global", "app"),
    ("StoryReel", "Unknown", "Global", "app"),
    ("VibeShort", "Unknown", "Global", "app"),
    ("Coin Drama", "Unknown", "Global", "app"),
    ("DotDrama", "Unknown", "Global", "app"),
    ("Playlet", "Unknown", "Global", "app"),
    ("Dramabite", "Unknown", "Global", "app"),
    ("iDrama", "Unknown", "Global", "app"),
    ("YuzuDrama", "Unknown", "Vietnam", "app"),
    ("FunReels", "Unknown", "Vietnam; Southeast Asia", "app"),
    ("FunDrama", "Unknown", "Vietnam; Southeast Asia", "app"),
    ("Soda Reels", "Unknown", "Indonesia", "app"),
    ("ShotShort", "Unknown", "Philippines", "app"),
    ("HoneyReels", "Unknown", "Vietnam", "app"),
    ("MiniShorts", "Unknown", "North America", "app"),
    ("DreameShort", "Unknown", "Germany; United Kingdom", "app"),
    ("BUMP", "Japan", "Japan", "app_web"),
    ("ShortTV", "India", "India", "app"),
    ("PocketFilms", "India", "India; global", "web"),
    ("Sweetz", "France", "France; Europe", "app_web"),
    ("Tattle TV", "United Kingdom", "United Kingdom", "app"),
]

class Command(BaseCommand):
    help = "Create or update the initial directory of 50 international short-drama platforms."

    def handle(self, *args, **options):
        created = updated = 0
        for rank, (name, country, market, kind) in enumerate(DATA, start=1):
            slug = slugify(name, allow_unicode=False).replace("+", "-plus") or f"platform-{rank}"
            defaults = {
                "rank": rank,
                "country": country,
                "market": market,
                "platform_type": kind,
                "description": f"{name} is listed in this international short-drama discovery directory. Confirm its official website, app-store availability, catalogue, and distribution rights before publishing platform-specific claims or linking to titles.",
                "source_note": "Industry app rankings and public platform directories; initial entry requires editorial verification.",
                "status": Platform.Status.NEEDS_REVIEW,
            }
            _, was_created = Platform.objects.update_or_create(slug=slug, defaults={"name": name, **defaults})
            created += int(was_created)
            updated += int(not was_created)
        self.stdout.write(self.style.SUCCESS(f"Platform seed complete: {len(DATA)} records; {created} created, {updated} updated."))
