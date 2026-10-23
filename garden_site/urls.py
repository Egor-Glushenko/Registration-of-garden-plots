from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls")),
    path("registry/", include("registry.urls")),
]

handler404 = "home.views.not_found"
