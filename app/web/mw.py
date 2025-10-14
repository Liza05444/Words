import json
import typing

from aiohttp.web_exceptions import (
    HTTPException,
    HTTPForbidden,
    HTTPUnauthorized,
    HTTPUnprocessableEntity,
)
from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware
from aiohttp_session import get_session

from app.web.mixins import AuthRequiredMixin
from app.web.utils import error_json_response

if typing.TYPE_CHECKING:
    from app.web.app import Application, Request

HTTP_ERROR_CODES: dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "not_implemented",
    409: "conflict",
    500: "internal_server_error",
}


@middleware
async def error_handling_middleware(request: "Request", handler):
    """Middleware для обработки ошибок и аутентификации."""
    try:
        path_segments = request.path[1:].split(".")
        if _should_authenticate(path_segments):
            session = await get_session(request)
            try:
                auth_data = session["auth"]
            except KeyError:
                raise HTTPUnauthorized from None
            
            auth_result = await AuthRequiredMixin.get_auth(
                role=path_segments[0], 
                user=auth_data, 
                acc=request.app.store.user_accessor
            )
            if auth_result is None:
                raise HTTPForbidden
        
        response = await handler(request)
        
    except HTTPUnprocessableEntity as e:
        return error_json_response(
            http_status=400, 
            status=HTTP_ERROR_CODES[400], 
            message=e.reason, 
            data=json.loads(e.text)
        )
    except HTTPException as e:
        return error_json_response(
            http_status=e.status, 
            status=HTTP_ERROR_CODES.get(e.status, "error"), 
            message=e.reason
        )
    except Exception as e:
        return error_json_response(
            http_status=500, 
            status=HTTP_ERROR_CODES[500], 
            message=str(e)
        )

    return response


def _should_authenticate(path_segments: list[str]) -> bool:
    """Проверка необходимости аутентификации для пути."""
    return (
        "swagger" not in path_segments[0] and 
        "docs" not in path_segments[0] and 
        path_segments[1] != "login"
    )


def configure_middlewares(app: "Application") -> None:
    """Настройка middleware для приложения."""
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(validation_middleware)
