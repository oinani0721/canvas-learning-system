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


def test_vault_id_bound_to_vault_config(tmp_path):
    """Codex round-3 未覆盖面（本轮主动补强）: payload.vault_id 与账本所在
    vault 的 .canvas-config.yaml 声明必须一致 — 防事件写错 vault / 账本被
    搬运后仍自称原 vault; 无配置文件时降级 WARN 保持独立可跑。"""
    ledger = tmp_path / "learning_events.jsonl"

    # 无 .canvas-config.yaml → 只 WARN 不判错
    ledger.write_text(json.dumps(_review_ext_record(), ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 0, result.stdout
    assert "vault_id 未绑定" in result.stdout

    # 有配置且一致 → PASS 且无该 WARN
    (tmp_path / ".canvas-config.yaml").write_text(
        '# 注释行\nvault_id: "canvas-vault"\nsubject: cs-61b\n', encoding="utf-8"
    )
    assert _run(ledger).returncode == 0

    # 有配置但不一致 → 违规
    mismatched = _review_ext_record(vault_id="别的vault")
    ledger.write_text(json.dumps(mismatched, ensure_ascii=False) + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1
    assert "账本所在 vault" in result.stdout


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


def test_schedulable_time_upper_bound():
    """A7 (Codex round-6 MEDIUM): 调度会叠加最长 36500 天 + A3 等时 +1s,
    9999 年这类值会让二者都 OverflowError — 契约上界机械强制。"""
    assert validator._parse_ts("9999-12-31T23:59:59Z")[0] is False
    assert validator._parse_ts("9000-01-01T00:00:01Z")[0] is False
    assert validator._parse_ts("8999-12-31T23:59:59Z")[0] is True
    assert validator._parse_ts("2026-08-01T10:00:00Z")[0] is True


def test_vault_config_parser_form_matrix(tmp_path):
    """`.canvas-config.yaml` 的 vault_id 最小行解析形态矩阵 (stdlib, 不引
    PyYAML)。锁死 11 种形态的判定, 防正则改动时静默放宽/收窄。

    关键: 缩进/嵌套/注释行不得匹配 (它们不是顶层 vault_id), 重复键取首个
    (与 YAML 'duplicate key' 的常见实现相反, 故显式锁定为已知口径)。
    """
    cases = [
        ('vault_id: "canvas_vault"\n', "canvas_vault"),
        ("vault_id: 'x1'\n", "x1"),
        ("vault_id: bare_value\n", "bare_value"),
        ('vault_id: "x"  # 尾注释\n', "x"),
        ("vault_id: bare  # 尾注释\n", "bare"),
        # round-5 HIGH#4 反例组
        ('vault_id: "team#1"\n', "team#1"),  # 引号内 # 曾被截成 'team'
        ("vault_id: 'sq#2'\n", "sq#2"),
        ("vault_id:\nsubject: cs61b\n", None),  # 跨行曾读成 'subject: cs61b'
        ("vault_id: |\n  block\n", None),  # block scalar 曾读成 '|'
        ("vault_id: >-\n  folded\n", None),
        ('vault_id: "unclosed\n', None),  # 未闭引号
        ('vault_id: "first"\nvault_id: "second"\n', "second"),  # 重复取末项(PyYAML 语义)
        # round-6 HIGH#3 反例组: 正则白名单仍会对合法 YAML 静默错绑
        ("vault_id: team#1\n", "team#1"),  # 裸词 # 前无空白 ⇒ 非注释(PyYAML 语义)
        ('vault_id: "a\\u0023b"\n', None),  # 双引号含转义 ⇒ 无法可靠解码, 放弃绑定
        ('vault_id: "early"\nvault_id: |\n  block\n', None),  # 末项 block scalar 覆盖早项
        ('other: "x\nvault_id: fake\nmore"\n', None),  # 多行引号体内的列首 vault_id
        # 现网形态(多键共存)必须正确绑定
        ('vault_id: "canvas_vault"\nsubject: cs-61b\nvault_display_name: "CS 61B"\n', "canvas_vault"),
        ('  vault_id: "indented"\n', None),
        ('other:\n  vault_id: "nested"\n', None),
        ('VAULT_ID: "upper"\n', None),
        ('vault_id: "中文库"\n', "中文库"),
        ("vault_id:\n", None),
        ('# vault_id: "commented"\n', None),
    ]
    for index, (content, expected) in enumerate(cases):
        config_dir = tmp_path / f"case{index}"
        config_dir.mkdir()
        (config_dir / ".canvas-config.yaml").write_text(content, encoding="utf-8")
        got = validator._vault_id_of(config_dir / "learning_events.jsonl")
        assert got == expected, f"{content!r} → {got!r}, 期望 {expected!r}"

    # 非法 UTF-8 配置 → None (不炸)
    bad_utf8 = tmp_path / "badutf8"
    bad_utf8.mkdir()
    (bad_utf8 / ".canvas-config.yaml").write_bytes(b'vault_id: "\xff\xfe"\n')
    assert validator._vault_id_of(bad_utf8 / "learning_events.jsonl") is None

    # 无配置文件 → None (独立可跑前提)
    assert validator._vault_id_of(tmp_path / "nowhere" / "learning_events.jsonl") is None


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
