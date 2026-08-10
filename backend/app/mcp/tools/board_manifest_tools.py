"""RAG-S2.5 T3 (2026-08-10): get_board_manifest MCP 工具 (只读, 第 6 个白名单工具)。

照 wikilink_tools 范式: 直接读 get_settings().CANVAS_BASE_PATH (MCP 面向当前
挂载 vault, 无跨 vault 语义)。错误不抛 HTTP 异常 — MCP 消费方拿结构化
{ok, error, manifest} 自行降级 (skill 侧契约: 失败静默退回 Grep)。
"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, Field

from app.models.board_manifest import (
    ExamManifestResponse,
    StudyManifestResponse,
    project_manifest,
)
from app.services.board_manifest_service import serve_manifest

logger = logging.getLogger(__name__)


class GetBoardManifestInput(BaseModel):
    """入参全可选: 空 body = study 视图列板模式 (P16: 空 schema 防 422)。"""

    board_id: str | None = Field(
        default=None,
        description="白板 basename (如 '特征值与特征向量'); 缺省 = 列出所有白板摘要",
    )
    view: Literal["study", "exam"] = Field(
        default="study",
        description="study=学习面全字段; exam=出题安全白名单",
    )
    include_exam_history: bool = Field(default=True, description="附带检验白板历史 + 历史考题摘句")


class GetBoardManifestOutput(BaseModel):
    """结构化结果包裹: ok=False 时 error 说明原因, manifest 为空。"""

    ok: bool = True
    error: str | None = None
    manifest: StudyManifestResponse | ExamManifestResponse | None = None


async def get_board_manifest(input: GetBoardManifestInput) -> dict:
    """白板目录卡: 成员 + 派生原因 + 掌握度 + 历史考察, 一次调用替代 N 次 Grep。"""
    from app.config import get_settings

    settings = get_settings()
    try:
        raw = serve_manifest(
            settings.CANVAS_BASE_PATH,
            board_id=input.board_id,
            include_exam_history=input.include_exam_history,
            stale_after_s=settings.MANIFEST_SNAPSHOT_STALE_AFTER_S,
        )
        manifest = project_manifest(raw, input.view)
    except ValueError as e:
        return GetBoardManifestOutput(ok=False, error=f"非法参数: {e}").model_dump()
    except KeyError as e:
        detail = str(e.args[0]) if e.args else str(e)
        return GetBoardManifestOutput(ok=False, error=detail).model_dump()
    return GetBoardManifestOutput(ok=True, manifest=manifest).model_dump()
