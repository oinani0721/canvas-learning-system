#!/usr/bin/env python3
"""board-split · split_preview.py — 拆分建议 preview 引擎（CARD-G5-2 · 只读）v2

对指定原白板生成「建议拆成哪些节点」的 preview：候选单元清单（建议节点名 /
来源锚点 file+行区间+标题路径 / 与 节点/ 扁平池的重名标记 / 已派生重叠标记），
输出版本化 JSON（schema_version=1）+ 自渲染人读 MD（含「确认后将发生的
wikilink 插入」**展示性** diff，显式标注未执行）。

⛔ 红线（G5-2 越界禁令）：
  - **零写侧**：只读 vault 既有文件；唯一写入 = --out-dir（缺省 <vault>/outputs/）
    下的两个 preview 产物。不建节点、不动原板、不落派生文件。
  - scripts-only：无 SKILL.md、无 LLM 叙述层；确认/创建 = G5-10；稳定 ID 契约 = G5-3。
  - 确定性：同输入二跑输出逐字节相等（零时间戳零随机）。

写侧物理防御（Codex 二轮 HIGH-1 加固）：
  - out-dir 路径必须**全程无 symlink 组件**（realpath 与词法规范化不一致即拒绝）；
  - out-dir 只做单级 mkdir（父目录必须已存在——不静默创建祖先链）；
  - 目标文件已存在且硬链接数 >1 → 拒绝（防 hardlink 把写引到别处）；
  - 写入用 O_NOFOLLOW 原子拒绝 symlink 目标（消除 is_symlink→write 竞态窗口）；
  - 已知边界（用户态不可判定，如实声明不掩饰）：bind mount / 覆盖挂载重定向无法检测。

读侧 containment（Codex 二轮 HIGH-2 加固）：
  - 板名与 Concepts 成员名同一套非法字符/路径逃逸校验；越界成员**跳过并留痕**；
  - 板文件 / 种子文件本体是 symlink → 拒绝/跳过（不跟随链接读 vault 外内容）。

命名真相源 = frontend/obsidian-plugin/src/node-derivation.ts:32 deriveConceptStub
（Python 移植；金样本双向断言见 backend/tests/skills/test_split_preview.py）。
v2 等价性精修（Codex 二轮 HIGH-3）：
  - 空白折叠与 trim 用 **ECMAScript 空白集**（含 U+FEFF；不含 Python 特有的
    U+001C-001F——JS \\s 与 Python \\s 的集合差已按 JS 口径固化）；
  - 词边界回退阈值按 **UTF-16 code unit** 下标比较（TS lastIndexOf 语义；
    astral 字符前缀不再产生码点/单元偏差）。
剩余显式偏差（全部声明，无未声明项）：
  1. 空输入 fallback：TS 用时间戳（非确定），本引擎为「同输入二跑 diff 空」硬门
     改用锚点 sha1 前 6 位；
  2. 重名判定做 NFC 归一（TS existsCheck 按字节精确）——macOS NFD 落盘文件与
     NFC 候选名同形不同字节，不归一会漏报重名，此为 preview 侧的自觉增强；
  3. 本 preview 内候选互撞检测（claimed 集合）为 TS 无对应物的确定性补充；
  4. TS 9+ 重名 throw；preview 标 conflict_unresolvable 并停用该条的展示性 diff；
  5. **输入预处理**：preview 在调 derive_concept_stub **之前**先 clean_heading()
     剥离标题编号（1.2 / 一、）与时间戳标记（[MM:SS]()）——TS 管道传的是用户选中
     原文无此步。等价性宣称范围 = slug 函数本体（同输入同输出），不含此预处理
     （对照: 「1. Topic」直传 TS 得 1.-Topic? 不——TS 先句号分割得「1」；preview
     清洗后得 Topic。这是 preview 侧对标题形态输入的自觉适配，Codex 三轮点名后显式declare）。

生成段剥离**只按确定性标记**（不做启发式内容判断）：
  1. YAML frontmatter（文件头 --- 对）
  2. AUTO-GENERATED 注释对（`<!-- AUTO-GENERATED` … `/AUTO-GENERATED … -->`；
     缺闭合按确定性规则吞到 EOF）
  3. 代码 fence（``` 对，fence 内标题不算小节；缺闭合同上）
  4. `Recent Activity` 标题节（到下一个同级或更高级标题为止）
另：普通 HTML 注释（含跨行）不参与小节切分与正文计数、也不产生派生重叠证据
（注释是说明不是内容——特征值板实测教训）。
候选单元判据（确定性常量，非 LLM）：##+ 级小节，剥离后直属正文
≥ MIN_PLAIN_LINES 行且 ≥ MIN_PLAIN_CHARS 字符。纯脚手架板 → 0 单元 + 诚实自陈。

用法:
    python3 split_preview.py --vault <vault> --board <板名stem> [--out-dir DIR] [--max-units N]
退出码: 0 成功（含 0 单元）/ 1 输入非法、板不存在或写侧防御拒绝
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

SCHEMA_VERSION = 1
GENERATOR = "board-split/split_preview.py v3.0 (CARD-G5-2 read-only preview)"
MAX_NAME_LEN = 40  # deriveConceptStub 截断上限（TS 同值）
MIN_PLAIN_LINES = 2  # 小节直属正文最少行数（确定性门槛）
MIN_PLAIN_CHARS = 60  # 小节直属正文最少字符数（确定性门槛）
DEFAULT_MAX_UNITS = 30  # 规模门缺省阈值

NOT_EXECUTED = (
    "本 preview 只读生成：未创建任何节点、未修改任何既有 vault 文件"
    "（唯一写入 = out-dir 下两个 preview 产物，缺省落 <vault>/outputs/）；"
    "wikilink 插入 diff 仅为展示（确认/创建/插链属 G5-10）。"
)

# ───────────────────────── slug 移植（node-derivation.ts:32） ─────────────────────────

#: TS: /[\\/:*?"<>|#^[\]]/g
_ILLEGAL = re.compile(r'[\\/:*?"<>|#^\[\]]')
#: ECMAScript WhiteSpace ∪ LineTerminator（JS \s / trim() 的集合, 含 U+FEFF;
#: ⛔ 不用 Python \s——两者对 U+FEFF / U+001C-001F / U+0085 的归属不同）
_JS_WS = "\t\v\f\u0020\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff\r\n"
_JS_WS_RUN = re.compile(f"[{_JS_WS}]+")
_JS_TRIM = re.compile(f"^[{_JS_WS}]+|[{_JS_WS}]+$")
#: TS: selected.split(/[\n。.！!？?；;]/u)[0]
_SENT_SPLIT = re.compile(r"[\n。.！!？?；;]")


def _js_trim(s: str) -> str:
    return _JS_TRIM.sub("", s)


def _clean_for_slug(selected: str) -> str:
    """TS 步骤 1-2: 取首句 → trim → 去非法字符 → 空白折叠为 - → 去首尾 -（JS 空白集）。"""
    head = _js_trim(_SENT_SPLIT.split(selected)[0])
    if not head:
        return ""
    cleaned = _ILLEGAL.sub("", head)
    cleaned = _JS_WS_RUN.sub("-", cleaned)
    return re.sub(r"^-+|-+$", "", cleaned)


def _hard_cut(s: str, max_len: int = MAX_NAME_LEN) -> str:
    """P4 修复**前**的硬砍（Array.from 码点级）。现网存量截断名
    （Eigenvalues-are-special-vectors-that-sat）即此规则产物——保留为
    重名/重叠比对的历史锚，金样本测试双向钉住。"""
    chars = list(s)
    return s if len(chars) <= max_len else "".join(chars[:max_len])


def _utf16_len(s: str) -> int:
    """字符串的 UTF-16 code unit 数（astral 字符计 2——TS 字符串下标口径）。"""
    return sum(2 if ord(c) > 0xFFFF else 1 for c in s)


def _truncate_unicode_aware(s: str, max_len: int = MAX_NAME_LEN) -> str:
    """TS truncateUnicodeAware（现行规则，含 P4 词边界回退）。
    切片按 Array.from 码点取前 max_len 个（与 TS 相同）；
    回退阈值按 **UTF-16 code unit** 下标比较（TS `cut.lastIndexOf("-")` 语义——
    astral 前缀时码点下标与 code unit 下标不同, v2 已按 TS 口径精确移植）。"""
    chars = list(s)
    if len(chars) <= max_len:
        return s
    cut = "".join(chars[:max_len])
    last_dash_cp = cut.rfind("-")
    if last_dash_cp == -1:
        return cut
    if _utf16_len(cut[:last_dash_cp]) >= max_len // 2:
        return cut[:last_dash_cp]
    return cut


def _fallback_stub(anchor: str) -> str:
    """⛔ 显式偏差 1: TS fallbackStub() 用当前时间戳（非确定性）。本引擎受
    「同输入二跑 diff 空」硬门约束, 改用来源锚点 sha1 前 6 位——同锚点恒同名。"""
    return "derived-" + hashlib.sha1(anchor.encode("utf-8")).hexdigest()[:6]


def derive_concept_stub(selected: str, anchor: str = "") -> str:
    """deriveConceptStub 的 Python 移植。"""
    if not selected:
        return _fallback_stub(anchor)
    cleaned = _clean_for_slug(selected)
    if not cleaned:
        return _fallback_stub(anchor)
    truncated = _truncate_unicode_aware(cleaned, MAX_NAME_LEN)
    if not truncated:
        return _fallback_stub(anchor)
    return truncated


# ───────────────────────── 输入防御 ─────────────────────────

_BAD_NAME = re.compile(r'[\\/`$"\']|\.\.|^\.|[\x00-\x1f]')


def validate_board_name(board: str) -> None:
    if not board or _BAD_NAME.search(board):
        raise SystemExit(f"✗ 板名含非法字符或路径逃逸: {board!r}")


def member_name_ok(name: str) -> bool:
    """Concepts 成员名 containment（与板名同一套判据, 越界成员跳过留痕）。"""
    return bool(name) and not _BAD_NAME.search(name)


# ───────────────────────── 生成段剥离（确定性标记） ─────────────────────────

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_RECENT_ACTIVITY_RE = re.compile(r"^#{1,6}\s+Recent Activity\b")


def strip_generated(lines: list[str]) -> list[bool]:
    """返回 stripped 掩码（True = 该行属生成段/标记段, 不参与小节与正文判定）。
    缺闭合的 fence / AUTO 对按确定性规则吞到 EOF（宁可少判候选不误判）。"""
    n = len(lines)
    stripped = [False] * n
    # 1. frontmatter
    if n and lines[0].strip() == "---":
        for i in range(1, n):
            if lines[i].strip() == "---":
                for j in range(0, i + 1):
                    stripped[j] = True
                break
    # 2/3. AUTO-GENERATED 对 + 代码 fence（线性扫描, fence 优先级最高）
    in_fence = in_auto = False
    for i, ln in enumerate(lines):
        if stripped[i]:
            continue
        t = ln.strip()
        if t.startswith("```"):
            stripped[i] = True
            in_fence = not in_fence
            continue
        if in_fence:
            stripped[i] = True
            continue
        if not in_auto and t.startswith("<!-- AUTO-GENERATED"):
            in_auto = True
        if in_auto:
            stripped[i] = True
            if "/AUTO-GENERATED" in t:
                in_auto = False
    # 4. Recent Activity 节（在非剥离行上判标题）
    i = 0
    while i < n:
        if not stripped[i]:
            m = _HEADING_RE.match(lines[i])
            if m and _RECENT_ACTIVITY_RE.match(lines[i]):
                level = len(m.group(1))
                j = i + 1
                while j < n:
                    m2 = _HEADING_RE.match(lines[j]) if not stripped[j] else None
                    if m2 and len(m2.group(1)) <= level:
                        break
                    j += 1
                for k in range(i, j):
                    stripped[k] = True
                i = j
                continue
        i += 1
    return stripped


def comment_mask(lines: list[str], stripped: list[bool]) -> list[bool]:
    """普通 HTML 注释掩码（含跨行——注释续行不带 <!-- 前缀, 特征值板实测教训）。
    v2: 该掩码同时约束 小节切分 / 正文计数 / 派生重叠证据（注释不是内容）。"""
    mask = [False] * len(lines)
    in_c = False
    for i, ln in enumerate(lines):
        if stripped[i]:
            continue
        t = ln.strip()
        if not in_c and "<!--" in t:
            in_c = True
        if in_c:
            mask[i] = True
            if "-->" in t:
                in_c = False
    return mask


# ───────────────────────── 小节切分与候选判定 ─────────────────────────

#: 直属正文的「非正文」行首（确定性）: 引用/标题/表格/图片/HTML注释/无序列表标记
_NON_PLAIN = re.compile(r"^(>|#|\||!\[|<!--|[-+*]\s)")
#: 水平分割线（--- / *** / ___）不算正文（特征值板实测: hr 曾把链接段凑成假候选）
_HR_LINE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")

#: 标题清洗: 尾部时间戳标记 [MM:SS]() / [H:MM:SS]() 与首部中文/数字编号
_TS_MARK = re.compile(r"\s*\[\d{1,2}:\d{2}(?::\d{2})?\]\(\)\s*$")
_NUM_PREFIX = re.compile(r"^(?:[一二三四五六七八九十百]+、|\d+(?:\.\d+)*[.、]?\s+)")


def clean_heading(text: str) -> str:
    return _NUM_PREFIX.sub("", _TS_MARK.sub("", text).strip()).strip()


def sections_of(
    lines: list[str], stripped: list[bool], comments: list[bool]
) -> list[dict]:
    """全部标题小节（含层级路径与原始行号, 1-based）。
    v2: 注释掩码行上的 # 不算标题（注释里的标题曾能截断真实小节/伪造小节）。"""
    heads = []
    for i, ln in enumerate(lines):
        if stripped[i] or comments[i]:
            continue
        m = _HEADING_RE.match(ln)
        if m:
            heads.append({"level": len(m.group(1)), "text": m.group(2), "line": i + 1})
    out = []
    for idx, h in enumerate(heads):
        end = len(lines)
        for h2 in heads[idx + 1 :]:
            if h2["level"] <= h["level"]:
                end = h2["line"] - 1
                break
        direct_end = heads[idx + 1]["line"] - 1 if idx + 1 < len(heads) else len(lines)
        path = []
        lvl = h["level"]
        for prev in reversed(heads[:idx]):
            if prev["level"] < lvl:
                path.append(prev["text"])
                lvl = prev["level"]
        out.append(
            {
                **h,
                "end": end,
                "direct_end": min(direct_end, end),
                "path": list(reversed(path)),
            }
        )
    return out


