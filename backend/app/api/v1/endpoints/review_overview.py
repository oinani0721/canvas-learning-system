"""跨 vault 复习总览 (CARD-C2 → CARD-D1 Anki 化, BATCH-2026-08-27)。

GET /api/v1/review/overview       — JSON 聚合各 vault outputs/今日复习.json
GET /api/v1/review/overview/page  — 内联 HTML 总览页 (零外部 CDN / 零 JS)

只读展示: 本端点是 A2 投影 (schema v3) 的纯消费方 — 不重算到期口径、不写
任何文件。诚实四态: ok / stale / no_projection / corrupt 显式区分 — 缺投影
与损坏 JSON 都以降级条目出现在列表里, 禁静默跳过、禁 500 (单库坏账不拖垮
总览)。stale 判定只看投影自带 generated_at (上海本地日 != 今天), 不看文件
mtime (mtime 被 runner 刻意回拨到扫描起点, 见 daily_review_run.ensure_payload)。

CARD-D1 三级视图: vault 卡片 (名+四态徽标+汇总行) → 板表格 (白板名|到期|
新卡|待剖析|最早到期)。板级到期数由 due_nodes group-by 派生 (行级门禁,
脏行按既有 corrupt 语义降级); 行序 = 有到期板按 top_boards 优先级 → 零到期
板按 next_due。时间统一转 Asia/Shanghai 人话化 (修现网容器 UTC 缺陷);
obsidian:// 深链按 原白板/<板名>.md 约定, 无投影 vault 降级文案不做假链接。

CARD-G3-6a (BATCH-2026-08-29-第六批) 消费端最小接线: 投影加性新增顶层
buckets 五桶 (new/learning_queue/due_now/due_today/future) 后, 本端点只多
消费桶位计数 — 卡片汇总行下多一条「分层」分布行, JSON 多 bucket_counts。
板级到期数仍由 due_nodes group-by 派生 (不从 buckets 抄), stats.due_nodes
仍是权威计数 (生产器 S2「加标签不搬移」使这两条口径分毫未动)。桶内
why_due 的节点级展示属 G6-5 地盘, 这里只门禁不渲染。旧投影 (无 buckets 键)
保持 ok 且 bucket_counts=null — 不伪造分层数字, 也不倒逼迁移。
"""

from __future__ import annotations

import html
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.config import get_settings

logger = structlog.get_logger(__name__)

review_overview_router = APIRouter()

#: 每库投影相对路径 (A2: 全系统到期口径唯一裁判)
_PROJECTION_REL = ("outputs", "今日复习.json")

#: 展示时区: 统一 Asia/Shanghai (CARD-D1 — live 容器跑 UTC, astimezone()
#: 会显示 UTC 裸串差 8 小时)。容器缺 tzdata 时退化为固定 +8 (Asia/Shanghai
#: 自 1991 年起无夏令时, 固定偏移语义等价)。
try:
    from zoneinfo import ZoneInfo

    _TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")
except Exception:  # noqa: BLE001 — ZoneInfoNotFoundError / ImportError 同一退化
    _TZ_SHANGHAI = timezone(timedelta(hours=8))

#: A2 生产器 fsrs_due/next_due 形态: UTC 秒级 Z 后缀 (daily_review_pick 的
#: 落盘正则)。空串 = 新卡/fail-open 即刻到期。其余形态不是生产器产物 —
#: 一律按形状垃圾 corrupt。
_FSRS_DUE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

#: A2 生产器的 generated_at 形态: 本地带时区秒级 isoformat(timespec="seconds")
#: (daily_review_pick.build_payload)。宽松解析会让 "20260825" / 纯日期 /
#: 无时区值冒充今日新鲜投影 (Codex-C2 B2) — 只认生产器的确切形态。
#: offset 收紧到日历合法范围 (时 00-14 / 分 00-59): fromisoformat 会把
#: +08:60 静默归一化成 +09:00, 不设范围等于没锁 (round2 实测绕过)。
_GENERATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-](?:0\d|1[0-4]):[0-5]\d|Z)$")


def _strict_int(v) -> int:
    """非负 int (bool 拒绝 — JSON true 属 int 子类, int(True)=1 会冒充计数)。"""
    if type(v) is not int or v < 0:
        raise ValueError(f"应为非负整数, 实为 {v!r}")
    return v


def _opt_str(v, field: str):
    if v is not None and not isinstance(v, str):
        raise ValueError(f"{field} 应为字符串或缺省, 实为 {type(v).__name__}")
    return v


def _finite_float(s: str) -> float:
    """json 解码层的浮点门禁 (Codex-C2 round2): 标准数字 1e999 会被解成
    inf 并透传进响应 — 非有限数不是合法 v3 投影值。"""
    v = float(s)
    if not math.isfinite(v):
        raise ValueError(f"非有限数值 {s}")
    return v


def _due_ts(v, field: str, *, allow_empty: bool = True) -> str:
    """fsrs_due/next_due 门禁: 空串或生产器 UTC-Z 秒级形态且日历合法。

    词形正则 + strptime 双重: "2026-13-01T00:00:00Z" 形状对但月份非法,
    只靠正则会让后续人话化渲染吞掉一个不可解释值。
    """
    if not isinstance(v, str):
        raise ValueError(f"{field} 应为字符串, 实为 {type(v).__name__}")
    if v == "":
        if allow_empty:
            return v
        raise ValueError(f"{field} 不得为空串")
    if not _FSRS_DUE_RE.fullmatch(v):
        raise ValueError(f"{field} 非生产器 UTC-Z 形态: {v!r}")
    try:
        datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError(f"{field} 日历非法: {v!r}")
    return v


