import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


def _response(status: int, code: str, message: str, details=None) -> JSONResponse:
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return _response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        details = []
        for err in exc.errors():
            loc = [str(x) for x in err["loc"] if x not in ("body", "query", "path")]
            message = err["msg"].removeprefix("Value error, ")
            details.append({"field": ".".join(loc) or "request", "message": message})
        return _response(400, "validation_error", "Некорректные входные данные", details)

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(_: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return _response(404, "not_found", "Ресурс не найден")
        if exc.status_code == 405:
            return _response(405, "method_not_allowed", "Метод не поддерживается")
        return _response(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception):
        logger.exception("Необработанная ошибка", exc_info=exc)
        return _response(500, "internal_error", "Внутренняя ошибка сервера")


ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Некорректные данные / нарушено бизнес-правило"},
    404: {"model": ErrorResponse, "description": "Объект не найден"},
    409: {"model": ErrorResponse, "description": "Конфликт данных"},
    500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервера"},
}
