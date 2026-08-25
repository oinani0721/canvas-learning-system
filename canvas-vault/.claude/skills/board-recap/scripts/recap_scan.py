#!/usr/bin/env python3
"""board-recap 确定性收集器 (CARD-C5 薄版, BATCH-2026-08-25-跨vault与收束).

职责边界 (与 SKILL.md 的分工):
  本脚本负责一切**可确定性计算**的数据面 — manifest JSON 解析、种子/派生
  分流台账 (含每种子的派生子女数、每节点 tips/未闭环计数)、tips 未答计数
  与最老 3 条、source revision (板 SHA-256 + 板文件 mtime + manifest
  freshness)、上次回顾「你现在可以做的」段与用户自评行抽取 (供闭环 diff)、
  规模门计数 (超线时附 detail_node_ids 与尾部聚合)、幂等检测。
  LLM 只做三维审查叙述与白名单动作句 — 报告中的每个数字与清单必须逐项
  对应本脚本输出的字段, 不得回读 manifest/文件自行统计。

硬约束 (Codex CARD-C5 审查两轮 B1/B2/H3/H4/H5/M8/M9 修复后):
  - **零写侧**: 本脚本只读文件, 不写任何文件 (含 /tmp)。manifest 由 skill
    用 Write 落到 ``outputs/.recap-manifest-<board>.json`` (outputs/ 是 skill
    声明的唯一写面, 该文件兼作审计快照) 后以路径传入; ``--manifest -``
    stdin 通道保留给非 shell 调用方 (shell heredoc 会落 mkstemp 临时文件,
    不作为 SKILL 主路径)。
  - **路径 containment**: --board 与成员名拒绝路径分隔符/父目录引用/shell
    元字符(` $ ' "), 且最终路径必须 resolve 在 vault 对应目录内 — 越界一律
    按不存在处理; 原白板/节点/outputs 三目录若整体 symlink 到 vault 外则
    直接判环境不可用 (exit 2)。
  - **manifest fail-closed**: 解包后必须 board_id 与 --board 精确一致、
    source_status ∈ {ok, snapshot}、nodes 非空且形状合法; 任一不满足 →
    fallback_local 并给出 unusable_reason (报告头如实声明)。
  - 纯 stdlib, 输出单个 JSON 对象到 stdout。
  - 退出码: 0 = 正常 (board 不存在/板名非法也是 0 — 拒绝是 skill 的决策,
    数据里有 board_exists=false 与原因); 2 = 环境不可用。

数据模式 (data_mode):
  - "manifest": stdin/文件提供了通过全部 fail-closed 校验的 manifest。
    snapshot/degraded 原样透传进 source_revision, 报告头必须诚实声明。
  - "fallback_local": 其余一切情况。本地只读扫描: 成员**只取白板
    ``## Concepts`` 小节内的链接** (与后端 canonical 成员判定同窄度,
    防把正文示例/Recent Activity 历史链接误收为成员); 节点侧
    frontmatter 正则抽取 (含 ``text: |-`` block scalar)。此模式下
    role/is_stub/mastery 均为**本地推定**, 报告头必须声明 FALLBACK。

口径脚注:
  - annotations = frontmatter tips 计数 (两种模式同口径, 规模门共用)。
    正文 callout 计数单独给出 (body_callouts), **不参与规模门** — 镜像
    callout 与 frontmatter tips 重复、模板 [!info] 属噪声, 相加必虚高。
  - tips added_at = 最后一次内容变更时间, 非首次批注时间 → 时序结论只可
    标【文件】档。无法解析的时间戳不参与"最老"排序 (tips_undated 计数)。
  - 学习 vault 无「已答」标记 → 未答数 = 全部 tips 计数, 报告只可标
    【未确认-无法判定已答】, 不得宣称「没人答」。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MEMBER_THRESHOLD = 30  # 规模门: 成员数 (设计稿 v2 §七)
ANNOTATION_THRESHOLD = 100  # 规模门: 批注数 (frontmatter tips 口径)
DETAIL_K = 10  # 超线时详审的 pick_rank 前 K
STUB_PLACEHOLDER = "你的 1-2 句精准定义"

_FM_RE = re.compile(r"^﻿?---\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)$", re.S)
_CONCEPT_LINK_RE = re.compile(r"\[\[节点/([^\]|#]+?)(?:\|[^\]]*)?\]\]")
# 成员窄扫: 只认 ## Concepts 小节 (对齐 board_manifest_service 的 canonical 判定)
_CONCEPTS_SECTION_RE = re.compile(r"^## Concepts\s*$(.*?)(?=^## |\Z)", re.M | re.S)
# 批注扫描铁律 (设计稿 §三): 全文匹配并集正则, 不做行首锚定 (四代格式漂移)
_CALLOUT_RE = re.compile(r"\[!(question|error|tip|tips|note|key)\]", re.I)
_USER_INLINE_RE = re.compile(r"\*\*User[：:][^*]+\*\*")
_SELFEVAL_LINE_RE = re.compile(r"^（你说过：.*）\s*$", re.M)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _oneline(text: str, limit: int = 200) -> str:
    """折叠空白/换行 — 防 tips 原话用换行+## 伪造报告结构 (M9)。"""
    return " ".join(str(text).split())[:limit]


