from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    specialty: Mapped[str] = mapped_column(String(100))
    course: Mapped[int] = mapped_column(Integer)

    students: Mapped[list["Student"]] = relationship(back_populates="group")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    birth_date: Mapped[date] = mapped_column(Date)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))

    group: Mapped[Group] = relationship(back_populates="students")
    practices: Mapped[list["Practice"]] = relationship(back_populates="student")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    department: Mapped[str] = mapped_column(String(100))

    subjects: Mapped[list["Subject"]] = relationship(back_populates="teacher")
    practices: Mapped[list["Practice"]] = relationship(back_populates="teacher")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    hours: Mapped[int] = mapped_column(Integer)
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"), nullable=True)

    teacher: Mapped[Teacher | None] = relationship(back_populates="subjects")
    practices: Mapped[list["Practice"]] = relationship(back_populates="subject")


class Practice(Base):
    """Производственная практика студента (шапка дневника)."""

    __tablename__ = "practices"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))  # руководитель практики
    organization: Mapped[str] = mapped_column(String(150))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    hours_per_day: Mapped[float] = mapped_column(Float, default=8.0)
    # in_progress | credited | not_credited
    status: Mapped[str] = mapped_column(String(20), default="in_progress")

    student: Mapped[Student] = relationship(back_populates="practices")
    subject: Mapped[Subject] = relationship(back_populates="practices")
    teacher: Mapped[Teacher] = relationship(back_populates="practices")
    entries: Mapped[list["PracticeEntry"]] = relationship(
        back_populates="practice", cascade="all, delete-orphan", order_by="PracticeEntry.work_date"
    )


class PracticeEntry(Base):
    """Запись дневника практики за один рабочий день."""

    __tablename__ = "practice_entries"
    __table_args__ = (UniqueConstraint("practice_id", "work_date", name="uq_practice_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    practice_id: Mapped[int] = mapped_column(ForeignKey("practices.id"))
    work_date: Mapped[date] = mapped_column(Date)
    hours_worked: Mapped[float] = mapped_column(Float, default=0.0)
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    practice: Mapped[Practice] = relationship(back_populates="entries")
