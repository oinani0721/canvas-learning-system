"""Vault runtime API — Story 1.8 / P0-3 write-side quarantine.

POST /api/v1/vault/switch  — QUARANTINED (410): global switch retired 2026-07-31
GET  /api/v1/vault/current — return info about the active vault
GET  /api/v1/vault/list    — list candidate vaults (read-only)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import get_settings, sanitize_vault_id

logger = structlog.get_logger(__name__)

vault_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response schemas
# ═══════════════════════════════════════════════════════════════════════════════


class VaultSwitchRequest(BaseModel):
    vault_path: str = Field(..., description="Absolute path to the target vault directory")


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


# P0-3 (2026-07-31 二轮对抗审查): global vault switch 隔离退役。
# 该端点用 reload_settings 改可变全局 Settings —— vault A 的长请求
# mid-flight 会读到 vault B 路径 (端点自身 description 早已承认此竞态),
# 且文件写侧 (errors/targeting-material) 的路径解析靠同一全局, 切换中途会
# 产生「group_id 归 A、文件落 B」的 split-brain。调用方 (插件状态卡 CTA /
# 高级下拉 / MCP switch_vault) 已全部下架。vault 由部署期 .env 的
# ACTIVE_VAULT 固定 (compose 内 CANVAS_BASE_PATH=/vaults/${ACTIVE_VAULT},
# 宿主 .env 的 CANVAS_BASE_PATH 不进容器); 换 vault = 改 ACTIVE_VAULT 为
# VAULTS_ROOT 下的 vault 目录名 + docker compose up -d backend。
# 实现机器 (vault_switch_coordinator / reload_settings) 保留未删 —— 观察期
# 零命中后随 Tier B 批次物理删除。
@vault_router.post(
    "/switch",
    deprecated=True,
    summary="QUARANTINED (410) — vault fixed at deploy time via .env",
    description=(
        "P0-3 quarantine (2026-07-31): runtime global vault switch retired — "
        "it mutated global Settings, racing concurrent requests and splitting "
        "Graphiti group_id vs. file writes across vaults. To change vault: "
        "edit ACTIVE_VAULT in .env (a vault dir name under VAULTS_ROOT), "
        "then `docker compose up -d backend`."
    ),
)
async def switch_vault(request: VaultSwitchRequest) -> JSONResponse:
    logger.warning(
        "[VAULT-SWITCH-QUARANTINE] blocked runtime vault switch "
        "(P0-3 write-side isolation; see 2026-07-31 审查吸收文档)",
        vault_path=request.vault_path,
    )
    return JSONResponse(
        status_code=410,
        content={
            "error": "gone",
            "detail": (
                "Runtime vault switch is quarantined (P0-3, 2026-07-31). "
                "The active vault is fixed at deploy time: edit "
                "ACTIVE_VAULT in .env (a vault dir name under VAULTS_ROOT) "
                "and run `docker compose up -d backend` to change vault."
            ),
        },
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

    只读端点 — runtime switch 已隔离 (P0-3)，列表仅供状态展示。
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
