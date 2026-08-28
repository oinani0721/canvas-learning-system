#!/usr/bin/env python3
"""learning_events.jsonl schema v1 确定性校验器 (CARD-G3-1)。

契约: docs/learning-events-schema-v1.md §八。真相源 = backend/app/services/
learning_event_log.py 的 EVENT_VERSION=1 现实; 本脚本 stdlib-only、可独立对
任意 vault 账本执行, 白名单复制份由契约测试与真相源锁死同步
(tests/regression/test_learning_events_schema_contract.py)。

Codex round-1 整改 (2026-08-28):
  - 严格 JSON: 拒 NaN/Infinity 非标准常量、拒对象内重复键;
  - 前向兼容真跳过: event_version 为 int 且 != 1 的行只 WARN, 不再按 v1
    形状判错 (原实现 WARN+FAIL 双发, 违反 §一 前向兼容条款);
  - UTF-8 容错: 逐行二进制读+解码, 非法字节序列 = 该行违规, 不炸 traceback;
  - 复习域扩展 (§六): payload.schema_ext == "review/1" 的行强制扩展键类型。

Codex round-2 整改 (2026-08-28):
  - 行裁剪只剥行尾 CR/LF: str.strip() 会洗掉 RFC 8259 禁止的控制字符,
    让敌对行伪装成合法 JSON (HIGH);
  - 时间词法改 §三 白名单正则: fromisoformat 另收 week-date / 省略分钟 /
    '+00' offset / 逗号小数 / offset 秒, 与冻结语法不符 (MEDIUM);
  - review/1 跨字段绑定 (HIGH): concept_id==node_id、review_time==
    effective_at、version/hash 形状、degraded 成对且原因非空;
  - 超长整数字面量的 stdlib 限额 ValueError 单行判违规, 不炸整体 (MEDIUM)。

exit code: 0 = 全部通过; 1 = 存在违规; 2 = 用法/IO 错误。
输出按行号确定性排序, 可入 CI / 存证。
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

#: 与 learning_event_log.EVENT_VERSION 锁死同步 (契约测试断言)
EVENT_VERSION = 1

#: 与 learning_event_log.EVENT_TYPES 锁死同步 (契约测试断言)
EVENT_TYPES = frozenset(
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

#: 顶层恰好 7 键 (schema v1 冻结)
TOP_LEVEL_KEYS = frozenset(
    {
        "event_id",
        "event_version",
        "event_type",
        "node_id",
        "recorded_at",
        "effective_at",
        "payload",
    }
)

#: 复习域扩展标记 (schema 文档 §六): 含此标记的行强制扩展键
REVIEW_EXT_MARKER = "review/1"
#: 降级写点的合法哨兵前缀 (fsrs 库不可用时的诚实口径, §六)
DEGRADED_PREFIX = "degraded:"


class _NonStandardJSON(ValueError):
    """NaN/Infinity/-Infinity 或重复键 — 非 RFC 8259 严格 JSON。"""


def _reject_constant(name: str) -> None:
    raise _NonStandardJSON(f"非标准 JSON 常量 {name} (RFC 8259 禁止, 跨语言读方会炸)")


def _reject_dup_keys(pairs: list[tuple[str, object]]) -> dict:
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise _NonStandardJSON(f"对象内重复键 {key!r} (json.loads 静默取后者, 审计不容许歧义)")
        seen.add(key)
    return dict(pairs)


def _strict_loads(line: str) -> object:
    """严格 JSON 解析: 拒 NaN/Infinity 与重复键 (真实写点 json.dumps(dict)
    不可能产出两者, 合法数据零误报)。"""
    return json.loads(line, parse_constant=_reject_constant, object_pairs_hook=_reject_dup_keys)


#: §三 冻结受理语法的正词法 (Codex round-2 MEDIUM: fromisoformat 另收 week-date /
#: 省略分钟 / '+00' / 逗号小数 / offset 秒, 与冻结语法不符 — 改正则先判词法)
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$")


def _parse_ts(value: object) -> tuple[bool, str]:
    """扩展格式 ISO-8601 datetime 且 timezone-aware → (True, ''); 否则 (False, 原因)。

    受理语法 (§三, 白名单正则): YYYY-MM-DD[Tt ]HH:MM[:SS[.f+]](Z|±HH:MM)。
    先过正则再 fromisoformat 验语义 (月/日/时分秒取值合法)。
    """
    if not isinstance(value, str) or not value:
        return False, "必须为非空字符串"
    if not _TS_RE.match(value):
        return False, f"不符 §三 受理语法 YYYY-MM-DD[T ]HH:MM[:SS[.f]](Z|±HH:MM): {value!r}"
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return False, f"非法日期时间取值: {value!r}"
    if parsed.tzinfo is None:
        return False, f"缺 timezone (必须 aware): {value!r}"
    return True, ""


#: 正常 (非降级) 形状: 版本 = PEP 440 数字点版; hash = 64 hex (sha256)
_VERSION_RE = re.compile(r"^\d+(\.\d+)*$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _validate_review_ext(payload: dict, record: dict) -> list[str]:
    """§六 复习域扩展行 (payload.schema_ext == 'review/1') 的完整校验。

    含跨字段绑定 (Codex round-2 HIGH): concept_id 必须 == 顶层 node_id、
    review_time 必须 == effective_at (同一业务时刻的两处表达)、
    library_version/params_hash 形状受控且 degraded 哨兵必须成对+带非空原因。
    """
    problems: list[str] = []
    rating = payload.get("rating")
    if isinstance(rating, bool) or not isinstance(rating, int) or rating not in (1, 2, 3, 4):
        problems.append("扩展键 rating 必须为 int 1-4 (FSRS Rating)")

    review_time = payload.get("review_time")
    ok, why = _parse_ts(review_time)
    if not ok:
        problems.append(f"扩展键 review_time {why}")
    elif review_time != record.get("effective_at"):
        problems.append(
            f"扩展键 review_time {review_time!r} != 顶层 effective_at "
            f"{record.get('effective_at')!r} (§6.1 同一业务时刻必须一致)"
        )

    for key in ("vault_id", "concept_id"):
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            problems.append(f"扩展键 {key} 必须为非空字符串")
    concept_id = payload.get("concept_id")
    node_id = record.get("node_id")
    if isinstance(concept_id, str) and concept_id and concept_id != node_id:
        problems.append(
            f"扩展键 concept_id {concept_id!r} != 顶层 node_id {node_id!r} (§6.1 映射关系: node_id 承载 concept_id)"
        )

    version = payload.get("fsrs_library_version")
    hash_value = payload.get("fsrs_params_hash")
    degraded_flags = []
    for key, value, shape_re, shape_desc in (
        ("fsrs_library_version", version, _VERSION_RE, "数字点版 (如 6.3.1)"),
        ("fsrs_params_hash", hash_value, _HASH_RE, "64 位小写 hex (sha256)"),
    ):
        if not isinstance(value, str) or not value:
            problems.append(f"扩展键 {key} 必须为非空字符串 (降级时用 'degraded:<原因>')")
            degraded_flags.append(None)
            continue
        if value.startswith(DEGRADED_PREFIX):
            degraded_flags.append(True)
            if not value[len(DEGRADED_PREFIX) :].strip():
                problems.append(f"扩展键 {key} 的 degraded 哨兵必须带非空原因")
        else:
            degraded_flags.append(False)
            if not shape_re.match(value):
                problems.append(f"扩展键 {key} 形状非法 (须为{shape_desc}或 degraded 哨兵): {value!r}")
    if len(set(f for f in degraded_flags if f is not None)) > 1:
        problems.append(
            "fsrs_library_version 与 fsrs_params_hash 的 degraded 状态必须成对 "
            "(§6.1: 降级时两键同为哨兵, 正常时两键同为真实值)"
        )
    return problems


def validate_record(record: object) -> list[str]:
    """单条 v1 记录的违规清单 (空 = 合规)。

    调用方须先按 §一 前向兼容规则分流: event_version 为 int 且 != 1 的行
    不应进入本函数 (validate_file 已处理)。
    """
    problems: list[str] = []
    if not isinstance(record, dict):
        return ["顶层必须是 JSON object"]

    keys = set(record.keys())
    missing = sorted(TOP_LEVEL_KEYS - keys)
    extra = sorted(keys - TOP_LEVEL_KEYS)
    if missing:
        problems.append(f"缺字段: {', '.join(missing)}")
    if extra:
        problems.append(f"未知顶层字段 (v1 冻结恰好 7 键): {', '.join(extra)}")

    event_id = record.get("event_id")
    if "event_id" in keys and (not isinstance(event_id, str) or not event_id):
        problems.append("event_id 必须为非空字符串 (幂等键)")

    version = record.get("event_version")
    if "event_version" in keys and (isinstance(version, bool) or not isinstance(version, int)):
        problems.append("event_version 必须为整数")

    event_type = record.get("event_type")
    if "event_type" in keys:
        if not isinstance(event_type, str):
            problems.append("event_type 必须为字符串")
        elif event_type not in EVENT_TYPES:
            problems.append(f"event_type {event_type!r} 不在 9 类白名单")

    if "node_id" in keys and not isinstance(record.get("node_id"), str):
        problems.append("node_id 必须为字符串 (可为空串)")

    for field in ("recorded_at", "effective_at"):
        if field in keys:
            ok, why = _parse_ts(record.get(field))
            if not ok:
                problems.append(f"{field} {why}")

    payload = record.get("payload")
    if "payload" in keys and not isinstance(payload, dict):
        problems.append("payload 必须为 JSON object")
    elif isinstance(payload, dict) and payload.get("schema_ext") == REVIEW_EXT_MARKER:
        problems.extend(_validate_review_ext(payload, record))

    return problems


def validate_file(path: Path) -> tuple[list[str], list[str]]:
    """整文件校验 → (violations, warnings), 均按行号升序。

    逐行二进制读+独立 UTF-8 解码: 单行坏字节序列 = 该行违规,
    不中断其余行的校验 (Codex round-1: 原 text-mode 读会炸 traceback)。
    """
    violations: list[str] = []
    warnings: list[str] = []
    seen_ids: dict[str, int] = {}

    with open(path, "rb") as f:
        for lineno, raw in enumerate(f, 1):
            try:
                decoded = raw.decode("utf-8")
            except UnicodeDecodeError as e:
                violations.append(f"LINE {lineno}: 非法 UTF-8 字节序列 (offset {e.start}) — 疑似损坏行")
                continue
            # 只剥行尾 CR/LF: str.strip() 会连 RFC 8259 禁止的控制字符
            # (U+001C-1F 等) 一并洗掉, 让敌对行伪装成合法 JSON (Codex round-2 HIGH)
            line = decoded.rstrip("\r\n")
            if not line.strip():
                violations.append(f"LINE {lineno}: 空行 (append-only JSONL 不应出现)")
                continue
            try:
                record = _strict_loads(line)
            except json.JSONDecodeError as e:
                violations.append(f"LINE {lineno}: JSON 解析失败 ({e.msg}) — 疑似截断/损坏行")
                continue
            except _NonStandardJSON as e:
                violations.append(f"LINE {lineno}: {e}")
                continue
            except ValueError as e:
                # 超长整数字面量 (int_max_str_digits) 等 stdlib 限额 —
                # 该行判违规, 不炸整个校验 (Codex round-2 MEDIUM)
                violations.append(f"LINE {lineno}: JSON 值超出解析限额 ({e})")
                continue

            # 前向兼容分流 (§一): 未知 int 版本 → 只 WARN, 完全跳过 v1 形状校验
            # (仍登记 event_id 唯一性 — 幂等键跨版本恒定, append_event 不看版本查重)
            if isinstance(record, dict):
                version = record.get("event_version")
                unknown_version = (
                    isinstance(version, int) and not isinstance(version, bool) and version != EVENT_VERSION
                )
            else:
                unknown_version = False

            if unknown_version:
                warnings.append(
                    f"LINE {lineno}: event_version={version} != {EVENT_VERSION} — "
                    "前向兼容跳过形状校验 (读方须容忍未知版本)"
                )
            else:
                for problem in validate_record(record):
                    violations.append(f"LINE {lineno}: {problem}")

            if isinstance(record, dict):
                event_id = record.get("event_id")
                if isinstance(event_id, str) and event_id:
                    if event_id in seen_ids:
                        violations.append(
                            f"LINE {lineno}: event_id {event_id!r} 重复 "
                            f"(首见 LINE {seen_ids[event_id]}) — 幂等键必须全文件唯一"
                        )
                    else:
                        seen_ids[event_id] = lineno

    return violations, warnings


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print(
            "用法: validate_learning_events.py <learning_events.jsonl 路径>",
            file=sys.stderr,
        )
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"错误: 文件不存在: {path}", file=sys.stderr)
        return 2

    try:
        violations, warnings = validate_file(path)
    except OSError as e:
        print(f"错误: 读取失败: {e}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"WARN  {warning}")
    for violation in violations:
        print(f"FAIL  {violation}")
    if violations:
        print(f"RESULT: FAIL — {len(violations)} 项违规 (schema v1, {path})")
        return 1
    print(f"RESULT: PASS — schema v1 合规 ({path})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
