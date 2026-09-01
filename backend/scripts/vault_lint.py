#!/usr/bin/env python3
"""CARD-G8-2 (BATCH-2026-09-01-第八批) — 统一 vault lint runner (live vault 只读)。

锚点: 计划书 §3.7 Karpathy 映射表 L189 (lint 缺口: "census 零散存在, 没有统一生产门")
      + §G8 L344 (统一 /lint: orphan / 污染 / 事实支持 / 批注覆盖 / 恢复检查)。

单命令跑首批**三**项确定性检查, 逐检查报告 + 汇总退出码:

  orphan_nodes           `节点/` 下既无入链、又无 frontmatter source_board 的 md
  raw_derived_confusion  派生物混入 raw/wiki 区 (读 G8-1 台账) + `回顾-*.md` 缺 recap frontmatter
  projection_freshness   `outputs/今日复习.json` 的 generated_at 是否过期 (上海本地日)

## 退出码 (⚠️ 与同目录两个 checker 的 2 号码语义**不同**, 见下)

  0  全部检查 ok
  2  有 warn、无 fail
  1  有 fail
  3  配置/环境错误 —— lint **自己没跑成** (vault 路径不存在 / 台账 SHA 不符 / --now 非法)

⛔ 3 号码是本脚本对卡文 (只规定 0/1/2) 的**显式扩展**, 理由如实记录:
   `check_vault_doc_roles.py` 与 `check_readme_claims.py` 都用 **2 = 配置/环境错误**,
   而本卡把 2 定义成 **有 warn**。若把配置错也压进 1 或 2, 调用方就无法区分
   "vault 有问题" 与 "lint 没跑成" —— 计划书 §4 硬边界第 4 条要求
   「"空结果"与"系统故障"必须分开」, 把故障伪装成一条 warn 正是它禁止的事。
   故新开 3 号码。**这是待用户裁决项**, 不是既定裁定。

## 零写铁律 (作用域: live vault + 本仓工作区, 如实收窄)

本模块**没有任何写路径**: 全文只有 `read_text` / `read_bytes` / `iterdir` / `rglob` / `stat`,
不存在 `--fix` / `--write` 参数。`test_vault_lint.py` 有源码级写原语扫描门 + 真跑前后
shasum 逐字节比对门。

⚠️ 如实声明**不由本模块承诺**的边界:
  1. `raw_derived_confusion` 调 `check_vault_doc_roles.scan(..., with_probe=False)`。
     **必须是 False**: `with_probe=True` 会 import `app.services` 链并触发
     `jieba.initialize()`, 实测在系统临时目录写 `jieba.cache` —— 那不在 vault 内,
     但"零写"若不加限定就是过宽的声明。代价: G5/G6/G7 三类 finding 本脚本**不跑**,
     报告里逐次显式声明, 不冒充全量。
  2. 本模块被**当作库 import** 时自身的 .pyc: Python 在模块代码执行前就落盘字节码,
     第 64 行的 `sys.dont_write_bytecode = True` 管不到自己 —— 该场景只有调用方的
     `PYTHONDONTWRITEBYTECODE=1` 能挡。CLI 直跑 (本脚本的声明入口, `__main__` 不缓存
     自身) 则由第 64 行完全兜底, 实测无环境变量时 0 个 .pyc。

## freshness 口径的来源 (复制, 非 import)

唯一口径在 `backend/app/api/v1/endpoints/review_overview.py:845-860` —— 它是 `_vault_entry()`
的**内联**逻辑, 没有可 import 的独立函数, 且该文件被 W6 (CARD-G3-6b) 车道独占、本卡禁改。
故本模块**逐字复制**那段判定, 并在 `test_vault_lint.py` 用**同源锁**绑定:
构造 vault fixture → 调**真实的** `_vault_entry` 当 oracle → 断言两侧 status 逐字相等。
「抽 `is_projection_stale()` 公共函数」已登记为 W6 合并后的 micro-patch。

⛔ 复制面**比 oracle 窄**, 这条差异不许含糊 (详见 `_projection_status` docstring):
   oracle 的 `corrupt` 还包含 `_summarize()` 那几百行 v3 形状门禁 (schema_version / 容器形状 /
   buckets 对账…); 本模块只复现 **stale 判定**那一段, corrupt 只覆盖
   "读不出 / 不是 JSON object / 没有 generated_at 字段" 三类。
   同源锁因此只对**合法 v3 投影**逐字相等, 形状垃圾面不比 —— 验收单「不比什么」表有登记。
"""

from __future__ import annotations

import sys

# ⛔ 零写铁律的模块级兜底 (Codex round-1 BLOCKER-1): 必须先于**一切** import 执行 ——
# 实测无 PYTHONDONTWRITEBYTECODE 时, 仅 `python vault_lint.py --help` 就会经顶层
# `import check_vault_doc_roles` 写出 .pyc。零写不依赖调用方自觉设环境变量。
sys.dont_write_bytecode = True

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:  # 允许被 pytest / 其它 cwd 直接 import
    sys.path.insert(0, str(_SCRIPTS_DIR))

import check_vault_doc_roles as cvr  # noqa: E402  — 同目录 G8-1 台账裁判 (只 import, 禁改)

