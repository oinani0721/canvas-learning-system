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

CARD-G6-1 (BATCH-2026-08-31-第七批) 投影按需重建: 新增
POST /api/v1/review/overview/refresh — 显式用户触发, subprocess 直调
scripts/daily_review_pick.py --vault <该库> --write。GET 两个端点的**只读
纯度不变** (本模块仍不含第二套到期算法, 重建一律委托生产器唯一裁判);
写侧安全与 fail-closed 口径见 _rebuild_projection 的 docstring。

CARD-G6-4 (同批) 节点级明细: 板行之下加一行 details/summary 折叠区, 展开逐
节点显示 名称 / 桶位 / 到期人话 / why_due, 节点名是 obsidian://open 深链指向
节点/<name>.md。**零 schema 改动** —— 全部字段都已在 due_nodes 行里, 本卡只
是把此前只用于对账的 bucket/why_due 拿来渲染 (并因此给它们补了独立门禁:
旧投影没有 buckets 顶层键时 _gate_buckets 不跑, 这两个字段此前完全没验形)。
"""

from __future__ import annotations

import hashlib
import html
import ipaddress
import json
import math
import os
import re
import subprocess
import sys
import threading
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import structlog
from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.config import get_settings

logger = structlog.get_logger(__name__)

review_overview_router = APIRouter()

#: 每库投影相对路径 (A2: 全系统到期口径唯一裁判)
_PROJECTION_REL = ("outputs", "今日复习.json")

#: 展示时区: 统一 Asia/Shanghai (CARD-D1 — live 容器跑 UTC, astimezone()
#: 会显示 UTC 裸串差 8 小时)。容器缺 tzdata 时退化为固定 +8 (Asia/Shanghai
#: 自 1991 年起无夏令时, 固定偏移语义等价)。
#: 显示时区的名字 —— 读侧的 _TZ_SHANGHAI 与写侧子进程的 TZ 共用这一个字面量,
#: 二者永不漂移 (CARD-G6-1 收官审计)
_DISPLAY_TZ_NAME = "Asia/Shanghai"

try:
    from zoneinfo import ZoneInfo

    _TZ_SHANGHAI = ZoneInfo(_DISPLAY_TZ_NAME)
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
        # CARD-G6-4: bucket/why_due 从"只留底给 _gate_buckets 对账"升为"要渲染
        # 到页面上", 所以必须自己验形 —— 旧投影 (无 buckets 顶层键) 下
        # _gate_buckets 根本不跑, 这两个字段此前是**完全没门禁**的; 直接拿去
        # 渲染就等于开了一条形状垃圾通道。缺省 (None) 是合法的旧投影形态,
        # 有值就必须是生产器的合法取值。
        bucket = row.get("bucket")
        if bucket is not None:
            # Codex-G6-4 round-1: 只校验"属于五桶之一"不够 —— due_nodes 的行
            # **按构造只可能落三个到期桶** (生产器 S1: 到期三桶的成员恒等于
            # due_nodes 明细; due_today/future 是非到期侧, 在 due_nodes 里没有
            # 对手盘)。放行 bucket="future" 会让一个已逾期节点在页面上被标成
            # 「未来」—— 比不标更坏, 那是主动误导。
            if bucket not in _DUE_BUCKETS:
                raise ValueError(f"due_nodes[{i}].bucket 非到期桶: {bucket!r} (due_nodes 行只可能落到期三桶)")
            # 与 _gate_buckets ④ 同一条构造律的逆检查 —— 顶层无 buckets 键时
            # 那个函数根本不跑, 这条自洽性此前无人把关
            if (bucket == "new") != (reason == "new"):
                raise ValueError(f"due_nodes[{i}] bucket={bucket!r} 与 due_reason={reason!r} 不自洽")
        why = row.get("why_due")
        if why is not None and (not isinstance(why, str) or not why):
            raise ValueError(f"due_nodes[{i}].why_due 应为非空字符串或缺省, 实为 {why!r}")
        g = groups.setdefault(board, {"due": 0, "new": 0, "scheduled": 0, "earliest": "", "rows": {}})
        # CARD-G3-6a: 逐行留底 (节点身份 + 行内 bucket/why_due) 供 _gate_buckets
        # 做成员级跨源核对 —— 只留聚合计数会让"身份被替换但计数不变"的桶位
        # 投影蒙混过关 (Codex round-1 HIGH)
        g["rows"][node] = {
            "reason": reason,
            "fsrs_due": ts,
            "bucket": bucket,
            "why_due": why,
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


def _node_link(vault_id: str, node: str) -> str:
    """obsidian:// 节点深链 (CARD-G6-4) —— 节点名==扁平池文件 stem 约定。

    与 _board_link 同一条编码纪律: `safe=""` 让路径分隔符 `/` 也被
    percent-encode 成 `%2F` —— 节点名里出现 `/`(macOS 目录名里非法但 JSON
    投影里可以有)、`&`、`#`、`?` 时, 不转义会把 query 参数截断成另一个链接。
    库名与节点名分别编码, 不拼完再编。
    """
    return "obsidian://open?vault=" + quote(vault_id, safe="") + "&file=" + quote(f"节点/{node}.md", safe="")


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
        {
            "board": b,
            "due": g["due"],
            "due_new": g["new"],
            "placeholder": ph_map.get(b),
            "earliest": g["earliest"],
            # CARD-G6-4 加性: 板内到期节点明细 (纯消费既有 due_nodes 行, 零 schema 改动)
            "nodes": _node_rows(g["rows"]),
        }
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
                "nodes": [],  # 零到期板没有到期节点可展开 (未来节点不在 due_nodes 里)
            }
            for z in rollup_zero
            if z["board"] not in groups  # 防御: 同板双列时到期行为准
        ]
        zero_rows.sort(key=lambda r: (r["earliest"] is None, r["earliest"] or "", r["board"]))
    else:
        zero_rows = [
            {
                "board": u["board"],
                "due": 0,
                "due_new": 0,
                "placeholder": None,
                "earliest": u["next_due"],
                "nodes": [],
            }
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


def _node_rows(rows: dict[str, dict]) -> list[dict]:
    """板内到期节点明细 (CARD-G6-4) —— 纯消费 _gate_due_groups 已门禁过的行。

    排序 = 紧迫度降序, 与既有板级 `earliest` 的口径**同一条规则**:
    已排期的到期时刻恒在过去, 越早越紧迫, 所以先按非空时间戳升序; 新卡的
    fsrs_due 是空串 (语义 = 现在), 排在已逾期节点之后 —— 字典序把 "" 当最小
    会让"逾期 3 天"被"现在"盖掉, 那正是 D1 复核抓过的低估紧迫度缺陷, 这里
    不许在明细里重犯一遍。同刻按节点名稳定排序 (防同分随机漂)。

    bucket / why_due 可能为 None (G3-6a 之前的旧投影没有这两个字段) —— 渲染层
    据此降级为"—", 不伪造分层标签。
    """
    return sorted(
        (
            {
                "node": node,
                "due_reason": meta["reason"],
                "fsrs_due": meta["fsrs_due"],
                "bucket": meta["bucket"],
                "why_due": meta["why_due"],
            }
            for node, meta in rows.items()
        ),
        key=lambda r: (r["fsrs_due"] == "", r["fsrs_due"], r["node"]),
    )


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
    try:
        vaults_root = Path(s.VAULTS_ROOT).resolve()
    except OSError as e:
        # 防御深度 (Codex round-3 提出; 本平台未复现 resolve 抛错, 如实登记):
        # 本端点的全部错误路径都该是 503, 不许有一条能逃逸成 500
        raise HTTPException(
            status_code=503,
            detail={"error": "vaults_root_invalid", "message": f"{type(e).__name__}: {str(e)[:200]}"},
        )
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


#: 节点明细行样式 (CARD-G6-4) —— 全部相对单位 + 允许折行, 375px 窄窗不横溢
_NODE_LI = "margin:0 0 6px;list-style:none;line-height:1.5;overflow-wrap:anywhere;word-break:break-word"
#: 桶位小标签
_NODE_TAG = (
    "display:inline-block;background:#f3f4f6;color:#4b5563;border-radius:4px;"
    "padding:0 6px;font-size:11px;margin-left:6px;white-space:nowrap"
)


def _node_detail_html(vault_id: str, nodes: list[dict], now_sh: datetime) -> str:
    """板行下的节点级明细 (CARD-G6-4): 名称 + 桶位 + 到期人话 + why_due + 深链。

    纯 `<details>/<summary>` 折叠, 零 JS。每个节点名是一条 obsidian:// 深链,
    点了直接开那个节点 md。
    bucket / why_due 缺省 (G3-6a 之前的旧投影) 时整块不出现 —— 不伪造分层标签,
    与卡片汇总行"无 buckets 就不显示分层行"同一条纪律。
    """
    if not nodes:
        return ""
    items = []
    for n in nodes:
        name = html.escape(n["node"])
        link = html.escape(_node_link(vault_id, n["node"]))
        eta, eta_color = _humanize_due(n["fsrs_due"], now_sh)
        tag = (
            ""
            if n.get("bucket") is None
            else f'<span style="{_NODE_TAG}">{html.escape(_BUCKET_CN[n["bucket"]])}</span>'
        )
        why = (
            ""
            if not n.get("why_due")
            else f'<div style="color:#6b7280;font-size:12px;margin-top:1px">{html.escape(n["why_due"])}</div>'
        )
        items.append(
            f'<li style="{_NODE_LI}">'
            f'<a href="{link}" style="color:#2563eb;text-decoration:none">{name}</a>'
            f"{tag}"
            f'<span style="color:{eta_color};font-size:12px;margin-left:6px">{html.escape(eta)}</span>'
            f"{why}</li>"
        )
    return (
        f'<details style="margin:2px 0 4px"><summary style="cursor:pointer;color:#6b7280;'
        f'font-size:12px;padding:2px 0">展开 {len(nodes)} 个到期节点</summary>'
        f'<ul style="margin:6px 0 2px;padding:0">{"".join(items)}</ul></details>'
    )


def _board_table_html(vault_id: str, boards: list[dict], now_sh: datetime) -> str:
    """三级视图第二/三级: 板表格 白板名|到期|新卡|待剖析|最早到期。

    CARD-G6-4: 有到期节点的板在数据行之下多一行 `colspan=5` 的折叠区
    (`<details>`)。放在整宽的第二行而不是塞进"白板名"那一格 —— 塞进单元格
    会把第一列撑宽、把其余四列挤扁, 375px 窄窗尤其难看。
    """
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
        detail = _node_detail_html(vault_id, r.get("nodes") or [], now_sh)
        if detail:
            rows_html.append(f'<tr><td colspan="5" style="{_TD};padding-top:0">{detail}</td></tr>')
    return (
        '<div style="overflow-x:auto;margin:10px 0 4px">'
        '<table style="border-collapse:collapse;width:100%;font-size:13px">'
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows_html)}</tbody></table></div>"
    )


#: 刷新按钮样式 (CARD-G6-1) — 与页面既有配色同族, 无外部资源
_BTN = (
    "font-size:13px;color:#2563eb;background:#eff6ff;border:1px solid #bfdbfe;"
    "border-radius:6px;padding:3px 10px;cursor:pointer;font-family:inherit"
)


def _refresh_form_html(vault_id: str, action: str) -> str:
    """「刷新投影」表单按钮 — 纯 HTML form POST, 零 JS。

    redirect=page 让端点以 303 回本页 (PRG): 浏览器刷新不会重复提交,
    也就不会绕过 TTL 去抖反复起子进程。
    """
    return (
        f'<form method="post" action="{html.escape(action)}" style="display:inline;margin:0">'
        f'<input type="hidden" name="vault_id" value="{html.escape(vault_id)}">'
        '<input type="hidden" name="redirect" value="page">'
        f'<button type="submit" style="{_BTN}">🔄 刷新投影</button></form>'
    )


def _card_html(entry: dict, now_sh: datetime, refresh_action: str) -> str:
    """三级视图第一级: vault 卡片 (名+四态徽标+汇总行) → 板表格 → 操作行。"""
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
    # CARD-G6-1 操作行: 四态一律给刷新按钮 —— no_projection 恰恰是最需要它
    # 的一态 (推送管道还没为该库跑过, 点一次就有了)
    actions = (
        '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:10px">'
        + _refresh_form_html(entry["vault_id"], refresh_action)
        + "</div>"
    )
    return (
        '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px 20px;'
        "flex:1 1 320px;min-width:0;max-width:520px;background:#fff;"
        'box-shadow:0 1px 3px rgba(0,0,0,.06)">'
        f"{header}{body}{actions}</div>"
    )


@review_overview_router.get(
    "/overview/page",
    response_class=HTMLResponse,
    summary="跨 vault 复习总览页 (内联 HTML, 零外部 CDN / 零 JS)",
)
async def review_overview_page(request: Request) -> HTMLResponse:
    data = _collect()
    # 同一次时钟读数贯穿页面 (generated_at 是 _collect 的上海本地 iso)
    now_sh = datetime.fromisoformat(data["generated_at"])
    # 表单 action 用 url_for 的 **path**: 前缀改了不会漂 (硬编码 /api/v1/…
    # 会), 取 .path 而非绝对 URL 则不受反代改 host/scheme 影响
    refresh_action = request.url_for("review_overview_refresh").path
    cards = "".join(_card_html(e, now_sh, refresh_action) for e in data["vaults"]) or (
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
        f"页面生成于 {generated} · 只读聚合, 数据来自各库 outputs/今日复习.json"
        f" · 「刷新投影」按需重建该库投影（只写它自己的 outputs/今日复习.*）</div>"
        f'<div style="display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start">{cards}</div>'
        '<div style="color:#9ca3af;font-size:12px;margin-top:24px">'
        "⚠ obsidian:// 跳转需在 Obsidian 打开过该库（未注册的库点击无响应）；"
        "存在同名库时可能跳到先注册的那个，以 Obsidian 侧库列表为准</div>"
        "</body></html>"
    )
    return HTMLResponse(content=page)


# ════════════════════════════════════════════════════════════════════
# CARD-G6-1 投影按需重建 (BATCH-2026-08-31-第七批)
# ════════════════════════════════════════════════════════════════════

#: 去抖窗口 (秒): 窗口内的重复 refresh 直接复用上次重建结果, 不再起子进程。
#: 单调钟计量 —— 系统时钟被回拨不会让窗口永久卡死或整体失效。
_REFRESH_TTL_SECONDS = 10.0

#: 子进程墙钟上限 (秒)。超时按 fail-closed 报 503, 不装成功。
_REFRESH_TIMEOUT_SECONDS = 120.0

#: 生产器脚本的显式指定口 (部署逃生阀 — 见 _pick_script_candidates)
_PICK_SCRIPT_ENV = "DAILY_REVIEW_PICK"

#: 仓库内生产器相对路径 (A2 唯一裁判; 本端点严禁实现第二套到期算法)
_PICK_REL = ("scripts", "daily_review_pick.py")

#: per-vault 去抖账与串行锁。key = **已解析的 vault 目录绝对路径** (不是
#: vault_id): 不同 VAULTS_ROOT 下的同名库是两个库, 用名字做 key 会让它们
#: 共享同一个去抖窗口与计数。
_refresh_guard = threading.Lock()  # 只保护下面三个字典的惰性建键
_refresh_locks: dict[str, threading.Lock] = {}
_refresh_marks: dict[str, float] = {}
_refresh_counts: dict[str, int] = {}


def _pick_script_candidates(vaults_root: Path) -> list[Path]:
    """生产器脚本候选路径, 按可信度降序。

    1. 环境变量 _PICK_SCRIPT_ENV — 部署方显式指定, 无歧义;
    2. 与**正在运行的后端代码同一份 checkout** 的 scripts/ (本文件在
       backend/app/api/v1/endpoints/ → parents[5] = 仓库根)。语义最强:
       脚本与端点同 commit。容器里 /app 是 backend/ 本身, parents[5] 退化
       为 `/` → `/scripts/...` 不存在, 自然落空而非误命中;
    3. VAULTS_ROOT/scripts/ — 卡文点名的路径耦合。⚠ 这条是纯路径巧合,
       仅当 VAULTS_ROOT 恰好指向含 scripts/ 的仓库根时成立。

    全部落空即 503 (见 _resolve_pick_script) —— 绝不退化成「本地重算一份
    到期口径」, 那会立刻造出 A2 明令禁止的第二套裁判。
    """
    cands: list[Path] = []
    env = os.environ.get(_PICK_SCRIPT_ENV)
    if env:
        cands.append(Path(env))
    try:
        cands.append(Path(__file__).resolve().parents[5].joinpath(*_PICK_REL))
    except IndexError:
        # 本文件被放到浅于 5 层的路径上 (打包/单文件部署): 这条候选不成立,
        # 但不该把整个端点打成 500 —— 少一条候选而已, 其余照试
        pass
    cands.append(vaults_root.joinpath(*_PICK_REL))
    seen: set[str] = set()
    uniq: list[Path] = []
    for c in cands:
        k = str(c)
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    return uniq


def _resolve_pick_script(vaults_root: Path) -> Path:
    """定位生产器脚本; 找不到 → 503 fail-closed (附已试路径便于诊断)。"""
    tried: list[str] = []
    for c in _pick_script_candidates(vaults_root):
        tried.append(str(c))
        try:
            if c.is_file():
                return c
        except OSError:  # 路径过长 / 权限 / 断链 symlink: 当作未命中继续
            continue
    raise HTTPException(
        status_code=503,
        detail={
            "error": "pick_script_not_found",
            "message": (
                "未找到 daily_review_pick.py — 投影重建委托生产器唯一裁判, "
                f"脚本不可达时拒绝服务而非本地重算。可用环境变量 {_PICK_SCRIPT_ENV} 显式指定。"
            ),
            "tried": tried,
        },
    )


#: 子进程环境白名单 —— 只透传这些, 其余一律不带 (见 _child_env)。
#: ⛔ TZ **不在**白名单里: 它由 _child_env 强制设成 _DISPLAY_TZ_NAME, 不接受
#: 父进程的值 (容器里父进程的 TZ 是空的, 空 = UTC = 错日期)
_ENV_PASSTHROUGH = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "SYSTEMROOT")


def _child_env() -> dict[str, str]:
    """生产器子进程的环境 —— 白名单, 不是 `dict(os.environ)`。

    整份继承会把父进程环境变成一条注入面: `PYTHONPATH` 能让子进程
    `import decay_beta` 解析到**库外**的另一个模块 (生产器用
    sys.path.insert 把库内目录插到最前, 但 PYTHONPATH 的目录同样在
    sys.path 上, 库内没有该文件时就轮到它), 那段代码在后端进程的权限下
    执行、想写哪儿写哪儿 —— Codex 探针 INHERITED_ENV 实测成立。
    `PYTHONSTARTUP` / `PYTHONHOME` / `PYTHONWARNINGS` 同族。

    白名单只保留跑一个 stdlib 脚本真正需要的: 解释器路径查找 (PATH)、
    临时目录、locale。

    ⛔ TZ 是**强制**设成显示时区, 不是"有就透传": 生产器的
    `payload["date"] = now.astimezone().date().isoformat()` 与由它派生的
    md 标题 `# 今日复习 · <date>`、Bark 通知 id `canvas-review-<date>` 全都
    走**进程本地时区**。而后端容器 `TZ` 为空、`/etc/localtime -> Etc/UTC`
    (现网实测), 于是上海 00:00-08:00 这 8 小时里 refresh 产出的是**昨天**的
    日期 —— 端点照样返回 rebuilt=true / status=ok, 页面上没有任何异常信号,
    正是"静默产出错日期"。宿主 launchd runner 跑在 Asia/Shanghai 下产出的
    是正确日期, 于是同一个库的两条生成路径会给出不同的 date, 取决于谁最后写。

    这条坑本文件读侧早已点名并修掉 (stale 判定用 `astimezone(_TZ_SHANGHAI)`,
    见 _vault_entry 的注释), 本卡新开的**写侧**必须同口径, 否则等于把它原样
    搬了回来。用同一个 _DISPLAY_TZ_NAME 字面量, 读写两侧永不漂移。
    (收官审计实测: TZ=Asia/Shanghai → date=2026-08-31, TZ=UTC → date=2026-08-30,
     同一时刻同一个库。)

    PYTHONDONTWRITEBYTECODE=1 不是可选项: 生产器的 load_decay() 会
    `import decay_beta`, 该模块在 **vault 内** (<vault>/.claude/scripts/),
    不禁字节码就会在库里落 __pycache__/ —— 直接打破「只写 outputs/今日
    复习.*」的写面承诺, 且这类残渣会被 Obsidian 同步/备份链一路带走。
    PYTHONNOUSERSITE=1 同理堵掉 ~/.local/lib 的用户级 site-packages。
    """
    env = {k: v for k in _ENV_PASSTHROUGH if (v := os.environ.get(k)) is not None}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    # 强制, 不是透传 —— 见上面 docstring。父进程的 TZ 不参与决定 (容器里它是空的,
    # 空就等于 UTC; 而"读侧显示用 Shanghai、写侧落盘用 UTC"是不能存在的组合)
    env["TZ"] = _DISPLAY_TZ_NAME
    return env


def _run_pick(script: Path, vault_dir: Path) -> subprocess.CompletedProcess:
    """跑 `python <script> --vault <vault> --write` (写面只有 outputs/今日复习.*)。"""
    # stdout 丢弃 (Codex round-3): 生产器会把整份 payload 打到 stdout —— 大库
    # 里那是几 MB 的无用副本, 我们只从盘上读产物。errors="replace": 子进程
    # 若吐出非法字节, 严格解码会抛 UnicodeDecodeError 逃逸成 500, 而这里的
    # 全部错误路径都该是 503。
    return subprocess.run(  # noqa: S603 — argv 列表 + 服务端自解析路径, 无 shell
        [sys.executable, str(script), "--vault", str(vault_dir), "--write"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
        timeout=_REFRESH_TIMEOUT_SECONDS,
        cwd=str(script.parent),
        env=_child_env(),
        check=False,
    )


#: 生产器对一个库的最低要求, (相对路径, 是否应为目录)。
#: daily_review_pick.scan_nodes 扫 节点/; load_decay 从库内 .claude/scripts 导 decay_beta。
#: ⚠ 收官审计: 这个常量一度成了**死常量** —— 定义在这里带着"最低要求"的注释,
#: 而 _pick_failure_hint 里内联重写了同一对判据, 全仓零引用它。以后有人按注释
#: 改这里, 提示文案不会跟着变且无人报警。现在由 _pick_failure_hint 唯一消费。
_REVIEW_ENABLED_MARKERS = (("节点", True), (".claude/scripts/decay_beta.py", False))


def _pick_failure_hint(vault_dir: Path) -> str | None:
    """失败后的人话诊断 —— **只读检查, 不参与"要不要重建"的决策**。

    刻意不做成 pre-flight 准入: 生产器在哪儿找 decay_beta 是它自己的约定
    (load_decay), 在端点里复刻成准入条件就多出一个会漂的真相源 —— 漂了会
    把本来能跑的库挡在门外。放在失败之后当提示, 漂了最多是提示没用。

    最常见的真实场景: 一个只有 .obsidian/ 的库 (被库枚举捞进来但从没为
    每日复习配过), 点刷新时生产器抛 ModuleNotFoundError: decay_beta ——
    直接把 traceback 甩给用户等于没解释。
    """
    # Codex round-3: 原来用 .exists(), 一个普通文件叫「节点」或一个目录叫
    # 「decay_beta.py」都会被判成"配置齐全"(实测确认) —— 按类型逐项判。
    # (它同时断言 .exists() 会抛异常把 503 打成 500 —— 实测**不成立**:
    #  Path.exists() 内部吞 OSError/ValueError, 软链自环下返回 False。这里
    #  仍包一层 try 只是防御深度, 不宣称修掉了一个已复现的缺陷。)
    try:
        missing = [
            rel
            for rel, want_dir in _REVIEW_ENABLED_MARKERS
            if not ((vault_dir / rel).is_dir() if want_dir else (vault_dir / rel).is_file())
        ]
    except OSError:
        return None  # 提示是锦上添花, 探不出来就不提示, 绝不影响主判定
    if not missing:
        return None
    return (
        "该库还没为「每日复习」配置好: 缺 "
        + " 与 ".join(missing)
        + " —— 每日复习需要库内有 节点/ 池和 .claude/scripts/decay_beta.py"
    )


def _refresh_key(vault_dir: Path) -> str:
    """去抖账 / 串行锁的 key = **物理路径**。

    Codex round-1 (BLOCKER-2 附带): VAULTS_ROOT 下两个软链别名指向同一个
    物理库时, 用字面路径做 key 会给它们两把锁、两本去抖账 —— 同一个物理
    库能被两条别名并发重建。resolve 后同一物理库恒得同一把锁。
    """
    try:
        return str(vault_dir.resolve())
    except OSError as e:
        # Codex round-3: 退回字面路径会重新把同一物理库的两条别名拆成两把锁 ——
        # 那正是本函数要消灭的东西。解析不了就 fail-closed 拒绝重建。
        raise HTTPException(
            status_code=503,
            detail={"error": "path_resolve_failed", "message": f"{type(e).__name__}: {str(e)[:200]}"},
        )


#: 投影产物相对路径 (生产器 --write 的全部写面)
_PROJECTION_MD_REL = ("outputs", "今日复习.md")


def _publish_fingerprint(path: Path) -> tuple[int, int, str] | None:
    """(st_ino, st_mtime_ns, sha256) —— 证明「**这一次**真的发布了产物」。

    Codex round-3 HIGH: 只看"盘上有一份可消费 JSON"证不了本次重建成功 ——
    一个 rc=0 却什么都不写的生产器, 若盘上原本就有昨天的好投影, 会被算成
    本次重建成功。生产器发布走 os.replace(新写的 tmp): 路径改指向一个新建
    的 inode, 于是 inode 变、mtime 变; 内容变了 sha 也变。三者全没动 =
    什么都没发布。

    ⚠ 为什么必须三个信号一起用 (实测, 不是推测):
    - **只用 sha 不成立**: generated_at 是**秒级**精度, 同一秒内的两次重建
      产出**逐字节相同**的文件 (本机实测 5 次连点 sha 全等)。
    - **只用 mtime 不成立**: mtime 粒度随文件系统而变 —— 容器 /tmp 的
      overlayfs 上 6 次连续 os.replace 只得到 3 个不同 mtime (实测)。
    - inode 在生产路径上是最强的那个: /vaults 的 VirtioFS 与宿主 APFS 都是
      6/6 全不同 (实测)。

    ⚠ 残余 (如实登记, 不假装堵住): 在**同时**具备 inode 复用与粗粒度 mtime
    的文件系统上 (实测 /tmp overlayfs 就是: inode 在两个值间轮换),
    "同一 tick 内内容无变化的重建" 仍可能三个信号全等而被判成「没发布」。
    该误判方向是 **fail-closed** —— 用户看到 503 而不是假成功, 盘上数据仍
    正确。且它在生产挂载上不可达 (上面两组实测)。VAULTS_ROOT 若被指到
    这类文件系统, 现象是"刷新恒 503 projection_not_republished", 日志里有
    明确哨兵可查。
    """
    try:
        st = path.stat()
        return (st.st_ino, st.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    except OSError:
        return None


def _read_entry(vault_dir: Path) -> dict:
    """读回该库的聚合条目 —— 与 _collect 同一条终极防线, 绝不逃逸成 500。"""
    try:
        return _vault_entry(vault_dir, datetime.now(_TZ_SHANGHAI).date())
    except Exception as e:  # noqa: BLE001
        logger.exception("review_overview refresh 读回异常", vault=vault_dir.name)
        return {
            "vault_id": vault_dir.name,
            "path": str(vault_dir),
            "status": "corrupt",
            "projection": None,
            "error": f"{type(e).__name__}: {str(e)[:200]}",
        }


def _rebuild_projection(vault_dir: Path, script: Path) -> tuple[dict, dict | None]:
    """per-vault 串行 + TTL 去抖地重建一次投影 (同步; 由 FastAPI 线程池承载)。

    ── 写侧安全 (本函数的全部承诺) ──
    ① 只写 outputs/今日复习.md + .json: 生产器 --write 的写面就是这两个文件
       (加 outputs/ 目录本身的 mkdir), 配 PYTHONDONTWRITEBYTECODE 堵掉
       vault 内 __pycache__ 这条隐藏写面;
    ② 不走 runner、不写 runner state: 不传 --state (生产器对 state 本就
       只读), 更不碰 backups/daily-review.*.state.json —— 结构性保证, 不
       靠约定。**代价如实登记**: runner 的 board_last_recommended 记录不
       参与本次 tie-break, 故同分并列的板在 refresh 与 launchd 跑批之间
       可能排序不同 (取 board_last_recommended 需要 send_bark.vault_key
       的命名规则, 那是本卡硬边界外的文件, 不为一个排序细节去耦合它);
    ③ 落盘撕裂: 生产器侧 atomic_write 已改 tmp 唯一化 + os.replace, 与
       宿主 launchd 跑批并发时最坏结果是「后写者覆盖先写者」而非拼接损坏;
    ④ 去抖: 同一库 TTL 窗口内只有第一次真起子进程, 其余直接读盘返回。
    ⑤ 同库已有重建在飞时**不排队**, 立刻以 in_progress 返回: sync 端点跑在
       FastAPI 的共享线程池里 (默认 40 线程), 阻塞等锁会让连点把整池占满,
       连只读的 /overview 都被拖住 —— 快速如实回话比排队更诚实也更安全。

    失败一律抛 HTTPException(503) —— 拿不到重建结果时返回旧投影并宣称
    成功, 就是卡文点名要堵的「静默假成功」。

    ⚠ 已知残余 (如实登记, 不假装堵住): 子进程若在 write_text 与 os.replace
    之间被超时 kill (SIGKILL 不走 except 分支), 会在 outputs/ 里留下一个
    `今日复习.*.tmp` 残渣。不做"清扫陈旧 tmp"是刻意的 —— 清扫无法区分
    "陈旧残渣"与"另一个写者正在用的 tmp", 误删后者会把并发写直接打断,
    比留一个无害残渣糟得多。该残渣名仍在 `今日复习.*` 前缀内。
    """
    key = _refresh_key(vault_dir)
    with _refresh_guard:
        lock = _refresh_locks.setdefault(key, threading.Lock())
    if not lock.acquire(blocking=False):
        return {
            "rebuilt": False,
            "reason": "in_progress",
            "duration_ms": None,
            "retry_after_seconds": round(_REFRESH_TTL_SECONDS, 3),
            "rebuild_count": _refresh_counts.get(key, 0),
        }, None
    try:
        now = time.monotonic()
        last = _refresh_marks.get(key)
        if last is not None and (now - last) < _REFRESH_TTL_SECONDS:
            return {
                "rebuilt": False,
                "reason": "debounced",
                "duration_ms": None,
                "retry_after_seconds": round(_REFRESH_TTL_SECONDS - (now - last), 3),
                "rebuild_count": _refresh_counts.get(key, 0),
            }, None
        started = time.monotonic()
        json_path = vault_dir.joinpath(*_PROJECTION_REL)
        md_path = vault_dir.joinpath(*_PROJECTION_MD_REL)
        before_fp = _publish_fingerprint(json_path)
        try:
            proc = _run_pick(script, vault_dir)
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "pick_timeout",
                    "message": f"生产器超过 {_REFRESH_TIMEOUT_SECONDS:g}s 未返回, 投影未重建",
                },
            )
        except OSError as e:
            raise HTTPException(
                status_code=503,
                detail={"error": "pick_spawn_failed", "message": f"{type(e).__name__}: {str(e)[:200]}"},
            )
        if proc.returncode != 0:
            # stderr 尾部足以定位 (argparse 报错 / traceback 末行), 不回全文
            detail = {
                "error": "pick_failed",
                "message": "生产器非零退出, 投影未重建",
                "returncode": proc.returncode,
                "stderr_tail": (proc.stderr or "")[-800:],
            }
            hint = _pick_failure_hint(vault_dir)
            if hint:
                detail["hint"] = hint
            raise HTTPException(status_code=503, detail=detail)
        elapsed_ms = round((time.monotonic() - started) * 1000, 1)
        # rc=0 还不算重建成功 (Codex round-1 HIGH-1 + round-3 收紧)。
        # 两道独立的证明, 缺一不可:
        #   ① **发布证明** —— json 的 (mtime_ns, sha256) 相对本次调用前必须变过,
        #      且 md 必须在位。只查"盘上有一份可消费 JSON"证不了本次重建成功:
        #      一个 rc=0 却什么都不写的生产器, 在盘上原本就有昨天好投影的库上
        #      会被算成成功 (round-3 实证)。生产器发布走 os.replace(新写的 tmp),
        #      每次发布必得新 mtime, 所以"两者都没动"= 什么都没发布。
        #   ② **可消费证明** —— 读回来必须过 schema v3 门禁。
        # 任一不成立都不提交 TTL mark / 计数 —— 否则用户修好之前的每次点击
        # 都被去抖吃掉, 永远修不回来。
        after_fp = _publish_fingerprint(json_path)
        if after_fp is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "projection_missing_after_rebuild",
                    "message": "生产器退出码为 0, 但盘上仍没有 outputs/今日复习.json — 未视为重建成功",
                    "stderr_tail": (proc.stderr or "")[-400:],
                },
            )
        if after_fp == before_fp:
            # 哨兵: 这条也可能是"文件系统 inode 复用 + 粗粒度 mtime"造成的误判
            # (见 _publish_fingerprint 的残余登记) —— 把三元组打进日志, 现场可辨
            logger.error(
                "review_overview refresh 判定未发布",
                vault=vault_dir.name,
                fingerprint=str(after_fp),
                hint="若该 vault 所在文件系统 inode 复用且 mtime 粗粒度, 这可能是误判",
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "projection_not_republished",
                    "message": (
                        "生产器退出码为 0, 但 outputs/今日复习.json 的 inode/mtime/内容三者与调用前全等"
                        " — 本次什么都没发布"
                    ),
                    "stderr_tail": (proc.stderr or "")[-400:],
                },
            )
        if not md_path.is_file():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "projection_md_missing",
                    "message": "生产器退出码为 0, 但 outputs/今日复习.md 不在位 — 产物不成对, 未视为重建成功",
                    "stderr_tail": (proc.stderr or "")[-400:],
                },
            )
        entry = _read_entry(vault_dir)
        if entry["status"] == "corrupt":
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "projection_corrupt_after_rebuild",
                    "message": "生产器退出码为 0, 但产出的投影过不了 schema v3 门禁 — 未视为重建成功",
                    "projection_error": entry.get("error"),
                },
            )
        _refresh_marks[key] = time.monotonic()
        _refresh_counts[key] = _refresh_counts.get(key, 0) + 1
        return {
            "rebuilt": True,
            "reason": "rebuilt",
            "duration_ms": elapsed_ms,
            "retry_after_seconds": 0.0,
            "rebuild_count": _refresh_counts[key],
        }, entry
    finally:
        lock.release()


def _assert_write_target_contained(vault_dir: Path, vaults_root: Path) -> None:
    """写目标必须真的落在这个库里 —— 符号链接逃逸 fail-closed。

    `_list_vault_dirs` 用 `is_dir()` 枚举, 它**跟随符号链接**: VAULTS_ROOT 下
    一个指向任意目录的软链只要那边有 .obsidian/, 就会被当成一个库列出来,
    然后 refresh 会往库外写 (Codex 探针 VAULT_SYMLINK 实测成立)。同理
    `<vault>/outputs` 若是指向库外的软链, 生产器的两个产物就落在库外
    (探针 OUTPUTS_SYMLINK 实测成立) —— 那时"只写 outputs/今日复习.*"
    这句话字面还成立, 实际写面却已经出了库。

    两条都按 realpath 归属判定, 不成立即 503 拒绝重建。

    ⚠ 残余 (如实登记, 与本仓 C1 的 TOCTOU 记录同口径): 判定与子进程真正
    open() 之间非原子 —— 在这中间把 outputs 换成软链仍可绕过。堵住的是
    "已经存在的逃逸链", 不是"判定后现换链"。
    """
    try:
        real_root = vaults_root.resolve()
        real_vault = vault_dir.resolve()
    except OSError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "path_resolve_failed", "message": f"{type(e).__name__}: {str(e)[:200]}"},
        )
    if real_vault != real_root and real_root not in real_vault.parents:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "vault_outside_root",
                "message": f"库 {vault_dir.name!r} 的真实路径在 VAULTS_ROOT 之外 (软链逃逸), 拒绝写入",
                "real_path": str(real_vault),
            },
        )
    out = vault_dir / "outputs"
    if out.exists():
        try:
            real_out = out.resolve()
        except OSError as e:
            raise HTTPException(
                status_code=503,
                detail={"error": "path_resolve_failed", "message": f"{type(e).__name__}: {str(e)[:200]}"},
            )
        if real_out != real_vault and real_vault not in real_out.parents:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "outputs_outside_vault",
                    "message": f"库 {vault_dir.name!r} 的 outputs/ 真实路径在库外 (软链逃逸), 拒绝写入",
                    "real_path": str(real_out),
                },
            )


def _refresh_target(vault_id: str) -> tuple[Path, Path]:
    """(vault 目录, 生产器脚本) — 三道 fail-closed 门全过才返回。

    vault_id 必须**命中枚举出来的真实目录名** (与 GET /overview 同一条
    候选规则), 不是「拼路径再看存不存在」: 候选集本身就是枚举结果, 天然
    没有 ../ 遍历与符号链接逃逸的入口。
    """
    s = get_settings()
    vaults_root = Path(s.VAULTS_ROOT).resolve()
    if not vaults_root.is_dir():
        raise HTTPException(
            status_code=503,
            detail={"error": "vaults_root_invalid", "message": f"VAULTS_ROOT not a directory: {vaults_root}"},
        )
    try:
        vault_dirs = _list_vault_dirs(vaults_root)
    except OSError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "vaults_root_scan_failed", "message": f"{type(e).__name__}: {str(e)[:200]}"},
        )
    match = next((d for d in vault_dirs if d.name == vault_id), None)
    if match is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "vault_not_found",
                "message": f"VAULTS_ROOT 下无名为 {vault_id!r} 的库 (需含 .obsidian/)",
                "known": [d.name for d in vault_dirs],
            },
        )
    _assert_write_target_contained(match, vaults_root)
    return match, _resolve_pick_script(vaults_root)


#: 额外放行的 Host (逗号分隔) —— 默认只放行 localhost 与 IP 字面量;
#: 需要按主机名访问 (Tailscale MagicDNS / mDNS 名) 时由部署方显式列出
_ALLOWED_HOSTS_ENV = "REVIEW_REFRESH_ALLOWED_HOSTS"


def _extra_allowed_hosts() -> frozenset[str]:
    """解析白名单并**归一到与 request.url.hostname 同一形态**。

    收官审计: `request.url.hostname` 是 urlsplit 归一过的 —— **小写、不含端口、
    IPv6 去方括号**。而白名单原来只 strip 后裸比, 于是用户照着地址栏里看到的
    东西去配 (`My-Mac.local` 或 `my-mac.local:8011`) 会继续 403, 错误信息还
    只说"逗号分隔列出", 没说必须小写、不带端口 —— 一个"照做了却还是不行"的坑。
    这里替用户把大小写、端口、方括号都吃掉。
    """
    out = set()
    for raw in os.environ.get(_ALLOWED_HOSTS_ENV, "").split(","):
        h = raw.strip().lower()
        if not h:
            continue
        if h.startswith("["):  # [::1]:8011 / [::1]
            h = h[1:].split("]", 1)[0]
        elif h.count(":") == 1:  # host:port (IPv6 裸串含多个冒号, 不在此列)
            h = h.split(":", 1)[0]
        if h:
            out.add(h)
    return frozenset(out)


def _assert_same_origin(request: Request) -> None:
    """状态变更请求的同源门 (纯 HTML 表单可用, 零 JS)。

    ⚠ 事实更正 (收官审计): 本后端**并非**全站无鉴权 —— `app/security.py` 的
    `require_internal_api_key` 是成体系的写侧约定 (sync / boards / memory /
    exam_sessions / system 与 chat router 都挂了它, 现网 INTERNAL_API_KEY 已配)。
    本端点没挂它, 是因为它读自定义请求头 `X-CLS-Internal-Key`, 而卡文硬要求的
    "纯 HTML 表单、零 JS" 发不出自定义头 —— 二者不可兼得, 已上用户裁决点 D-7。
    在那之前本端点对"能连到这个端口的人"是敞开的; 下面这道门只解决 CSRF。

    这个端点会**写文件并起 Python
    子进程** —— 用户在浏览器里打开的任意页面, 只要放一个跨站 <form
    action="http://localhost:8011/...">, 浏览器就会替用户把这个 POST 发出去;
    CORS 只挡"读响应", 挡不住副作用。这是本端点独有的新暴露面 (GET 侧只读,
    没有这个问题), 所以门开在这里而不是全站。

    判据用浏览器一定会带的两个头:
      Sec-Fetch-Site — 跨站表单为 cross-site/same-site, 必须是 same-origin 或 none;
      Origin         — 跨站表单必带且为对方站点, 必须与本请求同源。
    两个头都没有 (curl / 本地脚本 / 验收脚本) 则放行 —— 非浏览器客户端本来
    就不受 CSRF 摆布, 强制要求会把命令行调用全挡死。

    ⚠ 这不是鉴权: 同机的任意进程仍能直接调它 (全站皆然)。堵住的是"用户
    浏览器被别的网页当枪使"这一条, 不是"本机进程越权"。
    """
    # Codex round-3: 期望 Origin 是拿请求自身的 Host 拼的 —— DNS rebinding 下
    # 攻击者的域名解析到 127.0.0.1, 于是 Host / Origin / Sec-Fetch-Site 三者
    # 会同时"合法", 整道门被绕过。rebinding 必须依赖**域名**(IP 字面量没法
    # 重新解析), 所以只放行 localhost 与 IP 字面量, 就把这条路堵死;
    # IP 字面量一律放行。⚠ 如实说明: 当前端口只绑 127.0.0.1 (2026-07-31 P0-0,
    # 实测局域网 IP 连不上), 所以局域网 IP 这一支现在走不到 —— 它是纵深防御,
    # 将来若放开监听不必再回来改代码。
    host = request.url.hostname or ""
    if host != "localhost" and host not in _extra_allowed_hosts():
        try:
            ipaddress.ip_address(host)
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "host_not_allowed",
                    "message": (
                        f"只接受 localhost 或 IP 字面量访问 (实为 Host: {host}) — 防 DNS rebinding。"
                        f"确需按主机名访问时, 用环境变量 {_ALLOWED_HOSTS_ENV} 逗号分隔列出"
                    ),
                },
            )
    site = request.headers.get("sec-fetch-site")
    if site is not None and site not in ("same-origin", "none"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "cross_site_blocked",
                "message": f"跨站请求被拒 (Sec-Fetch-Site: {site}) — 刷新只接受本页发起的提交",
            },
        )
    origin = request.headers.get("origin")
    if origin is not None and origin != f"{request.url.scheme}://{request.url.netloc}":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "cross_site_blocked",
                "message": f"跨站请求被拒 (Origin: {origin}) — 刷新只接受本页发起的提交",
            },
        )


def _notice_page_html(title: str, body: str, back: str) -> str:
    """中性提示页 (零 JS) —— 既不是成功也不是失败的那一类结果。"""
    return (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(title)}</title></head>"
        '<body style="font-family:-apple-system,BlinkMacSystemFont,'
        "'PingFang SC','Helvetica Neue',sans-serif;background:#f5f5f7;"
        'margin:0;padding:24px"><div style="max-width:640px;background:#fff;border:1px solid #e5e7eb;'
        'border-radius:12px;padding:20px 24px">'
        f'<h1 style="font-size:20px;margin:0 0 8px">⏳ {html.escape(title)}</h1>'
        f'<div style="font-size:14px;margin-bottom:14px">{html.escape(body)}</div>'
        f'<a href="{html.escape(back)}" style="font-size:14px;color:#2563eb;'
        'text-decoration:none">← 回到总览页</a></div></body></html>'
    )


def _error_page_html(status: int, vault_id: str, detail, back: str) -> str:
    """表单路径的失败页 (零 JS, 与总览页同族配色)。

    每一段都来自 detail 本身, 不编造原因; 原始 stderr 尾部原样放在
    <pre> 里 (人话解释不了的现场, 也不许藏)。
    """
    d = detail if isinstance(detail, dict) else {"message": str(detail)}
    parts = [
        f'<h1 style="font-size:20px;margin:0 0 6px">刷新失败 · {html.escape(vault_id)}</h1>',
        f'<div style="color:#6b7280;font-size:13px;margin-bottom:14px">HTTP {int(status)} · '
        f"{html.escape(str(d.get('error') or 'error'))}</div>",
        f'<div style="font-size:14px;margin-bottom:10px">{html.escape(str(d.get("message") or ""))}</div>',
    ]
    if d.get("hint"):
        parts.append(
            f'<div style="font-size:14px;background:#fffbeb;border:1px solid #fde68a;'
            f'border-radius:8px;padding:10px 12px;margin-bottom:12px">💡 {html.escape(str(d["hint"]))}</div>'
        )
    for field, label in (("tried", "已试过的脚本路径"), ("known", "本机可用的库")):
        if d.get(field):
            items = "".join(f"<li><code>{html.escape(str(x))}</code></li>" for x in d[field])
            parts.append(
                f'<div style="font-size:13px;color:#374151;margin-bottom:10px">{label}:'
                f'<ul style="margin:4px 0 0;padding-left:20px">{items}</ul></div>'
            )
    if d.get("stderr_tail"):
        parts.append(
            '<pre style="background:#f3f4f6;border-radius:8px;padding:10px;font-size:11px;'
            f'overflow-x:auto;white-space:pre-wrap;word-break:break-all">{html.escape(str(d["stderr_tail"]))}</pre>'
        )
    parts.append(
        f'<a href="{html.escape(back)}" style="font-size:14px;color:#2563eb;text-decoration:none">← 回到总览页</a>'
    )
    return (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>刷新失败</title></head>"
        '<body style="font-family:-apple-system,BlinkMacSystemFont,'
        "'PingFang SC','Helvetica Neue',sans-serif;background:#f5f5f7;"
        'margin:0;padding:24px"><div style="max-width:640px;background:#fff;border:1px solid #e5e7eb;'
        'border-radius:12px;padding:20px 24px">' + "".join(parts) + "</div></body></html>"
    )


@review_overview_router.post(
    "/overview/refresh",
    summary="按需重建单库今日复习投影 (CARD-G6-1; 显式用户触发)",
)
def review_overview_refresh(
    request: Request,
    vault_id: str = Form(..., description="要重建投影的 vault 目录名 (须命中 VAULTS_ROOT 下的真实库)"),
    redirect: str | None = Form(None, description="传 page 则 303 回总览页 (纯 HTML 表单用, 零 JS)"),
) -> Response:
    """重建该库的 outputs/今日复习.{md,json}, 返回重建后的聚合条目。

    同步 def: 由 FastAPI 丢进线程池, 既不堵事件循环, 也不让模块级锁绑定
    到某个 event loop (TestClient 每请求换 loop, asyncio.Lock 会跨 loop 炸)。

    响应字段:
      rebuilt / reason      本次是否真起了子进程并**发布了新产物**。
                            rebuilt=true 时三件事同时成立 (round-3 收紧):
                            子进程 rc=0、json 的 (inode, mtime_ns, sha) 相对
                            调用前变过、md 在位、且读回过 schema v3 门禁。
                            任一不成立 → 503, 不会返回 rebuilt=true。
                            ⚠ 本段曾写着"rebuilt=true 可与 entry.status=
                            no_projection 并存" —— 那是 round-3 之前的语义,
                            现在那种情形一律 503 (收官审计抓到的过期自述,
                            且它会进 OpenAPI 误导 API 调用方)。
                            reason ∈ rebuilt / debounced (落在 TTL 窗口内) /
                            in_progress (同库另一次重建在飞, 本次不排队)
      rebuild_count         该库自**本进程启动**以来的真实重建次数 (进程内计数,
                            多 worker 或重启后归零 —— 它是去抖行为的证据, 不是
                            持久化审计账)
      debounce_ttl_seconds  当前去抖窗口
      entry                 与 GET /overview 中该库条目同形 (四态 + projection)

    表单路径 (redirect=page) 的失败呈现: 渲染一页人话错误页, **状态码仍是
    原样的 4xx/5xx** —— 失败时跳回总览页会让人以为刷新成功了 (页面上什么
    都没变), 那正是"静默假成功"的浏览器版本。
    """
    try:
        _assert_same_origin(request)
        vault_dir, script = _refresh_target(vault_id)
        result, entry = _rebuild_projection(vault_dir, script)
        if entry is None:  # debounced / in_progress 分支没读回, 这里补一次
            entry = _read_entry(vault_dir)
    except HTTPException as e:
        if redirect != "page":
            raise
        return HTMLResponse(
            content=_error_page_html(e.status_code, vault_id, e.detail, request.url_for("review_overview_page").path),
            status_code=e.status_code,
        )
    if redirect == "page":
        # ⛔ **凡是没真重建的分支, 都不许走那条与成功逐字节同形的 303**。
        # round-3 只为 in_progress 做了这件事, 把 debounced 漏在原地 (收官审计
        # 抓到, 复核员实测"实况比报告更坏: 连『生成于』时间没走这条线索都不存在"):
        # 用户刚做完一道题 (写了 fsrs_due) 、10 秒内点刷新 → 拿到与成功一模一样
        # 的 303 + 相同 Location + 空 body → 页面看着刷新了、数字却没动, 而他
        # 没有任何办法知道"这次根本没重建"。
        if not result["rebuilt"]:
            wait = result.get("retry_after_seconds") or 0
            title, body = (
                (f"{vault_id} 正在重建中", "这个库已经有一次刷新在跑了，本次没有重复启动。等几秒回总览页看最新数字。")
                if result["reason"] == "in_progress"
                else (
                    f"{vault_id} 刚刚才刷新过",
                    f"{_REFRESH_TTL_SECONDS:g} 秒内已经重建过一次，本次**没有**重新计算，"
                    f"页面上还是上一次的结果。若你刚改过节点，等约 {wait:.0f} 秒后再点一次。",
                )
            )
            return HTMLResponse(
                content=_notice_page_html(title, body, request.url_for("review_overview_page").path),
                status_code=200,
            )
        # PRG: 303 回 GET, 浏览器刷新不会重复提交 —— 只有**真重建了**才走这里
        return RedirectResponse(url=request.url_for("review_overview_page").path, status_code=303)
    return JSONResponse(
        {
            "vault_id": vault_dir.name,
            "vault_path": str(vault_dir),
            "pick_script": str(script),
            "debounce_ttl_seconds": _REFRESH_TTL_SECONDS,
            **result,
            "entry": entry,
        }
    )
