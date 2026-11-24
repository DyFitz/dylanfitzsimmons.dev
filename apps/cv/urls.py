from django.urls import path

from apps.cv import views

app_name = "cv"

urlpatterns = [
    path("", views.CvView.as_view(), name="page"),
]
