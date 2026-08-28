"""学习事件账 schema v1 冻结契约 (CARD-G3-1, BATCH-2026-08-28-第五批)。

锁五件事:
  1. 真相源冻结 — learning_event_log 的 EVENT_VERSION=1 / 9 类白名单 / 7 键
     record 形状, 漂移即红;
  2. 校验脚本与真相源锁死同步 — validate_learning_events.py 的复制份常量
     不许与 learning_event_log 分叉;
  3. 判定正确性 — 合法 / 缺字段 / 重复 event_id 三 fixture 的 PASS/FAIL,
     加截断行 / 未知字段 / naive 时间戳 / 严格 JSON (NaN·重复键) / 非法
     UTF-8 / 分隔符词法 / §六 扩展键 / 前向兼容真跳过 各边界;
  4. 真实 producer 执行 (Codex round-1 HIGH 整改) — vault 三 skill 写点的
     python 代码从 SKILL.md 逐字提取执行 (仅路径常量重定向到 tmp fixture),
     backend 写点经真实 append_event; 产物必须过校验器 — SKILL.md 里的
     writer 代码漂移会在此翻红;
  5. 现网零误报 — real_shapes fixture 按 8 写点建模全过, 仓内 vault 根若
     存在真实账本则直接校验 (live 判据的可重跑锚)。

契约文档: docs/learning-events-schema-v1.md
"""

import builtins
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from app.services import learning_event_log as source

WT = Path(__file__).resolve().parents[3]
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "learning_events"
#: 仓内 vault 根账本 — worktree 无此文件 (skip), 主仓/live 环境即现网账本
REPO_VAULT_LEDGER = WT / "canvas-vault" / "learning_events.jsonl"

_spec = importlib.util.spec_from_file_location("validate_learning_events", VALIDATOR)
validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validator)


def _run(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
        timeout=60,
    )


# ── 1. 真相源冻结 ──


def test_event_version_frozen_at_1():
    assert source.EVENT_VERSION == 1


def test_event_types_frozen_nine():
    """白名单恰好 9 类 — 增删任一类都必须先过对账评审并同步契约。"""
    assert source.EVENT_TYPES == frozenset(
        {
            "node_derived",
            "exam_created",
            "answer_scored",
            "answer_abandoned",
            "candidate_created",
            "candidate_accepted",
            "candidate_disputed",
            "session_archived",
            "callout_ingested",
        }
    )


def test_append_event_record_shape_frozen(monkeypatch, tmp_path):
    """append_event 产出的行恰好 7 键且通过 v1 校验器 (写读同一契约)。"""
    ledger = tmp_path / "learning_events.jsonl"
    monkeypatch.setattr(source, "_log_path", lambda: ledger)
    assert source.append_event(
        "answer_scored",
        event_id="quiz:contract-1",
        node_id="Eigenvalues",
        payload={"grade_norm": 0.9},
    )
    record = json.loads(ledger.read_text().strip())
    assert set(record.keys()) == set(validator.TOP_LEVEL_KEYS)
    assert validator.validate_record(record) == []


# ── 2. 校验脚本与真相源锁死同步 ──


def test_validator_whitelist_matches_truth_source():
    assert validator.EVENT_TYPES == source.EVENT_TYPES


def test_validator_version_matches_truth_source():
    assert validator.EVENT_VERSION == source.EVENT_VERSION


# ── 3. 三 fixture 判定正确性 + 边界 ──


def test_fixture_valid_passes():
    result = _run(FIXTURES / "valid.jsonl")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULT: PASS" in result.stdout


def test_fixture_missing_field_fails():
    result = _run(FIXTURES / "missing_field.jsonl")
    assert result.returncode == 1
    assert "缺字段" in result.stdout
    assert "effective_at" in result.stdout


def test_fixture_duplicate_event_id_fails():
    result = _run(FIXTURES / "duplicate_event_id.jsonl")
    assert result.returncode == 1
    assert "重复" in result.stdout


def test_torn_line_detected(tmp_path):
    """断电截断行 = 违规如实报告 (审计工具必须暴露损坏, 不静默)。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(
        '{"event_id": "archive:ok", "event_version": 1, "event_type": "session_archived",'
        ' "node_id": "", "recorded_at": "2026-08-01T10:00:00+00:00",'
        ' "effective_at": "2026-08-01T10:00:00+00:00", "payload": {}}\n'
        '{"event_id": "archive:torn", "event_version": 1, "event_ty\n',
        encoding="utf-8",
    )
    result = _run(ledger)
    assert result.returncode == 1
    assert "JSON 解析失败" in result.stdout


def test_unknown_top_level_field_rejected():
    record = {
        "event_id": "quiz:x",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "",
        "recorded_at": "2026-08-01T10:00:00+00:00",
        "effective_at": "2026-08-01T10:00:00+00:00",
        "payload": {},
        "vault_id": "smuggled",
    }
    problems = validator.validate_record(record)
    assert any("未知顶层字段" in p for p in problems)


def test_naive_timestamp_rejected():
    record = {
        "event_id": "quiz:naive",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "",
        "recorded_at": "2026-08-01T10:00:00",
        "effective_at": "2026-08-01T10:00:00+00:00",
        "payload": {},
    }
    problems = validator.validate_record(record)
    # naive 串不匹配受理语法 (缺时区段) → 词法门先拦; 语义门 (tzinfo is None)
    # 作为纵深防御保留 (validate_record 之外的直接 _parse_ts 调用方)
    assert any("受理语法" in p or "timezone" in p for p in problems)
    assert validator._parse_ts("2026-08-01T10:00:00")[0] is False


def test_nan_constant_rejected(tmp_path):
    """RFC 8259 严格性: NaN/Infinity 是 Python json 扩展, 跨语言读方
    (JSON.parse) 会炸 — 审计器必须拦, 不得静默放行。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(
        '{"event_id": "quiz:nan", "event_version": 1, "event_type": "answer_scored",'
        ' "node_id": "", "recorded_at": "2026-08-01T10:00:00+00:00",'
        ' "effective_at": "2026-08-01T10:00:00+00:00", "payload": {"grade_norm": NaN}}\n',
        encoding="utf-8",
    )
    result = _run(ledger)
    assert result.returncode == 1
    assert "非标准 JSON 常量" in result.stdout


def test_duplicate_key_within_line_rejected(tmp_path):
    """行内重复键 json.loads 静默取后者 — 审计语义不容歧义, 判违规。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(
        '{"event_id": "a", "event_id": "b", "event_version": 1,'
        ' "event_type": "answer_scored", "node_id": "",'
        ' "recorded_at": "2026-08-01T10:00:00+00:00",'
        ' "effective_at": "2026-08-01T10:00:00+00:00", "payload": {}}\n',
        encoding="utf-8",
    )
    result = _run(ledger)
    assert result.returncode == 1
    assert "重复键" in result.stdout


def test_unknown_event_version_warns_not_fails(tmp_path):
    """前向兼容: 未知 event_version 行 → WARN 通道, 不判 FAIL。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(
        '{"event_id": "quiz:v2", "event_version": 2, "event_type": "answer_scored",'
        ' "node_id": "", "recorded_at": "2026-08-01T10:00:00+00:00",'
        ' "effective_at": "2026-08-01T10:00:00+00:00", "payload": {}}\n',
        encoding="utf-8",
    )
    result = _run(ledger)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WARN" in result.stdout
    assert "event_version=2" in result.stdout


