"""
Модель владельца участка.
"""
from .base import BaseEntity, log_action


class Owner(BaseEntity):
    """
    Владелец дачного участка.

    Атрибуты:
        full_name (str): ФИО владельца
        phone (str): Телефон
        email (str | None): Email (необязательно)
    """

    def __init__(self, full_name: str, phone: str, email: str = None):
        super().__init__()
        if not full_name or not phone:
            raise ValueError("ФИО и телефон обязательны")
        self.full_name = full_name
        self.phone = phone
        self.email = email

    @log_action
    def update(self, full_name: str = None, phone: str = None, email: str = None):
        """Обновляет данные владельца."""
        if full_name:
            self.full_name = full_name
        if phone:
            self.phone = phone
        if email is not None:
            self.email = email

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls.__new__(cls)
        obj.id = data['id']
        obj.full_name = data['full_name']
        obj.phone = data['phone']
        obj.email = data.get('email')
        obj.created_at = data.get('created_at')
        return obj

    def __repr__(self):
        email = f", email: {self.email}" if self.email else ""
        return f"[{self.id}] {self.full_name}, тел: {self.phone}{email}"

    def __str__(self):
        return self.__repr__()