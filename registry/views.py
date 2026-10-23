from django.shortcuts import render

from .database import (
    get_owner_rows,
    get_payment_rows,
    get_plot_by_id,
    get_plot_rows,
    get_statistics,
)


def plots(request):
    status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    return render(request, "registry/plots.html", {
        "plots": get_plot_rows(status=status, query=query),
        "status": status,
        "query": query,
        "statuses": (("free", "Свободен"), ("occupied", "Занят"), ("leased", "Аренда"), ("disputed", "Спорный")),
    })


def plot_detail(request, plot_id):
    plot = get_plot_by_id(plot_id)
    if plot is None:
        return render(request, "404.html", status=404)
    return render(request, "registry/plot_detail.html", {"plot": plot})


def owners(request):
    return render(request, "registry/owners.html", {"owners": get_owner_rows()})


def payments(request):
    return render(request, "registry/payments.html", {"payments": get_payment_rows()})


def statistics(request):
    return render(request, "registry/statistics.html", {"stats": get_statistics()})
