from django.contrib import admin
from .models import PageView, OutboundClick

@admin.register(OutboundClick)
class OutboundClickAdmin(admin.ModelAdmin):
    list_display = ("drama", "link", "created_at")
    list_filter = ("created_at",)
    date_hierarchy = "created_at"

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ("path", "referrer", "created_at")
    date_hierarchy = "created_at"
