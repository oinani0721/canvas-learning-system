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
板按 next_due。时间统一转显示时区人话化 (CARD-G6-9c: 单一来源, 缺省机器本地);
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

CARD-G3-6b (BATCH-2026-09-01-第八批) 板级解释加性消费: top_boards 行新增的
why_this_board / estimated_minutes 在场即严验 (非空串 / 非负 int, 垃圾走既有
corrupt 降级), 按板名挂到 boards 行渲染一条整宽解释行 —— 字段全部是生产器
投影内复算落盘的, 本端点照旧一个数都不算 (缺省 = 旧投影 / 榜外板, 整块不
出现, 不伪造)。

CARD-G6-7 (BATCH-2026-09-05-第十二批) 完成本板反馈 —— Web UI 的第一个**写侧
业务动作**: 新增 POST /api/v1/review/overview/board-done, 把「今天这块板做完
了」记进 runner 的 per-vault state (加性键 board_done)。三条边界写在这里,
因为它们是本端点此后所有写侧动作的共同纪律:

  ① **零 FSRS 污染** —— 本动作不写节点 frontmatter、不追加 learning_events,
     写面恰是 backups/daily-review.<key>.state.json 一个文件。「做完了」是
     看板顺序的偏好, 不是一次学习事件; 让它去动记忆曲线就是拿用户的调度
     换一个 UI 手感 (页面上也照实说了这句)。
  ② **读路径零写盘** —— 写侧复用 daily_review_run.load_state/save_state
     (含损坏隔离 + os.replace 原子写); 但**读侧另走**纯投影 _read_board_done,
     因为 load_state 遇到损坏文件会改名隔离 —— 那是一次写盘, 放进 GET 就
     当场破坏本模块的只读契约。同一份 schema, 两条路径, 不是两套口径。
  ③ **不进投影层** —— 已完成的板照旧在 boards/buckets/stats 里 (投影是
     A2 唯一裁判, _gate_buckets 的三桶合计恒等 stats.due_nodes 不容动),
     完成状态只在**渲染层**折叠、在**生产器榜首**处让位。
"""

from __future__ import annotations

import hashlib
import html
import importlib.util
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

from zoneinfo import ZoneInfo

from app.config import get_settings
from app.core.display_tz import display_tz as _resolve_display_tz
from app.core.display_tz import parse_posix_tz as _parse_posix_tz

logger = structlog.get_logger(__name__)

review_overview_router = APIRouter()

#: 每库投影相对路径 (A2: 全系统到期口径唯一裁判)
_PROJECTION_REL = ("outputs", "今日复习.json")

#: 显示时区 (CARD-G6-9c / D-18 2026-09-07): 单一来源 app.core.display_tz ——
#: 缺省 = 机器本地的 IANA 名 (TZ 环境变量 → /etc/localtime 软链), CANVAS_TZ
#: 显式覆盖。D-18 推翻了此前"恒 Asia/Shanghai"的口径:「今天」= 用户**当前
#: 所在地**, 出门换个时区, 页面、早间 runner、清单三处的「今天」仍是同一天。
#: 读侧的 _display_tz() 与写侧子进程 (_child_env 透传 TZ/CANVAS_TZ) 同一来源,
#: 二者永不漂移 —— CARD-G6-1 收官审计的那条承诺不变, 只是换了个更宽的锚。
#:
#: ⛔ **每次调用现取**, 禁止绑成模块级常量 / functools.lru_cache / 默认参数:
#: 进程运行期 TZ 可被改 (测试夹具 TZ + time.tzset() 正是这么做的, 且它**不
#: reload 模块**)。求值时机一旦固化在 import 那一刻, 后续改时区对显示侧完全
#: 无效 —— 门恒绿而缺陷照旧 (test_g6_9c_single_tz_source.py 门 ⑤ 锁这条)。


def _display_tz():
    """显示/归日用时区 —— 每次调用现取 (见上方 ⛔ 段)。"""
    return _resolve_display_tz()


def _display_tz_name() -> str | None:
    """显示时区的 IANA 名; 三档都取不到名而落到固定偏移时无 .key ⇒ None。"""
    return getattr(_display_tz(), "key", None)


# 启动校验: 无效 CANVAS_TZ ⇒ 应用启动即 ValueError (配置断裂当场可见, 不拖到
# 第一次请求)。刻意丢弃返回值 —— 不缓存、不赋给任何被后续读取的名字。
_resolve_display_tz()

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
#: CARD-G6-5-R 透传白名单: 生产器落盘的桶行四字段 (daily_review_pick.py:1007-1013)。
#: 与 _gate_buckets 验形处 (那里的 `for f in ("node", "board", "why_due")` 循环 +
#: 紧随其后的 _due_ts(r.get("fsrs_due"), ...)) 是**两个字面量**, 靠本文件的
#: test_bucket_rows_passthrough_* 锁在一起 —— 验形没覆盖的字段一旦进白名单,
#: 那道门会红 (未验字段不许出门)。
_BUCKET_ROW_FIELDS = ("node", "board", "why_due", "fsrs_due")
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


def _display_day(ts: str, tz=None):
    """UTC-Z 定长串 → 显示时区(或显式指定 tz)的日期; 不可表示时 None (年份极值)。

    `tz` 显式传入的唯一用途见 _gate_buckets: 校验一份**已落盘**的投影时, 参照系
    必须是它**生成时**的时区 —— 由投影顶层自报的 `display_tz` 重建的完整时区规则,
    不是此刻的显示时区, 也不再是 generated_at 自带的固定偏移（CARD-G6-9c-R2: 自报值
    缺席或为 null 时整份判 corrupt, 不退固定偏移）。
    """
    try:
        return (
            datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=timezone.utc)
            .astimezone(tz if tz is not None else _display_tz())
            .date()
        )
    except (ValueError, OverflowError, OSError):
        return None


def _display_today(now_utc: datetime | None = None) -> str:
    """现在的显示时区本地日 "YYYY-MM-DD" (CARD-G6-7 完成账的日历键)。

    刻意绕道 _display_day: 完成状态的「今天」必须与页面上到期人话的「今天」
    严格同一条换算 —— 直接写 datetime.now(_display_tz()).date() 数值上等价,
    但那是第二个时区入口, 将来 _display_day 的换算一改就分叉 (本文件已经为
    「容器 UTC 当本地日」这条缺陷付过一次代价)。
    """
    d = _display_day((now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    return d.isoformat() if d is not None else ""


def _display_now() -> datetime:
    """此刻的显示时区本地时间 —— 页面 / 端点共用的**同一个**时钟入口。

    CARD-G6-6。单独抽成模块级函数而不是各处写 `datetime.now(_display_tz())`:
      · 「读了几次时钟」这件事在源码里数得出来 —— 推迟的两档换算、20:00 判定、
        页面时间人话必须来自同一次读数, 分散的 now() 调用点谁也数不清;
      · 门可以把它钉死。没有可钉的入口就只能去打 datetime 这个**解释器全局**,
        那会连累同进程里任何别的调用方 (本仓已为同类做法付过一次代价, 见
        daily_review_run._state_tmp_path 的注释)。
    时区仍是每次现调 _display_tz() (U6-A 的「不缓存」口径), 本函数不持有任何状态。
    """
    return datetime.now(_display_tz())


def _gate_buckets(
    buckets,
    due_groups: dict[str, dict],
    stats: dict,
    generated_at: str,
    future_map: dict[str, tuple[int, str]],
    up_gated: list[dict],
    producer_tz: str | None = None,
) -> tuple[dict[str, int], dict[str, list[dict]]]:
    """G3-6a 加性 buckets 门禁 (可选顶层键: 旧投影缺省走 None 路径)。

    返回 (桶位计数, 已验节点行) —— CARD-G6-5-R 起第二项由本函数出门: 节点行
    此前验完即丢, 两页只拿得到一行计数, **due_today / future 两桶**在节点级
    完全不可见 (它们在 due_nodes 里没有对手盘; new 属 _DUE_BUCKETS, 早就随
    板行明细出现了 —— Codex round-1 LOW 更正)。透传的行**就是本函数逐行验过、
    并用来数出计数的那些行** (同一个 buckets[name] 列表, 见函数末尾的构造点),
    不从别处再取一次; 字段按 _BUCKET_ROW_FIELDS 白名单原样搬运, 不重算不改写。
    调用方在边界上再核一次「逐桶行数 == 计数」——那是一条**逐桶行数漂移守卫**,
    只能发现长度变了; 等长替换 (换身份 / 改字段值 / 改顺序) 它一概发现不了
    (Codex round-1 LOW: 别把它说成来源或身份守卫)。

    ⚠ 三方计数 (⑤) 的参照系, 逐字: 本断言的参照系是 generated_at，不是 now；
    读侧到点标记不并入本等式的任何被加数。
    (出处: _bmad-output/研究/2026-09-05-乙2-读时重判到期-可行性设计.md §三)
    把参照时钟换成读取时刻的后果 (Codex round-1 更正了先后顺序): 最先炸的是
    **非到期侧**的桶判据重算 —— 一个合法的 due_today 行到点之后 fsrs_due 就
    不再晚于新时钟, 于是"未到期桶的时刻必须晚于参照时钟"那条对**合法投影**抛
    ValueError → 整库 corrupt。到期侧的逆检查是更靠后才会碰到的一层。

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
           generated_at 同一本地日 (按投影自报 display_tz 重建的完整时区规则, 见 ref_tz;
           自报值缺席/为 null 时不退固定偏移而是整份判 corrupt)、
           future 必须晚于该日;
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
        # 参照系 = 生产器**自报**的时区 (payload 顶层 display_tz)。三轮收敛的结论:
        #   · 恒用此刻的显示时区 ⇒ 用户一改时区, 盘上合法投影被判 corrupt (r1);
        #   · 恒用 generated_at 自带的固定偏移 ⇒ DST 边界误拒, 反过来放行错误归桶 (r2);
        #   · 靠"偏移是否匹配"在两者间猜 ⇒ 同偏移不同规则的时区对 (Bogota 恒 -05:00
        #     vs New_York 的 EST) 仍会选错, 而且两个方向都错 (r3)。
        # 偏移**不能**决定时区规则, 只有生产器自己知道它用了哪个 —— 所以让它自报。
        # 自报值必须与 generated_at 的偏移自洽 (否则 payload 自相矛盾, 拒收);
        # **缺席 (旧投影 / 末档无名时区) ⇒ 整份按 corrupt 降级** —— 见下方 ref_tz is None 段。
        # ⛔ 这里原先写的是「退回此刻的显示时区……不会放行错误归桶」: 前半与代码不符
        #    (r2 起退的是固定偏移), 后半已被 r5 证伪 (误拒与误放行是同一偏差的两侧)。
        # 「投影是不是今天的」由 _vault_entry 的 stale 判定负责, 那里恒用此刻时区。
    except (ValueError, OverflowError, OSError) as e:
        raise ValueError(f"generated_at 无法换算为参照时钟: {generated_at!r} ({e})")
    # ⛔ display_tz 的校验放在上面那个 try **之外**: 它抛的 ValueError 语义是
    #    「payload 自相矛盾」, 落进 except 会被重包成「generated_at 无法换算」——
    #    两个完全不同的拒因混成一条, 排障时看不出是哪种。
    ref_tz = None
    if producer_tz is not None:
        # 静态签名是 str|None, 该 isinstance 看似恒真; 但运行时该值来自盘上
        # JSON(payload.get), 12/{} 这类非串真实存在(Codex r4 反例), 必须防。
        if not isinstance(producer_tz, str) or not producer_tz.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ValueError(f"display_tz 非法: {producer_tz!r} — 应为 IANA 名或 POSIX TZ 串")
        candidate = None
        try:
            candidate = ZoneInfo(producer_tz)  # IANA 名 / tzfile 简名
        except Exception:  # noqa: BLE001
            candidate = _parse_posix_tz(producer_tz)  # POSIX 串: 用与生产者同源的解析器重建完整规则
        if candidate is None:
            raise ValueError(f"display_tz 不是可解析的时区名: {producer_tz!r}")
        try:
            same_offset = ref.astimezone(candidate).utcoffset() == ref.utcoffset()
        except (OverflowError, OSError) as e:
            raise ValueError(f"display_tz={producer_tz!r} 在 generated_at 处换算溢出 ({type(e).__name__})")
        if not same_offset:
            raise ValueError(
                f"display_tz={producer_tz!r} 与 generated_at={generated_at} 的偏移不自洽 "
                f"(该时区在那一刻是 {ref.astimezone(candidate).utcoffset()}, "
                f"generated_at 自带 {ref.utcoffset()}) — payload 自相矛盾"
            )
        ref_tz = candidate
    if ref_tz is None:
        # ⛔ 旧投影 / 末档无名时区（`display_tz` 键缺席或为 null）⇒ **整份判 corrupt**,
        #    不再回退到 generated_at 自带的固定偏移。
        # 为什么不能退固定偏移: 它只在 generated_at **那一刻**等于生产者的真实偏移; 到期
        #    时刻落在 DST 切换另一侧时就差一档, 而误拒与误放行是同一个偏差的**两侧**,
        #    不可能只占一侧（Codex r5 HIGH-2 实证: 同一份 NY 投影, 自报时区时门判得对,
        #    键缺席时合法的 future 被拒、伪造的 due_today 被放行）。
        # 为什么不能用「偏移 ±Δ 敏感性复算」兜（本卡 r1 试过、被 r1 Codex 打回）:
        #    带宽要同时满足两个互斥要求 —— 小到不误拒合法投影, 大到不漏放行错误归桶。
        #    实测 `ABC-1DEF-5`(Δ=+4h) 就在 ±2h 带外、伪造的 due_today 照样放行; 而把带宽
        #    提到覆盖本实现接受的全部 Δ 就等于拒绝一切。
        #    ⚠️ Δ 的界是多少, 两轮都写错过, 这里写准: **不是**「无界」（r2 LOW-2 更正）,
        #    也**不再**是「正则字段位宽给的 ±83 天」（r10 L4 更正 —— r11 已把位宽放宽成
        #    `\d+`, 那条论证作废）。当前的界来自解析器的量级检查: 两侧偏移各自 < 24h
        #    且两侧之**差** < 24h ⇒ |Δ| < 24h。界变小了但结论不变 —— 24 小时仍远大于
        #    任何实用带宽, 缺 display_tz 时那两个要求不可兼得, 才是这条路走不通的原因。
        # 取舍如实声明: 没有 `display_tz` 就无法可靠归日, 正确性优先于对旧投影的兼容。
        #    代价是那类投影整份走 corrupt 降级（页面显示「投影损坏」, 需重新生成）。
        raise ValueError(
            f"display_tz 缺席或为 null — 无可信参照时区规则, 旧投影的归桶无法重算 "
            f"(generated_at={generated_at} 自带的固定偏移只在那一刻等于生产者的真实偏移)"
        )
    try:
        ref_day = ref.astimezone(ref_tz).date()
    except (OverflowError, OSError) as e:
        raise ValueError(f"generated_at 无法换算为参照日: {generated_at!r} ({type(e).__name__})")
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
            day = _display_day(ts, ref_tz)
            if day is None:
                # 时刻不可表示: 生产器兜底恒归 future, 不可能是"今天"
                if name != "future":
                    raise ValueError(f"buckets.{name}[{i}] fsrs_due={ts} 不可换算, 只允许出现在 future 桶")
            elif name == "due_today" and day != ref_day:
                raise ValueError(f"buckets.due_today[{i}] fsrs_due={ts} 非 generated_at 的同一本地日 {ref_day}")
            elif name == "future" and day <= ref_day:
                raise ValueError(
                    f"buckets.future[{i}] fsrs_due={ts} 仍在 generated_at 的本地日 {ref_day} 内, 应属 due_today"
                )
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
    # CARD-G6-5-R 透传构造点 (全部判据通过之后): 逐桶从 **counts 数的同一个
    # 列表** buckets[name] 取行, 只做字段白名单投影 —— 不排序不去重不补字段,
    # 所以 len(passed_rows[name]) 恒等于上面 `counts[name] = len(rows)` 那一行
    # 数出的值; 调用方边界上的那条等式因此只可能被「改行数」的未来改动打破
    # (等长替换它发现不了 —— Codex round-1 LOW)。
    # 变量名不复用循环里的 `rows`: 那个名字在上面的验形循环里指"当前这一桶的
    # 原始行", 循环虽已结束, 同名重绑会让后来读的人以为是同一个东西。
    passed_rows = {name: [{f: r[f] for f in _BUCKET_ROW_FIELDS} for r in buckets[name]] for name in _BUCKET_ORDER}
    return counts, passed_rows


