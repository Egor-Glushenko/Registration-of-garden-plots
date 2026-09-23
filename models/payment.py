"""
Модель платежа.
"""
from datetime import date
from .base import BaseEntity, log_action


class Payment(BaseEntity):
    """
    Платёж владельца.

    Атрибуты:
        owner_id (int): ID владельца
        amount (float): Сумма
        description (str): Описание
        payment_date (str): Дата (ISO)
    """

    def __init__(self, owner_id: int, amount: float, description: str):
        super().__init__()
        if amount <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        if not owner_id:
            raise ValueError("ID владельца обязателен")
        self.owner_id = owner_id
        self.amount = amount
        self.payment_date = date.today().isoformat()
        self.description = description or "Без описания"

    @log_action
    def update(self, amount: float = None, description: str = None):
        """Обновляет данные платежа."""
        if amount is not None and amount > 0:
            self.amount = amount
        if description:
            self.description = description

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'amount': self.amount,
            'payment_date': self.payment_date,
            'description': self.description,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls.__new__(cls)
        obj.id = data['id']
        obj.owner_id = data['owner_id']
        obj.amount = data['amount']
        obj.payment_date = data['payment_date']
        obj.description = data['description']
        obj.created_at = data.get('created_at')
        return obj

    def __repr__(self):
        return (f"[{self.id}] owner_id={self.owner_id}: {self.amount} руб. "
                f"({self.payment_date}) — {self.description}")

    def __str__(self):
        return self.__repr__()