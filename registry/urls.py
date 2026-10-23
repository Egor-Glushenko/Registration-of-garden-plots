from django.urls import path
from . import views

app_name = "registry"
urlpatterns = [
    path("plots/", views.plots, name="plots"),
    path("plots/<int:plot_id>/", views.plot_detail, name="plot_detail"),
    path("owners/", views.owners, name="owners"),
    path("payments/", views.payments, name="payments"),
    path("statistics/", views.statistics, name="statistics"),
]
