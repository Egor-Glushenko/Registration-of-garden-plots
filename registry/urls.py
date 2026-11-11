from django.urls import path

from . import views

app_name = "registry"

urlpatterns = [
    path("plots/", views.plots, name="plots"),
    path("plots/add/", views.plot_create, name="plot_create"),
    path("plots/id/<int:plot_id>/", views.plot_detail_by_id, name="plot_detail_legacy"),
    path("plots/<slug:slug>/", views.plot_detail, name="plot_detail"),
    path("plots/<slug:slug>/edit/", views.plot_update, name="plot_update"),
    path("owners/", views.owners, name="owners"),
    path("owners/add/", views.owner_create, name="owner_create"),
    path("owners/<int:pk>/edit/", views.owner_update, name="owner_update"),
    path("payments/", views.payments, name="payments"),
    path("payments/add/", views.payment_create, name="payment_create"),
    path("payments/<int:pk>/cancel/", views.payment_cancel, name="payment_cancel"),
    path("leases/", views.leases, name="leases"),
    path("leases/add/", views.lease_create, name="lease_create"),
    path("leases/<int:pk>/", views.lease_detail, name="lease_detail"),
    path("leases/<int:pk>/edit/", views.lease_update, name="lease_update"),
    path("leases/<int:pk>/cancel/", views.lease_cancel, name="lease_cancel"),
    path("statistics/", views.statistics, name="statistics"),
]