def _humanize_due(ts: str | None, now_local: datetime) -> tuple[str, str]:
    """到期时刻 → (人话, 颜色)。跨午夜用显示时区本地日判定 (CARD-G6-9c)。

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
        due_local = due.astimezone(_display_tz())
        delta = (due_local.date() - now_local.astimezone(_display_tz()).date()).days
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
    if due_local.year == now_local.astimezone(_display_tz()).year:
        return f"{due_local.month}月{due_local.day}日", "#6b7280"
    return f"{due_local.year}年{due_local.month}月{due_local.day}日", "#6b7280"


def _fmt_local_dt(dt: datetime) -> str:
    """tz-aware 时刻 → 显示时区本地 "YYYY-MM-DD HH:MM (UTC+N)"。"""
    local = dt.astimezone(_display_tz())
    off = local.utcoffset() or timedelta(0)
    # ⛔ 不能只取整小时（Codex r1 LOW-2）：本卡之前显示时区恒是整小时偏移的
    #    Asia/Shanghai，取整看不出问题；收敛到「跟随用户所在地」之后，半小时/
    #    三刻钟时区变得可达 —— Kolkata 的 +05:30 会被显示成 UTC+5、
    #    St. John's 的 -02:30 显示成 UTC-3，都是错的。
    #    整小时偏移的输出与本卡之前逐字相同（+08:00 仍是 "UTC+8"）。
    total_min = int(off.total_seconds()) // 60
    sign = "-" if total_min < 0 else "+"
    hh, mm = divmod(abs(total_min), 60)
    off_txt = f"UTC{sign}{hh}" + (f":{mm:02d}" if mm else "")
    return local.strftime("%Y-%m-%d %H:%M") + f" ({off_txt})"


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

#: CARD-G6-9b: 推送降级徽标的文案。⚠ 它是**面向用户的契约**, 不是内部标识 ——
#: 用户认的就是这四个字; 改它等于改产品语义, 门 test_overview_page_degrade_badge_
#: only_when_failed 在测试侧另写一份同样的字面量把它钉住 (期望值与被测量同源
#: 时, 改错了两边一起变, 门就永远不会红)。
_PUSH_DEGRADED_LABEL = "推送降级"


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
    board_explain: dict[str, tuple[str | None, int | None]] = {}
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
        # CARD-G3-6b 加性消费: 板级解释与预计分钟 (旧投影缺省 → None, 渲染层
        # 整块不出现)。在场即严验 — 消费的字段必须验形, 垃圾不发 ok;
        # minutes 不许 bool 冒充 (JSON true 属 int 子类, 同 _strict_int 口径)。
        why = tb.get("why_this_board")
        if why is not None and (not isinstance(why, str) or not why):
            raise ValueError(f"top_boards[{i}].why_this_board 应为非空字符串或缺省, 实为 {why!r}")
        mins = tb.get("estimated_minutes")
        if mins is not None and (type(mins) is not int or mins < 0):
            raise ValueError(f"top_boards[{i}].estimated_minutes 应为非负整数或缺省, 实为 {mins!r}")
        board_explain[b] = (why, mins)
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
    # CARD-G6-5-R: 已验节点行 (缺省 None = 旧投影无 buckets 键, 与 bucket_counts 同缺省纪律)
    bucket_rows = None
    if "buckets" in payload:
        # Codex round-3: 二者由同一版生产器一起产出 —— "有 buckets 无 boards"
        # 不是任何历史形态, 放行它等于放弃非到期两桶的逐板对账
        if future_map is None:
            raise ValueError("buckets 在场但 boards 缺席 — 非生产器产物 (二者同版一起落盘)")
        bucket_counts, bucket_rows = _gate_buckets(
            payload["buckets"],
            groups,
            stats,
            generated_at,
            future_map,
            up_gated,
            producer_tz=payload.get("display_tz"),
        )
        # CARD-G6-5-R 边界不变量 = **逐桶行数漂移守卫**, 不是来源/身份守卫
        # (Codex round-1 LOW 收窄措辞): 它只能发现"行数与计数对不上"; 等长的
        # 身份替换 / 字段改值 / 顺序变动它一概发现不了 —— 那些由 _gate_buckets
        # 内的成员恒等与逐字相等判据管, 本条不重复也不冒领。
        # 行数一旦脱钩, 卡片上的计数与队列区块里能点开的卡就各说各话; 与其发
        # 一个自相矛盾的页面, 不如按既有 corrupt 语义降级。
        # 当前实现下本式恒真 (行与计数取自同一个列表), 守的是**未来改动**。
        drift = {
            b: (len(bucket_rows[b]), bucket_counts[b]) for b in _BUCKET_ORDER if len(bucket_rows[b]) != bucket_counts[b]
        }
        if drift:
            raise ValueError(f"bucket_rows 逐桶行数与 bucket_counts 脱钩 (桶: (行数, 计数)): {drift}")
    board_rows = [
        {
            "board": b,
            "due": g["due"],
            "due_new": g["new"],
            "placeholder": ph_map.get(b),
            "earliest": g["earliest"],
            # CARD-G6-4 加性: 板内到期节点明细 (纯消费既有 due_nodes 行, 零 schema 改动)
            "nodes": _node_rows(g["rows"]),
            # CARD-G3-6b 加性: 该板若在 top_boards 榜上 → 解释与预计分钟;
            # 不在榜 (top_boards 截 3 之外) 或旧投影 → None, 渲染层整块不出现。
            # 值全部来自投影已落盘的字段, 本端点一个数都不算。
            "why_this_board": board_explain.get(b, (None, None))[0],
            "estimated_minutes": board_explain.get(b, (None, None))[1],
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
        # CARD-G6-5-R 加性: 五桶节点行 (_gate_buckets 已验并已数过的那些行);
        # 缺省 null = 旧投影无 buckets 键 —— 两页据此整块不渲染, 不伪造空队列
        "bucket_rows": bucket_rows,
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


def _vault_entry(
    vault_dir: Path,
    today: date,
    done_boards: "list[str] | tuple[str, ...]" = (),
    snoozed: "dict[str, str] | None" = None,
    push_degraded: "bool | None" = None,
    last_error: "str | None" = None,
) -> dict:
    """单 vault 聚合条目 — 诚实四态, 任何脏数据都不许把请求打成 500。

    CARD-G6-7 加性 board_done: 今天被标「做完了」的板名列表。它**不进
    projection** —— 投影是 A2 唯一裁判的产物, 完成状态是本机用户偏好,
    混进去会让"投影字段"这个词失去意义。四态一律带该键 (空列表 = 没有
    完成记录), 消费方不做存在性分支。

    CARD-G6-6 加性 snoozed: {board: until_iso}, 与 board_done 同一条纪律
    (不进 projection、四态一律带该键)。**只投影仍在生效的**那些 —— 到期的
    条目虽然还留在 state 里, 但它对页面和榜单都已经不存在了。

    CARD-G6-9b 加性 push_degraded / last_error: 最近一次推送的结果 (源 =
    runner state, 见 _read_push_status)。同上两条纪律 —— 不进 projection、
    四态一律带这两个键。⚠ `push_degraded` 是**三态**: True 失败 / False 成功
    / None 没推过或读不出; `last_error` 只在能读出时带字符串。与 `error`
    是两回事: `error` 说的是"这个库的投影文件坏了", 这两个说的是"推送这件事
    成没成" —— 投影好端端的、推送挂掉, 正是本卡要让它现形的那一格。
    """
    entry: dict = {
        "vault_id": vault_dir.name,
        "path": str(vault_dir),
        "status": "no_projection",
        "projection": None,
        "error": None,
        "board_done": list(done_boards),
        "snoozed": dict(snoozed or {}),
        "push_degraded": push_degraded,
        "last_error": last_error,
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
            # CARD-G6-9c / D-18: 本地日走单一显示时区来源 (裸 astimezone()
            # 会让容器 UTC 与页面口径分叉, 跨午夜误判)
            stale = gen.astimezone(_display_tz()).date() != today
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
    now = _display_now()  # CARD-G6-9c: 全链路单一显示时区 (CARD-G6-6 收成单一入口)
    try:
        vault_dirs = _list_vault_dirs(vaults_root)
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "vaults_root_scan_failed", "message": str(e)},
        )
    # CARD-G6-7: 完成账的「今天」与页面其余时间人话共用同一次时钟读数
    today_local = _display_today(now)
    vaults = []
    for v in vault_dirs:
        try:
            vaults.append(
                _vault_entry(
                    v,
                    now.date(),
                    _board_done_today(v, vaults_root, today_local),
                    # CARD-G6-6: 与完成账共用同一次 now 读数 —— 两个账各读一次
                    # 时钟, 跨 20:00 / 跨午夜那一秒会给出互相矛盾的页面
                    _snoozed_active(v, vaults_root, now),
                    # CARD-G6-9b: (push_degraded, last_error) 一次读出、按位展开
                    *_push_status(v, vaults_root),
                )
            )
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
                    "board_done": [],
                    "snoozed": {},
                    # CARD-G6-9b: 兜底条目也要带齐 —— 消费方不做存在性分支。
                    # None 而不是 False: 这一格根本没读到推送结果, 说"推成功了"
                    # 就是拿兜底路径伪造了一条好消息。
                    "push_degraded": None,
                    "last_error": None,
                }
            )
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        # CARD-G6-9c 加性: 服务端显示时区的 IANA 名, 供前端 Intl.DateTimeFormat
        # 用同一口径归日 (此前 JS 里写死了一个固定时区名, 那是第五套时钟)。
        # 每次请求现算; 三档都取不到名 (末档固定偏移) 时为 null, 前端退浏览器本地。
        "display_tz": _display_tz_name(),
        # CARD-G6-6 加性: 「今晚再说」这一档此刻还给不给点。⛔ **20:00 的判定
        # 只在服务端做这一次**, 前端拿到的是结论不是原料 —— 让 JS 自己按
        # display_tz 算一遍就有了两个判定: display_tz 为 null 时 (三档都取不到
        # IANA 名) JS 退回浏览器本地, 异地访问的用户会看到「今晚」钮, 而服务端
        # 按自己的本地时间必以 snooze_until_in_past 打回。同一次 now 读数, 与
        # 端点那侧的比较口径逐字相同。
        "tonight_available": now.hour < _SNOOZE_TONIGHT_HOUR,
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


def _node_detail_html(vault_id: str, nodes: list[dict], now_local: datetime) -> str:
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
        eta, eta_color = _humanize_due(n["fsrs_due"], now_local)
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


def _queue_layers_html(vault_id: str, bucket_rows: dict | None, now_local: datetime) -> str:
    """CARD-G6-5-R 队列分层区块 (零 JS): 五桶各自成区, 区内逐节点点名。

    与板表格 (_board_table_html) 是同一批节点的**另一种切法**, 不是它的替代:
    板视图回答「今天先开哪块板」, 队列视图回答「这张卡为什么现在出现 / 什么时候
    轮到它」。

    ⚠ 真正此前节点级不可见的是 **due_today 与 future 两桶**, 不是 new
    (Codex-G6-5-R round-1 LOW 更正): _DUE_BUCKETS 含 new, 到期三桶的成员按
    _gate_buckets ② 恒等于 due_nodes 明细, 所以新卡早就随板行的 nodes 明细
    出现了。due_today / future 在 due_nodes 里没有对手盘 (生产器 S2 不搬移),
    投影内只有 upcoming 点名过其中极少数 —— 本区块补的是这一块。

    数据全部来自 _gate_buckets 已验并已数过的透传行。本函数**只数已验行的条数**
    (桶内 len 与总数), 不重判到期、不重新排序、不改任何字段 (桶内顺序 = 生产器
    扫描序)。bucket_rows 缺省 (旧投影无 buckets 键) → 整块不出现, 与卡片汇总
    分层行同一条纪律。空桶保留分区并显示 0: 与汇总行摆 0 同口径 —— 藏掉空桶会让
    "今天这一桶是空的"看起来像"系统里没有这一桶"。
    """
    if bucket_rows is None:
        return ""
    sections = []
    for b in _BUCKET_ORDER:
        rows = bucket_rows[b]
        head = (
            f'<div style="font-size:12px;color:#374151;margin:6px 0 2px">'
            f'{html.escape(_BUCKET_CN[b])} <span style="color:#6b7280">（{len(rows)}）</span></div>'
        )
        if not rows:
            body = '<div style="color:#9ca3af;font-size:12px;margin:0 0 2px">这一桶今天是空的</div>'
        else:
            items = []
            for r in rows:
                link = html.escape(_node_link(vault_id, r["node"]))
                eta, eta_color = _humanize_due(r["fsrs_due"], now_local)
                items.append(
                    f'<li style="{_NODE_LI}">'
                    f'<a href="{link}" style="color:#2563eb;text-decoration:none">{html.escape(r["node"])}</a>'
                    f'<span style="{_NODE_TAG}">{html.escape(r["board"])}</span>'
                    f'<span style="color:{eta_color};font-size:12px;margin-left:6px">{html.escape(eta)}</span>'
                    f'<div style="color:#6b7280;font-size:12px;margin-top:1px">{html.escape(r["why_due"])}</div>'
                    f"</li>"
                )
            body = f'<ul style="margin:2px 0 2px;padding:0">{"".join(items)}</ul>'
        sections.append(f'<div data-queue-bucket="{b}">{head}{body}</div>')
    total = sum(len(bucket_rows[b]) for b in _BUCKET_ORDER)
    return (
        f'<details data-queue-layers="1" style="margin:4px 0 2px">'
        f'<summary style="cursor:pointer;color:#6b7280;font-size:12px;padding:2px 0">'
        f"按到期阶段看队列（{total} 张卡分五块）</summary>"
        f'<div style="margin:2px 0 0">{"".join(sections)}</div></details>'
    )


def _board_table_html(
    vault_id: str,
    boards: list[dict],
    now_local: datetime,
    done_action: str | None = None,
    undo_action: str | None = None,
    snooze_action: str | None = None,
    unsnooze_action: str | None = None,
    tonight_available: bool = True,
) -> str:
    """三级视图第二/三级: 板表格 白板名|到期|新卡|待剖析|最早到期。

    CARD-G6-4: 有到期节点的板在数据行之下多一行 `colspan=5` 的折叠区
    (`<details>`)。放在整宽的第二行而不是塞进"白板名"那一格 —— 塞进单元格
    会把第一列撑宽、把其余四列挤扁, 375px 窄窗尤其难看。
    CARD-G3-6b: 折叠区之前再加一条整宽的解释行 —— 「为什么是这块板 · 预计 N
    分钟」, 字段由生产器投影内复算落盘, 本页只 html.escape 原样显示, 一个数
    都不算。任一字段缺省 (旧投影 / 截 3 之外的板) → 整块不出现, 不伪造。
    CARD-G6-7: done_action 在场时每块板尾再加一行「这板做完了」表单按钮
    (零 JS, 沿 _refresh_form_html 形态)。缺省 None = 不出按钮 —— 已完成区
    里复用本函数渲染时就走这条 (做完了的板不该再给一个"再做完一次"的钮)。
    CARD-G6-7-R: undo_action 同理, 只在**已完成区**在场 —— 那里才有东西可撤。
    两个参数互斥地用: 待做区给 done_action, 已完成区给 undo_action; 同时给
    会让同一块板既能"再做完一次"又能撤销, 两个钮说的是矛盾的话。
    CARD-G6-6: snooze_action / unsnooze_action 同一条互斥纪律 —— 待做区给
    snooze_action (两档「再说」), 已推迟区给 unsnooze_action (「取回」)。
    tonight_available 只在 snooze_action 在场时起作用: 已过 20:00 就不出
    「今晚」那个钮 (判定在服务端做过, 这里只照结论渲染)。
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
        eta, eta_color = _humanize_due(r["earliest"], now_local)
        rows_html.append(
            f"<tr>"
            f'<td style="{_TD}"><a href="{link}" style="color:#2563eb;text-decoration:none">{name}</a></td>'
            f'<td style="{_TD_NUM}">{due_disp}</td>'
            f'<td style="{_TD_NUM}">{int(r["due_new"])}</td>'
            f'<td style="{_TD_NUM}">{html.escape(ph)}</td>'
            f'<td style="{_TD};white-space:nowrap;color:{eta_color}">{html.escape(eta)}</td>'
            f"</tr>"
        )
        why = r.get("why_this_board")
        mins = r.get("estimated_minutes")
        # 原子对 (Codex round-1 MEDIUM): 两字段由生产器成对产出, 单边缺省
        # 不是旧投影的"降级形态"而是半份配置 —— 整块不出现, 不渲染一条
        # 没有分钟的裸解释 (那会让人把预估时长当成"没说"而非"没配")
        if why and mins is not None:
            text = html.escape(why) + f" · 预计 {int(mins)} 分钟"
            rows_html.append(
                f'<tr><td colspan="5" style="{_TD};padding-top:0;color:#6b7280;font-size:12px">'
                f"为什么是这块板 · {text}</td></tr>"
            )
        detail = _node_detail_html(vault_id, r.get("nodes") or [], now_local)
        if detail:
            rows_html.append(f'<tr><td colspan="5" style="{_TD};padding-top:0">{detail}</td></tr>')
        # CARD-G6-6: 推迟与完成是待做区并列的两个出口, 同一格里挨着放 ——
        # 「今天先不做」和「今天做过了」都是对同一块板的处置。⚠ snooze_action
        # 缺省时这一格与本参数出现之前逐字节相同 (只剩完成钮那一份)。
        if done_action or snooze_action:
            btns = ""
            if snooze_action:
                btns += _board_snooze_form_html(vault_id, r["board"], snooze_action, tonight_available)
            if done_action:
                btns += _board_done_form_html(vault_id, r["board"], done_action)
            rows_html.append(f'<tr><td colspan="5" style="{_TD};padding-top:0">{btns}</td></tr>')
        if undo_action:
            rows_html.append(
                f'<tr><td colspan="5" style="{_TD};padding-top:0">'
                f"{_board_undone_form_html(vault_id, r['board'], undo_action)}</td></tr>"
            )
        if unsnooze_action:
            rows_html.append(
                f'<tr><td colspan="5" style="{_TD};padding-top:0">'
                f"{_board_unsnooze_form_html(vault_id, r['board'], unsnooze_action)}</td></tr>"
            )
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


