"""Views of the registry: ORM reads and Django Forms handling (PR9–PR11)."""
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_POST

from . import queries, services
from .forms import (
    LeaseFilterForm,
    LeaseForm,
    OwnerFilterForm,
    OwnerForm,
    PaymentFilterForm,
    PaymentForm,
    PlotFilterForm,
    PlotForm,
)
from .models import Lease, Owner, Payment, Plot


def _page_number(request):
    """Read a page number, tolerating invalid values."""
    try:
        return max(int(request.GET.get("page", 1)), 1)
    except (TypeError, ValueError):
        return 1


def _querystring(request, drop=("page",)):
    """Rebuild the current filter string for pagination links."""
    params = {key: value for key, value in request.GET.items() if key not in drop and value}
    return urlencode(params)


def _clean_filters(request, form_class):
    """Validate GET parameters and return a dictionary with safe values.

    An invalid filter never raises: the page shows the warning and falls back to
    the unfiltered list, so a broken link cannot produce a server error.
    """
    if not request.GET:
        return form_class(), {}
    form = form_class(request.GET)
    if not form.is_valid():
        messages.warning(request, "Параметры фильтра некорректны — показаны все записи.")
        return form, {}
    return form, dict(form.cleaned_data)


def plots(request):
    """Plot list with the filter form, sorting and pagination."""
    form, filters = _clean_filters(request, PlotFilterForm)
    page = queries.plot_page(
        status=filters.get("status") or "",
        query=filters.get("q") or "",
        ordering=filters.get("ordering") or queries.DEFAULT_PLOT_ORDERING,
        area_min=filters.get("area_min"),
        page=_page_number(request),
    )
    return render(request, "registry/plots.html", {
        "page_obj": page,
        "plots": page.object_list,
        "form": form,
        "querystring": _querystring(request),
        "has_filters": any(filters.get(key) for key in ("status", "q", "area_min")),
    })


def plot_detail(request, slug):
    """Plot card; an unknown slug returns the 404 page."""
    plot = get_object_or_404(
        Plot.objects.select_related("owner").prefetch_related("leases__owner", "owner__payments"),
        slug=slug,
    )
    return render(request, "registry/plot_detail.html", {
        "plot": plot,
        "leases": plot.leases.select_related("owner"),
        "payments": plot.owner.payments.posted()[:5] if plot.owner_id else [],
    })


def plot_detail_by_id(request, plot_id):
    """Legacy numeric address kept for the links created before PR9."""
    plot = Plot.objects.filter(pk=plot_id).only("slug").first()
    if plot is None:
        raise Http404("Участок не найден")
    return redirect(reverse("registry:plot_detail", kwargs={"slug": plot.slug}), permanent=True)


def plot_create(request):
    """Create a plot through ModelForm (GET shows the form, POST saves it)."""
    form = PlotForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        plot = form.save()
        messages.success(request, f"Участок № {plot.plot_number} добавлен в реестр.")
        return redirect(plot.get_absolute_url())
    return render(request, "registry/form_page.html", {
        "form": form,
        "title": "Новый участок",
        "intro": "Заполните сведения об участке. Поля, отмеченные подсказками, влияют на проверки реестра.",
        "submit_label": "Сохранить участок",
        "cancel_url": reverse("registry:plots"),
    })


def plot_update(request, slug):
    """Edit an existing plot; the image can be replaced or kept."""
    plot = get_object_or_404(Plot, slug=slug)
    form = PlotForm(request.POST or None, request.FILES or None, instance=plot)
    if request.method == "POST" and form.is_valid():
        plot = form.save()
        messages.success(request, f"Данные участка № {plot.plot_number} сохранены.")
        return redirect(plot.get_absolute_url())
    return render(request, "registry/form_page.html", {
        "form": form,
        "plot": plot,
        "title": f"Участок № {plot.plot_number}",
        "intro": "Изменение карточки участка. История аренды и платежи сохраняются.",
        "submit_label": "Сохранить изменения",
        "cancel_url": plot.get_absolute_url(),
    })


def owners(request):
    form, filters = _clean_filters(request, OwnerFilterForm)
    page = queries.owner_page(query=filters.get("q") or "", page=_page_number(request))
    return render(request, "registry/owners.html", {
        "page_obj": page,
        "owners": page.object_list,
        "form": form,
        "querystring": _querystring(request),
    })


def owner_create(request):
    form = OwnerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        owner = form.save()
        messages.success(request, f"Владелец «{owner.full_name}» добавлен.")
        return redirect("registry:owners")
    return render(request, "registry/form_page.html", {
        "form": form,
        "title": "Новый владелец",
        "intro": "Контактные данные владельца. Участки закрепляются в карточке участка.",
        "submit_label": "Сохранить владельца",
        "cancel_url": reverse("registry:owners"),
    })