def passes_content_gate(
    sec: dict, lines: list[str], stripped: list[bool], comments: list[bool]
) -> bool:
    """直属正文达标判定（确定性门槛, 与标题层级无关）。"""
    plain, chars = 0, 0
    for i in range(sec["line"], sec["direct_end"]):
        if stripped[i] or comments[i]:
            continue
        t = lines[i].strip()
        if not t or _NON_PLAIN.match(t) or _HR_LINE.match(t):
            continue
        plain += 1
        chars += len(t)
    return plain >= MIN_PLAIN_LINES and chars >= MIN_PLAIN_CHARS


_DERIVED_CALLOUT = re.compile(r"已派生为 \[\[节点/([^\]|]+)\]\]")


def derived_names_in(
    sec: dict, lines: list[str], stripped: list[bool], comments: list[bool]
) -> list[str]:
    """小节内派生重叠证据。v2: 生成段/注释里的 callout 不算证据（fence 里的示例
    或注释里的历史记录不能制造 overlap）。"""
    found: list[str] = []
    for i in range(sec["line"] - 1, sec["end"]):
        if stripped[i] or comments[i]:
            continue
        for m in _DERIVED_CALLOUT.finditer(lines[i]):
            if m.group(1) not in found:
                found.append(m.group(1))
    return found


