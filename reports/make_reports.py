"""Generate the PR9, PR10 and PR11 reports as DOCX files.

Run with the bundled Python that ships python-docx:
    python make_reports.py
"""
import pathlib

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = pathlib.Path(r"C:\Users\samsu\Desktop\Registration-of-garden-plots-main")
SHOTS = ROOT / "reports" / "screenshots"
OUT = ROOT / "reports"

STUDENT = "Глущенко Егор Игоревич"
GROUP = "ЭФБО-09-24"
VARIANT = "6 (по списку группы)"
TEACHER = "Ящун Татьяна Викторовна"
DISCIPLINE = "Технологии разработки приложений на базе фреймворков"
INSTITUTE = "Институт перспективных технологий и индустриального программирования"
DEPARTMENT = "Кафедра Индустриального программирования"
PROJECT = "«Садовый реестр»"

BODY_FONT = "Times New Roman"
CODE_FONT = "Consolas"


# --------------------------------------------------------------------------- #
# Low-level helpers
# --------------------------------------------------------------------------- #
def _shade(cell, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(shd)


def _cell_text(cell, text, bold=False, size=11, font=BODY_FONT, align=None):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.LEFT
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = font


def _page_number_footer(section):
    paragraph = section.footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.font.size = Pt(11)
    run.font.name = BODY_FONT
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)


def new_document():
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)

    normal = document.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(14)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.first_line_indent = Cm(1.25)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name, size in (("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 13)):
        style = document.styles[name]
        style.font.name = BODY_FONT
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.first_line_indent = Cm(0)
        style.paragraph_format.keep_with_next = True

    _page_number_footer(section)
    return document


def h1(document, text):
    return document.add_heading(text, level=1)


def h2(document, text):
    return document.add_heading(text, level=2)


def p(document, text, first_indent=True, bold=False, italic=False, size=14, align=None):
    paragraph = document.add_paragraph()
    if not first_indent:
        paragraph.paragraph_format.first_line_indent = Cm(0)
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    return paragraph


def bullets(document, items):
    for item in items:
        paragraph = document.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.line_spacing = 1.3
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(item)
        run.font.size = Pt(14)


def code(document, text, caption=None):
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Cm(16)
    _shade(cell, "F5F5F2")
    cell.text = ""
    lines = text.strip("\n").split("\n")
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for index, line in enumerate(lines):
        run = paragraph.add_run(line)
        run.font.name = CODE_FONT
        run.font.size = Pt(9)
        if index < len(lines) - 1:
            run.add_break()
    if caption:
        note = document.add_paragraph()
        note.paragraph_format.first_line_indent = Cm(0)
        note.paragraph_format.space_after = Pt(8)
        run = note.add_run(caption)
        run.font.size = Pt(11)
        run.italic = True
    else:
        document.add_paragraph().paragraph_format.space_after = Pt(6)


def table(document, headers, rows, widths=None, font_size=10, caption=None, header_fill="E8EDE4"):
    table_obj = document.add_table(rows=1, cols=len(headers))
    table_obj.style = "Table Grid"
    table_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_cells = table_obj.rows[0].cells
    for index, header in enumerate(headers):
        _cell_text(header_cells[index], header, bold=True, size=font_size)
        _shade(header_cells[index], header_fill)
    # Repeat the header row on every page and keep rows unsplit.
    header_row = table_obj.rows[0]
    tr_pr = header_row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)
    for row in rows:
        new_row = table_obj.add_row()
        cant_split = OxmlElement("w:cantSplit")
        new_row._tr.get_or_add_trPr().append(cant_split)
        cells = new_row.cells
        for index, value in enumerate(row):
            _cell_text(cells[index], str(value), size=font_size)
    if widths:
        for row in table_obj.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)
    if caption:
        note = document.add_paragraph()
        note.paragraph_format.first_line_indent = Cm(0)
        note.paragraph_format.space_before = Pt(4)
        note.paragraph_format.space_after = Pt(8)
        run = note.add_run(caption)
        run.font.size = Pt(11)
        run.italic = True
    else:
        document.add_paragraph().paragraph_format.space_after = Pt(4)
    return table_obj


FIGURES = {"count": 0, "prefix": ""}


def reset_figures(prefix):
    FIGURES["count"] = 0
    FIGURES["prefix"] = prefix


def figure(document, relative_path, caption):
    path = SHOTS / relative_path
    if not path.exists():
        p(document, f"[нет файла {relative_path}]", first_indent=False)
        return
    FIGURES["count"] += 1
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run()
    run.add_picture(str(path), width=Cm(16))

    note = document.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    note.paragraph_format.first_line_indent = Cm(0)
    note.paragraph_format.space_after = Pt(10)
    text_run = note.add_run(f"Рисунок {FIGURES['prefix']}.{FIGURES['count']} – {caption}")
    text_run.font.size = Pt(11)
    text_run.italic = True


