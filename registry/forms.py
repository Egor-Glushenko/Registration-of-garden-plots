"""Django Forms of the registry (PR11).

Two groups of forms live here:

* filter forms based on ``forms.Form`` — they read GET parameters, validate them
  and return ``cleaned_data`` for the ORM query layer;
* model forms based on ``forms.ModelForm`` — they create and edit plots, owners,
  payments and leases, check the business rules and upload images.
"""
from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Lease, LeaseStatus, Owner, Payment, PaymentStatus, Plot, PlotStatus


class BootstrapFormMixin:
    """Add CSS classes and empty labels to rendered widgets."""

    css_class = "form-control"

    def _style_fields(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.FileInput)):
                continue
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {self.css_class}".strip()


class PlotFilterForm(BootstrapFormMixin, forms.Form):
    """GET filter of the plot registry page."""

    q = forms.CharField(
        label="Поиск",
        required=False,
        max_length=60,
        widget=forms.TextInput(attrs={"placeholder": "Номер участка или владелец"}),
    )
    status = forms.ChoiceField(
        label="Статус",
        required=False,
        choices=[("", "Все статусы"), *PlotStatus.choices],
    )
    ordering = forms.ChoiceField(
        label="Сортировка",
        required=False,
        choices=(("number", "По номеру"), ("area", "По площади"),
                 ("debt", "По задолженности"), ("status", "По статусу")),
    )
    area_min = forms.DecimalField(
        label="Площадь от, м²",
        required=False,
        min_value=0,
        max_digits=8,
        decimal_places=2,
        help_text="Отбор участков площадью не меньше указанной.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean_q(self):
        """Trim the search string and drop too short values."""
        value = (self.cleaned_data["q"] or "").strip()
        if len(value) == 1:
            raise ValidationError("Введите хотя бы два символа для поиска.")
        return value


class OwnerFilterForm(BootstrapFormMixin, forms.Form):
    """GET filter of the owner registry page."""

    q = forms.CharField(
        label="Поиск",
        required=False,
        max_length=60,
        widget=forms.TextInput(attrs={"placeholder": "ФИО, телефон или почта"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean_q(self):
        return (self.cleaned_data["q"] or "").strip()


class PaymentFilterForm(BootstrapFormMixin, forms.Form):
    """GET filter of the payment history page."""

    q = forms.CharField(
        label="Поиск",
        required=False,
        max_length=60,
        widget=forms.TextInput(attrs={"placeholder": "Владелец или назначение"}),
    )
    status = forms.ChoiceField(
        label="Состояние",
        required=False,
        choices=[("", "Все состояния"), *PaymentStatus.choices],
    )
    ordering = forms.ChoiceField(
        label="Сортировка",
        required=False,
        choices=(("date", "По дате"), ("amount", "По сумме"), ("owner", "По владельцу")),
    )
    date_from = forms.DateField(
        label="Платежи с",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        label="Платежи по",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean(self):
        cleaned = super().clean()
        date_from, date_to = cleaned.get("date_from"), cleaned.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Дата начала периода не может быть позже даты окончания.")
        return cleaned


class LeaseFilterForm(BootstrapFormMixin, forms.Form):
    """GET filter of the lease page (plot, owner, state and period)."""

    plot = forms.ModelChoiceField(
        label="Участок",
        required=False,
        queryset=Plot.objects.order_by("plot_number"),
        empty_label="Все участки",
    )
    owner = forms.ModelChoiceField(
        label="Арендатор",
        required=False,
        queryset=Owner.objects.order_by("full_name"),
        empty_label="Все арендаторы",
    )
    status = forms.ChoiceField(
        label="Статус",
        required=False,
        choices=[("", "Все статусы"), *LeaseStatus.choices],
    )
    ordering = forms.ChoiceField(
        label="Сортировка",
        required=False,
        choices=(("start", "По дате начала"), ("plot", "По участку"), ("owner", "По арендатору")),
    )
    date_from = forms.DateField(
        label="Период с",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        label="Период по",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean(self):
        cleaned = super().clean()
        date_from, date_to = cleaned.get("date_from"), cleaned.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Дата начала периода не может быть позже даты окончания.")
        return cleaned


class OwnerForm(BootstrapFormMixin, forms.ModelForm):
    """Create or edit an owner."""

    class Meta:
        model = Owner
        fields = ("full_name", "phone", "email")
        labels = {
            "full_name": "ФИО владельца",
            "phone": "Телефон",
            "email": "Электронная почта",
        }
        help_texts = {
            "full_name": "Фамилия, имя и отчество полностью.",
            "phone": "Например: +7 916 240-11-08.",
            "email": "Необязательное поле для уведомлений.",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Иванова Мария Петровна"}),
            "phone": forms.TextInput(attrs={"placeholder": "+7 916 000-00-00"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class PlotForm(BootstrapFormMixin, forms.ModelForm):
    """Create or edit a plot; checks the status/owner rule and the image type."""

    class Meta:
        model = Plot
        fields = ("plot_number", "area_sqm", "status", "owner", "debt", "image")
        labels = {
            "plot_number": "Номер участка",
            "area_sqm": "Площадь, м²",
            "status": "Статус",
            "owner": "Владелец",
            "debt": "Задолженность, ₽",
            "image": "Изображение участка",
        }
        help_texts = {
            "plot_number": "Число и, при необходимости, буква: 15 или 16-Б.",
            "area_sqm": "Площадь в квадратных метрах, больше нуля.",
            "owner": "Для свободного участка владелец не указывается.",
            "image": "Файл JPG, PNG или WebP до 5 МБ.",
        }
        widgets = {
            "plot_number": forms.TextInput(attrs={"placeholder": "16-Б"}),
            "area_sqm": forms.NumberInput(attrs={"step": "0.01", "min": "1"}),
            "debt": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].empty_label = "Владелец не назначен"
        self._style_fields()

    def clean_area_sqm(self):
        area = self.cleaned_data["area_sqm"]
        if area is not None and area < 1:
            raise ValidationError("Площадь участка должна быть не меньше 1 м².")
        return area

    def clean_image(self):
        """Reject files that are too large before they reach the storage."""
        image = self.cleaned_data.get("image")
        if image and image.size > 5 * 1024 * 1024:
            raise ValidationError("Размер изображения не должен превышать 5 МБ.")
        return image

    def clean(self):
        cleaned = super().clean()
        status, owner = cleaned.get("status"), cleaned.get("owner")
        if status == PlotStatus.FREE and owner:
            self.add_error("owner", "У свободного участка не может быть владельца.")
        if status in {PlotStatus.OCCUPIED, PlotStatus.LEASED} and not owner:
            self.add_error("owner", "Для занятого или арендованного участка укажите владельца.")
        return cleaned


class PaymentForm(BootstrapFormMixin, forms.ModelForm):
    """Register a payment; the date cannot be in the future."""

    class Meta:
        model = Payment
        fields = ("owner", "amount", "payment_date", "description")
        labels = {
            "owner": "Владелец",
            "amount": "Сумма, ₽",
            "payment_date": "Дата платежа",
            "description": "Назначение платежа",
        }
        help_texts = {
            "amount": "Сумма больше нуля.",
            "payment_date": "Дата не может быть в будущем.",
            "description": "Например: членский взнос за 2026 год.",
        }
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.TextInput(attrs={"placeholder": "Членский взнос за 2026 год"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["payment_date"].initial = timezone.localdate()
        self._style_fields()

    def clean_payment_date(self):
        payment_date = self.cleaned_data["payment_date"]
        if payment_date and payment_date > timezone.localdate():
            raise ValidationError("Дата платежа не может быть в будущем.")
        return payment_date

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount is not None and amount <= 0:
            raise ValidationError("Сумма платежа должна быть больше нуля.")
        return amount


class LeaseForm(BootstrapFormMixin, forms.ModelForm):
    """Create or edit a lease with availability and period checks."""

    class Meta:
        model = Lease
        fields = ("plot", "owner", "start_date", "end_date", "rent_amount", "note")
        labels = {
            "plot": "Участок",
            "owner": "Арендатор",
            "start_date": "Дата начала",
            "end_date": "Дата окончания",
            "rent_amount": "Арендная плата, ₽",
            "note": "Комментарий",
        }
        help_texts = {
            "plot": "Участок, который передаётся в аренду.",
            "start_date": "Дата не может быть в прошлом.",
            "end_date": "Дата окончания не раньше даты начала.",
            "rent_amount": "Сумма договора аренды за период.",
        }
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "rent_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "note": forms.TextInput(attrs={"placeholder": "Например: договор на сезон"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and not self.instance.pk:
            self.fields["start_date"].initial = timezone.localdate()
            self.fields["end_date"].initial = timezone.localdate() + timedelta(days=90)
        self._style_fields()

    def clean_start_date(self):
        start_date = self.cleaned_data["start_date"]
        is_new = self.instance.pk is None
        if start_date and is_new and start_date < timezone.localdate():
            raise ValidationError("Нельзя оформить аренду с прошедшей даты.")
        return start_date

    def clean(self):
        cleaned = super().clean()
        plot = cleaned.get("plot")
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "Дата окончания не может быть раньше даты начала.")
            return cleaned
        if plot and start_date and end_date and self._period_is_busy(plot, start_date, end_date):
            raise ValidationError(
                "На выбранные даты участок уже арендован. Выберите другой участок или период."
            )
        return cleaned

    def _period_is_busy(self, plot, start_date, end_date):
        """Check active leases of the plot, excluding the edited record itself."""
        conflict = (
            Lease.objects.active()
            .filter(plot=plot, start_date__lte=end_date, end_date__gte=start_date)
            .exclude(pk=self.instance.pk)
        )
        return conflict.exists()


class CancelForm(forms.Form):
    """Empty POST form used to confirm cancellation without a GET link."""

    confirm = forms.BooleanField(
        required=True,
        label="Подтверждаю отмену",
        initial=True,
        widget=forms.CheckboxInput,
    )
