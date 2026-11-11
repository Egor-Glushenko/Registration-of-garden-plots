"""Domain operations of the registry (PR11).

The functions keep the plot state in sync with the lease register: an active
lease marks the plot as leased, and the cancellation releases it again.
"""
from django.db import transaction

from .models import LeaseStatus, PlotStatus


@transaction.atomic
def save_lease(lease):
    """Save a lease and update the plot status accordingly."""
    lease.save()
    sync_plot_status(lease.plot)
    return lease


@transaction.atomic
def cancel_lease(lease):
    """Cancel a lease instead of deleting it and release the plot."""
    lease.cancel()
    sync_plot_status(lease.plot)
    return lease


@transaction.atomic
def cancel_payment(payment):
    """Cancel a payment keeping the financial history."""
    payment.cancel()
    return payment


def sync_plot_status(plot):
    """Recalculate the plot status from its active leases."""
    active_leases = plot.leases.filter(status=LeaseStatus.ACTIVE)
    if active_leases.exists():
        lease = active_leases.order_by("-start_date").first()
        changed = False
        if plot.status != PlotStatus.LEASED:
            plot.status = PlotStatus.LEASED
            changed = True
        if plot.owner_id is None and lease.owner_id:
            plot.owner = lease.owner
            changed = True
        if changed:
            plot.save(update_fields=["status", "owner", "updated_at"])
        return plot

    if plot.status == PlotStatus.LEASED:
        plot.status = PlotStatus.OCCUPIED if plot.owner_id else PlotStatus.FREE
        plot.save(update_fields=["status", "updated_at"])
    return plot
