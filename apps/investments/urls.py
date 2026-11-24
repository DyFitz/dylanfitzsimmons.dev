from django.urls import path

from apps.investments import views

app_name = "investments"

urlpatterns = [
    path("", views.InvestmentsView.as_view(), name="page"),
]
