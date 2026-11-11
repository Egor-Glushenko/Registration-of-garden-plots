"""Query layer tests: filtering, sorting, pagination and aggregation (PR9)."""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from registry import queries
from registry.models import LeaseStatus, PaymentStatus, PlotStatus
from registry.tests.factories import make_lease, make_owner, make_payment, make_plot


class PlotPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ivanov = make_owner(1, full_name="Иванов Пётр")
        cls.petrova = make_owner(2, full_name="Петрова Анна")
        cls.free_plot = make_plot(1, plot_number="12", status=PlotStatus.FREE)
        cls.busy_plot = make_plot(2, plot_number="13", owner=cls.ivanov,
                                  status=PlotStatus.OCCUPIED, debt=Decimal("1500.00"))
        cls.leased_plot = make_plot(3, plot_number="14", owner=cls.petrova,
                                    status=PlotStatus.LEASED, debt=Decimal("500.00"))

    def test_status_filter(self):
        page = queries.plot_page(status=PlotStatus.FREE)
        self.assertEqual([plot.plot_number for plot in page.object_list], ["12"])

    def test_unknown_status_returns_everything(self):
        page = queries.plot_page(status="unknown")
        self.assertEqual(page.paginator.count, 3)

    def test_search_by_owner_name(self):
        page = queries.plot_page(query="Петрова")
        self.assertEqual([plot.plot_number for plot in page.object_list], ["14"])

    def test_search_by_plot_number(self):
        page = queries.plot_page(query="13")
        self.assertEqual([plot.plot_number for plot in page.object_list], ["13"])

    def test_ordering_by_debt(self):
        page = queries.plot_page(ordering="debt")
        self.assertEqual([plot.plot_number for plot in page.object_list], ["13", "14", "12"])

    def test_pagination_splits_results(self):
        for index in range(20, 33):
            make_plot(index, plot_number=str(index))
        page = queries.plot_page(page=2, per_page=10)
        self.assertEqual(page.number, 2)
        self.assertEqual(len(page.object_list), 6)
        self.assertEqual(page.paginator.num_pages, 2)
        self.assertEqual(page.paginator.count, 16)

    def test_invalid_page_number_falls_back_to_first(self):
        page = queries.plot_page(page="not-a-number")
        self.assertEqual(page.number, 1)

    def test_owner_is_joined_in_the_same_query(self):
        # One COUNT for the paginator plus one SELECT with JOIN; no per-row queries.
        with self.assertNumQueries(2):
            page = queries.plot_page()
            list(page.object_list)


class OwnerPageTests(TestCase):
    def test_aggregates_plot_count_and_debt(self):
        owner = make_owner()
        make_plot(1, owner=owner, status=PlotStatus.OCCUPIED, debt=Decimal("100.00"))
        make_plot(2, owner=owner, status=PlotStatus.OCCUPIED, debt=Decimal("200.00"))
        page = queries.owner_page()
        row = page.object_list[0]
        self.assertEqual(row.plot_count, 2)
        self.assertEqual(row.total_debt, Decimal("300.00"))

    def test_search_by_phone(self):
        make_owner(1, full_name="Иванов", phone="+7 916 111-22-33")
        make_owner(2, full_name="Петров", phone="+7 916 999-88-77")
        page = queries.owner_page(query="999")
        self.assertEqual([owner.full_name for owner in page.object_list], ["Петров"])


class PaymentPageTests(TestCase):
    def setUp(self):
        self.owner = make_owner()
        self.first = make_payment(self.owner, amount="1000.00", description="Взнос")
        self.second = make_payment(self.owner, amount="2000.00", description="Целевой взнос")

    def test_status_filter_hides_cancelled(self):
        self.second.cancel()
        page = queries.payment_page(status=PaymentStatus.POSTED)
        self.assertEqual([payment.pk for payment in page.object_list], [self.first.pk])

    def test_search_by_description(self):
        page = queries.payment_page(query="Целевой")
        self.assertEqual([payment.pk for payment in page.object_list], [self.second.pk])

    def test_ordering_by_amount(self):
        page = queries.payment_page(ordering="amount")
        self.assertEqual(page.object_list[0].pk, self.second.pk)


class LeasePageTests(TestCase):
    def setUp(self):
        self.owner = make_owner()
        self.plot = make_plot()
        today = timezone.localdate()
        self.active = make_lease(self.plot, self.owner, start=today, end=today + timedelta(days=30))
        self.old = make_lease(self.plot, self.owner, status=LeaseStatus.COMPLETED,
                              start=today - timedelta(days=90), end=today - timedelta(days=60))

    def test_status_filter(self):
        page = queries.lease_page(status=LeaseStatus.ACTIVE)
        self.assertEqual([lease.pk for lease in page.object_list], [self.active.pk])

    def test_future_filter_skips_finished_leases(self):
        page = queries.lease_page(date_from=timezone.localdate())
        self.assertEqual([lease.pk for lease in page.object_list], [self.active.pk])

    def test_available_plots_excludes_busy_period(self):
        available = queries.available_plots(timezone.localdate(), timezone.localdate())
        self.assertNotIn(self.plot, list(available))


class StatisticsTests(TestCase):
    def test_dashboard_counts_and_totals(self):
        owner = make_owner()
        make_plot(1, owner=owner, status=PlotStatus.OCCUPIED, debt=Decimal("700.00"))
        make_plot(2, status=PlotStatus.FREE)
        make_payment(owner, amount="300.00")
        stats = queries.dashboard_stats()
        self.assertEqual(stats["plot_count"], 2)
        self.assertEqual(stats["owner_count"], 1)
        self.assertEqual(stats["payment_count"], 1)
        self.assertEqual(stats["total_debt"], Decimal("700.00"))

    def test_statistics_groups_by_status(self):
        make_plot(1, status=PlotStatus.FREE, area_sqm=Decimal("400.00"))
        make_plot(2, status=PlotStatus.FREE, area_sqm=Decimal("600.00"))
        make_plot(3, owner=make_owner(), status=PlotStatus.OCCUPIED, debt=Decimal("100.00"))
        stats = queries.statistics()
        rows = {row["status"]: row for row in stats["by_status"]}
        self.assertEqual(rows[PlotStatus.FREE]["plot_count"], 2)
        self.assertEqual(rows[PlotStatus.FREE]["average_area"], Decimal("500.00"))
        self.assertEqual(stats["top_debtors"][0].full_name, "Тестовый владелец 1")
