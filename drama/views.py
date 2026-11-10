from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import Category
from operations.services import public_dramas, eligible_links, structured_data
from core.views import ad_context

def list_view(request):
    return render(request, "drama/list.html", {"dramas": public_dramas(request.site)})

def category_view(request, slug):
    dramas = public_dramas(request.site)
    category = get_object_or_404(Category.objects.distinct(), slug=slug, drama__pk__in=[d.pk for d in dramas])
    return render(request, "drama/list.html", {"dramas": [d for d in dramas if d.category_id == category.pk], "current_category": category})

def detail(request, slug):
    drama = next(iter(public_dramas(request.site, slug=slug)), None)
    if not drama:
        raise Http404
    canonical = f"https://{request.site.domain}{drama.get_absolute_url()}"
    return render(request, "drama/detail.html", {"drama": drama, "canonical": canonical, "structured_json": structured_data(drama, canonical), "viewing_links": eligible_links(drama, request.site), **ad_context(request, "detail")})
