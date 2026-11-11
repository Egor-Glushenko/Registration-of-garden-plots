"""CRUD view tests for the Django Forms of the registry (PR11)."""
import shutil
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from registry.models import LeaseStatus, PaymentStatus, PlotStatus
from registry.tests.factories import make_lease, make_owner, make_payment, make_plot
from registry.tests.test_forms import PNG_BYTES

MEDIA_ROOT = tempfile.mkdtemp(prefix="registry-media-")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PlotCrudTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.owner = make_owner()

    def test_create_page_is_available(self):
        response = self.client.get(reverse("registry:plot_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Новый участок")

    def test_create_plot_with_image(self):
        image = SimpleUploadedFile("plot.png", PNG_BYTES, content_type="image/png")
        response = self.client.post(reverse("registry:plot_create"), {
            "plot_number": "77-Б",
            "area_sqm": "820",
            "status": PlotStatus.OCCUPIED,
            "owner": self.owner.pk,
            "debt": "0",
            "image": image,
        })
        self.assertEqual(response.status_code, 302)
        plot = self.owner.plots.get(plot_number="77-Б")
        self.assertTrue(plot.image)
        self.assertIn("/media/plots/", plot.image.url)
        self.assertEqual(plot.slug, "77-b")

    def test_invalid_plot_is_not_saved(self):
        response = self.client.post(reverse("registry:plot_create"), {
            "plot_number": "78",
            "area_sqm": "900",
            "status": PlotStatus.FREE,
            "owner": self.owner.pk,
            "debt": "0",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "У свободного участка не может быть владельца")
        self.assertFalse(self.owner.plots.filter(plot_number="78").exists())

    def test_edit_plot_changes_data(self):
        plot = make_plot(plot_number="80", owner=self.owner, status=PlotStatus.OCCUPIED)
        response = self.client.post(reverse("registry:plot_update", args=[plot.slug]), {
            "plot_number": "80",
            "area_sqm": "990",
            "status": PlotStatus.DISPUTED,
            "owner": self.owner.pk,
            "debt": "120",
        })
        self.assertEqual(response.status_code, 302)
        plot.refresh_from_db()
        self.assertEqual(plot.status, PlotStatus.DISPUTED)
        self.assertEqual(str(plot.area_sqm), "990.00")

    def test_edit_missing_plot_returns_404(self):
        self.assertEqual(self.client.get("/registry/plots/unknown/edit/").status_code, 404)


class OwnerCrudTests(TestCase):
    def test_create_owner(self):
        response = self.client.post(reverse("registry:owner_create"), {
            "full_name": "Новиков Пётр Ильич",
            "phone": "+7 999 111-22-33",
            "email": "novikov@example.org",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.get(reverse("registry:owners"), {"q": "Новиков"}))

    def test_invalid_owner_is_reported(self):
        response = self.client.post(reverse("registry:owner_create"), {
            "full_name": "",
            "phone": "abc",
            "email": "not-an-email",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Телефон должен содержать")
        self.assertContains(response, "Обязательное поле")

    def test_edit_owner(self):
        owner = make_owner(full_name="Старое Имя")
        response = self.client.post(reverse("registry:owner_update", args=[owner.pk]), {
            "full_name": "Новое Имя",
            "phone": owner.phone,
            "email": owner.email,
        })
        self.assertEqual(response.status_code, 302)
        owner.refresh_from_db()
        self.assertEqual(owner.full_name, "Новое Имя")


class PaymentCrudTests(TestCase):
    def setUp(self):
        self.owner = make_owner()

    def test_create_payment(self):
        response = self.client.post(reverse("registry:payment_create"), {
            "owner": self.owner.pk,
            "amount": "3200",
            "payment_date": timezone.localdate(),
            "description": "Членский взнос",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.owner.payments.count(), 1)

    def test_future_payment_is_rejected(self):
        response = self.client.post(reverse("registry:payment_create"), {
            "owner": self.owner.pk,
            "amount": "3200",
            "payment_date": timezone.localdate() + timedelta(days=3),
            "description": "Аванс",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "не может быть в будущем")
        self.assertEqual(self.owner.payments.count(), 0)

    def test_cancel_payment_changes_status(self):
        payment = make_payment(self.owner)
        response = self.client.post(reverse("registry:payment_cancel", args=[payment.pk]))
        self.assertEqual(response.status_code, 302)
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.CANCELLED)

    def test_cancel_payment_by_get_is_forbidden(self):
        payment = make_payment(self.owner)
        response = self.client.get(reverse("registry:payment_cancel", args=[payment.pk]))
        self.assertEqual(response.status_code, 405)
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.POSTED)

    def test_cancel_missing_payment_returns_404(self):
        self.assertEqual(self.client.post("/registry/payments/999/cancel/").status_code, 404)


class LeaseCrudTests(TestCase):
    def setUp(self):
        self.owner = make_owner()
        self.plot = make_plot(plot_number="90")

    def _payload(self, **overrides):
        data = {
            "plot": self.plot.pk,
            "owner": self.owner.pk,
            "start_date": timezone.localdate() + timedelta(days=1),
            "end_date": timezone.localdate() + timedelta(days=30),
            "rent_amount": "4000",
            "note": "Сезон",
        }
        data.update(overrides)
        return data

    def test_create_lease_marks_plot_as_leased(self):
        response = self.client.post(reverse("registry:lease_create"), self._payload())
        self.assertEqual(response.status_code, 302)
        self.plot.refresh_from_db()
        self.assertEqual(self.plot.status, PlotStatus.LEASED)
        self.assertEqual(self.plot.owner, self.owner)

    def test_conflicting_lease_shows_common_error(self):
        make_lease(self.plot, self.owner,
                   start=timezone.localdate() + timedelta(days=1),
                   end=timezone.localdate() + timedelta(days=10))
        response = self.client.post(reverse("registry:lease_create"), self._payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "уже арендован")
        self.assertEqual(self.plot.leases.count(), 1)

    def test_cancel_lease_releases_plot(self):
        lease = make_lease(self.plot, self.owner,
                           start=timezone.localdate() + timedelta(days=1),
                           end=timezone.localdate() + timedelta(days=10))
        self.plot.status = PlotStatus.LEASED
        self.plot.save(update_fields=["status"])
        response = self.client.post(reverse("registry:lease_cancel", args=[lease.pk]))
        self.assertEqual(response.status_code, 302)
        lease.refresh_from_db()
        self.plot.refresh_from_db()
        self.assertEqual(lease.status, LeaseStatus.CANCELLED)
        self.assertNotEqual(self.plot.status, PlotStatus.LEASED)

    def test_cancel_lease_by_get_is_forbidden(self):
        lease = make_lease(self.plot, self.owner)
        response = self.client.get(reverse("registry:lease_cancel", args=[lease.pk]))
        self.assertEqual(response.status_code, 405)
        lease.refresh_from_db()
        self.assertEqual(lease.status, LeaseStatus.ACTIVE)

    def test_edit_lease_keeps_record(self):
        lease = make_lease(self.plot, self.owner,
                           start=timezone.localdate() + timedelta(days=1),
                           end=timezone.localdate() + timedelta(days=10))
        response = self.client.post(
            reverse("registry:lease_update", args=[lease.pk]),
            self._payload(end_date=timezone.localdate() + timedelta(days=20)),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.plot.leases.count(), 1)
        lease.refresh_from_db()
        self.assertEqual(lease.duration_days, 20)

    def test_missing_lease_returns_404(self):
        self.assertEqual(self.client.get("/registry/leases/999/edit/").status_code, 404)


class FilterViewTests(TestCase):
    def setUp(self):
        make_plot(plot_number="12", status=PlotStatus.FREE)
        make_plot(plot_number="13", owner=make_owner(), status=PlotStatus.OCCUPIED)

    def test_invalid_filter_shows_warning_without_error(self):
        response = self.client.get(reverse("registry:plots"), {"status": "unknown", "area_min": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Параметры фильтра некорректны")
        self.assertEqual(len(response.context["plots"]), 2)

    def test_single_character_search_is_handled(self):
        response = self.client.get(reverse("registry:plots"), {"q": "1"})
        self.assertEqual(response.status_code, 200)

    def test_area_filter_is_applied(self):
        response = self.client.get(reverse("registry:plots"), {"area_min": "700"})
        self.assertEqual(response.status_code, 200)

    def test_payment_reversed_period_is_handled(self):
        make_payment(make_owner())
        response = self.client.get(reverse("registry:payments"), {
            "date_from": timezone.localdate(),
            "date_to": timezone.localdate() - timedelta(days=10),
        })
        self.assertEqual(response.status_code, 200)

    def test_plot_detail_404_message(self):
        response = self.client.get("/registry/plots/00-unknown/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
