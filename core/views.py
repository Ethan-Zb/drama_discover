from urllib.parse import urlsplit
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.utils.html import escape
from django.core.exceptions import ValidationError
from drama.models import Category, DramaLink
from platforms.models import Platform
from analytics.models import OutboundClick, AdEvent
from advertising.models import AdPosition
from operations.models import public_url
from operations.services import public_dramas, eligible_links
from platforms.services import site_platforms, destinations
from platforms.templatetags.navigation_i18n import country_info
from collections import Counter

def current_ads(site, placement=None):
    now = timezone.now()
    qs = AdPosition.objects.filter(site=site, is_active=True).filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now)).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
    if placement:
        qs = qs.filter(placement=placement)
    ads = []
    for ad in qs:
        try:
            public_url(ad.target_url)
            if ad.image_url:
                public_url(ad.image_url)
        except ValidationError:
            continue
        ads.append(ad)
    return ads

def ad_context(request, placement):
    ads = current_ads(request.site, placement)
    if request.method == "GET":
        AdEvent.objects.bulk_create([AdEvent(ad=ad, site=request.site, kind="impression") for ad in ads])
    return {"site_ads": ads}

def home(request):
    dramas = public_dramas(request.site)
    all_platforms = list(site_platforms(request.site))
    for platform in all_platforms:
        platform.navigation_targets = destinations(platform)
        platform.country_code, platform.country_label = country_info(platform.country)
    q = request.GET.get("q", "").strip()[:200]
    kind = request.GET.get("kind", "all")
    campaign = request.GET.get("utm_campaign", "")[:120]
    region = request.GET.get("region", "all")
    country = request.GET.get("country", "all")
    if region not in {"all", "domestic", "overseas"}:
        region = "all"
    region_platforms = [p for p in all_platforms if region == "all" or p.audience_region == region]
    counts = Counter(p.country_code for p in region_platforms)
    country_labels = {p.country_code: p.country_label for p in region_platforms}
    countries = [{"code": key, "label": country_labels[key], "count": counts[key]} for key in sorted(counts)]
    if country not in counts:
        country = "all"
    platforms = [p for p in region_platforms if (country == "all" or p.country_code == country) and (not q or q.casefold() in f"{p.name} {p.market} {p.country_label} {p.description}".casefold())]
    if kind in {"website", "android", "ios"}:
        platforms = [p for p in platforms if any(target["kind"] == kind for target in p.navigation_targets)]
    elif kind == "ready":
        platforms = [p for p in platforms if p.navigation_targets]
    categories = Category.objects.filter(drama__pk__in=[d.pk for d in dramas]).distinct()[:12]
    return render(request, "navigation/home.html", {"dramas": dramas[:12], "categories": categories, "platforms": platforms, "q": q, "kind": kind, "campaign": campaign,
        "region": region, "country": country, "countries": countries, "overseas_count": sum(p.audience_region == "overseas" for p in all_platforms), "domestic_count": sum(p.audience_region == "domestic" for p in all_platforms),
        "platform_total": len(all_platforms), "ready_count": sum(bool(p.navigation_targets) for p in all_platforms),
        "featured_platforms": [p for p in all_platforms if p.is_featured and p.navigation_targets][:6], **ad_context(request, "home")})

def search(request):
    q = request.GET.get("q", "").strip()[:200]
    dramas = public_dramas(request.site)
    if q:
        dramas = [d for d in dramas if q.casefold() in f"{d.title} {d.description} {d.tags}".casefold()]
    return render(request, "core/search.html", {"dramas": dramas[:60], "q": q})

def go_to_source(request, link_id):
    link = get_object_or_404(DramaLink.objects.select_related("drama"), pk=link_id)
    drama = next(iter(public_dramas(request.site, drama_id=link.drama_id)), None)
    if not drama or link.pk not in {item.pk for item in eligible_links(drama, request.site)}:
        raise Http404
    try:
        referrer = urlsplit(request.META.get("HTTP_REFERER", "")).hostname or ""
    except ValueError:
        referrer = ""
    OutboundClick.objects.create(site=request.site, drama=link.drama, link=link, campaign=request.GET.get("utm_campaign", "")[:120], referrer=referrer[:500])
    return redirect(link.url)

def ad_click(request, pk):
    ad = next((a for a in current_ads(request.site) if a.pk == pk), None)
    if not ad:
        raise Http404
    AdEvent.objects.create(ad=ad, site=request.site, kind="click")
    return redirect(ad.target_url)

def ads_txt(request):
    return HttpResponse("# Add authorized publisher IDs for this site before enabling programmatic ads.\n", content_type="text/plain")

def robots_txt(request):
    origin = f"https://{request.site.domain}" if request.site else ""
    return HttpResponse(f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /cms/\nSitemap: {origin}/sitemap.xml\n", content_type="text/plain")

def sitemap(request):
    origin = f"https://{request.site.domain}"
    urls = [origin + "/"] + [origin + drama.get_absolute_url() for drama in public_dramas(request.site)]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{escape(url)}</loc></url>" for url in urls) + "</urlset>"
    return HttpResponse(xml, content_type="application/xml")

