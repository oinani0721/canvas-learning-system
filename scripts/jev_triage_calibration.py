#!/usr/bin/env python3
"""Jev 分诊校准器 — 用 codex 审查记录回测分诊的命中率与误报率。

输入若干份 jev_review_triage.py 生成的报告（JSON），对每份报告从 commit
消息中提取卡号，并在审查目录找到该卡的全部 codex 审查轮次，解析出
「文件 × 严重度」的发现分布（ground truth），再与 Jev 的分诊标记逐文件对照，
汇总高危召回、标记命中率与漏报/误报清单。

用途：分诊口径调优与采用决策的回归证据；建议每积累 20-30 张卡复校一次。

用法:
  python scripts/jev_triage_calibration.py --reports /tmp/jev-reports
  python scripts/jev_triage_calibration.py --reports /tmp/jev-reports --out /tmp/calib.json

参数:
  --reports      分诊报告目录（递归收集 *.json；兼容旧式 report.json，
                 其 code_files 缺失时回退读取同目录 code_files.txt 第一列）
  --review-dir   审查记录目录（默认 _bmad-output/审查，相对当前工作目录）
  --out          校准结果 JSON 输出路径（默认 <reports>/jev-calibration.json）

返回码:
  0 - 成功 / 1 - 失败（目录不存在或无有效报告）

口径说明: 发现解析兼容审查文件的「章节式」（## MEDIUM：N + ### M1．）与
「行内式」（- **① MEDIUM —**）两种格式；严重度归因为「发现块内引用的文件
继承该发现的严重度」，属近似口径，非逐条人工判读。ground truth 指审查者
提出过什么，不构成缺陷存在的证明。
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from typing import Any

WEIGHT = {"BLOCKER": 3.0, "HIGH": 2.0, "MEDIUM": 1.0, "LOW": 0.5}
SEV_KEYS = ("BLOCKER", "HIGH", "MEDIUM", "LOW")

FILE_RE = re.compile(r"([A-Za-z0-9_\-]+\.(?:py|ts|tsx|sh|js))(?::\d+)?")
COUNT_LINE_RE = re.compile(r"(BLOCKER|HIGH|MEDIUM|LOW)\s*(\d+)")
HEADER_SEV_RE = re.compile(r"^\s*#{2,4}\s*(BLOCKER|HIGH|MEDIUM|LOW)\s*[:：]")
BULLET_SEV_RE = re.compile(r"^\s*(?:[-*]\s+|\d+[\.、]\s*)?\*\*\s*[①-⑳⓪\d]*\s*(BLOCKER|HIGH|MEDIUM|LOW)\s*[—–\-:：]")
NONE_SEV_RE = re.compile(r"^\s*[-*]?\s*\*\*(BLOCKER|HIGH|MEDIUM|LOW)\s*[:：]\s*无")
SUBFINDING_RE = re.compile(r"^\s*#{3,4}\s*[MHLB]\d+[．.、]")
CARD_RE = re.compile(r"CARD-([A-Za-z0-9\-]+)")


def find_reviews(review_dir: str, card: str) -> list[tuple[int, str]]:
    patterns = [
        f"codex-review-CARD-{card}.md",
        f"codex-review-CARD-{card}-r*.md",
        f"codex-review-CARD-{card}-round*.md",
    ]
    found: set[str] = set()
    for pattern in patterns:
        found.update(glob.glob(os.path.join(review_dir, pattern)))
    rounds: list[tuple[int, str]] = []
    for path in sorted(found):
        if ".body.md" in path:
            continue
        match = re.search(r"-r(\d+)\.md$", path)
        rounds.append((int(match.group(1)) if match else 1, path))
    return sorted(rounds)


def parse_reviews(rounds: list[tuple[int, str]]) -> tuple[dict[str, dict[str, int]], list[tuple[int, list[int]]]]:
    per_file: dict[str, dict[str, int]] = {}
    round_counts: list[tuple[int, list[int]]] = []
    for number, path in rounds:
        text = open(path, encoding="utf-8", errors="replace").read()
        for line in text.splitlines():
            found = dict(COUNT_LINE_RE.findall(line))
            if len(found) == 4:
                round_counts.append((number, [int(found[k]) for k in SEV_KEYS]))
                break
        cur: str | None = None
        recent: set[str] = set()
        for line in text.splitlines():
            header = HEADER_SEV_RE.match(line)
            if header:
                cur = header.group(1)
                recent = set()
                continue
            if re.match(r"^\s*#{1,2}\s+\S", line):
                cur = None
                recent = set()
                continue
            if NONE_SEV_RE.match(line):
                cur = None
                continue
            bullet = BULLET_SEV_RE.match(line)
            if bullet:
                cur = bullet.group(1)
                recent = set()
                continue
            if SUBFINDING_RE.match(line):
                recent = set()
                continue
            files = {os.path.basename(f) for f in FILE_RE.findall(line)}
            if cur and files:
                for name in files - recent:
                    per_file.setdefault(name, {})
                    per_file[name][cur] = per_file[name].get(cur, 0) + 1
                recent |= files
    return per_file, round_counts


def gt_of(per_file: dict[str, dict[str, int]], name: str) -> dict[str, Any]:
    counts = per_file.get(name, {})
    return {
        "BLOCKER": counts.get("BLOCKER", 0),
        "HIGH": counts.get("HIGH", 0),
        "MEDIUM": counts.get("MEDIUM", 0),
        "LOW": counts.get("LOW", 0),
        "weight": sum(WEIGHT[k] * v for k, v in counts.items()),
        "has_high": (counts.get("BLOCKER", 0) + counts.get("HIGH", 0)) > 0,
        "has_any": sum(counts.values()) > 0,
    }


def load_code_files(report_path: str, report: dict[str, Any]) -> list[str]:
    code_files = report.get("code_files")
    if code_files:
        return [os.path.basename(f) for f in code_files]
    sibling = os.path.join(os.path.dirname(report_path), "code_files.txt")
    if os.path.exists(sibling):
        names = []
        for line in open(sibling, encoding="utf-8", errors="replace"):
            parts = line.strip().split("\t")
            if len(parts) == 3:
                names.append(os.path.basename(parts[2]))
        return names
    return []


def analyze_card(report_path: str, review_dir: str, agg: dict[str, int]) -> dict[str, Any] | None:
    report = json.load(open(report_path, encoding="utf-8"))
    subject = report.get("commit", "")
    match = CARD_RE.search(subject)
    if not match:
        print(f"跳过（无法提取卡号）: {report_path}")
        return None
    card = match.group(1)
    code_files = load_code_files(report_path, report)
    review_files = find_reviews(review_dir, card)
    per_file, round_counts = parse_reviews(review_files)
    if not per_file and not round_counts:
        print(f"跳过（未找到审查记录）: CARD-{card}")
        return None

    jev: list[dict[str, Any]] = []
    for row in report["files"]:
        name = os.path.basename(row["file"])
        gt = gt_of(per_file, name)
        flagged = bool(row["flag"])
        if flagged and gt["has_high"]:
            verdict = "HIT-HIGH"
        elif flagged and gt["has_any"]:
            verdict = "HIT-MID"
        elif flagged:
            verdict = "FALSE-ALARM"
        elif gt["has_high"]:
            verdict = "MISSED-HIGH"
        elif gt["has_any"]:
            verdict = "low-pass"
        else:
            verdict = "clean-pass"
        agg[verdict.lower().replace("-", "_")] = agg.get(verdict.lower().replace("-", "_"), 0) + 1
        agg["judged"] += 1
        agg["flagged"] += 1 if flagged else 0
        jev.append({"file": name, "urgency": row["urgency"], "flagged": flagged, "gt": gt, "verdict": verdict})

    judged_names = {j["file"] for j in jev}
    unjudged_high = [f for f in code_files if f not in judged_names and gt_of(per_file, f)["has_high"]]
    agg["unjudged_high"] += len(unjudged_high)

    jev_top = max(jev, key=lambda j: j["urgency"])["file"] if jev else None
    candidates = [(f, gt_of(per_file, f)["weight"]) for f in code_files]
    candidates = [c for c in candidates if c[1] > 0] or [(j["file"], j["gt"]["weight"]) for j in jev]
    gt_top = max(candidates, key=lambda c: c[1])[0] if candidates else None
    agg["top1_total"] += 1
    if gt_top and jev_top == gt_top:
        agg["top1_hit"] += 1

    final_counts = round_counts[-1][1] if round_counts else [0, 0, 0, 0]
    print(
        f"\n===== CARD-{card} | 审查轮次: {len(review_files)} | 末轮 B/H/M/L = {'/'.join(map(str, final_counts))} ====="
    )
    print(f"{'file':<52} {'jevUrg':>6} {'flag':>7} {'GT H/M/L':>10}  verdict")
    for j in sorted(jev, key=lambda x: -x["urgency"]):
        gt = j["gt"]
        gts = f"{gt['HIGH']}+{gt['BLOCKER']}/{gt['MEDIUM']}/{gt['LOW']}"
        print(f"{j['file'][:52]:<52} {j['urgency']:>6.2f} {str(j['flagged']):>7} {gts:>10}  {j['verdict']}")
    if unjudged_high:
        print(f"  ⚠ 未被分诊的含 HIGH 文件: {unjudged_high}")
    print(f"  top1: jev={jev_top} | gt={gt_top}")

    return {
        "sha": report.get("sha"),
        "rounds": len(review_files),
        "final_counts_BHML": final_counts,
        "files": jev,
        "unjudged_high": unjudged_high,
        "jev_top": jev_top,
        "gt_top": gt_top,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Jev 分诊校准器")
    parser.add_argument("--reports", required=True, help="分诊报告目录（递归收集 *.json）")
    parser.add_argument("--review-dir", default=os.path.join("_bmad-output", "审查"), help="审查记录目录")
    parser.add_argument("--out", default=None, help="校准结果 JSON 输出路径")
    args = parser.parse_args()

    if not os.path.isdir(args.reports):
        sys.exit(f"报告目录不存在: {args.reports}")
    if not os.path.isdir(args.review_dir):
        sys.exit(f"审查目录不存在: {args.review_dir}")

    report_paths = sorted(glob.glob(os.path.join(args.reports, "**", "*.json"), recursive=True))
    agg: dict[str, int] = {
        "judged": 0,
        "flagged": 0,
        "hit_high": 0,
        "hit_mid": 0,
        "false_alarm": 0,
        "missed_high": 0,
        "low_pass": 0,
        "clean_pass": 0,
        "top1_hit": 0,
        "top1_total": 0,
        "unjudged_high": 0,
    }
    cards: dict[str, Any] = {}
    for path in report_paths:
        if os.path.basename(path).startswith("jev-calibration"):
            continue
        try:
            probe = json.load(open(path, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(probe, dict) or not isinstance(probe.get("files"), list):
            continue
        if not probe["files"] or "urgency" not in (probe["files"][0] or {}):
            continue
        result = analyze_card(path, args.review_dir, agg)
        if result:
            card_name = CARD_RE.search(str(probe.get("commit", "")))
            if card_name:
                cards[card_name.group(0)] = result

    if not cards:
        sys.exit("没有可分析的报告（检查 --reports 目录与报告格式）")

    print("\n================ AGGREGATE ================")
    print(f"judged files           : {agg['judged']}")
    print(f"flagged                : {agg['flagged']}")
    print(f"HIT-HIGH  (✓高危命中)   : {agg['hit_high']}")
    print(f"HIT-MID   (✓中危命中)   : {agg['hit_mid']}")
    print(f"FALSE-ALARM (✗误报)     : {agg['false_alarm']}")
    print(f"MISSED-HIGH (✗漏高危)   : {agg['missed_high']}")
    print(f"low-pass  (○低危放过)   : {agg['low_pass']}")
    print(f"clean-pass(○干净放过)   : {agg['clean_pass']}")
    print(f"top1 agreement         : {agg['top1_hit']}/{agg['top1_total']}")
    print(f"unjudged GT-high files : {agg['unjudged_high']}")

    out_path = args.out or os.path.join(args.reports, "jev-calibration.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"agg": agg, "cards": cards}, fh, ensure_ascii=False, indent=2)
    print(f"\n已保存: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
