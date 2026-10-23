from django import template

register = template.Library()

STATUS_LABELS = {
    "free": "Свободен",
    "occupied": "Занят",
    "leased": "Аренда",
    "disputed": "Спорный",
}


@register.filter
def status_label(value):
    return STATUS_LABELS.get(value, value)