def _parse_dt(value) -> datetime | None:
    """ISO 时间戳 → tz-aware datetime; 解析失败 → None (不参与排序)。"""
    try:
        d = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _contained_md(base: Path, name: str) -> Path | None:
    """路径 containment (B2): name 必须是纯文件名 stem, 解析后仍在 base 内。

    含 / \\ 或 .. 组件、以 . 开头、resolve 后逃出 base → None (按不存在/
    非法处理, 越界读一律拒绝)。
    """
    if not name or name.startswith("."):
        return None
    if "/" in name or "\\" in name or "\x00" in name:
        return None
    if name in ("..", "."):
        return None
    # shell 元字符与控制字符 (B2 补): 板名/节点名会出现在 Bash 单引号参数里,
    # 单引号本身会破坏引用; ` $ " 与控制字符没有任何合法板名需要 → 一律拒绝。
    if any(c in "`$'\"" or ord(c) < 32 for c in name):
        return None
    candidate = base / f"{name}.md"
    try:
        if not candidate.resolve().is_relative_to(base.resolve()):
            return None
    except (OSError, ValueError):
        return None
    return candidate


def _frontmatter_and_body(text: str) -> tuple[str, str]:
    m = _FM_RE.match(text)
    return (m.group(1), m.group(2)) if m else ("", text)


def _fm_scalar(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}\s*:\s*(.+?)\s*$", fm, re.M)
    if not m:
        return None
    return m.group(1).strip().strip("\"'") or None


_TIPS_BLOCK_RE = re.compile(r"^tips:\s*$(.*?)(?=^\S|\Z)", re.M | re.S)
_TIP_FIELD_RE = re.compile(r"^(\s*)(text|tag|understanding|added_at)\s*:\s*(.*)$")
_BLOCK_SCALAR_MARKERS = ("|", "|-", "|+", ">", ">-", ">+")


def _parse_tips_from_frontmatter(fm: str) -> list[dict]:
    """无 yaml 库解析 tips 列表 (text/tag/understanding/added_at 四字段)。

    行级状态机 (H4 二轮修复 — 正则 chunk 法会把 text 块标量吞掉后续字段,
    且块内嵌套 "- bullet" 会被误切成新条目):
      - 条目切分只认**首个条目的缩进层**上的 "- " 行 — 更深缩进的 "- "
        (如块标量正文里的列表) 归属当前条目正文。
      - ``text: |-`` 等块标量: 收集**缩进 > text 键缩进**的后续行 (含空行),
        遇到缩进 ≤ 键缩进的行终止 — tag/understanding 等同层字段不再被吞。
    解析失败的条目静默跳过 (单条损坏不拖垮全板, 与 parse_errors 同语义)。
    """
    m = _TIPS_BLOCK_RE.search(fm)
    if not m:
        return []
    lines = m.group(1).splitlines()
    # 1) 条目切分: 锁定第一条 "- " 的缩进为条目层
    entry_indent: int | None = None
    entries: list[list[str]] = []
    for line in lines:
        dm = re.match(r"^(\s*)-\s(.*)$", line)
        if dm and (entry_indent is None or len(dm.group(1)) == entry_indent):
            if entry_indent is None:
                entry_indent = len(dm.group(1))
            entries.append([" " * (entry_indent + 2) + dm.group(2)])
        elif entries:
            entries[-1].append(line)
    # 2) 逐条目按行解析字段
    tips: list[dict] = []
    for elines in entries:
        entry: dict = {}
        i = 0
        while i < len(elines):
            fmatch = _TIP_FIELD_RE.match(elines[i])
            if not fmatch:
                i += 1
                continue
            key_indent, key, value = (
                len(fmatch.group(1)),
                fmatch.group(2),
                fmatch.group(3).strip(),
            )
            if key == "text" and value in _BLOCK_SCALAR_MARKERS:
                block: list[str] = []
                j = i + 1
                while j < len(elines):
                    nxt = elines[j]
                    if nxt.strip() == "" or (len(nxt) - len(nxt.lstrip())) > key_indent:
                        block.append(nxt)
                        j += 1
                    else:
                        break
                entry["text"] = _oneline("\n".join(block))
                i = j
                continue
            entry[key] = _oneline(value.strip("\"'"), 200 if key == "text" else 80)
            i += 1
        if entry:
            tips.append(entry)
    return tips


