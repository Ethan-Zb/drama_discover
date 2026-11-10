from django import forms
from django.forms import modelform_factory
from drama.models import Drama, DramaLink, Category
from platforms.models import Platform
from advertising.models import AdPosition
from .models import Site, ContentSource, Publication

ENTITIES = {
    "sites": (Site, "站点管理", ["name", "domain", "description", "contact_email", "is_active", "is_default", "platforms"], ["name", "domain"]),
    "dramas": (Drama, "短剧内容", ["title", "slug", "category", "description", "cover", "language", "tags", "episode_count", "release_year", "rights_holder", "rights_scope", "rights_expires_at"], ["title", "description", "tags"]),
    "publications": (Publication, "站点发布 / SEO", ["site", "drama", "summary", "originality_confirmed", "meta_title", "meta_description", "status"], ["drama__title", "summary", "site__name"]),
    "sources": (ContentSource, "授权来源", ["name", "domain", "rights_holder", "evidence", "scope", "expires_at", "is_active", "is_verified", "allowed_sites"], ["name", "domain", "rights_holder"]),
    "links": (DramaLink, "推广链接", ["drama", "source", "label", "platform_name", "url", "is_official", "is_active"], ["drama__title", "platform_name", "url"]),
    "ads": (AdPosition, "广告管理", ["site", "name", "code", "placement", "headline", "target_url", "image_url", "starts_at", "ends_at", "is_active"], ["name", "code", "headline"]),
    "platforms": (Platform, "平台导航", ["name", "slug", "country", "audience_region", "market", "platform_type", "website", "ios_url", "android_url", "verification_url", "source_note", "description", "rank", "status", "is_featured"], ["name", "market", "country"]),
    "categories": (Category, "分类标签", ["name", "slug", "description"], ["name", "description"]),
}


def entity_form(key):
    model, title, fields, search = ENTITIES[key]
    widgets = {}
    for name in fields:
        field = model._meta.get_field(name)
        if field.get_internal_type() == "DateField":
            widgets[name] = forms.DateInput(attrs={"type": "date"})
        elif field.get_internal_type() == "DateTimeField":
            widgets[name] = forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"})
        elif field.get_internal_type() == "TextField":
            widgets[name] = forms.Textarea(attrs={"rows": 5})
    return modelform_factory(model, fields=fields, widgets=widgets)


class ImportForm(forms.Form):
    site = forms.ModelChoiceField(Site.objects.filter(is_active=True), label="导入到站点")
    file = forms.FileField(label="UTF-8 CSV 文件（最大 2 MB / 500 行）")
