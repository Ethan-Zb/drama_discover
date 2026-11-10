import json
from urllib.parse import urlsplit
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from .models import Publication, public_url


def eligible_links(drama, site):
    result = []
    for link in drama.links.all():
        if not (link.is_active and link.is_official and link.source_id):
            continue
        try:
            public_url(link.url)
        except ValidationError:
            continue
        if urlsplit(link.url).hostname.lower() == link.source.domain.lower() and link.source.valid_for(site):
            result.append(link)
    return result


def visible_publications(site, slug=None, drama_id=None):
    if not site:
        return []
    rows = Publication.objects.filter(site=site, status="published").select_related("drama__category", "site").prefetch_related("drama__links__source__allowed_sites")
    if slug is not None:
        rows = rows.filter(drama__slug=slug)
    if drama_id is not None:
        rows = rows.filter(drama_id=drama_id)
    return [row for row in rows if not row.publish_errors()]


def public_dramas(site, slug=None, drama_id=None):
    publications = visible_publications(site, slug=slug, drama_id=drama_id)
    for publication in publications:
        drama = publication.drama
        drama.description = publication.summary
        drama.meta_title = publication.meta_title or f"{drama.title} | {site.name}"
        drama.meta_description = publication.meta_description or strip_tags(publication.summary)[:160]
    return [row.drama for row in publications]


def generate_seo(publication):
    if not publication.originality_confirmed or len(publication.summary.strip()) < 80:
        raise ValidationError("先填写至少 80 字符的原创简介并确认许可，再生成 SEO。")
    publication.meta_title = f"{publication.drama.title} | {publication.site.name}"[:255]
    publication.meta_description = " ".join(strip_tags(publication.summary).split())[:160]
    publication.save(update_fields=["meta_title", "meta_description", "updated_at"])


def structured_data(drama, canonical):
    return json.dumps({"@context": "https://schema.org", "@type": "CreativeWork", "name": drama.title,
                       "description": drama.meta_description, "inLanguage": drama.language, "url": canonical}, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
