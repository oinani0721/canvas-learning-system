#!/usr/bin/env python3
"""FSRS golden vectors 生成器 (CARD-G3-4, BATCH-2026-08-28-第五批)。

用真实 fsrs 库在完全确定性配置下生成冻结向量集:
  - 固定 card_id / 固定 UTC 复习时刻链 / enable_fuzzing=False / 默认 21 参数;
  - 覆盖 新卡 / Learning 第二步 / Review 准时 / Review 逾期 30 天 / Relearning
    五种关键态 × again/hard/good/easy 四评分 = 20 条调度向量,
    外加 Review 卡在 due/due+7d/due+30d 的 retrievability 3 条;
  - manifest 锁 library version / algorithm 标识 / timezone / 参数 hash /
    枚举值面 — 依赖升级或语义漂移时对比测试
    (tests/regression/test_fsrs_golden_vectors.py) 立刻翻红。

动态时刻 (「到期时复习」) 在生成期解析为绝对 ISO 时间写入 JSON — golden
文件自包含, 测试端只按绝对时刻重放, 不依赖本生成器逻辑。

重新生成 (仅在有意更新基线时, 例如升级 fsrs 后经评审重冻结):
    backend/.venv/bin/python backend/scripts/generate_fsrs_golden_vectors.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from importlib.metadata import version as pkg_version
from pathlib import Path

from fsrs import Card, Rating, Scheduler
from fsrs.scheduler import DEFAULT_PARAMETERS

OUT_DIR = Path(__file__).resolve().parents[1] / "tests" / "regression"
MANIFEST_PATH = OUT_DIR / "fsrs_golden_manifest.json"
VECTORS_PATH = OUT_DIR / "fsrs_golden_vectors.json"

#: 全部确定性锚点 — 任何一项变化都等于换了基线
T0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
CARD_ID = 20260101000000
SCHEDULER_CONFIG = {
    "parameters": list(DEFAULT_PARAMETERS),
    "desired_retention": 0.9,
    "learning_steps_minutes": [1, 10],
    "relearning_steps_minutes": [10],
    "maximum_interval": 36500,
    "enable_fuzzing": False,
}

RATINGS = [("again", Rating.Again), ("hard", Rating.Hard), ("good", Rating.Good), ("easy", Rating.Easy)]

#: 场景 = 前缀步骤链 + 最终评分时刻。步骤时刻: 绝对 datetime 或动态标记
#: "due"(上一步结果卡的到期时刻) / "due+30d" / "due+10m"。
SCENARIOS = [
    ("new_card", "新卡首评 (state=Learning step=0, stability/difficulty=None)", [], "t0"),
    ("learning_step2", "Learning 第二步 (Good@T0 后 10 分钟到期复评)", [("good", "t0")], "due"),
    (
        "review_ontime",
        "Review 态准时复评 (两次 Good 毕业后恰于到期日复评)",
        [("good", "t0"), ("good", "due")],
        "due",
    ),
    (
        "review_overdue_30d",
        "Review 态逾期 30 天复评",
        [("good", "t0"), ("good", "due")],
        "due+30d",
    ),
    (
        "relearning",
        "Relearning 态 (Review 后 Again 进重学, 10 分钟到期复评)",
        [("good", "t0"), ("good", "due"), ("again", "due")],
        "due",
    ),
]

RATING_BY_NAME = {name: rating for name, rating in RATINGS}


def params_hash() -> str:
    canonical = json.dumps(SCHEDULER_CONFIG, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_scheduler() -> Scheduler:
    return Scheduler(
        parameters=SCHEDULER_CONFIG["parameters"],
        desired_retention=SCHEDULER_CONFIG["desired_retention"],
        learning_steps=[timedelta(minutes=m) for m in SCHEDULER_CONFIG["learning_steps_minutes"]],
        relearning_steps=[timedelta(minutes=m) for m in SCHEDULER_CONFIG["relearning_steps_minutes"]],
        maximum_interval=SCHEDULER_CONFIG["maximum_interval"],
        enable_fuzzing=SCHEDULER_CONFIG["enable_fuzzing"],
    )


def new_card() -> Card:
    return Card(card_id=CARD_ID, due=T0)


def resolve_when(marker: str, card: Card) -> datetime:
    if marker == "t0":
        return T0
    if marker == "due":
        return card.due
    if marker == "due+30d":
        return card.due + timedelta(days=30)
    raise ValueError(f"未知时刻标记: {marker}")


def card_expected(card: Card) -> dict:
    return {
        "stability": card.stability,
        "difficulty": card.difficulty,
        "due": card.due.isoformat(),
        "last_review": card.last_review.isoformat() if card.last_review else None,
        "state": int(card.state),
        "step": card.step,
    }


def generate() -> tuple[dict, dict]:
    scheduler = build_scheduler()
    vectors = []

    for scenario_id, description, prefix, final_marker in SCENARIOS:
        for rating_name, rating in RATINGS:
            card = new_card()
            steps = []
            for step_rating_name, when_marker in prefix:
                when = resolve_when(when_marker, card)
                card, _ = scheduler.review_card(card, RATING_BY_NAME[step_rating_name], when)
                steps.append({"rating": step_rating_name, "review_at": when.isoformat()})
            final_at = resolve_when(final_marker, card)
            state_before = int(card.state)
            card, _ = scheduler.review_card(card, rating, final_at)
            steps.append({"rating": rating_name, "review_at": final_at.isoformat()})
            vectors.append(
                {
                    "id": f"{scenario_id}__{rating_name}",
                    "scenario": scenario_id,
                    "description": description,
                    "state_before_final_review": state_before,
                    "steps": steps,
                    "expected": card_expected(card),
                }
            )

    # retrievability 曲线向量: Review 态卡在 due / due+7d / due+30d
    card = new_card()
    for step_rating_name, when_marker in [("good", "t0"), ("good", "due")]:
        when = resolve_when(when_marker, card)
        card, _ = scheduler.review_card(card, RATING_BY_NAME[step_rating_name], when)
    retrievability = {
        "steps": [
            {"rating": "good", "review_at": T0.isoformat()},
            {"rating": "good", "review_at": card.last_review.isoformat()},
        ],
        "card": card_expected(card),
        "at": [
            {
                "current_datetime": (card.due + timedelta(days=days)).isoformat(),
                "expected": scheduler.get_card_retrievability(card, card.due + timedelta(days=days)),
            }
            for days in (0, 7, 30)
        ],
    }

    manifest = {
        "manifest_version": 1,
        "frozen_on": "2026-08-28",
        "card": "CARD-G3-4 (BATCH-2026-08-28-第五批)",
        "library": "fsrs",
        "library_version": pkg_version("fsrs"),
        "algorithm": "FSRS-6 (py-fsrs 21-parameter scheduler)",
        "parameter_count": len(DEFAULT_PARAMETERS),
        "timezone": "UTC",
        "base_datetime": T0.isoformat(),
        "card_id": CARD_ID,
        "scheduler_config": SCHEDULER_CONFIG,
        "params_hash": params_hash(),
        "rating_values": {"again": 1, "hard": 2, "good": 3, "easy": 4},
        "state_values": {"Learning": 1, "Review": 2, "Relearning": 3},
        "generator": "backend/scripts/generate_fsrs_golden_vectors.py",
        "comparison_tolerance": {"float_rel": 1e-9, "float_abs": 1e-12},
    }
    payload = {
        "params_hash": params_hash(),
        "library_version": pkg_version("fsrs"),
        "vectors": vectors,
        "retrievability": retrievability,
    }
    return manifest, payload


def main() -> int:
    manifest, payload = generate()
    # newline 固定 LF: Windows 平台重生成不得引入 CRLF 漂移 (Codex round-1 LOW)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    VECTORS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"written: {MANIFEST_PATH}")
    print(f"written: {VECTORS_PATH}")
    print(f"library_version={manifest['library_version']} params_hash={manifest['params_hash']}")
    print(f"vectors={len(payload['vectors'])} retrievability_points={len(payload['retrievability']['at'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
