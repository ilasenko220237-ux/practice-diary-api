from sqlalchemy import func, select

from app.models import Group, Student
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository):
    model = Group
    entity_name = "Группа"

    def get_by_name(self, name: str):
        return self.db.scalar(select(Group).where(Group.name == name))

    def count_students(self, group_id: int) -> int:
        query = select(func.count()).select_from(Student).where(Student.group_id == group_id)
        return self.db.scalar(query) or 0
