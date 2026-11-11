"""Shared test data factories for the registry test suite."""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from registry.models import Lease, LeaseStatus, Owner, Payment, Plot, PlotStatus


def make_owner(index=1, **kwargs):
    defaults = {
        "full_name": f"Тестовый владелец {index}",
        "phone": f"+7 900 000-00-{index:02d}",
        "email": f"owner{index}@example.org",
    }
    defaults.update(kwargs)
    return Owner.objects.create(**defaults)


def make_plot(index=1, owner=None, status=PlotStatus.FREE, **kwargs):
    defaults = {
        "plot_number": str(index),
        "area_sqm": Decimal("600.00"),
        "status": status,
        "owner": owner,
        "debt": Decimal("0.00"),
    }
    defaults.update(kwargs)
    return Plot.objects.create(**defaults)


def make_payment(owner, amount="4500.00", status="posted", **kwargs):
    defaults = {
        "owner": owner,
        "amount": Decimal(amount),
        "payment_date": timezone.localdate() - timedelta(days=10),
        "description": "Членский взнос",
        "status": status,
    }
    defaults.update(kwargs)
    return Payment.objects.create(**defaults)


def make_lease(plot, owner, status=LeaseStatus.ACTIVE, start=None, end=None, **kwargs):
    start = start or timezone.localdate() + timedelta(days=1)
    end = end or start + timedelta(days=30)
    return Lease.objects.create(
        plot=plot,
        owner=owner,
        start_date=start,
        end_date=end,
        status=status,
        **kwargs,
    )
