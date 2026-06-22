# -*- coding: utf-8 -*-
"""Tests for shared API error helpers."""

from fastapi import HTTPException

from api.v1.errors import api_error, error_body, error_json_response


def test_error_body_includes_retryable_field() -> None:
    """error_body() 现在包含 retryable 字段（与 CLI/MCP 格式对齐）。"""
    body = error_body("validation_error", "bad input")
    assert body["error"] == "validation_error"
    assert body["message"] == "bad input"
    assert body["retryable"] is False


def test_api_error_uses_standard_detail_shape() -> None:
    exc = api_error(404, "not_found", "missing", detail={"id": 1})

    assert isinstance(exc, HTTPException)
    assert exc.status_code == 404
    assert exc.detail["error"] == "not_found"
    assert exc.detail["message"] == "missing"
    assert exc.detail["detail"] == {"id": 1}
    assert exc.detail["retryable"] is False


def test_error_json_response_includes_retryable() -> None:
    response = error_json_response(409, "conflict", "already exists")

    assert response.status_code == 409
    import json
    body = json.loads(response.body)
    assert body["error"] == "conflict"
    assert body["message"] == "already exists"
    assert body["retryable"] is False
