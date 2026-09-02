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

一梯队信号 (CARD-G5-4, BATCH-2026-08-28-第五批):
  - scan JSON 加性新增 ``signals`` 块 — 四信号 (未答问题年龄/来源覆盖率/
    无来源结论/重复堆积), 各含 value/denominator/percentile_ref (板内分位
    参考)/availability (实测|文件|推定|无据)/asof。
  - **0 阈值**: 只出信号值与板内分位参考, 无任何合格线/判定字段 —
    判偏航留人 (报告③段叙述以材料为主语)。
  - **零编造**: denominator == 0 或数据缺失 → availability="无据",
    value=null; 不用其他信号的数字顶替。
  - availability 档位 = min(数据源档, 语义档): manifest 实返="实测",
    本地 frontmatter 抄录="文件", 依赖 fallback 角色推断="推定";
    时序信号恒 ≤"文件" (added_at=最后变更时间, C5 已知边界)。
  - ledger 行加性补 ``source_note`` 字段 (manifest 透传 / fallback 从
    frontmatter 抄录并按 stem 归一)。
  - --verify 同步扩展: scan JSON 含 signals 键 → ③段信号标准行数字与
    档位全等绑定, 篡改任一数字 exit 1; 旧 scan JSON (无 signals 键) 不
    检查本条 (兼容)。
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import sys
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path

MEMBER_THRESHOLD = 30  # 规模门: 成员数 (设计稿 v2 §七)
ANNOTATION_THRESHOLD = 100  # 规模门: 批注数 (frontmatter tips 口径)
DETAIL_K = 10  # 超线时详审的 pick_rank 前 K
STUB_PLACEHOLDER = "你的 1-2 句精准定义"

# 一梯队信号 availability 档位 (G5-4): 与 SKILL 维度② 三档标注同語义 + 无据
AVAIL_MEASURED = "实测"  # manifest 实返数据
AVAIL_FILE = "文件"  # 本地文件抄录 / 时序封顶档
AVAIL_INFERRED = "推定"  # 依赖 fallback 角色推断
AVAIL_NODATA = "无据"  # denominator == 0 或数据缺失, value 必为 null
SIGNAL_GROUPS_CAP = 5  # 重复堆积组明细上限 (防超大板撑爆 JSON)
SIGNAL_NODE_IDS_CAP = 10  # 无来源结论点名清单上限

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


def unsafe_name_chars(name: str) -> list[str]:
    """板名/节点名里的**不可接受字符**, 返回其 U+XXXX 码位 (去重保序, 空 = 合法)。

    ⛔ M7 (CARD-M11M7, BATCH-2026-08-31-第七批) —— 原拒绝集只有 ``ord(c) < 32``
    (C0), 漏掉 DEL 与 C1, 二者均已**实测复现**消费面损坏:
      - ``U+007F`` (DEL): 板名会被 recap_exam_build 写进产物 frontmatter 的
        ``source_board``, PyYAML 对它直接抛 ReaderError ⇒ board_manifest_service
        记 ``file_parse_failed``, 整张检验白板从 exam_history 里消失;
      - ``U+0085`` (NEL): YAML 规范把它当**行断**处理 ⇒ ``source_board`` 的值在
        此处断裂 ⇒ ``exam_history.board_id`` 变成 ``null`` (板归属丢失, 且**不报**
        parse error —— 静默错更难发现)。``U+0080``-``U+009F`` 整段 C1 同族同理。

    ``U+2028``/``U+2029`` (行/段分隔符) **无实测症状** (当前 PyYAML 容忍) ——
    列入是因为 Python ``str.splitlines()`` 会在它们处分行, 而本脚本的解析与
    verifier 全是行级正则; 属预防性拒绝, 误伤面为零 (没有合法板名需要行分隔符)。
    两类字符的证据等级不同, 此处如实分列, 不混称"均已实证"。

    诚实边界: 本函数只管**字符集**, 不做 Unicode 归一化 (NFC/NFD 归一属
    CARD-G5-3 的稳定 ID 面, 两者互不覆盖 —— 归一化解决"同一板名两种编码形式",
    本函数解决"这个字符根本不能进 YAML/行级解析")。
    """
    bad: list[str] = []
    for ch in name:
        o = ord(ch)
        if o < 0x20 or 0x7F <= o <= 0x9F or ch in ("\u2028", "\u2029"):
            code = f"U+{o:04X}"
            if code not in bad:
                bad.append(code)
    return bad


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
    # M7: 控制字符判据抽成 unsafe_name_chars() —— 拒绝集扩到 DEL/C1/行分隔符,
    # 且同一份判据可被调用方复用于**点名码位**的可读拒绝原因 (一处判定, 一处诊断)。
    if any(c in "`$'\"" for c in name) or unsafe_name_chars(name):
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
    """frontmatter 顶层标量抄录 — 值必须与键**同行**, 键必须**顶格**。

    W2 (workflow round-1): 原正则 ``:\\s*(.+?)\\s*$`` 的 ``\\s`` 在 re.M 下
    可跨换行, 空键 (``derived-from:`` 后直接换行) 会把**下一行整行**
    (``mastery_score: 0.5``) 当成本键的值 — 凭空捏造出来源锚点/掌握度。
    改用 ``[^\\S\\n]*`` (同行空白) 两侧夹逼: 空键返回 None。

    Codex round-3 收口 (与后端 yaml 解析对齐, 减少分叉面):
      - 键必须顶格 (``^key:``) — 嵌套块里的同名子键 (如 relationships[].type
        下的 description) 不再被当顶层标量;
      - 剥 YAML 行尾注释 (`` #`` 前需空白, 与 YAML 规范同) —
        ``created_from: ai_linked_doc # 备注`` 抄成 ``ai_linked_doc``;
      - 块标量/流式集合起始符 (``|``/``>``/``[``/``{``) 不是标量值 → None
        (交由专门的块解析器, 避免把 ``|-`` 当成值)。
    ⛔ 本函数仍是正则近似, 不是完整 YAML: 重复键取首个、锚点/别名不解析 —
    fallback 模式的诚实边界 (报告标【推定】)。
    """
    m = re.search(rf"^{re.escape(key)}[^\S\n]*:[^\S\n]*(.*?)[^\S\n]*$", fm, re.M)
    if not m:
        return None
    raw = m.group(1)
    # YAML 行尾注释: " #" 起 (引号内的 # 不受影响 — 先剥注释再剥引号会误伤,
    # 故只在值未被引号包裹时剥)
    if not (raw.startswith(('"', "'")) and len(raw) >= 2):
        raw = re.split(r"(?:^|\s)#", raw, maxsplit=1)[0]
    raw = raw.strip()
    if raw[:1] in ("|", ">", "[", "{", "&", "*"):
        return None
    return raw.strip("\"'").strip() or None


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


def _passthrough_note_ref(value) -> str | None:
    """manifest 侧来源引用净化 — 后端已 resolve_node_id 归一, 这里只净化。

    round-3 M1: 对 manifest 值再调 _strip_note_ref **不幂等** —
    ``[[节点/null]]`` 在 fallback 归一成 stem ``"null"``, 再过一次却因裸
    值判空而变 None, 两模式/两次归一结果分叉。故 manifest 侧只在值**仍带
    wikilink 标记**时才归一 (手工/旧版 manifest 的兼容路径), 否则原样净化
    透传 — 后端 resolve 过的裸 stem 不再二次判 null。
    """
    s = _oneline(value or "", 200).strip("\"'")
    if not s:
        return None
    return _strip_note_ref(s) if "[[" in s else s


def _strip_note_ref(value) -> str | None:
    """fallback 侧来源引用抄录归一 → 节点 stem。

    对齐 board_manifest_service.resolve_node_id 的语义 (wikilink 内文 →
    剥 |别名 → 剥 #锚点 → basename → 剥 .md), 使两模式 ledger 的
    source_note 可比。非 wikilink 的裸值同样过 basename 归一。
    YAML null 字面量 (null / Null / NULL / ~, 正则 frontmatter 抄录拿到的是
    字面字符串) 按空处理 — ``source_note: null`` 不得被算成来源锚点 (F4)。
    ⛔ null 判定**只对裸值生效**: ``[[节点/null]]`` 是一个合法节点名的
    wikilink, 必须归一为 stem ``null`` 而不是被清成 None (Codex round-2
    M1 幂等性: 后端 resolve_node_id 已把它变成裸 "null", 本函数再过一次
    时不得改变结果) — 因此先剥 wikilink, 再只在**无 wikilink 包裹**时判
    null 字面量。YAML 的 null 拼写不含 ``none``, 不误杀名为 none 的节点。
    """
    s = _oneline(value or "", 200).strip("\"'")
    if not s:
        return None
    m = re.search(r"\[\[([^\]]+)\]\]", s)
    # round-4 H1: 与后端 yaml.safe_load 的 **falsy** 集合对齐, 不只 null/~ —
    # false/0/""/{}/[] 在后端同样是 falsy → 不算派生痕迹/来源锚点。
    if m is None and s.lower() in ("null", "~", "false", "0", "{}", "[]", "''", '""'):
        return None
    inner = m.group(1) if m else s
    inner = inner.split("|", 1)[0].split("#", 1)[0]
    out = inner.split("/")[-1].strip().removesuffix(".md")
    return out or None


