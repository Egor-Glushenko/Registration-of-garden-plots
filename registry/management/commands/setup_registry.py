from django.core.management.base import BaseCommand

from db.import_json import import_json


class Command(BaseCommand):
    help = "Create the SQL schema and import local or demo JSON records."

    def handle(self, *args, **options):
        counts = import_json()
        self.stdout.write(self.style.SUCCESS(
            "Registry ready: " + ", ".join(f"{name}={count}" for name, count in counts.items())
        ))