def _gate_due_groups(due_nodes: list) -> dict[str, dict]:
    """due_nodes 行级门禁 + 板级 group-by (CARD-D1)。

    只门禁消费字段 (board/due_reason/fsrs_due); 任一脏行 raise → 整库按
    既有 corrupt 语义降级, 绝不静默丢行 (丢行会让板级合计悄悄 != stats)。
    earliest 只在非空时间戳里取 min: 已到期 scheduled 的时刻恒在过去, 比
    新卡的 "" (=现在) 更紧迫 — 字典序把 "" 当最小会让"逾期3天"被"现在"
    盖掉, 低估紧迫度 (冒烟实测抓到)。全新卡板才落 "" → 渲染"现在"。
    """
    groups: dict[str, dict] = {}
    # Codex round-5 HIGH: 生产器的节点身份是**全局唯一**的文件 stem
    # (sorted((vault/"节点").glob("*.md")) → path.stem), 不是 (板, 节点) 复合键 —
    # 用复合键去重会放行"同一节点在两个板各出现一次"的伪造 (虚增板级与桶级计数)
    seen_rows: set[str] = set()
    for i, row in enumerate(due_nodes):
        if not isinstance(row, dict):
            raise ValueError(f"due_nodes[{i}] 应为 object, 实为 {type(row).__name__}")
        board = row.get("board")
        if not isinstance(board, str) or not board:
            raise ValueError(f"due_nodes[{i}].board 应为非空字符串, 实为 {board!r}")
        node = row.get("node")
        if not isinstance(node, str) or not node:
            raise ValueError(f"due_nodes[{i}].node 应为非空字符串, 实为 {node!r}")
        # Codex-D1 H5 + round-5 收紧: 重复行会被静默重复计数 — 生产器 stem
        # 全局唯一, 同名节点无论落在哪个板都是垃圾
        if node in seen_rows:
            raise ValueError(f"due_nodes[{i}] 节点重复 (stem 全局唯一): {node!r} (本行板 {board!r})")
        seen_rows.add(node)
        reason = row.get("due_reason")
        if reason not in ("new", "scheduled", "malformed"):
            raise ValueError(f"due_nodes[{i}].due_reason 枚举外: {reason!r}")
        ts = _due_ts(row.get("fsrs_due"), f"due_nodes[{i}].fsrs_due")
        # 生产器构造律: scheduled ⟺ fsrs_due 非空 (new/malformed 均为空串)
        if (reason == "scheduled") != bool(ts):
            raise ValueError(f"due_nodes[{i}] due_reason={reason!r} 与 fsrs_due={ts!r} 不自洽")
        g = groups.setdefault(board, {"due": 0, "new": 0, "scheduled": 0, "earliest": "", "rows": {}})
        # CARD-G3-6a: 逐行留底 (节点身份 + 行内 bucket/why_due) 供 _gate_buckets
        # 做成员级跨源核对 —— 只留聚合计数会让"身份被替换但计数不变"的桶位
        # 投影蒙混过关 (Codex round-1 HIGH)
        g["rows"][node] = {
            "reason": reason,
            "fsrs_due": ts,
            "bucket": row.get("bucket"),
            "why_due": row.get("why_due"),
        }
        g["due"] += 1
        if reason == "new":
            g["new"] += 1
        elif reason == "scheduled":
            g["scheduled"] += 1
        if ts and (not g["earliest"] or ts < g["earliest"]):
            g["earliest"] = ts
    return groups


def _gate_upcoming(upcoming: list) -> list[dict]:
    """upcoming 全量元素门禁 (CARD-D1 前只看 [0]): 板表格零到期行的数据源。"""
    gated = []
    seen: set[str] = set()
    for i, u in enumerate(upcoming):
        if not isinstance(u, dict):
            raise ValueError(f"upcoming[{i}] 应为 object, 实为 {type(u).__name__}")
        board = u.get("board")
        if not isinstance(board, str) or not board:
            raise ValueError(f"upcoming[{i}].board 应为非空字符串, 实为 {board!r}")
        if board in seen:  # Codex-D1 H5: 重复板会成双行 — 生产器一板一条
            raise ValueError(f"upcoming[{i}].board 重复: {board!r}")
        seen.add(board)
        node = u.get("node")
        # round2: 生产器 node 恒为非空 stem — 空值不再放行
        if not isinstance(node, str) or not node:
            raise ValueError(f"upcoming[{i}].node 应为非空字符串, 实为 {node!r}")
        gated.append(
            {
                "board": board,
                "next_due": _due_ts(u.get("next_due"), f"upcoming[{i}].next_due", allow_empty=False),
                "node": node,
            }
        )
    return gated


def _gate_boards_rollup(
    rollup, due_groups: dict[str, dict], flat_placeholder: int
) -> tuple[dict[str, int], list[dict], dict[str, tuple[int, str]]]:
    """P1 加性 boards rollup 门禁 (可选顶层键: 旧投影缺省走纯派生路径)。

    消费两块: 板级 placeholder 归属 (待剖析列) + due==0 零到期板全量
    (upcoming 只截 [:3] 的结构性缺口)。其余字段只门禁不消费 — 板级到期数
    仍由 due_nodes group-by 派生 (CARD-D1 P0 判据), 不从 rollup 抄。

    跨源一致性 (Codex-D1 H4): 生产器构造保证 rollup 与 due_nodes/扁平
    placeholder 同源 — rollup 的到期板集合+计数必须与 group-by 派生逐板
    相等 (否则"声称 due=1 但明细无此板"的板会静默消失), 板级 placeholder
    合计不得超过扁平列表总数 (无归属占位符只会让合计更小)。不一致即 corrupt。
    """
    if not isinstance(rollup, list):
        raise ValueError(f"boards 应为数组, 实为 {type(rollup).__name__}")
    ph_map: dict[str, int] = {}
    rollup_due: dict[str, int] = {}
    rollup_new: dict[str, int] = {}
    rollup_sched: dict[str, int] = {}
    # CARD-G3-6a: 板级未到期 (数量, 最近排期) —— buckets 的非到期两桶在
    # due_nodes 里没有对手盘 (S2 不搬移), rollup 是它们唯一的跨源对账面
    future_map: dict[str, tuple[int, str]] = {}
    zero: list[dict] = []
    for i, r in enumerate(rollup):
        if not isinstance(r, dict):
            raise ValueError(f"boards[{i}] 应为 object, 实为 {type(r).__name__}")
        board = r.get("board")
        if not isinstance(board, str) or not board:
            raise ValueError(f"boards[{i}].board 应为非空字符串, 实为 {board!r}")
        if board in ph_map:
            raise ValueError(f"boards[{i}].board 重复: {board!r}")
        counts: dict[str, int] = {}
        for f in ("due", "due_new", "due_scheduled", "future", "placeholder"):
            try:
                counts[f] = _strict_int(r.get(f))
            except ValueError as e:
                raise ValueError(f"boards[{i}].{f} {e}")
        next_due = _due_ts(r.get("next_due"), f"boards[{i}].next_due")
        _due_ts(r.get("earliest_overdue"), f"boards[{i}].earliest_overdue")
        # 生产器构造律 (Codex-D1 round2 补齐):
        # ① due 三分不越界 (malformed = due - new - scheduled >= 0)
        if counts["due_new"] + counts["due_scheduled"] > counts["due"]:
            raise ValueError(
                f"boards[{i}] due 三分越界: due={counts['due']} new={counts['due_new']} sched={counts['due_scheduled']}"
            )
        # ② future ⟺ next_due 非空 (未来成员必有合法 fsrs_due)
        if (counts["future"] > 0) != bool(next_due):
            raise ValueError(f"boards[{i}] future={counts['future']} 与 next_due={next_due!r} 不自洽")
        # ③ 全零幽灵板: 板只经成员或占位符进 rollup, 五计数全零非生产器产物
        if counts["due"] == 0 and counts["future"] == 0 and counts["placeholder"] == 0:
            raise ValueError(f"boards[{i}] 全零板 {board!r} 非生产器产物")
        ph_map[board] = counts["placeholder"]
        future_map[board] = (counts["future"], next_due)
        rollup_due[board] = counts["due"]
        rollup_new[board] = counts["due_new"]
        rollup_sched[board] = counts["due_scheduled"]
        if counts["due"] == 0:
            zero.append({"board": board, "next_due": next_due})
    derived_due = {b: g["due"] for b, g in due_groups.items()}
    claimed_due = {b: d for b, d in rollup_due.items() if d > 0}
    if claimed_due != derived_due:
        raise ValueError(f"boards rollup 到期计数与 due_nodes 明细不一致: rollup={claimed_due} 明细={derived_due}")
    # ④ due 三分逐板与明细 due_reason 同源 (round2: due_new/due_scheduled
    # 漂移会让"新卡"列造假)
    for b, g in due_groups.items():
        if rollup_new[b] != g["new"] or rollup_sched[b] != g["scheduled"]:
            raise ValueError(
                f"boards rollup {b!r} 三分与明细不一致: "
                f"rollup new={rollup_new[b]}/sched={rollup_sched[b]} 明细 new={g['new']}/sched={g['scheduled']}"
            )
    if sum(ph_map.values()) > flat_placeholder:
        raise ValueError(f"boards rollup placeholder 合计 {sum(ph_map.values())} 超过扁平列表总数 {flat_placeholder}")
    return ph_map, zero, future_map


