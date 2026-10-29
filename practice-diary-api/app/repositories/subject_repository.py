from sqlalchemy import func, select

from app.models import Practice, Subject
from app.repositories.base import BaseRepository


class SubjectRepository(BaseRepository):
    model = Subject
    entity_name = "Предмет"

    def get_by_name(self, name: str):
        return self.db.scalar(select(Subject).where(Subject.name == name))

    def count_practices(self, subject_id: int) -> int:
        query = select(func.count()).select_from(Practice).where(Practice.subject_id == subject_id)
        return self.db.scalar(query) or 0