# ───────────────────────── 板成员（Concepts 目录）解析 ─────────────────────────

_CONCEPT_LINE = re.compile(r"^-\s+\[\[节点/([^\]|]+)\]\]\s+—\s+(种子|派生自)")


def parse_members(board_lines: list[str]) -> tuple[list[str], list[str]]:
    """→ (seeds, derived)。Concepts 目录本身是生成态, 但它是成员真相源——
    此处只取结构（谁是种子）, 不把目录文本当候选内容。"""
    seeds, derived = [], []
    for ln in board_lines:
        m = _CONCEPT_LINE.match(ln.strip())
        if m:
            (seeds if m.group(2) == "种子" else derived).append(m.group(1))
    return seeds, derived


# ───────────────────────── 重名解析（resolveUniqueNodeName 语义） ─────────────────────────


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def resolve_name(stub: str, pool: set[str], claimed: set[str]) -> dict:
    """池内重名 → _2.._9（TS resolveUniqueNodeName 同规）; 9+ 诚实标不可解。
    显式偏差 2/3（见文件头）: NFC 归一比对 + 本 preview claimed 互撞检测。
    conflict_with 报池内**实际**文件名（NFD 落盘的文件按其真实字节名报）。"""
    key = nfc(stub)
    pool_by_nfc = {nfc(x): x for x in sorted(pool)}
    taken = set(pool_by_nfc) | {nfc(x) for x in claimed}
    hit_actual = pool_by_nfc.get(key)
    info = {
        "name_conflict": hit_actual is not None,
        "conflict_with": f"节点/{hit_actual}.md" if hit_actual is not None else None,
        "conflict_in_preview": hit_actual is None and key in {nfc(x) for x in claimed},
        "conflict_unresolvable": False,
    }
    if key not in taken:
        info["resolved_name"] = stub
        return info
    for i in range(2, 10):
        cand = f"{stub}_{i}"
        if nfc(cand) not in taken:
            info["resolved_name"] = cand
            return info
    info["resolved_name"] = stub
    info["conflict_unresolvable"] = (
        True  # 显式偏差 4: TS 此处 throw; preview 标注并停用其展示 diff
    )
    return info


