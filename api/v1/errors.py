# -*- coding: utf-8 -*-
"""Shared helpers for API error responses — aligned with dsa/errors.py ErrorCode schema."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from dsa.errors import ErrorCode


def error_body(
    error: str,
    message: str,
    *,
    detail: Any = None,
    retryable: Optional[bool] = None,
) -> dict[str, Any]:
    """Build a unified API error body aligned with CLI/MCP error format.

    Format:
        {"error": "NOT_FOUND", "message": "...", "retryable": false, "detail": ...}
    """
    body: dict[str, Any] = {
        "error": error,
        "message": message,
    }
    if retryable is not None:
        body["retryable"] = retryable
    elif error in {e.value for e in ErrorCode}:
        # 自动推断 retryable
        err_code = ErrorCode(error)
        body["retryable"] = err_code not in {
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.NOT_FOUND,
            ErrorCode.OPERATION_REJECTED,
            ErrorCode.APPROVAL_TIMEOUT,
            ErrorCode.CONFIG_MISSING,
            ErrorCode.DUPLICATE_TASK,
        }
    else:
        body["retryable"] = False
    if detail is not None:
        body["detail"] = detail
    return body


def api_error(
    status_code: int,
    error: str,
    message: str,
    *,
    detail: Any = None,
    retryable: Optional[bool] = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=error_body(error, message, detail=detail, retryable=retryable),
    )


def error_json_response(
    status_code: int,
    error: str,
    message: str,
    *,
    detail: Any = None,
    retryable: Optional[bool] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(error, message, detail=detail, retryable=retryable),
    )
