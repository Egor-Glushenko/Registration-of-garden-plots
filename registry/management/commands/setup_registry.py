"""Load the registry demo data through Django ORM (PR9).

The command replaces the PR7 SQL import: it creates owners, plots, payments and
leases with ORM methods, so the same code works for SQLite and PostgreSQL.
Migrations must be applied before the command runs.

Records whose related object is missing are skipped with a warning, therefore a
mixed data set cannot break the foreign keys.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from db.import_json import read_records
from registry.models import Lease, Owner, Payment, Plot


class Command(BaseCommand):
    help = "Импортирует демонстрационные данные реестра через Django ORM."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=("auto", "fixtures", "data"),
            default="auto",
            help="Откуда брать JSON: автоматически, только из fixtures/ или только из data/.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        source = options["source"]
        source_arg = None if source == "auto" else source
        owners = read_records("owners", source_arg)
        plots = read_records("plots", source_arg)
        payments = read_records("payments", source_arg)
        leases = read_records("leases", source_arg)
        skipped = 0

        for row in owners:
            Owner.objects.update_or_create(
                id=row["id"],
                defaults={
                    "full_name": row["full_name"],
                    "phone": row.get("phone", "—"),
                    "email": row.get("email") or "",
                },
            )
        for row in plots:
            Plot.objects.update_or_create(
                id=row["id"],
                defaults={
                    "plot_number": row["plot_number"],
                    "area_sqm": row["area_sqm"],
                    "status": row.get("status", "free"),
                    "owner_id": row.get("owner_id"),
                    "debt": row.get("debt", 0),
                },
            )
        for row in payments:
            if not Owner.objects.filter(pk=row["owner_id"]).exists():
                skipped += 1
                continue
            Payment.objects.update_or_create(
                id=row["id"],
                defaults={
                    "owner_id": row["owner_id"],
                    "amount": row["amount"],
                    "payment_date": row["payment_date"],
                    "description": row["description"],
                },
            )
        for row in leases:
            if not Plot.objects.filter(pk=row["plot_id"]).exists():
                skipped += 1
                continue
            if not Owner.objects.filter(pk=row["owner_id"]).exists():
                skipped += 1
                continue
            Lease.objects.update_or_create(
                id=row["id"],
                defaults={
                    "plot_id": row["plot_id"],
                    "owner_id": row["owner_id"],
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "status": row.get("status", "active"),
                    "rent_amount": row.get("rent_amount", 0),
                    "note": row.get("note", ""),
                },
            )

        summary = ", ".join(
            f"{name}={count}"
            for name, count in (
                ("владельцев", Owner.objects.count()),
                ("участков", Plot.objects.count()),
                ("платежей", Payment.objects.count()),
                ("аренд", Lease.objects.count()),
            )
        )
        if skipped:
            summary += f" (пропущено записей без связанных объектов: {skipped})"
        self.stdout.write(self.style.SUCCESS(f"Реестр готов: {summary}"))