def owner_update(request, pk):
    owner = get_object_or_404(Owner, pk=pk)
    form = OwnerForm(request.POST or None, instance=owner)
    if request.method == "POST" and form.is_valid():
        owner = form.save()
        messages.success(request, f"Данные владельца «{owner.full_name}» сохранены.")
        return redirect("registry:owners")
    return render(request, "registry/form_page.html", {
        "form": form,
        "owner": owner,
        "title": owner.full_name,
        "intro": "Изменение контактных данных владельца.",
        "submit_label": "Сохранить изменения",
        "cancel_url": reverse("registry:owners"),
    })


def payments(request):
    form, filters = _clean_filters(request, PaymentFilterForm)
    page = queries.payment_page(
        query=filters.get("q") or "",
        status=filters.get("status") or "",
        ordering=filters.get("ordering") or queries.DEFAULT_PAYMENT_ORDERING,
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
        page=_page_number(request),
    )
    return render(request, "registry/payments.html", {
        "page_obj": page,
        "payments": page.object_list,
        "form": form,
        "querystring": _querystring(request),
    })


def payment_create(request):
    form = PaymentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payment = form.save()
        messages.success(request, f"Платёж на {payment.amount} ₽ зарегистрирован.")
        return redirect("registry:payments")
    return render(request, "registry/form_page.html", {
        "form": form,
        "title": "Новый платёж",
        "intro": "Платёж привязывается к владельцу и учитывается в статистике.",
        "submit_label": "Зарегистрировать платёж",
        "cancel_url": reverse("registry:payments"),
    })


@require_POST
def payment_cancel(request, pk):
    """Cancel a payment with POST; a GET request receives 405."""
    payment = get_object_or_404(Payment.objects.with_owner(), pk=pk)
    services.cancel_payment(payment)
    messages.warning(
        request,
        f"Платёж от {payment.payment_date:%d.%m.%Y} отменён. Запись сохранена в истории.",
    )
    return redirect("registry:payments")


def leases(request):
    form, filters = _clean_filters(request, LeaseFilterForm)
    page = queries.lease_page(
        plot=filters.get("plot"),
        owner=filters.get("owner"),
        status=filters.get("status") or "",
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
        ordering=filters.get("ordering") or queries.DEFAULT_LEASE_ORDERING,
        page=_page_number(request),
    )
    return render(request, "registry/leases.html", {
        "page_obj": page,
        "leases": page.object_list,
        "form": form,
        "querystring": _querystring(request),
    })


def lease_detail(request, pk):
    lease = get_object_or_404(Lease.objects.with_related(), pk=pk)
    return render(request, "registry/lease_detail.html", {"lease": lease})


def lease_create(request):
    form = LeaseForm(request.POST or None, initial={"plot": request.GET.get("plot") or None})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            lease = services.save_lease(form.save())
        messages.success(
            request,
            f"Аренда участка № {lease.plot.plot_number} оформлена на период "
            f"{lease.start_date:%d.%m.%Y}–{lease.end_date:%d.%m.%Y}.",
        )
        return redirect("registry:lease_detail", pk=lease.pk)
    return render(request, "registry/form_page.html", {
        "form": form,
        "title": "Новая аренда участка",
        "intro": "Участок нельзя арендовать дважды на пересекающиеся даты.",
        "submit_label": "Оформить аренду",
        "cancel_url": reverse("registry:leases"),
    })


def lease_update(request, pk):
    lease = get_object_or_404(Lease.objects.with_related(), pk=pk)
    form = LeaseForm(request.POST or None, instance=lease)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            lease = services.save_lease(form.save())
        messages.success(request, "Изменения аренды сохранены.")
        return redirect("registry:lease_detail", pk=lease.pk)
    return render(request, "registry/form_page.html", {
        "form": form,
        "lease": lease,
        "title": f"Аренда участка № {lease.plot.plot_number}",
        "intro": "Проверка занятости не учитывает редактируемую запись.",
        "submit_label": "Сохранить изменения",
        "cancel_url": reverse("registry:lease_detail", kwargs={"pk": lease.pk}),
    })


@require_POST
def lease_cancel(request, pk):
    """Cancel a lease with POST and release the plot."""
    lease = get_object_or_404(Lease.objects.with_related(), pk=pk)
    services.cancel_lease(lease)
    messages.warning(
        request,
        f"Аренда участка № {lease.plot.plot_number} отменена. "
        "Статус участка обновлён, запись сохранена в архиве.",
    )
    return redirect("registry:leases")


def statistics(request):
    return render(request, "registry/statistics.html", {"stats": queries.statistics()})
