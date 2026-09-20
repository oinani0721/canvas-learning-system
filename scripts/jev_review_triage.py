#!/usr/bin/env python3
"""Jev 审查分诊器 — 按文件为卡级代码 diff 生成审查优先级分诊表。

在卡级 squash 提交后、codex 深审前运行：把 commit 的代码 diff 按文件切片，
每个文件向 Jev（TypeSafe AI 的 System One 模型）提交一组类型化判断问题
（运行时影响 / 风险类别 / 审查紧急度 / 是否值得人工审查 / 是否缺测试），
排序、阈值与分诊结论全部由本脚本合成 —— 判断归模型，算术归代码。

与 codex 审查记录做过 8 卡校准（24 文件 / 40+ 轮对照）：高危文件召回 7/7，
标记命中率 17/20；建议每积累 20-30 张卡用 jev_triage_calibration.py 复校。

用法:
  export TYPESAFE_API_KEY=...          # console.typesafe.ai 创建
  python scripts/jev_review_triage.py <ref>
  python scripts/jev_review_triage.py 61b85b5b --out /tmp/triage.json

参数:
  ref               git ref（commit / sha），默认 HEAD
  --out             报告 JSON 输出路径（默认 ./jev-triage-<short-sha>.json）
  --max-files       最多分诊文件数（默认 6，按改动行数降序）
  --pathspec        路径限定（可重复；默认常见代码扩展名）

返回码:
  0 - 成功（报告已生成；存在 REVIEW 标记不代表失败）
  1 - 运行失败（缺少 API key / git 失败 / API 调用失败）

成本参考: 单文件一次 API 调用（约 3-6k input tokens，输出 token 免费），
实测单次延迟约 0.3 秒；单卡 6 个文件约合 $0.001 量级。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
DEFAULT_PATHSPECS = ["*.py", "*.ts", "*.tsx", "*.sh", "*.js"]
REVIEW_THRESHOLD = 0.6
URGENCY_THRESHOLD = 2.5
MAX_PATCH_CHARS = 10000

QUESTIONS: dict[str, dict[str, Any]] = {
    "runtime_effect": {
        "type": "noul",
        "instructions": "This file's changes affect runtime behavior (not docs, evidence, or test-only edits)",
    },
    "risk_category": {
        "type": "choice",
        "instructions": "Main category of risk introduced by this diff",
        "criteria": {
            "null_safety": "Missing or changed null/undefined/None handling",
            "error_handling": "Error paths, exceptions, or fallbacks changed",
            "concurrency_state": "State, caching, ordering, or concurrency",
            "api_contract": "Callers, schemas, or interfaces may break",
            "security": "Auth, secrets, injection, or data leakage",
            "logic": "Business logic may be wrong for some inputs",
            "test_or_docs": "Tests or documentation only",
            "none": "Nothing meaningful",
        },
    },
    "review_urgency": {
        "type": "score",
        "instructions": "How urgently does this file's diff need careful review before merge",
        "criteria": [
            "Trivial; safe as-is",
            "Minor; a quick skim suffices",
            "Moderate; worth checking edge cases",
            "High; deserves careful review",
            "Critical; likely to cause a bug or outage",
        ],
    },
    "needs_human_review": {
        "type": "noul",
        "instructions": "This file's changes deserve a dedicated human review before merge",
    },
    "needs_test": {
        "type": "noul",
        "instructions": "The changed logic here should gain or keep automated test coverage",
    },
}


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} 执行失败: {result.stderr.strip()}")
    return result.stdout


def parse_diff(text: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            if cur:
                files.append(cur)
            match = re.match(r"diff --git a/(.*?) b/(.*)$", line)
            cur = {"path": match.group(2) if match else line[11:], "lines": []}
        elif cur is not None and not line.startswith(
            ("index ", "new file mode", "deleted file mode", "similarity ", "rename ")
        ):
            cur["lines"].append(line)
    if cur:
        files.append(cur)
    for f in files:
        f["added"] = sum(1 for l in f["lines"] if l.startswith("+") and not l.startswith("+++"))
        f["removed"] = sum(1 for l in f["lines"] if l.startswith("-") and not l.startswith("---"))
        f["churn"] = f["added"] + f["removed"]
        f["patch"] = "\n".join(f["lines"])
    return [f for f in files if f["churn"] > 0]


def ask_jev(state: dict[str, Any], api_key: str, retries: int = 2) -> dict[str, Any]:
    payload = json.dumps({"model": MODEL, "state": state, "questions": QUESTIONS}).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    last_error: str = ""
    for attempt in range(retries + 1):
        try:
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read())
            data["_latency_ms"] = int((time.time() - t0) * 1000)
            return data
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:200]}"
            if exc.code < 500:
                break
        except Exception as exc:  # noqa: BLE001 — 网络类异常统一重试
            last_error = str(exc)
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(last_error)


def main() -> int:
    parser = argparse.ArgumentParser(description="Jev 审查分诊器")
    parser.add_argument("ref", nargs="?", default="HEAD", help="git ref（默认 HEAD）")
    parser.add_argument("--out", default=None, help="报告 JSON 输出路径")
    parser.add_argument("--max-files", type=int, default=6, help="最多分诊文件数（默认 6）")
    parser.add_argument("--pathspec", action="append", default=None, help="路径限定（可重复）")
    args = parser.parse_args()

    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        sys.exit("TYPESAFE_API_KEY 未设置（console.typesafe.ai 创建）")

    pathspecs = args.pathspec or DEFAULT_PATHSPECS
    sha = run_git(["rev-parse", args.ref]).strip()
    subject = run_git(["log", "-1", "--format=%s", args.ref]).strip()
    diff_text = run_git(["show", "--no-color", "--format=", args.ref, "--", *pathspecs])
    numstat_text = run_git(["show", "--numstat", "--format=", args.ref, "--", *pathspecs])

    code_files = []
    for line in numstat_text.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            code_files.append(parts[2])

    diff_files = parse_diff(diff_text)
    diff_files.sort(key=lambda f: -f["churn"])
    picked = diff_files[: args.max_files]
    out_path = args.out or f"jev-triage-{sha[:8]}.json"

    print(f"Ref:    {args.ref} ({sha[:12]})")
    print(f"Commit: {subject}")
    print(f"Files:  {len(diff_files)} 个含代码改动（分诊前 {len(picked)} 个，按 churn 降序）")

    rows: list[dict[str, Any]] = []
    usage_in = 0
    usage_out = 0
    latencies: list[int] = []
    resolved_model = MODEL
    for f in picked:
        patch = f["patch"]
        truncated = len(patch) > MAX_PATCH_CHARS
        state = {
            "commit_message": subject,
            "file": f["path"],
            "diff_stats": f"+{f['added']} -{f['removed']}" + (" (patch truncated)" if truncated else ""),
            "diff": patch[:MAX_PATCH_CHARS],
        }
        try:
            result = ask_jev(state, api_key)
        except RuntimeError as exc:
            sys.exit(f"Jev 调用失败: {exc}")
        resolved_model = result.get("model", resolved_model)
        answers = result["answers"]
        usage = result.get("usage", {})
        usage_in += usage.get("input_tokens", 0)
        usage_out += usage.get("output_tokens", 0)
        latencies.append(result["_latency_ms"])
        urgency = answers["review_urgency"]["score"]
        review = answers["needs_human_review"]["noul"]
        rows.append(
            {
                "file": f["path"],
                "added": f["added"],
                "removed": f["removed"],
                "runtime": answers["runtime_effect"]["noul"],
                "risk": answers["risk_category"]["choice"],
                "risk_conf": answers["risk_category"]["confidence"],
                "urgency": urgency,
                "urgency_conf": answers["review_urgency"]["confidence"],
                "review": review,
                "test": answers["needs_test"]["noul"],
                "truncated": truncated,
                "flag": review >= REVIEW_THRESHOLD or urgency >= URGENCY_THRESHOLD,
            }
        )

    rows.sort(key=lambda r: (-r["urgency"], -r["review"]))
    print()
    print(f"{'FILE':<60} {'CHURN':>9}  {'URG':>5}  {'REVIEW':>6}  {'TEST':>5}  {'RISK':<16} VERDICT")
    print("-" * 108)
    for r in rows:
        churn = f"+{r['added']}/-{r['removed']}"
        verdict = "REVIEW" if r["flag"] else "pass"
        print(
            f"{r['file'][-60:]:<60} {churn:>9}  {r['urgency']:>5.2f}  {r['review']:>6.2f}  "
            f"{r['test']:>5.2f}  {r['risk']:<16} {verdict}"
        )
    print("-" * 108)

    lat = sorted(latencies) if latencies else [0]
    print(f"Model: {resolved_model} | calls: {len(rows)} | input_tokens: {usage_in} | output_tokens: {usage_out}")
    print(f"Latency ms: min {lat[0]} / median {lat[len(lat) // 2]} / max {lat[-1]}")
    flagged = [r for r in rows if r["flag"]]
    print(f"标记人工审查: {len(flagged)}/{len(rows)}")
    for r in flagged:
        print(f"  - {r['file']}  (urgency {r['urgency']:.2f}, P(review)={r['review']:.2f}, risk={r['risk']})")

    report = {
        "commit": subject,
        "ref": args.ref,
        "sha": sha,
        "model": resolved_model,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "code_files": code_files,
        "files": rows,
        "usage": {"input_tokens": usage_in, "output_tokens": usage_out},
        "latency_ms": {"min": lat[0], "median": lat[len(lat) // 2], "max": lat[-1]},
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(f"\n报告已保存: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
