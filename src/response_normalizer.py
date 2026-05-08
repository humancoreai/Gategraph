"""
WHY: The server API has a stable contract independent of core return shape or error path.
INV: This layer only wraps and normalizes structure; it never changes governance decisions.
SEC: Errors are code-based and do not expose internal exception details.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "0.8.35"
TOP_LEVEL_KEYS = ("ok", "data", "error", "meta")
ERROR_CODES = {
    "INVALID_JSON",
    "INVALID_CONTENT_TYPE",
    "PAYLOAD_TOO_LARGE",
    "MISSING_FIELD",
    "UNKNOWN_ENDPOINT",
    "METHOD_NOT_ALLOWED",
    "INTERNAL_ERROR",
}


def new_request_meta(stage: str, request_id: str | None = None) -> dict[str, str]:
    return {
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id or str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
    }


def success(core_result: dict[str, Any], *, stage: str = "core", request_id: str | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "data": _normalize_success_data(core_result),
        "error": None,
        "meta": new_request_meta(stage, request_id),
    }


def error(code: str, *, stage: str, request_id: str | None = None) -> dict[str, Any]:
    normalized_code = code if code in ERROR_CODES else "INTERNAL_ERROR"
    return {
        "ok": False,
        "data": None,
        "error": {"code": normalized_code},
        "meta": new_request_meta(stage, request_id),
    }


def wrap_data(data: dict[str, Any], *, stage: str, request_id: str | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "data": data,
        "error": None,
        "meta": new_request_meta(stage, request_id),
    }


def _normalize_success_data(core_result: dict[str, Any]) -> dict[str, Any]:
    reason = core_result.get("normalized_reason")
    if not isinstance(reason, dict):
        reason = {
            "risk_level": core_result.get("risk_level"),
            "risk_reason": core_result.get("risk_reason"),
            "selected_rule_id": core_result.get("selected_rule_id"),
            "matched_rule_ids": core_result.get("matched_rule_ids", []),
        }
    return {
        "decision": core_result.get("decision"),
        "stage": core_result.get("stage", "core"),
        "normalized_reason": reason,
    }


def assert_contract(payload: dict[str, Any]) -> None:
    keys = tuple(payload.keys())
    if set(keys) != set(TOP_LEVEL_KEYS):
        raise AssertionError(f"invalid top-level keys: {keys}")
    if not isinstance(payload.get("ok"), bool):
        raise AssertionError("ok must be bool")
    if payload["ok"]:
        if payload.get("error") is not None or not isinstance(payload.get("data"), dict):
            raise AssertionError("success payload must contain data and null error")
    else:
        if payload.get("data") is not None or not isinstance(payload.get("error"), dict):
            raise AssertionError("error payload must contain null data and error object")
        if set(payload["error"].keys()) != {"code"} or payload["error"]["code"] not in ERROR_CODES:
            raise AssertionError("invalid error code shape")
    meta = payload.get("meta")
    if not isinstance(meta, dict) or set(meta.keys()) != {"schema_version", "request_id", "timestamp", "stage"}:
        raise AssertionError("invalid meta shape")
