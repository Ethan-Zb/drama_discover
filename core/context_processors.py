from .models import SiteSetting

def site_settings(request):
    return {"site_setting": getattr(request, "site", None) or SiteSetting.objects.first(), "current_site": getattr(request, "site", None)}