def test_unknown_version_new_shape_truly_skipped(tmp_path):
    """Codex round-1 HIGH: v2 若形状变化 (缺 v1 键/加新键), 原实现 WARN+FAIL
    双发 exit 1 — 前向兼容必须**完全跳过**形状校验, 只 WARN。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(
        '{"event_id": "future:1", "event_version": 2, "brand_new_field": true, "payload_v2": [1, 2]}\n',
        encoding="utf-8",
    )
    result = _run(ledger)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WARN" in result.stdout
    assert "FAIL" not in result.stdout


def test_invalid_utf8_line_reported_not_crash(tmp_path):
    """Codex round-1 MEDIUM: 非法 UTF-8 字节序列 = 该行违规如实报告,
    不炸 traceback, 且不中断其余行的校验。"""
    ledger = tmp_path / "learning_events.jsonl"
    good = (
        '{"event_id": "archive:ok", "event_version": 1, "event_type": "session_archived",'
        ' "node_id": "", "recorded_at": "2026-08-01T10:00:00+00:00",'
        ' "effective_at": "2026-08-01T10:00:00+00:00", "payload": {}}\n'
    )
    ledger.write_bytes(b'{"event_id": "bad\xff\xfe"}\n' + good.encode("utf-8"))
    result = _run(ledger)
    assert result.returncode == 1
    assert "非法 UTF-8" in result.stdout
    assert "Traceback" not in result.stderr


def test_q_separator_rejected(tmp_path):
    """Codex round-1 MEDIUM: fromisoformat 接受任意单字符日期时间分隔符
    (如 'Q') — 校验器显式限 T/t/空格。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(
        '{"event_id": "quiz:qsep", "event_version": 1, "event_type": "answer_scored",'
        ' "node_id": "", "recorded_at": "2026-08-01Q10:00:00+00:00",'
        ' "effective_at": "2026-08-01T10:00:00+00:00", "payload": {}}\n',
        encoding="utf-8",
    )
    result = _run(ledger)
    assert result.returncode == 1
    assert "受理语法" in result.stdout


def _review_ext_line(**overrides):
    payload = {
        "schema_ext": "review/1",
        "vault_id": "canvas-vault",
        "concept_id": "Eigenvalues",
        "rating": 3,
        "review_time": "2026-08-01T10:00:00+00:00",
        "fsrs_library_version": "6.3.1",
        "fsrs_params_hash": "7b28ae29ac876981a7fca1424772214c7a4d9884439efd678ecb60e615b00342",
        "grade_norm": 0.75,
    }
    payload.update(overrides)
    return (
        json.dumps(
            {
                "event_id": "quiz:ext-1",
                "event_version": 1,
                "event_type": "answer_scored",
                "node_id": "Eigenvalues",
                "recorded_at": "2026-08-01T10:00:00+00:00",
                "effective_at": "2026-08-01T10:00:00+00:00",
                "payload": payload,
            },
            ensure_ascii=False,
        )
        + "\n"
    )


def test_review_ext_complete_row_passes(tmp_path):
    """§6.1: schema_ext=review/1 全键齐 → PASS; 降级哨兵形态同样合法。"""
    ledger = tmp_path / "learning_events.jsonl"
    degraded = _review_ext_line(
        fsrs_library_version="degraded:fsrs-import-failed",
        fsrs_params_hash="degraded:fsrs-import-failed",
    ).replace("quiz:ext-1", "quiz:ext-degraded")
    ledger.write_text(_review_ext_line() + degraded, encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 0, result.stdout + result.stderr


def test_review_ext_bad_rating_fails(tmp_path):
    """Codex round-1 HIGH: rating: true 曾静默 PASS — 扩展行强制 int 1-4,
    bool 伪装与越界均违规; 缺 review_time 同判。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(_review_ext_line(rating=True), encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1
    assert "rating" in result.stdout

    ledger.write_text(_review_ext_line(rating=5), encoding="utf-8")
    assert _run(ledger).returncode == 1

    ledger.write_text(_review_ext_line(review_time=None), encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1
    assert "review_time" in result.stdout


def test_control_char_wrapped_line_rejected(tmp_path):
    """Codex round-2 HIGH: str.strip() 会洗掉 RFC 8259 禁止的控制字符
    (U+001C-1F), 让敌对行伪装成合法 JSON — 只许剥行尾 CR/LF。"""
    ledger = tmp_path / "learning_events.jsonl"
    good = (
        '{"event_id": "archive:ok", "event_version": 1, "event_type": "session_archived",'
        ' "node_id": "", "recorded_at": "2026-08-01T10:00:00+00:00",'
        ' "effective_at": "2026-08-01T10:00:00+00:00", "payload": {}}'
    )
    ledger.write_text("" + good + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1, result.stdout


def test_timestamp_lexicon_variants_rejected(tmp_path):
    """Codex round-2 MEDIUM: fromisoformat 另收 week-date / 省略分钟 /
    '+00' offset / 逗号小数 / offset 秒 — §三受理语法须机械收窄。"""
    for bad in (
        "2026-W31-5T10:00:00+00:00",
        "2026-08-01T10+00:00",
        "2026-08-01T10:00:00+00",
        "2026-08-01T10:00:00,500+00:00",
        "2026-08-01T10:00:00+00:00:30",
    ):
        problems = validator._parse_ts(bad)
        assert not problems[0], f"{bad!r} 不应被受理"


def test_oversized_int_literal_not_crash(tmp_path):
    """Codex round-2 MEDIUM: 超长整数字面量触发 stdlib 限额 ValueError —
    该行判违规, 不炸整个校验。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(
        '{"event_id": "x", "event_version": ' + "9" * 5000 + "}\n",
        encoding="utf-8",
    )
    result = _run(ledger)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


def test_review_ext_cross_field_bindings(tmp_path):
    """Codex round-2 HIGH: concept_id/node_id、review_time/effective_at、
    version+hash 形状、degraded 成对 — 跨字段绑定必须机械验证。"""
    ledger = tmp_path / "learning_events.jsonl"
    cases = [
        ({"concept_id": "另一个节点"}, "concept_id"),
        ({"review_time": "2026-08-02T10:00:00+00:00"}, "effective_at"),
        ({"fsrs_library_version": "not-a-version"}, "fsrs_library_version"),
        ({"fsrs_params_hash": "deadbeef"}, "fsrs_params_hash"),
        ({"fsrs_library_version": "degraded:x"}, "成对"),  # hash 仍真实值 → 不成对
        ({"fsrs_library_version": "degraded:", "fsrs_params_hash": "degraded: "}, "非空原因"),
    ]
    for overrides, expected_marker in cases:
        ledger.write_text(_review_ext_line(**overrides), encoding="utf-8")
        result = _run(ledger)
        assert result.returncode == 1, f"{overrides} 应判违规\n{result.stdout}"
        assert expected_marker in result.stdout, f"{overrides} 的报告缺 {expected_marker}\n{result.stdout}"


def _review_ext_record(event_type="answer_scored", node_id="Eigenvalues", **overrides):
    """round-3 反例构造器: 可改顶层 event_type/node_id 与任意 payload 键。"""
    payload = {
        "schema_ext": "review/1",
        "vault_id": "canvas-vault",
        "concept_id": "Eigenvalues",
        "rating": 3,
        "review_time": "2026-08-01T10:00:00+00:00",
        "fsrs_library_version": "6.3.1",
        "fsrs_params_hash": "7b28ae29ac876981a7fca1424772214c7a4d9884439efd678ecb60e615b00342",
        "grade_norm": 0.75,
    }
    payload.update(overrides)
    return {
        "event_id": "quiz:r3",
        "event_version": 1,
        "event_type": event_type,
        "node_id": node_id,
        "recorded_at": "2026-08-01T10:00:00+00:00",
        "effective_at": "2026-08-01T10:00:00+00:00",
        "payload": payload,
    }


def test_review_time_must_be_whole_second(tmp_path):
    """Codex round-3 BLOCKER: W (frontmatter fsrs_last_review) 只有整秒精度,
    小数秒 review_time 恒满足 `> W` → 同一事件重放二次推进 (实测 Learning→Review)。
    契约 §6.2 A5 要求整秒, 校验器机械强制。"""
    ledger = tmp_path / "learning_events.jsonl"
    rec = _review_ext_record(review_time="2026-08-01T10:00:00.500000+00:00")
    rec["effective_at"] = "2026-08-01T10:00:00.500000+00:00"
    ledger.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1
    assert "整秒" in result.stdout


def test_review_ext_marker_downgrade_blocked(tmp_path):
    """Codex round-3 HIGH: schema_ext='review/01' 或非字符串曾让扩展门整体
    静默跳过 (坏行降级为历史行 exit 0); 去掉 marker 只留扩展键同理。"""
    ledger = tmp_path / "learning_events.jsonl"
    for marker in ("review/01", "review/2", 1, None):
        rec = _review_ext_record(concept_id="不匹配的节点")
        rec["payload"]["schema_ext"] = marker
        ledger.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
        result = _run(ledger)
        assert result.returncode == 1, f"marker={marker!r} 应判违规\n{result.stdout}"
        assert "schema_ext" in result.stdout

    rec = _review_ext_record(concept_id="不匹配的节点")
    del rec["payload"]["schema_ext"]
    ledger.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1, "带扩展键却无 marker 应判违规\n" + result.stdout
    assert "缺 schema_ext" in result.stdout


def test_review_ext_semantic_bindings(tmp_path):
    """Codex round-3 HIGH: 挂载点 / rating-grade 自洽 / 弃答一票否决 /
    库指纹绑定 manifest 真值 / grade_norm 必填, 逐条机械验证。"""
    ledger = tmp_path / "learning_events.jsonl"
    cases = [
        (dict(event_type="session_archived"), "只许挂在"),
        (dict(rating=4, grade_norm=0.0), "不自洽"),
        (dict(event_type="answer_abandoned", rating=4), "弃答"),
        (dict(fsrs_library_version="999.999"), "golden manifest 真值"),
        (dict(fsrs_params_hash="0" * 64), "golden manifest 真值"),
        (dict(grade_norm=None), "grade_norm"),
        (dict(grade_norm=1.5), "grade_norm"),
        (dict(grade_norm=True), "grade_norm"),
    ]
    for kwargs, marker in cases:
        event_type = kwargs.pop("event_type", "answer_scored")
        rec = _review_ext_record(event_type=event_type, **kwargs)
        ledger.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
        result = _run(ledger)
        assert result.returncode == 1, f"{event_type}/{kwargs} 应判违规\n{result.stdout}"
        assert marker in result.stdout, f"{event_type}/{kwargs} 报告缺 {marker!r}\n{result.stdout}"


def test_review_ext_valid_variants_pass(tmp_path):
    """零误报守卫: 合法扩展行 (含弃答 rating=1、Z/+00:00 混写、degraded 成对) 全过。"""
    ledger = tmp_path / "learning_events.jsonl"
    abandoned = _review_ext_record(event_type="answer_abandoned", rating=1, grade_norm=0.0)
    abandoned["event_id"] = "quiz:r3-abandoned"
    mixed_tz = _review_ext_record(review_time="2026-08-01T10:00:00Z")
    mixed_tz["event_id"] = "quiz:r3-tz"
    degraded = _review_ext_record(
        fsrs_library_version="degraded:fsrs-import-failed",
        fsrs_params_hash="degraded:fsrs-import-failed",
    )
    degraded["event_id"] = "quiz:r3-degraded"
    ledger.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in (abandoned, mixed_tz, degraded)),
        encoding="utf-8",
    )
    result = _run(ledger)
    assert result.returncode == 0, result.stdout + result.stderr


