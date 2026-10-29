"""Слой Service: дневник практики, отчёт и правило «>10% пропусков»."""
from datetime import date

from app.errors import BadRequestError, ConflictError, NotFoundError
from app.models import Practice, PracticeEntry
from app.repositories import (
    EntryRepository,
    PracticeRepository,
    StudentRepository,
    SubjectRepository,
    TeacherRepository,
)
from app.schemas import EntryIn, PracticeIn
from app.services.practice_rules import build_report, is_working_day, working_days


class PracticeService:
    def __init__(self, db):
        self.repo = PracticeRepository(db)
        self.entries = EntryRepository(db)
        self.students = StudentRepository(db)
        self.subjects = SubjectRepository(db)
        self.teachers = TeacherRepository(db)

    # ---------- проверки ----------
    def _validate_practice(self, data: PracticeIn, exclude_id: int | None = None):
        self.students.get_or_404(data.student_id)
        self.subjects.get_or_404(data.subject_id)
        self.teachers.get_or_404(data.teacher_id)

        if not working_days(data.start_date, data.end_date):
            raise BadRequestError("В периоде практики нет ни одного рабочего дня (пн–пт)")

        # у студента не должно быть двух пересекающихся практик
        for other in self.repo.list_by_student(data.student_id):
            if other.id == exclude_id:
                continue
            if data.start_date <= other.end_date and other.start_date <= data.end_date:
                raise ConflictError(
                    f"Период пересекается с практикой id={other.id} "
                    f"({other.start_date} — {other.end_date}) этого студента"
                )

    def _get_open(self, practice_id: int) -> Practice:
        practice = self.repo.get_or_404(practice_id)
        if practice.status != "in_progress":
            raise ConflictError("Практика уже закрыта — изменять дневник нельзя")
        return practice

    def _get_entry(self, practice_id: int, entry_id: int) -> PracticeEntry:
        entry = self.entries.get_in_practice(practice_id, entry_id)
        if entry is None:
            raise NotFoundError(f"Запись с id={entry_id} в практике id={practice_id} не найдена")
        return entry

    def _validate_entry(self, practice: Practice, data: EntryIn, exclude_id: int | None = None):
        if not (practice.start_date <= data.work_date <= practice.end_date):
            raise BadRequestError(
                f"Дата {data.work_date} вне периода практики "
                f"({practice.start_date} — {practice.end_date})"
            )
        if not is_working_day(data.work_date):
            raise BadRequestError("Запись можно вносить только за рабочий день (пн–пт)")
        if data.work_date > date.today():
            raise BadRequestError("Нельзя вносить запись за будущую дату")
        existing = self.entries.get_by_date(practice.id, data.work_date)
        if existing and existing.id != exclude_id:
            raise ConflictError(f"Запись за {data.work_date} уже есть в дневнике")
        max_hours = practice.hours_per_day * 1.5
        if data.hours_worked > max_hours:
            raise BadRequestError(
                f"Слишком много часов за день (норма {practice.hours_per_day} ч, максимум {max_hours} ч)"
            )

    # ---------- CRUD практики ----------
    def create(self, data: PracticeIn) -> Practice:
        self._validate_practice(data)
        practice = Practice(**data.model_dump(), status="in_progress")
        self.repo.add(practice)
        self.repo.commit()
        return practice

    def list(self, skip: int, limit: int, student_id: int | None = None, status: str | None = None):
        conditions = []
        if student_id is not None:
            conditions.append(Practice.student_id == student_id)
        if status is not None:
            conditions.append(Practice.status == status)
        return self.repo.get_all(skip, limit, *conditions)

    def get(self, practice_id: int) -> Practice:
        return self.repo.get_or_404(practice_id)

    def update(self, practice_id: int, data: PracticeIn) -> Practice:
        practice = self._get_open(practice_id)
        self._validate_practice(data, exclude_id=practice_id)
        if any(not (data.start_date <= e.work_date <= data.end_date) for e in practice.entries):
            raise ConflictError("Новый период не покрывает уже внесённые записи дневника")
        for key, value in data.model_dump().items():
            setattr(practice, key, value)
        self.repo.commit()
        return practice

    def delete(self, practice_id: int) -> None:
        practice = self.repo.get_or_404(practice_id)
        self.repo.delete(practice)
        self.repo.commit()

    # ---------- записи дневника ----------
    def add_entry(self, practice_id: int, data: EntryIn) -> PracticeEntry:
        practice = self._get_open(practice_id)
        self._validate_entry(practice, data)
        entry = PracticeEntry(practice_id=practice_id, **data.model_dump())
        self.entries.add(entry)
        self.entries.commit()
        return entry

    def list_entries(self, practice_id: int):
        return self.repo.get_or_404(practice_id).entries

    def update_entry(self, practice_id: int, entry_id: int, data: EntryIn) -> PracticeEntry:
        practice = self._get_open(practice_id)
        entry = self._get_entry(practice_id, entry_id)
        self._validate_entry(practice, data, exclude_id=entry_id)
        for key, value in data.model_dump().items():
            setattr(entry, key, value)
        self.entries.commit()
        return entry

    def delete_entry(self, practice_id: int, entry_id: int) -> None:
        self._get_open(practice_id)
        entry = self._get_entry(practice_id, entry_id)
        self.entries.delete(entry)
        self.entries.commit()

    # ---------- отчёт и бизнес-правило ----------
    def report(self, practice_id: int) -> dict:
        practice = self.repo.get_or_404(practice_id)
        return self._build(practice)

    def complete(self, practice_id: int) -> dict:
        practice = self._get_open(practice_id)
        if date.today() <= practice.end_date:
            raise ConflictError("Практика ещё не завершена — закрыть можно после даты окончания")
        report = self._build(practice)
        practice.status = report["credit_status"]
        self.repo.commit()
        return report

    @staticmethod
    def _build(practice: Practice) -> dict:
        report = build_report(practice, practice.entries)
        report["student_full_name"] = practice.student.full_name
        report["organization"] = practice.organization
        return report
