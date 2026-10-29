from app.repositories.group_repository import GroupRepository
from app.repositories.practice_repository import EntryRepository, PracticeRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.teacher_repository import TeacherRepository

__all__ = [
    "GroupRepository",
    "StudentRepository",
    "TeacherRepository",
    "SubjectRepository",
    "PracticeRepository",
    "EntryRepository",
]
