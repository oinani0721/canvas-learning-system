#!/usr/bin/env python3
"""learning_events.jsonl schema v1 确定性校验器 (CARD-G3-1)。

契约: docs/learning-events-schema-v1.md §八。真相源 = backend/app/services/
learning_event_log.py 的 EVENT_VERSION=1 现实; 白名单复制份由契约测试与真相源
锁死同步 (tests/regression/test_learning_events_schema_contract.py)。

依赖口径 (round-10/11 修正, 此前误称 stdlib-only):
  - **账本校验主体 = stdlib-only**, 可独立对任意 vault 的 jsonl 执行;
  - **vault_id 绑定层需 PyYAML + 可 import 的 backend app.config** —— 它必须
    与生产 Settings.vault_id 逐环节同源 (safe_load → isinstance(str) →
    sanitize_vault_id → != "default"), 复制副本必然漂移 (r5~r11 实证);
  - 两者任一不可达 ⇒ **不绑定 + WARN**, 主体校验不受影响。

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
    绝对瞬间比较; 深层嵌套 RecursionError 单行判违规 (MEDIUM);
  - vault_id 绑定账本同目录 .canvas-config.yaml 声明值 (round-3 点名的
    未覆盖面, 本轮主动补强; 配置不可达 → WARN 降级保持独立可跑)。

Codex round-5 整改 (2026-08-28):
  - vault_id 解析改**保守白名单** (HIGH): 原宽松正则把 `"team#1"` 截成
    `team`(错绑)、`vault_id:\nsubject: x` 跨行读成 `subject: x`、block
    scalar 读成 `|`; 现只认双引号/单引号/裸词三种明确顶层单行形态,
    重复键取**末项**(PyYAML 语义), 非法 UTF-8 与未闭引号一律 None;
  - manifest 真值需过形状校验 (MEDIUM): 只查"是字符串"会让空串/畸形值
    的真值绑定形同虚设; 现要求 version 为数字点版、hash 为 64 hex;
  - 时间戳补 UTC 归一化越界检查 (MEDIUM): 极端日期在 bridge 的
    astimezone(UTC) 处会 OverflowError, 提前拦。

exit code: 0 = 全部通过; 1 = 存在违规; 2 = 用法/IO 错误。
输出按行号确定性排序, 可入 CI / 存证。
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
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
#: review/1 的 review_time 完整形态: 必须含秒段且无小数秒 (round-4 HIGH#1 —
#: 省略秒的 '10:00+00:00' 不是任何写点会产出的形态, 与 W 的整秒口径对不齐)
_WHOLE_SECOND_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:[0-5]\d)$")


def _parse_ts(value: object, upper_bound: Optional[datetime] = None) -> tuple[bool, str]:
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
    try:
        # round-5 MEDIUM: UTC 归一化会越界的极端日期 (如 0001-01-01+08:00)
        # 在 bridge 的 astimezone(UTC) 处会抛 OverflowError — 提前拦
        normalized = parsed.astimezone(timezone.utc)
    except (OverflowError, OSError, ValueError):
        return False, f"UTC 归一化越界 (下游 astimezone 会溢出): {value!r}"
    # round-11 MEDIUM: 原用 `is` 判身份, 传值相等但新建的 datetime 会错误接受端点
    bound_exclusive = upper_bound is not None and upper_bound == REVIEW_INPUT_MAX
    if (normalized >= REVIEW_INPUT_MAX) if bound_exclusive else (normalized > (upper_bound or TIMESTAMP_MAX)):
        # A7 (round-6 MEDIUM, round-7 分档): review 输入用更保守的
        # REVIEW_INPUT_MAX (调度还要叠加 interval + A3 的 +1s);
        # 一般时间戳只拦 UTC 归一化本身会溢出的极端值
        bound = upper_bound or TIMESTAMP_MAX
        relation = "须严格小于" if bound_exclusive else "不得超过"
        return False, f"A7 时间域: {relation} {bound.date()} : {value!r}"
    return True, ""


#: A7 上界分两档 (round-7 MEDIUM: 原实现把一个上界通用到所有时间字段,
#: 导致合法 review_time=9000 产出的 due=9000-01-09 反被判 degraded)
#: ① review 域上界 — 调度会在其上叠加 interval, A3 还要 +1s。
#: ⚠️ round-9 闭包修正: `review_time` 与 `fsrs_last_review`(W) **同域同界且
#: 均须严格小于**该值 —— 否则合法的 review_time=9000 写出 W=9000 后,
#: 分类器立刻判 degraded (合法事件确定性制造残缺卡)。
REVIEW_INPUT_MAX = datetime(9000, 1, 1, tzinfo=timezone.utc)
#: ② 一般时间戳上界 (recorded_at/effective_at/fsrs_due 等) — 只拦 UTC
#: 归一化本身会溢出的极端值, 不施加 review 输入的保守上界
TIMESTAMP_MAX = datetime(9500, 1, 1, tzinfo=timezone.utc)
#: 可调度数值域 (§6.2 三态)。
#: ⚠️ round-7: stability **无 36500 上界** — FSRS 封顶的是 interval 不是
#: stability (实测连续 7 次 Easy 后 S=68949 > 36500, 原规则会误报合法卡)。
#: ⚠️ round-8: 但"任意有限正数"又过宽 — S=1.797e308 判 normal 而真实
#: bridge 抛 OverflowError(float infinity to integer)。
#: 取 1e9 天(约 274 万年)作**语义合理性上界**, 方向 fail-closed:
#:   - 技术可执行边界更高(实测 1e100 仍可执行, 1.797e308 才溢出);
#:   - 但真实语义远低于此(Easy 链实测 7 万量级, maximum_interval 封顶
#:     36500 天), 超过 1e9 天必是数据损坏;
#:   - 因此 1e9~1e100 区间**虽技术可执行仍判 degraded** — 有意的保守偏差
#:     (停下来要人工确认), 不是误判。
STABILITY_MAX = 1e9
DIFFICULTY_RANGE = (1.0, 10.0)
#: 纯整数词法 (round-7: float() 判整数会让 "1.0" 通过, 而 bridge 的
#: int("1.0") 实测抛 ValueError)
_INT_LEXEME_RE = re.compile(r"^[+-]?\d+$")


def _finite_number(value: object) -> Optional[float]:
    """有限实数 (排除 bool / NaN / ±Inf / 不可解析) → float; 否则 None。"""
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            # round-9 MEDIUM: float(10**309) 抛 OverflowError — 须 fail-closed
            number = float(value)
        elif isinstance(value, str) and value.strip():
            number = float(value)
        else:
            return None
    except (ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _int_lexeme(value: object) -> Optional[int]:
    """纯整数 (int 本身, 或 ^[+-]?\\d+$ 的字符串) → int; 否则 None。

    round-7: 用 float() 判整数会让 `fsrs_state: 1.0` 通过, 而真实 bridge
    的 `int(fields.get("fsrs_state", 1))` 对 "1.0" 抛 ValueError。
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and _INT_LEXEME_RE.match(value.strip()):
        try:
            return int(value.strip())
        except ValueError:
            # round-8 MEDIUM: 5000 位纯整数触发 stdlib int_max_str_digits 限额
            return None
    return None


