#!/usr/bin/env python3
"""CARD-G3-2b 裁判 3 的 fixture 生成器（卡内安全脚本）。

[BATCH-2026-09-01-第九批 / CARD-G3-2b]

产出 `/private/tmp/card-g3-2b-fixture/learning_events.jsonl` —— 一份由**逐字
提取的生产 PYEOF 写点**真实跑出来的 review/1 账本（非手写样例），供裁判 3：

    .venv/bin/python scripts/validate_learning_events.py \
        /private/tmp/card-g3-2b-fixture/learning_events.jsonl

安全边界（硬门，违反即拒跑，退出码 2）：
  - 写入面只有 `/private/tmp/card-g3-2b-fixture`（resolve 后严格相等）；
    删除仅在该目录**已带本脚本的标记文件**时发生，绝不递归删陌生目录；
  - SKILL.md / fsrs_bridge.py / decay_beta.py / validate_learning_events.py
    一律 **symlink 只读引用**，不复制、不修改；
  - 不触碰 live vault、Neo4j 7691、现网 LanceDB —— 本脚本无任何网络/DB 调用。

`--check` 只复算并打印现有 fixture 的 sha256，不重建。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE_ROOT = Path("/private/tmp/card-g3-2b-fixture")
MARKER = ".g32b-fixture-marker"
WT = Path(__file__).resolve().parents[2]
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VAULT_SCRIPTS = WT / "canvas-vault" / ".claude" / "scripts"
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"

NODE_REL = "节点/测试节点.md"
NODE_V0 = (
    '---\ntype: concept\nmastery_score: 0.5\ntitle: 测试节点\nsource_board: "[[原白板/CS 61B]]"\n---\n测试节点正文。\n'
)
CONFIG = '# CARD-G3-2b fixture\nvault_id: "canvas-vault-测试"\nsubject: cs-61b\n'


def _extract_writer() -> str:
    """逐字提取 SKILL.md 的**主写点** PYEOF 块（同 test_g3_2_review_ledger 范式）。"""
    text = SKILL.read_text(encoding="utf-8")
    blocks = [
        b
        for b in re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", text, re.DOTALL)
        if 'P = "/tmp/quiz-answer-payload.json"' in b
    ]
    if len(blocks) != 1:
        sys.exit(f"[g32b-fixture] SKILL.md 应恰有 1 个主写点 PYEOF 块, 实见 {len(blocks)} — 拒跑")
    return blocks[0]


def _guard_target() -> None:
    resolved = FIXTURE_ROOT.resolve() if FIXTURE_ROOT.exists() else FIXTURE_ROOT
    if str(resolved) != str(FIXTURE_ROOT):
        sys.exit(f"[g32b-fixture] 目标目录 resolve 后不等于约定路径 ({resolved}) — 拒跑")
    if FIXTURE_ROOT.exists() and not (FIXTURE_ROOT / MARKER).is_file():
        sys.exit(
            f"[g32b-fixture] {FIXTURE_ROOT} 已存在但没有本脚本的标记文件 {MARKER} — "
            "拒绝删除陌生目录, 请人工确认后手工清理"
        )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_writer(vault: Path, code: str, payload: dict) -> None:
    pfile = vault.parent / "payload.json"
    pfile.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    patched = code.replace('"/tmp/quiz-answer-payload.json"', json.dumps(str(pfile)))
    proc = subprocess.run(
        [sys.executable, "-c", patched],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(vault),
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
    )
    if proc.returncode != 0:
        sys.exit(f"[g32b-fixture] 写点非零退出 ({proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
    print("  writer:", proc.stdout.strip().split("\n")[-1])


def main() -> int:
    if "--check" in sys.argv:
        ledger = FIXTURE_ROOT / "learning_events.jsonl"
        if not ledger.is_file():
            sys.exit(f"[g32b-fixture] {ledger} 不存在 — 先不带 --check 跑一次")
        print(f"learning_events.jsonl sha256: {_sha(ledger)}")
        print(f".canvas-config.yaml   sha256: {_sha(FIXTURE_ROOT / '.canvas-config.yaml')}")
        return 0

    _guard_target()
    if FIXTURE_ROOT.exists():
        shutil.rmtree(FIXTURE_ROOT)
    FIXTURE_ROOT.mkdir(parents=True)
    (FIXTURE_ROOT / MARKER).write_text("CARD-G3-2b fixture root — 可安全重建\n", encoding="utf-8")

    # 镜像布局: repo/canvas-vault (写点用 REPO=dirname(VAULT) 定位 validator)
    repo = FIXTURE_ROOT / "build" / "repo"
    vault = repo / "canvas-vault"
    (vault / "节点").mkdir(parents=True)
    (vault / ".claude" / "scripts").mkdir(parents=True)
    (repo / "backend" / "scripts").mkdir(parents=True)
    (repo / "backend" / ".venv").symlink_to(WT / "backend" / ".venv", target_is_directory=True)
    (repo / "backend" / "scripts" / "validate_learning_events.py").symlink_to(VALIDATOR)
    (vault / ".claude" / "scripts" / "fsrs_bridge.py").symlink_to(VAULT_SCRIPTS / "fsrs_bridge.py")
    (vault / ".claude" / "scripts" / "decay_beta.py").symlink_to(VAULT_SCRIPTS / "decay_beta.py")
    (vault / ".canvas-config.yaml").write_text(CONFIG, encoding="utf-8")
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")

    code = _extract_writer()
    base = {
        "node": NODE_REL,
        "grade_norm": 0.752,
        "question_id": "q1",
        "source_board": "[[原白板/CS 61B]]",
        "self_confidence_raw": "半懂",
        "self_confidence_norm": 0.5,
        "abandoned": False,
        "callout": "",
    }
    print("跑生产写点 E1 (新卡首评) …")
    _run_writer(
        vault,
        code,
        {
            **base,
            "ts": "2026-08-01T10:00:00Z",
            # 稳定业务时刻（Step 3 的 scored_at）；两次是不同评分，故各自跟随 ts
            "review_time": "2026-08-01T10:00:00Z",
            "event_id": "测试检验-2026-08-01-1000#q1",
            "exam_board": "检验白板/测试检验-2026-08-01-1000.md",
        },
    )
    print("跑生产写点 E2 (次日复评, 走 A2 增量) …")
    _run_writer(
        vault,
        code,
        {
            **base,
            "ts": "2026-08-02T10:00:00Z",
            # 稳定业务时刻（Step 3 的 scored_at）；两次是不同评分，故各自跟随 ts
            "review_time": "2026-08-02T10:00:00Z",
            "grade_norm": 0.31,
            "event_id": "测试检验-2026-08-02-1000#q1",
            "exam_board": "检验白板/测试检验-2026-08-02-1000.md",
        },
    )

    shutil.copy2(vault / "learning_events.jsonl", FIXTURE_ROOT / "learning_events.jsonl")
    shutil.copy2(vault / ".canvas-config.yaml", FIXTURE_ROOT / ".canvas-config.yaml")
    ledger = FIXTURE_ROOT / "learning_events.jsonl"
    rows = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()]
    print(f"\nfixture: {ledger} ({len(rows)} 行)")
    for r in rows:
        print(
            f"  {r['event_id']} @ {r['payload']['review_time']} "
            f"rating={r['payload']['rating']} attempt={r['payload']['attempt_count']}"
        )
    print(f"learning_events.jsonl sha256: {_sha(ledger)}")
    print(f".canvas-config.yaml   sha256: {_sha(FIXTURE_ROOT / '.canvas-config.yaml')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
