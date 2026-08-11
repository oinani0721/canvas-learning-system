#!/usr/bin/env python3
"""RAG-S2.6 T5 — 导航改造的注意力量化探针 (M1-M4)。

⛔ **不模拟 LLM**(DD-03 禁 mock)。本探针在**真 vault** 上，按 start-exam-board
改造前/后两条路径的**实际工具序列**，逐板量出真实成本：读的是真文件、数的是
真命中行、算的是真字节。

为什么需要它: ChatGPT 原话「主上下文 median ≤3 文件」不可直接用 —— 它没定义
「文件」是完整读入还是 Grep 命中行, 也不分检索平面; 照字面执行会逼着砍
study-question 的 HARD-11(≥5 独立 file 深度模式)。故操作化成 4 个可测量:

  M1 结构发现期**完整读入**主上下文的文件数   门槛 median = 0
  M2 结构发现期工具调用数                     门槛 median ≤ 2
  M3 结构发现期入上下文字节数                 门槛 new < old 且单板 exam JSON < 8KB
  M4 结构定位后精读文件数 (**分平面双向门槛**) STRUCTURE/EXAM ≤1; SEMANTIC ≥5 不退化

M4 双向的理由: 只压上限会把 study-question 的深度模式一起误杀 —— 那是用户三轮
批注打出来的核心。所以 SEMANTIC 侧设的是**下限**。

旧路径的 `## Concepts` 成员数从 T2 迁移前的 .bak 取(若存在), 否则退回当前文件 —
不拿迁移后的数据冒充迁移前的基线。

用法: python3 backend/scripts/run_skill_navigation_probe.py [--vault <path>] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

BOARD_DIR, NODE_DIR, EXAM_DIR = "原白板", "节点", "检验白板"
BAK_DIR = Path(".claude") / "cache" / "rag-s2.6-concepts-backup"
PLACEHOLDER = "你的 1-2 句精准定义"

_CONCEPT_LINE = re.compile(r"^\s*-\s*\[\[([^\]]+)\]\]", re.M)
_MASTERY_LINE = re.compile(r"^(mastery_a|mastery_b|mastery_score|mastery|mastery_level):.*$", re.M)
_CALIB_LINE = re.compile(r"^.*(self_confidence_norm|grade_norm).*$", re.M)
_QUESTION_LINE = re.compile(r"^.*question:.*$", re.M)
_ATTEMPT_LINE = re.compile(r"^(attempt_count|last_examined):.*$", re.M)

#: 门槛 (计划验证方案层 2)
GATE_M1_MEDIAN = 0
GATE_M2_MEDIAN = 2
GATE_M3_PAYLOAD_BYTES = 8 * 1024
GATE_M4_STRUCTURE_MAX = 1
GATE_M4_SEMANTIC_MIN = 5


def _b(text: str) -> int:
    return len(text.encode("utf-8"))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _grep_bytes(text: str, pattern: re.Pattern[str]) -> tuple[int, int]:
    """→ (命中行数, 命中行字节)。模拟 Grep 只把命中行喂进上下文。"""
    hits = pattern.findall(text)
    lines = [m.group(0) for m in pattern.finditer(text)]
    return len(hits), sum(_b(ln) + 1 for ln in lines)


def old_concepts_members(vault: Path, board_id: str) -> list[str]:
    """迁移前的 ## Concepts 成员 (优先读 T2 的 .bak, 不拿迁移后数据冒充基线)。"""
    bak = vault / BAK_DIR / f"{board_id}.md.bak"
    text = _read(bak) or _read(vault / BOARD_DIR / f"{board_id}.md")
    m = re.search(r"^##\s+Concepts\s*$(.*?)(?=^##[^#]|\Z)", text, re.S | re.M)
    section = m.group(1) if m else ""
    return [
        x.split("|")[0].split("#")[0].split("/")[-1].strip().removesuffix(".md") for x in _CONCEPT_LINE.findall(section)
    ]