GREEN, RED, YELLOW, DIM, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[0m"

TAG = "[vault-lint]"

#: 状态三态 (与退出码的映射见 `exit_code`)
OK, WARN, FAIL = "ok", "warn", "fail"

#: 退出码
EXIT_OK, EXIT_FAIL, EXIT_WARN, EXIT_CONFIG = 0, 1, 2, 3

# ---------------------------------------------------------------------------
# freshness 口径 —— 逐字复制 review_overview.py:67/:72-93/:845-860
# ---------------------------------------------------------------------------
#: 投影相对路径 (review_overview.py:67 `_PROJECTION_REL`)
_PROJECTION_REL = ("outputs", "今日复习.json")

#: 显示时区 (review_overview.py:72-81) — 读侧与写侧子进程共用这一个字面量
_DISPLAY_TZ_NAME = "Asia/Shanghai"
try:
    from zoneinfo import ZoneInfo

    _TZ_SHANGHAI: Any = ZoneInfo(_DISPLAY_TZ_NAME)
except Exception:  # noqa: BLE001 — 无 tzdata 的最小环境 (与 oracle 同形回落)
    _TZ_SHANGHAI = timezone(timedelta(hours=8))

#: A2 生产器的确切 generated_at 形态 (review_overview.py:93) —— 数字串/纯日期/
#: 无时区值不许冒充今日
_GENERATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-](?:0\d|1[0-4]):[0-5]\d|Z)$")

# ---------------------------------------------------------------------------
# wikilink / frontmatter 窄解析 —— 复制自 canvas-vault/.claude/scripts/
# sync_board_concepts.py:49/:51 (G5-12 禁区, 只读参照; 见 `_wikilink_targets` docstring)
# ---------------------------------------------------------------------------
# ⛔ 不跨行 ([^\]\n]): Obsidian 的 wikilink 是行内的, 跨行 [[..]] 不是链接
#    (Codex round-1 HIGH-4: 跨行伪链曾让真孤儿免报)
_WIKILINK = re.compile(r"\[\[([^\]\n]+)\]\]")
_FRONTMATTER = re.compile(r"^﻿?---\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)$", re.S)

NODE_DIR = "节点"
BOARD_DIR = "原白板"
EXAM_DIR = "检验白板"
RECAP_PREFIX = "回顾-"

#: raw-derived 混淆采信的 G8-1 finding code 子集 (选取理由见 `check_raw_derived`)
CONFUSION_CODES = ("G1", "G2", "G3", "G4", "G9")
#: 报出但**不计入** finding 的扫描面 code —— "0 finding" 必须能与 "没看见" 区分开
BLIND_SPOT_CODES = ("G8", "G10", "G11")


class LintConfigError(RuntimeError):
    """配置或环境错误 → 退出码 3 (lint 自己没跑成, 不是 vault 有问题)。"""


# ---------------------------------------------------------------------------
# 报告数据结构 —— 文本与 JSON 的**唯一**真相源
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Finding:
    subject: str  #: 出问题的 vault 相对路径 / 主体
    detail: str


@dataclass
class CheckResult:
    """单个检查的结论。

    ⛔ 文本渲染与 JSON 序列化**都只读本对象**, 谁也不重新遍历一次原始数据 ——
    那样会变成两份逻辑, 卡文的「--json 与文本同源」门就测不出分叉。
    """

    name: str
    status: str  #: ok | warn | fail
    summary: str
    findings: list[Finding] = field(default_factory=list)
    #: 结论强度的如实限定 (未跑的子检查、扫描盲区、不比什么) —— 两种输出都必须带上
    notes: list[str] = field(default_factory=list)
    #: 检查专属的机读字段 (如 freshness 的 projection_status)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class LintReport:
    vault: str
    today: str
    checks: list[CheckResult]
    #: 被 --only 跳过的检查名 —— **不伪造 ok**, 显式列出"没跑"
    skipped: list[str] = field(default_factory=list)


def exit_code(report: LintReport) -> int:
    """0=全 ok / 2=有 warn 无 fail / 1=有 fail。跳过的检查不参与聚合。"""
    statuses = {c.status for c in report.checks}
    if FAIL in statuses:
        return EXIT_FAIL
    if WARN in statuses:
        return EXIT_WARN
    return EXIT_OK


def report_to_json(report: LintReport) -> dict[str, Any]:
    """JSON 视图 —— 只读 `report`, 与 `render_text` 同源。"""
    return {
        "vault": report.vault,
        "today": report.today,
        "summary": {
            "exit_code": exit_code(report),
            "checks_run": [c.name for c in report.checks],
            "checks_skipped": list(report.skipped),
            "status_counts": {s: sum(1 for c in report.checks if c.status == s) for s in (OK, WARN, FAIL)},
        },
        "checks": [
            {
                "name": c.name,
                "status": c.status,
                "summary": c.summary,
                "findings": [{"subject": f.subject, "detail": f.detail} for f in c.findings],
                "notes": list(c.notes),
                "details": dict(c.details),
            }
            for c in report.checks
        ],
    }