#: CARD-G3-6a 五桶枚举 — 与生产器 daily_review_pick.BUCKET_ORDER 同名同序
_BUCKET_ORDER = ("new", "learning_queue", "due_now", "due_today", "future")
#: 其中三个到期桶: 成员恒等于 due_nodes 明细 (生产器 S2「加标签不搬移」)
_DUE_BUCKETS = ("new", "learning_queue", "due_now")
#: 生产器 build_payload 对 upcoming 的截断上限 (payload["upcoming"] = upcoming[:3])
_UPCOMING_LIMIT = 3
#: 桶位人读标签 (页面汇总行)
_BUCKET_CN = {
    "new": "新卡",
    "learning_queue": "学习中",
    "due_now": "到期",
    "due_today": "今天晚些",
    "future": "未来",
}


def _sh_day(ts: str):
    """UTC-Z 定长串 → Asia/Shanghai 日期; 不可表示时 None (年份极值)。"""
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(_TZ_SHANGHAI).date()
    except (ValueError, OverflowError, OSError):
        return None


def _gate_buckets(
    buckets,
    due_groups: dict[str, dict],
    stats: dict,
    generated_at: str,
    future_map: dict[str, tuple[int, str]],
    up_gated: list[dict],
) -> dict[str, int]:
    """G3-6a 加性 buckets 门禁 (可选顶层键: 旧投影缺省走 None 路径)。

    只消费桶位计数 (卡片汇总行的分层分布); why_due 的节点级展示属 G6-5 地盘,
    这里只门禁不渲染 —— 但仍逐行验形, 不给形状垃圾发 ok。

    跨源一致性 (与 _gate_boards_rollup 同一纪律): 生产器 S1/S2 构造保证
    ① 五桶两两不交 (同一 board/node 只出现一次);
    ② 三个到期桶的**成员身份**恒等于 due_nodes 明细的 (board, node) 集合
       —— 只比计数会让"身份被整体替换但每板数量不变"的投影蒙混过关
       (Codex round-1 HIGH 实证), 故这里比集合而非比数字;
    ③ 逐节点 bucket / why_due / fsrs_due 在两处表示必须逐字相等 (生产器
       同源赋值), 且 bucket 值必须等于它所在的桶名;
    ④ 桶特定时间语义: new 桶 ⟺ 明细 due_reason=="new" 且 fsrs_due 空;
       learning_queue / due_now 的明细 reason ∈ {scheduled, malformed};
       due_today / future 的 fsrs_due 恒非空 (未到期必有合法排期);
    ⑤ 到期三桶合计 == stats.due_nodes 权威计数;
       due_today + future 合计 == stats.future_nodes;
    ⑥ 非到期两桶在 due_nodes 里没有对手盘 (S2 不搬移), 故改用两条独立对账
       (Codex round-2 HIGH: 只查"时间非空 + 总数"时, 把 due_today 整体换成
       远期 FAKE-* 身份仍能拿到 ok):
       (a) 以投影自带的 generated_at 为参照时钟**重算桶判据** —— 每行
           fsrs_due 必须严格晚于 generated_at (未到期), 且 due_today 与
           generated_at 同一 Asia/Shanghai 日、future 必须晚于该日;
           时刻不可表示 (年份极值) 只允许出现在 future (与生产器兜底同口径);
       (b) 与 boards rollup 逐板对账 —— 板级非到期行数 == rollup.future,
           板内最早 fsrs_due == rollup.next_due;
       (c) 与 upcoming 对身份 —— upcoming 逐条命名了"零到期板的最早到期节点",
           该 (board, node) 必须出现在非到期桶里且时刻等于 next_due
           (Codex round-3: 非到期节点在 due_nodes 里没有对手盘, upcoming 是
           投影内唯一另一处点名它们的地方)。upcoming 本身先被钉死在 rollup
           上 —— 板集合 / 条数 / 升序 / next_due 全从 rollup 复算 (Codex
           round-4: 否则清空或换板即可整体跳过本条);
       (d) 到期侧时间逆检查 —— due_reason=="scheduled" 的到期成员其 fsrs_due
           必须不晚于参照时钟 (Codex round-4: 否则未来时刻可伪装成 due_now)。
    任一不成立即 ValueError → 整库按既有 corrupt 语义降级。
    参照时钟要求: buckets 在场时 generated_at 必须是生产器确切形态 —— 拿不到
    可信时钟就无从重算桶判据, 与其放行不如按 corrupt 降级 (生产器恒产出该形态)。
    boards 同在要求: buckets 在场时 boards 必须同在 —— 二者由同一版生产器一起
    产出, "有 buckets 无 boards" 不是任何历史形态, 放行它等于放弃 (b) 的对账。

    ⚠ 消费端核验的原理上限 (Codex round-3/4 复核后如实记录, 非遗漏):
    本门禁能证的是「生产器发出的多份表示彼此自洽」。对**只在投影里出现一次**
    的数据 —— **凡未被 upcoming 点名的非到期节点名**(含: 截断范围外的零到期板、
    有到期成员之板的未来节点、入选板里非最早的那些节点), 以及判 learning 用的
    fsrs_state (根本不落盘) —— 消费端**在原理上**无法独立核验: 没有第二个来源
    可比, 再加断言也只是让伪造者多改一个字段
    (round-4 复核确认 fsrs_state 这条论证成立)。A2 的架构裁定本就是「投影是
    全系统到期口径唯一裁判, 消费端只读不重算」, 这类正确性由生产器侧契约
    测试保证 (五桶划分律 + fsrs_state 六态用例), 不由本函数保证。
    why_due 同理只验非空与两处相等 —— 在消费端重算 S3 模板等于把生产器逻辑
    抄第二份, 模板一演进两边必漂; 它是受信生产器字段。
    """
    if not isinstance(buckets, dict):
        raise ValueError(f"buckets 应为 object, 实为 {type(buckets).__name__}")
    if set(buckets) != set(_BUCKET_ORDER):
        raise ValueError(f"buckets 键集合非 G3-6a 五桶: {sorted(buckets)}")
    # ⑥(a) 参照时钟: 生产器 build_payload 的 now, 落盘为 generated_at
    if not _GENERATED_AT_RE.fullmatch(generated_at):
        raise ValueError(f"buckets 在场但 generated_at 非生产器形态, 无可信参照时钟: {generated_at!r}")
    try:
        ref = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        ref_z = ref.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ref_day = ref.astimezone(_TZ_SHANGHAI).date()
    except (ValueError, OverflowError, OSError) as e:
        raise ValueError(f"generated_at 无法换算为参照时钟: {generated_at!r} ({e})")
    nondue_by_board: dict[str, list[str]] = {}
    nondue_ids: dict[tuple[str, str], str] = {}
    # Codex round-5 HIGH: 节点身份全局唯一 (生产器 = 文件 stem) —— 用
    # (板, 节点) 复合键去重会放行"同名节点在两个板各落一桶"的伪造, 那直接
    # 违反 S1「每个节点恰好落一桶」并虚增计数
    counts: dict[str, int] = {}
    seen: set[str] = set()
    claimed_due: dict[tuple[str, str], tuple[str, str, str]] = {}
    for name in _BUCKET_ORDER:
        rows = buckets[name]
        if not isinstance(rows, list):
            raise ValueError(f"buckets.{name} 应为数组, 实为 {type(rows).__name__}")
        for i, r in enumerate(rows):
            if not isinstance(r, dict):
                raise ValueError(f"buckets.{name}[{i}] 应为 object, 实为 {type(r).__name__}")
            for f in ("node", "board", "why_due"):
                v = r.get(f)
                if not isinstance(v, str) or not v:
                    raise ValueError(f"buckets.{name}[{i}].{f} 应为非空字符串, 实为 {v!r}")
            ts = _due_ts(r.get("fsrs_due"), f"buckets.{name}[{i}].fsrs_due")
            key = (r["board"], r["node"])
            if r["node"] in seen:  # S1 互斥: 同一节点落两桶/两板 = 划分律被打破
                raise ValueError(f"buckets.{name}[{i}] 节点重复 (stem 全局唯一): {r['node']!r} (本行板 {r['board']!r})")
            seen.add(r["node"])
            if name in _DUE_BUCKETS:
                claimed_due[key] = (name, ts, r["why_due"])
                continue
            # ⑥(a) 非到期两桶: 用参照时钟重算生产器的判桶条件
            if not ts:
                # 未到期必有合法排期 (生产器: fsrs_due 空 ⟹ 恒 due_now)
                raise ValueError(f"buckets.{name}[{i}] 未到期桶的 fsrs_due 不得为空: {key[0]!r}/{key[1]!r}")
            if ts <= ref_z:
                raise ValueError(f"buckets.{name}[{i}] fsrs_due={ts} 不晚于 generated_at, 应属到期侧")
            day = _sh_day(ts)
            if day is None:
                # 时刻不可表示: 生产器兜底恒归 future, 不可能是"今天"
                if name != "future":
                    raise ValueError(f"buckets.{name}[{i}] fsrs_due={ts} 不可换算, 只允许出现在 future 桶")
            elif name == "due_today" and day != ref_day:
                raise ValueError(f"buckets.due_today[{i}] fsrs_due={ts} 非 generated_at 的同一上海日 {ref_day}")
            elif name == "future" and day <= ref_day:
                raise ValueError(f"buckets.future[{i}] fsrs_due={ts} 仍在上海日 {ref_day} 内, 应属 due_today")
            nondue_by_board.setdefault(r["board"], []).append(ts)
            nondue_ids[key] = ts
        counts[name] = len(rows)
    # ② 成员身份恒等 (只比计数挡不住整体身份替换 — Codex round-1 HIGH)
    detail = {(b, n): meta for b, g in due_groups.items() for n, meta in g["rows"].items()}
    if set(claimed_due) != set(detail):
        only_bucket = sorted(set(claimed_due) - set(detail))[:5]
        only_detail = sorted(set(detail) - set(claimed_due))[:5]
        raise ValueError(f"buckets 到期成员与 due_nodes 明细不一致: 仅在桶={only_bucket} 仅在明细={only_detail}")
    for key, (name, ts, why) in claimed_due.items():
        meta = detail[key]
        # ③ 两处表示同源: 行内 bucket/why_due/fsrs_due 与桶内逐字相等
        if meta["bucket"] != name:
            raise ValueError(f"due_nodes 行 {key[0]!r}/{key[1]!r} 的 bucket={meta['bucket']!r} 与所在桶 {name!r} 矛盾")
        if meta["why_due"] != why:
            raise ValueError(f"due_nodes 行 {key[0]!r}/{key[1]!r} 的 why_due 与桶内不一致")
        if meta["fsrs_due"] != ts:
            raise ValueError(f"due_nodes 行 {key[0]!r}/{key[1]!r} 的 fsrs_due 与桶内不一致")
        # ④ 桶特定时间语义 (生产器 S1 判据的逆检查)
        if name == "new" and (meta["reason"] != "new" or ts):
            raise ValueError(f"buckets.new 成员 {key[1]!r} 非真新卡: due_reason={meta['reason']!r} fsrs_due={ts!r}")
        if name != "new" and meta["reason"] == "new":
            raise ValueError(f"buckets.{name} 成员 {key[1]!r} 实为真新卡 (due_reason=new), 应属 new 桶")
        # 到期侧时间逆检查 (Codex round-4 HIGH): 已排期的到期成员其时刻必须
        # 不晚于参照时钟 —— 否则"未来时刻伪装成 due_now/learning_queue"能绕过
        if meta["reason"] == "scheduled" and ts > ref_z:
            raise ValueError(f"buckets.{name} 成员 {key[1]!r} 的 fsrs_due={ts} 晚于 generated_at, 不该在到期侧")
    due_total = sum(counts[b] for b in _DUE_BUCKETS)
    if due_total != _strict_int(stats.get("due_nodes")):
        raise ValueError(f"buckets 到期三桶合计 {due_total} != stats.due_nodes {stats.get('due_nodes')!r}")
    future_total = counts["due_today"] + counts["future"]
    try:
        stats_future = _strict_int(stats.get("future_nodes"))
    except ValueError as e:
        raise ValueError(f"stats.future_nodes {e}")
    if future_total != stats_future:
        raise ValueError(f"buckets 非到期两桶合计 {future_total} != stats.future_nodes {stats_future}")
    # ⑥(b) 与 boards rollup 逐板对账 (调用方已保证 boards 同在)
    claimed = {b: (len(ts_list), min(ts_list)) for b, ts_list in nondue_by_board.items()}
    rollup_future = {b: v for b, v in future_map.items() if v[0] > 0}
    if claimed != rollup_future:
        # Codex round-5 LOW: 大投影别把整张映射塞进错误消息 (会进响应 error 字段)
        diff = sorted(b for b in set(claimed) | set(rollup_future) if claimed.get(b) != rollup_future.get(b))
        raise ValueError(
            f"buckets 非到期分层与 boards rollup 不一致: 共 {len(diff)} 板不符, 例如 "
            + ", ".join(f"{b!r} 桶={claimed.get(b)} rollup={rollup_future.get(b)}" for b in diff[:3])
        )
    # ⑥(c) 与 upcoming 对身份: 零到期板的最早到期节点在两处必须是同一个。
    # 先把 upcoming 本身钉死在 rollup 上 (Codex round-4 HIGH): 否则清空
    # upcoming 或换成别的板, 本条对账就被整体跳过了。
    # 生产器构造律: upcoming = {rollup 里 due==0 且 future>0 的板} 按 next_due
    # 升序取前 3 —— 板集合 / 条数 / 顺序 / next_due 四者全可从 rollup 复算。
    cand = {b: nd for b, (cnt, nd) in future_map.items() if cnt > 0 and b not in due_groups}
    if len(up_gated) != min(_UPCOMING_LIMIT, len(cand)):
        raise ValueError(f"upcoming 条数 {len(up_gated)} != min({_UPCOMING_LIMIT}, 零到期且有排期板数 {len(cand)})")
    chosen = [u["board"] for u in up_gated]
    if any(b not in cand for b in chosen):
        raise ValueError(f"upcoming 含非「零到期且有排期」板: {[b for b in chosen if b not in cand]}")
    picked = [u["next_due"] for u in up_gated]
    if picked != sorted(picked):
        raise ValueError(f"upcoming 未按 next_due 升序: {picked}")
    rest = [nd for b, nd in cand.items() if b not in chosen]
    if rest and picked and max(picked) > min(rest):
        # 截断边界并列允许 (生产器 sort 稳定, 同刻任一板皆可), 严格更早的板被漏掉则不允许
        raise ValueError(f"upcoming 漏掉了更早到期的板: 已选最晚 {max(picked)} > 未选最早 {min(rest)}")
    for u in up_gated:
        if u["next_due"] != cand[u["board"]]:
            raise ValueError(f"upcoming {u['board']!r} 的 next_due={u['next_due']} != rollup {cand[u['board']]}")
        key = (u["board"], u["node"])
        if key not in nondue_ids:
            raise ValueError(f"upcoming 点名的 {u['board']!r}/{u['node']!r} 不在任何非到期桶里")
        if nondue_ids[key] != u["next_due"]:
            raise ValueError(
                f"upcoming {u['board']!r}/{u['node']!r} 的 next_due={u['next_due']} 与桶内 {nondue_ids[key]} 不一致"
            )
        board_min = min(nondue_by_board[u["board"]])
        if u["next_due"] != board_min:
            raise ValueError(f"upcoming {u['board']!r} 的 next_due={u['next_due']} 非板内最早 {board_min}")
    return counts


