"""
Модуль для сохранения и загрузки данных в JSON.
Использует контекстные менеджеры.
"""
import json
import os
from pathlib import Path
from typing import List


class FileStorage:
    """
    Хранилище данных в JSON-файлах.

    Атрибуты:
        data_dir (Path): Директория для данных
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def _get_path(self, name: str) -> Path:
        """Возвращает путь к файлу данных."""
        return self.data_dir / f"{name}.json"

    def save(self, name: str, data: list) -> None:
        """
        Сохраняет список словарей в JSON.

        Args:
            name: Имя файла (без .json)
            data: Список словарей
        """
        path = self._get_path(name)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise IOError(f"Не удалось сохранить {name}: {e}")

    def load(self, name: str) -> list:
        """
        Загружает JSON-файл. Если файла нет — возвращает пустой список.

        Args:
            name: Имя файла (без .json)
        """
        path = self._get_path(name)
        if not path.exists():
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"  [WARN] Не удалось загрузить {name}: {e}")
            return []

    def save_text_report(self, name: str, lines: List[str]) -> None:
        """
        Сохраняет текстовый отчёт (построчный).

        Args:
            name: Имя файла (без .txt)
            lines: Список строк
        """
        path = self.data_dir / f"{name}.txt"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"Отчёт сгенерирован: {__import__('datetime').datetime.now()}\n")
                f.write("=" * 60 + "\n\n")
                for line in lines:
                    f.write(line + "\n")
        except OSError as e:
            raise IOError(f"Не удалось сохранить отчёт: {e}")

    def list_files(self) -> List[str]:
        """Возвращает список файлов в директории данных."""
        return [f.name for f in self.data_dir.iterdir() if f.is_file()]