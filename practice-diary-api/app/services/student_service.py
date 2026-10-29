"""Слой Service: бизнес-логика студентов."""
from app.errors import ConflictError
from app.models import Student
from app.repositories import GroupRepository, StudentRepository
from app.schemas import StudentIn


class StudentService:
    def __init__(self, db):
        self.repo = StudentRepository(db)
        self.groups = GroupRepository(db)

    def _validate(self, data: StudentIn, exclude_id: int | None = None):
        existing = self.repo.get_by_email(data.email)
        if existing and existing.id != exclude_id:
            raise ConflictError(f"Студент с email {data.email} уже существует")
        self.groups.get_or_404(data.group_id)

    def create(self, data: StudentIn):
        self._validate(data)
        student = Student(**data.model_dump())
        self.repo.add(student)
        self.repo.commit()
        return student

    def list(self, skip: int, limit: int, group_id: int | None = None):
        conditions = [Student.group_id == group_id] if group_id is not None else []
        return self.repo.get_all(skip, limit, *conditions)

    def get(self, student_id: int):
        return self.repo.get_or_404(student_id)

    def update(self, student_id: int, data: StudentIn):
        student = self.repo.get_or_404(student_id)
        self._validate(data, exclude_id=student_id)
        for key, value in data.model_dump().items():
            setattr(student, key, value)
        self.repo.commit()
        return student

    def delete(self, student_id: int):
        student = self.repo.get_or_404(student_id)
        if self.repo.count_practices(student_id):
            raise ConflictError("Нельзя удалить студента: у него есть записи практики")
        self.repo.delete(student)
        self.repo.commit()