def test_out_of_order_marker_shape_frozen(tmp_path):
    """Codex round-4 HIGH#3: `out_of_order` 的位置/类型/真假语义未冻结时,
    字符串或对象值均零违规 — 而 pending 排除条件依赖该标记, 歧义即漏事件。
    唯一合法形态: payload.out_of_order === true; 未标则不写该键。"""
    ledger = tmp_path / "learning_events.jsonl"
    for bad in ("true", {"x": 1}, False, 1, None):
        rec = _review_ext_record()
        rec["payload"]["out_of_order"] = bad
        ledger.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
        result = _run(ledger)
        assert result.returncode == 1, f"out_of_order={bad!r} 应判违规\n{result.stdout}"
        assert "out_of_order" in result.stdout

    rec = _review_ext_record()
    rec["payload"]["out_of_order"] = True
    ledger.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    assert _run(ledger).returncode == 0, "out_of_order=true 是唯一合法形态"


def test_review_time_must_carry_seconds(tmp_path):
    """Codex round-4 HIGH#1: 省略秒段的 '10:00+00:00' 与 W 的整秒口径对不齐,
    且不是任何写点会产出的形态 — review/1 要求完整整秒形态。"""
    ledger = tmp_path / "learning_events.jsonl"
    rec = _review_ext_record(review_time="2026-08-01T10:00+00:00")
    rec["effective_at"] = "2026-08-01T10:00+00:00"
    ledger.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1
    assert "完整整秒形态" in result.stdout


def test_manifest_corrupt_forms_degrade_not_crash():
    """Codex round-4 MEDIUM: manifest 为 None / 空 dict / list / 标量 时,
    扩展校验必须降级为形状校验 + WARN, 不得 AttributeError/traceback。"""
    record = _review_ext_record()
    for bad_manifest in (None, {}, [1, 2], 42, "text"):
        problems, warnings = validator._validate_review_ext(
            record["payload"], record, bad_manifest, vault_id=record["payload"]["vault_id"]
        )
        assert problems == [], f"manifest={bad_manifest!r} 不应产生违规: {problems}"
        assert any("只做形状校验" in w for w in warnings), f"manifest={bad_manifest!r} 应降级 WARN"


