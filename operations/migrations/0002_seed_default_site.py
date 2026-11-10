from django.db import migrations


def seed(apps, schema_editor):
    Site = apps.get_model("operations", "Site")
    Publication = apps.get_model("operations", "Publication")
    Drama = apps.get_model("drama", "Drama")
    Settings = apps.get_model("core", "SiteSetting")
    old = Settings.objects.first()
    site, created = Site.objects.get_or_create(domain="127.0.0.1", defaults={"name": old.site_name if old else "Drama Discover", "description": old.site_description if old else "", "contact_email": old.contact_email if old else "", "is_default": True})
    for drama in Drama.objects.all().iterator():
        Publication.objects.get_or_create(site=site, drama=drama, defaults={"summary": drama.description, "meta_title": drama.meta_title, "meta_description": drama.meta_description, "status": "draft"})
    for app, model in [("analytics", "PageView"), ("analytics", "OutboundClick"), ("advertising", "AdPosition")]:
        apps.get_model(app, model).objects.filter(site__isnull=True).update(site=site)


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial"), ("operations", "0001_initial"), ("drama", "0002_dramalink_source"), ("analytics", "0003_outboundclick_site_pageview_drama_pageview_site_and_more"), ("advertising", "0003_adposition_site_adposition_starts_at_and_more")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
