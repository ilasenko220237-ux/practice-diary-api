import re
from datetime import date
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

_NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё'\-]+( [A-Za-zА-Яа-яЁё'\-]+)+$")


def _check_full_name(value: str) -> str:
    value = " ".join(value.split())
    if not _NAME_RE.match(value):
        raise ValueError(
            "ФИО должно содержать минимум два слова и состоять только из букв, дефиса и апострофа"
        )
    return value


FullName = Annotated[
    str,
    Field(min_length=5, max_length=150, examples=["Иванов Иван Иванович"]),
    AfterValidator(_check_full_name),
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Группа ----------
class GroupIn(BaseModel):
    name: str = Field(min_length=2, max_length=30, examples=["454"])
    specialty: str = Field(min_length=2, max_length=100, examples=["Информационные системы"])
    course: int = Field(ge=1, le=4, examples=[3])


class GroupOut(GroupIn, ORMModel):
    id: int


# ---------- Преподаватель ----------
class TeacherIn(BaseModel):
    full_name: FullName
    email: EmailStr
    department: str = Field(min_length=2, max_length=100, examples=["Кафедра ИТ"])


class TeacherOut(ORMModel):
    id: int
    full_name: str
    email: str
    department: str


# ---------- Предмет ----------
class SubjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=150, examples=["Производственная практика"])
    hours: int = Field(ge=1, le=2000, examples=[144])
    teacher_id: int | None = Field(default=None, ge=1)


class SubjectOut(ORMModel):
    id: int
    name: str
    hours: int
    teacher_id: int | None


# ---------- Студент ----------
class StudentIn(BaseModel):
    full_name: FullName
    email: EmailStr
    birth_date: date = Field(examples=["2005-03-14"])
    group_id: int = Field(ge=1)

    @field_validator("birth_date")
    @classmethod
    def _check_birth_date(cls, v: date) -> date:
        today = date.today()
        if v >= today:
            raise ValueError("Дата рождения не может быть в будущем")
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 14 or age > 100:
            raise ValueError("Возраст студента должен быть от 14 до 100 лет")
        return v


class StudentOut(ORMModel):
    id: int
    full_name: str
    email: str
    birth_date: date
    group_id: int


# ---------- Практика ----------
class PracticeIn(BaseModel):
    student_id: int = Field(ge=1)
    subject_id: int = Field(ge=1)
    teacher_id: int = Field(ge=1, description="Руководитель практики")
    organization: str = Field(min_length=2, max_length=150, examples=["ООО «Вебстудия»"])
    start_date: date = Field(examples=["2026-09-14"])
    end_date: date = Field(examples=["2026-10-09"])
    hours_per_day: float = Field(default=8.0, gt=0, le=12)

    @model_validator(mode="after")
    def _check_period(self):
        if self.end_date < self.start_date:
            raise ValueError("Дата окончания практики не может быть раньше даты начала")
        if (self.end_date - self.start_date).days > 365:
            raise ValueError("Практика не может длиться более года")
        return self


class PracticeOut(ORMModel):
    id: int
    student_id: int
    subject_id: int
    teacher_id: int
    organization: str
    start_date: date
    end_date: date
    hours_per_day: float
    status: Literal["in_progress", "credited", "not_credited"]


# ---------- Запись дневника ----------
class EntryIn(BaseModel):
    work_date: date = Field(examples=["2026-09-15"])
    hours_worked: float = Field(default=0, ge=0, le=12)
    is_absent: bool = False
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _check_entry(self):
        if self.is_absent:
            if self.hours_worked != 0:
                raise ValueError("Для отсутствия на практике hours_worked должно быть 0")
        else:
            if self.hours_worked <= 0:
                raise ValueError("Укажите количество отработанных часов (больше 0)")
            if not self.description or len(self.description.strip()) < 3:
                raise ValueError("Опишите выполненную работу (description, минимум 3 символа)")
        return self


class EntryOut(ORMModel):
    id: int
    practice_id: int
    work_date: date
    hours_worked: float
    is_absent: bool
    description: str | None


# ---------- Отчёт ----------
class ReportDay(BaseModel):
    work_date: date
    hours_worked: float
    is_absent: bool
    description: str | None


class PracticeReport(BaseModel):
    practice_id: int
    student_full_name: str
    organization: str
    start_date: date
    end_date: date
    hours_per_day: float
    total_working_days: int
    attended_days: int
    missed_days: int
    missed_dates: list[date]
    missed_percent: float
    allowed_missed_days: int
    planned_hours: float
    worked_hours: float
    completion_percent: float
    rule_violated: bool
    credit_status: Literal["in_progress", "credited", "not_credited"]
    verdict: str
    entries: list[ReportDay]
