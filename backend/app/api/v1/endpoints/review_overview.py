"""跨 vault 复习总览 (CARD-C2, BATCH-2026-08-25-跨vault与收束; D3 方案 B 预演)。

GET /api/v1/review/overview       — JSON 聚合各 vault outputs/今日复习.json
GET /api/v1/review/overview/page  — 内联 HTML 总览页 (零外部 CDN / 纯内联样式)

只读展示: 本端点是 A2 投影 (schema v3) 的纯消费方 — 不重算到期口径、不写
任何文件。诚实四态: ok / stale / no_projection / corrupt 显式区分 — 缺投影
与损坏 JSON 都以降级条目出现在列表里, 禁静默跳过、禁 500 (单库坏账不拖垮
总览)。stale 判定只看投影自带 generated_at (本地日 != 今天), 不看文件 mtime
(mtime 被 runner 刻意回拨到扫描起点, 见 daily_review_run.ensure_payload)。
"""

from __future__ import annotations

import html
import json
import math
import re
from datetime import date, datetime
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
    top = top_boards[0] if top_boards else {}
    if not isinstance(top, dict):
        raise ValueError("top_boards 元素应为 object")
    raw_up = upcoming[0] if upcoming else None
    if raw_up is not None and not isinstance(raw_up, dict):
        raise ValueError("upcoming 元素应为 object")
    # 不透传整对象 (round3: 内部字段未验的 dict 原样进响应仍是形状垃圾
    # 通道) — 只提取消费方要的三个字段并逐一门禁
    next_up = None
    if raw_up is not None:
        next_up = {
            "board": _opt_str(raw_up.get("board"), "upcoming[0].board"),
            "next_due": _opt_str(raw_up.get("next_due"), "upcoming[0].next_due"),
            "node": _opt_str(raw_up.get("node"), "upcoming[0].node"),
        }
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
            stale = gen.astimezone().date() != today
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
    now = datetime.now().astimezone()
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


def _card_html(entry: dict) -> str:
    vid = html.escape(entry["vault_id"])
    label, color = _STATUS_META[entry["status"]]
    obsidian_url = html.escape("obsidian://open?vault=" + quote(entry["vault_id"], safe=""))
    proj = entry.get("projection")
    if proj:
        board = html.escape(str(proj.get("recommended_board") or "—"))
        gen = html.escape(str(proj.get("generated_at") or "—"))
        body = (
            f'<div style="font-size:28px;margin:8px 0">'
            f"到期 <b>{int(proj['due_count'])}</b>"
            f'<span style="font-size:14px;color:#6b7280"> · 待剖析积压 '
            f"{int(proj['placeholder_backlog'])}</span></div>"
            f'<div style="margin:4px 0">推荐白板: <b>{board}</b></div>'
            f'<div style="color:#6b7280;font-size:12px">生成于 {gen}</div>'
        )
    elif entry["status"] == "no_projection":
        body = '<div style="color:#6b7280;margin:12px 0">该库尚无今日复习投影 — 推送管道尚未为它跑过</div>'
    else:
        err = html.escape(str(entry.get("error") or ""))
        body = (
            f'<div style="color:#dc2626;margin:12px 0">投影文件无法解析'
            f'<br><code style="font-size:11px">{err}</code></div>'
        )
    return (
        f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px 20px;'
        f"min-width:260px;max-width:340px;background:#fff;"
        f'box-shadow:0 1px 3px rgba(0,0,0,.06)">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<b style="font-size:16px">{vid}</b>'
        f'<span style="background:{color};color:#fff;border-radius:999px;'
        f'padding:2px 10px;font-size:12px">{label}</span></div>'
        f"{body}"
        f'<a href="{obsidian_url}" style="font-size:13px;color:#2563eb;'
        f'text-decoration:none">在 Obsidian 中打开 ↗</a>'
        f"</div>"
    )


@review_overview_router.get(
    "/overview/page",
    response_class=HTMLResponse,
    summary="跨 vault 复习总览页 (内联 HTML, 零外部 CDN)",
)
async def review_overview_page() -> HTMLResponse:
    data = _collect()
    cards = "".join(_card_html(e) for e in data["vaults"]) or (
        '<div style="color:#6b7280">VAULTS_ROOT 下未发现任何 vault (需含 .obsidian/ 目录)</div>'
    )
    generated = html.escape(data["generated_at"])
    page = (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>跨库复习总览</title></head>"
        '<body style="font-family:-apple-system,BlinkMacSystemFont,'
        "'PingFang SC','Helvetica Neue',sans-serif;background:#f5f5f7;"
        'margin:0;padding:32px">'
        '<h1 style="font-size:22px;margin:0 0 4px">📚 跨库复习总览</h1>'
        f'<div style="color:#6b7280;font-size:13px;margin-bottom:20px">'
        f"页面生成于 {generated} · 只读聚合, 数据来自各库 outputs/今日复习.json</div>"
        f'<div style="display:flex;flex-wrap:wrap;gap:16px">{cards}</div>'
        "</body></html>"
    )
    return HTMLResponse(content=page)