#: 「这板做完了」按钮样式 (CARD-G6-7) — 绿系, 与刷新按钮区分开: 一个是
#: "再算一次给我看", 一个是"记下我做完了", 误点代价不同, 不该长得一样
_DONE_BTN = (
    "font-size:12px;color:#15803d;background:#f0fdf4;border:1px solid #bbf7d0;"
    "border-radius:6px;padding:2px 9px;cursor:pointer;font-family:inherit"
)

#: 写侧动作的诚实说明 —— 完成条件 (c) 要求页面明示「不影响 FSRS」。
#: 用户可以在一道题都没答的情况下标完成 (裁决: 允许), 所以这句话必须在
#: 按钮旁边而不是藏在帮助里: 它是"这个钮到底动了什么"的全部答案。
_DONE_NOTE = (
    "✅「这板做完了」只把它折进下面的「已完成」区，并把今天的推荐让给下一块板 ——"
    " 不影响 FSRS 记忆曲线（不写节点、不记学习事件），明天自动回来，点错了可以撤销。"
)


#: 「撤销」按钮样式 (CARD-G6-7-R) — 灰系, 与绿色的完成钮拉开: 完成是推进,
#: 撤销是**收回一个误操作**, 长得一样会让人在已完成区里又点一次以为在确认
_UNDO_BTN = (
    "font-size:12px;color:#4b5563;background:#f9fafb;border:1px solid #d1d5db;"
    "border-radius:6px;padding:2px 9px;cursor:pointer;font-family:inherit"
)


#: 「再说」按钮样式 (CARD-G6-6) — 琥珀系, 与绿色的完成钮、灰色的撤销钮都
#: 拉开: 完成是"做过了", 推迟是"今天先不做", 两件事的代价与可逆性都不同
_SNOOZE_BTN = (
    "font-size:12px;color:#b45309;background:#fffbeb;border:1px solid #fde68a;"
    "border-radius:6px;padding:2px 9px;cursor:pointer;font-family:inherit;margin-right:6px"
)

#: 「取回」按钮样式 (CARD-G6-6) — 与撤销完成同一个灰系: 两者都是收回一个
#: 误操作, 长得一样反而是对的
_UNSNOOZE_BTN = _UNDO_BTN

#: 推迟动作的诚实说明 —— 与 _DONE_NOTE 同一条纪律: 这个钮到底动了什么,
#: 答案必须就在钮旁边。⛔ 文案里不写事件账的文件名 (写点普查门的白名单是
#: 按文件字面量算的, 一条注释就能让它多出一个"实现点")。
_SNOOZE_NOTE = (
    "⏰「今晚 / 明天再说」只把它挪进下面的「已推迟」区，把今天的推荐让给下一块板 ——"
    " 到点它自己回来。不影响 FSRS 记忆曲线（不写节点、不记学习事件，卡片该什么时候到期还是什么时候）。"
)


