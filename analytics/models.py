from django.db import models

class PageView(models.Model):
    site = models.ForeignKey("operations.Site", on_delete=models.SET_NULL, null=True, blank=True)
    drama = models.ForeignKey("drama.Drama", on_delete=models.SET_NULL, null=True, blank=True)
    path = models.CharField(max_length=500, db_index=True)
    referrer = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "页面访问记录"
        verbose_name_plural = "页面访问记录"

class OutboundClick(models.Model):
    site = models.ForeignKey("operations.Site", on_delete=models.SET_NULL, null=True, blank=True)
    campaign = models.CharField(max_length=120, blank=True)
    drama = models.ForeignKey("drama.Drama", on_delete=models.CASCADE, related_name="outbound_clicks")
    link = models.ForeignKey("drama.DramaLink", on_delete=models.CASCADE)
    referrer = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "外链点击记录"
        verbose_name_plural = "外链点击记录"

class AdEvent(models.Model):
    ad = models.ForeignKey("advertising.AdPosition", on_delete=models.CASCADE)
    site = models.ForeignKey("operations.Site", on_delete=models.CASCADE)
    kind = models.CharField(max_length=12, choices=[("impression", "展示"), ("click", "点击")])
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class PlatformClick(models.Model):
    platform = models.ForeignKey("platforms.Platform", on_delete=models.PROTECT, related_name="navigation_clicks")
    site = models.ForeignKey("operations.Site", on_delete=models.SET_NULL, null=True, blank=True)
    destination_kind = models.CharField(max_length=12, choices=[("website", "官网"), ("android", "Google Play"), ("ios", "App Store")])
    campaign = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "平台导航点击"
        verbose_name_plural = "平台导航点击"
