"""Слой Controller: HTTP-эндпоинты предметов."""
from fastapi import APIRouter, Query, Response

from app.dependencies import SubjectServiceDep
from app.errors import ERROR_RESPONSES
from app.schemas import SubjectIn, SubjectOut

router = APIRouter(prefix="/api/subjects", tags=["Предметы"], responses=ERROR_RESPONSES)


@router.post("", response_model=SubjectOut, status_code=201, summary="Создать предмет")
def create_subject(data: SubjectIn, service: SubjectServiceDep):
    """Создаёт предмет. Название уникально; teacher_id (если указан) должен существовать."""
    return service.create(data)


@router.get("", response_model=list[SubjectOut], summary="Список предметов")
def list_subjects(
    service: SubjectServiceDep,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(50, ge=1, le=200, description="Максимум записей в ответе"),
):
    """Возвращает список предметов с пагинацией."""
    return service.list(skip, limit)


@router.get("/{subject_id}", response_model=SubjectOut, summary="Получить предмет по id")
def get_subject(subject_id: int, service: SubjectServiceDep):
    """Возвращает предмет или 404, если его нет."""
    return service.get(subject_id)


@router.put("/{subject_id}", response_model=SubjectOut, summary="Обновить предмет")
def update_subject(subject_id: int, data: SubjectIn, service: SubjectServiceDep):
    """Полностью заменяет данные предмета."""
    return service.update(subject_id, data)


@router.delete("/{subject_id}", status_code=204, summary="Удалить предмет")
def delete_subject(subject_id: int, service: SubjectServiceDep):
    """Удаляет предмет. Если по нему есть практики — 409."""
    service.delete(subject_id)
    return Response(status_code=204)