def _board_snooze_form_html(vault_id: str, board: str, action: str, tonight_available: bool) -> str:
    """两档「再说」表单按钮 — 一个 form 两个 submit, 零 JS。

    档位靠 `<button name="until" value="…">` 携带 —— 浏览器只提交被点的那个
    按钮的 name/value, 于是两档共用一份 hidden 字段, 也不需要单选框。
    ⛔ 没有输入框: 两档就是全部选择 (D-8 甲)。

    tonight_available 为假 (已过 20:00) 时**不渲染**「今晚」钮 —— 判定在服务端
    做过了, 这里只是照结论渲染。留着它只会让人点出一个必然 422 的请求。
    """
    tonight = (
        f'<button type="submit" name="until" value="tonight" style="{_SNOOZE_BTN}">🌙 今晚再说</button>'
        if tonight_available
        else ""
    )
    return (
        f'<form method="post" action="{html.escape(action)}" style="display:inline;margin:0">'
        f'<input type="hidden" name="vault_id" value="{html.escape(vault_id)}">'
        f'<input type="hidden" name="board" value="{html.escape(board)}">'
        '<input type="hidden" name="redirect" value="page">'
        f"{tonight}"
        f'<button type="submit" name="until" value="tomorrow" style="{_SNOOZE_BTN}">📅 明天再说</button></form>'
    )


def _board_unsnooze_form_html(vault_id: str, board: str, action: str) -> str:
    """「取回」表单按钮 — 纯 HTML form POST, 零 JS (沿 _board_undone_form_html)。"""
    return (
        f'<form method="post" action="{html.escape(action)}" style="display:inline;margin:0">'
        f'<input type="hidden" name="vault_id" value="{html.escape(vault_id)}">'
        f'<input type="hidden" name="board" value="{html.escape(board)}">'
        '<input type="hidden" name="redirect" value="page">'
        f'<button type="submit" style="{_UNSNOOZE_BTN}">↩︎ 取回</button></form>'
    )


def _board_undone_form_html(vault_id: str, board: str, action: str) -> str:
    """「撤销」表单按钮 — 纯 HTML form POST, 零 JS (沿 _board_done_form_html)。"""
    return (
        f'<form method="post" action="{html.escape(action)}" style="display:inline;margin:0">'
        f'<input type="hidden" name="vault_id" value="{html.escape(vault_id)}">'
        f'<input type="hidden" name="board" value="{html.escape(board)}">'
        '<input type="hidden" name="redirect" value="page">'
        f'<button type="submit" style="{_UNDO_BTN}">↩︎ 撤销</button></form>'
    )


def _board_done_form_html(vault_id: str, board: str, action: str) -> str:
    """「这板做完了」表单按钮 — 纯 HTML form POST, 零 JS (沿 _refresh_form_html)。

    redirect=page → 303 PRG: 浏览器刷新不会重复提交同一块板的完成。
    """
    return (
        f'<form method="post" action="{html.escape(action)}" style="display:inline;margin:0">'
        f'<input type="hidden" name="vault_id" value="{html.escape(vault_id)}">'
        f'<input type="hidden" name="board" value="{html.escape(board)}">'
        '<input type="hidden" name="redirect" value="page">'
        f'<button type="submit" style="{_DONE_BTN}">✅ 这板做完了</button></form>'
    )


def _snooze_wake_label(untils: "list[str]") -> str:
    """「已推迟（N）· 到 HH:MM 自动回来」里的那个时刻 (CARD-G6-6)。

    多块板各有各的 until ⇒ 取**最早**的那个: summary 上那一行回答的是
    "这个区什么时候开始有东西回来"。解析不出的条目跳过; 一条都解析不出
    → 空串, 调用方退回不带时刻的措辞 (不编一个时间出来)。
    显示时区现调 `_display_tz()` —— 与页面其余时间人话同一来源。
    """
    times = []
    for raw in untils:
        try:
            dt = datetime.fromisoformat(raw)
        except (TypeError, ValueError):
            continue
        if dt.utcoffset() is not None:
            times.append(dt)
    if not times:
        return ""
    try:
        return min(times).astimezone(_display_tz()).strftime("%H:%M")
    except (OverflowError, OSError, ValueError):
        return ""  # 极值时刻换算溢出 → 退回不带时刻的措辞, 不把只读页打成 500


def _boards_split_html(
    vault_id: str,
    boards: list[dict],
    now_local: datetime,
    done: set,
    done_action: str,
    undo_action: str | None = None,
    snoozed: "dict[str, str] | None" = None,
    snooze_action: str | None = None,
    unsnooze_action: str | None = None,
    tonight_available: bool = True,
) -> str:
    """CARD-G6-7: 板表格分成「待做」与「已完成」两区。

    ⛔ 折叠不是隐藏, 也不是从投影里剔除 —— 已完成的板行原样还在页面上,
    只是收进 details 里。投影层压制会当场撞 _gate_buckets 的"到期三桶合计
    恒等 stats.due_nodes", 更要紧的是它会让页面上的数字对不上盘上的数字。

    CARD-G6-6 第三区「已推迟」同一条律 —— 行原样在, 只是折起来。
    ⛔ **活跃推迟集为空时一个字节都不输出**(沿已完成区 `if not finished` 的
    同一条律): 页面上 `<details>` 的个数是有「恰好等于」断言守着的
    (test_review_overview.py 的 g64 两条), 无条件多渲染一个空折叠区会当场
    打红它们 —— 而那两条断言不该为了本卡的新区被放宽。
    同一块板既完成又被推迟时**只进已完成区**(done 优先): 一行渲染两次会让
    页面上的板数比投影里的多。这是实现决定, 不是产品裁定。
    """
    snoozed = snoozed or {}
    todo = [r for r in boards if r["board"] not in done and r["board"] not in snoozed]
    finished = [r for r in boards if r["board"] in done]
    pending = [r for r in boards if r["board"] in snoozed and r["board"] not in done]
    if todo:
        head = _board_table_html(vault_id, todo, now_local, done_action, None, snooze_action, None, tonight_available)
    elif finished and not pending:
        # 全做完了: 不复用 _board_table_html 的空态文案 (那句说的是"没有板",
        # 与"板都做完了"是两回事 —— 一字之差就把成就说成了空库)
        head = '<div style="color:#16a34a;margin:10px 0 4px;font-size:14px">🎉 今天列出的白板都标完成了</div>'
    elif pending:
        # 全被推迟 (或推迟+完成) 时那句"都标完成了"是错的 —— 推迟不是做完
        head = (
            '<div style="color:#b45309;margin:10px 0 4px;font-size:14px">😴 今天列出的白板都推开了 · 到点自己回来</div>'
        )
    else:
        head = _board_table_html(vault_id, todo, now_local, done_action)
    out = head
    if finished:
        out += (
            f'<details style="margin:6px 0 2px"><summary style="cursor:pointer;color:#6b7280;font-size:12px">'
            f"已完成（{len(finished)}）· 明天自动回来</summary>"
            # 已完成区: 不带完成钮 (done_action 缺省), 带撤销钮 —— 误点的唯一出口
            + _board_table_html(vault_id, finished, now_local, None, undo_action)
            + "</details>"
        )
    if pending:
        wake = _snooze_wake_label([snoozed[r["board"]] for r in pending])
        back = f"· 到 {html.escape(wake)} 自动回来" if wake else "· 到点自动回来"
        out += (
            f'<details style="margin:6px 0 2px"><summary style="cursor:pointer;color:#6b7280;font-size:12px">'
            f"已推迟（{len(pending)}）{back}</summary>"
            # 已推迟区: 既不带完成钮也不带撤销钮, 只带「取回」—— 误点的唯一出口
            + _board_table_html(vault_id, pending, now_local, None, None, None, unsnooze_action)
            + "</details>"
        )
    return out