def _humanize_due(ts: str | None, now_sh: datetime) -> tuple[str, str]:
    """到期时刻 → (人话, 颜色)。跨午夜用上海本地日判定 (CARD-D1)。

    None = 无数据 (P0 下板级待剖析等无归属信息) → "—"; "" = 即刻到期。
    渲染层防御: 门禁已保证形态, 这里仍容错返回 "—" 而非异常 (绝不 500)。
    """
    if ts is None:
        return "—", "#6b7280"
    if ts == "":
        return "现在", "#d97706"
    try:
        due = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        # astimezone 也在 try 内: 日历合法极值 (9999-12-31T23:59:59Z) +8h
        # 会年份溢出 OverflowError — 门禁挡不住的极值不许 500
        due_sh = due.astimezone(_TZ_SHANGHAI)
        delta = (due_sh.date() - now_sh.astimezone(_TZ_SHANGHAI).date()).days
    except (ValueError, OverflowError, OSError):
        return "—", "#6b7280"
    if delta < 0:
        return f"逾期{-delta}天", "#dc2626"
    if delta == 0:
        return "现在", "#d97706"
    if delta == 1:
        return "明天", "#374151"
    if delta <= 7:
        return f"{delta}天后", "#374151"
    if due_sh.year == now_sh.astimezone(_TZ_SHANGHAI).year:
        return f"{due_sh.month}月{due_sh.day}日", "#6b7280"
    return f"{due_sh.year}年{due_sh.month}月{due_sh.day}日", "#6b7280"


