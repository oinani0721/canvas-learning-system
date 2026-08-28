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

Codex round-3 整改 (2026-08-28):
  - review_time 必须整秒 (BLOCKER): W(fsrs_last_review) 只有整秒精度,
    小数秒事件恒满足 `> W` → 同一事件二次推进 (实测 Learning→Review);
  - marker 降级绕过封堵 (HIGH): schema_ext 值非 'review/1' 即违规;
    复习事件带扩展键却无 marker 同样违规 (历史行不含这些键, 零误报);
  - 完整语义绑定 (HIGH): 挂载点限 answer_scored/answer_abandoned;
    grade_norm 必填且 ∈[0,1]; rating 与 grade_norm 按 rating_from_grade
    口径自洽; 弃答 rating 恒为 1; library_version/params_hash 与同仓
    G3-4 golden manifest **真值**相等 (manifest 不可达 → 形状校验 + WARN);
  - offset 分钟限 00-59 (原 \\d{2} 收了 '+00:60'); 'Z' 与 '+00:00' 改按
    绝对瞬间比较; 深层嵌套 RecursionError 单行判违规 (MEDIUM)。

exit code: 0 = 全部通过; 1 = 存在违规; 2 = 用法/IO 错误。
输出按行号确定性排序, 可入 CI / 存证。
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

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


#: §三 冻结受理语法的正词法 (round-2: fromisoformat 另收 week-date / 省略分钟 /
#: '+00' / 逗号小数 / offset 秒; round-3: offset 分钟须 00-59, 原 \d{2} 收了 +00:60)
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:[0-5]\d)$")
#: 小数秒段 — review/1 事件禁用 (round-3 BLOCKER: W 只有整秒精度, 见 §6.2 A5)
_SUBSECOND_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}\.\d+")


