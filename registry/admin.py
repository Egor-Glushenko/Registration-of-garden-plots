"""Django Admin configuration for the registry (PR10).

Every model is registered with a ModelAdmin that exposes list columns, search,
filters, ordering, inlines and bulk actions, so the registry can be maintained
without the front-end pages.
"""
from django.contrib import admin, messages
from django.db.models import Count, F, Sum
from django.urls import reverse
from django.utils.html import format_html

from .models import Lease, LeaseStatus, Owner, Payment, PaymentStatus, Plot, PlotStatus

admin.site.site_header = "Садовый реестр — администрирование"
admin.site.site_title = "Садовый реестр"
admin.site.index_title = "Управление данными реестра"


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    """Owner list with aggregated figures and inline related records."""

    list_display = ("full_name", "phone", "email", "plots_total", "debt_total", "created_at")
    list_filter = ("created_at", "plots__status")
    search_fields = ("full_name", "phone", "email")
    ordering = ("full_name",)
    list_per_page = 20
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Контакты", {"fields": ("full_name", "phone", "email")}),
        ("Служебная информация", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    inlines = []

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(plots_amount=Count("plots", distinct=True), debt_sum=Sum("plots__debt"))
        )

    @admin.display(description="Участков", ordering="plots_amount")
    def plots_total(self, obj):
        return obj.plots_amount

    @admin.display(description="Задолженность, ₽", ordering="debt_sum")
    def debt_total(self, obj):
        return obj.debt_sum or 0


class PlotInline(admin.TabularInline):
    """Owner card shows the plots of the owner."""

    model = Plot
    fk_name = "owner"
    extra = 0
    fields = ("plot_number", "status", "area_sqm", "debt")
    readonly_fields = ("plot_number",)
    show_change_link = True
    verbose_name_plural = "Участки владельца"


class LeaseInline(admin.TabularInline):
    """Plot card shows its lease history."""

    model = Lease
    fk_name = "plot"
    extra = 1
    fields = ("owner", "start_date", "end_date", "status", "rent_amount", "note")
    autocomplete_fields = ("owner",)
    verbose_name_plural = "Аренда участка"


class OwnerLeaseInline(admin.TabularInline):
    """Owner card shows the leases of the owner."""

    model = Lease
    fk_name = "owner"
    extra = 0
    fields = ("plot", "start_date", "end_date", "status")
    autocomplete_fields = ("plot",)
    verbose_name_plural = "Аренды владельца"


class PaymentInline(admin.TabularInline):
    """Owner card shows the latest payments (read only)."""

    model = Payment
    fk_name = "owner"
    extra = 0
    can_delete = False
    fields = ("payment_date", "amount", "description", "status")
    readonly_fields = ("payment_date", "amount", "description", "status")
    verbose_name_plural = "Платежи владельца"

    def has_add_permission(self, request, obj=None):
        return False


OwnerAdmin.inlines = [PlotInline, OwnerLeaseInline, PaymentInline]


