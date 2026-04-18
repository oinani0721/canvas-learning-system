"""Config drift detection service — Story 1.11.

Compares shared variables between root .env and backend/.env,
reports mismatches, and masks sensitive values.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

SHARED_VARS = [
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "NEO4J_HTTP_PORT",
    "NEO4J_BOLT_PORT",
    "CANVAS_BASE_PATH",
    "VAULTS_ROOT",
    "ACTIVE_VAULT",
    "OLLAMA_HOST",
    "CORS_ORIGINS",
    "API_PORT",
    "DEBUG",
]

SENSITIVE_KEYS = {"NEO4J_PASSWORD", "GOOGLE_API_KEY", "AI_API_KEY", "ANTHROPIC_API_KEY"}


def _parse_env_file(path: str | Path) -> dict[str, str]:
    """Parse a .env file into a dict, ignoring comments and empty lines."""
    result: dict[str, str] = {}
    p = Path(path)
    if not p.is_file():
        return result
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        result[key] = value
    return result


def mask_sensitive(key: str, value: str) -> str:
    """Mask sensitive values: show first 2 + last 2 chars only."""
    if key not in SENSITIVE_KEYS or len(value) <= 4:
        return value
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def detect_config_drift(
    root_env: str | Path | None = None,
    backend_env: str | Path | None = None,
) -> dict[str, Any]:
    """Compare root .env vs backend/.env for shared variables.

    Returns {"drifts": [...], "synced": [...], "missing": [...]}.
    """
    if root_env is None:
        backend_dir = Path(__file__).parent.parent.parent
        root_env = backend_dir.parent / ".env"
    if backend_env is None:
        backend_dir = Path(__file__).parent.parent.parent
        backend_env = backend_dir / ".env"

    root_vals = _parse_env_file(root_env)
    backend_vals = _parse_env_file(backend_env)

    drifts = []
    synced = []
    missing = []

    for key in SHARED_VARS:
        root_v = root_vals.get(key)
        backend_v = backend_vals.get(key)

        if root_v is None and backend_v is None:
            continue

        if root_v is None:
            missing.append({"key": key, "present_in": "backend_only"})
            continue
        if backend_v is None:
            missing.append({"key": key, "present_in": "root_only"})
            continue

        if root_v != backend_v:
            effective = os.environ.get(key, root_v)
            drifts.append(
                {
                    "key": key,
                    "root": mask_sensitive(key, root_v),
                    "backend": mask_sensitive(key, backend_v),
                    "effective": mask_sensitive(key, effective),
                }
            )
        else:
            synced.append(key)

    if drifts:
        logger.warning(
            "config.drift_detected",
            drift_count=len(drifts),
            keys=[d["key"] for d in drifts],
        )

    return {"drifts": drifts, "synced": synced, "missing": missing}
