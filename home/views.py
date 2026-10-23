from django.shortcuts import render

from registry.database import get_dashboard_stats


def index(request):
    return render(request, "home/index.html", {"stats": get_dashboard_stats()})


def not_found(request, exception):
    return render(request, "404.html", status=404)
