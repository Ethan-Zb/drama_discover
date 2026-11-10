from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "operations"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", auth_views.LoginView.as_view(template_name="operations/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("import/", views.import_csv, name="import"),
    path("export/", views.export_csv, name="export"),
    path("bulk/", views.bulk, name="bulk"),
    path("prepare/", views.prepare_pages, name="prepare"),
    path("<slug:entity>/", views.listing, name="list"),
    path("<slug:entity>/new/", views.edit, name="new"),
    path("<slug:entity>/<int:pk>/", views.edit, name="edit"),
]
