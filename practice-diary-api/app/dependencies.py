"""Внедрение зависимостей: сессия БД и сервисы для контроллеров."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.group_service import GroupService
from app.services.practice_service import PracticeService
from app.services.student_service import StudentService
from app.services.subject_service import SubjectService
from app.services.teacher_service import TeacherService

DbSession = Annotated[Session, Depends(get_db)]


def get_group_service(db: DbSession) -> GroupService:
    return GroupService(db)


def get_student_service(db: DbSession) -> StudentService:
    return StudentService(db)


def get_teacher_service(db: DbSession) -> TeacherService:
    return TeacherService(db)


def get_subject_service(db: DbSession) -> SubjectService:
    return SubjectService(db)


def get_practice_service(db: DbSession) -> PracticeService:
    return PracticeService(db)


GroupServiceDep = Annotated[GroupService, Depends(get_group_service)]
StudentServiceDep = Annotated[StudentService, Depends(get_student_service)]
TeacherServiceDep = Annotated[TeacherService, Depends(get_teacher_service)]
SubjectServiceDep = Annotated[SubjectService, Depends(get_subject_service)]
PracticeServiceDep = Annotated[PracticeService, Depends(get_practice_service)]
