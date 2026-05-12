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

import asyncio
from pathlib import Path
from typing import Any, Literal, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator

from app.security import require_internal_api_key
from app.services.chat_context_assembler import (
    ChatContextAssembler,
    CurrentNoteContext,
)
from app.services.supplementary_search_service import (
    format_supplementary_xml,
    search_supplementary,
)
from app.services.wikilink_context_service import enrich_from_wikilink_graph

logger = structlog.get_logger(__name__)

# Phase A0.5-L (Round-4 ChatGPT V3 + cross-check confirmed P0 安全 bug):
# 旧: chat_router 完全无鉴权 → 任何本地进程可 POST 注入 Claude additionalContext
# 新: 全 chat router 加 require_internal_api_key 全局 dependency
# fail-closed 矩阵:
#   - DEBUG=True + key 未配置 → allow + warning log (dev 透明，不破坏现有 plugin/hook)
#   - DEBUG=False + key 未配置 → 503 (强制 ops 配置)
#   - DEBUG=False + key 配置 + header 不匹配 → 403
# Phase A1 计划: plugin 与 settings.json hook 加 X-CLS-Internal-Key header,
#               然后切到 production 模式 (DEBUG=False)
chat_router = APIRouter(dependencies=[Depends(require_internal_api_key)])

# Story 2.2 Phase A — module-level LanceDBClient singleton + lock
# 每个 endpoint call 之前 get_lancedb_client() 都 new instance → BGEM3 model 每次重加载 60s+
# Module singleton 让 client 跨请求复用 — first request cold-start，subsequent warm
_supp_lancedb_singleton: Any = None
_supp_init_lock: asyncio.Lock | None = None


async def _get_supp_lancedb_client(init_timeout: float = 30.0) -> Any:
    """获取或懒初始化 module-level LanceDBClient singleton（Story 2.2 Phase A 优化）。

    First request 路径: init_timeout=30s（不 block 用户主对话太久）
    Backend startup eager init 路径: init_timeout=600s（4 min BGEM3 cold-start 留余）

    First call: 触发 BGEM3 model 加载，cache 到全局
    Subsequent: 复用 cached client，避免重复 init
    """
    global _supp_lancedb_singleton, _supp_init_lock
    if _supp_lancedb_singleton is not None:
        return _supp_lancedb_singleton
    if _supp_init_lock is None:
        _supp_init_lock = asyncio.Lock()
    async with _supp_init_lock:
        if _supp_lancedb_singleton is not None:
            return _supp_lancedb_singleton
        from app.api.v1.endpoints.metadata import get_lancedb_client

        client = get_lancedb_client()
        if client is None:
            return None
        if hasattr(client, "_initialized") and not client._initialized:
            try:
                await asyncio.wait_for(client.initialize(), timeout=init_timeout)
            except asyncio.TimeoutError:
                logger.warning(
                    "[Story-2.2-PhaseA] LanceDBClient init timeout — singleton not cached",
                    timeout=init_timeout,
                )
                return None
        _supp_lancedb_singleton = client
        logger.info("[Story-2.2-PhaseA] LanceDBClient singleton 缓存就绪")
        return _supp_lancedb_singleton


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
    mode: Literal["preload", "answer", "deep"] = Field(
        default="preload",
        description=(
            "preload = 仅装通用上下文（hotkey 预加载）；"
            "answer = 用 user_question rerank（Cmd+Shift+E 快问快答，"
            "top_k_max=20 / hard_cap=15）；"
            "deep = Story 2.3 study-question 解题深度模式（Cmd+Shift+Q，"
            "top_k_max=30 / hard_cap=20，预算 30-45s）"
        ),
    )
    # Multi-vault P0-1 (2026-05-10) — vault_id 必填，注入 ContextVar 防 5 vault 串库。
    # 参考 PostTurnExtractRequest (Story 2.5.Y AC #2) 已建立的必填契约。
    # Plugin 用 inferVaultId(app.vault.getName()) 取 raw vault name；backend 端
    # 调 sanitize_vault_id 标准化（NFKC + casefold + Unicode \w）后再 build group_id。
    vault_id: str = Field(
        ...,
        min_length=1,
        description=(
            "当前 active vault 标识符（plugin 端 app.vault.getName() 或 "
            ".canvas-config.yaml 的 vault_id 字段）。Backend 用 sanitize_vault_id "
            "标准化后调 build_vault_group_id → set_current_subject_id 注入 ContextVar，"
            "让 downstream wikilink/lancedb/supplementary 都看到同一 vault_id。"
            "5 vault 共存时多请求并发不互相串库。"
        ),
        examples=["cs_61b", "数学", "Physics 101"],
    )
    subject_id: str | None = Field(
        default=None,
        description=(
            "（可选）vault 内学科二级 namespace。一 vault 一学科时留 None，"
            "build_vault_group_id 自动 fallback 到默认。"
        ),
    )


