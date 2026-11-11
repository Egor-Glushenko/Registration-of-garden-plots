"""Import the PR7 SQL tables and JSON files (previous data layer).

The module is kept as the archived PR7 implementation: it creates the legacy
``owners`` / ``plots`` / ``payments`` tables from ``sql/schema.sql`` and fills
them. The PR9 data migration copies these tables into the Django models.
"""
from django.core.management.base import BaseCommand

from db.import_json import import_json


class Command(BaseCommand):
    help = "Создаёт SQL-таблицы ПР7 и импортирует в них JSON (устаревший слой)."

    def handle(self, *args, **options):
        counts = import_json()
        self.stdout.write(self.style.SUCCESS(
            "Слой ПР7 заполнен: " + ", ".join(f"{name}={count}" for name, count in counts.items())
        ))