def _card_html(
    entry: dict,
    now_local: datetime,
    refresh_action: str,
    done_action: str,
    undo_action: str | None = None,
    snooze_action: str | None = None,
    unsnooze_action: str | None = None,
    tonight_available: bool = True,
) -> str:
    """三级视图第一级: vault 卡片 (名+四态徽标+汇总行) → 板表格 → 操作行。"""
    vid = html.escape(entry["vault_id"])
    label, color = _STATUS_META[entry["status"]]
    status_badge = (
        f'<span style="background:{color};color:#fff;border-radius:999px;'
        f'padding:2px 10px;font-size:12px;white-space:nowrap">{label}</span>'
    )
    # CARD-G6-9b: 推送降级徽标。⛔ 条件是 `is True` 而不是真值判断 —— False
    # (推成功) 与 None (没推过/读不出) 都**不出**徽标。一枚无条件渲染的徽标
    # 零信息量: 每张卡都在喊降级等于没喊, 而那正是 test_overview_page_degrade_
    # badge_only_when_failed 的验伪锚要排除的形态。
    push_badge = ""
    if entry.get("push_degraded") is True:
        why = entry.get("last_error")
        # title 里带上原因: 徽标只有四个字, 到底是 Bark 没配 key 还是网断了,
        # 得能一眼问出来。html.escape 默认 quote=True —— 这串要进 title="…" 属性。
        tip = f"最近一次推送失败：{why}" if isinstance(why, str) and why else "最近一次推送失败"
        push_badge = (
            f'<span title="{html.escape(tip)}" style="background:#dc2626;color:#fff;'
            f"border-radius:999px;padding:2px 10px;font-size:12px;white-space:nowrap;"
            f'cursor:help">{_PUSH_DEGRADED_LABEL}</span>'
        )
    # 降级时两枚徽标归进一个 flex 容器: 外层是 space-between, 直接并排会把状态
    # 徽标甩到卡片正中间。不降级时**一个字节都不变** —— 既有页面门不受影响。
    badges = (
        status_badge
        if not push_badge
        else f'<span style="display:flex;gap:6px;align-items:center">{status_badge}{push_badge}</span>'
    )
    header = (
        '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
        f'<b style="font-size:16px">{vid}</b>'
        f"{badges}</div>"
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
            # CARD-G6-5-R: 分层计数行紧跟着它的节点级明细 (缺省整块不出现)
            + _queue_layers_html(entry["vault_id"], proj.get("bucket_rows"), now_local)
            # CARD-G6-7: 待做 / 已完成两区 + 写侧动作的诚实说明
            + _boards_split_html(
                entry["vault_id"],
                proj["boards"],
                now_local,
                set(entry.get("board_done") or ()),
                done_action,
                undo_action,
                # CARD-G6-6: 只投影仍在生效的推迟 (到期的条目对页面已不存在)
                dict(entry.get("snoozed") or {}),
                snooze_action,
                unsnooze_action,
                tonight_available,
            )
            + f'<div style="color:#6b7280;font-size:12px;margin:2px 0 6px">{html.escape(_DONE_NOTE)}</div>'
            + (
                f'<div style="color:#6b7280;font-size:12px;margin:2px 0 6px">{html.escape(_SNOOZE_NOTE)}</div>'
                if snooze_action
                else ""
            )
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
    now_local = datetime.fromisoformat(data["generated_at"])
    # 表单 action 用 url_for 的 **path**: 前缀改了不会漂 (硬编码 /api/v1/…
    # 会), 取 .path 而非绝对 URL 则不受反代改 host/scheme 影响
    refresh_action = request.url_for("review_overview_refresh").path
    done_action = request.url_for("review_overview_board_done").path
    undo_action = request.url_for("review_overview_board_undone").path
    snooze_action = request.url_for("review_overview_board_snooze").path
    unsnooze_action = request.url_for("review_overview_board_unsnooze").path
    # CARD-G6-6: 「今晚」这一档还给不给点, 由 _collect 那**一次**判定说了算 ——
    # 页面这里不再读一遍时钟 (两次读数会在 20:00 那一秒上互相矛盾)
    tonight_available = bool(data.get("tonight_available", True))
    cards = "".join(
        _card_html(
            e, now_local, refresh_action, done_action, undo_action, snooze_action, unsnooze_action, tonight_available
        )
        for e in data["vaults"]
    ) or ('<div style="color:#6b7280">VAULTS_ROOT 下未发现任何 vault (需含 .obsidian/ 目录)</div>')
    generated = html.escape(_fmt_local_dt(now_local))
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
#: CARD-G6-9c / D-18: TZ 与 CANVAS_TZ **在**白名单里 —— 生产器与后端进程必须
#: 看到同一个时区视图。此前它们由 _child_env 强制设成固定的 Asia/Shanghai,
#: 那让「用户所在地」这条口径在 refresh 路径上被硬编码顶掉 (见 _child_env)。
_ENV_PASSTHROUGH = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "SYSTEMROOT", "TZ", "CANVAS_TZ")


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

    TZ / CANVAS_TZ **透传**(CARD-G6-9c / D-18 2026-09-07)。要解决的问题没变:
    生产器的 `payload["date"] = now.astimezone(...).date().isoformat()` 与由它
    派生的 md 标题 `# 今日复习 · <date>`、Bark 通知 id `canvas-review-<date>`
    全都走**子进程自己看到的时区**; 后端容器 `TZ` 为空、`/etc/localtime ->
    Etc/UTC`(现网实测), 一旦父子两侧看到的时区不同, 同一个库的两条生成路径
    就会给出不同的 date, 取决于谁最后写 —— 而端点照样返回 rebuilt=true /
    status=ok, 页面上没有任何异常信号, 正是"静默产出错日期"。
    (CARD-G6-1 收官审计实测: TZ=Asia/Shanghai → date=2026-08-31,
     TZ=UTC → date=2026-08-30, 同一时刻同一个库。)

    ⛔ **历史记录 + D-18 反转**: 此前这里把子进程的 TZ 强制赋成一个固定的
    显示时区名, 不接受父进程的值。那在"显示口径恒为该固定时区"的
    前提下是对的, 但 D-18 (2026-09-07 用户裁定) 推翻了该前提:「今天」= 用户
    **当前所在地**。硬编码的强制值会让 refresh 路径成为第五套时钟 —— 用户
    出门换时区后, 页面按机器本地归日, refresh 重生成的 payload 却仍是上海日。
    改为透传后, 父子进程读的是同一个 `app.core.display_tz` / `scripts.local_tz`
    来源 (CANVAS_TZ 优先, 否则 TZ, 否则 /etc/localtime), 分叉面消失。
    父进程 TZ 为空时子进程也读不到, 双方一起落到 `/etc/localtime` 那一档 ——
    仍是同一个答案, 这正是"同一视图"要的。

    PYTHONDONTWRITEBYTECODE=1 不是可选项: 生产器的 load_decay() 会
    `import decay_beta`, 该模块在 **vault 内** (<vault>/.claude/scripts/),
    不禁字节码就会在库里落 __pycache__/ —— 直接打破「只写 outputs/今日
    复习.*」的写面承诺, 且这类残渣会被 Obsidian 同步/备份链一路带走。
    PYTHONNOUSERSITE=1 同理堵掉 ~/.local/lib 的用户级 site-packages。
    """
    env = {k: v for k in _ENV_PASSTHROUGH if (v := os.environ.get(k)) is not None}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    # CARD-G6-9c: TZ / CANVAS_TZ 走 _ENV_PASSTHROUGH 透传, 这里**不再强制赋值**
    # —— 见上面 docstring 的「历史记录 + D-18 反转」段。
    return env


def _run_pick(script: Path, vault_dir: Path, state_file: Path | None = None) -> subprocess.CompletedProcess:
    """跑 `python <script> --vault <vault> --write` (写面只有 outputs/今日复习.*)。

    CARD-G6-7-R: state_file 非 None 时追加 `--state <它>` —— 生产器对 state
    **只读** (取 board_last_recommended 与 board_done), 从不写它。缺省 None
    保留"不传"这条路: runner 不可达时刷新照常跑, 只是拿不到那两笔账。
    """
    # stdout 丢弃 (Codex round-3): 生产器会把整份 payload 打到 stdout —— 大库
    # 里那是几 MB 的无用副本, 我们只从盘上读产物。errors="replace": 子进程
    # 若吐出非法字节, 严格解码会抛 UnicodeDecodeError 逃逸成 500, 而这里的
    # 全部错误路径都该是 503。
    argv = [sys.executable, str(script), "--vault", str(vault_dir), "--write"]
    if state_file is not None:
        argv += ["--state", str(state_file)]
    return subprocess.run(  # noqa: S603 — argv 列表 + 服务端自解析路径, 无 shell
        argv,
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
        return _vault_entry(vault_dir, datetime.now(_display_tz()).date())
    except Exception as e:  # noqa: BLE001
        logger.exception("review_overview refresh 读回异常", vault=vault_dir.name)
        return {
            "vault_id": vault_dir.name,
            "path": str(vault_dir),
            "status": "corrupt",
            "projection": None,
            "error": f"{type(e).__name__}: {str(e)[:200]}",
            # CARD-G6-9b: 本条兜底此前**漏了** board_done / snoozed 两个加性键
            # (G6-7 / G6-6 各自加键时没回来补这一格), 于是"四态一律带键"在
            # refresh 的 corrupt 路径上其实是不成立的。本卡加 push 两键时一并
            # 补齐 —— 缺键与值为空是两回事, 消费方只该面对后者。
            "board_done": [],
            "snoozed": {},
            "push_degraded": None,
            "last_error": None,
        }


def _rebuild_projection(vault_dir: Path, script: Path, state_file: Path | None = None) -> tuple[dict, dict | None]:
    """per-vault 串行 + TTL 去抖地重建一次投影 (同步; 由 FastAPI 线程池承载)。

    ── 写侧安全 (本函数的全部承诺) ──
    ① 只写 outputs/今日复习.md + .json: 生产器 --write 的写面就是这两个文件
       (加 outputs/ 目录本身的 mkdir), 配 PYTHONDONTWRITEBYTECODE 堵掉
       vault 内 __pycache__ 这条隐藏写面;
    ② 不走 runner、**不写** runner state: CARD-G6-7-R 起传 `--state` (生产器
       对 state 只读, 从不写它), 但本函数自己一个字节都不往
       backups/daily-review.*.state.json 里写 —— 只读地把它交给子进程。
       board_last_recommended 与 board_done 自本卡起参与本次 tie-break /
       让位: 从前不传的代价是"页面上把板折进已完成区了, 榜首却纹丝不动",
       用户看到的是标了完成也没用。state 不可达 (runner 缺席) 时退回不传,
       响应里 state_passed=false 如实说出走了哪条路;
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
            # ⚠ Codex round-2 L3: 没起子进程 ⇒ 这一次**没有**把账交给生产器。
            # 报 true 会让调用方以为让位已经算过了 (它其实只是"路径可用")。
            "state_passed": False,
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
                "state_passed": False,  # 同 in_progress: 本次没起子进程, 账没交出去
                "duration_ms": None,
                "retry_after_seconds": round(_REFRESH_TTL_SECONDS - (now - last), 3),
                "rebuild_count": _refresh_counts.get(key, 0),
            }, None
        started = time.monotonic()
        json_path = vault_dir.joinpath(*_PROJECTION_REL)
        md_path = vault_dir.joinpath(*_PROJECTION_MD_REL)
        before_fp = _publish_fingerprint(json_path)
        try:
            proc = _run_pick(script, vault_dir, state_file)
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
            # 本次真起了子进程 —— argv 里到底带没带 --state
            "state_passed": state_file is not None,
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


# ════════════════════════════════════════════════════════════════════
# CARD-G6-7 完成本板反馈 (BATCH-2026-09-05-第十二批)
# ════════════════════════════════════════════════════════════════════

#: runner 脚本文件名 —— 与生产器同目录 (同一 checkout, 同一 commit)。
#: 定位复用 _pick_script_candidates 的候选序: 「脚本在哪」只有一条规则,
#: 不给"生产器找得到、runner 找不到"这种半可用状态留缝。
_RUNNER_BASENAME = "daily_review_run.py"


def _refresh_state_file(vault_dir: Path) -> Path | None:
    """刷新要传给生产器的 state 路径; 拿不到就 None (读松, 不 503)。

    与 _board_done_today 同一条读侧纪律: runner 缺席 / 路径派生失败, 代价
    只是这一轮少两笔账, 不该把刷新本身打死。
    """
    runner = _runner_or_none(Path(get_settings().VAULTS_ROOT).resolve())
    if runner is None:
        return None
    try:
        return runner.state_path(vault_dir)
    except Exception:  # noqa: BLE001 — 派生失败按"没有 state", 不拖垮刷新
        logger.warning("review_overview 无法为刷新派生 state 路径", vault=vault_dir.name)
        return None


#: 已加载的 runner 模块 (进程内单例)。state 文件名规则 (vault_key)、
#: BACKUPS 位置、损坏隔离与原子写全部住在它里面 —— 本端点一行都不复制。
_RUNNER_MODULE_NAME = "daily_review_run"
_runner_load_lock = threading.Lock()

#: per-state-file 写锁: 同一库的两次点击串行化 (read-modify-write)。
#: 这是**第二层** —— CARD-G6-7-R 起真正跨进程的那把在 runner 侧
#: (state_locked, fcntl 文件锁), 本表只省掉同进程内取文件锁的开销并保持
#: 既有语义。runner 每小时 :05 档与本端点之间的窄竞态窗已由那把锁 + 锁内
#: 三方合并收口 (合并律见 daily_review_run._merge_state_with_disk)。
_board_done_locks: dict[str, threading.Lock] = {}
_board_done_locks_guard = threading.Lock()


def _runner_script(vaults_root: Path) -> Path | None:
    """daily_review_run.py 的位置; 找不到返回 None (调用方自行决定松紧)。

    读路径拿 None 当作"没有完成记录"(总览页照常出), 写路径拿 None 当作
    503 fail-closed —— 读松写紧, 因为读错了只是少显示一块折叠区, 写错了
    是把用户的完成账落到一个谁也不会再读的地方。
    """
    for c in _pick_script_candidates(vaults_root):
        runner = c.with_name(_RUNNER_BASENAME)
        try:
            if runner.is_file():
                return runner
        except OSError:  # 路径过长 / 权限 / 断链 symlink: 当作未命中继续
            continue
    return None


def _load_runner(script: Path):
    """加载 runner 模块 (state schema 与路径规则的唯一定义点)。

    进程内单例: 已在 sys.modules 且指向同一份文件时直接复用 —— 回归测试
    自己也 import 了同一个文件, 复用同一个对象才让 monkeypatch(BACKUPS)
    在两边看到同一份状态, 否则会出现"补丁打在 A 副本、被测代码读 B 副本"
    的假绿。⚠ 必须先 sys.modules 注册再 exec_module: 未注册时模块内的自
    引用 (含 dataclass 自省) 会拿不到自己的命名空间。
    """
    with _runner_load_lock:
        cached = sys.modules.get(_RUNNER_MODULE_NAME)
        if cached is not None:
            try:
                if Path(getattr(cached, "__file__", "") or "").resolve() == script.resolve():
                    return cached
            except OSError:
                pass
        spec = importlib.util.spec_from_file_location(_RUNNER_MODULE_NAME, script)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法为 {script} 建立 import spec")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[_RUNNER_MODULE_NAME] = mod
        # CARD-G6-7 (Codex round-1 LOW): 加载不许留下副产品。SourceFileLoader 默认写
        # scripts/__pycache__/{daily_review_run,send_bark}.cpython-*.pyc, 而**读路径**
        # (GET /overview 经 _runner_or_none) 也会走到这里 —— 一个 GET 写文件, 哪怕写的
        # 是 gitignored 的字节码, 也已经破坏了本模块自 CARD-G6-1 起就成文、也有门守着的
        # 「两个 GET 端点只读」不变量 (冷启动实测: 首次 GET 写出那两个 .pyc)。
        # ⚠ 副作用面如实登记: dont_write_bytecode 是解释器级全局, 这段窗口内**其它线程**
        # 的 import 也不写缓存 —— 代价只是那几次 import 慢一点, 不改变任何语义; 窗口被
        # _runner_load_lock 限制在一次模块加载内, 且无条件恢复。
        prev_dont_write = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(mod)
        except BaseException:
            sys.modules.pop(_RUNNER_MODULE_NAME, None)  # 半加载的壳不留在表里
            raise
        finally:
            sys.dont_write_bytecode = prev_dont_write
        return mod


def _runner_or_none(vaults_root: Path):
    """读路径用: 拿不到 runner 就 None —— 代价只是少显示一块「已完成」区。

    读松写紧是本卡的口径 (见 _runner_script): 读错了页面少块东西, 写错了
    是把用户的完成账落到一个谁也不会再读的地方。
    """
    script = _runner_script(vaults_root)
    if script is None:
        return None
    try:
        return _load_runner(script)
    except Exception as e:  # noqa: BLE001 — 外部脚本任意失败形态
        logger.warning("review_overview 无法加载 runner 模块 (读路径降级)", script=str(script), error=repr(e))
        return None


