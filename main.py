"""
Система учёта дачных участков.
Точка входа.
"""
from cli import CLI


def main():
    try:
        app = CLI()
        app.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем. Данные сохранены.")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main()