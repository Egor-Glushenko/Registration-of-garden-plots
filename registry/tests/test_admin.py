"""Admin panel tests: registration, lists, search, filters and actions (PR10)."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from registry.models import LeaseStatus, PaymentStatus, PlotStatus
from registry.tests.factories import make_lease, make_owner, make_payment, make_plot


class AdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.org",
            password="secret-password",
        )
        cls.owner = make_owner(full_name="Иванова Мария Петровна")
        cls.plot = make_plot(plot_number="15-А", owner=cls.owner,
                             status=PlotStatus.OCCUPIED, debt=Decimal("1500.00"))
        cls.payment = make_payment(cls.owner, amount="1500.00")
        today = timezone.localdate()
        cls.lease = make_lease(cls.plot, cls.owner, start=today, end=today)

    def setUp(self):
        self.client.force_login(self.admin)


class AdminIndexTests(AdminTestCase):
    def test_dashboard_opens_with_custom_header(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Садовый реестр")

    def test_all_models_are_registered(self):
        for name in ("registry_owner_changelist", "registry_plot_changelist",
                     "registry_payment_changelist", "registry_lease_changelist"):
            self.assertEqual(self.client.get(reverse(f"admin:{name}")).status_code, 200)


class OwnerAdminTests(AdminTestCase):
    def test_list_shows_aggregated_columns(self):
        response = self.client.get(reverse("admin:registry_owner_changelist"))
        self.assertContains(response, "Иванова Мария Петровна")

    def test_search_by_phone(self):
        response = self.client.get(reverse("admin:registry_owner_changelist"), {"q": "+7 900"})
        self.assertContains(response, "Иванова Мария Петровна")

    def test_change_page_contains_inlines(self):
        response = self.client.get(reverse("admin:registry_owner_change", args=[self.owner.pk]))
        self.assertContains(response, "Участки владельца")
        self.assertContains(response, "Платежи владельца")


class PlotAdminTests(AdminTestCase):
    def test_search_by_owner_name(self):
        response = self.client.get(reverse("admin:registry_plot_changelist"), {"q": "Иванова"})
        self.assertContains(response, "15-А")

    def test_filter_by_status(self):
        response = self.client.get(
            reverse("admin:registry_plot_changelist"), {"status__exact": PlotStatus.OCCUPIED}
        )
        self.assertContains(response, "15-А")

    def test_action_marks_plots_as_free(self):
        response = self.client.post(
            reverse("admin:registry_plot_changelist"),
            {"action": "mark_as_free", "_selected_action": [self.plot.pk]},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.plot.refresh_from_db()
        self.assertEqual(self.plot.status, PlotStatus.FREE)
        self.assertIsNone(self.plot.owner)

    def test_action_clears_debt(self):
        self.client.post(
            reverse("admin:registry_plot_changelist"),
            {"action": "clear_debt", "_selected_action": [self.plot.pk]},
            follow=True,
        )
        self.plot.refresh_from_db()
        self.assertEqual(self.plot.debt, Decimal("0.00"))

    def test_penalty_action_uses_f_expression(self):
        self.client.post(
            reverse("admin:registry_plot_changelist"),
            {"action": "apply_penalty", "_selected_action": [self.plot.pk]},
            follow=True,
        )
        self.plot.refresh_from_db()
        self.assertEqual(self.plot.debt, Decimal("1575.00"))

    def test_change_page_shows_lease_inline(self):
        response = self.client.get(reverse("admin:registry_plot_change", args=[self.plot.pk]))
        self.assertContains(response, "Аренда участка")


class PaymentAdminTests(AdminTestCase):
    def test_cancel_action_changes_status(self):
        self.client.post(
            reverse("admin:registry_payment_changelist"),
            {"action": "cancel_payments", "_selected_action": [self.payment.pk]},
            follow=True,
        )
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.CANCELLED)

    def test_filter_by_state(self):
        response = self.client.get(
            reverse("admin:registry_payment_changelist"), {"status__exact": PaymentStatus.POSTED}
        )
        self.assertEqual(response.status_code, 200)


class LeaseAdminTests(AdminTestCase):
    def test_cancel_action_changes_status(self):
        self.client.post(
            reverse("admin:registry_lease_changelist"),
            {"action": "cancel_leases", "_selected_action": [self.lease.pk]},
            follow=True,
        )
        self.lease.refresh_from_db()
        self.assertEqual(self.lease.status, LeaseStatus.CANCELLED)

    def test_cancelled_lease_does_not_block_plot(self):
        self.lease.cancel()
        available = self.plot.leases.active().filter(pk=self.lease.pk).exists()
        self.assertFalse(available)


class AdminAccessTests(TestCase):
    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_regular_user_is_rejected(self):
        user = get_user_model().objects.create_user(username="guest", password="secret-password")
        self.client.force_login(user)
        response = self.client.get(reverse("admin:registry_plot_changelist"))
        # Django sends non-staff users back to the admin login page.
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])
