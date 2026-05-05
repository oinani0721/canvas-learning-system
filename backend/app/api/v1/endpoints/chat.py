"""Story 2.1 — POST /api/v1/chat/enrich-context endpoint.

提供 LLM 对话上下文组装的 REST 接口（plugin / Skill 都可调用）。

Plugin 的调用流程（Mode D 替代方案）：
  1. plugin 收集 current_note (path + content + frontmatter)
  2. POST 本 endpoint
  3. 拿到 enriched_context 字符串
  4. 写剪贴板 + 切 Claudian sidebar
  5. 用户粘贴 → Claude Code 直接基于已注入 context 回答

避免 Story 3.2 MCP 工具暴露的依赖（路径 A 直 REST 实施）。
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, model_validator

from app.services.chat_context_assembler import (
    ChatContextAssembler,
    CurrentNoteContext,
)
from app.services.wikilink_context_service import enrich_from_wikilink_graph

chat_router = APIRouter()


class EnrichContextRequest(BaseModel):
    node_path: str = Field(
        ...,
        description="节点 vault 相对路径（如 '节点/Eigenvalues.md'）",
        examples=["节点/Eigenvalues.md"],
    )
    current_note_content: str = Field(
        ...,
        description="节点完整 md 正文（已剥 frontmatter）",
    )
    current_note_frontmatter: dict[str, Any] = Field(
        default_factory=dict,
        description="节点 frontmatter（type / mastery_score / relationships 等)",
    )
    max_hops: int = Field(
        default=2,
        ge=1,
        le=3,
        description="wikilink graph 遍历最大跳数（默认 2）",
    )
    token_budget: int | None = Field(
        default=None,
        description="LLM token 预算（None → 默认 8192 / env CHAT_CONTEXT_TOKEN_BUDGET）",
    )
    timeout_ms: int = Field(
        default=200,
        ge=50,
        le=2000,
        description="单次 graph 遍历超时（默认 200ms 对齐 NFR-PERF）",
    )
    user_question: str | None = Field(
        default=None,
        description=(
            "（可选）用户实际问题。提供则启用 query-aware rerank（Phase 2 实施）。"
            "Hotkey 预加载场景留 None。"
        ),
    )
    mode: Literal["preload", "answer"] = Field(
        default="preload",
        description=(
            "preload = 仅装通用上下文（hotkey 触发）；"
            "answer = 用 user_question rerank（Phase 2 实施）"
        ),
    )


class TraceItemModel(BaseModel):
    """Story 2.1 P1.1 — RetrievalTrace 单条入选项（API contract）。"""

    path: str
    hop: int
    relationship_type: str | None = None
    reason: str
    tokens: int = 0


class RetrievalTraceModel(BaseModel):
    """Story 2.1 P1.1 — 检索过程结构化追踪。"""

    seed: str
    max_hops: int
    graph_version: str
    elapsed_ms: float
    included: list[TraceItemModel] = Field(default_factory=list)
    omitted: list[dict[str, Any]] = Field(default_factory=list)
    degradations: list[str] = Field(default_factory=list)


class EnrichContextResponse(BaseModel):
    enriched_context: str
    used_tokens: int
    budget: int
    assembler_budget: int = Field(
        default=0,
        description=(
            "实际分配给 assembler 的 token 预算（= budget - reserve）。"
            "用户看到的 budget 是完整额度，assembler 只能装到 assembler_budget。"
        ),
    )
    truncated: bool
    sections_included: list[str]
    neighbors_count: int
    degraded: bool
    degraded_reason: str | None = None
    enrichment_elapsed_ms: float
    retrieval_trace: RetrievalTraceModel | None = Field(
        default=None,
        description="Story 2.1 P1.1 — 结构化检索追踪（None 表示历史降级路径未填充）",
    )


@chat_router.post(
    "/enrich-context",
    response_model=EnrichContextResponse,
    status_code=status.HTTP_200_OK,
    summary="Story 2.1 — 节点对话上下文组装",
    description=(
        "调用 wikilink graph 服务获取 N-hop 邻居，"
        "按优先级填充 token 预算（公式 / 代码块保护），返回 LLM-ready 上下文字符串。"
        "AC #5: 图服务降级时返回 degraded=True + 仅当前笔记内容。"
    ),
)
async def enrich_context(req: EnrichContextRequest) -> EnrichContextResponse:
    if not req.node_path.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="node_path 不能为空",
        )

    enrichment = await enrich_from_wikilink_graph(
        node_path=req.node_path,
        max_hops=req.max_hops,
        timeout_ms=req.timeout_ms,
    )

    assembler = ChatContextAssembler(token_budget=req.token_budget)
    current_note = CurrentNoteContext(
        path=req.node_path,
        content=req.current_note_content,
        frontmatter=req.current_note_frontmatter,
    )
    assembled = assembler.assemble_context(
        current_note=current_note,
        neighbors=enrichment.neighbors,
        token_budget=req.token_budget,
        trace=enrichment.trace,
    )

    final_text = assembled.text
    if enrichment.degraded:
        final_text += (
            f"\n\n---\n邻居上下文暂时不可用（{enrichment.degraded_reason}），"
            "仅基于当前笔记回答。"
        )

    trace_model: RetrievalTraceModel | None = None
    if enrichment.trace is not None:
        trace_model = RetrievalTraceModel(
            seed=enrichment.trace.seed,
            max_hops=enrichment.trace.max_hops,
            graph_version=enrichment.trace.graph_version,
            elapsed_ms=round(enrichment.trace.elapsed_ms, 2),
            included=[
                TraceItemModel(
                    path=item.path,
                    hop=item.hop,
                    relationship_type=item.relationship_type,
                    reason=item.reason,
                    tokens=item.tokens,
                )
                for item in enrichment.trace.included
            ],
            omitted=list(enrichment.trace.omitted),
            degradations=list(enrichment.trace.degradations),
        )

    return EnrichContextResponse(
        enriched_context=final_text,
        used_tokens=assembled.used_tokens,
        budget=assembled.budget,
        assembler_budget=assembled.assembler_budget,
        truncated=assembled.truncated,
        sections_included=assembled.sections_included,
        neighbors_count=len(enrichment.neighbors),
        degraded=enrichment.degraded,
        degraded_reason=enrichment.degraded_reason,
        enrichment_elapsed_ms=round(enrichment.elapsed_ms, 2),
        retrieval_trace=trace_model,
    )


# ════════════════════════════════════════════════════════════════════════════
# Story 2.5 P0#4 fix (ChatGPT 二轮审查 2026-05-04) — Post-turn extract hook
#
# PRD §FR-CONV-06 AC #1: "对话轮次结束 → 系统自动分析对话内容, 提取学习者错误".
# 之前 Story 2.5 spec done 但缺真实 lifecycle hook (依赖 Agent 主动调
# record_error MCP tool). 本 endpoint 给 plugin / 外部对话引擎一个明确入口,
# 一次 POST 完成 提取 + 分类 + 双写 完整链路.
# ════════════════════════════════════════════════════════════════════════════


class PostTurnMessage(BaseModel):
    """对话单轮消息.

    Story 2.5 ChatGPT 三轮审查 fix (2026-05-04):
    - HIGH#2: content 加 max_length=8000 防 LLM prompt 爆炸 (DoS / 成本)
    - MEDIUM#2: role 改 str + endpoint 真过滤 (而非 422 拒绝)
    """

    role: str = Field(
        ...,
        description=(
            "对话角色. user/assistant 进入 LLM 提取链路; "
            "其他 (system/tool) 自动过滤跳过."
        ),
    )
    content: str = Field(..., min_length=1, max_length=8000)
    turn_index: int = Field(default=0)


# Story 2.5 ChatGPT round-4 HIGH#2 fix: 总字符预算 (40 × 8000 = 320k 仍可
# 打爆成本/上下文, 加 total chars cap 防过大对话整体).
MAX_TOTAL_DIALOG_CHARS = 48_000


class PostTurnExtractRequest(BaseModel):
    """Story 2.5 — 对话轮次结束后请求自动错误提取.

    Story 2.5 ChatGPT 三轮审查 HIGH#2 fix:
    - messages min_length=1 防空 + max_length=40 防超长对话历史
    Story 2.5 ChatGPT round-4 HIGH#2 fix:
    - 加 total chars budget validator (≤48000) 防 40 × 8000 总和爆炸
    """

    node_id: str = Field(..., description="Canvas 节点 ID (vault-relative path).")
    session_id: str = Field(..., description="对话 session ID.")
    messages: list[PostTurnMessage] = Field(
        ...,
        min_length=1,
        max_length=40,
        description=(
            "对话消息 (≤40 轮 + 每轮 ≤8000 字符 + 总字符 ≤48000, "
            "防 LLM 成本/上下文爆炸)."
        ),
    )
    fire_and_forget_graphiti: bool = Field(
        default=True,
        description="True → Graphiti 后台异步; False → 同步等待 Graphiti 结果.",
    )

    @model_validator(mode="after")
    def _validate_total_dialog_chars(self):
        """ChatGPT round-4 HIGH#2 fix — 总字符预算上限.

        统计**所有 role** (含 user/assistant/system/tool) — deliberate 决定:
        防止用户用 system/tool role 大 payload 绕过总预算.
        """
        total = sum(len(m.content) for m in self.messages)
        if total > MAX_TOTAL_DIALOG_CHARS:
            raise ValueError(
                f"dialog total chars {total} exceeds budget "
                f"{MAX_TOTAL_DIALOG_CHARS}"
            )
        return self


class PostTurnExtractedError(BaseModel):
    """单条提取并分类后的错误 (response 结构)."""

    error_id: Optional[str] = None
    pedagogy_type: str
    legacy_type: str
    description: str
    confidence: float
    is_ambiguous: bool
    pedagogy_remedies: list[str]
    frontmatter_written: bool
    graphiti_status: str  # queued / ok / failed / skipped_frontmatter_failed


class PostTurnExtractResponse(BaseModel):
    node_id: str
    session_id: str
    extracted_count: int
    errors: list[PostTurnExtractedError] = Field(default_factory=list)
    elapsed_ms: float


@chat_router.post(
    "/post-turn-extract",
    response_model=PostTurnExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Auto-extract errors from a completed dialog turn (Story 2.5 AC #1)",
    description=(
        "Plugin / 外部对话引擎在每轮 AI 回复完成后调用此 endpoint, "
        "传入完整 dialog messages. backend 会:\n"
        "1. 用 ErrorExtractor LLM 分析对话提取错误描述 (AC #1, #5)\n"
        "2. classify_with_pedagogy 双标签分类 (D 方案, AC #2)\n"
        "3. write_error_dual 双写 frontmatter + Graphiti (AC #4, #6)\n"
        "无错误时 errors=[] (AC #5 防 false positive)."
    ),
)
async def post_turn_extract(
    req: PostTurnExtractRequest,
) -> PostTurnExtractResponse:
    """Story 2.5 — 真实对话生命周期 hook (ChatGPT 二轮审查 P0#4 fix)."""
    import time

    from app.mcp.tools.error_tools import _resolve_node_file_path
    from app.services.error_extractor import (
        DialogMessage,
        get_error_extractor,
    )
    from app.services.error_writer import write_error_dual

    start = time.monotonic()

    extractor = get_error_extractor()
    # MEDIUM#2 fix — system/tool 自动过滤而非 422 拒绝 (与 description 一致)
    dialog = [
        DialogMessage(role=m.role, content=m.content, turn_index=m.turn_index)
        for m in req.messages
        if m.role in ("user", "assistant")
    ]
    if not dialog:
        # 全部被过滤 → 直接返回空 (AC #5)
        return PostTurnExtractResponse(
            node_id=req.node_id,
            session_id=req.session_id,
            extracted_count=0,
            errors=[],
            elapsed_ms=round((time.monotonic() - start) * 1000.0, 2),
        )

    classified = await extractor.extract_and_classify(
        dialog, node_id=req.node_id, session_id=req.session_id
    )

    file_path = _resolve_node_file_path(req.node_id)
    out_errors: list[PostTurnExtractedError] = []
    for err in classified:
        if file_path:
            # Story 2.5.X (D15=C+) 兼容: 显式 mode="write_confirmed" 保留 v1.0 行为
            # (write_error_dual 默认改为 candidate_only, post-turn-extract 在 Task 5 切到 candidate_only)
            dual = await write_error_dual(
                file_path=file_path,
                error=err,
                node_id=req.node_id,
                session_id=req.session_id,
                fire_and_forget_graphiti=req.fire_and_forget_graphiti,
                mode="write_confirmed",
            )
            fm_ok = dual["frontmatter"]
            graphiti_status = dual["graphiti"]
            err_id = dual.get("error_id")
        else:
            # MEDIUM#3 + round-4 fix (ChatGPT): file_path 不可解析时仍尝试
            # Graphiti-only, 但**遵守** fire_and_forget_graphiti flag
            # (上轮漏修: Graphiti-only fallback 永远同步等, 与 flag 语义不一致).
            import asyncio as _asyncio
            import uuid as _uuid

            from app.services.error_writer import write_error_to_graphiti

            err_id = str(_uuid.uuid4())
            fm_ok = False
            if req.fire_and_forget_graphiti:
                _asyncio.create_task(
                    write_error_to_graphiti(
                        err, req.node_id, req.session_id, error_id=err_id
                    )
                )
                graphiti_status = "queued"
            else:
                graphiti_ok = await write_error_to_graphiti(
                    err, req.node_id, req.session_id, error_id=err_id
                )
                graphiti_status = "ok" if graphiti_ok else "failed"

        out_errors.append(
            PostTurnExtractedError(
                error_id=err_id,
                pedagogy_type=err.pedagogy_type.value,
                legacy_type=err.legacy_type.value,
                description=err.description,
                confidence=err.confidence,
                is_ambiguous=err.is_ambiguous,
                pedagogy_remedies=[r.value for r in err.pedagogy_remedies],
                frontmatter_written=fm_ok,
                graphiti_status=graphiti_status,
            )
        )

    elapsed_ms = (time.monotonic() - start) * 1000.0
    return PostTurnExtractResponse(
        node_id=req.node_id,
        session_id=req.session_id,
        extracted_count=len(out_errors),
        errors=out_errors,
        elapsed_ms=round(elapsed_ms, 2),
    )
