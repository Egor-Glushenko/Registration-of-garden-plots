"""View tests: pages, filters, pagination and 404 handling (PR9)."""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from registry.models import LeaseStatus, PaymentStatus, PlotStatus
from registry.tests.factories import make_lease, make_owner, make_payment, make_plot


class PlotViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_owner(1, full_name="Иванова Мария")
        cls.plot = make_plot(1, plot_number="15-А", owner=cls.owner,
                             status=PlotStatus.OCCUPIED, debt=Decimal("1200.00"))
        make_plot(2, plot_number="16-Б", status=PlotStatus.FREE)

    def test_list_page_is_rendered(self):
        response = self.client.get(reverse("registry:plots"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registry/plots.html")
        self.assertEqual(response.context["page_obj"].paginator.count, 2)

    def test_list_applies_status_and_search(self):
        response = self.client.get(reverse("registry:plots"), {"status": "free", "q": "16"})
        plots = list(response.context["plots"])
        self.assertEqual([plot.plot_number for plot in plots], ["16-Б"])

    def test_unknown_status_is_ignored(self):
        response = self.client.get(reverse("registry:plots"), {"status": "broken"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["plots"]), 2)

    def test_invalid_page_number_is_safe(self):
        response = self.client.get(reverse("registry:plots"), {"page": "abc"})
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_detail_page_is_available_by_slug(self):
        response = self.client.get(self.plot.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "15-А")

    def test_unknown_slug_returns_404(self):
        response = self.client.get("/registry/plots/does-not-exist/")
        self.assertEqual(response.status_code, 404)

    def test_legacy_numeric_link_redirects_to_slug(self):
        response = self.client.get(f"/registry/plots/id/{self.plot.pk}/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], self.plot.get_absolute_url())

    def test_missing_legacy_identifier_returns_404(self):
        self.assertEqual(self.client.get("/registry/plots/id/999/").status_code, 404)


class OwnerAndPaymentViewTests(TestCase):
    def setUp(self):
        self.owner = make_owner(full_name="Петров Сергей")
        make_plot(1, owner=self.owner, status=PlotStatus.OCCUPIED, debt=Decimal("300.00"))
        self.payment = make_payment(self.owner)

    def test_owner_page_shows_aggregates(self):
        response = self.client.get(reverse("registry:owners"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Петров Сергей")

    def test_owner_search(self):
        response = self.client.get(reverse("registry:owners"), {"q": "Петров"})
        self.assertEqual(len(response.context["owners"]), 1)

    def test_payment_page_hides_cancelled_by_filter(self):
        self.payment.cancel()
        response = self.client.get(reverse("registry:payments"), {"status": PaymentStatus.POSTED})
        self.assertEqual(len(response.context["payments"]), 0)

    def test_payment_page_shows_owner_name(self):
        response = self.client.get(reverse("registry:payments"))
        self.assertContains(response, "Петров Сергей")


class LeaseViewTests(TestCase):
    def setUp(self):
        self.owner = make_owner()
        self.plot = make_plot()
        today = timezone.localdate()
        self.lease = make_lease(self.plot, self.owner, start=today, end=today + timedelta(days=7))

    def test_lease_list_page(self):
        response = self.client.get(reverse("registry:leases"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registry/leases.html")

    def test_lease_detail_page(self):
        response = self.client.get(reverse("registry:lease_detail", args=[self.lease.pk]))
        self.assertEqual(response.status_code, 200)

    def test_cancelled_leases_filtered_out(self):
        self.lease.cancel()
        response = self.client.get(reverse("registry:leases"), {"status": LeaseStatus.ACTIVE})
        self.assertEqual(len(response.context["leases"]), 0)


class StatisticsAndHomeTests(TestCase):
    def test_home_page_uses_dashboard_counters(self):
        make_plot()
        response = self.client.get(reverse("home:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stats"]["plot_count"], 1)

    def test_statistics_page(self):
        make_plot()
        response = self.client.get(reverse("registry:statistics"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("by_status", response.context["stats"])