def title_page(document, work_number, topic, annotation):
    p(document, "МИНОБРНАУКИ РОССИИ", first_indent=False, bold=True, size=13,
      align=WD_ALIGN_PARAGRAPH.CENTER)
    p(document, INSTITUTE, first_indent=False, bold=True, size=13, align=WD_ALIGN_PARAGRAPH.CENTER)
    p(document, DEPARTMENT, first_indent=False, size=13, align=WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(3):
        p(document, "", first_indent=False)
    p(document, f"Дисциплина: {DISCIPLINE}", first_indent=False, size=14,
      align=WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(2):
        p(document, "", first_indent=False)
    p(document, f"ПРАКТИЧЕСКАЯ РАБОТА № {work_number}", first_indent=False, bold=True,
      size=18, align=WD_ALIGN_PARAGRAPH.CENTER)
    p(document, topic, first_indent=False, bold=True, size=15, align=WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(3):
        p(document, "", first_indent=False)
    rows = [
        ("Студент", STUDENT),
        ("Учебная группа", GROUP),
        ("Вариант", VARIANT),
        ("Преподаватель", TEACHER),
        ("Семестр", "5 семестр, 2026–2027 учебный год"),
        ("Проект", PROJECT),
    ]
    table_obj = document.add_table(rows=0, cols=2)
    table_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
    for label, value in rows:
        cells = table_obj.add_row().cells
        _cell_text(cells[0], label, bold=True, size=12)
        _cell_text(cells[1], value, size=12)
        cells[0].width = Cm(4.6)
        cells[1].width = Cm(10.4)
    for _ in range(5):
        p(document, "", first_indent=False)
    p(document, "Москва, 2026", first_indent=False, size=13, align=WD_ALIGN_PARAGRAPH.CENTER)
    document.add_page_break()
    p(document, annotation, first_indent=False, italic=True, size=12)
    p(document, "", first_indent=False)


def appendix(document, title, figures):
    document.add_page_break()
    h1(document, title)
    for relative_path, caption in figures:
        figure(document, relative_path, caption)


# --------------------------------------------------------------------------- #
# PR9
# --------------------------------------------------------------------------- #
def build_pr9():
    reset_figures("А")
    document = new_document()
    title_page(
        document, 9, "МОДЕЛИ DJANGO, СВЯЗИ И ОПЕРАЦИИ С БАЗОЙ ДАННЫХ ЧЕРЕЗ ORM",
        "Отчёт содержит описание моделей индивидуального проекта, миграций, "
        "переноса данных предыдущей практической работы, реализованных ORM-операций, "
        "результатов проверок и подтверждающие скриншоты.",
    )

    h1(document, "1. Общие сведения")
    table(document, ["Параметр", "Значение"], [
        ["Образовательная организация", INSTITUTE],
        ["Кафедра", DEPARTMENT],
        ["Дисциплина", DISCIPLINE],
        ["Номер практической работы", "9"],
        ["Тема", "Модели Django, связи и операции с базой данных через ORM"],
        ["Учебная группа", GROUP],
        ["ФИО студента", STUDENT],
        ["Вариант", VARIANT],
    ], widths=[6.0, 10.0], caption="Таблица 1 – Общие сведения о работе")

    h1(document, "2. Цель работы")
    p(document, "Цель работы — изучить принципы описания моделей Django и связей между ними, "
                "освоить создание и применение миграций, а также выполнение операций создания, "
                "чтения, изменения и удаления записей средствами Django ORM. Полученные знания "
                "применяются в индивидуальном сквозном проекте «Садовый реестр»: слой доступа к "
                "данным переводится с ручных SQL-запросов на Django ORM при сохранении "
                "работоспособности ранее реализованных страниц и пользовательских сценариев.")

    h1(document, "3. Выполненные материалы Яндекс Практикума")
    p(document, "В рамках практической работы изучен раздел 05 «База данных и Django ORM» "
                "курса «Бэкенд-разработка».")
    table(document, ["Раздел", "Выполненные темы", "Отметка"], [
        ["Раздел 05 «База данных и Django ORM»",
         "«Отношения между таблицами»: один к одному, многие к одному, JOIN, "
         "многие ко многим, изменение таблиц и ссылочная целостность", "Выполнено"],
        ["Раздел 05 «База данных и Django ORM»",
         "«Django ORM. Модели»: описание таблиц классами, связи между моделями, "
         "наследование от абстрактных моделей, миграции, Django shell, "
         "CRUD-операции, заполнение и выгрузка данных", "Выполнено"],
    ], widths=[4.4, 9.6, 2.0], caption="Таблица 2 – Материалы Яндекс Практикума")

    h1(document, "4. Доработка индивидуального проекта")
    h2(document, "4.1. Анализ базы данных, созданной в ПР7")
    p(document, "Предыдущий этап проекта использовал три таблицы, созданные вручную по "
                "схеме sql/schema.sql (SQLite) и sql/schema_postgres.sql (PostgreSQL): "
                "owners, plots и payments. Таблицы содержали первичные ключи INTEGER, внешние "
                "ключи owner_id, ограничения CHECK на положительную площадь, неотрицательный "
                "долг и допустимые статусы, а также индексы по внешним ключам. Доступ к данным "
                "выполнялся параметризованными SQL-запросами через django.db.connection, а "
                "импорт демонстрационного набора — командой setup_registry.")
    p(document, "Такой подход работоспособен, но имеет ограничения: структура базы не описана "
                "в коде приложения и меняется только вручную, запросы дублируются, типы полей "
                "проверяются слабо, а данные из базы возвращаются словарями, а не объектами. "
                "Поэтому в ПР9 принята стратегия перехода: новые таблицы registry_* описываются "
                "моделями, данные ПР7 переносятся отдельной миграцией, а слой ПР7 сохраняется в "
                "репозитории как предыдущая реализация предметной области.")

    h2(document, "4.2. Описанные модели и их поля")
    table(document, ["Модель", "Поля", "Особенности"], [
        ["Owner\n(владелец)",
         "full_name, phone, email, created_at, updated_at",
         "Абстрактная модель TimeStampedModel; валидатор телефона; индекс по ФИО"],
        ["Plot\n(участок)",
         "plot_number, slug, area_sqm, status, owner, debt, image, "
         "membership_fee, created_at, updated_at",
         "plot_number уникален и проверяется валидатором; status — TextChoices; "
         "membership_fee — GeneratedField (площадь × 12 ₽/м²); проверки площади и долга"],
        ["Payment\n(платёж)",
         "owner, amount, payment_date, description, status, created_at, updated_at",
         "amount проверяется валидатором; status — TextChoices; метод cancel()"],
        ["Lease\n(аренда участка)",
         "plot, owner, start_date, end_date, status, note, created_at, updated_at",
         "status — TextChoices; ограничение end_date ≥ start_date; метод cancel(); "
         "проверка пересечения периодов в clean()"],
    ], widths=[3.2, 6.4, 6.4], caption="Таблица 3 – Модели предметной области")

    h2(document, "4.3. Связи между моделями")
    p(document, "Связи реализованы через ForeignKey с явно заданными on_delete и related_name:")
    bullets(document, [
        "Plot.owner → Owner, on_delete=SET_NULL, related_name=\"plots\": при удалении "
        "владельца участок остаётся в реестре свободным от владельца.",
        "Payment.owner → Owner, on_delete=PROTECT, related_name=\"payments\": финансовую "
        "историю нельзя потерять при удалении владельца.",
        "Lease.plot → Plot, on_delete=CASCADE, related_name=\"leases\": арендные записи "
        "принадлежат участку.",
        "Lease.owner → Owner, on_delete=PROTECT, related_name=\"leases\": арендатор "
        "защищён от случайного удаления.",
        "Абстрактная модель TimeStampedModel добавляет всем сущностям поля created_at и "
        "updated_at и не создаёт отдельной таблицы.",
    ])

    h2(document, "4.4. Созданные и применённые миграции")
    code(document, """0001_initial.py                 модели, индексы, CHECK-ограничения
0002_transfer_legacy_sql_data.py  перенос данных ПР7
0003_lease_rent_amount.py         поле Lease.rent_amount (ПР10)
0004_fill_lease_rent.py           заполнение арендной платы (ПР10)""")
    p(document, "Миграция 0002 проверяет наличие таблиц ПР7 через introspection, читает строки "
                "и создаёт объекты моделей с сохранением идентификаторов и внешних ключей; "
                "timestamps и slug восстанавливаются из данных, для PostgreSQL дополнительно "
                "выполняется setval() для identity-последовательностей. На чистой базе шаг "
                "пропускается, поэтому миграция безопасна и для развёртывания на Render.")

    h2(document, "4.5. Перенос данных из базы ПР7")
    p(document, "Перенос проверялся на локальной базе: сначала командой legacy_sql_import "
                "создан слой ПР7 и загружен демонстрационный набор, затем применены миграции.")
    code(document, """> python manage.py legacy_sql_import
Слой ПР7 заполнен: owners=6, plots=14, payments=8

> python manage.py migrate
  Applying registry.0001_initial... OK
  Applying registry.0002_transfer_legacy_sql_data... OK

> python manage.py shell -c "..."
=== 1. Object counts (ORM) ===
owners: 6
plots: 15
payments: 9
leases: 6""",
         "Вывод команд переноса и подсчёта объектов (числа выросли после создания "
         "демонстрационных записей на этапах ПР10–ПР11)")

    h2(document, "4.6. Реализованные операции ORM")
    table(document, ["Операция", "Пример из проекта", "Где используется"], [
        ["Создание", "PlotForm.save() → Plot.objects.create(...)", "формы и админка"],
        ["Чтение списка", "Plot.objects.with_owner().of_status(status).search(q)",
         "registry/queries.py"],
        ["Получение одного объекта",
         "get_object_or_404(Plot..., slug=slug)", "карточка участка"],
        ["Фильтрация и исключение", "Plot.objects.free(), .exclude(status=\"free\")",
         "список и статистика"],
        ["Поиск по Q", "Q(plot_number__icontains) | Q(owner__full_name__icontains)",
         "поиск на страницах"],
        ["Агрегирование и группировка",
         "annotate(Count(\"plots\"), Sum(\"plots__debt\")), values().annotate()",
         "владельцы, статистика"],
        ["Обновление и удаление", "plot.save(update_fields=[...]), plot.delete()", "формы и админка"],
        ["Сортировка, срез, пагинация", "order_by(\"-debt\")[:5], Paginator(queryset, 10)",
         "списки и карточки"],
    ], widths=[3.4, 7.6, 5.0], caption="Таблица 4 – Операции ORM в проекте")

    h2(document, "4.7. Адаптированные представления и страницы")
    table(document, ["Адрес", "Содержание", "ORM-функция"], [
        ["/", "Сводка реестра", "queries.dashboard_stats()"],
        ["/registry/plots/", "Реестр участков: поиск, фильтр, сортировка, пагинация",
         "queries.plot_page()"],
        ["/registry/plots/<slug>/", "Карточка участка", "queries.plot_get()"],
        ["/registry/owners/, /registry/payments/", "Владельцы и история платежей",
         "queries.owner_page(), payment_page()"],
        ["/registry/leases/, /registry/statistics/", "Аренда и аналитика",
         "queries.lease_page(), statistics()"],
    ], widths=[5.0, 6.6, 4.4], caption="Таблица 5 – Страницы проекта после перехода на ORM")
    p(document, "Шаблоны переведены с обращений к словарям (plot.owner_name) на поля моделей "
                "(plot.owner.full_name), ссылки строятся через get_absolute_url() и "
                "{% url %}, добавлены блоки пагинации и сообщений. Файл README.md обновлён: "
                "описаны модели, слой запросов, порядок запуска и проверок.")

    h1(document, "5. Результат работы")
    bullets(document, [
        "описаны модели четырёх сущностей предметной области и их поля;",
        "настроены связи «многие к одному» с параметрами on_delete и related_name;",
        "созданы и применены миграции, структура базы управляется только ими;",
        "данные ПР7 перенесены без потери связей: идентификаторы и внешние ключи сохранены;",
        "операции с данными выполняются средствами ORM, SQL в представлениях отсутствует;",
        "страницы и пользовательские сценарии предыдущих работ работают без изменений.",
    ])

    h1(document, "6. Проверка")
    code(document, """> python manage.py check
System check identified no issues (0 silenced).

> python manage.py showmigrations registry
registry
 [X] 0001_initial
 [X] 0002_transfer_legacy_sql_data
 [X] 0003_lease_rent_amount
 [X] 0004_fill_lease_rent

> python -m pytest -q
133 passed

> python -m flake8 .
(замечаний нет)""", "Результаты проверок проекта")
    p(document, "Дополнительно операции проверены в Django shell: подсчёт объектов, "
                "filter(), select_related(), aggregate(), annotate(), get() с обработкой "
                "DoesNotExist и CRUD-операции с откатом транзакции.")
    code(document, """=== 3. Related fields through JOIN ===
23 | Волков Артём Денисович | 5200.00
19 | Морозова Анна Сергеевна | 4800.00
17 | Соколов Дмитрий Игоревич | 3400.00

=== 5. aggregate() ===
{'plots': 15, 'debt': Decimal('16750'), 'area': Decimal('792')}

=== 7. get() and DoesNotExist ===
plot: Участок № 14 | slug: 14 | fee: 9600.00
Plot.DoesNotExist: object not found (404 in the view)""", "Фрагмент вывода Django shell")

    h1(document, "7. Контрольная точка Git")
    table(document, ["Коммит", "Содержание"], [
        ["PR9: модели Django Owner, Plot, Payment, Lease и миграции",
         "модели, миграции 0001–0002, слой запросов queries.py, перевод представлений, "
         "тесты, README"],
    ], widths=[7.0, 9.0], caption="Таблица 6 – Коммит контрольной точки ПР9")
    p(document, "Рабочее дерево после коммита чистое, изменения отправлены в удалённый "
                "репозиторий GitHub проекта.")

    h1(document, "8. Вывод")
    p(document, "Переход на Django ORM выполнен без потери функциональности: структура базы "
                "описывается моделями и миграциями, данные ПР7 перенесены с сохранением связей, "
                "представления работают с объектами моделей, а повторяющиеся выборки собраны в "
                "слой queries.py. Проект получил типовой для Django слой доступа к данным и "
                "готов к дальнейшему развитию: настройке административной панели и форм.")

    appendix(document, "Приложение А. Скриншоты работы приложения", [
        ("pr9/01_overview.png", "Главная страница: сводные показатели реестра"),
        ("pr9/02_plots_list.png", "Реестр участков: поиск, фильтр, сортировка, пагинация"),
        ("pr9/03_plots_page2.png", "Вторая страница списка участков"),
        ("pr9/04_plot_detail.png", "Карточка участка, владелец и история аренды"),
        ("pr9/05_owners.png", "Реестр владельцев с агрегатами по участкам"),
        ("pr9/06_payments.png", "История платежей"),
        ("pr9/07_leases.png", "Реестр аренды участков"),
        ("pr9/08_statistics.png", "Страница статистики"),
        ("pr9/09_legacy_redirect.png", "Совместимый адрес ПР7 перенаправляет на карточку участка"),
    ])
    document.save(OUT / "PR9_Django_ORM_modeli_otchet.docx")
    print("saved PR9")


# --------------------------------------------------------------------------- #
# PR10
# --------------------------------------------------------------------------- #
def build_pr10():
    reset_figures("Б")
    document = new_document()
    title_page(
        document, 10, "АДМИНИСТРАТИВНАЯ ПАНЕЛЬ DJANGO И РАБОТА С ДАННЫМИ ЧЕРЕЗ ORM",
        "Отчёт содержит описание настроек административной панели, изменений моделей и "
        "миграций, проверенных ORM-запросов, анализа SQL с помощью Django Debug Toolbar, "
        "результатов проверок и подтверждающие скриншоты.",
    )

    h1(document, "1. Тема и цель работы")
    p(document, "Тема — административная панель Django и работа с данными через ORM.")
    p(document, "Цель работы — закрепить навыки работы с административной панелью Django и "
                "Django ORM: настроить управление моделями предметной области, освоить "
                "фильтрацию, сортировку, агрегирование и оптимизацию запросов, проверить "
                "SQL-запросы страниц и сохранить работоспособность ранее реализованной "
                "функциональности проекта «Садовый реестр».")

    h1(document, "2. Выполненные задания Яндекс Практикума")
    table(document, ["Тема", "Содержание", "Отметка"], [
        ["Административная панель Django", "регистрация моделей, ModelAdmin, список, "
         "фильтры, поиск, inline, действия", "Выполнено"],
        ["ORM-запросы", "QuerySet, filter(), exclude(), Q, F, сортировка, срезы",
         "Выполнено"],
        ["Связанные модели", "select_related(), prefetch_related(), поля связанных моделей",
         "Выполнено"],
        ["Агрегирование", "Count(), Sum(), Avg(), Min(), Max(), annotate(), aggregate()",
         "Выполнено"],
        ["Доработка проекта", "настройка админки, менеджеры, миграции, отладка запросов",
         "Выполнено"],
    ], widths=[4.6, 9.4, 2.0], caption="Таблица 1 – Выполненные задания практикума")

    h1(document, "3. Настройки административной панели")
    p(document, "Все модели проекта зарегистрированы в registry/admin.py. Заголовки панели "
                "переведены на русский язык, для каждой модели задан собственный класс "
                "ModelAdmin.")
    table(document, ["Модель", "Список (list_display)", "Поиск и фильтры", "Связанные записи"],
          [
              ["Владельцы", "ФИО, телефон, почта, участков, долг, дата",
               "поиск по ФИО, телефону, почте; фильтр по дате и статусу участков",
               "inline: участки, аренды, платежи"],
              ["Участки", "номер, статус, площадь, владелец, долг, взнос, число аренд, фото",
               "поиск по номеру, slug, владельцу; фильтр по статусу, владельцу, дате",
               "inline: аренда участка"],
              ["Платежи", "дата, владелец, сумма, назначение, состояние",
               "поиск по владельцу и назначению; фильтр по состоянию и дате",
               "autocomplete владельца"],
              ["Аренда", "участок, арендатор, период, дней, плата, статус",
               "поиск по участку и арендатору; фильтр по статусу и датам",
               "autocomplete участка и владельца"],
          ], widths=[2.6, 5.4, 4.8, 3.2], caption="Таблица 2 – Настройки ModelAdmin")
    p(document, "Дополнительно настроены list_editable (задолженность меняется прямо в "
                "списке), fieldsets, readonly_fields, date_hierarchy, list_per_page и "
                "list_select_related. Пользовательские действия описаны в таблице 3.")
    table(document, ["Действие", "Что делает", "Реализация"], [
        ["Освободить участки", "статус free, владелец снимается", "queryset.update()"],
        ["Перевести в спорные", "статус disputed", "queryset.update()"],
        ["Обнулить задолженность", "debt = 0", "queryset.update()"],
        ["Начислить пеню 5%", "debt = debt × 1.05 в базе", "update(debt=F(\"debt\") * 1.05)"],
        ["Отменить платежи", "статус cancelled, запись сохраняется", "queryset.update()"],
        ["Вернуть платежи", "статус posted", "queryset.update()"],
        ["Отменить аренды", "статус cancelled, участок освобождается", "queryset.update()"],
    ], widths=[4.2, 7.0, 4.8], caption="Таблица 3 – Действия административной панели")
    p(document, "Действия намеренно выполняются через QuerySet.update(): массовая операция "
                "не должна читать каждую запись в память. Проверка бизнес-правил выполняется "
                "в формах, моделях и представлениях, поэтому настройки админки не заменяют "
                "серверную валидацию.")

    h1(document, "4. Изменения моделей, миграций и менеджера QuerySet")
    p(document, "В рамках работы модель аренды дополнена полем rent_amount (арендная плата), "
                "так как стоимость договора требуется и в списке аренды, и в административной "
                "панели. Создана миграция схемы 0003_lease_rent_amount и миграция данных "
                "0004_fill_lease_rent, которая заполняет новое поле существующих записей "
                "значением членского взноса участка.")
    code(document, """# Добавление поля в модель (registry/models.py)
rent_amount = models.DecimalField(
    "Арендная плата, ₽",
    max_digits=10,
    decimal_places=2,
    default=Decimal("0.00"),
    validators=[MinValueValidator(Decimal("0.00"))],
)""")
    p(document, "Кроме того, в модели участка используется GeneratedField — вычисляемый "
                "столбец membership_fee (площадь × 12 ₽/м²), значение которого формирует сама "
                "база данных, а не приложение.")
    code(document, """membership_fee = models.GeneratedField(
    expression=F("area_sqm") * FEE_PER_SQM,
    output_field=models.DecimalField(max_digits=12, decimal_places=2),
    db_persist=True,
    verbose_name="Членский взнос, ₽/год",
)""")
    p(document, "Пользовательские менеджеры и QuerySet-методы вынесены в модели и "
                "используются представлениями и админкой:")
    table(document, ["Менеджер", "Методы", "Назначение"], [
        ["Plot.objects", "with_owner(), of_status(), search(), free(), with_counters()",
         "список участков, поиск, подсчёт связанных записей"],
        ["Owner.objects", "with_totals(), search()",
         "агрегаты по участкам и платежам, поиск владельца"],
        ["Lease.objects", "active(), for_plot(), overlapping(), with_related()",
         "правило занятости участка"],
        ["Payment.objects", "posted(), cancelled(), with_owner()",
         "финансовые итоги, история платежей"],
    ], widths=[3.8, 7.2, 5.0], caption="Таблица 4 – Менеджеры и QuerySet-методы")

    h1(document, "5. Проверенные ORM-запросы, фильтрация, сортировка и пагинация")
    p(document, "Список участков собирается функцией queries.plot_page(): фильтр по статусу, "
                "поиск по номеру и владельцу через Q, фильтр по минимальной площади, "
                "сортировка по выбранному полю и пагинация по 10 записей.")
    code(document, """def plot_page(status="", query="", ordering="number", owner=None,
              area_min=None, page=1, per_page=10):
    queryset = Plot.objects.with_owner().with_counters()
    queryset = queryset.of_status(status).search(query)
    if owner:
        queryset = queryset.filter(owner=owner)
    if area_min:
        queryset = queryset.filter(area_sqm__gte=area_min)
    queryset = queryset.order_by(*PLOT_ORDERINGS[ordering])
    return Paginator(queryset, per_page).get_page(page)""")
    p(document, "Список страницы выполняет два запроса: COUNT для пагинатора и SELECT с "
                "JOIN и GROUP BY, который сразу возвращает владельца и счётчики связанных "
                "записей. Это устраняет проблему N+1: в шаблоне не происходит обращений к "
                "базе для каждой строки.")
    code(document, """=== 3. Count by status (GROUP BY) ===
{'status': 'disputed', 'total': 2}
{'status': 'free', 'total': 3}
{'status': 'leased', 'total': 3}
{'status': 'occupied', 'total': 7}

=== 4. Aggregates ===
{'avg_area': Decimal('792'), 'max_area': Decimal('1100'),
 'min_area': Decimal('580'), 'debt': Decimal('16750')}""", "Вывод Django shell: группировка и агрегаты")
    p(document, "Страница статистики использует aggregate() для общих показателей и "
                "values().annotate() для распределения по статусам, а также список "
                "владельцев-должников, полученный через annotate() и order_by().")
    code(document, """=== 6. annotate() by related objects ===
Иванова Мария Петровна | plots: 2 | debt: 0
Петров Сергей Николаевич | plots: 2 | debt: 3350
Кузнецова Ольга Андреевна | plots: 3 | debt: 0""")

    h2(document, "5.1. Доступность участка с учётом статусов аренды")
    p(document, "Правило предметной области: участок блокируется только действующей арендой. "
                "Метод Lease.objects.active() фильтрует статус «действует», метод "
                "overlapping() проверяет пересечение периодов, а форма аренды исключает "
                "редактируемую запись из проверки. Отменённые и завершённые аренды не мешают "
                "оформить новый договор; при отмене аренды статус участка пересчитывается "
                "сервисом sync_plot_status().")
    code(document, """=== 6. Active leases rule ===
active leases: 3
cancelled leases: 2
plots blocked now: ['22-В', '17', '21-В']""", "Вывод Django shell: действующие аренды блокируют участки")

    h2(document, "5.2. Анализ SQL-запросов с помощью Django Debug Toolbar")
    p(document, "При DJANGO_DEBUG=1 подключается Django Debug Toolbar. На странице списка "
                "участков панель SQL показывает 6 запросов: COUNT для пагинатора, три "
                "COUNT для счётчиков контекстного процессора, SELECT с JOIN и GROUP BY для "
                "списка и служебные запросы. Время выполнения — около 1,21 мс, дубликатов "
                "запросов нет.")
    figure(document, "pr10/09_debug_toolbar_sql.png",
           "SQL-панель Django Debug Toolbar на странице списка участков")

    h1(document, "6. Результаты проверки доступности и статистики")
    p(document, "Проверены три сценария на одной и той же дате: оформление аренды свободного "
                "участка, попытка повторной аренды того же участка на пересекающиеся даты и "
                "повторное оформление после отмены. Первый и третий сценарии завершаются "
                "успешно, второй отклоняется с сообщением «На выбранные даты участок уже "
                "арендован». Страница статистики корректно учитывает статусы аренды: "
                "действующие, отменённые и завершённые записи показаны отдельно, а "
                "задолженность и число участков считаются по действующим данным.")

    h1(document, "7. Результаты выполнения проверок")
    code(document, """> python manage.py check
System check identified no issues (0 silenced).

> python manage.py makemigrations --check --dry-run
No changes detected

> python -m pytest -q
133 passed

> python -m flake8 .
(замечаний нет)""", "Результаты проверок проекта")

    h1(document, "8. Контрольная точка Git")
    table(document, ["Коммит", "Содержание"], [
        ["PR10: административная панель Django и ORM-запросы",
         "ModelAdmin для четырёх моделей, действия и inline, поле Lease.rent_amount с "
         "миграциями 0003–0004, контекстный процессор, Debug Toolbar, тесты админки"],
    ], widths=[7.0, 9.0], caption="Таблица 5 – Коммит контрольной точки ПР10")
    p(document, "Рабочее дерево после коммита чистое, изменения отправлены в удалённый "
                "репозиторий проекта.")

    h1(document, "9. Выводы")
    p(document, "Административная панель настроена для всех моделей реестра: списки содержат "
                "нужные столбцы, работают поиск, фильтры и сортировка, связанные записи "
                "показаны через inline, а типовые операции выполняются действиями. ORM-запросы "
                "проверены в Django shell и через Debug Toolbar: страницы не создают лишних "
                "обращений к базе, агрегаты считаются в SQL. Изменения моделей оформлены "
                "миграциями схемы и данных, ранее реализованная функциональность сохранена.")

    appendix(document, "Приложение Б. Скриншоты работы приложения", [
        ("pr10/01_admin_index.png", "Главная страница административной панели"),
        ("pr10/02_admin_plot_list.png", "Список участков: столбцы, фильтры, редактирование в списке"),
        ("pr10/03_admin_plot_filtered.png", "Фильтрация участков по статусу «аренда»"),
        ("pr10/04_admin_plot_change.png", "Карточка участка со встроенной таблицей аренды"),
        ("pr10/05_admin_owner_change.png", "Карточка владельца: участки, аренды и платежи"),
        ("pr10/06_admin_lease_search.png", "Поиск аренды по арендатору"),
        ("pr10/07_admin_payment_list.png", "Список платежей с фильтрами и действиями"),
        ("pr10/08_admin_actions.png", "Выбор действия «Начислить пеню» в списке участков"),
    ])
    document.save(OUT / "PR10_Django_ORM_Admin_otchet.docx")
    print("saved PR10")


# --------------------------------------------------------------------------- #
# PR11
# --------------------------------------------------------------------------- #
def build_pr11():
    reset_figures("В")
    document = new_document()
    title_page(
        document, 11, "ФОРМЫ В DJANGO",
        "Отчёт содержит описание созданных форм, фильтрации через GET-параметры, валидации "
        "и обработки ошибок, создания и редактирования записей через ModelForm, отмены "
        "записей со сменой статуса, результатов проверки сценариев и подтверждающие "
        "скриншоты.",
    )

    h1(document, "1. Тема и цель работы")
    p(document, "Тема — формы в Django.")
    p(document, "Цель работы — изучить создание, настройку, валидацию и обработку форм Django, "
                "освоить фильтрацию данных по параметрам запроса, формы на основе ModelForm, "
                "проверку бизнес-правил, редактирование и отмену записей, а также загрузку "
                "файлов; применить полученные приёмы к предметной области индивидуального "
                "проекта «Садовый реестр».")

    h1(document, "2. Выполненные задания Яндекс Практикума")
    table(document, ["Тема", "Содержание", "Отметка"], [
        ["Создание и обработка форм", "forms.Form, поля, виджеты, GET и POST, cleaned_data",
         "Выполнено"],
        ["Формы на основе моделей", "forms.ModelForm, Meta, save(), commit=False",
         "Выполнено"],
        ["Валидация и ошибки", "clean_<field>(), clean(), ValidationError, вывод ошибок",
         "Выполнено"],
        ["Редактирование и отмена", "instance=, exclude(pk), смена статуса вместо удаления",
         "Выполнено"],
        ["Загрузка файлов", "ImageField, request.FILES, multipart/form-data", "Выполнено"],
    ], widths=[4.6, 9.4, 2.0], caption="Таблица 1 – Выполненные задания практикума")

    h1(document, "3. Созданные формы и их назначение")
    table(document, ["Форма", "База", "Поля", "Назначение и проверки"], [
        ["PlotFilterForm", "forms.Form", "q, status, ordering, area_min",
         "фильтр реестра участков; длина строки поиска, числовые значения"],
        ["OwnerFilterForm", "forms.Form", "q", "поиск владельца по ФИО, телефону, почте"],
        ["PaymentFilterForm", "forms.Form", "q, status, ordering, date_from, date_to",
         "фильтр платежей; проверка порядка дат периода"],
        ["LeaseFilterForm", "forms.Form", "plot, owner, status, ordering, date_from, date_to",
         "фильтр аренды; проверка порядка дат периода"],
        ["PlotForm", "ModelForm", "plot_number, area_sqm, status, owner, debt, image",
         "создание и редактирование участка; формат номера, площадь, согласованность "
         "статуса и владельца, размер файла"],
        ["OwnerForm", "ModelForm", "full_name, phone, email",
         "создание и редактирование владельца; формат телефона"],
        ["PaymentForm", "ModelForm", "owner, amount, payment_date, description",
         "регистрация платежа; запрет будущей даты и нулевой суммы"],
        ["LeaseForm", "ModelForm", "plot, owner, start_date, end_date, rent_amount, note",
         "оформление аренды; прошедшая дата, обратный период, занятость участка"],
    ], widths=[3.0, 2.2, 5.2, 5.6], caption="Таблица 2 – Формы проекта")

    h1(document, "4. Фильтрация данных с использованием GET-параметров")
    p(document, "Фильтры передаются методом GET: параметры попадают в адресную строку, "
                "сохраняются при переходе между страницами и не изменяют данные на сервере. "
                "Представление валидирует форму и передаёт только cleaned_data в слой запросов.")
    code(document, """def _clean_filters(request, form_class):
    if not request.GET:
        return form_class(), {}
    form = form_class(request.GET)
    if not form.is_valid():
        messages.warning(request, "Параметры фильтра некорректны — показаны все записи.")
        return form, {}
    return form, dict(form.cleaned_data)


def plots(request):
    form, filters = _clean_filters(request, PlotFilterForm)
    page = queries.plot_page(
        status=filters.get("status") or "",
        query=filters.get("q") or "",
        ordering=filters.get("ordering") or queries.DEFAULT_PLOT_ORDERING,
        area_min=filters.get("area_min"),
        page=_page_number(request),
    )
    ...""")
    p(document, "Некорректные параметры (например, status=unknown или q из одного символа) "
                "не приводят к ошибке сервера: показывается предупреждение и список без "
                "фильтра. Номер страницы разбирается безопасно, значение по умолчанию — первая "
                "страница. Это проверено тестами FilterViewTests.")
    figure(document, "pr11/01_filter_filled.png", "Форма фильтрации с заполненными полями")
    figure(document, "pr11/02_filter_result.png", "Результат фильтрации списка участков")

    h1(document, "5. Валидация данных и обработка ошибок")
    p(document, "Проверки выполняются на трёх уровнях: типы полей формы, методы "
                "clean_<field>() и общий clean(). Дополнительно при сохранении ModelForm "
                "вызывает full_clean() модели, поэтому ограничения предметной области не "
                "дублируются, а сообщение о конфликте аренды выводится один раз как общая "
                "ошибка формы.")
    table(document, ["Правило", "Где реализовано", "Сообщение"], [
        ["Номер участка: число и необязательная буква", "validate_plot_number (модель)",
         "«Номер участка должен состоять из числа (1–3 цифры) и, при необходимости, буквы»"],
        ["Площадь не меньше 1 м²", "PlotForm.clean_area_sqm",
         "«Площадь участка должна быть не меньше 1 м²»"],
        ["Свободный участок без владельца", "Plot.clean(), PlotForm.clean()",
         "«У свободного участка не может быть владельца»"],
        ["Занятый участок с владельцем", "Plot.clean(), PlotForm.clean()",
         "«Для занятого или арендованного участка укажите владельца»"],
        ["Телефон: 7–20 цифр и разделители", "validate_phone (модель)",
         "«Телефон должен содержать 7–20 цифр…»"],
        ["Сумма платежа больше нуля", "PaymentForm.clean_amount",
         "«Сумма платежа должна быть больше нуля»"],
        ["Дата платежа не в будущем", "PaymentForm.clean_payment_date",
         "«Дата платежа не может быть в будущем»"],
        ["Дата начала аренды не в прошлом", "LeaseForm.clean_start_date",
         "«Нельзя оформить аренду с прошедшей даты»"],
        ["Окончание не раньше начала", "Lease.clean(), LeaseForm.clean()",
         "«Дата окончания не может быть раньше даты начала»"],
        ["Участок не занят на выбранные даты", "Lease.clean()",
         "«На выбранные даты участок уже арендован. Выберите другой период или участок»"],
        ["Размер изображения не более 5 МБ", "PlotForm.clean_image",
         "«Размер изображения не должен превышать 5 МБ»"],
    ], widths=[4.6, 5.0, 6.4], caption="Таблица 3 – Проверки данных")
    figure(document, "pr11/04_plot_form_error.png",
           "Ошибка отдельного поля: свободный участок не может иметь владельца")
    figure(document, "pr11/07_lease_conflict_error.png",
           "Общая ошибка формы: участок уже арендован на выбранные даты")

    h1(document, "6. Создание и редактирование записей через ModelForm")
    p(document, "Создание и редактирование выполняются одним представлением и одним классом "
                "формы. При редактировании форма получает параметр instance, поэтому поля "
                "заполнены текущими значениями, а сохранение обновляет существующую запись. "
                "После успешного сохранения выполняется перенаправление (PRG), чтобы "
                "повторная отправка формы не создавала дубликат.")
    code(document, """def plot_create(request):
    form = PlotForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        plot = form.save()
        messages.success(request, f"Участок № {plot.plot_number} добавлен в реестр.")
        return redirect(plot.get_absolute_url())
    return render(request, "registry/form_page.html", {...})


def plot_update(request, slug):
    plot = get_object_or_404(Plot, slug=slug)
    form = PlotForm(request.POST or None, request.FILES or None, instance=plot)
    ...""")
    figure(document, "pr11/03_plot_form_filled.png", "Форма создания участка")
    figure(document, "pr11/05_plot_created_image.png",
           "Созданный участок с загруженным изображением")
    figure(document, "pr11/09_lease_edit_form.png",
           "Редактирование существующей аренды")

    h1(document, "7. Проверка даты и доступности участка")
    p(document, "Форма аренды не позволяет оформить договор с прошедшей даты, с обратным "
                "периодом и на участок, у которого есть действующая аренда с пересечением "
                "дат. При редактировании проверяемая запись исключается из выборки через "
                "exclude(pk=self.instance.pk), поэтому сохранение без изменения дат проходит "
                "успешно. Отменённая аренда не блокирует участок: метод active() учитывает "
                "только статус «действует».")
    code(document, """def clean(self):
    cleaned = super().clean()
    start_date = cleaned.get("start_date")
    end_date = cleaned.get("end_date")
    if start_date and end_date and end_date < start_date:
        self.add_error("end_date", "Дата окончания не может быть раньше даты начала.")
    # Правило занятости реализовано в Lease.clean(): ModelForm вызывает full_clean()
    return cleaned


# registry/models.py
def clean(self):
    ...
    if self.plot_id and self.start_date and self.end_date:
        conflict = Lease.objects.overlapping(
            self.plot, self.start_date, self.end_date, exclude_pk=self.pk,
        ).exists()
        if conflict:
            raise ValidationError("На выбранные даты участок уже арендован. ...")""")

    h1(document, "8. Отмена записи с изменением статуса")
    p(document, "Платёж и аренда не удаляются: методы cancel() переводят запись в состояние "
                "«отменён», запись остаётся в базе и в истории. Отмена выполняется только "
                "POST-запросом: представления помечены @require_POST, кнопки находятся в "
                "формах с CSRF-токеном, а прямой GET-запрос возвращает 405 Method Not Allowed. "
                "После отмены аренды сервис sync_plot_status() пересчитывает статус участка: "
                "если других действующих аренд нет, участок снова становится занятым или "
                "свободным.")
    code(document, """@require_POST
def lease_cancel(request, pk):
    lease = get_object_or_404(Lease.objects.with_related(), pk=pk)
    services.cancel_lease(lease)
    messages.warning(request, f"Аренда участка № {lease.plot.plot_number} отменена. "
                              "Статус участка обновлён, запись сохранена в архиве.")
    return redirect("registry:leases")


@require_POST
def payment_cancel(request, pk):
    payment = get_object_or_404(Payment.objects.with_owner(), pk=pk)
    services.cancel_payment(payment)
    return redirect("registry:payments")""")
    figure(document, "pr11/10_lease_detail_before_cancel.png",
           "Карточка аренды до отмены")
    figure(document, "pr11/11_lease_cancelled.png",
           "Результат отмены аренды: статус изменён, запись сохранена")
    figure(document, "pr11/14_payment_cancelled.png",
           "Результат отмены платежа в истории")
    figure(document, "pr11/15_not_found_404.png",
           "Страница 404 при обращении к несуществующему участку")

    h1(document, "9. Загрузка файлов и изображений")
    p(document, "В модель участка добавлено поле ImageField(upload_to=\"plots/\"), в настройках "
                "заданы MEDIA_URL и MEDIA_ROOT, форма сохраняет файл через request.FILES, а "
                "шаблон формы использует enctype=\"multipart/form-data\". Размер файла "
                "ограничен 5 МБ проверкой формы, изображение выводится в карточке участка. "
                "В рабочем режиме раздачу медиафайлов выполняет веб-сервер, в режиме "
                "разработки — Django.")

    h1(document, "10. Результаты проверки пользовательских сценариев")
    table(document, ["Сценарий", "Ожидаемый результат", "Факт"], [
        ["Фильтрация списка участков по статусу, владельцу и площади",
         "список соответствует параметрам", "Выполнено"],
        ["Сортировка и переход между страницами с сохранением фильтров",
         "параметры сохраняются в ссылках", "Выполнено"],
        ["Создание участка с корректными данными", "запись сохранена, открыта карточка",
         "Выполнено"],
        ["Свободный участок с владельцем", "ошибка поля, запись не сохраняется", "Выполнено"],
        ["Создание аренды на свободный участок",
         "запись создана, участок переведён в статус «аренда»", "Выполнено"],
        ["Аренда участка на занятые даты", "общая ошибка формы, запись не создана",
         "Выполнено"],
        ["Начало аренды в прошедшей дате", "ошибка поля, запись не создана", "Выполнено"],
        ["Редактирование аренды без изменения дат", "сохранение проходит без конфликта",
         "Выполнено"],
        ["Отмена аренды", "статус «отменена», участок освобождён", "Выполнено"],
        ["Регистрация платежа и его отмена",
         "платёж создан, затем переведён в состояние «отменён»", "Выполнено"],
        ["Обращение к адресу отмены GET-запросом", "ответ 405, данные не меняются",
         "Выполнено"],
        ["Обращение к несуществующему участку", "страница 404", "Выполнено"],
        ["Загрузка изображения участка", "файл сохранён, изображение отображается",
         "Выполнено"],
    ], widths=[6.2, 7.0, 2.8], caption="Таблица 4 – Проверенные сценарии")

    h1(document, "11. Результаты выполнения проверок")
    code(document, """> python manage.py check
System check identified no issues (0 silenced).

> python manage.py makemigrations --check --dry-run
No changes detected

> python -m pytest -q
133 passed

> python -m flake8 .
(замечаний нет)""", "Результаты проверок проекта")

    h1(document, "12. Контрольная точка Git")
    table(document, ["Коммит", "Содержание"], [
        ["PR11: формы Django для участков, владельцев, платежей и аренды",
         "фильтры на forms.Form, ModelForm для четырёх сущностей, проверки и сообщения, "
         "CRUD-представления, отмена через статус, загрузка изображений, тесты, README"],
    ], widths=[7.0, 9.0], caption="Таблица 5 – Коммит контрольной точки ПР11")
    p(document, "Рабочее дерево после коммита чистое, изменения отправлены в удалённый "
                "репозиторий проекта.")

    h1(document, "13. Выводы")
    p(document, "Формы Django стали единой точкой ввода и проверки данных реестра. "
                "Фильтрация через GET-параметры работает предсказуемо и безопасно для "
                "некорректных значений, ModelForm избавил от дублирования кода при создании и "
                "редактировании, а проверки предметной области (дата, сумма, площадь, "
                "занятость участка) выполняются на сервере и не могут быть обойдены через "
                "интерфейс. Отмена записей со сменой статуса сохраняет историю и корректно "
                "влияет на занятость участков.")

    appendix(document, "Приложение В. Скриншоты работы приложения", [
        ("pr11/06_lease_form.png", "Форма оформления аренды участка"),
        ("pr11/08_lease_created.png", "Созданная аренда: карточка записи"),
        ("pr11/12_payment_form.png", "Форма регистрации платежа"),
        ("pr11/13_payment_created.png", "Платёж добавлен в историю"),
    ])
    document.save(OUT / "PR11_Django_Forms_otchet.docx")
    print("saved PR11")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    build_pr9()
    build_pr10()
    build_pr11()
