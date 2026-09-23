"""
Модель дачного участка.
"""
from .base import BaseEntity, log_action, validate_positive


VALID_STATUSES = {"free", "occupied", "leased", "disputed"}
STATUS_LABELS = {
    "free": "свободен",
    "occupied": "занят",
    "leased": "аренда",
    "disputed": "спорный",
}


class Plot(BaseEntity):
    """
    Дачный участок.

    Атрибуты:
        plot_number (str): Номер участка
        area_sqm (float): Площадь в кв.м
        status (str): Статус (free/occupied/leased/disputed)
        owner_id (int | None): ID владельца
        debt (float): Задолженность
    """

    def __init__(self, plot_number: str, area_sqm: float,
                 status: str = "free", owner_id: int = None, debt: float = 0.0):
        super().__init__()
        if not plot_number:
            raise ValueError("Номер участка обязателен")
        if status not in VALID_STATUSES:
            raise ValueError(f"Неверный статус: {status}")
        if area_sqm < 0:
            raise ValueError("Площадь не может быть отрицательной")
        if debt < 0:
            raise ValueError("Долг не может быть отрицательным")

        self.plot_number = plot_number
        self.area_sqm = area_sqm
        self.status = status
        self.owner_id = owner_id
        self.debt = debt

    @log_action
    @validate_positive
    def update(self, plot_number: str = None, area_sqm: float = None,
               status: str = None, owner_id: int = None, debt: float = None):
        """Обновляет данные участка."""
        if plot_number:
            self.plot_number = plot_number
        if area_sqm is not None:
            self.area_sqm = area_sqm
        if status:
            if status not in VALID_STATUSES:
                raise ValueError(f"Неверный статус: {status}")
            self.status = status
        if owner_id is not None:
            self.owner_id = owner_id if owner_id > 0 else None
        if debt is not None:
            self.debt = debt

    @property
    def status_label(self) -> str:
        """Человекочитаемый статус."""
        return STATUS_LABELS.get(self.status, self.status)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'plot_number': self.plot_number,
            'area_sqm': self.area_sqm,
            'status': self.status,
            'owner_id': self.owner_id,
            'debt': self.debt,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls.__new__(cls)
        obj.id = data['id']
        obj.plot_number = data['plot_number']
        obj.area_sqm = data['area_sqm']
        obj.status = data['status']
        obj.owner_id = data.get('owner_id')
        obj.debt = data.get('debt', 0.0)
        obj.created_at = data.get('created_at')
        return obj

    def __repr__(self):
        return (f"[{self.id}] №{self.plot_number}, {self.area_sqm} кв.м, "
                f"статус: {self.status_label}, долг: {self.debt} руб.")

    def __str__(self):
        return self.__repr__()