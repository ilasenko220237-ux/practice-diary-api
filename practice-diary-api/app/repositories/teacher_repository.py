from sqlalchemy import func, select

from app.models import Practice, Subject, Teacher
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository):
    model = Teacher
    entity_name = "Преподаватель"

    def get_by_email(self, email: str):
        return self.db.scalar(select(Teacher).where(Teacher.email == email))

    def count_links(self, teacher_id: int) -> int:
        """Сколько предметов и практик привязано к преподавателю."""
        subjects = select(func.count()).select_from(Subject).where(Subject.teacher_id == teacher_id)
        practices = select(func.count()).select_from(Practice).where(Practice.teacher_id == teacher_id)
        return (self.db.scalar(subjects) or 0) + (self.db.scalar(practices) or 0)
