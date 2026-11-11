"""Form tests: filter forms, ModelForms and business rules (PR11)."""
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from registry.forms import (
    LeaseFilterForm,
    LeaseForm,
    OwnerFilterForm,
    OwnerForm,
    PaymentFilterForm,
    PaymentForm,
    PlotFilterForm,
    PlotForm,
)
from registry.models import LeaseStatus, PlotStatus
from registry.tests.factories import make_lease, make_owner, make_plot

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class PlotFilterFormTests(TestCase):
    def test_valid_parameters_are_cleaned(self):
        form = PlotFilterForm({"q": " 12 ", "status": PlotStatus.FREE, "ordering": "debt"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["q"], "12")
        self.assertEqual(form.cleaned_data["status"], PlotStatus.FREE)

    def test_unknown_status_is_rejected(self):
        form = PlotFilterForm({"status": "unknown"})
        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)

    def test_single_character_search_is_rejected(self):
        form = PlotFilterForm({"q": "1"})
        self.assertFalse(form.is_valid())
        self.assertIn("q", form.errors)

    def test_negative_area_is_rejected(self):
        form = PlotFilterForm({"area_min": "-5"})
        self.assertFalse(form.is_valid())
        self.assertIn("area_min", form.errors)

    def test_empty_form_is_valid(self):
        self.assertTrue(PlotFilterForm({}).is_valid())