def _require_runner(vaults_root: Path):
    """写路径用: 拿不到 runner 一律 503 fail-closed, 绝不另起一套账。

    与 _runner_or_none 分成两个函数而不是一个 `required: bool` 开关 ——
    后者的返回类型恒是 `模块 | None`, 调用点必须为一条**走不到**的 None
    分支写防御代码 (或者不写, 让类型检查器闭嘴)。分开之后本函数的返回
    类型就是模块本身: 拿到手即可用, 这一点由签名保证而不是靠注释。
    """
    script = _runner_script(vaults_root)
    if script is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "runner_script_not_found",
                "message": (
                    f"未找到 {_RUNNER_BASENAME} —— 完成账要写进 runner 的 per-vault state, "
                    "脚本不可达时拒绝服务而非另起一套账。"
                ),
                "tried": [str(c.with_name(_RUNNER_BASENAME)) for c in _pick_script_candidates(vaults_root)],
            },
        )
    try:
        return _load_runner(script)
    except Exception as e:  # noqa: BLE001 — 外部脚本任意失败形态
        logger.warning("review_overview 无法加载 runner 模块 (写路径拒绝)", script=str(script), error=repr(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": "runner_module_unavailable",
                "message": f"无法加载 {_RUNNER_BASENAME} (完成账的 schema 与路径规则住在它里面): {type(e).__name__}",
                "tried": [str(script)],
            },
        )


def _read_board_done(state_file: Path) -> dict[str, str]:
    """state 的 board_done 只读投影 —— **不隔离、不重建、不写盘**。

    与 runner.load_state 的分工见模块 docstring ②: 那条路径遇到损坏文件会
    改名隔离 (一次写), 放进 GET 就破坏本模块的只读契约。所以读侧只做最窄的
    事: 读得出就用, 读不出/形状不对一律当作"没有完成记录", 绝不把总览页
    打成 500, 也绝不因为"顺手修一下"而在只读请求里动盘。
    """
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    done = st.get("board_done") if isinstance(st, dict) else None
    if not isinstance(done, dict):
        return {}
    return {k: v for k, v in done.items() if isinstance(k, str) and isinstance(v, str)}


def _board_done_today(vault_dir: Path, vaults_root: Path, today: str) -> list[str]:
    """该库今天被标完成的板名 (排序稳定)。读路径, 任何不可用 → 空列表。"""
    runner = _runner_or_none(vaults_root)
    if runner is None or not today:
        return []
    try:
        state_file = runner.state_path(vault_dir)
    except Exception:  # noqa: BLE001 — 派生失败按"没有完成记录", 不拖垮总览
        logger.warning("review_overview 无法派生 state 路径", vault=vault_dir.name)
        return []
    return sorted(b for b, d in _read_board_done(state_file).items() if d == today)


def _read_push_status(state_file: Path) -> tuple[bool | None, str | None]:
    """state 的推送结果只读投影 —— **不隔离、不重建、不写盘** (CARD-G6-9b)。

    与 _read_board_done / _read_snoozed 逐条同纪律 (见那里)。本函数的全部意义
    在于**三态可区分**:
      True  = 最近一次跑推失败了 (runner 写 last_result="generated_push_failed"
              + last_error="bark-send", scripts/daily_review_run.py:745/:746);
      False = 最近一次推成功了 (同文件 :739 写 "pushed") —— **只认这一个枚举**;
      None  = 没有 state 文件 / 读不出 / 形状不对 / 从来没推过 (无 last_result 键)
              / last_result 是个既非成功也非已知失败的值 (未知不等于成功)。

    ⛔ None 不得用 False 冒充 —— False 说的是"推过, 好着呢"。把"今天根本没跑过"
    显示成那样, 正是本卡要消灭的那种「看起来一切正常」: 用户手机上什么都没收到,
    页面上却一片绿。

    ⚠ last_error 是从外部文件读出的 str, 会原样进响应 JSON 与页面 —— JSON 的
    `\\ud800` 转义解出的**孤立 surrogate** 是合格的 str, 过得了 isinstance 的门,
    却在响应做 UTF-8 序列化时才抛 UnicodeEncodeError; 那一刻已经出了 _collect 的
    单库兜底, 于是**整个**总览变 500 (与 _read_snoozed 同款陷阱)。故编不出 UTF-8
    的原因文本丢弃成 None —— 但 degraded 这个信号本身留住: **读不出原因不等于
    没出事**。
    """
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return (None, None)
    if not isinstance(st, dict) or "last_result" not in st:
        # 键不在 = 这个库从来没跑过推送 (旧 state / 刚建的库), 与"没有文件"
        # 同等对待 —— 两者在用户那里是同一件事: 今天的推送根本没发生。
        return (None, None)
    err = st.get("last_error")
    # Codex r1 MEDIUM-1: 三态由 last_result 的**明确枚举**决定, 不许由「它不是
    # 失败」反推出「它是成功」。原写法 `== 失败 or bool(err)` 有两个反面:
    #   · `{"last_result": null}` / 任何未知值 + 无 err ⇒ 判 False = 报告推成功,
    #     可我们一次都没确认过它推过 —— 与本函数开头那条「None 不得用 False
    #     冒充」是同一个缺陷, 只是换了个输入面;
    #   · `{"last_result": "pushed", "last_error": "陈旧原因"}` ⇒ 判 True =
    #     给一个好好的库挂假警报, 徽标天天喊狼来了就没人看了。
    if st.get("last_result") == "pushed":
        degraded = False
    elif st.get("last_result") == "generated_push_failed" or bool(err):
        # 已知失败枚举, **或**未知结果却记下了错误原因 —— 后者是给将来 runner
        # 新增失败值留的余量: 说不清错在哪, 但它确实记了个错, 不该装没事。
        degraded = True
    else:
        # 未知 / null / 其它值且没有错误记录: 说不准。一律 None, 绝不报成功。
        # 连带 last_error 也归 None —— 既然结果读不出, 就没资格顺带断言
        # "而且没有错误"(`""` 正是这个断言)。与「无 last_result 键」那条出口
        # 同一个形状: 说不准就什么都不说。
        return (None, None)
    if not isinstance(err, str):
        return (degraded, None)
    try:
        err.encode("utf-8")
    except UnicodeEncodeError:
        # 与本模块其余读路径同纪律: 读不出的部分丢弃, 不把只读请求打成 500。
        # ⚠ 不把那个坏串塞进日志 —— 它正是编不出 UTF-8 的那个东西, structlog
        # 的序列化会在同一处再炸一次 (_read_snoozed 同款处置)。
        logger.warning("review_overview 推送原因含不可编码字符, 已丢弃该文本", state_file=state_file.name)
        return (degraded, None)
    return (degraded, err)


def _push_status(vault_dir: Path, vaults_root: Path) -> tuple[bool | None, str | None]:
    """该库最近一次推送的结果 (读路径, 任何不可用 → (None, None))。

    取 runner 与派生 state 路径的形态照抄 _board_done_today —— 推送账与完成账
    读的是**同一个 state 文件**, 两处各写一套取法早晚会漂移出"页面说推挂了、
    完成区却好好的"这种自相矛盾。
    """
    runner = _runner_or_none(vaults_root)
    if runner is None:
        return (None, None)
    try:
        state_file = runner.state_path(vault_dir)
    except Exception:  # noqa: BLE001 — 派生失败按"没有推送记录", 不拖垮总览
        logger.warning("review_overview 无法派生 state 路径 (推送状态)", vault=vault_dir.name)
        return (None, None)
    return _read_push_status(state_file)


#: 「今晚」这一档的小时阈值 (显示时区本地时)。⚠ CARD-G6-6: 这是**任务书默认
#: 值**, 未经用户显式裁定 —— 改产品语义只动这一个常量, 但那是用户的决定。
_SNOOZE_TONIGHT_HOUR = 20

#: 推迟的两档 (D-8 甲: 板级 + 两档)。⛔ 只有这两档 —— 自定义天数 / 自由时间
#: 一律 422, 页面上也没有输入框。收窄的理由: 一个"推迟多久"的输入框会让
#: snooze 变成第二套排期系统, 而排期归 FSRS。
_SNOOZE_CHOICES = ("tonight", "tomorrow")


def _snooze_until(choice: str, now_local: datetime) -> datetime | None:
    """把一档枚举换算成绝对时刻; 不在两档里 → None (调用方 422)。

    ⛔ 「明天」用 **date 加法 + combine** 而不是 `now + timedelta(hours=24)`:
    DST 切换日的一天不是 24 小时, 加满 24 小时会落到 23:00 或次日 01:00 ——
    「明天 00:00」就成了今天深夜或明天凌晨一点, 而用户看到的文案还写着 00:00。
    tzinfo 用调用方那一次读数的 tzinfo (ZoneInfo 实例), 于是 offset 按**那一天**
    求值, 不是把今天的偏移量硬搬到明天。
    """
    if choice == "tonight":
        return now_local.replace(hour=_SNOOZE_TONIGHT_HOUR, minute=0, second=0, microsecond=0)
    if choice == "tomorrow":
        return datetime.combine(now_local.date() + timedelta(days=1), datetime.min.time(), tzinfo=now_local.tzinfo)
    return None


def _read_snoozed(state_file: Path) -> dict[str, str]:
    """state 的 snoozed 只读投影 —— **不隔离、不重建、不写盘**。

    与 _read_board_done 逐条同纪律 (见那里): 读得出就用, 读不出 / 形状不对
    一律当作"没有推迟记录", 绝不把总览页打成 500, 也绝不在只读请求里动盘。
    值本身能不能解析成时刻由 _snoozed_active 再判一道 —— 这里只管形状。

    ⚠ Codex round-1 MEDIUM-2: `isinstance(str)` 不够。JSON 的 "\\ud800" 转义解出
    的是**孤立 surrogate** —— 它是合格的 str, 过得了下面的门, 却在响应做 UTF-8
    序列化时才抛 UnicodeEncodeError。那一刻已经出了 _collect 的单库兜底
    (`except Exception` 包的是 _vault_entry 那一层), 于是**整个**总览 GET 变 500,
    连别的库都看不成。projection 那一侧早有同款门 (_vault_entry 里那句
    `json.dumps(...).encode("utf-8")`), 本卡新增的这条投影必须同样过一遍。
    """
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    snoozed = st.get("snoozed") if isinstance(st, dict) else None
    if not isinstance(snoozed, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in snoozed.items():
        if not (isinstance(k, str) and isinstance(v, str)):
            continue
        try:
            (k + v).encode("utf-8")
        except UnicodeEncodeError:
            # 与本模块其余读路径同纪律: 读不出的条目丢弃, 不把只读请求打成 500
            # ⚠ 字段名给的是 **state 文件名**(含 vault key) 而不是 `vault=` ——
            # state_file.parent.name 恒是 "backups", 拿它当 vault 名是 DD-13 名实不符。
            # 也不把那个坏键塞进日志: 它正是编不出 UTF-8 的那个东西, structlog 的
            # 序列化会在同一处再炸一次。
            logger.warning("review_overview 推迟账含不可编码字符, 已丢弃该条", state_file=state_file.name)
            continue
        out[k] = v
    return out


def _snoozed_active(vault_dir: Path, vaults_root: Path, now: datetime) -> dict[str, str]:
    """该库此刻**仍在生效**的推迟 {board: until_iso}。读路径, 不可用 → 空。

    活跃判定与生产器**共用同一个函数** (daily_review_pick.active_snoozed) ——
    页面上"还在已推迟区里"与榜上"还没回来"必须是同一件事; 两处各写一遍
    早晚会漂移出「页面说已回来、榜上还压着」这种自相矛盾的形态。
    """
    runner = _runner_or_none(vaults_root)
    if runner is None:
        return {}
    try:
        state_file = runner.state_path(vault_dir)
    except Exception:  # noqa: BLE001 — 派生失败按"没有推迟记录", 不拖垮总览
        logger.warning("review_overview 无法派生 state 路径 (snoozed)", vault=vault_dir.name)
        return {}
    raw = _read_snoozed(state_file)
    if not raw:
        return {}
    try:
        active = runner.active_snoozed(raw, now)
    except Exception:  # noqa: BLE001 — 与本模块其余读路径同纪律, 只读绝不 500
        logger.warning("review_overview 推迟账解析失败", vault=vault_dir.name)
        return {}
    return {board: raw[board] for board in sorted(active)}


def _write_board_done(vault_dir: Path, vaults_root: Path, board: str, day: str) -> Path:
    """把「板 board 在 day 这天做完了」记进 state, 返回被写的 state 文件。

    ⛔ 本函数是本端点**唯一**的写点, 写面恰是那一个 state 文件:
      · 不碰任何节点 md (fsrs_* frontmatter 一个字节都不动);
      · 不追加 learning_events 账本 ——「做完了」是看板偏好, 不是学习事件;
      · 不写 vault 内任何路径 (BACKUPS 在仓库下, 不在库内)。
    读改写全程复用 runner.load_state / save_state: 损坏隔离与 os.replace
    原子写都是它们的既有行为, 这里不另写一套。

    ⚠ CARD-G6-7-R: load→改→save **三步在同一把跨进程锁内** (runner.state_locked)。
    只锁"写"那一下没有意义 —— load 与 save 之间正是 runner 的 :05 档能插进来
    的那段窗口。内层的 save_state 会检测到本线程已持锁而复用它。
    """
    runner = _require_runner(vaults_root)
    state_file = runner.state_path(vault_dir)
    with _board_done_locks_guard:
        lock = _board_done_locks.setdefault(str(state_file), threading.Lock())
    try:
        # ⚠ Codex round-1 M1: 取锁本身也在 try 里 —— mkdir/open 失败 (backups 被
        # 文件占位、锁文件不可写、锁路径是软链被 O_NOFOLLOW 拒) 都是 OSError,
        # 它们发生在 save_state 之前, 漏在 try 外就成了 500 裸 traceback,
        # 表单路径连动作专属错误页都拿不到。BASE 上这些情形返回的是 503。
        with lock, runner.state_locked(vault_dir):
            st = runner.load_state(vault_dir)
            done = st.setdefault("board_done", {})
            done[board] = day
            # 形态已含 v2 键 → 声明版本同步前进 (load_state 的同一条单调规则)
            declared = st.get("schema_version")
            if not isinstance(declared, int) or declared < runner.STATE_SCHEMA_VERSION:
                st["schema_version"] = runner.STATE_SCHEMA_VERSION
            runner.save_state(st, vault_dir)
    except OSError as e:
        # CARD-G6-7: save_state 的 mkdir / open / write / os.replace **四段任一**
        # 失败都落到这里 —— 那是**拒绝写出去**, 是本端点的正常失败态, 不该逃逸成
        # 500 裸 traceback。CARD-G6-7-R 起取锁的 mkdir/open 失败同样落这里。
        # ⚠ round-2 整改: 原文案把因果写死成「临时件路径异常」, 于是磁盘写满 /
        # backups 只读 / 超配额 (ENOSPC/EROFS/EDQUOT, 全是裸 OSError) 都被指向
        # "去查软链"这个错方向; 且 FileExistsError 在「backups 被文件占位」与
        # 「tmp 被抢先建成软链」两个不相干根因下报文逐字节相同。改回本文件其余
        # 6 处 OSError 一贯的 `类名: 详情` 形态 —— errno 与出错路径都在 str(e) 里。
        # 「未写出任何内容」这半句是承重的且全分支为真: 写失败即 unlink tmp,
        # os.replace 原子, state 与节点 md 逐字节不动。
        logger.warning("board-done 落账失败", vault=vault_dir.name, error=repr(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": "state_write_refused",
                "message": f"完成账落盘被拒绝 ({type(e).__name__}: {str(e)[:200]}) —— 未写出任何内容",
            },
        )
    return state_file


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


def _assert_board_name(board: str) -> None:
    """板名长度门 —— 两个写侧端点共用这一个实现。

    ⚠ CARD-G6-7-R (Codex round-1 第 5 问): 此前两处各写一份判断与错误体, 只共享
    _BOARD_NAME_MAX 一个常量, 自述里却称"三道门都是复用"。两份 422 报文会漂移,
    自述也就名实不符 (DD-13)。
    """
    if not board or len(board) > _BOARD_NAME_MAX:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "board_invalid",
                "message": f"board 必须是 1..{_BOARD_NAME_MAX} 字符的白板名 (实为 {len(board)} 字符)",
            },
        )


