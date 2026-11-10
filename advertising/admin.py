from django.contrib import admin
from .models import AdPosition

@admin.register(AdPosition)
class AdPositionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
