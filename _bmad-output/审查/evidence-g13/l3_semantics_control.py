#!/usr/bin/env python3
"""CARD-G1-3 —— L3「全称 vs 存在」语义对照实验（新门红 + 旧门绿）。

**为什么需要这个脚本**：L3 的缺陷是「命中第一份合格 manifest 就放行」。要把它暴露出来，
需要一个「一份合格 + 一份不合格」的输入。但 `9c4e7e82` 的树内**没有任何合格的 live
manifest**（只有 example-backfill-d5 那份 reconstructed），所以这个输入在真树上造不出来
——它不是不想测，是树上没有这个素材。

于是这里在临时目录里放两份 manifest（一份 live/dirty=false、一份 reconstructed），把
**旧实现**与**新实现**的判定逻辑各跑一遍，证明：同一个输入下旧门放行、新门拦下。
临时目录用完即弃，不碰仓内任何文件。

跑法: python3 l3_semantics_control.py     退出码恒 0（它是对照实验，不是门）
"""

from __future__ import annotations

import json
import os
import tempfile


def judge_old(repo: str, hits: list[str]) -> tuple[bool, str]:
    """旧实现：遍历，命中第一份合格的就 break —— 存在判据。"""
    good, why = False, ""
    for h in hits:
        full = os.path.join(repo, h)
        if not os.path.exists(full):
            why = f"{h} 不存在"
            continue
        with open(full, encoding="utf-8") as fh:
            mf = json.load(fh)
        mode = (mf.get("provenance") or {}).get("mode")
        dirty = (mf.get("candidate") or {}).get("dirty")
        if mode == "live" and dirty is False:
            good, why = True, f"{h} 合格 → 放行（不再看后面的）"
            break
        why = f"{h} mode={mode!r} dirty={dirty!r}"
    return good, why


def judge_new(repo: str, hits: list[str]) -> tuple[bool, str]:
    """新实现：每一份都要合格，且至少一份 —— 全称判据。"""
    ok, bad = [], []
    for h in sorted(set(hits)):
        full = os.path.join(repo, h)
        if not os.path.exists(full):
            bad.append(f"{h} 不存在")
            continue
        with open(full, encoding="utf-8") as fh:
            mf = json.load(fh)
        mode = (mf.get("provenance") or {}).get("mode")
        dirty = (mf.get("candidate") or {}).get("dirty")
        if mode == "live" and dirty is False:
            ok.append(h)
        else:
            bad.append(f"{h} mode={mode!r} dirty={dirty!r}")
    return (not bad) and bool(ok), f"合格 {len(ok)}/{len(set(hits))}" + (
        "; 不合格: " + "; ".join(bad) if bad else ""
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        live = "docs/release-evidence/rc-fixture/journeys/J01/manifest.json"
        recon = "docs/release-evidence/rc-fixture/journeys/J02/manifest.json"
        for rel, body in (
            (live, {"provenance": {"mode": "live"}, "candidate": {"dirty": False}}),
            (recon, {"provenance": {"mode": "reconstructed"}, "candidate": {"dirty": True}}),
        ):
            path = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(body, fh)

        cases = [
            ("对照输入 A：只有一份合格的 live manifest", [live]),
            ("负控输入 B：一份合格 + 一份 reconstructed（合格的排在前）", [live, recon]),
            ("负控输入 C：同 B，但顺序颠倒", [recon, live]),
            ("对照输入 D：只有一份 reconstructed", [recon]),
        ]
        print("# L3 语义对照：旧实现（存在判据）vs 新实现（全称判据）")
        print(f"# 临时素材目录: {tmp}（用完即弃；真树上没有合格的 live manifest 可用）")
        print()
        print(f"{'输入':<46} {'旧门':<8} {'新门':<8} 说明")
        print("-" * 110)
        rows = []
        for name, hits in cases:
            o, _ = judge_old(tmp, hits)
            n, why = judge_new(tmp, hits)
            rows.append((name, o, n))
            print(f"{name:<46} {'PASS' if o else 'FAIL':<8} {'PASS' if n else 'FAIL':<8} {why}")
        print()
        # 结论必须可机械核：B / C 两例是「旧门绿、新门红」，这正是本次改动要堵的路径。
        target = [r for r in rows if r[0].startswith("负控输入")]
        proved = all(o and not n for _, o, n in target)
        print(f"「旧门放行、新门拦下」的输入数 = {sum(1 for _, o, n in rows if o and not n)} / 负控输入数 {len(target)}")
        print(f"结论: 新实现确实拦下了旧实现放行的路径 = {proved}")
        print("（A / D 两例在新旧实现下判定一致 —— 说明改动没有翻转这两个输入的结论。）")
        print("⚠️ 本实验直接喂预先给定的 hits 列表，**没有调用正式 L3**：它证明的只是")
        print("   「存在判据 → 全称判据」这一处语义改动，不替 L3 的路径发现、schema 校验")
        print("   或其它输入背书（Codex r2 LOW-10 指出原措辞超出了输出能证明的范围）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
