# ✅ Verified structure from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层
"""
Review Service - Business logic for verification canvas and review operations.

This service provides async methods for review scheduling and
verification canvas generation, implementing FSRS (Free Spaced Repetition Scheduler)
algorithm for scientifically-optimized, personalized review intervals.

Story 32.2: Migrated from Ebbinghaus fixed intervals to FSRS-4.5 dynamic scheduling.
[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
[Source: docs/stories/32.2.story.md]

# ═══════════════════════════════════════════════════════════════════════════════
# FSRS MIGRATION DOCUMENTATION (Story 32.2 AC-32.2.5)
# ═══════════════════════════════════════════════════════════════════════════════
#
# OVERVIEW:
# This service was migrated from fixed Ebbinghaus intervals to FSRS-4.5 algorithm
# which provides personalized, adaptive spaced repetition scheduling.
#
# KEY CHANGES:
# 1. EbbinghausReviewScheduler → FSRSManager
# 2. Fixed intervals (1, 3, 7, 30 days) → Dynamic intervals based on:
#    - Memory stability (how well the card is remembered)
#    - Card difficulty (1-10 scale)
#    - Review history (reps, lapses)
#    - Desired retention rate (default: 90%)
#
# BACKWARD COMPATIBILITY (AC-32.2.4):
# - score (0-100) is still accepted and auto-converted to FSRS rating (1-4)
# - Conversion logic:
#   * score < 40  → rating 1 (Again/Forgot) - needs immediate relearning
#   * score 40-59 → rating 2 (Hard) - recalled with significant difficulty
#   * score 60-84 → rating 3 (Good) - recalled with some effort
#   * score >= 85 → rating 4 (Easy) - recalled effortlessly
#
# FSRS RATINGS (AC-32.2.2):
# - 1 (Again): Completely forgot, reset to learning state
# - 2 (Hard): Recalled with significant difficulty, shorter interval
# - 3 (Good): Recalled with acceptable effort, optimal interval
# - 4 (Easy): Recalled effortlessly, longer interval + lower difficulty
#
# CARD STATE PERSISTENCE:
# Card states are persisted via:
# 1. In-memory cache (_card_states dict) for fast access during session
# 2. Graphiti knowledge graph for long-term storage (optional)
# 3. API response card_data field for client-side caching
#
# MIGRATION STEPS FOR EXISTING DATA:
# 1. Existing review history is preserved (no data deletion required)
# 2. New cards start as "New" state with default parameters
# 3. First review establishes initial FSRS parameters
# 4. Subsequent reviews use FSRS algorithm for interval calculation
#
# FALLBACK BEHAVIOR:
# If FSRS is unavailable (import error), the service falls back to
# legacy Ebbinghaus fixed intervals for graceful degradation.
#
# ═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import logging
import random
import re

import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path as _Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from app.core.decision_tracker import log_decision
from app.core.exceptions import CanvasNotFoundException, TaskNotFoundError
from app.services.weight_calculator import ConceptWeightData, WeightCalculator

# Story 32.2 AC-32.2.1: Import FSRSManager for FSRS-4.5 algorithm
# [Source: src/memory/temporal/fsrs_manager.py]
try:
    import sys
    from pathlib import Path

    _project_root = Path(__file__).parent.parent.parent
    _src_path = _project_root / "lib"
    if str(_src_path) not in sys.path:
        sys.path.insert(0, str(_src_path))

    from memory.temporal.fsrs_manager import (
        CardState,
        FSRSManager,
        get_rating_from_score,
    )

    FSRS_AVAILABLE = True
except ImportError:
    FSRS_AVAILABLE = False
    FSRSManager = None
    get_rating_from_score = None
    CardState = None

# Story 38.3 AC-3 Code Review M2 Fix: Module-level runtime FSRS status.
# FSRS_AVAILABLE = library importable (compile-time).
# FSRS_RUNTIME_OK = FSRSManager actually initialized (runtime). None = not yet attempted.
FSRS_RUNTIME_OK: Optional[bool] = None

# P0-2: Card state persistence file path (matches learning_memories.json pattern)
#
# ⚠️ CARD-G3-7: 非 FSRS 调度真相源 —— 本文件是**投影/缓存**, 不是 current state。
# D0 修订 (docs/fsrs-truth-source-d0-revision.md) §一 铁律 1 + §五 T1: 节点当前
# 调度状态的唯一真相源是该节点 .md 的 frontmatter (fsrs_due 等), 写侧为 vault
# 的 quiz-answer × fsrs_bridge 链。此处的 JSON 及其内存镜像 self._card_states
# 只是后端侧投影, 与 frontmatter 分歧时**一律以 frontmatter 为准**, 并须以
# degraded 信号如实透出 (禁假成功)。裁定表: _bmad-output/审查/evidence-g37/decision.md
#
# ⚠️ CARD-G3-5: 本文件的 JSON **顶层键是 vault_id**, 二层才是 concept_id
# (``{vault_id: {concept_id: card_json}}``)。键化前是扁平
# ``{concept_id: card_json}``, 不带 vault 维度 —— 两个 vault 的同名 concept
# 撞同一个 JSON 键、后写覆盖先写。legacy 扁平快照在启动时按当前作用域**推定**
# 归桶 (可能归错, 见 _VaultScopedCardStates.from_persisted 的反例) 并告警;
# 只有作用域解析不出来时才不载入那部分。归属的**裁定**走
# ``backend/scripts/migrate_fsrs_card_states_vault_key_g35.py``(人给 --vault-id)。
# 前提: 「同名 concept 由目录天然隔离」只在**一进程一 vault** 时成立 ——
# 真相源 reader 的 ``settings.CANVAS_BASE_PATH`` 是进程级
# (``frontmatter_signals._node_md_path``), 该缺口本卡只登记不修。
_CARD_STATES_FILE = (
    _Path(__file__).parent.parent.parent / "data" / "fsrs_card_states.json"
)

# H2 fix: Module-level asyncio.Lock for concurrent card_states write protection
_card_states_lock = asyncio.Lock()

# ── CARD-G3-7: frontmatter 真相源只读入口 ────────────────────────────────────
#: frontmatter **块切分** —— 与 scripts/daily_review_pick.py::scan_nodes 逐字同源
#: (BOM 容忍 + CRLF 容忍; 无 frontmatter 块时 fm = "" 而**不是**整份文本)。
#:
#: ⚠️ Codex r1 HIGH-2 整改 (2026-09-06): 初版只有下面的字段正则、却把它作用在
#: **整份 .md** 上, 于是正文里顶格出现的 `fsrs_due: ...`(最典型的就是讲解该字段
#: 怎么写的文档节点) 会被当成权威 due, 并连带把门锁误判为"有真相源"。实测复现:
#: frontmatter 无该字段 + 正文一行 `fsrs_due: 2020-01-01T00:00:00Z`
#: → 返回 due=2020-01-01 且 reason=None (毫无察觉)。
#: 教训: **口径 = 正则 + 输入面**。正则逐字相同不足以证明解析语义相同 ——
#: 生产 reader 收到的参数是已切好的 `fm`(fsrs_bridge.py:149 形参名即 `fm`;
#: daily_review_pick.py 在 scan_nodes 内先切块再调 _fm_str)。
#: BOM 写成 ASCII 转义序列而非直接敲入 —— 不可见字符会被工具链静默改写, 且 review
#: diff 里看不出来。前缀段用普通字符串 (raw 串不处理 \u), 其余保持 raw。
_FM_BLOCK_RE = re.compile("^\\ufeff?" + r"---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.S)

#: 生产口径字段正则 —— 与既有两个 FSRS-frontmatter 生产 reader **逐字相同**:
#: canvas-vault/.claude/scripts/fsrs_bridge.py:151 fields_from_frontmatter()
#: scripts/daily_review_pick.py:341 _fm_str()
#: D0 修订 §五 T3 (禁第二套解析) 禁的是"另立一套语义", 不是"另写一个函数"。
#: 特意不走 PyYAML: live frontmatter 的 fsrs_due 未加引号 (实测
#: canvas-vault/节点/csm-tutoring-unit-credit.md), PyYAML 的 timestamp resolver
#: 会把它解析成 datetime, 而整条复习投影链 (daily_review_pick / review_overview)
#: 按 UTC-Z **字符串**比较 —— 换口径即制造分歧。
_FM_FIELD_RE = r'^{key}:\s*"?([^"\n]+?)"?\s*$'

#: fsrs_due 形态门禁 + 解析 —— 与 scripts/daily_review_pick.py:541-545 同口径。
_FM_DUE_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_FM_DUE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _whole_second_utc(value: Optional[datetime]) -> Optional[datetime]:
    """投影侧 due 归一到整秒 UTC, 供与 frontmatter 真相源比较。

    ⚠️ 分歧检测的比较精度必须等于**真相源本身的分辨率**, 否则测到的是分辨率
    差异而不是分歧。frontmatter 的 fsrs_due 按构造就是整秒 UTC-Z ——
    canvas-vault/.claude/scripts/fsrs_bridge.py 的 _whole_second() 归一后写出
    (该文件 :27「输出的 review_time 即本次实际采用的整秒 UTC 时刻」), 而后端
    投影的 due 带微秒。逐字节比较会让 truth_source_divergence **恒真**, 变成
    一个永远在响的警报 —— 那比没有信号更糟, 它会训练消费方忽略它。
    """
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _node_lookup_is_blinded(concept_id: str) -> bool:
    """定位「找不到节点」这个结论是否**不可信**（Codex r2 HIGH 整改）。

    `frontmatter_signals._node_md_path()` 用 `Path.exists()` 判存在, 而
    `Path.exists()` **自己吞掉 OSError 返回 False** —— 于是「确实没有这个节点」
    与「目录不可读所以看不见」在它的返回值里**完全不可区分**, 两者都给 None。
    2026-09-06 实测: 把 `节点/` 目录 chmod 000 后 `Path.exists()` 返 False
    (不抛异常), `_node_md_path` 返 None, 门锁据此放行 —— r1 HIGH-1 的同一
    缺陷在更早一层复发。
    ⚠️ Codex r2 把成因归给 `_read_frontmatter_fsrs` 里的 `except OSError` 分支;
    实测那条分支**根本没被触发**。照该归因去改会修错地方, 缺陷原样留着。

    这里用**不吞异常**的 `os.stat` 复核: 只有 FileNotFoundError / NotADirectory
    才算「确实没有」; 其余 OSError (PermissionError 等) 说明我们**看不见**,
    「没找到」这个结论不可信 ⇒ 调用方须 fail-closed。

    目录约定与 base 解析逐字对齐 `frontmatter_signals.py:33-40`（同一来源,
    该模块不在本卡地盘故只 import 不改; 默认值字面量在此重复一次是已知代价）。
    """
    import os

    from app.config import settings as _settings
    from app.services.frontmatter_signals import _NODE_DIR_PREFIXES

    canvas_base = getattr(_settings, "CANVAS_BASE_PATH", None) or "/vaults/canvas-vault"
    for prefix in _NODE_DIR_PREFIXES:
        candidate = _Path(canvas_base) / prefix / f"{concept_id}.md"
        try:
            os.stat(candidate)
        except (FileNotFoundError, NotADirectoryError):
            continue  # 这一路确实没有, 继续看下一个 prefix
        except ValueError:
            # UnicodeEncodeError (lone surrogate concept_id) / 内嵌 NUL 等 ——
            # 这个 id **在编码上就不可能**对应任何文件名, 所以"没有"是正确
            # 结论, 不是"看不见"。判成被蒙蔽会让门锁把这类 id 永久拦死; 且
            # 异常会冒泡到 record_review_result 的宽 except, 把整条 FSRS 路径
            # 降级成 ebbinghaus-fallback —— 实测打红既有两条测试
            # (test_surrogate_key_does_not_poison_subsequent_saves /
            #  test_record_review_unicode_write_failure_stays_fsrs_and_honest)。
            # 同族问题见 CARD-D3 Codex HIGH-3。
            continue
        except OSError:
            return True  # 真 I/O 受阻 ⇒ 「找不到」不可信
        else:
            return False  # 竟然 stat 到了 (定位后被创建), 不算被蒙蔽
    return False


def _read_frontmatter_fsrs(concept_id: str) -> Dict[str, Any]:
    """读节点 frontmatter 的 FSRS 真相源 (只读, 永不写)。

    CARD-G3-7 / D0 修订 §五 T1: 「读取"某节点当前该何时复习"必须最终溯源到
    frontmatter」。本函数是 backend/app 内该真相源的**唯一**读入口 —— 在本卡
    之前 backend 侧对它零实现 (`grep -c 'fsrs_due' review_service.py` == 0),
    这正是双真相源的物理成因。

    路径解析**复用** frontmatter_signals._node_md_path (节点/ 优先, 退 原白板/),
    不另立目录约定 (T3)。注意它比 daily_review_pick 多一个 原白板/ 回退面 ——
    这是超集, 已在验收单如实登记。

    Returns:
        found:      该 concept 是否有对应 .md (= 真相源载体是否存在)
        governed:   该 concept 是否**由 frontmatter 真相源管辖** (= 门锁判据)
        fsrs_due:   frontmatter 原始字符串 (无字段/读不到则 None)
        due:        解析出的 tz-aware datetime; 无字段或形态非规范时为 None
        reason:     'no_node_file' / 'node_file_unreadable' / 'no_fsrs_due'
                    / 'malformed_fsrs_due' / None

    门锁语义 (裁定 ②) —— `governed` 的四态, 注意它**不等于** `found`:
      1. .md 不存在                → governed=False (无真相源, 放行投影写)
      2. .md 可读但无 fsrs_due     → governed=False (新卡语义, 对齐
                                     scripts/daily_review_pick.py:435「无
                                     fsrs_due 即真新卡」)
      3. .md 可读且有 fsrs_due     → governed=True  (拦)
      4. .md 存在但**读不出来**    → governed=True  (**fail-closed**, 拦)

    第 4 态是 Codex r1 HIGH-1 整改 (2026-09-06): 初版把读取失败 `return out`
    成 `fsrs_due=None`, 门锁据此放行 —— 于是「节点确实有 fsrs_due、只是这一刻
    文件不可读」会让 GET 推进投影缓存并落盘, 直接推翻「有真相源时一律不推进」。
    附带 bug: reason 还停在初始的 'no_node_file', 谎报文件没找到。
    收紧理由: 读不出来 ⇒ **不知道**它说了什么 ⇒ 不能假设它没话说。宁可少写一次
    投影缓存 (下一次 GET 会重读), 也不能把第二真相源推进出去。
    """
    # frontmatter_signals 不在本卡地盘 (只 import 不改); 局部 import 避免
    # 模块级循环依赖并把 vault I/O 限制在真正需要的调用上。
    from app.services.frontmatter_signals import _node_md_path

    out: Dict[str, Any] = {
        "found": False,
        "governed": False,
        "fsrs_due": None,
        "due": None,
        "reason": "no_node_file",
    }
    if not concept_id:
        return out
    try:
        path = _node_md_path(concept_id)
    except ValueError:
        # 编码上不可能对应文件名 (lone surrogate / 内嵌 NUL) ⇒ "确实没有"
        # 是正确结论, 不走 fail-closed。见 _node_lookup_is_blinded 同款说明。
        return out
    except OSError:
        # 防御性: 现行 _node_md_path 用 Path.exists() 不会抛到这里 (实测),
        # 但真抛了属于"看不见" ⇒ fail-closed, 不能当成"没有这个节点"。
        out["governed"] = True
        out["reason"] = "node_lookup_unreadable"
        return out
    if path is None:
        # Codex r2 HIGH: "没找到"可能是"看不见"。Path.exists() 吞 OSError,
        # 两者在 _node_md_path 的返回值里不可区分 —— 必须独立复核一次。
        if _node_lookup_is_blinded(concept_id):
            out["governed"] = True
            out["reason"] = "node_lookup_unreadable"
            logger.warning(
                "CARD-G3-7: 节点定位被阻断 (目录不可读), 按 fail-closed 处理: %s",
                concept_id,
            )
        return out

    out["found"] = True
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        # fail-closed: 载体在但内容未知 ⇒ 按"归 frontmatter 管"处理
        out["governed"] = True
        out["reason"] = "node_file_unreadable"
        logger.warning(f"CARD-G3-7: frontmatter 读取失败 {concept_id}: {e}")
        return out

    # ⚠️ 只在 frontmatter **块内**取字段 —— 作用在整份 .md 上会把正文里顶格的
    # `fsrs_due: ...` 当成权威 due (Codex r1 HIGH-2 实测复现)。
    block = _FM_BLOCK_RE.match(text)
    fm = block.group(1) if block else ""

    m = re.search(_FM_FIELD_RE.format(key="fsrs_due"), fm, re.M)
    raw = m.group(1).strip() if m else ""
    if not raw:
        out["reason"] = "no_fsrs_due"
        return out
    out["governed"] = True

    out["fsrs_due"] = raw
    if not _FM_DUE_SHAPE.fullmatch(raw):
        out["reason"] = "malformed_fsrs_due"
        return out
    try:
        out["due"] = datetime.strptime(raw, _FM_DUE_FORMAT).replace(tzinfo=timezone.utc)
        out["reason"] = None
    except ValueError:
        # 形态过门但日历非法 (如 2026-13-45T00:00:00Z)
        out["reason"] = "malformed_fsrs_due"
    return out


# Story 34.8 AC3: Hard cap for show_all=True to prevent memory overflow
MAX_HISTORY_RECORDS = 1000


def _fmt_optional_2f(value: Optional[float]) -> str:
    """Format optional float for logs — fsrs 6.x new cards carry None
    stability/difficulty, and f-string ':.2f' on None raises TypeError."""
    return f"{value:.2f}" if value is not None else "None"

if TYPE_CHECKING:
    from app.services.background_task_manager import BackgroundTaskManager
    from app.services.canvas_service import CanvasService

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CARD-G3-5 (BATCH-2026-09-07-第十三批): FSRS 投影状态的 vault 分桶
# ═══════════════════════════════════════════════════════════════════════════


class _VaultScopedCardStates:
    """FSRS 投影状态容器 — 存储按 vault 分桶, 调用面保持裸 concept_id 语义。

    **存储形态 (内存与落盘同构)**: ``{vault_id: {concept_id: card_json_str}}``
    嵌套字典。**禁**分隔符拼接的复合键 (如 ``"vault_a:concept"``):
    ``concept_id`` 是节点文件 basename, 可含任意分隔符字面量, 拼接方案会让
    ``vault_a`` 的键面吃掉 ``vault_ab`` 的 (同 ``vault_scope.read_group_filter``
    的 ``__`` 定界符教训); 嵌套字典把这条歧义整个消掉。

    **调用面**: ``states[cid]`` / ``cid in states`` / ``states.get(cid)`` /
    ``states.items()`` 一律作用于**当前作用域**那一桶 — 既有调用点一行不用改,
    vault 维度由本容器在存取时解析。

    **作用域取值口 (fail-closed)**: ``require_read_group(None)`` 抛
    ``VaultScopeUnresolved`` 是"解析不出来"的**唯一**判据。⚠️ **不用**
    ``vault_scope.current_vault_id()``: 它**不会主动拒绝**无 ContextVar 的情形 ——
    未注入时回落进程级 active vault, 返回值里没有"解析不出来"的信号 (它并非
    在任何执行下都不抛: 依赖调用的异常它也没捕获, 但那不是可用的失败判据)。
    拿"缺 ContextVar"当它的失败判据, 那条 fail-closed 分支永远走不到 = 假
    fail-closed (读契约 R4「静默退化」同族)。解析失败 ⇒ **不推进投影** + ``logger.error``,
    绝不静默落进某个缺省桶 — 那是把配置断裂伪装成写入成功。

    ⚠️ **本容器解决的是投影侧撞键, 不解决真相源侧串库**: 调度真相源是节点
    ``.md`` 的 frontmatter, 其 reader (``frontmatter_signals._node_md_path``)
    走**进程级** ``settings.CANVAS_BASE_PATH``。「不同 vault 的同名 concept 由
    目录天然隔离」只在**一个后端进程只服务一个 vault** 时成立; 一进程多 vault
    时真相源 reader 本身就串库, 投影侧键化救不了 (CARD-G3-5 登记, 归后续卡)。
    """

    __slots__ = ("_buckets", "_orphan_legacy")

    def __init__(
        self,
        buckets: Optional[Dict[str, Dict[str, str]]] = None,
        orphan_legacy: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._buckets: Dict[str, Dict[str, str]] = buckets if buckets is not None else {}
        #: **未归属**的 legacy 裸键 —— 归不掉但也不能丢的那部分 (Codex r2 H4)。
        #: 它不参与任何读写 (不属于任何 vault), 但**必须随每次落盘原样写回**:
        #: 否则「本次不加载」只保护了这一次读, 下一次成功写入的全量快照就会把
        #: 它从磁盘永久删除 —— 那是把 fail-closed 变成了静默删数据。
        self._orphan_legacy: Dict[str, Any] = (
            orphan_legacy if orphan_legacy is not None else {}
        )

    # ── 作用域解析 ──────────────────────────────────────────────────────
    @staticmethod
    def _resolve_vault(context: str) -> Optional[str]:
        """当前作用域的 vault 段; 解析不出来返回 None (调用方据此 fail-closed)。

        延迟 import: 保 monkeypatch 可达 (负控 N2 靠打断解析链让本函数返 None)。
        """
        from app.core.vault_scope import VaultScopeUnresolved, require_read_group

        try:
            group_id = require_read_group(None, context=context)
        except VaultScopeUnresolved as e:
            logger.error(
                "CARD-G3-5 vault scope unresolved [context: %s]: %s — "
                "拒绝推进 FSRS 投影 (不落进缺省桶: 那会把配置断裂伪装成写入成功)",
                context,
                e,
            )
            return None

        # D16 逻辑组 ``vault:<vid>[:<二级>]`` → 取 vault 段。二级 (subject /
        # canvas) 段**故意不进键**: 投影按 vault 隔离即可, 再细分会让同一 vault
        # 内换白板读不到自己刚写的卡。
        segments = group_id.split(":")
        if len(segments) >= 2 and segments[1].strip():
            return segments[1]
        logger.error(
            "CARD-G3-5 vault scope shape invalid [context: %s]: %r 取不出 vault 段 — "
            "拒绝推进 FSRS 投影",
            context,
            group_id,
        )
        return None

    def _bucket(self, context: str, *, create: bool = False) -> Optional[Dict[str, str]]:
        vault_id = self._resolve_vault(context)
        if vault_id is None:
            return None
        if create:
            return self._buckets.setdefault(vault_id, {})
        return self._buckets.get(vault_id, {})

    # ── 写入 (显式返回是否推进, 供 fail-closed 调用方消费) ─────────────
    def try_set(self, concept_id: str, card_data: str, *, context: str) -> bool:
        """写入当前作用域桶; 作用域解析不出来 ⇒ 不写并返回 False。"""
        bucket = self._bucket(context, create=True)
        if bucket is None:
            return False
        bucket[concept_id] = card_data
        return True

    # ── Mapping 协议 (扁平 concept_id 语义, 作用于当前作用域桶) ────────
    def __getitem__(self, concept_id: str) -> str:
        bucket = self._bucket("review_service._card_states.__getitem__")
        if bucket is None or concept_id not in bucket:
            raise KeyError(concept_id)
        return bucket[concept_id]

    def __setitem__(self, concept_id: str, value: str) -> None:
        # 形参名与 ``dict.__setitem__(key, value)`` 对齐 —— 调用面是扁平 dict
        # 语义, 类型诊断消息也应与 dict 同形。
        #
        # 作用域解析失败时静默不写是**有意**的: 本魔术方法无返回值通道,
        # fail-closed 的可观测信号由 _resolve_vault 的 logger.error 承担;
        # 需要知道写没写成的调用方一律走 try_set。
        self.try_set(concept_id, value, context="review_service._card_states.__setitem__")

    def __contains__(self, concept_id: object) -> bool:
        bucket = self._bucket("review_service._card_states.__contains__")
        return bool(bucket) and concept_id in bucket

    def __eq__(self, other: object) -> bool:
        """与普通 dict 比较时按**当前作用域桶**比 — 保持扁平调用面的等价语义。

        既有调用点/测试写 ``states == {...}`` 时问的是"当前这个 vault 看到的
        投影是不是这些", 不是"全部 vault 的桶结构长这样"。与另一个容器比较
        则比全部桶 (存储层等价)。
        """
        if isinstance(other, _VaultScopedCardStates):
            return self._buckets == other._buckets
        if isinstance(other, dict):
            bucket = self._bucket("review_service._card_states.__eq__")
            return (bucket or {}) == other
        return NotImplemented

    # 注: 定义 __eq__ 的类, Python 自动置 __hash__ = None (与 dict 同为不可
    # 哈希的可变映射) —— 不必也不该显式重复赋值。

    def __len__(self) -> int:
        bucket = self._bucket("review_service._card_states.__len__")
        return len(bucket) if bucket else 0

    def __bool__(self) -> bool:
        bucket = self._bucket("review_service._card_states.__bool__")
        return bool(bucket)

    def __iter__(self):
        bucket = self._bucket("review_service._card_states.__iter__")
        return iter(bucket or {})

    def get(self, concept_id: str, default: Any = None) -> Any:
        # default 取 Any 而非 Optional[str]: 调用方用哨兵对象区分"缺失"与
        # "值为 None" (_save_card_states 的 `_missing = object()` 回滚路径)。
        bucket = self._bucket("review_service._card_states.get")
        if bucket is None:
            return default
        return bucket.get(concept_id, default)

    def pop(self, concept_id: str, default: Any = None) -> Any:
        bucket = self._bucket("review_service._card_states.pop", create=True)
        if bucket is None:
            return default
        return bucket.pop(concept_id, default)

    def items(self):
        bucket = self._bucket("review_service._card_states.items")
        return (bucket or {}).items()

    def keys(self):
        bucket = self._bucket("review_service._card_states.keys")
        return (bucket or {}).keys()

    def values(self):
        bucket = self._bucket("review_service._card_states.values")
        return (bucket or {}).values()

    # ── 存储层 ──────────────────────────────────────────────────────────
    def to_nested(self) -> Dict[str, Any]:
        """落盘快照 (浅拷贝到二层, 防调用方改动内部桶)。

        ⚠️ **未归属的 legacy 裸键必须原样写回** (Codex r2 H4): 它们归不掉
        (作用域解析不出来 / 与已迁桶同名冲突), 但**不能丢** —— 若落盘时省略,
        下一次成功写入就会把它们从磁盘永久删除, 「本次不加载」这道 fail-closed
        就变成了静默删数据。写回后文件是混合形态, 这是**有意**的: 保住数据 >
        格式纯净, 且下次启动的逐条分类照样认得出它们。
        """
        payload: Dict[str, Any] = {
            vid: dict(bucket) for vid, bucket in self._buckets.items()
        }
        for concept_id, card in self._orphan_legacy.items():
            # setdefault: 万一某个 legacy concept_id 与某个 vault_id 同名,
            # 保留 vault 桶 (它有明确身份), 不让裸键顶掉它。
            payload.setdefault(concept_id, card)
        return payload

    def total_cards(self) -> int:
        """全部 vault 桶的卡数 + 未归属 legacy 条数 — 日志用 (``len()`` 只数当前桶)。"""
        return sum(len(bucket) for bucket in self._buckets.values()) + len(
            self._orphan_legacy
        )

    @classmethod
    def from_persisted(cls, raw: Dict[str, Any]) -> "_VaultScopedCardStates":
        """从落盘 JSON 还原 —— **逐条**分形态: dict 值 = vault 桶, 其余 = legacy 裸键。

        **形态判据必须逐条, 不能整体** (Codex r1 HIGH-1 整改): 用
        ``all(isinstance(v, dict) ...)`` 整体判形态时, 混合快照
        ``{"vaultA": {"c": "卡"}, "d": "另一张卡"}`` 会被整体当成 legacy ——
        **已经迁好的 vaultA 桶被降格成一个名叫 "vaultA" 的 concept**, 它的卡
        数据变成一个 dict。迁移器 ``classify()`` 一直是逐条分类的, 加载器必须
        与它同口径, 否则两边对同一份文件给出不同的形态判断。

        **legacy 裸键的归属是「推定」, 不是「可证」** (同上整改): 归进当前解析
        到的 vault 桶并 ``logger.warning``。必须说清它可能错 —— 反例: 旧进程
        服务 vault A 留下扁平快照, 配置改成 B 后重启; 两个时点都满足「一进程一
        vault」, 但全部旧数据会被归进 B, 且**下一次落盘就把这个错误归属固化**。
        所以这里做的是「过渡期不丢数据」的推定, 不是归属证明; 真正的归属裁定
        在迁移器 (人显式 ``--vault-id``)。

        **「没有请求上下文」不构成保护** (同上整改): 解析链在 ContextVar 未注入
        时仍会推导进程 active vault, 正常启动**不会**因缺上下文而拒载。只有推导
        失败 / 结果落进污染桶时才拒 —— 那时连"归给谁"都答不上来, 此时**只载入
        已是 vault 桶的部分**, legacy 裸键进 ``_orphan_legacy`` (硬归缺省桶属读
        契约 R4 同族的静默降级)。

        **归不掉的 legacy 不丢, 进 ``_orphan_legacy``** (Codex r2 H3/H4):
          · 作用域解析不出来 ⇒ 全部 legacy 进隔离区 —— 否则「不加载」只保护了
            这一次读, 下一次成功写入的全量快照会把它们从磁盘**永久删除**;
          · legacy 的 concept_id 与目标桶已有条目**同名** ⇒ 保留桶内那份 (它有
            **明确**的 vault 身份), legacy 那份进隔离区。用推定归属去覆盖明确
            身份是反的: 前者可能错, 后者是上一次迁移/写入确定下来的。
        隔离区的内容随每次落盘原样写回, 直到有人用迁移器显式裁定归属。
        """
        if not raw:
            return cls()

        # 逐条分形态 —— 与迁移器 classify() 同口径
        buckets: Dict[str, Dict[str, str]] = {}
        legacy: Dict[str, Any] = {}
        for key, value in raw.items():
            if isinstance(value, dict):
                buckets[str(key)] = dict(value)
            else:
                legacy[str(key)] = value

        if not legacy:
            return cls(buckets)

        vault_id = cls._resolve_vault("review_service._load_card_states.legacy")
        if vault_id is None:
            logger.warning(
                "CARD-G3-5: %s 含 %d 条 legacy 裸 concept_id 键, 但当前作用域解析"
                "不出来 ⇒ 这部分**不归入任何 vault**(拒绝硬归缺省桶), 转入隔离区: "
                "它们不参与读写, 但**每次落盘都会原样写回**, 不会被删掉。已是 "
                "vault 桶的 %d 个桶照常载入。请跑 backend/scripts/"
                "migrate_fsrs_card_states_vault_key_g35.py --apply --vault-id <vault> "
                "裁定归属。",
                _CARD_STATES_FILE,
                len(legacy),
                len(buckets),
            )
            return cls(buckets, orphan_legacy=legacy)

        bucket = buckets.setdefault(vault_id, {})
        # 同名冲突: 桶内那份有**明确** vault 身份, legacy 那份只是**推定**归属。
        # 用推定去覆盖明确是反的 (Codex r2 H3) —— 保留桶内, legacy 进隔离区。
        clobbered = [cid for cid in legacy if cid in bucket]
        orphan = {cid: legacy[cid] for cid in clobbered}
        for cid, card in legacy.items():
            if cid not in bucket:
                bucket[cid] = card
        logger.warning(
            "CARD-G3-5: %s 含 %d 条 legacy 裸 concept_id 键, 已按当前作用域**推定**"
            "归入 vault %r 桶 (另有 %d 个已迁桶原样载入)。⚠️ 该归属是推定不是证明: "
            "若这份快照出自服务别的 vault 的旧进程, 归属就是错的, 且下次落盘会把它"
            "固化。%s请跑 backend/scripts/migrate_fsrs_card_states_vault_key_g35.py "
            "以显式 --vault-id 裁定归属。",
            _CARD_STATES_FILE,
            len(legacy) - len(clobbered),
            vault_id,
            max(len(buckets) - 1, 0),
            f"另有 {len(clobbered)} 条与该桶已有同名条目冲突 {clobbered[:5]}, "
            "**保留桶内那份**(它有明确 vault 身份), legacy 那份转入隔离区不丢也不覆盖。 "
            if clobbered
            else "",
        )
        return cls(buckets, orphan_legacy=orphan)


def _card_states_try_set(
    states: Any, concept_id: str, card_data: str, *, context: str
) -> bool:
    """写入形态分派 — 返回本次是否真的推进了投影。

    容器走 ``try_set`` (作用域解析不出来 ⇒ False, fail-closed);
    被测试整体替换成普通 dict 时直接写 (旧扁平语义, 恒 True)。

    ``states`` 取 ``Any``: 运行期它可能是容器也可能是普通 dict, 收窄成前者
    会让这里的 isinstance 变成"恒真"而被静态检查判为多余 —— 那正好把本函数
    存在的理由(形态分派)注释掉。
    """
    if isinstance(states, _VaultScopedCardStates):
        return states.try_set(concept_id, card_data, context=context)
    states[concept_id] = card_data
    return True


def _card_states_vault(states: Any, *, context: str) -> Optional[str]:
    """当前作用域的 vault 段 — 形态分派。

    容器走它自己的解析口 (失败返 None 并记 logger.error); 被测试整体替换成
    普通 dict 时没有 vault 维度可言, 返回 None。

    ``states`` 取 ``Any`` 的理由同 :func:`_card_states_try_set`。
    """
    if isinstance(states, _VaultScopedCardStates):
        return states._resolve_vault(context)
    return None


def _card_states_payload(states: Any) -> Any:
    """落盘 payload — 容器给嵌套快照; 被替换成普通 dict 时原样写。"""
    if isinstance(states, _VaultScopedCardStates):
        return states.to_nested()
    return states


def _card_states_count(states: Any) -> int:
    """日志计数 — 容器数全部桶的卡总数, 而不是当前桶 (``len()`` 只数当前桶)。"""
    if isinstance(states, _VaultScopedCardStates):
        return states.total_cards()
    return len(states)


class ReviewStatus(str, Enum):
    """复习状态枚举"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ReviewProgress:
    """
    复习进度数据类
    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    """

    task_id: str
    canvas_name: str
    total_nodes: int = 0
    reviewed_nodes: int = 0
    green_nodes: int = 0
    purple_nodes: int = 0
    red_nodes: int = 0
    status: ReviewStatus = ReviewStatus.PENDING
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """计算复习进度百分比"""
        if self.total_nodes == 0:
            return self.progress * 100
        return (self.reviewed_nodes / self.total_nodes) * 100

    @property
    def mastery_percentage(self) -> float:
        """计算掌握程度百分比 (绿色节点占比)"""
        if self.total_nodes == 0:
            return 0.0
        return (self.green_nodes / self.total_nodes) * 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "canvas_name": self.canvas_name,
            "total_nodes": self.total_nodes,
            "reviewed_nodes": self.reviewed_nodes,
            "green_nodes": self.green_nodes,
            "purple_nodes": self.purple_nodes,
            "red_nodes": self.red_nodes,
            "status": self.status.value
            if isinstance(self.status, ReviewStatus)
            else str(self.status),
            "progress": self.progress,
            "progress_percentage": self.progress_percentage,
            "mastery_percentage": self.mastery_percentage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "error": self.error,
        }


