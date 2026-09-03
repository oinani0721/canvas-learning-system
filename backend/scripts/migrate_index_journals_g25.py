#!/usr/bin/env python3
"""G2-5 索引 journal 命名空间迁移器 (BATCH-2026-08-29-第七批 / CARD-G2-5).

CARD-G2-5 把两处 durable pending journal 从固定文件名改成按 vault 命名空间
(``vault_index_pending__<vault_key>.jsonl`` / ``lancedb_pending_index__<vault_key>.jsonl``)。
本脚本处理**存量**: 升级前留下的无维度旧文件。

处置口径 = **隔离, 不迁移**:

旧文件的条目只有相对路径, **无从判断属于哪个 vault**。把它改名成
``<name>.pre-g25.bak`` 保留证据, 但绝不加载 —— 猜一个归属重放, 就是本卡要消灭
的那条串台路径。这与 ``app/core/vault_state_paths.quarantine_legacy_state_file``
是同一个函数, 服务在 recover 时也会自动做同样的事; 本脚本只是让 Ops 能**在
启动之前**看清楚、并显式执行。

⚠️ 语义损失 (如实, Codex round-1 HIGH-4 修正 —— 原文案统一写"60s 必收敛"是错的):

- ``vault_index_pending`` (orchestrator): 有周期反熵 (``reconcile()`` 的指纹
  diff + orphan sweep, ``VAULT_INDEX_SCAN_INTERVAL_S`` 默认 60s, 启动先跑一趟),
  但那趟扫描**只覆盖当前部署的这个 vault**。准确口径: 等**该 vault 自己再次运行
  且扫描健康**之后才收敛; 若隔离件属于一个以后不再打开的 vault, 它不会被补上。
- ``lancedb_pending_index``: **没有周期反熵**。条目只记 ``canvas_name``, 靠该
  canvas 再次变更才重新入队; 隔离后若它不再改动, 需要 Ops 判归属或对该 vault
  做一次全量重建。

用法::

    python scripts/migrate_index_journals_g25.py                 # 只读普查
    python scripts/migrate_index_journals_g25.py --out /tmp/e.json
    python scripts/migrate_index_journals_g25.py --apply         # 执行隔离

Exit codes: 0 = 无待隔离项 (或 apply 完成后归零); 2 = dry-run 发现待隔离项;
1 = 运行错误。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

#: 本卡命名空间化的 journal 词干 (与两个服务里的常量一一对应)。
NAMESPACED_STEMS = ("vault_index_pending", "lancedb_pending_index")

NAMESPACE_SEP = "__"
QUARANTINE_MARK = ".pre-g25.bak"


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def census(data_dir: Path) -> Dict[str, Any]:
    """只读普查 —— 分出「无维度旧件 / 已命名空间化 / 已隔离件」三类。"""
    legacy: List[Dict[str, Any]] = []
    namespaced: List[Dict[str, Any]] = []
    quarantined: List[Dict[str, Any]] = []

    unclassified: List[Dict[str, Any]] = []

    if data_dir.exists():
        for p in sorted(data_dir.iterdir()):
            if not p.is_file():
                continue
            try:
                entry: Dict[str, Any] = {"name": p.name, "bytes": p.stat().st_size}
                entry["sha256"] = _sha256(p)
                entry["lines"] = sum(1 for _ in p.open("r", encoding="utf-8", errors="replace"))
            except OSError as e:
                # LOW-12: 读不了的文件不能混进"干净"的类别里, 单列出来让人看见
                unclassified.append({"name": p.name, "error": f"{type(e).__name__}: {e}"})
                continue

            stem = next((st for st in NAMESPACED_STEMS if p.name.startswith(st)), None)
            if stem is None:
                continue  # 与本卡无关的文件, 不属于 census 射程

            rest = p.name[len(stem) :]
            if QUARANTINE_MARK in rest:
                quarantined.append({**entry, "stem": stem})
            # MEDIUM-7: 崩溃残留的 <stem>.jsonl.tmp 同样是**无维度**旧件 ——
            # 它由 _persist_sync 的 tmp+os.replace 产生, 且被 .gitignore 藏住。
            # 只认 canonical .jsonl 会把带 delete 意图的 crash residue 报成 clean。
            elif rest in (".jsonl", ".jsonl.tmp"):
                legacy.append({**entry, "stem": stem, "residue": rest == ".jsonl.tmp"})
            elif rest.startswith(NAMESPACE_SEP) and rest.endswith((".jsonl", ".jsonl.tmp")):
                key = rest[len(NAMESPACE_SEP) :].rsplit(".jsonl", 1)[0]
                if key:
                    namespaced.append({**entry, "stem": stem, "vault_key": key})
                else:
                    # 空 key 的 <stem>__.jsonl 不是合法命名空间件
                    unclassified.append({**entry, "stem": stem, "why": "empty vault_key"})
            else:
                unclassified.append({**entry, "stem": stem, "why": "unrecognized suffix"})

    return {
        "data_dir": str(data_dir),
        "legacy_dimensionless": legacy,
        "namespaced": namespaced,
        "quarantined": quarantined,
        "unclassified": unclassified,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="G2-5 索引 journal 存量隔离器 (默认只读)")
    ap.add_argument(
        "--data-dir",
        default=str(_BACKEND_ROOT / "app" / "data"),
        help="状态文件目录 (默认 backend/app/data)",
    )
    ap.add_argument("--apply", action="store_true", help="执行隔离 (改名为 .pre-g25.bak)")
    ap.add_argument("--out", help="证据 JSON 落盘路径")
    args = ap.parse_args()

    data_dir = Path(args.data_dir).expanduser().resolve()
    report = census(data_dir)
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["mode"] = "apply" if args.apply else "dry-run"
    report["pending_count"] = len(report["legacy_dimensionless"])

    if args.apply and report["legacy_dimensionless"]:
        from app.core.vault_state_paths import quarantine_legacy_state_file

        done = []
        for item in report["legacy_dimensionless"]:
            src = data_dir / item["name"]
            before = item.get("sha256")
            target = quarantine_legacy_state_file(src, context="migrate_index_journals_g25")
            rec = {"source": item["name"], "quarantined_to": target.name if target else None}
            if target is not None:
                rec["sha_preserved"] = _sha256(target) == before
            done.append(rec)
        report["quarantine_actions"] = done
        report["post_census"] = census(data_dir)
        report["pending_after"] = len(report["post_census"]["legacy_dimensionless"])
        rc = 0 if report["pending_after"] == 0 and all(d.get("sha_preserved") for d in done) else 1
    else:
        rc = 2 if report["legacy_dimensionless"] else 0

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).expanduser().write_text(text + "\n", encoding="utf-8")
    print(text)
    return rc


if __name__ == "__main__":
    sys.exit(main())