def _write_board_undone(vault_dir: Path, vaults_root: Path, board: str) -> tuple[Path, bool]:
    """把「这块板的完成记录」撤掉, 返回 (被写的 state 文件, 本来就没有)。

    与 _write_board_done 同一条纪律 (同一把锁、同一个写面、零 FSRS):
      · 写面恰是那一个 state 文件 (加 backups/ 下那把锁);
      · 不碰任何节点 md, 不追加 learning_events 账本;
      · 「撤销」撤的只是**人的判断**, 调度面本来就没被动过, 所以也没有
        任何东西需要"恢复"。

    键不存在 = **幂等**: 返回 already_undone=True 让调用方 200, 不 404。
    用户要的结果 (这块板现在没被标完成) 已经成立了; 把"已经是目标状态"
    报成失败, 是用状态码描述过程而不是结果。代价如实登记: 板名拼错也会
    答成功 —— 所以 already_undone 单独出现在响应里, 调用方分得出
    "撤掉了一条"与"本来就没有"。

    ⚠ 本来就没有时**不改写 state**: 一次无事可做的撤销不该动 state 的字节与
    mtime, 否则每点一次都在跟 runner 的 :05 档抢一次发布。
    说"不落盘"要收窄到 state 本身 (Codex round-1 第 5 问): 这条路仍会创建那把
    锁文件, 且若 state 当时是损坏的, load_state 照旧把它改名隔离 —— 两者都不是
    完成账的内容写入, 但确实动了盘。
    """
    runner = _require_runner(vaults_root)
    state_file = runner.state_path(vault_dir)
    with _board_done_locks_guard:
        lock = _board_done_locks.setdefault(str(state_file), threading.Lock())
    try:
        # 取锁也在 try 内 (Codex round-1 M1, 与 _write_board_done 同款)
        with lock, runner.state_locked(vault_dir):
            st = runner.load_state(vault_dir)
            done = st.setdefault("board_done", {})
            if board not in done:
                return state_file, True
            done.pop(board, None)
            declared = st.get("schema_version")
            if not isinstance(declared, int) or declared < runner.STATE_SCHEMA_VERSION:
                st["schema_version"] = runner.STATE_SCHEMA_VERSION
            runner.save_state(st, vault_dir)
    except OSError as e:
        # 与 board-done 同款: 取锁的 mkdir/open 与 save_state 的四段任一失败
        # 都是**拒绝写出去**, 是正常失败态而不是 500 裸 traceback。
        # 「未写出任何内容」全分支为真: 写失败即 unlink tmp, os.replace 原子。
        logger.warning("board-undone 落账失败", vault=vault_dir.name, error=repr(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": "state_write_refused",
                "message": f"撤销落盘被拒绝 ({type(e).__name__}: {str(e)[:200]}) —— 未写出任何内容",
            },
        )
    return state_file, False


def _write_board_snooze(vault_dir: Path, vaults_root: Path, board: str, until_iso: str) -> Path:
    """把「板 board 推迟到 until_iso」记进 state, 返回被写的 state 文件。

    与 _write_board_done 逐条同纪律 (同一把锁、同一个写面、零 FSRS):
      · 写面恰是那一个 state 文件 (加 backups/ 下那把锁);
      · 不碰任何节点 md —— **推迟改的是今天的推荐顺序, 不是任何节点的
        到期时刻**。压制 due 仍然是禁令 (D-8): 一块板被推到晚上, 它的卡
        该什么时候到期还是什么时候到期, 桶与合计一个数都不动;
      · 不追加 learning_events 账本 ——「今天先不看这块」是看板偏好, 不是
        学习事件。

    到期不需要清理器: 值 <= now 即非活跃 (active_snoozed 的判定), 旧键留在
    账里也不影响任何人。与完成账的隔日自然失效同一条律。
    """
    runner = _require_runner(vaults_root)
    state_file = runner.state_path(vault_dir)
    with _board_done_locks_guard:
        lock = _board_done_locks.setdefault(str(state_file), threading.Lock())
    try:
        # 取锁也在 try 内 (Codex round-1 M1, 与 _write_board_done 同款)
        with lock, runner.state_locked(vault_dir):
            st = runner.load_state(vault_dir)
            snoozed = st.setdefault("snoozed", {})
            snoozed[board] = until_iso
            declared = st.get("schema_version")
            if not isinstance(declared, int) or declared < runner.STATE_SCHEMA_VERSION:
                st["schema_version"] = runner.STATE_SCHEMA_VERSION
            runner.save_state(st, vault_dir)
    except OSError as e:
        # 与 board-done 同款: 取锁的 mkdir/open 与 save_state 的四段任一失败
        # 都是**拒绝写出去**, 是正常失败态而不是 500 裸 traceback。
        logger.warning("board-snooze 落账失败", vault=vault_dir.name, error=repr(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": "state_write_refused",
                "message": f"推迟落盘被拒绝 ({type(e).__name__}: {str(e)[:200]}) —— 未写出任何内容",
            },
        )
    return state_file


def _write_board_unsnooze(vault_dir: Path, vaults_root: Path, board: str) -> tuple[Path, bool]:
    """把「这块板的推迟记录」撤掉, 返回 (被写的 state 文件, 本来就没有)。

    与 _write_board_undone 逐条同形 —— 幂等 200 而不是 404 (用户要的结果
    「这块板现在没被推迟」已经成立), 本来就没有时**不改写 state**(一次无事
    可做的撤销不该动 state 的字节与 mtime, 否则每点一次都在跟 runner 的
    :05 档抢一次发布)。
    """
    runner = _require_runner(vaults_root)
    state_file = runner.state_path(vault_dir)
    with _board_done_locks_guard:
        lock = _board_done_locks.setdefault(str(state_file), threading.Lock())
    try:
        with lock, runner.state_locked(vault_dir):
            st = runner.load_state(vault_dir)
            snoozed = st.setdefault("snoozed", {})
            if board not in snoozed:
                return state_file, True
            snoozed.pop(board, None)
            declared = st.get("schema_version")
            if not isinstance(declared, int) or declared < runner.STATE_SCHEMA_VERSION:
                st["schema_version"] = runner.STATE_SCHEMA_VERSION
            runner.save_state(st, vault_dir)
    except OSError as e:
        logger.warning("board-unsnooze 落账失败", vault=vault_dir.name, error=repr(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": "state_write_refused",
                "message": f"取消推迟落盘被拒绝 ({type(e).__name__}: {str(e)[:200]}) —— 未写出任何内容",
            },
        )
    return state_file, False


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


def _error_page_html(status: int, vault_id: str, detail, back: str, action_label: str = "刷新") -> str:
    """表单路径的失败页 (零 JS, 与总览页同族配色)。

    每一段都来自 detail 本身, 不编造原因; 原始 stderr 尾部原样放在
    <pre> 里 (人话解释不了的现场, 也不许藏)。
    CARD-G6-7: action_label 让第二个写侧动作复用本页而不是另抄一份 ——
    但标题必须说清是哪个动作失败了 (一页写着"刷新失败"、用户刚点的却是
    "这板做完了", 那比没有错误页更糟)。
    """
    d = detail if isinstance(detail, dict) else {"message": str(detail)}
    parts = [
        f'<h1 style="font-size:20px;margin:0 0 6px">{html.escape(action_label)}失败 · {html.escape(vault_id)}</h1>',
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
        f"<title>{html.escape(action_label)}失败</title></head>"
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
    state_file = None
    try:
        _assert_same_origin(request)
        vault_dir, script = _refresh_target(vault_id)
        # CARD-G6-7-R: 把 runner 的 state 只读地交给生产器 —— 完成账要参与
        # 让位, 否则页面折了、榜首没动。**读松**: 刷新是读侧重算, runner 不
        # 可达时退回不传而不是 503 (写侧的完成账才 fail-closed) —— Y2 之前
        # 这条路本来就不传 state, 为一个 tie-break 把整个刷新打死不划算。
        state_file = _refresh_state_file(vault_dir)
        result, entry = _rebuild_projection(vault_dir, script, state_file)
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
            # state_passed 由 _rebuild_projection 放进 result —— 只有它知道这一次
            # 到底有没有起子进程 (⚠ Codex round-2 L3: 在这里按"路径可用"算, 会让
            # debounced / in_progress 也报 true, 而那两条路根本没把账交出去)。
            # 语义: 本次有没有把完成账 / tie-break 记录交给生产器。false 不是失败。
            **result,
            "entry": entry,
        }
    )


#: 板名长度上限 (字符)。板名来自本页自己渲染的 hidden input, 但端点对
#: "能连到这个端口的人"是敞开的 (见 _assert_same_origin 的事实更正) ——
#: 没有上限的话, state 文件可以被一串超长键撑大到不可读。
_BOARD_NAME_MAX = 200


