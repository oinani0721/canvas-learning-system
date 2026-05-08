"""Vault switch runtime API — Story 1.8.

POST /api/v1/vault/switch  — switch to a different Obsidian vault
GET  /api/v1/vault/current — return info about the active vault
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings, reload_settings, sanitize_vault_id
from app.services.vault_switch_coordinator import vault_switch_coordinator

logger = structlog.get_logger(__name__)

vault_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response schemas
# ═══════════════════════════════════════════════════════════════════════════════


class VaultSwitchRequest(BaseModel):
    vault_path: str = Field(
        ..., description="Absolute path to the target vault directory"
    )


class VaultSwitchResponse(BaseModel):
    vault_path: str
    vault_name: str
    vault_id: str
    switched_at: float
    previous_vault: Optional[str] = None
    duration_ms: float


class VaultCurrentResponse(BaseModel):
    vault_path: str
    vault_name: str
    vault_id: str
    vaults_root: str


class VaultInfo(BaseModel):
    name: str
    path: str
    vault_id: str
    is_active: bool


class VaultListResponse(BaseModel):
    vaults_root: str
    active_vault: str
    vaults: list[VaultInfo]


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@vault_router.post("/switch", response_model=VaultSwitchResponse)
async def switch_vault(request: VaultSwitchRequest):
    """Switch the active vault at runtime (Story 1.8 AC #1, #2, #4, #6)."""
    vault_path = Path(request.vault_path).resolve()

    # AC #2: validate path exists and is an Obsidian vault
    if not vault_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "vault_not_found",
                "message": f"Directory does not exist: {vault_path}",
            },
        )

    obsidian_dir = vault_path / ".obsidian"
    if not obsidian_dir.is_dir():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "vault_not_found",
                "message": f"Not an Obsidian vault (missing .obsidian/): {vault_path}",
            },
        )

    # AC #6: reject if another switch is in progress
    if vault_switch_coordinator.is_switching:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "switch_in_progress",
                "message": "Another vault switch is in progress",
            },
        )

    vault_name = vault_path.name

    async def perform_switch() -> None:
        # AC #4: clear lru_cache and inject new path
        reload_settings(
            overrides={
                "CANVAS_BASE_PATH": str(vault_path),
                "ACTIVE_VAULT": vault_name,
            }
        )

    result = await vault_switch_coordinator.switch(
        new_vault_path=str(vault_path),
        new_vault_name=vault_name,
        perform_switch=perform_switch,
    )

    return VaultSwitchResponse(
        vault_path=result["vault_path"],
        vault_name=result["vault_name"],
        vault_id=sanitize_vault_id(vault_name),
        switched_at=result["switched_at"],
        previous_vault=result["previous_vault"],
        duration_ms=result["duration_ms"],
    )


@vault_router.get("/current", response_model=VaultCurrentResponse)
async def get_current_vault():
    """Return info about the currently active vault (Story 1.8 AC #3)."""
    s = get_settings()
    return VaultCurrentResponse(
        vault_path=s.CANVAS_BASE_PATH,
        vault_name=s.ACTIVE_VAULT,
        vault_id=s.vault_id,
        vaults_root=s.VAULTS_ROOT,
    )


@vault_router.get("/list", response_model=VaultListResponse)
async def list_vaults():
    """List all candidate Obsidian vaults under VAULTS_ROOT.

    扫描 VAULTS_ROOT 下所有含 .obsidian/ 子目录的目录作为 vault 候选。
    返回列表供前端 (plugin Settings) 渲染 vault selector dropdown。

    支持用户主动切换 active vault（配合 POST /api/v1/vault/switch）。
    """
    s = get_settings()
    vaults_root = Path(s.VAULTS_ROOT).resolve()
    active_vault_path = Path(s.CANVAS_BASE_PATH).resolve()

    if not vaults_root.is_dir():
        raise HTTPException(
            status_code=500,
            detail={
                "error": "vaults_root_invalid",
                "message": f"VAULTS_ROOT not a directory: {vaults_root}",
            },
        )

    candidates: list[VaultInfo] = []
    try:
        for entry in sorted(vaults_root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("."):
                continue  # 跳过隐藏目录（.git / .vscode 等）
            if not (entry / ".obsidian").is_dir():
                continue  # 不是 Obsidian vault
            entry_resolved = entry.resolve()
            candidates.append(
                VaultInfo(
                    name=entry.name,
                    path=str(entry_resolved),
                    vault_id=sanitize_vault_id(entry.name),
                    is_active=(entry_resolved == active_vault_path),
                )
            )
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "vaults_root_scan_failed",
                "message": f"Failed to scan VAULTS_ROOT: {e}",
            },
        )

    return VaultListResponse(
        vaults_root=str(vaults_root),
        active_vault=s.ACTIVE_VAULT,
        vaults=candidates,
    )
