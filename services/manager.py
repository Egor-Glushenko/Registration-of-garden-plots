"""
Менеджер данных: связывает модели и хранилище.
"""
from typing import List, Optional
from models import Owner, Plot, Payment, VALID_STATUSES, STATUS_LABELS
from storage import FileStorage


class Manager:
    """
    Менеджер учёта дачных участков.

    Управляет владельцами, участками и платежами.
    Автоматически сохраняет данные в файлы.
    """

    def __init__(self, storage: FileStorage = None, auto_save: bool = True):
        self.storage = storage or FileStorage()
        self.auto_save = auto_save

        self.owners: List[Owner] = []
        self.plots: List[Plot] = []
        self.payments: List[Payment] = []

        self._load_all()

    # ─────────── Загрузка / Сохранение ───────────
    def _load_all(self):
        """Загружает все данные из файлов."""
        self.owners = [Owner.from_dict(d) for d in self.storage.load('owners')]
        self.plots = [Plot.from_dict(d) for d in self.storage.load('plots')]
        self.payments = [Payment.from_dict(d) for d in self.storage.load('payments')]

        # Восстанавливаем счётчики ID
        Owner._counter = max([o.id for o in self.owners], default=0)
        Plot._counter = max([p.id for p in self.plots], default=0)
        Payment._counter = max([p.id for p in self.payments], default=0)

    def save_all(self):
        """Сохраняет все данные в файлы."""
        self.storage.save('owners', [o.to_dict() for o in self.owners])
        self.storage.save('plots', [p.to_dict() for p in self.plots])
        self.storage.save('payments', [p.to_dict() for p in self.payments])

    def _auto_save(self):
        """Автосохранение после изменений."""
        if self.auto_save:
            self.save_all()

    # ─────────── Поиск ───────────
    def find_owner(self, owner_id: int) -> Optional[Owner]:
        return next((o for o in self.owners if o.id == owner_id), None)

    def find_plot(self, plot_id: int) -> Optional[Plot]:
        return next((p for p in self.plots if p.id == plot_id), None)

    def find_payment(self, payment_id: int) -> Optional[Payment]:
        return next((p for p in self.payments if p.id == payment_id), None)

    # ─────────── CRUD: Владельцы ───────────
    def add_owner(self, full_name: str, phone: str, email: str = None) -> int:
        owner = Owner(full_name, phone, email)
        self.owners.append(owner)
        self._auto_save()
        return owner.id

    def edit_owner(self, owner_id: int, **kwargs) -> bool:
        owner = self.find_owner(owner_id)
        if not owner:
            return False
        owner.update(**kwargs)
        self._auto_save()
        return True

    def delete_owner(self, owner_id: int) -> bool:
        owner = self.find_owner(owner_id)
        if not owner:
            return False
        # Освобождаем участки
        for p in self.plots:
            if p.owner_id == owner_id:
                p.owner_id = None
                p.status = "free"
        self.owners.remove(owner)
        self._auto_save()
        return True

    # ─────────── CRUD: Участки ───────────
    def add_plot(self, plot_number: str, area_sqm: float,
                 status: str = "free", owner_id: int = None, debt: float = 0.0) -> int:
        if any(p.plot_number == plot_number for p in self.plots):
            raise ValueError(f"Участок с номером {plot_number} уже существует")
        plot = Plot(plot_number, area_sqm, status, owner_id, debt)
        self.plots.append(plot)
        self._auto_save()
        return plot.id

    def edit_plot(self, plot_id: int, **kwargs) -> bool:
        plot = self.find_plot(plot_id)
        if not plot:
            return False
        plot.update(**kwargs)
        self._auto_save()
        return True

    def delete_plot(self, plot_id: int) -> bool:
        plot = self.find_plot(plot_id)
        if not plot:
            return False
        self.plots.remove(plot)
        self._auto_save()
        return True

    def list_plots(self, status: str = None, has_debt: bool = False) -> List[Plot]:
        result = self.plots
        if status:
            result = [p for p in result if p.status == status]
        if has_debt:
            result = [p for p in result if p.debt > 0]
        return result

    # ─────────── CRUD: Платежи ───────────
    def add_payment(self, owner_id: int, amount: float, description: str) -> int:
        if not self.find_owner(owner_id):
            raise ValueError("Владелец не найден")
        payment = Payment(owner_id, amount, description)
        self.payments.append(payment)
        self._recalculate_debt(owner_id)
        self._auto_save()
        return payment.id

    def delete_payment(self, payment_id: int) -> bool:
        payment = self.find_payment(payment_id)
        if not payment:
            return False
        owner_id = payment.owner_id
        self.payments.remove(payment)
        self._recalculate_debt(owner_id)
        self._auto_save()
        return True

    def _recalculate_debt(self, owner_id: int):
        """Уменьшает долг участков владельца на сумму его платежей."""
        total_paid = sum(p.amount for p in self.payments if p.owner_id == owner_id)
        for plot in self.plots:
            if plot.owner_id == owner_id and plot.debt > 0:
                plot.debt = max(0, plot.debt - total_paid)
                break

    # ─────────── Отчёты ───────────
    def generate_report(self) -> List[str]:
        """Формирует текстовый отчёт по всем данным."""
        lines = []
        lines.append(f"Владельцев: {len(self.owners)}")
        lines.append(f"Участков: {len(self.plots)}")
        lines.append(f"Платежей: {len(self.payments)}")
        lines.append("")
        lines.append("--- ВЛАДЕЛЬЦЫ ---")
        for o in self.owners:
            lines.append(str(o))
        lines.append("")
        lines.append("--- УЧАСТКИ ---")
        for p in self.plots:
            lines.append(str(p))
        lines.append("")
        lines.append("--- ПЛАТЕЖИ ---")
        for p in self.payments:
            lines.append(str(p))
        return lines

    def save_report(self, filename: str = "report"):
        """Сохраняет текстовый отчёт в файл."""
        lines = self.generate_report()
        self.storage.save_text_report(filename, lines)

    # ─────────── Демо-данные ───────────
    def load_demo_data(self):
        """Загружает демонстрационные данные."""
        self.owners.clear()
        self.plots.clear()
        self.payments.clear()
        Owner._counter = 0
        Plot._counter = 0
        Payment._counter = 0

        oid1 = self.add_owner("Иванов Иван Иванович", "+79991234567", "ivanov@example.com")
        oid2 = self.add_owner("Петров Пётр Петрович", "+79997654321")

        self.add_plot("15А", 6.5, "occupied", owner_id=oid1, debt=3000.0)
        self.add_plot("16Б", 8.0, "free")
        self.add_plot("22В", 10.0, "leased", owner_id=oid2, debt=1500.0)
        self.add_plot("33Г", 4.5, "disputed")

        self.add_payment(oid1, 500.0, "Членский взнос 2024")
        self.add_payment(oid2, 1000.0, "Целевой взнос на дорогу")

        self._auto_save()
        return "Демо-данные загружены."