class OtherFilterFormTests(TestCase):
    def test_owner_filter_strips_spaces(self):
        form = OwnerFilterForm({"q": "  Иванов  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["q"], "Иванов")

    def test_payment_filter_rejects_reversed_period(self):
        form = PaymentFilterForm({
            "date_from": timezone.localdate(),
            "date_to": timezone.localdate() - timedelta(days=5),
        })
        self.assertFalse(form.is_valid())

    def test_lease_filter_accepts_empty_values(self):
        self.assertTrue(LeaseFilterForm({}).is_valid())

    def test_lease_filter_rejects_reversed_period(self):
        form = LeaseFilterForm({
            "date_from": timezone.localdate(),
            "date_to": timezone.localdate() - timedelta(days=1),
        })
        self.assertFalse(form.is_valid())


class PlotFormTests(TestCase):
    def _payload(self, **overrides):
        data = {
            "plot_number": "31-А",
            "area_sqm": "700",
            "status": PlotStatus.OCCUPIED,
            "owner": self.owner.pk,
            "debt": "0",
        }
        data.update(overrides)
        return data

    def setUp(self):
        self.owner = make_owner()

    def test_valid_plot_is_created(self):
        form = PlotForm(self._payload())
        self.assertTrue(form.is_valid(), form.errors)
        plot = form.save()
        self.assertEqual(plot.slug, "31-a")
        self.assertEqual(plot.owner, self.owner)

    def test_free_plot_with_owner_is_rejected(self):
        form = PlotForm(self._payload(status=PlotStatus.FREE))
        self.assertFalse(form.is_valid())
        self.assertIn("owner", form.errors)

    def test_occupied_plot_without_owner_is_rejected(self):
        form = PlotForm(self._payload(owner=""))
        self.assertFalse(form.is_valid())
        self.assertIn("owner", form.errors)

    def test_invalid_plot_number_is_rejected(self):
        form = PlotForm(self._payload(plot_number="участок 5/1"))
        self.assertFalse(form.is_valid())
        self.assertIn("plot_number", form.errors)

    def test_area_below_one_is_rejected(self):
        form = PlotForm(self._payload(area_sqm="0.5"))
        self.assertFalse(form.is_valid())
        self.assertIn("area_sqm", form.errors)

    def test_too_large_image_is_rejected(self):
        big_image = SimpleUploadedFile("big.png", PNG_BYTES + b"0" * (6 * 1024 * 1024),
                                       content_type="image/png")
        form = PlotForm(self._payload(), {"image": big_image})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_valid_image_is_accepted(self):
        image = SimpleUploadedFile("plot.png", PNG_BYTES, content_type="image/png")
        form = PlotForm(self._payload(), {"image": image})
        self.assertTrue(form.is_valid(), form.errors)

    def test_edit_keeps_existing_plot_number(self):
        plot = make_plot(plot_number="41", owner=self.owner, status=PlotStatus.OCCUPIED)
        form = PlotForm({"plot_number": "41", "area_sqm": "650", "status": PlotStatus.OCCUPIED,
                         "owner": self.owner.pk, "debt": "10"}, instance=plot)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn("image", form.fields)


class OwnerFormTests(TestCase):
    def test_valid_owner(self):
        form = OwnerForm({"full_name": "Сидоров Иван", "phone": "+7 916 000-11-22", "email": ""})
        self.assertTrue(form.is_valid(), form.errors)

    def test_phone_with_letters_is_rejected(self):
        form = OwnerForm({"full_name": "Сидоров Иван", "phone": "телефон", "email": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)


class PaymentFormTests(TestCase):
    def setUp(self):
        self.owner = make_owner()

    def test_date_is_prefilled_with_today(self):
        form = PaymentForm()
        self.assertEqual(form.fields["payment_date"].initial, timezone.localdate())

    def test_future_date_is_rejected(self):
        form = PaymentForm({
            "owner": self.owner.pk,
            "amount": "1000",
            "payment_date": timezone.localdate() + timedelta(days=2),
            "description": "Взнос",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("payment_date", form.errors)

    def test_zero_amount_is_rejected(self):
        form = PaymentForm({
            "owner": self.owner.pk,
            "amount": "0",
            "payment_date": timezone.localdate(),
            "description": "Взнос",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_valid_payment_is_saved(self):
        form = PaymentForm({
            "owner": self.owner.pk,
            "amount": "2500",
            "payment_date": timezone.localdate(),
            "description": "Членский взнос",
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().amount, 2500)


class LeaseFormTests(TestCase):
    def setUp(self):
        self.owner = make_owner()
        self.plot = make_plot(plot_number="51")

    def _payload(self, **overrides):
        data = {
            "plot": self.plot.pk,
            "owner": self.owner.pk,
            "start_date": timezone.localdate() + timedelta(days=2),
            "end_date": timezone.localdate() + timedelta(days=32),
            "rent_amount": "5000",
            "note": "Сезон",
        }
        data.update(overrides)
        return data

    def test_valid_lease(self):
        form = LeaseForm(self._payload())
        self.assertTrue(form.is_valid(), form.errors)

    def test_past_start_date_is_rejected(self):
        form = LeaseForm(self._payload(
            start_date=timezone.localdate() - timedelta(days=3),
            end_date=timezone.localdate() + timedelta(days=5),
        ))
        self.assertFalse(form.is_valid())
        self.assertIn("start_date", form.errors)

    def test_end_before_start_is_rejected(self):
        form = LeaseForm(self._payload(
            start_date=timezone.localdate() + timedelta(days=10),
            end_date=timezone.localdate() + timedelta(days=5),
        ))
        self.assertFalse(form.is_valid())

    def test_overlapping_lease_is_reported_as_common_error(self):
        make_lease(self.plot, self.owner,
                   start=timezone.localdate() + timedelta(days=1),
                   end=timezone.localdate() + timedelta(days=9))
        form = LeaseForm(self._payload())
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())

    def test_non_overlapping_lease_is_accepted(self):
        make_lease(self.plot, self.owner,
                   start=timezone.localdate() + timedelta(days=1),
                   end=timezone.localdate() + timedelta(days=9))
        form = LeaseForm(self._payload(
            start_date=timezone.localdate() + timedelta(days=20),
            end_date=timezone.localdate() + timedelta(days=40),
        ))
        self.assertTrue(form.is_valid(), form.errors)

    def test_cancelled_lease_does_not_block_the_plot(self):
        cancel = make_lease(self.plot, self.owner,
                            start=timezone.localdate() + timedelta(days=1),
                            end=timezone.localdate() + timedelta(days=9))
        cancel.cancel()
        form = LeaseForm(self._payload())
        self.assertTrue(form.is_valid(), form.errors)

    def test_editing_lease_does_not_conflict_with_itself(self):
        lease = make_lease(self.plot, self.owner,
                           start=timezone.localdate() + timedelta(days=2),
                           end=timezone.localdate() + timedelta(days=32))
        form = LeaseForm(self._payload(rent_amount="6000"), instance=lease)
        self.assertTrue(form.is_valid(), form.errors)

    def test_editing_into_another_lease_is_rejected(self):
        lease = make_lease(self.plot, self.owner,
                           start=timezone.localdate() + timedelta(days=2),
                           end=timezone.localdate() + timedelta(days=12))
        other_plot = make_plot(plot_number="52")
        make_lease(other_plot, self.owner,
                   start=timezone.localdate() + timedelta(days=40),
                   end=timezone.localdate() + timedelta(days=60))
        form = LeaseForm(self._payload(plot=other_plot.pk,
                                       start_date=timezone.localdate() + timedelta(days=45),
                                       end_date=timezone.localdate() + timedelta(days=50)),
                         instance=lease)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())

    def test_cancelled_lease_keeps_status_field_out_of_the_form(self):
        self.assertNotIn("status", LeaseForm().fields)
        self.assertEqual(LeaseStatus.ACTIVE, "active")
