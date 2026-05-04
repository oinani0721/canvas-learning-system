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

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

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
