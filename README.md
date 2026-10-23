# Садовый реестр

Строгое веб-приложение для учёта садовых участков, владельцев и платежей. Проект развивает исходную консольную систему в рамках практических работ PR5–PR7: Django, шаблоны и статические файлы, реляционная база данных и SQL-запросы.

## Возможности

- главная страница со сводными показателями;
- реестр участков с поиском по номеру или владельцу и фильтром по статусу;
- карточка участка с данными владельца;
- списки владельцев и платежей;
- статистика по статусам участков и задолженности;
- SQLite для локальной работы и выполнения PR7;
- PostgreSQL через `DATABASE_URL` для публикации приложения;
- импорт записей из JSON с демонстрационным набором данных, если локальные JSON-файлы отсутствуют.

## Страницы

| Адрес | Содержание |
| --- | --- |
| `/` | Сводка и переходы по разделам |
| `/registry/plots/` | Участки, поиск и фильтрация |
| `/registry/plots/<id>/` | Карточка участка и сведения о владельце |
| `/registry/owners/` | Владельцы, число участков и долг |
| `/registry/payments/` | История платежей |
| `/registry/statistics/` | Агрегаты и группировка по статусам |
| `/admin/` | Стандартная панель Django |

## Структура данных

| Таблица | Основные поля | Связи |
| --- | --- | --- |
| `owners` | `id`, `full_name`, `phone`, `email`, `created_at` | Владелец может иметь несколько участков и платежей |
| `plots` | `id`, `plot_number`, `area_sqm`, `status`, `owner_id`, `debt`, `created_at` | `owner_id → owners.id`; владелец необязателен |
| `payments` | `id`, `owner_id`, `amount`, `payment_date`, `description`, `created_at` | `owner_id → owners.id` |

SQLite-схема для задания находится в `sql/schema.sql`; схема PostgreSQL — в `sql/schema_postgres.sql`. Оба варианта используют первичные и внешние ключи, ограничения целостности и индексы. Идемпотентный импорт JSON реализован в `db/import_json.py`. Файл `sql/queries.sql` содержит примеры выборок, фильтрации, `JOIN`, агрегатных функций, `GROUP BY`, `HAVING`, параметризации и пагинации.

Представления выполняют параметризованные SQL-запросы через `registry/database.py` и передают строки в Django-шаблоны. Django ORM для таблиц предметной области не используется. Шаблоны наследуют `templates/base.html`, навигация вынесена в include, оформление хранится в `static/css/site.css`.

## Локальный запуск

Требуется Python 3.10 или новее.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py setup_registry
python manage.py runserver
```

Откройте <http://127.0.0.1:8000/>. При отсутствии переменной `DATABASE_URL` Django создаёт SQLite-базу в `data/garden.sqlite3`. Команда `setup_registry` создаёт SQL-схему и загружает локальные `data/owners.json`, `data/plots.json` и `data/payments.json`, если они есть; иначе используются обезличенные файлы в `fixtures/`.

### Конфигурация

| Переменная | Назначение |
| --- | --- |
| `DATABASE_URL` | Необязательный адрес SQLite или PostgreSQL; без него используется SQLite |
| `DJANGO_SECRET_KEY` | Секрет Django; задайте отдельное случайное значение для публикации |
| `DJANGO_DEBUG` | Включает режим разработки только при значении `1` |
| `DJANGO_ALLOWED_HOSTS` | Список допустимых хостов через запятую |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Доверенные HTTPS-адреса через запятую, если они необходимы |

Не сохраняйте строку подключения, пароль или `DJANGO_SECRET_KEY` в исходниках, README и Git. Локальные файлы `data/*.json`, `data/*.txt` и базы исключены из Git: исходные записи содержат личные данные.

## Публикация

Для Django-проекта подходит **Render Web Service**: приложение выполняет серверный Python-код и работает с базой данных. GitHub Pages размещает статические сайты и не запускает Django-сервер. У Render есть готовый процесс развёртывания Django и подключение PostgreSQL; у бесплатных веб-сервисов возможна остановка после периода без запросов. См. [руководство Render по Django](https://render.com/docs/deploy-django), [типы сервисов Render](https://render.com/docs/your-first-deploy) и [возможности GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

### Развёртывание на Render

1. Отправьте проект в GitHub и подключите репозиторий в Render: **New → Blueprint** (файл `render.yaml`) или **New → Web Service**.
2. Задайте переменную `DATABASE_URL` в настройках сервиса. Для PostgreSQL вставьте строку подключения к Neon или Render PostgreSQL в поле переменной окружения. Не добавляйте её в репозиторий.
3. Проверьте переменные `DJANGO_SECRET_KEY` и `DJANGO_ALLOWED_HOSTS`. Для собственного домена добавьте HTTPS-адрес в `DJANGO_CSRF_TRUSTED_ORIGINS`.
4. Запустите развёртывание. Команда старта применит служебные миграции Django, создаст SQL-схему реестра, загрузит обезличенные примеры и запустит Gunicorn.
5. Откройте выданный адрес `*.onrender.com` и проверьте разделы приложения.

Файл `render.yaml` настроен на использование уже имеющегося `DATABASE_URL`, поэтому для Blueprint-публикации Neon можно указать как переменную `DATABASE_URL` в Render. Веб-сервис на Render использует PostgreSQL-схему; локальная SQLite-схема остаётся доступной для выполнения PR7. Не храните единственную копию важных данных на файловой системе веб-сервиса.

## Контрольные команды

```powershell
python manage.py check
python manage.py migrate
python manage.py setup_registry
python manage.py runserver
```

Исходное консольное приложение `python main.py` и классы предметной области сохранены как предыдущий этап проекта. Новая веб-версия запускается через `manage.py`.