def _iso_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_manifest(source: str, board_stem: str) -> tuple[dict | None, str | None]:
    """→ (manifest dict | None, 不可用原因 | None)。fail-closed (B1)。

    source = "-" 读 stdin (SKILL 主路径, 零临时文件), 否则按文件路径读。
    """
    try:
        if source == "-":
            raw = sys.stdin.read()
        else:
            p = Path(source)
            if not p.is_file():
                return None, f"manifest 文件不存在: {source}"
            raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        return None, f"manifest 读取/解析失败: {type(e).__name__}"
    # MCP 工具返回体是 {ok, error, manifest} 包裹 (实测 2026-08-25);
    # HTTP 端点返回裸 manifest。两种形状都接受。
    if isinstance(data, dict) and isinstance(data.get("manifest"), dict):
        if data.get("ok") is False:
            return None, f"manifest 工具报错: {_oneline(data.get('error'), 120)}"
        data = data["manifest"]
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), list):
        return None, "manifest 缺 nodes 列表 (非 get_board_manifest 返回体)"
    if data.get("source_status") not in ("ok", "snapshot"):
        return (
            None,
            f"manifest source_status={data.get('source_status')!r} 不可信 (只接受 ok/snapshot)",
        )
    if not data["nodes"]:
        return None, "manifest nodes 为空 (无结构数据可用)"
    # M8 二轮: 逐节点形状校验 — 非 dict / 缺 node_id 的条目不许被静默跳过
    # 后仍冒充 "manifest 实测" (nodes:[7] 反例), 整包降级。
    for n in data["nodes"]:
        if (
            not isinstance(n, dict)
            or not isinstance(n.get("node_id"), str)
            or not n["node_id"]
        ):
            return None, "manifest nodes 形状损坏 (存在非对象或缺 node_id 的条目)"
    board = data.get("board")
    mid = board.get("board_id") if isinstance(board, dict) else None
    if mid != board_stem:
        # 跨 vault / 跨板 / 并发串料防御: 头身必须同板 (B1)
        return None, f"manifest 板名不匹配: {_oneline(mid, 60)!r} ≠ {board_stem!r}"
    return data, None


def _row_tips(raw_tips) -> list[dict]:
    # M9 三轮: 每个字符串字段都过 _oneline — 不可信数据没有"看起来像枚举
    # 就不用净化"的豁免 (tag/understanding/added_at 同样可被写侧投毒换行)。
    out = []
    for t in raw_tips or []:
        if isinstance(t, dict):
            out.append(
                {
                    "text": _oneline(t.get("text", "")),
                    "tag": _oneline(t.get("tag") or "", 40) or None,
                    "understanding": _oneline(t.get("understanding") or "", 40) or None,
                    "added_at": _oneline(t.get("added_at") or "", 64) or None,
                }
            )
    return out


