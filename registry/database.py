"""Parameterized SQL queries used by Django views. No Django ORM is used."""
from django.db import connection


def fetch_all(sql, params=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [column[0] for column in cursor.description or ()]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_one(sql, params=()):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def get_dashboard_stats():
    return fetch_one("""
        SELECT (SELECT COUNT(*) FROM owners) AS owner_count,
               (SELECT COUNT(*) FROM plots) AS plot_count,
               (SELECT COUNT(*) FROM payments) AS payment_count,
               (SELECT COALESCE(SUM(debt), 0) FROM plots) AS total_debt
    """)


def get_plot_rows(status="", query=""):
    sql = """
        SELECT p.id, p.plot_number, p.area_sqm, p.status, p.debt,
               o.full_name AS owner_name, o.phone AS owner_phone
        FROM plots AS p LEFT JOIN owners AS o ON o.id = p.owner_id
        WHERE (%s = '' OR p.status = %s)
          AND (%s = '' OR p.plot_number LIKE %s OR o.full_name LIKE %s)
        ORDER BY p.plot_number
    """
    search = f"%{query}%"
    return fetch_all(sql, (status, status, query, search, search))


def get_plot_by_id(plot_id):
    return fetch_one("""
        SELECT p.id, p.plot_number, p.area_sqm, p.status, p.debt, p.created_at,
               o.full_name AS owner_name, o.phone AS owner_phone, o.email AS owner_email
        FROM plots AS p LEFT JOIN owners AS o ON o.id = p.owner_id
        WHERE p.id = %s
    """, (plot_id,))


def get_owner_rows():
    return fetch_all("""
        SELECT o.id, o.full_name, o.phone, o.email, COUNT(p.id) AS plot_count,
               COALESCE(SUM(p.debt), 0) AS total_debt
        FROM owners AS o LEFT JOIN plots AS p ON p.owner_id = o.id
        GROUP BY o.id, o.full_name, o.phone, o.email
        ORDER BY o.full_name
    """)


def get_payment_rows():
    return fetch_all("""
        SELECT p.id, p.payment_date, p.amount, p.description, o.full_name AS owner_name
        FROM payments AS p JOIN owners AS o ON o.id = p.owner_id
        ORDER BY p.payment_date DESC, p.id DESC
    """)


def get_statistics():
    return {
        "summary": get_dashboard_stats(),
        "by_status": fetch_all("""
            SELECT status, COUNT(*) AS plot_count, COALESCE(AVG(area_sqm), 0) AS average_area
            FROM plots GROUP BY status ORDER BY status
        """),
        "top_debtors": fetch_all("""
            SELECT o.full_name, COUNT(p.id) AS plot_count, SUM(p.debt) AS total_debt
            FROM owners AS o JOIN plots AS p ON p.owner_id = o.id
            WHERE p.debt > 0
            GROUP BY o.id, o.full_name HAVING SUM(p.debt) > %s
            ORDER BY total_debt DESC
        """, (0,)),
    }