def classify_card_state(fields: dict) -> tuple[str, str]:
    """节点 frontmatter 的 fsrs_* 字段 → ("new"|"normal"|"degraded", reason)。

    §6.2 水位线三态的**可执行实现** (round-6 HIGH#1): G3-2/G3-3 直接复用本
    函数, 避免"文档一套实现一套"。按 state 校验 canonical 形状与可调度域 —
    round-6 四反例 (state=3 缺 step / state=2 带 step / state=1 且 S=D=0 /
    S=D=1e308) 在真实 review() 上分别抛 AssertionError、写回非 canonical
    tuple、ZeroDivisionError、产生 NaN 路径。
    """
    present = {k: v for k, v in fields.items() if k.startswith("fsrs_")}
    if not present:
        return "new", "无任何 fsrs_* 字段 = 真新卡 (W = -inf, 全部事件 pending)"

    # W(fsrs_last_review) 是"上一次 review 的时刻", 与 review_time 同域:
    # 必须**严格小于** review 输入上界, 否则无任何合法后继事件可写
    # (round-8 HIGH#2: W=9400 曾判 normal, 但后继须 > W 且 <= 9000 ⇒ 空集;
    #  W 恰为上界时 A3 的 W+1s 也立即越界)。fsrs_due 是调度产物, 用更宽的一般上界。
    for key, bound in (("fsrs_last_review", REVIEW_INPUT_MAX), ("fsrs_due", TIMESTAMP_MAX)):
        value = present.get(key)
        if not isinstance(value, str) or not value.strip():
            return "degraded", f"缺 {key} 或非字符串 — 无法证明 state 与水位线同源"
        ok, why = _parse_ts(value.strip(), upper_bound=bound)
        if not ok:
            return "degraded", f"{key} 不可解析: {why}"
        if key == "fsrs_last_review":
            # round-9 MEDIUM: W 与 review_time 同为 canonical 秒精度
            if _SUBSECOND_RE.match(value.strip()):
                return "degraded", (f"fsrs_last_review {value!r} 含小数秒 — 与 §6.2 A5 的整秒口径不一致")

    raw_state = present.get("fsrs_state")
    state = _int_lexeme(raw_state)
    if state is None or state not in (1, 2, 3):
        return "degraded", (
            f"fsrs_state 须为整数 1/2/3 (纯整数词法), 实为 {raw_state!r} "
            "— '1.0' 这类写法 bridge 的 int() 会抛 ValueError; 0 属 legacy 迁移分支"
        )

    step = present.get("fsrs_step")
    stability = _finite_number(present.get("fsrs_stability"))
    difficulty = _finite_number(present.get("fsrs_difficulty"))
    step_number = _int_lexeme(step)
    has_step = step is not None and str(step).strip() != ""
    step_ok = step_number is not None and step_number >= 0

    def _domain_ok() -> Optional[str]:
        if stability is None or difficulty is None:
            return "stability/difficulty 缺失或非有限数"
        if stability <= 0:
            return f"stability {stability} 须为正数 (0 会让调度器 ZeroDivisionError)"
        if stability > STABILITY_MAX:
            return (
                f"stability {stability} 超出语义合理性上界 {STABILITY_MAX:g} 天 "
                "(fail-closed: 该量级必是数据损坏, 停下来要人工确认; "
                "技术可执行边界更高但不作判据)"
            )
        if not DIFFICULTY_RANGE[0] <= difficulty <= DIFFICULTY_RANGE[1]:
            return f"difficulty {difficulty} 越出 FSRS 定义域 {DIFFICULTY_RANGE}"
        return None

    if state == 1:  # Learning: step 必需; S/D 要么同缺要么同在域内
        if not has_step or not step_ok:
            return "degraded", "state=1(Learning) 须带非负整数 fsrs_step"
        both_absent = present.get("fsrs_stability") in (None, "") and present.get("fsrs_difficulty") in (None, "")
        if both_absent:
            return "normal", "Learning 首步 (stability/difficulty 未初始化)"
        problem = _domain_ok()
        if problem:
            return "degraded", f"state=1 的 {problem} (S=D=0 会让调度器 ZeroDivisionError)"
        return "normal", "Learning 且 S/D 在可调度域内"

    if state == 2:  # Review: 禁 step (非 canonical); S/D 必需且在域内
        if has_step:
            return "degraded", f"state=2(Review) 不得带 fsrs_step, 实为 {step!r} (非 canonical tuple)"
        problem = _domain_ok()
        if problem:
            return "degraded", f"state=2 的 {problem}"
        return "normal", "Review 且 S/D 在可调度域内"

    # state == 3 Relearning: step 与 S/D 都必需
    if not has_step or not step_ok:
        return "degraded", "state=3(Relearning) 须带非负整数 fsrs_step (缺失时真实 review() 抛 AssertionError)"
    problem = _domain_ok()
    if problem:
        return "degraded", f"state=3 的 {problem}"
    return "normal", "Relearning 且 step 与 S/D 齐备"


# --------------------------------------------------------------------------
# degraded proof 的**结构参考 verifier** (round-14 HIGH: 此前 proof 只有散文,
# Codex round-13 指出"没有 proof 行为实现, 存证仅做文本计数, 无法消除歧义")
#
# ⚠️ **诚实的范围声明** (round-15 逐项收紧): 本 verifier 判 §6.2 proof schema 的
# **结构、分层与真实绑定**门 —— 必填字段齐备与形状、状态形状/类型/hash、区间
# (左开右闭按行号)、层内单调、跨层单调、链终止与防循环、snapshot 三等式、
# genesis 真锚、尾部作用域。
#
# **不做的事** (round-14 Codex HIGH: 此前只说"不复算 FSRS", 未点名以下三项):
#   ① **不复算 FSRS 折叠** —— canonical reducer 的精度常量属 G3-2, 需真实 fsrs;
#   ② **不复算 `result_hash`** —— 它是折叠产物的 hash, 同样依赖 reducer;
#   ③ 不传 `ledger_path` 时**不复算 `ledger_prefix_sha256`、不自行抽取事件** ——
#      此时 `applicable` 是**信任边界**, 其完整性由调用方保证 (抽取不全会让尾部
#      门真空通过)。**传 `ledger_path` 即消除该边界**: verifier 自行抽取事件、
#      复算 prefix、判定 `prefix_ends_without_lf`, 并忽略调用方传入的 applicable。
#
# 因此 verifier 返回空违规**不等于** proof 成立, 只等于"在上述已判门内无歧义,
# 可交付 reducer 复算"。
# --------------------------------------------------------------------------

