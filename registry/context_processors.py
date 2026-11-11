"""Template context processors of the registry (PR10, subsection 5.4.6)."""

from .models import Lease, Owner, Plot, PlotStatus

# Pages that do not need registration counters (admin renders its own context).
SKIPPED_PREFIXES = ("/admin/", "/static/", "/media/", "/__debug__/")


def registry_summary(request):
    """Add short registry counters to every public page."""
    path = getattr(request, "path", "")
    if path.startswith(SKIPPED_PREFIXES):
        return {}
    return {
        "registry_summary": {
            "plots": Plot.objects.count(),
            "free_plots": Plot.objects.filter(status=PlotStatus.FREE).count(),
            "owners": Owner.objects.count(),
            "active_leases": Lease.objects.active().count(),
        },
    }
