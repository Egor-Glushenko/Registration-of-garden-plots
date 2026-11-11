"""Validators shared by the registry models and forms (PR9, PR11)."""
import re

from django.core.exceptions import ValidationError

# Plot numbers look like "15", "16-Б", "104-A".
PLOT_NUMBER_PATTERN = re.compile(r"^\d{1,3}(?:-[А-ЯЁA-Z])?$", re.IGNORECASE)
# Local and international phone numbers with optional separators.
PHONE_PATTERN = re.compile(r"^\+?[\d\s()\-]{7,20}$")


def validate_plot_number(value):
    """Reject plot numbers that do not match the registry convention."""
    if not PLOT_NUMBER_PATTERN.match(str(value).strip()):
        raise ValidationError(
            "Номер участка должен состоять из числа (1–3 цифры) "
            "и, при необходимости, буквы: например 15 или 16-Б.",
            code="invalid_plot_number",
        )


def validate_phone(value):
    """Reject phone numbers that contain letters or are too short."""
    if not PHONE_PATTERN.match(str(value).strip()):
        raise ValidationError(
            "Телефон должен содержать 7–20 цифр и может включать +, пробелы, "
            "скобки и дефисы.",
            code="invalid_phone",
        )