_STATE_KEYS_BY_FSRS_STATE = {
    1: ("fsrs_due", "fsrs_state", "fsrs_step", "fsrs_stability", "fsrs_difficulty", "fsrs_last_review"),
    2: ("fsrs_due", "fsrs_state", "fsrs_stability", "fsrs_difficulty", "fsrs_last_review"),
    3: ("fsrs_due", "fsrs_state", "fsrs_step", "fsrs_stability", "fsrs_difficulty", "fsrs_last_review"),
}
#: ⚠️ 必须用 \A..\Z 而非 ^..$ —— Python 的 `$` 也匹配末尾换行前的位置,
#: 故 "2026-01-01T10:00:00Z\n" 会被 ^..$ 放行 (round-14 Codex MEDIUM 实证)
_CANONICAL_TS_RE = re.compile(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
#: 64 位小写十六进制 (sha256 摘要的唯一合法形状)
_SHA256_HEX_RE = re.compile(r"\A[0-9a-f]{64}\Z")
#: proof 顶层必填字段 —— schema §6.2 表"缺任一项即不可证明"
_PROOF_REQUIRED_KEYS = (
    "vault_id",
    "node_id",
    "event_id",
    "review_time",
    "cursor_line",
    "ledger_prefix_sha256",
    "fsrs_library_version",
    "fsrs_params_hash",
    "scheduler_config",
    "reducer",
    "origin",
    "result_hash",
)
#: ancestor_proof 链的深度保险 (schema §6.2 已成文): cursor_line 严格递减本已
#: 界定有限步, 本上限只防御畸形/自引用输入, 取值须与 schema 一致。
#: ⚠️ round-15 自查: 取值**必须远低于 sys.getrecursionlimit()** (默认 1000)。
#: 此前取 1024 > 1000, 深度 ~985 起的链在递归中抛**未捕获的 RecursionError**
#: (工具崩溃而非报违规) —— 为修 round-14 的"64 层误拒"反而引入了更坏的失败模式。
#: 128 层对单节点的解冻链 (层数 = 历史重建次数) 已极为宽裕。
PROOF_MAX_DEPTH = 128
#: scheduler_config 的必要字段 (manifest 不可达时的降级形状校验口径)
_SCHEDULER_CONFIG_KEYS = frozenset(
    {
        "parameters",
        "desired_retention",
        "learning_steps_minutes",
        "relearning_steps_minutes",
        "maximum_interval",
        "enable_fuzzing",
    }
)


def canonical_state_bytes(state: object) -> tuple[Optional[bytes], list[str]]:
    """proof 里的"状态对象" → canonical JSON 字节 (§6.2 状态对象的唯一形状)。

    键集按 fsrs_state 分档 (Review 五键省略 fsrs_step); 值类型归一化 (时刻为
    UTC 整秒 Z 串、state/step 为整数 number、S/D 为 float)。返回 (字节, 违规)。
    """
    problems: list[str] = []
    if not isinstance(state, dict):
        return None, ["state 必须是 JSON object"]

    raw_state = state.get("fsrs_state")
    if not isinstance(raw_state, int) or isinstance(raw_state, bool) or raw_state not in _STATE_KEYS_BY_FSRS_STATE:
        return None, [f"fsrs_state 必须是 number 1/2/3, 得到 {raw_state!r}"]

    expected = set(_STATE_KEYS_BY_FSRS_STATE[raw_state])
    actual = set(state)
    if actual != expected:
        problems.append(
            f"fsrs_state={raw_state} 的键集必须恰为 {sorted(expected)}, "
            f"多出 {sorted(actual - expected)} / 缺失 {sorted(expected - actual)}"
        )

    for key, bound in (("fsrs_last_review", REVIEW_INPUT_MAX), ("fsrs_due", TIMESTAMP_MAX)):
        value = state.get(key)
        if not isinstance(value, str) or not _CANONICAL_TS_RE.match(value):
            problems.append(f"{key} 必须是 UTC 整秒 'Z' 串 (%Y-%m-%dT%H:%M:%SZ), 得到 {value!r}")
            continue
        # round-14 Codex MEDIUM: 只过正则会放行 '2026-99-99T99:99:99Z' —— 词法
        # 合规不等于取值合法, 必须真解析 (并复用 A7 的域上界)
        ok, why = _parse_ts(value, upper_bound=bound)
        if not ok:
            problems.append(f"{key} 取值非法: {why}")

    if "fsrs_step" in expected:
        step = state.get("fsrs_step")
        if not isinstance(step, int) or isinstance(step, bool) or step < 0:
            problems.append(f"fsrs_step 必须是非负整数 number, 得到 {step!r}")

    for key in ("fsrs_stability", "fsrs_difficulty"):
        value = state.get(key)
        # canonical 要求 float: 整数值也须为 10.0 而非 10 (bool 是 int 子类, 排除)
        if isinstance(value, bool) or not isinstance(value, float):
            problems.append(f"{key} 必须是 JSON float (整数值也写 10.0), 得到 {value!r}")
        elif not math.isfinite(value):
            problems.append(f"{key} 必须有限, 得到 {value!r}")

    if problems:
        return None, problems
    blob = json.dumps(state, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return blob.encode("utf-8"), []


def state_hash(state: object) -> tuple[Optional[str], list[str]]:
    """canonical 状态对象 → sha256 十六进制串。"""
    blob, problems = canonical_state_bytes(state)
    if blob is None:
        return None, problems
    return hashlib.sha256(blob).hexdigest(), []


def _split_ledger_lines(raw: bytes) -> list[bytes]:
    """账本字节 → 物理行列表 (1-based 行号 = 索引 + 1)。

    ⚠️ 必须按 \\n 切分, **不能**用 splitlines(): 后者还会在 \\r / \\v / \\f /
    \\x1c-\\x1e / \\x85 处断行, 与主体校验 (二进制文件迭代, 只认 \\n) 和
    prefix 计算的行号定义不一致 —— 一条含裸 CR 的记录会让两套编号错位,
    cursor_line 与 prefix 指向不同的行 (round-15 自查实证)。
    """
    chunks = raw.split(b"\n")
    if chunks and chunks[-1] == b"":
        chunks.pop()  # 末尾 LF 不产生额外空行
    return chunks


def scan_ledger_bytes(raw: bytes, node_id: object) -> tuple[dict, list[str]]:
    """在**同一份字节快照**上扫出 proof 所需的全部账本事实。

    返回 (scan, problems)。scan 各键:
      - `applicable`：[(行号, review_time, event_id)] —— node 相同、
        `schema_ext == "review/1"`、未标 `out_of_order` 的事件;
      - `node_event_lines`：该节点的**全部**事件行号 (不限 review/1) ——
        §6.2 genesis 锚要求的是"最早一条事件", 不是"最早适用事件";
      - `unextended_lines`：该节点**无 review/1 扩展**的事件行号 —— 存在即
        禁止走 new_card 分支 (§6.2: 账本历史不完整时须人工裁定);
      - `degraded_lines`：算法身份为 `degraded:*` 哨兵的适用事件行号;
      - `vault_ids`：适用事件 payload 里出现过的 vault_id 集合;
      - `bad_lines`：无法解码/解析的行号。

    ⚠️ 只接受**字节**而非路径: proof 校验必须在单一快照上完成, 否则抽取与
    prefix 可能读到不同版本 (round-15 Codex HIGH: 两次 read_bytes 之间的
    并发追加会让最外层尾部门失效)。
    """
    problems: list[str] = []
    scan = {
        "applicable": [],
        "node_event_lines": [],
        "unextended_lines": [],
        "degraded_lines": [],
        "vault_ids": set(),
        "bad_lines": [],
    }
    for idx, chunk in enumerate(_split_ledger_lines(raw), start=1):
        if not chunk.strip():
            continue
        try:
            record = _strict_loads(chunk.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            # round-15 Codex MEDIUM: 原实现静默 continue —— 但无法判断坏行
            # 是否本应参与该节点的 proof, 静默跳过即静默削弱尾部门 ⇒ fail-closed
            scan["bad_lines"].append(idx)
            continue
        if not isinstance(record, dict) or record.get("node_id") != node_id:
            continue
        scan["node_event_lines"].append(idx)
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("schema_ext") != REVIEW_EXT_MARKER:
            scan["unextended_lines"].append(idx)
            continue
        if "out_of_order" in payload:
            continue
        review_time = payload.get("review_time")
        event_id = record.get("event_id")
        if not isinstance(review_time, str) or not isinstance(event_id, str):
            problems.append(f"第 {idx} 行: review_time/event_id 非字符串, 无法参与 proof")
            continue
        for key in ("fsrs_library_version", "fsrs_params_hash"):
            value = payload.get(key)
            if isinstance(value, str) and value.startswith(DEGRADED_PREFIX):
                scan["degraded_lines"].append(idx)
        vault_id = payload.get("vault_id")
        if isinstance(vault_id, str) and vault_id:
            scan["vault_ids"].add(vault_id)
        scan["applicable"].append((idx, review_time, event_id))
    return scan, problems


def extract_applicable(source, node_id: object) -> tuple[list[tuple[int, str, str]], list[str]]:
    """`scan_ledger_bytes()` 的便捷入口 → (适用事件, 违规)。接受 Path 或 bytes。"""
    raw, read_problems = _ledger_bytes(source)
    if raw is None:
        return [], read_problems
    scan, problems = scan_ledger_bytes(raw, node_id)
    return scan["applicable"], read_problems + problems


def _ledger_bytes(source) -> tuple[Optional[bytes], list[str]]:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source), []
    try:
        return Path(source).read_bytes(), []
    except OSError as exc:
        return None, [f"账本不可读: {exc}"]


def ledger_prefix(source, cursor_line: int) -> tuple[Optional[str], bool, list[str]]:
    """账本从第 0 字节到第 `cursor_line` 行终止 LF (含) 的 sha256。接受 Path 或 bytes。

    返回 (sha256 十六进制, 该行是否无终止 LF, 违规)。§6.2 `ledger_prefix_sha256`
    与 `prefix_ends_without_lf` 的**可执行定义** —— 此前只有散文, 无法复算。
    """
    raw, problems = _ledger_bytes(source)
    if raw is None:
        return None, False, problems
    offset = 0
    for seen in range(1, cursor_line + 1):
        nl = raw.find(b"\n", offset)
        if nl == -1:
            if seen == cursor_line and offset < len(raw):
                return hashlib.sha256(raw).hexdigest(), True, []
            return None, False, [f"账本不足 {cursor_line} 行"]
        offset = nl + 1
    return hashlib.sha256(raw[:offset]).hexdigest(), False, []


def _frontmatter_fsrs_keys(text: str) -> tuple[list[str], bool]:
    """frontmatter 原文 → (顶层 `fsrs_*` 键列表, 是否用真 YAML 解析)。

    round-15 Codex HIGH/NEW-FINDING 双向修正:
      - 加引号的顶层键 `"fsrs_state": 2` 是合法 YAML, 原正则识别不出 (漏检);
      - block scalar 正文里的 `fsrs_state: ...` 是字符串内容不是键, 原正则
        误判 (误拒)。
    有 PyYAML 时按真语义取顶层键; 无则退化为**行首** (第 0 列) 正则 ——
    顶层键必在第 0 列, 故缩进的 block scalar 正文不再误命中。
    """
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
        except Exception:
            return ["<frontmatter 无法解析>"], True
        if data is None:
            return [], True
        if not isinstance(data, dict):
            return ["<frontmatter 顶层非映射>"], True
        return sorted(k for k in data if isinstance(k, str) and k.startswith("fsrs_")), True
    found = {m.group(1) for m in re.finditer(r"(?m)^[\"']?(fsrs_[A-Za-z0-9_]*)[\"']?\s*:", text)}
    return sorted(found), False


def _verify_proof_level(
    proof: object,
    applicable: list[tuple[int, str, str]],
    *,
    scan: Optional[dict] = None,
    ledger_raw: Optional[bytes] = None,
    is_top_level: bool = True,
    _depth: int = 0,
) -> list[str]:
    """degraded 解冻 proof 的结构 / 分层 / 真实绑定门。返回违规列表。

    见 `verify_degraded_proof()` 的 docstring 了解调用契约与范围声明。
    """
    problems: list[str] = []
    if _depth > PROOF_MAX_DEPTH:
        return [f"ancestor_proof 链深度超过 {PROOF_MAX_DEPTH} — 疑似自引用或异常构造"]
    if not isinstance(proof, dict):
        return ["proof 必须是 JSON object"]

    for key in _PROOF_REQUIRED_KEYS:
        if key not in proof:
            problems.append(f"缺必填字段 {key} (§6.2 表: 缺任一项即不可证明)")

    cursor = proof.get("cursor_line")
    if not isinstance(cursor, int) or isinstance(cursor, bool) or cursor < 1:
        return problems + [f"cursor_line 必须是 >=1 的整数, 得到 {cursor!r}"]

    # 账本直读模式: 全部事实取自**同一份字节快照** (round-15 Codex HIGH)
    if scan is not None:
        applicable = scan["applicable"]
        if scan["bad_lines"]:
            problems.append(
                f"账本第 {scan['bad_lines']} 行无法解析 — 无法判断其是否本应参与本节点的 proof, "
                f"fail-closed (须先由主体校验修复账本)"
            )
        computed_prefix, ends_without_lf, prefix_problems = ledger_prefix(ledger_raw, cursor)
        problems.extend(prefix_problems)
        if computed_prefix is not None:
            if proof.get("ledger_prefix_sha256") != computed_prefix:
                problems.append(
                    f"ledger_prefix_sha256 与账本实算不符: 声称 {proof.get('ledger_prefix_sha256')!r}, "
                    f"实算 {computed_prefix}"
                )
            if ends_without_lf and proof.get("prefix_ends_without_lf") is not True:
                problems.append("E 所在行无终止 LF, 必须写 prefix_ends_without_lf: true")
            if not ends_without_lf and "prefix_ends_without_lf" in proof:
                problems.append("E 所在行有终止 LF, 必须省略 prefix_ends_without_lf")
        vault_ids = scan["vault_ids"]
        if vault_ids and proof.get("vault_id") not in vault_ids:
            problems.append(
                f"vault_id 与账本事件不符: proof 声称 {proof.get('vault_id')!r}, 账本为 {sorted(vault_ids)}"
            )

    problems.extend(_check_proof_identity(proof))

    review_time = proof.get("review_time")
    if not isinstance(review_time, str):
        return problems + ["review_time 必须是字符串"]
    # round-15 Codex MEDIUM: 原只用宽松 fromisoformat, naive 时间与
    # 9999-12-31 均放行, 且 naive/aware 混排会在比较处抛 TypeError
    ok, why = _parse_ts(review_time, upper_bound=REVIEW_INPUT_MAX)
    if not ok:
        return problems + [f"review_time 不合法: {why}"]
    if not _WHOLE_SECOND_RE.match(review_time):
        problems.append(f"review_time 必须是整秒且带秒段 (§6.2 A5): {review_time!r}")
    e_instant = _aware_instant(review_time)
    if e_instant is None:
        return problems + [f"review_time 不可解析为绝对瞬间: {review_time!r}"]

    lines: dict[int, tuple[str, str]] = {}
    seen_lines: set[int] = set()
    for entry in applicable:
        if not isinstance(entry, (tuple, list)) or len(entry) != 3:
            # round-15 Codex LOW: 旧二元接口会在解包处抛 ValueError 而非报违规
            problems.append(f"applicable 元素必须是 (行号, review_time, event_id) 三元组, 得到 {entry!r}")
            continue
        line_no, ts, event_id = entry
        if line_no in seen_lines:
            problems.append(f"applicable 内行号 {line_no} 重复 — 输入不自洽")
        seen_lines.add(line_no)
        lines[line_no] = (ts, event_id)

    if cursor not in lines:
        problems.append(f"cursor_line={cursor} 不是该节点的适用事件行")
    else:
        cursor_ts, cursor_event_id = lines[cursor]
        if _aware_instant(cursor_ts) != e_instant:
            problems.append(f"review_time 与第 {cursor} 行的事件时刻不一致")
        if proof.get("event_id") != cursor_event_id:
            problems.append(
                f"event_id 未绑定到 E: proof 声称 {proof.get('event_id')!r}, 第 {cursor} 行为 {cursor_event_id!r}"
            )

    # 尾部作用域 —— round-13 冻结: 仅最外层
    if is_top_level:
        tail = sorted(ln for ln in lines if ln > cursor)
        if tail:
            problems.append(f"最外层 proof 的 cursor_line={cursor} 之后仍有适用事件 {tail} — 未覆盖到账本末尾")

    origin = proof.get("origin")
    if not isinstance(origin, dict):
        return problems + ["origin 必须是 JSON object"]
    kind = origin.get("kind")

    if kind == "new_card":
        left, genesis_problems = _check_genesis(origin, lines, scan)
        problems.extend(genesis_problems)
        ancestor_end: Optional[datetime] = None
    elif kind == "snapshot":
        left, ancestor_end, snapshot_problems = _check_snapshot(
            proof, origin, applicable, cursor, scan, ledger_raw, _depth
        )
        problems.extend(snapshot_problems)
        if left is _ABORT:
            return problems
    else:
        return problems + [f"origin.kind 必须是 new_card 或 snapshot, 得到 {kind!r}"]

    # 折叠区间 (left, cursor] 按行号左开右闭 + 层内单调 + 跨层单调
    if left is not None:
        interval = sorted(ln for ln in lines if left < ln <= cursor)
        if not interval:
            problems.append(f"折叠区间 ({left}, {cursor}] 内无适用事件")
        else:
            if scan is not None:
                tainted = sorted(ln for ln in scan["degraded_lines"] if left < ln <= cursor)
                if tainted:
                    problems.append(
                        f"折叠区间内第 {tainted} 行的算法身份是 degraded 哨兵 — 无法确定性复算, 该区间须人工裁定 (§6.2)"
                    )
            instants = [_aware_instant(lines[ln][0]) for ln in interval]
            if any(i is None for i in instants):
                problems.append("折叠区间内存在不可解析或非 aware 的 review_time")
            else:
                for idx in range(1, len(instants)):
                    if instants[idx] <= instants[idx - 1]:
                        problems.append(
                            f"层内单调门失败: 第 {interval[idx]} 行时刻未严格大于第 {interval[idx - 1]} 行 "
                            f"— 迟到事件未标 out_of_order, 账本不自洽"
                        )
                        break
                if ancestor_end is not None and ancestor_end >= instants[0]:
                    problems.append(
                        f"跨层单调门失败: ancestor.review_time 未严格小于本层首个事件 (第 {interval[0]} 行) 的时刻"
                    )

    if "prefix_ends_without_lf" in proof and proof["prefix_ends_without_lf"] is not True:
        problems.append("prefix_ends_without_lf 出现时必须恰为 true (有 LF 时须省略, 不得写 false)")

    return problems


#: `_check_snapshot` 用于示意"本层已无法继续判定"的哨兵
_ABORT = object()


def _check_proof_identity(proof: dict) -> list[str]:
    """身份、算法身份与 hash 形状 (§6.2 表)。

    round-15 Codex HIGH: 原实现只验非空 —— `library_version="garbage"`、
    `params_hash="degraded:x"`、`scheduler_config={}`、`reducer={}` 全部放行。
    §6.2 明写算法身份"须与 G3-4 golden manifest 同源", 故与 manifest 真值绑定;
    manifest 不可达时降级为形状校验 (与 review/1 行同口径)。
    """
    problems: list[str] = []
    for key in ("vault_id", "node_id", "event_id"):
        value = proof.get(key)
        if key in proof and (not isinstance(value, str) or not value.strip()):
            problems.append(f"{key} 必须是非空字符串")

    manifest = _golden_manifest()
    version = proof.get("fsrs_library_version")
    if "fsrs_library_version" in proof:
        if not isinstance(version, str) or not version:
            problems.append("fsrs_library_version 必须是非空字符串")
        elif version.startswith(DEGRADED_PREFIX):
            problems.append("fsrs_library_version 为 degraded 哨兵 — 哨兵不参与自动证明链 (§6.2)")
        elif manifest is not None and version != manifest["library_version"]:
            problems.append(
                f"fsrs_library_version 与 golden manifest 不同源: proof {version!r} vs manifest "
                f"{manifest['library_version']!r}"
            )
        elif manifest is None and not _VERSION_RE.match(version):
            problems.append(f"fsrs_library_version 形状非法 (manifest 不可达, 降级形状校验): {version!r}")

    params_hash = proof.get("fsrs_params_hash")
    if "fsrs_params_hash" in proof:
        if not isinstance(params_hash, str) or not params_hash:
            problems.append("fsrs_params_hash 必须是非空字符串")
        elif params_hash.startswith(DEGRADED_PREFIX):
            problems.append("fsrs_params_hash 为 degraded 哨兵 — 哨兵不参与自动证明链 (§6.2)")
        elif manifest is not None and params_hash != manifest["params_hash"]:
            problems.append(
                f"fsrs_params_hash 与 golden manifest 不同源: proof {params_hash!r} vs manifest "
                f"{manifest['params_hash']!r}"
            )
        elif manifest is None and not _HASH_RE.match(params_hash):
            problems.append(f"fsrs_params_hash 形状非法 (manifest 不可达, 降级形状校验): {params_hash!r}")

    config = proof.get("scheduler_config")
    if "scheduler_config" in proof:
        if not isinstance(config, dict) or not config:
            problems.append("scheduler_config 必须是非空 JSON object (须完整可复算)")
        elif manifest is not None and isinstance(manifest.get("scheduler_config"), dict):
            if config != manifest["scheduler_config"]:
                missing = sorted(set(manifest["scheduler_config"]) - set(config))
                problems.append(
                    f"scheduler_config 与 golden manifest 不同源"
                    + (f" (缺键 {missing})" if missing else " (同键集但取值不同)")
                )
        else:
            missing = sorted(_SCHEDULER_CONFIG_KEYS - set(config))
            if missing:
                problems.append(f"scheduler_config 缺字段 {missing} (manifest 不可达, 降级形状校验)")

    reducer = proof.get("reducer")
    if "reducer" in proof:
        if not isinstance(reducer, dict):
            problems.append("reducer 必须是 JSON object")
        else:
            if not isinstance(reducer.get("id"), str) or not reducer["id"]:
                problems.append("reducer.id 必须是非空字符串 (canonical reducer 标识)")
            precision = reducer.get("precision")
            if not isinstance(precision, int) or isinstance(precision, bool) or precision < 0:
                problems.append(f"reducer.precision 必须是非负整数 (精度常量), 得到 {precision!r}")

    for key in ("ledger_prefix_sha256", "result_hash"):
        value = proof.get(key)
        if key in proof and (not isinstance(value, str) or not _SHA256_HEX_RE.match(value)):
            problems.append(f"{key} 必须是 64 位小写十六进制 sha256, 得到 {value!r}")
    return problems


def _check_genesis(origin: dict, lines: dict, scan: Optional[dict]) -> tuple[Optional[int], list[str]]:
    """`origin.kind == "new_card"` 的 genesis 真锚 (§6.2)。→ (折叠区间左端点, 违规)。"""
    problems: list[str] = []
    evidence = origin.get("genesis_evidence")
    if not isinstance(evidence, dict):
        return None, ["origin.kind=new_card 必须附 genesis_evidence object"]

    fm_hash = evidence.get("node_frontmatter_hash")
    if not isinstance(fm_hash, str) or not _SHA256_HEX_RE.match(fm_hash):
        problems.append(f"genesis_evidence.node_frontmatter_hash 必须是 64 位十六进制, 得到 {fm_hash!r}")
    # round-15 Codex NEW-FINDING: 空 frontmatter 是合法的 (规范未要求非空),
    # 原实现私加"非空"门属误拒 —— 只要求是字符串
    fm_text = evidence.get("node_frontmatter_text")
    if not isinstance(fm_text, str):
        problems.append("genesis_evidence.node_frontmatter_text 必须是字符串")
    else:
        offenders, parsed = _frontmatter_fsrs_keys(fm_text)
        if offenders:
            how = "YAML 顶层键" if parsed else "行首键 (无 PyYAML, 降级正则)"
            problems.append(f"genesis_evidence 原文含 FSRS {how} {offenders} — 与 new_card(三态判别为 new) 矛盾")
        if isinstance(fm_hash, str) and _SHA256_HEX_RE.match(fm_hash):
            if hashlib.sha256(fm_text.encode("utf-8")).hexdigest() != fm_hash:
                problems.append("genesis_evidence.node_frontmatter_hash 与所附原文不符 (自洽性)")

    # §6.2: new_card 只在该节点**账本历史完整**时可用 —— 存在无 review/1
    # 扩展的旧行时必须人工裁定 (round-15 Codex HIGH: 原实现未查此条)
    if scan is not None and scan["unextended_lines"]:
        problems.append(
            f"该节点第 {scan['unextended_lines']} 行是无 review/1 扩展的历史事件 — "
            f"§6.2 禁止在账本历史不完整时采信 new_card, 须改走 snapshot 或人工裁定"
        )

    first_line = evidence.get("first_event_line")
    if not isinstance(first_line, int) or isinstance(first_line, bool) or first_line < 1:
        problems.append(f"genesis_evidence.first_event_line 必须 >=1, 得到 {first_line!r}")
        return None, problems
    # §6.2 的定义是"该节点在账本中**最早一条事件**的行号" —— 不是最早的
    # *适用* 事件 (round-15 Codex HIGH: 二者在有历史无扩展行时不同)
    earliest = min(scan["node_event_lines"]) if (scan and scan["node_event_lines"]) else (min(lines) if lines else None)
    if earliest is not None and first_line != earliest:
        problems.append(
            f"genesis_evidence.first_event_line={first_line} 不是该节点最早的事件行 (实为 {earliest}) "
            f"— 区间左端点不可核验"
        )
    return first_line - 1, problems


def _check_snapshot(
    proof: dict,
    origin: dict,
    applicable: list,
    cursor: int,
    scan: Optional[dict],
    ledger_raw: Optional[bytes],
    depth: int,
):
    """`origin.kind == "snapshot"` 的三等式、链约束与递归。→ (左端点, ancestor 时刻, 违规)。"""
    problems: list[str] = []
    ancestor = origin.get("ancestor_proof")
    snap_hash = origin.get("snapshot_hash")
    state = origin.get("state")

    computed, state_problems = state_hash(state)
    problems.extend(f"origin.state: {p}" for p in state_problems)
    if isinstance(state, dict):
        problems.extend(f"origin.state: {p}" for p in _state_domain_problems(state))
    if not isinstance(snap_hash, str) or not _SHA256_HEX_RE.match(snap_hash):
        problems.append(f"origin.snapshot_hash 必须是 64 位十六进制, 得到 {snap_hash!r}")
    elif computed is not None and snap_hash != computed:
        problems.append("等式1 失败: snapshot_hash != sha256(canonical(state))")
    if not isinstance(ancestor, dict):
        return _ABORT, None, problems + ["origin.kind=snapshot 必须附 ancestor_proof object"]

    # 递归: ancestor 是中间层, 不受尾部约束 (round-13 冻结)
    problems.extend(
        f"ancestor_proof: {p}"
        for p in _verify_proof_level(
            ancestor,
            applicable,
            scan=scan,
            ledger_raw=ledger_raw,
            is_top_level=False,
            _depth=depth + 1,
        )
    )
    if isinstance(snap_hash, str) and ancestor.get("result_hash") != snap_hash:
        problems.append("等式2 失败: snapshot_hash != ancestor_proof.result_hash")

    anc_rt = ancestor.get("review_time")
    anc_instant = _aware_instant(anc_rt)
    state_w = state.get("fsrs_last_review") if isinstance(state, dict) else None
    state_w_instant = _aware_instant(state_w)
    if state_w_instant is None or anc_instant is None or state_w_instant != anc_instant:
        problems.append("等式3 失败: state.fsrs_last_review != ancestor_proof.review_time (按绝对瞬间)")

    anc_cursor = ancestor.get("cursor_line")
    if not isinstance(anc_cursor, int) or isinstance(anc_cursor, bool):
        return _ABORT, None, problems + ["ancestor_proof.cursor_line 必须是整数"]
    if anc_cursor >= cursor:
        problems.append(f"链未严格递减: ancestor.cursor_line={anc_cursor} >= 本层 {cursor}")
    for key in ("vault_id", "node_id"):
        if ancestor.get(key) != proof.get(key):
            problems.append(f"链上 {key} 必须相同")
    if anc_instant is None:
        problems.append("ancestor_proof.review_time 不可解析")
    return anc_cursor, anc_instant, problems


def _state_domain_problems(state: dict) -> list[str]:
    """snapshot state 的数值域 —— 与 `classify_card_state()` 同判据。

    round-15 Codex: 原实现只查类型不查域, `stability=-1.0, difficulty=99.0`
    能算出无违规的 hash, 而同文件的三态判别对同一组值判 degraded。
    """
    problems: list[str] = []
    stability = state.get("fsrs_stability")
    if isinstance(stability, float) and not (0 < stability <= STABILITY_MAX):
        problems.append(f"fsrs_stability {stability!r} 不在可调度域 (0, {STABILITY_MAX}]")
    difficulty = state.get("fsrs_difficulty")
    low, high = DIFFICULTY_RANGE
    if isinstance(difficulty, float) and not (low <= difficulty <= high):
        problems.append(f"fsrs_difficulty {difficulty!r} 不在可调度域 [{low}, {high}]")
    return problems


def _aware_instant(value: object) -> Optional[datetime]:
    """`_instant()` 的 **timezone-aware 限定**版 —— naive 一律 None。

    round-15 Codex MEDIUM: naive 与 aware 的 datetime 相比会抛 TypeError,
    proof 校验必须报违规而不是崩溃。
    """
    parsed = _instant(value)
    if parsed is None or parsed.tzinfo is None:
        return None
    return parsed


def verify_degraded_proof(
    proof: object,
    applicable: list[tuple[int, str, str]],
    *,
    ledger_path: Optional[Path] = None,
) -> list[str]:
    """degraded 解冻 proof 的结构 / 分层 / 真实绑定门。返回违规列表。

    `applicable` = 该节点全部**适用事件**的 [(行号, review_time, event_id)],
    行号 1-based。传 `ledger_path` 时**忽略本参数**, 改由 `scan_ledger_bytes()`
    在**单一字节快照**上抽取, 并复算 `ledger_prefix_sha256` 与
    `prefix_ends_without_lf`。

    ⚠️ **信任边界**: 不传 `ledger_path` 时本函数**不读账本**, `applicable` 的
    完整性完全由调用方保证 —— 抽取不全会让最外层尾部门**真空通过**, prefix
    也只校验形状不复算。**生产接入必须传 `ledger_path`**。

    ⚠️ **本函数不做的事** (round-15 逐项收紧后仍成立):
      ① 不复算 FSRS 折叠 (canonical reducer 属 G3-2);
      ② 不复算 `result_hash` (同样依赖 reducer);
      ③ 不把 `genesis_evidence.node_frontmatter_text` 与**真实节点文件**的字节
         比对 —— 只验其与自报 hash 自洽、且不含 FSRS 顶层键。节点文件路径不在
         proof 内, 该绑定须由调用方在重建时另行完成;
      ④ 传 `ledger_path` 时读取的是**调用瞬间的快照**: 快照之后的并发追加不在
         本次判定内 (调用方须在持有账本锁时校验)。
    返回空 ≠ proof 成立, 只 = 已判门内无歧义, 可交付 reducer 复算。

    注: 尾部作用域参数 `is_top_level` 不在公开签名内 —— 它是递归内部状态,
    公开可写会变成"关掉尾部门"的脚枪 (round-15 Codex LOW)。
    """
    scan: Optional[dict] = None
    ledger_raw: Optional[bytes] = None
    prelude: list[str] = []
    if ledger_path is not None:
        ledger_raw, read_problems = _ledger_bytes(ledger_path)
        prelude.extend(read_problems)
        if ledger_raw is not None:
            node_id = proof.get("node_id") if isinstance(proof, dict) else None
            scan, scan_problems = scan_ledger_bytes(ledger_raw, node_id)
            prelude.extend(scan_problems)
    try:
        return prelude + _verify_proof_level(proof, applicable, scan=scan, ledger_raw=ledger_raw)
    except RecursionError:
        return prelude + [f"ancestor_proof 链过深, 递归耗尽栈 (上限 {PROOF_MAX_DEPTH} 层) — 疑似自引用或异常构造"]


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

    只接受**含两个真值键的 dict**; 缺失/损坏/空对象/非 dict 一律 → None,
    调用方降级为形状校验 + WARN (round-4 MEDIUM: 非 dict 曾可 traceback)。
    """
    candidate = Path(__file__).resolve().parents[1] / "tests" / "regression" / "fsrs_golden_manifest.json"
    if not candidate.is_file():
        return None
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return None
    if not isinstance(data, dict):
        return None
    version, params_hash = data.get("library_version"), data.get("params_hash")
    # round-5 MEDIUM: 只查"是字符串"不够 — 空串或畸形值会让真值绑定形同虚设
    if not isinstance(version, str) or not _VERSION_RE.match(version):
        return None
    if not isinstance(params_hash, str) or not _HASH_RE.match(params_hash):
        return None
    return data


#: 极简可证形态 (round-7 终局决策): 逐行状态机仍会对合法 YAML 错绑
#: (plain scalar 折行 `vault_id: first` + 缩进续行, PyYAML 真值是
#: "first second"; `description: it's fine` 的撇号被当跨行引号起点)。
#: 手写 YAML 子集打不赢, 改为**只在形态确定无歧义时绑定**, 其余不绑定 + WARN:
#:   (1) 全文件恰有一处行首 `vault_id:`;
#:   (2) 该行是 `vault_id: "<无转义无换行>"` 或 `vault_id: <安全裸词>`;
#:   (3) 下一行不是缩进行 (排除 plain scalar 折行续接)。
#: 代价: `vault_id: team#1` 等形态退化为不绑定 (保守: 失一层防护 != 错绑),
#: 且 vault_id 本就是文件名安全 slug, 现网与部署模板均落在白名单形态内。
def _sanitize_vault_id(value: str) -> Optional[str]:
    """走 backend 的真实 `sanitize_vault_id`（同仓可达时），否则 None。

    ⚠️ round-11 HIGH#2: 只做 `safe_load + strip` **仍与生产分叉** ——
    `Settings.vault_id` 还会调 `sanitize_vault_id()`（`config.py:1020`），
    实测 `vault_id: team#1` 生产得 `team_1` 而本脚本曾绑定 `team#1`。
    复制该函数会重演"手写副本漂移"，故直接 import 真实实现；不可达时
    (脚本被拷到别处) **不绑定**，由调用方 WARN 降级。
    """
    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    try:
        from app.config import sanitize_vault_id  # noqa: PLC0415
    except Exception:  # noqa: BLE001 — 任何导入失败都降级为不绑定
        return None
    try:
        sanitized = sanitize_vault_id(value)
    except Exception:  # noqa: BLE001
        return None
    return sanitized if sanitized and sanitized != "default" else None


def _vault_id_of(ledger_path: Path) -> Optional[str]:
    """账本所在 vault 的**规范化** vault_id（同目录 .canvas-config.yaml）。

    ⚠️ **round-10/11 终局：与 backend 生产入口逐环节同源。**
    此前 r5~r9 手写 YAML 子集反复静默错绑；r10 改走 `yaml.safe_load` 后
    r11 又发现只做 `safe_load + strip` 仍与生产分叉——生产 `Settings.vault_id`
    的完整链是 **`safe_load` → `isinstance(str)` → `sanitize_vault_id()` →
    `!= "default"` 才采信**（`config.py:782-795`）。现逐环节复用同一实现：
    解析用 PyYAML，规范化用 backend 的 `sanitize_vault_id` 本体。

    任一环节不可达（PyYAML 缺失 / backend 不可 import）⇒ **不绑定 + WARN**，
    校验器其余功能不受影响。
    """
    config = ledger_path.parent / ".canvas-config.yaml"
    if not config.is_file():
        return None
    try:
        import yaml  # noqa: PLC0415 — 可选依赖, 不可用时降级
    except ImportError:
        return None
    try:
        with open(config, encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception:  # noqa: BLE001 — 与生产同口径 (config.py:777 捕 Exception)
        # round-11: 深嵌套 YAML 抛 RecursionError;
        # round-12: `vault_id: 2023-13-40` 让 PyYAML timestamp constructor 抛
        # ValueError(非 YAMLError) — 窄捕获会 traceback + exit 1, 而生产是回退。
        # 任何解析异常一律降级为不绑定 + WARN。
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("vault_id")
    if not isinstance(value, str) or not value.strip():
        return None
    return _sanitize_vault_id(value)


def _rating_from_grade_norm(grade_norm: float) -> int:
    """grade_norm → FSRS Rating, 与 fsrs_bridge.rating_from_grade 同口径
    ([Decision-FSRS-1]: 还原 grade = 1 + 3·gn 后就近落四档, 越界钳制)。"""
    grade = 1.0 + 3.0 * grade_norm
    rating = int(math.floor(grade + 0.5))
    return max(1, min(4, rating))


def _validate_review_ext(
    payload: dict, record: dict, manifest: Optional[dict], vault_id: Optional[str] = None
) -> tuple[list[str], list[str]]:
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

    marker_value = payload.get("out_of_order", None)
    if "out_of_order" in payload and marker_value is not True:
        problems.append(
            f"payload.out_of_order 唯一合法值为布尔 true, 实为 {marker_value!r} — "
            "未标乱序时不得写该键 (§6.2 字段冻结: false/字符串/对象均会让 pending 排除条件产生歧义)"
        )

    review_time = payload.get("review_time")
    ok, why = _parse_ts(review_time, upper_bound=REVIEW_INPUT_MAX)
    if not ok:
        problems.append(f"扩展键 review_time {why}")
    else:
        if _SUBSECOND_RE.match(review_time):
            problems.append(
                f"扩展键 review_time 必须为整秒 {review_time!r} — frontmatter 水位线 "
                "fsrs_last_review 只有整秒精度 (§6.2 A5), 小数秒会导致同一事件二次推进"
            )
        elif not _WHOLE_SECOND_RE.match(review_time):
            problems.append(
                f"扩展键 review_time 必须为完整整秒形态 YYYY-MM-DDTHH:MM:SS(Z|±HH:MM), "
                f"实为 {review_time!r} — 省略秒段与 W 的整秒口径对不齐 (§6.2 A5)"
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
    declared_vault = payload.get("vault_id")
    if isinstance(declared_vault, str) and declared_vault:
        if vault_id is None:
            warnings.append("vault_id 未绑定 — 账本同目录无 .canvas-config.yaml 或其中无 vault_id 键")
        elif declared_vault != vault_id:
            problems.append(
                f"扩展键 vault_id {declared_vault!r} != 账本所在 vault 声明的 {vault_id!r} "
                "(.canvas-config.yaml) — 事件写错 vault 或账本被搬运"
            )
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

    # 防御: _golden_manifest 已保证 dict|None, 此处对任意坏值也不炸
    # (round-4 MEDIUM: 非 dict manifest 曾可触发 AttributeError)
    manifest = manifest if isinstance(manifest, dict) else None
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


def validate_record(record: object, manifest: Optional[dict] = None, vault_id: Optional[str] = None) -> list[str]:
    """单条 v1 记录的违规清单 (空 = 合规); 便捷入口, 丢弃 warnings。"""
    return validate_record_full(record, manifest, vault_id)[0]


def validate_record_full(
    record: object, manifest: Optional[dict] = None, vault_id: Optional[str] = None
) -> tuple[list[str], list[str]]:
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
            ext_problems, ext_warnings = _validate_review_ext(payload, record, manifest, vault_id)
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
    vault_id = _vault_id_of(path)

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
                line_problems, line_warnings = validate_record_full(record, manifest, vault_id)
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
