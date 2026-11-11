"""Views of the registry. All data is read through the ORM layer (PR9)."""
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode

from . import queries
from .models import Lease, LeaseStatus, PaymentStatus, Plot, PlotStatus

PAGE_SIZE = queries.PER_PAGE


def _page_number(request):
    """Read a page number, tolerating invalid values."""
    try:
        return max(int(request.GET.get("page", 1)), 1)
    except (TypeError, ValueError):
        return 1


def _querystring(request, drop=("page",)):
    """Rebuild the current filter string for pagination links."""
    params = {key: value for key, value in request.GET.items() if key not in drop and value}
    return urlencode(params)


def plots(request):
    """Plot list with search, status filter, sorting and pagination."""
    status = request.GET.get("status", "").strip()
    if status not in PlotStatus.values:
        status = ""
    query = request.GET.get("q", "").strip()
    ordering = request.GET.get("ordering", queries.DEFAULT_PLOT_ORDERING)
    page = queries.plot_page(
        status=status,
        query=query,
        ordering=ordering,
        page=_page_number(request),
    )
    return render(request, "registry/plots.html", {
        "page_obj": page,
        "plots": page.object_list,
        "querystring": _querystring(request),
        "status": status,
        "query": query,
        "ordering": ordering,
        "statuses": PlotStatus.choices,
        "orderings": (
            ("number", "По номеру"),
            ("area", "По площади"),
            ("debt", "По задолженности"),
            ("status", "По статусу"),
        ),
    })


def plot_detail(request, slug):
    """Plot card opened by a slug; unknown slugs return 404."""
    plot = queries.plot_get(slug)
    if plot is None:
        raise Http404("Участок не найден")
    return render(request, "registry/plot_detail.html", {
        "plot": plot,
        "leases": plot.leases.select_related("owner"),
        "payments": plot.owner.payments.posted()[:5] if plot.owner_id else [],
    })


def plot_detail_by_id(request, plot_id):
    """Legacy numeric address kept for the links created before PR9."""
    plot = Plot.objects.filter(pk=plot_id).only("slug").first()
    if plot is None:
        raise Http404("Участок не найден")
    return redirect(reverse("registry:plot_detail", kwargs={"slug": plot.slug}), permanent=True)


def owners(request):
    query = request.GET.get("q", "").strip()
    page = queries.owner_page(query=query, page=_page_number(request))
    return render(request, "registry/owners.html", {
        "page_obj": page,
        "owners": page.object_list,
        "query": query,
        "querystring": _querystring(request),
    })


def payments(request):
    status = request.GET.get("status", "").strip()
    if status not in PaymentStatus.values:
        status = ""
    ordering = request.GET.get("ordering", queries.DEFAULT_PAYMENT_ORDERING)
    query = request.GET.get("q", "").strip()
    page = queries.payment_page(
        query=query,
        status=status,
        ordering=ordering,
        page=_page_number(request),
    )
    return render(request, "registry/payments.html", {
        "page_obj": page,
        "payments": page.object_list,
        "query": query,
        "status": status,
        "ordering": ordering,
        "querystring": _querystring(request),
        "statuses": PaymentStatus.choices,
        "orderings": (
            ("date", "По дате"),
            ("amount", "По сумме"),
            ("owner", "По владельцу"),
        ),
    })


def leases(request):
    """Lease list: filtering, sorting and pagination live in the query layer."""
    status = request.GET.get("status", "").strip()
    if status not in LeaseStatus.values:
        status = ""
    ordering = request.GET.get("ordering", queries.DEFAULT_LEASE_ORDERING)
    today = _today()
    page = queries.lease_page(
        status=status,
        ordering=ordering,
        page=_page_number(request),
        date_from=today if request.GET.get("future") == "1" else None,
    )
    return render(request, "registry/leases.html", {
        "page_obj": page,
        "leases": page.object_list,
        "querystring": _querystring(request),
        "status": status,
        "ordering": ordering,
        "statuses": LeaseStatus.choices,
        "orderings": (
            ("start", "По дате начала"),
            ("plot", "По участку"),
            ("owner", "По арендатору"),
        ),
        "future": request.GET.get("future") == "1",
    })


def lease_detail(request, pk):
    lease = Lease.objects.with_related().filter(pk=pk).first()
    if lease is None:
        raise Http404("Аренда не найдена")
    return render(request, "registry/lease_detail.html", {"lease": lease})


def statistics(request):
    return render(request, "registry/statistics.html", {"stats": queries.statistics()})


def _today():
    from django.utils import timezone

    return timezone.localdate()
