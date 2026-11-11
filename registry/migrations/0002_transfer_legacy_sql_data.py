"""Copy PR7 SQL tables into the new ORM models (PR9, subsection 5.8).

The migration is safe on a clean database: if the legacy tables created by
``sql/schema.sql`` (or ``sql/schema_postgres.sql``) are absent, nothing happens.
Rows keep their identifiers, so the foreign keys of plots and payments stay
valid after the transfer.
"""
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from django.db import migrations
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

LEGACY_TABLES = ("owners", "plots", "payments")
PLOT_STATUSES = {"free", "occupied", "leased", "disputed"}
PAYMENT_STATUSES = {"posted", "cancelled"}

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _legacy_slug(plot_number):
    """Repeat the model slug rule inside the migration (self-contained)."""
    text = str(plot_number or "").strip().lower()
    prefix = "".join(TRANSLIT.get(char, char) for char in text)
    cleaned = "".join(char if char.isalnum() else "-" for char in prefix)
    return "-".join(part for part in cleaned.split("-") if part) or "plot"


def _to_datetime(value):
    """Convert a legacy SQLite/PostgreSQL timestamp into an aware datetime."""
    if value in (None, ""):
        return timezone.now()
    if isinstance(value, datetime):
        moment = value
    else:
        moment = parse_datetime(str(value).replace(" ", "T"))
        if moment is None:
            parsed_date = parse_date(str(value)[:10])
            if parsed_date is None:
                return timezone.now()
            moment = datetime.combine(parsed_date, time.min)
    if timezone.is_naive(moment):
        moment = timezone.make_aware(moment, timezone.get_default_timezone())
    return moment


def _to_date(value, fallback=None):
    """Convert a legacy payment date into a ``date`` object."""
    if value in (None, ""):
        return fallback or timezone.localdate()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = parse_date(str(value)[:10])
    return parsed or fallback or timezone.localdate()


def _to_decimal(value, fallback="0"):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(fallback)


def _fetch(cursor, table):
    cursor.execute(f"SELECT * FROM {table}")  # noqa: S608 - fixed table names
    columns = [column[0] for column in cursor.description or ()]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def transfer_legacy_data(apps, schema_editor):
    """Read the PR7 tables and fill the Django models."""
    Owner = apps.get_model("registry", "Owner")
    Plot = apps.get_model("registry", "Plot")
    Payment = apps.get_model("registry", "Payment")

    connection = schema_editor.connection
    existing = set(connection.introspection.table_names())
    if not set(LEGACY_TABLES).issubset(existing):
        return

    with connection.cursor() as cursor:
        owners = _fetch(cursor, "owners")
        plots = _fetch(cursor, "plots")
        payments = _fetch(cursor, "payments")

    for row in owners:
        Owner.objects.update_or_create(
            id=row["id"],
            defaults={
                "full_name": row.get("full_name") or "Без имени",
                "phone": row.get("phone") or "—",
                "email": row.get("email") or "",
                "created_at": _to_datetime(row.get("created_at")),
            },
        )

    for row in plots:
        status = (row.get("status") or "free").strip()
        plot = Plot.objects.filter(id=row["id"]).first() or Plot(id=row["id"])
        plot.plot_number = row.get("plot_number") or f"Участок-{row['id']}"
        plot.area_sqm = _to_decimal(row.get("area_sqm"), "1")
        plot.status = status if status in PLOT_STATUSES else "free"
        plot.owner_id = row.get("owner_id") or None
        plot.debt = _to_decimal(row.get("debt"), "0")
        plot.created_at = _to_datetime(row.get("created_at"))
        if not plot.slug:
            base = _legacy_slug(plot.plot_number)
            candidate, counter = base, 1
            while Plot.objects.filter(slug=candidate).exclude(pk=plot.pk).exists():
                counter += 1
                candidate = f"{base}-{counter}"
            plot.slug = candidate
        plot.save()

    for row in payments:
        status = (row.get("status") or "posted").strip()
        if row.get("owner_id") is None or not Owner.objects.filter(pk=row["owner_id"]).exists():
            continue  # a payment without an owner cannot be migrated
        Payment.objects.update_or_create(
            id=row["id"],
            defaults={
                "owner_id": row["owner_id"],
                "amount": _to_decimal(row.get("amount"), "0.01"),
                "payment_date": _to_date(row.get("payment_date")),
                "description": row.get("description") or "Платёж по реестру",
                "status": status if status in PAYMENT_STATUSES else "posted",
                "created_at": _to_datetime(row.get("created_at")),
            },
        )

    if connection.vendor == "postgresql":
        # Explicit identifiers do not advance identity sequences automatically.
        with connection.cursor() as cursor:
            for table in ("registry_owner", "registry_plot", "registry_payment"):
                cursor.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
                )


class Migration(migrations.Migration):
    dependencies = [("registry", "0001_initial")]
    operations = [migrations.RunPython(transfer_legacy_data, migrations.RunPython.noop)]
