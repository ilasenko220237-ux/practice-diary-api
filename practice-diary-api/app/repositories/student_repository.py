from sqlalchemy import func, select

from app.models import Practice, Student
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository):
    model = Student
    entity_name = "Студент"

    def get_by_email(self, email: str):
        return self.db.scalar(select(Student).where(Student.email == email))

    def count_practices(self, student_id: int) -> int:
        query = select(func.count()).select_from(Practice).where(Practice.student_id == student_id)
        return self.db.scalar(query) or 0
