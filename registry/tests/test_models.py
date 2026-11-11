"""Model tests: fields, relations, constraints and model methods (PR9)."""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from registry.models import Lease, LeaseStatus, Payment, PaymentStatus, PlotStatus
from registry.slugs import build_plot_slug
from registry.tests.factories import make_lease, make_owner, make_payment, make_plot


class SlugTests(TestCase):
    def test_cyrillic_suffix_is_transliterated(self):
        self.assertEqual(build_plot_slug("16-Б"), "16-b")

    def test_plain_number_keeps_its_form(self):
        self.assertEqual(build_plot_slug(" 25 "), "25")

    def test_empty_number_falls_back(self):
        self.assertEqual(build_plot_slug(""), "plot")

    def test_plot_receives_unique_slug_on_save(self):
        first = make_plot(plot_number="7")
        second = make_plot(plot_number="7-А")
        self.assertEqual(first.slug, "7")
        self.assertEqual(second.slug, "7-a")


class OwnerModelTests(TestCase):
    def test_str_returns_full_name(self):
        owner = make_owner(full_name="Иванова Мария Петровна")
        self.assertEqual(str(owner), "Иванова Мария Петровна")

    def test_debt_total_sums_related_plots(self):
        owner = make_owner()
        make_plot(1, owner=owner, status=PlotStatus.OCCUPIED, debt=Decimal("100.50"))
        make_plot(2, owner=owner, status=PlotStatus.OCCUPIED, debt=Decimal("200.25"))
        self.assertEqual(owner.debt_total(), Decimal("300.75"))

    def test_plot_count_uses_related_manager(self):
        owner = make_owner()
        make_plot(1, owner=owner, status=PlotStatus.OCCUPIED)
        self.assertEqual(owner.plot_count(), 1)


class PlotModelTests(TestCase):
    def test_str_contains_number(self):
        plot = make_plot(plot_number="15-А")
        self.assertEqual(str(plot), "Участок № 15-А")

    def test_get_absolute_url_uses_slug(self):
        plot = make_plot(plot_number="12")
        self.assertEqual(plot.get_absolute_url(), "/registry/plots/12/")

    def test_membership_fee_is_generated_by_database(self):
        plot = make_plot(area_sqm=Decimal("650.00"))
        plot.refresh_from_db()
        self.assertEqual(plot.membership_fee, Decimal("7800.00"))

    def test_negative_debt_is_rejected_by_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_plot(debt=Decimal("-1.00"))

    def test_free_plot_cannot_have_owner(self):
        plot = make_plot(status=PlotStatus.FREE, owner=make_owner())
        with self.assertRaises(ValidationError):
            plot.full_clean()

    def test_occupied_plot_requires_owner(self):
        plot = make_plot(status=PlotStatus.OCCUPIED, owner=None)
        with self.assertRaises(ValidationError):
            plot.full_clean()

    def test_occupied_plot_with_owner_is_valid(self):
        make_plot(status=PlotStatus.OCCUPIED, owner=make_owner()).full_clean()

    def test_owner_deletion_keeps_plot(self):
        owner = make_owner()
        plot = make_plot(owner=owner, status=PlotStatus.OCCUPIED)
        owner.delete()
        plot.refresh_from_db()
        self.assertIsNone(plot.owner)


class PaymentModelTests(TestCase):
    def test_cancel_changes_status_and_keeps_record(self):
        payment = make_payment(make_owner())
        payment.cancel()
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.CANCELLED)
        self.assertEqual(Payment.objects.count(), 1)

    def test_owner_with_payments_is_protected(self):
        owner = make_owner()
        make_payment(owner)
        with self.assertRaises(ProtectedError):
            owner.delete()

    def test_posted_manager_excludes_cancelled(self):
        owner = make_owner()
        make_payment(owner)
        cancelled = make_payment(owner)
        cancelled.cancel()
        self.assertEqual(Payment.objects.posted().count(), 1)
        self.assertEqual(Payment.objects.cancelled().count(), 1)


class LeaseModelTests(TestCase):
    def test_clean_rejects_backwards_period(self):
        lease = Lease(plot=make_plot(), owner=make_owner(),
                      start_date=timezone.localdate(),
                      end_date=timezone.localdate() - timedelta(days=1))
        with self.assertRaises(ValidationError):
            lease.full_clean()

    def test_clean_rejects_overlapping_active_lease(self):
        plot = make_plot()
        owner = make_owner()
        make_lease(plot, owner, start=timezone.localdate(), end=timezone.localdate() + timedelta(days=10))
        conflict = Lease(
            plot=plot,
            owner=owner,
            start_date=timezone.localdate() + timedelta(days=5),
            end_date=timezone.localdate() + timedelta(days=15),
        )
        with self.assertRaises(ValidationError):
            conflict.full_clean()

    def test_clean_allows_saving_edited_lease(self):
        plot = make_plot()
        owner = make_owner()
        lease = make_lease(plot, owner, start=timezone.localdate(), end=timezone.localdate() + timedelta(days=10))
        lease.note = "Продлено"
        lease.full_clean()

    def test_cancelled_lease_does_not_block_plot(self):
        plot = make_plot()
        owner = make_owner()
        make_lease(plot, owner, status=LeaseStatus.CANCELLED,
                   start=timezone.localdate(), end=timezone.localdate() + timedelta(days=10))
        candidate = Lease(
            plot=plot,
            owner=owner,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=10),
        )
        candidate.full_clean()

    def test_cancel_sets_status(self):
        lease = make_lease(make_plot(), make_owner())
        lease.cancel()
        lease.refresh_from_db()
        self.assertEqual(lease.status, LeaseStatus.CANCELLED)
        self.assertFalse(lease.is_active)

    def test_duration_counts_both_border_days(self):
        lease = make_lease(
            make_plot(),
            make_owner(),
            start=timezone.localdate(),
            end=timezone.localdate() + timedelta(days=9),
        )
        self.assertEqual(lease.duration_days, 10)

    def test_active_manager_filters_by_status(self):
        plot = make_plot()
        owner = make_owner()
        make_lease(plot, owner)
        make_lease(plot, owner, status=LeaseStatus.COMPLETED,
                   start=timezone.localdate() + timedelta(days=100),
                   end=timezone.localdate() + timedelta(days=140))
        self.assertEqual(Lease.objects.active().count(), 1)
