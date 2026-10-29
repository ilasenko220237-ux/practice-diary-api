"""Слой Controller: HTTP-эндпоинты студентов."""
from fastapi import APIRouter, Query, Response

from app.dependencies import StudentServiceDep
from app.errors import ERROR_RESPONSES
from app.schemas import StudentIn, StudentOut

router = APIRouter(prefix="/api/students", tags=["Студенты"], responses=ERROR_RESPONSES)


@router.post("", response_model=StudentOut, status_code=201, summary="Создать студента")
def create_student(data: StudentIn, service: StudentServiceDep):
    """Создаёт студента. Проверяются email, ФИО, дата рождения и существование группы."""
    return service.create(data)


@router.get("", response_model=list[StudentOut], summary="Список студентов")
def list_students(
    service: StudentServiceDep,
    group_id: int | None = Query(None, ge=1, description="Фильтр по группе"),
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(50, ge=1, le=200, description="Максимум записей в ответе"),
):
    """Возвращает список студентов, при необходимости — только из одной группы."""
    return service.list(skip, limit, group_id)


@router.get("/{student_id}", response_model=StudentOut, summary="Получить студента по id")
def get_student(student_id: int, service: StudentServiceDep):
    """Возвращает студента или 404, если его нет."""
    return service.get(student_id)


@router.put("/{student_id}", response_model=StudentOut, summary="Обновить студента")
def update_student(student_id: int, data: StudentIn, service: StudentServiceDep):
    """Полностью заменяет данные студента."""
    return service.update(student_id, data)


@router.delete("/{student_id}", status_code=204, summary="Удалить студента")
def delete_student(student_id: int, service: StudentServiceDep):
    """Удаляет студента. Если у него есть практики — 409."""
    service.delete(student_id)
    return Response(status_code=204)
