#!/usr/bin/env python3
"""CARD-G8-4 — 复习完成率周汇总（只读）+ 人工修复登记 / 找材料时间自报.

[BATCH-2026-09-18-第十五批 / CARD-G8-4]

**只读 / 零库连接**：全文件只用标准库 + 仓内三个只读 helper
（``local_tz`` / ``daily_review_pick`` 的 ``_fm_str``、``_board_name`` /
``daily_review_run`` 的 ``state_path``），不导入后端应用包、不连图数据库 /
向量库。**唯一写口**是 ``report --out``（缺省打印 stdout）与
``log-fix`` / ``log-material`` 的 ``--ledger``（必填，无缺省）。

**三个子命令的 ``--now`` 同语义**（裸时间按报告时区解释；缺省当前时刻）：
``report`` 用它钉窗口与周过滤，``log-fix`` / ``log-material`` 用它钉登记账的
``week`` —— 两侧同钟才可能跨周对得上（H-1 整改：登记侧时钟必须可注入）。

⛔ 本脚本**绝不**做的事：

* 不写 vault（``节点/*.md`` / ``learning_events.jsonl`` / ``outputs/`` 全只读）；
* 不写 state —— 读侧照 ``review_overview._read_board_done`` 的**只读投影**：
  读得出就用、读不出或形状不对一律当「无完成记录」，**不隔离、不重建、不写盘**。
  ⛔ 不调 ``runner.load_state`` / ``state_locked`` / ``save_state``（它们会建
  ``.lock``、损坏时改名隔离 —— 那是写）；
* 不新增 event_type、不改 frontmatter；
* 不引用 picker 里那个模块级时区常量与它的两个归日 helper（那是 P5 的改动面，
  且模块级常量在 import 期就定死了）——日界**每次调用**自己取
  :func:`report_timezone`。

**口径（与报告头逐字一致）**：对窗口内每一天 D ——

* ``reviewed(D)`` = 三来源**按节点去重**的并集：① 事件账里 ``schema_ext ==
  "review/1"`` 的 ``answer_scored`` / ``answer_abandoned`` 行，其 ``review_time``
  落在 D；② frontmatter ``calibration_log[].ts`` 落在 D；③ ``last_examined``
  落在 D。每个来源另出一列计数（列之和 ≥ 去重后的 ``reviewed``）。
* ``due(D)`` = ``reviewed(D)`` ∪ {节点：``fsrs_due`` 缺失（New）**或**非规范
  （fail-open，与 ``picker`` :547-555 同口径）**或** ``fsrs_due <= D 当日末刻的
  UTC-Z 串``（词法比较，与 ``picker`` :566 同口径）}。
* ``completion_rate(D)`` = ``|reviewed| / |due|``；``due`` 为 0 记 ``—``，**不记 0%**
  （0/0 不是 0）。
* 板级完成(D) = ``state.board_done[板] == D``；推迟中（今日）= ``state.snoozed``
  里 ``until > now`` 的板。

⚠️ **回溯日的到期集是估计**：frontmatter 是 *current state*（D0 修订），历史某天
「当时该复习哪些」**无法从当前状态精确回放** —— 复习后 ``fsrs_due`` 前移（低估）、
窗口内新建的 New 节点会被计入更早的日子（高估）。因此只有「今日」那一行可以与
``outputs/今日复习.json`` 精确对账。

退出码：``0`` 正常（state / 事件账缺失也算正常，报告里标明）；
``2`` 参数或输入形态拒绝（``--vault`` 不是目录 / ``节点/`` 缺失 / ``--out`` 不可写）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import daily_review_pick as picker  # noqa: E402
import daily_review_run as runner  # noqa: E402
import local_tz  # noqa: E402

RC_OK = 0
RC_REFUSED = 2

#: 最近一次 :func:`build_report` 的结构化结果 —— **只读快照**，供测试与调试
#: 逐格断言用；不参与任何判定，置不置它都不改变本脚本的行为与输出。
LAST_REPORT: dict | None = None

#: frontmatter 块 —— 与 ``picker`` :486 同款形态（含可选 BOM 与 CRLF）。
_FM_BLOCK_RE = re.compile("^\\ufeff?" + r"---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.S)
#: ``fsrs_due`` 规范形态 —— 与 ``picker`` :547 逐字同。
_DUE_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
#: 解析回合用的格式 —— 形态过了还要**日历有效**才算规范（见 :func:`_due_is_canonical`）。
_DUE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
#: ``calibration_log`` 块内的 ``ts:`` —— 要求**有前导空白**（= 嵌在列表项里），
#: 这样顶格的同名字段不会被误收。⛔ 只 regex 取，不解析 YAML（picker 也不引 yaml）。
_CAL_TS_RE = re.compile(r"^\s+ts:\s*\"?([^\"\n]+?)\"?\s*$", re.M)

#: 复习事件族 —— 与 ``learning_event_log`` :41-53 的白名单取交集。
REVIEW_EVENT_TYPES = frozenset({"answer_scored", "answer_abandoned"})
#: 唯一机械分界（schema 文档 :91-93）：只认挂在上面两类事件上的这个标记。
REVIEW_EXT_MARKER = "review/1"

#: 供 G8-6 采集器消费的字段名（报告 ① 段写明）。
COMPLETION_RATE_FIELD = "completion_rate"


# ═══════════════════════════════════════════════════════════════════════════
# 时间 / 日界
# ═══════════════════════════════════════════════════════════════════════════
def report_timezone():
    """报告的显示时区 —— **每次调用**都重新取（D-18）。

    ⛔ 不借 picker 的模块级时区常量：它在 import 期就定死了（此后改 ``CANVAS_TZ``
    对它无效），而且属 P5 的改动面；本脚本对它零耦合。
    """
    return local_tz.display_tz()


def _parse_instant(raw):
    """把 UTC-Z / 带偏移 / 裸 ISO 串解析成 tz-aware 时刻；解析不出给 None。

    裸串（无时区）一律按 **UTC** 解释：本脚本读到的三种时刻
    （``review_time`` / ``calibration_log.ts`` / ``last_examined``）按 schema 与
    live 实测都是 UTC-Z 整秒，裸串属于形态异常，猜本地只会制造沉默的偏移。
    """
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith(("z", "Z")):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _due_is_canonical(fsrs_due: str) -> bool:
    """``fsrs_due`` 是否规范 —— **两段**判定，与 ``picker`` :547-552 逐字同。

    ⚠️ 只查正则不够（picker 的 Codex-A2 M2 就是这条）：``2026-13-01T00:00:00Z``
    **能过**两位数字那档形态检查，却是个不存在的日历时刻；它在词法比较里排在
    ``2026-09-…`` 之后，会被静默判成「未来、还没到期」——一个脏值因此从待复习
    集里消失。所以形态过了还要 ``strptime`` 一次；过不了就 fail-open 视同到期。
    """
    if not _DUE_SHAPE.fullmatch(fsrs_due):
        return False
    try:
        datetime.strptime(fsrs_due, _DUE_FORMAT)
    except ValueError:
        return False
    return True


def _local_day(instant, tz) -> str | None:
    """tz-aware 时刻 → 显示时区的本地日 ``YYYY-MM-DD``。"""
    if instant is None:
        return None
    try:
        return instant.astimezone(tz).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _day_end_utc_z(day: str, tz) -> str:
    """显示时区某一天的**末刻**，格式化成 UTC-Z 串。

    产出的串专门拿去和 ``fsrs_due`` 做**词法**比较（与 ``picker`` :566 同法），
    所以格式必须与 ``fsrs_due`` 的规范形态逐字同款（定长、整秒、``Z`` 结尾）。
    """
    naive_end = datetime.fromisoformat(f"{day}T23:59:59")
    return naive_end.replace(tzinfo=tz).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_now(raw, tz):
    """``--now`` → tz-aware 时刻。

    ⚠️ **与 picker :1296 的一处有意偏离**（验收单已登记）：picker 对裸时间用
    ``.astimezone()``，那是**机器本地**；本脚本按**报告时区**解释。两者在
    ``CANVAS_TZ`` 未设时完全一致（``display_tz()`` 此时就是机器本地）；设了
    ``CANVAS_TZ`` 时才分叉，而那正是用户显式说了「我的显示时区是 X」的场合 ——
    一份按天汇总的报告里，裸的墙上时间只可能指那个时区的墙上时间。
    """
    if not raw:
        return datetime.now(timezone.utc).astimezone(tz)
    dt = _parse_instant_allow_local(raw, tz)
    if dt is None:
        raise ValueError(f"--now 解析不出: {raw!r}")
    return dt.astimezone(tz)


def _parse_instant_allow_local(raw: str, tz):
    text = raw.strip()
    if text.endswith(("z", "Z")):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=tz)


def iso_week(instant) -> str:
    y, w, _ = instant.isocalendar()
    return f"{y}-W{w:02d}"


# ═══════════════════════════════════════════════════════════════════════════
# 只读输入
# ═══════════════════════════════════════════════════════════════════════════
def _file_source(role: str, path: Path | None, *, lines: int | None = None, readable: bool | None = None) -> dict:
    """报告 ① 段的一条数据源自证（路径 / 是否存在 / sha256 / 行数）。"""
    entry = {"role": role, "path": str(path) if path else None, "exists": False, "sha256": None, "lines": lines}
    # ⚠️ 数据源不都是文件: ``节点/`` 是**目录**。只判 ``is_file()`` 会让它在
    # 报告里显示成「不存在」—— 一份声称「我读了这些」的自证表格里写错「存在」
    # 比不写更坏。目录按存在算, 但没有单一 sha256。
    if path is not None and path.is_dir():
        entry["exists"] = True
    elif path is not None and path.is_file():
        entry["exists"] = True
        try:
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            entry["sha256"] = None
    if readable is not None:
        entry["readable"] = readable
    return entry


def _split_physical_lines(raw: bytes) -> list[str]:
    """按**物理 LF** 切行 —— 与 ``learning_event_log._iter_lines`` :101-117 同语义。

    ⛔ 禁 ``str.splitlines()``：它还会在 ``\\v \\f \\x1c \\x1d \\x1e \\x85
    U+2028 U+2029`` 上切，而这些字符**可以合法出现**在某行的字符串值里。
    一条含裸 U+2028 的合法记录会被切成两个碎片、两半都 JSON 解析失败 ——
    那条复习记录就从统计里消失了，而且是静默消失。
    """
    text = raw.decode("utf-8", errors="replace")
    parts = text.split("\n")
    if text.endswith("\n"):
        parts = parts[:-1]
    return parts


def read_state_readonly(state_file: Path) -> dict:
    """per-vault state 的**只读投影**（抄 ``review_overview._read_board_done`` :2497）。

    读得出就用；读不出 / 顶层不是 dict / ``board_done`` 形状不对 —— 一律当作
    「无完成记录」并把 ``readable`` 标 False。⛔ **不隔离、不重建、不写盘**：
    那条路径（``runner.load_state`` → ``state_locked``）会建 ``.lock`` 并在损坏时
    改名留档，放进一个只读汇总里就破坏了只读契约。
    """
    out = {"path": str(state_file), "readable": False, "board_done": {}, "snoozed": {}}
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return out
    if not isinstance(payload, dict):
        return out
    done = payload.get("board_done")
    snoozed = payload.get("snoozed")
    if not isinstance(done, dict) or not isinstance(snoozed, dict):
        return out
    out["readable"] = True
    out["board_done"] = {k: v for k, v in done.items() if isinstance(k, str) and isinstance(v, str)}
    out["snoozed"] = {k: v for k, v in snoozed.items() if isinstance(k, str) and isinstance(v, str)}
    return out


def read_review_events(events_file: Path, tz) -> dict:
    """事件账里的复习行 —— 只收 ``review/1`` 标记的 ``answer_scored`` / ``answer_abandoned``。"""
    out = {"path": str(events_file), "exists": False, "total_lines": 0, "bad_lines": 0, "skipped": 0, "rows": []}
    try:
        raw = events_file.read_bytes()
    except OSError:
        return out
    out["exists"] = True
    for line in _split_physical_lines(raw):
        if not line.strip():
            continue
        out["total_lines"] += 1
        try:
            rec = json.loads(line)
        except ValueError:
            out["bad_lines"] += 1
            continue
        if not isinstance(rec, dict) or rec.get("event_type") not in REVIEW_EVENT_TYPES:
            out["skipped"] += 1
            continue
        payload = rec.get("payload")
        if not isinstance(payload, dict) or payload.get("schema_ext") != REVIEW_EXT_MARKER:
            out["skipped"] += 1
            continue
        node_id = rec.get("node_id") or payload.get("concept_id")
        day = _local_day(_parse_instant(payload.get("review_time")), tz)
        if not isinstance(node_id, str) or not node_id or day is None:
            out["skipped"] += 1
            continue
        out["rows"].append({"node_id": node_id, "day": day})
    return out


def read_frontmatter_signals(vault: Path, tz) -> dict:
    """扫 ``<vault>/节点/*.md``，逐节点取 ``fsrs_due`` / ``last_examined`` /
    ``calibration_log[].ts`` / ``source_board``。**只读**。"""
    out = {"nodes": [], "unreadable": []}
    for path in sorted((vault / "节点").glob("*.md")):
        stem = path.stem
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            out["unreadable"].append(stem)
            continue
        block = _FM_BLOCK_RE.match(text)
        fm = block.group(1) if block else ""
        fsrs_due = picker._fm_str(fm, "fsrs_due") or ""
        last_examined = picker._fm_str(fm, "last_examined")
        board = picker._board_name(picker._fm_str(fm, "source_board"))
        cal_days = sorted({d for d in (_local_day(_parse_instant(ts), tz) for ts in _CAL_TS_RE.findall(fm)) if d})
        out["nodes"].append(
            {
                "node_id": stem,
                "fsrs_due": fsrs_due,
                "fsrs_due_shape_ok": _due_is_canonical(fsrs_due) if fsrs_due else False,
                "board": board,
                "last_examined_day": _local_day(_parse_instant(last_examined), tz),
                "calibration_days": cal_days,
            }
        )
    return out


def read_ledger(ledger_file: Path, week: str) -> dict:
    """人工修复登记 / 找材料自报的只读侧。按物理 LF 切行，坏行跳过并计数。"""
    out = {"path": str(ledger_file), "exists": False, "bad_lines": 0, "fixes": [], "minutes": None}
    try:
        raw = ledger_file.read_bytes()
    except OSError:
        return out
    out["exists"] = True
    for line in _split_physical_lines(raw):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            out["bad_lines"] += 1
            continue
        if not isinstance(rec, dict) or rec.get("week") != week:
            continue
        if rec.get("kind") == "manual_fix":
            out["fixes"].append(
                {"ts": rec.get("ts"), "what": rec.get("what"), "who": rec.get("who"), "cmd": rec.get("cmd")}
            )
        elif rec.get("kind") == "material_minutes" and isinstance(rec.get("minutes"), int):
            out["minutes"] = rec["minutes"]  # 本周最后一条胜出
    return out


def read_today_json(path: Path) -> dict:
    """``outputs/今日复习.json`` 的只读投影（对账用）。"""
    out = {"path": str(path), "exists": False, "readable": False, "date": None, "due_nodes": None, "buckets": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return out
    out["exists"] = True
    if not isinstance(payload, dict):
        return out
    out["readable"] = True
    out["date"] = payload.get("date") if isinstance(payload.get("date"), str) else None
    due = payload.get("due_nodes")
    if isinstance(due, list):
        out["due_nodes"] = len(due)
    else:
        stats = payload.get("stats")
        if isinstance(stats, dict) and isinstance(stats.get("due_nodes"), int):
            out["due_nodes"] = stats["due_nodes"]
    stats = payload.get("stats")
    if isinstance(stats, dict):
        # 差额从哪来: 生产端把一部分节点判为 ineligible (占位符 / 测试 / 损坏)
        # 后才算 due_nodes, 而本报告的 due 按口径涵盖全部节点。把这些桶原样带出来,
        # 「不一致」才是一条能追下去的信息, 而不是两个对不上的数字。
        out["buckets"] = {k: v for k, v in stats.items() if isinstance(v, int) and k != "due_nodes"}
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 汇总
# ═══════════════════════════════════════════════════════════════════════════
def day_rows(days: list[str], signals: dict, events: dict, state: dict, now, tz) -> list[dict]:
    """逐日算 到期 / 已复习 / 三来源分列 / 完成率 / 板级完成 / 推迟中。"""
    events_by_day: dict[str, set] = {}
    for row in events["rows"]:
        events_by_day.setdefault(row["day"], set()).add(row["node_id"])

    rows = []
    for day in days:
        from_events = set(events_by_day.get(day, ()))
        from_cal = {n["node_id"] for n in signals["nodes"] if day in n["calibration_days"]}
        from_last = {n["node_id"] for n in signals["nodes"] if n["last_examined_day"] == day}
        reviewed = from_events | from_cal | from_last

        end_z = _day_end_utc_z(day, tz)
        due = set(reviewed)
        for node in signals["nodes"]:
            if not node["fsrs_due"]:
                due.add(node["node_id"])  # New：无字段 = 即刻到期（picker :566）
            elif not node["fsrs_due_shape_ok"]:
                due.add(node["node_id"])  # 非规范 fail-open（picker :547-555）
            elif node["fsrs_due"] <= end_z:
                due.add(node["node_id"])  # 词法比较，与 picker :566 同法

        rate = "—" if not due else f"{len(reviewed) * 100.0 / len(due):.1f}%"
        rows.append(
            {
                "date": day,
                "due": len(due),
                "reviewed": len(reviewed),
                "from_events": len(from_events),
                "from_calibration": len(from_cal),
                "from_last_examined": len(from_last),
                COMPLETION_RATE_FIELD: rate,
                "boards_done": sorted(b for b, d in state["board_done"].items() if d == day),
                "snoozed": sorted(_active_snoozed(state, now)) if day == days[-1] else [],
            }
        )
    return rows


def _active_snoozed(state: dict, now) -> list[str]:
    """仍在推迟中的板。

    ⛔ 不用 ``runner.active_snoozed``：它内部消费 picker 的模块级时钟，而本脚本
    的 ``--now`` 是可注入的；借那个函数会让「现在」有两个来源。
    """
    out = []
    for board, until in state["snoozed"].items():
        moment = _parse_instant(until)
        if moment is not None and moment > now:
            out.append(board)
    return out


def build_report(
    vault: Path,
    *,
    state_file: Path,
    events_file: Path,
    today_json: Path,
    ledger_file: Path,
    now,
    days: int,
    tz,
) -> dict:
    """产出结构化报告（不写任何文件）。"""
    today = now.astimezone(tz).date()
    window = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

    signals = read_frontmatter_signals(vault, tz)
    events = read_review_events(events_file, tz)
    state = read_state_readonly(state_file)
    week = iso_week(now.astimezone(tz))
    ledger = read_ledger(ledger_file, week)
    snapshot = read_today_json(today_json)

    rows = day_rows(window, signals, events, state, now, tz)
    today_row = rows[-1]

    if not snapshot["readable"]:
        reconcile = {
            "status": "不可读",
            "script": today_row["due"],
            "snapshot": None,
            "snapshot_date": None,
            "buckets": {},
        }
    elif snapshot["date"] != window[-1]:
        reconcile = {
            "status": "快照非当日",
            "script": today_row["due"],
            "snapshot": snapshot["due_nodes"],
            "snapshot_date": snapshot["date"],
            "buckets": snapshot["buckets"],
        }
    elif snapshot["due_nodes"] == today_row["due"]:
        reconcile = {
            "status": "一致",
            "script": today_row["due"],
            "snapshot": snapshot["due_nodes"],
            "snapshot_date": snapshot["date"],
            "buckets": snapshot["buckets"],
        }
    else:
        reconcile = {
            "status": "不一致",
            "script": today_row["due"],
            "snapshot": snapshot["due_nodes"],
            "snapshot_date": snapshot["date"],
            "buckets": snapshot["buckets"],
        }

    notes = []
    if not events["exists"]:
        notes.append("事件账文件不存在 —— 事件账来源整列为 0。")
    elif not events["rows"]:
        notes.append(f"事件账存在但没有 {REVIEW_EXT_MARKER} 行 —— 事件账来源整列为 0，复习数全靠 frontmatter 两源。")
    if not state["readable"]:
        notes.append("state: 不可读 —— 按「无完成记录」处理；⛔ 未隔离、未重建、未写盘。")
    if signals["unreadable"]:
        notes.append(f"{len(signals['unreadable'])} 个节点读不出，已跳过：{signals['unreadable'][:5]}")

    return {
        "card": "CARD-G8-4",
        "vault": str(vault),
        "timezone": getattr(tz, "key", str(tz)),
        "generated_at": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "week": week,
        "window": {"days": days, "from": window[0], "to": window[-1]},
        "sources": [
            _file_source("nodes_dir", vault / "节点", lines=len(signals["nodes"])),
            _file_source("state", state_file, readable=state["readable"]),
            _file_source("events", events_file, lines=events["total_lines"], readable=events["exists"]),
            _file_source("today_json", today_json, readable=snapshot["readable"]),
            _file_source("manual_ledger", ledger_file, readable=ledger["exists"]),
        ],
        "state": state,
        "events": {k: events[k] for k in ("exists", "total_lines", "bad_lines", "skipped")},
        "days": rows,
        "today_reconcile": reconcile,
        "manual_fixes": {"count": len(ledger["fixes"]), "items": ledger["fixes"], "bad_lines": ledger["bad_lines"]},
        "material_minutes": {"value": ledger["minutes"], "week": week},
        "notes": notes,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 渲染
# ═══════════════════════════════════════════════════════════════════════════
def render_md(report: dict) -> str:
    """六段 md：① 窗口与数据源 ② 日表 ③ 今日对账 ④ 人工修复 ⑤ 找材料时间 ⑥ 口径声明。"""
    w = report["window"]
    out = [
        f"# 复习完成率周报 · {w['from']} → {w['to']}",
        "",
        f"> 卡：`{report['card']}` · vault：`{report['vault']}` · 显示时区：`{report['timezone']}`",
        f"> 生成于：`{report['generated_at']}` · ISO 周：`{report['week']}`",
        "",
        "## ① 窗口与数据源",
        "",
        f"窗口 = 最近 **{w['days']}** 天（显示时区本地日），`{w['from']}` 到 `{w['to']}`。",
        f"完成率字段名 = `{COMPLETION_RATE_FIELD}`（供 G8-6 采集器消费，与本报告同源同口径）。",
        "",
        "| 角色 | 路径 | 存在 | 可读 | 行数/节点数 | sha256 |",
        "|---|---|---|---|---|---|",
    ]
    for s in report["sources"]:
        out.append(
            f"| {s['role']} | `{s['path']}` | {'是' if s['exists'] else '否'} | "
            f"{'是' if s.get('readable', s['exists']) else '否'} | "
            f"{'' if s['lines'] is None else s['lines']} | "
            f"`{(s['sha256'] or '')[:16]}` |"
        )
    for note in report["notes"]:
        out.append(f"\n> ⚠️ {note}")

    out += [
        "",
        "## ② 日表",
        "",
        "| 日期 | 到期 | 已复习 | 事件账 | 校准记录 | last_examined | 完成率 | 板级完成 | 推迟中 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in report["days"]:
        out.append(
            f"| {r['date']} | {r['due']} | {r['reviewed']} | {r['from_events']} | "
            f"{r['from_calibration']} | {r['from_last_examined']} | {r[COMPLETION_RATE_FIELD]} | "
            f"{'、'.join(r['boards_done']) or '—'} | {'、'.join(r['snoozed']) or '—'} |"
        )

    rec = report["today_reconcile"]
    out += ["", "## ③ 今日对账", ""]
    if rec["status"] == "一致":
        out.append(f"**一致**：本脚本算出今日到期 **{rec['script']}**，`今日复习.json` 也是 **{rec['snapshot']}**。")
    elif rec["status"] == "不一致":
        out.append(
            f"**不一致（{rec['script']} vs {rec['snapshot']}）**：本脚本 {rec['script']}，"
            f"`今日复习.json` {rec['snapshot']}。⚠️ 本报告**只报不改**，两边都原样保留。"
        )
        if rec.get("buckets"):
            listed = "、".join(f"`{k}`={v}" for k, v in sorted(rec["buckets"].items()) if v)
            out += [
                "",
                f"差额的去向（抄自快照自己的分桶，本报告不重算）：{listed or '（快照未给分桶）'}。",
                "",
                "> 口径差说明：本报告的「到期」按 ⑥ 段定义**涵盖 `节点/` 下全部节点**；"
                "生产端的 `due_nodes` 是在先剔掉 `ineligible`（占位符 / 测试 / 损坏）之后才数的。"
                "两个数字不等**不代表哪一边错**，但差额应当能被上面这些桶解释完；"
                "解释不完才是要追的信号。",
            ]
    elif rec["status"] == "快照非当日":
        out.append(f"**快照非当日，不对账**：`今日复习.json` 的 `date` 是 `{rec['snapshot_date']}`，不是今日。")
    else:
        out.append(f"**今日快照不可读**，无法对账（本脚本算出今日到期 {rec['script']}）。")

    mf = report["manual_fixes"]
    out += [
        "",
        "## ④ 人工修复登记",
        "",
        f"本周 **{mf['count']}** 条" + (f"（另有 {mf['bad_lines']} 行坏行已跳过）" if mf["bad_lines"] else "") + "。",
    ]
    for item in mf["items"]:
        extra = f" · 命令 `{item['cmd']}`" if item.get("cmd") else ""
        out.append(f"- `{item['ts']}` · {item['what']} · {item.get('who') or '—'}{extra}")
    if not mf["items"]:
        out.append("- （无）")

    mm = report["material_minutes"]
    out += [
        "",
        "## ⑤ 找材料时间自报",
        "",
        f"本周（`{mm['week']}`）：" + (f"**{mm['value']} 分钟**" if mm["value"] is not None else "**未自报**"),
    ]

    out += [
        "",
        "## ⑥ 口径声明",
        "",
        "- `已复习` = 三来源按节点去重的并集：事件账 `review/1` 行 / frontmatter "
        "`calibration_log[].ts` / `last_examined`；右侧三列是各来源的分别计数（会重复计同一节点）。",
        "- `到期` = `已复习` ∪ {`fsrs_due` 缺失（新卡）或形态非规范（fail-open）或 `fsrs_due` ≤ 当日末刻}。",
        f"- `{COMPLETION_RATE_FIELD}` = `已复习 / 到期`；`到期` 为 0 时记 `—`，不记 0%。",
        "- ⚠️ **frontmatter 是 current state**（D0 修订）：**回溯日的到期集是估计**，"
        "不是当天的真实到期集 —— 复习后 `fsrs_due` 前移（低估）、窗口内新建的 New 节点"
        "计入更早的日子（高估）。**只有「今日」那一行**可以与 `outputs/今日复习.json` 精确对账。",
        "- 本脚本全程只读：不写 vault、不写 state（不建 `.lock`、不隔离、不重建）、不连任何数据库。",
    ]
    return "\n".join(out) + "\n"


# ═══════════════════════════════════════════════════════════════════════════
# 登记（唯一的另一处写口）
# ═══════════════════════════════════════════════════════════════════════════
def append_ledger_line(ledger_file: Path, record: dict) -> None:
    """往登记账追加**一行** —— 单次 ``os.write``，避免半行。

    半行会被读侧算成一条坏行（而且可能把下一条正常记录也带坏），所以这里
    把「一条 JSON + 末尾 LF」编码成一个 bytes 后**一次写完**，不分两次。
    """
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    blob = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(ledger_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        written = os.write(fd, blob)
        if written != len(blob):
            raise OSError(f"登记只写进 {written}/{len(blob)} 字节 — 半行会被读侧当坏行")
    finally:
        os.close(fd)


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="review_weekly_report.py",
        description="CARD-G8-4 — 复习完成率周汇总（只读）+ 人工修复登记 / 找材料时间自报",
    )
    # ⚠️ dest 用 subcommand 不用 cmd: ``log-fix`` 有个 ``--cmd`` 参数, 两者
    # 同名时后者会把子命令名覆盖成 None, 于是分派恒落到最后一个分支。
    sub = parser.add_subparsers(dest="subcommand", required=True)

    rep = sub.add_parser("report", help="出周报（只读；--out 是唯一写口，缺省打印 stdout）")
    rep.add_argument("--vault", required=True, help="vault 目录（只读）")
    rep.add_argument("--state", default=None, help="per-vault state json（缺省按 runner.state_path 派生；只读投影）")
    rep.add_argument("--events", default=None, help="learning_events.jsonl（缺省 <vault>/learning_events.jsonl）")
    rep.add_argument("--today-json", default=None, help="今日复习.json（缺省 <vault>/outputs/今日复习.json）")
    rep.add_argument(
        "--manual-ledger", default=None, help="人工修复登记账（缺省 <vault>/outputs/review_manual_ledger.jsonl）"
    )
    rep.add_argument("--now", default=None, help="ISO 时刻；裸时间按报告时区解释")
    rep.add_argument("--days", type=int, default=7, help="窗口天数（含今日）")
    rep.add_argument("--out", default=None, help="报告 md 路径（唯一写口）；不给则打印 stdout")

    fix = sub.add_parser("log-fix", help="登记一次人工修复")
    fix.add_argument("--ledger", required=True, help="登记账 jsonl（**必填，无缺省** —— 避免顺手写进 live）")
    fix.add_argument("--what", required=True, help="一句话说清修了什么")
    fix.add_argument("--cmd", default=None, help="用到的命令（可选）")
    fix.add_argument("--who", default=None, help="谁修的（可选）")
    fix.add_argument("--now", default=None, help="ISO 时刻；裸时间按报告时区解释（缺省当前；登记账 week 由它决定）")

    mat = sub.add_parser("log-material", help="自报本周找材料花的分钟数")
    mat.add_argument("--ledger", required=True, help="登记账 jsonl（**必填，无缺省**）")
    mat.add_argument("--minutes", type=int, required=True, help="分钟数（≥0）")
    mat.add_argument("--now", default=None, help="ISO 时刻；裸时间按报告时区解释（缺省当前；登记账 week 由它决定）")
    return parser


def _run_report(args) -> int:
    global LAST_REPORT
    tz = report_timezone()
    vault = Path(args.vault)
    if not vault.is_dir():
        print(f"ERROR: --vault 不是目录: {vault}", file=sys.stderr)
        return RC_REFUSED
    if not (vault / "节点").is_dir():
        print(f"ERROR: {vault}/节点 不存在 —— 这不像一个 canvas vault。", file=sys.stderr)
        return RC_REFUSED
    if args.days < 1:
        print(f"ERROR: --days 必须 ≥ 1，实得 {args.days}", file=sys.stderr)
        return RC_REFUSED

    try:
        now = _resolve_now(args.now, tz)
    except (ValueError, OverflowError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return RC_REFUSED

    state_file = Path(args.state) if args.state else runner.state_path(vault)
    events_file = Path(args.events) if args.events else vault / "learning_events.jsonl"
    today_json = Path(args.today_json) if args.today_json else vault / "outputs" / "今日复习.json"
    ledger_file = Path(args.manual_ledger) if args.manual_ledger else vault / "outputs" / "review_manual_ledger.jsonl"

    report = build_report(
        vault,
        state_file=state_file,
        events_file=events_file,
        today_json=today_json,
        ledger_file=ledger_file,
        now=now,
        days=args.days,
        tz=tz,
    )
    LAST_REPORT = report
    text = render_md(report)

    if args.out:
        out_path = Path(args.out)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: --out 写不了 {out_path}: {exc}", file=sys.stderr)
            return RC_REFUSED
        print(f"周报已写: {out_path}")
    else:
        print(text, end="")
    return RC_OK


def _run_log_fix(args) -> int:
    # H-1 整改（ZCode 补审 r2 / 主 session 裁「整改」）：登记侧时钟**可注入**，
    # 与 report 的 --now 同语义。旧实现用真实时钟落 week，而测试读账用注入时钟，
    # 两钟一旦跨周（2026-09-21 起）账行被周过滤整行滤掉 —— 时间炸弹。
    tz = report_timezone()
    try:
        now = _resolve_now(args.now, tz)
    except (ValueError, OverflowError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return RC_REFUSED
    record = {
        "kind": "manual_fix",
        "ts": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "week": iso_week(now.astimezone(tz)),
        "what": args.what,
        "who": args.who,
    }
    if args.cmd:
        record["cmd"] = args.cmd
    try:
        append_ledger_line(Path(args.ledger), record)
    except OSError as exc:
        print(f"ERROR: 登记写不进 {args.ledger}: {exc}", file=sys.stderr)
        return RC_REFUSED
    print(f"已登记人工修复: {record['ts']} · {args.what}")
    return RC_OK


def _run_log_material(args) -> int:
    if args.minutes < 0:
        print(f"ERROR: --minutes 必须 ≥ 0，实得 {args.minutes}", file=sys.stderr)
        return RC_REFUSED
    # 与 _run_log_fix 同：登记侧时钟可注入（H-1 整改），缺省当前时刻。
    tz = report_timezone()
    try:
        now = _resolve_now(args.now, tz)
    except (ValueError, OverflowError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return RC_REFUSED
    record = {
        "kind": "material_minutes",
        "ts": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "week": iso_week(now.astimezone(tz)),
        "minutes": args.minutes,
        "who": None,
    }
    try:
        append_ledger_line(Path(args.ledger), record)
    except OSError as exc:
        print(f"ERROR: 登记写不进 {args.ledger}: {exc}", file=sys.stderr)
        return RC_REFUSED
    print(f"已自报找材料时间: {args.minutes} 分钟（{record['week']}）")
    return RC_OK


def main(argv: list | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.subcommand == "report":
        return _run_report(args)
    if args.subcommand == "log-fix":
        return _run_log_fix(args)
    return _run_log_material(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
