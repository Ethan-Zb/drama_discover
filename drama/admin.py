from django.contrib import admin
from .models import Category, Drama, DramaLink

class DramaLinkInline(admin.TabularInline):
    model = DramaLink
    extra = 1

@admin.register(Drama)
class DramaAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "language", "status", "rights_status", "created_at")
    list_filter = ("status", "category", "language")
    search_fields = ("title", "description", "tags", "rights_holder")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [DramaLinkInline]
    readonly_fields = ("created_at", "updated_at")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(DramaLink)
class DramaLinkAdmin(admin.ModelAdmin):
    list_display = ("drama", "platform_name", "is_official", "is_active")
    list_filter = ("is_official", "is_active")
