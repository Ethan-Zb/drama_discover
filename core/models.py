from django.db import models

class SiteSetting(models.Model):
    site_name = models.CharField("网站名称", max_length=100, default="Drama Discover")
    site_description = models.CharField("网站描述", max_length=255, blank=True)
    google_analytics_id = models.CharField("GA4 Measurement ID", max_length=40, blank=True)
    adsense_client_id = models.CharField("AdSense Client ID", max_length=100, blank=True)
    contact_email = models.EmailField("联系邮箱", blank=True)

    class Meta:
        verbose_name = "网站设置"
        verbose_name_plural = "网站设置"

    def __str__(self):
        return self.site_name
