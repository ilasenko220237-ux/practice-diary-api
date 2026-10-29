"""Слой Controller: HTTP-эндпоинты групп."""
from fastapi import APIRouter, Query, Response

from app.dependencies import GroupServiceDep
from app.errors import ERROR_RESPONSES
from app.schemas import GroupIn, GroupOut

router = APIRouter(prefix="/api/groups", tags=["Группы"], responses=ERROR_RESPONSES)


@router.post("", response_model=GroupOut, status_code=201, summary="Создать группу")
def create_group(data: GroupIn, service: GroupServiceDep):
    """Создаёт группу. Название группы должно быть уникальным (иначе 409)."""
    return service.create(data)


@router.get("", response_model=list[GroupOut], summary="Список групп")
def list_groups(
    service: GroupServiceDep,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(50, ge=1, le=200, description="Максимум записей в ответе"),
):
    """Возвращает список групп с пагинацией."""
    return service.list(skip, limit)


@router.get("/{group_id}", response_model=GroupOut, summary="Получить группу по id")
def get_group(group_id: int, service: GroupServiceDep):
    """Возвращает группу или 404, если её нет."""
    return service.get(group_id)


@router.put("/{group_id}", response_model=GroupOut, summary="Обновить группу")
def update_group(group_id: int, data: GroupIn, service: GroupServiceDep):
    """Полностью заменяет данные группы."""
    return service.update(group_id, data)


@router.delete("/{group_id}", status_code=204, summary="Удалить группу")
def delete_group(group_id: int, service: GroupServiceDep):
    """Удаляет группу. Если в группе есть студенты — 409."""
    service.delete(group_id)
    return Response(status_code=204)
