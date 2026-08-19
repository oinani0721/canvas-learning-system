"""P1-05b SnapshotV3 契约锁 — allowlist 快照 + pick_eligible + 读时重算。

覆盖计划验收门:
  1. 五类反例: forged v3 / version=999 / version="3" / 根 []/null / 错型
     freshness — 全部按 cache miss, 且 live 路径不受影响
  2. 投毒专项: inf/nan mastery 节点经 V3 快照往返后仍不得参与竞秩
     (对应 test_non_finite_mastery_cannot_hijack_pick_rank 的快照面)
  3. 降级态 exam + study 双视图投影无 ValidationError
  4. 折旧解冻: 降级态 days_idle 按请求级 now 重算, 不冻结在落盘那刻
  5. 磁盘面 allowlist: 无 digest/title/derived_reason/pick_hint 等被删键

⛔ 不使用 mock: 真实临时 vault + 真实快照 JSON 落盘 + 真实 serve 三态。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.models.board_manifest import project_manifest
from app.services import board_manifest_service as svc

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)


def _write(vault: Path, rel: str, content: str) -> None:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _board_md() -> str:
    return "---\ntype: whiteboard\n---\n# 板\n\n## Concepts\n\n## Recent Activity\n\n- created\n"


def _node_md(fm_lines: list[str], body: str = "真实内容。") -> str:
    return "---\n" + "\n".join(fm_lines) + "\n---\n" + body + "\n"


@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    for d in ("节点", "原白板", "检验白板"):
        (v / d).mkdir(parents=True)
    return v


def _poison_vault(vault: Path) -> None:
    """投毒 + 真薄弱 + 强 三节点 (HIGH-2 场景) + 一条带 last_examined 的节点。"""
    _write(vault, "原白板/板.md", _board_md())
    _write(vault, "节点/A投毒.md", _node_md(["mastery_a: .inf", "mastery_b: 1.0", 'source_board: "[[原白板/板]]"']))
    _write(vault, "节点/M真薄弱.md", _node_md(["mastery_score: 0.02", 'source_board: "[[原白板/板]]"']))
    _write(
        vault,
        "节点/Z强.md",
        _node_md(
            [
                "mastery_score: 0.9",
                f"last_examined: {(NOW - timedelta(days=10)).isoformat()}",
                'source_board: "[[原白板/板]]"',
            ]
        ),
    )


def _degrade(vault: Path) -> None:
    (vault / "节点").rename(vault / "节点-改名")


# ══ 磁盘面 allowlist ══


def test_snapshot_on_disk_is_v3_allowlist(vault):
    _poison_vault(vault)
    svc.serve_manifest(vault, board_id="板", now=NOW)

    snap_path = svc.snapshot_file(vault)
    assert snap_path.name == "manifest-v3.json"
    data = json.loads(snap_path.read_text(encoding="utf-8"))
    assert data["snapshot_schema_version"] == 3
    assert data["capabilities"] == {"history_text": False}

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

    dropped = {
        "digest",
        "title",
        "aliases",
        "derived_reason",
        "source_board_raw",
        "pick_hint",
        "created_from",
        "next_review",
        "calibration_count",
        "tips",
        "errors",
        "error_candidates",
        "error",  # parse_errors 只存 error_code
    }
    on_disk = _all_keys(data)
    assert on_disk & dropped == set(), f"被删字段泄漏落盘: {sorted(on_disk & dropped)}"
    # 投毒节点的资格位显式落盘为 false
    members = {m["node_id"]: m for m in data["boards"]["板"]["members"]}
    assert members["A投毒"]["pick_eligible"] is False
    assert members["M真薄弱"]["pick_eligible"] is True


# ══ 五类反例 (全部 cache miss + 不炸 live) ══


def _valid_v3_on_disk(vault: Path) -> dict:
    """先用真实 serve 写出一份合法 v3, 返回其 JSON (供篡改)。"""
    _poison_vault(vault)
    svc.serve_manifest(vault, board_id="板", now=NOW)
    return json.loads(svc.snapshot_file(vault).read_text(encoding="utf-8"))


def _put_snapshot(vault: Path, payload) -> None:
    p = svc.snapshot_file(vault)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _tamper_forged_extra_field(data: dict) -> dict:
    data["boards"]["板"]["members"][0]["smuggled_freetext"] = "反例 diag(-1,-1) 行列式为 1 但负定"
    return data


def _tamper_version_999(data: dict) -> dict:
    data["snapshot_schema_version"] = 999
    return data


def _tamper_version_str3(data: dict) -> dict:
    data["snapshot_schema_version"] = "3"
    return data


def _tamper_bad_freshness(data: dict) -> dict:
    data["freshness"] = {"generated_at": "2026-08-19T00:00:00+00:00", "generation": 12345}
    return data


@pytest.mark.parametrize(
    "tamper",
    [_tamper_forged_extra_field, _tamper_version_999, _tamper_version_str3, _tamper_bad_freshness],
    ids=["forged-extra-field", "version-999", "version-str-3", "freshness-wrong-type"],
)
def test_tampered_snapshot_is_cache_miss(vault, tamper):
    data = _valid_v3_on_disk(vault)
    _put_snapshot(vault, tamper(data))

    assert svc.load_snapshot(vault) is None

    _degrade(vault)
    result = svc.serve_manifest(vault, board_id=None, now=NOW)
    assert result["source_status"] == "error", "坏快照必须落到空壳 error 三态, 不得恢复也不得 500"


@pytest.mark.parametrize("root", [[], None, "v3", 3], ids=["list", "null", "str", "int"])
def test_non_dict_root_snapshot_is_cache_miss(vault, root):
    _poison_vault(vault)
    _put_snapshot(vault, root)

    assert svc.load_snapshot(vault) is None

    _degrade(vault)
    result = svc.serve_manifest(vault, board_id=None, now=NOW)
    assert result["source_status"] == "error"


def test_corrupt_snapshot_never_affects_live(vault):
    """live 可用时, 坏快照只是被覆盖重写 — serve 结果仍是 live ok。"""
    _poison_vault(vault)
    _put_snapshot(vault, {"snapshot_schema_version": "3", "junk": True})

    result = svc.serve_manifest(vault, board_id="板", now=NOW)

    assert result["source"] == "live" and result["source_status"] == "ok"
    # 且坏快照已被合法 v3 覆盖
    data = json.loads(svc.snapshot_file(vault).read_text(encoding="utf-8"))
    assert data["snapshot_schema_version"] == 3


# ══ 投毒往返 (HIGH-2 快照面) ══


def test_non_finite_mastery_stays_dead_after_v3_roundtrip(vault):
    """投毒节点在快照里与"从未评估"同为 source=absent — pick_eligible 显式
    资格位保证它经往返后仍不参与竞秩, 真薄弱节点保住 rank=1。"""
    _poison_vault(vault)
    svc.serve_manifest(vault, board_id="板", now=NOW)  # 落 v3 快照
    _degrade(vault)

    result = svc.serve_manifest(vault, board_id="板", now=NOW)

    assert result["source_status"] == "snapshot" and result["degraded"] is True
    by_id = {n["node_id"]: n for n in result["nodes"]}
    assert by_id["A投毒"]["pick_hint"] is None, "投毒节点经 V3 往返后复活竞秩 (HIGH-2 回归)"
    rank1 = [n["node_id"] for n in result["nodes"] if (n["pick_hint"] or {}).get("pick_rank") == 1]
    assert rank1 == ["M真薄弱"]
    # 投毒与"从未评估"在 mastery 面确实同构 — 资格位是唯一区分 (前置自检)
    assert by_id["A投毒"]["mastery"]["source"] == "absent"


# ══ 折旧解冻 ══


def test_degraded_days_idle_tracks_request_now_not_snapshot_time(vault):
    """旧缺陷: 降级返回的秩/折旧是快照落盘那刻的口径。V3 读时重算后,
    days_idle 必须跟着请求级 now 走。"""
    _poison_vault(vault)
    svc.serve_manifest(vault, board_id="板", now=NOW)  # last_examined = NOW-10d
    _degrade(vault)

    later = NOW + timedelta(days=30)
    result = svc.serve_manifest(vault, board_id="板", now=later)

    z = next(n for n in result["nodes"] if n["node_id"] == "Z强")
    assert z["pick_hint"] is not None
    assert z["pick_hint"]["days_idle"] == pytest.approx(40.0, abs=0.1), (
        f"降级态 days_idle 冻结在落盘口径 (期望 ~40, 实得 {z['pick_hint']['days_idle']})"
    )


# ══ 降级态双视图投影 ══


def test_degraded_both_views_project_without_validation_error(vault):
    _poison_vault(vault)
    svc.serve_manifest(vault, board_id="板", now=NOW)
    _degrade(vault)

    raw = svc.serve_manifest(vault, board_id="板", now=NOW)

    exam = project_manifest(raw, "exam").model_dump()
    study = project_manifest(raw, "study").model_dump()
    assert exam["degraded"] is True and study["degraded"] is True
    # study 面被删字段以安全默认回放 (无 ValidationError 即本断言主体)
    s = next(n for n in study["nodes"] if n["node_id"] == "M真薄弱")
    assert s["title"] is None and s["aliases"] == [] and s["tips"] == []
    assert s["calibration_count"] == 0
    # parse_errors 在降级态由 error_code 合成定长文案 (必填字段不缺)
    assert all(e["error"] for e in exam["parse_errors"])


# ══ P1-05c B3 (Codex 三轮 F-04/F-05/F-06) ══


def test_same_generation_forged_snapshot_self_heals(vault):
    """F-04: 同 generation 的伪造 v3(垃圾键)/v999 曾落入死区 — 写侧"够新就跳过"
    与读侧"不合规就拒载"判据不对称: 写侧永不重写、读侧永远 None、伪造留盘。
    修复后: 跳过判据 = 版本严格==3 且整份过 SnapshotV3 校验 → live 正常时自愈。"""
    _poison_vault(vault)
    svc.serve_manifest(vault, board_id="板", now=NOW)
    good = json.loads(svc.snapshot_file(vault).read_text(encoding="utf-8"))

    for tamper_name, tampered in [
        ("v3+junk", {**good, "CANARY_GARBAGE_KEY": "forged"}),
        ("v999", {**good, "snapshot_schema_version": 999}),
    ]:
        _put_snapshot(vault, tampered)
        result = svc.serve_manifest(vault, board_id="板", now=NOW)  # live ok, 同 generation
        assert result["source_status"] == "ok"
        on_disk = json.loads(svc.snapshot_file(vault).read_text(encoding="utf-8"))
        assert "CANARY_GARBAGE_KEY" not in on_disk, f"{tamper_name}: 伪造键未被自愈重写"
        assert on_disk["snapshot_schema_version"] == 3, f"{tamper_name}: 版本未被自愈"
        assert svc.load_snapshot(vault) is not None, f"{tamper_name}: 自愈后快照应可加载"


@pytest.mark.parametrize("root", [[], None, "v3"], ids=["list", "null", "str"])
def test_non_dict_root_snapshot_never_breaks_live_write_path(vault, root):
    """F-05: 根为 []/null 的旧快照曾让 **live 成功路径** 上的
    write_snapshot_if_changed 抛 AttributeError (prev.get on list) 穿透成 500。
    既有用例只测了先降级的 load 路径, 没盖住这条 — 本测试 live 目录完好。"""
    _poison_vault(vault)
    _put_snapshot(vault, root)

    result = svc.serve_manifest(vault, board_id="板", now=NOW)  # 不得抛

    assert result["source"] == "live" and result["source_status"] == "ok"
    on_disk = json.loads(svc.snapshot_file(vault).read_text(encoding="utf-8"))
    assert on_disk["snapshot_schema_version"] == 3, "坏根快照应被合法 v3 覆盖"


def test_strict_contract_rejects_lax_and_malformed(vault):
    """F-06: extra=forbid ≠ 严格契约 — 五类实锤反例全部必须 cache miss。"""
    data = _valid_v3_on_disk(vault)
    board = data["boards"]["板"]
    member = board["members"][0]

    def _clone():
        return json.loads(json.dumps(data, ensure_ascii=False))

    cases = {}
    c = _clone()
    c["boards"] = {"outer": {**c["boards"]["板"], "board_id": "inner"}}
    cases["board-key-mismatch"] = c

    c = _clone()
    c["boards"]["板"]["members"][0]["pick_eligible"] = "yes"  # lax 强转
    cases["lax-bool"] = c

    c = _clone()
    c["boards"]["板"]["members"][0]["attempt_count"] = "2"  # lax int
    cases["lax-int"] = c

    c = _clone()
    c["node_stems"] = ["x" * 10_000]
    cases["unbounded-stem"] = c

    c = _clone()
    c["freshness"]["generated_at"] = "not-a-time"
    cases["bad-time"] = c

    c = _clone()
    c["boards"]["板"]["members"][0]["node_id"] = "../CANARY\n"
    cases["traversal-node-id"] = c

    c = _clone()
    c["boards"]["板"]["concepts_listed"] = ["y" * 201]
    cases["overlong-concept"] = c

    for name, payload in cases.items():
        _put_snapshot(vault, payload)
        assert svc.load_snapshot(vault) is None, f"{name}: 错型快照未被拒 (F-06 回归)"
    # 引用消除 linter 噪音
    assert member["node_id"]


def test_write_side_filters_overlong_ids_instead_of_truncating(vault):
    """F-06: 201 字 concept 曾被静默截断成 200 字 — dual_source_gap 拿截断值
    比对把真实存在的 node 误判 exists=false。修复后写侧**过滤**超长项。"""
    from app.models.snapshot_v3 import project_full_state

    _poison_vault(vault)
    full = svc.scan_vault(vault, now=NOW)
    long_concept = "长" * 201
    full["boards"]["板"]["concepts_listed"] = ["M真薄弱", long_concept]
    full["node_stems"] = [*full["node_stems"], "s" * 500]

    snap = project_full_state(full).model_dump()

    assert long_concept not in snap["boards"]["板"]["concepts_listed"]
    assert long_concept[:200] not in snap["boards"]["板"]["concepts_listed"], "不得截断落盘"
    assert "M真薄弱" in snap["boards"]["板"]["concepts_listed"]
    assert all(len(s) <= 200 for s in snap["node_stems"])


def test_empty_pick_hint_dict_not_treated_as_eligible():
    """F-06(5): 旧态 full state 的 pick_hint={} 曾被 `is not None` 推导为
    eligible=True — 空 dict 不是有效 hint (生产不可达, 防御收紧)。"""
    from app.models.snapshot_v3 import _member_from_full

    m = {
        "node_id": "n1",
        "mastery": {"source": "absent", "score": None, "a": None, "b": None},
        "pick_hint": {},
    }
    assert _member_from_full(m)["pick_eligible"] is False


# ══ P1-05d C2 (Codex 四轮 V3/V4/V5) ══


def test_nested_bad_freshness_snapshot_self_heals(vault):
    """V3: {"snapshot_schema_version":3,"freshness":[]} 曾在 :956 抛 AttributeError
    被外层兜底吞成"写失败" → 坏快照永不自愈。修复后 live 正常时重写覆盖。"""
    _poison_vault(vault)
    _put_snapshot(vault, {"snapshot_schema_version": 3, "freshness": []})

    result = svc.serve_manifest(vault, board_id="板", now=NOW)

    assert result["source_status"] == "ok"
    on_disk = json.loads(svc.snapshot_file(vault).read_text(encoding="utf-8"))
    assert isinstance(on_disk.get("freshness"), dict), "嵌套错型快照未被自愈重写 (V3 回归)"
    assert svc.load_snapshot(vault) is not None


def test_dirty_last_examined_does_not_kill_snapshot(vault):
    """V4 (B3 引入的新回归止血): 单个脏 last_examined 曾让整个降级快照写不出。
    修复后: 脏值投影为 None (与"按从未考"语义一致), 快照照常落盘, 错误码保留。"""
    _poison_vault(vault)
    _write(
        vault,
        "节点/脏日期.md",
        _node_md(["mastery_score: 0.5", "last_examined: 这不是日期", 'source_board: "[[原白板/板]]"']),
    )

    result = svc.serve_manifest(vault, board_id="板", now=NOW)

    assert result["source_status"] == "ok"
    assert any(e.get("error_code") == "last_examined_invalid" for e in result["parse_errors"])
    assert svc.snapshot_file(vault).exists(), "单个脏 frontmatter 杀掉了整个降级快照 (V4 回归)"
    snap = json.loads(svc.snapshot_file(vault).read_text(encoding="utf-8"))
    dirty = next(m for m in snap["boards"]["板"]["members"] if m["node_id"] == "脏日期")
    assert dirty["last_examined"] is None, "脏时间原串不得落盘"
    # 降级态仍可用
    _degrade(vault)
    degraded = svc.serve_manifest(vault, board_id="板", now=NOW)
    assert degraded["source_status"] == "snapshot"


def test_overlong_ascii_stem_drops_member_not_snapshot(vault):
    """V5: 201 字 ASCII stem 在 APFS 合法 (<255 bytes) — 曾整包写失败。
    修复后: 丢该 member, 其余照常落盘。"""
    _poison_vault(vault)
    long_stem = "x" * 201
    _write(vault, f"节点/{long_stem}.md", _node_md(["mastery_score: 0.5", 'source_board: "[[原白板/板]]"']))

    result = svc.serve_manifest(vault, board_id="板", now=NOW)

    assert result["source_status"] == "ok"
    assert svc.snapshot_file(vault).exists(), "超长 stem 杀掉了整个快照"
    snap = json.loads(svc.snapshot_file(vault).read_text(encoding="utf-8"))
    ids = {m["node_id"] for m in snap["boards"]["板"]["members"]}
    assert long_stem not in ids and "M真薄弱" in ids


def test_no_id_slicing_and_no_nan_lag(vault):
    """V5: ID 语义字段写侧不得切片 (切片值=另一个 ID); lag_seconds 拒 NaN;
    _require_id_like 拒 tab 等控制字符。"""
    import math as _math

    from pydantic import ValidationError as _VE

    from app.models.snapshot_v3 import SnapshotV3Freshness, _require_id_like, project_full_state

    # tab 控制字符被拒
    with pytest.raises(ValueError):
        _require_id_like("bad\tid")
    # NaN lag_seconds 被拒
    with pytest.raises(_VE):
        SnapshotV3Freshness(
            generated_at="2026-08-20T00:00:00+00:00",
            generation="ab12cd34ef56",
            lag_seconds=_math.nan,
            stale=False,
        )
    # 超长 qid/selected_node 丢弃为 None 而非切片
    _poison_vault(vault)
    full = svc.scan_vault(vault, now=NOW)
    full["exam_history"] = [
        {
            "exam_board_id": "考察板",
            "board_id": "b" * 500,
            "created_at": None,
            "status": None,
            "selected_node": "s" * 500,
            "question_count": 1,
        }
    ]
    snap = project_full_state(full).model_dump()
    (eh,) = snap["exam_history"]
    assert eh["board_id"] is None and eh["selected_node"] is None, "超长 ID 被切片而非丢弃"
