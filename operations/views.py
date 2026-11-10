import csv
import io
from collections import Counter
from datetime import datetime, time, timedelta
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from analytics.models import PageView, OutboundClick, AdEvent, PlatformClick
from .models import Site, Publication, ContentSource
from .forms import ENTITIES, entity_form, ImportForm
from .services import generate_seo


def staff(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def permission(request, model, action):
    if not request.user.has_perm(f"{model._meta.app_label}.{action}_{model._meta.model_name}"):
        raise PermissionDenied


def context(**kwargs):
    return {"navigation": [(key, entry[1]) for key, entry in ENTITIES.items()], **kwargs}


def scoped(qs, request):
    site = request.GET.get("site", "")
    return qs.filter(site_id=site) if site.isdigit() else qs


@staff
def dashboard(request):
    for model in (PageView, OutboundClick, AdEvent, PlatformClick, Publication, ContentSource, Site):
        permission(request, model, "view")
    try:
        days = min(max(int(request.GET.get("days", 7)), 1), 90)
    except ValueError:
        days = 7
    first_day = timezone.localdate() - timedelta(days=days - 1)
    start = timezone.make_aware(datetime.combine(first_day, time.min))
    views = scoped(PageView.objects.filter(created_at__gte=start), request)
    clicks = scoped(OutboundClick.objects.filter(created_at__gte=start), request)
    ads = scoped(AdEvent.objects.filter(created_at__gte=start), request)
    platform_clicks = scoped(PlatformClick.objects.filter(created_at__gte=start), request)
    # MySQL installations often lack named timezone tables. Group actual UTC
    # timestamps in Python so Asia/Shanghai dates never collapse into NULL.
    daily = Counter(timezone.localdate(stamp) for stamp in views.values_list("created_at", flat=True).iterator())
    dates = [timezone.localdate() - timedelta(days=n) for n in range(days - 1, -1, -1)]
    maximum = max([daily.get(day, 0) for day in dates] + [1])
    chart = [{"label": day.strftime("%m-%d"), "count": daily.get(day, 0), "height": max(2, daily.get(day, 0) * 100 / maximum)} for day in dates]
    selected = request.GET.get("site", "")
    pubs = scoped(Publication.objects.all(), request)
    return render(request, "operations/dashboard.html", context(title="运营概览", sites=Site.objects.all(), selected_site=selected, days=days,
        metrics=[("页面访问 PV", views.count()), ("平台导航点击", platform_clicks.count()), ("已发布页面", pubs.filter(status="published").count()), ("广告点击", ads.filter(kind="click").count())], chart=chart,
        platform_report=platform_clicks.values("site__name", "platform__name", "destination_kind", "campaign").annotate(total=Count("id")).order_by("-total")[:50],
        page_report=views.values("site__name", "path").annotate(total=Count("id")).order_by("-total")[:15],
        drama_report=views.filter(drama__isnull=False).values("site__name", "drama__title").annotate(total=Count("id")).order_by("-total")[:15],
        link_report=clicks.values("site__name", "link__platform_name", "link_id", "drama__title", "campaign").annotate(total=Count("id")).order_by("-total")[:15],
        ad_report=ads.values("site__name", "ad__name").annotate(impressions=Count("id", filter=Q(kind="impression")), clicks=Count("id", filter=Q(kind="click"))).order_by("-clicks")[:15],
        pending=pubs.filter(status="draft").count(), source_count=ContentSource.objects.filter(is_verified=True, is_active=True).count()))


@staff
def listing(request, entity):
    if entity not in ENTITIES:
        raise Http404
    model, title, fields, searches = ENTITIES[entity]
    permission(request, model, "view")
    qs = model.objects.all().order_by("-pk")
    query = request.GET.get("q", "").strip()[:200]
    if query:
        condition = Q()
        for field in searches:
            condition |= Q(**{field + "__icontains": query})
        qs = qs.filter(condition)
    if entity in {"publications", "ads"}:
        qs = scoped(qs.select_related("site"), request)
    state = request.GET.get("status", "")
    if state and "status" in fields:
        qs = qs.filter(status=state)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    rows = []
    for obj in page:
        label = str(obj)
        state_label = obj.get_status_display() if hasattr(obj, "get_status_display") else ("启用" if getattr(obj, "is_active", True) else "停用")
        if entity == "sources":
            state_label = "已到期" if obj.expires_at and obj.expires_at < timezone.localdate() else ("已核验" if obj.is_verified else "待核验")
        detail = getattr(obj, "domain", "") or getattr(obj, "market", "") or str(getattr(obj, "site", "") or "")
        rows.append({"obj": obj, "label": label, "status": state_label, "detail": detail})
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "operations/list.html", context(entity=entity, title=title, rows=rows, page=page, query=query, sites=Site.objects.all(), selected_site=request.GET.get("site", ""), status=state,
        query_params=params.urlencode(), can_prepare=entity == "dramas" and request.user.has_perm("operations.add_publication"), can_add=request.user.has_perm(f"{model._meta.app_label}.add_{model._meta.model_name}"), can_change=request.user.has_perm(f"{model._meta.app_label}.change_{model._meta.model_name}")))


