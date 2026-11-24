from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("projects/", include("apps.projects.urls")),
    path("cv/", include("apps.cv.urls")),
    path("contact/", include("apps.contact.urls")),
    path("", include("apps.core.urls")),
]
