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
import os
import re
from typing import Any

import structlog

from app.services import retrieval_reranker

logger = structlog.get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# RAG-S2 T4 (2026-08-10): cross-encoder 精排常数
# ═══════════════════════════════════════════════════════════════════════════════
#
# 分数契约 (三量纲共存, 勿混):
#   _raw_score / raw_score — 未加权语义分 (min_relevance 过滤量纲)
#   score                  — source_priority 加权分 (排序/elbow 唯一量纲)
#   ce_score               — bge-reranker sigmoid(logit), 强双峰
#                            (实测正确 +6.5→0.999 / 垃圾 -11→1.6e-5 /
#                             跨语弱相关 0.05-0.2) — 纯语义, 只做交付门
# ⛔ CE 不参与排序 (两轮金集校准实证 2026-08-10): 纯 CE 排序与 CE×权重
# 融合排序都让 raw/ 转录反扑 (转录 400 字窗口关键词密集, CE 语义分差
# 2-3 倍, 手写 ×1.5 权重差压不住; 手写占比@10 59.5%→29%/31%)。排序保持
# T2/T3 已验证的加权序 (用户初衷: 手写优先), CE 只当交付判官。
# 命名刻意避开 rerank_score (已被 supplementary_reranker 启发式公式占用)。

# CE 门激活时预过滤放宽到此召回地板 — 正解 raw 分 0.4x 被生产 0.50 杀光
# (金集 vq-a01/a02/a05 实证), CE 才是交付判官; CE 失败回落按原 min_relevance
# 重过滤, 行为与旧版一致。0.30 = 本服务历史默认 (适配 RRF 实测分布)。
_RERANK_RECALL_FLOOR = 0.30

# CE sigmoid 交付门: 垃圾 ≤1e-3, 跨语弱相关落 0.05-0.2 区间 — 取 0.02
# 杀垃圾不误杀跨语 (金集校准锚点, 调整须重跑金集)。
_CE_DELIVERY_FLOOR = 0.02


# ═══════════════════════════════════════════════════════════════════════════════
# Wave-5 Stage C P1-9 (ChatGPT v4): LanceDB Tier-2 unprefixed fallback gate
# ═══════════════════════════════════════════════════════════════════════════════
#
# Bug: Tier-2 fallback reads unprefixed ``vault_notes`` table (Story 1.9 legacy
# index). If legacy vault data exists in residual unprefixed table, vault A's
# query can pick up legacy mixed-content rows via fallback path → cross-vault
# leak in multi-vault deployments.
#
# Fix: env-var gated. Default ``"false"`` (production-safe, multi-vault). Dev /
# single-vault legacy can opt-in with ``ENABLE_LANCEDB_TIER2_FALLBACK=true``.