def _pctl(sorted_vals: list[int], q: float) -> int | None:
    """nearest-rank 分位 (确定性, 无插值): 取第 ceil(q*n) 位次的值。"""
    if not sorted_vals:
        return None
    k = max(1, math.ceil(q * len(sorted_vals)))
    return sorted_vals[min(k, len(sorted_vals)) - 1]


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
                # G5-4 加性: 后端已 resolve_node_id 归一为 stem;
                # _passthrough_note_ref 只对残留 wikilink 形态补归一 (幂等, M1)
                "source_note": _passthrough_note_ref(n.get("source_note")),
                "pick_rank": _int_or_none(pick.get("pick_rank")),
                "relation_type": _oneline(rel.get("type") or "", 40) or None,
                # Codex round-2 M1: relation_target 与 source_note 同归一,
                # 否则同一来源在两字段/两模式间形态不一 (一个 stem 一个原串);
                # round-3 M1: 用幂等的 passthrough 版 (后端已 resolve 过)
                "relation_target": _passthrough_note_ref(rel.get("target_node_id")),
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
        # F1 (Codex G5-4 round-1): derived-from 是来源锚点 — fallback 不解析它
        # 会让同一 vault 的来源覆盖/无来源信号与 manifest 模式分叉 (manifest 侧
        # _node_relation 的退路分支就是 derived-from)。对齐: 有可解析的
        # derived-from → relation_target/relation_type 同型落 ledger;
        # 派生子女计数仍恒无据 (C5 铁律不破, 由 derived_children=None 承载)。
        derived_target = _strip_note_ref(
            _fm_scalar(fm, "derived-from") or _fm_scalar(fm, "derived_from")
        )
        # H1/W1/W3 (Codex round-2/3 + workflow): role 判定对齐后端
        # board_manifest_service._node_role 的 **truthiness** 语义 —
        #   · 裸子串 "derived-from" in fm 会被 tips 正文里提到该词的节点触发
        #     (假 derived → 假"无来源结论"点名);
        #   · 只认连字符会让 derived_from: 写法的节点 role=seed 却带
        #     relation_target, 自相矛盾;
        #   · **键存在**也不对: 后端对 `derived-from: null` / 空值取 falsy 判
        #     seed, 键存在检测会判 derived → round-3 H1 实测分叉。
        # 故: 有可解析的 derived 目标 (derived_target 非空) 或 relationships
        # 块 或 created_from==ai_linked_doc → derived, 与后端三支同构。
        # round-4: relationships 也要 truthiness — 后端 fm.get("relationships")
        # 对 `relationships:` (空值/null) 取 None → falsy → 不算派生。故要求
        # 键后**确有列表内容**: 同行流式 `[...]` 非空, 或次行起有缩进 `- ` 项。
        mrel = re.search(r"^relationships[^\S\n]*:[^\S\n]*(.*)$", fm, re.M)
        has_relationships = False
        if mrel:
            inline = re.split(r"(?:^|\s)#", mrel.group(1), maxsplit=1)[0].strip()
            # round-4 H1: 与后端 truthiness 对齐的 falsy 全集
            if inline and inline.lower() not in (
                "null",
                "~",
                "false",
                "0",
                "[]",
                "{}",
                "[ ]",
                "{ }",
                "''",
                '""',
            ):
                has_relationships = True
            elif not inline:
                # 空值 → 看次行是否真有列表项 (缩进 `- `) 或缩进 mapping 键
                tail = fm[mrel.end() :]
                has_relationships = bool(
                    re.match(r"\s*\n[^\S\n]+(?:-[^\S\n]|\S+[^\S\n]*:)", tail)
                )
        is_derived = bool(
            derived_target
            or has_relationships
            or _fm_scalar(fm, "created_from") == "ai_linked_doc"
        )
        rows.append(
            {
                "node_id": name,
                # 种子 = 无派生痕迹 (设计稿 §四); 本地推定, 报告标【推定】
                # 口径对齐 board_manifest_service._node_role 的 truthiness 三支
                "role": "derived" if is_derived else "seed",
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
                # G5-4 加性: frontmatter 抄录, 剥 wikilink 归一 stem (可比性)
                "source_note": _strip_note_ref(_fm_scalar(fm, "source_note")),
                "pick_rank": None,
                "relation_type": "derived_from" if derived_target else None,
                "relation_target": derived_target,
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


def _has_provenance(row: dict) -> bool:
    """来源锚点在位判定: source_note 或 relation.target 任一非空。

    fallback 模式 relation_target 恒 None (C5 既有语义, 派生子女无据不破) →
    F1 后 fallback 也从 derived-from 抄录 relation_target (同 manifest 侧
    _node_relation 退路分支), 两模式来源口径对齐; 差异仅剩 relationships[]
    列表 (fallback 无 yaml 库不解析) — 由 availability 档位如实反映。
    """
    return bool(row.get("source_note") or row.get("relation_target"))


def _build_signals(
    ledger: list[dict],
    all_tips: list[dict],
    dated: list[dict],
    data_mode: str,
    scan_at: str,
    now: datetime,
) -> dict:
    """一梯队偏航信号 (CARD-G5-4) — 全部确定性可复算, 0 阈值。

    结构契约 (测试锁定): 四信号各含 value / denominator / percentile_ref
    (板内分位参考) / availability / asof 五键; 判定字段一律不存在 —
    判偏航留人。denominator == 0 → value=null + availability="无据"。
    """
    measured = AVAIL_MEASURED if data_mode == "manifest" else AVAIL_FILE
    members = len(ledger)
    derived_rows = [r for r in ledger if r.get("role") == "derived"]

    # 信号1 · 未答问题年龄 — dated tips 的年龄天数分布 (整数天, floor);
    # added_at 在未来 (时钟漂移/投毒) → 按 0 天计, 不产出负年龄。
    ages = sorted(
        max(0, int((now - _parse_dt(t["added_at"])).total_seconds() // 86400))
        for t in dated
    )
    sig_age = {
        "value": ages[-1] if ages else None,
        "denominator": len(ages),
        "percentile_ref": (
            {
                "p25_days": _pctl(ages, 0.25),
                "p50_days": _pctl(ages, 0.50),
                "p75_days": _pctl(ages, 0.75),
                "max_days": ages[-1],
            }
            if ages
            else None
        ),
        # 时序封顶【文件】: added_at=最后变更时间 (C5 已知边界), manifest 也不升档
        "availability": AVAIL_FILE if ages else AVAIL_NODATA,
        "asof": scan_at,
        "undated": len(all_tips) - len(dated),
        "note": (
            "value=最老年龄(天); added_at=最后变更时间(C5 边界), 时序封顶文件档; "
            "未答=全部 tips 上界(无已答标记); 无时间戳条目不参与"
        ),
    }

    # 信号2 · 来源覆盖率 — 成员含来源锚点占比; 二值分布无分位,
    # 板内参考改用 by_role 拆分 (percentile_ref 如实置 null)
    prov_count = sum(1 for r in ledger if _has_provenance(r))
    by_role: dict[str, dict[str, int]] = {}
    for r in ledger:
        role = r.get("role") if r.get("role") in ("seed", "derived") else "unknown"
        bucket = by_role.setdefault(role, {"with_provenance": 0, "total": 0})
        bucket["total"] += 1
        if _has_provenance(r):
            bucket["with_provenance"] += 1
    sig_cov = {
        "value": prov_count if members else None,
        "denominator": members,
        "percentile_ref": None,
        "by_role": by_role,
        "availability": measured if members else AVAIL_NODATA,
        "asof": scan_at,
        "note": "来源锚点=source_note 或 relation.target; 二值信号无分位, 板内参考=by_role",
    }

    # 信号3 · 无来源结论 — 派生角色成员缺来源锚点计数;
    # fallback 的 role 是本地推定 → 整信号降"推定"档
    unsourced_ids = [r["node_id"] for r in derived_rows if not _has_provenance(r)]
    sig_unsourced = {
        "value": len(unsourced_ids) if derived_rows else None,
        "denominator": len(derived_rows),
        "percentile_ref": None,
        "node_ids": unsourced_ids[:SIGNAL_NODE_IDS_CAP],
        "availability": (
            AVAIL_NODATA
            if not derived_rows
            else (AVAIL_MEASURED if data_mode == "manifest" else AVAIL_INFERRED)
        ),
        "asof": scan_at,
        "note": "分母=派生角色成员; fallback 的角色为本地推定 → 推定档; 分母 0 = 无据",
    }

    # 信号4 · 重复堆积 — tips 文本归一化 (空白折叠+casefold) 全等分组,
    # value = Σ(组内条数-1) 即冗余条数; 不做语义相似判定 (零编造)
    norm_map: dict[str, list[str]] = {}
    for t in all_tips:
        key = " ".join(str(t.get("text") or "").split()).casefold()
        if key:
            norm_map.setdefault(key, []).append(t["node_id"])
    dup_groups = sorted(
        ((k, v) for k, v in norm_map.items() if len(v) >= 2),
        key=lambda kv: (-len(kv[1]), kv[0]),
    )
    sizes = sorted(len(v) for _, v in dup_groups)
    sig_dup = {
        "value": sum(s - 1 for s in sizes) if all_tips else None,
        "denominator": len(all_tips),
        "percentile_ref": (
            {
                "p50_group_size": _pctl(sizes, 0.50),
                "max_group_size": sizes[-1],
                "group_count": len(sizes),
            }
            if sizes
            else None
        ),
        "groups": [
            {"text_preview": k[:60], "count": len(v), "node_ids": v[:5]}
            for k, v in dup_groups[:SIGNAL_GROUPS_CAP]
        ],
        "availability": measured if all_tips else AVAIL_NODATA,
        "asof": scan_at,
        "note": (
            "重复口径=空白折叠+casefold+200字截断后全等 (超长 tips 仅比对前 200 字, "
            "M9 截断口径); value=冗余条数 Σ(组-1); 空文本不参与"
        ),
    }

    return {
        "signals_version": 1,
        # 0 阈值声明: 本块只提供数值与板内分位参考, 不含任何判定 — 判偏航留人
        "policy": "zero_threshold",
        "asof": scan_at,
        "unanswered_question_age": sig_age,
        "source_coverage": sig_cov,
        "unsourced_conclusions": sig_unsourced,
        "duplicate_accumulation": sig_dup,
    }


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
# ⛔ round-6 终裁复核: 本词表是**子串**匹配, 三处曾造成误伤/自相矛盾 —
#   · 「子节点」是「种**子节点**」的真子串 → 合法中文「这块板只有 1 个种子节点」被判违规;
#   · 「无派生」是白名单无据文案「本板**无派生**角色成员」的真子串 → 自家两条规则打架;
#   · SKILL 白名单动作句「…`Cmd+Shift+D` **派生**新节点」本就含该词。
# 词表只保留**明确断言子女数**且不与合法文本重叠的形态; 结构性防线由
# 下方的「含『派生』的行必须整行匹配白名单」承担。
_VERIFY_FALLBACK_DERIVE = (
    "已派生",
    "未派生",
    "从未派生",
    "派生出",
    "没有派生",
    "零派生",
)
_VERIFY_ACTION_VERBS = (
    "/node-chat",
    "/start-exam-board",
    "/board-recap",
    "Cmd+Shift+D",
    "Cmd+Shift+A",
    "Dashboard",
)


_SIGNAL_SPECS = (
    ("unanswered_question_age", "未答问题年龄"),
    ("source_coverage", "来源覆盖率"),
    ("unsourced_conclusions", "无来源结论"),
    ("duplicate_accumulation", "重复堆积"),
)
# 维护卡 B · H-3: X/N 型信号行的**标准尾部文案**(SKILL Step 5 模板逐字规定)。
# 有了它, 尾部校验从"先开放再排除"(黑名单) 转成整行正向允许式 —— 尾部只许是
# 这三句之一, 夹带任何别的内容 (含「另有仨条」这类黑名单外的中文数量词) 一律 FAIL。
# ⛔ 新增信号必须在此登记, 否则 verifier 会显式报"未登记标准尾部文案"而不是静默放行。
_SIGNAL_TAILS = {
    "source_coverage": "成员含来源锚点",
    "unsourced_conclusions": "派生角色成员缺来源锚点",
    "duplicate_accumulation": "条批注为重复条目",
}
# CARD-维护B-R2 (e) · 第七批裁定 B-1 甲（放宽规则, 待用户裁决）: 信号行尾部的
# **封闭注记表** — 标准尾部与档位标注之间允许一个可选注记, 注记只许**逐字**取自
# 本表（正向允许式, 不是自由文本槽——槽退化成 `[^【】]*` 就重开了 H-3 黑名单老路）。
# 与 SKILL.md ③段信号行铁律同表同改, 同步由 e3 表锁测试逐字比对。
# ⛔ 表内短语不得含任何数字/量词字符（槽在 D2 治理之外, 靠表封闭性兜底）。
# 无据行**不适用**本表（无据行另有整行固定模板, 见 _NODATA_REASONS）。
_SIGNAL_TAIL_NOTES = ("口径一致",)
# 年龄信号标准行: 最老 N 天（参与统计 D 条，p25/p50/p75 = a/b/c 天）
_SIG_AGE_RE = re.compile(
    r"最老\s*(\d+)\s*天\s*[（(]\s*参与统计\s*(\d+)\s*条[，,]\s*"
    r"p25/p50/p75\s*=\s*(\d+)/(\d+)/(\d+)\s*天\s*[）)]"
)


_AVAIL_ENUM = (AVAIL_MEASURED, AVAIL_FILE, AVAIL_INFERRED, AVAIL_NODATA)
_SIGNAL_REQUIRED_FIELDS = (
    "value",
    "denominator",
    "percentile_ref",
    "availability",
    "asof",
)
# 无据行允许的**全部**原因文案 (round-5: 白名单取代数字黑名单)。
# 与 SKILL.md Step 5 模板逐字一致 — 新增文案必须两处同改
# (同步由 b1「SKILL 同步锁」测试逐字比对, 单侧改动即红)。
# ⛔ CARD-维护B-R2: 此前「两处同改」只是注释约定, 表增一条只放宽那一个字面,
# 没有任何测试锁成员/长度/与 SKILL.md 的同步 (S1 survivor 实测)。
_NODATA_REASONS = (
    "无带时间戳批注",
    "分母为零",
    "本板无派生角色成员",
    "本板无批注",
    "数据源不可用",
)


def _verify_signal_schema(key: str, sig, problems: list[str]) -> bool:
    """signals.<key> 子对象 schema fail-closed (Codex round-2 M2)。

    只校验顶层 signals 是 dict 不够 — 把子对象削成 {"availability":"无据"}
    就能让报告写四条"无据"蒙混过关。必需五键齐全 / availability 属枚举 /
    无据 ⇒ value is None 且 denominator == 0 / 有数 ⇒ value 是整数。
    """
    if not isinstance(sig, dict):
        problems.append(f"数字终核: scan JSON signals.{key} 形状损坏")
        return False
    missing = [f for f in _SIGNAL_REQUIRED_FIELDS if f not in sig]
    if missing:
        problems.append(f"数字终核: signals.{key} 缺必备字段 {missing}")
        return False
    avail = sig.get("availability")
    if avail not in _AVAIL_ENUM:
        problems.append(f"数字终核: signals.{key}.availability 非法值 {avail!r}")
        return False
    if avail == AVAIL_NODATA:
        if sig.get("value") is not None or sig.get("denominator") != 0:
            problems.append(f"数字终核: signals.{key} 标无据却带数值 (契约违反)")
            return False
    else:
        # round-3 M2: Python 里 bool 是 int 子类 — `value: true` 配报告 "1/N"
        # 曾整条通过。显式排除 bool。
        for f in ("value", "denominator"):
            v = sig.get(f)
            if isinstance(v, bool) or not isinstance(v, int):
                problems.append(
                    f"数字终核: signals.{key}.{f} 非整数 ({type(v).__name__})"
                )
                return False
        # round-4 新增 FAIL: 年龄信号有数档时 percentile_ref 必须是含三个整数
        # 分位的对象 — 置 null 时报告渲染成 "None/None/None" 曾照样通过。
        if key == "unanswered_question_age":
            pr = sig.get("percentile_ref")
            if not isinstance(pr, dict):
                problems.append(
                    f"数字终核: signals.{key} 有数档但 percentile_ref 非对象"
                )
                return False
            for pk in ("p25_days", "p50_days", "p75_days"):
                pv = pr.get(pk)
                if isinstance(pv, bool) or not isinstance(pv, int):
                    problems.append(
                        f"数字终核: signals.{key}.percentile_ref.{pk} 非整数"
                    )
                    return False
    return True


def _quote_width(line: str) -> int:
    """行首到引用内容起点的宽度: 前导空白 + 逐层 `>`(+至多一空白)。

    `> > - x` → 4; ` > - x` → 3 (⛔ round-4 抢救探针 A: 引用标记**前**的
    前导空白计入——它是引用层的一部分); 无引用 (`- x` / `    x`) → 0。
    """
    pos, n = 0, len(line)
    while pos < n and line[pos] in " \t":
        pos += 1
    w = pos
    saw = False
    while pos < n:
        ch = line[pos]
        if ch == ">":
            saw = True
            pos += 2 if pos + 1 < n and line[pos + 1] in " \t" else 1
            w = pos
        elif ch in " \t" and pos + 1 < n and line[pos + 1] == ">":
            pos += 1
            w = pos
        else:
            break
    return w if saw else 0


def _indent_after_quotes(line: str) -> int:
    """引用系前缀之后的剩余缩进 (与 _quote_width 相加 = 内容的绝对列)。"""
    w = _quote_width(line)
    rest = line[w:]
    return len(rest) - len(rest.lstrip(" \t"))


def _strip_code_blocks(text: str) -> str:
    """剔除**围栏**代码块 (```/~~~), 含引用块内的围栏 (round-4 M3 → round-5)。

    代码块里的内容渲染为字面文本, 不是报告的陈述 —— 把信号行藏进去曾让
    verifier 认为"信号行在场"。行数保持不变 (整行替空), 以免影响其他基于
    行的校验。

    round-5 两项修正:
      · 引用前缀 (``> ``) 内的围栏此前不被识别 (``> ``` `` 逃逸) → 先剥
        引用前缀再判围栏;
      · **不再剥四空格缩进块** —— 合法的三级嵌套列表 (四空格缩进) 会被误删,
        实测导致"③段缺信号行"误报。缩进块里的信号行改由信号行自身的
        严格模板拒绝 (模板行首只允许 ``> ``/``- ``/空白, 不允许四空格缩进)。

    ⛔ 维护卡 B · E1 (round-6 实证反例 `four-fence-short-close`): 原实现只存
    ``bare[:3]`` 并用 ``startswith`` 判闭合 —— 四反引号开栏、三反引号"闭合"后,
    后续内容被当成**块外正文**, 于是藏在 ``<pre><code>`` 里的信号行仍被 verifier
    当成在场陈述 (实测 exit 0)。CommonMark 的规则是: 闭合围栏必须**同字符**且
    **不短于**开栏。这里按规则记录开栏的完整标记再比长度。
    """
    out: list[str] = []
    fence: str | None = None  # 开栏的完整标记, 如 "````"
    # ⛔ Codex round-1 BLOCKER-1: 只比字符与长度**仍不是** CommonMark ——
    # 闭栏行在标记之后**只能有空白**(`` ````not-a-valid-close `` 不是闭栏),
    # 且围栏行缩进最多三格 (四格起是缩进代码块)。少这两条时,
    # ````text 后跟一个带 info string 的伪闭栏就能让后续信号行"看起来在块外",
    # 而 CommonMark 渲染里它们全在 <pre><code> 内 —— 实测 exit 0。
    open_re = re.compile(r"^(?P<ind> {0,3})(?P<fence>`{3,}|~{3,})")
    close_re = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})[^\S\n]*$")
    for ln in text.splitlines():
        # 剥任意层引用前缀后再判围栏。
        # ⛔ CARD-维护B-R2 round-2 线索（Codex 被截断前的中途发现, 本车道独立复现）:
        # 只剥 `>`/空白不剥**列表标记**时, `> - ``` ` (列表项内围栏, Obsidian 渲染为
        # 列表项内的代码块) 不被识别为开栏 —— 藏进里面的信号行被当成在场陈述,
        # 整篇 VERIFY PASS (实测 A/A2 两形态 exit 0)。剥列表符只影响**围栏判定**
        # (非围栏行 out.append 原样保留), 标记后须有空白 (`- ``` 是列表项围栏,
        # `---` 是 thematic break 不是列表)。
        # ⛔ CARD-维护B-R2 round-3: 无序 marker 之外**有序 marker** (`1. `) 与
        # **多层 marker** (`- - `) 同样是列表容器 (渲染为列表项内围栏), 一并剥。
        # ⛔ R3 round-26（冻结审查 v7）：原式的 `[>\s]` 会**吃掉任意前导空白**，
        #    于是 open_re 的 ` {0,3}` 形同虚设 —— 顶层缩进四格的 ``` 被当成开栏
        #    （CommonMark 里那是 indented code block，不是围栏），其后用户
        #    **看得见**的「本板共有 N 个…」会被当成围栏内内容整段免检。
        #    ⇒ 只剥**容器前缀**（引用 `>` / 列表 marker，各自最多 3 格缩进），
        #      无 marker 时**不动**前导空白，让 ` {0,3}` 真正生效。
        # ⛔ R3 round-27（冻结审查 v8）：round-26 的 marker 后 `[^\S\n]*` 会**吞任意
        #    空白** —— `>` 后 5 格再跟三反引号被剥成顶层 fence，而 CommonMark 里
        #    引用 padding 至多 1 格、余下 4 格使其成为 indented code，不该开栏。
        #    ⇒ 引用后至多 1 格 padding；列表 marker 后 1-4 格（再多是 indented code）。
        #    ⚠️ **列表 continuation 未建模**（`- item` 之后的相对内容列）——
        #      审查方指出继续补单条 regex 无法闭合这一面，属重做设计，如实登记。
        bare = re.sub(
            r"^(?: {0,3}(?:>[^\S\n]?|(?:[-*+]|\d{1,9}[.)])[^\S\n]{1,4}))*", "", ln
        )
        if fence is None:
            m = open_re.match(bare)
            # 反引号围栏的 info string 不得含反引号 (CommonMark);
            # 波浪线围栏无此限制。
            if m and not (m.group("fence")[0] == "`" and "`" in bare[m.end() :]):
                fence = m.group("fence")
                # ⛔ round-3 BLOCKER-1 (Codex 实证 + 车道独立复现): 列表项内围栏
                # 的内容行**绝对内容列必须 ≥ 开栏行剥到围栏标记的绝对列** ——
                # 缩进不足的非空行会结束容器, 围栏随之结束, 该行渲染为
                # **可见正文** (三个 sibling <li> 的中间项)。不跟踪这一点时,
                # 可见伪计数被误当围栏内容剥掉, D2 漏拦 (实测
                # `- ``` / - 本板共有 987654 个… / - ``` ` exit 0)。
                # ⛔ 口径 = **绝对列** (round-5 LOW 更正: 原注释写「相对口径」与
                # 实现矛盾)——开栏列 = 本行剥掉的前缀长度; 内容行绝对列 =
                # _quote_width + _indent_after_quotes (引用系前缀 + 其后缩进,
                # 前导空白计入引用系)。无列表容器 (纯引用/缩进) 时无边界,
                # 行为不变。
                fence_list_col = None
                if re.search(r"(?:[-*+]|\d{1,9}[.)])[^\S\n]", ln):
                    fence_list_col = len(ln) - len(bare)
                out.append("")
                continue
        else:
            # ⛔ R3 round-28（冻结审查 v9 反例）：围栏打开后仍对内容逐行剥
            #    **列表** marker，于是块内的 `- ``` ` 被当成闭栏、下一行重新
            #    开栏，最终把用户可见的正文剥到 EOF。CommonMark 里闭栏必须在
            #    **同一容器**内 —— 带列表 marker 的行是新列表项，不可能是闭栏。
            #    ⇒ 判闭栏时只剥引用前缀，不剥列表 marker。
            #    ⚠️ 完整的容器状态（列表 continuation 的相对内容列）仍未建模，
            #      审查方判为需重做设计，如实登记。
            #   剥引用前缀恒做；**列表 marker 只在开栏本身就在列表项内时才剥** ——
            #   顶层围栏里的 `- ``` ` 是字面内容（审查方反例），列表项内围栏
            #   则本来就由下一个 `- ``` ` 闭合（round-2 固化形态）。
            if fence_list_col is None:
                bare_close = re.sub(r"^(?: {0,3}>[^\S\n]?)*", "", ln)
            else:
                bare_close = bare
            mc = close_re.match(bare_close)
            # 闭合: 同字符 + 长度 ≥ 开栏 + 其后只有空白
            if (
                mc
                and mc.group("fence")[0] == fence[0]
                and len(mc.group("fence")) >= len(fence)
            ):
                fence = None
                out.append("")
                continue
            if fence_list_col is not None and ln.strip():
                # 缩进不足 (相对引用系) 的非空行 → 容器结束, 围栏随之结束:
                # 该行按普通正文保留, 交回 D2/信号行校验。
                if _quote_width(ln) + _indent_after_quotes(ln) < fence_list_col:
                    fence = None
                    out.append(ln)
                    continue
            out.append("")
            continue
        out.append(ln)
    return "\n".join(out)


def _verify_signal_lines(text: str, signals: dict, problems: list[str]) -> None:
    """G5-4 信号绑定 (fail-closed): scan JSON 含 signals 键才进本函数。

    ③段必须逐信号给**独占一行**的标准行, 行内数字与 availability 档与
    signals.* 全等 — 篡改任一数字 / 档位 / 缺行 / 无据错标 / 合并行 → FAIL。
    旧 scan JSON (无 signals 键) 由调用方跳过 (兼容)。同 label 行若出现
    多条, 逐条全查 — 防"一条合规一条私货"的双行逃逸。
    """
    # M3 (round-2 → round-4): ③ 段止于下一个 ## / ###。历轮收紧:
    #   round-2 只认 ###（"## 附录"可越界）→ round-3 认 tab 分隔（"##\t附录"）
    #   → round-4 认**空标题** `##`（行尾即止，无标题文字也是合法标题）。
    # 另: 信号行**不得藏在代码块里** — fenced (```/~~~) 与四空格缩进块在渲染
    # 时是字面文本, 与"报告在说什么"分叉, 故校验前整体剔除。
    scan_text = _strip_code_blocks(text)
    # ⛔ round-6 终裁复核: 剔除代码块是**双向**的 — 它挡住"把必需行藏进围栏",
    # 却放行"在合规行之外再往围栏里追加一组造假信号行"(围栏内容在 Obsidian
    # 里照常渲染为可见文本, 读者会看到与 scan JSON 冲突的第二组数字)。
    # 故: 被剔除的那部分文本里**不得出现任何信号 label**。
    # ⛔ CARD-维护B-R2 round-3 HIGH-3: 原 zip() 在行数不等时静默截断 ——
    # EOF 未闭合围栏把尾部行全部剥空后, splitlines() 行数差让**最后一行原文
    # 不参与比较**, 藏在里面的伪信号逃过本检查。改 zip_longest 对齐。
    stripped_only = "\n".join(
        a
        for a, b in zip_longest(text.splitlines(), scan_text.splitlines(), fillvalue="")
        if a != b
    )
    for _, lb in _SIGNAL_SPECS:
        if lb in stripped_only:
            problems.append(
                f"代码块内出现信号名 {lb} (围栏内容仍会渲染给读者, "
                "不得放置第二组信号数字)"
            )
    s3 = "\n".join(
        re.findall(r"^### ③.*?(?=^#{2,3}(?:[^\S\n]|$)|\Z)", scan_text, re.M | re.S)
    )
    if not s3:
        problems.append("数字终核: scan JSON 含 signals 但报告缺 ③ 段可绑定信号行")
        return
    all_labels = [lb for _, lb in _SIGNAL_SPECS]
    for key, label in _SIGNAL_SPECS:
        sig = signals.get(key)
        if not _verify_signal_schema(key, sig, problems):
            continue
        # ⛔ R3 round-18 (冻结审查 §一.3 raw 专用绑定): 原实现在 **raw** 行上
        # 找 label 选行 ⇒ 保留一条合规行, 再加一条**渲染等价但 label 被
        # 切开**的冲突行 (`来源**覆盖**率：99/3…` / `来源<b>覆盖</b>率：99/3…`),
        # 后者根本进不了「逐条全查」—— 两条实测 exit 0 放行。
        # 零宽切开的形态被全文零宽门拦下, 但排版标记/HTML 标签没有那道门。
        # ⇒ 选行与后续校验全部改在 _visible_text() 上: **读者看到的那一行**
        #   才是判据对象 —— 与 D2/fallback 两条主链同一个文本空间。
        lines = [v for v in _visible_block(s3).splitlines() if label in v]
        if not lines:
            problems.append(f"数字终核: ③段缺信号行 {label}")
            continue
        avail = sig.get("availability")
        for line in lines:
            # H3 (Codex round-2): 每行只许承载一个信号 — 四信号合并成一行时,
            # "首个数字匹配 + 整行任意位置找档位" 会让档位互相借用而放行。
            if sum(1 for lb in all_labels if lb in line) > 1:
                problems.append(
                    f"数字终核: 信号行合并了多个信号 (每信号必须独占一行): {label}"
                )
                continue
            if avail == AVAIL_NODATA:
                # H2 (round-2 → round-5 结构性终结): "禁数字字符" 是打不完的
                # 长尾 (全角/汉字大小写/仨/皕/Arabic-Indic/上标/罗马/分数…),
                # 且「零/零」这类还与自然表述冲突。改为**整行固定模板白名单**:
                # 无据行必须整行等于 `- <信号名>：无据（<白名单原因>）`,
                # 原因只能从 _NODATA_REASONS 里挑 —— 无从夹带任何数字。
                strict_nodata = (
                    rf"^[>\s\-*·]*{re.escape(label)}[：:]\s*无据\s*[（(]\s*"
                    rf"(?:{'|'.join(re.escape(x) for x in _NODATA_REASONS)})"
                    rf"\s*[）)]\s*$"
                )
                if not re.match(strict_nodata, line):
                    problems.append(
                        f"数字终核: 信号 {label} 无据行未整行匹配标准式 "
                        f"(须为『无据（<固定原因>）』, 原因取自: {'/'.join(_NODATA_REASONS)})"
                    )
                continue
            if "无据" in line:
                problems.append(f"数字终核: 信号 {label} 有数, 报告行却标了无据")
                continue
            # H3 (round-3 收紧): **整行**必须严格等于本信号的标准式 —
            # 原先"首个数字匹配 + 档位出现过"允许在正确串之后追加
            # "99/99【实测】"这类第二组数字而照样 PASS。这里改为整行
            # fullmatch: 行 = 前缀装饰 + 标准式 + 档位标注, 其后不许有任何
            # 非空白残留 (词表竞赛就此打住, 结构说了算)。
            pr = sig.get("percentile_ref") or {}
            if key == "unanswered_question_age":
                # round-4 新增 FAIL: percentile_ref 为 null 时原先会渲染成
                # "p25/p50/p75 = None/None/None" 且照样匹配 → schema 侧已要求
                # 有数档必须有 dict 分位, 这里再兜一层
                if not isinstance(sig.get("percentile_ref"), dict):
                    problems.append(
                        f"数字终核: signals.{key} 有数档但 percentile_ref 不是对象"
                    )
                    continue
                body = (
                    rf"{re.escape(label)}[：:]\s*最老\s*{sig['value']}\s*天\s*"
                    rf"[（(]\s*参与统计\s*{sig['denominator']}\s*条[，,]\s*"
                    rf"p25/p50/p75\s*=\s*{pr.get('p25_days')}/{pr.get('p50_days')}"
                    rf"/{pr.get('p75_days')}\s*天\s*[）)]"
                )
            else:
                # ⛔ 维护卡 B · H-3: 尾部原为 `(?P<tail>[^【】]*)` —— **先开放再排除**
                # (排除数值字符与 `/` 形态)。复核者的判词是对的: 那"本质仍是黑名单",
                # 实测「另有仨条」照样放行 (生僻量词不在任何表内且无 `/`)。
                # 而尾部本来就是**固定文案** (SKILL Step 5 模板逐字规定), 所以改成
                # 正向允许式: 只许这三句之一, 锚 `$`。字符层攻防到此结束 ——
                # 「仨/皕/零」这类生僻写法不需要被逐个枚举, 它们进不来。
                tail = _SIGNAL_TAILS.get(key)
                if tail is None:  # 新增信号必须在 _SIGNAL_TAILS 里登记尾部文案
                    problems.append(
                        f"数字终核: 信号 {label} 未登记标准尾部文案 (verifier 无法整行校验)"
                    )
                    continue
                body = (
                    rf"{re.escape(label)}[：:]\s*{sig['value']}\s*/\s*"
                    rf"{sig['denominator']}\s*{re.escape(tail)}"
                )
            # 行首前缀白名单: 引用符/列表符/单空格间隔 — ⛔ 不允许四空格以上
            # 缩进 (缩进代码块形态, round-5: 不再靠 _strip_code_blocks 剥它)
            # CARD-维护B-R2 (e): body 与档位之间插入**可选注记槽** — 注记只许逐字
            # 取自 _SIGNAL_TAIL_NOTES（封闭表 alternation, 槽至多出现一次）,
            # 可紧接或以 ·/，/,/、 与标准尾部分隔。四条信号行统一适用;
            # 无据行不适用（其整行模板在上方, 未插槽）。
            note_slot = (
                rf"(?:\s*[·，,、]?\s*"
                rf"(?:{'|'.join(re.escape(x) for x in _SIGNAL_TAIL_NOTES)}))?"
            )
            strict = (
                rf"^(?! {{4}}|\t)[>\-*·\s]{{0,6}}{body}{note_slot}"
                rf"\s*【{re.escape(str(avail))}】\s*$"
            )
            m = re.match(strict, line)
            if not m:
                problems.append(
                    f"数字终核: 信号行 {label} 未整行匹配标准式 "
                    f"(数字/档位/尾随内容任一不符即 FAIL)"
                )
            # ⛔ 维护卡 B · H-3: 这里原有一段"尾部禁数值字符 + 禁 X/N 形态"的**黑名单**
            # 后置检查 (round-4→round-5 的字符表路线)。现已**整体删除** —— 尾部改成
            # 正向允许式后, 任何非标准尾部在上面的整行 fullmatch 处就已经 FAIL,
            # 这段检查恒不触发, 留着只会让人以为字符表还在承重
            # (「口径一致」早年的字符表误伤也随之消灭, 见 (e) 注记槽)。


def _SECTION_RE(section: str) -> str:
    """段落标题的**唯一**匹配口径 (round-6 BLOCKER 同源修复)。

    段名之后只允许两种形态: 直接行尾, 或全角括号补充 (模板自带的
    `## 台账（种子/排生）`、`## 本段新增（上次回顾 → 现在）`)。
    ⛔ 存在性检查与下游定位**必须共用本函数** —— 两处口径一旦不同,
    就会出现"算在场却定位不到"的缝隙, 让整块数字绑定被静默跳过。
    """
    return rf"^{re.escape(section)}(?:[^\S\n]*$|（[^\n]*$)"


def _verify_signals_if_present(text: str, scan: dict, problems: list[str]) -> None:
    """signals 绑定入口 (round-6 BLOCKER: 从 _verify_numbers 尾部提出来)。

    旧 scan JSON (无 signals 键) 兼容跳过; 键存在但形状非 dict = 被动过
    手脚, fail-closed。⛔ 本函数必须在 _verify_numbers 的**每条**返回路径上
    被调用 —— 原实现把它放在函数尾部, 前面任何 early return 都会连带跳过
    整块信号绑定 (「AI 侧对账」标题加后缀即可触发)。
    """
    if "signals" not in scan:
        return
    signals = scan.get("signals")
    if isinstance(signals, dict):
        _verify_signal_lines(text, signals, problems)
    else:
        problems.append("数字终核: scan JSON signals 键存在但形状损坏 (非对象)")


# ⛔ Codex round-1 BLOCKER-3: 原式要求「批注 N 条」后**直接行尾**, 于是真实 manifest
# 台账行 (`- cs-61b-csm — 批注 2 条；未派生…· mastery 0.3…`) 根本不匹配 → 被 continue
# 跳过 → 把 2 改成 999 照样 exit 0。**门在真实语料上完全不生效**, 而放行门只证明了
# "真报告 PASS", 没证明"真报告被篡改后 FAIL" —— 这正是假绿的经典形态。
# 现在: 数字后允许 SKILL 明确允许的后续字段 (`；…` / `· …`), 只锚到分隔符。
_SEED_LEDGER_LINE_RE = re.compile(
    r"^[>\s]*-\s+(?P<node>\S.*?)\s+—\s+"
    r"(?:批注\s*(?P<n>\d+)\s*条|(?P<none>无批注))"
    # ⛔ R3 round-25（冻结审查 v6 + 真实报告实测）：`rest` 原先只接受以
    #   `；/;/·` 开头的尾巴，而**线上真实报告**的尾巴是 `（理解度未闭环 3 条）；…`
    #   —— 以全角括号开头 ⇒ 整条不匹配 ⇒ 走 `continue` **静默跳过、从未绑值**。
    #   也就是说这道"绑值"检查在真实数据上一直没生效。放宽 rest 的起始字符集，
    #   让它们真正进入绑定（覆盖面**扩大**，不是放松）。
    #   ⚠️ rest 内部仍是 `.*`，尾巴里再写一个数不受本绑定管 —— 如实登记。
    r"(?P<rest>\s*[（(【\[；;·].*)?\s*$"
)

# ── CARD-维护B-R2 (d): fallback 派生允许式（从 _verify_report 局部提为模块级） ──
# 行为与原局部 tuple 逐条等价（纯搬家）, 除 ⑦ 及其同句式 ⑧ 的 D3 收紧（见行内注）。
# 每条附「依据」元数据, 由 d2 绑定结构门逐条验证——依据必须真实存在:
#   scan:<路径>          collect 产物 JSON 里可解析到的真实字段
#   md:heading           Markdown 标题结构（模式必须以 ^#{1,6} 起）
#   skill:action-verb    SKILL HARD-CONSTRAINTS 白名单动词句（含 Cmd+Shift+D）
#   skill:③段固定句式    SKILL.md ③段模板（:267 无来源结论信号行）与叙述句式
#                        （:203「N 个派生成员缺来源锚点」——语义锚, 非逐字）
# ⛔ 新增条目必须带上表内可验证的依据; 无依据可写的允许式（如「备注：…派生」
# 自由叙述）会被 d2 结构门与 d1 行为门双向拒绝（S4 survivor 的承重防线）。
# ⛔ R3 round-11: 数词/定界集**上移**到 _FALLBACK_DERIVE_ALLOW 之前 ——
# ⑦⑧允许式的尾段数字禁令原先手抄了一份数词集, 与定界集分叉 55 个字符
# (廿卅仨俩壹贰… / 带圈数字 / 苏州码), 写进③段固定句式尾段即可绕过禁令。
# 上移后两式直接引用 _NUMERAL_LIKE_CHARS, 副本消失。
_CJK_NUM = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_CJK_UNIT = {"十": 10, "百": 100, "千": 1000, "万": 10000, "亿": 100000000}
# ⛔ R3: 提取字符类**由两张表机械派生**, 不再手抄字面量。
# 判据 (`_cjk_single_to_int`) 只认 `_CJK_NUM` 单字; 提取面必须是
# `_CJK_NUM ∪ _CJK_UNIT` 的**超集方向** —— 抓得到才拒得掉:
# 提取面漏掉某个数词字, 该字组成的串会落到检查面**之外** = 漏拦 (不是
# fail-closed)。两处消费点 (D2 叙述段 / fallback 允许式) 共用本常量,
# 手抄两份字面量正是它们此前分叉的成因。
_CJK_NUM_CHARS = "".join(sorted(set(_CJK_NUM) | set(_CJK_UNIT)))
# ⛔ R3 round-2: 数串必须**跨连接字符**整体抓取 —— 原 `[...]+` / `[...]{1,12}`
# 遇到 `九十八万**五` 会断开, 匹配重锚到尾片 `五` 并按 5 查池 (实测 exit 0)。
# 单一来源: 两个消费点 (D2 叙述段 / fallback 允许式) 共用本模式。
# `*+` possessive: 连接字符集与数词字集**不相交**, 贪婪吞完即可, 无需回溯 ——
# 同时杜绝嵌套量词的病态回溯。
# ⛔ R3 round-3 (Codex round-2 四条 HIGH, 车道逐条实测复现): 取数**不能按字符类
# 分成两条循环**。原实现 CJK 一条、ASCII 一条, 于是**跨类**或**表外**的数词字
# 成了断点, 匹配重锚到尾片:
#   · `本板共有九十八万5个子节点`  → CJK run 停在 `万`, ASCII 只取 `5` ⇒ exit 0
#   · `本板共有廿五个子节点`        → `廿` 表外, 从 `五` 重锚按 5 查池 ⇒ exit 0 (读者读 25)
#   · `本板共有壹佰个子节点`        → 两字全表外, **一个 token 都抽不出** ⇒ exit 0
#   · fallback `#### 派生子女 1 000 个` → `\d+` 拆成 [1, 000] 逐片碰池 ⇒ exit 0
# ⇒ 合并为**一条规则**: 用「数词样字符」的**宽集合**取整串 → 剥连接字符 →
#   只有「全 ASCII 数字」或「表内单字数词」才给值, 其余一律 fail-closed。
#   宽集合只用于**定界**(判断哪些字符属于同一个数), 不赋任何值 —— 表外字符
#   进来只会让整串变得"无法确定", 不会被猜成某个数。
# 表外中文数词按常用面登记 (仍是**封闭表**, 与量词表同口径): 廿卅卌 + 大写金融
# 数字 + 异体。加它们**只增加拒绝面**, 不增加放行面。
# ⛔ R3 round-5 (Codex round-4 HIGH-6): 漏 `兆京垓秭穰` 等大数单位 ⇒
# `九兆五个` 会从 `五` 重锚按 5 查池（与此前判 HIGH 的 `廿五` **同机制**）。
# 定界集只定界不赋值, 加字符**只增加拒绝面**、不增加放行面。
# ⛔ R3 round-9 (Codex round-7 HIGH-3): 补带圈数字 ①-⑳ / 全角旧式 〡〢〣 等
# **可见数字**字符 —— 它们不在定界集时 D2 与 fallback **一个 token 都抽不出**,
# 整句零校验(比尾片重锚更彻底)。仍是**封闭表**, 如实登记。
_CJK_NUM_EXTRA = (
    "廿卅卌壹贰貳叁參参肆伍陆陸柒捌玖拾佰仟萬亿億两兩兆京垓秭穰仨俩"
    "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
    "〡〢〣〤〥〦〧〨〩〸〹〺"
)
_NUMERAL_LIKE_CHARS = "".join(
    sorted(set(_CJK_NUM_CHARS) | set(_CJK_NUM_EXTRA) | set("0123456789"))
)

_FALLBACK_DERIVE_ALLOW: tuple[tuple[re.Pattern[str], str], ...] = (
    # ① 规模自陈行 — counts.derived
    # ⛔ 维护卡 B · H-2: 原式**缺 `$`**, 而 `p.match()` 只认前缀 —— 于是在
    # 一条完全正确的规模行**尾部追加**任意文字 (实证:「，SeedA 的派生子女
    # 共有仨个」) 仍然 match 成功、照样 PASS。现按模板补全整行并锚 `$`:
    # 五元组之后只许是 `/ N 批注` 与可选的行尾 `/`。
    (
        re.compile(
            r"^[>\s]*\d+\s*成员（\d+\s*种子\s*\+\s*\d+\s*派生，\d+\s*占位）"
            r"\s*/\s*\d+\s*批注\s*/?\s*$"
        ),
        "scan:counts.derived",
    ),
    # ② 任意层级的段落标题 (## 台账（种子/派生） / ### 派生)
    (re.compile(r"^#{1,6}[^\S\n].*$"), "md:heading"),
    # ③ 无来源结论信号行 — signals.unsourced_conclusions (分母=派生角色数)
    (
        re.compile(r"^[>\-*·\s]{0,6}无来源结论[：:].*【.+】\s*$"),
        "scan:signals.unsourced_conclusions",
    ),
    # ④ 无来源结论**无据**行 — 白名单文案「本板无派生角色成员」含该词
    (
        re.compile(r"^[>\-*·\s]{0,6}无来源结论[：:]\s*无据\s*[（(][^\n]*[）)]\s*$"),
        "scan:signals.unsourced_conclusions",
    ),
    # ⑤ 关系类型分布行 — counts.relation_types
    (re.compile(r"^[>\-*·\s]{0,6}关系类型分布[：:].*$"), "scan:counts.relation_types"),
    # ⑥ SKILL HARD-CONSTRAINTS #3 的白名单动作句 (含「Cmd+Shift+D 派生」)
    #    ⛔ round-6 终裁复核: 漏掉它曾让**按 SKILL 逐字写的合法报告**FAIL
    (re.compile(r"^\s*\d+\.\s.*Cmd\+Shift\+D.*派生.*$"), "skill:action-verb"),
    # ⑦ ③段定量叙述 — CARD-维护B-R2 D3 收紧: 谓语绑定「缺来源锚点」
    #    (SKILL.md:267 信号行模板 / :203 叙述句式的语义锚), 且尾段禁裸数字。
    #    原式 `派生角色成员[^。\n]*` 的自由段放行过
    #    「派生角色成员的子女数为 987654 个。」(同族缺口, (a) 重放实证)。
    #    ⛔ round-3 HIGH-5: 尾段数字禁令从 ASCII 扩到**全角 + 中文数词**
    #    (`９８７６５４` / `九十八万` 实测曾放行); 前置 N 的**值绑定**在
    #    _verify_fallback_derive_numbers (正则层管不到值)。
    #    live 4 份 fixture 实测**零命中**「派生角色成员」(全为 manifest 报告,
    #    本检查是 fallback 专属), 收紧无 live 正例可伤。
    (
        re.compile(
            rf"^[>\s]*(?:\d+\s*个)?派生角色成员缺来源锚点[^。\n0-9０-９{_NUMERAL_LIKE_CHARS}]*。?\s*$"
        ),
        "skill:③段固定句式",
    ),
    # ⑧ 同句式「集中在」变体 — 与 ⑦ 同步收紧两侧尾段禁数字 (含全角/中文数词)
    #    (否则「优化集中在派生角色成员的 987654 个子女上」同型放行)
    (
        re.compile(
            rf"^[^。\n0-9０-９{_NUMERAL_LIKE_CHARS}]*集中在派生角色成员"
            rf"[^。\n0-9０-９{_NUMERAL_LIKE_CHARS}]*。?\s*$"
        ),
        "skill:③段固定句式",
    ),
)

# ── 维护卡 B · D2「有据叙述域」 ────────────────────────────────────────────
# ⛔ Codex round-1 HIGH「D1 仍只是少量枚举，不是卡文声明的整域绑定」的整改:
# 原实现是**点名两段**的允许式 (`("你现在可以做的", "三维审查")`) —— 于是
# 规模 callout 的「1 次调用」、台账派生行、AI 侧对账段其余数字、新增的 `## 附录` 段
# 全都在域外, 实测逐条 exit 0。那不是"域", 那是"几个段名 + 几条正则"。
#
# 现在倒转成**默认全域 + 显式例外**(default-deny): 报告正文的每一段都在 D2 里,
# 只有下面这张表里的段落显式出域。新增段落 (附录/脚注/任何自造标题) 默认**进域**,
# 这才符合治理域裁定"按位置划分"的本意 —— 加一个标题就能逃出治理, 才是漏。
_D2_EXEMPT_SECTIONS = (
    # 纯取数元信息: 哈希前缀 / mtime / manifest lag / 扫描时刻。这些值的形态自带
    # 单位或由 E4 时间豁免覆盖, 且不是"报告对材料的陈述"。
    "数据来源与新鲜度",
)
# 计数形态: 数字 + 中文量词。⛔ 只认**量词紧随**的数字, 不是"段内所有数字" ——
# mastery 0.3 / 量表 1-4 / p25/p50/p75 这类带自己单位或形态的值不在其中,
# 误伤面因此小得多。量词表按 live 真报告实际出现的形态扩充 (板/项/篇/道/张),
# 每扩一个都由 live 放行门实测把关。
# ⛔ 三处收紧, 全部由对抗审查实测驱动 (每条都在四份真报告上验过):
#  ① **数字与量词之间的排版噪声**: 原式前瞻只容 `\s`, 于是加粗 `**987654** 个`、
#     `<span>987654</span> 个`、`987654&nbsp;个` 一律漏检 —— 而加粗数字正是 LLM
#     写报告的常见排版, 这既是绕过面也是静默漏检面。现在容忍 * _ ~ 反斜杠、
#     HTML 标签、`&nbsp;`/`&#160;` 实体。
#  ② **小数前缀**: `(?<![0-9.])` 的本意是不切开小数, 实际效果是"任何数字前面补一个
#     `0.` 就退出治理"。改为只在**紧邻**数字时排除 (即真正的小数尾部), 且对
#     `0.987654 个` 这种整体形态改由下面的 _D2_DECIMAL_RE 单独识别。
#  ③ 量词表保持封闭 —— 这是**如实登记的边界**, 不假装"位置承担了一切":
#     中文数字与表外量词仍不在覆盖面 (见验收单裁决点)。
# 噪声集含反引号: `` `987654` 个 `` 里的收尾反引号也是"数字与量词之间的排版噪声"
# （可见计数 code span 已由 _blank_inline_code 有意保留下来交给这里判）。
_D2_NOISE_ONE = r"(?:[*_~\\`]|<[^>\n]{1,20}>|&nbsp;|&#160;|[多余来几约近超]|\s)"
_D2_NOISE = rf"{_D2_NOISE_ONE}*"
# ⛔ R3 round-2 (车道对抗审查 BLOCKER, 5 个镜头独立收敛 + 本地实测复现):
# 噪声**不只出现在数与量词之间, 也能被塞进数串内部**。原提取式只有右侧量词
# 前瞻, 于是 `本板共有九十八万**五**个子节点` (Markdown 粗体, **渲染出来就是
# 「九十八万五个」**) 的匹配重锚到尾片 `五`, `_cjk_single_to_int("五")==5` 且
# 5 在池内 ⇒ 纯虚构的 980005 **exit 0 放行**。ASCII 侧同形: `980 005个`
# (空格千分位) 只查到 `005`。round-5 的「按局部值查池」并没有被消除, 只是
# 从**解析器**搬到了**提取器** —— 判据拿到的 token 不是那句话里的数。
# ⇒ 数串必须**跨噪声整体抓取**, 剥掉噪声后再交判据 (见 _join_free)。
# 不可见/零宽字符与排版标记同罪: 渲染后读者看不到, 却能在源码里切断数串。
# ⛔ R3 round-8 (Codex round-6 HIGH-5): 补 U+2066-2069 bidi isolate ——
# 与 U+202A-202E 同族, 渲染不可见却能改变阅读顺序/切断数串。
_INVISIBLE_ONE = r"[\u00ad\u200b-\u200f\u2028\u2029\u202a-\u202e\u2060-\u2069\ufeff]"
_D2_JOIN_ONE = rf"(?:{_D2_NOISE_ONE}|{_INVISIBLE_ONE})"
_D2_JOIN_RE = re.compile(_D2_JOIN_ONE)


def _join_free(s: str) -> str:
    """剥掉数串内部的排版噪声/不可见字符, 还原成**不被排版切断**的数串。

    ⚠️ 措辞收窄 (Codex round-2 属实指出): 原写"还原读者**看到**的那个数"过宽 ——
    连接集里未配对的 `*`/`_`/`~`、`<br>` 这类短标签、修饰字 `[多余来几约近超]`
    渲染后是**可见**的, 拼起来并不等于读者看到的数 (`1*0个` 会被当成 10)。
    ⛔⛔ **这里曾写「那是安全向的过度拼接: 查到的值 ⊇ 读者看到的数」—— 已被
    Codex round-7 证伪, 车道实测确认**: `本板共有1\\*5个子节点` 渲染出来是可见的
    `1*5个`, 而实现先删 `*`、再把反斜线当连接字符剥掉, 最终把 **15** 送进池;
    15 恰好在池内 ⇒ **放行**。池含 15 并不能证明读者看到的 `1*5` 或其中任何一个
    数有出处。同理 `5多个` 是近似计数, 却按**精确 5** 入池。
    ⇒ 过度拼接**不是保值关系**, 它是一个**已知的 fail-open 面**, 不是安全边界。
    本卡未改变该行为(改成 fail-closed 会波及大量当前合法形态, 需单独裁决),
    **但不再声称它安全** —— 如实登记在验收单 §五之三。
    """
    return _D2_JOIN_RE.sub("", s)


# ⛔ 这里曾写过一个"左边界守卫"(匹配左侧跳过连接字符若仍有同类数字字则判无法
# 确定)。**实测它永不触发**: 数串已跨连接字符整体抓取, 能被守卫命中的形态都
# 先被 run 模式吞掉了; 而连接集**表外**字符 (`九十八万x五个`) 又不满足守卫条件。
# 一个永不执行的分支正是 round-5 判过的病 (死代码冒充防线), 故删除而非保留。
# 残余面如实登记: 连接集是**封闭表**(与量词表同口径), 表外字符仍能切断数串 ——
# 但那类断点在**渲染后可见**, 读者不会读成一个连续的数; 表外的**不可见**
# 字符 (如超长 HTML 注释) 是真残余, 记在验收单 §五之三。
# ⛔ 量词表按对抗审查给的 21 个常用表外量词扩充 (原 11 字表实测被
# 「名/位/台/件/册/组/批/轮/遍/趟/人/句/行/段/点/种/类/本/页/题/章」整域绕过)。
# 这仍是**封闭表**——如实登记的边界, 不宣称"位置承担了一切"。
# ⛔ R3 round-5 (Codex round-4 HIGH-7): 表漏 `层/节/列/枚/步/级/则/回/幕/维`
# ⇒ `本板共有987654层关系` 整句**零校验**。补入常用计数量词。
# 仍是**封闭表**(与定界集、数词表同口径, 如实登记, 不宣称覆盖全部量词)。
_D2_QUANT = r"[个条块次份处板项篇道张名位台件册组批轮遍趟人句行段点种类本页题章层节列枚步级则回幕维门套对场部只支株棵笔封片卷格轮次例束艘架间]"
# ⛔ R3 round-3: 原 `_D2_COUNT_RE`(ASCII 专用取数式) 与 `_CJK_NUM_RUN_*`(CJK 专用)
# 已**合并**为 `_COUNT_BEFORE_QUANT_RE` / `_NUM_RUN_RE`(见 _NUM_RUN_PAT 处)——
# 按字符类分成两条循环正是「跨类/表外字符成为断点」的成因。两者删除而非保留:
# 只剩定义、无生产调用的常量就是死代码, 而死代码冒充防线是本卡在审的那种病。
# D2 的**适用句式**: 只查明确自称"全板/整体规模"的断言。
# 判据从"值在池里"(碰撞) 换成"句式 + 值"(绑定) —— 这类句子的数字必须来自 scan,
# 而普通叙述 (引用原话 / 序数 / 自指 / 同义量词) 不再被牵连。
# 小数形态的计数 (`0.987654 个`): 整体取出, 小数点前后都不该成为免检通道。
_D2_DECIMAL_RE = re.compile(rf"[0-9]+\.[0-9]+{_D2_NOISE}(?={_D2_QUANT})")
# 时间形态豁免 (E4): 先把它们挖空, 免得 "2026-08-27" 里的片段被当计数。
_D2_TIME_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?"
    r"|\b\d{1,2}:\d{2}(?::\d{2})?\b"
)
# ⛔ E2 收窄 (对抗审查实测): 原式挖空**任意**行内代码, 于是
# `` 本板共有 `987654` 个子节点 `` 整段免检 —— 而它的渲染结果与裸写等价地在向读者
# 断言一个计数。行内代码的正当豁免是"命令/路径/字段名示例", 那些**不是纯数字**。
# 故只豁免不含裸计数的 code span; `` `987654` `` 这种纯数字跨度不再豁免。
# ⚠️ 第一版把负前瞻写成"跨度**内部**不含量词"，但量词恰恰在跨度**外面**
# （`` `987654` 个子节点 ``），于是它照样被挖空。判据应当是"跨度内容不是**纯数字**"。
# ⛔ 再收一次 (对抗审查 MEDIUM): 把**量词**单独包进反引号 (``987654 `条` ``) 时,
# 挖空量词会让前面的数字失去锚点而免检。故纯数字**与**纯量词的 code span 都不豁免。
# ⛔ R3 round-11 (Codex round-8 HIGH-1): 这里原先**手抄**了一份量词表, 且停在
# `章` —— 主表 _D2_QUANT 后来扩到 63 字, 副本没跟, 于是把 `例` 单独写成 code span
# 就能把量词锚点挖空。**改为从 _D2_QUANT 机械派生**: 一个原则只有一个应用点,
# 这正是本卡反复证明的那条 (判据分叉/双循环/顺序耦合都是同一个病).
# ⛔ R3 round-14 (冻结审查): 数字部分原先仍手写 `[0-9]+` —— 我上一轮只派生了
# **量词**部分, 「副本已消除」只对了一半。于是 `` `九十八万个` ``、`` `987654 个` ``
# 这类**完整可见计数**写进 code span 会被整体挖空、整域免检。
# 数字部分改为派生自 _NUMERAL_LIKE_CHARS(定界集), 与取数同源。
# 「纯计数」= 只由数词样字符 / 量词 / 空白组成 —— 这类 code span 是**可见计数**,
# 不该按「字段值」豁免掉。合并成一个否定前瞻。
_D2_COUNTISH_CHARS = _NUMERAL_LIKE_CHARS + _D2_QUANT.strip("[]")
# ⛔ R3 round-17 (冻结审查 §一.2): 上一版是**正则否定前瞻**, 判据作用在 **raw**
# code span 上 —— 而它跑在 `_visible_text` / `_normalize_number_seps` **之前**。
# 于是 `` `-5` 个``、`` `5.5个` ``、`` `1,005个` ``、`` `５个` `` 里的符号/小数点/
# 千分位/全角数字都不在 _D2_COUNTISH_CHARS 里 ⇒ 前瞻失败 ⇒ 整段按"字段值"挖空,
# 后续所有数值门都看不见它们（四条实测放行）。这是**又一处顺序耦合**, 与本卡
# 已修的三处同型（wikilink 挖空早于归一 / fallback 白名单判在源码行 / 千分位）。
# ⇒ 改为**先归一再判**的函数式替换: 判据看的是读者渲染后看到的内容。
_D2_CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
# 计数里可以合法出现、但不属于"数词样字符"的附属符号（符号/小数点/分隔符）。
# ⛔ round-20 (冻结审查 v2 §四.2): 这张表与**区间主表**再次分叉 ——
#    区间分隔符 `~～〜到至—–` 不在其中, 于是 `` `2~3个` `` / `` `999~999个` ``
#    这类**可见区间**被当字段值整段挖空, 区间门与普通数字门**都不可达**
#    (两条实测放行)。空白也只列了普通空格与 tab, 而主连接集用的是 `\s` ——
#    code span 内的 NBSP 同样让整段被豁免(第三条实测放行)。
#    ⇒ 分隔符与区间主表同源; 空白改用 str.isspace() 判(覆盖 NBSP/全角空格)。
_D2_RANGE_SEPS = "~～〜-－−‑—–到至"
_D2_COUNTISH_EXTRA = "-−－‑﹣负.．,，'’" + _D2_RANGE_SEPS


def _codespan_is_visible_count(inner: str) -> bool:
    """code span 的**渲染后**内容是不是一串可见计数（而非字段值）。

    要求至少含一个数词样字符 —— 否则 `` `-` `` / `` `.` `` 这种纯符号 span
    会被当成计数, 白白失去 E2 豁免。
    """
    norm = _normalize_number_seps(_visible_text(inner)).strip()
    if not norm:
        return False
    if not all(
        ch in _D2_COUNTISH_CHARS or ch in _D2_COUNTISH_EXTRA or ch.isspace()
        for ch in norm
    ):
        return False
    # ⚠️ 至少要有一个"数词样字符或量词" —— 纯符号 span（`` `-` `` / `` `.` ``）
    #    不是计数, 白白失去 E2 豁免。但**纯量词**（`` `个` ``）必须算:
    #    挖掉单独成 span 的量词会让它前面的数字失锚（round-11 修过的缺陷,
    #    第一版这里写成"至少一个 _NUMERAL_LIKE_CHARS"当场把它重新引入, 被 r12 门抓住）。
    return any(ch in _D2_COUNTISH_CHARS for ch in norm)


def _blank_inline_code(mm: "re.Match[str]") -> str:
    """字段值 span 整段挖空; 可见计数 span **只挖掉反引号**, 内容留给数值门。

    ⚠️ 只挖反引号（而不是原样保留）: 反引号**在**连接字符集 `_D2_NOISE_ONE` 里,
    所以量词锚本身不会因它失效 —— 原注释称"反引号不在连接集"是**事实错误**
    (round-20 冻结审查 v2 指出)。保留这个做法的真实理由是**语义**: 判定为可见
    计数的 span, 其反引号只是排版, 读者看到的就是里面的数; 挖掉它让后续所有
    判据面对的文本与读者一致, 不必依赖"反引号恰好也算连接字符"这个巧合。
    等长替换, 行内偏移不变。
    """
    span = mm.group(0)
    if _codespan_is_visible_count(span[1:-1]):
        return " " + span[1:-1] + " "
    return " " * len(span)


# ⛔ E3 同理: wikilink 的**别名显示文本**是读者看得见的正文
# (`[[节点/x|本板共有 987654 个子节点]]` 渲染出来就是那句话)。只豁免**目标部分**,
# 别名部分留给 D2 校验。
# ⛔ R3 round-6 (Codex round-5 HIGH-8): 只在**有别名**时挖空目标 ——
# 无别名的 `[[987654]]` 里, 目标本身就是读者看到的显示文本, 挖掉它等于把
# 可见计数藏起来。无别名形态交给 _visible_text() 还原成显示文本。
# ⛔ R3 round-8: _D2_WIKILINK_RE 已删除 —— 移出豁免链后只剩定义、无生产调用,
# 就是死代码; wikilink 两种形态现由 _visible_text() 取显示文本。
_D2_ORDERED_LIST_RE = re.compile(r"^(\s*)\d+\.(\s)", re.M)
# E6b · SKILL 模板里**逐字规定的固定短语**, 其中的数字是模板常量而非从数据算出的计数。
# ⛔ 实测发现: 域倒转成 default-deny 后, live「递归与分治」报告的
# `- 最老 3 条原话：无（tips_total 为 0）` 被误判 —— 那个 3 来自 SKILL.md:255 的模板
# 「最老 3 条原话（added_at = …）」, 板上只有 0 条 tips 时它当然在 scan 里找不到同值。
# 正向允许式: 只豁免这张表里的**逐字**短语, 不是"凡是像模板的都放行"。
_D2_TEMPLATE_CONSTANTS = ("最老 3 条原话",)
# ⛔ R3 round-4 (Codex round-3): 原式手抄了**旧的 11 字**量词表, 与已扩到 34 字的
# _D2_QUANT 分叉 —— 表外量词的区间根本不被识别为区间。改为共用 _D2_QUANT。
# ⛔ R3 round-5 (Codex round-4 HIGH-2): 原式是**裸 ASCII 窄路径**, 不复用
# 数串/连接字符 —— `本板共有987654<b>-</b>0个…` 渲染成同一个区间, 却整条不匹配,
# 于是只按右端 `0` 入池; 中文/混写端点同理。改为共用 _NUM_RUN_PAT 与 _D2_JOIN_ONE。
# ⚠️ 定义位置在 _NUM_RUN_PAT 之后(见文件下方), 故此处只留占位说明, 实体见 :RANGE。


def _scan_number_pool(obj, pool: set[int]) -> None:
    """递归收集 scan JSON 里的**数值型**整数 —— D2 的「有出处」判据。

    ⛔ Codex round-1 HIGH: 原实现**也从字符串里抽整数**, 于是池被哈希与用户原话
    污染 —— 实测「544 个子节点」通过 (544 只来自 board_sha256 的片段)、
    「111 个子节点」通过 (111 只来自用户作答原话)。池越脏, "有出处"越没意义。
    现在只收 JSON 的**数值类型**; 字符串里真正该被绑定的量 (日期/哈希/原话)
    要么由 E1-E6 豁免, 要么本来就不该被当成本报告的计数陈述。
    """
    if isinstance(obj, bool):
        return
    if isinstance(obj, int):
        pool.add(obj)
    elif isinstance(obj, float):
        if obj.is_integer():
            pool.add(int(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            _scan_number_pool(v, pool)
    elif isinstance(obj, list):
        for v in obj:
            _scan_number_pool(v, pool)


_FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


def _derived_number_pool(scan: dict) -> set[int]:
    """scan 数值池 (排除 scale_gate 常量, 含一阶和差) — D2 与 fallback
    允许式数字绑定 (round-3 HIGH-6) 共用的「有出处」判据。

    ⛔ 池必须排除**与板内容无关的源码常量** (scale_gate 的 30/100/10) 与
    字符串污染; 「有出处」≠「字面出现」: 池含一阶和与差 (合法算术, 如
    「7 个派生点中仅 2 个带 derived_at……其余 5 个无据」的 5=7−2)。
    代价如实记: 池变大 ⇒ 对小数值拦截力下降 (罕见大数仍拦得住)。
    """
    scan_for_pool = {k: v for k, v in scan.items() if k != "scale_gate"}
    base: set[int] = set()
    _scan_number_pool(scan_for_pool, base)
    pool = set(base)
    ordered = sorted(base)
    for i, a in enumerate(ordered):
        for b in ordered[i:]:
            pool.add(a + b)
            pool.add(abs(a - b))
    return pool


_NUM_RUN_PAT = rf"[{_NUMERAL_LIKE_CHARS}](?:{_D2_JOIN_ONE}*+[{_NUMERAL_LIKE_CHARS}])*"
_NUM_RUN_RE = re.compile(_NUM_RUN_PAT)

# ⛔ R3 round-6: 定义下移至此 —— 句式门现在引用 _NUMERAL_LIKE_CHARS（定界集），
# 与取数**同源**；原位置在定界集之前，会前向引用。
_D2_CLAIM_RE = re.compile(
    r"(?:本板|全板|该板|这块板|整体)[^。；\n]{0,12}?(?:共有|共|总共|合计|一共|有)"
    # ⛔ R3 round-6 (Codex round-5 HIGH-2): 原式只接受「空白 + ASCII 数字」,
    # 于是 `总计五个子节点` / `总计：987654个` 渲染后是明确自陈却 is_claim=False。
    # 放宽为: 冒号/空白任意, 其后是**任一数词样字符**(定界集, 与取数同源)。
    rf"|(?:共有|总计|合计)[\s：:]*[{_NUMERAL_LIKE_CHARS}]"
)
# 量词前的计数: 整串 + 连接字符 + 量词前瞻。
_COUNT_BEFORE_QUANT_RE = re.compile(rf"({_NUM_RUN_PAT}){_D2_JOIN_ONE}*(?={_D2_QUANT})")
# :RANGE —— 区间式(E7)。端点用与普通计数**同一个** _NUM_RUN_PAT, 连字符两侧
# 容连接字符, 量词共用 _D2_QUANT。端点判值走 _count_token_value(同一判据)。
# ⛔ R3 round-6 (Codex round-5 HIGH-5): 分隔表补 `～〜−‑－`(全角波浪/减号/
# 非断连字符/全角连字符) —— `987654～0个` 原不算区间, 于是只核右端 0。
# 仍是**封闭表**, 如实登记。
# ⛔ R3 round-23（冻结审查 v4）：这里原先**手抄了第二份**分隔表 —— 我 round-20
# 声称"分隔符与区间主表同源"，实际只是 code span 那侧引用了 `_D2_RANGE_SEPS`，
# 区间正则自己仍写死 `[~～〜\-－−‑—–]|到|至`。**声明比证据宽**，第 N 次。
# 现从同一常量机械生成：改一处即两处同步。
_D2_RANGE_SEP_PAT = "(?:" + "|".join(re.escape(c) for c in _D2_RANGE_SEPS) + ")"
_D2_RANGE_RE = re.compile(
    rf"({_NUM_RUN_PAT}){_D2_JOIN_ONE}*{_D2_RANGE_SEP_PAT}{_D2_JOIN_ONE}*"
    rf"({_NUM_RUN_PAT}){_D2_JOIN_ONE}*(?={_D2_QUANT})"
)
# ⛔ CJK 小数形态: `点` 在量词表里 (`3 点建议` 是合法量词用法), 于是
# `五点五个` / `5点5个` 被拆成两个 5 分别碰池, 而读者看到的是 5.5 (实测 exit 0)。
# ASCII 侧早有 _D2_DECIMAL_RE 把小数一律判 FAIL (scan 的计数都是整数),
# 这里补上 CJK/混写形态: 数串 + `点`/`.` + 数串 + 量词 = 小数, 恒 FAIL。
# ⛔ R3 round-4 (Codex round-3 HIGH): 小数点两侧**也可能被连接字符包住** ——
# `987654<b>.</b>0个` 渲染成 `987654.0`, 但原式要求数串与 `[.点]` 直接相邻,
# 两道小数防线全不命中, 普通循环只按尾片 `0` 查池 (实测 exit 0)。
# 小数分隔符同时认半角 `.`、全角 `．` 与中文 `点`。
_DECIMAL_SEP = rf"{_D2_JOIN_ONE}*[.．点]{_D2_JOIN_ONE}*"
# ⛔ R3 round-5 (Codex round-4 HIGH-5): 原式要求分隔符**两侧都有数串**,
# 于是 `.5个` / `．五个` 不命中小数式, 尾片 `5` 照常入池 —— 违反本域
# 「小数计数恒 FAIL」的既有口径。左侧数串改为可选。
_DECIMAL_ANY_RE = re.compile(rf"(?:{_NUM_RUN_PAT})?{_DECIMAL_SEP}{_NUM_RUN_PAT}")
_CJK_DECIMAL_RE = re.compile(
    rf"((?:{_NUM_RUN_PAT})?{_DECIMAL_SEP}{_NUM_RUN_PAT}){_D2_JOIN_ONE}*(?={_D2_QUANT})"
)


# ⛔⛔ R3 round-6 —— 本卡五轮的**共同根因**收口。
# 前五轮每一条 finding 都是同一句话的不同实例: **校验器工作在「源码文本」上, 而
# 威胁定义在「渲染后读者看到的数」上**。`**` / `&nbsp;` / `<b>` / `&#46;` /
# `&#xff19;` / 全角标点 / HTML 实体 / 无别名 wikilink / 长标签……源码到渲染的
# 映射面是**开放集**, 逐个补归一化每轮都会冒出新代表 (HIGH 走势 5→3→7→10)。
# ⇒ 不再逐个补, 改为在**最前面**跑一次 _visible_text(), 把源码推成读者看到的文本,
#    此后所有判据都在**同一个文本空间**里工作。
# 诚实边界: 这不是完整的 markdown 渲染器, 是**针对本域已知构造**的收敛器;
# 仍是封闭集, 但收敛点从"每个判据各自防"变成"一处统一"。
_VIS_TAG_RE = re.compile(r"<[^>\n]*>")
_VIS_WIKILINK_ALIAS_RE = re.compile(r"\[\[[^\]\n|]*\|([^\]\n]*)\]\]")
_VIS_WIKILINK_PLAIN_RE = re.compile(r"\[\[([^\]\n|]*)\]\]")
# ⛔ R3 round-8 (Codex round-6 HIGH-5): 标准 Markdown link 的**显示文本**才是
# 读者看到的字 —— `总[计](http://x)987654个` 渲染成 `总计987654个`, 是明确
# 自陈句, 而源码里 `总` 与 `计` 被 `[](...)` 隔开, 句式门当场失锚。
_VIS_MDLINK_RE = re.compile(r"\[([^\]\n]*)\]\([^)\n]*\)")
# ⛔ R3 round-12 (Codex round-6 HIGH-4 / round-7 HIGH-4, 三轮点名): 还有
# **reference-style** link —— `总[计][r]987654个` 渲染同样是 `总计987654个`,
# 而源码里 `总` 与 `计` 被 `[][]` 隔开, 句式门失锚。与 inline link 同处理。
# ⚠️ 如实声明: `_visible_text` **仍不是完整 renderer**(Obsidian highlight `==x==`、
# math `$x$`、脚注 `[^1]` 等未覆盖), 这是**又补一个已知构造**, 不是闭包。
_VIS_REFLINK_RE = re.compile(r"\[([^\]\n]*)\]\[[^\]\n]*\]")
# ⛔ R3 round-16 (冻结审查 HIGH): 上面两式覆盖 `[t](url)` 与 `[t][r]`/`[t][]`,
# 但 **shortcut** 形态 `[t]`(定义写在别处) 渲染同样是 `t` —— `总[计]987654个`
# 读者看到 `总计987654个`, 而源码里 `总` 与 `计` 被方括号隔开, 句式门失锚。
# 逐字符方向如实说明: 即使**没有**对应定义, `[3]` 里的 `3` 读者也照样看得见,
# 所以剥掉方括号是**更贴近读者所见**, 不是放宽 —— 它让更多文本进入受检面。
# 排除 `[!callout]` 与 `[^footnote]`: 这两个前缀在 Obsidian 里不是链接语法。
_VIS_SHORTCUT_LINK_RE = re.compile(r"\[(?![!^])([^\[\]\n]*)\]")
_VIS_INVISIBLE_RE = re.compile(_INVISIBLE_ONE)
# ⛔ R3 round-6 自查回归 (Codex round-6 HIGH-1, 车道实测确认并含**误伤**):
# 第一版写成 `[*_~]` 无条件剥 —— 但 `~` 在中文里是**常用区间号**, 而
# _visible_text() 跑在 _D2_RANGE_RE **之前**, 于是 `2~3个` 被拼成 `23`:
#   · 合法区间(两端在池) 被拼成池外的一个数 ⇒ **误伤**(实测 rc=1);
#   · `9~5个` 的区间分支同时失效(round-5 刚补的 `~` 白补)。
# ⇒ 只剥**成对**的删除线 `~~`; 单个 `~` 保留给区间正则。
# ⛔ 「安全向」的说法**已被证伪**(见 _join_free docstring): `1\\*5个` 渲染可见
# `1*5`, 实现却按 **15** 查池且 15 在池内 ⇒ 放行。查到的值与读者看到的数之间
# **没有包含关系**。剥 `*`/`_` 是一个**已知 fail-open 面**, 不是安全边界。
# round-13 试过「成对剥离 + 落单移出连接集」, 实测只是把 fail-open 从「拼错的数」
# 挪到「尾片」, 还打破 3 道门 ⇒ 已回退, 如实登记在验收单 §五之三。
# `~` 另论: 剥它会**改变数的边界**(区间号), 故只剥成对的 `~~`。
# ⛔ R3 round-14 (冻结审查): 负号集原先在 D2(:1891) 与 fallback(:2179) **手抄两次**
# —— 又一处副本(本卡反复证明: 一个原则只应有一个应用点)。提为单一常量。
_NEG_SIGN = r"(?:[-−－‑﹣]|负)"
# ⚠️ 必须定义在 _NEG_SIGN **之后**（它是模块级 compile，第一版放在
#    _D2_RANGE_RE 旁边，import 当场 NameError）。
# 区间首端左侧的"危险前文": 负号, 或**小数点**(整数部分可有可无)。命中即说明
# 这个区间是从符号/小数点之后**重新起锚**的碎片, 不是一个完整的数 (round-17)。
# ⛔ round-20 (冻结审查 v2 §四.1): 原式要求小数点**前面必须有数词样字符**,
#    于是 `.2~3个` / `．二~三个` / `点二~三个` 三条(无整数部分的小数)全部
#    绕过 —— 区间照旧从 `2~3` 重锚并整段挖空, 小数门再也看不到(三条实测放行)。
#    整数部分改为可选。
_RANGE_LEFT_BAD_RE = re.compile(
    rf"(?:{_NEG_SIGN}|[{_NUMERAL_LIKE_CHARS}]?{_D2_JOIN_ONE}*[.．点]){_D2_JOIN_ONE}*$"
)
_VIS_STRIKE_RE = re.compile(r"~~")
_VIS_EMPHASIS_RE = re.compile(r"[*_]")


def _visible_text(line: str) -> str:
    """源码行 → **读者在 Obsidian 里看到的文本**（本域收敛器，非完整渲染器）。

    顺序有讲究（每一步都对应前几轮的一条实测 HIGH）：
      1. **先解 HTML 实体**再做全角转换 —— 反过来会让 `&#xff19;` 解出 `９`
         之后再没有机会转成 ASCII（round-5 HIGH-3 实测）;
      2. 剥 HTML 标签 —— `<b>` 长度不限, 原先只有 ≤22 字符的短标签算连接字符;
      3. wikilink 取**显示文本** —— 有别名取别名, 无别名取目标本身
         （原实现把无别名链接的目标挖空, 而那正是读者看到的字, round-5 HIGH-8）;
      3b. link 三形态按 **inline → reference → shortcut** 顺序剥 —— shortcut 式
         方括号最宽, 放最后才不会把 inline/reference 的显示文本先吃掉留下裸 url;
      4. 去零宽/双向控制字符;
      5. 去强调标记 `*_` 与成对 `~~` —— ⚠️ 未配对时渲染**可见**, 去掉它们是一个
         **已知 fail-open 面**而非安全边界（`1\\*5个` 按 15 入池，池含 15 并不能
         证明读者看到的 `1*5` 有出处）。此前写的「安全向、不构成虚构通道」**已被
         证伪**，round-13 的试修亦实测无收益并已回退。如实登记，不再声称安全。

    ⚠️ **不碰 inline code**: `` `…` `` 的内容在本域是**有意豁免**的字段值
    （E2, 见 _blank_inline_code），不是"被隐藏的计数"。这是**声明过的设计选择**,
    不是遗漏 —— 如实登记在验收单, 不在这里悄悄改语义。
    """
    line = html.unescape(line)
    # ⛔ R3 round-25（冻结审查 v6）：`html.unescape` 会把 `&#10;` / `&#13;` /
    #    `&NewLine;` 解成**真换行** ⇒ 一行变多行，`_visible_block` 号称的
    #    「行数与顺序不变」当场失效，而 seed 的 raw/visible **按下标配对**
    #    正依赖这个不变式。⇒ 行内解出的换行一律折成空格：单行的渲染结果
    #    仍是单行，不变式才是真的。
    line = line.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    line = line.translate(_FULLWIDTH_DIGITS)
    line = _VIS_TAG_RE.sub("", line)
    line = _VIS_WIKILINK_ALIAS_RE.sub(r"\1", line)
    line = _VIS_WIKILINK_PLAIN_RE.sub(r"\1", line)
    line = _VIS_MDLINK_RE.sub(r"\1", line)
    line = _VIS_REFLINK_RE.sub(r"\1", line)
    line = _VIS_SHORTCUT_LINK_RE.sub(r"\1", line)
    line = _VIS_INVISIBLE_RE.sub("", line)
    line = _VIS_STRIKE_RE.sub("", line)
    return _VIS_EMPHASIS_RE.sub("", line)


def _visible_block(text: str) -> str:
    """整块文本的**渲染后**形态：逐行过 `_visible_text` 再拼回去。

    ⛔ 这个模式在本卡出现了**四次**（③段信号行选行 / 五元组 / 台账种子行的
    值绑定与形状门），每次都是"某处判据还在源码文本上做，而同一条内容的另一道
    检查已经在渲染文本上做"。⇒ 提为**单一应用点**，新增消费方直接用它。

    ⚠️ 逐行归一后拼接，**行数与顺序不变** —— 依赖 `^...$` 多行锚点的正则
    （段落抓取、整行 fullmatch）可以直接换用它而不改语义。
    """
    return "\n".join(_visible_text(ln) for ln in text.splitlines())


def _normalize_number_seps(line: str) -> str:
    """千分位分隔符归一 —— **D2 与 fallback 共用**。

    ⛔ R3 round-4: 原先只在 D2 路径做, 且只认半角 `,` ——
    `987654，000个`(全角逗号) 在 D2 侧只被取到 `000`;
    `#### 派生子女 1,005 个` 在 fallback 侧被拆成 [1, 5] 逐片碰池 (实测 exit 0)。
    ⚠️ 必须**删掉**分隔符而不是换成空格: 换成空格会让它落进连接集,
    虽然仍能拼回, 但诊断里会出现带空格的原串, 与"读者看到的数"错位。
    """
    # ⛔ R3 round-6: 解 HTML 实体已上移到 _visible_text() —— 两个消费点都在最前面
    # 跑它, 此处再解一次是**冗余**（且 `&amp;#46;` 会被双重解码成 `.`, 反而错）。
    # 一个性质只应有一个实现位置; 留在这里就是死代码。
    # ⛔ R3 round-5 (Codex round-4 HIGH-3): 逗号两侧也可能夹连接字符 ——
    # `987654<b>,</b>000个` 渲染成 `987654,000个`, 原式(要求逗号紧邻数字)不命中。
    return re.sub(
        rf"([0-9]){_D2_JOIN_ONE}*[,，'’]{_D2_JOIN_ONE}*(?=[0-9]{{3}}(?![0-9]))",
        r"\1",
        line,
    )


def _count_token_value(token: str) -> int | None:
    """剥过连接字符的计数 token → int; **无法确定就 None**(不猜)。

    只两种情形给值:
      · 全 ASCII 数字 —— `int()` 本就按十进制解析 (前导零无害);
      · 表内**单字**中文数词 —— 值 = 映射, 绝对确定 (见 _cjk_single_to_int)。
    其余 (多字中文数词 / 混写 / 含表外数词字) 一律 None, 调用方 fail-closed。
    """
    if not token:
        return None
    if token.isascii() and token.isdigit():
        return int(token)
    return _cjk_single_to_int(token)


def _cjk_single_to_int(s: str) -> int | None:
    """中文数词 → int; **只认单字数词**, 其余一律 None (不猜)。

    ⛔ 对抗审查 BLOCKER: D2 的数字原为 `[0-9]+`, 于是「本板共有九十八万个子节点」
    这类**完全虚构**的规模自陈整域免检。scan 的计数都是 ASCII 整数, 报告换个写法
    不该换来免检 —— 归一后照常比对。

    ⛔ round-5 (Codex 定向复核 HIGH) + R3 收口: 原实现是**多位文法解析器**
    `_cjk_to_int`, 两条毛病一体:
      1. 提取正则 `[零〇一二两三四五六七八九十百千万亿]+` 与 `_CJK_NUM`/`_CJK_UNIT`
         **完全同集** ⇒ 任何非空匹配必返回某个整数, 所谓「解析失败 fail-closed」
         分支**静态不可达** (死代码冒充防线);
      2. 连续数字字不校验文法, 只反复覆盖 `digit` ⇒ 「五四」得 4、「一零」得 0,
         按**局部值**查池。而 0 恒在池内 (`abs(a-a)`), 于是
         `本板共有一零个子节点。` 这句**纯虚构**自陈实测 exit 0 放行
         (红证据 `_bmad-output/审查/evidence-maintb-r3/b-prefix-red-repro.txt`)。

    终态口径 (R3 冻结, 不得再引入多位解析器): 值 = 单字映射, **绝对确定**才认;
    多字 / 单字量词 (十百千万亿, 不在 `_CJK_NUM`) / 集合外字符一律 None,
    由调用方按「无法验证 / 无法解析」fail-closed 处理, 不静默放行。
    代价如实记: 合法的多字中文数词计数也会被拒 —— 诊断已提示「请改用阿拉伯
    数字」, 且报告为机器渲染 (模板与合成语料无多字合法用例, 实测零误伤)。
    """
    return _CJK_NUM.get(s) if len(s) == 1 else None


def _verify_prose_counts(text: str, scan: dict, problems: list[str]) -> None:
    """D2: 叙述段里的**计数**必须能在 scan JSON 找到同值来源。

    ⛔ 维护卡 B 的原始命题 (卡名「裸数字绑定」): 报告正文写一句
    「这块板有 99 个子节点」, 99 既不匹配规模行、也不在 frontmatter 与 tips 段,
    于是**既没被绑定也没被禁止** → exit 0。这不是实现 bug 而是设计边界,
    本函数把该边界推到「域内计数必须有出处」。

    按治理域裁定 (卡文 §零) 的顺序: **先剥豁免跨度, 再判域**。剥的是
    行内代码 / wikilink / 时间形态 / 有序列表序号 —— 全部按**结构**判定,
    不维护"哪些字符算数值"的字符表 (那条路线在 round-5 已被证伪)。

    诚实边界: 当前只覆盖「数字 + 中文量词」的**计数形态**, 不是段内全部数字
    (mastery 0.3、量表 1-4、分位值等带自身形态的量不在内)。全量绑定是增量项,
    如实登记在卡文与验收单, 不宣称"域内已全覆盖"。
    """
    # ⛔ 池必须排除**与板内容无关的源码常量**与字符串污染, 并含一阶和差
    # (合法算术) —— 判据与构建细节见 _derived_number_pool (round-3 提取共用)。
    pool = _derived_number_pool(scan)
    # default-deny 切段: preamble (首个 `##` 之前, 含「规模自陈」callout) + 每个 `##` 段。
    # ⛔ BLOCKER-2 的教训保留在这里: 段名匹配用**宽松**口径 (`## 三维审查（本轮）` 也算),
    # 与报告别处的存在性检查同一套 —— 否则给标题加四个字就能逃出治理。
    # ⛔ E1 必须**先**剥围栏 —— 卡文 §0.1 把「先剥豁免跨度」写在第一位, 而这里原先
    # 从不调用 _strip_code_blocks。后果是双向的 (对抗审查实测):
    #   · 误伤: 围栏里的字面文本被当成报告的陈述 (与 §0.1 的写死判据相反);
    #   · 绕过: 围栏里的 `## 板级数据来源与新鲜度` 被下面的 heads 正则当成真标题,
    #     从而凭空开出一个"出域段"—— 读者在 Obsidian 里看到的只是一段灰底代码。
    text = _strip_code_blocks(text)
    parts: list[tuple[str, str]] = []
    # ⛔ 段首必须**恰好两个** `#`: 原式 `^##[^\n]*$` 连 `###`/`####` 一起命中,
    # 于是一个三级标题就能开出新段 —— 配合下面的出域判定即可整段逃出治理。
    heads = list(re.finditer(r"^##(?!#)[^\n]*$", text, re.M))
    if heads:
        parts.append(("（规模自陈等前置段）", text[: heads[0].start()]))
        for i, h in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
            parts.append((h.group(0).lstrip("# ").strip(), text[h.end() : end]))
    else:
        parts.append(("（全文）", text))
    for sec, body in parts:
        # ⛔ 出域判定必须**前缀锚定**, 不能用子串 `ex in sec`:
        # 子串匹配下 `## 附录（数据来源与新鲜度）` 也算出域 —— 把豁免段名塞进任意标题
        # 的非开头位置就能整段免检, 而报告别处的重复段检查是前缀锚定的, 两者错位。
        # 与 _SECTION_RE 同口径: 段名开头相符 + 其后只能是空白或全角括号补充说明。
        if any(
            re.match(rf"^{re.escape(ex)}(?:[\s（(]|$)", sec)
            for ex in _D2_EXEMPT_SECTIONS
        ):
            continue
        # E2/E3/E4/E5: 结构性跨度挖空 (等长替换, 保持行内偏移不乱)
        # ⛔ R3 round-8 (Codex round-6 HIGH-2): _D2_WIKILINK_RE 移出豁免链 ——
        # 它把 `[[目标` 挖空**跑在 _visible_text 之前**, 于是 `[[x|987654]]个`
        # 只剩 `|987654]]个`, 量词锚失效。wikilink 的两种形态(有/无别名)现在
        # 都由 _visible_text 取**显示文本**, 语义更准且不再有顺序耦合。
        body = _D2_CODE_SPAN_RE.sub(_blank_inline_code, body)
        body = _D2_TIME_RE.sub(lambda mm: " " * len(mm.group(0)), body)
        body = _D2_ORDERED_LIST_RE.sub(
            lambda mm: mm.group(1) + "  " + mm.group(2), body
        )
        for line in body.splitlines():
            # ⛔⛔ R3 round-6: **一次性**把源码行推成读者看到的文本(实体/标签/
            # wikilink 显示文本/零宽/强调标记/全角数字), 此后所有判据都在同一个
            # 文本空间里工作 —— 前五轮"逐个补归一化"的路线已被证明发散(见 _visible_text)。
            line = _visible_text(line)
            # ⛔ 对抗审查 HIGH: 千分位与前导零把量级洗掉 —— `999,016 个` 只会被切成
            # 尾段 `016` 去比对, 于是①判决取决于该板恰好有没有 16, ②诊断报的数字是错的
            # (报 016 而报告写的是 999,016)。归一掉分隔符与前导零, 让比对对准真实量级。
            # ⚠️ 必须**删掉**分隔符而不是换成空格：换成空格会把 `999,016` 变成
            #    `999 016`，而空白在噪声集里 ⇒ 仍然只取到尾段 016（第一版就这么错的）。
            #    本行的等长约束到此为止——检查是逐行独立的，偏移不再被别处依赖。
            line = _normalize_number_seps(line)
            # ⛔ R3 round-2: 前导零**不能**在行级剥 —— 与「数串跨连接字符整体抓取」
            # 相冲: `本板共有1 000个子节点` (渲染 = 1000, SI 千分位) 会先被剥成
            # `1 0`, 再拼成 `10` 落进池内 ⇒ 放行 (车道实测)。归一化必须作用在
            # **拼接后的 token** 上, 而 `int("000123")` 本来就按十进制解析,
            # 无需额外剥零 —— 故此处整条删除, 由下面的 int(tok) 承担。

            # E7 范围表达 (Codex round-1 HIGH): `2~3 个` 这类**区间**里的端点不是
            # 独立计数, 逐个去池里找会让"合法与否取决于另一块板恰好有没有那个数"
            # —— 复核者实测同一句话在 CS 61B 报告通过、在递归与分治报告 FAIL。
            # 按结构豁免整段区间。
            # ⛔ 对抗审查 MEDIUM: E7 原为**无条件**整段挖空 ⇒ `1-987654 个` 成了
            # 洗钱通道 (写个 `1-` 前缀, 任意量级都不受检)。现在只有**两端都有出处**
            # 才算合法区间; 否则不挖空, 交给下面的计数检查逐个判。
            # ⛔ R3 round-4 (Codex round-3 HIGH): 原实现在"某端无出处"时**保留原串**,
            # 指望后面的循环"逐个判" —— 但那个循环只取**紧邻量词**的端点。于是
            # `本板共有987654-0个…` 只按右端 `0` 查池, 而 0 恒在池内 (`abs(a-a)`)
            # ⇒ exit 0 放行 (实测)。既有门只测了反方向 `1-987654`(大数在右)。
            # 现改为: **两端都终核**, 无出处的端点逐个报, 并把整段挖空
            # (避免后面的循环再按单端重复判/漏判)。
            # ⛔ R3 round-5 (Codex round-4 HIGH-1): 句式判定必须取自**挖空之前**的行 ——
            # `_D2_CLAIM_RE` 的「共有/总计 + 数字」分支依赖其后仍有数字, 而区间替换
            # 先把整段挖空, 于是 `总计987654-0个…` 挖空后句式门直接 continue,
            # 已收集的坏端点再也报不出来 (实测 exit 0)。
            is_claim = bool(_D2_CLAIM_RE.search(line))
            bad_ends: list[str] = []
            bad_range_ctx: list[str] = []

            def _range_ok(mm):
                # ⛔ R3 round-17 (冻结审查 §一.1): 区间端点用的 _NUM_RUN_PAT **不含
                # 符号与小数点**, 于是匹配能从负号或小数点**之后**重新起锚:
                #   · `-2~3个`  → 按 `2~3` 终核, 两端都在池 ⇒ 整段挖空
                #   · `2.2~3个` → 从小数尾片起锚 `2~3`, 同样挖空
                # 挖空发生在负号守卫与小数门**之前**, 两道防线再也看不到它们
                # (两条实测放行)。⇒ 首端左边紧邻负号或"数字+小数点"时, 这个区间
                # **无法确定是不是一个完整的数**, 按卡文默认 fail-closed 报错。
                # ⚠️ 诊断必须报**读者看到的完整串**（含那个危险前缀），不能报
                #    _join_free 之后的形态 —— `~` 在噪声集里，`_join_free("2~3")`
                #    == "23"，第一版就报成了「区间 23」，把"这是个区间"本身抹掉了。
                #    （本卡已因"诊断报尾片"被打回过一次，这是同一个病。）
                _pre = _RANGE_LEFT_BAD_RE.search(line[: mm.start(1)])
                if _pre:
                    bad_range_ctx.append(_pre.group(0) + mm.group(0))
                    return " " * len(mm.group(0))
                # 端点走**同一个**判值器: 中文/混写端点不再免检 (原为裸 int())。
                for raw in (mm.group(1), mm.group(2)):
                    tok = _join_free(raw)
                    val = _count_token_value(tok)
                    if val is None or val not in pool:
                        bad_ends.append(tok)
                return " " * len(mm.group(0))

            # ⚠️ 端点报错必须发在**句式门之后** —— 第一版发在这里, 于是
            # `建议覆盖 2~3 个节点。`(非规模自陈句) 也被判, 而池小的板上 2 或 3
            # 不在池 ⇒ 合法语料被误伤 (放行门 legit_range 当场变红)。
            line = _D2_RANGE_RE.sub(_range_ok, line)
            # E6b: 逐字模板常量整段挖空 (等长, 保持偏移)
            for const in _D2_TEMPLATE_CONSTANTS:
                line = line.replace(const, " " * len(const))
            # ⛔⛔ 适用范围收窄 (对抗审查 BLOCKER, 四板实测):
            # 「值落在 scan 数值池里 = 有出处」是个**碰撞判据**, 不是绑定判据 ——
            # 实测同一句合法叙述 (`你说「我做了 5 个练习」` / `第 4 条动作建议` /
            # `有 5 处值得注意`) 在 CS 61B / 特征值 / CS188 上放行, 在「递归与分治」
            # 上 FAIL, 只因后者的 scan 数值池小 (`[0,1]`)。**同一句话的对错取决于
            # 另一组数据** —— 这在任何判据里都是致命的, 不是覆盖面问题。
            # 反过来它也解释了拦截力为何弱: 能拦住的只有大到不可能碰撞的数。
            # ⇒ D2 只对**明确自称全板规模**的句式生效 (「本板共有 N 个…」这类),
            # 其余叙述交给 D1 的逐字段绑定与人工判读。宁可少管, 不可乱判。
            if not (is_claim or _D2_CLAIM_RE.search(line)):
                continue
            for _r in bad_range_ctx:
                problems.append(
                    f"数字终核: 『{sec}』段区间 {_r} 的首端紧邻负号或小数点, "
                    f"无法确定它是不是一个完整的数 (区间端点不含符号/小数, "
                    f"按此匹配会跳过负数与小数检查) ⇒ fail-closed: "
                    f"{line.strip()[:50]}"
                )
            for _e in bad_ends:
                problems.append(
                    f"数字终核: 『{sec}』段区间端点 {_e} 在 scan JSON 里找不到同值来源 "
                    f"(区间两端都必须有出处, 无法解析的端点同样不算有出处): "
                    f"{line.strip()[:50]}"
                )
            # 小数形态的计数一律 FAIL: scan JSON 的计数都是整数, 一个"0.987654 个"
            # 不可能有出处; 放行它等于给任意数字留一个 `0.` 前缀的免检通道。
            for dec in _D2_DECIMAL_RE.findall(line):
                problems.append(
                    f"数字终核: 『{sec}』段出现小数形态的计数 {dec.strip()} "
                    f"(scan JSON 的计数均为整数, 小数不可能有出处): {line.strip()[:50]}"
                )
            # 中文数字写的计数 (`共有九十八万个子节点`): 归一成整数后同样比对。
            # ⛔ R3 收口: 这里原来也调多位解析器 _cjk_to_int —— 与 fallback 侧
            # 同一个不健全实现, c754b043 只封了那一处。实测红证据:
            # `本板共有一零个子节点。` 得 _cjk_to_int("一零")==0, 而 0 恒在池内
            # (`abs(a-a)`), 于是**纯虚构**的规模自陈 exit 0 放行。现两处共用
            # _cjk_single_to_int (只认单字), 多字一律「无法解析」fail-closed。
            # 提取面必须**抓得到**多字串才能拒绝它 (只抓单字 = 多字落到检查面
            # 外, 那是漏拦不是 fail-closed), 且必须**跨排版噪声/不可见字符**整体
            # 抓 —— 否则 `九十八万**五**个` 只被按尾片 `五` 判 (R3 round-2 实测)。
            # ⛔ R3 round-3: CJK 与 ASCII **合并为一条规则** (原双循环让跨类/
            # 表外字符成为断点, 匹配重锚到尾片 —— 见 _NUM_RUN_PAT 处的四个实测)。
            # CJK 小数形态先判 (`五点五个` / `5点5个`): 与 ASCII 小数同口径恒 FAIL。
            for m_dec in _CJK_DECIMAL_RE.finditer(line):
                problems.append(
                    f"数字终核: 『{sec}』段出现小数形态的计数 "
                    f"{_join_free(m_dec.group(1))} "
                    f"(scan JSON 的计数均为整数, 小数不可能有出处): {line.strip()[:50]}"
                )
            for m_cnt in _COUNT_BEFORE_QUANT_RE.finditer(line):
                # ⛔ R3 round-6 (Codex round-5 HIGH-6): 负号不属于数串, 于是
                # `本板共有-5个` 按 **+5** 比对 —— 进池值 ≠ 读者看到的数。
                # scan 的计数都是非负整数, 负计数**不可能有出处** ⇒ 恒 FAIL。
                if re.search(rf"{_NEG_SIGN}{_D2_JOIN_ONE}*$", line[: m_cnt.start(1)]):
                    problems.append(
                        f"数字终核: 『{sec}』段出现负数形态的计数 "
                        f"-{_join_free(m_cnt.group(1))} "
                        f"(scan JSON 的计数均为非负整数, 负数不可能有出处): "
                        f"{line.strip()[:50]}"
                    )
                    continue
                token = _join_free(m_cnt.group(1))
                val = _count_token_value(token)
                if val is None:
                    problems.append(
                        f"数字终核: 『{sec}』段的计数 {token} 无法解析 "
                        f"(多字中文数词/混写/表外数词字都无法确定值, "
                        f"报告请用阿拉伯数字写计数): {line.strip()[:50]}"
                    )
                elif val not in pool:
                    problems.append(
                        f"数字终核: 『{sec}』段的计数 {token}({val}) "
                        f"在 scan JSON 里找不到同值来源: {line.strip()[:50]}"
                    )


def _tail_conflict(mm: "re.Match[str]", key: str, problems: list[str]) -> None:
    """种子行尾巴里若再出现**同一字段**的计数，与已绑定的首数矛盾 ⇒ fail-closed。

    ⛔ R3 round-26（冻结审查 v7 直接回答了我提的问题）：round-25 放宽尾巴起始
    字符集，让真实报告的 `（理解度未闭环 3 条）；…` 进入首数绑定 —— 这是**覆盖
    扩大**；但相对于同轮新增的 fail-closed 形状门，它**也确实放松了接受集**。
    审查方判词是「两者兼有」，我原来只说了扩大那一半 —— 措辞比证据宽。

    ⚠️ 能力边界：尾巴里的**其它**字段（`理解度未闭环 N 条` / `已派生 N 点`）
    在 scan JSON 里没有对应的逐节点字段可绑，**本函数不管**，如实登记。
    这里只堵一种明确矛盾：尾巴里又写了一个 `批注 N 条`。
    """
    # ⛔ R3 round-27（冻结审查 v8）：原先只在 **raw** 尾巴上找，`批**注** 999 条` /
    #    `批<b>注</b> 999 条` / 全角数字全部漏；且 `未批注 999 条` 会因**子串**命中
    #    被误当同名字段。⇒ 先归一再判，并加**词边界**（前一个字不能是汉字）。
    rest = _visible_text(mm.groupdict().get("rest") or "")
    # ⛔ round-28（冻结审查 v9）：round-27 用 `(?<![\u4e00-\u9fff])` 排除了
    #    **所有**汉字前缀 —— `未批注` 修好了，但 `累计批注 999 条` /
    #    `共批注 999 条` / `已批注 999 条` 也一并放过，它们仍是读者看得见的
    #    第二个同字段数字。⇒ 只排除**否定前缀**「未」这一个字。
    for _n in re.findall(r"(?<!未)批注\s*(\d+)\s*条", rest):
        problems.append(
            f"数字终核: 台账『种子』行 {key} 的尾巴里又出现『批注 {_n} 条』——"
            "同一字段两处计数, 无法确定以哪个为准 (fail-closed)"
        )


def _verify_seed_ledger_counts(text: str, scan: dict, problems: list[str]) -> None:
    """台账『种子』行的批注数必须绑到 scan JSON 里**该节点的** tips_count。

    ⛔ 维护卡 B · H-2 后半 (round-6 实证): 原实现只有整行**形状**白名单
    (``- <节点> — 批注 N 条``), 不绑值 —— 把真实的「批注 2 条」改成
    「批注 999 条」形状照样合法, 实测 exit 0。白名单管住了句式, 没管住数字的出处。

    scan JSON 的 ``ledger`` 是**按角色分组的 dict** (seeds/derived/unknown) 而非扁平
    列表 —— 我第一版直接迭代它, 拿到的是键字符串, verifier 当场抛 NameError/AttributeError,
    stdout 全空 exit 1, 症状伪装成"报告不合规"。这里显式摊平并容两种形态。
    """
    # ⛔ R3 round-22（冻结审查 v3）：段抓取与行匹配原先都在 **raw** 文本上做 ——
    #    留一条正确的种子行、再加一条**渲染等价但源码不命中**的冲突行
    #    （`- SeedA — 批**注** 999 条` / `批<b>注</b>`），后者匹配不上就静默
    #    continue，绑定被跳过。**fallback 模式**下有形状门兜底（这正是我上一轮
    #    『未复现』的原因），但 **manifest 模式没有那层门** —— 两条实测 exit 0。
    #    与③段信号行、五元组的双行逃逸完全同型，第三次。
    # ⛔ R3 round-25（冻结审查 v6）：round-24 用**两次独立 re.search** 分别在 raw
    #    与 visible 上取段，再按下标配对 —— 未验证两边选中的是**同一小节**；且
    #    `_visible_block` 的拼接依赖「行数不变」这个当时**并不成立**的不变式
    #    （`&#10;` 解出换行）。另外只处理**首个** `### 种子`，一个正确的诱饵小节
    #    就能遮住后面的冲突小节。
    #    ⇒ 改为：**一次切行**，raw 与 visible 是同一份 list 的逐行映射（下标即同源
    #      行，不可能错配）；小节按 visible 标题识别（兼容被排版切开的标题）并
    #      **逐个**处理，不再只取第一个。
    raw_lines = text.splitlines()
    vis_lines = [_visible_text(_ln) for _ln in raw_lines]
    # ⛔ R3 round-27（冻结审查 v8）：round-26 我在这里**手抄了第二份围栏状态机** ——
    #    「遇到任意三反引号就布尔翻转」，比 `_strip_code_blocks` 本体弱得多：
    #    四反引号开栏 → 块内三反引号伪闭栏 → 四反引号真闭栏，状态会 True→False→True，
    #    于是真闭栏之后的可见冲突小节被整段跳过。**同一原则两处定义**，第 N 次。
    #    ⇒ 复用本体：`_strip_code_blocks` 把围栏行与围栏内容都置空。
    #    ⚠️ 措辞更正（v9）：并非无条件「行数恒等」—— 返回字符串再 splitlines 时
    #      **末尾空项会丢**（既有测试已记录三空行只得两项）。准确说法是
    #      **索引映射保持、尾项由越界兜底补偿**（下面按空串处理）。
    #      「原行非空而剥后为空」即「在围栏内（或本身是围栏标记）」。
    # ⛔ 同轮收紧两处判定（审查方逐条点名）：
    #    · 父级 H2 原用 `"台账" in heading` ⇒ `## 非台账示例` 也算 —— 改整行匹配
    #      （允许模板里设计内的全角括号补充与 ATX 闭合井号）；
    #    · `### 种子 ###`（合法 ATX 闭合序列）原不识别，而 `###种子`（非法 ATX，
    #      Obsidian 不渲染成标题）反而命中 —— 两侧都改正。
    _stripped = _strip_code_blocks(text).splitlines()
    _in_fence = [
        bool(raw_lines[_n].strip())
        and not (_stripped[_n] if _n < len(_stripped) else "").strip()
        for _n in range(len(raw_lines))
    ]
    # ⛔ R3 round-29（冻结审查 v10）：round-28 我在这里**自己写了两式**
    #    （`^ {0,3}##\s+台账…`、闭合井号…），而 `_SECTION_RE` 的 docstring 里
    #    **明写着**「存在性检查与下游定位**必须共用本函数** —— 两处口径一旦不同，
    #    就会出现『算在场却定位不到』的缝隙」。我正好犯了它警告的那件事：
    #      · `## 台账（x`（未闭合括号）—— 必需段门认在场，我的式子不认 ⇒
    #        种子校验器拿到零个 section 直接返回，`999` 完全不绑定；
    #      · 反向，我新接受的 `   ## 台账` / `## 台账 ###` 又会被必需段门拒绝。
    #    ⇒ **改回共用 `_SECTION_RE`**。缩进标题与**裸的** ATX 闭合井号两侧一致地不接受。
    #    ⚠️ 措辞更正（v11）：「不接受所有 ATX 闭合井号」这句**过宽** ——
    #      `_SECTION_RE` 的括号分支是 `（[^\n]*$`，会吞下括号后的任意尾巴，
    #      所以 `## 台账（x ###` 是**被接受**的。如实登记，不吹。
    #    两侧一致地不接受的部分：
    #      写成那样的报告会被必需段门直接判 FAIL，整体仍是 fail-closed。
    #      要放宽就得改 `_SECTION_RE` 本体，让两侧同时动 —— 不在本轮范围。
    _H2_LEDGER_RE = re.compile(_SECTION_RE("## 台账"))
    _H3_SEED_RE = re.compile(_SECTION_RE("### 种子"))
    # ⛔ R3 round-32（冻结审查 v13 的第六形态）：只收集**认可的**小节，等于把
    #    「不被 `_SECTION_RE` 认可的种子 H3」整块**排除在审计面之外** ——
    #      · `seeds=[]` + `### 种子 ###` + `- Ghost — 批注 9 条` ⇒ 零 section 且
    #        零种子，函数直接返回，Ghost 行永不受审；
    #      · 更强：先放一个**认可的空** `### 种子`，再放第二个**不认可**的 H3 +
    #        Ghost 行 ⇒ 第二块永不审，非零种子板同样可绕。
    #    ⇒ 凡是「H3 且可见文本以『种子』开头」却不被 `_H3_SEED_RE` 认可的行，
    #      自己报出来（fail-closed），不再静默跳过。
    _H3_SEEDISH_RE = re.compile(r"^[^\S\n]*###[^\S\n]*种子")
    _under_ledger = False
    sections: list[tuple[int, int]] = []
    _i = 0
    while _i < len(vis_lines):
        if _in_fence[_i]:
            _i += 1
            continue
        if re.match(r"^##[^\S\n]", vis_lines[_i]):
            _under_ledger = bool(_H2_LEDGER_RE.match(vis_lines[_i]))
        if (
            _H3_SEEDISH_RE.match(vis_lines[_i])
            and not _H3_SEED_RE.match(vis_lines[_i])
            and not _in_fence[_i]
        ):
            problems.append(
                "数字终核: 出现形似『### 种子』但不合统一口径的小节标题 "
                f"({vis_lines[_i].strip()[:40]!r}) —— 该块不会进入台账绑定面, "
                "标题须为 `### 种子` 或 `### 种子（补充）` (统一口径 _SECTION_RE)"
            )
        if _under_ledger and _H3_SEED_RE.match(vis_lines[_i]):
            _j = _i + 1
            # ⛔ round-29（冻结审查 v10）：终点扫描原先**不判围栏** ⇒ 围栏内的
            #    `## 假标题` 会提前截断小节，真闭栏之后的可见冲突行完全不再遍历。
            #    「小节内跳过围栏」上一轮只保护了消费行，没保护小节**终点**。
            while _j < len(vis_lines) and not (
                not _in_fence[_j] and re.match(r"^#{2,3}[^\S\n]", vis_lines[_j])
            ):
                _j += 1
            sections.append((_i + 1, _j))
            _i = _j
        else:
            _i += 1
    if not sections:
        # ⛔ R3 round-30（冻结审查 v11）：H2 有全局必需段门兜底，**H3 没有** ——
        #    于是「与统一口径一致地不接受」对 H3 就成了**静默洞**：
        #    `### 种子 ###` 这类写法既不被本函数扫描、也没有任何别处会报，
        #    整块台账行不受绑定。上一轮我把这种「静默不检查」写进门当成期望，
        #    等于把缺陷编码成了正确行为（审查方点名的目标无关假绿）。
        #    ⇒ 台账段在场却找不到可扫描的『种子』小节 = fail-closed。
        # ⛔ R3 round-31（冻结审查 v12）：round-30 这道 fail-closed **误伤了合法的
        #    零种子报告** —— 生成侧允许 `ledger.seeds == []` / `counts.seeds == 0`，
        #    那种板本来就没有种子小节。⇒ 只有在**确有种子可绑**时才要求小节在场。
        _seed_rows = (
            (scan.get("ledger") or {}).get("seeds")
            if isinstance(scan.get("ledger"), dict)
            else None
        )
        if _seed_rows and re.search(_SECTION_RE("## 台账"), text, re.M):
            problems.append(
                "数字终核: 报告有『## 台账』段却找不到可绑定的『### 种子』小节 "
                "(标题须与统一口径 _SECTION_RE 一致: 段名后只能是行尾或全角括号补充)"
            )
        return
    groups = scan.get("ledger")
    rows: list[dict] = []
    if isinstance(groups, dict):
        # ⛔ R3 round-27（冻结审查 v8）：原先**摊平全部角色**（seeds/derived/unknown）
        #    ⇒ 把**派生节点**写进「种子」小节、按它的 tips_count 就能通过。
        #    本函数管的是种子小节，绑定面就只能是 seeds。
        #    ⚠️ 仅当 ledger 是按角色分组的 dict 时才收窄；扁平 list 形态无角色信息，
        #      维持原样并如实登记（那是 scan 侧的形态问题，不在本函数职责内）。
        seeds = groups.get("seeds")
        if isinstance(seeds, list):
            rows = [x for x in seeds if isinstance(x, dict)]
        else:
            # ⛔ round-28（冻结审查 v9）：round-27 在 `seeds` 缺失/非 list 时**静默
            #    回落到摊平全部角色** —— 那正是本轮要堵的洞（派生节点混进种子小节）。
            #    分组形态却没有 seeds = scan 侧异常，**fail-closed**，不猜。
            problems.append(
                "数字终核: scan JSON 的 ledger 是分组形态但缺少可用的 seeds 列表, "
                "台账『种子』行无法绑定 (不回落到其它角色, 避免派生节点冒充种子)"
            )
            return
    elif isinstance(groups, list):
        rows = [x for x in groups if isinstance(x, dict)]
    if not rows:
        # ⛔ round-31（冻结审查 v12）：`seeds == []` 是**合法**的零种子板，
        #    与「scan JSON 根本没有 ledger」不是一回事。前者放行（没有种子可绑，
        #    小节里也不该有台账行——真有行会在下面按「不在 ledger 里」报）；
        #    后者仍 fail-closed。
        _raw_seeds = groups.get("seeds") if isinstance(groups, dict) else None
        if isinstance(_raw_seeds, list) and any(
            not isinstance(x, dict) for x in _raw_seeds
        ):
            # ⛔ round-32（冻结审查 v13）：`seeds=[None]` 会被过滤成空 rows，
            #    随后因**原值仍是 list** 被当成合法零种子 ⇒ 损坏数据静默通过。
            problems.append(
                "数字终核: scan JSON 的 ledger.seeds 含非对象条目 (损坏), "
                "台账『种子』行无法绑定"
            )
            return
        if not (isinstance(groups, dict) and isinstance(groups.get("seeds"), list)):
            problems.append("数字终核: scan JSON 无可用 ledger, 台账『种子』行无法绑定")
            return
        # ⚠️ `seeds == []` 时**不能提前 return** —— 那样零种子板里写的任何台账行
        #    都会被静默放行（我第一版就是这么写的，当场实测漏）。
        #    继续往下走：绑定面为空 ⇒ 每一行都会按「不在 ledger 里」报。
    tips_by_node = {str(r.get("node_id")): r.get("tips_count") for r in rows}
    # 归一空间的候选索引：只在 raw 行解析不出时才用（round-25）
    vis_index: dict[str, list[str]] = {}
    for _raw_id in tips_by_node:
        vis_index.setdefault(_visible_text(_raw_id), []).append(_raw_id)
    for _lo, _hi in sections:
        for _k in range(_lo, _hi):
            ln = vis_lines[_k]
            if not ln.strip():
                continue
            # ⛔ round-28（冻结审查 v9）：`_in_fence` 原先只用于**找标题**，
            #    进了小节之后逐行检查不再判围栏 ⇒ 小节里放一段代码块，
            #    块内的字面行会被当成台账行强判。
            if _in_fence[_k]:
                continue
            raw_ln = raw_lines[_k]  # 同一下标 = 同一源行（一次切行保证）
            raw_ms = _SEED_LEDGER_LINE_RE.match(raw_ln)
            ms = _SEED_LEDGER_LINE_RE.match(ln)
            if not ms and not raw_ms:
                # ⛔ R3 round-25（冻结审查 v6）：原先静默 `continue`，理由是"形状问题
                #    由 _verify_report 的模板白名单报" —— 但那道白名单**只在 fallback
                #    路径**上跑，**manifest 模式没有兜底**，于是种子小节里任何不匹配
                #    模板的行（含 `批注 999 条&#10;x` 这种尾巴）整条免检。
                #    ⇒ 本函数自己 fail-closed：小节内的非空行必须是标准模板行。
                problems.append(
                    f"数字终核: 台账『种子』小节出现非模板行 (每行须为 "
                    f"`- <节点> — 批注 N 条` 或 `- <节点> — 无批注`): {ln.strip()[:60]}"
                )
                continue
            if not ms:
                ms = raw_ms
            if raw_ms:
                node = raw_ms.group("node").strip()
                if node in tips_by_node:
                    key = node
                    got = 0 if raw_ms.group("none") else int(raw_ms.group("n"))
                    want = tips_by_node[key]
                    if got != want:
                        problems.append(
                            f"数字终核: 台账『种子』行 {key} 报批注 {got} 条, "
                            f"scan JSON 的 tips_count 是 {want} (形状对不等于数字有据)"
                        )
                    _tail_conflict(raw_ms, key, problems)
                    continue
                # ⛔ round-25: raw 精确未命中**不等于**身份非法 —— ledger id 为 `A&B`
                #    而报告合法写成 `A&amp;B` 时，读者看到的是同一个名字。原实现
                #    在这里直接报错，不再尝试唯一的归一候选 ⇒ 合法用法误伤。
                #    改为**继续往下**走归一候选（唯一才绑，撞车仍 fail-closed）。
            node = ms.group("node").strip()
            cands = vis_index.get(node) or []
            if len(cands) > 1:
                problems.append(
                    f"数字终核: 台账『种子』行的节点 {node!r} 归一后同时对应 "
                    f"{sorted(cands)!r} —— 无法确定是哪一个, 不猜 (fail-closed)"
                )
                continue
            if not cands:
                problems.append(
                    f"数字终核: 台账『种子』行的节点 {node!r} 不在 scan JSON 的 ledger 里 "
                    "(台账不得列出未扫描到的节点)"
                )
                continue
            key = cands[0]
            want = tips_by_node[key]
            got = 0 if ms.group("none") else int(ms.group("n"))
            if got != want:
                problems.append(
                    f"数字终核: 台账『种子』行 {key} 报批注 {got} 条, "
                    f"scan JSON 的 tips_count 是 {want} (形状对不等于数字有据)"
                )
            _tail_conflict(ms, key, problems)


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
    board_id = mb.group(1).strip()
    # ⛔ round-6 终裁复核: 绑定对象此前完全由报告自己的 frontmatter 指定 —
    # 报告可以指向**另一块板**的 scan JSON 来匹配自己的数字。报告文件名
    # 形如 `回顾-<board>-<date>.md`, 与 frontmatter board 必须一致。
    mname = re.match(r"^回顾-(.+)-(\d{4}-\d{2}-\d{2})\.md$", report_path.name)
    if not mname:
        problems.append(f"报告文件名不符 `回顾-<板>-<日期>.md`: {report_path.name}")
    elif mname.group(1) != board_id:
        problems.append(
            f"数字终核: frontmatter board={board_id!r} 与文件名的板 "
            f"{mname.group(1)!r} 不一致 (不得绑定另一块板的 scan JSON)"
        )
    scan_path = report_path.parent / f".recap-scan-{board_id}.json"
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
    # ⛔ round-6 HIGH (终裁复核实测): 原用 re.search 全文取**首个**五元组匹配,
    # 且无唯一性约束 —— 在报告更早处放一行携带真数字的诱饵 (散文行, 甚至
    # 代码围栏里), 可见的「规模自陈」callout 就能写任意假数字并 PASS
    # (实测 120 成员/350 批注 通过)。改为: 全文所有五元组形态的行**逐条**
    # 校验且必须恰好一条 —— 诱饵行自己也会被校验, 无处可藏。
    scale_pat = re.compile(
        r"(\d+)\s*成员（(\d+)\s*种子\s*\+\s*(\d+)\s*派生，(\d+)\s*占位）/\s*(\d+)\s*批注"
    )
    # ⛔ R3 round-20 (冻结审查 v2「三处不改」判断被推翻): 原先在 **raw 全文**
    #    上 findall ⇒ 保留一条正确五元组、再加一条**渲染等价但源码不命中**的
    #    冲突行 (`999 成**员**（…）` / `999 成<b>员</b>（…）`), 后者既不计入
    #    「恰好一处」的计数、也不被逐条校验 —— 两条实测 exit 0 放行。
    #    与 ③段信号行的双行逃逸**同型**; 我上一轮只测了「改坏那条唯一正确行」
    #    (形状一坏就 fail-closed), 没把「留一条好的 + 加一条冲突的」这个形态
    #    迁移过来, 于是误判为「实测不成立」。⇒ 逐行归一后再匹配。
    scale_hits = scale_pat.findall(_visible_block(text))
    want = tuple(
        counts.get(k, -1)
        for k in ("members", "seeds", "derived", "stubs", "annotations")
    )
    if not scale_hits:
        problems.append("规模自陈行未按模板格式给出五元组 (成员/种子/派生/占位/批注)")
    elif len(scale_hits) > 1:
        problems.append(
            f"数字终核: 报告出现 {len(scale_hits)} 处规模自陈五元组 (只许一处, "
            "多处 = 诱饵/自相矛盾)"
        )
    for hit in scale_hits:
        got = tuple(int(x) for x in hit)
        if got != want:
            problems.append(f"数字终核: 规模自陈 {got} ≠ scan JSON {want}")
    # tips 两数只在「AI 侧对账」段绑定 — 台账里逐节点的 "tips 未闭环 n 条"
    # 是行级数字, 与全局计数不同, 不参与本绑定 (全文搜索会误命中)。
    #
    # ⛔ round-6 BLOCKER (终裁复核实测): 此处原为 `if not recon: return` —
    # 而段落存在性检查 (_verify_report 的 _VERIFY_SECTIONS 循环) 是**前缀
    # 匹配**, `## AI 侧对账（本轮）` 照样算"段落在场"。两者叠加 = 给标题加
    # 任意后缀就能让本函数提前 return, **tips 绑定与整块 signals 绑定全部
    # 跳过** (信号行可整体删除/随意改数/谎标无据仍 PASS)。这是五轮信号防线
    # 的总开关。现在: 缺段落 → 记 problem 并**继续**跑 signals 绑定, 绝不
    # 静默 return; 段落标题的整行锚定另在 _verify_report 收口。
    recon = re.search(
        _SECTION_RE("## AI 侧对账") + r"(.*?)(?=^#{2}(?:[^\S\n]|$)|\Z)",
        text,
        re.M | re.S,
    )
    if not recon:
        problems.append(
            "数字终核: 未找到『## AI 侧对账』段 (标题须为段名本身或段名+（补充）) "
            "— tips 两数无法绑定"
        )
        _verify_signals_if_present(text, scan, problems)
        return
    # 两行均为必需 (五轮 H5 残余: 缺行不许静默豁免 — 改写成非模板措辞
    # 即逃逸绑定, 必须 fail-closed)。
    # ⛔ round-6 终裁复核: 原用 re.search 只绑**首个**匹配, 段内第二条同形句
    # 与段外同一句都不受检 → 改为**全文逐条**校验且段内必须各恰好一条。
    for pat, ckey, name in (
        (r"tips 批注共\s*(\d+)\s*条", "tips_total", "tips 总数"),
        (r"其中理解度未闭环\s*(\d+)\s*条", "tips_understanding_open", "tips 未闭环"),
    ):
        in_sec = re.findall(pat, recon.group(1))
        all_hits = re.findall(pat, text)
        want_v = counts.get(ckey, -1)
        if not in_sec:
            problems.append(f"数字终核: AI 侧对账缺『{name}』标准计数行")
        elif len(in_sec) > 1:
            problems.append(
                f"数字终核: AI 侧对账段内出现 {len(in_sec)} 条『{name}』(只许一条)"
            )
        for got in all_hits:  # 段外同形句同样绑定, 不留"第二处说法"
            if int(got) != want_v:
                problems.append(f"数字终核: {name} {got} ≠ scan JSON {want_v}")
    _verify_seed_ledger_counts(text, scan, problems)
    _verify_prose_counts(text, scan, problems)
    _verify_signals_if_present(text, scan, problems)
    _verify_fallback_derive_numbers(text, scan, problems)


def _verify_fallback_derive_numbers(text: str, scan: dict, problems: list[str]) -> None:
    """CARD-维护B-R2 round-3 (Codex HIGH-4/5b/6): fallback 允许式的**数字出处**绑定。

    措辞白名单 ``_FALLBACK_DERIVE_ALLOW`` (在 _verify_report) 只管「这句话允许说」,
    这里管「说出来的数字必须有据」——白名单匹配与值绑定分属两处, 缺一即漏:
      · HIGH-4 (round-4 补: ③段限定移出 data_mode 条件——manifest 报告的附录
        伪信号实测同样放行): 「无来源结论」信号行只许出现在**③段** ——
        ③段外 (附录/自造段) 的同形行不受信号绑定保护;
      · HIGH-5b: ⑦『N 个派生角色成员缺来源锚点』的前置 N 必须全等
        ``signals.unsourced_conclusions.value`` (无据档不容许前置 N);
      · HIGH-6: 允许式 #2 (段落标题) 与 #5 (关系类型分布行) 行内出现的任何
        数字都必须在 scan 数值池 —— `#### 派生子女 987654 个的说明` /
        `- 关系类型分布：无 987654` 实测曾放行。
    """
    # HIGH-4 (round-4: 对 manifest 模式同样生效)
    s3 = "\n".join(
        re.findall(r"^### ③.*?(?=^#{2,3}(?:[^\S\n]|$)|\Z)", text, re.M | re.S)
    )
    rest = text.replace(s3, "", 1) if s3 else text
    if "无来源结论" in rest:
        problems.append(
            "数字终核: 「无来源结论」信号行只许出现在③段 "
            "(段外同形行不受信号绑定保护, 附录伪信号实测曾放行)"
        )
    if scan.get("data_mode") != "fallback_local":
        return
    # HIGH-5b: ⑦ 前置 N 与 signals.unsourced_conclusions.value 全等
    sig = (scan.get("signals") or {}).get("unsourced_conclusions") or {}
    m7 = re.compile(r"^[>\s]*(?:(?P<n>\d+)\s*个)?派生角色成员缺来源锚点")
    for ln in text.splitlines():
        # ⛔ R3 round-19 (冻结审查 §一.3): 这里原先在 **raw** 行上匹配, 而同一条
        # 叙述的措辞白名单 (:2437) 早已改在 _visible_text 上判 —— 两侧口径分叉 ⇒
        # 「白名单放行、N 绑定跳过」的夹缝: 三条实测 exit 0
        #   · `999 个派**生**角色成员缺来源锚点。`
        #   · `999 个派<b>生</b>角色成员缺来源锚点。`
        #   · `999<b></b> 个派生角色成员缺来源锚点。`
        # 渲染后都是明确的 `999 个…`, 而 signals.value=0 ⇒ 本该 FAIL。
        # ⇒ 与白名单同口径, 一律在渲染后文本上匹配。
        mm = m7.match(_visible_text(ln))
        if not mm:
            continue
        n = mm.group("n")
        want = sig.get("value")
        if sig.get("availability") == "无据" or want is None:
            if n is not None:
                problems.append(
                    f"数字终核: 『派生角色成员』叙述前置 N={n}, 但 "
                    "signals.unsourced_conclusions 无据 (不容许前置 N)"
                )
        elif n is not None and int(n) != int(want):
            problems.append(
                f"数字终核: 『派生角色成员』叙述前置 N={n} ≠ "
                f"signals.unsourced_conclusions.value={want}"
            )
    # HIGH-6: 标题行与关系分布行内的数字必须有出处
    pool = _derived_number_pool(scan)
    heading_pat = next(p for p, b in _FALLBACK_DERIVE_ALLOW if b == "md:heading")
    relation_pat = next(
        p for p, b in _FALLBACK_DERIVE_ALLOW if b == "scan:counts.relation_types"
    )
    for ln in text.splitlines():
        # ⚠️ 检查范围: 标题条目 = fallback 措辞白名单实际放行的行 (含「派生」)——
        # 不过滤会误伤报告主标题的年份 (`# 回顾 · 板 · 2026-09-01` 首跑即中);
        # 关系类型分布条目 = 该白名单自身匹配的行 (不含「派生」也要查)。
        # ⛔ R3 round-8 (Codex round-6 HIGH-3): **先归一再选行** ——
        # 原实现在**源码行**上判「含派生」与白名单匹配, 于是
        # `#### 派**生**子女 987654 个` 渲染后是明确计数, 却因源码里 `派` 与 `生`
        # 被 `**` 隔开而整行不进检查面(实测 exit 0)。
        vis = _visible_text(ln)
        tags = []
        if "派生" in vis and heading_pat.match(vis):
            tags.append(("标题", heading_pat))
        if relation_pat.match(vis):
            tags.append(("关系类型分布", relation_pat))
        for tag, pat in tags:
            # ⛔ round-4 (Codex 抢救探针 C): 数字提取必须含**中文数词** ——
            # `#### 派生子女 九十八万个` 的 `九十八万` 用 `\d+` 抓不到, 实测放行。
            # ⛔ round-5 (Codex 定向复核 HIGH): 原实现把多字串交给 _cjk_to_int 并
            # 宣称"解析失败 fail-closed"——但提取字符集与 _CJK_NUM/_CJK_UNIT 完全
            # 同集, 非空匹配必能返回**某个**整数 (「五四」只留末位得 4), 该分支
            # 静态不可达且可能按错值查池。现改为**只认单字数词** (值=映射, 绝对
            # 确定); 多字串一律「无法验证」fail-closed——模板与合成语料的允许式
            # 行没有多字中文数词的合法用例, 误伤面为零。
            # ⛔ R3: 判据提为模块级 _cjk_single_to_int, 与 D2 叙述段**同一份**
            # 实现 —— 两处曾经分叉 (只修一处 = 另一处继续按局部值查池)。
            # ⛔ R3 round-2: 提取面同样跨连接字符整串抓 (`九**五**` 曾被拆成
            # 两个单字碎片, 逐片查池全部命中而整体虚构值放行)。
            # ⛔ R3 round-3 (Codex round-2 HIGH): 这里的 ASCII 侧原先仍是
            # `re.findall(r"\d+")` —— `1 000` / `9**5` 被拆成碎片逐片碰池,
            # 「CJK 与 ASCII 同一口径」当时并不成立。现两类共用 _NUM_RUN_RE。
            # ⛔ R3 round-4 (Codex round-3 HIGH): 千分位归一与小数防线原先**只在 D2
            # 路径**存在, fallback 直接对原行 findall 并逐片入池 —— `0.0个` /
            # `零点零个` 按 [0,0] 查池、`1,005个` 按 [1,5] 查池, 读者所见值与进池值
            # 不同 (实测 exit 0)。两条前处理下沉为共用。
            # ⛔⛔ R3 round-6: 与 D2 侧**同一个**归一器, 同一个文本空间。
            norm = _normalize_number_seps(_visible_text(ln))
            for m_dec in _DECIMAL_ANY_RE.finditer(norm):
                problems.append(
                    f"数字终核: fallback 允许式({tag})行内出现小数形态 "
                    f"{_join_free(m_dec.group(0))} "
                    f"(scan JSON 的计数均为整数, 小数不可能有出处): {ln.strip()[:40]}"
                )
            # ⛔ R3 round-8 (Codex round-6 HIGH-4): 负数守卫原先**只在 D2 侧** ——
            # fallback 的 `-5` 按 +5 入池。两侧同口径: scan 计数均非负, 负数恒 FAIL。
            for m_neg in re.finditer(
                rf"{_NEG_SIGN}{_D2_JOIN_ONE}*({_NUM_RUN_PAT})", norm
            ):
                problems.append(
                    f"数字终核: fallback 允许式({tag})行内出现负数形态 "
                    f"-{_join_free(m_neg.group(1))} "
                    f"(scan JSON 的计数均为非负整数, 负数不可能有出处): {ln.strip()[:40]}"
                )
            nums: list[int] = []
            for tok in (_join_free(x) for x in _NUM_RUN_RE.findall(norm)):
                v = _count_token_value(tok)
                if v is None:
                    problems.append(
                        f"数字终核: fallback 允许式({tag})行内数字 {tok!r} 无法验证 "
                        f"(多字中文数词/混写/表外数词字都无法确定值, "
                        f"请改用阿拉伯数字): {ln.strip()[:40]}"
                    )
                else:
                    nums.append(v)
            for num in nums:
                if num not in pool:
                    problems.append(
                        f"数字终核: fallback 允许式({tag})行内数字 {num} 无出处 "
                        f"(数字必须在 scan 数值池): {ln.strip()[:40]}"
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
    problems: list[str] = []
    # ⛔ 顺序必须是**先检后剥** (对抗审查实测的 BLOCKER):
    # 原实现先无条件 `re.sub` 剥掉闭合注释, 再用 `if "<!--" in text` 查残留 ——
    # 两个标记都被吃掉了, 于是这道检查恒不触发。后果远不止 D2:
    # 把标记包成 code span (`` `<!--` `` … `` `-->` ``), 在 Obsidian 里它渲染成
    # **字面可见的正文**, 而 verifier 先把整段删掉 ⇒ 该段落对**全部**基于 text 的
    # 检查隐身 —— 实测连 HARD-R4 禁词「偏离」都能这样藏进去并 VERIFY PASS。
    # 报告本就禁写任何 HTML 注释 (F2 已有此口径), 所以在**原始文本**上一次判死,
    # 不区分闭合与否、也不管标记是否落在代码跨度内。
    if "<!--" in text_raw or "-->" in text_raw:
        problems.append(
            "正文含 HTML 注释标记 (渲染隐藏面/可见文本与校验文本分叉, 报告禁写注释)"
        )
    # 六轮影子字段防御: 正文校验前剥 HTML 注释 — "注释里藏正确模板行、
    # 可见文本撒谎"的形态失效, 可见文本必须独立过全部校验。
    text = re.sub(r"<!--.*?-->", "", text_raw, flags=re.S)
    # round-4: 零宽/双向控制字符 — 渲染不可见但能改变正则匹配与阅读顺序,
    # 是"看起来合规、实际另一回事"的通用载体。合法报告没有理由出现它们。
    # ⛔ R3 round-15 (冻结审查): 这里原先**手抄**了一份不可见字符集, 只到 U+2064,
    #    而 _INVISIBLE_ONE 覆盖到 U+2069 ⇒ bidi isolate U+2065-2069 能过全局门。
    #    又一处「同一原则两处定义」。改为共用 _INVISIBLE_ONE。
    if re.search(_INVISIBLE_ONE, text):
        problems.append("正文含零宽/双向控制字符 (不可见字符, 报告禁用)")
    _verify_numbers(fm, text, Path(path), problems)
    if not re.search(r"^type:\s*recap\s*$", fm, re.M):
        problems.append("frontmatter 缺 type: recap")
    if "规模自陈" not in text:
        problems.append("缺 规模自陈 callout")
    # 六轮防御③: 必需段落唯一 — 重复段(第一段合规第二段夹私货)不放行。
    # ⛔ round-6 BLOCKER 同源修复: 根因是**存在性检查与下游定位口径不一致**
    # —— 存在性用前缀匹配 (`^## AI 侧对账`), 下游 tips 绑定/动作段白名单却用
    # 整行正则定位, 于是 `## AI 侧对账（本轮）` 两头讨好: 算"段落在场"、
    # 却让下游整块校验静默跳过。模板里 `## 台账（种子/派生）` 这类**设计内的
    # 括号补充**又必须放行, 所以不能一刀切整行精确。
    # 统一口径 = `_SECTION_RE`: 段名之后只允许「行尾」或「全角括号补充」,
    # 存在性检查与下游定位共用它, 缝隙消失。
    for s in _VERIFY_SECTIONS:
        n = len(re.findall(_SECTION_RE(s), text, re.M))
        if n == 0:
            problems.append(f"缺段落 {s} (标题须为段名本身或段名+（补充）)")
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
        # H4 (round-4 真结构级): 词表与"整段禁某词"都能被同义改写绕过
        # (「派生数量为零」→「后代节点数量为零」实测曾 PASS)。fallback 下
        # 派生**子女数**恒无据, 这类断言只可能出现在台账「种子」小节 —— 故
        # 改为**整行白名单**: 该小节每一行要么空, 要么必须整行匹配
        #   `- <node_id> — 批注 N 条`  /  `- <node_id> — 无批注`
        # 模板 (数字由 ledger 的 tips_count 支持)。任何自由叙述一律 FAIL,
        # 不再判断它"是不是在说派生"。
        # ⛔ round-22：形状门同样要在渲染文本上做，否则「源码不命中 ⇒
        #    整行白名单也不管」，两道门一起被同一条冲突行绕过。
        # ⚠️ 必须用**局部变量**，不能重绑 `text` —— 第一版写成 `text = _visible_block(text)`,
        #    它落在 `_verify_report` 的函数体作用域里, 于是**其后所有检查**（含全文
        #    『派生』门）都吃到了归一文本: 一次范围远超意图的改动。症状是
        #    survivor-35 变成**空变异**（那道门自己的 `_visible_text(ln)` 成了冗余）。
        seed_vis = _visible_block(text)
        mseed = re.search(
            r"^### 种子\s*$(.*?)(?=^#{2,3}[^\S\n]|\Z)", seed_vis, re.M | re.S
        )
        if mseed:
            # ⛔ 维护卡 B · H-2 后半: 原式只查**形状** (`批注 \d+ 条`), 不绑值 ——
            # 实证「- SeedA — 批注 999 条」形状合法即 PASS。白名单管住了句式,
            # 没管住数字的出处。现在捕获节点名与数字, 与 scan JSON 的 ledger 里
            # **该节点的 tips_count** 全等比对: 形状 + 出处双绑。
            seed_line = re.compile(
                r"^[>\s]*-\s+(?P<node>\S.*?)\s+—\s+"
                r"(?:批注\s*(?P<n>\d+)\s*条|(?P<none>无批注))\s*$"
            )
            # ⚠️ 只查**形状**在这里做; 绑**值**在 _verify_numbers 里 (scan JSON 只在
            # 那边加载)。职责切分: 本函数管措辞与模板, 数字出处统一归数字终核。
            for ln in mseed.group(1).splitlines():
                if ln.strip() and not seed_line.match(ln):
                    problems.append(
                        "fallback 台账『种子』小节存在模板外的行 "
                        "(该段每行只许 `- <节点> — 批注 N 条` 或 `— 无批注`; "
                        f"子女数在 fallback 恒无据): {ln.strip()[:40]}"
                    )
        # round-5: 断言可以写在种子段**之外** (派生段/①②段/散文行) —— 段内
        # 白名单管不到。故对**全文**做一层: fallback 下任何含「派生」的行都
        # 必须整行匹配 _FALLBACK_DERIVE_ALLOW 的有据模板之一 (表定义与逐条
        # 依据见模块级常量, CARD-维护B-R2 (d) 纯搬家)。其余一律违规,
        # 不再问它"是不是在断言子女数"。
        for ln in text.splitlines():
            # ⛔ R3 round-9 (Codex round-7 HIGH-1): 这道**全文门**原先也在**源码行**
            # 上判「含派生」与白名单匹配 —— round-8 只把局部数字函数改成先归一,
            # 这里没改, 于是 `- 派**生**出 987654 个新节点` 渲染后是派生断言,
            # 却既不进局部数字循环、也绕过本门(实测 exit 0)。两处同口径。
            vis_ln = _visible_text(ln)
            if "派生" in vis_ln and not any(
                p.match(vis_ln) for p, _ in _FALLBACK_DERIVE_ALLOW
            ):
                problems.append(
                    "fallback 报告出现模板外的『派生』表述 "
                    "(子女数在 fallback 恒无据; 允许的只有规模自陈行/段落标题/"
                    "无来源结论信号行(含无据行)/关系类型分布行/白名单动作句/"
                    f"『派生角色成员』定量叙述): {ln.strip()[:40]}"
                )
    elif not re.search(r"^data_mode:\s*manifest", fm, re.M):
        problems.append("frontmatter 缺 data_mode: manifest|fallback_local")
    # round-6: 与存在性检查共用 _SECTION_RE 口径 — 原整行正则让
    # `## 你现在可以做的（本轮）` 定位失败, 动作段白名单被整块跳过
    acts = re.search(
        _SECTION_RE("## 你现在可以做的") + r"(.*?)(?=^#{2}(?:[^\S\n]|$)|\Z)",
        text,
        re.M | re.S,
    )
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
        # M7 · Codex round-1 LOW: containment 拒绝有两个不同成因, 原文案一律说成
        # "路径分隔符/父目录引用或越界" —— 板名含不可见控制字符时那句话是**错的**,
        # 用户按它去查路径永远查不出问题。字符类拒绝改为点名码位 (与 recap_exam_build
        # 的诊断同源, 同一个 unsafe_name_chars 判据)。
        bad_chars = unsafe_name_chars(args.board)
        print(
            json.dumps(
                {
                    "board_exists": False,
                    "board_stem": args.board,
                    "refusal_reason": (
                        (
                            f"板名含不可用于 YAML/行级解析的字符 {', '.join(bad_chars)} "
                            "(containment 拒绝)"
                            if bad_chars
                            else "板名含路径分隔符/父目录引用或越界 (containment 拒绝)"
                        )
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
    # G5-4: scan 时刻单次计算 — signals.asof 与 source_revision.scan_at_utc
    # 必须同源同值 (年龄天数也以此为基准)
    scan_now = datetime.now(timezone.utc)
    scan_at = scan_now.strftime("%Y-%m-%dT%H:%M:%SZ")
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
            "scan_at_utc": scan_at,
            "manifest_generated_at": manifest_meta.get("generated_at"),
            "manifest_lag_seconds": manifest_meta.get("lag_seconds"),
            "manifest_stale": manifest_meta.get("stale"),
        },
        # G5-4 加性: 一梯队信号 (0 阈值, 判偏航留人)
        "signals": _build_signals(
            ledger, all_tips, dated, data_mode, scan_at, scan_now
        ),
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
