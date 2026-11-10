from django.db import models

from operations.models import public_url

class AdPosition(models.Model):
    site = models.ForeignKey("operations.Site", on_delete=models.PROTECT, null=True, blank=True, verbose_name="站点")
    placement = models.CharField("展示位置", max_length=20, choices=[("home", "首页"), ("detail", "详情页")], default="home")
    headline = models.CharField("广告标题", max_length=160, blank=True)
    target_url = models.URLField("推广目标地址", blank=True, validators=[public_url])
    image_url = models.URLField("横幅图片地址", blank=True, validators=[public_url])
    starts_at = models.DateTimeField("开始时间", null=True, blank=True)
    ends_at = models.DateTimeField("结束时间", null=True, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError("结束时间必须晚于开始时间。")
        if self.is_active and (not self.site_id or not self.target_url or not self.headline):
            raise ValidationError("启用广告需要选择站点、填写标题和目标地址。")
    name = models.CharField("广告位名称", max_length=100)
    code = models.SlugField("广告位代码", unique=True)
    description = models.CharField("描述", max_length=255, blank=True)
    ad_code = models.TextField("广告代码", blank=True, help_text="仅粘贴你自己 AdSense 账号生成的代码。")
    is_active = models.BooleanField("启用", default=False)

    class Meta:
        verbose_name = "广告位"
        verbose_name_plural = "广告位"

    def __str__(self):
        return self.name
