from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views
from platforms import views as platform_views

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("platform-go/<int:pk>/", platform_views.go, name="platform_go"),
    path("cms/", include("operations.urls")),
    path("ad-click/<int:pk>/", core_views.ad_click, name="ad_click"),
    path("admin/", admin.site.urls),
    path("", core_views.home, name="home"),
    path("search/", core_views.search, name="search"),
    path("go/<int:link_id>/", core_views.go_to_source, name="go_to_source"),
    path("drama/", include("drama.urls")),
    path("ads.txt", core_views.ads_txt, name="ads_txt"),
    path("robots.txt", core_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", core_views.sitemap, name="sitemap"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
