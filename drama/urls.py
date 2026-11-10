from django.urls import path
from . import views

app_name = "drama"
urlpatterns = [
    path("", views.list_view, name="list"),
    path("category/<slug:slug>/", views.category_view, name="category"),
    path("<slug:slug>/", views.detail, name="detail"),
]
