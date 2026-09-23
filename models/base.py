"""
Базовые классы и декораторы для всех сущностей.
"""
import json
from datetime import datetime
from functools import wraps


def log_action(func):
    """
    Декоратор для логирования вызовов методов.
    Записывает в консоль, какой метод был вызван.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"  [LOG] Вызов: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper


def validate_positive(func):
    """
    Декоратор для проверки, что числовые аргументы положительные.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, (int, float)) and arg < 0:
                raise ValueError(f"Значение не может быть отрицательным: {arg}")
        return func(self, *args, **kwargs)
    return wrapper


class BaseEntity:
    """
    Базовый класс для всех сущностей (Владелец, Участок, Платёж).
    Содержит общие атрибуты и методы.
    """
    _counter = 0  # Общий счётчик для всех наследников (переопределяется)

    def __init__(self):
        type(self)._counter += 1
        self.id = type(self)._counter
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Преобразует объект в словарь для сериализации."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт объект из словаря."""
        obj = cls.__new__(cls)
        obj.__dict__.update(data)
        return obj

    def __repr__(self):
        return f"<{type(self).__name__} id={self.id}>"