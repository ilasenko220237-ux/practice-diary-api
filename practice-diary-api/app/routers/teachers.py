"""Слой Controller: HTTP-эндпоинты преподавателей."""
from fastapi import APIRouter, Query, Response

from app.dependencies import TeacherServiceDep
from app.errors import ERROR_RESPONSES
from app.schemas import TeacherIn, TeacherOut

router = APIRouter(prefix="/api/teachers", tags=["Преподаватели"], responses=ERROR_RESPONSES)


@router.post("", response_model=TeacherOut, status_code=201, summary="Создать преподавателя")
def create_teacher(data: TeacherIn, service: TeacherServiceDep):
    """Создаёт преподавателя. Email должен быть уникальным."""
    return service.create(data)


@router.get("", response_model=list[TeacherOut], summary="Список преподавателей")
def list_teachers(
    service: TeacherServiceDep,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(50, ge=1, le=200, description="Максимум записей в ответе"),
):
    """Возвращает список преподавателей с пагинацией."""
    return service.list(skip, limit)


@router.get("/{teacher_id}", response_model=TeacherOut, summary="Получить преподавателя по id")
def get_teacher(teacher_id: int, service: TeacherServiceDep):
    """Возвращает преподавателя или 404, если его нет."""
    return service.get(teacher_id)


@router.put("/{teacher_id}", response_model=TeacherOut, summary="Обновить преподавателя")
def update_teacher(teacher_id: int, data: TeacherIn, service: TeacherServiceDep):
    """Полностью заменяет данные преподавателя."""
    return service.update(teacher_id, data)


@router.delete("/{teacher_id}", status_code=204, summary="Удалить преподавателя")
def delete_teacher(teacher_id: int, service: TeacherServiceDep):
    """Удаляет преподавателя. Если он привязан к предметам или практикам — 409."""
    service.delete(teacher_id)
    return Response(status_code=204)
