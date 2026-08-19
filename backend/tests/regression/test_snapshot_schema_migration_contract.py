"""快照 schema 版本迁移契约锁 — P1-01（Codex 对抗审查 2026-08-19）。

背景
----
R11-BATCH2 T3 给 `write_snapshot_if_changed` 加了脱敏投影（E-2），但只在
generation 变化时才触发重写。于是 E-2 上线**之前**落盘的未脱敏快照，只要 vault
内容没变（generation 相同），就永远不会被重写 —— 投影对存量快照完全失效。

Codex 复现的反例：

    changed=False
    secret_on_disk=True
    load_has_secret=True
    degraded_study_has_secret=True
    exam_has_secret=False

即：exam 视图靠 Pydantic 模型结构性缺字段仍然安全，但**磁盘文件**和**降级态
study 面**都还带着原文。

本文件锁住修复语义：
  1. schema 版本落后 → 无论 generation 是否相同都强制重写
  2. load 侧对 v1 fail closed（宁可退到三态里的「空壳 error」也不加载可疑快照）
  3. 新写快照必带 snapshot_schema_version 且不含禁项

⛔ 不使用 mock：全部用真实临时目录 + 真实 JSON 落盘 + 真实 scan_vault 输出结构。
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from app.services import board_manifest_service as svc

# 与金集 forbidden_keys 同源的禁项（board_manifest_gold_set.yaml config 段）
FORBIDDEN_KEYS = {
    "tips",
    "errors",
    "error_candidates",
    "misconception",
    "correction",
    "raw_dialog_excerpt",
    "evidence_turns",
    "ai_reason",
}

SECRET_MARKER = "反例 diag(-1,-1) 行列式为 1 但负定"


def _all_keys(obj, acc=None):
    acc = acc if acc is not None else set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.add(k)
            _all_keys(v, acc)
    elif isinstance(obj, list):
        for x in obj:
            _all_keys(x, acc)
    return acc


def _legacy_v1_snapshot(generation: str) -> dict:
    """构造一份 E-2 之前格式的快照：无版本字段 + 带禁项原文。"""
    return {
        # 刻意不写 snapshot_schema_version —— 这正是 v1 的识别特征
        "freshness": {
            "generated_at": "2026-08-01T00:00:00+00:00",
            "generation": generation,
            "lag_seconds": 0.0,
            "stale": False,
        },
        "boards": {
            "线性代数": {
                "board_id": "线性代数",
                "members": [
                    {
                        "node_id": "positive-definite",
                        "exists": True,
                        "role": "derived",
                        "is_stub": False,
                        "mastery": {"score": 0.4, "a": None, "b": None, "source": "legacy_v2"},
                        "pick_hint": {"mu": 0.4, "sigma": 0.1, "pick_score": 0.3, "days_idle": 2.0},
                        "past_question_digests": [],
                        "title": "正定矩阵",
                        # ⛔ 禁项原文 —— v1 快照的问题所在
                        "error_candidates": [
                            {
                                "misconception": SECRET_MARKER,
                                "correction": "需特征值全正",
                                "ai_reason": "从对话推断",
                            }
                        ],
                        "tips": [{"text": "先看基线"}],
                        "errors": [],
                    }
                ],
            }
        },
        "node_stems": ["positive-definite"],
        "orphans": [],
        "exam_history": [],
        "parse_errors": [],
    }


def _current_full(generation: str) -> dict:
    """构造一份与 v1 快照 generation **相同**的 live state（内容未变的场景）。"""
    full = _legacy_v1_snapshot(generation)
    return json.loads(json.dumps(full, ensure_ascii=False))


@pytest.fixture
def vault():
    d = Path(tempfile.mkdtemp(prefix="p101-snapshot-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ── 核心反例：generation 相同的 v1 快照必须被迁移 ─────────────────────────


def test_same_generation_v1_snapshot_is_force_rewritten(vault):
    """Codex 反例的正面修复：generation 未变但版本落后 → 仍然重写。"""
    gen = "deadbeef1234"
    snap = svc.snapshot_file(vault)
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps(_legacy_v1_snapshot(gen), ensure_ascii=False), encoding="utf-8")

    on_disk_before = snap.read_text(encoding="utf-8")
    assert SECRET_MARKER in on_disk_before, "前置条件：v1 快照本应含禁项原文"

    changed = svc.write_snapshot_if_changed(vault, _current_full(gen))

    assert changed is True, (
        "generation 相同但 schema 版本落后时必须强制重写 —— 这正是 Codex 反例 changed=False 的修复点"
    )

    on_disk_after = snap.read_text(encoding="utf-8")
    assert SECRET_MARKER not in on_disk_after, "迁移后磁盘上不应再有禁项原文"
    assert not (_all_keys(json.loads(on_disk_after)) & FORBIDDEN_KEYS), (
        f"迁移后仍残留禁键: {sorted(_all_keys(json.loads(on_disk_after)) & FORBIDDEN_KEYS)}"
    )


def test_same_generation_current_snapshot_is_not_rewritten(vault):
    """已是当前版本且内容未变 → 保持原有的「不重写」优化，不做无谓 IO。"""
    gen = "cafe99887766"
    full = _current_full(gen)
    assert svc.write_snapshot_if_changed(vault, full) is True  # 首次写入

    assert svc.write_snapshot_if_changed(vault, full) is False, "当前版本且 generation 未变时应跳过重写"


# ── load 侧 fail closed ───────────────────────────────────────────────────


def test_load_snapshot_rejects_v1(vault):
    """v1 快照一律拒绝加载 —— 宁可无快照，也不从可能含原文的旧格式恢复。"""
    snap = svc.snapshot_file(vault)
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps(_legacy_v1_snapshot("aaaa11112222"), ensure_ascii=False), encoding="utf-8")

    assert svc.load_snapshot(vault) is None, (
        "load_snapshot 必须对 v1 fail closed（Codex 反例 load_has_secret=True 的修复点）"
    )


def test_load_snapshot_rejects_v2_denylist_era(vault):
    """P1-05b: v2 (denylist pop 三键时代) 同样拒绝 — 只认严格 int 3。"""
    v2 = _legacy_v1_snapshot("abab12123434")
    v2["snapshot_schema_version"] = 2
    snap = svc.snapshot_file(vault)
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps(v2, ensure_ascii=False), encoding="utf-8")

    assert svc.load_snapshot(vault) is None, "v2 denylist 时代快照必须按 cache miss"


def test_load_snapshot_accepts_current_v3(vault):
    """当前版本快照正常加载，且还原后带版本字段。"""
    svc.write_snapshot_if_changed(vault, _current_full("bbbb33334444"))

    loaded = svc.load_snapshot(vault)

    assert loaded is not None
    assert loaded.get("snapshot_schema_version") == svc.SNAPSHOT_SCHEMA_VERSION


def test_degraded_serve_does_not_leak_from_v1(vault, monkeypatch):
    """降级态整链验证：live 失败 + 磁盘只有 v1 → 走空壳 error，而非吐出原文。

    对应 Codex 反例的 degraded_study_has_secret=True。
    """
    snap = svc.snapshot_file(vault)
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps(_legacy_v1_snapshot("cccc55556666"), ensure_ascii=False), encoding="utf-8")

    def _boom(*a, **kw):
        raise OSError("P1-01 演练: live 扫描不可用")

    monkeypatch.setattr(svc, "scan_vault", _boom)
    result = svc.serve_manifest(vault, board_id=None)

    assert result["source_status"] == "error", (
        f"v1 快照被拒后应落到空壳 error 三态，实际 source_status={result['source_status']}"
    )
    assert SECRET_MARKER not in json.dumps(result, ensure_ascii=False), "降级响应中泄漏了禁项原文"


# ── 新写快照的版本戳 ───────────────────────────────────────────────────────


def test_new_snapshot_carries_version_stamp(vault):
    svc.write_snapshot_if_changed(vault, _current_full("dddd77778888"))

    data = json.loads(svc.snapshot_file(vault).read_text(encoding="utf-8"))

    assert data["snapshot_schema_version"] == svc.SNAPSHOT_SCHEMA_VERSION
    assert not (_all_keys(data) & FORBIDDEN_KEYS)


def test_projection_stamps_version_without_touching_live(vault):
    """投影打版本戳时不得污染入参（:716 契约：live 与快照共用同一 state）。"""
    full = _current_full("eeee99990000")

    projected = svc._project_for_snapshot(full)

    assert projected["snapshot_schema_version"] == svc.SNAPSHOT_SCHEMA_VERSION
    assert "snapshot_schema_version" not in full, "投影把版本字段写回了 live state"
    assert _all_keys(full) & FORBIDDEN_KEYS, "live state 的禁项被就地删除了（应只在副本上删）"
