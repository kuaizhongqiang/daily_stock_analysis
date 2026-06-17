"""dsa config — configuration management."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from ..output import JsonOutput, pass_json

# Sensitive keys that should be masked in output
SENSITIVE_KEYS = {"API_KEY", "API_KEYS", "SECRET", "TOKEN", "PASSWORD", "KEY"}


@click.group(name="config")
def config() -> None:
    """Manage configuration."""


@config.command(name="ls")
@pass_json
def list_all(json_out: JsonOutput) -> None:
    """List all configuration keys and values (secrets masked)."""
    from src.config import get_config

    cfg = get_config()
    raw: Dict[str, Any] = {}
    for key, value in vars(cfg).items():
        if value is None:
            continue
        key_upper = key.upper()
        # Mask sensitive values
        if any(s in key_upper for s in SENSITIVE_KEYS) and isinstance(value, str):
            raw[key] = value[:4] + "****" if len(value) > 4 else "****"
        else:
            raw[key] = str(value)[:200]  # Truncate long values

    json_out.ok({"config": raw})


@config.command()
@click.argument("key")
@pass_json
def get(json_out: JsonOutput, key: str) -> None:
    """Get a single configuration value."""
    import os

    from dotenv import dotenv_values

    env_path = Path(".env")
    if not env_path.exists():
        json_out.error("NOT_FOUND", ".env file not found")

    env = dotenv_values(env_path)
    value = env.get(key)
    if value is None:
        json_out.error("NOT_FOUND", f"Config key '{key}' not found")

    json_out.ok({"key": key, "value": value})


@config.command()
@click.argument("key")
@click.argument("value")
@pass_json
def set_key(json_out: JsonOutput, key: str, value: str) -> None:
    """Set a configuration value."""
    from dotenv import set_key as dotenv_set_key

    env_path = Path(".env")
    if not env_path.exists():
        json_out.error("NOT_FOUND", ".env file not found")

    dotenv_set_key(str(env_path), key, value)
    json_out.ok({"key": key, "value": value, "message": f"Set {key}={value}"})


@config.command()
@click.argument("key")
@pass_json
def unset(json_out: JsonOutput, key: str) -> None:
    """Unset/remove a configuration key."""
    json_out.ok({"key": key, "message": f"Unset {key} (not yet implemented)"})


@config.command()
@pass_json
def validate(json_out: JsonOutput) -> None:
    """Validate configuration completeness."""
    from src.config import get_config

    cfg = get_config()
    issues: List[str] = []
    if not cfg.litellm_model:
        issues.append("LITELLM_MODEL not configured")
    if not cfg.stock_list:
        issues.append("STOCK_LIST not configured")

    json_out.ok({
        "valid": len(issues) == 0,
        "issues": issues,
        "model": cfg.litellm_model,
    })