def _fmt_local_dt(dt: datetime) -> str:
    """tz-aware 时刻 → 上海本地 "YYYY-MM-DD HH:MM (UTC+N)"。"""
    local = dt.astimezone(_TZ_SHANGHAI)
    off = local.utcoffset() or timedelta(0)
    hours = int(off.total_seconds() // 3600)
    return local.strftime("%Y-%m-%d %H:%M") + f" (UTC{'+' if hours >= 0 else ''}{hours})"


def _fmt_projection_time(generated_at: str) -> str:
    """投影 generated_at → 上海本地显示; 解析失败原样返回 (stale 库的畸形
    时间已由徽标诚实标注, 这里不装能解析)。"""
    try:
        gen = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        if gen.tzinfo is None:
            return generated_at
        return _fmt_local_dt(gen)
    except (ValueError, OverflowError, OSError):
        # OverflowError: fromisoformat 放行 -23:59 极端 offset, astimezone
        # 溢出 (Codex-C2 B1 同款) — stale 库的畸形时间原样展示, 不 500
        return generated_at


def _board_link(vault_id: str, board: str) -> str:
    """obsidian:// 深链 — 板名==原白板文件 stem 约定 (勘探 4/4 实测)。"""
    return "obsidian://open?vault=" + quote(vault_id, safe="") + "&file=" + quote(f"原白板/{board}.md", safe="")


#: 状态 → (徽标文案, 徽标色) — 页面与 JSON status 同一枚举
_STATUS_META = {
    "ok": ("今日投影", "#16a34a"),
    "stale": ("过期投影", "#d97706"),
    "no_projection": ("无投影", "#6b7280"),
    "corrupt": ("投影损坏", "#dc2626"),
}


def _list_vault_dirs(vaults_root: Path) -> list[Path]:
    """与 GET /vault/list 同一条候选规则: 非隐藏目录且含 .obsidian/。"""
    dirs: list[Path] = []
    for entry in sorted(vaults_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if not (entry / ".obsidian").is_dir():
            continue
        dirs.append(entry)
    return dirs


def _summarize(payload: dict) -> dict:
    """严格 v3 形状门禁 + 摘要 (Codex-C2 B3): 本端点只消费冻结的 schema v3
    投影 — 版本/嵌套容器/计数类型任一不符即抛 ValueError → corrupt 降级,
    绝不给形状垃圾发 ok。只挑总览页要的字段, 不重算到期口径。"""
    if payload.get("schema_version") != 3 or type(payload.get("schema_version")) is not int:
        raise ValueError(f"仅支持 schema_version 3, 实为 {payload.get('schema_version')!r}")
    stats = payload.get("stats")
    if not isinstance(stats, dict):
        raise ValueError(f"stats 应为 object, 实为 {type(stats).__name__}")
    top_boards = payload.get("top_boards")
    upcoming = payload.get("upcoming")
    due_nodes = payload.get("due_nodes")
    ineligible = payload.get("ineligible")
    if not (
        isinstance(top_boards, list)
        and isinstance(upcoming, list)
        and isinstance(due_nodes, list)
        and isinstance(ineligible, dict)
    ):
        raise ValueError("top_boards/upcoming/due_nodes/ineligible 容器形状不符 v3")
    placeholder = ineligible.get("placeholder")
    if not isinstance(placeholder, list):
        raise ValueError(f"ineligible.placeholder 应为数组, 实为 {type(placeholder).__name__}")
    for j, p in enumerate(placeholder):
        if not isinstance(p, str):  # Codex-D1 H5: len() 消费也不给垃圾元素发 ok
            raise ValueError(f"ineligible.placeholder[{j}] 应为字符串, 实为 {type(p).__name__}")
    # top_boards 全量元素门禁 (CARD-D1: 行序依赖每个元素的 board) —
    # [0] 额外保留 top_node/pending 门禁 (汇总行消费)
    prio: dict[str, int] = {}
    for i, tb in enumerate(top_boards):
        if not isinstance(tb, dict):
            raise ValueError(f"top_boards[{i}] 应为 object, 实为 {type(tb).__name__}")
        b = tb.get("board")
        # round2: 空板名也是垃圾 (生产器 _board_name 恒非空) — 不再 _opt_str 放行
        if not isinstance(b, str) or not b:
            raise ValueError(f"top_boards[{i}].board 应为非空字符串, 实为 {b!r}")
        # Codex-D1 H5: 重复板会让后续板与非 top 板共享排序优先级
        if b in prio:
            raise ValueError(f"top_boards[{i}].board 重复: {b!r}")
        prio[b] = i
    top = top_boards[0] if top_boards else {}
    up_gated = _gate_upcoming(upcoming)
    # 不透传整对象 (round3: 内部字段未验的 dict 原样进响应仍是形状垃圾
    # 通道) — 只提取消费方要的三个字段并逐一门禁
    next_up = dict(up_gated[0]) if up_gated else None

    # ── CARD-D1 板表格派生: 到期板 (due_nodes group-by, top_boards 优先级
    # 排序) → 零到期板 (按 next_due 升序)。P1 rollup 在场时提供板级
    # placeholder 归属 (待剖析列) 与零到期板全量; 缺省 (旧投影) 时待剖析
    # 为 null → 渲染 "—", 零到期板回落 upcoming[:3]。
    generated_at = payload.get("generated_at")
    if not isinstance(generated_at, str):
        raise ValueError(f"generated_at 应为字符串, 实为 {type(generated_at).__name__}")
    groups = _gate_due_groups(due_nodes)
    ph_map: dict[str, int] = {}
    rollup_zero: list[dict] | None = None
    future_map: dict[str, tuple[int, str]] | None = None
    # "boards" in payload 而非 .get(): 显式 null 不是"旧投影缺省", 是形状
    # 垃圾 (Codex-D1 H5) — 生产器恒产出数组
    if "boards" in payload:
        ph_map, rollup_zero, future_map = _gate_boards_rollup(payload["boards"], groups, len(placeholder))
    # CARD-G3-6a 加性: 五桶分层计数 (同 "boards" 口径 — 显式 null 不是"旧
    # 投影缺省", 是形状垃圾; 生产器恒产出五键 object)
    bucket_counts = None
    if "buckets" in payload:
        # Codex round-3: 二者由同一版生产器一起产出 —— "有 buckets 无 boards"
        # 不是任何历史形态, 放行它等于放弃非到期两桶的逐板对账
        if future_map is None:
            raise ValueError("buckets 在场但 boards 缺席 — 非生产器产物 (二者同版一起落盘)")
        bucket_counts = _gate_buckets(payload["buckets"], groups, stats, generated_at, future_map, up_gated)
    board_rows = [
        {"board": b, "due": g["due"], "due_new": g["new"], "placeholder": ph_map.get(b), "earliest": g["earliest"]}
        for b, g in groups.items()
    ]
    board_rows.sort(key=lambda r: (prio.get(r["board"], len(prio)), -r["due"], r["board"]))
    if rollup_zero is not None:
        zero_rows = [
            {
                "board": z["board"],
                "due": 0,
                "due_new": 0,
                "placeholder": ph_map.get(z["board"]),
                # next_due 空串 = 无未来排期 (占位符专属板) → 无数据 "—"
                "earliest": z["next_due"] or None,
            }
            for z in rollup_zero
            if z["board"] not in groups  # 防御: 同板双列时到期行为准
        ]
        zero_rows.sort(key=lambda r: (r["earliest"] is None, r["earliest"] or "", r["board"]))
    else:
        zero_rows = [
            {"board": u["board"], "due": 0, "due_new": 0, "placeholder": None, "earliest": u["next_due"]}
            for u in up_gated
            if u["board"] not in groups  # 防御: 生产器不会让同板双列, 双列时到期行为准
        ]
        zero_rows.sort(key=lambda r: (r["earliest"], r["board"]))
    board_rows += zero_rows

    # round2 (Codex-D1 H5 残留): date 是生产器 date().isoformat() 产物 —
    # 词形 + 日历双验, 垃圾值不发 ok (缺省 None 容旧投影)
    date_v = payload.get("date")
    if date_v is not None:
        if not isinstance(date_v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_v):
            raise ValueError(f"date 非日历日期形态: {date_v!r}")
        try:
            datetime.strptime(date_v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"date 日历非法: {date_v!r}")
    pending = top.get("pending")
    if pending is not None:
        pending = _strict_int(pending)
    return {
        "schema_version": 3,
        "vault_id": _opt_str(payload.get("vault_id"), "vault_id"),  # C1a 加性; 旧投影缺 → null
        "date": date_v,
        "generated_at": generated_at,
        # stats.due_nodes 是 v3 权威计数 (A2 构造保证与明细同源) — 不退
        # 明细重数, 类型不符即 corrupt
        "due_count": _strict_int(stats.get("due_nodes")),
        "placeholder_backlog": len(placeholder),
        "recommended_board": _opt_str(top.get("board"), "top_boards[0].board"),
        "top_node": _opt_str(top.get("top_node"), "top_boards[0].top_node"),
        "pending": pending,
        "next_upcoming": next_up,
        # CARD-D1 加性: 板表格行 (due 来自 due_nodes group-by; 正常投影下
        # 合计==due_count, A2 同源构造保证; 手工投影不一致时两数并陈)
        "boards": board_rows,
        "due_new_count": sum(r["due_new"] for r in board_rows),
        # round2 (Codex-D1 M1 残留): rollup 在场时的板级归属合计 — 渲染层
        # 据此算"未归板"差额; 不能从 board_rows 重加 (纯无主占位符时
        # boards 为空, 差额会被错误置零)。缺省 null = rollup 不在场
        "placeholder_attributed": sum(ph_map.values()) if rollup_zero is not None else None,
        # CARD-G3-6a 加性: 五桶分层计数; 缺省 null = 旧投影无 buckets 键
        "bucket_counts": bucket_counts,
    }


def _reject_nonstandard_json(const: str):
    # json.loads 默认放行 NaN/Infinity — 非标准 JSON 不是合法 v3 投影
    raise ValueError(f"非标准 JSON 常量 {const}")


def _vault_entry(vault_dir: Path, today: date) -> dict:
    """单 vault 聚合条目 — 诚实四态, 任何脏数据都不许把请求打成 500。"""
    entry: dict = {
        "vault_id": vault_dir.name,
        "path": str(vault_dir),
        "status": "no_projection",
        "projection": None,
        "error": None,
    }
    proj_path = vault_dir.joinpath(*_PROJECTION_REL)
    try:
        raw = proj_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return entry  # 显式"无投影"降级条目 (推送管道尚未跑过该库)
    except (OSError, UnicodeDecodeError) as e:
        entry["status"] = "corrupt"
        entry["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        return entry
    try:
        payload = json.loads(raw, parse_constant=_reject_nonstandard_json, parse_float=_finite_float)
        if not isinstance(payload, dict):
            raise ValueError("投影根节点不是 JSON object")
        # Codex-D1 H2: JSON "\ud800" 转义会解出孤立 surrogate 字符串,
        # isinstance(str) 门禁放行, 到响应 UTF-8 序列化 / quote() 才炸成
        # 500 — 解析层就地折断 (UnicodeEncodeError ⊂ ValueError → corrupt)
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
        summary = _summarize(payload)
    except Exception as e:  # noqa: BLE001 — 外部文件任意形状, 统一 corrupt 降级
        entry["status"] = "corrupt"
        entry["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        return entry

    # stale 判定: 只认 A2 生产器的确切形态 (带时区秒级) — 数字串/纯日期/
    # 无时区值不许冒充今日 (Codex-C2 B2); 解析中的任何异常 (含
    # fromisoformat 通过但 astimezone 溢出的 OverflowError, Codex-C2 B1)
    # 都按 stale 降级, 绝不逃逸成 500。
    stale = True
    try:
        if _GENERATED_AT_RE.fullmatch(summary["generated_at"]):
            gen = datetime.fromisoformat(summary["generated_at"].replace("Z", "+00:00"))
            # CARD-D1: 本地日统一 Asia/Shanghai (容器 UTC 下 astimezone()
            # 会用错误的"本地日"跨午夜误判)
            stale = gen.astimezone(_TZ_SHANGHAI).date() != today
    except Exception:  # noqa: BLE001 — 畸形时间按 stale, 不装新鲜也不炸
        stale = True

    entry["status"] = "stale" if stale else "ok"
    entry["projection"] = summary
    return entry


def _collect() -> dict:
    s = get_settings()
    vaults_root = Path(s.VAULTS_ROOT).resolve()
    if not vaults_root.is_dir():
        raise HTTPException(
            status_code=500,
            detail={
                "error": "vaults_root_invalid",
                "message": f"VAULTS_ROOT not a directory: {vaults_root}",
            },
        )
    now = datetime.now(_TZ_SHANGHAI)  # CARD-D1: 全链路上海本地时区
    try:
        vault_dirs = _list_vault_dirs(vaults_root)
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "vaults_root_scan_failed", "message": str(e)},
        )
    vaults = []
    for v in vault_dirs:
        try:
            vaults.append(_vault_entry(v, now.date()))
        except Exception as e:  # noqa: BLE001 — 终极防线 (Codex-C2 B1):
            # 单库任何未预期异常都不许把全局打成 500, 以 corrupt 条目呈现;
            # traceback 落服务端日志 (兜底不等于不可观测)
            logger.exception("review_overview 单库聚合异常", vault=v.name)
            vaults.append(
                {
                    "vault_id": v.name,
                    "path": str(v),
                    "status": "corrupt",
                    "projection": None,
                    "error": f"{type(e).__name__}: {str(e)[:200]}",
                }
            )
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "vaults_root": str(vaults_root),
        "active_vault": s.ACTIVE_VAULT,
        "vaults": vaults,
    }


@review_overview_router.get(
    "/overview",
    summary="跨 vault 复习总览聚合 (CARD-C2)",
)
async def review_overview() -> dict:
    """聚合各 vault 的今日复习投影 — 只读, 缺投影/损坏均显式降级。"""
    return _collect()


_TH = (
    "padding:4px 8px;border-bottom:1px solid #e5e7eb;color:#6b7280;"
    "font-weight:500;text-align:left;white-space:nowrap;font-size:12px"
)
_TD = "padding:5px 8px;border-bottom:1px solid #f3f4f6"
_TD_NUM = _TD + ";text-align:center;white-space:nowrap"


def _board_table_html(vault_id: str, boards: list[dict], now_sh: datetime) -> str:
    """三级视图第二/三级: 板表格 白板名|到期|新卡|待剖析|最早到期。"""
    if not boards:
        return '<div style="color:#6b7280;margin:10px 0;font-size:13px">该库暂无到期或已排期的白板</div>'
    head = "".join(f'<th style="{_TH}">{c}</th>' for c in ("白板名", "到期", "新卡", "待剖析", "最早到期"))
    rows_html = []
    for r in boards:
        name = html.escape(r["board"])
        link = html.escape(_board_link(vault_id, r["board"]))
        due_disp = f"<b>{int(r['due'])}</b>" if r["due"] else '<span style="color:#9ca3af">0</span>'
        ph = "—" if r.get("placeholder") is None else str(int(r["placeholder"]))
        eta, eta_color = _humanize_due(r["earliest"], now_sh)
        rows_html.append(
            f"<tr>"
            f'<td style="{_TD}"><a href="{link}" style="color:#2563eb;text-decoration:none">{name}</a></td>'
            f'<td style="{_TD_NUM}">{due_disp}</td>'
            f'<td style="{_TD_NUM}">{int(r["due_new"])}</td>'
            f'<td style="{_TD_NUM}">{html.escape(ph)}</td>'
            f'<td style="{_TD};white-space:nowrap;color:{eta_color}">{html.escape(eta)}</td>'
            f"</tr>"
        )
    return (
        '<div style="overflow-x:auto;margin:10px 0 4px">'
        '<table style="border-collapse:collapse;width:100%;font-size:13px">'
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows_html)}</tbody></table></div>"
    )