def create_fsrs_manager(settings=None) -> Optional[Any]:
    """
    Unified FSRSManager factory. Used by both DI and singleton paths.

    Story 32.8 AC-32.8.3 + AC-32.8.4: Single creation path with USE_FSRS check.

    Args:
        settings: Application settings. If None, loads from get_settings().

    Returns:
        FSRSManager instance or None if FSRS is disabled/unavailable.
    """
    if settings is None:
        try:
            from app.config import get_settings

            settings = get_settings()
        except (ImportError, RuntimeError) as e:
            logger.warning(f"Cannot load settings for FSRSManager: {e}")
            return None

    if not settings.USE_FSRS:
        logger.info("FSRS disabled via USE_FSRS=False")
        return None

    if not FSRS_AVAILABLE or FSRSManager is None:
        logger.warning("FSRS not available (py-fsrs not installed)")
        return None

    try:
        retention = settings.FSRS_DESIRED_RETENTION
        mgr = FSRSManager(desired_retention=retention)
        logger.info(f"FSRSManager created (desired_retention={retention})")
        return mgr
    except (TypeError, ValueError, RuntimeError) as e:
        logger.warning(f"FSRSManager creation failed: {e}")
        return None


class ReviewService:
    """
    Review and verification canvas business logic service.

    Provides async methods for:
    - Generating verification canvases
    - Scheduling reviews based on Ebbinghaus curve
    - Tracking review progress

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    """

    def __init__(
        self,
        canvas_service: "CanvasService",
        task_manager: "BackgroundTaskManager",
        graphiti_client: Optional[Any] = None,
        fsrs_manager: Optional[Any] = None,
    ):
        """
        Initialize ReviewService.

        Args:
            canvas_service: CanvasService instance for canvas operations
            task_manager: BackgroundTaskManager instance for async tasks
            graphiti_client: Optional GraphitiEdgeClient for history tracking
            fsrs_manager: Optional FSRSManager for FSRS-4.5 scheduling (Story 32.2)

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        [Source: Story 24.1 - Graphiti Integration]
        [Source: Story 32.2 - FSRS Integration]
        """
        self.canvas_service = canvas_service
        self.task_manager = task_manager
        self.graphiti_client = graphiti_client

        # Story 32.2 AC-32.2.1: Initialize FSRSManager with configurable desired_retention
        # Story 32.8 AC-32.8.3: USE_FSRS=False skips FSRSManager initialization
        # Story 38.3 AC-3: Enhanced init logging for FSRS status
        self._fsrs_init_ok = False
        self._fsrs_init_reason: Optional[str] = None
        global FSRS_RUNTIME_OK
        if fsrs_manager is not None:
            self._fsrs_manager = fsrs_manager
            self._fsrs_init_ok = True
            FSRS_RUNTIME_OK = True
            # CARD-DEBT-8 (Codex round-1 M1): 外来注入的 manager 缺
            # library_available 时 helper 走 fail-open 缺省 True——改
            # fail-closed 会打红既有 mock 注入套件, 故保留 HEAD 行为但
            # 让这个边缘显式出声 (一次性, 不在每次调用时刷屏)。
            if not hasattr(self._fsrs_manager, "library_available"):
                logger.warning(
                    "Injected fsrs_manager lacks 'library_available' "
                    "(CARD-DEBT-8); assuming real py-fsrs library (fail-open)"
                )
            logger.info("FSRS manager initialized successfully")
        else:
            # Story 32.8: Auto-create via unified factory (checks USE_FSRS internally)
            auto_mgr = create_fsrs_manager()
            if auto_mgr is not None:
                self._fsrs_manager = auto_mgr
                self._fsrs_init_ok = True
                FSRS_RUNTIME_OK = True
                logger.info("FSRS manager auto-created via factory")
            else:
                self._fsrs_manager = None
                self._fsrs_init_reason = "FSRS disabled or unavailable"
                FSRS_RUNTIME_OK = False
                logger.warning(
                    f"FSRS manager not initialized: {self._fsrs_init_reason}"
                )

        self._initialized = True
        self._task_canvas_map: Dict[str, str] = {}  # Maps task_id to canvas_name
        # Story 32.2 + P0-2: Card state storage with file persistence
        # CARD-G3-7: 非 FSRS 调度真相源 —— 这是 frontmatter 的后端投影/缓存,
        # 不是 current state。分歧时以 frontmatter 为准 (D0 修订 T1)。
        #
        # ⚠️ CARD-G3-5: 本容器的**存储键带 vault 维度**
        # (``{vault_id: {concept_id: card}}``), 但调用面仍是裸 ``concept_id``
        # 语义 —— 读写自动落到**当前作用域**那一桶 (取值口
        # ``require_read_group(None)``, 解析不出来即 fail-closed 不推进)。
        # 键化前这里是扁平 ``{concept_id: card}``, 两个 vault 的同名 concept
        # 撞同一条记录、后写覆盖先写。
        # 前提缺口 (本卡不修, 只登记): 调度真相源 reader 走**进程级**
        # ``settings.CANVAS_BASE_PATH`` (``frontmatter_signals._node_md_path``),
        # 故「同名 concept 由目录天然隔离」只在**一进程一 vault** 时成立;
        # 一进程多 vault 时真相源侧本身就串库, 投影侧键化救不了。
        self._card_states: "_VaultScopedCardStates" = self._load_card_states()
        # CARD-D3 Codex HIGH-1: 写失败后仍留在内存缓存的 concept (重启即丢)。
        # 全量快照写成功时整体治愈 (clear), 查询侧据此如实上报 persisted。
        #
        # ⚠️ CARD-G3-5 (Codex r1 MEDIUM-1): 元素是 **(vault_id, concept_id)**
        # 二元组, 不是裸 concept_id —— 主状态有了 vault 维度, 这个附属状态就
        # 必须同维, 否则 A 的 c 写盘失败会让 B 的同名 c 也被报成
        # persisted=False (跨 vault 误报)。vault 解析不出来时用 None 占位:
        # 那种情形下投影本来就没推进, 记录它只为让查询侧仍能如实说"没落盘"。
        self._unpersisted_concepts: set = set()
        logger.debug("ReviewService initialized")

    def _fsrs_library_ok(self) -> bool:
        """CARD-DEBT-8: 底层 py-fsrs 是否真在位。

        manager 存在只证明 fsrs_manager 模块可导入; py-fsrs 缺失时底层走
        _fallback_review（简单倍率调度）, algorithm 字段必须据此如实上报。
        getattr 缺省 True 是**显式裁决** (Codex round-1 M1): 生产 factory
        产出的 FSRSManager 恒有此属性, 缺属性的只有外来注入的替身/旧式
        wrapper——对它们 fail-open 保持 HEAD 行为, 改 fail-closed 会把
        既有 mock 注入套件全部打红; 缺属性情形已在 __init__ 一次性
        warning 出声。
        """
        return bool(getattr(self._fsrs_manager, "library_available", True))

    @staticmethod
    def _load_card_states() -> "_VaultScopedCardStates":
        """P0-2: Load card states from persistent JSON file on startup.

        CARD-G3-7: 非 FSRS 调度真相源 —— 载入的是投影/缓存快照。调度真相源是
        节点 frontmatter (见 _read_frontmatter_fsrs)。

        CARD-G3-5: 返回 vault 分桶容器 (``{vault_id: {concept_id: card}}``)。
        legacy 裸键按当前作用域**推定**归桶 (可能归错, 会告警; 作用域解析不出来
        时该部分不载入) —— 处置、反例与理由见
        ``_VaultScopedCardStates.from_persisted``。
        """
        try:
            if _CARD_STATES_FILE.exists():
                data = _CARD_STATES_FILE.read_text(encoding="utf-8")
                loaded = json.loads(data)
                if isinstance(loaded, dict):
                    states = _VaultScopedCardStates.from_persisted(loaded)
                    logger.info(
                        f"Loaded {states.total_cards()} FSRS card states "
                        f"across {len(states.to_nested())} vault(s) from {_CARD_STATES_FILE}"
                    )
                    return states
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to load FSRS card states: {e}")
        return _VaultScopedCardStates()

    def _dirty_key(self, concept_id: str) -> Tuple[Optional[str], str]:
        """`_unpersisted_concepts` 的元素身份 = ``(vault_id, concept_id)``。

        CARD-G3-5 (Codex r1 MEDIUM-1): 主状态有了 vault 维度, 这个附属状态就
        必须同维 —— 否则 vault A 的 concept ``c`` 写盘失败后, vault B 的同名
        ``c`` 命中缓存时也会被报成 ``persisted=False``(跨 vault 误报)。

        vault 解析不出来 ⇒ 用 ``None`` 占位: 那种情形投影本来就没推进, 记录它
        只为让查询侧仍能如实说"没落盘"。
        """
        vault_id = _card_states_vault(
            self._card_states, context="review_service._dirty_key"
        )
        return (vault_id, concept_id)

    def _is_unpersisted(self, concept_id: str) -> bool:
        """该 concept 在**当前作用域**下是否有未落盘的写 (见 :meth:`_dirty_key`)。"""
        return self._dirty_key(concept_id) in self._unpersisted_concepts

    async def _save_card_states(
        self, pending: Optional[Tuple[str, str]] = None
    ) -> bool:
        """P0-2: Persist card states to JSON file with concurrency protection.

        CARD-G3-7: 非 FSRS 调度真相源 —— 本方法写的是投影/缓存, 落盘成功
        **不代表**节点的调度状态被更新 (那要靠 vault 侧 quiz-answer ×
        fsrs_bridge 写 frontmatter)。调用方须把 persisted 与 truth_source
        两个信号分开转述, 禁止用前者冒充后者 (D0 修订 T1 / 禁假成功)。

        H2 fix: Uses asyncio.Lock to prevent concurrent writes and atomic
        write (temp file + rename) to prevent file corruption.

        Args:
            pending: (concept_id, card_data) 本次要写入的状态。
                CARD-D3 Codex HIGH-2: mutation 必须在锁内应用, 快照才必然
                包含本次状态 — 返回的 bool 才与本次响应的 card_data 绑定
                (原锁外 mutate 可被并发覆盖, True 证明不了本次成功)。

        Returns:
            True if the atomic write completed; False if it failed (logged).
            CARD-C4 Codex HIGH-1: 文件是唯一真实持久化通道, 失败必须可被
            调用方看见。CARD-D3: 评分/auto-create 两处调用点均已消费此值
            (原第三处是一条零调用方的死路径, 已随 CARD-G3-7-R2 退役)。
            失败时 pending concept 进 _unpersisted_
            concepts; 成功的全量快照治愈全部历史失败 (clear)。
            CARD-D3 Codex HIGH-3: except 含 ValueError — lone surrogate
            concept_id 的 UnicodeEncodeError 属 ValueError 族, 必须在
            持久化边界归一为 False, 不得冒泡进算法 fallback。
        """
        _missing = object()
        async with _card_states_lock:
            if pending is not None:
                prev = self._card_states.get(pending[0], _missing)
                dirty_key = self._dirty_key(pending[0])
                # CARD-G3-5 fail-closed: 作用域解析不出来 ⇒ **不推进投影**。
                # 判据是 try_set 的返回值 (内部走 require_read_group(None) 捕
                # VaultScopeUnresolved); 静默落进某个缺省桶 = 把配置断裂伪装成
                # 写入成功, 且会把一个 vault 的卡写进另一个 vault 的桶。
                # logger.error 由 _resolve_vault 记 (含 context)。
                if not _card_states_try_set(
                    self._card_states,
                    pending[0],
                    pending[1],
                    context="review_service._save_card_states",
                ):
                    self._unpersisted_concepts.add(dirty_key)
                    return False
            try:
                _CARD_STATES_FILE.parent.mkdir(parents=True, exist_ok=True)
                data = json.dumps(
                    _card_states_payload(self._card_states),
                    ensure_ascii=False,
                    indent=2,
                )
                # Atomic write: write to temp file then rename
                tmp_file = _CARD_STATES_FILE.with_suffix(".json.tmp")
                await asyncio.to_thread(tmp_file.write_text, data, "utf-8")
                await asyncio.to_thread(tmp_file.replace, _CARD_STATES_FILE)
                logger.debug(
                    f"Saved {_card_states_count(self._card_states)} FSRS card states "
                    f"to {_CARD_STATES_FILE}"
                )
                # 全量快照已落盘 → 所有历史写失败的 concept 同时被治愈
                self._unpersisted_concepts.clear()
                return True
            except (TypeError, ValueError) as e:
                # Codex 二轮残留 HIGH: 序列化/编码失败 = 本次 pending 数据
                # 有毒 (mutation 是唯一入口, 存量条目必然干净) — 必须回滚
                # 隔离, 否则毒 key 留在全量快照里拖垮后续所有 concept 的写。
                if pending is not None:
                    if prev is _missing:
                        self._card_states.pop(pending[0], None)
                    else:
                        self._card_states[pending[0]] = prev
                    self._unpersisted_concepts.add(dirty_key)
                logger.warning(f"Failed to save FSRS card states: {e}")
                return False
            except OSError as e:
                # 磁盘失败: 卡数据本身没问题, 保留内存 (重启即丢, dirty
                # 标记), 磁盘恢复后下一次成功全量写即治愈。
                if pending is not None:
                    self._unpersisted_concepts.add(dirty_key)
                logger.warning(f"Failed to save FSRS card states: {e}")
                return False

    def _extract_question_from_node(self, node: Dict[str, Any]) -> str:
        """
        Extract a question from a node's text content.

        If the text contains a colon, treat the part before as the topic
        and generate a question about it.

        Args:
            node: Node dict with 'text' field

        Returns:
            Generated question string
        """
        text = node.get("text", "")
        if "：" in text:
            # Chinese colon - extract topic
            topic = text.split("：")[0]
            return f"请解释{topic}的概念和含义？"
        elif ":" in text:
            # English colon - extract topic
            topic = text.split(":")[0]
            return f"请解释{topic}的概念和含义？"
        else:
            # No colon - ask about the whole text
            return f"请解释{text}的概念和含义？"

    async def generate_review_canvas(
        self, canvas_name: str, node_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a verification canvas asynchronously.

        Returns immediately with task_id, actual generation happens in background.

        Args:
            canvas_name: Source canvas name
            node_ids: Optional list of specific node IDs to include

        Returns:
            Dict with task_id and status

        Raises:
            CanvasNotFoundException: If source canvas doesn't exist
        """
        # Check if canvas exists
        if not await self.canvas_service.canvas_exists(canvas_name):
            raise CanvasNotFoundException(f"Canvas not found: {canvas_name}")

        # Create background task
        async def _generate():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
            return {
                "name": f"{canvas_name}-检验白板-{timestamp}",
                "source_canvas": canvas_name,
                "nodes": [],
                "edges": [],
            }

        task_id = await self.task_manager.create_task(
            "review_generation", _generate, metadata={"canvas_name": canvas_name}
        )

        self._task_canvas_map[task_id] = canvas_name

        return {
            "task_id": task_id,
            "status": "processing",
            "message": f"Generating verification canvas for {canvas_name}",
        }

    async def get_progress(self, task_id: str) -> ReviewProgress:
        """
        Get progress of a review generation task.

        Args:
            task_id: Task ID from generate_review_canvas

        Returns:
            ReviewProgress object

        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        task_info = self.task_manager.get_task_status(task_id)
        canvas_name = self._task_canvas_map.get(task_id, "unknown")

        # Map TaskStatus to ReviewStatus
        from app.services.background_task_manager import TaskStatus

        status_map = {
            TaskStatus.PENDING: ReviewStatus.PENDING,
            TaskStatus.RUNNING: ReviewStatus.RUNNING,
            TaskStatus.COMPLETED: ReviewStatus.COMPLETED,
            TaskStatus.FAILED: ReviewStatus.FAILED,
            TaskStatus.CANCELLED: ReviewStatus.CANCELLED,
        }

        return ReviewProgress(
            task_id=task_id,
            canvas_name=canvas_name,
            status=status_map.get(task_info.status, ReviewStatus.PENDING),
            progress=task_info.progress,
            error=task_info.error,
        )

    async def get_progress_dict(self, task_id: str) -> Dict[str, Any]:
        """
        Get progress as a dictionary.

        Args:
            task_id: Task ID

        Returns:
            Progress dictionary
        """
        progress = await self.get_progress(task_id)
        return progress.to_dict()

    async def cancel_generation(self, task_id: str) -> bool:
        """
        Cancel a running generation task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled, False if already completed
        """
        try:
            return await self.task_manager.cancel_task(task_id)
        except TaskNotFoundError:
            return False

    async def list_tasks(
        self, canvas_name: Optional[str] = None, status: Optional[ReviewStatus] = None
    ) -> List[ReviewProgress]:
        """
        List review generation tasks.

        Args:
            canvas_name: Optional filter by canvas name
            status: Optional filter by status

        Returns:
            List of ReviewProgress objects
        """
        from app.services.background_task_manager import TaskStatus

        # Get all review tasks from task manager
        tasks = self.task_manager.list_tasks(task_type="review_generation")

        results = []
        for task_info in tasks:
            task_canvas = self._task_canvas_map.get(task_info.task_id, "unknown")

            # Filter by canvas_name if specified
            if canvas_name and task_canvas != canvas_name:
                continue

            # Map TaskStatus to ReviewStatus
            status_map = {
                TaskStatus.PENDING: ReviewStatus.PENDING,
                TaskStatus.RUNNING: ReviewStatus.RUNNING,
                TaskStatus.COMPLETED: ReviewStatus.COMPLETED,
                TaskStatus.FAILED: ReviewStatus.FAILED,
                TaskStatus.CANCELLED: ReviewStatus.CANCELLED,
            }
            review_status = status_map.get(task_info.status, ReviewStatus.PENDING)

            # Filter by status if specified
            if status and review_status != status:
                continue

            results.append(
                ReviewProgress(
                    task_id=task_info.task_id,
                    canvas_name=task_canvas,
                    status=review_status,
                    progress=task_info.progress,
                    error=task_info.error,
                )
            )

        return results

    async def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """
        Get list of pending review items.

        Returns:
            List of review items with due dates and canvas info

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug("Getting pending reviews")
        # Stub implementation
        return []

    async def generate_verification_canvas(
        self,
        source_canvas_name: str,
        mode: str = "fresh",
        weak_weight: float = 0.7,
        mastered_weight: float = 0.3,
        include_colors: Optional[List[str]] = None,
        question_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a verification canvas with mode support.

        ✅ Verified from Story 24.1 Dev Notes (lines 180-220)

        Args:
            source_canvas_name: Name of source canvas to create verification from
            mode: "fresh" for blind test, "targeted" for weakness-focused
            weak_weight: Weight for weak concepts (targeted mode only)
            mastered_weight: Weight for mastered concepts (targeted mode only)
            include_colors: Optional color filter for node selection
            question_count: Optional limit on question count

        Returns:
            Generated verification canvas data with mode metadata

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: Story 24.1 - Mode Support Implementation]
        """
        logger.debug(
            f"Generating verification canvas from: {source_canvas_name} "
            f"(mode={mode}, weak_weight={weak_weight}, mastered_weight={mastered_weight})"
        )

        # Get all eligible concepts from canvas
        # Mastery-aware: color filter kept as fallback; mastery engine provides
        # more nuanced filtering via effective_proficiency < 0.70
        if include_colors is None:
            include_colors = ["3", "4"]  # Default fallback: purple and red

        # Load canvas data to get nodes
        canvas_data = await self.canvas_service.get_canvas(source_canvas_name)
        all_nodes = canvas_data.get("nodes", [])

        # Filter by colors (baseline)
        eligible_nodes = [
            node
            for node in all_nodes
            if node.get("type") == "text" and node.get("color") in include_colors
        ]

        # === Mastery enrichment (Phase 1.5) ===
        # Expand eligible_nodes with mastery-weak concepts not caught by color filter
        mastery_lookup: dict = {}  # node_text[:50] -> effective_proficiency
        enrichment_available = (
            False  # G-SILENT-001: signal whether enrichment succeeded
        )
        try:
            from app.clients.neo4j_client import get_neo4j_client
            from app.services.mastery_engine import get_mastery_engine
            from app.services.mastery_store import MasteryStore

            m_engine = get_mastery_engine()  # Uses fusion-enabled singleton
            m_store = MasteryStore(get_neo4j_client())
            from app.config import DEFAULT_GROUP_ID
            from app.core.subject_config import (
                canonical_group_id,
                get_current_subject_id,
            )

            # wave-5 Stage B P0 (2026-05-11): prefer ContextVar so the review
            # candidates are pulled from the originating request's vault.
            _ctx_value = get_current_subject_id()
            _effective_group_id = (
                canonical_group_id(_ctx_value) if _ctx_value else DEFAULT_GROUP_ID
            )

            all_mastery = await m_store.get_all_concepts(group_id=_effective_group_id)
            review_candidates = m_engine.get_review_candidates(all_mastery)

            # Build name -> proficiency lookup for question_generator
            mastery_lookup = {
                c.name: m_engine.effective_proficiency(c) for c in all_mastery
            }

            # Add mastery-weak concepts that aren't already in eligible_nodes
            eligible_ids = {n.get("id") for n in eligible_nodes}
            candidate_names = {c.name for c in review_candidates}
            for node in all_nodes:
                if (
                    node.get("type") == "text"
                    and node.get("id") not in eligible_ids
                    and (node.get("text", "")[:50].strip() in candidate_names)
                ):
                    eligible_nodes.append(node)
                    eligible_ids.add(node.get("id"))

            enrichment_available = True
            logger.info(
                f"Mastery enrichment: {len(review_candidates)} weak concepts, "
                f"{len(eligible_nodes)} total eligible after enrichment"
            )
        except (
            ImportError,
            RuntimeError,
            ConnectionError,
            ValueError,
            TypeError,
            AttributeError,
        ) as e:
            logger.warning(f"Mastery enrichment unavailable (degraded mode): {e}")

        weak_concepts_data = []
        weight_config = {
            "weak_weight": weak_weight,
            "mastered_weight": mastered_weight,
            "applied": False,
            "enrichment_available": enrichment_available,
        }
        fallback_used = False  # AC2 of Story 24.6: Track fallback usage

        if mode == "targeted":
            # Query Graphiti for review history (Story 24.3)
            review_history = await self._query_review_history_from_memory(
                source_canvas_name
            )

            # AC2: Detect fallback scenario (Graphiti unavailable or no history)
            if not review_history:
                fallback_used = True
                logger.warning(
                    f"Targeted mode fallback: No Graphiti history for {source_canvas_name}, "
                    "using equal probability selection for all eligible concepts"
                )

            # Prepare concepts list from eligible nodes
            concepts = [
                {"id": node.get("id", ""), "name": node.get("text", "")}
                for node in eligible_nodes
            ]

            # Calculate weakness scores using WeightCalculator (Story 24.3)
            calculator = WeightCalculator()
            weight_data = await calculator.calculate_weakness_scores(
                concepts, review_history
            )

            # Apply weighted selection (Story 24.3)
            target_count = question_count or len(eligible_nodes)
            selected_weight_data = await self._apply_weighted_selection(
                weight_data, target_count, weak_weight, mastered_weight
            )

            # Convert back to node objects for canvas generation
            selected_ids = {c.concept_id for c in selected_weight_data}
            selected_concepts = [
                node for node in eligible_nodes if node.get("id", "") in selected_ids
            ]

            # Prepare weak_concepts for response (AC5)
            weak_concepts_data = [
                {
                    "concept_name": c.concept_name,
                    "weakness_score": c.weakness_score,
                    "failure_count": c.failure_count,
                    "avg_rating": c.avg_rating,
                }
                for c in weight_data
                if c.category == "weak"
            ]

            weight_config["applied"] = True

            logger.info(
                f"Targeted mode: selected {len(selected_concepts)} concepts using weighted algorithm "
                f"({sum(1 for c in selected_weight_data if c.category == 'weak')} weak, "
                f"{sum(1 for c in selected_weight_data if c.category == 'mastered')} mastered)"
            )
        else:
            # Fresh mode: equal probability selection from all eligible nodes
            selected_concepts = eligible_nodes
            logger.info(f"Fresh mode: selected {len(selected_concepts)} concepts")

        # Apply question_count limit if specified
        if question_count and len(selected_concepts) > question_count:
            selected_concepts = random.sample(selected_concepts, question_count)

        # Generate verification canvas (simplified stub - actual generation logic elsewhere)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        review_canvas_name = f"{source_canvas_name}-检验白板-{timestamp}"

        # Store relationship in Graphiti
        await self._store_review_relationship(
            source_canvas_name, review_canvas_name, mode
        )

        result = {
            "review_canvas_name": review_canvas_name,
            "source_canvas_name": source_canvas_name,
            "question_count": len(selected_concepts),
            "mode_used": mode,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "weak_concepts": weak_concepts_data,  # AC5: Enhanced response
            "weight_config": weight_config,  # AC5: Weight configuration
            "fallback_used": fallback_used,  # AC2 of Story 24.6: Indicate if fallback was triggered
        }

        log_decision(
            function="generate_verification_canvas",
            input_summary={
                "source_canvas": source_canvas_name,
                "mode": mode,
                "eligible_nodes": len(eligible_nodes),
            },
            output=f"selected {len(selected_concepts)} nodes -> {review_canvas_name}",
            reason=f"mode={mode}, fallback_used={fallback_used}, "
            f"weak_weight={weak_weight}, mastered_weight={mastered_weight}",
        )

        logger.info(
            f"Generated verification canvas: {review_canvas_name} "
            f"with {len(selected_concepts)} questions (mode={mode})"
        )

        return result

    async def schedule_review(
        self,
        canvas_name: str,
        concept_id: str = "",
        trigger_point: int = 1,
        card_state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a review using FSRS algorithm (Story 32.2).

        Story 32.2 AC-32.2.3: FSRS calculates dynamic intervals based on
        card state (stability, difficulty) rather than fixed Ebbinghaus intervals.

        Args:
            canvas_name: Canvas to schedule review for
            concept_id: Concept identifier for card tracking
            trigger_point: Legacy parameter (maintained for backward compatibility)
            card_state: Optional serialized FSRS card JSON from previous review

        Returns:
            Review schedule with FSRS-calculated due date and card state

        Migration Path (AC-32.2.5):
        - If card_state is None: Creates new FSRS card (first review)
        - If card_state exists: Deserializes and uses existing card state
        - Existing Ebbinghaus records: Treated as new cards on first FSRS review

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: Story 32.2 - FSRS Integration]
        """
        logger.debug(f"Scheduling FSRS review for {canvas_name}/{concept_id}")

        # Story 32.2: Use FSRS for scheduling if available
        if self._fsrs_manager is not None:
            try:
                # Load or create card (AC-32.2.4 backward compatibility)
                if card_state:
                    card = self._fsrs_manager.deserialize_card(card_state)
                    logger.debug(f"Loaded existing FSRS card for {concept_id}")
                else:
                    # Check in-memory cache
                    cached_state = self._card_states.get(concept_id)
                    if cached_state:
                        card = self._fsrs_manager.deserialize_card(cached_state)
                        logger.debug(f"Loaded cached FSRS card for {concept_id}")
                    else:
                        # New card - immediately due for first review
                        card = self._fsrs_manager.create_card()
                        logger.info(f"Created new FSRS card for {concept_id}")

                # Get due date from card
                due_date = self._fsrs_manager.get_due_date(card)
                retrievability = self._fsrs_manager.get_retrievability(card)

                # Calculate interval in days from now
                if due_date:
                    interval_days = max(
                        0, (due_date - datetime.now(due_date.tzinfo)).days
                    )
                else:
                    interval_days = 0  # New card, due immediately

                log_decision(
                    function="schedule_review",
                    input_summary={
                        "canvas_name": canvas_name,
                        "concept_id": concept_id,
                        "card_state_provided": card_state is not None,
                    },
                    output=f"interval={interval_days}d, R={retrievability:.3f}",
                    # New cards: stability/difficulty are None — formatting them
                    # with ':.2f' raised TypeError, silently degrading every new
                    # concept to the Ebbinghaus fallback via the except below.
                    # CARD-DEBT-8: 底层 fallback 激活时决策日志也不得谎报 FSRS-4.5。
                    reason=f"{'FSRS-4.5' if self._fsrs_library_ok() else 'fallback'} scheduling, "
                    f"stability={_fmt_optional_2f(getattr(card, 'stability', None))}, "
                    f"difficulty={_fmt_optional_2f(getattr(card, 'difficulty', None))}",
                )

                # CARD-DEBT-8: manager 在位 != py-fsrs 在位。底层 fallback
                # 激活时如实上报 fsrs-fallback-scheduler + degraded_reason
                # （加性, 沿 CARD-D3 先例; 真实库在位响应逐键与此前相同）。
                lib_ok = self._fsrs_library_ok()
                response = {
                    "canvas_name": canvas_name,
                    "concept_id": concept_id,
                    "scheduled_date": due_date.isoformat()
                    if due_date
                    else (
                        datetime.now(timezone.utc) + timedelta(days=interval_days)
                    ).isoformat(),
                    "interval_days": interval_days,
                    "retrievability": retrievability,
                    # Display mirror of the card: new cards carry None
                    # stability/difficulty — surface the Story 38.3 AC-4
                    # default-card contract (1.0/5.0) so consumers building
                    # FSRSStateResponse (requires float, difficulty ge=1)
                    # never hit ValidationError. card_data below keeps the
                    # authoritative null for scheduler roundtrip.
                    "fsrs_state": {
                        "stability": getattr(card, "stability", None)
                        if getattr(card, "stability", None) is not None
                        else 1.0,
                        "difficulty": getattr(card, "difficulty", None)
                        if getattr(card, "difficulty", None) is not None
                        else 5.0,
                        "state": int(getattr(card, "state", 0).value)
                        if hasattr(getattr(card, "state", 0), "value")
                        else int(getattr(card, "state", 0)),
                        "reps": getattr(card, "reps", 0),
                        "lapses": getattr(card, "lapses", 0),
                    },
                    "card_data": self._fsrs_manager.serialize_card(card),
                    "status": "scheduled",
                    "algorithm": "fsrs-4.5" if lib_ok else "fsrs-fallback-scheduler",
                }
                if not lib_ok:
                    response["degraded_reason"] = "fsrs_library_missing"
                return response

            # INTENTIONAL: Third-party py-fsrs library may raise unpredictable errors; fallback to Ebbinghaus
            except Exception as e:
                logger.error(f"FSRS scheduling failed, using fallback: {e}")
                # Fall through to fallback

        # Fallback: Legacy Ebbinghaus fixed intervals
        logger.warning("Using fallback Ebbinghaus scheduling (FSRS unavailable)")
        ebbinghaus_intervals = {1: 1, 2: 7, 3: 30, 4: 90}
        interval = ebbinghaus_intervals.get(trigger_point, 1)

        # Story 32.9 AC-1: scheduled_date must be a future date, not "now"
        scheduled_date = datetime.now(timezone.utc) + timedelta(days=interval)
        return {
            "canvas_name": canvas_name,
            "concept_id": concept_id,
            "trigger_point": trigger_point,
            "scheduled_date": scheduled_date.isoformat(),
            "interval_days": interval,
            "status": "scheduled",
            "algorithm": "ebbinghaus-fallback",
        }

    async def record_review_result(
        self,
        canvas_name: str,
        concept_id: str = "",
        score: Optional[float] = None,
        rating: Optional[int] = None,
        card_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record the result of a review session using FSRS algorithm (Story 32.2).

        Story 32.2 AC-32.2.2: Accepts FSRS ratings (1=Again, 2=Hard, 3=Good, 4=Easy)
        Story 32.2 AC-32.2.3: Returns dynamically calculated next review date
        Story 32.2 AC-32.2.4: Backward compatible with score-based inputs (0-100)

        Args:
            canvas_name: Canvas that was reviewed
            concept_id: Concept identifier for card tracking
            score: Legacy score (0-100), converted to rating if rating not provided
            rating: FSRS rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            card_state: Optional serialized FSRS card JSON from previous review
            details: Optional detailed scoring breakdown

        Returns:
            Recorded review result with FSRS state:
            - next_review: ISO timestamp of next scheduled review
            - interval_days: Days until next review
            - fsrs_state: {stability, difficulty, state, reps, lapses}
            - card_data: Serialized card for persistence

        Rating Conversion (AC-32.2.4 backward compatibility):
            Score 0-39:   Again (1) - forgot
            Score 40-59:  Hard (2) - serious difficulty
            Score 60-84:  Good (3) - remembered with hesitation
            Score 85-100: Easy (4) - easily recalled

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: Story 32.2 - FSRS Integration]
        """
        logger.debug(f"Recording FSRS review result for {canvas_name}/{concept_id}")

        # Story 32.2 AC-32.2.2/AC-32.2.4: Convert score to rating if needed
        if rating is None and score is not None:
            if get_rating_from_score is not None:
                rating = get_rating_from_score(score)
                logger.debug(f"Converted score {score} to FSRS rating {rating}")
            else:
                # Fallback conversion
                if score < 40:
                    rating = 1  # Again
                elif score < 60:
                    rating = 2  # Hard
                elif score < 85:
                    rating = 3  # Good
                else:
                    rating = 4  # Easy
        elif rating is None:
            rating = 3  # Default to Good if no input provided

        # P0-3: Validate rating - handle non-integer types (e.g. "abc", 5.7)
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            logger.warning(f"Invalid rating value '{rating}', defaulting to 3")
            rating = 3
        rating = max(1, min(4, rating))

        # Story 32.2: Use FSRS for recording if available
        if self._fsrs_manager is not None:
            try:
                # Load or create card (AC-32.2.4 backward compatibility)
                if card_state:
                    card = self._fsrs_manager.deserialize_card(card_state)
                    logger.debug(f"Loaded existing FSRS card for {concept_id}")
                else:
                    # Check in-memory cache
                    cached_state = self._card_states.get(concept_id)
                    if cached_state:
                        card = self._fsrs_manager.deserialize_card(cached_state)
                        logger.debug(f"Loaded cached FSRS card for {concept_id}")
                    else:
                        # New card - existing Ebbinghaus records treated as first FSRS review
                        card = self._fsrs_manager.create_card()
                        logger.info(
                            f"Created new FSRS card for {concept_id} (migration from Ebbinghaus)"
                        )

                # Story 32.2 AC-32.2.3: Review card with FSRS algorithm
                updated_card, review_log = self._fsrs_manager.review_card(card, rating)

                # Get next due date (dynamically calculated by FSRS)
                due_date = self._fsrs_manager.get_due_date(updated_card)

                # Calculate interval in days
                if due_date:
                    now = datetime.now(timezone.utc)
                    interval_days = max(0, (due_date - now).days)
                else:
                    interval_days = 1

                # Serialize card for persistence
                card_data = self._fsrs_manager.serialize_card(updated_card)

                # Store in memory cache + persist to file (P0-2)
                # CARD-D3: 消费 _save_card_states 返回值 (Codex HIGH-1 的
                # 失败信号在此前被丢弃) — 文件是唯一真实持久化通道, 写失败
                # 意味着"仅内存暂存、重启即丢", 必须在返回值里如实标注。
                #
                # CARD-G3-7 裁定 ① = 改造: 这次写的是**非 FSRS 调度真相源**的
                # 投影/缓存。写不进真相源 (frontmatter) 这件事必须让调用方看见,
                # 但**不覆盖** next_review —— 它是本次评分算出的新排期, 而此刻
                # frontmatter 里还是旧 due (vault 侧 quiz-answer × fsrs_bridge
                # 的写是另一条链、另一时刻)。用旧值覆盖新排期不是诚实, 是用 T1
                # 的名义制造错误。诚实义务由 truth_source / degraded_reason 承担。
                if concept_id:
                    # Codex HIGH-2: mutation 随 pending 进锁内, 不在此处赋值
                    card_state_persisted = await self._save_card_states(
                        pending=(concept_id, card_data)
                    )
                    degraded_reason = (
                        None if card_state_persisted else "card_state_write_failed"
                    )
                else:
                    # M3 fix: Warn when concept_id is empty — card state will not be persisted
                    logger.warning(
                        f"Empty concept_id for canvas '{canvas_name}' — "
                        f"FSRS card state computed but NOT persisted"
                    )
                    card_state_persisted = False
                    degraded_reason = "empty_concept_id_not_persisted"

                # CARD-DEBT-8: 底层 py-fsrs 缺失时如实上报, 不再谎报 fsrs-4.5。
                # fsrs_library_missing 与 CARD-D3 的持久化降级原因并存时
                # 逗号拼接——两个降级都真实, 谁也不冲掉谁。
                lib_ok = self._fsrs_library_ok()
                if not lib_ok:
                    degraded_reason = (
                        "fsrs_library_missing"
                        if degraded_reason is None
                        else f"fsrs_library_missing,{degraded_reason}"
                    )

                # CARD-G3-7: 真相源状态 —— 本次结果只进投影缓存, 真相源须由
                # vault 侧写链 (quiz-answer × fsrs_bridge) 更新。三种情形都要
                # 出声, 沿用上面的逗号拼接先例 (多个降级都真实, 谁也不冲掉谁):
                #   - due 可比且不同   → truth_source_divergence
                #   - 字段在但形态不合规 → truth_source_unparsable
                #   - 文件读不出来      → truth_source_unreadable
                # ⚠️ Codex r1 MEDIUM-4: 初版只在 `due is not None and due_date is
                # not None` 时比较, 于是"非法但非空的 fsrs_due"和"文件不可读"
                # 都拿到 degraded_reason=None —— 异常信号被整条吞掉。
                fm_truth = _read_frontmatter_fsrs(concept_id) if concept_id else None
                _g37_put_reason = None
                if fm_truth and fm_truth["governed"]:
                    if fm_truth["reason"] in (
                        "node_file_unreadable",
                        "node_lookup_unreadable",
                    ):
                        _g37_put_reason = "truth_source_unreadable"
                    elif fm_truth["due"] is None:
                        _g37_put_reason = "truth_source_unparsable"
                    elif fm_truth["due"] != _whole_second_utc(due_date):
                        # 整秒归一后比较, 见 _whole_second_utc 的口径说明。
                        # due_date 为 None 时 _whole_second_utc 返 None ≠ 真相源
                        # 的 due ⇒ 同样判分歧 (初版在此处静默跳过)。
                        _g37_put_reason = "truth_source_divergence"
                # 收窄条件写成 `fm_truth is not None and ...` 而不是只判
                # _g37_put_reason —— 后者对类型检查器不可见 (reason 只在
                # `if fm_truth` 内被赋值, 但那个不变式表达不出来), pyright
                # 会在下面的下标访问报 reportOptionalSubscript。
                # Codex r2 MEDIUM-3 的基线对照抓到的**唯一一条本卡真新增**。
                if fm_truth is not None and _g37_put_reason is not None:
                    logger.warning(
                        "CARD-G3-7 %s: concept=%s frontmatter_due=%s computed_due=%s — 本次结果只进投影缓存",
                        _g37_put_reason,
                        concept_id,
                        fm_truth["fsrs_due"],
                        due_date.isoformat() if due_date else None,
                    )
                    degraded_reason = (
                        _g37_put_reason if degraded_reason is None else f"{degraded_reason},{_g37_put_reason}"
                    )

                # Extract state value safely
                state_val = getattr(updated_card, "state", 0)
                if hasattr(state_val, "value"):
                    state_int = int(state_val.value)
                elif hasattr(state_val, "__int__"):
                    state_int = int(state_val)
                else:
                    state_int = 0

                return {
                    "canvas_name": canvas_name,
                    "concept_id": concept_id,
                    "rating": rating,
                    "score": score,  # Preserve original score for logging
                    "next_review": due_date.isoformat()
                    if due_date
                    else (datetime.now(timezone.utc) + timedelta(days=interval_days)).isoformat(),
                    "interval_days": interval_days,
                    "fsrs_state": {
                        "stability": float(getattr(updated_card, "stability", 0.0)),
                        "difficulty": float(getattr(updated_card, "difficulty", 0.0)),
                        "state": state_int,
                        "reps": int(getattr(updated_card, "reps", 0)),
                        "lapses": int(getattr(updated_card, "lapses", 0)),
                    },
                    "card_data": card_data,
                    "details": details or {},
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                    "status": "recorded",
                    "algorithm": "fsrs-4.5" if lib_ok else "fsrs-fallback-scheduler",
                    # CARD-D3: 持久化诚实信号 (评分计算成功 != 状态已落盘)
                    # CARD-G3-7: card_state_persisted=True 只说明**投影缓存**落了
                    # 盘, 不代表节点的调度真相源 (frontmatter) 被更新 —— 两个信号
                    # 不得互相冒充 (禁假成功)。真相源分歧经 degraded_reason 的
                    # truth_source_divergence 透出。
                    #
                    # ⚠️ 本 dict 的**键集合**被 tests/regression/
                    # test_debt8_fsrs_fallback_honest.py:185-189 精确锁死
                    # (CARD-DEBT-8 Codex round-1 M3 用它杀「夹带新键」变异),
                    # 故 CARD-G3-7 不在此新增 truth_source 键。该字段对本端点
                    # 恒为 "projection-cache" (裁定表 ①: 此处只写投影, 从不写
                    # 真相源), 是常量而非计算结果, 由 API 层直接给出 ——
                    # 见 app/api/v1/endpoints/review.py::record_review_result。
                    "card_state_persisted": card_state_persisted,
                    "degraded_reason": degraded_reason,
                }

            # INTENTIONAL: Third-party py-fsrs library may raise unpredictable errors; fallback to legacy
            except Exception as e:
                logger.error(f"FSRS recording failed, using fallback: {e}")
                # Fall through to fallback

        # Fallback: Legacy Ebbinghaus fixed intervals
        logger.warning("Using fallback Ebbinghaus recording (FSRS unavailable)")

        # Calculate interval based on score (legacy behavior)
        if score is not None:
            if score >= 85:
                interval = 30
            elif score >= 60:
                interval = 7
            elif score >= 40:
                interval = 3
            else:
                interval = 1
        else:
            # Map rating to interval
            rating_intervals = {1: 1, 2: 3, 3: 7, 4: 30}
            interval = rating_intervals.get(rating, 1)

        # Story 32.9 AC-1: next_review must be a future date, not "now"
        now_utc = datetime.now(timezone.utc)
        next_review_date = now_utc + timedelta(days=interval)
        return {
            "canvas_name": canvas_name,
            "concept_id": concept_id,
            "rating": rating,
            "score": score,
            "next_review": next_review_date.isoformat(),
            "interval_days": interval,
            "details": details or {},
            "recorded_at": now_utc.isoformat(),
            "status": "recorded",
            "algorithm": "ebbinghaus-fallback",
            # CARD-D3: fallback 分支没有 FSRS 卡状态可持久化 → 不适用 (None)
            "card_state_persisted": None,
            "degraded_reason": None,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Story 34.4: Review History with Pagination
    # [Source: specs/api/review-api.openapi.yml#L185-216]
    # [Source: docs/stories/34.4.story.md]
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_history(
        self,
        days: int = 7,
        canvas_path: Optional[str] = None,
        concept_name: Optional[str] = None,
        limit: Optional[int] = 5,
    ) -> Dict[str, Any]:
        """
        Get review history with pagination support.

        Story 34.4 AC1: Default limit=5 records.
        Story 34.4 AC2: limit=None returns all records.
        Story 34.4 AC3: Supports filtering by canvas_path and concept_name.

        Args:
            days: Number of days to look back (7, 30, 90)
            canvas_path: Filter by canvas file path
            concept_name: Filter by concept name
            limit: Maximum records (None = all, default=5)

        Returns:
            Dict with records, statistics, and has_more flag
        """
        from collections import defaultdict

        # Calculate date range
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)

        # Get history from storage/graphiti
        all_records: List[Dict[str, Any]] = []

        # Try to get history from Graphiti first
        if self.graphiti_client:
            try:
                from app.clients.graphiti_client import get_learning_memory_client

                memory_client = get_learning_memory_client()
                await memory_client.initialize()

                # Query all learning history within date range
                raw_history = await memory_client.get_learning_history(
                    canvas_name=canvas_path or "",
                    limit=1000,  # Get all records for filtering
                )

                # Filter and convert records
                for memory in raw_history:
                    timestamp_str = memory.get("timestamp", "")
                    try:
                        if isinstance(timestamp_str, str):
                            record_date = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            ).date()
                        else:
                            record_date = (
                                timestamp_str.date()
                                if hasattr(timestamp_str, "date")
                                else end_date
                            )
                    except (ValueError, AttributeError):
                        continue

                    # Skip records outside date range
                    if record_date < start_date or record_date > end_date:
                        continue

                    # Filter by canvas_path if specified
                    record_canvas = memory.get(
                        "canvas_name", memory.get("canvas_path", "")
                    )
                    if canvas_path and canvas_path not in record_canvas:
                        continue

                    # Filter by concept_name if specified
                    record_concept = memory.get(
                        "concept", memory.get("concept_name", "")
                    )
                    if concept_name and concept_name not in record_concept:
                        continue

                    # Convert score (0-100) to rating (1-4)
                    score = memory.get("score", 60)
                    if score >= 85:
                        rating = 4
                    elif score >= 60:
                        rating = 3
                    elif score >= 40:
                        rating = 2
                    else:
                        rating = 1

                    all_records.append(
                        {
                            "concept_id": memory.get(
                                "concept_id", memory.get("id", "")
                            ),
                            "concept_name": record_concept,
                            "canvas_path": record_canvas,
                            "rating": rating,
                            "review_time": timestamp_str,
                            "date": record_date.isoformat(),
                        }
                    )

                logger.info(f"Found {len(all_records)} history records from Graphiti")

            except (
                ConnectionError,
                TimeoutError,
                ValueError,
                KeyError,
                TypeError,
                AttributeError,
            ) as e:
                logger.error(f"Error querying history from Graphiti: {e}")

        # If no records from Graphiti, try FSRS card states
        if not all_records and self._card_states:
            for key, card_data in self._card_states.items():
                try:
                    # Handle both dict and serialized JSON string formats
                    # (FSRS serialize_card() stores strings, _load_card_states restores as-is)
                    if isinstance(card_data, str):
                        try:
                            card_data = json.loads(card_data)
                        except (json.JSONDecodeError, ValueError):
                            continue
                    if not isinstance(card_data, dict):
                        continue

                    last_review = card_data.get("last_review")
                    if not last_review:
                        continue

                    if isinstance(last_review, str):
                        record_date = datetime.fromisoformat(
                            last_review.replace("Z", "+00:00")
                        ).date()
                    else:
                        record_date = (
                            last_review.date()
                            if hasattr(last_review, "date")
                            else end_date
                        )

                    if record_date < start_date or record_date > end_date:
                        continue

                    parts = key.split(":")
                    record_canvas = parts[0] if len(parts) > 0 else ""
                    record_concept = parts[1] if len(parts) > 1 else key

                    if canvas_path and canvas_path not in record_canvas:
                        continue
                    if concept_name and concept_name not in record_concept:
                        continue

                    all_records.append(
                        {
                            "concept_id": key,
                            "concept_name": record_concept,
                            "canvas_path": record_canvas,
                            "rating": card_data.get("rating", 3),
                            "review_time": last_review,
                            "date": record_date.isoformat(),
                        }
                    )
                except (ValueError, AttributeError):
                    continue

        # Sort by review_time descending (newest first)
        all_records.sort(key=lambda x: x.get("review_time", ""), reverse=True)

        # Determine if there are more records than limit
        total_count = len(all_records)
        # Code Review H3 Fix: Cap None to MAX_HISTORY_RECORDS to enforce service-level protection
        effective_limit = limit if limit is not None else MAX_HISTORY_RECORDS
        has_more = total_count > effective_limit

        # Code Review H3 Fix: Calculate streak from ALL records BEFORE truncation
        # (streak must reflect true consecutive days, not limited view)
        all_dates: set = set()
        for record in all_records:
            date_key = record.get("date", "")
            if date_key:
                all_dates.add(date_key)

        streak_days = 0
        check_date = end_date
        while check_date >= start_date:
            if check_date.isoformat() in all_dates:
                streak_days += 1
                check_date -= timedelta(days=1)
            else:
                break

        # Apply limit after streak calculation
        limited_records = all_records[:effective_limit]

        # Group limited records by date for response
        records_by_date: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for record in limited_records:
            date_key = record.get("date", "")
            if date_key:
                records_by_date[date_key].append(record)

        # Build daily records list
        daily_records = []
        for date_key in sorted(records_by_date.keys(), reverse=True):
            daily_records.append(
                {"date": date_key, "reviews": records_by_date[date_key]}
            )

        # Story 34.12 AC3: Calculate retention_rate from rating data
        # retention_rate = count(rating >= 3) / count(total records with rating)
        rated_records = [r for r in all_records if r.get("rating") is not None]
        if rated_records:
            good_count = sum(1 for r in rated_records if r.get("rating", 0) >= 3)
            retention_rate = round(good_count / len(rated_records), 4)
        else:
            retention_rate = None

        return {
            "records": daily_records,
            "total_count": total_count,
            "has_more": has_more,
            "streak_days": streak_days,
            "retention_rate": retention_rate,
        }

    async def _query_weak_concepts_from_memory(
        self, canvas_name: str
    ) -> List[Dict[str, Any]]:
        """
        Query historical weak concepts from LearningMemoryClient (JSON storage).

        Renamed from _query_weak_concepts_from_graphiti: uses LearningMemoryClient
        (JSON-backed), not graphiti-core. See Task 10 fake naming cleanup.

        ✅ Verified from Story 24.1 Dev Notes (lines 224-239)

        Args:
            canvas_name: Canvas file name

        Returns:
            List of weak concept dicts with scores and review counts
        """
        if not self.graphiti_client:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "query_weak_concepts",
                "graphiti_client",
                "[]",
            )
            return []

        try:
            # Since we're using GraphitiEdgeClient with JSON storage,
            # we'll query from the learning memories instead
            from app.clients.graphiti_client import get_learning_memory_client

            memory_client = get_learning_memory_client()
            await memory_client.initialize()

            # Get learning history for this canvas
            history = await memory_client.get_learning_history(canvas_name, limit=50)

            # Calculate average scores per concept
            concept_scores: Dict[str, List[float]] = {}
            for memory in history:
                concept = memory.get("concept", "")
                score = memory.get("score")
                if concept and score is not None:
                    if concept not in concept_scores:
                        concept_scores[concept] = []
                    concept_scores[concept].append(score)

            # Build weak concepts list (avg score < 24 out of 40)
            weak_concepts = []
            for concept, scores in concept_scores.items():
                avg_score = sum(scores) / len(scores) if scores else 0
                if avg_score < 24:  # < 60% threshold
                    weak_concepts.append(
                        {
                            "concept_name": concept,
                            "avg_score": avg_score,
                            "review_count": len(scores),
                        }
                    )

            # Sort by avg_score ascending (weakest first)
            weak_concepts.sort(key=lambda x: (x["avg_score"], -x["review_count"]))

            logger.info(f"Found {len(weak_concepts)} weak concepts for {canvas_name}")
            return weak_concepts

        except (
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
        ) as e:
            logger.error(f"Error querying weak concepts: {e}")
            return []

    async def _store_review_relationship(
        self, original_canvas: str, review_canvas: str, mode: str
    ) -> None:
        """
        Store GENERATED_FROM relationship in Graphiti.

        ✅ Verified from Story 24.1 Dev Notes (lines 241-256)

        Args:
            original_canvas: Original canvas name
            review_canvas: Review canvas name
            mode: Mode used (fresh/targeted)
        """
        if not self.graphiti_client:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "store_review_relationship",
                "graphiti_client",
                "skip",
            )
            return

        try:
            from app.clients.graphiti_client import EdgeRelationship

            relationship = EdgeRelationship(
                canvas_name=original_canvas,
                from_node=review_canvas,
                to_node=original_canvas,
                label=f"GENERATED_FROM_{mode.upper()}",
                edge_id=None,
            )

            await self.graphiti_client.add_edge_relationship(relationship)

            # Also add episode for tracking
            await self.graphiti_client.add_episode_for_edge(
                canvas_name=original_canvas,
                edge={
                    "fromNode": review_canvas,
                    "toNode": original_canvas,
                    "label": f"generated in {mode} mode",
                    "id": f"review_{mode}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                },
            )

            logger.info(
                f"Stored review relationship: {review_canvas} --[{mode}]--> {original_canvas}"
            )

        except (
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
        ) as e:
            logger.warning(f"Failed to store review relationship: {e}")

    async def _apply_weighted_selection(
        self,
        weight_data: List[ConceptWeightData],
        question_count: int,
        weak_weight: float = 0.7,
        mastered_weight: float = 0.3,
    ) -> List[ConceptWeightData]:
        """
        Apply weighted selection to concept list.

        ✅ Verified from Story 24.3 Dev Notes (lines 345-401)

        AC2: Configurable Weight Distribution
        AC3: Weighted Concept Selection

        Args:
            weight_data: Calculated weight data for all concepts
            question_count: Number of questions to select
            weak_weight: Weight for weak concepts (default 0.7)
            mastered_weight: Weight for mastered concepts (default 0.3)

        Returns:
            Selected concepts based on weight distribution

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        # AC2: Validate weights
        if abs(weak_weight + mastered_weight - 1.0) > 0.01:
            raise ValueError("weak_weight + mastered_weight must equal 1.0")

        # AC3: Categorize concepts
        weak = [c for c in weight_data if c.category == "weak"]
        mastered = [c for c in weight_data if c.category == "mastered"]
        borderline = [c for c in weight_data if c.category == "borderline"]

        # Calculate target counts
        weak_count = int(question_count * weak_weight)
        mastered_count = int(question_count * mastered_weight)
        borderline_count = question_count - weak_count - mastered_count

        selected = []

        # Select from each category (with fallback if insufficient)
        if weak:
            selected.extend(self._weighted_sample(weak, min(weak_count, len(weak))))
        if mastered:
            selected.extend(
                self._weighted_sample(mastered, min(mastered_count, len(mastered)))
            )
        if borderline:
            selected.extend(
                self._weighted_sample(
                    borderline, min(borderline_count, len(borderline))
                )
            )

        # Fill remaining from any category
        remaining = question_count - len(selected)
        if remaining > 0:
            all_remaining = [c for c in weight_data if c not in selected]
            selected.extend(
                self._weighted_sample(all_remaining, min(remaining, len(all_remaining)))
            )

        logger.info(
            f"Weighted selection complete: {len(selected)} concepts selected "
            f"(target: {question_count}, weights: {weak_weight:.1%} weak / {mastered_weight:.1%} mastered)"
        )

        return selected

    def _weighted_sample(
        self, concepts: List[ConceptWeightData], count: int
    ) -> List[ConceptWeightData]:
        """
        Sample concepts with weights based on weakness_score.

        ✅ Verified from Story 24.3 Dev Notes (lines 403-445)

        AC3: Selection probability follows weight distribution.

        Args:
            concepts: List of concepts to sample from
            count: Number to sample

        Returns:
            Sampled concepts
        """
        if not concepts or count <= 0:
            return []

        # Use weakness_score as probability weight
        weights = [c.weakness_score for c in concepts]
        total = sum(weights)

        if total == 0:
            # Equal probability if all scores are 0
            return random.sample(concepts, min(count, len(concepts)))

        # Normalize weights
        probabilities = [w / total for w in weights]

        # Weighted sampling without replacement
        selected = []
        remaining = list(zip(concepts, probabilities))

        for _ in range(min(count, len(concepts))):
            if not remaining:
                break

            # Random selection based on probabilities
            r = random.random()
            cumulative = 0
            for i, (concept, prob) in enumerate(remaining):
                cumulative += prob
                if r <= cumulative:
                    selected.append(concept)
                    remaining.pop(i)
                    # Renormalize remaining probabilities
                    if remaining:
                        total_prob = sum(p for _, p in remaining)
                        remaining = [(c, p / total_prob) for c, p in remaining]
                    break

        return selected

    async def _query_review_history_from_memory(self, canvas_name: str) -> List[Dict]:
        """
        Query review history from LearningMemoryClient (JSON storage).

        Renamed from _query_review_history_from_graphiti: uses LearningMemoryClient
        (JSON-backed), not graphiti-core. See Task 10 fake naming cleanup.

        ✅ Verified from Story 24.3 Dev Notes (lines 538-592)

        PRD Reference: v1.1.8 - query_review_history_from_graphiti tool

        Args:
            canvas_name: Canvas file name

        Returns:
            List of review records with: concept_id, rating, timestamp, etc.
        """
        try:
            # Import learning memory client
            from app.clients.graphiti_client import get_learning_memory_client

            memory_client = get_learning_memory_client()
            await memory_client.initialize()

            # Get learning history for this canvas
            history = await memory_client.get_learning_history(
                canvas_name=canvas_name,
                limit=1000,  # Get all available history
            )

            logger.info(f"Retrieved {len(history)} review records for {canvas_name}")
            return history

        except (
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
        ) as e:
            logger.warning(f"Graphiti query failed, using empty history: {e}")
            return []

    async def get_multi_review_progress(
        self, original_canvas_path: str
    ) -> Dict[str, Any]:
        """
        Get multi-review trend analysis for an original canvas.

        Queries Graphiti for all verification canvases generated from
        this original canvas and calculates trend metrics.

        ✅ Verified from Story 24.4 Dev Notes (lines 230-267)
        [Source: specs/api/review-api.openapi.yml#L346-378]

        Args:
            original_canvas_path: Path to the original canvas file

        Returns:
            MultiReviewProgressResponse dict with reviews and trends

        Raises:
            CanvasNotFoundException: If no review history exists
        """
        # Query Graphiti for review sessions (Story 24.4)
        reviews = await self._query_review_sessions_from_memory(original_canvas_path)

        if not reviews:
            raise CanvasNotFoundException(
                f"No review history for: {original_canvas_path}"
            )

        # Calculate trends
        trends = self._calculate_trend_analysis(reviews)

        return {
            "original_canvas_path": original_canvas_path,
            "review_count": len(reviews),
            "reviews": reviews,
            "trends": trends,
        }

    async def _query_review_sessions_from_memory(
        self, original_canvas_path: str
    ) -> List[Dict[str, Any]]:
        """
        Query LearningMemoryClient (JSON storage) for all review sessions linked to original canvas.

        Renamed from _query_review_sessions_from_graphiti: uses LearningMemoryClient
        (JSON-backed), not graphiti-core. See Task 10 fake naming cleanup.

        ✅ Verified from Story 24.4 Dev Notes (lines 268-316)
        [Source: docs/architecture/decisions/0003-graphiti-memory.md]

        Cypher Query Pattern (for future Neo4j):
        MATCH (review:ReviewCanvas)-[r:GENERATED_FROM]->(original:Canvas {path: $path})
        RETURN review, r.mode, r.generated_at
        ORDER BY r.generated_at DESC

        For now, using JSON storage via LearningMemoryClient.

        Args:
            original_canvas_path: Path to the original canvas file

        Returns:
            List of review session dicts
        """
        if not self.graphiti_client:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "get_review_sessions",
                "graphiti_client",
                "[]",
            )
            return []

        try:
            # Story 36.7: Uses LearningMemoryClient (supports both JSON and Neo4j backends)
            from app.clients.graphiti_client import get_learning_memory_client

            memory_client = get_learning_memory_client()
            await memory_client.initialize()

            # Get all learning episodes for this canvas
            # Filter for verification canvas pattern: *-检验白板-*
            all_memories = await memory_client.get_learning_history(
                original_canvas_path, limit=100
            )

            # Group by verification canvas sessions
            review_sessions: Dict[str, Dict[str, Any]] = {}

            for memory in all_memories:
                # Check if this is from a verification canvas
                source = memory.get("source_canvas", "")
                if "-检验白板-" not in source:
                    continue

                # Extract session info
                if source not in review_sessions:
                    review_sessions[source] = {
                        "review_canvas_path": source,
                        "date": memory.get("timestamp", datetime.now(timezone.utc)),
                        "mode": memory.get("mode", "fresh"),
                        "concepts": [],
                        "scores": [],
                    }

                # Add concept score
                score = memory.get("score")
                if score is not None:
                    review_sessions[source]["concepts"].append(
                        memory.get("concept", "")
                    )
                    review_sessions[source]["scores"].append(score)

            # Transform to ReviewEntry format
            reviews = []
            for session_data in review_sessions.values():
                scores = session_data["scores"]
                if not scores:
                    continue

                total_concepts = len(scores)
                passed_concepts = sum(1 for s in scores if s >= 24)  # >= 60% threshold
                pass_rate = (
                    passed_concepts / total_concepts if total_concepts > 0 else 0.0
                )

                reviews.append(
                    {
                        "review_canvas_path": session_data["review_canvas_path"],
                        "date": session_data["date"],
                        "mode": session_data["mode"],
                        "pass_rate": pass_rate,
                        "total_concepts": total_concepts,
                        "passed_concepts": passed_concepts,
                    }
                )

            # Sort by date descending (newest first)
            reviews.sort(key=lambda x: x["date"], reverse=True)

            logger.info(
                f"Found {len(reviews)} review sessions for {original_canvas_path}"
            )
            return reviews

        except (
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
        ) as e:
            logger.error(f"Error querying review history: {e}")
            return []

    def _calculate_trend_analysis(
        self, reviews: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate trend metrics from review history.

        ✅ Verified from Story 24.4 Dev Notes (lines 317-362)

        Includes:
        - pass_rate_trend: Time series of pass rates
        - weak_concepts_improvement: Per-concept improvement tracking
        - overall_progress: Aggregate progress metrics

        Args:
            reviews: List of review entry dicts

        Returns:
            TrendAnalysis dict or None if insufficient data
        """
        if not reviews:
            return None

        # Pass rate trend (newest first in reviews, reverse for chronological chart)
        pass_rate_trend = [
            {
                "date": r["date"].split("T")[0]
                if isinstance(r["date"], str)
                else r["date"].strftime("%Y-%m-%d"),
                "pass_rate": r["pass_rate"],
            }
            for r in reversed(reviews)
        ]

        # Calculate overall progress
        if len(reviews) >= 2:
            first_pass_rate = reviews[-1]["pass_rate"]  # Oldest
            last_pass_rate = reviews[0]["pass_rate"]  # Newest
            progress_rate = last_pass_rate - first_pass_rate

            if progress_rate > 0.05:
                trend_direction = "up"
            elif progress_rate < -0.05:
                trend_direction = "down"
            else:
                trend_direction = "stable"
        else:
            progress_rate = 0.0
            trend_direction = "stable"

        return {
            "pass_rate_trend": pass_rate_trend,
            "weak_concepts_improvement": [],  # Populated by separate query if needed
            "overall_progress": {
                "progress_rate": progress_rate,
                "trend_direction": trend_direction,
            },
        }

    async def _query_weak_concepts_improvement(
        self, original_canvas_path: str
    ) -> List[Dict[str, Any]]:
        """
        Query Graphiti for weak concept improvement over time.

        ✅ Verified from Story 24.4 Dev Notes (lines 404-456)

        Tracks concepts that were weak (score < 60) in early reviews
        and their current status.

        Args:
            original_canvas_path: Path to the original canvas file

        Returns:
            List of WeakConceptImprovement dicts
        """
        if not self.graphiti_client:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "get_weak_concept_improvement",
                "graphiti_client",
                "[]",
            )
            return []

        try:
            from app.clients.graphiti_client import get_learning_memory_client

            memory_client = get_learning_memory_client()
            await memory_client.initialize()

            # Get all verification session memories
            all_memories = await memory_client.get_learning_history(
                original_canvas_path, limit=200
            )

            # Filter for verification canvas sessions
            verification_memories = [
                m for m in all_memories if "-检验白板-" in m.get("source_canvas", "")
            ]

            # Group by concept
            concept_scores: Dict[str, List[Dict[str, Any]]] = {}
            for memory in verification_memories:
                concept = memory.get("concept", "")
                score = memory.get("score")
                timestamp = memory.get("timestamp")

                if concept and score is not None and timestamp:
                    if concept not in concept_scores:
                        concept_scores[concept] = []
                    concept_scores[concept].append(
                        {"score": score, "timestamp": timestamp}
                    )

            # Calculate improvement for each concept
            improvements = []
            for concept_name, score_history in concept_scores.items():
                # Sort by timestamp
                score_history.sort(key=lambda x: x["timestamp"])

                first_score = score_history[0]["score"]
                last_score = score_history[-1]["score"]

                # Only include if initially weak (< 60%)
                if first_score < 24:  # 24/40 = 60%
                    improvement_rate = (
                        last_score - first_score
                    ) / 40  # Normalize to 0-1

                    # Determine status
                    if last_score >= 32:  # >= 80%
                        status = "mastered"
                    elif last_score > first_score:
                        status = "improving"
                    else:
                        status = "weak"

                    improvements.append(
                        {
                            "concept_name": concept_name,
                            "improvement_rate": max(0, improvement_rate),
                            "current_status": status,
                        }
                    )

            # Sort by improvement_rate descending
            improvements.sort(key=lambda x: x["improvement_rate"], reverse=True)

            return improvements

        except (
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
        ) as e:
            logger.error(f"Error querying weak concept improvement: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 32.2 Task 4: FSRS Card State Persistence
    # [Source: docs/stories/32.2.story.md#Task-4]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def load_card_state(
        self, concept_id: str, canvas_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Load FSRS card state from the in-memory cache (file-backed, P0-2).

        Story 32.2 AC-32.2.4: Backward compatible - returns None for new concepts.
        CARD-C4 (G-FAKE-007): 原 "load from Graphiti" 读侧死块已下线——它查询
        的 LearningMemoryClient 是本地 JSON 存储, 其 canonical schema
        (add_learning_episode/LearningMemory) 从不承载 card_data 字段: 历史
        普通学习记录存在, 但 FSRS 卡镜像从未被持久化过, 死块按 card_data
        过滤故永远返回 None (详见 docs/known-gotchas.md G-FAKE-007)。真接
        Graphiti 须等 epic-5a C-1/C-2 契约 (episode schema 归主干工程独占)。

        Args:
            concept_id: Concept identifier
            canvas_name: Unused; kept for call-site compatibility

        Returns:
            Serialized card JSON string or None if not found
        """
        if concept_id in self._card_states:
            logger.debug(f"Loaded card state from memory cache: {concept_id}")
            return self._card_states[concept_id]

        return None

    # CARD-G3-7-R2 (BATCH-2026-09-07-第十三批): 此处原有一个公开的卡状态
    # 保存入口, 已退役 —— 它在 backend/app 内零调用方, 唯一动作是转调
    # `_save_card_states`, 即 DD-13 意义上的名实不符: 一个看似公开的写入口,
    # 实际既没有调用者, 也不是这份状态的真实持久化通道。退役后 backend/app
    # 内**不再出现它的名字** (含注释), 否则 grep 到的人会以为它还在;
    # 该名字与本次处置记在 docs/known-gotchas.md G-FAKE-007 与
    # docs/fsrs-truth-source-d0-revision.md 的四写点表 ④ 行。
    # 现在写入口只剩 `_save_card_states` 一个 (调用点: record_review_result /
    # get_fsrs_state auto-create 两处)。
    # 注意 `load_card_state` **未**退役: 它有真实调用方 (get_fsrs_state 内存
    # 未命中时的回退)。两者名字相似, 改动面必须逐字区分。
    # G-FAKE-007 防复活锁未削弱, 只是改指真实通道: 见
    # tests/unit/test_review_service_fsrs.py::TestAutoPersistCounterRemoved。

    def get_cached_card_states(self) -> Dict[str, str]:
        """
        Get all cached card states.

        CARD-G3-5: "all" 的语义已收窄为**当前作用域那一个 vault 桶** —— 不再
        跨 vault 返回全部投影 (那正是撞键期的旧行为)。作用域解析不出来时返回
        空字典 (fail-closed, 见 ``_VaultScopedCardStates``)。

        Returns:
            Dictionary of concept_id -> card_data JSON (当前 vault 桶)
        """
        return dict(self._card_states)

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 32.3: FSRS State Query for Plugin Priority Calculation
    # [Source: docs/stories/32.3.story.md#Task-1]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def get_fsrs_state(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        Get FSRS state for a concept for plugin priority calculation.

        Story 32.3 AC-32.3.1: Plugin queries backend for FSRS state.
        Story 32.3 AC-32.3.2: Returns stability, difficulty, state, reps, lapses,
                              retrievability, due.
        Story 32.3 AC-32.3.3: Includes full card_state JSON for plugin caching.

        Args:
            concept_id: Concept identifier (node_id from canvas)

        Returns:
            Dict with FSRS state fields and card_state JSON, or None if not found
        """
        logger.debug(f"Getting FSRS state for concept: {concept_id}")

        # Story 32.3: Try to get card from cache or persistence
        if self._fsrs_manager is None:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "get_fsrs_state",
                "fsrs_manager",
                "found=False",
            )
            return {"found": False, "reason": "fsrs_not_initialized"}

        try:
            # CARD-G3-7 裁定 ②: 先问真相源 —— frontmatter 是唯一 current state
            # (D0 修订 T1)。has_truth_source 同时决定两件事:
            #   (1) 门锁: 有真相源时本次 GET 一律不推进投影状态 (不写内存/不落盘);
            #   (2) 覆盖: 返回的 due 以 frontmatter 为准, 分歧如实标 degraded。
            # 判据是 reader 的 governed 四态 (见 _read_frontmatter_fsrs docstring):
            # 无文件 / 可读但无 fsrs_due → 放行; 有 fsrs_due / 文件读不出来 → 拦。
            # ⚠️ Codex r1 HIGH-1: 不得写成 `found and fsrs_due` —— 那会把"文件
            # 在但这一刻读不出来"判成无真相源并放行写入。
            #
            # ⚠️ TOCTOU 窗口 (Codex r1 MEDIUM-3, 登记不修): 真相源只在此处读一次,
            # 之后还要 await load_card_state 与 _card_states_lock; 若这期间 vault
            # 侧刚写出 fsrs_due, 本次仍按旧判定推进投影。不闭合的理由: 闭合需在
            # 全局写锁内再做一次文件 I/O (把 vault 磁盘延迟拖进所有写者的临界区),
            # 代价大于收益; 后果有界 —— 写进去的是一张默认卡, 落点是已显式降格的
            # 非真相源缓存, 且**下一次 GET 就会读到 frontmatter、正确拦截并报
            # truth_source_divergence**, 不会静默固化。
            # ⚠️ CARD-G3-5 已落地 (投影按 vault 分桶), **但没有闭合本 TOCTOU**:
            # 键化改的是"写到哪个桶", 真相源在此读一次、之后还要 await
            # load_card_state 与 _card_states_lock 的那个窗口原样还在 —— 窗口
            # 长度与键形态无关。彻底闭合仍待后续卡 (需在全局写锁内重读真相源,
            # 代价是把 vault 磁盘延迟拖进所有写者的临界区)。
            fm_truth = _read_frontmatter_fsrs(concept_id)
            has_truth_source = bool(fm_truth["governed"])

            # Check in-memory cache first
            card_data = self._card_states.get(concept_id)

            if not card_data:
                # Try to load from persistence
                card_data = await self.load_card_state(concept_id)

            gate_blocked = False
            if not card_data:
                # Story 38.3 AC-4: Auto-create default FSRS card for new concepts
                logger.info(
                    f"Auto-creating default FSRS card for concept: {concept_id}"
                )
                card = self._fsrs_manager.create_card()
                card_data = self._fsrs_manager.serialize_card(card)
                # Cache the newly created card + persist to file (P0-2).
                # CARD-C4 (G-FAKE-007): 原 fire-and-forget "_persist_auto_created_card"
                # 后台任务已下线——它调用的方法从未存在 (详见 known-gotchas
                # G-FAKE-007), 每次必失败只留 warning + 计数器, 从未写入过任何
                # 存储。文件通道即唯一真实持久化; 真接 Graphiti 须等 epic-5a
                # C-1/C-2 契约。
                # CARD-D3: 消费返回值 — auto-create 写失败时卡只活在内存,
                # 重启后消失、due 被重置, 必须让调用方看见 (persisted=False)。
                # Codex HIGH-2: mutation 随 pending 进锁内。
                auto_created = True
                if has_truth_source:
                    # CARD-G3-7 门锁边界: 该 concept 归 frontmatter 管, GET 不得
                    # 把默认卡写进**非真相源**的投影缓存 —— 那正是双真相源的
                    # 制造过程 (且 GET 写盘本身违反 HTTP safe-method 语义)。
                    # 默认卡只在本次响应内存活, 不进 _card_states、不落盘。
                    gate_blocked = True
                    persisted = False
                    logger.info(
                        "CARD-G3-7 truth_source_gate: concept=%s 有 frontmatter "
                        "真相源 (fsrs_due=%s), 跳过 auto-create 写盘",
                        concept_id,
                        fm_truth["fsrs_due"],
                    )
                else:
                    persisted = await self._save_card_states(pending=(concept_id, card_data))
                    if not persisted:
                        logger.warning(
                            f"Auto-created FSRS card for {concept_id} NOT persisted "
                            f"(file write failed) — card exists in memory only"
                        )
            else:
                # Deserialize existing card
                card = self._fsrs_manager.deserialize_card(card_data)
                # CARD-D3 Codex HIGH-1: 缓存命中不得无条件视为已持久化 —
                # 此前写失败的 concept 在 _unpersisted_concepts 里, 命中它
                # 必须继续如实上报 False (锁内读: 与在途写串行, 写者失败
                # add / 成功 clear 之后本读取才进行)。
                auto_created = False
                async with _card_states_lock:
                    persisted = not self._is_unpersisted(concept_id)

            # Get retrievability (current recall probability)
            retrievability = self._fsrs_manager.get_retrievability(card)

            # Get due date
            due_date = self._fsrs_manager.get_due_date(card)

            # Extract state value safely
            state_val = getattr(card, "state", 0)
            if hasattr(state_val, "value"):
                state_int = int(state_val.value)
            elif hasattr(state_val, "__int__"):
                state_int = int(state_val)
            else:
                state_int = 0

            # fsrs 6.x new cards: stability/difficulty are None until first
            # review. card_state (below) keeps the authoritative JSON null for
            # roundtrip; these two display fields fall back to the Story 38.3
            # AC-4 default-card contract (stability=1.0, difficulty=5.0)
            # because FSRSStateResponse requires float (difficulty ge=1) and
            # the API layer forwards them via result.get().
            stability = getattr(card, "stability", None)
            difficulty = getattr(card, "difficulty", None)
            result = {
                "found": True,
                # CARD-D3: found=True 只说明卡存在 (可能仅内存), persisted
                # 才是持久层的真话; reason 仅在失败时出现 (避免 None 值
                # 破坏既有 result.get("reason", "") 消费方)。
                "persisted": persisted,
                "stability": float(stability) if stability is not None else 1.0,
                "difficulty": float(difficulty) if difficulty is not None else 5.0,
                "state": state_int,
                "reps": int(getattr(card, "reps", 0)),
                "lapses": int(getattr(card, "lapses", 0)),
                "retrievability": retrievability,
                "due": due_date,
                "last_review": getattr(card, "last_review", None),
                "card_state": card_data,  # Full JSON for plugin to cache/deserialize
            }
            if not persisted:
                # CARD-G3-7: 门锁拦下的"未持久化"是**设计如此**, 不是写失败 ——
                # 用 auto_created_not_persisted 描述它会谎报一次不存在的失败。
                result["reason"] = (
                    "truth_source_gate_no_projection_write"
                    if gate_blocked
                    else ("auto_created_not_persisted" if auto_created else "cached_state_not_persisted")
                )
            # CARD-DEBT-8: 底层 py-fsrs 缺失时加性声明降级（真实库在位
            # 不加键, 响应逐键与此前相同）。retrievability/due 此时来自
            # fallback 估算, 消费方须能看见这不是 FSRS-4.5 的输出。
            if not self._fsrs_library_ok():
                result["algorithm"] = "fsrs-fallback-scheduler"
                result["degraded_reason"] = "fsrs_library_missing"

            # ── CARD-G3-7 裁定 ②: 以 frontmatter 为准 (D0 修订 §五 T1) ────────
            # truth_source 回答"这个 concept 的调度状态归谁管", degraded_reason
            # 回答"这次读它出了什么问题" —— 两者正交, 不得互相冒充。
            # 逗号拼接沿用 CARD-DEBT-8 先例: 多个降级都真实, 谁也不冲掉谁。
            if has_truth_source:
                result["truth_source"] = "frontmatter"
                if fm_truth["due"] is None:
                    # 有真相源但拿不到时刻: 不编造 due。返回投影侧的 due 而
                    # 声称 truth_source=frontmatter 才是假成功。
                    # 两种成因必须分开报 (Codex r1 HIGH-1): 字段在但形态不合规
                    # vs 文件根本没读出来 —— 后者是运维问题, 前者是数据问题。
                    result["due"] = None
                    _g37_reason = (
                        "truth_source_unreadable"
                        if fm_truth["reason"] in ("node_file_unreadable", "node_lookup_unreadable")
                        else "truth_source_unparsable"
                    )
                    logger.warning(
                        "CARD-G3-7 %s: concept=%s frontmatter fsrs_due=%r reason=%s, due 置空不猜测",
                        _g37_reason,
                        concept_id,
                        fm_truth["fsrs_due"],
                        fm_truth["reason"],
                    )
                elif _whole_second_utc(due_date) != fm_truth["due"]:
                    # 整秒归一后比较, 见 _whole_second_utc 的口径说明
                    _g37_reason = "truth_source_divergence"
                    logger.warning(
                        "CARD-G3-7 truth_source_divergence: concept=%s "
                        "frontmatter_due=%s projection_due=%s — 返回 frontmatter 值",
                        concept_id,
                        fm_truth["fsrs_due"],
                        due_date.isoformat() if due_date else None,
                    )
                    result["due"] = fm_truth["due"]
                else:
                    _g37_reason = None
                    result["due"] = fm_truth["due"]
                if _g37_reason is not None:
                    prev = result.get("degraded_reason")
                    result["degraded_reason"] = _g37_reason if prev is None else f"{prev},{_g37_reason}"
            else:
                # 无真相源 (节点 .md 不存在, 或存在但无 fsrs_due = 新卡语义,
                # 对齐 scripts/daily_review_pick.py:435「无 fsrs_due 即真新卡」)。
                # 此时如实说 due 来自投影缓存, 禁止谎称 frontmatter。
                result["truth_source"] = "projection-cache"

            logger.debug(
                f"FSRS state for {concept_id}: stability={result['stability']:.2f}, "
                f"difficulty={result['difficulty']:.2f}, retrievability={f'{retrievability:.3f}' if retrievability is not None else 'N/A'}"
            )

            return result

        # INTENTIONAL: API-facing endpoint; third-party FSRS library may raise unpredictable errors
        except Exception as e:
            logger.error(f"Error getting FSRS state for {concept_id}: {e}")
            return {"found": False, "reason": f"error: {e}"}

    async def cleanup(self) -> None:
        """
        Cleanup resources when service is no longer needed.

        Note: _card_states is NOT cleared here because it is shared persistent state
        that survives across requests. Clearing it would cause unnecessary file re-reads.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self._initialized = False
        self._task_canvas_map.clear()
        # H1 fix: Do NOT clear _card_states — it's cross-request persistent cache.
        # Clearing here causes data loss when DI yield calls cleanup after each request.
        logger.debug("ReviewService cleanup completed")


# ═══════════════════════════════════════════════════════════════════════════════
# Story 38.9: ReviewService Singleton Factory (canonical entry point)
# Pattern: async double-check lock (aligned with get_memory_service in memory_service.py)
# ═══════════════════════════════════════════════════════════════════════════════

_review_service_singleton: Optional["ReviewService"] = None
_review_service_singleton_lock = asyncio.Lock()


async def get_review_service() -> "ReviewService":
    """Get or create the ReviewService singleton.

    Story 38.9 AC1: Canonical singleton factory with double-check lock.
    All consumers (dependencies.py, review.py endpoints) must use this
    single entry point to ensure DI alignment.

    Dependencies created:
    - CanvasService with memory_client (EPIC-36 P0 fix)
    - BackgroundTaskManager
    - FSRSManager via create_fsrs_manager() (Story 32.8)
    - graphiti_client via get_graphiti_temporal_client() (Story 34.8 AC2)
    """
    global _review_service_singleton
    if _review_service_singleton is not None:
        return _review_service_singleton

    async with _review_service_singleton_lock:
        # Double-check after acquiring lock
        if _review_service_singleton is not None:
            return _review_service_singleton

        from app.config import get_settings
        from app.services.background_task_manager import BackgroundTaskManager
        from app.services.canvas_service import CanvasService

        settings = get_settings()

        # 1. CanvasService with memory_client (EPIC-36 P0 fix alignment)
        memory_client = None
        try:
            from app.services.memory_service import get_memory_service as _get_mem

            memory_client = await _get_mem()
        except (ImportError, RuntimeError, AttributeError) as e:
            logger.warning(
                f"MemoryService not available for CanvasService edge sync: {e}"
            )

        canvas_service = CanvasService(
            canvas_base_path=settings.canvas_base_path, memory_client=memory_client
        )

        # 2. BackgroundTaskManager
        task_manager = BackgroundTaskManager()

        # 3. FSRSManager (Story 32.8: unified factory)
        fsrs_manager = create_fsrs_manager(settings)

        # 4. graphiti_client (Story 34.8 AC2: explicit injection)
        graphiti_client = None
        try:
            from app.dependencies import get_graphiti_temporal_client

            graphiti_client = get_graphiti_temporal_client()
        except (ImportError, RuntimeError, AttributeError) as e:
            logger.warning(f"Failed to get graphiti_client for ReviewService: {e}")

        if not graphiti_client:
            logger.warning(
                "Graphiti client not available for ReviewService, "
                "history will use FSRS fallback"
            )

        _review_service_singleton = ReviewService(
            canvas_service=canvas_service,
            task_manager=task_manager,
            graphiti_client=graphiti_client,
            fsrs_manager=fsrs_manager,
        )
        logger.info("ReviewService singleton created via services layer factory")
        return _review_service_singleton


def reset_review_service_singleton() -> None:
    """Reset the ReviewService singleton (for test isolation).

    Story 38.9 AC4: Tests call this instead of directly setting
    review._review_service_instance = None.
    """
    global _review_service_singleton
    _review_service_singleton = None
