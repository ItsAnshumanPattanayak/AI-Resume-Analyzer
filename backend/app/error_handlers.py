import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


def build_error_response(
    *,
    status_code: int,
    error_type: str,
    message: Any,
) -> JSONResponse:
    """
    Build a consistent JSON error response.
    """

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
            },
        },
    )


async def http_exception_handler(
    request: Request,
    exception: HTTPException,
) -> JSONResponse:
    """
    Handle explicit FastAPI HTTP errors.
    """

    logger.warning(
        "HTTP error %s on %s %s: %s",
        exception.status_code,
        request.method,
        request.url.path,
        exception.detail,
    )

    return build_error_response(
        status_code=exception.status_code,
        error_type="http_error",
        message=exception.detail,
    )


async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    """
    Handle invalid request parameters and form fields.
    """

    logger.warning(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        exception.errors(),
    )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "type": "validation_error",
                "message": (
                    "The request contains invalid or "
                    "missing data."
                ),
                "details": exception.errors(),
            },
        },
    )


async def value_error_handler(
    request: Request,
    exception: ValueError,
) -> JSONResponse:
    """
    Handle invalid application-level input.
    """

    logger.warning(
        "Value error on %s %s: %s",
        request.method,
        request.url.path,
        exception,
    )

    return build_error_response(
        status_code=422,
        error_type="processing_error",
        message=str(exception),
    )


async def runtime_error_handler(
    request: Request,
    exception: RuntimeError,
) -> JSONResponse:
    """
    Handle unavailable models, configuration or resources.
    """

    logger.error(
        "Runtime error on %s %s: %s",
        request.method,
        request.url.path,
        exception,
    )

    return build_error_response(
        status_code=503,
        error_type="service_unavailable",
        message=str(exception),
    )


async def unexpected_exception_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """
    Handle unexpected internal errors without leaking
    sensitive implementation details.
    """

    logger.exception(
        "Unexpected error on %s %s",
        request.method,
        request.url.path,
    )

    return build_error_response(
        status_code=500,
        error_type="internal_server_error",
        message=(
            "An unexpected internal error occurred. "
            "Please try again."
        ),
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    """
    Register all centralized exception handlers.
    """

    app.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    app.add_exception_handler(
        ValueError,
        value_error_handler,
    )

    app.add_exception_handler(
        RuntimeError,
        runtime_error_handler,
    )

    app.add_exception_handler(
        Exception,
        unexpected_exception_handler,
    )