"""Слой Repository: единственное место, где выполняются запросы к БД."""
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model: type
    entity_name: str = "Объект"

    def __init__(self, db: Session):
        self.db = db

    def get(self, obj_id: int):
        return self.db.get(self.model, obj_id)

    def get_or_404(self, obj_id: int):
        obj = self.get(obj_id)
        if obj is None:
            raise NotFoundError(f"{self.entity_name} с id={obj_id} не найден(а)")
        return obj

    def get_all(self, skip: int = 0, limit: int = 50, *conditions):
        query = select(self.model).order_by(self.model.id)
        for condition in conditions:
            query = query.where(condition)
        return list(self.db.scalars(query.offset(skip).limit(limit)).all())

    def count(self, *conditions) -> int:
        query = select(func.count()).select_from(self.model)
        for condition in conditions:
            query = query.where(condition)
        return self.db.scalar(query) or 0

    def add(self, obj) -> None:
        self.db.add(obj)

    def delete(self, obj) -> None:
        self.db.delete(obj)

    def commit(self) -> None:
        """Коммит; ошибки целостности БД превращаются в 409."""
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Операция нарушает ограничения целостности данных")