@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    """Plot list with editable status and debt plus bulk actions."""

    list_display = (
        "plot_number", "status_badge", "area_sqm", "owner_link",
        "debt", "membership_fee", "leases_total", "image_preview",
    )
    list_display_links = ("plot_number",)
    list_filter = ("status", "created_at", "owner")
    search_fields = ("plot_number", "slug", "owner__full_name", "owner__phone")
    list_select_related = ("owner",)
    autocomplete_fields = ("owner",)
    list_editable = ("debt",)
    ordering = ("plot_number",)
    list_per_page = 15
    date_hierarchy = "created_at"
    readonly_fields = ("slug", "membership_fee", "image_preview", "created_at", "updated_at")
    fieldsets = (
        ("Участок", {"fields": ("plot_number", "slug", "area_sqm", "status", "owner")}),
        ("Финансы", {"fields": ("debt", "membership_fee")}),
        ("Изображение", {"fields": ("image", "image_preview"), "classes": ("collapse",)}),
        ("Служебная информация", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    inlines = [LeaseInline]
    actions = ("mark_as_free", "mark_as_disputed", "clear_debt", "apply_penalty")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(leases_amount=Count("leases"))

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        colors = {
            PlotStatus.FREE: "#2f5b3c",
            PlotStatus.OCCUPIED: "#315b48",
            PlotStatus.LEASED: "#7a5c1e",
            PlotStatus.DISPUTED: "#8c2d1f",
        }
        color = colors.get(obj.status, "#4d5a51")
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Владелец", ordering="owner__full_name")
    def owner_link(self, obj):
        if not obj.owner_id:
            return "—"
        url = reverse("admin:registry_owner_change", args=[obj.owner_id])
        return format_html('<a href="{}">{}</a>', url, obj.owner)

    @admin.display(description="Аренд", ordering="leases_amount")
    def leases_total(self, obj):
        return obj.leases_amount

    @admin.display(description="Фото")
    def image_preview(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" style="height:44px;border-radius:4px" alt="">', obj.image.url)

    @admin.action(description="Отметить выбранные участки свободными")
    def mark_as_free(self, request, queryset):
        updated = queryset.update(status=PlotStatus.FREE, owner=None)
        self.message_user(request, f"Освобождено участков: {updated}.", messages.SUCCESS)

    @admin.action(description="Отметить выбранные участки спорными")
    def mark_as_disputed(self, request, queryset):
        updated = queryset.update(status=PlotStatus.DISPUTED)
        self.message_user(request, f"Переведено в спорные: {updated}.", messages.WARNING)

    @admin.action(description="Обнулить задолженность")
    def clear_debt(self, request, queryset):
        updated = queryset.update(debt=0)
        self.message_user(request, f"Задолженность снята по {updated} участкам.", messages.SUCCESS)

    @admin.action(description="Начислить пеню 5%% (вычисление в базе через F())")
    def apply_penalty(self, request, queryset):
        # F() keeps the arithmetic in SQL: no read-modify-write round trip.
        updated = queryset.filter(debt__gt=0).update(debt=F("debt") * 1.05)
        self.message_user(
            request,
            f"Пеня начислена по {updated} участкам с задолженностью.",
            messages.WARNING,
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment register with cancellation action instead of deletion."""

    list_display = ("payment_date", "owner", "amount", "description", "status_badge")
    list_filter = ("status", "payment_date")
    search_fields = ("owner__full_name", "description")
    autocomplete_fields = ("owner",)
    date_hierarchy = "payment_date"
    list_select_related = ("owner",)
    ordering = ("-payment_date", "-id")
    list_per_page = 20
    readonly_fields = ("created_at", "updated_at")
    actions = ("cancel_payments", "restore_payments")

    @admin.display(description="Состояние", ordering="status")
    def status_badge(self, obj):
        color = "#2f5b3c" if obj.status == PaymentStatus.POSTED else "#8c2d1f"
        return format_html('<span style="color:{};font-weight:600">{}</span>', color, obj.get_status_display())

    @admin.action(description="Отменить выбранные платежи")
    def cancel_payments(self, request, queryset):
        updated = queryset.update(status=PaymentStatus.CANCELLED)
        self.message_user(request, f"Отменено платежей: {updated}.", messages.WARNING)

    @admin.action(description="Вернуть платежи в состояние «проведён»")
    def restore_payments(self, request, queryset):
        updated = queryset.update(status=PaymentStatus.POSTED)
        self.message_user(request, f"Восстановлено платежей: {updated}.", messages.SUCCESS)


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    """Lease register with period filters and cancellation action."""

    list_display = ("plot", "owner", "start_date", "end_date", "duration", "rent_amount", "status_badge")
    list_filter = ("status", "start_date", "end_date", "plot__status")
    search_fields = ("plot__plot_number", "owner__full_name", "note")
    autocomplete_fields = ("plot", "owner")
    list_select_related = ("plot", "owner")
    date_hierarchy = "start_date"
    ordering = ("-start_date",)
    list_per_page = 20
    readonly_fields = ("created_at", "updated_at")
    actions = ("cancel_leases",)

    @admin.display(description="Дней")
    def duration(self, obj):
        return obj.duration_days

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        colors = {
            LeaseStatus.ACTIVE: "#2f5b3c",
            LeaseStatus.CANCELLED: "#8c2d1f",
            LeaseStatus.COMPLETED: "#6b5f47",
        }
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>',
            colors.get(obj.status, "#4d5a51"),
            obj.get_status_display(),
        )

    @admin.action(description="Отменить выбранные аренды")
    def cancel_leases(self, request, queryset):
        updated = queryset.update(status=LeaseStatus.CANCELLED)
        self.message_user(
            request,
            f"Отменено аренд: {updated}. Отменённые аренды больше не блокируют участки.",
            messages.WARNING,
        )


# The registry admin index also shows a short help block.
admin.site.empty_value_display = "—"
