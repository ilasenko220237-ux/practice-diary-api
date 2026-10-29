from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (регистрирует таблицы)
from app.database import Base, engine
from app.errors import register_error_handlers
from app.routers import groups, practice, students, subjects, teachers


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Колледж: учёт студентов и производственной практики",
    description=(
        "Практическая работа №8, вариант 11.\n\n"
        "Общее ядро: студенты, группы, предметы, преподаватели (CRUD).\n"
        "Дополнительно: **дневник производственной практики**, отчёт по часам "
        "`GET /api/practice/{id}/report` и правило: практика не засчитывается, "
        "если пропущено более 10% рабочих дней."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

register_error_handlers(app)

for r in (groups.router, students.router, teachers.router, subjects.router, practice.router):
    app.include_router(r)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "API работает. Документация: /docs"}