@review_overview_router.post(
    "/overview/board-done",
    summary="标记某块白板今天已完成 (CARD-G6-7; 显式用户触发, 零 FSRS 写入)",
)
def review_overview_board_done(
    request: Request,
    vault_id: str = Form(..., description="板所属的 vault 目录名 (须命中 VAULTS_ROOT 下的真实库)"),
    board: str = Form(..., description="白板名 (与投影 boards[].board 逐字节同形)"),
    redirect: str | None = Form(None, description="传 page 则 303 回总览页 (纯 HTML 表单用, 零 JS)"),
) -> Response:
    """把「这块板今天做完了」记进 runner 的 per-vault state。

    这是本端点第一个写侧**业务**动作 (refresh 写的是投影产物, 是重算的
    副产品; 本动作写的是用户的判断)。三条纪律见模块 docstring:

      · 写面恰是 backups/daily-review.<key>.state.json 一个文件 —— 节点
        frontmatter 的 fsrs_* 一个字节不动, learning_events 账本不追加。
        标记完成**不影响 FSRS**, 页面上也这么写着 (_DONE_NOTE)。
      · 允许一道题都没答就标完成 (用户裁决) —— 因为"做完了"记的是人的
        判断, 不是系统对掌握度的判断; 后者归 FSRS, 本动作碰不到它。
      · 「今天」是显示时区本地日 (_display_today, 与页面到期人话同源)。隔日
        自然失效: 不删旧键、不起定时清理 —— 值不等于今天就是没完成。

    两道写侧门与 refresh 完全同源 (复制一份 = 两份会漂移):
      _assert_same_origin  跨站表单 CSRF;
      _assert_write_target_contained  (在 _refresh_target 内) 软链逃逸。
    失败一律回原样 4xx/5xx —— 表单路径渲染人话错误页, 状态码不粉饰。

    撤销 (CARD-G6-7-R 已做): 误点后有 POST /overview/board-undone 当场取回,
    零 JS 页与交互壳各有一个入口。推迟 (snooze) 仍未做, 归后续卡 (D-8)。
    """
    try:
        _assert_same_origin(request)
        _assert_board_name(board)
        day = _display_today()
        if not day:
            # _display_day 在年份极值下返回 None —— 拿不到"今天"就没有可写的账,
            # 宁可 503 也不写一个空日期 (那会让"今天完成"永久为假)
            raise HTTPException(
                status_code=503,
                detail={"error": "today_unresolvable", "message": "无法解析当前显示时区的日期"},
            )
        vault_dir, _script = _refresh_target(vault_id)
        s = get_settings()
        vaults_root = Path(s.VAULTS_ROOT).resolve()
        state_file = _write_board_done(vault_dir, vaults_root, board, day)
    except HTTPException as e:
        if redirect != "page":
            raise
        return HTMLResponse(
            content=_error_page_html(
                e.status_code, vault_id, e.detail, request.url_for("review_overview_page").path, "标记完成"
            ),
            status_code=e.status_code,
        )
    if redirect == "page":
        # PRG: 303 回 GET —— 这里**只有成功一条路**能走到 (失败已在上面
        # 的 except 里渲染成错误页), 所以不存在 refresh 那种"与成功同形的
        # 303 掩盖了没重建"的问题: 走到这一行就是账已经落盘了。
        return RedirectResponse(url=request.url_for("review_overview_page").path, status_code=303)
    return JSONResponse(
        {
            "vault_id": vault_dir.name,
            "board": board,
            "done_date": day,
            "state_path": str(state_file),
            "fsrs_touched": False,  # 契约字面化: 本动作永不改调度面
        }
    )


@review_overview_router.post(
    "/overview/board-undone",
    summary="撤销「这板今天做完了」(CARD-G6-7-R; 显式用户触发, 零 FSRS 写入)",
)
def review_overview_board_undone(
    request: Request,
    vault_id: str = Form(..., description="板所属的 vault 目录名 (须命中 VAULTS_ROOT 下的真实库)"),
    board: str = Form(..., description="白板名 (与投影 boards[].board 逐字节同形)"),
    redirect: str | None = Form(None, description="传 page 则 303 回总览页 (纯 HTML 表单用, 零 JS)"),
) -> Response:
    """把「这块板今天做完了」这条记录撤掉。

    为什么要有它: 完成动作从前没有回头路 —— 误点之后板折进已完成区、榜首
    让给了别人, 而唯一的恢复途径是**等到明天**。一天太久了, 何况手滑是最
    常见的那种错。

    三道写侧门与 board-done 是**同一个函数**, 不是各写一份 (两份必然漂移):
      _assert_same_origin              跨站表单 CSRF;
      _assert_write_target_contained   (在 _refresh_target 内) 软链逃逸;
      _assert_board_name               空 / 超长板名 422。
    失败一律回原样 4xx/5xx —— 表单路径渲染人话错误页, 状态码不粉饰。

    本动作**不需要**「今天」: 完成账按 {board: 日期} 存, 撤销是按板名摘键。
    少一个可失败的依赖 (board-done 那边拿不到今天要 503) 就少一条失败路径。

    与 board-done 唯一形态差异: 键本来就不在账里 ⇒ 幂等 200 + already_undone,
    不 404 (理由与代价见 _write_board_undone)。
    """
    try:
        _assert_same_origin(request)
        _assert_board_name(board)
        vault_dir, _script = _refresh_target(vault_id)
        s = get_settings()
        vaults_root = Path(s.VAULTS_ROOT).resolve()
        state_file, already_undone = _write_board_undone(vault_dir, vaults_root, board)
    except HTTPException as e:
        if redirect != "page":
            raise
        return HTMLResponse(
            content=_error_page_html(
                e.status_code, vault_id, e.detail, request.url_for("review_overview_page").path, "取消完成"
            ),
            status_code=e.status_code,
        )
    if redirect == "page":
        # PRG: 303 回 GET —— 与 board-done 同款, 走到这一行就是账已经处理完了
        # (失败已在上面的 except 里渲染成错误页)。
        return RedirectResponse(url=request.url_for("review_overview_page").path, status_code=303)
    return JSONResponse(
        {
            "vault_id": vault_dir.name,
            "board": board,
            "undone": True,
            # 分开说: 调用方要区分得出"我撤掉了一条"和"本来就没有"
            "already_undone": already_undone,
            "state_path": str(state_file),
            "fsrs_touched": False,  # 契约字面化: 本动作永不改调度面
        }
    )


@review_overview_router.post(
    "/overview/board-snooze",
    summary="把某块白板推迟到今晚 / 明天 (CARD-G6-6; 显式用户触发, 零 FSRS 写入)",
)
def review_overview_board_snooze(
    request: Request,
    vault_id: str = Form(..., description="板所属的 vault 目录名 (须命中 VAULTS_ROOT 下的真实库)"),
    board: str = Form(..., description="白板名 (与投影 boards[].board 逐字节同形)"),
    until: str = Form(..., description="推迟档位: tonight (当日 20:00) 或 tomorrow (次日 00:00), 显示时区"),
    redirect: str | None = Form(None, description="传 page 则 303 回总览页 (纯 HTML 表单用, 零 JS)"),
) -> Response:
    """把「这块板今天先放一放」记进 runner 的 per-vault state。

    与 board-done 同一条纪律, 差别只在**它会自己回来**:

      · 写面恰是 backups/daily-review.<key>.state.json 一个文件 —— 节点
        frontmatter 的 fsrs_* 一个字节不动, learning_events 账本不追加。
        ⛔ **推迟不压制 due**: 板上每张卡该什么时候到期还是什么时候到期,
        五桶与合计一个数不动 —— 变的只是"今天先推荐哪块板"。
      · 两档而已 (D-8 甲): 今晚 = 当日 20:00, 明天 = 次日 00:00, 都按显示
        时区。没有自定义天数, 也没有自由时间输入 —— 一个"推迟多久"的框会
        让它变成第二套排期系统, 而排期归 FSRS。
      · until 一到自然回队: 没有清理器, 也不需要有。生产器每次算榜都现判
        "还活着吗", runner 的缓存门记着最早的唤醒点, 越过就重扫。

    ⚠ 20:00 之后点「今晚」= 一个已经过去的时刻 ⇒ 422 snooze_until_in_past,
    state 一个字节不动。页面本来就不该在那时渲染出「今晚」钮 (服务端按
    tonight_available 决定), 这条 422 是**兜底而不是消除竞态** —— GET 与
    POST 之间隔着一次网络往返, 正好跨过 20:00 那一秒的用户会看到钮、被打回。

    三道写侧门与 board-done 是**同一个函数**, 不是各写一份 (两份必然漂移):
      _assert_same_origin              跨站表单 CSRF;
      _assert_write_target_contained   (在 _refresh_target 内) 软链逃逸;
      _assert_board_name               空 / 超长板名 422。
    """
    try:
        _assert_same_origin(request)
        _assert_board_name(board)
        # 同一次时钟读数贯穿换算与"是不是已经过去了"的判定 —— 两次各读一遍
        # 会在 20:00 那一秒上给出自相矛盾的答案 (换算出的时刻合法, 紧接着的
        # 比较又说它已经过去)。tz 现调不缓存 (U6-A: 每次调用现取)。
        now_local = _display_now()
        until_dt = _snooze_until(until, now_local)
        if until_dt is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "snooze_until_invalid",
                    "message": f"until 只接受 {' / '.join(_SNOOZE_CHOICES)} 两档 (实为 {until[:50]!r})",
                },
            )
        if until_dt <= now_local:
            # ⛔ 不静默夹到下一档: 用户点的是「今晚」, 把它悄悄改成「明天」
            # 等于替他做了一个他没做的决定, 而他看到的反馈还写着"今晚"。
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "snooze_until_in_past",
                    "message": f"「{until}」换算出的时刻已经过去了 ({until_dt.isoformat(timespec='seconds')})",
                },
            )
        until_iso = until_dt.isoformat(timespec="seconds")
        vault_dir, _script = _refresh_target(vault_id)
        s = get_settings()
        vaults_root = Path(s.VAULTS_ROOT).resolve()
        state_file = _write_board_snooze(vault_dir, vaults_root, board, until_iso)
    except HTTPException as e:
        if redirect != "page":
            raise
        return HTMLResponse(
            content=_error_page_html(
                e.status_code, vault_id, e.detail, request.url_for("review_overview_page").path, "推迟"
            ),
            status_code=e.status_code,
        )
    if redirect == "page":
        # PRG: 303 回 GET —— 与 board-done 同款, 走到这一行就是账已经落盘了
        return RedirectResponse(url=request.url_for("review_overview_page").path, status_code=303)
    return JSONResponse(
        {
            "vault_id": vault_dir.name,
            "board": board,
            "snoozed_until": until_iso,
            "state_path": str(state_file),
            "fsrs_touched": False,  # 契约字面化: 本动作永不改调度面
        }
    )


@review_overview_router.post(
    "/overview/board-unsnooze",
    summary="取消某块白板的推迟 (CARD-G6-6; 显式用户触发, 零 FSRS 写入)",
)
def review_overview_board_unsnooze(
    request: Request,
    vault_id: str = Form(..., description="板所属的 vault 目录名 (须命中 VAULTS_ROOT 下的真实库)"),
    board: str = Form(..., description="白板名 (与投影 boards[].board 逐字节同形)"),
    redirect: str | None = Form(None, description="传 page 则 303 回总览页 (纯 HTML 表单用, 零 JS)"),
) -> Response:
    """把「这块板被推迟了」这条记录撤掉 —— 它立刻回到待做区。

    与 board-undone 同形 (那条的理由逐字适用: 误点之后唯一的恢复途径不该是
    "等到点"), 本动作同样**不需要**「今天」: 推迟账按 {board: 时刻} 存, 撤销
    是按板名摘键, 少一个可失败的依赖就少一条失败路径。

    键本来就不在账里 ⇒ 幂等 200 + already_unsnoozed, 不 404。
    """
    try:
        _assert_same_origin(request)
        _assert_board_name(board)
        vault_dir, _script = _refresh_target(vault_id)
        s = get_settings()
        vaults_root = Path(s.VAULTS_ROOT).resolve()
        state_file, already_unsnoozed = _write_board_unsnooze(vault_dir, vaults_root, board)
    except HTTPException as e:
        if redirect != "page":
            raise
        return HTMLResponse(
            content=_error_page_html(
                e.status_code, vault_id, e.detail, request.url_for("review_overview_page").path, "取消推迟"
            ),
            status_code=e.status_code,
        )
    if redirect == "page":
        return RedirectResponse(url=request.url_for("review_overview_page").path, status_code=303)
    return JSONResponse(
        {
            "vault_id": vault_dir.name,
            "board": board,
            "unsnoozed": True,
            # 分开说: 调用方要区分得出"我撤掉了一条"和"本来就没有"
            "already_unsnoozed": already_unsnoozed,
            "state_path": str(state_file),
            "fsrs_touched": False,  # 契约字面化: 本动作永不改调度面
        }
    )
