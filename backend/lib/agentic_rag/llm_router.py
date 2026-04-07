"""
L1 LLM Router — replace rule-based query intent classification with LLM judgment.

Background (A9):
    The original L1 router (state_graph.py:66 classify_query_intent) uses
    keyword matching to map queries to one of 4 intents. User feedback (A9)
    flagged this as "rigid" and asked for an LLM-based smarter agent.

This module:
    1. Calls Gemini Flash via LiteLLM to classify query intent.
    2. Returns one of the project's existing 4 intents so _build_sends_for_intent
       (state_graph.py:133) can be reused without changes.
    3. Has strict timeout + JSON parsing tolerance (markdown code fence handling
       per project convention faithfulness_check.py:158).
    4. Never raises — caller is expected to fall back to rule-based router on
       any error (timeout / network / JSON / unknown intent).

Output contract:
    LLMRouterResult dataclass with:
        - intent: str — one of {"file_locate", "learning_history",
                                  "knowledge_point", "comprehensive"}
        - reason: str — short LLM explanation (or empty on fallback)
        - latency_ms: float — LLM call duration
        - success: bool — True if LLM succeeded; False on any error
        - error: Optional[str] — short error tag (timeout / parse_error / etc.)

[OpenSpec change: agentic-rag-l1-llm-router]
[Reuses pattern from: state_graph.py:389 (litellm + asyncio.wait_for),
                      faithfulness_check.py:158 (_parse_json_response)]
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

# Allowed intents — must match _build_sends_for_intent in state_graph.py
ALLOWED_INTENTS: frozenset[str] = frozenset(
    {"file_locate", "learning_history", "knowledge_point", "comprehensive"}
)

# Default config — overridable via CanvasRAGConfig
DEFAULT_LLM_ROUTER_MODEL = "gemini/gemini-2.0-flash"
DEFAULT_LLM_ROUTER_TIMEOUT_S = 3.0
DEFAULT_LLM_ROUTER_MAX_TOKENS = 150


# ──────────────────────────────────────────────────────────────────────────────
# Prompt template
# ──────────────────────────────────────────────────────────────────────────────

# Note: Uses project convention of plain JSON output without response_format
# parameter (faithfulness_check.py uses the same approach with _parse_json_response).
LLM_ROUTER_SYSTEM_PROMPT = """你是 Canvas 学习系统的查询路由专家。
根据用户查询的语义，从以下 4 种意图中选择最匹配的一个：

1. **file_locate**：用户想找具体的笔记、文件或文档位置。
   关键特征：包含"在哪""找到""哪个文件""find""locate"等定位词；
   或者明确询问某个笔记/文档/PDF的存放位置。
   适用检索器：vault_notes（笔记）+ lancedb（向量）+ cross_canvas（跨白板）

2. **learning_history**：用户想回顾自己之前学过的内容、复习记录或学习进度。
   关键特征：包含"之前""上次""复习""历史""学过""掌握""progress"等时间/状态词；
   或者询问"我上次学到哪了"。
   适用检索器：graphiti（知识图谱）+ lancedb + vault_notes

3. **knowledge_point**：用户想理解某个具体的知识点、概念或术语含义。
   关键特征：纯学术性问题，不含定位词或回顾词，问"是什么""为什么""怎么算"。
   例：万有引力公式、链式法则推导、TCP 三次握手原理。
   适用检索器：5 路全开（graphiti + lancedb + multimodal + cross_canvas + vault_notes）

4. **comprehensive**：综合性查询，无法明确归类到上述 3 类，或需要广泛检索。
   适用检索器：5 路全开

请输出 JSON 对象，格式严格如下：
{"intent": "<intent_name>", "reason": "<10-30 字简短解释>"}

