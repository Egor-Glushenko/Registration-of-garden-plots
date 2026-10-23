"""Database helpers for the PR7 SQLite/SQL layer and optional PostgreSQL."""
from django.db import connection


def get_connection():
    """Return Django's configured DB connection (SQLite locally, Postgres on deploy)."""
    connection.ensure_connection()
    return connection


def initialize_schema():
    """Create the SQL tables from the schema matching the selected backend."""
    from pathlib import Path

    schema_file = "schema_postgres.sql" if connection.vendor == "postgresql" else "schema.sql"
    schema = Path(__file__).resolve().parent.parent / "sql" / schema_file
    sql = schema.read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement and not statement.lower().startswith("pragma"):
                cursor.execute(statement)


def rows_as_dicts(cursor):
    columns = [item[0] for item in cursor.description or ()]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