def test_vault_id_bound_to_vault_config(tmp_path):
    """`payload.vault_id` 必须等于账本所在 vault 的**规范化** vault_id
    (与生产 `Settings.vault_id` 同链: safe_load → sanitize_vault_id)。

    ⚠️ round-11: 事件里的 `vault_id` 也必须是**规范化后**的形式 —— 配置写
    `"canvas-vault"` 时生产取值是 `canvas_vault`(连字符被 sanitize 成下划线),
    事件若写原始连字符形式即判不一致。§6.1 已冻结该口径。
    """
    ledger = tmp_path / "learning_events.jsonl"

    # 无 .canvas-config.yaml → 只 WARN 不判错
    ledger.write_text(json.dumps(_review_ext_record(), ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 0, result.stdout
    assert "vault_id 未绑定" in result.stdout

    # 有配置且事件用规范化值 → PASS
    (tmp_path / ".canvas-config.yaml").write_text(
        '# 注释行\nvault_id: "canvas-vault"\nsubject: cs-61b\n', encoding="utf-8"
    )
    normalized = _review_ext_record(vault_id="canvas_vault")  # sanitize 后形式
    ledger.write_text(json.dumps(normalized, ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 0, result.stdout

    # 事件写未规范化的原始值 → 违规 (与生产取值不同)
    raw = _review_ext_record(vault_id="canvas-vault")
    ledger.write_text(json.dumps(raw, ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1
    assert "账本所在 vault" in result.stdout

    # 完全不同的 vault → 违规
    mismatched = _review_ext_record(vault_id="别的vault")
    ledger.write_text(json.dumps(mismatched, ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1
    assert "账本所在 vault" in result.stdout


def test_watermark_comparison_must_be_instant_based():
    """§6.2 比较语义: bridge 的 _iso() 把 W 归一化为 UTC 'Z' 形式, 而事件
    review_time 允许任意合法 offset — 同一瞬间可有不同字符串。按字符串比较
    会把"已应用"误判为 pending 并二次推进, 故契约要求按绝对瞬间比较。

    本测试钉死该等价关系 (bridge 改写出格式时会红) 与整秒性在 UTC 归一化
    后的保持 (A5 前提)。
    """
    sys.path.insert(0, str(WT / "canvas-vault" / ".claude" / "scripts"))
    import fsrs_bridge as fb  # noqa: PLC0415

    event_time = "2026-08-01T18:00:00+08:00"
    watermark = fb._iso(fb._aware(event_time))
    assert watermark == "2026-08-01T10:00:00Z", "bridge 写出格式漂移 — 比较语义前提须复核"
    assert watermark != event_time, "本测试的前提是两者字符串不同"
    assert validator._instant(event_time) == validator._instant(watermark), (
        "同一瞬间必须比较相等 — 否则水位线判据会二次推进"
    )
    assert validator._parse_ts(event_time)[0] and not validator._SUBSECOND_RE.match(event_time)


def _fsrs_fields(**overrides):
    base = {
        "fsrs_last_review": "2026-01-01T00:00:00Z",
        "fsrs_due": "2026-01-02T00:00:00Z",
        "fsrs_state": 2,
        "fsrs_stability": 10.0,
        "fsrs_difficulty": 5.0,
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


def test_classify_card_state_matrix():
    """§6.2 三态判别的可执行实现 (Codex round-6 HIGH#1)。

    四个 round-6 反例在真实 bridge `review()` 上分别抛 AssertionError、
    写回非 canonical tuple、ZeroDivisionError、产生 NaN 路径 —— 规则必须
    把它们判 degraded 而非 normal。
    """
    cases = [
        ({}, "new"),
        # round-6 四反例
        (_fsrs_fields(fsrs_state=3, fsrs_step=None), "degraded"),  # 缺 step → AssertionError
        (_fsrs_fields(fsrs_state=2, fsrs_step=0), "degraded"),  # Review 带 step → 非 canonical
        (
            _fsrs_fields(fsrs_state=1, fsrs_step=0, fsrs_stability=0, fsrs_difficulty=0),
            "degraded",
        ),  # S=D=0 → ZeroDivisionError
        (_fsrs_fields(fsrs_stability=1e308, fsrs_difficulty=1e308), "degraded"),  # → NaN 路径
        # canonical 形态
        (_fsrs_fields(), "normal"),  # Review
        (_fsrs_fields(fsrs_state=1, fsrs_step=0, fsrs_stability=None, fsrs_difficulty=None), "normal"),
        (_fsrs_fields(fsrs_state=3, fsrs_step=0, fsrs_stability=2.0, fsrs_difficulty=6.0), "normal"),
        # 残缺组合
        (_fsrs_fields(fsrs_last_review=None), "degraded"),
        (_fsrs_fields(fsrs_due=None, fsrs_state=None, fsrs_stability=None, fsrs_difficulty=None), "degraded"),
        (_fsrs_fields(fsrs_state=0), "degraded"),  # legacy
        (_fsrs_fields(fsrs_state=2, fsrs_difficulty=0.5), "degraded"),  # difficulty 越界
        (_fsrs_fields(fsrs_stability=float("nan")), "degraded"),
        (_fsrs_fields(fsrs_last_review="not-a-time"), "degraded"),
    ]
    for fields, expected in cases:
        got, reason = validator.classify_card_state(fields)
        assert got == expected, f"{fields} → {got} ({reason}), 期望 {expected}"


def test_stability_has_no_maximum_interval_ceiling():
    """Codex round-7 HIGH: 早前把 maximum_interval=36500 当 stability 上界是
    **本方引入的误报** — FSRS 封顶的是 interval 不是 stability。真实连续
    Easy 链 7 次后 S=68949 > 36500, 合法卡曾被误判 degraded。"""
    got, reason = validator.classify_card_state(_fsrs_fields(fsrs_stability=68949.18))
    assert got == "normal", f"高 stability 合法卡不得判 degraded: {reason}"
    # 但 0 与负数仍非法 (调度器 ZeroDivisionError)
    assert validator.classify_card_state(_fsrs_fields(fsrs_stability=0))[0] == "degraded"
    assert validator.classify_card_state(_fsrs_fields(fsrs_stability=-1.0))[0] == "degraded"
    # difficulty 的 [1,10] 定义域仍生效
    assert validator.classify_card_state(_fsrs_fields(fsrs_difficulty=10.5))[0] == "degraded"


def test_review_domain_closure():
    """Codex round-9 HIGH#1: schema 允许 review_time <= 9000 而分类器拒绝
    W >= 9000 ⇒ 合法事件写出 W 后立即判 degraded(确定性制造残缺卡)。
    闭包要求: review_time 与 W **同域同界且均须严格小于** REVIEW_INPUT_MAX。"""
    # 输入侧
    assert validator._parse_ts("9000-01-01T00:00:00Z", upper_bound=validator.REVIEW_INPUT_MAX)[0] is False
    assert validator._parse_ts("8999-12-31T23:59:59Z", upper_bound=validator.REVIEW_INPUT_MAX)[0] is True
    # 输出侧 (W) 同界
    assert validator.classify_card_state(_fsrs_fields(fsrs_last_review="9000-01-01T00:00:00Z"))[0] == "degraded"
    assert validator.classify_card_state(_fsrs_fields(fsrs_last_review="8999-12-31T23:59:59Z"))[0] == "normal"
    # 一般时间戳 (fsrs_due) 仍用宽上界
    assert validator.classify_card_state(_fsrs_fields(fsrs_due="9400-01-01T00:00:00Z"))[0] == "normal"


def test_watermark_must_be_whole_second():
    """Codex round-9 MEDIUM: 分类器曾接受非整秒 W, 与 §6.2 A5 的 canonical
    秒精度不一致。"""
    got, reason = validator.classify_card_state(_fsrs_fields(fsrs_last_review="2026-01-01T00:00:00.5Z"))
    assert got == "degraded" and "小数秒" in reason, reason


def test_stability_semantic_ceiling():
    """Codex round-8 HIGH#1: 'any finite positive' 过宽 — S=1.797e308 曾判
    normal 而真实 bridge 抛 OverflowError(float infinity to integer)。
    ⚠️ round-9 措辞更正: 1e9 天是**语义合理性上界**(fail-closed), 不是技术
    可执行上界 — 实测 1e10/1e100 真实 bridge 都能跑, 但该量级必是数据损坏,
    保守拦下要人工确认。这是有意的偏差, 不是"会溢出"。"""
    assert validator.classify_card_state(_fsrs_fields(fsrs_stability=1.7976931348623157e308))[0] == "degraded"
    assert validator.classify_card_state(_fsrs_fields(fsrs_stability=1e10))[0] == "degraded"
    assert validator.classify_card_state(_fsrs_fields(fsrs_stability=1e9))[0] == "normal"
    assert validator.classify_card_state(_fsrs_fields(fsrs_stability=68949.18))[0] == "normal"


def test_oversized_numeric_field_fails_closed():
    """Codex round-9 MEDIUM: float(10**309) 抛 OverflowError —
    _finite_number 须 fail-closed 返回 None ⇒ degraded, 不得炸出去。"""
    for value in (10**309, "1" + "0" * 400, 10**400):
        got, reason = validator.classify_card_state(_fsrs_fields(fsrs_stability=value))
        assert got == "degraded", f"{value!r} → {got} ({reason})"
    assert validator._finite_number(10**309) is None


def test_watermark_must_leave_room_for_successor():
    """Codex round-8 HIGH#2: W=9400 曾判 normal, 但任何合法后继须
    review_time > W 且 <= 9000(review 域上界) ⇒ 空集; W 恰为上界时
    A3 的 W+1s 也立即越界。W 必须严格小于 review 上界。"""
    assert validator.classify_card_state(_fsrs_fields(fsrs_last_review="9400-01-01T00:00:00Z"))[0] == "degraded"
    assert validator.classify_card_state(_fsrs_fields(fsrs_last_review="9000-01-01T00:00:00Z"))[0] == "degraded"
    assert validator.classify_card_state(_fsrs_fields(fsrs_last_review="8999-12-31T23:59:59Z"))[0] == "normal"
    # fsrs_due 是调度产物, 用更宽的一般上界
    assert validator.classify_card_state(_fsrs_fields(fsrs_due="9400-01-01T00:00:00Z"))[0] == "normal"


def test_oversized_int_field_degrades_not_crash():
    """Codex round-8 MEDIUM: 5000 位纯整数曾让 _int_lexeme 自身抛
    ValueError(stdlib int_max_str_digits 限额), 未返回 degraded。"""
    got, reason = validator.classify_card_state(_fsrs_fields(fsrs_state="9" * 5000))
    assert got == "degraded", reason


def test_integer_fields_use_int_lexeme():
    """Codex round-7 HIGH: float() 判整数会让 `fsrs_state: "1.0"` 通过, 而
    真实 bridge 的 int("1.0") 抛 ValueError (fsrs_bridge.py:106)。"""
    assert validator.classify_card_state(_fsrs_fields(fsrs_state="1.0"))[0] == "degraded"
    assert validator.classify_card_state(_fsrs_fields(fsrs_state=2.0))[0] == "degraded"
    assert validator.classify_card_state(_fsrs_fields(fsrs_state="2"))[0] == "normal"
    assert validator.classify_card_state(_fsrs_fields(fsrs_state=3, fsrs_step="0.0"))[0] == "degraded"
    assert validator.classify_card_state(_fsrs_fields(fsrs_state=3, fsrs_step="0"))[0] == "normal"


def test_a7_bounds_are_tiered():
    """Codex round-7 MEDIUM: 把 review 输入上界通用到所有字段, 会让合法
    review_time=9000 产出的 due=9000-01-09 反被判 degraded。"""
    # review 输入上界 9000
    assert validator._parse_ts("9000-01-01T00:00:01Z", upper_bound=validator.REVIEW_INPUT_MAX)[0] is False
    assert validator._parse_ts("8999-12-31T23:59:59Z", upper_bound=validator.REVIEW_INPUT_MAX)[0] is True
    # 一般时间戳上界更宽 — due=9000-01-09 必须受理
    assert validator._parse_ts("9000-01-09T00:00:00Z")[0] is True
    assert validator._parse_ts("9499-12-31T23:59:59Z")[0] is True
    assert validator._parse_ts("9999-12-31T23:59:59Z")[0] is False
    # 三态判别对该 due 不得误判
    got, reason = validator.classify_card_state(_fsrs_fields(fsrs_due="9000-01-09T00:00:00Z"))
    assert got == "normal", reason


def test_schedulable_time_upper_bound():
    """A7 (round-6 MEDIUM, round-7 分档): 一般时间戳只拦 UTC 归一化本身会
    溢出的极端值; review 输入的更保守上界见 test_a7_bounds_are_tiered。"""
    assert validator._parse_ts("9999-12-31T23:59:59Z")[0] is False
    assert validator._parse_ts("2026-08-01T10:00:00Z")[0] is True
    assert validator._parse_ts("9000-01-01T00:00:01Z", upper_bound=validator.REVIEW_INPUT_MAX)[0] is False


def _backend_vault_id(config_dir: Path):
    """**真实生产入口**: Settings(CANVAS_BASE_PATH=...).vault_id。

    round-11 HIGH#2: 此前的 oracle 只自行复刻 safe_load + strip, 漏掉生产
    链路里的 sanitize_vault_id() (config.py:1020) —— 实测 `vault_id: team#1`
    生产得 team_1 而校验器曾绑定 team#1。现直接调真实 property, 不再复刻。
    """
    from app.config import Settings  # noqa: PLC0415

    try:
        return Settings(
            CANVAS_BASE_PATH=str(config_dir),
            DEBUG=True,
            CORS_ORIGINS="http://localhost:3000",
            INTERNAL_API_KEY="test-only-not-a-secret",
        ).vault_id
    except Exception:  # noqa: BLE001 — 生产入口异常时视为无可信值
        return None


def test_vault_id_never_misbinds_against_real_backend(tmp_path):
    """**安全性质**: 校验器绑定的 vault_id 要么等于真实生产入口取值, 要么是
    None (降级不绑定) —— **绝不产生与生产不同的非 None 值**。

    为何是这个性质而非"值恒等" (round-11 口径): 生产 Settings.vault_id 在
    显式字段无效时会回退到目录名/环境推断, 而校验器**不知道运行时环境**,
    对这类输入一律不绑定。不绑定 = 少一层防护(安全); 错绑 = 用错身份判事件
    归属(危险)。本测试锁住的正是"不错绑"。
    """
    cases = [
        ("vault_id: team#1\n", "sanitize 改写 (# → _)"),
        ('vault_id: "CS 61B"\n', "空格与大写归一"),
        ('vault_id: "../etc/passwd"\n', "路径穿越消解"),
        ('vault_id: "café"\n', "NFKC 保留重音"),
        ("vault_id: 0x10\n", "十六进制 (PyYAML 得 int)"),
        ("vault_id: 1_000\n", "下划线数字"),
        ("vault_id: -.inf\n", "负无穷"),
        ('vault_id: fake\n"vault_\\u0069d": real\n', "Unicode 转义键名"),
        ('other: "x\nvault_id: fake\nmore"\n', "多行引号体内的列首"),
        ('vault_id: fake\n"vault_id": real\n', "双引号键"),
        ("vault_id: fake\n'vault_id': real\n", "单引号键"),
        ("vault_id: true\n", "隐式 bool"),
        ("vault_id: null\n", "隐式 null"),
        ("vault_id: fake\nvault_id : real\n", "键后空格"),
        ("vault_id: first\n  second\n", "plain scalar 折行"),
        ("vault_id: old\ndescription: it's fine\nvault_id: new\n", "值内撇号 + 重复键"),
        ('vault_id: "team#1"\n', "引号内 #"),
        ("vault_id: |\n  block\n", "block scalar"),
        ('vault_id: "unclosed\n', "未闭引号 (YAMLError)"),
        ('vault_id: "canvas_vault"\nsubject: cs-61b\n', "现网形态"),
        ("vault_id: canvas_vault\n", "安全裸词"),
        ('vault_id: "中文库"\n', "中文值"),
        ('  vault_id: "indented"\n', "缩进"),
        ("vault_id:\n", "空值"),
        ('# 注释提到 vault_id\nvault_id: "ok"\n', "注释提及 + 真键"),
    ]
    misbinds = []
    for index, (content, desc) in enumerate(cases):
        config_dir = tmp_path / f"case{index}"
        config_dir.mkdir()
        (config_dir / ".canvas-config.yaml").write_text(content, encoding="utf-8")
        got = validator._vault_id_of(config_dir / "learning_events.jsonl")
        truth = _backend_vault_id(config_dir)
        if got is not None and got != truth:
            misbinds.append(f"[{desc}] validator={got!r} != 生产 {truth!r}")
    assert not misbinds, "校验器错绑 (绑定值与真实生产入口不同):\n" + "\n".join(misbinds)

    bad_utf8 = tmp_path / "badutf8"
    bad_utf8.mkdir()
    (bad_utf8 / ".canvas-config.yaml").write_bytes(b'vault_id: "\xff\xfe"\n')
    assert validator._vault_id_of(bad_utf8 / "learning_events.jsonl") is None
    assert validator._vault_id_of(tmp_path / "nowhere" / "learning_events.jsonl") is None


def test_vault_config_parse_errors_degrade_not_crash(tmp_path):
    """Codex round-12 MEDIUM: `vault_id: 2023-13-40` 让 PyYAML 的 timestamp
    constructor 抛 **ValueError**(非 YAMLError) — 窄捕获会 traceback + exit 1,
    而生产 (config.py:777) 捕 Exception 后回退。校验器须同口径降级。"""
    ledger_name = "learning_events.jsonl"
    for content, desc in [
        ("vault_id: 2023-13-40\n", "非法日期 (timestamp constructor ValueError)"),
        ("vault_id: [1, 2\n", "语法错 (YAMLError)"),
        ("[" * 2000 + "]" * 2000 + "\n", "深嵌套 YAML (RecursionError)"),
        ("!!python/object:os.system\nvault_id: x\n", "未知标签 (ConstructorError)"),
    ]:
        config_dir = tmp_path / f"case{abs(hash(content)) % 10**8}"
        config_dir.mkdir()
        (config_dir / ".canvas-config.yaml").write_text(content, encoding="utf-8")
        got = validator._vault_id_of(config_dir / ledger_name)
        assert got is None, f"[{desc}] 应降级为不绑定, 实为 {got!r}"

    # 端到端: 坏配置下账本仍能通过校验 (只 WARN 不 FAIL)
    config_dir = tmp_path / "e2e"
    config_dir.mkdir()
    (config_dir / ".canvas-config.yaml").write_text("vault_id: 2023-13-40\n", encoding="utf-8")
    ledger = config_dir / ledger_name
    ledger.write_text(json.dumps(_review_ext_record(), ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "vault_id 未绑定" in result.stdout
    assert "Traceback" not in result.stderr


def test_vault_id_degrades_without_pyyaml_and_warns(tmp_path, monkeypatch):
    """PyYAML 不可用时降级为不绑定; review/1 行据此产生 WARN 而非 FAIL
    (round-11: 此前只断言 None, 未验证 WARN 通道)。"""
    config_dir = tmp_path / "novyaml"
    config_dir.mkdir()
    (config_dir / ".canvas-config.yaml").write_text('vault_id: "x"\n', encoding="utf-8")
    real_import = builtins.__import__

    def _blocked(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("simulated: PyYAML absent")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocked)
    assert validator._vault_id_of(config_dir / "learning_events.jsonl") is None

    record = _review_ext_record()
    problems, warnings = validator._validate_review_ext(record["payload"], record, None, vault_id=None)
    assert not any("账本所在 vault" in p for p in problems)
    assert any("vault_id 未绑定" in w for w in warnings), warnings


def test_rating_from_grade_parity_with_bridge():
    """校验器的 rating 自洽判据必须与真相源 fsrs_bridge.rating_from_grade
    逐档一致 — 否则 bridge 改档位时校验器会静默漂移 (误报或漏报)。

    全网格 0.000-1.000 步长 0.001 + 三个档位分界两侧精确核对。
    """
    bridge_path = WT / "canvas-vault" / ".claude" / "scripts"
    sys.path.insert(0, str(bridge_path))
    import fsrs_bridge as fb  # noqa: PLC0415

    mismatches = [
        (i / 1000.0, fb.rating_from_grade(i / 1000.0, False), validator._rating_from_grade_norm(i / 1000.0))
        for i in range(1001)
        if fb.rating_from_grade(i / 1000.0, False) != validator._rating_from_grade_norm(i / 1000.0)
    ]
    assert not mismatches, f"档位口径漂移 (前 5): {mismatches[:5]}"

    for boundary in (1 / 6, 1 / 2, 5 / 6):
        for gn in (boundary - 1e-9, boundary, boundary + 1e-9):
            assert fb.rating_from_grade(gn, False) == validator._rating_from_grade_norm(gn), gn

    assert fb.rating_from_grade(1.0, abandoned=True) == 1, "弃答一票否决 Again 的真相源前提失效"


def test_offset_minute_range_enforced():
    """Codex round-3 MEDIUM: offset 分钟 \\d{2} 曾收 '+00:60'/'+00:99'。"""
    for bad in ("2026-08-01T10:00:00+00:60", "2026-08-01T10:00:00+00:99"):
        assert validator._parse_ts(bad)[0] is False, bad
    for good in ("2026-08-01T10:00:00+08:45", "2026-08-01T10:00:00-03:30"):
        assert validator._parse_ts(good)[0] is True, good


def test_deep_nesting_not_crash(tmp_path):
    """Codex round-3 MEDIUM: 深层嵌套曾 RecursionError 栈溢出并静默中断后续行。"""
    ledger = tmp_path / "learning_events.jsonl"
    depth = 200_000
    good = (
        '{"event_id": "archive:ok", "event_version": 1, "event_type": "session_archived",'
        ' "node_id": "", "recorded_at": "2026-08-01T10:00:00+00:00",'
        ' "effective_at": "2026-08-01T10:00:00+00:00", "payload": {}}'
    )
    ledger.write_text("[" * depth + "]" * depth + "\n" + good + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "LINE 1" in result.stdout


def test_review_ext_marker_absent_means_legacy_untouched(tmp_path):
    """§6.3: 无 schema_ext 标记的历史行零追溯 — 扩展键缺失不判 FAIL。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(
        '{"event_id": "quiz:legacy", "event_version": 1, "event_type": "answer_scored",'
        ' "node_id": "n", "recorded_at": "2026-08-01T10:00:00+00:00",'
        ' "effective_at": "2026-08-01T10:00:00+00:00",'
        ' "payload": {"grade_norm": 0.5}}\n',
        encoding="utf-8",
    )
    assert _run(ledger).returncode == 0


# ── 4. 真实 producer 执行 (Codex round-1 HIGH 整改: 不再只靠手工 shapes) ──

SKILLS = WT / "canvas-vault" / ".claude" / "skills"


def test_real_producer_backend_append_event(monkeypatch, tmp_path):
    """backend 侧真实 producer = append_event 本体 (5 调用点共用),
    按 5 个调用点的实参形状逐一真实写入, 产物过校验器。"""
    ledger = tmp_path / "learning_events.jsonl"
    monkeypatch.setattr(source, "_log_path", lambda: ledger)
    calls = [
        (
            "callout_ingested",
            "callout:cb-1",
            "Eigenvalues",
            {"callout_type": "question", "text": "为什么?"},
            "2026-08-01T10:00:00+00:00",
        ),
        ("session_archived", "archive:s-1", "n", {"tips": 1, "errors": 0, "group_id": "g"}, None),
        ("candidate_accepted", "accept:c-1", "n", {"edited": False}, None),
        ("candidate_disputed", "dispute:c-1", "n", {"dispute_reason": "不是错误"}, None),
        ("candidate_created", "cand:c-2", "n", {"source": "distillation", "description": "d"}, None),
    ]
    for etype, eid, node, payload, eff in calls:
        assert source.append_event(etype, event_id=eid, node_id=node, payload=payload, effective_at=eff)
    assert _run(ledger).returncode == 0
    assert len(ledger.read_text(encoding="utf-8").strip().splitlines()) == 5


def test_real_producer_ai_linked_doc_writer(tmp_path):
    """vault 写点 1/3: ai-linked-doc 的 python3 -c 单行模板**逐字提取执行**
    (仅替换 SKILL 自身声明的两处 <> 占位), 产物过校验器 + 幂等 —
    SKILL.md 里的 writer 代码漂移会在此翻红。"""
    text = (SKILLS / "ai-linked-doc" / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r'python3 -c "(.+?)"`', text, re.DOTALL)
    assert m, "ai-linked-doc SKILL.md 找不到 python3 -c 写点模板"
    code = m.group(1).replace("<vault绝对路径>", str(tmp_path)).replace("<新节点名>", "测试节点")
    for _ in range(2):  # 二跑验证幂等
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, proc.stderr
    ledger = tmp_path / "learning_events.jsonl"
    assert len(ledger.read_text(encoding="utf-8").strip().splitlines()) == 1
    assert _run(ledger).returncode == 0


def test_real_producer_start_exam_board_writer(tmp_path):
    """vault 写点 2/3: start-exam-board Step 6.5 PYEOF 块逐字提取执行。
    唯一重定向 = P 常量 (SKILL 硬编码 /tmp, 测试指到 tmp fixture 防与真实
    skill 并发运行相撞); writer 逻辑字节原样。"""
    text = (SKILLS / "start-exam-board" / "SKILL.md").read_text(encoding="utf-8")
    blocks = re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", text, re.DOTALL)
    matches = [b for b in blocks if 'P = "/tmp/exam-created-event.json"' in b]
    assert len(matches) == 1, f"SKILL.md 应恰有 1 个账本写点 PYEOF 块 (exam-created-event), 实见 {len(matches)}"
    code = matches[0]
    event_json = tmp_path / "exam-created-event.json"
    code = code.replace('"/tmp/exam-created-event.json"', json.dumps(str(event_json)))
    payload = {
        "vault_root": str(tmp_path),
        "exam_board": "检验白板/测试节点-检验.md",
        "node": "测试节点",
        "ts": "2026-08-01T10:00:00+00:00",
    }
    for _ in range(2):  # 二跑验证幂等 (脚本每次 os.remove(P), 重建输入)
        event_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, proc.stderr
    assert not event_json.exists(), "脚本应 os.remove 输入文件"
    ledger = tmp_path / "learning_events.jsonl"
    assert len(ledger.read_text(encoding="utf-8").strip().splitlines()) == 1
    assert _run(ledger).returncode == 0


def test_real_producer_quiz_answer_writer(tmp_path):
    """vault 写点 3/3: quiz-answer 评分链的账本写段逐字提取, 以真实上下文
    变量 exec, 产物过校验器 + 幂等 + abandoned 分支。"""
    text = (SKILLS / "quiz-answer" / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(
        r'(EV = os\.path\.join\(VAULT.*?写入失败\(不影响评分\): \{_e\}"\))',
        text,
        re.DOTALL,
    )
    assert m, "quiz-answer SKILL.md 找不到账本写段"
    code = m.group(1)

    def run_writer(p_extra, eid):
        ns = {
            "os": __import__("os"),
            "json": json,
            "VAULT": str(tmp_path),
            "p": {"ts": "2026-08-01T10:00:00+00:00", "exam_board": "检验白板/x-检验.md", **p_extra},
            "eid": eid,
            "NODE": str(tmp_path / "节点" / "测试节点.md"),
            "GN": 0.752,
            "n_att": 2,
        }
        exec(compile(code, "quiz-answer-SKILL-extract", "exec"), ns)

    run_writer({}, "e-scored-1")
    run_writer({}, "e-scored-1")  # 幂等重放
    run_writer({"abandoned": True}, "e-abandoned-1")
    ledger = tmp_path / "learning_events.jsonl"
    lines = [json.loads(ln) for ln in ledger.read_text(encoding="utf-8").strip().splitlines()]
    assert [r["event_type"] for r in lines] == ["answer_scored", "answer_abandoned"]
    assert _run(ledger).returncode == 0


# ── 5. 现网零误报 ──


def test_real_write_point_shapes_zero_false_positives():
    """按 8 个现网写点 (backend 5 调用点 + vault 3 skill) 1:1 建模的行全过 —
    含 Z 后缀时间戳 / 紧凑分隔符 / 中文 event_id 等真实形态变体。"""
    result = _run(FIXTURES / "real_shapes.jsonl")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(
    not REPO_VAULT_LEDGER.is_file(),
    reason="仓内 vault 根无 learning_events.jsonl (worktree 环境) — live 判据见验收单存证",
)
def test_repo_vault_ledger_schema_v1():
    """现网账本 (仓内 vault 根) 必须 v1 全合规 — 只读校验。"""
    result = _run(REPO_VAULT_LEDGER)
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# degraded proof 参考 verifier 的行为门 (round-14 新增, round-15 按 Codex
# 十四轮 HIGH/MEDIUM 收紧)
#
# Codex round-13: "现有校验器和测试也没有 proof 行为实现, 十二轮存证仅做文本
# 计数, 无法消除该歧义" ⇒ round-14 落成 verifier。
# Codex round-14: verifier 对多项 schema 必填/真实绑定违规返回空; hash 门同源
# 循环 (state_hash 被替换为恒定值后 14/14 仍过) ⇒ 本轮补真实绑定门 + 独立 oracle。
# ---------------------------------------------------------------------------

_T1 = "2026-01-01T10:00:00Z"
_T2 = "2026-01-02T10:00:00Z"
_HEX = "a" * 64

#: **独立 oracle** (round-15): 该 digest 由 shell `printf ... | shasum -a 256`
#: 算出, 不经被测的 canonical_state_bytes/state_hash —— 破除"用被测函数生成
#: 期望值"的同源循环 (Codex 十四轮 MEDIUM: 把 state_hash 换成恒返回 "0"*64 后
#: 原 14 门仍全绿)。对应 canonical 串:
#: {"fsrs_difficulty":5.0,"fsrs_due":"2026-02-01T10:00:00Z",
#:  "fsrs_last_review":"2026-01-01T10:00:00Z","fsrs_stability":10.0,"fsrs_state":2}
_KNOWN_STATE_DIGEST = "4f26831a0f4e60998f463ca6ed5091831e5ad7cba9e242789ad23acccc1e3b57"


def _state(last_review, *, fsrs_state=2, due="2026-02-01T10:00:00Z"):
    """canonical 状态对象 (Review 五键, 省略 fsrs_step)。"""
    out = {
        "fsrs_due": due,
        "fsrs_state": fsrs_state,
        "fsrs_stability": 10.0,
        "fsrs_difficulty": 5.0,
        "fsrs_last_review": last_review,
    }
    if fsrs_state in (1, 3):
        out["fsrs_step"] = 0
    return out


def _genesis(first_event_line=1):
    text = "title: n\n"
    return {
        "node_frontmatter_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "node_frontmatter_text": text,
        "first_event_line": first_event_line,
    }


def _identity(cursor_line, review_time, **over):
    """proof 的 schema 必填字段骨架 (round-15: 原 helper 缺四个必填字段)。"""
    base = {
        "vault_id": "v",
        "node_id": "n",
        "event_id": f"e{cursor_line}",
        "review_time": review_time,
        "cursor_line": cursor_line,
        "ledger_prefix_sha256": _HEX,
        "fsrs_library_version": "6.3.1",
        "fsrs_params_hash": "b" * 64,
        "scheduler_config": {"desired_retention": 0.9},
        "reducer": {"id": "per-event-round", "precision": 4},
        "result_hash": "c" * 64,
    }
    base.update(over)
    return base


def _leaf(cursor_line, review_time, *, first_event_line=1, **over):
    """origin.kind=new_card 的叶层 proof。"""
    proof = _identity(cursor_line, review_time, **over)
    proof["origin"] = {"kind": "new_card", "genesis_evidence": _genesis(first_event_line)}
    return proof


def _layered(child_cursor, child_rt, ancestor):
    """origin.kind=snapshot 的上层 proof, 三条等式自洽构造。"""
    snap_state = _state(ancestor["review_time"])
    snap_hash, problems = validator.state_hash(snap_state)
    assert not problems, problems
    ancestor = dict(ancestor, result_hash=snap_hash)
    proof = _identity(child_cursor, child_rt)
    proof["origin"] = {
        "kind": "snapshot",
        "state": snap_state,
        "snapshot_hash": snap_hash,
        "ancestor_proof": ancestor,
    }
    return proof


_APPLICABLE_2 = [(1, _T1, "e1"), (2, _T2, "e2")]


def test_normal_two_layer_chain_is_provable():
    """正常链 L1=t1、L2=t2 的两层 proof **必须通过**。

    这是 round-13 HIGH 的判据: 若把"其后无适用事件"递归施于 ancestor,
    ancestor(cursor_line=1) 会因 L2 存在而失效 ⇒ 本测试红。冻结为仅最外层后绿。
    """
    proof = _layered(2, _T2, _leaf(1, _T1))
    assert validator.verify_degraded_proof(proof, _APPLICABLE_2) == []


def test_layered_split_cannot_bypass_monotonicity():
    """round-12 绕过: L1=t2、L2=t1 拆成两个单事件区间 ⇒ 跨层单调门必须拒。"""
    applicable = [(1, _T2, "e1"), (2, _T1, "e2")]
    proof = _layered(2, _T1, _leaf(1, _T2))
    problems = validator.verify_degraded_proof(proof, applicable)
    assert any("跨层单调门失败" in p for p in problems), problems


def test_top_level_must_cover_ledger_tail():
    """最外层 proof 后仍有适用事件 ⇒ 拒 (尾部逃逸门, round-11)。"""
    problems = validator.verify_degraded_proof(_leaf(1, _T1), _APPLICABLE_2)
    assert any("未覆盖到账本末尾" in p for p in problems), problems


def test_intra_layer_monotonicity_gate():
    """同一层内行号递增而时刻不增 ⇒ 账本不自洽, 拒 (round-10)。"""
    applicable = [(1, _T2, "e1"), (2, _T1, "e2")]
    proof = _leaf(2, _T1, first_event_line=1)
    problems = validator.verify_degraded_proof(proof, applicable)
    assert any("层内单调门失败" in p for p in problems), problems


@pytest.mark.parametrize(
    "mutate, marker",
    [
        (lambda o: o["origin"].__setitem__("snapshot_hash", "d" * 64), "等式1 失败"),
        (lambda o: o["origin"]["ancestor_proof"].__setitem__("result_hash", "d" * 64), "等式2 失败"),
        (lambda o: o["origin"]["state"].__setitem__("fsrs_last_review", _T2), "等式3 失败"),
    ],
)
def test_snapshot_three_equalities_each_enforced(mutate, marker):
    """三条等式各自独立成门 — 任一被破坏都必须报出对应违规。"""
    proof = _layered(2, _T2, _leaf(1, _T1))
    mutate(proof)
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert any(marker in p for p in problems), (marker, problems)


def test_equality3_compares_instants_not_strings():
    """等式3 必须按**绝对瞬间**比较 — '+08:00' 与等瞬间的 'Z' 不得判不等。

    Codex 十四轮 MEDIUM: 原实现直接比字符串, 合法 proof 假阳性。
    """
    offset_form = "2026-01-01T18:00:00+08:00"  # 与 _T1 (Z 形) 是同一绝对瞬间
    snap_state = _state(_T1)  # canonical state 恒为 Z 形, 这是 schema 要求
    snap_hash, errs = validator.state_hash(snap_state)
    assert not errs, errs
    ancestor = _leaf(1, offset_form, result_hash=snap_hash)
    proof = _identity(2, _T2)
    proof["origin"] = {
        "kind": "snapshot",
        "state": snap_state,
        "snapshot_hash": snap_hash,
        "ancestor_proof": ancestor,
    }
    problems = validator.verify_degraded_proof(proof, [(1, offset_form, "e1"), (2, _T2, "e2")])
    assert problems == [], problems


def test_chain_cursor_line_must_strictly_decrease():
    """ancestor.cursor_line >= 本层 ⇒ 链不终止/可自引用, 拒。"""
    proof = _layered(2, _T2, _leaf(2, _T2))
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert any("链未严格递减" in p for p in problems), problems


@pytest.mark.parametrize(
    "state, marker",
    [
        ({**_state(_T1), "fsrs_step": 0}, "键集必须恰为"),  # Review 带 step
        ({k: v for k, v in _state(_T1, fsrs_state=1).items() if k != "fsrs_step"}, "键集必须恰为"),
        ({**_state(_T1), "fsrs_stability": 10}, "必须是 JSON float"),  # int 而非 float
        ({**_state(_T1), "fsrs_state": "2"}, "必须是 number 1/2/3"),  # 字符串 state
        ({**_state(_T1), "fsrs_last_review": "2026-01-01T10:00:00+00:00"}, "UTC 整秒"),
        # round-15 (Codex 十四轮 MEDIUM): 词法合规不等于取值合法
        ({**_state(_T1), "fsrs_due": "2026-99-99T99:99:99Z"}, "取值非法"),
        # Python 的 `$` 也匹配末尾换行前 ⇒ 必须用 \Z
        ({**_state(_T1), "fsrs_due": "2026-02-01T10:00:00Z\n"}, "UTC 整秒"),
    ],
)
def test_canonical_state_shape_is_unique(state, marker):
    """同一信息的不同写法必须被拒 — 否则 hash 失去唯一性 (round-10 HIGH)。"""
    blob, problems = validator.canonical_state_bytes(state)
    assert blob is None
    assert any(marker in p for p in problems), (marker, problems)


def test_canonical_state_hash_matches_independent_oracle():
    """canonical hash 必须等于**独立算出**的已知真值。

    round-15: 原稳定性测试只比较 state_hash 自身两次调用, 把该函数换成恒返回
    常量后仍全绿 (Codex 十四轮 MEDIUM 实证)。本门钉死外部 digest 字面量。
    """
    digest, problems = validator.state_hash(_state(_T1))
    assert not problems, problems
    assert digest == _KNOWN_STATE_DIGEST


def test_canonical_state_hash_is_order_independent():
    """键序不同的同一状态必须得到同一 hash (sort_keys 冻结)。"""
    a = _state(_T1)
    b = {k: a[k] for k in reversed(list(a))}
    assert validator.state_hash(b)[0] == _KNOWN_STATE_DIGEST


@pytest.mark.parametrize("missing", sorted(validator._PROOF_REQUIRED_KEYS))
def test_every_schema_required_field_is_gated(missing):
    """§6.2 表"缺任一项即不可证明" — 逐字段删除都必须报出对应缺失。

    Codex 十四轮 HIGH: 原实现连 fsrs_library_version/params_hash/
    scheduler_config/reducer 是否存在都不要求。
    """
    proof = _leaf(2, _T2, first_event_line=1)
    proof.pop(missing)
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert problems, f"删除必填字段 {missing} 后竟无违规"
    assert any(missing in p for p in problems), (missing, problems)


@pytest.mark.parametrize(
    "mutate, marker",
    [
        (lambda g: g.__setitem__("node_frontmatter_hash", "not-a-sha256"), "64 位十六进制"),
        (lambda g: g.__setitem__("node_frontmatter_text", "fsrs_state: 2\n"), "原文含 FSRS 字段"),
        (lambda g: g.__setitem__("first_event_line", 2), "不是该节点最早的适用事件行"),
    ],
)
def test_genesis_anchor_is_really_anchored(mutate, marker):
    """new_card 的全部证明力在 genesis 锚 — 原实现只查非空 (Codex 十四轮 HIGH)。"""
    proof = _leaf(2, _T2, first_event_line=1)
    mutate(proof["origin"]["genesis_evidence"])
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert any(marker in p for p in problems), (marker, problems)


def test_event_id_must_bind_to_cursor_event():
    """proof 的 event_id 必须就是 cursor_line 那行的幂等键。"""
    proof = _leaf(2, _T2, first_event_line=1, event_id="wrong")
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert any("event_id 未绑定到 E" in p for p in problems), problems


def test_degraded_sentinel_cannot_enter_proof_chain():
    """degraded:* 哨兵无法确定性复算 ⇒ 不得参与自动证明链 (§6.2)。"""
    proof = _leaf(2, _T2, first_event_line=1, fsrs_library_version="degraded:fsrs-missing")
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert any("哨兵" in p for p in problems), problems


def test_duplicate_line_numbers_fail_closed():
    """applicable 内重复行号 = 输入不自洽, 必须报错而非静默取后者。"""
    proof = _leaf(2, _T2, first_event_line=1)
    problems = validator.verify_degraded_proof(proof, [(1, _T1, "e1"), (1, _T1, "e1"), (2, _T2, "e2")])
    assert any("行号 1 重复" in p for p in problems), problems


# ── 账本直读模式: 消除 applicable 信任边界 (Codex 十四轮 HIGH) ──


def _write_ledger(tmp_path, *, trailing_lf=True):
    """两条真实 review/1 事件的账本。"""
    rows = []
    for idx, (ts, eid) in enumerate(((_T1, "e1"), (_T2, "e2")), start=1):
        rows.append(
            json.dumps(
                {
                    "event_id": eid,
                    "event_version": 1,
                    "event_type": "answer_scored",
                    "node_id": "n",
                    "recorded_at": ts,
                    "effective_at": ts,
                    "payload": {"schema_ext": "review/1", "review_time": ts},
                },
                ensure_ascii=False,
            )
        )
    text = "\n".join(rows) + ("\n" if trailing_lf else "")
    path = tmp_path / "learning_events.jsonl"
    path.write_text(text, encoding="utf-8")
    return path


def test_ledger_mode_extracts_events_itself(tmp_path):
    """传 ledger_path 时忽略调用方 applicable — 截断列表不再能让尾部门真空通过。

    Codex 十四轮 HIGH: 把 applicable 截成 [(1,t1)] 后原实现返回 []。
    """
    ledger = _write_ledger(tmp_path)
    prefix, ends_no_lf, errs = validator.ledger_prefix(ledger, 1)
    assert not errs and not ends_no_lf
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    # 调用方蓄意只给第一行 —— verifier 仍应自行发现第二行
    problems = validator.verify_degraded_proof(proof, [(1, _T1, "e1")], ledger_path=ledger)
    assert any("未覆盖到账本末尾" in p for p in problems), problems


def test_ledger_mode_recomputes_prefix_hash(tmp_path):
    """ledger_prefix_sha256 必须与账本实算一致 — 此前只校验形状。"""
    ledger = _write_ledger(tmp_path)
    prefix, _, _ = validator.ledger_prefix(ledger, 2)
    good = _leaf(2, _T2, first_event_line=1, ledger_prefix_sha256=prefix)
    assert validator.verify_degraded_proof(good, [], ledger_path=ledger) == []
    bad = _leaf(2, _T2, first_event_line=1, ledger_prefix_sha256="f" * 64)
    problems = validator.verify_degraded_proof(bad, [], ledger_path=ledger)
    assert any("与账本实算不符" in p for p in problems), problems


def test_ledger_mode_enforces_prefix_ends_without_lf(tmp_path):
    """末行无终止 LF 时必须写 prefix_ends_without_lf: true; 有 LF 时必须省略。"""
    (tmp_path / "a").mkdir()
    no_lf = _write_ledger(tmp_path / "a", trailing_lf=False)
    prefix, ends, _ = validator.ledger_prefix(no_lf, 2)
    assert ends is True
    missing_flag = _leaf(2, _T2, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(missing_flag, [], ledger_path=no_lf)
    assert any("必须写 prefix_ends_without_lf" in p for p in problems), problems

    (tmp_path / "b").mkdir()
    with_lf = _write_ledger(tmp_path / "b")
    prefix2, ends2, _ = validator.ledger_prefix(with_lf, 2)
    assert ends2 is False
    spurious = _leaf(2, _T2, first_event_line=1, ledger_prefix_sha256=prefix2)
    spurious["prefix_ends_without_lf"] = True
    problems = validator.verify_degraded_proof(spurious, [], ledger_path=with_lf)
    assert any("必须省略 prefix_ends_without_lf" in p for p in problems), problems


def test_ledger_mode_skips_out_of_order_events(tmp_path):
    """标了 out_of_order 的行不进 pending 集合 (§6.2), 抽取必须排除。"""
    ledger = tmp_path / "learning_events.jsonl"
    rows = [
        json.dumps(
            {
                "event_id": "e1",
                "event_version": 1,
                "event_type": "answer_scored",
                "node_id": "n",
                "recorded_at": _T1,
                "effective_at": _T1,
                "payload": {"schema_ext": "review/1", "review_time": _T1},
            }
        ),
        json.dumps(
            {
                "event_id": "late",
                "event_version": 1,
                "event_type": "answer_scored",
                "node_id": "n",
                "recorded_at": _T2,
                "effective_at": _T2,
                "payload": {"schema_ext": "review/1", "review_time": _T2, "out_of_order": True},
            }
        ),
    ]
    ledger.write_text("\n".join(rows) + "\n", encoding="utf-8")
    found, errs = validator.extract_applicable(ledger, "n")
    assert not errs
    assert [line for line, _, _ in found] == [1], found
