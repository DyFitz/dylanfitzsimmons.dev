from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("robots.txt", views.RobotsTxtView.as_view(), name="robots_txt"),
]
