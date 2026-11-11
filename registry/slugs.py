"""Slug helpers for the registry (PR9, subsection 5.5)."""
from django.utils.text import slugify

# Cyrillic letters transliterated for readable ASCII addresses.
TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def build_plot_slug(plot_number):
    """Turn ``15-А`` into ``15-a`` so the card address stays ASCII."""
    text = str(plot_number or "").strip().lower()
    transliterated = "".join(TRANSLIT.get(char, char) for char in text)
    return slugify(transliterated) or "plot"
