"""Слой Service: бизнес-логика преподавателей."""
from app.errors import ConflictError
from app.models import Teacher
from app.repositories import TeacherRepository
from app.schemas import TeacherIn


class TeacherService:
    def __init__(self, db):
        self.repo = TeacherRepository(db)

    def _ensure_unique_email(self, email: str, exclude_id: int | None = None):
        existing = self.repo.get_by_email(email)
        if existing and existing.id != exclude_id:
            raise ConflictError(f"Преподаватель с email {email} уже существует")

    def create(self, data: TeacherIn):
        self._ensure_unique_email(data.email)
        teacher = Teacher(**data.model_dump())
        self.repo.add(teacher)
        self.repo.commit()
        return teacher

    def list(self, skip: int, limit: int):
        return self.repo.get_all(skip, limit)

    def get(self, teacher_id: int):
        return self.repo.get_or_404(teacher_id)

    def update(self, teacher_id: int, data: TeacherIn):
        teacher = self.repo.get_or_404(teacher_id)
        self._ensure_unique_email(data.email, exclude_id=teacher_id)
        for key, value in data.model_dump().items():
            setattr(teacher, key, value)
        self.repo.commit()
        return teacher

    def delete(self, teacher_id: int):
        teacher = self.repo.get_or_404(teacher_id)
        if self.repo.count_links(teacher_id):
            raise ConflictError("Нельзя удалить преподавателя: он привязан к предметам или практикам")
        self.repo.delete(teacher)
        self.repo.commit()