# ───────────────────────── 主流程 ─────────────────────────


def sha256_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def collect_candidates(file_rel: str, text: str, basis: str) -> list[dict]:
    lines = text.splitlines()
    stripped = strip_generated(lines)
    comments = comment_mask(lines, stripped)
    secs = sections_of(lines, stripped, comments)

    def emit(sec: dict, b: str) -> dict:
        anchor = f"{file_rel}:{sec['line']}"
        stub = derive_concept_stub(clean_heading(sec["text"]), anchor=anchor)
        overlaps = derived_names_in(sec, lines, stripped, comments)
        return {
            "suggested_name": stub,
            "source_anchor": {
                "file": file_rel,
                "line_start": sec["line"],
                "line_end": sec["end"],
                "heading_path": sec["path"] + [sec["text"]],
            },
            "derived_overlap": {
                "overlapping": bool(overlaps),
                "existing_nodes": overlaps,
            },
            "basis": b,
            "_heading_raw": sec["text"],
            "_heading_level": sec["level"],
        }

    out = [
        emit(sec, basis)
        for sec in secs
        if sec["level"] >= 2 and passes_content_gate(sec, lines, stripped, comments)
    ]
    # 种子无 ##+ 达标小节 → 整篇回退（Fundamentals 实况: 只有 # 一级标题,
    # 真派生痕迹全在 # 节内——0 候选会把真实拆分源漏掉）
    if not out and basis == "seed-note-section":
        out = [
            emit(sec, "seed-note-whole")
            for sec in secs
            if sec["level"] == 1 and passes_content_gate(sec, lines, stripped, comments)
        ]
    return out


