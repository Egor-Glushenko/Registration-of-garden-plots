"""
Меню для работы с системой учёта.
"""
import sys
from services import Manager
from models import VALID_STATUSES, STATUS_LABELS


class CLI:
    def __init__(self):
        self.manager = Manager()

    # ─────────── Вспомогательные ───────────
    def _input_int(self, prompt: str):
        while True:
            raw = input(prompt).strip()
            if raw == "":
                return None
            try:
                return int(raw)
            except ValueError:
                print("  Введите число.")

    def _input_float(self, prompt: str):
        while True:
            raw = input(prompt).strip()
            if raw == "":
                return None
            try:
                return float(raw)
            except ValueError:
                print("  Введите число.")

    def _input_status(self):
        print("  Доступные статусы:")
        for key, label in STATUS_LABELS.items():
            print(f"    {key} — {label}")
        while True:
            raw = input("  Статус (Enter = без изменений): ").strip()
            if raw == "":
                return None
            if raw in VALID_STATUSES:
                return raw
            print("  Неверный статус.")

    # ─────────── Меню владельцев ───────────
    def menu_owners(self):
        while True:
            print("\n─── Владельцы ───")
            print("1. Список")
            print("2. Добавить")
            print("3. Редактировать")
            print("4. Удалить")
            print("0. Назад")
            choice = input("> ").strip()

            if choice == "1":
                if not self.manager.owners:
                    print("  Владельцев нет.")
                for o in self.manager.owners:
                    print(f"  {o}")

            elif choice == "2":
                full_name = input("  ФИО: ").strip()
                phone = input("  Телефон: ").strip()
                email = input("  Email (необязательно): ").strip() or None
                if not full_name or not phone:
                    print("  ФИО и телефон обязательны.")
                    continue
                try:
                    oid = self.manager.add_owner(full_name, phone, email)
                    print(f"  ✅ Владелец добавлен, ID: {oid}")
                except ValueError as e:
                    print(f"  ❌ Ошибка: {e}")

            elif choice == "3":
                for o in self.manager.owners:
                    print(f"  {o}")
                oid = self._input_int("  ID владельца: ")
                if oid is None:
                    continue
                owner = self.manager.find_owner(oid)
                if not owner:
                    print("  ❌ Не найден.")
                    continue
                full_name = input(f"  ФИО (Enter = {owner.full_name}): ").strip() or None
                phone = input(f"  Телефон (Enter = {owner.phone}): ").strip() or None
                email = input(f"  Email (Enter = {owner.email or ''}): ").strip()
                email = email if email != "" else None
                if self.manager.edit_owner(oid, full_name=full_name, phone=phone, email=email):
                    print("  ✅ Обновлено.")

            elif choice == "4":
                for o in self.manager.owners:
                    print(f"  {o}")
                oid = self._input_int("  ID владельца: ")
                if oid is None:
                    continue
                if self.manager.delete_owner(oid):
                    print("  ✅ Удалён, участки освобождены.")

            elif choice == "0":
                break

    # ─────────── Меню участков ───────────
    def menu_plots(self):
        while True:
            print("\n─── Участки ───")
            print("1. Все участки")
            print("2. По статусу")
            print("3. С задолженностью")
            print("4. Добавить")
            print("5. Редактировать")
            print("6. Удалить")
            print("0. Назад")
            choice = input("> ").strip()

            if choice == "1":
                self._print_plots(self.manager.plots)

            elif choice == "2":
                status = self._input_status()
                if status:
                    self._print_plots(self.manager.list_plots(status=status))

            elif choice == "3":
                self._print_plots(self.manager.list_plots(has_debt=True))

            elif choice == "4":
                plot_number = input("  Номер: ").strip()
                area = self._input_float("  Площадь (кв.м): ") or 0.0
                status = self._input_status() or "free"
                oid = self._input_int("  ID владельца (Enter = без): ")
                debt = self._input_float("  Долг (Enter = 0): ") or 0.0
                try:
                    pid = self.manager.add_plot(plot_number, area, status, oid, debt)
                    print(f"  ✅ Участок добавлен, ID: {pid}")
                except ValueError as e:
                    print(f"  ❌ Ошибка: {e}")

            elif choice == "5":
                self._print_plots(self.manager.plots)
                pid = self._input_int("  ID участка: ")
                if pid is None:
                    continue
                plot = self.manager.find_plot(pid)
                if not plot:
                    print("  ❌ Не найден.")
                    continue
                plot_number = input(f"  Номер (Enter = {plot.plot_number}): ").strip() or None
                area = self._input_float(f"  Площадь (Enter = {plot.area_sqm}): ")
                status = self._input_status()
                oid = self._input_int("  ID владельца (Enter = без изменений, 0 = убрать): ")
                if oid == 0:
                    oid = -1
                debt = self._input_float(f"  Долг (Enter = {plot.debt}): ")
                try:
                    if self.manager.edit_plot(pid, plot_number=plot_number,
                                              area_sqm=area, status=status,
                                              owner_id=oid, debt=debt):
                        print("  ✅ Обновлено.")
                except ValueError as e:
                    print(f"  ❌ Ошибка: {e}")

            elif choice == "6":
                self._print_plots(self.manager.plots)
                pid = self._input_int("  ID участка: ")
                if pid is None:
                    continue
                if self.manager.delete_plot(pid):
                    print("  ✅ Удалён.")

            elif choice == "0":
                break

    def _print_plots(self, plots):
        if not plots:
            print("  Участков нет.")
            return
        for p in plots:
            print(f"  {p}")

    # ─────────── Меню платежей ───────────
    def menu_payments(self):
        while True:
            print("\n─── Платежи ───")
            print("1. Все платежи")
            print("2. По владельцу")
            print("3. Добавить")
            print("4. Удалить")
            print("0. Назад")
            choice = input("> ").strip()

            if choice == "1":
                for p in self.manager.payments:
                    print(f"  {p}")

            elif choice == "2":
                for o in self.manager.owners:
                    print(f"  {o}")
                oid = self._input_int("  ID владельца: ")
                if oid is None:
                    continue
                for p in self.manager.payments:
                    if p.owner_id == oid:
                        print(f"  {p}")

            elif choice == "3":
                for o in self.manager.owners:
                    print(f"  {o}")
                oid = self._input_int("  ID владельца: ")
                amount = self._input_float("  Сумма: ")
                desc = input("  Описание: ").strip()
                if oid is None or amount is None:
                    print("  ID и сумма обязательны.")
                    continue
                try:
                    pid = self.manager.add_payment(oid, amount, desc)
                    print(f"  ✅ Платёж добавлен, ID: {pid}")
                except ValueError as e:
                    print(f"  ❌ Ошибка: {e}")

            elif choice == "4":
                for p in self.manager.payments:
                    print(f"  {p}")
                pid = self._input_int("  ID платежа: ")
                if pid is None:
                    continue
                if self.manager.delete_payment(pid):
                    print("  ✅ Удалён.")

            elif choice == "0":
                break

    # ─────────── Главное меню ───────────
    def run(self):
        while True:
            print("\n" + "═" * 50)
            print("  СИСТЕМА УЧЁТА САДОВЫХ УЧАСТКОВ")
            print("═" * 50)
            print("1. Владельцы")
            print("2. Участки")
            print("3. Платежи")
            print("4. Сохранить отчёт в файл")
            print("5. Показать файлы данных")
            print("6. Загрузить демо-данные")
            print("0. Выход")
            choice = input("> ").strip()

            if choice == "1":
                self.menu_owners()
            elif choice == "2":
                self.menu_plots()
            elif choice == "3":
                self.menu_payments()
            elif choice == "4":
                self.manager.save_report()
                print("  ✅ Отчёт сохранён в data/report.txt")
            elif choice == "5":
                files = self.manager.storage.list_files()
                print(f"  Файлы: {', '.join(files) if files else 'пусто'}")
            elif choice == "6":
                print(f"  {self.manager.load_demo_data()}")
            elif choice == "0":
                self.manager.save_all()
                print("  💾 Данные сохранены. До встречи!")
                sys.exit()
            else:
                print("  ❌ Неверный выбор.")