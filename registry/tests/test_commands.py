"""Management command tests: demo data import and data consistency (PR9)."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from registry.models import Lease, Owner, Payment, Plot


class SetupRegistryCommandTests(TestCase):
    def test_command_imports_demo_fixtures(self):
        out = StringIO()
        call_command("setup_registry", "--source", "fixtures", stdout=out)
        self.assertEqual(Owner.objects.count(), 6)
        self.assertEqual(Plot.objects.count(), 14)
        self.assertEqual(Payment.objects.count(), 8)
        self.assertEqual(Lease.objects.count(), 5)
        self.assertIn("Реестр готов", out.getvalue())

    def test_command_is_idempotent(self):
        call_command("setup_registry", "--source", "fixtures", stdout=StringIO())
        call_command("setup_registry", "--source", "fixtures", stdout=StringIO())
        self.assertEqual(Owner.objects.count(), 6)
        self.assertEqual(Plot.objects.count(), 14)

    def test_plot_numbers_and_slugs_are_filled(self):
        call_command("setup_registry", "--source", "fixtures", stdout=StringIO())
        plot = Plot.objects.get(plot_number="15-А")
        self.assertEqual(plot.slug, "15-a")
        self.assertEqual(str(plot.membership_fee), "10800.00")
