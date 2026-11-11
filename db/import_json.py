"""Idempotently import owners, plots, and payments JSON into the SQL database."""
import json
from pathlib import Path

from django.db import connection, transaction

from db.database import initialize_schema

ROOT = Path(__file__).resolve().parent.parent


def read_records(name, source=None):
    """Read a data file: private data/ first, then the demo fixtures/.

    ``source="fixtures"`` or ``source="data"`` forces one location, which keeps
    the import of logically related entities consistent.
    """
    private_file = ROOT / "data" / f"{name}.json"
    demo_file = ROOT / "fixtures" / f"{name}.json"
    if source == "fixtures":
        candidates = [demo_file]
    elif source == "data":
        candidates = [private_file]
    else:
        candidates = [private_file, demo_file]
    path = next((item for item in candidates if item.exists()), None)
    if path is None:
        return []
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def import_json():
    initialize_schema()
    owners, plots, payments = (read_records(name) for name in ("owners", "plots", "payments"))
    # Owners must exist before plots and payments due to their foreign keys.
    with transaction.atomic():
        with connection.cursor() as cursor:
            for owner in owners:
                cursor.execute("""
                    INSERT INTO owners (id, full_name, phone, email, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name,
                        phone = EXCLUDED.phone, email = EXCLUDED.email
                """, [owner["id"], owner["full_name"], owner["phone"], owner.get("email"), owner.get("created_at")])
            for plot in plots:
                cursor.execute("""
                    INSERT INTO plots (id, plot_number, area_sqm, status, owner_id, debt, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET plot_number = EXCLUDED.plot_number,
                        area_sqm = EXCLUDED.area_sqm, status = EXCLUDED.status,
                        owner_id = EXCLUDED.owner_id, debt = EXCLUDED.debt
                """, [
                    plot["id"], plot["plot_number"], plot["area_sqm"], plot["status"],
                    plot.get("owner_id"), plot.get("debt", 0), plot.get("created_at"),
                ])
            for payment in payments:
                cursor.execute("""
                    INSERT INTO payments (id, owner_id, amount, payment_date, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET owner_id = EXCLUDED.owner_id,
                        amount = EXCLUDED.amount, payment_date = EXCLUDED.payment_date,
                        description = EXCLUDED.description
                """, [
                    payment["id"], payment["owner_id"], payment["amount"],
                    payment["payment_date"], payment["description"], payment.get("created_at"),
                ])
    return {"owners": len(owners), "plots": len(plots), "payments": len(payments)}
