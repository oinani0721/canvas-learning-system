#!/usr/bin/env python3
"""每日复习选板 (DAILY-REVIEW-PUSH-2026-07-29, ChatGPT 终审 A3 修正版)。

扫 vault 节点/*.md frontmatter → 衰减 Beta 读时时效 pick → 板级 min 聚合
→ outputs/今日复习.md (人读) + outputs/今日复习.json (推送 payload, 终审 A7:
stdout 是瞬时数据, 推送失败补跑必须有持久化 payload)。

三态兼容 (live 实测 18 节点: 新字段 1 / 仅旧 10 / 无字段 7):
  mastery_a/b (+last_examined) → effective() 闲置折扣后 pick
  仅 mastery_score             → from_legacy() 均值继承低置信
  无字段                       → 先验 Beta(0.9,2.1), 从未考 σ 大自动优先

终审 A3 三修正:
  1. eligibility 与 start-exam-board 同规则 — 含「你的 1-2 句精准定义」
     占位符的未剖析节点跳过 (否则推荐无法出题的节点到手机)
  2. 输出命令绑定 node <top_node> — start-exam-board 自己重选点时不含
     闲置折扣, 不绑定会出现「通知说考 A 实际考 B」
  3. min() 并列 tie-break: 板上次被推荐日期(久者先) → 最老 last_examined
     → 板名 (防启动期先验板按扫描顺序永久霸榜)

依赖: 仅 stdlib + vault 内 decay_beta.py (launchd 环境无 pip 包可假设)。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

#: 与 start-exam-board SKILL Step 3 完全同一条占位符规则 (终审 A3)
PLACEHOLDER = "你的 1-2 句精准定义"

#: 生产数据污染标记 (对齐 memory-health.sh 批次1'⑥ 审计清单) — 不推测试节点。
#: ⚠ 只匹配文件名: 真实节点 frontmatter 可能引用测试会话 id (live 实测
#: Fundamentals 的 error_candidates 含 m3-e2e-sessionend-test, 按全文匹配会误杀)
TEST_MARKERS = ("TestConcept", "UAT-2.5", "m3-e2e")

#: [Decision-FSRS-2] WHEN/WHAT 分工 (FSRS-V2-2026-07-30):
#: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
#: 衰减 Beta 管 WHAT — 到期集合内按 pick=μ−σ 排序。
#: 本文件保持纯 stdlib: 只做 UTC 定长字符串日期比较, 不 import fsrs。

#: Bark 通知标题上限 (方案规范: ≤20 全角字符)
TITLE_LIMIT = 20


def _aware(s: str) -> datetime:
    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _fm_num(fm: str, key: str):
    # 容负号 (Code-Review L5): mastery_a: -3 应进 corrupt 分支而非静默当无字段
    m = re.search(rf'^{key}:\s*"?(-?[0-9]*\.?[0-9]+)"?\s*$', fm, re.M)
    return float(m.group(1)) if m else None


def _fm_str(fm: str, key: str):
    m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
    return m.group(1).strip() if m else None


def _board_name(raw: str | None):
    """source_board 归一化 → 板名 (live 数据实为 wikilink '[[原白板/X]]')。"""
    if not raw:
        return None
    name = raw.strip()
    if name.startswith("[[") and name.endswith("]]"):
        name = name[2:-2]
    name = name.split("|")[0]                 # [[path|alias]] 取 path
    name = name.rsplit("/", 1)[-1].strip()    # 原白板/X → X
    return name or None


def scan_nodes(vault: Path, now: datetime, decay):
    """扫描 节点/ 池 → (nodes, stats)。逐节点容错: 单个脏节点不崩全轮。"""
    stats = {"new": 0, "legacy": 0, "none": 0, "ineligible": 0, "test_excluded": 0, "corrupt": 0}
    now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    nodes = []
    for path in sorted((vault / "节点").glob("*.md")):
        stem = path.stem
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            stats["corrupt"] += 1
            print(f"[pick] 读取失败跳过 {stem}: {e}", file=sys.stderr)
            continue
        if any(mk in stem for mk in TEST_MARKERS):
            stats["test_excluded"] += 1
            continue
        m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
        fm, body = (m.group(1), m.group(2)) if m else ("", text)
        if PLACEHOLDER in body:
            stats["ineligible"] += 1
            continue

        a_raw, b_raw = _fm_num(fm, "mastery_a"), _fm_num(fm, "mastery_b")
        legacy = next(
            (v for k in ("mastery_score", "mastery", "mastery_level")
             if (v := _fm_num(fm, k)) is not None),
            None,
        )
        if a_raw is not None and b_raw is not None:
            a, b, state = a_raw, b_raw, "new"
        elif legacy is not None:
            a, b = decay.from_legacy(legacy)
            state = "legacy"
        else:
            a, b, state = decay.PRIOR_A, decay.PRIOR_B, "none"
        stats[state] += 1

        last_exam = _fm_str(fm, "last_examined")
        idle_days = None
        if last_exam:
            try:
                idle_days = max(0.0, (now - _aware(last_exam)).total_seconds() / 86400.0)
            except ValueError:
                print(f"[pick] last_examined 无法解析, 按从未考: {stem}", file=sys.stderr)
                last_exam = None
        try:
            # pick_score 也在 try 内 (Code-Review M2): 除零/溢出同属脏数据
            a_eff, b_eff = decay.effective(a, b, idle_days or 0.0)
            pick = decay.pick_score(a_eff, b_eff)
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            stats["corrupt"] += 1
            print(f"[pick] Beta 参数损坏跳过 {stem}: {e}", file=sys.stderr)
            continue

        fsrs_due = _fm_str(fm, "fsrs_due") or ""
        # Code-Review M2: Obsidian Properties 面板可能把 datetime 重新序列化成
        # 带偏移格式, 词法比较会反向误判「永不到期」。非规范格式 fail-open
        # 视同到期 (与 New 语义一致), 不静默消失。
        if fsrs_due and not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due):
            print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
            fsrs_due = ""
        nodes.append({
            "node": stem,
            "board": _board_name(_fm_str(fm, "source_board")),
            "state": state,
            "pick": pick,
            "idle_days": idle_days,          # None = 从未考
            "last_examined": last_exam or "",
            "fsrs_due": fsrs_due,
            "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
            "difficulty": _fm_str(fm, "fsrs_difficulty") or "",
        })
    return nodes, stats


def rank_boards(nodes, board_last_recommended: dict):
    """板级聚合: priority = min(pick), 终审 A3 tie-break。"""
    boards: dict[str, list] = {}
    unassigned = []
    for n in nodes:
        if not n["board"]:
            unassigned.append(n["node"])
            continue
        boards.setdefault(n["board"], []).append(n)

    ranked, upcoming = [], []
    for board, members in boards.items():
        due = [n for n in members if n["due_now"]]
        if not due:
            # WHEN: 全员未到期 → 不进推荐榜, 记最近的未来到期 (F1 放假语义)
            nxt = min(members, key=lambda n: n["fsrs_due"])
            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
            continue
        top = min(due, key=lambda n: n["pick"])   # WHAT: 到期集合内衰减 Beta 排序
        ranked.append({
            "board": board,
            "top_node": top["node"],
            "priority": round(top["pick"], 4),
            "pending": len(due),                   # 到期即待复习 (Decision-FSRS-2)
            "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
            "difficulty": top["difficulty"],
            "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
            "_tie": (
                round(top["pick"], 8),
                board_last_recommended.get(board, ""),   # 空串 = 从未被推荐, 排最前
                min(n["last_examined"] for n in due),    # 空串 = 有从未考节点, 排最前
                board,
            ),
        })
    ranked.sort(key=lambda r: r["_tie"])
    for r in ranked:
        del r["_tie"]
    upcoming.sort(key=lambda u: u["next_due"])
    return ranked, upcoming, unassigned


def _title(board: str) -> str:
    prefix = "📚 今日复习 · "
    room = TITLE_LIMIT - len(prefix)
    return prefix + (board if len(board) <= room else board[: room - 1] + "…")


def _body(top: dict) -> str:
    idle = "从未考察" if top["idle_days"] is None else f"已闲置 {top['idle_days']} 天"
    if top["pending"] >= 2:
        return f"{top['top_node']} 等 {top['pending']} 节点待巩固 · {idle}"
    return f"{top['top_node']} 待巩固 · {idle}"


def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
    nodes, stats = scan_nodes(vault, now, decay)
    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
    stats["unassigned"] = len(unassigned)
    stats["due_nodes"] = sum(1 for n in nodes if n["board"] and n["due_now"])
    stats["future_nodes"] = sum(1 for n in nodes if n["board"] and not n["due_now"])
    payload = {
        "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
        "schema_version": 2,             # v2: FSRS WHEN 化 (upcoming/due 语义)
        "date": now.astimezone().date().isoformat(),
        "generated_at": now.astimezone().isoformat(timespec="seconds"),
        "top_boards": ranked[:3],
        "upcoming": upcoming[:3],
        "stats": stats,
        "notification": None,
    }
    day_id = f"canvas-review-{payload['date']}"
    if ranked:
        payload["notification"] = {
            "title": _title(ranked[0]["board"]),
            "body": _body(ranked[0]),
            "group": "canvas复习",
            "id": day_id,
        }
    elif upcoming:
        # F1 放假语义: 有调度中的板但今天零到期 → 诚实说不用复习
        nxt = upcoming[0]
        payload["notification"] = {
            "title": "📚 今日无到期节点",
            "body": f"按计划推进，休息一天 · 最近到期 {nxt['board']} · {nxt['next_due'][:10]}",
            "group": "canvas复习",
            "id": day_id,
        }
    return payload, ranked


def render_md(payload, ranked) -> str:
    s = payload["stats"]
    lines = [
        f"# 今日复习 · {payload['date']}",
        "",
        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
        f" · 节点状态: new={s['new']} / legacy={s['legacy']}"
        f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
        f" / 未归板={s['unassigned']} / 损坏={s['corrupt']}",
        "",
        "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in ranked:
        idle = "从未考" if r["idle_days"] is None else f"{r['idle_days']} 天"
        nxt = r["next_due"][:10] if r["next_due"] else "-"
        diff = r["difficulty"] or "-"
        lines.append(
            f"| {r['board']} | {r['priority']} | {r['pending']} | {r['top_node']} | {diff} | {idle} | {nxt} |"
        )
    if payload.get("upcoming"):
        for u in payload["upcoming"]:
            lines.append(f"| {u['board']} | - | 0（未到期） | - | - | - | {u['next_due'][:10]} |")
    if ranked:
        lines += ["", "## 一键开考（整行复制到 Claudian）", ""]
        for r in ranked:
            lines.append(f"- `/start-exam-board from {r['board']} node {r['top_node']}`")
    else:
        lines += ["", "> ✅ 今日无到期节点，休息一天。"]
    if payload.get("unassigned_nodes"):
        lines += ["", "> ⚠ 未归板节点（无 source_board，不参与推荐）: "
                  + "、".join(payload["unassigned_nodes"])]
    lines += [
        "",
        "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
        "> （含闲置回升，证据质量半衰期 69 天）。未剖析占位节点已跳过；命令已绑定最该考节点。",
    ]
    return "\n".join(lines) + "\n"


def atomic_write(path: Path, content: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def load_decay(vault: Path):
    sys.path.insert(0, str(vault / ".claude" / "scripts"))
    import decay_beta
    return decay_beta


def main():
    ap = argparse.ArgumentParser(description="每日复习选板")
    ap.add_argument("--vault", required=True)
    ap.add_argument("--state", help="daily-review.state.json (只读, 取 board_last_recommended)")
    ap.add_argument("--now", help="ISO 时间覆盖 (测试用)")
    ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
    args = ap.parse_args()

    vault = Path(args.vault)
    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
    if args.now:
        dt = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        now = dt if dt.tzinfo else dt.astimezone()
    else:
        now = datetime.now(timezone.utc)
    blr = {}
    if args.state and Path(args.state).exists():
        try:
            blr = json.loads(Path(args.state).read_text(encoding="utf-8")).get(
                "board_last_recommended", {})
        except (json.JSONDecodeError, OSError):
            pass  # state 损坏由 runner 处置, 选点侧降级为无记录

    payload, ranked = build_payload(vault, now, blr, load_decay(vault))
    if args.write:
        out = vault / "outputs"
        out.mkdir(parents=True, exist_ok=True)
        atomic_write(out / "今日复习.md", render_md(payload, ranked))
        atomic_write(out / "今日复习.json",
                     json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
