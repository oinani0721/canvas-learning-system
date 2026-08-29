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
import pathlib
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
    双发 exit 1 — 前向兼容必须**完全跳过形状校验**, 只 WARN。

    ⚠️ round-21 更新: 前向兼容跳过的是**形状**, **不包括路由信封**。原 fixture
    连 node_id 都没有, 编码的是 §一 加入信封条款**之前**的契约; 现补齐信封键,
    仍验"新增字段 + 改造 payload 不触发 FAIL"这一原意。
    """
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(
        '{"event_id": "future:1", "event_version": 2, "node_id": "n", "brand_new_field": true, "payload_v2": [1, 2]}\n',
        encoding="utf-8",
    )
    result = _run(ledger)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WARN" in result.stdout
    assert "FAIL" not in result.stdout


@pytest.mark.parametrize(
    "row, missing",
    [
        ('{"event_id": "future:1", "event_version": 2, "payload_v2": {}}', "node_id"),
        ('{"event_version": 2, "node_id": "n", "payload_v2": {}}', "event_id"),
    ],
)
def test_main_validator_enforces_routing_envelope(tmp_path, row, missing):
    """主体校验器必须执行 §一 路由信封 —— 规范说"必须"就得有门。

    round-21 Codex MEDIUM: schema 已冻结三键跨版本保留, 但主体对未知版本整行
    跳过只发 WARN ⇒ 缺 node_id 的 v2 在主入口仍 PASS, 形成"proof scanner 拒绝、
    主体裁判接受"的分裂。前向兼容跳过的是形状, 不包括信封。
    """
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(row + "\n", encoding="utf-8")
    result = _run(ledger)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "路由信封" in result.stdout and missing in result.stdout


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


#: 算法身份取自**真实 golden manifest** (round-16: §6.2 要求 proof 的算法身份
#: 与 G3-4 manifest 同源, 故测试桩值也必须是真值 —— 用假值会让门失去意义)
_GOLDEN_MANIFEST = json.loads(
    (WT / "backend" / "tests" / "regression" / "fsrs_golden_manifest.json").read_text(encoding="utf-8")
)


def _identity(cursor_line, review_time, **over):
    """proof 的 schema 必填字段骨架 (round-15 补齐四项, round-16 绑真 manifest)。"""
    base = {
        "vault_id": "v",
        "node_id": "n",
        "event_id": f"e{cursor_line}",
        "review_time": review_time,
        "cursor_line": cursor_line,
        "ledger_prefix_sha256": _HEX,
        "fsrs_library_version": _GOLDEN_MANIFEST["library_version"],
        "fsrs_params_hash": _GOLDEN_MANIFEST["params_hash"],
        "scheduler_config": _GOLDEN_MANIFEST["scheduler_config"],
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
        (lambda g: g.__setitem__("node_frontmatter_text", "fsrs_state: 2\n"), "原文含 FSRS"),
        (lambda g: g.__setitem__("first_event_line", 2), "不是该节点最早的事件行"),
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
    """两条真实 review/1 事件的账本 (含同目录 vault 配置)。"""
    (tmp_path / ".canvas-config.yaml").write_text("vault_id: v\n", encoding="utf-8")
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
    # ⚠️ 真正的乱序事件其 review_time 必须**早于**已应用的最新事件 (§6.2:
    # 乱序判据是 review_time <= W)。round-17 起, 标了 out_of_order 却更晚的行
    # 会被判为"伪装成乱序的真实后继"并仍计入适用集。
    earlier = "2025-12-01T10:00:00Z"
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
                "payload": {"schema_ext": "review/1", "review_time": earlier, "out_of_order": True},
            }
        ),
    ]
    ledger.write_text("\n".join(rows) + "\n", encoding="utf-8")
    found, errs = validator.extract_applicable(ledger, "n")
    assert not errs
    assert [line for line, _, _ in found] == [1], found


# ── round-15 自查发现的两条 (均为本轮自己引入的缺陷) ──


def _nested_chain(depth):
    proof = _leaf(1, _T1, first_event_line=1)
    for idx in range(2, depth + 2):
        proof = {
            **_identity(idx, _T1),
            "origin": {
                "kind": "snapshot",
                "state": {},
                "snapshot_hash": "d" * 64,
                "ancestor_proof": proof,
            },
        }
    return proof


@pytest.mark.parametrize("depth", [validator.PROOF_MAX_DEPTH + 2, 900, 5000])
def test_deep_chain_reports_violation_not_crash(depth):
    """超深链必须**报违规**, 不得抛未捕获的 RecursionError。

    round-15 自查: 为修 round-14 的"64 层误拒"把上限提到 1024, 但 Python 默认
    递归上限是 1000 —— 深度 ~985 起的链直接崩溃, 比原问题更坏。现上限 128 且
    公开入口另捕 RecursionError 作纵深防御。
    """
    assert validator.PROOF_MAX_DEPTH < sys.getrecursionlimit(), "深度上限必须远低于 Python 递归上限"
    problems = validator.verify_degraded_proof(_nested_chain(depth), [])
    assert any("深度超过" in p or "递归耗尽栈" in p for p in problems), problems[:3]


def test_self_referencing_proof_does_not_crash():
    """自引用 proof 必须被深度门抓住而非无限递归。"""
    proof = _identity(5, _T1)
    proof["origin"] = {"kind": "snapshot", "state": {}, "snapshot_hash": "d" * 64}
    proof["origin"]["ancestor_proof"] = proof
    problems = validator.verify_degraded_proof(proof, [])
    assert any("深度超过" in p or "递归耗尽栈" in p for p in problems), problems[:3]


def test_line_numbering_agrees_with_prefix_on_bare_cr(tmp_path):
    """含裸 CR 的记录不得让抽取与 prefix 的行号错位。

    round-15 自查: extract_applicable 曾用 splitlines() —— 它还在 \\r / \\v /
    \\f / \\x1c-\\x1e / \\x85 处断行, 而主体校验 (二进制文件迭代) 与
    ledger_prefix 只认 \\n。一条含裸 CR 的坏记录会让其**后续**所有事件的行号
    多算 1, cursor_line 与 prefix 指向不同的行。
    """

    def event(eid, ts):
        return json.dumps(
            {
                "event_id": eid,
                "event_version": 1,
                "event_type": "answer_scored",
                "node_id": "n",
                "recorded_at": ts,
                "effective_at": ts,
                "payload": {"schema_ext": "review/1", "review_time": ts},
            }
        )

    ledger = tmp_path / "learning_events.jsonl"
    # 第 2 行是含裸 CR 的坏记录 (RFC 8259 禁止未转义控制字符, 主体会判违规)
    ledger.write_bytes(
        (event("e1", _T1) + "\n").encode("utf-8") + b'{"broken":"x\ry"}\n' + (event("e2", _T2) + "\n").encode("utf-8")
    )
    found, _ = validator.extract_applicable(ledger, "n")
    assert [line for line, _, _ in found] == [1, 3], f"行号错位: {found}"

    # 第 3 行的 prefix 必须覆盖到 e2 所在行的终止 LF —— 与上面的行号同域
    prefix, ends_without_lf, errs = validator.ledger_prefix(ledger, 3)
    assert not errs and ends_without_lf is False
    assert prefix == hashlib.sha256(ledger.read_bytes()).hexdigest()


# ── round-16: Codex 十五轮的三组 HIGH + MEDIUM/LOW 逐条行为门 ──


@pytest.mark.parametrize(
    "field, value, marker",
    [
        ("fsrs_library_version", "garbage", "不同源"),
        ("fsrs_library_version", "degraded:fsrs-missing", "哨兵"),
        ("fsrs_params_hash", "degraded:x", "哨兵"),
        ("fsrs_params_hash", "e" * 64, "不同源"),
        ("scheduler_config", {}, "非空"),
        ("scheduler_config", {"desired_retention": 0.9}, "不同源"),
        ("reducer", {}, "reducer.id"),
        ("reducer", {"id": "r"}, "reducer.precision"),
    ],
)
def test_algorithm_identity_binds_to_golden_manifest(field, value, marker):
    """§6.2 要求算法身份与 G3-4 manifest 同源 — 原实现只验非空 (十五轮 HIGH)。"""
    proof = _leaf(2, _T2, first_event_line=1, **{field: value})
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert any(marker in p for p in problems), (field, value, problems)


@pytest.mark.parametrize(
    "text, should_reject",
    [
        ('"fsrs_state": 2\n', True),  # 加引号的顶层键: 合法 YAML, 原正则漏检
        ("'fsrs_stability': 1.0\n", True),
        ("fsrs_state: 2\n", True),
        ("description: |\n  fsrs_state: documentation only\n", False),  # block scalar 正文: 原正则误拒
        ("", False),  # 空 frontmatter 合法, 规范未要求非空
        ("title: n\nnote: mentions fsrs_state inline\n", False),
    ],
)
def test_genesis_fsrs_detection_is_yaml_semantic(text, should_reject):
    """genesis 原文的 FSRS 判据必须按 YAML 顶层键, 不是行内文本匹配。"""
    proof = _leaf(2, _T2, first_event_line=1)
    proof["origin"]["genesis_evidence"]["node_frontmatter_text"] = text
    proof["origin"]["genesis_evidence"]["node_frontmatter_hash"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    hit = [p for p in problems if "原文含 FSRS" in p]
    assert bool(hit) is should_reject, (text, problems)


def _ledger_with(tmp_path, rows, name="learning_events.jsonl", vault_id="v"):
    """写一份账本 + 同目录 vault 配置。

    round-17 起 vault 身份无任何证据时 fail-closed, 而真实 vault 根都带
    `.canvas-config.yaml` —— 夹具必须还原这一现实形态。
    """
    if vault_id is not None:
        (tmp_path / ".canvas-config.yaml").write_text(f"vault_id: {vault_id}\n", encoding="utf-8")
    path = tmp_path / name
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _event(eid, ts, *, ext=True, vault_id=None, node_id="n"):
    payload = {"review_time": ts}
    if ext:
        payload["schema_ext"] = "review/1"
    if vault_id:
        payload["vault_id"] = vault_id
    return json.dumps(
        {
            "event_id": eid,
            "event_version": 1,
            "event_type": "answer_scored",
            "node_id": node_id,
            "recorded_at": ts,
            "effective_at": ts,
            "payload": payload,
        }
    )


def test_new_card_rejected_when_node_has_unextended_history(tmp_path):
    """§6.2: 该节点存在无 review/1 扩展的旧行时, 不得采信 new_card。

    十五轮 HIGH: 实现原取"最早**适用**行", 与规范的"最早一条事件"不同 ——
    历史无扩展行时二者分叉, 该 proof 曾返回 []。
    """
    ledger = _ledger_with(tmp_path, [_event("old", _T1, ext=False), _event("e2", _T2)])
    prefix, _, _ = validator.ledger_prefix(ledger, 2)
    proof = _leaf(2, _T2, first_event_line=2, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("账本历史不完整" in p for p in problems), problems


def test_first_event_line_counts_all_node_events(tmp_path):
    """first_event_line 的定义是"该节点最早**一条事件**", 不是最早适用事件。"""
    ledger = _ledger_with(tmp_path, [_event("old", _T1, ext=False), _event("e2", _T2)])
    scan, _ = validator.scan_ledger_bytes(ledger.read_bytes(), "n")
    assert scan["node_event_lines"] == [1, 2]
    assert [line for line, _, _ in scan["applicable"]] == [2]
    assert scan["unextended_lines"] == [1]


def test_ledger_mode_uses_single_byte_snapshot(tmp_path):
    """直读模式必须在**同一份字节快照**上完成 — 否则并发追加可让尾部门失效。

    十五轮 HIGH: extract_applicable 与 ledger_prefix 各自 read_bytes(), 两次
    读之间追加的 L2 对适用集不可见, 而 cursor=1 的 prefix 仍只覆盖 L1 ⇒ []。
    """
    import inspect

    assert "is_top_level" not in inspect.signature(validator.verify_degraded_proof).parameters
    source = pathlib.Path(validator.__file__).read_text(encoding="utf-8")
    assert source.count("read_bytes()") == 1, "账本字节必须只读一次 (单快照)"

    ledger = _ledger_with(tmp_path, [_event("e1", _T1), _event("e2", _T2)])
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("未覆盖到账本末尾" in p for p in problems), problems


def test_vault_id_must_match_ledger_events(tmp_path):
    """proof 的 vault_id 必须与账本事件一致 — 原实现只验非空。"""
    ledger = _ledger_with(tmp_path, [_event("e1", _T1, vault_id="real_vault")])
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, vault_id="different_vault", ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("vault_id 与账本事件不符" in p for p in problems), problems


def test_unparseable_ledger_line_fails_closed(tmp_path):
    """坏行不得静默跳过 — 无法判断它是否本应参与本节点的 proof。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(_event("e1", _T1) + "\n" + '{"broken\n' + _event("e3", _T2) + "\n", encoding="utf-8")
    prefix, _, _ = validator.ledger_prefix(ledger, 3)
    proof = _leaf(3, _T2, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("无法解析" in p and "fail-closed" in p for p in problems), problems


@pytest.mark.parametrize(
    "review_time, marker",
    [
        ("2026-01-02T10:00:00", "不合法"),  # naive
        ("9999-12-31T23:59:59Z", "A7"),  # 越 A7 上界
        ("2026-01-02T10:00Z", "整秒"),  # 缺秒段 (过 §三 语法但违 A5)
    ],
)
def test_proof_review_time_is_strictly_validated(review_time, marker):
    """proof 的 review_time 必须过 §三 语法 + A7 域 + A5 整秒。"""
    problems = validator.verify_degraded_proof(_leaf(2, review_time, first_event_line=1), _APPLICABLE_2)
    assert any(marker in p for p in problems), (review_time, problems)


def test_mixed_naive_aware_does_not_raise():
    """naive 与 aware 混排必须报违规, 不得抛 TypeError。"""
    problems = validator.verify_degraded_proof(
        _leaf(2, _T2, first_event_line=1), [(1, "2026-01-01T10:00:00", "e1"), (2, _T2, "e2")]
    )
    assert problems  # 具体条目不重要, 关键是没崩溃


@pytest.mark.parametrize(
    "field, value",
    [("fsrs_stability", -1.0), ("fsrs_stability", 0.0), ("fsrs_difficulty", 99.0), ("fsrs_difficulty", 0.5)],
)
def test_snapshot_state_numeric_domain_is_checked(field, value):
    """snapshot state 的数值域必须与 classify_card_state() 同判据。"""
    state = {**_state(_T1), field: value}
    snap_hash, _ = validator.state_hash(state)
    proof = _identity(2, _T2)
    proof["origin"] = {
        "kind": "snapshot",
        "state": state,
        "snapshot_hash": snap_hash,
        "ancestor_proof": dict(_leaf(1, _T1), result_hash=snap_hash),
    }
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert any("可调度域" in p for p in problems), (field, value, problems)


def test_degraded_sentinel_event_in_interval_is_rejected(tmp_path):
    """折叠区间内出现算法身份为 degraded 哨兵的事件 ⇒ 该区间须人工裁定。"""
    row = json.dumps(
        {
            "event_id": "e1",
            "event_version": 1,
            "event_type": "answer_scored",
            "node_id": "n",
            "recorded_at": _T1,
            "effective_at": _T1,
            "payload": {
                "schema_ext": "review/1",
                "review_time": _T1,
                "fsrs_library_version": "degraded:fsrs-missing",
            },
        }
    )
    ledger = _ledger_with(tmp_path, [row])
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("degraded 哨兵" in p and "人工裁定" in p for p in problems), problems


def test_legacy_two_tuple_applicable_fails_closed():
    """旧二元 applicable 必须报违规, 不得抛 ValueError (API fail-closed)。"""
    problems = validator.verify_degraded_proof(_leaf(2, _T2, first_event_line=1), [(1, _T1), (2, _T2)])
    assert any("三元组" in p for p in problems), problems


def test_first_event_line_must_equal_earliest_node_event(tmp_path):
    """verifier 必须拒绝错位的 first_event_line — 区间左端点否则不可核验。

    与 `test_first_event_line_counts_all_node_events`(只验 scan 的抽取口径)
    互补: 本条直击 `_check_genesis` 里的比对门。
    """
    ledger = _ledger_with(tmp_path, [_event("e1", _T1), _event("e2", _T2)])
    prefix, _, _ = validator.ledger_prefix(ledger, 2)
    proof = _leaf(2, _T2, first_event_line=2, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("不是该节点最早的事件行" in p for p in problems), problems


# ── round-17: Codex 十六轮的 4 HIGH + 4 MEDIUM 逐条行为门 ──
#
# 其中五条专补十六轮实证的 **survivor**：把对应实现分支破坏后, 原 130 条契约
# 测试仍全绿 —— 说明那些分支当时没有承重门。


def _cfg(**over):
    cfg = dict(_GOLDEN_MANIFEST["scheduler_config"])
    cfg.update(over)
    return cfg


@pytest.mark.parametrize(
    "config, differing",
    [
        # Python 里 0 == False、True == 1 ⇒ dict 相等比较看不出类型漂移
        (_cfg(enable_fuzzing=0), "enable_fuzzing"),
        (_cfg(learning_steps_minutes=[True, 10]), "learning_steps_minutes"),
    ],
)
def test_scheduler_config_compared_by_canonical_json(config, differing):
    """algorithm 同源必须按 canonical JSON 文本比 — Python 的类型碰撞会放行漂移。"""
    problems = validator.verify_degraded_proof(
        _leaf(2, _T2, first_event_line=1, scheduler_config=config), _APPLICABLE_2
    )
    assert any("不同源" in p and differing in p for p in problems), problems


def test_manifest_unreachable_fails_closed(monkeypatch):
    """manifest 不可达 ⇒ 无法证明同源 ⇒ proof 侧 fail-closed。

    十六轮 HIGH: 原实现降级为形状校验, 于是"合法形状版本 + 任意 64-hex +
    六个配置键全取 0"即可返回 []。
    """
    monkeypatch.setattr(validator, "_golden_manifest", lambda: None)
    problems = validator.verify_degraded_proof(_leaf(2, _T2, first_event_line=1), _APPLICABLE_2)
    assert any("无法证明算法身份" in p for p in problems), problems


def test_out_of_order_false_cannot_hide_tail_event(tmp_path):
    """`out_of_order: false` 不得把尾部事件从适用集里藏掉。

    十六轮 HIGH: scanner 原按"键是否存在"排除。§6.2 冻结其唯一合法值是布尔
    true, 未标则不写该键 —— 其他形态是非法记录, 既要报错, 又**仍计入适用集**。
    """
    rows = [_event("e1", _T1), _event("e2", _T2)]
    tampered = json.loads(rows[1])
    tampered["payload"]["out_of_order"] = False
    ledger = _ledger_with(tmp_path, [rows[0], json.dumps(tampered)])
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("out_of_order 形态非法" in p for p in problems), problems
    assert any("未覆盖到账本末尾" in p for p in problems), problems


def test_missing_pyyaml_fails_closed(monkeypatch):
    """无 PyYAML 时正则 fallback 漏掉 YAML 转义键 ⇒ genesis 门必须 fail-closed。"""
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    problems = validator.verify_degraded_proof(_leaf(2, _T2, first_event_line=1), _APPLICABLE_2)
    assert any("PyYAML 不可达" in p and "fail-closed" in p for p in problems), problems


def test_mixed_vault_ids_are_rejected(tmp_path):
    """vault 绑定必须**严格等值**, 不是集合成员关系。

    十六轮 HIGH: L1 vault=A、L2 vault=B, cursor 指向 L2 而 proof 写 A 曾通过。
    """
    ledger = _ledger_with(tmp_path, [_event("e1", _T1, vault_id="A"), _event("e2", _T2, vault_id="B")])
    prefix, _, _ = validator.ledger_prefix(ledger, 2)
    proof = _leaf(2, _T2, first_event_line=1, vault_id="A", ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("须严格等于单一值" in p for p in problems), problems


def test_non_review_events_do_not_block_new_card(tmp_path):
    """§6.2 要求的是"全部**复习事件**都带 review/1" — 非复习事件不得误拒。

    十六轮 MEDIUM: 同节点的合法 callout_ingested 曾被算作"历史不完整"。
    """
    callout = json.dumps(
        {
            "event_id": "c1",
            "event_version": 1,
            "event_type": "callout_ingested",
            "node_id": "n",
            "recorded_at": _T1,
            "effective_at": _T1,
            "payload": {"callout_type": "tip", "text": "x"},
        }
    )
    ledger = _ledger_with(tmp_path, [callout, _event("e2", _T2)])
    prefix, _, _ = validator.ledger_prefix(ledger, 2)
    proof = _leaf(2, _T2, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert not any("历史不完整" in p for p in problems), problems


def test_blank_line_matches_main_validator_verdict(tmp_path):
    """空行在 scanner 与主体校验必须同口径 (主体判违规)。"""
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text(_event("e1", _T1) + "\n\n" + _event("e3", _T2) + "\n", encoding="utf-8")
    prefix, _, _ = validator.ledger_prefix(ledger, 3)
    proof = _leaf(3, _T2, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("空行" in p for p in problems), problems


# ── 五个 survivor 的专门门 (十六轮实证: 破坏这些分支后原测试仍全绿) ──


def test_survivor_earliest_uses_all_node_events(tmp_path):
    """earliest 必须取 node_event_lines, 不是最早**适用**行。

    构造上二者必须不同: L1 是非复习事件 (不进 applicable, 也不算历史不完整),
    L2/L3 才是适用事件。把实现退回 min(applicable) 时本门变红。
    """
    callout = json.dumps(
        {
            "event_id": "c1",
            "event_version": 1,
            "event_type": "callout_ingested",
            "node_id": "n",
            "recorded_at": _T1,
            "effective_at": _T1,
            "payload": {"callout_type": "tip", "text": "x"},
        }
    )
    ledger = _ledger_with(tmp_path, [callout, _event("e2", _T2)])
    prefix, _, _ = validator.ledger_prefix(ledger, 2)
    # first_event_line=2 = 最早**适用**行; 正确判据 (最早**事件**行) 是 1 ⇒ 须拒
    proof = _leaf(2, _T2, first_event_line=2, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("不是该节点最早的事件行" in p for p in problems), problems


def test_survivor_single_read_is_behavioral(tmp_path, monkeypatch):
    """单快照必须是**行为**保证, 不是源码字符串计数。

    十六轮: 原门只查 `source.count("read_bytes()") == 1`, 改成两次
    `.open().read()` 仍绿。本门直接计账本读取次数。
    """
    ledger = _ledger_with(tmp_path, [_event("e1", _T1), _event("e2", _T2)])
    reads = []
    real_read = pathlib.Path.read_bytes

    def counting(self, *args, **kwargs):
        if self == ledger:
            reads.append(1)
        return real_read(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "read_bytes", counting)
    prefix, _, _ = validator.ledger_prefix(ledger, 2)
    reads.clear()
    validator.verify_degraded_proof(
        _leaf(2, _T2, first_event_line=1, ledger_prefix_sha256=prefix), [], ledger_path=ledger
    )
    assert len(reads) == 1, f"账本被读取 {len(reads)} 次, 单快照要求恰 1 次"


def test_survivor_recursion_reuses_single_snapshot(tmp_path, monkeypatch):
    """两层 proof 的递归必须复用同一快照, 不得各层重读账本。"""
    ledger = _ledger_with(tmp_path, [_event("e1", _T1), _event("e2", _T2)])
    reads = []
    real_read = pathlib.Path.read_bytes

    def counting(self, *args, **kwargs):
        if self == ledger:
            reads.append(1)
        return real_read(self, *args, **kwargs)

    prefix2, _, _ = validator.ledger_prefix(ledger, 2)
    prefix1, _, _ = validator.ledger_prefix(ledger, 1)
    ancestor = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix1)
    proof = _layered(2, _T2, ancestor)
    proof["ledger_prefix_sha256"] = prefix2
    monkeypatch.setattr(pathlib.Path, "read_bytes", counting)
    validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert len(reads) == 1, f"两层 proof 读取账本 {len(reads)} 次, 应复用单快照"


def test_survivor_stability_upper_bound_is_enforced():
    """stability 上界必须成门 — 删掉上界后本门变红。"""
    state = {**_state(_T1), "fsrs_stability": validator.STABILITY_MAX * 10}
    snap_hash, _ = validator.state_hash(state)
    proof = _identity(2, _T2)
    proof["origin"] = {
        "kind": "snapshot",
        "state": state,
        "snapshot_hash": snap_hash,
        "ancestor_proof": dict(_leaf(1, _T1), result_hash=snap_hash),
    }
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert any("fsrs_stability" in p and "可调度域" in p for p in problems), problems


def test_survivor_params_hash_sentinel_in_interval(tmp_path):
    """区间事件的 params_hash 哨兵同样须拦 — 原实现只看 library_version。"""
    row = json.loads(_event("e1", _T1))
    row["payload"]["fsrs_params_hash"] = "degraded:no-params"
    ledger = _ledger_with(tmp_path, [json.dumps(row)])
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("degraded 哨兵" in p and "人工裁定" in p for p in problems), problems


# ── round-18: Codex 十七轮的 3 HIGH + 5 MEDIUM + 3 LOW 逐条行为门 ──


def test_partially_corrupt_manifest_fails_closed(monkeypatch):
    """manifest **可达但残缺**时不得失败开放 (十七轮 HIGH)。

    `_golden_manifest()` 只校验 version/hash；若其 scheduler_config 缺失或键不
    全, 比较分支会被整个跳过 —— proof 携同款残缺配置即返回 []。
    """
    base = {"library_version": _GOLDEN_MANIFEST["library_version"], "params_hash": _GOLDEN_MANIFEST["params_hash"]}
    for broken in (
        {**base, "scheduler_config": {"desired_retention": 0.9}},  # 键不全
        base,  # 整个字段缺失
        {**base, "scheduler_config": "not-an-object"},
    ):
        monkeypatch.setattr(validator, "_golden_manifest", lambda b=broken: b)
        proof = _leaf(2, _T2, first_event_line=1, scheduler_config={"desired_retention": 0.9})
        problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
        assert any("残缺" in p and "fail-closed" in p for p in problems), (broken, problems)


def test_out_of_order_true_cannot_disguise_a_real_successor(tmp_path):
    """标了 out_of_order 但时刻更晚 = 伪装成乱序的真实后继 (十七轮 HIGH)。

    形态合法不等于语义为真: §6.2 的乱序判据是 `review_time <= W`。
    """
    later = json.loads(_event("e2", _T2))
    later["payload"]["out_of_order"] = True
    ledger = _ledger_with(tmp_path, [_event("e1", _T1), json.dumps(later)])
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("伪装成乱序的真实后继" in p for p in problems), problems
    assert any("未覆盖到账本末尾" in p for p in problems), problems


def test_genuine_out_of_order_event_is_not_misrejected(tmp_path):
    """真正的乱序事件 (时刻更早) 必须仍被排除, 不得误拒。"""
    earlier = json.loads(_event("late", "2025-12-01T10:00:00Z"))
    earlier["payload"]["out_of_order"] = True
    ledger = _ledger_with(tmp_path, [_event("e1", _T1), json.dumps(earlier)])
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    assert validator.verify_degraded_proof(proof, [], ledger_path=ledger) == []


@pytest.mark.parametrize("carried", ["none", "partial"])
def test_vault_identity_without_evidence_fails_closed(tmp_path, carried):
    """两个锚都缺 / 只有部分行带 vault_id ⇒ vault 身份不可证, fail-closed。"""
    rows = [_event("e1", _T1), _event("e2", _T2)]
    if carried == "partial":
        first = json.loads(rows[0])
        first["payload"]["vault_id"] = "v"
        rows[0] = json.dumps(first)
    ledger = _ledger_with(tmp_path, rows, vault_id=None)  # 不写 .canvas-config.yaml
    prefix, _, _ = validator.ledger_prefix(ledger, 2)
    proof = _leaf(2, _T2, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    marker = "纯属自报" if carried == "none" else "不可证"
    assert any(marker in p for p in problems), (carried, problems)


@pytest.mark.parametrize("bad", [[], 42, None, {"a": 1}])
def test_non_string_vault_id_reports_instead_of_crashing(tmp_path, bad):
    """非字符串 vault_id 必须报违规, 不得在集合构造处抛 TypeError。"""
    ledger = _ledger_with(tmp_path, [_event("e1", _T1, vault_id="v")], vault_id=None)
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, vault_id=bad, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("必须是字符串" in p for p in problems), (bad, problems)


def test_survivor_recursion_shares_ledger_facts(tmp_path):
    """ancestor 必须消费**共享的**账本事实, 而不是被跳过校验。

    十七轮 survivor: 原门只统计最外层读取次数, 递归丢弃 scan/raw 后仍全绿。
    判据改为**行为**——把 ancestor 的 prefix 改错, 必须报 ancestor 的实算不符。
    """
    ledger = _ledger_with(tmp_path, [_event("e1", _T1), _event("e2", _T2)])
    prefix2, _, _ = validator.ledger_prefix(ledger, 2)
    ancestor = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256="f" * 64)
    proof = _layered(2, _T2, ancestor)
    proof["ledger_prefix_sha256"] = prefix2
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("ancestor_proof:" in p and "与账本实算不符" in p for p in problems), problems


def test_missing_pyyaml_rejects_even_clean_frontmatter(monkeypatch):
    """无 PyYAML 时连干净的 frontmatter 也必须拒 —— 这是硬依赖不是降级。

    十七轮: 原 PyYAML 测试的 fixture 只是默认 `title: n`, 说明却提到转义键;
    本门把两种输入都锁死。
    """
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    for text in ("title: n\n", '"fsrs_\\u0073tate": 2\n'):
        proof = _leaf(2, _T2, first_event_line=1)
        proof["origin"]["genesis_evidence"]["node_frontmatter_text"] = text
        proof["origin"]["genesis_evidence"]["node_frontmatter_hash"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
        assert any("PyYAML 不可达" in p and "fail-closed" in p for p in problems), (text, problems)


def test_degraded_lines_are_deduplicated(tmp_path):
    """同一行的两个算法字段都是哨兵时, 行号不得重复记录 (十七轮 LOW)。"""
    row = json.loads(_event("e1", _T1))
    row["payload"]["fsrs_library_version"] = "degraded:x"
    row["payload"]["fsrs_params_hash"] = "degraded:y"
    ledger = _ledger_with(tmp_path, [json.dumps(row)])
    scan, _ = validator.scan_ledger_bytes(ledger.read_bytes(), "n")
    assert scan["degraded_lines"] == [1], scan["degraded_lines"]


# ── round-19: Codex 十八轮的 1 HIGH + 3 MEDIUM + 3 LOW ──


def test_genuine_out_of_order_cannot_hide_another_vault(tmp_path):
    """真正的乱序行不得把**另一个 vault** 的事件整个藏起来 (十八轮 HIGH)。

    根因: 确认真乱序后的 `continue` 早于 vault 收集 ⇒ L2 的 vault=B 不可见,
    proof 声称 vault=A 返回 []。§6.2 声称 scanner 抽取的是该节点 review/1
    事件的 vault 集合, 不是"适用集的 vault 集合"。
    """
    late = json.loads(_event("e1", _T2, vault_id="a"))
    early = json.loads(_event("e2", _T1, vault_id="b"))
    early["payload"]["out_of_order"] = True
    ledger = _ledger_with(tmp_path, [json.dumps(late), json.dumps(early)], vault_id=None)
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T2, first_event_line=1, vault_id="a", ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("vault_id 与账本事件不符" in p for p in problems), problems


def test_scanner_collects_vault_from_out_of_order_rows(tmp_path):
    """**纯 scanner 事实门**: 乱序行的 vault 必须进集合。

    round-21 Codex MEDIUM: 负验证变体 Q(把 vault 收集移到 continue 之后) 之所以
    变红, 是被"仅 N/M 条带 vault_id"这条**替代**门拒绝的 —— 无法归因于"次序"
    本身。本门只断言 scanner 的直接产物, 它失败**只可能**因为收集次序变了。
    """
    late = json.loads(_event("e1", _T2, vault_id="a"))
    early = json.loads(_event("e2", _T1, vault_id="b"))
    early["payload"]["out_of_order"] = True
    ledger = _ledger_with(tmp_path, [json.dumps(late), json.dumps(early)], vault_id=None)
    scan, _ = validator.scan_ledger_bytes(ledger.read_bytes(), "n")
    assert scan["vault_ids"] == {"a", "b"}, scan["vault_ids"]
    assert scan["vault_id_lines"] == {1, 2}, scan["vault_id_lines"]
    assert [line for line, _, _ in scan["applicable"]] == [1]


def test_out_of_order_at_exactly_watermark_is_not_misrejected(tmp_path):
    """`review_time == W` 的乱序事件合法 —— 比较必须是 `>` 不是 `>=`。

    十八轮 survivor: 把该比较改成 `>=` 后原测试仍全绿。
    """
    same = json.loads(_event("same", _T1, vault_id="v"))
    same["payload"]["out_of_order"] = True
    ledger = _ledger_with(tmp_path, [_event("e1", _T1, vault_id="v"), json.dumps(same)])
    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    assert validator.verify_degraded_proof(proof, [], ledger_path=ledger) == []


#: ⚠️ 字面量而非 `validator._SCHEDULER_CONFIG_KEYS` —— round-19 Codex MEDIUM:
#: 参数来自被测常量时, 从该常量删掉一个键会让参数集**同步缩小**, survivor 依旧全绿。
_REQUIRED_SCHEDULER_KEYS = (
    "parameters",
    "desired_retention",
    "learning_steps_minutes",
    "relearning_steps_minutes",
    "maximum_interval",
    "enable_fuzzing",
)


def test_scheduler_config_key_set_matches_literal():
    """被测常量必须恰等于上面的字面量集合 (常量本身也要有门守着)。"""
    assert validator._SCHEDULER_CONFIG_KEYS == frozenset(_REQUIRED_SCHEDULER_KEYS)


@pytest.mark.parametrize("missing", _REQUIRED_SCHEDULER_KEYS)
def test_manifest_missing_any_required_config_key_fails_closed(monkeypatch, missing):
    """manifest 的 scheduler_config **缺任一必要键**都必须 fail-closed。

    十八轮 survivor: 从 `_SCHEDULER_CONFIG_KEYS` 删掉 `parameters` 后, 只缺该键
    的 manifest/proof 从 fail-closed 变成 [] —— 说明当时没有逐键的承重门。
    """
    partial = {k: v for k, v in _GOLDEN_MANIFEST["scheduler_config"].items() if k != missing}
    monkeypatch.setattr(
        validator,
        "_golden_manifest",
        lambda: {
            "library_version": _GOLDEN_MANIFEST["library_version"],
            "params_hash": _GOLDEN_MANIFEST["params_hash"],
            "scheduler_config": partial,
        },
    )
    proof = _leaf(2, _T2, first_event_line=1, scheduler_config=partial)
    problems = validator.verify_degraded_proof(proof, _APPLICABLE_2)
    assert any("残缺" in p and "fail-closed" in p for p in problems), (missing, problems)


def test_scheduler_config_mismatch_has_its_own_gate():
    """`scheduler_config` 与 manifest 不同源时必须报出 —— 独立于类型碰撞门。

    十八轮 survivor: 禁用该 mismatch 分支后无独立行为门。
    """
    drifted = {**_GOLDEN_MANIFEST["scheduler_config"], "desired_retention": 0.8}
    problems = validator.verify_degraded_proof(
        _leaf(2, _T2, first_event_line=1, scheduler_config=drifted), _APPLICABLE_2
    )
    assert any("不同源" in p and "desired_retention" in p for p in problems), problems


def test_recursion_shares_ledger_vault_id(tmp_path):
    """递归必须把 `ledger_vault_id` 一并传下去 —— 否则 ancestor 出现假阳性。

    十八轮 survivor: 只丢 ledger_vault_id 时, 合法两层 proof 的 ancestor 会报
    "vault 身份无证据可绑", 而原测试仍全绿。
    """
    ledger = _ledger_with(tmp_path, [_event("e1", _T1), _event("e2", _T2)])
    prefix1, _, _ = validator.ledger_prefix(ledger, 1)
    prefix2, _, _ = validator.ledger_prefix(ledger, 2)
    ancestor = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix1)
    proof = _layered(2, _T2, ancestor)
    proof["ledger_prefix_sha256"] = prefix2
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert not any("ancestor_proof:" in p and "vault" in p for p in problems), problems


def _normalized_scope_items(lines, start_pred, end_pred):
    """从三种载体里抽出「不做的事」六条并正规化 (去缩进/注释前缀/换行/空白)。"""
    start = next(i for i, ln in enumerate(lines) if start_pred(ln))
    end = next((i for i, ln in enumerate(lines[start:], start) if end_pred(ln)), len(lines))
    items, cur = [], None

    def _finish(text):
        # round-19 Codex MEDIUM: 原实现 re.sub(r"\s+", "") 把**标识符内部**的空白
        # 也吞掉 —— "review_time / event_id" 与 "review_time/event_id" 会判相同,
        # 门就查不出实质措辞差异。三处载体只在**空格处**折行, 故正确做法是
        # 「按空格重新拼接 + 折叠连续空白」, 而不是全删空白。
        return re.sub(r"\s+", " ", text).strip()

    for ln in lines[start:end]:
        stripped = re.sub(r"^[#\s]*", "", ln.rstrip())
        if re.match(r"^[①②③④⑤⑥]", stripped):
            if cur:
                items.append(_finish(cur))
            cur = stripped
        elif cur is not None and stripped:
            cur += " " + stripped
    if cur:
        items.append(_finish(cur))
    return items


def test_scope_declaration_is_identical_in_three_places():
    """「verifier 不做的六件事」在 schema / 模块注释 / docstring 三处必须**逐字同文**。

    十八轮 Codex: "六条"CONFIRMED 但"三处同文"STILL-OPEN —— 模块第③④信息量不同、
    docstring 第⑤省略了字段清单。声称同文却不同文, 就是又一处未经验证的声明,
    故把核对本身做成机械门。
    """
    source = pathlib.Path(validator.__file__).read_text(encoding="utf-8").splitlines()
    schema = (WT / "docs" / "learning-events-schema-v1.md").read_text(encoding="utf-8").splitlines()

    module_items = _normalized_scope_items(
        source, lambda ln: ln.startswith("# **不做的事**"), lambda ln: ln.startswith("# **proof 侧的额外依赖")
    )
    doc_items = _normalized_scope_items(
        source, lambda ln: "本函数不做的六件事" in ln, lambda ln: "proof 侧的强依赖" in ln
    )
    schema_items = _normalized_scope_items(
        schema, lambda ln: "verifier 不做的六件事" in ln, lambda ln: "proof 侧的强依赖" in ln
    )

    assert len(module_items) == len(doc_items) == len(schema_items) == 6, (
        len(module_items),
        len(doc_items),
        len(schema_items),
    )
    for idx, (a, b, c) in enumerate(zip(module_items, doc_items, schema_items), 1):
        assert a == b == c, f"第 {idx} 条三处不同文:\n模块: {a}\ndocstring: {b}\nschema: {c}"


# ── round-20: Codex 十九轮 ──


def test_unknown_event_version_is_not_interpreted_as_v1(tmp_path):
    """未知 `event_version` 的行不得被 proof scanner 当 v1 解释 (十九轮 MEDIUM)。

    主体按 §一 前向兼容规则跳过并 WARN, 而 scanner 原本解析后直接取 v1 字段 ——
    一条**合法的** v2 行 (vault=b) 会让 `vault_ids={'a','b'}`, 使 vault=a 的
    合法 proof 被假阳性拒绝。proof 侧既无法解释它也不能假装它不存在 ⇒ fail-closed。
    """
    future = json.loads(_event("v2row", _T1, vault_id="b"))
    future["event_version"] = 2
    ledger = _ledger_with(tmp_path, [_event("e1", _T2, vault_id="a"), json.dumps(future)], vault_id=None)

    scan, _ = validator.scan_ledger_bytes(ledger.read_bytes(), "n")
    assert scan["unknown_version_lines"] == [2], scan
    assert scan["vault_ids"] == {"a"}, "v2 行的 vault 不得进入 v1 集合"
    assert scan["node_event_lines"] == [1], "v2 行不得计入 v1 事件行"

    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T2, first_event_line=1, vault_id="a", ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("event_version" in p and "fail-closed" in p for p in problems), problems
    # 关键: 不得是"vault 不符"那种假阳性
    assert not any("vault_id 与账本事件不符" in p for p in problems), problems


def test_vault_coverage_denominator_counts_out_of_order_rows(tmp_path):
    """vault 覆盖率的分母是**全部 review/1 行**, 不是适用集。

    十九轮 MEDIUM: `review_ext_lines` 完整回退成旧 applicable 口径时原测试仍全绿 ——
    差异点正是"标了 out_of_order 的行进分母、不进适用集"。
    """
    ooo = json.loads(_event("ooo", "2025-12-01T10:00:00Z"))  # 更早 ⇒ 真乱序; 且不带 vault_id
    ooo["payload"]["out_of_order"] = True
    ledger = _ledger_with(tmp_path, [_event("e1", _T1, vault_id="v"), json.dumps(ooo)], vault_id=None)

    scan, _ = validator.scan_ledger_bytes(ledger.read_bytes(), "n")
    assert scan["review_ext_lines"] == [1, 2], scan["review_ext_lines"]
    assert [line for line, _, _ in scan["applicable"]] == [1]

    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, vault_id="v", ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    # 分母若退回 applicable(=1), carried==total ⇒ 无违规; 正确分母是 2 ⇒ 报 1/2
    assert any("仅 1/2 条 review/1 事件带 vault_id" in p for p in problems), problems


def test_scope_normalizer_detects_internal_whitespace_change():
    """三处同文门的正规化不得吞掉标识符内部空白 (十九轮 MEDIUM)。

    原实现 `re.sub(r"\\s+", "")` 会把 "a / b" 与 "a/b" 判成相同 —— 门就查不出
    实质措辞差异。本条直接测正规化函数本身。
    """
    a = _normalized_scope_items(["# ① review_time / event_id;"], lambda ln: True, lambda ln: False)
    b = _normalized_scope_items(["# ① review_time/event_id;"], lambda ln: True, lambda ln: False)
    assert a != b, "内部空白差异必须可被区分"
    # 而**折行**造成的差异必须被正规化吸收
    wrapped = _normalized_scope_items(["# ① review_time /", "#    event_id;"], lambda ln: True, lambda ln: False)
    assert wrapped == a, (wrapped, a)


def test_v2_without_node_id_is_unroutable_not_silently_skipped(tmp_path):
    """改名/删除 `node_id` 的合法 v2 行必须判**不可路由**并 fail-closed。

    二十轮 Codex MEDIUM: 原实现先按 v1 的 node_id 过滤、再判版本 —— 一条改名了
    node_id 的 v2 行被当成"不属于本节点"整个跳过, scanner 完全看不见它, proof
    静默返回 []。§一 已冻结路由信封: 缺 node_id 一律不可路由, 因为**恰恰无法
    判定归属**。
    """
    future = json.dumps(
        {"event_id": "future:1", "event_version": 2, "brand_new_field": True, "payload_v2": {"concept_ref": "n"}}
    )
    ledger = _ledger_with(tmp_path, [_event("e1", _T1, vault_id="v"), future])
    scan, _ = validator.scan_ledger_bytes(ledger.read_bytes(), "n")
    assert scan["unroutable_lines"] == [2], scan

    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    problems = validator.verify_degraded_proof(proof, [], ledger_path=ledger)
    assert any("不可路由" in p or "无法判定其归属" in p for p in problems), problems


def test_v2_of_another_node_does_not_false_reject(tmp_path):
    """保留了路由信封、但属于**别的节点**的 v2 行不得误伤本节点的 proof。

    二十轮 Codex 指出的**误拒方向** survivor: 把版本判断前移到 node 过滤之前时,
    `event_version=2, node_id=other` 会误拒节点 n 的 proof, 而契约测试仍全绿。
    """
    other = json.loads(_event("v2other", _T2, vault_id="v"))
    other["event_version"] = 2
    other["node_id"] = "other-node"
    ledger = _ledger_with(tmp_path, [_event("e1", _T1, vault_id="v"), json.dumps(other)])
    scan, _ = validator.scan_ledger_bytes(ledger.read_bytes(), "n")
    assert scan["unknown_version_lines"] == [] and scan["unroutable_lines"] == [], scan

    prefix, _, _ = validator.ledger_prefix(ledger, 1)
    proof = _leaf(1, _T1, first_event_line=1, ledger_prefix_sha256=prefix)
    assert validator.verify_degraded_proof(proof, [], ledger_path=ledger) == []


def test_routing_envelope_is_frozen_in_schema():
    """§一 必须成文冻结路由信封 —— 否则跨版本 routing 只能靠猜。"""
    schema = (WT / "docs" / "learning-events-schema-v1.md").read_text(encoding="utf-8")
    assert "路由信封" in schema
    for key in ("event_id", "event_version", "node_id"):
        assert key in schema.split("路由信封")[1][:400], key


@pytest.mark.parametrize("bad_node", [123, None, [], {"a": 1}, True])
def test_non_string_node_id_is_unroutable(tmp_path, bad_node):
    """`node_id` 非字符串同样**不可路由** —— 不能因类型不对就当成别的节点。"""
    row = json.loads(_event("weird", _T1, vault_id="v"))
    row["node_id"] = bad_node
    ledger = _ledger_with(tmp_path, [_event("e1", _T1, vault_id="v"), json.dumps(row)])
    scan, _ = validator.scan_ledger_bytes(ledger.read_bytes(), "n")
    assert scan["unroutable_lines"] == [2], (bad_node, scan["unroutable_lines"])
