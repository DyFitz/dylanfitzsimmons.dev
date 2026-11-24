from django.contrib.sitemaps.views import sitemap
from django.urls import path

from apps.core import views
from apps.core.sitemaps import SITEMAPS

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("robots.txt", views.RobotsTxtView.as_view(), name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
]