def render_text(report: LintReport, *, color: bool = True) -> str:
    """文本视图 —— 只读 `report`, 与 `report_to_json` 同源。

    每个检查恰一行机读状态行 `{TAG} <name> status=<status> ...`, 同源门据此解析比对。
    """

    def c(code: str, s: str) -> str:
        return f"{code}{s}{RESET}" if color else s

    hue = {OK: GREEN, WARN: YELLOW, FAIL: RED}
    out: list[str] = [
        f"{c(DIM, 'vault')} {report.vault}",
        f"{c(DIM, 'today')} {report.today} ({_DISPLAY_TZ_NAME})",
    ]
    for chk in report.checks:
        out.append(f"{TAG} {chk.name} status={c(hue[chk.status], chk.status)} {chk.summary}")
        for note in chk.notes:
            out.append(f"    {c(DIM, 'note  ' + note)}")
        for fd in chk.findings:
            out.append(f"    - {fd.subject}\n      {fd.detail}")
    for name in report.skipped:
        out.append(f"{TAG} {name} status=skipped (--only 未选中; **未跑, 非 ok**)")
    rc = exit_code(report)
    tail = {EXIT_OK: (GREEN, "全部检查 ok"), EXIT_WARN: (YELLOW, "有 warn"), EXIT_FAIL: (RED, "有 fail")}[rc]
    out.append(f"{TAG} exit={rc} {c(tail[0], tail[1])}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 共用只读 helpers
# ---------------------------------------------------------------------------
def _scan_block_reason(vault: Path, path: Path) -> str | None:
    """扫描读取的统一边界守卫: 返回拦截原因; None = 可以读。

    覆盖 (Codex round-2 HIGH-1 的三条旁路, 复用 G8-1 的 G11 判据 `cvr.
    _resolves_inside_vault` —— realpath 展开整条 symlink 链):
      - 文件自身是 symlink (无论指内指外, 保守拒读);
      - **祖先链上有 symlink** (目录 symlink 指向 vault 外时, 其后代文件自身
        is_symlink()==False, 只有整链 realpath 才能识破);
      - 解析后越出 vault (含 `..` 穿越、dangling 指外)。
    dangling 指内的文件 resolve 在内但读不了 → 由 `_read_text` 的 OSError 分支记盲区。
    """
    if path.is_symlink():
        return "symlink"
    try:
        rel = path.relative_to(vault).as_posix()
    except ValueError:
        return "outside-vault"
    if not cvr._resolves_inside_vault(vault, rel):
        return "resolves-outside-vault"
    return None


def _read_text(path: Path) -> str | None:
    """严格 UTF-8 只读。读不了返回 None (调用方登记为扫描盲区, 不静默当空)。

    ⛔ symlink 一律拒绝读 (Codex round-1 HIGH-1): 文件 symlink 会被 is_file() 接纳并
    跟随到 vault 外 —— 外部内容里的 wikilink 能藏住真孤儿。指 vault 内的 symlink
    同样拒读 (保守, 方向 = 报盲区不假绿)。祖先链/越界由 `_scan_block_reason` 在
    调用方先行拦截并记盲区 —— 本函数只是最后一道。
    """
    if path.is_symlink():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _split_frontmatter(text: str) -> tuple[str, str]:
    """→ (frontmatter 块, 正文)。复制 sync_board_concepts.py:51/:62-64 的窄解析。"""
    m = _FRONTMATTER.match(text)
    return (m.group(1), m.group(2)) if m else ("", text)


def _fm_scalar(fm: str, key: str) -> str | None:
    """顶层标量取值。复制 sync_board_concepts.py:67-86 的语义。

    `^key:` 不容前导空白 → 天然排除嵌套同名键; 取**最后一个**同名 key (YAML 后者胜);
    剥行内注释 (引号包裹的值里 `#` 不算注释)。
    ⛔ YAML null 语义 (Codex round-1 MEDIUM-1b + round-2 MEDIUM-1): 只认**裸** null 字面
    (null/Null/NULL/~), 且必须在剥引号**之前**判 —— `source_board: "null"` 是字面
    字符串 "null" (YAML 引号 = 强制字符串), 不是 null。不含 "none": PyYAML 把
    `none` 解析为普通字符串, 吞掉它 = 比 YAML 更宽 = 会误豁免真的叫 "none" 的值。
    """
    matches = re.findall(rf"^{re.escape(key)}:[ \t]*(.*)$", fm, re.M)
    if not matches:
        return None
    v = matches[-1].strip()
    if v in ("null", "Null", "NULL", "~"):
        return None  # 裸 null 字面 (先于剥引号 —— 引号包裹的是字符串, 不是 null)
    if not (v.startswith(('"', "'")) and v.endswith(('"', "'"))):
        v = re.sub(r"\s+#.*$", "", v)
    v = v.strip().strip('"').strip("'")
    return v or None


def _norm_key(name: str) -> str:
    """入链匹配键: NFC 归一 + casefold。

    ⛔ 两条都是**刻意放宽**, 方向一律是"少报孤儿":
      - NFC: macOS 文件名可能以 NFD 存储 (`é` = e + U+0301), 而 md 正文里用户打的是 NFC。
        不归一 → 同一个名字两种字节串 → 真有链的节点被判成孤儿 (假阳)。
      - casefold: Obsidian 的 wikilink 解析与 APFS 默认都大小写不敏感, `[[Agent]]` 确实
        能打开 `agent.md`。判定若大小写敏感, 会产出用户在 Obsidian 里根本复现不了的假阳。
    代价: 真实存在两个仅差大小写/归一形态的不同节点时, 一个的入链会被算到另一个头上
    (假阴)。该权衡进验收单「不比什么」表。
    """
    return unicodedata.normalize("NFC", name).casefold().strip()


#: sync_board_concepts.py 的哨兵块边界 (同源锁先例: 复制正则 + 测试对齐; 该文件
#: 位于 live vault 内禁 import)。成员行夹在 BEGIN/END 两行注释**之间**, 不是注释
#: 内容 —— 必须段级剥离, 单剥 HTML 注释够不着它 (Codex round-1 HIGH-2)。
_AUTO_BEGIN_RE = re.compile(r"^<!--\s*AUTO-GENERATED by \.claude/scripts/sync_board_concepts\.py")
_AUTO_END_RE = re.compile(r"^<!--\s*/AUTO-GENERATED")


def _strip_nonsemantic(body: str) -> str:
    """剥离正文里**非语义**的 wikilink 载体 (Codex round-1 HIGH-2/HIGH-4 +
    round-2 HIGH-4 整改)。

    两段式 (round-2 教训: 行级剥 span 会把跨行 span 的**另一半**留在别行,
    拼回后已无反引号对可配 —— 剥不到):
      1. 行级状态机只管**按行判定的**结构: AUTO-GENERATED 哨兵段 (BEGIN→END 整段)
         与 fenced code (CommonMark: closing fence 同字符且长度 ≥ opener ——
         四反引号栏内的三反引号不关闭围栏), 命中行整行丢弃;
      2. 拼回后文件级剥 code span (`+...`+ 可跨行) 与 HTML 注释
         (<!-- --> 跨行; **未闭合**按 CommonMark 剥到 EOF)。

    live 复算 (Codex round-1): 14 个节点的入链全部同时来自 source_board 与自动
    成员块, 去掉 AUTO 后 3 个节点没有其他入链 —— 陈旧自动块绝不能豁免孤儿。

    ⛔ 如实登记的剩余缝隙 (Codex round-2 HIGH-4 末项, 不处理): AUTO 段与围栏**交叉**
    的对抗构造 (手改哨兵块再夹围栏) —— 真实生成器不产出此形态, 哨兵块明写"⛔ 请勿
    手改", 解析按 AUTO 段优先; 该构造性前提登记进验收单「不比什么」。
    """
    out_lines: list[str] = []
    fence_re: re.Pattern[str] | None = None  # closing fence 全文匹配 (同字符 ≥ opener 长)
    in_auto = False
    for line in body.splitlines():
        stripped = line.strip()
        if in_auto:
            if _AUTO_END_RE.match(stripped):
                in_auto = False
            continue  # 哨兵段内整行丢弃 (含 BEGIN/END 行本身)
        if _AUTO_BEGIN_RE.match(stripped):
            in_auto = True
            continue
        if fence_re is not None:
            if fence_re.fullmatch(stripped):
                fence_re = None
            continue  # 围栏内整行丢弃
        m = re.match(r"^(`{3,}|~{3,})", stripped)
        if m:
            fence_re = re.compile(re.escape(m.group(1)[0]) + "{%d,}" % len(m.group(1)))
            continue
        out_lines.append(line)
    text = "\n".join(out_lines)
    # 文件级: code span (可跨行) + HTML 注释 (跨行; 未闭合剥到 EOF)
    text = re.sub(r"<!--.*?-->|<!--.*\Z", "", text, flags=re.S)
    text = re.sub(r"`+[^`]*`+", " ", text, flags=re.S)
    return text


def _wikilink_targets(body: str) -> set[str]:
    """正文里全部 wikilink 的 basename 集合 (已归一)。先经 `_strip_nonsemantic`。

    解析规则复制自 `canvas-vault/.claude/scripts/sync_board_concepts.py:49/:125`
    (`_WIKILINK` + `wikilink_basename`) 与 `board_manifest_service.py:132`
    (`resolve_node_id`) —— 三者本就同规则。

    ⛔ **复制而非 import**, 理由是零写铁律: `sync_board_concepts.py` 位于 **live vault 内**
       (`canvas-vault/.claude/scripts/`), import 它会在缺省时往 **live vault 里**写
       `__pycache__` —— 一个只读审计器绝不该改被审对象。
       (MEMORY `reference_importlib_pycache_writes_into_vault` 记的就是这个坑。)
       复制的代价 = 会漂; 故 `test_vault_lint.py` 有**同源锁**: 对同一批输入断言
       本函数的 basename 与真实 `wikilink_basename` / `resolve_node_id` 逐字相等。

    覆盖形态 (各有测试用例): `[[x]]` / `[[x|别名]]` / `[[节点/x]]` / `![[x]]` (embed —
    `!` 在捕获组外, 天然命中) / `[[x#小节]]` / `[[x#^块]]` / `[[x.md]]` (含 `.MD` 大写,
    Codex round-1 MEDIUM-1a)。**不**覆盖: 围栏/行内 code、HTML 注释 (含 AUTO 哨兵块)、
    跨行 `[[..]]`、空 `[[]]` —— 全部判定为非入链。
    """
    out: set[str] = set()
    for raw in _WIKILINK.findall(_strip_nonsemantic(body)):
        inner = raw.split("|", 1)[0].split("#", 1)[0].split("/")[-1].strip()
        inner = re.sub(r"\.md\Z", "", inner, flags=re.IGNORECASE)
        if inner:
            out.add(_norm_key(inner))
    return out


def _iter_md(root: Path) -> list[Path]:
    """目录下全部 md 候选 (排序稳定, 扩展名大小写不敏感, symlink 含 dangling 保留在列)。

    - suffix.lower() == ".md" 与 check_vault_doc_roles.py:1001 同口径 —— 本卡 round-2
      前用 rglob("*.md"), 对 `.MD` 文件两边存在性判定不一致 (Codex round-1 MEDIUM-1a)。
    - `is_file() or is_symlink()`: dangling symlink 的 is_file()==False, 只用 is_file()
      会把它**静默滤掉** → "0 盲区" 是"没看见" (Codex round-2 HIGH-1 第二旁路)。
      保留在列后由调用方的 `_scan_block_reason` 拦截并记盲区。
    ⛔ rglob 会跟随**目录** symlink 递归 —— 其后代不是 symlink 却越界, 必须由调用方
      对每个文件跑 `_scan_block_reason` (Codex round-2 HIGH-1 第一旁路)。
    """
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*") if (p.is_file() or p.is_symlink()) and p.suffix.lower() == ".md")


# ---------------------------------------------------------------------------
# 检查 1 — orphan_nodes
# ---------------------------------------------------------------------------
def check_orphan_nodes(vault: Path) -> CheckResult:
    """`节点/` 下既无入链、又无 frontmatter `source_board` 的 md。

    入链源 = `原白板/` + `检验白板/` + `节点/` 三处的**正文** (frontmatter 之外)。
    刻意不扫 frontmatter: `source_note` / `up` / `derived-from` 都是 frontmatter 里的
    wikilink, 把它们算作入链会让 `source_board` 豁免条件变成冗余 —— 两个条件必须各自
    可证伪, 否则去掉其中一个的变异杀不死任何门。

    自链不算: 顶层节点正文里的裸 `[[自己]]` 不构成"有人引用 A"。**仅对顶层文件适用**
    (Codex round-1 MEDIUM-1c): 子目录文件 `d1/A.md` 链 `[[d2/a]]` 在 Obsidian 里指向
    `d2/a.md` 而非自己, 一律不排除 (方向 = 少误杀入链 = 少报孤儿, 保守)。

    ⛔ 状态分级 (Codex round-1 HIGH-3 整改, "没发现" ≠ "没去查"):
       - `节点/` 目录不存在 → **fail** (检查无对象可查, 不是零孤儿);
       - 存在扫描盲区 (symlink/不可读) → **至少 warn** (盲区里的文件可能是孤儿);
       - 孤儿 → warn (治理信号, 非系统故障; 判 fail 会让真实 vault 恒红 = 死门, 待用户裁决)。
    """
    node_root = vault / NODE_DIR
    notes: list[str] = []
    blind: dict[str, str] = {}  # rel -> 拦截原因 (去重 + 带原因)

    nodes = _iter_md(node_root)
    if not node_root.is_dir():
        return CheckResult(
            name="orphan_nodes",
            status=FAIL,
            summary=f"`{NODE_DIR}/` 不存在 —— 检查无对象可查 (不是「零孤儿」)",
            findings=[Finding(f"{NODE_DIR}/", f"目录不存在, orphan 检查无法进行 —— 这不是「零孤儿」, 是「没查成」")],
            notes=[f"以 `{NODE_DIR}/` 为判定对象的检查在缺该目录的 vault 上必须显性失败"],
            details={"nodes_scanned": 0, "inbound_targets": 0},
        )

    # 入链索引: 三处正文的 wikilink basename → 来源文件集合。
    # ⛔ 每个文件先过 `_scan_block_reason` (Codex round-2 HIGH-1): 文件 symlink /
    #    symlink 祖先 / 越界解析, 一律拒读并记盲区 —— rglob 会跟随目录 symlink 递归,
    #    外部文件的后代自身不是 symlink, 只有整链 realpath 能识破。
    inbound: dict[str, set[str]] = {}
    for src_dir in (BOARD_DIR, EXAM_DIR, NODE_DIR):
        for src in _iter_md(vault / src_dir):
            blocked = _scan_block_reason(vault, src)
            if blocked:
                blind[src.relative_to(vault).as_posix()] = blocked
                continue
            text = _read_text(src)
            if text is None:
                blind[src.relative_to(vault).as_posix()] = "unreadable"
                continue
            _fm, body = _split_frontmatter(text)
            src_rel = src.relative_to(vault).as_posix()
            for target in _wikilink_targets(body):
                inbound.setdefault(target, set()).add(src_rel)

    findings: list[Finding] = []
    for node in nodes:
        own = node.relative_to(vault).as_posix()
        blocked = _scan_block_reason(vault, node)
        if blocked:
            blind[own] = blocked
            continue
        # ⛔ 检查时排除**自身**贡献 (Codex round-2 MEDIUM-1a): d1/A 链 [[d2/a]] 时,
        #    target "a" 的来源集合是 {d1/A.md} —— 对 A 自己这是自贡献, 不构成豁免;
        #    对 d2/a.md 才是有效入链。顶层裸自链 [[A]] 与子目录同名跨链由此**统一**处理,
        #    不再需要"仅顶层适用"的特判。
        sources = inbound.get(_norm_key(node.stem), set()) - {own}
        if sources:
            continue
        text = _read_text(node)
        if text is None:
            blind[own] = "unreadable"
            continue
        fm, _body = _split_frontmatter(text)
        if _fm_scalar(fm, "source_board"):
            continue
        findings.append(
            Finding(
                own,
                f"无来自 {BOARD_DIR}/ {EXAM_DIR}/ {NODE_DIR}/ 正文的 wikilink 入链 "
                f"(自身出链不计), 且 frontmatter 无 source_board",
            )
        )

    if blind:
        notes.append(
            f"扫描盲区: {len(blind)} 个文件未参与判定 (原因见前缀), "
            + ", ".join(f"{rel}[{why}]" for rel, why in sorted(blind.items())[:5])
            + " —— 这些文件可能是孤儿也可能不是, 结论按此打折"
        )
    notes.append(
        "不比: frontmatter 里的 wikilink (source_note/up/derived-from) 不算入链; "
        "自身出链不豁免自己 (含顶层裸自链); 围栏/行内 code、HTML 注释 (含 AUTO-GENERATED "
        "哨兵段)、跨行 [[..]] 不算入链; 大小写与 NFC/NFD 归一后匹配 (方向=少报孤儿); "
        "symlink 文件、symlink 目录的后代、解析越界文件拒读并记盲区"
    )
    status = WARN if (findings or blind) else OK
    return CheckResult(
        name="orphan_nodes",
        status=status,
        summary=f"{len(nodes)} 个节点, {len(findings)} 个孤儿" + (f", {len(blind)} 个盲区" if blind else ""),
        findings=findings,
        notes=notes,
        details={
            "nodes_scanned": len(nodes),
            "inbound_targets": len(inbound),
            "blind_spots": len(blind),
            "blind_detail": dict(sorted(blind.items())),
        },
    )


# ---------------------------------------------------------------------------
# 检查 2 — raw_derived_confusion
# ---------------------------------------------------------------------------
def check_raw_derived(vault: Path) -> CheckResult:
    """派生物混入 raw/wiki 区 (读 G8-1 台账) + `回顾-*.md` 缺 recap frontmatter。

    数据来自 `check_vault_doc_roles.scan(..., with_probe=False)` —— **不重新实现**台账语义。

    采信的 finding 子集 `CONFUSION_CODES` 与理由:
      G1 未登记目录        新目录未被任何 dir_glob 命中 = 新的一类文档混进 vault, role 未定
      G2 未登记根级文件    同上, 根级面
      G3 frontmatter type 不在其归属条目白名单内 —— **本子集的核心**: `节点/`(role=wiki)
                          的白名单是 concept/(none), 一个 `type: recap` 的派生物混进去
                          正是"raw-derived 混淆"的机械定义
      G4 doc_type 野值     type 落在 rag_index 覆盖面下却不在白名单 = 野值入库面
      G9 未登记根级 md     落到兜底行但未逐个登记 —— 兜底行断不了 owner/role/retention

    **不**计入的 code 与理由 (不是漏掉, 是语义不同, 但仍在 notes 里报出):
      G8/G10/G11 是**扫描面**问题 (symlink 子树未递归 / 枚举失败 / 越界), 不是混淆;
                 但绝不能不报 —— 否则 "0 finding" 是"没看见"而不是"没问题"
      G5/G6/G7   需要真实准入函数求值 (probe 档), 本脚本因零写铁律走 with_probe=False,
                 **本次未验证**, 报告逐次声明

    ⛔ 判 fail 的只有一种情况: 台账契约本身坏了 (load_rules 抛 ConfigError) —— 那时
       抛 `LintConfigError` 走退出码 3, 不在本函数里伪装成一条 finding。
    """
    try:
        data = cvr.load_rules()
    except cvr.ConfigError as exc:
        raise LintConfigError(f"G8-1 台账不可用 ({exc}) —— raw_derived 检查无法进行") from exc
    try:
        res = cvr.scan(data, vault, with_probe=False)
    except cvr.ConfigError as exc:
        raise LintConfigError(str(exc)) from exc

    findings = [
        Finding(fd.subject, f"[{fd.code}] {fd.detail}")
        for fd in res.findings
        if fd.code in CONFUSION_CODES and fd.blocking
    ]
    exempted = sum(1 for fd in res.findings if fd.code in CONFUSION_CODES and not fd.blocking)

    # 回顾报告的 recap frontmatter (台账管不到的一条: 文件名前缀 → 期望 type)
    recap_bad = 0
    recap_blind: dict[str, str] = {}
    for md in _iter_md(vault):
        if not md.name.startswith(RECAP_PREFIX):
            continue
        # ⛔ 与 orphan 同一条边界守卫 (Codex round-2 HIGH-1 第三旁路):
        #    指向 vault 外的 回顾-* symlink 会被 read_frontmatter_type 跟随读取 ——
        #    先拦截记盲区, 不读不判 (越界细节由 G8-1 的 G10/G11 判红)。
        blocked = _scan_block_reason(vault, md)
        if blocked:
            recap_blind[md.relative_to(vault).as_posix()] = blocked
            continue
        # parser=None: 强制走 cvr 的保守回落解析, 不 import 写侧 (jieba 会写临时缓存)
        ftype = cvr.read_frontmatter_type(md, parser=None)
        if ftype != "recap":
            recap_bad += 1
            findings.append(
                Finding(
                    md.relative_to(vault).as_posix(),
                    f"`{RECAP_PREFIX}*` 回顾报告的 frontmatter type={ftype!r}, 期望 'recap' "
                    f"—— 派生报告不带派生标记, 会被当成用户 wiki 内容",
                )
            )
    notes: list[str] = [
        f"采信 finding 子集: {'/'.join(CONFUSION_CODES)}; 台账 = {cvr.ROLES_YAML.name} (SHA 契约已校验)",
        "本次**未验证** G5/G6/G7 (台账双列与真实准入函数是否一致) —— 需 probe 档, "
        "而 probe 的 import 链会写系统临时缓存, 与本卡零写铁律冲突",
    ]
    if recap_blind:
        notes.append(
            "recap 扫描盲区 (未读未判): " + ", ".join(f"{rel}[{why}]" for rel, why in sorted(recap_blind.items())[:5])
        )
    blind = [fd for fd in res.findings if fd.code in BLIND_SPOT_CODES]
    if blind:
        notes.append(
            f"扫描面问题 {len(blind)} 条 (不计入 finding, 但结论按此打折): "
            + "; ".join(f"[{fd.code}] {fd.subject}" for fd in blind[:5])
        )
    if exempted:
        notes.append(f"另有 {exempted} 条命中子集但被台账 known_gaps 豁免, 未计入")
    for msg in res.info:
        notes.append(f"台账扫描 info: {msg}")

    return CheckResult(
        name="raw_derived_confusion",
        status=WARN if findings else OK,
        summary=f"{res.files_seen} 文件 / {res.dirs_seen} 目录, {len(findings)} 条混淆 (含 {recap_bad} 条 recap 标记缺失)",
        findings=findings,
        notes=notes,
        details={
            "files_seen": res.files_seen,
            "dirs_seen": res.dirs_seen,
            "codes_counted": list(CONFUSION_CODES),
            "recap_missing_type": recap_bad,
            "recap_blind": dict(sorted(recap_blind.items())),
            "blind_spots": len(blind),
            "probe_skipped": res.probe_skipped,
        },
    )


# ---------------------------------------------------------------------------
# 检查 3 — projection_freshness
# ---------------------------------------------------------------------------
def _is_stale(generated_at: Any, today: date) -> bool:
    """⛔ 逐字复制 `review_overview.py:849-857` 的 stale 判定。

    只认 A2 生产器的确切形态 (带时区秒级); 数字串/纯日期/无时区值不许冒充今日;
    解析中的任何异常 (含 fromisoformat 通过但 astimezone 溢出的 OverflowError)
    都按 stale 降级, 绝不逃逸成异常。
    """
    stale = True
    try:
        if isinstance(generated_at, str) and _GENERATED_AT_RE.fullmatch(generated_at):
            gen = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            stale = gen.astimezone(_TZ_SHANGHAI).date() != today
    except Exception:  # noqa: BLE001 — 畸形时间按 stale, 不装新鲜也不炸
        stale = True
    return stale


def _projection_status(vault: Path, today: date) -> tuple[str, str | None, Any]:
    """→ (status, error, generated_at)。status 词汇与 oracle `_vault_entry` **完全一致**:
    `no_projection` / `corrupt` / `stale` / `ok` —— 同源锁据此逐字比对。

    ⛔ corrupt 面**比 oracle 窄**, 如实声明: oracle 在 stale 判定之前还要过
       `_summarize()` 的严格 v3 形状门禁 (schema_version==3 / 五个容器形状 /
       boards·buckets 对账 / 非有限数拒收…), 任何不符即 corrupt。本函数**不复制**
       那几百行 (复制必漂, 且 W6 独占该文件), 只覆盖四类:
       读不出 / 不是 JSON object / 缺 generated_at 键 / generated_at 非字符串
       (最后这类的同语义是实测钉的: int 20260831 → oracle=corrupt, 不是 stale)。
       故同源锁只在**合法 v3 投影**上成立; 其余形状垃圾面两侧可能分歧
       (oracle=corrupt, 本函数可能=stale/ok) —— 验收单「不比什么」表登记。
    """
    proj = vault.joinpath(*_PROJECTION_REL)
    raw = _read_text(proj)
    if raw is None:
        if not proj.exists():
            return "no_projection", None, None
        return "corrupt", "读取失败 (非 UTF-8 / 权限)", None
    try:
        payload = json.loads(raw)
    except (ValueError, RecursionError) as e:
        return "corrupt", f"{type(e).__name__}: {str(e)[:200]}", None
    if not isinstance(payload, dict):
        return "corrupt", "投影根节点不是 JSON object", None
    if "generated_at" not in payload:
        return "corrupt", "投影缺 generated_at 字段", None
    gen = payload["generated_at"]
    # oracle 的 `_summarize` (:678-680) 对非字符串 generated_at 抛 ValueError → corrupt
    # (实测: int 20260831 → oracle=corrupt 而非 stale)。必须同语义, 否则同源锁在此分叉。
    if not isinstance(gen, str):
        return "corrupt", f"generated_at 应为字符串, 实为 {type(gen).__name__}", None
    return ("stale" if _is_stale(gen, today) else "ok"), None, gen


def check_projection_freshness(vault: Path, today: date) -> CheckResult:
    """`outputs/今日复习.json` 的 generated_at 是否是上海本地的今日。

    状态分级 (**待用户裁决**):
      ok            → ok
      stale         → warn  (只是今天还没跑推送, 不是坏)
      no_projection → warn  (该 vault 从没跑过推送 —— 新 vault 的正常初态)
      corrupt       → fail  (投影文件坏了, 下游 Web UI / 推送会拿不到数据 = 真故障)
    """
    status, error, gen = _projection_status(vault, today)
    mapped = {"ok": OK, "stale": WARN, "no_projection": WARN, "corrupt": FAIL}[status]
    detail = {
        "ok": f"generated_at={gen!r} 是 {today} 的投影",
        "stale": f"generated_at={gen!r} 不是 {today} ({_DISPLAY_TZ_NAME}) 的投影",
        "no_projection": f"{'/'.join(_PROJECTION_REL)} 不存在 —— 该 vault 尚未跑过推送",
        "corrupt": f"投影不可用: {error}",
    }[status]
    findings = [] if status == "ok" else [Finding("/".join(_PROJECTION_REL), detail)]
    return CheckResult(
        name="projection_freshness",
        status=mapped,
        summary=f"projection_status={status}",
        findings=findings,
        notes=[
            "口径复制自 review_overview.py:845-860 (`_vault_entry` 内联逻辑, 无可 import 的函数; "
            "该文件 W6 独占禁改), 由 test_vault_lint.py 的同源锁绑定",
            "不比: corrupt 面比 oracle 窄 —— 本检查不复现 `_summarize()` 的 v3 形状门禁, "
            "只判 读不出/非 object/缺 generated_at",
        ],
        details={"projection_status": status, "generated_at": gen, "error": error},
    )


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------
#: 检查注册表 —— name → (说明, 是否需要 today)
CHECKS: dict[str, str] = {
    "orphan_nodes": "节点/ 下既无入链、又无 source_board 的 md",
    "raw_derived_confusion": "派生物混入 raw/wiki 区 (读 G8-1 台账) + 回顾-*.md 缺 recap frontmatter",
    "projection_freshness": "outputs/今日复习.json 的 generated_at 是否过期",
}


def run_checks(vault: Path, today: date, *, only: list[str] | None = None) -> LintReport:
    """跑选中的检查。`only=None` = 全跑。未跑的检查进 `skipped`, **不伪造 ok**。"""
    if not vault.is_dir():
        raise LintConfigError(f"vault 根目录不存在: {vault}")
    selected = list(CHECKS) if not only else [n for n in CHECKS if n in only]
    checks: list[CheckResult] = []
    for name in selected:
        if name == "orphan_nodes":
            checks.append(check_orphan_nodes(vault))
        elif name == "raw_derived_confusion":
            checks.append(check_raw_derived(vault))
        elif name == "projection_freshness":
            checks.append(check_projection_freshness(vault, today))
    return LintReport(
        vault=str(vault),
        today=today.isoformat(),
        checks=checks,
        skipped=[n for n in CHECKS if n not in selected],
    )


def _utcnow() -> datetime:
    """时钟缝 (Codex round-1 MEDIUM-2): 唯一的取当前时刻处, 测试 patch 它来锁
    「无 --now 的默认分支走上海日, 不是宿主本地日 / date.today()」。"""
    return datetime.now(timezone.utc)


def resolve_today(now: str | None) -> date:
    """`--now` → 上海本地日。

    ⛔ 不用 `date.today()`: 那是**进程本地日**。MEMORY 记过一条真实缺陷 —— 容器 TZ 为空时
       写侧产出了"昨天"的日期。今日口径必须显式绑定 Asia/Shanghai, 与
       review_overview.py:855 的 `astimezone(_TZ_SHANGHAI).date()` 同一条规则。
    """
    if now is None:
        return _utcnow().astimezone(_TZ_SHANGHAI).date()
    try:
        dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LintConfigError(f"--now 不是合法 ISO-8601 时间: {now!r} ({exc})") from exc
    if dt.tzinfo is None:  # 无时区 → 按上海本地时间解释 (与显示时区一致, 不引入第二种默认)
        dt = dt.replace(tzinfo=_TZ_SHANGHAI)
    try:
        return dt.astimezone(_TZ_SHANGHAI).date()
    except (OverflowError, OSError) as exc:
        raise LintConfigError(f"--now 时间超出可表示范围: {now!r} ({exc})") from exc


_EPILOG = f"""
检查项与状态分级 (ok/warn/fail 的判定规则, Codex round-1 MEDIUM-4 要求写进 --help):
  orphan_nodes            {CHECKS["orphan_nodes"]}
                            warn = 有孤儿或有扫描盲区 (symlink/不可读, 盲区里的文件未参与判定);
                            fail = `节点/` 目录不存在 (检查没查成, 不是零孤儿)
  raw_derived_confusion   {CHECKS["raw_derived_confusion"]}
                            warn = 有混淆 finding (G1/G2/G3/G4/G9 或 回顾-* 缺 type: recap);
                            本检查无 fail 态
  projection_freshness    {CHECKS["projection_freshness"]}
                            warn = stale (今天还没跑推送) 或 no_projection;
                            fail = corrupt (投影文件坏, 下游拿不到数据)

退出码:
  0  全部检查 ok
  2  有 warn、无 fail
  1  有 fail
  3  配置/环境错误 —— lint 自己没跑成 (vault 路径不存在 / 台账 SHA 不符 / --now 非法 /
      参数用法错误)

⚠️ 3 号码是本脚本对卡文 (只规定 0/1/2) 的显式扩展, 待用户裁决:
   同目录 check_vault_doc_roles.py / check_readme_claims.py 都用 2 = 配置/环境错误,
   而本卡把 2 定义成"有 warn"。若把配置错压进 1 或 2, 调用方就无法区分
   "vault 有问题" 与 "lint 没跑成"。参数用法错误也归 3 (Codex round-1 HIGH-6:
   argparse 默认 exit(2) 会与"有 warn"撞码)。

只读: 本脚本对 vault 只有读取, 无 --fix / --write; 不写 __pycache__ (模块级
sys.dont_write_bytecode 兜底, 不依赖调用方环境变量)。
"""


class _LintArgumentParser(argparse.ArgumentParser):
    """argparse 默认 error() 走 sys.exit(2) —— 与"有 warn"的 2 撞码
    (Codex round-1 HIGH-6)。用法错误 = "lint 没跑成" = 配置/环境错误族, 统一退 3。"""

    def error(self, message: str):  # type: ignore[override]
        self.print_usage(sys.stderr)
        print(f"{RED}{TAG} 用法错误: {message}{RESET}", file=sys.stderr)
        raise SystemExit(EXIT_CONFIG)


def main(argv: list[str] | None = None) -> int:
    ap = _LintArgumentParser(
        prog="vault_lint.py",
        description="CARD-G8-2 统一 vault lint (live vault 只读, 三检查)",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--vault", type=Path, required=True, help="vault 根目录 (含 节点/ 原白板/ outputs/)")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出 (stdout 纯 JSON, 与文本同源)")
    ap.add_argument("--now", default=None, help="注入'现在' (ISO-8601); 缺省取当前 Asia/Shanghai 日")
    ap.add_argument(
        "--only",
        action="append",
        choices=sorted(CHECKS),
        default=None,
        help="只跑指定检查 (可重复)。未选中的显式记为 skipped, 不算 ok",
    )
    args = ap.parse_args(argv)

    try:
        report = run_checks(args.vault.expanduser(), resolve_today(args.now), only=args.only)
    except LintConfigError as exc:
        print(f"{RED}{TAG} 配置/环境错误: {exc}{RESET}", file=sys.stderr)
        return EXIT_CONFIG

    if args.json:
        print(json.dumps(report_to_json(report), ensure_ascii=False, indent=2))
    else:
        print(render_text(report, color=sys.stdout.isatty()))
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
