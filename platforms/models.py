from django.db import models
from django.utils.translation import gettext_lazy as _

class Platform(models.Model):
    class Status(models.TextChoices):
        NEEDS_REVIEW = "needs_review", "待核实"
        VERIFIED = "verified", "已核实"
        INACTIVE = "inactive", "已停用"

    class PlatformType(models.TextChoices):
        APP = "app", "移动应用"
        WEB = "web", "网站"
        APP_WEB = "app_web", "应用+网站"
        DISTRIBUTOR = "distributor", "发行/内容平台"

    name = models.CharField("平台名称", max_length=120, unique=True)
    slug = models.SlugField("URL 标识", max_length=140, unique=True)
    country = models.CharField("总部/来源地区", max_length=80, blank=True)
    audience_region = models.CharField("服务区域分类", max_length=12, choices=[("overseas", _("Overseas")), ("domestic", _("Domestic"))], default="overseas")
    market = models.CharField("主要目标市场", max_length=160, blank=True)
    platform_type = models.CharField("平台类型", max_length=20, choices=PlatformType.choices, default=PlatformType.APP)
    website = models.URLField("官方网站", blank=True)
    verification_url = models.URLField("入口核实依据（官网或官方商店）", max_length=500, blank=True)
    link_checked_at = models.DateTimeField("入口核实时间", null=True, blank=True)
    ios_url = models.URLField("iOS 应用商店链接", blank=True)
    android_url = models.URLField("Android 应用商店链接", blank=True)
    logo_url = models.URLField("Logo 图片地址", blank=True)
    description = models.TextField("平台简介", blank=True)
    rank = models.PositiveSmallIntegerField("参考收录排序", default=0)
    source_note = models.CharField("收录依据", max_length=255, blank=True)
    status = models.CharField("核验状态", max_length=20, choices=Status.choices, default=Status.NEEDS_REVIEW)
    is_featured = models.BooleanField("首页推荐", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "短剧平台"
        verbose_name_plural = "短剧平台"
        ordering = ["rank", "name"]

    def __str__(self):
        return self.name
