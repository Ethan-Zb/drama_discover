from django.core.exceptions import ValidationError
from operations.models import public_url
from .models import Platform
from urllib.parse import urlsplit
from django.utils.translation import gettext_lazy as _


def site_platforms(site):
    qs = Platform.objects.exclude(status=Platform.Status.INACTIVE)
    if not site:
        return qs.none()
    return qs if site.is_default else qs.filter(site=site)


def destinations(platform):
    if platform.status != Platform.Status.VERIFIED:
        return []
    result = []
    for key, field, label in [("website", "website", _("Visit website")), ("android", "android_url", _("Google Play")), ("ios", "ios_url", _("App Store"))]:
        value = getattr(platform, field)
        if not value:
            continue
        try:
            public_url(value)
            host = (urlsplit(value).hostname or "").lower()
        except (ValidationError, ValueError):
            continue
        if key == "ios" and host not in {"apps.apple.com", "itunes.apple.com"}:
            continue
        if key == "android" and host != "play.google.com":
            continue
        result.append({"kind": key, "url": value, "label": label})
    return result