def _enable_tier2_fallback() -> bool:
    """Return True only if ENABLE_LANCEDB_TIER2_FALLBACK env var is truthy.

    Production default: ``False`` (skip tier-2 unprefixed fallback to prevent
    cross-vault leakage in multi-vault deployments). Single-vault legacy dev
    can opt-in with ``ENABLE_LANCEDB_TIER2_FALLBACK=true``.
    """
    val = os.environ.get("ENABLE_LANCEDB_TIER2_FALLBACK", "false").strip().lower()
    return val in ("1", "true", "yes", "on")


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
    include_content: bool = False,
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
        include_content: RAG-S2 T5 MCP profile — True 时 material 额外带完整
            chunk 正文 ``content`` 字段（MCP search_notes 需要正文而非 300 字
            snippet）。hook 链不传 → prompt 面不变。⛔ 这是共享链的 profile
            参数, 不是平行搜索函数 (DD-13/防蔓延)。

    Returns:
        {
            "materials": list[dict],   # 动态长度（不固定 5），含 title/snippet/wikilink/score/source_path
            "degraded": bool,
            "reason": str | None,
            "confidence": dict,        # RAG-S2 T5: {level, signals} 查询级检索置信度
        }
    """
    if lancedb_client is None:
        return _empty_result("lancedb_unavailable", degraded=True)

    if not query or not query.strip():
        return _empty_result("empty_query", degraded=False)

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
        return _empty_result("timeout", degraded=True)
    except (RuntimeError, ConnectionError, ValueError) as e:
        logger.warning(
            "[SupplementarySearch] 搜索失败",
            error=str(e)[:120],
            query=query[:80],
        )
        return _empty_result(f"search_failed: {str(e)[:80]}", degraded=True)

    if not results:
        return _empty_result("empty_index", degraded=False)

    try:
        from app.core.reference_config import apply_source_priority

        results = apply_source_priority(results)
    except ImportError:
        logger.debug("[SupplementarySearch] reference_config 不可用，跳过 source priority")

    # Filter + normalize + 空文档检测（防 ghost reference / 路径漂移 / 空 frontmatter）
    # Phase A0.5-P (Round-4 ChatGPT V3 + cross-check confirmed P0 安全):
    # 加 classify_snippet 扫描 prompt injection 风险, 防钓鱼 .md 下载 → 注入 Claude additionalContext.
    # 阈值 (Q4 选项 2 中等): is_blocked → quarantine; injection_risk >= 0.45 → review; else clean.
    materials: list[dict[str, Any]] = []
    skipped_empty = 0
    quarantined_count = 0
    review_count = 0
    # RAG-S2 T4: rerank 启用时预过滤放宽到召回地板 (CE 是交付判官);
    # rerank 失败的回落分支会按原 min_relevance 重过滤 (行为与旧版一致)。
    rerank_enabled = retrieval_reranker.is_enabled()
    effective_floor = min(min_relevance, _RERANK_RECALL_FLOOR) if rerank_enabled else min_relevance
    n_above_min = 0  # raw >= min_relevance 的条数 (放宽地板行不占配额)
    for raw in results:
        # R1 根因二 (2026-07-12): 过滤用原始语义分 (_raw_score), 不用
        # source_priority 加权后的 score — 否则 ×1.5 权重击穿门槛 /
        # ×0.3 权重误杀正确命中 (真机: 烤面包查询 10 条全过)。
        score = float(raw.get("_raw_score", raw.get("score", 0.0)))
        if score < effective_floor:
            continue

        normalized = _normalize_material(raw)
        path = normalized["source_path"]
        if "-explanations/" in path:
            continue

        # 空文档 / 路径不存在检测（防 Claude 引用空文件后凭 snippet 编内容）
        if not _is_real_vault_file(path):
            skipped_empty += 1
            continue

        raw_content_for_check = str(raw.get("content", "") or "") or normalized.get("snippet", "")

        # RAG-S2 T5: MCP profile — 完整 chunk 正文挂 material。hook 链不传
        # include_content, content 键不存在 → XML/prompt 面不变。
        # ⛔ 必须在 taint 扫描之前挂载 (审查 HIGH-2): 交付面 = 扫描面 —
        # 否则 payload 藏在 301 字之后 (snippet 只截前 300 字) 即绕过扫描,
        # MCP 全文交付成 prompt injection 绕行通道。
        if include_content:
            normalized["content"] = raw_content_for_check

        # Phase A0.5-P + P0-3c: prompt injection taint 扫描 (multi-field).
        # 旧逻辑只扫 snippet → 攻击者把 payload 埋 frontmatter title / wikilink /
        # source_path 即可绕过 (snippet 看着干净 → clean → 整条进 prompt).
        # 新逻辑扫描 snippet + title + wikilink + source_path (+ MCP profile 的
        # content 全文) 各跑一遍 taint scan, 取 max risk_score + worst taint level.
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
        if _is_link_list_chunk(raw_content_for_check):
            normalized["is_link_list_chunk"] = True

        # RAG-S2 T4: CE 输入透传 — material 只留 300 字 snippet, 完整 content
        # 仅此循环可得; 截 2000 字 (retrieval_reranker MaxP 切 5×400 字窗口,
        # 单 400 字头截断会漏掉 chunk 尾部正解 — 咖啡句实测 ce=0.0000;
        # 2000 字覆盖英文 500-token chunk)。
        # _filter_score = 本轮预过滤用的语义分, 回落分支重过滤同量纲。
        normalized["_ce_text"] = raw_content_for_check[:2000]
        normalized["_filter_score"] = score

        # P0-D (2026-05-12 hotfix): tier-2 legacy fallback flag 必须从 raw
        # 透传到 normalized, 否则下面 any(...is_legacy_fallback) 永不命中.
        # raw['is_legacy_fallback'] 由 _two_tier_search tier-2 路径设置 (top-level
        # 也保留以备 metadata 嵌套不一致).
        if raw.get("is_legacy_fallback") or (raw.get("metadata") or {}).get("is_legacy_fallback"):
            normalized["is_legacy_fallback"] = True

        materials.append(normalized)
        # 审查 HIGH (2026-08-10): 放宽地板 (0.30) 的行不得占 top_k_max 配额 —
        # 否则低分行挤占名额把 raw>=min_relevance 的正解挤出池, 回落重过滤后
        # 找不回、门控路径 CE 也见不到。2× 总量护栏防池爆; 超额部分在
        # 门/回落过滤后统一收口回 top_k_max。
        if score >= min_relevance:
            n_above_min += 1
        if n_above_min >= top_k_max or len(materials) >= top_k_max * 2:
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

    # ── RAG-S2 T4 (2026-08-10): 源文件级 dedup + cross-encoder 交付门 ──
    # dedup 无条件生效 (用户实证 rank1/2 同文件重复的治法), 且在 CE 打分前
    # 执行以省 CE 调用量。排序不动 (见顶部分数契约: CE 不参与排序)。
    materials = _dedup_by_source(materials)

    # CE 门只在 min_relevance>0 (生产交付) 时激活 — 金集 Tier R
    # (min_relevance=0) 要全量排序, 不设门也不花 CE 预算。
    # tier-2 legacy 材料带人造 rank-decay 分 (0.31-0.50), CE 打分会
    # 掩盖 degraded 信号 — 同样跳过。
    gated = False
    if rerank_enabled and min_relevance > 0 and materials and not any(m.get("is_legacy_fallback") for m in materials):
        try:
            gated = await _apply_ce_gate(query, materials)
        except Exception as e:
            # 防御纵深 (审查): score_documents 契约是"绝不抛异常", 但本函数
            # T4 前的实际契约是"内部全降级不外抛" — 任何逃逸异常都不能
            # 毁掉已召回的材料, 走与 CE 失败同路的回落。
            logger.warning("[SupplementarySearch] CE 门异常逃逸, 回落", error=str(e)[:120])
            gated = False

    gate_killed_all = False
    if gated:
        # CE 是交付判官: 垃圾 (语义无关但 embedding 分虚高) 被门杀,
        # 低 raw 正解 (放宽预过滤放进来的) 被门放行。
        pre_gate_count = len(materials)
        materials = [m for m in materials if m.get("ce_score", 0.0) >= _CE_DELIVERY_FLOOR]
        gate_killed_all = pre_gate_count > 0 and not materials
        if gate_killed_all:
            # 观测区分 (审查 LOW): CE 整批枪毙 ≠ raw 分全低 — T5 confidence
            # 与 Ops 排障需要这个信号 (CE 盲区类 query 丢失走此路径)
            logger.warning(
                "[SupplementarySearch] CE 交付门杀光全部材料",
                pre_gate=pre_gate_count,
                query=query[:60],
            )
    elif rerank_enabled:
        # CE 失败/未激活: 收回放宽的预过滤 — 与旧版行为一致
        materials = [m for m in materials if m.get("_filter_score", m["score"]) >= min_relevance]

    # 放宽池的 2× 超额在门/回落过滤后收口回 top_k_max (加权序截尾)
    materials = materials[:top_k_max]

    # ── Elbow cut: 悬崖在**交付面序列** (dedup+CE 门/回落抽稀之后) 上定 ──
    # ⛔ T6 三轮金集 A/B 裁决 (2026-08-10, 勿无据翻案): 审查曾 CONFIRMED
    # 「门抽稀后幸存者 gap 是被移除条目两侧 gap 的叠加 (telescoping), 非
    # 语义悬崖, 会误砍 CE 已放行的材料」— 数学成立, 但两种"修复"都被金集
    # 打回: 悬崖域移到全量序列 → 同文件重复 chunk 填平真悬崖, 转录尾巴全
    # 放行 (交付污染 39.83→57.38% / FPR 6→8%); 移到 dedup 后门前 → 仍
    # 48.25% / 8%。门后序列的 telescoping 截断在真实分布上是净正收益的
    # 保守护栏 (+1.8pp 命中换不回 +8~17pp 污染), 交付面相邻落差本身就是
    # 用户可见的列表质量信号。保留 T4 行为; 数据见 T6 契约锁
    # test_gate_thinning_elbow_is_deliberate_t4_behavior。
    elbow_floor = _elbow_score_floor(materials, drop_threshold=elbow_drop_threshold)
    materials = [m for m in materials if m["score"] > elbow_floor][:hard_cap]

    # 内部字段收尾 (不进 XML/API 面)
    for m in materials:
        m.pop("_ce_text", None)
        m.pop("_filter_score", None)

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
            # T5: legacy 人造 rank-decay 分无真实背书 → level=none (degraded)
            "confidence": _build_retrieval_confidence(materials, gated=gated, degraded=True, reason=merged_reason),
        }

    if materials:
        empty_reason = None
    elif gate_killed_all:
        # 审查 LOW: CE 判官整批枪毙 ≠ raw 分全低 — 观测面必须可区分
        empty_reason = "ce_gate_all_filtered"
    else:
        empty_reason = "all_filtered_below_threshold"
    return {
        "materials": materials,
        "degraded": False,
        "reason": empty_reason,
        "confidence": _build_retrieval_confidence(
            materials,
            gated=gated,
            gate_killed_all=gate_killed_all,
            reason=empty_reason,
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RAG-S2 T5 (2026-08-10): retrieval_confidence — 诚实遥测
# ═══════════════════════════════════════════════════════════════════════════════


def _build_retrieval_confidence(
    materials: list[dict[str, Any]],
    *,
    gated: bool,
    gate_killed_all: bool = False,
    degraded: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    """查询级检索置信度 {level, signals} — 双面注入 (hook XML attr / MCP 顶层字段)。

    起始档位规则 (T5 计划 + 2026-08-10 金集探针校准):
      high   — CE 门放行 且 top1 双通道确认 (fts_confirmed) 且 ce_score>=0.5
      medium — 过了 CE 门 (每条幸存者都有 CE 背书), 或 top1 fts_confirmed
      low    — CE 回落/熔断/未启用: 只有加权分背书
      none   — 空交付或 degraded (含 tier2 legacy 人造 rank-decay 分)

    ⛔ fts_confirmed 只作遥测信号, 不进交付门 (T5 探针实锤不可分):
    zh 常用词 (节点/删除/平衡) 让垃圾 query 也大面积 FTS 命中 (n01 5 条 /
    n03 7 条 raw>=0.50 全 fts=True), 而真命中 a01/z05 的 Fundamentals
    (appended 咖啡段) 反而 fts=False — 词法双通道在本 vault 分布下救不了
    该救的、放进不该放的, 按计划回退遥测-only。

    signals 是内部观测量纲 — XML 面只渲染 level 离散档
    (ce_score not in xml 契约保持), MCP 面整个 dict 透出。
    """
    top = materials[0] if materials else None
    if degraded or top is None:
        level = "none"
    elif gated and top.get("fts_confirmed") and float(top.get("ce_score") or 0.0) >= 0.5:
        level = "high"
    elif gated or top.get("fts_confirmed"):
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "signals": {
            "fts_confirmed_count": sum(1 for m in materials if m.get("fts_confirmed")),
            "delivered": len(materials),
            "ce_gated": gated,
            "ce_gate_all_filtered": gate_killed_all,
            "degraded_reason": reason if (degraded or not materials) else None,
            "top_score": round(float(top.get("score") or 0.0), 4) if top else 0.0,
        },
    }


def _empty_result(reason: str | None, *, degraded: bool) -> dict[str, Any]:
    """空交付/降级的统一返回体 (T5: 每条早退路径都必须带 confidence)。"""
    return {
        "materials": [],
        "degraded": degraded,
        "reason": reason,
        "confidence": _build_retrieval_confidence([], gated=False, degraded=degraded, reason=reason),
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
        # RAG-S2 T5: 降级/空交付定义即 none — 让 Claude 能区分
        # 「检索降级/CE 全杀/真无材料」而不是无声空白
        attrs += ' confidence="none"'
        return f"<supplementary_materials {attrs}/>"

    # RAG-S2 T5: 查询级置信度只渲染离散档位 (high/medium/low/none), 裸分数
    # (ce_score/top_score 等 signals) 是内部量纲不进 prompt 面。confidence
    # 键缺失时不渲染 attr — 老调用方/手工构造 dict 向后兼容。
    conf_level = (result.get("confidence") or {}).get("level")
    conf_attr = f' confidence="{_xml_escape(str(conf_level))}"' if conf_level else ""
    parts = [f'<supplementary_materials count="{len(materials)}"{conf_attr}>']
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
                f"[REDACTED: suspicious content (risk={injection_risk:.2f}); open source_path manually to verify]"
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
        # RAG-S2 T5 (审查 HIGH-2): MCP profile 的完整正文也要扫 — 交付面 =
        # 扫描面。hook 链无 content 键 → 空串跳过, 成本不变。
        material.get("content", "") or "",
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


def _elbow_score_floor(
    materials: list[dict[str, Any]],
    drop_threshold: float = 0.05,
) -> float:
    """全量加权序列上的 elbow 悬崖分数线（业界推荐做法 vs 硬编码 top_k）.

    用户原话: "我没硬编码要多少材料，要把有用的材料都提供给我"
    → 当相邻 score 差 > drop_threshold 视为"相关性悬崖"
    → 返回悬崖下沿分数 s_cut: score <= s_cut 的条目应被截断; 无悬崖返回
      -inf (全保留)。

    RAG-S2 T6 (2026-08-10): 由旧 _elbow_cut(列表截断) 重写为分数线模式,
    行为等价 (悬崖下沿之下截断 + 调用方 [:hard_cap] 收口)。作用域是
    **交付面序列** (dedup+门抽稀之后) — 三轮金集 A/B 裁决保留 T4 行为,
    理由与数据见 search_supplementary 调用点注释。
    """
    for i in range(1, len(materials)):
        gap = materials[i - 1]["score"] - materials[i]["score"]
        if gap > drop_threshold:
            return float(materials[i]["score"])
    return float("-inf")


# T4: taint 严重度序 — dedup 合并时幸存者继承组内最严 taint (fail-closed)
_TAINT_SEVERITY = {"clean": 0, "review": 1, "quarantine": 2}


def _dedup_by_source(materials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """RAG-S2 T4: 源文件级收敛 — 同 source_path 多 chunk 只留最高分一条。

    用户实证: top 结果 rank1/2 同文件相邻 chunk 重复 (chunk 粒度索引 +
    分数相邻 + 交付层无去重)。materials 已按 score 降序 → 首见即最高分。
    fail-closed 合并: 幸存者继承组内最严 taint / 最高 injection_risk /
    legacy 旗帜 (防 dedup 洗掉安全标记)。注意: CE 回落路径下放宽池
    (raw 0.30-0.50) 同源 chunk 的 taint 也会被继承 — 方向保守, 接受。
    CE 证据合并 (审查 MEDIUM): 被合并 chunk 的 _ce_text 在 MaxP 预算内
    拼给幸存者 — 否则同文件正解落在低分 chunk 时 CE 只见高分 chunk 的
    无关文本, 整个文件被交付门误杀 (头截断瞎评的文件粒度重现)。
    """
    kept: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for idx, m in enumerate(materials):
        key = m.get("source_path") or f"__no_path_{idx}"
        keeper = kept.get(key)
        if keeper is None:
            kept[key] = m
            order.append(key)
            continue
        if _TAINT_SEVERITY.get(m.get("taint", "clean"), 0) > _TAINT_SEVERITY.get(keeper.get("taint", "clean"), 0):
            keeper["taint"] = m["taint"]
        keeper["injection_risk"] = max(
            float(keeper.get("injection_risk", 0.0) or 0.0),
            float(m.get("injection_risk", 0.0) or 0.0),
        )
        if m.get("is_legacy_fallback"):
            keeper["is_legacy_fallback"] = True
        # T5: 词法确认按文件粒度继承 (a01 实证: 咖啡段藏在低分 chunk, 其
        # FTS 命中不继承则文件级 fts_confirmed 失真)。只作 confidence
        # 遥测信号, 不进交付门 (探针实锤不可分, 见 _build_retrieval_confidence)。
        if m.get("fts_confirmed"):
            keeper["fts_confirmed"] = True
        merged_ce_text = m.get("_ce_text")
        if merged_ce_text:
            base_ce_text = keeper.get("_ce_text") or ""
            if merged_ce_text not in base_ce_text:
                combined = f"{base_ce_text}\n{merged_ce_text}" if base_ce_text else merged_ce_text
                keeper["_ce_text"] = combined[:2000]
    return [kept[k] for k in order]


async def _apply_ce_gate(query: str, materials: list[dict[str, Any]]) -> bool:
    """RAG-S2 T4: 整批 cross-encoder 打分 — 只写 ce_score, ⛔ 不重排。

    ce_score 供调用方做交付门 (_CE_DELIVERY_FLOOR) 与 T5 confidence 观测。
    不排序的原因见模块顶部分数契约 (两轮金集校准实证 CE 排序让转录反扑)。

    整批失败 (超时/500/熔断/响应缺洞) → 返回 False 且不写任何分,
    调用方走回落分支 (行为与无 CE 一致)。
    """
    docs = [m.get("_ce_text") or m.get("snippet", "") or "" for m in materials]
    scores = await retrieval_reranker.score_documents(query, docs)
    if scores is None:
        return False
    for m, ce in zip(materials, scores):
        m["ce_score"] = ce
    return True


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
            # R3 第二层防御 (2026-07-12): exam_board 加入查询侧排除 — 索引黑名单
            # 是单层防御 (incremental/index_single_file 曾有旁路), 考题万一入库
            # 也在查询层拦住, 信息隔离 (d=1.50) 不再靠单点
            exclude_doc_types=["whiteboard", "exam_board"],
        )
    except Exception as e:  # noqa: BLE001  T5 审查 HIGH-1: 任何异常都走 vector 回退
        logger.warning(
            "[SupplementarySearch] tier-1 hybrid 失败，回退到 vector-only",
            error=str(e)[:120],
        )
        try:
            results = await client.search(
                query=query,
                table_name="vault_notes",
                num_results=num_results,
                # RAG-S2 T5 (2026-08-10): 回退分支此前漏排 exam_board — hybrid
                # 异常时 vector-only 路径成了考题隔离 (HARD-ISO) 的旁路, 与
                # Tier-1 口径对齐。
                exclude_doc_types=["whiteboard", "exam_board"],
            )
        except Exception as e2:  # noqa: BLE001
            # T5 审查 HIGH-1: 两级都异常 = 基础设施故障, 不得吞成 [] —
            # 旧行为会让上层判成 empty_index (degraded=False), MCP 面报
            # ok_empty、hook 面标「检索正常但无材料」, 阶段 0 契约 3
            # (健康空 ≠ 故障) 被打穿。包成 RuntimeError 走 search_failed
            # 降级通道 (search_supplementary 只捕 RuntimeError/Connection/
            # ValueError, 裸 re-raise 会逃逸破坏"内部全降级不外抛"契约)。
            raise RuntimeError(f"tier-1 search failed (hybrid+vector): {str(e2)[:80]}") from e2

    if results:
        return results

    # Wave-5 Stage C P1-9 (ChatGPT v4) — Tier-2 fallback gated by env var.
    # Default production: skip tier-2 to prevent cross-vault leak via legacy
    # unprefixed table (residual Story 1.9 升级前老索引). Dev / single-vault
    # legacy can opt-in with ENABLE_LANCEDB_TIER2_FALLBACK=true.
    if not _enable_tier2_fallback():
        return []

    # Tier-2 enabled — emit warning so Ops sees we're running in legacy mode.
    try:
        _active_vault_id = ""
        try:
            from app.config import get_settings as _gs

            _active_vault_id = getattr(_gs(), "vault_id", "") or ""
        except Exception:  # noqa: BLE001  config 缺失时不阻断 fallback
            _active_vault_id = ""
        logger.warning(
            "[SupplementarySearch] tier-2 fallback enabled — single-vault legacy mode "
            "(ENABLE_LANCEDB_TIER2_FALLBACK=true); cross-vault leak risk if residual "
            "unprefixed vault_notes carries other vaults' data",
            vault_id=_active_vault_id,
            query=query[:60],
        )
    except Exception:  # noqa: BLE001  日志失败不阻断
        pass

    # ── Tier 2 ── unprefixed legacy table（兼容老索引；Story 1.9 升级前的数据）
    try:
        if not (hasattr(client, "_db") and client._db is not None):
            return []
        list_tables_fn = (
            client._db.list_tables if hasattr(client._db, "list_tables") else getattr(client._db, "table_names", None)
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
            rank_score = 0.50 - 0.19 * (idx / max(df_size - 1, 1)) if df_size > 1 else 0.50
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
    # RAG-S2 T2 (2026-08-09): confidence 地基三字段透传 —
    # raw_score(未加权语义分, 权重污染后可回算真实相关度) +
    # rrf/fts 融合信号(区分双通道确认 vs dense-only, 此前 convert 层丢弃)。
    raw_score = raw.get("_raw_score")
    doc_type = metadata.get("doc_type", "") or raw.get("doc_type", "") or ""
    # RAG-S2 T6 审查修复 (2026-08-10): 双通道确认改用 _fts_hit — 旧公式
    # bool(_rrf_score) 名实颠倒: _rrf_score 写给所有融合行 (含 dense-only
    # 甚至 FTS 分支整个挂掉的批次), dense-only 恒 True、真词法命中
    # (FTS-only) 反而 False。现语义 = 出现在 FTS 通道 且 非 FTS-only
    # (vector 亦命中) = 真·双通道确认。仍只做 confidence 遥测, 不进交付门。
    fts_confirmed = bool(metadata.get("_fts_hit")) and not metadata.get("_fts_only")

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
        display_heading = re.sub(r"\s+-\s*$", "", display_heading).strip()  # 末尾 ` -` 残留
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
        # RAG-S2 T2: confidence 地基 (raw_score=未加权语义分 /
        # doc_type=按类型加权与断言用 / fts_confirmed=双通道确认)
        "raw_score": raw_score,
        "doc_type": doc_type,
        "fts_confirmed": fts_confirmed,
    }


def _xml_escape(text: str) -> str:
    """最小 XML 安全转义（防止 vault 笔记内容里的 `<` / `&` 破坏 XML 解析）。"""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("\n", " ")
    )
