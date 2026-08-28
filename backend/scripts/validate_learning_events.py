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
