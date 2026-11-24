from django.urls import path

from apps.projects import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("<slug:slug>/", views.ProjectDetailView.as_view(), name="detail"),
]
