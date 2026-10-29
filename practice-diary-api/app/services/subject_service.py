"""Слой Service: бизнес-логика предметов."""
from app.errors import ConflictError
from app.models import Subject
from app.repositories import SubjectRepository, TeacherRepository
from app.schemas import SubjectIn


class SubjectService:
    def __init__(self, db):
        self.repo = SubjectRepository(db)
        self.teachers = TeacherRepository(db)

    def _validate(self, data: SubjectIn, exclude_id: int | None = None):
        existing = self.repo.get_by_name(data.name)
        if existing and existing.id != exclude_id:
            raise ConflictError(f"Предмет «{data.name}» уже существует")
        if data.teacher_id is not None:
            self.teachers.get_or_404(data.teacher_id)

    def create(self, data: SubjectIn):
        self._validate(data)
        subject = Subject(**data.model_dump())
        self.repo.add(subject)
        self.repo.commit()
        return subject

    def list(self, skip: int, limit: int):
        return self.repo.get_all(skip, limit)

    def get(self, subject_id: int):
        return self.repo.get_or_404(subject_id)

    def update(self, subject_id: int, data: SubjectIn):
        subject = self.repo.get_or_404(subject_id)
        self._validate(data, exclude_id=subject_id)
        for key, value in data.model_dump().items():
            setattr(subject, key, value)
        self.repo.commit()
        return subject

    def delete(self, subject_id: int):
        subject = self.repo.get_or_404(subject_id)
        if self.repo.count_practices(subject_id):
            raise ConflictError("Нельзя удалить предмет: по нему есть записи практики")
        self.repo.delete(subject)
        self.repo.commit()
