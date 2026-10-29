from datetime import date

from sqlalchemy import select

from app.models import Practice, PracticeEntry
from app.repositories.base import BaseRepository


class PracticeRepository(BaseRepository):
    model = Practice
    entity_name = "Практика"

    def list_by_student(self, student_id: int):
        return list(self.db.scalars(select(Practice).where(Practice.student_id == student_id)).all())


class EntryRepository(BaseRepository):
    model = PracticeEntry
    entity_name = "Запись дневника"

    def get_by_date(self, practice_id: int, work_date: date):
        return self.db.scalar(
            select(PracticeEntry).where(
                PracticeEntry.practice_id == practice_id,
                PracticeEntry.work_date == work_date,
            )
        )

    def get_in_practice(self, practice_id: int, entry_id: int):
        entry = self.db.get(PracticeEntry, entry_id)
        if entry is None or entry.practice_id != practice_id:
            return None
        return entry