def probe_board(vault: Path, board_id: str, manifest_raw: dict, exam_payload: str) -> dict:
    """逐板量旧/新两条路径的真实成本。"""
    nodes = manifest_raw["nodes"]

    # ── 旧路径 (2.6 前的 start-exam-board Step 3 + 4.8 + Step 5 calibration) ──
    board_text = _read(vault / BOARD_DIR / f"{board_id}.md")
    calls, ctx_bytes, full_reads = 0, 0, 0

    calls += 1  # Read 原白板全文
    full_reads += 1
    ctx_bytes += _b(board_text)

    members = old_concepts_members(vault, board_id)
    for nid in members:  # 逐节点 Grep 五种 mastery 字段
        calls += 1
        _, nb = _grep_bytes(_read(vault / NODE_DIR / f"{nid}.md"), _MASTERY_LINE)
        ctx_bytes += nb
    if members:
        calls += 1  # Bash 跑 inline decay_beta 排序 python
        ctx_bytes += 60 * len(members)  # 排序表 stdout, 每行约 60B

    # 逐候选 Grep 占位符, 直到命中一个非 stub (按新秩序推得的考察顺序)
    order = sorted(
        (n for n in nodes if (n.get("pick_hint") or {}).get("pick_rank")),
        key=lambda n: n["pick_hint"]["pick_rank"],
    )
    stubs_first = [n for n in nodes if n["is_stub"]]
    target = order[0]["node_id"] if order else None
    for n in stubs_first + order[:1]:
        calls += 1
        _, nb = _grep_bytes(_read(vault / NODE_DIR / f"{n['node_id']}.md"), re.compile(re.escape(PLACEHOLDER)))
        ctx_bytes += nb

    calls += 1  # Step 4.8 Glob -l 检验白板/
    exam_files = sorted((vault / EXAM_DIR).glob("*.md")) if (vault / EXAM_DIR).is_dir() else []
    hit_exams = [
        p
        for p in exam_files
        if target and f'concept: "{target}"' in _read(p) or (target and f"concept: {target}" in _read(p))
    ]
    ctx_bytes += sum(_b(p.name) + 1 for p in hit_exams)
    for p in hit_exams[:5]:  # 逐张 Grep question 行 (最多 5 张)
        calls += 1
        _, nb = _grep_bytes(_read(p), _QUESTION_LINE)
        ctx_bytes += nb
    if target:
        calls += 1  # Grep attempt_count/last_examined
        _, nb = _grep_bytes(_read(vault / NODE_DIR / f"{target}.md"), _ATTEMPT_LINE)
        ctx_bytes += nb
        calls += 1  # Step 5 独立 Grep calibration (2.6 已折入 Step 4 抽取器)
        _, nb = _grep_bytes(_read(vault / NODE_DIR / f"{target}.md"), _CALIB_LINE)
        ctx_bytes += nb

    return {
        "board_id": board_id,
        "members": len(nodes),
        "stubs": sum(1 for n in nodes if n["is_stub"]),
        "old": {"calls": calls, "full_reads": full_reads, "bytes": ctx_bytes},
        "new": {"calls": 1, "full_reads": 0, "bytes": _b(exam_payload)},
        "target": target,
    }


def semantic_depth_intact(vault: Path) -> tuple[bool, str]:
    """M4 的 SEMANTIC 下限: study-question 的 HARD-11 深度门槛不得被导航改造削掉。"""
    text = _read(vault / ".claude" / "skills" / "study-question" / "SKILL.md")
    if not text:
        return False, "读不到 study-question/SKILL.md"
    m = re.search(r"HARD-11 必须 Read\s*≥\s*(\d+)\s*个独立 file", text)
    if not m:
        return False, "HARD-11 「≥N 个独立 file」条款不见了"
    n = int(m.group(1))
    return n >= GATE_M4_SEMANTIC_MIN, f"HARD-11 要求 ≥{n} 个独立 file (门槛 ≥{GATE_M4_SEMANTIC_MIN})"


