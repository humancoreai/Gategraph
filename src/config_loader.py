"""
WHY: Single-node usability needs external configuration without introducing runtime dependencies.
INV: config loading never changes governance behavior; it only supplies explicit operator values.
SEC: malformed config fails closed before any task is evaluated.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SessionBudgetConfig:
    max_session_cost_units: int = 100
    max_session_tasks: int = 50
    max_agent_cost_units: int = 60


@dataclass(frozen=True)
class RuntimeBudgetConfig:
    max_steps: int = 20
    max_runtime_seconds: int = 300
    max_cost_units: int = 100
    repeated_action_limit: int = 3


@dataclass(frozen=True)
class FloodConfig:
    window_seconds: int = 60
    max_tasks_per_window: int = 50
    max_cost_units_per_window: int = 100


@dataclass(frozen=True)
class AppConfig:
    mode: str = "single_node"
    db_path: str = "gategraph.db"
    actor_id: str = "local-actor"
    session_id: str = "local-session"
    system_budget_units: int = 100
    actor_budget_units: int = 100
    session_budget: SessionBudgetConfig = field(default_factory=SessionBudgetConfig)
    runtime_budget: RuntimeBudgetConfig = field(default_factory=RuntimeBudgetConfig)
    flood_guard: FloodConfig = field(default_factory=FloodConfig)


def load_config(path: str | Path | None) -> AppConfig:
    if path is None:
        return AppConfig()
    raw = Path(path).read_text(encoding="utf-8")
    data = _parse_config(raw, Path(path).suffix.lower())
    return _config_from_dict(data)


def _parse_config(raw: str, suffix: str) -> dict[str, Any]:
    if suffix == ".json":
        value = json.loads(raw)
    else:
        # Minimal dependency-free YAML subset: nested mappings via indentation, scalar values only.
        value = _parse_simple_yaml(raw)
    if not isinstance(value, dict):
        raise ValueError("config root must be an object/mapping")
    return value


def _parse_simple_yaml(raw: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current_section: dict[str, Any] | None = None
    for line_no, line in enumerate(raw.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"unsupported config line {line_no}: {line!r}")
        indent = len(line) - len(line.lstrip(" "))
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if indent == 0:
            if raw_value == "":
                current_section = {}
                root[key] = current_section
            else:
                root[key] = _parse_scalar(raw_value)
                current_section = None
        elif indent == 2 and current_section is not None:
            current_section[key] = _parse_scalar(raw_value)
        else:
            raise ValueError(f"unsupported indentation at config line {line_no}")
    return root


def _parse_scalar(value: str) -> Any:
    clean = value.strip().strip('"').strip("'")
    if clean.lower() in {"true", "false"}:
        return clean.lower() == "true"
    try:
        return int(clean)
    except ValueError:
        return clean


def _config_from_dict(data: dict[str, Any]) -> AppConfig:
    mode = str(data.get("mode", "single_node"))
    if mode != "single_node":
        raise ValueError("only mode='single_node' is supported in v0.8.32")
    return AppConfig(
        mode=mode,
        db_path=str(data.get("db_path", "gategraph.db")),
        actor_id=str(data.get("actor_id", "local-actor")),
        session_id=str(data.get("session_id", "local-session")),
        system_budget_units=_positive_int(data.get("system_budget_units", 100), "system_budget_units"),
        actor_budget_units=_positive_int(data.get("actor_budget_units", 100), "actor_budget_units"),
        session_budget=SessionBudgetConfig(**_bounded_section(data.get("session_budget", {}), SessionBudgetConfig, "session_budget")),
        runtime_budget=RuntimeBudgetConfig(**_bounded_section(data.get("runtime_budget", {}), RuntimeBudgetConfig, "runtime_budget")),
        flood_guard=FloodConfig(**_bounded_section(data.get("flood_guard", {}), FloodConfig, "flood_guard")),
    )


def _bounded_section(value: Any, cls: type, name: str) -> dict[str, int]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    allowed = set(cls.__dataclass_fields__.keys())
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"unknown keys in {name}: {sorted(unknown)}")
    return {key: _positive_int(raw, f"{name}.{key}") for key, raw in value.items()}


def _positive_int(value: Any, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an integer") from None
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed
