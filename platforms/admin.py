from django.contrib import admin
from .models import Platform

@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("rank", "name", "country", "platform_type", "status", "link_checked_at", "is_featured")
    readonly_fields = ("link_checked_at",)
    list_filter = ("status", "country", "audience_region", "platform_type", "is_featured")
    search_fields = ("name", "country", "market", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("status", "is_featured")
    ordering = ("rank", "name")
