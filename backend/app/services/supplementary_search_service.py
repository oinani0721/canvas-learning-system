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
    top_k_max: int = 20,
    min_relevance: float = 0.30,
    elbow_drop_threshold: float = 0.05,
    hard_cap: int = 15,
) -> dict[str, Any]:
    """RAG-as-tool 范式（2026-05-09 重构）: 大召回 + Claude Read 真验证.

    用户原话: "RAG 是辅助 claude code 用 grep 找得更准，把有用的材料都提供给我"
    → supplementary = candidate generator (大召回不限 5)，Claude Read = verifier
    → 不硬编码 top_k，按 score gap 动态截断 (elbow cut, 业界推荐)

    Args:
        query: 搜索 query（建议 user_question + node_title 组合）
        lancedb_client: 已 init 的 LanceDB client（None 表示降级）
        top_k_max: 召回上限（默认 20，给 Claude 大候选池做 Read 验证）
        min_relevance: 阈值（0.30 适配 RRF 实测分布，待 Phase B sigmoid 归一化恢复 0.70）
        elbow_drop_threshold: 相邻 score gap > 此值视为"相关性悬崖"动态截断
        hard_cap: 即使 elbow 不触发，最多返回此数量（保护 prompt 长度）

    Returns:
        {
            "materials": list[dict],   # 动态长度（不固定 5），含 title/snippet/wikilink/score/source_path
            "degraded": bool,
            "reason": str | None,
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
            await asyncio.wait_for(lancedb_client.initialize(), timeout=10.0)

        # 大召回：top_k_max + 50% buffer 给 source_priority 重排和空文档过滤留空间
        results = await asyncio.wait_for(
            _two_tier_search(
                lancedb_client,
                query=query,
                num_results=int(top_k_max * 1.5),
            ),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "[SupplementarySearch] 超时降级（首次 model cold-start 可能 60s+）",
            query=query[:80],
        )
        return {
            "materials": [],
            "degraded": True,
            "reason": "timeout",
        }
    except (RuntimeError, ConnectionError, ValueError) as e:
        logger.warning(
            "[SupplementarySearch] 搜索失败",
            error=str(e)[:120],
            query=query[:80],
        )
        return {
            "materials": [],
            "degraded": True,
            "reason": f"search_failed: {str(e)[:80]}",
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

    # Filter + normalize + 空文档检测（防 ghost reference / 路径漂移 / 空 frontmatter）
    # Phase A0.5-P (Round-4 ChatGPT V3 + cross-check confirmed P0 安全):
    # 加 classify_snippet 扫描 prompt injection 风险, 防钓鱼 .md 下载 → 注入 Claude additionalContext.
    # 阈值 (Q4 选项 2 中等): is_blocked → quarantine; injection_risk >= 0.45 → review; else clean.
    materials: list[dict[str, Any]] = []
    skipped_empty = 0
    quarantined_count = 0
    review_count = 0
    for raw in results:
        score = float(raw.get("score", 0.0))
        if score < min_relevance:
            continue

        normalized = _normalize_material(raw)
        path = normalized["source_path"]
        if "-explanations/" in path:
            continue

        # 空文档 / 路径不存在检测（防 Claude 引用空文件后凭 snippet 编内容）
        if not _is_real_vault_file(path):
            skipped_empty += 1
            continue

        # Phase A0.5-P + P0-3c: prompt injection taint 扫描 (multi-field).
        # 旧逻辑只扫 snippet → 攻击者把 payload 埋 frontmatter title / wikilink /
        # source_path 即可绕过 (snippet 看着干净 → clean → 整条进 prompt).
        # 新逻辑扫描 snippet + title + wikilink + source_path 各跑一遍 taint scan,
        # 取 max risk_score + worst taint level (quarantine > review > clean).
        taint_info = _classify_material_taint(normalized)
        normalized["taint"] = taint_info["taint"]
        normalized["injection_risk"] = taint_info["risk_score"]
        if taint_info["taint"] == "quarantine":
            quarantined_count += 1
        elif taint_info["taint"] == "review":
            review_count += 1

        # Bonus (2026-05-12 hotfix): chunk-type-aware link-list 标记.
        # 用 raw content (完整 chunk 文本) 比 snippet (截 300 字) 更准.
        # 不过滤 — 标记给 rerank 看见, 让下游可降权 link-list chunk 优先 atomic 笔记.
        raw_content_for_check = str(raw.get("content", "") or "") or normalized.get(
            "snippet", ""
        )
        if _is_link_list_chunk(raw_content_for_check):
            normalized["is_link_list_chunk"] = True

        # P0-D (2026-05-12 hotfix): tier-2 legacy fallback flag 必须从 raw
        # 透传到 normalized, 否则下面 any(...is_legacy_fallback) 永不命中.
        # raw['is_legacy_fallback'] 由 _two_tier_search tier-2 路径设置 (top-level
        # 也保留以备 metadata 嵌套不一致).
        if raw.get("is_legacy_fallback") or (raw.get("metadata") or {}).get(
            "is_legacy_fallback"
        ):
            normalized["is_legacy_fallback"] = True

        materials.append(normalized)
        if len(materials) >= top_k_max:
            break

    if skipped_empty > 0:
        logger.warning(
            "[SupplementarySearch] 过滤空文档/不存在文件",
            count=skipped_empty,
            query=query[:60],
        )
    if quarantined_count or review_count:
        logger.warning(
            "[SupplementarySearch] prompt injection taint 命中",
            quarantined=quarantined_count,
            review=review_count,
            query=query[:60],
        )

    # Elbow cut: 按 score gap 动态截断（不硬编码 top_k）
    materials = _elbow_cut(
        materials,
        drop_threshold=elbow_drop_threshold,
        hard_cap=hard_cap,
    )

    # P0-D (2026-05-12 hotfix): tier-2 legacy fallback 命中时, 行级
    # is_legacy_fallback=True 但顶层 dict 仍 degraded=False, 下游观测拿不到旗帜.
    # 这里检测任一 material 是 legacy fallback, 顶层 degraded=True + reason
    # set + logger.warning 通知 Ops 重建索引.
    #
    # Wave-2 P0-2 漏修-2 (2026-05-12): 移除 ``prior_reason = None if materials
    # else "all_filtered_below_threshold"`` 死分支 (信息丢失 bug).
    # legacy_hit = any(materials...) 已隐含 materials 非空, 三元 else 分支永不触发,
    # prior_reason 始终为 None, merged_reason 始终为 "tier2_legacy_unprefixed".
    # 这是死代码且会让维护者误以为有"prior reason 保留"行为.
    # 上游 _two_tier_search 返回 list (无 reason 字段) — 直接写单一标志.
    legacy_hit = any(m.get("is_legacy_fallback") for m in materials)
    if legacy_hit:
        merged_reason = "tier2_legacy_unprefixed"
        logger.warning(
            "[SupplementarySearch] degraded 顶层标志: tier-2 legacy fallback 命中",
            materials=len(materials),
            query=query[:60],
        )
        return {
            "materials": materials,
            "degraded": True,
            "reason": merged_reason,
        }

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

    Phase A0.5-P (Round-4): taint-aware 输出
    - taint=quarantine: 不输出 snippet 正文 + 加 quarantined="true" attr (防 indirect injection)
    - taint=review: snippet 替换为 placeholder, **不暴露**原文任何字符 (P0-3a fail-closed)
    - taint=clean (默认): 完整输出

    P0-3a (2026-05-12 hotfix, ChatGPT v2 对抗审查): review 之前截前 240 字保留原文,
    攻击 payload 在开头 240 字内 (典型 "IGNORE ALL PREVIOUS INSTRUCTIONS...") 仍进
    prompt → 升级为固定 placeholder + risk_score 提示, 用户可手动 Read source_path
    verify (符合 RAG-as-tool 范式: Claude Read = verifier).

    Story 2.2+2.9 T3.8 (2026-05-11): 透出 rerank 4 字段 (rerank_score / type_weight
    / hub_penalty / query_overlap) 供 Claude 在 prompt 中看见排序原因 (AC #4 trace
    可解释性). 字段缺失时 (rerank 未运行) 不渲染该 attribute, XML 仍兼容.
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
        taint = m.get("taint", "clean")
        injection_risk = m.get("injection_risk", 0.0)

        # Build material attrs
        material_attrs = f'rank="{i}" score="{m["score"]:.3f}"'
        # Story 2.2+2.9 T3.8: rerank trace attributes (仅当 rerank 已运行)
        for field, fmt in [
            ("rerank_score", ".3f"),
            ("type_weight", ".2f"),
            ("query_overlap", ".3f"),
            ("hub_penalty", ".3f"),
        ]:
            if field in m:
                material_attrs += f' {field}="{m[field]:{fmt}}"'
        if taint != "clean":
            material_attrs += f' taint="{taint}" injection_risk="{injection_risk:.2f}"'
        # Bonus (2026-05-12 hotfix): link-list chunk 标记 (仿同款 rerank attribute,
        # 只在 True 时渲染保持 XML 兼容).
        if m.get("is_link_list_chunk"):
            material_attrs += ' is_link_list="true"'

        # Snippet + metadata content based on taint level.
        #
        # Wave-3 P0 hotfix (2026-05-12, ChatGPT v4 verdict #1): worst-takes-all
        # 已让 title / wikilink / source_path 任一含 payload 升级 taint, 但渲染时
        # 只 placeholder 了 snippet — 攻击者把 prompt injection payload 埋
        # frontmatter title 即绕过 (snippet redacted 但 title 原样进 prompt).
        # 升级: review/quarantine 时 title/wikilink/source_path 同样 placeholder.
        # clean 路径保持 _xml_escape 原值, 不影响正常材料展示.
        if taint == "quarantine":
            snippet_content = (
                "[QUARANTINED — content blocked due to suspected prompt injection. "
                "Use Read tool on source_path to verify if needed.]"
            )
            title_content = f"[QUARANTINED: tainted title (risk={injection_risk:.2f})]"
            wikilink_content = "[QUARANTINED]"
            source_path_content = "[QUARANTINED]"
        elif taint == "review":
            # P0-3a (2026-05-12 hotfix): fixed placeholder, 不暴露原文任何字符.
            # 旧逻辑截前 240 字保留原文 → 攻击 payload 在开头 240 字内 (典型
            # "IGNORE ALL PREVIOUS INSTRUCTIONS...") 仍进 prompt. 升级为固定
            # placeholder + risk_score 提示, 用户可手动 Read source_path verify.
            snippet_content = (
                f"[REDACTED: suspicious content (risk={injection_risk:.2f}); "
                f"open source_path manually to verify]"
            )
            title_content = f"[REDACTED: tainted title (risk={injection_risk:.2f})]"
            wikilink_content = "[REDACTED]"
            source_path_content = "[REDACTED]"
        else:
            snippet_content = _xml_escape(m["snippet"])
            title_content = _xml_escape(m["title"])
            wikilink_content = _xml_escape(m["wikilink"])
            source_path_content = _xml_escape(m["source_path"])

        parts.append(
            f"  <material {material_attrs}>\n"
            f"    <title>{title_content}</title>\n"
            f"    <wikilink>{wikilink_content}</wikilink>\n"
            f"    <snippet>{snippet_content}</snippet>\n"
            f"    <source_path>{source_path_content}</source_path>\n"
            f"  </material>"
        )
    parts.append("</supplementary_materials>")
    return "\n".join(parts)


def _classify_snippet_taint(snippet: str) -> dict[str, Any]:
    """Phase A0.5-P (Round-4 ChatGPT V3 P0 安全): supplementary 内容 prompt injection 扫描.

    防御场景: 攻击者发钓鱼 .md 给用户 → 用户下载到 vault → hook 召回 → 注入 Claude additionalContext.
    阈值 (Q4 选项 2 中等):
    - is_blocked (>= INJECTION_THRESHOLD): quarantine, 不输出正文
    - risk_score >= 0.45: review, 截断 240 字摘要
    - else: clean, 正常输出

    P0-E (2026-05-12 hotfix): 异常分类处理.
    - ImportError → clean (开发环境模块缺失正常, 不能因此 fail-closed 影响功能)
    - RuntimeError / 其他 → review + risk_score=0.5 (fail-closed, 让 snippet
      被截 240 字 + 注入 risk_score 让下游可见, 防 guard 故障时绕过审查).
    """
    if not snippet or not snippet.strip():
        return {"taint": "clean", "risk_score": 0.0}
    try:
        from app.middleware.prompt_injection_guard import check_input

        result = check_input(snippet)
        if result.is_blocked:
            return {"taint": "quarantine", "risk_score": result.risk_score}
        if result.risk_score >= 0.45:
            return {"taint": "review", "risk_score": result.risk_score}
        return {"taint": "clean", "risk_score": result.risk_score}
    except ImportError as e:
        # 模块未安装/开发环境 — 标志 clean (与 PhaseA0.5-P 原行为一致)
        logger.debug(
            "[SupplementarySearch] prompt_injection_guard 模块不可用，跳过 taint 扫描",
            error=str(e)[:120],
        )
        return {"taint": "clean", "risk_score": 0.0}
    except RuntimeError as e:
        # P0-E: guard 运行时故障 — fail-closed, 强制 review 让 snippet 被截断
        logger.warning(
            "[SupplementarySearch] prompt_injection_guard 运行时故障, fail-closed",
            error=str(e)[:120],
        )
        return {"taint": "review", "risk_score": 0.5}


# P0-3c (2026-05-12 hotfix, ChatGPT v2 fail-closed real): taint priority order.
# worst-takes-all 聚合: snippet/title/wikilink/source_path 任一字段含 payload
# 都会让整条材料 taint 升级.
_TAINT_PRIORITY: dict[str, int] = {"clean": 0, "review": 1, "quarantine": 2}


def _classify_material_taint(material: dict[str, Any]) -> dict[str, Any]:
    """P0-3c (ChatGPT v2 对抗审查): 扫描 material 全部 user-visible 字段.

    旧逻辑只扫 snippet → 攻击者把 payload 埋 frontmatter title / wikilink /
    source_path 即可绕过 (snippet 看着干净 → clean → 整条进 prompt).

    新逻辑: snippet + title + wikilink + source_path 各跑一遍 _classify_snippet_taint,
    取 max risk_score + worst taint level (quarantine > review > clean) — 任一字段
    含注入 payload 都会被升级 review/quarantine.

    Returns:
        {"taint": "clean"|"review"|"quarantine", "risk_score": float in [0,1]}
    """
    fields = (
        material.get("snippet", "") or "",
        material.get("title", "") or "",
        material.get("wikilink", "") or "",
        material.get("source_path", "") or "",
    )
    worst_taint = "clean"
    max_risk = 0.0
    for field in fields:
        if not field:
            continue
        info = _classify_snippet_taint(field)
        t = info["taint"]
        r = info["risk_score"]
        if _TAINT_PRIORITY[t] > _TAINT_PRIORITY[worst_taint]:
            worst_taint = t
        if r > max_risk:
            max_risk = r
    return {"taint": worst_taint, "risk_score": max_risk}


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _resolve_chunks_to_source_file(path: str) -> str:
    """把 LanceDB chunk 的 'X/chunks/<chunk>.md' 派生路径回写到原文件 X.md.

    业界共识 (Smart Connections / Khoj / Copilot for Obsidian 100% 一致):
    chunk 是索引时的虚拟切片，**绝不写虚拟派生文件**。citation 始终指向原 .md。

    Examples:
        'raw/CS188/videos/lectures/lecture 2/chunks/merged.md'
            → 'raw/CS188/videos/lectures/lecture 2/lecture 2.md'
        'raw/X/exam_prep/EP04_MDPs.../chunks/merged.md'
            → 'raw/X/exam_prep/EP04_MDPs.../EP04_MDPs....md'
        '节点/Eigenvalues.md' (不含 chunks/) → 原样返回
    """
    if not path or "/chunks/" not in path:
        return path
    parts = path.split("/")
    try:
        chunks_idx = parts.index("chunks")
    except ValueError:
        return path
    if chunks_idx == 0:
        return path  # 顶级 chunks/ 不应出现
    parent_dir_name = parts[chunks_idx - 1]
    # 父目录 + 父目录名.md = 原源文件
    return "/".join(parts[:chunks_idx]) + "/" + parent_dir_name + ".md"


def _is_real_vault_file(rel_path: str, min_size_bytes: int = 64) -> bool:
    """检查 vault 内文件存在 + 非空（防 ghost reference / 空文档 / 路径漂移）.

    用户实测痛点: Claude 列 wikilink 但点击后"找不到此文件"，或文件存在但内容为空
    （Claude 凭 snippet 编内容）。本函数在 supplementary 返回前过滤这些。
    """
    if not rel_path:
        return False
    try:
        from pathlib import Path

        from app.config import get_settings

        s = get_settings()
        vault_root = Path(s.canvas_base_path)
        # rel_path 可能是 "节点/X.md" / "raw/CS188/.../merged.md" 等 vault 相对路径
        abs_path = (vault_root / rel_path).resolve()
        # 防路径穿越（resolve 后必须仍在 vault 内）
        try:
            abs_path.relative_to(vault_root.resolve())
        except ValueError:
            return False
        if not abs_path.is_file():
            return False
        # < 64 字节视为空（仅 frontmatter / 空 md）
        if abs_path.stat().st_size < min_size_bytes:
            return False
        return True
    except Exception:  # noqa: BLE001  任何 OS 错误也跳过
        return False


# Bonus (2026-05-12 hotfix): chunk-type-aware filter helper.
# 用户痛点: MOC / index 节点 (大量 [[wikilink]] 但少正文) 被 RAG 召回到 supplementary,
# 占名额却没真信息 (链接列表是引用关系, 不是知识本体). 不在过滤层删除 — 标记给 rerank
# 看见, 让 Claude 在 supplementary XML 里看到 is_link_list="true" 后能优先 Read 真节点.
_WIKILINK_RE = re.compile(r"\[\[[^\[\]]+\]\]")


def _is_link_list_chunk(content: str, threshold: float = 0.6) -> bool:
    """检测内容是否以 wikilink 列表为主 (MOC/index chunk 标志).

    算 wikilink_count / max(non_link_token_count, 1) > threshold 即标 link-list.
    `non_link_tokens` = 去除全部 wikilink 后按空白分词的 token 数 (近似正文 token).

    Examples:
        "[[A]] [[B]] [[C]]" → 3/1 = 3.0 > 0.6 → True (纯 link 列表)
        "我们用 [[A*]] 算法" → 1/3 ≈ 0.33 < 0.6 → False (正文夹带 link)
    """
    if not content:
        return False
    wikilink_count = len(_WIKILINK_RE.findall(content))
    if wikilink_count == 0:
        return False
    stripped = _WIKILINK_RE.sub(" ", content)
    non_link_tokens = [tok for tok in stripped.split() if tok.strip()]
    ratio = wikilink_count / max(len(non_link_tokens), 1)
    return ratio > threshold


def _elbow_cut(
    materials: list[dict[str, Any]],
    drop_threshold: float = 0.05,
    hard_cap: int = 15,
) -> list[dict[str, Any]]:
    """按相邻 score gap 动态截断（业界推荐做法 vs 硬编码 top_k）.

    用户原话: "我没硬编码要多少材料，要把有用的材料都提供给我"
    → 当相邻 score 差 > drop_threshold 视为"相关性悬崖"截断
    → 即使 elbow 不触发，最多 hard_cap 条（保护 prompt 长度）
    """
    if not materials:
        return materials
    # materials 已按 score 降序（apply_source_priority 之后）
    cut_idx = len(materials)
    for i in range(1, len(materials)):
        gap = materials[i - 1]["score"] - materials[i]["score"]
        if gap > drop_threshold:
            cut_idx = i
            break
    return materials[: min(cut_idx, hard_cap)]


async def _two_tier_search(
    client: Any,
    query: str,
    num_results: int,
) -> list[dict[str, Any]]:
    """先查 vault_id 隔离的 prefix 表（Story 1.9 主路径），空则 fallback 到 unprefixed 老索引。

    Tier 1: client.search() 含 resolve_table_name 把 'vault_notes' 加 vault_id 前缀
            （如 'canvas_vault_vault_notes'）。多 vault 切换时各自隔离，正确的主路径。
    Tier 2: 直接 _db.open_table('vault_notes')（unprefixed），FTS 优先 + vector fallback。
            兼容 Story 1.9 vault_id 隔离机制 land 前建立的老索引。
            tier-2 命中时记 logger.warning 提醒 Ops 重建索引。
    """
    # ── Tier 1 ── prefix-resolved（Story 1.9 主路径，多 vault 隔离）
    # RAG-P0 A3 (2026-05-10): default exclude whiteboard. MOC/index whiteboards
    # carry mostly dataviewjs/callout boilerplate that pollutes solving queries.
    results: list[dict[str, Any]] = []
    try:
        results = await client.search(
            query=query,
            table_name="vault_notes",
            num_results=num_results,
            query_type="hybrid",
            exclude_doc_types=["whiteboard"],
        )
    except (RuntimeError, ConnectionError, ValueError, asyncio.TimeoutError) as e:
        logger.warning(
            "[SupplementarySearch] tier-1 hybrid 失败，回退到 vector-only",
            error=str(e)[:120],
        )
        try:
            results = await client.search(
                query=query,
                table_name="vault_notes",
                num_results=num_results,
                exclude_doc_types=["whiteboard"],
            )
        except (RuntimeError, ConnectionError, ValueError, asyncio.TimeoutError):
            results = []

    if results:
        return results

    # ── Tier 2 ── unprefixed legacy table（兼容老索引；Story 1.9 升级前的数据）
    try:
        if not (hasattr(client, "_db") and client._db is not None):
            return []
        list_tables_fn = (
            client._db.list_tables
            if hasattr(client._db, "list_tables")
            else getattr(client._db, "table_names", None)
        )
        if list_tables_fn is None:
            return []
        tables_raw = list_tables_fn()
        # LanceDB ≥ 0.x 返回 ListTablesResponse(tables=[...], page_token=None)
        # 旧版 / table_names() 返回 plain list — 兼容两者
        if hasattr(tables_raw, "tables"):
            tables_list = list(tables_raw.tables)
        elif hasattr(tables_raw, "__iter__") and not isinstance(tables_raw, str):
            tables_list = list(tables_raw)
        else:
            tables_list = []
        if "vault_notes" not in tables_list:
            return []
        # 仅当 Story 1.9 prefix !=unprefixed 时 tier-2 才有意义（避免重查 tier-1 同一表）
        if hasattr(client, "resolve_table_name"):
            resolved = client.resolve_table_name("vault_notes")
            if resolved == "vault_notes":
                return []
        tbl = client._db.open_table("vault_notes")
        # FTS 优先（已验证可用：BM25 score Top-1 ~11，覆盖中英文 jieba 分词）
        try:
            df = tbl.search(query, query_type="fts").limit(num_results).to_pandas()
        except Exception:  # noqa: BLE001  fallback 到 vector
            df = tbl.search(query).limit(num_results).to_pandas()
        if df is None or df.empty:
            return []
        logger.warning(
            "[SupplementarySearch] tier-2 fallback 命中 unprefixed vault_notes "
            "(Story 1.9 升级前老索引；建议 Ops 跑 POST /api/v1/metadata/index/vault rebuild)",
            rows=len(df),
        )
        # Phase A0 修复 I (Round-3 ChatGPT V2 + cross-check confirmed FATAL bug):
        # 旧逻辑硬编码 score=0.85 绕过 min_relevance=0.30 + 绕过 elbow_cut(0.05)
        # 旧 BM25 与 cosine [0,1] 不可比的简化 trade-off 代价过大 — 让 tier-2 与真实 hybrid 命中
        # 在下游过滤逻辑上完全等同对待。
        # 新逻辑: rank-decay score [0.31, 0.50] (恰好 > min_relevance=0.30 但远低于真实 hybrid)
        #        + degraded=True 顶层标志（下游可观测/过滤）
        # Phase B 必须接 supplementary_reranker 做真实 cross-encoder 精排（解决 BM25/cosine 不可比）
        normalized: list[dict[str, Any]] = []
        df_size = max(len(df), 1)
        for idx, (_, row) in enumerate(df.iterrows()):
            raw_canvas_file = str(row.get("canvas_file", "") or "")
            # rank 0 → 0.50, rank N-1 → 0.31（保留 FTS BM25 排序信号但不绕过 min_relevance）
            rank_score = (
                0.50 - 0.19 * (idx / max(df_size - 1, 1)) if df_size > 1 else 0.50
            )
            normalized.append(
                {
                    "score": rank_score,
                    "content": str(row.get("content", "") or ""),
                    "doc_id": str(row.get("doc_id", "") or ""),
                    "metadata": {
                        "canvas_file": raw_canvas_file,
                        "is_legacy_fallback": True,
                    },
                    "canvas_file": raw_canvas_file,
                    "is_legacy_fallback": True,  # 顶层标志，方便下游 filter
                    "degraded": True,
                }
            )
        return normalized
    except Exception as e:  # noqa: BLE001  tier-2 失败也不抛，让上层走 empty_index 降级
        logger.warning(
            "[SupplementarySearch] tier-2 fallback 失败",
            error=str(e)[:120],
        )
        return []


def _normalize_material(raw: dict[str, Any]) -> dict[str, Any]:
    """LanceDB raw 行 → Phase A material dict（title / snippet / wikilink / score / source_path）。

    复用 react_agent._format_results 的字段提取逻辑（Story 2.1 dad9ed7 通过 ChatGPT 8/10 审计）。
    """
    metadata = raw.get("metadata") or {}
    score = float(raw.get("score", 0.0))
    content = raw.get("content", "") or ""

    # 优先 metadata.canvas_file（新 schema），fallback 到顶层 canvas_file（老 schema / tier-2）
    canvas_file = metadata.get("canvas_file", "") or raw.get("canvas_file", "") or ""
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

    # 2026-05-09 P0 fix: chunks/merged.md 派生路径回写到原文件
    canvas_file = _resolve_chunks_to_source_file(canvas_file)
    file_display = canvas_file[:-3] if canvas_file.endswith(".md") else canvas_file

    # 2026-05-09 wikilink 跳转修复 (3 agent 实测确认):
    # ⛔ heading anchor 必须**字面 100% 匹配** vault 内文档的 heading
    # - 文档真实 heading: "6.4.1 解决局部最优陷阱的方法 [59:00]()-[01:00]()"
    # - 之前 over-strip [time]() 后剩 "6.4.1 ... 方法 -" → Obsidian 找不到 → 仅跳文件不滚动
    # → heading 字面完整保留（含视频 timestamp 残留），display text 才做清洗供视觉简洁
    raw_heading = heading or ""  # 保留 LanceDB 索引时的原始 heading 字面（与文档一致）
    display_heading = raw_heading
    if display_heading:
        # display text (用户视觉) 仅做清洗：去 [time]() / [[wikilink]] / 末尾空白
        display_heading = re.sub(r"\[\[.*?\]\]", "", display_heading).strip()
        display_heading = re.sub(r"\[.*?\]\(.*?\)", "", display_heading).strip()
        display_heading = re.sub(
            r"\s+-\s*$", "", display_heading
        ).strip()  # 末尾 ` -` 残留
        display_heading = re.sub(r"^\s+|\s+$", "", display_heading)
    heading = raw_heading  # ⭐ wikilink anchor 用字面 raw heading（保跳转）

    # 2026-05-09 wikilink 拼接: anchor 用 raw heading 字面匹配文档，display 用 clean 简洁视觉
    # ⛔ wikilink heading anchor 含 `[time]()` 时 Obsidian wikilink parser 行为未公开
    # 业界备选 (Smart Connections / Khoj): 用 markdown link `[display](file.md#heading)`
    # 当前先试 wikilink 字面 anchor 路径，如 Obsidian 解析仍失败再切 markdown link
    display_text = display_heading or heading or ""
    if file_display and heading and heading != file_display:
        wikilink = f"[[{file_display}#{heading}|{display_text}]]"
        title = display_text
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
