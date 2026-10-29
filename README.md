# Колледж: учёт студентов и производственной практики

Практическая работа №8, **вариант 11** (блок «Колледж / Техникум»).

REST API на **Python + FastAPI + SQLAlchemy + SQLite**, документация Swagger (OpenAPI) подключена автоматически.

## Что реализовано

**Общее ядро:** CRUD для Student, Group, Subject, Teacher; валидация входных данных (400); глобальные обработчики ошибок (400 / 404 / 409 / 500); Swagger со всеми эндпоинтами.

**Вариант 11:**
- Доп. сущность — **дневник производственной практики** (`Practice` + записи за каждый день `PracticeEntry`).
- Специфический GET — `GET /api/practice/{id}/report` — отчёт по отработанным часам.
- Бизнес-правило — **практика не засчитывается, если пропущено > 10% рабочих дней.**

## Запуск

Нужен Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json
- БД создаётся автоматически (файл `college.db`).

Тесты: `pytest -v`

## Модель данных

```
Group 1───* Student 1───* Practice *───1 Subject
                              │ *───1 Teacher (руководитель практики)
Teacher 1───* Subject         1
                              └───* PracticeEntry (запись за день, UNIQUE(practice_id, work_date))
```

| Таблица | Основные поля |
|---|---|
| groups | id, name (уникально), specialty, course (1–4) |
| students | id, full_name, email (уникально), birth_date, group_id |
| teachers | id, full_name, email (уникально), department |
| subjects | id, name (уникально), hours, teacher_id |
| practices | id, student_id, subject_id, teacher_id, organization, start_date, end_date, hours_per_day, status |
| practice_entries | id, practice_id, work_date, hours_worked, is_absent, description |

`status`: `in_progress` → `credited` / `not_credited`.

## Эндпоинты

| Ресурс | Методы |
|---|---|
| `/api/groups`, `/api/students`, `/api/teachers`, `/api/subjects` | `POST`, `GET` (список), `GET /{id}`, `PUT /{id}`, `DELETE /{id}` |
| `/api/practice` | `POST`, `GET`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` |
| `/api/practice/{id}/entries` | `POST`, `GET`; `PUT` и `DELETE` — `/{entry_id}` |
| `/api/practice/{id}/report` | `GET` — **отчёт по отработанным часам** |
| `/api/practice/{id}/complete` | `POST` — закрыть практику и вынести решение |

## Бизнес-правило

- Рабочие дни — пн–пт в периоде практики.
- **Пропуск** — рабочий день, который уже прошёл (дата < сегодня), но по нему нет записи с отработанными часами (или стоит отметка `is_absent`).
- Если `пропущено / всего рабочих дней > 10%` → `rule_violated = true`, `credit_status = not_credited`.
  Ровно 10% допускается (например, 1 пропуск из 10 дней).
- Пока практика идёт и порог не превышен — `in_progress`; после даты окончания — `credited`.
- `POST /complete` сохраняет итог в `practices.status`; после этого дневник изменять нельзя (409).

## Валидация и ошибки

| Код | Когда |
|---|---|
| 400 | неверный email / ФИО / дата, час ≤ 0, дата записи вне периода, выходной день, будущая дата |
| 404 | объект не найден, несуществующий маршрут |
| 409 | дубликат (email, название, запись за день), пересечение практик, удаление связанного объекта, закрытая практика |
| 500 | необработанная ошибка (единый формат, без стека в ответе) |

Единый формат ошибки:

```json
{ "error": { "code": "validation_error", "message": "Некорректные входные данные",
             "details": [{ "field": "email", "message": "..." }] } }
```

## Пример отчёта

`GET /api/practice/1/report`

```json
{
  "practice_id": 1,
  "student_full_name": "Ильященко Никита Сергеевич",
  "organization": "ООО Вебстудия",
  "total_working_days": 10,
  "attended_days": 8,
  "missed_days": 2,
  "missed_percent": 20.0,
  "allowed_missed_days": 1,
  "planned_hours": 80.0,
  "worked_hours": 64.0,
  "completion_percent": 80.0,
  "rule_violated": true,
  "credit_status": "not_credited",
  "verdict": "Практика не засчитывается: пропущено 2 из 10 рабочих дней (допустимо не более 1)."
}
```

## Архитектура (слои)

```
HTTP-запрос
   ↓
Controller  app/routers/*.py        — только HTTP: маршруты, параметры, коды ответов, описание для Swagger
   ↓
Service     app/services/*.py       — бизнес-логика и проверки (уникальность, связи, правило 10%)
   ↓
Repository  app/repositories/*.py   — все запросы к БД (SQLAlchemy)
   ↓
Model       app/models.py           — ORM-сущности; schemas.py — DTO и валидация (Pydantic)
```

Контроллеры получают сервис через внедрение зависимостей (`app/dependencies.py`).
Чистые расчёты отчёта вынесены в `app/services/practice_rules.py` (без БД, покрыты unit-тестами).

## Структура проекта

```
app/
  main.py                 # приложение, Swagger, подключение роутеров
  database.py             # engine, сессии
  dependencies.py         # DI: сессия БД и сервисы
  models.py               # ORM-модели
  schemas.py              # Pydantic-схемы и валидация
  errors.py               # глобальные обработчики ошибок
  routers/                # Controller: groups, students, teachers, subjects, practice
  services/               # Service: *_service.py, practice_rules.py (расчёт отчёта)
  repositories/           # Repository: base.py + по одному на сущность
tests/
  test_practice_service.py   # unit-тесты правила 10% и отчёта
  test_api.py                # интеграционные тесты API (TestClient, SQLite in-memory)
```
