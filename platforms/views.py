from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.views.decorators.http import require_safe
from analytics.models import PlatformClick
from .services import site_platforms, destinations


@require_safe
def go(request, pk):
    platform = get_object_or_404(site_platforms(request.site), pk=pk)
    targets = destinations(platform)
    selected = request.GET.get("target")
    target = next((item for item in targets if item["kind"] == selected), None) if selected is not None else next(iter(targets), None)
    if not target:
        raise Http404("No verified destination configured")
    if request.method == "GET":
        PlatformClick.objects.create(site=request.site, platform=platform, destination_kind=target["kind"], campaign=request.GET.get("utm_campaign", "")[:120])
    response = redirect(target["url"])
    response["Cache-Control"] = "no-store"
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Referrer-Policy"] = "no-referrer"
    return response
