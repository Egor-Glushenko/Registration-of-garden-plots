"""ORM query layer of the registry (PR9).

Every function returns model instances or plain dictionaries built by the ORM:
the views no longer execute hand-written SQL. QuerySets use ``select_related``,
``annotate``, ``aggregate`` and ``Paginator`` so that pages stay fast and the
business rules live in one place.
"""
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Avg, Count, Max, Min, Q, Sum

from .models import Lease, LeaseStatus, Owner, Payment, Plot, PlotStatus

PLOT_ORDERINGS = {
    "number": ("plot_number",),
    "area": ("-area_sqm", "plot_number"),
    "debt": ("-debt", "plot_number"),
    "status": ("status", "plot_number"),
}
DEFAULT_PLOT_ORDERING = "number"

PAYMENT_ORDERINGS = {
    "date": ("-payment_date", "-id"),
    "amount": ("-amount", "-payment_date"),
    "owner": ("owner__full_name", "-payment_date"),
}
DEFAULT_PAYMENT_ORDERING = "date"

LEASE_ORDERINGS = {
    "start": ("-start_date", "-id"),
    "plot": ("plot__plot_number",),
    "owner": ("owner__full_name",),
}
DEFAULT_LEASE_ORDERING = "start"

PER_PAGE = 10


def _resolved(ordering, available, default):
    return available.get(ordering, available[default])


def plot_page(status="", query="", ordering=DEFAULT_PLOT_ORDERING, owner=None,
              area_min=None, page=1, per_page=PER_PAGE):
    """Filtered, sorted and paginated plot list."""
    queryset = Plot.objects.with_owner().with_counters()
    queryset = queryset.of_status(status).search(query)
    if owner:
        queryset = queryset.filter(owner=owner)
    if area_min:
        queryset = queryset.filter(area_sqm__gte=area_min)
    queryset = queryset.order_by(*_resolved(ordering, PLOT_ORDERINGS, DEFAULT_PLOT_ORDERING))
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page)


def plot_get(slug):
    """One plot with its owner and related records (no N+1 selects)."""
    return (
        Plot.objects.select_related("owner")
        .prefetch_related("leases__owner", "owner__payments")
        .filter(slug=slug)
        .first()
    )


def plots_for_owner(owner):
    return owner.plots.order_by("plot_number")


def owner_page(query="", page=1, per_page=PER_PAGE):
    """Owners with aggregated plot count and debt."""
    queryset = Owner.objects.with_totals().search(query).order_by("full_name")
    return Paginator(queryset, per_page).get_page(page)


def payment_page(query="", status="", ordering=DEFAULT_PAYMENT_ORDERING, date_from=None,
                 date_to=None, page=1, per_page=PER_PAGE):
    """Payment history with the related owner joined in one query."""
    queryset = Payment.objects.with_owner()
    if status:
        queryset = queryset.filter(status=status)
    if query:
        queryset = queryset.filter(
            Q(owner__full_name__icontains=query) | Q(description__icontains=query)
        )
    if date_from:
        queryset = queryset.filter(payment_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(payment_date__lte=date_to)
    queryset = queryset.order_by(*_resolved(ordering, PAYMENT_ORDERINGS, DEFAULT_PAYMENT_ORDERING))
    return Paginator(queryset, per_page).get_page(page)


def lease_page(plot=None, owner=None, status="", date_from=None, date_to=None,
               ordering=DEFAULT_LEASE_ORDERING, page=1, per_page=PER_PAGE):
    """Lease list with filters used by the lease page and the filter form."""
    queryset = Lease.objects.with_related()
    if plot:
        queryset = queryset.filter(plot=plot)
    if owner:
        queryset = queryset.filter(owner=owner)
    if status:
        queryset = queryset.filter(status=status)
    if date_from:
        queryset = queryset.filter(end_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(start_date__lte=date_to)
    queryset = queryset.order_by(*_resolved(ordering, LEASE_ORDERINGS, DEFAULT_LEASE_ORDERING))
    return Paginator(queryset, per_page).get_page(page)


def available_plots(start_date, end_date=None):
    """Plots without an active lease that intersects the period."""
    end_date = end_date or start_date
    busy = Lease.objects.active().filter(
        start_date__lte=end_date, end_date__gte=start_date
    ).values("plot_id")
    return Plot.objects.with_owner().exclude(pk__in=busy).order_by("plot_number")


def dashboard_stats():
    """Counters for the overview page built with aggregate()."""
    plots = Plot.objects.aggregate(
        plot_count=Count("id"),
        total_debt=Sum("debt"),
        total_area=Sum("area_sqm"),
        average_area=Avg("area_sqm"),
    )
    return {
        "plot_count": plots["plot_count"] or 0,
        "owner_count": Owner.objects.count(),
        "payment_count": Payment.objects.posted().count(),
        "lease_count": Lease.objects.active().count(),
        "total_debt": plots["total_debt"] or Decimal("0.00"),
        "total_area": plots["total_area"] or Decimal("0.00"),
        "average_area": plots["average_area"] or Decimal("0.00"),
    }


def statistics():
    """Analytics page: distributions, averages and debt leaders."""
    summary = dashboard_stats()
    summary["payment_total"] = (
        Payment.objects.posted().aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    )
    by_status = (
        Plot.objects.values("status")
        .annotate(
            plot_count=Count("id"),
            average_area=Avg("area_sqm"),
            debt_total=Sum("debt"),
        )
        .order_by("status")
    )
    top_debtors = (
        Owner.objects.with_totals()
        .filter(total_debt__gt=0)
        .order_by("-total_debt")
        .only("full_name")[:5]
    )
    leases_by_status = (
        Lease.objects.values("status").annotate(total=Count("id")).order_by("status")
    )
    area_bounds = Plot.objects.aggregate(
        smallest=Min("area_sqm"),
        largest=Max("area_sqm"),
    )
    return {
        "summary": summary,
        "by_status": list(by_status),
        "top_debtors": list(top_debtors),
        "leases_by_status": list(leases_by_status),
        "area_bounds": area_bounds,
        "status_labels": dict(PlotStatus.choices),
        "lease_status_labels": dict(LeaseStatus.choices),
    }