def _finite(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _int_or_none(v) -> int | None:
    """pick_rank 等秩字段强制 int 化 — 混入字符串秩不许炸掉排序 (M8 二轮)。"""
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _relation_type_counts(ledger: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in ledger:
        t = r.get("relation_type")
        if t:
            out[t] = out.get(t, 0) + 1
    return out


def _sanitize_gap(gap) -> dict | None:
    """dual_source_gap 净化透传 (M9 三轮)。"""
    if not isinstance(gap, dict):
        return None
    return {
        "concepts_only": [
            {
                "node_id": _oneline(e.get("node_id") or "", 120),
                "exists": bool(e.get("exists")),
            }
            for e in (gap.get("concepts_only") or [])
            if isinstance(e, dict)
        ],
        "frontmatter_only": [
            _oneline(x, 120)
            for x in (gap.get("frontmatter_only") or [])
            if isinstance(x, str)
        ],
    }


def _ledger_from_manifest(manifest: dict) -> list[dict]:
    rows = []
    for n in manifest["nodes"]:
        if not isinstance(n, dict):
            continue
        mastery = n.get("mastery") if isinstance(n.get("mastery"), dict) else {}
        pick = n.get("pick_hint") if isinstance(n.get("pick_hint"), dict) else {}
        rel = n.get("relation") if isinstance(n.get("relation"), dict) else {}
        tips = _row_tips(n.get("tips"))
        rows.append(
            {
                "node_id": _oneline(n["node_id"], 120),
                "role": n.get("role", "unknown"),
                "role_source": "manifest",
                "is_stub": bool(n.get("is_stub")),
                "mastery_score": _finite(mastery.get("score")),
                "mastery_source": _oneline(mastery.get("source") or "", 40) or None,
                "attempt_count": _int_or_none(n.get("attempt_count")),
                "last_examined": _oneline(n.get("last_examined") or "", 64) or None,
                "created_at": _oneline(n.get("created_at") or "", 64) or None,
                "created_from": _oneline(n.get("created_from") or "", 80) or None,
                "pick_rank": _int_or_none(pick.get("pick_rank")),
                "relation_type": _oneline(rel.get("type") or "", 40) or None,
                "relation_target": _oneline(rel.get("target_node_id") or "", 120)
                or None,
                "derived_at": _oneline(rel.get("derived_at") or "", 64) or None,
                "derived_reason": _oneline(rel.get("derived_reason") or "", 200)
                or None,
                "tips": tips,
                "tips_count": len(tips),
                "tips_open": sum(
                    1 for t in tips if t.get("understanding") != "understood"
                ),
                "error_candidates_pending": sum(
                    1
                    for ec in (n.get("error_candidates") or [])
                    if isinstance(ec, dict) and ec.get("status") == "pending"
                ),
            }
        )
    return rows


def _ledger_from_local(vault: Path, members: list[str]) -> list[dict]:
    node_dir = vault / "节点"
    rows = []
    for name in members:
        node_path = _contained_md(node_dir, name)
        if node_path is None:
            rows.append(
                {
                    "node_id": name,
                    "role": "unknown",
                    "role_source": "invalid_name",
                    "exists": False,
                    "tips": [],
                    "tips_count": 0,
                    "tips_open": 0,
                }
            )
            continue
        if not node_path.is_file():
            rows.append(
                {
                    "node_id": name,
                    "role": "unknown",
                    "role_source": "local_missing",
                    "exists": False,
                    "tips": [],
                    "tips_count": 0,
                    "tips_open": 0,
                }
            )
            continue
        try:
            fm, body = _frontmatter_and_body(_read(node_path))
        except (OSError, UnicodeDecodeError):
            rows.append(
                {
                    "node_id": name,
                    "role": "unknown",
                    "role_source": "local_unreadable",
                    "exists": False,
                    "tips": [],
                    "tips_count": 0,
                    "tips_open": 0,
                }
            )
            continue
        mastery = None
        for key in ("mastery_score", "mastery", "mastery_level"):
            v = _fm_scalar(fm, key)
            if v is not None:
                mastery = _finite(v)
                break
        tips = _row_tips(_parse_tips_from_frontmatter(fm))
        rows.append(
            {
                "node_id": name,
                # 种子 = 无 derived-from (设计稿 §四); 本地推定, 报告标【推定】
                "role": "derived" if "derived-from" in fm else "seed",
                "role_source": "local_inferred",
                "is_stub": STUB_PLACEHOLDER in body,
                "mastery_score": mastery,
                "mastery_source": "local_frontmatter"
                if mastery is not None
                else "absent",
                "attempt_count": _fm_scalar(fm, "attempt_count"),
                "last_examined": _fm_scalar(fm, "last_examined"),
                "created_at": None,
                "created_from": _fm_scalar(fm, "created_from"),
                "pick_rank": None,
                "relation_type": None,
                "relation_target": None,
                "derived_at": None,
                "derived_reason": None,
                "tips": tips,
                "tips_count": len(tips),
                "tips_open": sum(
                    1 for t in tips if t.get("understanding") != "understood"
                ),
                "error_candidates_pending": 0,
                "body_callout_count": len(_CALLOUT_RE.findall(body))
                + len(_USER_INLINE_RE.findall(body)),
            }
        )
    return rows


def _previous_recap(outputs: Path, board_stem: str, today: str) -> dict | None:
    """最新一份**不晚于 today** 的本板回顾 (M8: 未来/非法日期不参选)。"""
    if not outputs.is_dir():
        return None
    pattern = re.compile(
        rf"^回顾-{re.escape(board_stem)}-(\d{{4}}-\d{{2}}-\d{{2}})\.md$"
    )
    candidates = []
    outputs_resolved = outputs.resolve()
    for p in outputs.iterdir():
        m = pattern.match(p.name)
        if not m:
            continue
        date = m.group(1)
        if _parse_dt(date) is None or date > today:
            continue
        # B2 二轮: 文件级 symlink 越界候选不参选 (跨 vault 读 previous recap)
        try:
            if not p.resolve().is_relative_to(outputs_resolved):
                continue
        except (OSError, ValueError):
            continue
        candidates.append((date, p))
    if not candidates:
        return None
    date, path = max(candidates)  # 合法 YYYY-MM-DD 字典序 = 时间序
    try:
        text = _read(path)
    except (OSError, UnicodeDecodeError):
        return {
            "path": str(path),
            "date": date,
            "same_day": date == today,
            "actions_section": None,
            "selfevals": [],
        }
    m = re.search(r"^## 你现在可以做的\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return {
        "path": str(path),
        "date": date,
        "same_day": date == today,
        "actions_section": m.group(1).strip()[:2000] if m else None,
        # Step 6 标准格式「（你说过：…）」的历史自评行, 供本次报告引用
        "selfevals": [_oneline(s, 300) for s in _SELFEVAL_LINE_RE.findall(text)][-3:],
    }


_VERIFY_SECTIONS = (
    "## 数据来源与新鲜度",
    "## 本段新增",
    "## 你现在可以做的",
    "## 台账",
    "## AI 侧对账",
    "## 三维审查",
)
_VERIFY_GLOBAL_FORBIDDEN = ("偏离", "你以为", "其实你", "你理解错", "但资料说")
_VERIFY_S3_FORBIDDEN = ("你当时", "你当初", "你选择", "你决定")
_VERIFY_PLACEHOLDERS = ("<X>", "<板名>", "<节点名>", "<node", "PENDING")
_VERIFY_BLAME = ("docker", "启动服务", "请先启动", "终端", "命令行")
_VERIFY_FALLBACK_DERIVE = (
    "已派生",
    "未派生",
    "从未派生",
    "派生出",
    "没有派生",
    "子节点",
)
_VERIFY_ACTION_VERBS = (
    "/node-chat",
    "/start-exam-board",
    "/board-recap",
    "Cmd+Shift+D",
    "Cmd+Shift+A",
    "Dashboard",
)


def _verify_numbers(fm: str, text: str, report_path: Path, problems: list[str]) -> None:
    """H5 数字绑定 (四轮+六轮): 报告核心计数必须与同目录 scan JSON 快照全等。

    scan JSON = 报告同目录 ``.recap-scan-<board>.json`` (SKILL Step 2 落盘)。
    缺失 = 无法终核 → fail-closed 直接 FAIL; 存在则绑定:
    board_sha256 / data_mode / recap_date / 规模自陈五元组 / AI 侧对账 tips 两数。
    六轮影子字段防御: frontmatter 键只在真 frontmatter 块 (fm) 里认 —
    把三行搬进正文冒充不算数; text 已在上游剥掉 HTML 注释。
    """
    mb = re.search(r'^board:\s*"?([^"\n]+)"?\s*$', fm, re.M)
    if not mb:
        problems.append("frontmatter 缺 board 字段 (数字终核无法定位 scan JSON)")
        return
    scan_path = report_path.parent / f".recap-scan-{mb.group(1).strip()}.json"
    try:
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        problems.append(
            f"数字终核 fail-closed: scan JSON 缺失或损坏 ({scan_path.name})"
        )
        return
    for key, pat in (
        ("board_sha256", r'^board_sha256:\s*"?([0-9a-f]{64})"?'),
        ("data_mode", r"^data_mode:\s*(\S+)"),
        ("recap_date", r"^recap_date:\s*(\S+)"),
    ):
        mm = re.search(pat, fm, re.M)
        want = (
            scan.get(key)
            if key != "board_sha256"
            else (scan.get("source_revision") or {}).get("board_sha256")
        )
        if not mm or str(mm.group(1)) != str(want):
            problems.append(f"数字终核: frontmatter {key} 与 scan JSON 不一致")
    counts = scan.get("counts") or {}
    mscale = re.search(
        r"(\d+)\s*成员（(\d+)\s*种子\s*\+\s*(\d+)\s*派生，(\d+)\s*占位）/\s*(\d+)\s*批注",
        text,
    )
    if not mscale:
        problems.append("规模自陈行未按模板格式给出五元组 (成员/种子/派生/占位/批注)")
    else:
        got = tuple(int(x) for x in mscale.groups())
        want = tuple(
            counts.get(k, -1)
            for k in ("members", "seeds", "derived", "stubs", "annotations")
        )
        if got != want:
            problems.append(f"数字终核: 规模自陈 {got} ≠ scan JSON {want}")
    # tips 两数只在「AI 侧对账」段绑定 — 台账里逐节点的 "tips 未闭环 n 条"
    # 是行级数字, 与全局计数不同, 不参与本绑定 (全文搜索会误命中)。
    recon = re.search(r"^## AI 侧对账\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not recon:
        return  # 段落缺失由段落检查报, 不重复报
    # 两行均为必需 (五轮 H5 残余: 缺行不许静默豁免 — 改写成非模板措辞
    # 即逃逸绑定, 必须 fail-closed)。
    mtips = re.search(r"tips 批注共\s*(\d+)\s*条", recon.group(1))
    if not mtips:
        problems.append("数字终核: AI 侧对账缺『tips 批注共 N 条』标准计数行")
    elif int(mtips.group(1)) != counts.get("tips_total", -1):
        problems.append(
            f"数字终核: tips 总数 {mtips.group(1)} ≠ scan JSON {counts.get('tips_total')}"
        )
    mopen = re.search(r"其中理解度未闭环\s*(\d+)\s*条", recon.group(1))
    if not mopen:
        problems.append("数字终核: AI 侧对账缺『其中理解度未闭环 N 条』标准计数行")
    elif int(mopen.group(1)) != counts.get("tips_understanding_open", -1):
        problems.append(
            f"数字终核: tips 未闭环 {mopen.group(1)} ≠ scan JSON {counts.get('tips_understanding_open')}"
        )


def _verify_report(path: str) -> int:
    """Step 5.5 机械自检 (确定性 verifier — LLM 自检不可靠, 命令输出才算数)。

    ✗ 任一条 → exit 1, skill 必须改写报告重跑本命令; 全 ✓ → exit 0 才许发回执。
    """
    try:
        text_raw = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"✗ 报告不可读: {type(e).__name__}")
        return 1
    # 八轮顺序修正: 栅栏在**原始文本**上判定 — 先剥注释会把
    # "---<!--x-->" 这类非法闭合行洗成合法 "---" (清洗旁路)。
    # 闭合栅栏必须是整行 --- (行尾至多空白, 七轮), 无合法闭合 = 缺块。
    fm_m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text_raw, re.S)
    if not fm_m:
        print("✗ 报告缺 frontmatter 块")
        return 1
    fm = fm_m.group(1)
    # frontmatter 块内禁 HTML 注释标记 — 注释跨栅栏/贴栅栏正是清洗旁路的
    # 载体, 合法报告的 frontmatter 里没有任何理由出现它。
    if "<!--" in fm or "-->" in fm:
        print("✗ frontmatter 块内含 HTML 注释标记")
        return 1
    # 六轮影子字段防御: 正文校验前剥 HTML 注释 — "注释里藏正确模板行、
    # 可见文本撒谎"的形态失效, 可见文本必须独立过全部校验。
    text = re.sub(r"<!--.*?-->", "", text_raw, flags=re.S)
    problems: list[str] = []
    _verify_numbers(fm, text, Path(path), problems)
    if not re.search(r"^type:\s*recap\s*$", fm, re.M):
        problems.append("frontmatter 缺 type: recap")
    if "规模自陈" not in text:
        problems.append("缺 规模自陈 callout")
    # 六轮防御③: 必需段落唯一 — 重复段(第一段合规第二段夹私货)不放行
    for s in _VERIFY_SECTIONS:
        n = len(re.findall(rf"^{re.escape(s)}", text, re.M))
        if n == 0:
            problems.append(f"缺段落 {s}")
        elif n > 1:
            problems.append(f"段落重复 {n} 次(只许一个): {s}")
    msha = re.search(r'^board_sha256:\s*"?([0-9a-f]+)"?', fm, re.M)
    if not msha or len(msha.group(1)) != 64:
        problems.append("board_sha256 必须完整 64 hex (在 frontmatter 内)")
    for w in _VERIFY_GLOBAL_FORBIDDEN:
        if w in text:
            problems.append(f"HARD-R4 禁词命中: {w}")
    for w in _VERIFY_PLACEHOLDERS:
        if w in text:
            problems.append(f"占位符残留: {w}")
    for w in _VERIFY_BLAME:
        if w in text:
            problems.append(f"白名单外动作/甩锅词: {w}")
    s3_all = re.findall(r"^### ③.*?(?=^### |\Z)", text, re.M | re.S)
    if not s3_all:
        problems.append("缺 ### ③ 方向段")
    for s3 in s3_all:  # 逐个检查 — 重复③段同样全查
        for w in _VERIFY_S3_FORBIDDEN:
            if w in s3:
                problems.append(f"③段用户主语: {w}")
    is_fallback = bool(re.search(r"^data_mode:\s*fallback_local", fm, re.M))
    if is_fallback:
        if "FALLBACK" not in text:
            problems.append("fallback 报告缺 FALLBACK 声明")
        for w in _VERIFY_FALLBACK_DERIVE:
            if w in text:
                problems.append(f"fallback 派生断言(无据不得断言): {w}")
    elif not re.search(r"^data_mode:\s*manifest", fm, re.M):
        problems.append("frontmatter 缺 data_mode: manifest|fallback_local")
    acts = re.search(r"^## 你现在可以做的\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if acts:
        # 续行止于空行 (五轮 M7 逃逸: 贪婪续行会把空行后的散文吸进编号项,
        # 让越界正文搭编号项的白名单便车)
        items = re.findall(
            r"^\d+\.\s.*(?:\n(?!\d+\.\s|##|\s*$).*)*", acts.group(1), re.M
        )
        if not items:
            problems.append("「你现在可以做的」没有编号动作项")
        for it in items:
            if not any(v in it for v in _VERIFY_ACTION_VERBS):
                problems.append(
                    f"动作项缺白名单动词(无动作的信号移去 AI 侧对账): {it.strip()[:40]}"
                )
        # M7 五轮: 结构性拦截 — 动作段只许编号项, 任何编号项之外的正文行
        # (无论措辞, 同义改写也一样) 都是越界内容, 词表补丁竞赛到此为止。
        leftover = acts.group(1)
        for it in items:
            leftover = leftover.replace(it, "")
        stray = [ln.strip() for ln in leftover.splitlines() if ln.strip()]
        if stray:
            problems.append(
                f"动作段含编号项之外的正文行(移去对应段落): {stray[0][:40]}"
            )
    for p in problems:
        print(f"✗ {p}")
    if problems:
        print(f"VERIFY FAIL ({len(problems)} 项) — 改写报告后重跑本命令")
        return 1
    print("VERIFY PASS — 可以发回执")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="board-recap 确定性收集器 + 报告 verifier (只读, 输出 JSON / 校验行)"
    )
    ap.add_argument("--vault", help="vault 根目录绝对路径 (收集模式必填)")
    ap.add_argument(
        "--board", help="原白板文件名 stem (非显示名; 禁路径分隔符; 收集模式必填)"
    )
    ap.add_argument(
        "--manifest",
        default=None,
        help="get_board_manifest 返回体: '-' 从 stdin 读, 或 JSON 文件路径; 缺省 = fallback 本地扫描",
    )
    ap.add_argument(
        "--date",
        default=None,
        help="回顾日期 YYYY-MM-DD (缺省 = 本机今日), 用于幂等检测与报告文件名",
    )
    ap.add_argument(
        "--verify",
        default=None,
        metavar="REPORT_MD",
        help="Step 5.5 机械自检: 校验已写好的报告, 全过 exit 0; 与收集模式互斥",
    )
    args = ap.parse_args()

    if args.verify:
        return _verify_report(args.verify)
    if not args.vault or not args.board:
        ap.error("收集模式需要 --vault 与 --board (或改用 --verify <report.md>)")

    vault = Path(args.vault)
    board_dir = vault / "原白板"
    if not board_dir.is_dir():
        print(
            json.dumps(
                {"error": f"vault 不可用: {board_dir} 不存在"}, ensure_ascii=False
            )
        )
        return 2
    # B2 二轮: 目录级 symlink 守卫 — 原白板/节点/outputs 任一被换成指向
    # vault 外 (如 sibling vault) 的目录 symlink, 一切 containment 都会被
    # 架空 → 环境不可用, 拒绝扫描。
    vault_resolved = vault.resolve()
    for sub in ("原白板", "节点", "outputs"):
        d = vault / sub
        if not d.exists():
            continue
        try:
            escaped = not d.resolve().is_relative_to(vault_resolved)
        except (OSError, ValueError):
            escaped = True
        if escaped:
            print(
                json.dumps(
                    {
                        "error": f"vault 不可用: {sub}/ 目录 resolve 到 vault 之外 (symlink 越界)"
                    },
                    ensure_ascii=False,
                )
            )
            return 2

    today = args.date or datetime.now().strftime("%Y-%m-%d")
    if not _DATE_RE.match(today) or _parse_dt(today) is None:
        print(
            json.dumps(
                {"error": f"--date 非法: {today!r} (须为 YYYY-MM-DD)"},
                ensure_ascii=False,
            )
        )
        return 2

    board_path = _contained_md(board_dir, args.board)
    if board_path is None or not board_path.is_file():
        print(
            json.dumps(
                {
                    "board_exists": False,
                    "board_stem": args.board,
                    "refusal_reason": (
                        "板名含路径分隔符/父目录引用或越界 (containment 拒绝)"
                        if board_path is None
                        else "原白板文件不存在"
                    ),
                    "available_boards": sorted(p.stem for p in board_dir.glob("*.md")),
                },
                ensure_ascii=False,
                indent=1,
            )
        )
        return 0

    board_text = _read(board_path)
    board_fm, board_body = _frontmatter_and_body(board_text)
    board_name = _oneline(
        _fm_scalar(board_fm, "board_name") or args.board, 120
    ).replace('"', "'")
    # 成员窄扫 (H3): 只认 ## Concepts 小节, 与后端 canonical 同窄度;
    # 剥 HTML 注释 — 维护说明里的 [[节点/xxx]] 示例不是成员 (Codex 反例实测)
    sec = _CONCEPTS_SECTION_RE.search(board_body)
    sec_body = re.sub(r"<!--.*?-->", "", sec.group(1), flags=re.S) if sec else ""
    # 只认行首 bullet 行上的链接 (对齐 canonical 托管块判定, H3 残余收口):
    # 散文/引用行里提到的 [[节点/x]] 不是成员声明
    bullet_lines = "\n".join(
        ln for ln in sec_body.splitlines() if re.match(r"^\s*-\s", ln)
    )
    concepts_members = _CONCEPT_LINK_RE.findall(bullet_lines)
    concepts_members = list(dict.fromkeys(m.strip() for m in concepts_members))

    manifest, manifest_unusable_reason = (None, "未提供 --manifest")
    if args.manifest:
        manifest, manifest_unusable_reason = _load_manifest(args.manifest, args.board)

    ledger: list[dict] = []
    manifest_meta: dict = {}
    if manifest is not None:
        try:
            ledger = _ledger_from_manifest(manifest)
            freshness = (
                manifest.get("freshness")
                if isinstance(manifest.get("freshness"), dict)
                else {}
            )
            orphans = [
                {
                    "node_id": _oneline(o.get("node_id") or "", 120),
                    "reason": _oneline(o.get("reason") or "", 80),
                    "source_board_raw": _oneline(o.get("source_board_raw") or "", 120)
                    or None,
                }
                for o in (manifest.get("orphans") or [])
                if isinstance(o, dict)
            ]
            exam_history = [
                {
                    "exam_board_id": _oneline(h.get("exam_board_id") or "", 200),
                    "created_at": _oneline(h.get("created_at") or "", 64) or None,
                    "status": _oneline(h.get("status") or "", 40) or None,
                    "selected_node": _oneline(h.get("selected_node") or "", 200)
                    or None,
                    "question_count": _int_or_none(h.get("question_count")),
                }
                for h in (manifest.get("exam_history") or [])
                if isinstance(h, dict)
            ]
            manifest_meta = {
                "source": manifest.get("source"),
                "source_status": manifest.get("source_status"),
                "degraded": bool(manifest.get("degraded")),
                "degraded_reason": manifest.get("degraded_reason"),
                "generated_at": freshness.get("generated_at"),
                "lag_seconds": freshness.get("lag_seconds"),
                "stale": bool(freshness.get("stale")),
                # H5/M9 二轮: 净化后的明细 + 计数一并给足, 报告不需要也不允许
                # 回读 manifest 原文 (AI 侧对账/考察历史的数字全部由此取)
                "orphans": orphans,
                "orphans_count": len(orphans),
                "dual_source_gap": _sanitize_gap(manifest.get("dual_source_gap")),
                "parse_errors_count": len(manifest.get("parse_errors") or []),
                "exam_history": exam_history,
                "exam_history_count": len(exam_history),
            }
            data_mode = "manifest"
        except (TypeError, AttributeError, KeyError, ValueError) as e:
            # 形状损坏 fail-closed → 降级而非异常退出 (M8)
            manifest, manifest_unusable_reason = (
                None,
                f"manifest 形状损坏: {type(e).__name__}",
            )
    if manifest is None:
        data_mode = "fallback_local"
        ledger = _ledger_from_local(vault, concepts_members)
        manifest_meta = {"unusable_reason": manifest_unusable_reason}

    seeds = [r for r in ledger if r.get("role") == "seed"]
    derived = [r for r in ledger if r.get("role") == "derived"]
    # 每种子的派生子女 (H5): manifest 模式由 relation_target 反查; fallback 无据 → None
    for s in seeds:
        if data_mode == "manifest":
            children = [
                r["node_id"]
                for r in derived
                if r.get("relation_target") == s.get("node_id")
            ]
            s["derived_children"] = children
            s["derived_children_count"] = len(children)
        else:
            s["derived_children"] = None
            s["derived_children_count"] = None

    all_tips = [
        {**t, "node_id": r["node_id"]} for r in ledger for t in r.get("tips", [])
    ]
    dated = sorted(
        (t for t in all_tips if _parse_dt(t.get("added_at")) is not None),
        key=lambda t: _parse_dt(t["added_at"]),
    )
    body_callouts = sum(r.get("body_callout_count", 0) for r in ledger)
    annotation_count = len(
        all_tips
    )  # 口径: frontmatter tips (两模式一致, 见 docstring)

    over_threshold = (
        len(ledger) > MEMBER_THRESHOLD or annotation_count > ANNOTATION_THRESHOLD
    )
    ranked = sorted(
        (r for r in ledger if r.get("pick_rank") is not None),
        key=lambda r: r["pick_rank"],
    )
    detail_rows = (ranked or ledger)[:DETAIL_K] if over_threshold else ledger
    detail_ids = [r["node_id"] for r in detail_rows]
    tail_rows = [r for r in ledger if r["node_id"] not in set(detail_ids)]

    stat = board_path.stat()
    out = {
        "board_exists": True,
        "board_stem": args.board,
        "board_name": board_name,
        "recap_date": today,
        "report_path": f"outputs/回顾-{args.board}-{today}.md",
        "data_mode": data_mode,
        "manifest": manifest_meta,
        "source_revision": {
            "board_sha256": hashlib.sha256(board_text.encode("utf-8")).hexdigest(),
            "board_mtime_utc": _iso_utc(stat.st_mtime),
            "scan_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "manifest_generated_at": manifest_meta.get("generated_at"),
            "manifest_lag_seconds": manifest_meta.get("lag_seconds"),
            "manifest_stale": manifest_meta.get("stale"),
        },
        "ledger": {
            "seeds": seeds,
            "derived": derived,
            "unknown": [r for r in ledger if r.get("role") not in ("seed", "derived")],
        },
        "counts": {
            "members": len(ledger),
            "seeds": len(seeds),
            "derived": len(derived),
            "stubs": sum(1 for r in ledger if r.get("is_stub")),
            "never_examined": sum(1 for r in ledger if not r.get("last_examined")),
            "tips_total": len(all_tips),
            # 学习 vault 无「已答」标记 → 未答 = 全部 tips, 只可标【未确认-无法判定已答】
            "tips_unanswered_upper_bound": len(all_tips),
            "tips_understanding_open": sum(
                1 for t in all_tips if t.get("understanding") != "understood"
            ),
            "tips_undated": len(all_tips) - len(dated),
            "body_callouts": body_callouts,
            "annotations": annotation_count,
            # H5 三轮: 关系类型聚合由脚本给出, ③ 方向段引用它而非自行数
            "relation_types": _relation_type_counts(ledger),
            "error_candidates_pending": sum(
                r.get("error_candidates_pending", 0) for r in ledger
            ),
        },
        "tips_oldest3": dated[:3],
        "scale_gate": {
            "member_threshold": MEMBER_THRESHOLD,
            "annotation_threshold": ANNOTATION_THRESHOLD,
            "over_threshold": over_threshold,
            "detail_k": DETAIL_K,
            # 超线时: 详审名单与尾部聚合都由本脚本给出, LLM 不自行聚合 (H5)
            "detail_node_ids": detail_ids if over_threshold else None,
            "tail_counts": (
                {
                    "members": len(tail_rows),
                    "stubs": sum(1 for r in tail_rows if r.get("is_stub")),
                    "never_examined": sum(
                        1 for r in tail_rows if not r.get("last_examined")
                    ),
                    "tips_total": sum(r.get("tips_count", 0) for r in tail_rows),
                }
                if over_threshold
                else None
            ),
        },
        "concepts_members": concepts_members,
        "previous_recap": _previous_recap(vault / "outputs", args.board, today),
        # B2 三轮: 写侧目标 lstat 预检 — skill 在 Step 5 Write 前必须确认为空;
        # 非空 = vault 被布防 (预置 symlink 可把 Write 导向 vault 外), 显式拒绝
        "unsafe_write_targets": [
            str(p)
            for p in (
                vault / "outputs",
                vault / "outputs" / f".recap-manifest-{args.board}.json",
                vault / "outputs" / f".recap-scan-{args.board}.json",
                vault / "outputs" / f"回顾-{args.board}-{today}.md",
            )
            if p.is_symlink()
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
