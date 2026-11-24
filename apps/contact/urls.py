from django.urls import path

from apps.contact import views

app_name = "contact"

urlpatterns = [
    path("", views.ContactView.as_view(), name="page"),
    path("sent/", views.SentView.as_view(), name="sent"),
]