只输出 JSON，不要 markdown 代码块，不要任何其他文字。"""

LLM_ROUTER_USER_TEMPLATE = "查询：{query}"


# ──────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class LLMRouterResult:
    """Result of an LLM-based L1 routing call."""

    intent: (
        str  # Always one of ALLOWED_INTENTS, defaults to "comprehensive" on fallback
    )
    reason: str  # LLM-provided rationale, or empty on fallback
    latency_ms: float
    success: bool
    error: Optional[str] = (
        None  # short tag: "timeout" / "parse_error" / "import_error" / "unknown_intent" / etc.
    )


# ──────────────────────────────────────────────────────────────────────────────
# JSON parsing helper (mirrors faithfulness_check._parse_json_response)
# ──────────────────────────────────────────────────────────────────────────────


def _parse_json_response(text: str) -> dict:
    """
    Parse JSON from LLM response, handling markdown code fences.

    Mirrors the helper in faithfulness_check.py:158 — kept local rather than
    imported to avoid coupling llm_router to faithfulness_check.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Drop opening fence (```json or ```) and closing fence (```)
        lines = [line for line in lines if not line.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


# ──────────────────────────────────────────────────────────────────────────────
# Main async router function
# ──────────────────────────────────────────────────────────────────────────────


async def llm_route(
    query: str,
    model: str = DEFAULT_LLM_ROUTER_MODEL,
    timeout_s: float = DEFAULT_LLM_ROUTER_TIMEOUT_S,
    max_tokens: int = DEFAULT_LLM_ROUTER_MAX_TOKENS,
) -> LLMRouterResult:
    """
    Classify a query into one of the 4 intents using an LLM (Gemini Flash by default).

    Never raises — returns LLMRouterResult with success=False on any error.
    The caller is expected to fall back to rule-based classify_query_intent
    on failure.

    Args:
        query: Raw user query text.
        model: LiteLLM model identifier (e.g., "gemini/gemini-2.0-flash").
        timeout_s: Hard timeout for the LLM call (seconds).
        max_tokens: Max tokens for the LLM response (small budget — ~50 is enough).

    Returns:
        LLMRouterResult with success=True and a valid intent on success,
        or success=False and intent="comprehensive" (safe fallback) on error.
    """
    start = time.perf_counter()

    if not query or not query.strip():
        return LLMRouterResult(
            intent="comprehensive",
            reason="empty query",
            latency_ms=0.0,
            success=False,
            error="empty_query",
        )

    try:
        import litellm
    except ImportError:
        logger.warning("[l1_router] litellm not installed, falling back to rule-based")
        return LLMRouterResult(
            intent="comprehensive",
            reason="",
            latency_ms=(time.perf_counter() - start) * 1000,
            success=False,
            error="import_error",
        )

    user_prompt = LLM_ROUTER_USER_TEMPLATE.format(query=query.strip()[:500])

    try:
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": LLM_ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=max_tokens,
            ),
            timeout=timeout_s,
        )
    except asyncio.TimeoutError:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning(
            f"[l1_router] LLM timeout after {timeout_s}s for query: {query[:60]!r}"
        )
        return LLMRouterResult(
            intent="comprehensive",
            reason="",
            latency_ms=latency_ms,
            success=False,
            error="timeout",
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning(f"[l1_router] LLM call failed: {type(exc).__name__}: {exc}")
        return LLMRouterResult(
            intent="comprehensive",
            reason="",
            latency_ms=latency_ms,
            success=False,
            error=f"{type(exc).__name__}",
        )

    latency_ms = (time.perf_counter() - start) * 1000

    # Extract content
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError) as exc:
        logger.warning(f"[l1_router] Malformed LLM response: {exc}")
        return LLMRouterResult(
            intent="comprehensive",
            reason="",
            latency_ms=latency_ms,
            success=False,
            error="malformed_response",
        )

    # Parse JSON (with markdown code fence tolerance)
    try:
        parsed = _parse_json_response(content)
    except json.JSONDecodeError as exc:
        logger.warning(
            f"[l1_router] JSON parse failed: {exc}, content: {content[:200]!r}"
        )
        return LLMRouterResult(
            intent="comprehensive",
            reason="",
            latency_ms=latency_ms,
            success=False,
            error="parse_error",
        )

    intent = parsed.get("intent", "")
    reason = parsed.get("reason", "")

    if not isinstance(intent, str) or intent not in ALLOWED_INTENTS:
        logger.warning(
            f"[l1_router] LLM returned unknown intent: {intent!r}, content: {content[:200]!r}"
        )
        return LLMRouterResult(
            intent="comprehensive",
            reason=str(reason)[:200] if reason else "",
            latency_ms=latency_ms,
            success=False,
            error="unknown_intent",
        )

    logger.info(
        f"[l1_router] LLM routed: query={query[:50]!r} -> intent={intent} "
        f"({latency_ms:.0f}ms) reason={reason[:60]!r}"
    )

    return LLMRouterResult(
        intent=intent,
        reason=str(reason)[:200] if reason else "",
        latency_ms=latency_ms,
        success=True,
        error=None,
    )
