from typing import Any

from fastapi import HTTPException, Response
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.core.app_status import AppStatus


def make_error_response(app_status=AppStatus.ERROR_INTERNAL_SERVER_ERROR, detail=None):
    if detail is None:
        detail = {}

    return JSONResponse(
        status_code=app_status.status_code,
        content=jsonable_encoder({"detail": detail}),
    )


def error_exception_handler(app_status: AppStatus, data: dict| list = None):
    return HTTPException(
        status_code=app_status.status_code,
        detail={
            **app_status.meta,
            "data": data or {}
        }
    )


def handle_response(response: dict | None = None, app_status: AppStatus = AppStatus.SUCCESS):
    """Standardize API response format.

    Args:
        response (dict | None): The data to include in the response. Defaults to None.
        app_status (AppStatus): The status of the response. Defaults to AppStatus.SUCCESS.
    """

    if isinstance(response, HTTPException):
        raise response

    return JSONResponse(
        status_code=app_status.status_code,
        content=jsonable_encoder({
             **app_status.meta,
            "data": response
        })
    )