def _contained_regular_file(p: Path, vault_real: str) -> bool:
    """v3 (Codex 三轮 H2): 叶子非 symlink 之外, realpath 必须仍在 vault 物理树内
    (目录级 symlink 把 节点/原白板 指到外部时, 叶子 is_symlink()==False 也会越界)。
    已知边界: 检查与读取之间的替换竞态 (TOCTOU) 用户态无法完全关闭, 如实声明。"""
    if p.is_symlink():
        return False
    return os.path.realpath(p).startswith(vault_real + os.sep)


def build_preview(vault: Path, board: str, max_units: int) -> dict:
    vault_real = os.path.realpath(vault)
    for d in ("原白板", "节点"):
        dp = vault / d
        if dp.is_symlink():
            raise SystemExit(f"✗ {d}/ 目录本身是 symlink, 拒绝越界读取: {dp}")
    board_file = vault / "原白板" / f"{board}.md"
    if not _contained_regular_file(board_file, vault_real):
        if board_file.exists() or board_file.is_symlink():
            raise SystemExit(
                f"✗ 板文件是 symlink 或物理位置越出 vault, 拒绝读取: {board_file}"
            )
    if not board_file.exists():
        stems = sorted(p.stem for p in (vault / "原白板").glob("*.md"))
        raise SystemExit(f"✗ 原白板/{board}.md 不存在。可选的板: {stems}")

    # v3 (Codex 三轮 MEDIUM): 每个来源文件只读一次, sha 对同一份字节计算 —
    # 消除「候选正文与声明 SHA 来自不同读取版本」的不一致窗口
    board_bytes = board_file.read_bytes()
    board_sha = hashlib.sha256(board_bytes).hexdigest()
    board_text = board_bytes.decode("utf-8")
    board_lines = board_text.splitlines()
    seeds_raw, derived_members = parse_members(board_lines)

    sources = [
        {
            "file": f"原白板/{board}.md",
            "role": "board_body",
            "sha256": board_sha,
        }
    ]
    candidates = collect_candidates(
        f"原白板/{board}.md", board_text, "board-body-section"
    )

    seeds: list[str] = []
    for seed in seeds_raw:
        if not member_name_ok(seed):
            # H2: 成员名 containment — 越界名不拼路径不读文件, 跳过留痕
            sources.append(
                {
                    "file": f"节点/{seed}.md",
                    "role": "seed",
                    "sha256": None,
                    "skipped": "成员名含非法字符/路径逃逸, 越界拒扫",
                }
            )
            continue
        sp = vault / "节点" / f"{seed}.md"
        if sp.exists() and not _contained_regular_file(sp, vault_real):
            sources.append(
                {
                    "file": f"节点/{seed}.md",
                    "role": "seed",
                    "sha256": None,
                    "skipped": "种子文件是 symlink 或物理位置越出 vault, 拒绝跟随",
                }
            )
            continue
        if not sp.exists():
            sources.append(
                {
                    "file": f"节点/{seed}.md",
                    "role": "seed",
                    "sha256": None,
                    "missing": True,
                }
            )
            continue
        seed_bytes = sp.read_bytes()
        seeds.append(seed)
        sources.append(
            {
                "file": f"节点/{seed}.md",
                "role": "seed",
                "sha256": hashlib.sha256(seed_bytes).hexdigest(),
            }
        )
        candidates += collect_candidates(
            f"节点/{seed}.md", seed_bytes.decode("utf-8"), "seed-note-section"
        )

    node_dir = vault / "节点"
    pool = {p.stem for p in node_dir.glob("*.md")} if node_dir.is_dir() else set()

    total = len(candidates)
    over = total > max_units
    kept = candidates[:max_units]

    claimed: set[str] = set()
    final = []
    for i, c in enumerate(kept, start=1):
        res = resolve_name(c["suggested_name"], pool, claimed)
        claimed.add(res["resolved_name"])
        final.append(
            {
                "index": i,
                "suggested_name": c["suggested_name"],
                "resolved_name": res["resolved_name"],
                "name_conflict": res["name_conflict"],
                "conflict_with": res["conflict_with"],
                "conflict_in_preview": res["conflict_in_preview"],
                "conflict_unresolvable": res["conflict_unresolvable"],
                "source_anchor": c["source_anchor"],
                "derived_overlap": c["derived_overlap"],
                "basis": c["basis"],
                "_heading_raw": c["_heading_raw"],
                "_heading_level": c["_heading_level"],
            }
        )

    scaffold_only = total == 0
    scaffold_note = ""
    if scaffold_only:
        seed_part = (
            "板无种子成员"
            if not seeds_raw
            else f"{len(seeds_raw)} 份种子笔记剥离生成段后亦无达标小节"
        )
        scaffold_note = (
            "剥离生成段（AUTO-GENERATED 对 / 代码 fence / Recent Activity）后, "
            f"板体无实质内容小节; {seed_part}。本板当前为纯脚手架, 可拆单元 = 0——这不是失败, "
            "是诚实结论: 拆分素材应先进入种子笔记/板正文。"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "generator": GENERATOR,
        "board": board,
        "board_file": f"原白板/{board}.md",
        "board_sha256": board_sha,
        "sources": sources,
        "board_members": {"seeds": seeds_raw, "derived": derived_members},
        "existing_node_pool_count": len(pool),
        "scaffold_only": scaffold_only,
        "scaffold_note": scaffold_note,
        "candidates": final,
        "scale_gate": {
            "threshold": max_units,
            "total_candidates": total,
            "kept": len(kept),
            "over_threshold": over,
        },
        "not_executed_disclaimer": NOT_EXECUTED,
    }


