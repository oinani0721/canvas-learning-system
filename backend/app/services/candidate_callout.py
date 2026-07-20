"""方案 A 双写回显 (轨道 B · 2026-07-20) — 错误候选正文 callout 渲染与 upsert。

背景: error_candidates[] 只存 frontmatter, 节点正文/Dashboard 无人类可读
视图 (UAT C2 观察 c)。方案 A 定稿 (用户 2026-07-20 拍板 + 样稿确认):
候选状态变更时在节点正文同步维护三态卡片 —
  pending  → [!error-candidate]+ 🔴 待复盘
  accepted → [!success]+ ✅ 已确认误区
  disputed/dismissed → [!warning]+ ⚠️ 已异议/已忽略
视觉格式以 `canvas-vault/样稿-错误候选复盘UX-方案A预览.md` 为真相源,
按 2026-07-20 对抗审查裁决修正三条硬要求:
  ① raw_dialog_excerpt 为空禁止渲染"你说过"句式 (生产链该字段恒空,
     error_extractor.py:154) → 改「AI 从会话归纳（无逐字引语）」
  ② provenance: seeded|distilled — seeded 卡片带「测试种子」角标
  ③ 卡片默认只展示 misconception; correction 放嵌套折叠 callout

锚点: 卡片标题行尾部埋 `%%cand:<id>%%` 注释 (阅读视图不可见),
upsert 按锚点整块替换。用户手删卡片的容错 (提案风险提示): 状态变更
时锚点缺失 → 只改 frontmatter 不补卡片 (append_if_missing=False);
新候选写入 → 直接追加 (append_if_missing=True)。
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

#: description 单字段拆分 misconception / correction (P5 / 裁决风险 4)。
#: 生产语料格式 "认为 X — 实际上 Y" / "认为 X — 反例 Z; 更正 Y"。
_SPLIT_RE = re.compile(r"\s*[—–]\s*|\s+-\s+(?=实际上|反例|更正|正确)")


def split_description(description: str) -> tuple[str, str]:
    """description → (misconception, correction)。无分隔符时 correction 为空。"""
    if not description:
        return "", ""
    parts = _SPLIT_RE.split(description, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return description.strip(), ""


def candidate_misconception(candidate: dict[str, Any]) -> str:
    """读侧回退链: misconception 字段 → description 拆分前半句。"""
    explicit = (candidate.get("misconception") or "").strip()
    if explicit:
        return explicit
    return split_description(candidate.get("description") or "")[0]


def candidate_correction(candidate: dict[str, Any]) -> str:
    explicit = (candidate.get("correction") or "").strip()
    if explicit:
        return explicit
    return split_description(candidate.get("description") or "")[1]


def _marker(candidate_id: str) -> str:
    return f"%%cand:{candidate_id}%%"


def _evidence_line(candidate: dict[str, Any]) -> str:
    """硬要求①: 无逐字引语禁止"你说过"句式。"""
    excerpt = (candidate.get("raw_dialog_excerpt") or "").strip()
    if excerpt:
        if len(excerpt) > 120:
            excerpt = excerpt[:120] + "…"
        return f"> 依据：你在会话中说「{excerpt}」"
    return "> 依据：AI 从会话归纳（无逐字引语）"


def _provenance_badge(candidate: dict[str, Any]) -> str:
    """硬要求②: seeded 候选在标题行带角标。"""
    return " · 测试种子" if candidate.get("provenance") == "seeded" else ""


def _correction_block(candidate: dict[str, Any]) -> list[str]:
    """硬要求③: correction 嵌套折叠 callout, 默认不展开。"""
    correction = candidate_correction(candidate)
    if not correction:
        return []
    return [
        "> > [!note]- 更正参考（折叠）",
        f"> > {correction}",
    ]


def render_candidate_callout(
    candidate: dict[str, Any],
    state: str,
    *,
    dispute_reason: Optional[str] = None,
    today: Optional[str] = None,
) -> str:
    """按样稿渲染三态卡片。state ∈ pending|accepted|disputed|dismissed。"""
    cid = candidate.get("id") or ""
    mark = _marker(cid)
    mis = candidate_misconception(candidate) or "（无描述）"
    day = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    badge = _provenance_badge(candidate)

    if state == "pending":
        conf = candidate.get("confidence")
        conf_str = f"{float(conf):.2f}" if conf is not None else "?"
        ptype = candidate.get("pedagogy_type") or "misconception"
        lines = [
            f"> [!error-candidate]+ 🔴 待复盘 · AI 建议（置信 {conf_str} · {ptype}）{badge} {mark}",
            f"> **{mis}**",
            _evidence_line(candidate),
            *_correction_block(candidate),
            "> 处理：`Cmd+P` →「复盘错误候选」（或 Dashboard 点本节点的处理按钮）",
        ]
    elif state == "accepted":
        lines = [
            f"> [!success]+ ✅ 已确认误区（{day} 复盘）{badge} {mark}",
            f"> **{mis}**",
            "> 已移入 errors[]，之后的考察会针对这个误区出题",
        ]
    elif state == "disputed":
        reason = (dispute_reason or candidate.get("dispute_reason") or "").strip()
        reason_part = f" · 理由：{reason}" if reason else ""
        lines = [
            f"> [!warning]+ ⚠️ 已异议（{day} 复盘{reason_part}）{badge} {mark}",
            f"> ~~{mis}~~",
            "> 不入 errors[]，不会用于出题",
        ]
    else:  # dismissed / expired 等终态
        lines = [
            f"> [!warning]+ ⚠️ 已忽略（{day} 复盘）{badge} {mark}",
            f"> ~~{mis}~~",
            "> 不入 errors[]，不会用于出题",
        ]
    return "\n".join(lines)


def upsert_candidate_callout(
    body: str,
    candidate_id: str,
    callout_md: str,
    *,
    append_if_missing: bool,
) -> tuple[str, bool]:
    """按 %%cand:<id>%% 锚点整块替换; 缺锚点按策略追加或跳过。

    Returns:
        (new_body, changed)
    """
    mark = _marker(candidate_id)
    lines = body.split("\n")
    anchor_idx = next((i for i, ln in enumerate(lines) if mark in ln), None)

    if anchor_idx is None:
        if not append_if_missing:
            return body, False
        sep = "" if body.endswith("\n\n") else ("\n" if body.endswith("\n") else "\n\n")
        return f"{body}{sep}{callout_md}\n", True

    # 锚点行向上找块首 (连续 > 行), 向下吞整个引用块
    start = anchor_idx
    while start > 0 and lines[start - 1].startswith(">"):
        start -= 1
    end = anchor_idx
    while end + 1 < len(lines) and lines[end + 1].startswith(">"):
        end += 1
    new_lines = lines[:start] + callout_md.split("\n") + lines[end + 1 :]
    return "\n".join(new_lines), True
