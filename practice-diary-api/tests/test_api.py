from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def seed(client):
    g = client.post("/api/groups", json={"name": "454", "specialty": "ИС", "course": 3}).json()
    s = client.post(
        "/api/students",
        json={
            "full_name": "Ильященко Никита Сергеевич",
            "email": "nikita@example.com",
            "birth_date": "2005-03-14",
            "group_id": g["id"],
        },
    ).json()
    t = client.post(
        "/api/teachers",
        json={"full_name": "Петров Пётр Петрович", "email": "petrov@example.com", "department": "ИТ"},
    ).json()
    sub = client.post(
        "/api/subjects", json={"name": "Производственная практика", "hours": 144, "teacher_id": t["id"]}
    ).json()
    return s, t, sub


def last_weekdays(n):
    """n последних рабочих дней, заканчивая вчерашним (по возрастанию)."""
    days, d = [], date.today() - timedelta(days=1)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return sorted(days)


def test_validation_returns_400(client):
    r = client.post("/api/students", json={"full_name": "Иван", "email": "bad", "birth_date": "2999-01-01", "group_id": 1})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "validation_error"


def test_not_found_404(client):
    assert client.get("/api/students/999").status_code == 404
    assert client.get("/api/unknown").status_code == 404


def test_group_crud_and_conflict(client):
    r = client.post("/api/groups", json={"name": "101", "specialty": "ИС", "course": 1})
    assert r.status_code == 201
    gid = r.json()["id"]
    assert client.post("/api/groups", json={"name": "101", "specialty": "ИС", "course": 1}).status_code == 409
    assert client.put(f"/api/groups/{gid}", json={"name": "101", "specialty": "ПО", "course": 2}).json()["course"] == 2
    assert client.delete(f"/api/groups/{gid}").status_code == 204
    assert client.get(f"/api/groups/{gid}").status_code == 404


def test_practice_report_and_rule(client):
    s, t, sub = seed(client)
    days = last_weekdays(10)
    practice = client.post(
        "/api/practice",
        json={
            "student_id": s["id"], "subject_id": sub["id"], "teacher_id": t["id"],
            "organization": "ООО Вебстудия",
            "start_date": days[0].isoformat(), "end_date": days[-1].isoformat(),
        },
    )
    assert practice.status_code == 201, practice.text
    pid = practice.json()["id"]

    # вносим 8 из 10 дней -> 2 пропуска (20%) -> не засчитывается
    for d in days[:8]:
        r = client.post(f"/api/practice/{pid}/entries", json={"work_date": d.isoformat(), "hours_worked": 8, "description": "Вёрстка страниц"})
        assert r.status_code == 201, r.text

    report = client.get(f"/api/practice/{pid}/report").json()
    assert report["worked_hours"] == 64
    assert report["missed_days"] == 2
    assert report["rule_violated"] is True
    assert report["credit_status"] == "not_credited"

    # дубль записи за тот же день -> 409
    dup = client.post(f"/api/practice/{pid}/entries", json={"work_date": days[0].isoformat(), "hours_worked": 8, "description": "ещё"})
    assert dup.status_code == 409

    done = client.post(f"/api/practice/{pid}/complete")
    assert done.status_code == 200
    assert client.get(f"/api/practice/{pid}").json()["status"] == "not_credited"
    # после закрытия дневник изменять нельзя
    late = client.post(f"/api/practice/{pid}/entries", json={"work_date": days[9].isoformat(), "hours_worked": 8, "description": "поздно"})
    assert late.status_code == 409


def test_entry_validation(client):
    s, t, sub = seed(client)
    days = last_weekdays(5)
    pid = client.post(
        "/api/practice",
        json={"student_id": s["id"], "subject_id": sub["id"], "teacher_id": t["id"], "organization": "ООО Вебстудия",
              "start_date": days[0].isoformat(), "end_date": days[-1].isoformat()},
    ).json()["id"]
    outside = (days[0] - timedelta(days=30)).isoformat()
    assert client.post(f"/api/practice/{pid}/entries", json={"work_date": outside, "hours_worked": 8, "description": "тест"}).status_code == 400
    assert client.post(f"/api/practice/{pid}/entries", json={"work_date": days[0].isoformat(), "hours_worked": 0, "description": "тест"}).status_code == 400
    assert client.post(f"/api/practice/{pid}/entries", json={"work_date": days[0].isoformat(), "is_absent": True, "hours_worked": 5}).status_code == 400
