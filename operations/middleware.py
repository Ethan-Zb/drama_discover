from urllib.parse import urlsplit
from django.conf import settings
from django.http import HttpResponseNotFound
from django.http.request import split_domain_port
from .models import Site


class SiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host, port = split_domain_port(request.META.get("HTTP_HOST", request.META.get("SERVER_NAME", "")).lower())
        local = host in settings.CMS_LOCAL_HOSTS
        request.site = Site.objects.filter(is_active=True, is_default=True).first() if local else Site.objects.filter(domain=host, is_active=True).first()
        if not host or (not local and not request.site):
            return HttpResponseNotFound("Unknown or inactive site")
        if not request.site and not request.path.startswith(("/cms", "/admin", "/static", "/media")):
            return HttpResponseNotFound("No active default site configured")
        response = self.get_response(request)
        if (request.method == "GET" and response.status_code == 200 and request.site
                and response.get("Content-Type", "").startswith("text/html")
                and not request.path.startswith(("/cms", "/admin", "/static", "/media"))
                and "bot" not in request.META.get("HTTP_USER_AGENT", "").lower()):
            from analytics.models import PageView
            from drama.models import Drama
            drama = None
            if request.resolver_match and request.resolver_match.view_name == "drama:detail":
                drama = Drama.objects.filter(slug=request.resolver_match.kwargs.get("slug")).first()
            try:
                referrer = urlsplit(request.META.get("HTTP_REFERER", "")).hostname or ""
            except ValueError:
                referrer = ""
            PageView.objects.create(site=request.site, drama=drama, path=request.path[:500], referrer=referrer[:500])
        return response
