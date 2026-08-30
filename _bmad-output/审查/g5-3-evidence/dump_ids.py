#!/usr/bin/env python3
"""G5-3 取证辅助：把 preview / diff 产物里的稳定 ID 与四态汇总打成人可核对的清单。

只读 JSON，不改任何文件。用法:
    python3 dump_ids.py preview A.json B.json
    python3 dump_ids.py diff    A.json B.json
"""

from __future__ import annotations

import json
import sys


def dump_preview(path: str) -> None:
    d = json.loads(open(path, encoding="utf-8").read())
    print(
        f"== {d['board']} · schema_version={d['schema_version']} · "
        f"id_stability={d['id_stability']} · ns={d['stable_id_namespace']} · 候选 {len(d['candidates'])}"
    )
    for c in d["candidates"]:
        b = c["stable_id_basis"]
        print(
            f"  {c['stable_id']}  {c['content_fingerprint']}  occ={b['occurrence']}  "
            f"{c['resolved_name']}  ← {' › '.join(b['heading_path_normalized'])}"
        )


def dump_diff(path: str) -> None:
    d = json.loads(open(path, encoding="utf-8").read())
    print(
        f"== diff {d['board']} · summary={json.dumps(d['summary'], ensure_ascii=False)} · "
        f"entries={len(d['entries'])} · unchanged={len(d['unchanged'])}"
    )
    for e in d["entries"]:
        print(f"  {e['state']:<8} {e['stable_id']}  reasons={e['change_reasons']}  moved={e['moved']}")


if __name__ == "__main__":
    mode, paths = sys.argv[1], sys.argv[2:]
    fn = dump_preview if mode == "preview" else dump_diff
    for p in paths:
        fn(p)
