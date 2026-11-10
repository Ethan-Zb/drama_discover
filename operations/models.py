import ipaddress
from urllib.parse import urlsplit
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from django.utils import timezone


def public_url(value):
    URLValidator(schemes=["http", "https"])(value)
    parsed = urlsplit(value)
    if parsed.username or parsed.password or not parsed.hostname or parsed.hostname.lower() in {"localhost", "localhost.localdomain"}:
        raise ValidationError("请填写公开的 HTTP/HTTPS 地址，不要包含账号密码。")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        return
    if not address.is_global:
        raise ValidationError("不能使用本地或内网地址。")


class Site(models.Model):
    name = models.CharField("站点名称", max_length=100)
    domain = models.CharField("域名（不含协议和端口）", max_length=253, unique=True, validators=[RegexValidator(r"^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$", "请使用小写域名。")])
    description = models.CharField("站点介绍", max_length=255, blank=True)
    contact_email = models.EmailField("联系邮箱", blank=True)
    is_active = models.BooleanField("启用", default=True)
    is_default = models.BooleanField("本机默认站点", default=False)
    platforms = models.ManyToManyField("platforms.Platform", blank=True, verbose_name="收录平台（默认站点展示全部）")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        if self.is_default and Site.objects.filter(is_default=True).exclude(pk=self.pk).exists():
            raise ValidationError({"is_default": "已有默认站点，请先取消原站点的默认状态。"})

    @property
    def site_name(self):
        return self.name

    @property
    def site_description(self):
        return self.description

    def __str__(self):
        return self.name


class ContentSource(models.Model):
    name = models.CharField("来源名称", max_length=120)
    domain = models.CharField("授权链接域名", max_length=253, validators=Site._meta.get_field("domain").validators[:1])
    rights_holder = models.CharField("权利人", max_length=200)
    evidence = models.TextField("授权依据 / 合同编号（仅后台）", help_text="填写可追溯的授权依据，人工核验后才能启用。")
    scope = models.TextField("授权范围", blank=True)
    expires_at = models.DateField("到期日", null=True, blank=True)
    is_verified = models.BooleanField("已人工核验授权", default=False)
    is_active = models.BooleanField("启用", default=True)
    allowed_sites = models.ManyToManyField(Site, blank=True, verbose_name="许可站点（留空表示所有受许可站点）")
    updated_at = models.DateTimeField(auto_now=True)

    def valid_for(self, site):
        sites = list(self.allowed_sites.all())
        return bool(self.is_active and self.is_verified and self.evidence.strip() and self.rights_holder.strip()
                    and (not self.expires_at or self.expires_at >= timezone.localdate())
                    and (not sites or any(allowed.pk == site.pk for allowed in sites)))

    def __str__(self):
        return self.name


class Publication(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"
    site = models.ForeignKey(Site, on_delete=models.PROTECT, verbose_name="站点")
    drama = models.ForeignKey("drama.Drama", on_delete=models.CASCADE, related_name="publications", verbose_name="短剧")
    summary = models.TextField("本站原创简介", blank=True, help_text="请人工撰写或提供已获授权且适用于本站的原创文案。")
    originality_confirmed = models.BooleanField("已确认文案原创或具备发布许可", default=False)
    meta_title = models.CharField("SEO 标题", max_length=255, blank=True)
    meta_description = models.CharField("SEO 摘要", max_length=320, blank=True)
    status = models.CharField("发布状态", choices=Status.choices, default=Status.DRAFT, max_length=20)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["site", "drama"], name="unique_site_drama")]

    def publish_errors(self):
        errors = []
        if self.drama.status == "hidden":
            errors.append("短剧已被全局隐藏。")
        if not self.originality_confirmed or len(self.summary.strip()) < 80:
            errors.append("需要至少 80 字符的原创简介，并确认原创或发布许可。")
        if not self.site.is_active:
            errors.append("站点未启用。")
        if self.drama.rights_expires_at and self.drama.rights_expires_at < timezone.localdate():
            errors.append("短剧授权已到期。")
        from .services import eligible_links
        if not eligible_links(self.drama, self.site):
            errors.append("需要至少一个已核验、未到期且域名匹配的授权来源链接。")
        return errors

    def clean(self):
        if self.status == self.Status.PUBLISHED and self.site_id and self.drama_id:
            errors = self.publish_errors()
            if errors:
                raise ValidationError(" ".join(errors))

    def __str__(self):
        return f"{self.site} · {self.drama}"
