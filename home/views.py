from django.shortcuts import render

from registry import queries


def index(request):
    return render(request, "home/index.html", {"stats": queries.dashboard_stats()})


def not_found(request, exception):
    return render(request, "404.html", status=404)