class TraceItemModel(BaseModel):
    """Story 2.1 P1.1 — RetrievalTrace 单条入选项（API contract）。

    Story 2.2+2.9 T3.8 (2026-05-11) — rerank 4 字段加为 optional，让 API contract
    前瞻包含 wikilink 邻居 rerank 维度 (本 iteration 仅 supplementary 走 rerank,
    neighbor rerank 留待下一 Phase 接入,届时 ChatContextAssembler 回填这 4 字段).

    Story 2.2+2.9 T5.1 (2026-05-11) — Relationship Evidence (AC #6):
    evidence: frontmatter relationships[].evidence 字段, 让外部书目/公式锚点
    跨过 prompt 进入 Claude 视野 (e.g. "see eq. 3.2 in Strang").
    """

    path: str
    hop: int
    relationship_type: str | None = None
    reason: str
    tokens: int = 0
    rerank_score: float | None = None
    type_weight: float | None = None
    hub_penalty: float | None = None
    query_overlap: float | None = None
    evidence: str | None = None


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
    supplementary_count: int = Field(
        default=0,
        description=(
            "Story 2.2 Phase A — 注入到 enriched_context 的补充材料数量。"
            "0 = 降级 / 空索引 / preload 模式未触发搜索。"
        ),
    )
    supplementary_degraded: bool = Field(
        default=False,
        description="Story 2.2 Phase A — 补充搜索是否降级（True 表示外部因素失败，主对话仍正常）。",
    )
    supplementary_reason: str | None = Field(
        default=None,
        description=(
            "Story 2.2 Phase A — 降级或空结果原因（lancedb_unavailable / search_failed: ... / "
            "empty_index / empty_query / all_filtered_below_threshold）。"
        ),
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

    # Multi-vault P0-1 (2026-05-10) — 注入 ContextVar 防 5 vault 串库。
    # Plugin 传 raw vault name (inferVaultId(app.vault.getName()))；
    # backend 用 sanitize_vault_id 标准化（NFKC + casefold + Unicode \w）→
    # build_vault_group_id 构造 group_id (vault:<sanitized>:<subject>) →
    # set_current_subject_id 写 ContextVar，让 downstream 各 service
    # (wikilink_graph_service / lancedb_client / supplementary_search) 都
    # 通过 get_current_subject_id() 拿到同一 vault_id，5 vault 并发不互相串库。
    # 参考 PostTurnExtractRequest (Story 2.5.Y AC #2) 已建立的契约。
    from app.config import sanitize_vault_id
    from app.core.subject_config import build_vault_group_id, set_current_subject_id

    sanitized_vault_id = sanitize_vault_id(req.vault_id)
    derived_group_id = build_vault_group_id(
        sanitized_vault_id,
        subject_id=req.subject_id,
        canvas_path=req.node_path,
    )
    set_current_subject_id(derived_group_id)

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

    # Story 2.2 Phase A + Story 2.3 v1.0 — PRD §4.1.1 9-step workflow Step 5: 补充材料搜索
    # mode=preload (hotkey 触发，未提问) 跳过；
    # mode=answer 用快问快答参数（top_k_max=20 / hard_cap=15）；
    # mode=deep 用解题深度参数（top_k_max=30 / hard_cap=20，30-45s 预算）
    supp_count = 0
    supp_degraded = False
    supp_reason: str | None = None
    if (
        req.mode in ("answer", "deep")
        and req.user_question
        and req.user_question.strip()
    ):
        # Story 2.3 v1.0 — deep mode 加大召回。设计 §4.3 关键参数对比：
        # answer (5s)  → top_k_max=20 / hard_cap=15
        # deep   (30s) → top_k_max=30 / hard_cap=20
        # Claude 200K context 用 Read tool 在内部交叉验证（verifier 分离原则）
        if req.mode == "deep":
            supp_top_k_max = 30
            supp_hard_cap = 20
        else:
            supp_top_k_max = 20
            supp_hard_cap = 15

        try:
            # P0-C (2026-05-12 hotfix): 冷启 30s 内 singleton 仍 None,
            # 直接读会立即 fallback lancedb_unavailable, 用户冷启首问也拿不到补充材料.
            # 改走 lazy init 路径 (5s budget) — 若已 ready 立即返回, 未 ready 时
            # 给 5s 窗口尝试触发 init (init 真要 60s+ 走 timeout 自然降级).
            # 5s 是 hook/answer 模式延迟预算的合理上限.
            lancedb_client = await _get_supp_lancedb_client(init_timeout=5.0)
            node_title = Path(req.node_path).stem
            supp_query = f"{node_title} {req.user_question}".strip()
            supp_result = await search_supplementary(
                query=supp_query,
                lancedb_client=lancedb_client,
                # 2026-05-09 RAG-as-tool 范式重构：用户原话"不硬编码 5 条，把有用的都提供"
                # → top_k_max 大召回 + elbow_cut 动态截断（业界推荐 vs 硬编码 top_k）
                # → Claude 用 Read tool 真核实是 verifier（candidate generator + verifier 分离）
                top_k_max=supp_top_k_max,
                min_relevance=0.30,  # RRF 实测分布，Phase B sigmoid 归一化后恢复 0.70
                elbow_drop_threshold=0.05,
                hard_cap=supp_hard_cap,
            )
            # Story 2.2+2.9 T3.7-T3.10 (2026-05-11) — query-aware rerank
            # final_score = relevance × type_weight + query_overlap × 0.3 - hub_penalty
            # 顺序: score → sort → filter(0.42) → truncate(top 5)
            from app.services.supplementary_reranker import (
                get_filter_threshold,
                rerank,
            )
            from app.services.wikilink_graph_service import (
                get_wikilink_graph_service,
            )

            graph_svc = get_wikilink_graph_service()
            if graph_svc.is_built:
                degree_stats = graph_svc.get_degree_stats()
                median_degree = float(degree_stats.get("median", 0.0))
                # 用 source_path 反查 degree (best-effort, basename fallback 已内置)
                for m in supp_result.get("materials", []):
                    sp = m.get("source_path", "")
                    if sp:
                        m["degree"] = graph_svc.get_degree(sp)
            else:
                median_degree = 0.0

            pre_rerank_count = len(supp_result.get("materials", []))
            supp_result["materials"] = rerank(
                supp_result.get("materials", []),
                query=req.user_question,
                median_degree=median_degree,
                min_score_threshold=get_filter_threshold(),
                top_k=5,
            )
            post_rerank_count = len(supp_result["materials"])
            logger.info(
                "[Story-2.2+2.9-T3] rerank 完成",
                pre=pre_rerank_count,
                post=post_rerank_count,
                filter_threshold=round(get_filter_threshold(), 3),
                median_degree=median_degree,
                query=req.user_question[:60] if req.user_question else None,
            )

            supp_xml = format_supplementary_xml(supp_result)
            final_text += "\n\n" + supp_xml
            supp_count = len(supp_result.get("materials", []))
            supp_degraded = supp_result.get("degraded", False)
            supp_reason = supp_result.get("reason")
            logger.info(
                "[Story-2.2-PhaseA] supplementary 注入完成",
                count=supp_count,
                degraded=supp_degraded,
                reason=supp_reason,
                query=supp_query[:80],
            )
        except Exception as e:  # noqa: BLE001  Task 4 降级铁律：主对话不受补充搜索失败影响
            logger.warning(
                "[Story-2.2-PhaseA] supplementary 异常降级",
                error=str(e)[:120],
                node_path=req.node_path,
            )
            supp_degraded = True
            supp_reason = f"unexpected: {str(e)[:80]}"

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
                    evidence=getattr(item, "evidence", None),
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
        supplementary_count=supp_count,
        supplementary_degraded=supp_degraded,
        supplementary_reason=supp_reason,
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
    # Story 2.5.Y AC #1 — vault_id 必填 (multi-vault 隔离强制)
    vault_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Vault stable identifier (Story 2.5.Y multi-vault 隔离强制). "
            "如 'cs_61b' / '数学'. 缺失 → 422."
        ),
    )
    subject_id: Optional[str] = Field(
        default=None,
        description="Story 2.5.Y AC #1 — 可选 subject 二级隔离 (优先级 > canvas_path).",
    )
    canvas_path: Optional[str] = Field(
        default=None,
        description="Story 2.5.Y AC #1 — 可选 canvas/board 名 (subject_id 为空时使用).",
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
                f"dialog total chars {total} exceeds budget {MAX_TOTAL_DIALOG_CHARS}"
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
    """Story 2.5 — 真实对话生命周期 hook (ChatGPT 二轮审查 P0#4 fix).

    Story 2.5.Y AC #2: 入口注入 group_id 到 ContextVar (复用 SubjectConfig).
    所有下游 service 通过 get_current_subject_id() 获取当前请求的 group_id.
    """
    import time

    # Story 2.5.Y Task 2 — 注入 ContextVar (vault_id 是必填, Pydantic 已校验)
    from app.core.subject_config import build_vault_group_id, set_current_subject_id

    derived_group_id = build_vault_group_id(
        req.vault_id, subject_id=req.subject_id, canvas_path=req.canvas_path
    )
    set_current_subject_id(derived_group_id)

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


# ════════════════════════════════════════════════════════════════════════════
# 2026-05-09 Story 2.2 Phase A T1.7 — UserPromptSubmit hook auto-RAG injection
# 用户原话: "对话过程中天然有很多次相关知识点返回，不要每次按快捷键"
# 设计: Claude Code SDK UserPromptSubmit hook (Anthropic 钦定模式)
# - 用户在 Claudian 内每次 user message 时，SDK 自动调本 endpoint
# - endpoint 调 search_supplementary 拿 vault wikilink 候选
# - 返回 {hookSpecificOutput.additionalContext} → SDK 自动 prepend 到 system context
# - Claude 拿到 supplementary XML 后用 Read tool 真核实再回答（commit 98dbc2d 约束）
# ════════════════════════════════════════════════════════════════════════════


class HookEnrichRequest(BaseModel):
    """Claude Code UserPromptSubmit hook stdin payload."""

    session_id: str | None = None
    transcript_path: str | None = None
    cwd: str | None = None
    hook_event_name: str | None = None
    prompt: str = ""

    class Config:
        extra = "ignore"  # 容忍 Claude Code SDK 后续添加新字段


class HookEnrichOutput(BaseModel):
    """Claude Code hook output (additionalContext 会被 prepend 到 system context)."""

    hookSpecificOutput: dict[str, Any]


@chat_router.post(
    "/rag/enrich-hook",
    response_model=HookEnrichOutput,
    summary="UserPromptSubmit hook — 自动 RAG 注入到 Claudian 每次对话",
)
async def rag_enrich_hook(req: HookEnrichRequest) -> HookEnrichOutput:
    """每次 Claudian 内用户提问时被 SDK 自动调，注入 supplementary 到 system context.

    设计要点:
    - 短 prompt (< 5 char) 跳过（避免 "hi" 之类无意义触发）
    - LanceDB singleton 未 ready → 静默跳过 (不阻塞用户对话)
    - 5s timeout 内 supplementary 拿不到 → 静默跳过
    - 0 命中 → 不注入（保持对话简洁，避免 spam）
    - 命中 N 条 → 注入 anchor instruction + supplementary XML
    """
    user_prompt = (req.prompt or "").strip()
    if len(user_prompt) < 5:
        return HookEnrichOutput(
            hookSpecificOutput={
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "",
            }
        )

    # 复用 chat.py module-level singleton (commit 5dfad13 endpoint 不 acquire lock)
    lancedb_client = _supp_lancedb_singleton
    if lancedb_client is None:
        # singleton 还在 background eager-init，本次跳过
        logger.debug(
            "[T1.7-AutoRAG] lancedb singleton not ready, skip injection",
            prompt=user_prompt[:60],
        )
        return HookEnrichOutput(
            hookSpecificOutput={
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "",
            }
        )

    try:
        supp_result = await asyncio.wait_for(
            search_supplementary(
                query=user_prompt,
                lancedb_client=lancedb_client,
                top_k_max=15,
                min_relevance=0.30,
                elbow_drop_threshold=0.05,
                hard_cap=10,
            ),
            timeout=5.0,  # hook 严格延迟预算
        )
    except asyncio.TimeoutError:
        logger.debug("[T1.7-AutoRAG] timeout 5s, skip", prompt=user_prompt[:60])
        return HookEnrichOutput(
            hookSpecificOutput={
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "",
            }
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[T1.7-AutoRAG] search exception", error=str(e)[:120])
        return HookEnrichOutput(
            hookSpecificOutput={
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "",
            }
        )

    materials = supp_result.get("materials", [])
    if not materials:
        # 0 命中（vault 无相关材料）→ 不注入（避免对话 spam）
        return HookEnrichOutput(
            hookSpecificOutput={
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "",
            }
        )

    supp_xml = format_supplementary_xml(supp_result)

    anchor_instruction = (
        "⛔ Canvas Auto-RAG (UserPromptSubmit hook 自动注入):\n"
        "用户在 Canvas vault 内提问时，下方 <supplementary_materials> 是 vault 内"
        "可能相关的笔记片段。回答时必须遵循:\n"
        "(1) 必须先用 Read tool 实际读 top 2-3 条 <source_path> 完整文件，"
        "禁止仅凭 snippet 编内容\n"
        "(2) 回答正文必须含 ≥1 个 [[file#具体heading]] 精度 wikilink 作 inline evidence\n"
        "(3) heading anchor 必须字面保留（含视频 timestamp [01:05:34]() 残留）"
        "供 Obsidian 字面匹配跳转\n"
        "(4) Read 失败/文件空 → 跳过该条 + 标 (read_failed=<reason>)\n"
        "(5) 禁止凭训练数据答 vault 含的课程材料问题\n"
        "(6) 末尾 `---` 分隔后展示完整 supplementary 列表便于跳转\n\n"
    )
    additional_context = anchor_instruction + supp_xml

    logger.info(
        "[T1.7-AutoRAG] supplementary auto-injected",
        prompt=user_prompt[:60],
        materials=len(materials),
        bytes=len(additional_context),
    )

    return HookEnrichOutput(
        hookSpecificOutput={
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context,
        }
    )


# ════════════════════════════════════════════════════════════════════════════
# Story 2.2+2.9 Global-Search (2026-05-12) — POST /chat/global-search
#
# 用户需求: "不在任何节点也能全局搜索教学笔记".
# 设计:
#   - 不依赖 node_path 上下文 (Cmd palette / 主对话框直接发问)
#   - 直接走 supplementary_search (vault 全域 LanceDB) + rerank(median_degree=0)
#   - 无 graph context, 无 wikilink neighbor, 纯 RAG-as-tool 候选池
#   - 返回 enriched_context 顶部带 manifest 让 Claude 看到来源
#   - 失败全降级 (主对话不阻断, 与 enrich-context body P0-C 同款防护)
# ════════════════════════════════════════════════════════════════════════════


class GlobalSearchRequest(BaseModel):
    """全局搜索请求 — 不依赖 node_path, vault 全域 RAG.

    复用 enrich-context 的 vault 隔离契约 (sanitize_vault_id + build_vault_group_id
    → ContextVar 注入), 让 downstream supplementary_search 看到正确的 vault_id.
    """

    user_question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户问题 (e.g. 求解 Linear Independence 的方法)",
    )
    vault_id: str = Field(
        ...,
        min_length=1,
        description=(
            "当前 active vault 标识 (plugin app.vault.getName() 或 yaml vault_id). "
            "Backend 用 sanitize_vault_id 标准化 → build_vault_group_id → "
            "set_current_subject_id 注入 ContextVar, 5 vault 并发不互串."
        ),
    )
    subject_id: str | None = Field(
        default=None,
        description="可选 subject 二级 namespace (一 vault 一学科时留 None).",
    )
    top_k_max: int = Field(
        default=30,
        ge=5,
        le=50,
        description=(
            "supplementary 召回上限 (默认 30, 对齐 study-question deep mode). "
            "_two_tier_search 内部会取 top_k_max × 1.5 作 buffer."
        ),
    )
    hard_cap: int = Field(
        default=20,
        ge=3,
        le=30,
        description="即使 elbow 不触发, 最多返回此数量 (保护 prompt 长度).",
    )


class GlobalSearchResponse(BaseModel):
    enriched_context: str = Field(
        ...,
        description=(
            "manifest + supplementary_materials XML 拼接, Claude 可直接读. "
            "0 命中时 enriched_context 仅含 manifest + 空提示."
        ),
    )
    supplementary_count: int = Field(
        default=0,
        description="入选 supplementary 材料数量 (0 = 空 vault / 全部低于阈值).",
    )
    supplementary_degraded: bool = Field(
        default=False,
        description="True = 外部因素失败 (lancedb_unavailable / search_failed / timeout).",
    )
    supplementary_reason: str | None = Field(
        default=None,
        description=(
            "降级或空结果原因 (lancedb_unavailable / search_failed / empty_index / "
            "empty_query / all_filtered_below_threshold / unexpected_error: ...)."
        ),
    )
    elapsed_ms: float = Field(..., description="端到端耗时 (ms).")


@chat_router.post(
    "/global-search",
    response_model=GlobalSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Story 2.2+2.9 — 不依赖节点的 vault 全域 RAG 搜索",
    description=(
        "用户在 Cmd palette / 主对话框直接发问 (不打开任何节点) 时调本 endpoint. "
        "走 supplementary_search 全域候选池 + rerank (median_degree=0, 无 graph context). "
        "返回 enriched_context (含 manifest + supplementary XML), Claude 用 Read tool "
        "真核实再回答 (RAG-as-tool 范式)."
    ),
)
async def global_search(req: GlobalSearchRequest) -> GlobalSearchResponse:
    import time

    start = time.monotonic()

    # Multi-vault 隔离 (与 enrich-context 同款契约)
    from app.config import sanitize_vault_id
    from app.core.subject_config import build_vault_group_id, set_current_subject_id

    sanitized_vault_id = sanitize_vault_id(req.vault_id)
    derived_group_id = build_vault_group_id(
        sanitized_vault_id,
        subject_id=req.subject_id,
        canvas_path=None,  # 全局搜索无 canvas 上下文
    )
    set_current_subject_id(derived_group_id)

    supp_count = 0
    supp_degraded = False
    supp_reason: str | None = None
    supp_xml = ""

    try:
        # 复用 P0-C lazy init (避免 _supp_lancedb_singleton 直读 race condition)
        lancedb_client = await _get_supp_lancedb_client(init_timeout=5.0)

        supp_result = await search_supplementary(
            query=req.user_question,
            lancedb_client=lancedb_client,
            top_k_max=req.top_k_max,
            min_relevance=0.30,  # RRF 实测分布 (与 enrich-context 一致)
            elbow_drop_threshold=0.05,
            hard_cap=req.hard_cap,
        )

        # rerank 应用 type_weight + query_overlap (median_degree=0.0 — 全局搜索无 graph context)
        from app.services.supplementary_reranker import (
            get_filter_threshold,
            rerank,
        )

        pre_rerank_count = len(supp_result.get("materials", []))
        supp_result["materials"] = rerank(
            supp_result.get("materials", []),
            query=req.user_question,
            median_degree=0.0,
            min_score_threshold=get_filter_threshold(),
            top_k=5,
        )
        post_rerank_count = len(supp_result["materials"])

        supp_xml = format_supplementary_xml(supp_result)
        supp_count = len(supp_result.get("materials", []))
        supp_degraded = supp_result.get("degraded", False)
        supp_reason = supp_result.get("reason")

        logger.info(
            "[Story-2.2+2.9-GlobalSearch] supplementary 完成",
            pre=pre_rerank_count,
            post=post_rerank_count,
            count=supp_count,
            degraded=supp_degraded,
            reason=supp_reason,
            query=req.user_question[:80],
            vault=sanitized_vault_id,
        )
    except Exception as e:  # noqa: BLE001  — 降级铁律: 主对话不受全局搜索失败影响
        logger.warning(
            "[Story-2.2+2.9-GlobalSearch] 异常降级",
            error=str(e)[:120],
            query=req.user_question[:80],
        )
        supp_degraded = True
        supp_reason = f"unexpected_error: {type(e).__name__}: {str(e)[:80]}"

    # 组装 manifest + body
    degradations_str = supp_reason if supp_degraded else "none"
    manifest = (
        "<!-- Global Search Manifest:\n"
        f"  vault: {sanitized_vault_id}\n"
        f"  query: {req.user_question[:80]}\n"
        f"  sources: {supp_count} supplementary materials\n"
        f"  degradations: {degradations_str}\n"
        "-->\n"
    )
    if supp_xml:
        enriched_context = manifest + "\n" + supp_xml
    else:
        enriched_context = (
            manifest
            + "\n<supplementary_materials>\n"
            + "  <!-- 无匹配材料 -->\n"
            + "</supplementary_materials>\n"
        )

    elapsed_ms = (time.monotonic() - start) * 1000.0
    return GlobalSearchResponse(
        enriched_context=enriched_context,
        supplementary_count=supp_count,
        supplementary_degraded=supp_degraded,
        supplementary_reason=supp_reason,
        elapsed_ms=round(elapsed_ms, 2),
    )
