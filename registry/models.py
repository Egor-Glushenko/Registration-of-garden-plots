"""Django models of the garden plot registry.

PR9 moves the data layer of the project from hand-written SQL to Django ORM:
``Owner``, ``Plot``, ``Payment`` and ``Lease`` describe the same domain the
PR7 schema used, now with relations, choices, constraints and managers.
"""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, F, Q
from django.urls import reverse
from django.utils import timezone

from .slugs import build_plot_slug
from .validators import validate_plot_number, validate_phone

# Annual membership fee per square metre, used by the generated column below.
FEE_PER_SQM = Decimal("12.00")


class TimeStampedModel(models.Model):
    """Abstract base model with audit timestamps (lesson: abstract models)."""

    created_at = models.DateTimeField("Создано", default=timezone.now, db_index=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        abstract = True


class PlotStatus(models.TextChoices):
    """Allowed plot states; the values match the PR7 CHECK constraint."""

    FREE = "free", "Свободен"
    OCCUPIED = "occupied", "Занят"
    LEASED = "leased", "Аренда"
    DISPUTED = "disputed", "Спорный"


class LeaseStatus(models.TextChoices):
    """Lease life cycle: only active leases block a plot."""

    ACTIVE = "active", "Действует"
    CANCELLED = "cancelled", "Отменена"
    COMPLETED = "completed", "Завершена"


class PaymentStatus(models.TextChoices):
    """A cancelled payment stays in the database but is ignored in totals."""

    POSTED = "posted", "Проведён"
    CANCELLED = "cancelled", "Отменён"


class PlotQuerySet(models.QuerySet):
    """Reusable querysets for the plot registry page."""

    def with_owner(self):
        """Join the owner in the same query to avoid N+1 selects."""
        return self.select_related("owner")

    def of_status(self, status):
        """Filter by a status value coming from an HTTP parameter."""
        if not status or status not in PlotStatus.values:
            return self
        return self.filter(status=status)

    def search(self, text):
        """Search by plot number or by the related owner name."""
        text = (text or "").strip()
        if not text:
            return self
        return self.filter(
            Q(plot_number__icontains=text) | Q(owner__full_name__icontains=text)
        )

    def free(self):
        return self.filter(status=PlotStatus.FREE)

    def with_counters(self):
        """Annotate related object counters using a single GROUP BY query."""
        return self.annotate(
            lease_count=Count("leases", distinct=True),
            payment_count=Count("owner__payments", distinct=True),
        )


PlotManager = models.Manager.from_queryset(PlotQuerySet)


class OwnerQuerySet(models.QuerySet):
    """Querysets with aggregated plot and payment figures."""

    def with_totals(self):
        """Annotate plot count and debt with aggregate functions."""
        return self.annotate(
            plot_count=Count("plots", distinct=True),
            total_debt=models.Sum("plots__debt"),
            paid_total=models.Sum(
                "payments__amount",
                filter=Q(payments__status=PaymentStatus.POSTED),
            ),
        )

    def search(self, text):
        text = (text or "").strip()
        if not text:
            return self
        return self.filter(
            Q(full_name__icontains=text)
            | Q(phone__icontains=text)
            | Q(email__icontains=text)
        )


OwnerManager = models.Manager.from_queryset(OwnerQuerySet)


class LeaseQuerySet(models.QuerySet):
    """Querysets that encapsulate the "lease blocks a plot" rule."""

    def active(self):
        return self.filter(status=LeaseStatus.ACTIVE)

    def for_plot(self, plot):
        return self.filter(plot=plot)

    def overlapping(self, plot, start_date, end_date, exclude_pk=None):
        """Return active leases of a plot that intersect the given period."""
        query = self.active().filter(
            plot=plot,
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        if exclude_pk:
            query = query.exclude(pk=exclude_pk)
        return query

    def with_related(self):
        return self.select_related("plot", "owner")


LeaseManager = models.Manager.from_queryset(LeaseQuerySet)


class PaymentQuerySet(models.QuerySet):
    """Posted payments only take part in financial totals."""

    def posted(self):
        return self.filter(status=PaymentStatus.POSTED)

    def cancelled(self):
        return self.filter(status=PaymentStatus.CANCELLED)

    def with_owner(self):
        return self.select_related("owner")


PaymentManager = models.Manager.from_queryset(PaymentQuerySet)


class Owner(TimeStampedModel):
    """A gardener registered in the registry."""

    full_name = models.CharField("ФИО", max_length=200)
    phone = models.CharField(
        "Телефон", max_length=40, validators=[validate_phone]
    )
    email = models.EmailField("Электронная почта", blank=True)

    objects = OwnerManager()

    class Meta:
        verbose_name = "Владелец"
        verbose_name_plural = "Владельцы"
        ordering = ("full_name",)
        indexes = [models.Index(fields=["full_name"], name="owner_name_idx")]

    def __str__(self):
        return self.full_name

    def debt_total(self):
        """Total debt of all plots of the owner (aggregate() call)."""
        return self.plots.aggregate(total=models.Sum("debt"))["total"] or Decimal("0.00")

    def plot_count(self):
        """Number of plots bound to the owner."""
        return self.plots.count()


class Plot(TimeStampedModel):
    """A garden plot: the central entity of the registry."""

    plot_number = models.CharField(
        "Номер участка",
        max_length=40,
        unique=True,
        validators=[validate_plot_number],
    )
    slug = models.SlugField("Адрес", max_length=60, unique=True, blank=True)
    area_sqm = models.DecimalField(
        "Площадь, м²",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1.00"))],
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=PlotStatus.choices,
        default=PlotStatus.FREE,
        db_index=True,
    )
    owner = models.ForeignKey(
        Owner,
        verbose_name="Владелец",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plots",
    )
    debt = models.DecimalField(
        "Задолженность, ₽",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    image = models.ImageField(
        "Изображение",
        upload_to="plots/",
        blank=True,
        null=True,
    )
    # Generated column: the database itself keeps area * rate up to date.
    membership_fee = models.GeneratedField(
        expression=F("area_sqm") * FEE_PER_SQM,
        output_field=models.DecimalField(max_digits=12, decimal_places=2),
        db_persist=True,
        verbose_name="Членский взнос, ₽/год",
    )

    objects = PlotManager()

    class Meta:
        verbose_name = "Участок"
        verbose_name_plural = "Участки"
        ordering = ("plot_number",)
        constraints = [
            models.CheckConstraint(
                condition=Q(area_sqm__gt=0), name="plot_area_positive"
            ),
            models.CheckConstraint(
                condition=Q(debt__gte=0), name="plot_debt_not_negative"
            ),
        ]
        indexes = [
            models.Index(fields=["status", "plot_number"], name="plot_status_idx"),
        ]

    def __str__(self):
        return f"Участок № {self.plot_number}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._build_slug()
        super().save(*args, **kwargs)

    def _build_slug(self):
        """Build a unique ASCII slug from the plot number."""
        base = build_plot_slug(self.plot_number)
        candidate, counter = base, 1
        queryset = Plot.objects.exclude(pk=self.pk)
        while queryset.filter(slug=candidate).exists():
            counter += 1
            candidate = f"{base}-{counter}"
        return candidate

    def clean(self):
        """Keep the status/owner pair consistent."""
        from django.core.exceptions import ValidationError

        if self.status == PlotStatus.FREE and self.owner_id:
            raise ValidationError(
                {"owner": "У свободного участка не может быть владельца."}
            )
        if self.status in {PlotStatus.OCCUPIED, PlotStatus.LEASED} and not self.owner_id:
            raise ValidationError(
                {"owner": "Для занятого или арендованного участка укажите владельца."}
            )

    def get_absolute_url(self):
        return reverse("registry:plot_detail", kwargs={"slug": self.slug})

    @property
    def has_owner(self):
        return self.owner_id is not None

    @property
    def active_lease(self):
        """The lease that currently blocks the plot, if any."""
        return self.leases.active().order_by("-start_date").first()


class Payment(TimeStampedModel):
    """A membership fee payment made by an owner."""

    owner = models.ForeignKey(
        Owner,
        verbose_name="Владелец",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(
        "Сумма, ₽",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    payment_date = models.DateField("Дата платежа", default=timezone.localdate, db_index=True)
    description = models.CharField("Назначение", max_length=200)
    status = models.CharField(
        "Состояние",
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.POSTED,
        db_index=True,
    )

    objects = PaymentManager()

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ("-payment_date", "-id")
        indexes = [
            models.Index(fields=["owner", "-payment_date"], name="payment_owner_date_idx"),
        ]

    def __str__(self):
        return f"{self.owner}: {self.amount} ₽ от {self.payment_date:%d.%m.%Y}"

    def cancel(self):
        """Cancel a payment instead of deleting financial history."""
        self.status = PaymentStatus.CANCELLED
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_posted(self):
        return self.status == PaymentStatus.POSTED


class Lease(TimeStampedModel):
    """A lease of a plot for a period; only active leases block the plot."""

    plot = models.ForeignKey(
        Plot,
        verbose_name="Участок",
        on_delete=models.CASCADE,
        related_name="leases",
    )
    owner = models.ForeignKey(
        Owner,
        verbose_name="Арендатор",
        on_delete=models.PROTECT,
        related_name="leases",
    )
    start_date = models.DateField("Дата начала", default=timezone.localdate)
    end_date = models.DateField("Дата окончания")
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=LeaseStatus.choices,
        default=LeaseStatus.ACTIVE,
        db_index=True,
    )
    note = models.CharField("Комментарий", max_length=200, blank=True)

    objects = LeaseManager()

    class Meta:
        verbose_name = "Аренда участка"
        verbose_name_plural = "Аренды участков"
        ordering = ("-start_date", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="lease_period_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["plot", "start_date"], name="lease_plot_date_idx"),
        ]

    def __str__(self):
        return f"{self.plot} для {self.owner} ({self.start_date:%d.%m.%Y}–{self.end_date:%d.%m.%Y})"

    def clean(self):
        """Validate the period and the plot availability."""
        from django.core.exceptions import ValidationError

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": "Дата окончания не может быть раньше даты начала."}
            )
        if self.plot_id and self.start_date and self.end_date:
            conflict = Lease.objects.overlapping(
                self.plot,
                self.start_date,
                self.end_date,
                exclude_pk=self.pk,
            ).exists()
            if conflict:
                raise ValidationError(
                    "На выбранные даты участок уже арендован. "
                    "Выберите другой период или участок."
                )

    def cancel(self):
        """Cancel the lease keeping the record for the archive."""
        self.status = LeaseStatus.CANCELLED
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_active(self):
        return self.status == LeaseStatus.ACTIVE

    @property
    def duration_days(self):
        if not self.end_date or not self.start_date:
            return 0
        return (self.end_date - self.start_date).days + 1
