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
    seen_rows: set[tuple[str, str]] = set()
    for i, row in enumerate(due_nodes):
        if not isinstance(row, dict):
            raise ValueError(f"due_nodes[{i}] 应为 object, 实为 {type(row).__name__}")
        board = row.get("board")
        if not isinstance(board, str) or not board:
            raise ValueError(f"due_nodes[{i}].board 应为非空字符串, 实为 {board!r}")
        node = row.get("node")
        if not isinstance(node, str) or not node:
            raise ValueError(f"due_nodes[{i}].node 应为非空字符串, 实为 {node!r}")
        # Codex-D1 H5: 重复行会被静默重复计数 — 生产器 stem 唯一, 重复即垃圾
        if (board, node) in seen_rows:
            raise ValueError(f"due_nodes[{i}] 重复行: {board!r}/{node!r}")
        seen_rows.add((board, node))
        reason = row.get("due_reason")
        if reason not in ("new", "scheduled", "malformed"):
            raise ValueError(f"due_nodes[{i}].due_reason 枚举外: {reason!r}")
        ts = _due_ts(row.get("fsrs_due"), f"due_nodes[{i}].fsrs_due")
        # 生产器构造律: scheduled ⟺ fsrs_due 非空 (new/malformed 均为空串)
        if (reason == "scheduled") != bool(ts):
            raise ValueError(f"due_nodes[{i}] due_reason={reason!r} 与 fsrs_due={ts!r} 不自洽")
        g = groups.setdefault(board, {"due": 0, "new": 0, "earliest": ""})
        g["due"] += 1
        if reason == "new":
            g["new"] += 1
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
        gated.append(
            {
                "board": board,
                "next_due": _due_ts(u.get("next_due"), f"upcoming[{i}].next_due", allow_empty=False),
                "node": _opt_str(u.get("node"), f"upcoming[{i}].node"),
            }
        )
    return gated


def _gate_boards_rollup(
    rollup, due_groups: dict[str, dict], flat_placeholder: int
) -> tuple[dict[str, int], list[dict]]:
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
        ph_map[board] = counts["placeholder"]
        rollup_due[board] = counts["due"]
        if counts["due"] == 0:
            zero.append({"board": board, "next_due": next_due})
    derived_due = {b: g["due"] for b, g in due_groups.items()}
    claimed_due = {b: d for b, d in rollup_due.items() if d > 0}
    if claimed_due != derived_due:
        raise ValueError(f"boards rollup 到期计数与 due_nodes 明细不一致: rollup={claimed_due} 明细={derived_due}")
    if sum(ph_map.values()) > flat_placeholder:
        raise ValueError(f"boards rollup placeholder 合计 {sum(ph_map.values())} 超过扁平列表总数 {flat_placeholder}")
    return ph_map, zero


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
        b = _opt_str(tb.get("board"), f"top_boards[{i}].board")
        if b:
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
    groups = _gate_due_groups(due_nodes)
    ph_map: dict[str, int] = {}
    rollup_zero: list[dict] | None = None
    # "boards" in payload 而非 .get(): 显式 null 不是"旧投影缺省", 是形状
    # 垃圾 (Codex-D1 H5) — 生产器恒产出数组
    if "boards" in payload:
        ph_map, rollup_zero = _gate_boards_rollup(payload["boards"], groups, len(placeholder))
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

    generated_at = payload.get("generated_at")
    if not isinstance(generated_at, str):
        raise ValueError(f"generated_at 应为字符串, 实为 {type(generated_at).__name__}")
    pending = top.get("pending")
    if pending is not None:
        pending = _strict_int(pending)
    return {
        "schema_version": 3,
        "vault_id": _opt_str(payload.get("vault_id"), "vault_id"),  # C1a 加性; 旧投影缺 → null
        "date": _opt_str(payload.get("date"), "date"),
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
        # 且板级合计小于总数时标注差额, 汇总与表格才能对账
        ph_known = [r["placeholder"] for r in proj["boards"] if r.get("placeholder") is not None]
        unattributed = proj["placeholder_backlog"] - sum(ph_known) if ph_known else 0
        ph_note = f"（含未归板 {int(unattributed)}）" if unattributed > 0 else ""
        summary = (
            f'<div style="font-size:26px;margin:8px 0 0">到期 <b>{int(proj["due_count"])}</b>{mismatch}'
            f'<span style="font-size:13px;color:#6b7280"> · 新卡 {int(proj["due_new_count"])}'
            f" · 待剖析 {int(proj['placeholder_backlog'])}{ph_note}</span></div>"
        )
        gen_disp = html.escape(_fmt_projection_time(str(proj.get("generated_at") or "—")))
        body = (
            summary
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
