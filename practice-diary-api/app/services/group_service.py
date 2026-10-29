"""Слой Service: бизнес-логика групп."""
from app.errors import ConflictError
from app.models import Group
from app.repositories import GroupRepository
from app.schemas import GroupIn


class GroupService:
    def __init__(self, db):
        self.repo = GroupRepository(db)

    def _ensure_unique_name(self, name: str, exclude_id: int | None = None):
        existing = self.repo.get_by_name(name)
        if existing and existing.id != exclude_id:
            raise ConflictError(f"Группа с названием «{name}» уже существует")

    def create(self, data: GroupIn):
        self._ensure_unique_name(data.name)
        group = Group(**data.model_dump())
        self.repo.add(group)
        self.repo.commit()
        return group

    def list(self, skip: int, limit: int):
        return self.repo.get_all(skip, limit)

    def get(self, group_id: int):
        return self.repo.get_or_404(group_id)

    def update(self, group_id: int, data: GroupIn):
        group = self.repo.get_or_404(group_id)
        self._ensure_unique_name(data.name, exclude_id=group_id)
        for key, value in data.model_dump().items():
            setattr(group, key, value)
        self.repo.commit()
        return group

    def delete(self, group_id: int):
        group = self.repo.get_or_404(group_id)
        students = self.repo.count_students(group_id)
        if students:
            raise ConflictError(f"Нельзя удалить группу: в ней {students} студент(ов)")
        self.repo.delete(group)
        self.repo.commit()