def _parse_ts(value: object) -> tuple[bool, str]:
    """扩展格式 ISO-8601 datetime 且 timezone-aware → (True, ''); 否则 (False, 原因)。

    受理语法 (§三, 白名单正则): YYYY-MM-DD[Tt ]HH:MM[:SS[.f+]](Z|±HH:[0-5]M)。
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


def _instant(value: object) -> Optional[datetime]:
    """已过 _parse_ts 的串 → 绝对瞬间 (用于跨字段语义比较: 'Z' 与 '+00:00'
    是同一瞬间的两种写法, 不得因原字符串不等而误判 — round-3 MEDIUM)。"""
    if not isinstance(value, str):
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


#: 正常 (非降级) 形状: 版本 = PEP 440 数字点版; hash = 64 hex (sha256)
_VERSION_RE = re.compile(r"^\d+(\.\d+)*$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")

#: review/1 扩展只许挂在这两类复习事件上 (round-3 HIGH: 曾可挂 session_archived)
REVIEW_EVENT_TYPES = frozenset({"answer_scored", "answer_abandoned"})

#: §6.1 扩展必填键 — 出现其中任一即视为"意图写扩展行", 缺 marker 判违规
REVIEW_EXT_KEYS = frozenset(
    {"vault_id", "concept_id", "rating", "review_time", "fsrs_library_version", "fsrs_params_hash"}
)


def _looks_like_review_ext(payload: dict) -> bool:
    """payload 带扩展键但无合法 marker → 视为规避扩展校验的写法。

    历史行 payload 只有 grade_norm/exam_board/attempt_count, 不含这些键,
    因此对存量零误报 (round-3: 去掉 marker 曾等于免检)。
    """
    return bool(REVIEW_EXT_KEYS & set(payload.keys()))


def _golden_manifest() -> Optional[dict]:
    """定位同仓 G3-4 golden manifest (库版本/参数 hash 真值源)。

    找不到 (校验器被拷到别处独立跑) → None, 调用方降级为只验形状 + WARN。
    """
    candidate = Path(__file__).resolve().parents[1] / "tests" / "regression" / "fsrs_golden_manifest.json"
    if not candidate.is_file():
        return None
    try:
        return json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _rating_from_grade_norm(grade_norm: float) -> int:
    """grade_norm → FSRS Rating, 与 fsrs_bridge.rating_from_grade 同口径
    ([Decision-FSRS-1]: 还原 grade = 1 + 3·gn 后就近落四档, 越界钳制)。"""
    grade = 1.0 + 3.0 * grade_norm
    rating = int(math.floor(grade + 0.5))
    return max(1, min(4, rating))


def _validate_review_ext(payload: dict, record: dict, manifest: Optional[dict]) -> tuple[list[str], list[str]]:
    """§六 复习域扩展行 (payload.schema_ext == 'review/1') 的完整语义校验。

    → (violations, warnings)

    绑定面 (round-2 HIGH + round-3 HIGH):
      - 挂载点: 只许 answer_scored / answer_abandoned (曾可挂 session_archived);
      - 身份: concept_id == 顶层 node_id;
      - 时刻: review_time 与 effective_at 同一瞬间 (Z/+00:00 语义比较),
        且**必须整秒** — W (fsrs_last_review) 只有整秒精度, 小数秒会让
        同一事件恒满足 `> W` 而二次推进 (round-3 BLOCKER, §6.2 A5);
      - 评分自洽: grade_norm ∈ [0,1] 必填; answer_scored 的 rating 必须等于
        rating_from_grade(grade_norm); answer_abandoned 的 rating 恒为 1
        ([Decision-FSRS-1] 弃答一票否决 Again);
      - 库指纹: 非降级时须与 G3-4 golden manifest 的 library_version/
        params_hash **真值相等** (manifest 不可达时降级为形状校验 + WARN);
        degraded 哨兵成对且原因非空。
    """
    problems: list[str] = []
    warnings: list[str] = []

    event_type = record.get("event_type")
    if event_type not in REVIEW_EVENT_TYPES:
        problems.append(
            f"schema_ext='{REVIEW_EXT_MARKER}' 只许挂在 {sorted(REVIEW_EVENT_TYPES)} 上, 实为 {event_type!r}"
        )

    rating = payload.get("rating")
    rating_ok = not isinstance(rating, bool) and isinstance(rating, int) and rating in (1, 2, 3, 4)
    if not rating_ok:
        problems.append("扩展键 rating 必须为 int 1-4 (FSRS Rating)")

    review_time = payload.get("review_time")
    ok, why = _parse_ts(review_time)
    if not ok:
        problems.append(f"扩展键 review_time {why}")
    else:
        if _SUBSECOND_RE.match(review_time):
            problems.append(
                f"扩展键 review_time 必须为整秒 {review_time!r} — frontmatter 水位线 "
                "fsrs_last_review 只有整秒精度 (§6.2 A5), 小数秒会导致同一事件二次推进"
            )
        left, right = _instant(review_time), _instant(record.get("effective_at"))
        if left is None or right is None or left != right:
            problems.append(
                f"扩展键 review_time {review_time!r} 与顶层 effective_at "
                f"{record.get('effective_at')!r} 不是同一瞬间 (§6.1)"
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

    grade_norm = payload.get("grade_norm")
    grade_ok = (
        not isinstance(grade_norm, bool) and isinstance(grade_norm, (int, float)) and 0.0 <= float(grade_norm) <= 1.0
    )
    if not grade_ok:
        problems.append("扩展键 grade_norm 必须为 [0,1] 区间数值")
    if event_type == "answer_abandoned":
        if rating_ok and rating != 1:
            problems.append(
                f"answer_abandoned 的 rating 必须为 1 (弃答一票否决 Again, [Decision-FSRS-1]), 实为 {rating}"
            )
    elif event_type == "answer_scored" and rating_ok and grade_ok:
        expected = _rating_from_grade_norm(float(grade_norm))
        if rating != expected:
            problems.append(
                f"rating {rating} 与 grade_norm {grade_norm} 不自洽 (rating_from_grade 口径应为 {expected})"
            )

    truth_version = manifest.get("library_version") if manifest else None
    truth_hash = manifest.get("params_hash") if manifest else None
    degraded_flags = []
    for key, shape_re, shape_desc, truth in (
        ("fsrs_library_version", _VERSION_RE, "数字点版 (如 6.3.1)", truth_version),
        ("fsrs_params_hash", _HASH_RE, "64 位小写 hex (sha256)", truth_hash),
    ):
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            problems.append(f"扩展键 {key} 必须为非空字符串 (降级时用 'degraded:<原因>')")
            degraded_flags.append(None)
            continue
        if value.startswith(DEGRADED_PREFIX):
            degraded_flags.append(True)
            if not value[len(DEGRADED_PREFIX) :].strip():
                problems.append(f"扩展键 {key} 的 degraded 哨兵必须带非空原因")
            continue
        degraded_flags.append(False)
        if not shape_re.match(value):
            problems.append(f"扩展键 {key} 形状非法 (须为{shape_desc}或 degraded 哨兵): {value!r}")
        elif truth is None:
            warnings.append(f"{key} 只做形状校验 — 未找到同仓 fsrs_golden_manifest.json, 无法绑定真值")
        elif value != truth:
            problems.append(
                f"扩展键 {key} {value!r} != G3-4 golden manifest 真值 {truth!r} (§6.1 库指纹必须与冻结基线同源)"
            )
    if len(set(f for f in degraded_flags if f is not None)) > 1:
        problems.append(
            "fsrs_library_version 与 fsrs_params_hash 的 degraded 状态必须成对 "
            "(§6.1: 降级时两键同为哨兵, 正常时两键同为真实值)"
        )
    return problems, warnings


def validate_record(record: object, manifest: Optional[dict] = None) -> list[str]:
    """单条 v1 记录的违规清单 (空 = 合规); 便捷入口, 丢弃 warnings。"""
    return validate_record_full(record, manifest)[0]


def validate_record_full(record: object, manifest: Optional[dict] = None) -> tuple[list[str], list[str]]:
    """单条 v1 记录 → (violations, warnings)。

    调用方须先按 §一 前向兼容规则分流: event_version 为 int 且 != 1 的行
    不应进入本函数 (validate_file 已处理)。
    """
    problems: list[str] = []
    warnings: list[str] = []
    if not isinstance(record, dict):
        return ["顶层必须是 JSON object"], warnings

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
    elif isinstance(payload, dict):
        marker = payload.get("schema_ext")
        if marker == REVIEW_EXT_MARKER:
            ext_problems, ext_warnings = _validate_review_ext(payload, record, manifest)
            problems.extend(ext_problems)
            warnings.extend(ext_warnings)
        elif "schema_ext" in payload:
            # marker 降级绕过 (round-3 HIGH): 'review/01' / 非字符串等
            # 曾让扩展门整体静默跳过, 坏行伪装成历史行 exit 0
            problems.append(
                f"payload.schema_ext 值非法 {marker!r} — v1 仅定义 '{REVIEW_EXT_MARKER}'; "
                "禁止以未知 marker 绕过扩展校验"
            )
        elif event_type in REVIEW_EVENT_TYPES and _looks_like_review_ext(payload):
            # 带扩展键但无 marker: 同样按扩展行校验, 防"去掉 marker 即免检"
            problems.append(
                "复习事件 payload 含扩展键但缺 schema_ext 标记 — 新写入必须显式标 "
                f"'{REVIEW_EXT_MARKER}' (§6.1 机械标记), 历史行不得追加扩展键"
            )

    return problems, warnings


def validate_file(path: Path) -> tuple[list[str], list[str]]:
    """整文件校验 → (violations, warnings), 均按行号升序。

    逐行二进制读+独立 UTF-8 解码: 单行坏字节序列 = 该行违规,
    不中断其余行的校验 (Codex round-1: 原 text-mode 读会炸 traceback)。
    """
    violations: list[str] = []
    warnings: list[str] = []
    seen_ids: dict[str, int] = {}
    manifest = _golden_manifest()

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
            except RecursionError:
                # 深层嵌套 (round-3 MEDIUM: ~50 万层曾栈溢出并静默中断后续行)
                violations.append(f"LINE {lineno}: JSON 嵌套过深, 超出解析器递归上限 — 疑似构造行")
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
                line_problems, line_warnings = validate_record_full(record, manifest)
                for problem in line_problems:
                    violations.append(f"LINE {lineno}: {problem}")
                for warning in line_warnings:
                    warnings.append(f"LINE {lineno}: {warning}")

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
