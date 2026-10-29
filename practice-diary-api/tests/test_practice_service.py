from datetime import date, timedelta
from types import SimpleNamespace

from app.services.practice_rules import build_report, working_days

# Период 2026-09-14 (пн) — 2026-09-25 (пт): ровно 10 рабочих дней
START, END = date(2026, 9, 14), date(2026, 9, 25)
AFTER_END = date(2026, 10, 1)


def make_practice():
    return SimpleNamespace(id=1, start_date=START, end_date=END, hours_per_day=8.0)


def entries_for(days):
    return [
        SimpleNamespace(work_date=d, hours_worked=8.0, is_absent=False, description="работа")
        for d in days
    ]


def test_working_days_skip_weekends():
    days = working_days(START, END)
    assert len(days) == 10
    assert all(d.weekday() < 5 for d in days)


def test_one_missed_day_of_ten_is_allowed():
    days = working_days(START, END)
    report = build_report(make_practice(), entries_for(days[:-1]), today=AFTER_END)
    assert report["missed_days"] == 1
    assert report["missed_percent"] == 10.0
    assert report["rule_violated"] is False
    assert report["credit_status"] == "credited"


def test_two_missed_days_of_ten_not_credited():
    days = working_days(START, END)
    report = build_report(make_practice(), entries_for(days[:-2]), today=AFTER_END)
    assert report["missed_days"] == 2
    assert report["rule_violated"] is True
    assert report["credit_status"] == "not_credited"


def test_hours_report():
    days = working_days(START, END)
    report = build_report(make_practice(), entries_for(days), today=AFTER_END)
    assert report["planned_hours"] == 80
    assert report["worked_hours"] == 80
    assert report["completion_percent"] == 100.0


def test_in_progress_today_not_counted_as_missed():
    days = working_days(START, END)
    today = days[3]  # 4-й день ещё идёт
    report = build_report(make_practice(), entries_for(days[:3]), today=today)
    assert report["missed_days"] == 0
    assert report["credit_status"] == "in_progress"


def test_absent_marker_counts_as_missed():
    days = working_days(START, END)
    entries = entries_for(days[:-2])
    entries.append(SimpleNamespace(work_date=days[-2], hours_worked=0, is_absent=True, description=None))
    report = build_report(make_practice(), entries, today=AFTER_END)
    assert report["missed_days"] == 2
    assert report["credit_status"] == "not_credited"
