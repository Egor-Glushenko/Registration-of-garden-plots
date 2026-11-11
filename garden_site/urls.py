from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls")),
    path("registry/", include("registry.urls")),
]

# Uploaded images are served by Django only in the development mode (PR11).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SQL panel of the Django Debug Toolbar (PR10).
if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))

handler404 = "home.views.not_found"