def _card_html(entry: dict, now_sh: datetime) -> str:
    """三级视图第一级: vault 卡片 (名+四态徽标+汇总行) → 板表格。"""
    vid = html.escape(entry["vault_id"])
    label, color = _STATUS_META[entry["status"]]
    header = (
        '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
        f'<b style="font-size:16px">{vid}</b>'
        f'<span style="background:{color};color:#fff;border-radius:999px;'
        f'padding:2px 10px;font-size:12px;white-space:nowrap">{label}</span></div>'
    )
    obsidian_url = html.escape("obsidian://open?vault=" + quote(entry["vault_id"], safe=""))
    open_link = (
        f'<a href="{obsidian_url}" style="font-size:13px;color:#2563eb;text-decoration:none">在 Obsidian 中打开 ↗</a>'
    )
    proj = entry.get("projection")
    if proj:
        derived = sum(int(r["due"]) for r in proj["boards"])
        mismatch = (
            ""
            if derived == proj["due_count"]
            else f'<span style="color:#d97706;font-size:12px">（明细 {derived}）</span>'
        )
        # Codex-D1 M1: 无 source_board 的占位符只在扁平总数里 — rollup 在场
        # 且板级归属合计小于总数时标注差额 (取 placeholder_attributed 而非
        # 从行重加: 纯无主占位符时 boards 为空, 重加会把差额错误置零)
        attributed = proj.get("placeholder_attributed")
        unattributed = proj["placeholder_backlog"] - attributed if attributed is not None else 0
        ph_note = f"（含未归板 {int(unattributed)}）" if unattributed > 0 else ""
        summary = (
            f'<div style="font-size:26px;margin:8px 0 0">到期 <b>{int(proj["due_count"])}</b>{mismatch}'
            f'<span style="font-size:13px;color:#6b7280"> · 新卡 {int(proj["due_new_count"])}'
            f" · 待剖析 {int(proj['placeholder_backlog'])}{ph_note}</span></div>"
        )
        # CARD-G3-6a: 分层分布行 (缺省 = 旧投影无 buckets 键 → 整行不出现,
        # 不显示可能不可信的零)
        bc = proj.get("bucket_counts")
        layers = (
            ""
            if bc is None
            else '<div style="font-size:12px;color:#6b7280;margin:2px 0 0">分层 · '
            + " · ".join(f"{_BUCKET_CN[b]} {int(bc[b])}" for b in _BUCKET_ORDER)
            + "</div>"
        )
        gen_disp = html.escape(_fmt_projection_time(str(proj.get("generated_at") or "—")))
        body = (
            summary
            + layers
            + _board_table_html(entry["vault_id"], proj["boards"], now_sh)
            + f'<div style="color:#6b7280;font-size:12px;margin:4px 0 6px">生成于 {gen_disp}</div>'
            + open_link
        )
    elif entry["status"] == "no_projection":
        # 无投影 → 不做假链接 (现网 test-vault 死链缺陷的诚实降级)
        body = (
            '<div style="color:#6b7280;margin:12px 0;font-size:13px">该库尚无今日复习投影 — '
            "推送管道尚未为它跑过<br>深链已降级：需在 Obsidian 打开过该库后才提供跳转</div>"
        )
    else:
        err = html.escape(str(entry.get("error") or ""))
        body = (
            f'<div style="color:#dc2626;margin:12px 0">投影文件无法解析'
            f'<br><code style="font-size:11px">{err}</code></div>' + open_link
        )
    return (
        '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px 20px;'
        "flex:1 1 320px;min-width:0;max-width:520px;background:#fff;"
        'box-shadow:0 1px 3px rgba(0,0,0,.06)">'
        f"{header}{body}</div>"
    )


