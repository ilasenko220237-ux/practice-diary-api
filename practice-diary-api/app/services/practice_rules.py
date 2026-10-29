"""Бизнес-логика практики. Модуль не зависит от БД — его легко тестировать."""
from datetime import date, timedelta

# Практика не засчитывается, если пропущено БОЛЬШЕ 10% рабочих дней
MAX_MISSED_PERCENT = 10


def working_days(start: date, end: date) -> list[date]:
    """Рабочие дни (пн–пт) в периоде [start, end] включительно."""
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def is_working_day(d: date) -> bool:
    return d.weekday() < 5


def build_report(practice, entries, today: date | None = None) -> dict:
    """Строит отчёт по отработанным часам и применяет правило «>10% пропусков».

    Пропуск = рабочий день, который уже закончился (дата < сегодня),
    но по нему нет записи с отработанными часами (либо стоит отметка «отсутствовал»).
    """
    today = today or date.today()
    days = working_days(practice.start_date, practice.end_date)
    total = len(days)

    present_dates = {e.work_date for e in entries if not e.is_absent and e.hours_worked > 0}
    missed_dates = [d for d in days if d < today and d not in present_dates]
    attended = len([d for d in days if d in present_dates])
    missed = len(missed_dates)

    # missed / total > 10%  <=>  missed * 100 > total * 10 (без ошибок float)
    violated = total > 0 and missed * 100 > total * MAX_MISSED_PERCENT
    allowed_missed = total * MAX_MISSED_PERCENT // 100

    planned = round(total * practice.hours_per_day, 2)
    worked = round(sum(e.hours_worked for e in entries if not e.is_absent), 2)

    finished = today > practice.end_date
    if violated:
        status = "not_credited"
        verdict = (
            f"Практика не засчитывается: пропущено {missed} из {total} рабочих дней "
            f"(допустимо не более {allowed_missed})."
        )
    elif finished:
        status = "credited"
        verdict = f"Практика засчитывается: пропущено {missed} из {total} рабочих дней."
    else:
        status = "in_progress"
        verdict = (
            f"Практика продолжается: пропущено {missed} из {total} рабочих дней "
            f"(допустимо не более {allowed_missed})."
        )

    return {
        "practice_id": practice.id,
        "start_date": practice.start_date,
        "end_date": practice.end_date,
        "hours_per_day": practice.hours_per_day,
        "total_working_days": total,
        "attended_days": attended,
        "missed_days": missed,
        "missed_dates": missed_dates,
        "missed_percent": round(missed / total * 100, 2) if total else 0.0,
        "allowed_missed_days": allowed_missed,
        "planned_hours": planned,
        "worked_hours": worked,
        "completion_percent": round(worked / planned * 100, 2) if planned else 0.0,
        "rule_violated": violated,
        "credit_status": status,
        "verdict": verdict,
        "entries": [
            {
                "work_date": e.work_date,
                "hours_worked": e.hours_worked,
                "is_absent": e.is_absent,
                "description": e.description,
            }
            for e in sorted(entries, key=lambda x: x.work_date)
        ],
    }