# ───────────────────────── 人读 MD 渲染（纯自渲染, 只消费 JSON dict） ─────────────────────────


def render_md(data: dict) -> str:
    L: list[str] = []
    L.append(f"# 拆分建议 preview · {data['board']}")
    L.append("")
    L.append(
        "> ⛔ 本文件由 `board-split/scripts/split_preview.py` **只读**生成（CARD-G5-2）。"
    )
    L.append(
        "> **未创建任何节点、未修改任何既有 vault 文件**（唯一写入 = 本 preview 两个产物）。"
    )
    L.append(
        "> 下方 wikilink 插入 diff 仅为展示——真正的确认/创建/插链属 G5-10，届时逐条经你确认后才会发生。"
    )
    L.append(
        f"> schema_version: {data['schema_version']} · 板文件 sha256: `{data['board_sha256'][:12]}…`"
    )
    L.append("")
    sg = data["scale_gate"]
    L.append("## 规模自陈")
    L.append("")
    seeds = data["board_members"]["seeds"]
    L.append(
        f"- 候选单元: **{sg['kept']}**"
        + (
            f"（总 {sg['total_candidates']}，⚠ 已按规模门截断保留文档序前 {sg['threshold']} 个）"
            if sg["over_threshold"]
            else ""
        )
    )
    L.append(
        f"- 来源: 板体 + 种子笔记 {len(seeds)} 份（{('、'.join(seeds)) if seeds else '无'}）"
    )
    L.append(
        f"- 现有 节点/ 扁平池: {data['existing_node_pool_count']} 个（重名判定基准, NFC 归一）"
    )
    if data["scaffold_only"]:
        L.append("")
        L.append("> [!warning]+ 纯脚手架自陈（0 单元）")
        L.append(f"> {data['scaffold_note']}")
    for s in data["sources"]:
        if s.get("missing"):
            L.append(f"- ⚠ 种子缺失: `{s['file']}`（Concepts 目录声明了但文件不在）")
        if s.get("skipped"):
            L.append(f"- ⛔ 种子跳过: `{s['file']}`（{s['skipped']}）")
    L.append("")
    if data["candidates"]:
        L.append("## 候选单元清单")
        L.append("")
        L.append("| # | 建议节点名 | 来源锚点 | 标题路径 | 重名 | 已派生重叠 |")
        L.append("|---|---|---|---|---|---|")
        for c in data["candidates"]:
            a = c["source_anchor"]
            anchor = f"`{a['file']}:{a['line_start']}-{a['line_end']}`"
            path = " › ".join(a["heading_path"])
            if c["conflict_unresolvable"]:
                dup = "⛔ 9+ 重名不可解"
            elif c["name_conflict"]:
                dup = f"⚠ 撞 `{c['conflict_with']}` → 建议 `{c['resolved_name']}`"
            elif c["conflict_in_preview"]:
                dup = f"⚠ 与本 preview 前序候选同名 → 建议 `{c['resolved_name']}`"
            else:
                dup = "无"
            ov = (
                "、".join(c["derived_overlap"]["existing_nodes"])
                if c["derived_overlap"]["overlapping"]
                else "无"
            )
            L.append(
                f"| {c['index']} | `{c['resolved_name']}` | {anchor} | {path} | {dup} | {ov} |"
            )
        L.append("")
        L.append("## 确认后将发生的 wikilink 插入（展示性 diff · ⛔ 未执行）")
        L.append("")
        L.append(
            "> 每条 = 若你在 G5-10 确认创建该节点，源文件该小节标题下**将会**插入的派生 callout。"
        )
        L.append(
            "> 本轮零写入；关系类型（示例用 related_to）与是否插入均由确认阶段决定。"
        )
        L.append("")
        for c in data["candidates"]:
            a = c["source_anchor"]
            L.append(f"### {c['index']} · {c['resolved_name']}")
            L.append("")
            if c["conflict_unresolvable"]:
                L.append(
                    "⛔ 该候选与 节点/ 池 9+ 重名不可自动解（TS 同场景直接报错）——"
                )
                L.append(
                    "**不提供展示性 diff**，须先人工改名/合并后再进入 G5-10 确认。"
                )
                L.append("")
                continue
            L.append(f"目标位置: `{a['file']}:{a['line_start']}`")
            L.append("")
            L.append("```diff")
            L.append(f"  {'#' * c['_heading_level']} {c['_heading_raw']}")
            L.append(
                f"+ > [!relation/related_to]+ 已派生为 [[节点/{c['resolved_name']}]] · 相关"
            )
            L.append(
                "+ > （展示性 preview·未执行——关系类型与是否插入由 G5-10 确认阶段决定）"
            )
            L.append("```")
            L.append("")
    L.append("---")
    L.append("")
    L.append(f"> {data['not_executed_disclaimer']}")
    L.append("")
    return "\n".join(L)