@review_overview_router.get(
    "/overview/page",
    response_class=HTMLResponse,
    summary="跨 vault 复习总览页 (内联 HTML, 零外部 CDN / 零 JS)",
)
async def review_overview_page() -> HTMLResponse:
    data = _collect()
    # 同一次时钟读数贯穿页面 (generated_at 是 _collect 的上海本地 iso)
    now_sh = datetime.fromisoformat(data["generated_at"])
    cards = "".join(_card_html(e, now_sh) for e in data["vaults"]) or (
        '<div style="color:#6b7280">VAULTS_ROOT 下未发现任何 vault (需含 .obsidian/ 目录)</div>'
    )
    generated = html.escape(_fmt_local_dt(now_sh))
    page = (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>跨库复习总览</title></head>"
        '<body style="font-family:-apple-system,BlinkMacSystemFont,'
        "'PingFang SC','Helvetica Neue',sans-serif;background:#f5f5f7;"
        'margin:0;padding:24px">'
        '<h1 style="font-size:22px;margin:0 0 4px">📚 跨库复习总览</h1>'
        f'<div style="color:#6b7280;font-size:13px;margin-bottom:20px">'
        f"页面生成于 {generated} · 只读聚合, 数据来自各库 outputs/今日复习.json</div>"
        f'<div style="display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start">{cards}</div>'
        '<div style="color:#9ca3af;font-size:12px;margin-top:24px">'
        "⚠ obsidian:// 跳转需在 Obsidian 打开过该库（未注册的库点击无响应）；"
        "存在同名库时可能跳到先注册的那个，以 Obsidian 侧库列表为准</div>"
        "</body></html>"
    )
    return HTMLResponse(content=page)
