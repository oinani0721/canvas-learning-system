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
