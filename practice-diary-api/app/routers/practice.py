"""Слой Controller: дневник производственной практики (вариант 11)."""
from fastapi import APIRouter, Query, Response

from app.dependencies import PracticeServiceDep
from app.errors import ERROR_RESPONSES
from app.schemas import EntryIn, EntryOut, PracticeIn, PracticeOut, PracticeReport

router = APIRouter(prefix="/api/practice", tags=["Дневник практики"], responses=ERROR_RESPONSES)


# ---------- практика ----------
@router.post("", response_model=PracticeOut, status_code=201, summary="Открыть дневник практики")
def create_practice(data: PracticeIn, service: PracticeServiceDep):
    """Создаёт практику студента. Проверяет существование студента, предмета и руководителя,
    наличие рабочих дней в периоде и отсутствие пересечений с другими практиками студента."""
    return service.create(data)


@router.get("", response_model=list[PracticeOut], summary="Список практик")
def list_practices(
    service: PracticeServiceDep,
    student_id: int | None = Query(None, ge=1, description="Фильтр по студенту"),
    status: str | None = Query(
        None, pattern="^(in_progress|credited|not_credited)$", description="Фильтр по статусу"
    ),
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(50, ge=1, le=200, description="Максимум записей в ответе"),
):
    """Возвращает список практик с фильтрами по студенту и статусу."""
    return service.list(skip, limit, student_id, status)


@router.get("/{practice_id}", response_model=PracticeOut, summary="Получить практику по id")
def get_practice(practice_id: int, service: PracticeServiceDep):
    """Возвращает практику или 404."""
    return service.get(practice_id)


@router.put("/{practice_id}", response_model=PracticeOut, summary="Обновить практику")
def update_practice(practice_id: int, data: PracticeIn, service: PracticeServiceDep):
    """Меняет данные практики. Закрытую практику менять нельзя (409)."""
    return service.update(practice_id, data)


@router.delete("/{practice_id}", status_code=204, summary="Удалить практику вместе с дневником")
def delete_practice(practice_id: int, service: PracticeServiceDep):
    """Удаляет практику и все записи её дневника."""
    service.delete(practice_id)
    return Response(status_code=204)


# ---------- записи дневника ----------
@router.post(
    "/{practice_id}/entries",
    response_model=EntryOut,
    status_code=201,
    summary="Добавить запись в дневник за день",
)
def create_entry(practice_id: int, data: EntryIn, service: PracticeServiceDep):
    """Добавляет запись за рабочий день. Дата должна быть в периоде практики, не в будущем;
    запись за один день — только одна (иначе 409)."""
    return service.add_entry(practice_id, data)


@router.get("/{practice_id}/entries", response_model=list[EntryOut], summary="Записи дневника")
def list_entries(practice_id: int, service: PracticeServiceDep):
    """Возвращает все записи дневника практики по датам."""
    return service.list_entries(practice_id)


@router.put(
    "/{practice_id}/entries/{entry_id}",
    response_model=EntryOut,
    summary="Изменить запись дневника",
)
def update_entry(practice_id: int, entry_id: int, data: EntryIn, service: PracticeServiceDep):
    """Меняет запись дневника. В закрытой практике изменения запрещены (409)."""
    return service.update_entry(practice_id, entry_id, data)


@router.delete(
    "/{practice_id}/entries/{entry_id}", status_code=204, summary="Удалить запись дневника"
)
def delete_entry(practice_id: int, entry_id: int, service: PracticeServiceDep):
    """Удаляет запись дневника. В закрытой практике удаление запрещено (409)."""
    service.delete_entry(practice_id, entry_id)
    return Response(status_code=204)


# ---------- специфический GET и бизнес-правило ----------
@router.get(
    "/{practice_id}/report",
    response_model=PracticeReport,
    summary="Отчёт по отработанным часам",
)
def practice_report(practice_id: int, service: PracticeServiceDep):
    """Считает рабочие дни (пн–пт), отработанные и плановые часы, пропуски и % выполнения.

    **Правило:** практика не засчитывается, если пропущено более 10% рабочих дней
    (`rule_violated = true`, `credit_status = not_credited`)."""
    return service.report(practice_id)


@router.post(
    "/{practice_id}/complete",
    response_model=PracticeReport,
    summary="Закрыть практику и вынести решение (зачёт / незачёт)",
)
def complete_practice(practice_id: int, service: PracticeServiceDep):
    """Закрывает практику после даты окончания и сохраняет итоговый статус
    (`credited` или `not_credited`) по правилу «>10% пропусков»."""
    return service.complete(practice_id)
