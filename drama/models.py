from django.db import models
from django.urls import reverse
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField("分类名称", max_length=80, unique=True)
    slug = models.SlugField("URL 标识", max_length=100, unique=True)
    description = models.CharField("分类描述", max_length=255, blank=True)

    class Meta:
        verbose_name = "短剧分类"
        verbose_name_plural = "短剧分类"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Drama(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"
        HIDDEN = "hidden", "隐藏"

    title = models.CharField("短剧名称", max_length=200)
    slug = models.SlugField("URL 标识", max_length=220, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="分类")
    description = models.TextField("剧情简介")
    cover = models.ImageField("封面图片", upload_to="drama_covers/", blank=True, null=True)
    language = models.CharField("语言", max_length=40, default="English")
    tags = models.CharField("标签（逗号分隔）", max_length=500, blank=True)
    episode_count = models.PositiveIntegerField("集数", default=1)
    release_year = models.PositiveIntegerField("年份", blank=True, null=True)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.DRAFT)
    meta_title = models.CharField("SEO Title", max_length=255, blank=True)
    meta_description = models.CharField("SEO Description", max_length=320, blank=True)
    canonical_url = models.URLField("Canonical URL", blank=True)
    rights_status = models.CharField("版权/授权状态", max_length=100, default="待核验")
    rights_holder = models.CharField("权利人/授权方", max_length=200, blank=True)
    rights_scope = models.CharField("授权范围", max_length=255, blank=True)
    rights_expires_at = models.DateField("授权到期日", blank=True, null=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "短剧"
        verbose_name_plural = "短剧"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("drama:detail", kwargs={"slug": self.slug})

class DramaLink(models.Model):
    source = models.ForeignKey("operations.ContentSource", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="授权来源")
    drama = models.ForeignKey(Drama, on_delete=models.CASCADE, related_name="links", verbose_name="短剧")
    label = models.CharField("链接名称", max_length=100, default="Watch on official platform")
    platform_name = models.CharField("平台名称", max_length=100)
    url = models.URLField("官方观看地址")
    is_official = models.BooleanField("是否官方/授权链接", default=False)
    is_active = models.BooleanField("启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "观看链接"
        verbose_name_plural = "观看链接"

    def __str__(self):
        return f"{self.drama.title} - {self.platform_name}"
