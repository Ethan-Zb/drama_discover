from django import template
from django.utils.translation import gettext as _

register = template.Library()

COUNTRIES = {
    "United States": ("us", "United States"), "Singapore": ("sg", "Singapore"), "China": ("cn", "China"),
    "India": ("in", "India"), "South Korea": ("kr", "South Korea"), "Japan": ("jp", "Japan"),
    "Germany": ("de", "Germany"), "Ukraine": ("ua", "Ukraine"), "Vietnam": ("vn", "Vietnam"),
    "France": ("fr", "France"), "United Kingdom": ("gb", "United Kingdom"), "Hong Kong": ("hk", "Hong Kong, China"),
}


def country_info(value):
    code, label = COUNTRIES.get(value, ("unknown", "Country pending review"))
    return code, _(label)


@register.filter
def market_label(value):
    if not value:
        return _("Overseas short-drama platform")
    known = {"North America", "Europe", "global", "Global", "Southeast Asia", "India", "Indonesia", "Thailand", "Philippines", "Vietnam", "Germany", "United Kingdom", "Japan", "France", "South Korea", "Türkiye", "emerging markets", "International", "China"}
    return " · ".join(_(part.strip()) if part.strip() in known else part.strip() for part in value.split(";"))


@register.filter
def localize_label(value):
    return _(value) if value in {"Watch on official platform", "Drama"} else value
