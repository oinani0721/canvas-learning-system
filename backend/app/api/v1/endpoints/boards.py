"""RAG-S2.5 T3 (2026-08-10): Board Manifest HTTP 暴露面。

⛔ 独立 prefix=/boards (router.py 注册) — 不挂 /canvas/... (wildcard 吞路由,
计划已验证事实 #8)。鉴权照 exam_sessions targeting-material 模板:
require_internal_api_key + vault_id 四步 (sanitize → build group → set subject)。

skill 侧降级契约: curl 失败静默退回 Grep — 本端点 5xx 不会破 skill 离线可用。
"""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.models.board_manifest import (
    ExamManifestResponse,
    StudyManifestResponse,
    project_manifest,
)
from app.security import require_internal_api_key
from app.services.board_manifest_service import serve_manifest

logger = logging.getLogger(__name__)

boards_router = APIRouter()


class BoardManifestRequest(BaseModel):
    """入参: vault_id 必填 (多 vault 防串), board_id=None 走列板模式。"""

    vault_id: str = Field(..., description="vault 目录名或 vault_id (服务端 sanitize)")
    subject_id: str | None = Field(default=None, description="可选学科二级 (D16 group 规约)")
    board_id: str | None = Field(
        default=None,
        description="白板 basename (如 '特征值与特征向量'); 缺省 = 列板模式",
    )
    view: Literal["study", "exam"] = Field(
        default="study",
        description="study=学习面全字段; exam=出题安全白名单 (禁项结构性缺字段)",
    )
    include_exam_history: bool = Field(default=True, description="是否附带检验白板历史 + 节点级历史考题摘句")


@boards_router.post(
    "/manifest",
    response_model=StudyManifestResponse | ExamManifestResponse,
    dependencies=[Depends(require_internal_api_key)],
    summary="RAG-S2.5 — 白板目录卡 (结构读模型, study/exam 双视图)",
)
async def get_board_manifest_http(
    req: BoardManifestRequest,
) -> StudyManifestResponse | ExamManifestResponse:
    """一次调用完整回答「白板怎么拆的」: 成员 + 派生原因 + 掌握度 + 历史考察。

    live 失败自动退 .claude/cache 快照 (source/degraded/stale 诚实标注);
    快照也无 → 200 + source_status=error + nodes=[] (不假空成功)。
    """
    import pydantic

    from app.config import get_current_vault_id, get_settings, sanitize_vault_id
    from app.core.subject_config import build_vault_group_id, set_current_subject_id

    # manifest 是文件读模型, 只能读当前挂载 vault — vault_id 不匹配即拒
    # (fail-closed 先行, 防 vault split-brain 把 A vault 的结构当 B vault 返回)
    resolved_vault = sanitize_vault_id(req.vault_id)
    current = get_current_vault_id()
    if resolved_vault != current:
        raise HTTPException(
            status_code=409,
            detail=f"vault 未激活: {resolved_vault} (当前挂载: {current}) — "
            "manifest 只读当前 vault, 不做跨 vault 文件访问",
        )
    # group 上下文仅为与 exam_sessions 模板姿势一致 (manifest 本身不读 Neo4j)
    set_current_subject_id(build_vault_group_id(resolved_vault, subject_id=req.subject_id))

    settings = get_settings()
    try:
        raw = serve_manifest(
            settings.CANVAS_BASE_PATH,
            board_id=req.board_id,
            include_exam_history=req.include_exam_history,
            stale_after_s=settings.MANIFEST_SNAPSHOT_STALE_AFTER_S,
        )
        return project_manifest(raw, req.view)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e.args[0]) if e.args else str(e)) from e
    except pydantic.ValidationError as e:
        # 纵深兜底: service 已做类型归一, 走到这说明 schema 契约被破 — 诚实
        # 500 + 日志, 绝不把未投影数据吐出去 (Code-Review H3)
        logger.error("[manifest] 投影 schema 异常: %s", e)
        raise HTTPException(status_code=500, detail="manifest 投影 schema 异常, 已记录日志") from e
