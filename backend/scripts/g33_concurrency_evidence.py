#!/usr/bin/env python3
"""CARD-G3-3 并发取证: 两进程同节点同时评分, 连跑 N 轮, 记录 lost update 计数。

与 `tests/regression/test_g3_3_cas.py::test_concurrent_same_node_no_lost_update`
同一形态 —— 区别只在这里把每轮的原始观测 (rc / 账本行 / attempt / 水位线 /
校验器 rc) 逐条落盘, 供验收单与复核引用。

⛔ 只在临时目录里造 vault: 不碰 live vault, 不连 7691。
用法: `backend/.venv/bin/python backend/scripts/g33_concurrency_evidence.py \
        --rounds 3 --out _bmad-output/审查/evidence-g33/concurrency-run.json`
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
SKILL = REPO / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VALIDATOR = BACKEND / "scripts" / "validate_learning_events.py"
VAULT_SCRIPTS = REPO / "canvas-vault" / ".claude" / "scripts"

NODE_REL = "节点/测试节点.md"
TS1 = "2026-08-01T10:00:00Z"
NODE_V0 = (
    '---\ntype: concept\nmastery_score: 0.5\ntitle: 测试节点\nsource_board: "[[原白板/CS 61B]]"\n---\n测试节点正文。\n'
)

_BLOCKS = re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", SKILL.read_text(encoding="utf-8"), re.DOTALL)
_MAIN = [b for b in _BLOCKS if 'P = "/tmp/quiz-answer-payload.json"' in b]
assert len(_MAIN) == 1, f"SKILL.md 主写点块应为 1, 实见 {len(_MAIN)}"
CODE = _MAIN[0]


def _make_vault(root: Path) -> Path:
    v = root / "canvas-vault"
    (v / "节点").mkdir(parents=True)
    (v / ".claude" / "scripts").mkdir(parents=True)
    (root / "backend" / "scripts").mkdir(parents=True)
    (root / "backend" / ".venv").symlink_to(BACKEND / ".venv", target_is_directory=True)
    (root / "backend" / "scripts" / "validate_learning_events.py").symlink_to(VALIDATOR)
    (v / ".claude" / "scripts" / "fsrs_bridge.py").symlink_to(VAULT_SCRIPTS / "fsrs_bridge.py")
    (v / ".claude" / "scripts" / "decay_beta.py").symlink_to(VAULT_SCRIPTS / "decay_beta.py")
    (v / ".canvas-config.yaml").write_text(
        '# 取证 config\nvault_id: "canvas-vault-取证"\nsubject: cs-61b\n', encoding="utf-8"
    )
    (v / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    return v


def _payload(event_id: str) -> dict:
    return {
        "node": NODE_REL,
        "grade_norm": 0.752,
        "ts": TS1,
        "review_time": TS1,
        "event_id": event_id,
        "exam_board": f"检验白板/{event_id}.md",
        "question_id": "q1",
        "source_board": "[[原白板/CS 61B]]",
        "self_confidence_raw": "半懂",
        "self_confidence_norm": 0.5,
        "abandoned": False,
        "callout": "",
    }


def _spawn(vault: Path, eid: str, tag: str):
    pf = vault.parent / f"payload-{tag}.json"
    pf.write_text(json.dumps(_payload(eid), ensure_ascii=False), encoding="utf-8")
    code = CODE.replace('"/tmp/quiz-answer-payload.json"', json.dumps(str(pf)))
    return subprocess.Popen(
        [sys.executable, "-c", code],
        cwd=str(vault),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
    )


def _fm(vault: Path, key: str):
    m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', (vault / NODE_REL).read_text(encoding="utf-8"), re.M)
    return m.group(1).strip() if m else None


def one_round(idx: int) -> dict:
    root = Path(tempfile.mkdtemp(prefix=f"g33-eviden-{idx}-"))
    try:
        v = _make_vault(root)
        e1, e2 = f"取证板A-{idx}#q1", f"取证板B-{idx}#q1"
        p1, p2 = _spawn(v, e1, f"{idx}a"), _spawn(v, e2, f"{idx}b")
        _, r1 = p1.communicate(timeout=300)
        _, r2 = p2.communicate(timeout=300)
        rows = [
            json.loads(x) for x in (v / "learning_events.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()
        ]
        att = _fm(v, "attempt_count")
        w = _fm(v, "fsrs_last_review")
        node_text = (v / NODE_REL).read_text(encoding="utf-8")
        val = subprocess.run(
            [sys.executable, str(VALIDATOR), str(v / "learning_events.jsonl")],
            capture_output=True,
            text=True,
            timeout=120,
        )
        # lost update 的定义: 账本记了 N 次评分, 而笔记只算进了不足 N 次。
        lost = int(att or 0) != len(rows) or any(f"quiz:{e}" not in node_text for e in (e1, e2))
        return {
            "round": idx,
            "rc": [p1.returncode, p2.returncode],
            "ledger_ids": [r["event_id"] for r in rows],
            "attempt_count": att,
            "fsrs_last_review": w,
            "latest_review_time": max((r["payload"].get("review_time") for r in rows), default=None),
            "validator_rc": val.returncode,
            "lost_update": lost,
            "stderr_tail": [r1.strip().splitlines()[-1:], r2.strip().splitlines()[-1:]],
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    rounds = [one_round(i + 1) for i in range(args.rounds)]
    lost = sum(1 for r in rounds if r["lost_update"])
    summary = {
        "rounds": rounds,
        "lost_update_count": lost,
        "all_rc_zero": all(rc == 0 for r in rounds for rc in r["rc"]),
        "all_validator_zero": all(r["validator_rc"] == 0 for r in rounds),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rounds:
        print(
            f"round {r['round']}: rc={r['rc']} 账本{len(r['ledger_ids'])}条 "
            f"attempt={r['attempt_count']} W={r['fsrs_last_review']} "
            f"validator={r['validator_rc']} lost_update={r['lost_update']}"
        )
    print(f"\nlost_update 轮数: {lost}/{len(rounds)}")
    return 0 if (lost == 0 and summary["all_rc_zero"] and summary["all_validator_zero"]) else 1


if __name__ == "__main__":
    sys.exit(main())
