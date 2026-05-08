"""Story 2.2 Phase A — 补充学习材料搜索服务。

PRD §4.1.1 9-步 workflow Step 5: 在 enrich-context 之后追加 vault hybrid 搜索，
为对话回答提供"相关学习材料"补充段。

Phase A 范围（最小可用）：
- hybrid 搜索（bge-m3 + jieba 关键词）
- source priority 复用 (apply_source_priority)
- explanation files filter（与 react_agent.search_vault_notes 一致）
- 阈值过滤 min_relevance >= 0.70
- 三档降级语义：lancedb_unavailable / search_failed / empty_index

Phase A 不做（留给 Phase B/C）：
- 类型权重精排（lecture_notes 1.0 / discussion 0.9 / ...）→ Phase B supplementary_reranker
- wikilink 三精度（file / heading / block_id）→ Phase B
- 单元测试 + 性能测试 → Phase C
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════


async def search_supplementary(
    query: str,
    lancedb_client: Any | None,
    top_k: int = 5,
    min_relevance: float = 0.70,
) -> dict[str, Any]:
    """对 vault_notes 做 hybrid 搜索 + source priority + 阈值过滤。

    Args:
        query: 搜索 query（建议 user_question + node_title 组合）
        lancedb_client: 已 init 的 LanceDB client（None 表示降级）
        top_k: 返回 Top N（默认 5）
        min_relevance: 相关度阈值（默认 0.70，对齐 PRD §4.1.1）

    Returns:
        {
            "materials": list[dict],     # 排序后 Top N（每条含 title/snippet/wikilink/score/source_path）
            "degraded": bool,             # True 表示因外部因素失败
            "reason": str | None,         # 降级原因或空索引等可观测性信息
        }
    """
    if lancedb_client is None:
        return {
            "materials": [],
            "degraded": True,
            "reason": "lancedb_unavailable",
        }

    if not query or not query.strip():
        return {
            "materials": [],
            "degraded": False,
            "reason": "empty_query",
        }

    try:
        if hasattr(lancedb_client, "_initialized") and not lancedb_client._initialized:
            await lancedb_client.initialize()

        results = await lancedb_client.search(
            query=query,
            table_name="vault_notes",
            num_results=max(top_k * 2, 8),
            query_type="hybrid",
        )
    except (RuntimeError, ConnectionError, ValueError, asyncio.TimeoutError) as e:
        logger.warning(
            "[SupplementarySearch] hybrid 失败，回退到 vector-only",
            error=str(e)[:120],
            query=query[:80],
        )
        try:
            results = await lancedb_client.search(
                query=query,
                table_name="vault_notes",
                num_results=max(top_k * 2, 8),
            )
        except (RuntimeError, ConnectionError, ValueError, asyncio.TimeoutError) as e2:
            return {
                "materials": [],
                "degraded": True,
                "reason": f"search_failed: {str(e2)[:80]}",
            }

    if not results:
        return {
            "materials": [],
            "degraded": False,
            "reason": "empty_index",
        }

    try:
        from app.core.reference_config import apply_source_priority

        results = apply_source_priority(results)
    except ImportError:
        logger.debug(
            "[SupplementarySearch] reference_config 不可用，跳过 source priority"
        )

    materials: list[dict[str, Any]] = []
    for raw in results:
        score = float(raw.get("score", 0.0))
        if score < min_relevance:
            continue

        normalized = _normalize_material(raw)
        path = normalized["source_path"]
        if "-explanations/" in path:
            continue

        materials.append(normalized)
        if len(materials) >= top_k:
            break

    return {
        "materials": materials,
        "degraded": False,
        "reason": None if materials else "all_filtered_below_threshold",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# XML formatting (consumed by Skill prompt)
# ═══════════════════════════════════════════════════════════════════════════════


def format_supplementary_xml(result: dict[str, Any]) -> str:
    """把 search_supplementary 返回的 dict 渲染成 `<supplementary_materials>` XML 段。

    Story 2.1 的 `<rag_context>` 包装风格保持一致 — Skill 端按相同 XML pattern 解析。

    降级场景：
    - degraded=True → `<supplementary_materials count="0" degraded="true" reason="..."/>` 自闭合
    - 空结果但未降级 → `<supplementary_materials count="0" reason="empty_index"/>`
    - 有材料 → 完整 `<supplementary_materials count="N">...<material .../>...</supplementary_materials>`
    """
    materials = result.get("materials", [])
    degraded = result.get("degraded", False)
    reason = result.get("reason")

    if degraded or not materials:
        attrs = f'count="{len(materials)}"'
        if degraded:
            attrs += ' degraded="true"'
        if reason:
            attrs += f' reason="{_xml_escape(reason)}"'
        return f"<supplementary_materials {attrs}/>"

    parts = [f'<supplementary_materials count="{len(materials)}">']
    for i, m in enumerate(materials, start=1):
        parts.append(
            f'  <material rank="{i}" score="{m["score"]:.3f}">\n'
            f"    <title>{_xml_escape(m['title'])}</title>\n"
            f"    <wikilink>{_xml_escape(m['wikilink'])}</wikilink>\n"
            f"    <snippet>{_xml_escape(m['snippet'])}</snippet>\n"
            f"    <source_path>{_xml_escape(m['source_path'])}</source_path>\n"
            f"  </material>"
        )
    parts.append("</supplementary_materials>")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _normalize_material(raw: dict[str, Any]) -> dict[str, Any]:
    """LanceDB raw 行 → Phase A material dict（title / snippet / wikilink / score / source_path）。

    复用 react_agent._format_results 的字段提取逻辑（Story 2.1 dad9ed7 通过 ChatGPT 8/10 审计）。
    """
    metadata = raw.get("metadata") or {}
    score = float(raw.get("score", 0.0))
    content = raw.get("content", "") or ""

    canvas_file = metadata.get("canvas_file", "") or ""
    heading = ""
    source_type = "note"
    meta_json_str = metadata.get("metadata_json", "")
    if isinstance(meta_json_str, str) and meta_json_str:
        try:
            meta_parsed = json.loads(meta_json_str)
            if not canvas_file:
                canvas_file = meta_parsed.get("file_path", "") or ""
            heading = meta_parsed.get("heading", "") or ""
            source_type = meta_parsed.get("source_type", "note") or "note"
        except json.JSONDecodeError:
            pass

    file_display = canvas_file[:-3] if canvas_file.endswith(".md") else canvas_file
    if heading:
        heading = re.sub(r"\[\[.*?\]\]", "", heading).strip()
        heading = re.sub(r"\[.*?\]\(.*?\)", "", heading).strip()
        heading = re.sub(r"\(\)\s*$", "", heading).strip()

    if file_display and heading and heading != file_display:
        wikilink = f"[[{file_display}#{heading}|{heading}]]"
        title = heading
    elif file_display:
        wikilink = f"[[{file_display}]]"
        title = file_display.split("/")[-1]
    else:
        doc_id = raw.get("doc_id", "") or ""
        wikilink = f"[Doc: {doc_id}]" if doc_id else "[unknown]"
        title = doc_id or "未命名片段"

    snippet = content[:300]
    if len(content) > 300:
        snippet += "..."

    return {
        "title": title,
        "wikilink": wikilink,
        "snippet": snippet,
        "score": score,
        "source_path": canvas_file,
        "source_type": source_type,
    }


def _xml_escape(text: str) -> str:
    """最小 XML 安全转义（防止 vault 笔记内容里的 `<` / `&` 破坏 XML 解析）。"""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("\n", " ")
    )