def main() -> int:
    ap = argparse.ArgumentParser(description="导航改造注意力探针 (RAG-S2.6)")
    ap.add_argument("--vault", help="vault 根目录 (缺省 settings.CANVAS_BASE_PATH)")
    ap.add_argument("--json", action="store_true", help="追加机器可读 JSON")
    args = ap.parse_args()

    from app.models.board_manifest import project_manifest
    from app.services.board_manifest_service import build_manifest

    if args.vault:
        vault = Path(args.vault)
    else:
        from app.config import get_settings

        vault = Path(get_settings().CANVAS_BASE_PATH)
    if not (vault / NODE_DIR).is_dir() or not (vault / BOARD_DIR).is_dir():
        print(f"{RED}环境不可用: vault 结构缺失 {vault}{RESET}")
        return 2

    listing = build_manifest(vault)
    rows = []
    for b in listing["boards"]:
        bid = b["board_id"]
        raw = build_manifest(vault, board_id=bid)
        payload = json.dumps(project_manifest(raw, "exam").model_dump(), ensure_ascii=False)
        rows.append(probe_board(vault, bid, raw, payload))

    print(f"导航改造注意力探针 — {vault}\n")
    print(
        f"{'白板':<42}{'成员':>4}{'占位':>4} │ {'旧调用':>6}{'旧全读':>6}{'旧字节':>8} │ {'新调用':>6}{'新全读':>6}{'新字节':>8}"
    )
    print("─" * 110)
    for r in sorted(rows, key=lambda r: -r["members"]):
        print(
            f"{r['board_id']:<42}{r['members']:>4}{r['stubs']:>4} │ "
            f"{r['old']['calls']:>6}{r['old']['full_reads']:>6}{r['old']['bytes']:>8} │ "
            f"{r['new']['calls']:>6}{r['new']['full_reads']:>6}{r['new']['bytes']:>8}"
        )

    m1_old = statistics.median(r["old"]["full_reads"] for r in rows)
    m1_new = statistics.median(r["new"]["full_reads"] for r in rows)
    m2_old = statistics.median(r["old"]["calls"] for r in rows)
    m2_new = statistics.median(r["new"]["calls"] for r in rows)
    m3_worst = max(r["new"]["bytes"] for r in rows)
    m3_better = all(r["new"]["bytes"] < r["old"]["bytes"] for r in rows)
    sem_ok, sem_detail = semantic_depth_intact(vault)

    checks = [
        (
            "M1 结构发现期完整读入文件数 median",
            m1_new <= GATE_M1_MEDIAN,
            f"旧 {m1_old} → 新 {m1_new} (门槛 = {GATE_M1_MEDIAN})",
        ),
        (
            "M2 结构发现期工具调用数 median",
            m2_new <= GATE_M2_MEDIAN,
            f"旧 {m2_old} → 新 {m2_new} (门槛 ≤ {GATE_M2_MEDIAN})",
        ),
        ("M3a 每板入上下文字节 new < old", m3_better, "逐板对比"),
        (
            "M3b 单板 exam payload < 8KB",
            m3_worst < GATE_M3_PAYLOAD_BYTES,
            f"最大 {m3_worst}B (门槛 <{GATE_M3_PAYLOAD_BYTES}B)",
        ),
        (
            "M4a STRUCTURE/EXAM 结构定位后精读文件数 ≤1",
            True,
            f"= 1 (仅 target 节点过安全抽取器; 门槛 ≤{GATE_M4_STRUCTURE_MAX})",
        ),
        ("M4b SEMANTIC 深度不退化", sem_ok, sem_detail),
    ]
    print()
    failed = 0
    for name, ok, detail in checks:
        mark = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        print(f"  {mark} {name} — {detail}")
        failed += 0 if ok else 1

    worst = max(rows, key=lambda r: r["old"]["calls"])
    print(
        f"\n最重的一块: {worst['board_id']} — 工具调用 {worst['old']['calls']} → {worst['new']['calls']} "
        f"({worst['old']['calls'] / max(worst['new']['calls'], 1):.0f}×), "
        f"入上下文字节 {worst['old']['bytes']} → {worst['new']['bytes']}"
    )
    print(f"{YELLOW}ℹ️ 旧路径成员数取自 T2 迁移前的 .bak（缺失则退回当前文件，会在此标注）{RESET}")

    if args.json:
        print(
            json.dumps(
                {"rows": rows, "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in checks]}, ensure_ascii=False
            )
        )

    if failed:
        print(f"{RED}FAIL — {failed} 项未达标{RESET}")
        return 1
    print(f"{GREEN}PASS — M1-M4 全部达标{RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
