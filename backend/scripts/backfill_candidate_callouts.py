#!/usr/bin/env python3
"""方案 A 存量回填 (轨道 B · 2026-07-20) — 给现有 error_candidates 补正文卡片。

用户拍板决策点 5: 存量候选回填。对指定 vault 的 节点/*.md:
  1. provenance 缺失 → 按裁决回填 "seeded" (现存候选全部是测试种子,
     真实蒸馏写侧断裂中 — P14)
  2. misconception/correction 缺失 → description 拆分回填
  3. 按候选当前 status 在正文 upsert 对应三态卡片 (锚点幂等, 重跑安全)

用法:
  .venv/bin/python scripts/backfill_candidate_callouts.py <vault_path> [--dry-run]
  可选 --include <basename> 只处理指定节点 (默认全部, 跳过 UAT-*/Test*)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

from app.services.candidate_callout import (  # noqa: E402
    render_candidate_callout,
    split_description,
    upsert_candidate_callout,
)

#: 待删测试节点 (P2/B-4 等用户点头), 默认不回填
_SKIP_PREFIXES = ("UAT-", "TestConcept", "考察-")

_STATE_FOR_STATUS = {
    "pending": "pending",
    "accepted": "accepted",
    "edited": "accepted",
    "disputed": "disputed",
    "dismissed": "dismissed",
    "expired": "dismissed",
}


def _split(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---", 4)
    if end == -1:
        return "", text
    return text[4:end], text[end + 4 :].lstrip("\n")


def backfill_file(path: Path, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    fm_str, body = _split(text)
    if not fm_str:
        return False
    fm = yaml.safe_load(fm_str)
    if not isinstance(fm, dict):
        return False
    candidates = fm.get("error_candidates")
    if not isinstance(candidates, list) or not candidates:
        return False

    changed = False
    for cand in candidates:
        if not isinstance(cand, dict) or not cand.get("id"):
            continue
        if not cand.get("provenance"):
            cand["provenance"] = "seeded"
            changed = True
        if not cand.get("misconception"):
            mis, cor = split_description(cand.get("description") or "")
            cand["misconception"] = mis
            cand.setdefault("correction", cor)
            changed = True
        state = _STATE_FOR_STATUS.get(str(cand.get("status")), "pending")
        card = render_candidate_callout(
            cand, state, dispute_reason=cand.get("dispute_reason")
        )
        body, card_changed = upsert_candidate_callout(
            body, cand["id"], card, append_if_missing=True
        )
        changed = changed or card_changed

    if not changed:
        return False
    if dry_run:
        print(f"  [dry-run] 将更新 {path.name}")
        return True
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{new_fm}---\n{body}", encoding="utf-8")
    print(f"  ✓ 已回填 {path.name}")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("vault_path")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--include", default=None, help="只处理指定 basename")
    args = ap.parse_args()

    nodes_dir = Path(args.vault_path) / "节点"
    if not nodes_dir.is_dir():
        sys.exit(f"节点目录不存在: {nodes_dir}")

    total = 0
    for md in sorted(nodes_dir.glob("*.md")):
        if args.include and md.stem != args.include:
            continue
        if not args.include and md.name.startswith(_SKIP_PREFIXES):
            print(f"  ⏭ 跳过测试节点 {md.name} (待 P2 处置)")
            continue
        if backfill_file(md, args.dry_run):
            total += 1
    print(f"完成: {total} 个节点已回填")


if __name__ == "__main__":
    main()