@staff
def edit(request, entity, pk=None):
    if entity not in ENTITIES:
        raise Http404
    model, title, fields, searches = ENTITIES[entity]
    permission(request, model, "change" if pk else "add")
    obj = get_object_or_404(model, pk=pk) if pk else None
    form = entity_form(entity)(request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "已保存。")
        return redirect("operations:list", entity=entity)
    return render(request, "operations/form.html", context(title=("编辑" if pk else "新增") + title, form=form, entity=entity))


@staff
@require_POST
def bulk(request):
    permission(request, Publication, "change")
    ids = request.POST.getlist("selected")[:500]
    if not ids or not all(item.isdigit() for item in ids):
        messages.error(request, "请先选择发布记录。")
        return redirect("operations:list", entity="publications")
    action = request.POST.get("action")
    if action not in {"seo", "publish", "unpublish"}:
        messages.error(request, "无效的批量操作。")
        return redirect("operations:list", entity="publications")
    successes, errors = 0, []
    with transaction.atomic():
        for pub in Publication.objects.select_for_update().filter(pk__in=ids).select_related("drama", "site"):
            try:
                if action == "seo":
                    generate_seo(pub)
                else:
                    pub.status = "published" if action == "publish" else "draft"
                    pub.full_clean()
                    pub.save(update_fields=["status", "updated_at"])
                successes += 1
            except ValidationError as exc:
                errors.append(f"{pub.drama.title}: {'; '.join(exc.messages)}")
    if successes:
        messages.success(request, f"已处理 {successes} 条记录。")
    for error in errors[:8]:
        messages.error(request, error)
    return redirect("operations:list", entity="publications")


@staff
@require_POST
def prepare_pages(request):
    from drama.models import Drama
    permission(request, Drama, "view")
    permission(request, Publication, "add")
    site = get_object_or_404(Site, pk=request.POST.get("site") if request.POST.get("site", "").isdigit() else 0, is_active=True)
    ids = request.POST.getlist("selected")[:500]
    if not ids or not all(value.isdigit() for value in ids):
        messages.error(request, "请先选择短剧。")
        return redirect("operations:list", entity="dramas")
    count = 0
    with transaction.atomic():
        for drama in Drama.objects.filter(pk__in=ids):
            pub, created = Publication.objects.get_or_create(site=site, drama=drama, defaults={"summary": drama.description, "status": "draft"})
            count += int(created)
    messages.success(request, f"已创建 {count} 条本站草稿；已有记录保持原状。请编辑原创简介并核验授权。")
    return redirect("operations:list", entity="publications")


@staff
def import_csv(request):
    from drama.models import Drama
    permission(request, Drama, "add")
    permission(request, Publication, "add")
    form = ImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        upload = form.cleaned_data["file"]
        try:
            if upload.size > 2 * 1024 * 1024:
                raise ValidationError("文件不能超过 2 MB。")
            reader = csv.DictReader(io.StringIO(upload.read().decode("utf-8-sig")), strict=True)
            if not reader.fieldnames or not {"title", "description"}.issubset(reader.fieldnames) or len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise ValidationError("表头必须包含 title、description，且不能有重复列名。")
            rows = list(reader)
            if not rows or len(rows) > 500:
                raise ValidationError("CSV 需要 1 至 500 行。")
            with transaction.atomic():
                for number, row in enumerate(rows, 2):
                    if None in row or any(value is None for value in row.values()):
                        raise ValidationError(f"第 {number} 行列数与表头不一致。")
                    title, description = (row.get("title") or "").strip(), (row.get("description") or "").strip()
                    slug = (row.get("slug") or "").strip() or slugify(title, allow_unicode=False)
                    if not title or not description or not slug:
                        raise ValidationError(f"第 {number} 行缺少 title、description 或有效 slug。")
                    if Drama.objects.filter(slug=slug).exists():
                        raise ValidationError(f"第 {number} 行 slug 已存在；导入已回滚，请在后台编辑已有记录。")
                    drama = Drama(title=title, slug=slug, description=description, language=row.get("language") or "English", tags=row.get("tags", ""), status="draft")
                    drama.full_clean()
                    drama.save()
                    Publication.objects.create(site=form.cleaned_data["site"], drama=drama, summary=description)
            messages.success(request, f"已导入 {len(rows)} 部短剧和草稿发布记录，待核验后发布。")
            return redirect("operations:list", entity="publications")
        except (ValidationError, UnicodeError, csv.Error) as exc:
            form.add_error("file", "; ".join(exc.messages) if isinstance(exc, ValidationError) else "文件编码或 CSV 格式无效。")
    return render(request, "operations/form.html", context(title="批量导入短剧", form=form, entity="dramas", import_help=True))


def csv_safe(value):
    value = str(value or "")
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


@staff
def export_csv(request):
    permission(request, Publication, "view")
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="publications.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["site", "title", "slug", "description", "status", "meta_title", "meta_description"])
    for pub in scoped(Publication.objects.select_related("drama", "site"), request):
        writer.writerow([csv_safe(value) for value in [pub.site.domain, pub.drama.title, pub.drama.slug, pub.summary, pub.status, pub.meta_title, pub.meta_description]])
    return response
