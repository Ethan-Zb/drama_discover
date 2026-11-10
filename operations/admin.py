from django.contrib import admin
from .models import Site, ContentSource, Publication

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "is_active", "is_default")
    filter_horizontal = ("platforms",)

@admin.register(ContentSource)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "rights_holder", "is_verified", "expires_at")
    filter_horizontal = ("allowed_sites",)

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("drama", "site", "status", "originality_confirmed")
    list_filter = ("site", "status")