# ───────────────────────── 写侧物理防御 ─────────────────────────


def assert_symlink_free(p: Path) -> None:
    """路径全程无 symlink 组件: realpath 与词法规范化必须一致（HIGH-1: 祖先
    symlink 会把词法上在 out-dir 内的写重定向到别处）。"""
    lexical = Path(os.path.normpath(p.absolute()))
    physical = Path(os.path.realpath(p))
    if lexical != physical:
        raise SystemExit(
            f"✗ 输出目录路径含 symlink 组件, 拒绝写入（词法 {lexical} ≠ 物理 {physical}）"
        )


def safe_write_text(p: Path, content: str) -> None:
    """v3 单 FD 写入 (Codex 三轮 H1): O_NOFOLLOW open（不带 O_TRUNC）→ 对**同一 FD**
    fstat 验 nlink → 通过后才 ftruncate+write——nlink 检查与写入之间零换身窗口。
    已知边界（如实声明, 用户态无法完全关闭）: 祖先目录在检查与 open 之间被整体
    替换的竞态; bind mount / 覆盖挂载重定向不可判定。"""
    flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(p), flags, 0o644)
    except OSError as e:
        raise SystemExit(
            f"✗ 写入目标被 symlink 布防或不可写, 拒绝写入: {p} ({e})"
        ) from e
    try:
        st = os.fstat(fd)
        if st.st_nlink > 1:
            raise SystemExit(
                f"✗ 写入目标存在多重硬链接 (nlink={st.st_nlink}), 拒绝写入: {p}"
            )
        os.ftruncate(fd, 0)
    except SystemExit:
        os.close(fd)
        raise
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> int:
    ap = argparse.ArgumentParser(description="拆分建议 preview（只读, CARD-G5-2）")
    ap.add_argument("--vault", required=True)
    ap.add_argument("--board", required=True)
    ap.add_argument(
        "--out-dir",
        default=None,
        help="产物目录（缺省 <vault>/outputs; 父目录必须已存在）",
    )
    ap.add_argument("--max-units", type=int, default=DEFAULT_MAX_UNITS)
    args = ap.parse_args()

    validate_board_name(args.board)
    vault = Path(args.vault).resolve()
    if not (vault / "原白板").is_dir():
        raise SystemExit(f"✗ 不是合法 vault（缺 原白板/）: {vault}")

    data = build_preview(vault, args.board, args.max_units)
    md = render_md(data)
    for c in data["candidates"]:
        c.pop("_heading_raw", None)
        c.pop("_heading_level", None)

    out_dir = Path(args.out_dir) if args.out_dir else vault / "outputs"
    if not out_dir.parent.exists():
        raise SystemExit(f"✗ 输出目录的父目录不存在, 拒绝创建祖先链: {out_dir.parent}")
    # v3 (Codex 三轮 H1): 先验祖先链无 symlink **再** mkdir —— 否则 mkdir 会先穿过
    # symlink 在物理目标处创建目录, 形成「拒绝但已写」
    assert_symlink_free(out_dir.parent)
    if not out_dir.exists():
        out_dir.mkdir(exist_ok=True)  # 单级创建, 不静默造祖先 (H1)
    assert_symlink_free(out_dir)
    json_path = out_dir / f"split-preview-{args.board}.json"
    md_path = out_dir / f"split-preview-{args.board}.md"
    safe_write_text(json_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    safe_write_text(md_path, md)
    print(f"✓ preview 已生成（只读引擎, 未动 vault 既有文件）: {json_path} / {md_path}")
    print(
        f"  候选 {data['scale_gate']['kept']}/{data['scale_gate']['total_candidates']}"
        f"{' · ⚠ 已截断' if data['scale_gate']['over_threshold'] else ''}"
        f"{' · 纯脚手架 0 单元' if data['scaffold_only'] else ''}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
