"""Fill the new lease rent with a value derived from the plot fee (PR10).

Existing rows receive a calculated rent so the column is not left empty after
the schema change; the value equals the annual membership fee of the plot and
can be adjusted by the registry administrator afterwards.
"""
from decimal import Decimal

from django.db import migrations

FEE_PER_SQM = Decimal("12.00")


def fill_rent(apps, schema_editor):
    Lease = apps.get_model("registry", "Lease")
    for lease in Lease.objects.select_related("plot").filter(rent_amount=0):
        area = lease.plot.area_sqm or Decimal("0")
        lease.rent_amount = (area * FEE_PER_SQM).quantize(Decimal("0.01"))
        lease.save(update_fields=["rent_amount"])


class Migration(migrations.Migration):
    dependencies = [("registry", "0003_lease_rent_amount")]
    operations = [migrations.RunPython(fill_rent, migrations.RunPython.noop)]
