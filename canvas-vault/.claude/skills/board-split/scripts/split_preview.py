#!/usr/bin/env python3
"""board-split · split_preview.py — 拆分建议 preview 引擎（CARD-G5-2 · 只读）v4
                                   + 分层稳定 ID 与 diff 契约（CARD-G5-3）

对指定原白板生成「建议拆成哪些节点」的 preview：候选单元清单（建议节点名 /
来源锚点 file+行区间+标题路径 / 与 节点/ 扁平池的重名标记 / 已派生重叠标记 /
**分层稳定 ID + 内容指纹**），输出版本化 JSON（schema_version=2）+ 自渲染人读 MD
（含「确认后将发生的 wikilink 插入」**展示性** diff，显式标注未执行）。

第二模式（G5-3）：`--diff OLD.json NEW.json` 比对两份 preview，输出
added / changed / removed / moved 四态差异 JSON + 人读 MD。

⛔ 红线（G5-2 越界禁令，G5-3 沿用）：
  - **零写侧**：只读 vault 既有文件；唯一写入 = --out-dir（缺省 <vault>/outputs/）
    下的 preview / diff 产物。不建节点、不动原板、不落派生文件。
  - scripts-only：无 SKILL.md、无 LLM 叙述层；确认/创建 = G5-10。
  - 确定性：同输入二跑输出逐字节相等（零时间戳零随机）。

━━━ G5-3 分层稳定 ID（契约全文 docs/design/split-stable-id-contract.md）━━━
  L1 身份键（抗行号漂移）= sha256(命名空间 ‖ 来源文件相对路径 ‖ 归一化标题路径 ‖
     同路径出现序号 ‖ basis) 前 16 位，形如 `bsa1-<16hex>`（段以长度前缀编码，
     对任意字节单射）。**键里没有任何行号**——行号漂移不换 ID 是结构性保证，不是巧合。
  L2 内容指纹（供 changed 判定）= sha256(小节 span 经 rstrip/丢空行/NFC 归一)
     前 16 位，形如 `cf1-<16hex>`。覆盖面两条边界都是有意的：
       ✅ **含**代码 fence 与 HTML 注释——它们是用户内容。跟着剥离掩码走的话，
          小节内代码块整块改写时指纹纹丝不动，diff 报「无变化」而实际全变了。
       ⛔ **不含** frontmatter / AUTO-GENERATED / Recent Activity（机器生成段）——
          板尾 Recent Activity 会落在最后一条候选的 span 内，不排除的话每派生一次
          节点就凭空多一条 changed(content)。

  哪些操作**会**换 ID（诚实边界，逐条见契约文档 §4.1）：改标题实词 / 改祖先标题实词 /
  小节搬到另一文件 / 层级调整改变祖先链 / 同名同父小节增删致序号位移 / 板文件改名 /
  种子笔记从「整篇回退候选」变成有 ##+ 小节（basis 变）/ 非行尾时间戳标记被改 /
  给标题行加行内 HTML 注释。
  哪些**不**换 ID：行号漂移、正文任意改动、小节整体调序、标题编号与**行尾** [MM:SS]()
  标记变化、NFC/NFD 差异（含文件名等价改名）、行尾空白与空行增删、机器刷新板尾生成段、
  resolved_name 因 节点/ 池变化而改、层级调整但祖先链不变。

  ⛔ 身份先天歧义（契约 §4.4）：同一文件里归一化标题路径**逐字相同**的多个小节，
  其 ID 绑的是「第 N 个槽位」而非内容单元——调序会让身份跟着槽位走。这类候选带
  identity_ambiguous=true，diff 显式告警，且**不具 provenance 效力**：G5-10 不得
  为它们持久化 split_stable_id。单跑 preview 只有位置与内容两种区分信息，
  选位置则调序换身份、选内容则正文一改就换 ID——二者必居其一，v1 选前者并标红旗。

  与 backend/app/services/board_manifest_service.py:57
  `ID_STABILITY = "basename_v1_will_upgrade_in_1_5"` 的关系（显式声明，防两套 ID
  互相冒充）：board_manifest 的 node_id/board_id = **文件 basename**，指向**已存在的
  节点文件**；本模块 stable_id 指向**原板/种子里的一段来源锚点**（尚未成为文件的
  候选单元）。两者不同层、不可互换，故本模块自陈独立值 `split_anchor_v1`。桥在
  G5-10：确认创建时把 stable_id 写进新节点 frontmatter `split_stable_id`，于是
  basename ↔ 锚点建立可迁移映射；board_manifest 未来从 basename_v1 升级时，该
  frontmatter 字段即现成迁移源。**本卡不改 board_manifest 任何行为。**

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
  4. `Recent Activity` 标题节（到下一个同级或更高级标题为止）——
     ⛔ 该扫描**先避开普通 HTML 注释**（G5-3 Codex round-2 HIGH-1）：注释里写着
     `## Recent Activity` 时不再把它当真标题，否则会一路吞到下一个同级标题为止，
     **连同注释后面的真实用户正文一起**，被吞的正文不进指纹 → 用户改了它 diff 报「无变化」。
另：普通 HTML 注释（含跨行）不参与小节切分与正文计数、也不产生派生重叠证据
（注释是说明不是内容——特征值板实测教训）。
候选单元判据（确定性常量，非 LLM）：##+ 级小节，剥离后直属正文
≥ MIN_PLAIN_LINES 行且 ≥ MIN_PLAIN_CHARS 字符。纯脚手架板 → 0 单元 + 诚实自陈。

用法:
    # preview 模式（G5-2）
    python3 split_preview.py --vault <vault> --board <板名stem> [--out-dir DIR] [--max-units N]
    # diff 模式（G5-3）—— 不读 vault，只比对两份 preview JSON
    python3 split_preview.py --diff OLD.json NEW.json [--out-dir DIR]
退出码: 0 成功（含 0 单元）/ 1 输入非法、板不存在、diff 输入不合契约或写侧防御拒绝
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

SCHEMA_VERSION = 2  # G5-3 加性升级: v1 字段全部保留, 只追加 stable_id 三件套
MIN_DIFF_SCHEMA = 2  # 稳定 ID 从 v2 起提供 —— diff 拒绝 v1 输入 (无 ID 可比)
DIFF_SCHEMA_VERSION = 1  # diff 产物自己的 schema (与 preview schema 独立编号)
GENERATOR = "board-split/split_preview.py v4.0 (CARD-G5-2 preview + CARD-G5-3 stable-id/diff, read-only)"

#: 稳定 ID 命名空间。⛔ 与 backend/app/services/board_manifest_service.py:57 的
#: ID_STABILITY = "basename_v1_will_upgrade_in_1_5" **不是同一层键**, 不可互换:
#:   - board_manifest: node_id/board_id = 文件 basename → 指向**已存在的节点文件**;
#:   - 本模块 stable_id: 指向**原板/种子里的一段来源锚点** → 该候选还不是文件。
#: 两者靠 G5-10 搭桥: 确认创建时把 stable_id 写进新节点 frontmatter `split_stable_id`,
#: 于是 basename ↔ 锚点建立可迁移映射; board_manifest 将来从 basename_v1 升级时,
#: 该 frontmatter 字段即现成迁移源。本卡不改 board_manifest 任何行为。
STABLE_ID_NAMESPACE = "split-anchor/v1"
ID_STABILITY = "split_anchor_v1"  # ≠ board_manifest 的 basename_v1_will_upgrade_in_1_5
STABLE_ID_PREFIX = "bsa1-"  # board-split anchor v1
FINGERPRINT_PREFIX = "cf1-"  # content fingerprint v1
_HASH_HEX = 16  # 截断长度 (64 bit): 单板候选量级 ≤ 数百, 碰撞面可忽略且引擎自检重复
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


#: 单个文件名的字节上限（APFS/ext4 同为 255）。产物名 = 前缀 + 板名 + 后缀,
#: 不预检就会「先建好 out-dir, 再在写入时 ENAMETOOLONG」——拒绝但已留空目录。
MAX_FILENAME_BYTES = 255


def validate_board_name(board: str) -> None:
    if not board or _BAD_NAME.search(board):
        raise SystemExit(f"✗ 板名含非法字符或路径逃逸: {board!r}")


def validate_product_filename(board: str, prefix: str) -> None:
    """产物文件名长度预检 —— 必须在 prepare_out_dir **之前**调用。"""
    for suffix in (".json", ".md"):
        n = len(f"{prefix}{board}{suffix}".encode("utf-8"))
        if n > MAX_FILENAME_BYTES:
            raise SystemExit(
                f"✗ 板名过长, 产物文件名 {n} 字节超出上限 {MAX_FILENAME_BYTES}: {prefix}{board}{suffix}"
            )


def member_name_ok(name: str) -> bool:
    """Concepts 成员名 containment（与板名同一套判据, 越界成员跳过留痕）。"""
    return bool(name) and not _BAD_NAME.search(name)


# ───────────────────────── 生成段剥离（确定性标记） ─────────────────────────

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_RECENT_ACTIVITY_RE = re.compile(r"^#{1,6}\s+Recent Activity\b")


#: strip_generated_detail 的行分类。G5-3 需要区分「机器生成段」与「代码 fence」——
#: 前者刷新是机器行为（不该算用户内容变更），后者是用户内容（改了必须被感知）。
GEN_NONE, GEN_FRONTMATTER, GEN_AUTO, GEN_FENCE, GEN_RECENT = 0, 1, 2, 3, 4
#: 机器生成、非用户内容的三类 —— 内容指纹忽略它们（G5-3 Codex/多镜头审查发现:
#: 末尾 Recent Activity / AUTO 段落在最后一条候选的 span 内, 每派生一次节点
#: 就凭空多一条 changed(content)）
MACHINE_KINDS = (GEN_FRONTMATTER, GEN_AUTO, GEN_RECENT)


def strip_generated_detail(lines: list[str]) -> list[int]:
    """逐行分类（GEN_* 常量）。`strip_generated` 是它的布尔投影 —— 单一真相源，
    避免「候选判定用一套掩码、指纹用另一套复制品」的漂移。
    缺闭合的 fence / AUTO 对按确定性规则吞到 EOF（宁可少判候选不误判）。"""
    n = len(lines)
    kind = [GEN_NONE] * n
    # 1. frontmatter
    if n and lines[0].strip() == "---":
        for i in range(1, n):
            if lines[i].strip() == "---":
                for j in range(0, i + 1):
                    kind[j] = GEN_FRONTMATTER
                break
    # 2/3. AUTO-GENERATED 对 + 代码 fence（线性扫描, fence 优先级最高）
    in_fence = in_auto = False
    for i, ln in enumerate(lines):
        if kind[i]:
            continue
        t = ln.strip()
        if t.startswith("```"):
            kind[i] = GEN_FENCE
            in_fence = not in_fence
            continue
        if in_fence:
            kind[i] = GEN_FENCE
            continue
        if not in_auto and t.startswith("<!-- AUTO-GENERATED"):
            in_auto = True
        if in_auto:
            kind[i] = GEN_AUTO
            if "/AUTO-GENERATED" in t:
                in_auto = False
    # 4. Recent Activity 节（在非剥离行上判标题）
    # ⛔ 必须先算一遍普通 HTML 注释掩码再扫（Codex round-2 HIGH-1 实证）：
    # 注释里写着 `## Recent Activity` 时，原实现会把它当真标题、一路吞到下一个同级
    # 标题为止 —— **连同注释后面的用户正文一起吞掉**。被吞的正文不进指纹，
    # 于是用户改了那段正文，diff 却报「无变化」。注释里的标题不是标题（这本就是
    # G5-2 comment_mask 的既有语义），只是 RA 这一趟原先没享受到。
    pre_comment = [False] * n
    in_c = False
    for i, ln in enumerate(lines):
        if kind[i]:
            continue
        t = ln.strip()
        if not in_c and "<!--" in t:
            in_c = True
        if in_c:
            pre_comment[i] = True
            if "-->" in t:
                in_c = False
    i = 0
    while i < n:
        if not kind[i] and not pre_comment[i]:
            m = _HEADING_RE.match(lines[i])
            if m and _RECENT_ACTIVITY_RE.match(lines[i]):
                level = len(m.group(1))
                j = i + 1
                while j < n:
                    m2 = (
                        _HEADING_RE.match(lines[j])
                        if not kind[j] and not pre_comment[j]
                        else None
                    )
                    if m2 and len(m2.group(1)) <= level:
                        break
                    j += 1
                for k in range(i, j):
                    kind[k] = GEN_RECENT
                i = j
                continue
        i += 1
    return kind


def strip_generated(lines: list[str]) -> list[bool]:
    """返回 stripped 掩码（True = 该行属生成段/标记段, 不参与小节与正文判定）。"""
    return [k != GEN_NONE for k in strip_generated_detail(lines)]


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


# ───────────────────── 分层稳定 ID 与内容指纹（CARD-G5-3） ─────────────────────


def normalize_heading_text(text: str) -> str:
    """标题文本 → 身份键用的归一化形态。

    clean_heading（剥编号 `1.2 ` / `一、` 与 `[MM:SS]()` 标记）→ NFC → 空白折叠为
    单空格 → trim。为什么必须吸收编号：真实讲义板重编号（中间插一节，后面全体 +1）
    是高频操作，不吸收则「稳定 ID」名存实亡。为什么必须 NFC：macOS 落盘会把带调
    拼音等分解成 NFD，同一标题两种字节形态必须归一到同一个 ID。
    """
    return _JS_WS_RUN.sub(" ", nfc(clean_heading(text))).strip()


def normalize_heading_path(path: list[str]) -> list[str]:
    return [normalize_heading_text(x) for x in path]


def compute_stable_id(
    file_rel: str, heading_path_normalized: list[str], occurrence: int, basis: str
) -> str:
    """L1 身份键。⛔ 输入里**没有行号**——行号漂移不换 ID 是结构性保证。

    occurrence = 同一文件内、归一化标题路径**逐字相同**的小节的出现序号（1-based,
    文档序，按**全部小节**计数而非仅候选——这样「原本不达标的重复小节后来达标」
    不会给它后面的同名小节改号）。没有它，同名同父的两个小节会撞成一个 ID，
    候选↔ID 的双射破裂，diff 会把两条互相吞掉。

    basis = 候选来源形态（board-body-section / seed-note-section / seed-note-whole）。
    进键的理由（Codex round-1 HIGH-2 实证）：种子笔记从 `# 讲义 + 正文` 变成
    `## 讲义 + 同正文` 时，归一化路径同为 ["讲义"]、内容逐字不变，只有 basis 从
    seed-note-whole 变 seed-note-section —— 不进键的话 diff 会报 unchanged，
    而契约 §4.1 #7 声明的是 removed+added。进键即让声明成真。

    载荷编码用**长度前缀**（`len:段`，段间以 U+0000 相连），不依赖「标题里不会出现
    分隔符」这类假设 —— Codex round-2 指出「标题正文不可能含 U+0000」不成立
    （UTF-8 文件可以包含它并构造出拼接碰撞）。长度前缀让编码对任意字节内容都单射。
    """
    segs = [
        STABLE_ID_NAMESPACE,
        nfc(file_rel),
        *heading_path_normalized,
        str(occurrence),
        basis,
    ]
    payload = "\x00".join(f"{len(seg)}:{seg}" for seg in segs)
    return (
        STABLE_ID_PREFIX
        + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:_HASH_HEX]
    )


def compute_content_fingerprint(
    lines: list[str], line_start: int, line_end: int, machine: list[bool] | None = None
) -> str:
    """L2 内容指纹：小节 span（不含标题行本身）的内容哈希，供 changed 判定。

    范围 = 1-based (line_start, line_end]，与 source_anchor 声明的区间一致；
    含子小节 ⇒ 改子小节正文会让父子两条候选都判 changed（候选可嵌套的既有事实，
    契约文档已声明，不是指纹引入的新问题）。

    归一化只做无语义项：每行 rstrip → 丢纯空行 → NFC → \\n 连接。

    覆盖面（两条边界都是有意的，不是随手定的）：
      ✅ **含**代码 fence 与 HTML 注释 —— 它们是用户内容。若跟着候选判定的剥离掩码
         走，小节内代码块整块改写会纹丝不动，diff 报「无变化」而实际全变了，那是掩饰。
      ⛔ **不含** frontmatter / AUTO-GENERATED 段 / Recent Activity 段（`machine` 掩码）
         —— 它们是**机器**刷新的，不是用户改的。不排除的话，板尾的 Recent Activity
         会落在最后一条候选的 span 内（剥离后的标题不算标题，前一节的 end 因而吞到
         EOF），于是每派生一次节点就凭空多一条 changed(content)。
         这条是 G5-3 多镜头审查 + Codex 实证发现的（原实现把两类混为一谈）。

    `machine` 省略时退化为「span 内全部行」——只有直接调用本函数的测试会走这条路。
    """
    body: list[str] = []
    for i in range(line_start, min(line_end, len(lines))):
        if machine is not None and i < len(machine) and machine[i]:
            continue
        t = lines[i].rstrip()
        if not t:
            continue
        body.append(nfc(t))
    return (
        FINGERPRINT_PREFIX
        + hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest()[:_HASH_HEX]
    )


# ───────────────────────── 主流程 ─────────────────────────


def sha256_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def collect_candidates(file_rel: str, text: str, basis: str) -> list[dict]:
    lines = text.splitlines()
    # stripped 走**公开函数** strip_generated（而不是就地由 kinds 投影）——
    # G5-2 的反事实常驻测试靠打桩 strip_generated 来验证剥离契约确实在生效,
    # 绕过它会让那道门失去抓力（本卡重构时当场被它抓到, 保留为教训）。
    stripped = strip_generated(lines)
    machine = [k in MACHINE_KINDS for k in strip_generated_detail(lines)]
    comments = comment_mask(lines, stripped)
    secs = sections_of(lines, stripped, comments)

    # G5-3: occurrence 按**全部小节**计数（不只候选）——原本不达标的重复小节后来
    # 达标时，不会连累它后面的同名小节改号
    seen_paths: dict[tuple[str, ...], int] = {}
    for sec in secs:
        norm = tuple(normalize_heading_path(sec["path"] + [sec["text"]]))
        seen_paths[norm] = seen_paths.get(norm, 0) + 1
        sec["_norm_path"] = list(norm)
        sec["_occurrence"] = seen_paths[norm]
    # 同路径出现 >1 次 = 身份**先天歧义**（Codex round-1 BLOCKER-1）：这一组里
    # ID 绑的是「第 N 个槽位」而非内容单元, 调序会让身份跟着槽位走。标出来,
    # 让 diff 与 G5-10 都能拒绝把它当 provenance 级身份用。
    for sec in secs:
        sec["_ambiguous_group"] = seen_paths[tuple(sec["_norm_path"])]

    def emit(sec: dict, b: str) -> dict:
        # ⛔ fallback 锚点**不含行号**（Codex round-1 HIGH-1 / 多镜头审查同点）:
        # 用行号会让「归一化后标题为空」的小节在纯行号漂移时改名, diff 误报
        # changed(name), 与契约 §4.2「行号漂移不算变化」直接冲突。
        anchor = f"{file_rel}\x00{'/'.join(sec['_norm_path'])}\x00{b}\x00{sec['_occurrence']}"
        stub = derive_concept_stub(clean_heading(sec["text"]), anchor=anchor)
        overlaps = derived_names_in(sec, lines, stripped, comments)
        return {
            "stable_id": compute_stable_id(
                file_rel, sec["_norm_path"], sec["_occurrence"], b
            ),
            "stable_id_basis": {
                "namespace": STABLE_ID_NAMESPACE,
                "file": file_rel,
                "heading_path_normalized": sec["_norm_path"],
                "occurrence": sec["_occurrence"],
                "basis": b,
            },
            "identity_ambiguous": sec["_ambiguous_group"] > 1,
            "ambiguous_group_size": sec["_ambiguous_group"],
            "content_fingerprint": compute_content_fingerprint(
                lines, sec["line"], sec["end"], machine
            ),
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
    # ⛔ 同一份种子只扫一次（G5-3 审查发现）：`## Concepts` 里同一个种子被列两行
    # （重复行，或 NFC / NFD 两种写法指向 macOS 上同一个文件）会让同一文件被扫两遍，
    # 于是 (file, path, occurrence, basis) 四元组逐字相同 → stable_id 必撞 →
    # 自检拒绝输出，整块板拿不到 preview。相对 G5-2 这是**可用性倒退**，
    # 所以在源头去重：按 NFC 归一后的成员名保留首次出现，被跳过的那行在 sources 留痕。
    seen_members: set[str] = set()
    for seed in seeds_raw:
        key = nfc(seed)
        if key in seen_members:
            sources.append(
                {
                    "file": f"节点/{seed}.md",
                    "role": "seed",
                    "sha256": None,
                    "skipped": "Concepts 目录重复列出同一份种子（NFC 归一后同名），只扫首次出现",
                }
            )
            continue
        seen_members.add(key)
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

    # ⛔ 身份自检必须跑在**规模门截断之前**（G5-3 审查发现的旁路）：只查 kept 的话,
    # 截断把撞车的两条切开时自检直接失效, 一份双射破裂的 preview 会照常落盘。
    by_id: dict[str, list[dict]] = {}
    for c in candidates:
        by_id.setdefault(c["stable_id"], []).append(c)
    dup = sorted(sid for sid, group in by_id.items() if len(group) > 1)
    if dup:
        detail = []
        for sid in dup:
            for c in by_id[sid]:
                a = c["source_anchor"]
                detail.append(
                    f"    {sid}  {a['file']}:{a['line_start']}  {' › '.join(a['heading_path'])}"
                )
        raise SystemExit(
            "✗ 引擎自检失败: 同一 preview 内 stable_id 重复, 拒绝输出一份双射破裂的 preview。\n"
            "  最常见成因是同一个来源文件被扫了两次（例如 ## Concepts 重复列同一份种子）；\n"
            "  也可能是身份键缺维。撞车的候选（同 ID 的都列出来）:\n"
            + "\n".join(detail)
        )

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
                "stable_id": c["stable_id"],
                "stable_id_basis": c["stable_id_basis"],
                "identity_ambiguous": c["identity_ambiguous"],
                "ambiguous_group_size": c["ambiguous_group_size"],
                "content_fingerprint": c["content_fingerprint"],
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
        "stable_id_namespace": STABLE_ID_NAMESPACE,
        "id_stability": ID_STABILITY,
        # vault 身份指纹（G5-3 审查发现）：stable_id 只含 vault **内**相对路径,
        # 所以两个不同 vault 里的同名板会产出可互比的 ID —— 不加这一维, 拿 A vault 的
        # preview 去比 B vault 的会凭空伪造出一份编辑史。落**哈希**而不是路径本身,
        # 避免把用户机器上的目录结构写进可分享的产物。
        "vault_fingerprint": "vf1-"
        + hashlib.sha256(vault_real.encode("utf-8")).hexdigest()[:_HASH_HEX],
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


def md_cell(s: str) -> str:
    """Markdown 表格单元格转义。标题里出现 `|`（条件概率 `P(A|B)`、逻辑或）会把
    整行的列切错位，把「重名」「已派生重叠」这些告警挤出可见列 —— 告警看不见
    等于没有（G5-3 审查发现）。"""
    return str(s).replace("\\", "\\\\").replace("|", "\\|")


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
    L.append(
        f"> 稳定 ID 命名空间 `{data['stable_id_namespace']}`（`bsa1-` 前缀）：抗行号漂移、抗调序、"
        "抗标题编号与 `[MM:SS]()` 变化；**改标题实词会换 ID**（设计取舍，"
        "全部边界见 `docs/design/split-stable-id-contract.md`）。"
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
        L.append(
            "| # | 建议节点名 | 稳定 ID | 来源锚点 | 标题路径 | 重名 | 已派生重叠 |"
        )
        L.append("|---|---|---|---|---|---|---|")
        for c in data["candidates"]:
            a = c["source_anchor"]
            anchor = f"`{md_cell(a['file'])}:{a['line_start']}-{a['line_end']}`"
            path = md_cell(" › ".join(a["heading_path"]))
            if c["conflict_unresolvable"]:
                dup = "⛔ 9+ 重名不可解"
            elif c["name_conflict"]:
                dup = f"⚠ 撞 `{md_cell(c['conflict_with'])}` → 建议 `{md_cell(c['resolved_name'])}`"
            elif c["conflict_in_preview"]:
                dup = f"⚠ 与本 preview 前序候选同名 → 建议 `{md_cell(c['resolved_name'])}`"
            else:
                dup = "无"
            ov = (
                md_cell("、".join(c["derived_overlap"]["existing_nodes"]))
                if c["derived_overlap"]["overlapping"]
                else "无"
            )
            L.append(
                f"| {c['index']} | `{md_cell(c['resolved_name'])}` | `{c['stable_id']}`"
                f"{' ⚠歧义' if c.get('identity_ambiguous') else ''} | {anchor} | {path} | {dup} | {ov} |"
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


# ───────────────────── diff 契约（CARD-G5-3 · 四态比对） ─────────────────────

MOVED_SEMANTICS = (
    "moved = **最小移动集**（共同候选序列的 LCS 补集，git 式）。"
    "交换相邻两条只标记其中一条为 moved，另一条作为 LCS 锚点视为未动——"
    "这是最小移动集的定义使然，不是漏判。选它而不选「秩比较法」的理由："
    "秩比较会把「末项拖到最前」报成全员 moved，过报等于信号失效。"
    "每条 entry 同时输出 old.rank / new.rank（共同集内 0-based 秩），"
    "想看完整位移图景的读这两个字段。"
)
TRADEOFF_NOTE = (
    "⚠ 设计取舍（不是缺陷）：改标题实词 → stable_id 变 → 本 diff 报一条 removed + "
    "一条 added，provenance 在此断开。引擎**不做**相似度改名识别——那要引入阈值与"
    "非确定性，与「同输入二跑逐字节相等」硬门冲突。改名后如需承接 provenance，"
    "由 G5-10 确认阶段人工指认。完整不稳定面清单见 docs/design/split-stable-id-contract.md。"
)
DIFF_NOT_EXECUTED = (
    "本 diff 只比对两份 preview JSON，**未执行**任何创建或修改："
    "未读取 vault、未创建任何节点、未改动任何既有文件"
    "（唯一写入 = out-dir 下两个 diff 产物）。确认/创建/插链属 G5-10。"
)

#: 参与 changed 判定的重名/冲突字段（任一变化 = 确认创建时实际落盘的文件名可能变）
_CONFLICT_FIELDS = (
    "name_conflict",
    "conflict_with",
    "conflict_in_preview",
    "conflict_unresolvable",
)


def _conflict_tuple(c: dict) -> tuple:
    return tuple(c.get(f) for f in _CONFLICT_FIELDS)


def _basis_key(b: dict) -> tuple:
    """身份依据的**可比形态**：`file` 按 NFC 归一后再比。

    产物里 `stable_id_basis.file` 存的是原始相对路径（可读），而 `compute_stable_id`
    对它做了 NFC。直接比 raw dict 会把「NFC / NFD 等价改名」判成 basis 不一致而
    **假拒绝** —— 那种改名恰恰是契约 §4.2 明确归入稳定面的（Codex round-2 MEDIUM-2 实证）。
    比较口径必须与身份键口径一致。
    """
    return (
        b.get("namespace"),
        nfc(b.get("file") or ""),
        tuple(b.get("heading_path_normalized") or ()),
        b.get("occurrence"),
        b.get("basis"),
    )


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"✗ {msg}")


def _nonempty_str(v: object) -> bool:
    return isinstance(v, str) and bool(v)


def _is_int(v: object) -> bool:
    """⛔ `isinstance(True, int)` 在 Python 里为真 —— JSON 的 `true/false` 会被当整数放行
    （Codex round-3 实证: 166 组畸形 schema 里有 8 组靠这个漏洞 rc=0）。"""
    return isinstance(v, int) and not isinstance(v, bool)


_ID_RE = re.compile(r"^bsa1-[0-9a-f]{16}$")
_FP_RE = re.compile(r"^cf1-[0-9a-f]{16}$")
_VF_RE = re.compile(r"^vf1-[0-9a-f]{16}$")
#: 候选来源形态的合法取值（也是身份键的第四个输入）
_KNOWN_BASIS = ("board-body-section", "seed-note-section", "seed-note-whole")


def load_preview_json(p: Path, role: str) -> dict:
    """读一份 preview 产物并做 diff 前置守卫。

    ⛔ 两条铁律：
    1. 全部校验在建 out-dir **之前**完成 —— 保证「拒绝路径零产物」；
    2. 校验**存在 + 类型**，不是只查 key 在不在（Codex round-2 HIGH-2 实证）：
       只查存在的话，`identity_ambiguous` / `vault_fingerprint` / `stable_id_basis`
       被删掉时三道安全处置会同时 **fail-open** ——
       歧义被投影成 false、跨 vault 不告警、basis 守卫因 `None == None` 被绕过，
       而 diff 照常 rc=0 输出一份看起来正常的报告。安全字段缺失必须等同于「拒绝」。
    """
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"✗ 读不到{role} preview JSON: {p} ({e})") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"✗ {role} preview 不是合法 JSON: {p} ({e})") from e
    _need(
        isinstance(data, dict) and isinstance(data.get("candidates"), list),
        f"{role} 文件不像 split preview 产物（缺 candidates 数组）: {p}",
    )
    sv = data.get("schema_version")
    if not isinstance(sv, int) or sv < MIN_DIFF_SCHEMA:
        raise SystemExit(
            f"✗ {role} preview 的 schema_version={sv!r} 低于 diff 所需的 {MIN_DIFF_SCHEMA}: {p}\n"
            "  稳定 ID 自 schema_version 2 起提供，v1 产物没有 ID 可比——请用本引擎重跑一次 preview。"
        )

    # ── 顶层：board 与两个 v2 安全字段（缺一即拒，不 fail-open）──────────────
    _need(
        _nonempty_str(data.get("board")),
        f"{role} preview 的 board 字段不是非空字符串（{data.get('board')!r}）: {p}",
    )
    _need(
        _nonempty_str(data.get("stable_id_namespace")),
        f"{role} preview 缺 stable_id_namespace（schema_version ≥2 必带）: {p}",
    )
    # ⛔ 本引擎只能校验**自己这一代**的产物：把两侧 namespace 协同改成 v999 时,
    # 同侧绑定 / 跨侧相等 / 复算三道全过（Codex round-4 实证）。所以这里必须钉死常量。
    _need(
        data["stable_id_namespace"] == STABLE_ID_NAMESPACE,
        f"{role} preview 的 stable_id_namespace={data['stable_id_namespace']!r} "
        f"不是本引擎这一代（{STABLE_ID_NAMESPACE}）——本引擎无法校验其他代际的 ID: {p}",
    )
    _need(
        _nonempty_str(data.get("vault_fingerprint"))
        and bool(_VF_RE.match(data["vault_fingerprint"])),
        f"{role} preview 的 vault_fingerprint 缺失或格式非法（缺了会让跨 vault 比对静默通过）: {p}",
    )
    # board 与 board_file 必须对得上：只重标 board 不改 board_file 同样是
    # 无需读 vault 就能发现的内部不一致（Codex round-5）。
    _need(
        _nonempty_str(data.get("board_file")),
        f"{role} preview 缺 board_file: {p}",
    )
    _need(
        data["board_file"] == f"原白板/{data['board']}.md",
        f"{role} preview 的 board={data['board']!r} 与 board_file={data['board_file']!r} 不一致: {p}",
    )
    _need(
        data.get("id_stability") == ID_STABILITY,
        f"{role} preview 的 id_stability={data.get('id_stability')!r} 不是本引擎的自陈值"
        f"（{ID_STABILITY}）: {p}",
    )
    _need(isinstance(data.get("sources"), list), f"{role} preview 缺 sources 数组: {p}")
    sg = data.get("scale_gate")
    _need(isinstance(sg, dict), f"{role} preview 缺 scale_gate: {p}")
    for k in ("threshold", "total_candidates", "kept"):
        _need(_is_int(sg.get(k)), f"{role} preview 的 scale_gate.{k} 不是整数: {p}")
    _need(
        isinstance(sg.get("over_threshold"), bool),
        f"{role} preview 的 scale_gate.over_threshold 非布尔: {p}",
    )
    # scale_gate 直接决定「截断嫌疑」告警要不要出。原先照单全收 → 改 total_candidates
    # 就能把告警静默压掉（Codex round-4 实证）。这里与候选数、阈值三方对账。
    _need(
        sg["threshold"] >= 1
        and sg["kept"] == len(data["candidates"])
        and sg["total_candidates"] >= sg["kept"],
        f"{role} preview 的 scale_gate 与候选数不自洽（{sg} vs {len(data['candidates'])} 条候选）: {p}",
    )
    _need(
        sg["over_threshold"] == (sg["total_candidates"] > sg["threshold"]),
        f"{role} preview 的 scale_gate.over_threshold 与阈值/总数不自洽（{sg}）: {p}",
    )

    source_files = {x.get("file") for x in data["sources"] if isinstance(x, dict)}
    seen: set[str] = set()
    for c in data["candidates"]:
        _need(isinstance(c, dict), f"{role} preview 的 candidates 里有非对象元素: {p}")
        sid = c.get("stable_id")
        _need(
            _nonempty_str(sid),
            f"{role} preview 有候选缺 stable_id（index={c.get('index')!r}）: {p}",
        )
        tag = f"（stable_id={sid}）: {p}"
        _need(bool(_ID_RE.match(sid)), f"{role} preview 候选的 stable_id 格式非法{tag}")
        _need(
            _nonempty_str(c.get("content_fingerprint"))
            and bool(_FP_RE.match(c["content_fingerprint"])),
            f"{role} preview 候选的 content_fingerprint 缺失或格式非法{tag}",
        )
        _need(
            _is_int(c.get("index")) and c["index"] >= 1,
            f"{role} preview 候选的 index 不是正整数{tag}",
        )
        for k in ("suggested_name", "resolved_name", "basis"):
            _need(
                _nonempty_str(c.get(k)),
                f"{role} preview 候选的 {k} 不是非空字符串{tag}",
            )
        _need(
            isinstance(c.get("identity_ambiguous"), bool),
            f"{role} preview 候选缺 identity_ambiguous 布尔{tag}",
        )
        n_amb = c.get("ambiguous_group_size")
        _need(
            _is_int(n_amb) and n_amb >= 1,
            f"{role} preview 候选的 ambiguous_group_size 非法{tag}",
        )
        _need(
            c["identity_ambiguous"] == (n_amb > 1),
            f"{role} preview 候选的 identity_ambiguous 与 ambiguous_group_size 自相矛盾{tag}",
        )

        b = c.get("stable_id_basis")
        _need(isinstance(b, dict), f"{role} preview 候选缺 stable_id_basis{tag}")
        _need(
            _nonempty_str(b.get("namespace")),
            f"{role} preview 候选 stable_id_basis.namespace 非法{tag}",
        )
        _need(
            _nonempty_str(b.get("file")),
            f"{role} preview 候选 stable_id_basis.file 非法{tag}",
        )
        _need(
            _nonempty_str(b.get("basis")),
            f"{role} preview 候选 stable_id_basis.basis 非法{tag}",
        )
        occ = b.get("occurrence")
        _need(
            _is_int(occ) and occ >= 1,
            f"{role} preview 候选 stable_id_basis.occurrence 非法{tag}",
        )
        hp = b.get("heading_path_normalized")
        _need(
            isinstance(hp, list) and hp and all(isinstance(x, str) for x in hp),
            f"{role} preview 候选 stable_id_basis.heading_path_normalized 非法{tag}",
        )

        a = c.get("source_anchor")
        _need(isinstance(a, dict), f"{role} preview 候选的 source_anchor 不是对象{tag}")
        _need(
            _nonempty_str(a.get("file")),
            f"{role} preview 候选 source_anchor.file 非法{tag}",
        )
        for k in ("line_start", "line_end"):
            _need(
                _is_int(a.get(k)) and a[k] >= 1,
                f"{role} preview 候选 source_anchor.{k} 不是正整数{tag}",
            )
        _need(
            a["line_end"] >= a["line_start"],
            f"{role} preview 候选 source_anchor 行区间倒置{tag}",
        )
        _need(
            isinstance(a.get("heading_path"), list)
            and a["heading_path"]
            and all(_nonempty_str(x) for x in a["heading_path"]),
            f"{role} preview 候选 source_anchor.heading_path 非法或为空{tag}",
        )
        # 原文标题路径必须与归一化路径**正向对得上**。
        # ⛔ 我在 round-4 写过「归一化有损、只能绑层数」——那是错的（Codex round-5 指出）：
        # 不需要从归一化反推原文, 把原文**再正向归一化一遍**比对即可。只绑层数时,
        # 同层数的伪造标题（["完全伪造的父标题","完全伪造的子标题"]）能静默通过并把
        # 伪造锚点送进 diff。这是**无需读 vault 就能对账的内部不一致**, 不属「无签名」边界。
        _need(
            normalize_heading_path(a["heading_path"]) == hp,
            f"{role} preview 候选的 heading_path 正向归一化后与 heading_path_normalized 不符{tag}",
        )

        # ⛔ 交叉绑定 + 身份复算：把「类型都对、但语义被改坏」整类挡在门外
        # （Codex round-3 点名的 13 类残余边界）。stable_id_basis 带齐了身份键的四个
        # 输入，所以可以直接复算一遍 —— 对不上就是产物被人动过，不是我们的候选。
        _need(
            b["namespace"] == data["stable_id_namespace"],
            f"{role} preview 候选 stable_id_basis.namespace 与顶层命名空间不一致{tag}",
        )
        _need(
            b["basis"] == c["basis"],
            f"{role} preview 候选 stable_id_basis.basis 与候选 basis 不一致{tag}",
        )
        _need(
            nfc(b["file"]) == nfc(a["file"]),
            f"{role} preview 候选 stable_id_basis.file 与 source_anchor.file 不一致{tag}",
        )
        _need(
            compute_stable_id(b["file"], hp, occ, b["basis"]) == sid,
            f"{role} preview 候选的 stable_id 与其 stable_id_basis 复算不符（产物被改过？）{tag}",
        )
        # basis ↔ file 的目录前缀必须自洽：board-body-section 只可能来自
        # 原白板/<board>.md, seed-note-* 只可能来自 节点/。不绑的话, 把板体候选的 file
        # 重绑到 节点/ 再重算 ID 就能通过 —— 那是**无需读 vault 就能对账**的矛盾,
        # 不属于「无签名」边界（Codex round-6 指正: 我原来的「自洽伪品」测试正是这种）。
        _need(
            c["basis"] in _KNOWN_BASIS,
            f"{role} preview 候选的 basis={c['basis']!r} 不是已知取值{tag}",
        )
        expect_dir = "原白板/" if c["basis"] == "board-body-section" else "节点/"
        _need(
            a["file"].startswith(expect_dir),
            f"{role} preview 候选 basis={c['basis']!r} 与来源目录不符"
            f"（应在 {expect_dir} 下，实为 {a['file']!r}）{tag}",
        )
        if c["basis"] == "board-body-section":
            _need(
                a["file"] == data["board_file"],
                f"{role} preview 板体候选的来源文件与 board_file 不符{tag}",
            )
        _need(
            a["file"] in source_files,
            f"{role} preview 候选的来源文件 {a['file']!r} 不在 sources 清单里{tag}",
        )
        # suggested_name 可由原文标题**复算** —— 名称伪造同样是内部可查的矛盾
        _need(
            derive_concept_stub(
                clean_heading(a["heading_path"][-1]),
                anchor=f"{a['file']}\x00{'/'.join(hp)}\x00{c['basis']}\x00{occ}",
            )
            == c["suggested_name"],
            f"{role} preview 候选的 suggested_name 与原文标题复算不符{tag}",
        )
        _need(
            sid not in seen,
            f"{role} preview 内 stable_id 重复 {sid}，双射破裂拒绝比对: {p}",
        )
        seen.add(sid)
    return data


def _short_src(p: Path) -> str:
    """产物里的来源标签: 「上一级目录名/文件名」。绝对路径不进产物（避免把用户
    机器上的目录结构写进可分享的文件），但保留一级父目录以便区分同名的两份 preview。"""
    parent = p.parent.name
    return f"{parent}/{p.name}" if parent else p.name


def _lcs_keep(old_seq: list[str], new_seq: list[str]) -> set[str]:
    """共同候选序列的 LCS（保持原位的那批）。确定性 tie-break：回溯时
    `dp[i-1][j] >= dp[i][j-1]` 退 i。复杂度 O(n·m)——候选量级为板内小节数（默认
    规模门 30），可忽略。"""
    n, m = len(old_seq), len(new_seq)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        oi = old_seq[i - 1]
        row, prev = dp[i], dp[i - 1]
        for j in range(1, m + 1):
            row[j] = (
                prev[j - 1] + 1 if oi == new_seq[j - 1] else max(prev[j], row[j - 1])
            )
    keep: set[str] = set()
    i, j = n, m
    while i > 0 and j > 0:
        if old_seq[i - 1] == new_seq[j - 1]:
            keep.add(old_seq[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return keep


def _side(c: dict, rank: int | None) -> dict:
    return {
        "index": c["index"],
        "rank": rank,
        "suggested_name": c["suggested_name"],
        "resolved_name": c["resolved_name"],
        "content_fingerprint": c["content_fingerprint"],
        "source_anchor": c["source_anchor"],
        "basis": c.get("basis"),
        "identity_ambiguous": bool(c.get("identity_ambiguous")),
        "derived_overlap": c.get("derived_overlap"),
        "stable_id_basis": c.get("stable_id_basis"),
        "name_conflict": c.get("name_conflict"),
        "conflict_with": c.get("conflict_with"),
        "conflict_in_preview": c.get("conflict_in_preview"),
        "conflict_unresolvable": c.get("conflict_unresolvable"),
    }


def build_diff(old: dict, new: dict, old_label: str, new_label: str) -> dict:
    """两份 preview → added / changed / removed / moved 四态（unchanged 单列）。

    状态互斥且有优先级：changed > moved > unchanged。内容/重名解析结果变了的条目
    即使同时换了位置也归 changed，位置信息由 entry 的 `moved` 布尔与 rank 字段补充——
    一条候选只出现在一个状态里，避免同一条被两处计数。

    change_reasons 取值（字典序输出，确定性）：
      conflict — 重名标志位变（撞池 / 撞本轮前序 / 9+ 不可解）
      content  — 内容指纹变
      name     — resolved_name 变（确认创建时实际会落到不同文件名）
    """
    if old.get("board") != new.get("board"):
        raise SystemExit(
            f"✗ 两份 preview 不是同一块板（旧={old.get('board')!r} / 新={new.get('board')!r}），拒绝比对"
        )
    # 跨命名空间比对守卫: 身份键算法换代（split-anchor/v1 → v2）后, 两代 ID 之间
    # 没有任何可比性——全部候选会互报 removed+added, 一份看似「板被重写了」的假 diff。
    # 换代那天必须是当场拒绝, 不是让人事后从 diff 里猜。
    if old["stable_id_namespace"] != new["stable_id_namespace"]:
        raise SystemExit(
            f"✗ 两份 preview 的 stable_id_namespace 不同"
            f"（旧={old['stable_id_namespace']!r} / 新={new['stable_id_namespace']!r}）："
            "跨身份键代际的 ID 不可比，拒绝比对。请用同一代引擎重跑两侧 preview。"
        )
    old_by = {c["stable_id"]: c for c in old["candidates"]}
    new_by = {c["stable_id"]: c for c in new["candidates"]}
    # 同一个 ID 两侧的身份依据必须一致。不一致 = 要么产物被人改过, 要么真发生了
    # 64-bit 截断碰撞 —— 两种情况下把它们当同一个候选比对都是错的, 当场拒绝而不是
    # 报一条看似正常的 unchanged（Codex round-1 LOW 实证）。
    for sid in set(old_by) & set(new_by):
        ob = _basis_key(old_by[sid]["stable_id_basis"])
        nb = _basis_key(new_by[sid]["stable_id_basis"])
        if ob != nb:
            raise SystemExit(
                f"✗ 同一 stable_id 在两侧的 stable_id_basis 不同（{sid}）：\n"
                f"  旧={ob}\n  新={nb}\n"
                "  这要么是产物被外部改过, 要么是身份键发生了真实碰撞——两种情况都不可比对。"
            )
    old_common = [c["stable_id"] for c in old["candidates"] if c["stable_id"] in new_by]
    new_common = [c["stable_id"] for c in new["candidates"] if c["stable_id"] in old_by]
    old_rank = {sid: i for i, sid in enumerate(old_common)}
    new_rank = {sid: i for i, sid in enumerate(new_common)}
    keep = _lcs_keep(old_common, new_common)

    # ── 告警必须在建 entries **之前**算好: truncation_suspect 要用到 ──────────
    og, ng = old.get("scale_gate") or {}, new.get("scale_gate") or {}
    truncated_either = bool(og.get("over_threshold") or ng.get("over_threshold"))
    warnings: list[str] = []
    if og.get("threshold") != ng.get("threshold"):
        warnings.append(
            f"⚠ 两侧规模门阈值不同（旧 --max-units={og.get('threshold')} / 新 {ng.get('threshold')}）："
            "被阈值切掉的候选会显示为 removed/added，那**不是**内容变化。请用相同阈值重跑两侧 preview 再比对。"
        )
    for side, g in (("旧", og), ("新", ng)):
        if g.get("over_threshold"):
            warnings.append(
                f"⚠ {side}侧 preview 被规模门截断（总 {g.get('total_candidates')} 条，"
                f"只保留文档序前 {g.get('kept')} 条）：**即使两侧阈值相同**，板体一旦跨过阈值，"
                "尾部仍在板上、一字未动的小节也会被挤出窗口并显示为 removed。"
                "下方带「截断嫌疑」标记的 added/removed 请先按此排查。"
            )
    if old.get("vault_fingerprint") != new.get("vault_fingerprint"):
        warnings.append(
            f"⚠ 两份 preview 来自**不同 vault**（旧 {old.get('vault_fingerprint')} / "
            f"新 {new.get('vault_fingerprint')}）：stable_id 只含 vault 内相对路径，"
            "跨 vault 比同名板会凭空造出一份不存在的编辑史。确认这是你要的比对再往下读。"
        )
    amb = sorted(
        {
            c["stable_id"]
            for c in list(old["candidates"]) + list(new["candidates"])
            if c.get("identity_ambiguous")
        }
    )
    if amb:
        warnings.append(
            f"⚠ {len(amb)} 条候选的身份**先天歧义**（同一文件里存在归一化标题路径逐字相同的多个小节）："
            "这些条目的 ID 绑的是「同路径第 N 个槽位」而不是内容单元，调序会让身份跟着槽位走。"
            "它们的 changed / moved / unchanged 判定**不具 provenance 效力**，"
            "G5-10 不得据此持久化 split_stable_id。详见 docs/design/split-stable-id-contract.md §4.4。"
        )

    entries: list[dict] = []
    unchanged: list[dict] = []
    counts = {"added": 0, "changed": 0, "removed": 0, "moved": 0, "unchanged": 0}

    for c in new["candidates"]:  # 新侧文档序 → added / changed / moved / unchanged
        sid = c["stable_id"]
        if sid not in old_by:
            entries.append(
                {
                    "state": "added",
                    "stable_id": sid,
                    "change_reasons": [],
                    "moved": False,
                    "truncation_suspect": truncated_either,
                    "old": None,
                    "new": _side(c, None),
                }
            )
            counts["added"] += 1
            continue
        o = old_by[sid]
        reasons: list[str] = []
        if _conflict_tuple(o) != _conflict_tuple(c):
            reasons.append("conflict")
        if o["content_fingerprint"] != c["content_fingerprint"]:
            reasons.append("content")
        if o["resolved_name"] != c["resolved_name"]:
            reasons.append("name")
        # overlap: 候选从「未派生」跃迁到「已派生为 [[节点/X]]」。原先它只表现为
        # content 一个 reason, 读 diff 的人分不出「正文改了」和「这段已经被拆过了」
        # —— 后者恰恰是 G5-10 最该知道的信号（G5-3 审查发现）。
        if (o.get("derived_overlap") or {}) != (c.get("derived_overlap") or {}):
            reasons.append("overlap")
        moved = sid not in keep
        so, sn = _side(o, old_rank[sid]), _side(c, new_rank[sid])
        if reasons:
            entries.append(
                {
                    "state": "changed",
                    "stable_id": sid,
                    "truncation_suspect": False,
                    "change_reasons": reasons,
                    "moved": moved,
                    "old": so,
                    "new": sn,
                }
            )
            counts["changed"] += 1
        elif moved:
            entries.append(
                {
                    "state": "moved",
                    "stable_id": sid,
                    "truncation_suspect": False,
                    "change_reasons": [],
                    "moved": True,
                    "old": so,
                    "new": sn,
                }
            )
            counts["moved"] += 1
        else:
            unchanged.append(
                {
                    "stable_id": sid,
                    "resolved_name": c["resolved_name"],
                    "old": so,
                    "new": sn,
                }
            )
            counts["unchanged"] += 1

    for c in old["candidates"]:  # 旧侧文档序 → removed
        sid = c["stable_id"]
        if sid not in new_by:
            entries.append(
                {
                    "state": "removed",
                    "stable_id": sid,
                    "change_reasons": [],
                    "moved": False,
                    # ⛔ 任一侧被规模门截断时, removed 可能只是「被窗口挤出去了」而非
                    # 从板上消失。这条标记 + 总览告警是 5 个独立审查镜头同时命中的问题。
                    "truncation_suspect": truncated_either,
                    "old": _side(c, None),
                    "new": None,
                }
            )
            counts["removed"] += 1

    # 记账自检: 四态 + unchanged 必须恰好覆盖两侧候选各一次, 不重不漏。
    # diff 的全部价值就是「这份账是准的」——账不平时宁可当场炸, 也不输出一份
    # 看起来正常、实际漏计了某条候选的差异报告。
    if counts["added"] + counts["changed"] + counts["moved"] + counts[
        "unchanged"
    ] != len(new["candidates"]):
        raise SystemExit(
            f"✗ 引擎自检失败: 新侧记账不平（summary={counts} vs 新侧 {len(new['candidates'])} 条候选）"
        )
    if counts["removed"] + counts["changed"] + counts["moved"] + counts[
        "unchanged"
    ] != len(old["candidates"]):
        raise SystemExit(
            f"✗ 引擎自检失败: 旧侧记账不平（summary={counts} vs 旧侧 {len(old['candidates'])} 条候选）"
        )
    if len(entries) + len(unchanged) != len(new["candidates"]) + counts["removed"]:
        raise SystemExit("✗ 引擎自检失败: entries + unchanged 条目数与两侧候选总量不符")

    def _meta(d: dict, label: str) -> dict:
        return {
            "source": label,
            "schema_version": d.get("schema_version"),
            "generator": d.get("generator"),
            "board_sha256": d.get("board_sha256"),
            "candidate_count": len(d["candidates"]),
            "scale_gate": d.get("scale_gate"),
        }

    return {
        "schema_version": DIFF_SCHEMA_VERSION,
        "kind": "split-diff",
        "generator": GENERATOR,
        "board": new.get("board"),
        "stable_id_namespace": STABLE_ID_NAMESPACE,
        "id_stability": ID_STABILITY,
        "old": _meta(old, old_label),
        "new": _meta(new, new_label),
        "warnings": warnings,
        "summary": counts,
        "entries": entries,
        "unchanged": unchanged,
        "moved_semantics": MOVED_SEMANTICS,
        "tradeoff_note": TRADEOFF_NOTE,
        "not_executed_disclaimer": DIFF_NOT_EXECUTED,
    }


def render_diff_md(d: dict) -> str:
    """人读 diff（纯自渲染，只消费 diff dict）。四态各占一节，空节也写出来——
    「移除：（无）」比整节消失更可读，也让人一眼看出引擎确实检查过这一态。"""
    s = d["summary"]
    L: list[str] = []
    L.append(f"# 拆分 preview 差异 · {d['board']}")
    L.append("")
    L.append(
        "> ⛔ 本文件由 `board-split/scripts/split_preview.py --diff` **只读**生成（CARD-G5-3）。"
    )
    L.append(f"> {d['not_executed_disclaimer']}")
    L.append(
        f"> 稳定 ID 命名空间: `{d['stable_id_namespace']}` · diff schema_version: {d['schema_version']}"
    )
    L.append("")
    if d.get("warnings"):
        L.append("> [!warning]+ 读这份 diff 之前先看这里")
        for w in d["warnings"]:
            L.append(f"> {w}")
        L.append("")
    L.append("## 总览")
    L.append("")
    L.append("| 新增 | 内容变更 | 移动 | 移除 | 未变 |")
    L.append("|---|---|---|---|---|")
    L.append(
        f"| {s['added']} | {s['changed']} | {s['moved']} | {s['removed']} | {s['unchanged']} |"
    )
    L.append("")
    L.append(
        f"- 旧: `{d['old']['source']}`（候选 {d['old']['candidate_count']}，"
        f"板 sha `{str(d['old']['board_sha256'])[:12]}…`）"
    )
    L.append(
        f"- 新: `{d['new']['source']}`（候选 {d['new']['candidate_count']}，"
        f"板 sha `{str(d['new']['board_sha256'])[:12]}…`）"
    )
    L.append("")

    def _anchor(side: dict) -> str:
        a = side["source_anchor"]
        return f"`{md_cell(a['file'])}:{a['line_start']}-{a['line_end']}`"

    def _flags(e: dict, side: dict) -> str:
        """条目级红旗。两者都是「这条 diff 结论别当真」的信号, 必须出现在表里
        （只写进 JSON 等于没写——读 diff 的人看的是 MD）。"""
        f = []
        if e.get("truncation_suspect"):
            f.append("⚠截断嫌疑")
        if side.get("identity_ambiguous"):
            f.append("⚠身份歧义")
        return " ".join(f) or "—"

    def _rows(state: str, title: str, cols: list[str], row: object) -> None:
        L.append(f"## {title}")
        L.append("")
        hits = [e for e in d["entries"] if e["state"] == state]
        if not hits:
            L.append("（无）")
            L.append("")
            return
        L.append("| " + " | ".join(cols) + " |")
        L.append("|" + "---|" * len(cols))
        for e in hits:
            L.append(row(e))  # type: ignore[operator]
        L.append("")

    _rows(
        "added",
        "新增（added）",
        ["建议节点名", "稳定 ID", "来源锚点", "标题路径", "标记"],
        lambda e: (
            f"| `{md_cell(e['new']['resolved_name'])}` | `{e['stable_id']}` | {_anchor(e['new'])} | "
            + md_cell(" › ".join(e["new"]["source_anchor"]["heading_path"]))
            + f" | {_flags(e, e['new'])} |"
        ),
    )
    _rows(
        "changed",
        "内容变更（changed）",
        ["节点名", "稳定 ID", "变更项", "旧锚点", "新锚点", "同时移动", "标记"],
        lambda e: (
            f"| `{md_cell(e['new']['resolved_name'])}` | `{e['stable_id']}` | "
            f"{'、'.join(e['change_reasons'])} | {_anchor(e['old'])} | {_anchor(e['new'])} | "
            f"{'是' if e['moved'] else '否'} | {_flags(e, e['new'])} |"
        ),
    )
    _rows(
        "moved",
        "移动（moved）",
        ["节点名", "稳定 ID", "旧序号→新序号", "旧秩→新秩", "标记"],
        lambda e: (
            f"| `{md_cell(e['new']['resolved_name'])}` | `{e['stable_id']}` | "
            f"{e['old']['index']} → {e['new']['index']} | {e['old']['rank']} → {e['new']['rank']} | "
            f"{_flags(e, e['new'])} |"
        ),
    )
    _rows(
        "removed",
        "移除（removed）",
        ["节点名", "稳定 ID", "旧锚点", "标题路径", "标记"],
        lambda e: (
            f"| `{md_cell(e['old']['resolved_name'])}` | `{e['stable_id']}` | {_anchor(e['old'])} | "
            + md_cell(" › ".join(e["old"]["source_anchor"]["heading_path"]))
            + f" | {_flags(e, e['old'])} |"
        ),
    )
    L.append("## 未变（unchanged）")
    L.append("")
    if d["unchanged"]:
        L.append(
            "共 "
            + str(len(d["unchanged"]))
            + " 条：内容指纹、重名解析、相对位置全部一致（行号漂移不算变化）。"
        )
    else:
        L.append("（无）")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"> **moved 语义**：{d['moved_semantics']}")
    L.append("")
    L.append(f"> {d['tradeoff_note']}")
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


def safe_open_checked(p: Path) -> int:
    """O_NOFOLLOW 打开（不带 O_TRUNC）并验 nlink —— 只做准入, 不动内容。
    拆出来是为了让调用方能**先把两份产物的目标都验完再落笔**（Codex round-2 MEDIUM-1:
    把第二份产物预置成 symlink 时, 第一份 JSON 已经写下去了, 留下半份产物）。"""
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
    except SystemExit:
        os.close(fd)
        raise
    return fd


def write_checked_fd(fd: int, content: str) -> None:
    """对已通过准入的 fd 落盘（ftruncate + write），并关闭它。"""
    os.ftruncate(fd, 0)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)


def write_pair_atomically_checked(items: list[tuple[Path, str]]) -> None:
    """成对发布：**先把所有目标的准入验完**，任一不过则一份都不写。

    已知边界（如实声明，用户态不可完全关闭）：准入通过之后、写入过程中若发生
    I/O 错误（磁盘满等），仍可能只落一份。本函数消除的是「可预见的拒绝」造成的
    半份产物，不是所有失败模式。
    """
    # ⛔ O_CREAT 会把目标**建出来**（0 字节）。若第二个目标准入不过就直接抛,
    # 第一个目标会留下一个空文件 —— 那仍然是半份产物。所以要记住哪些是本次新建的,
    # 失败时撤销掉（只删本次自己创建的, 绝不碰既有文件）。
    # ⛔ 用 lexists 而不是 exists：dangling symlink 的 exists() 为 False，
    # 会被误判成「本次新建」→ 回滚时把用户既存的那条链接删掉
    # （Codex round-3 MEDIUM 实证：这不是零产物问题，是破坏既有目录项）
    created = [not os.path.lexists(str(path)) for path, _ in items]
    fds: list[int] = []
    try:
        for path, _ in items:
            fds.append(safe_open_checked(path))
    except SystemExit:
        for fd in fds:
            os.close(fd)
        for (path, _), was_new in zip(items, created):
            if was_new:
                try:
                    os.unlink(str(path))
                except OSError:
                    pass
        raise
    for fd, (_, content) in zip(fds, items):
        write_checked_fd(fd, content)


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


def prepare_out_dir(out_dir: Path) -> Path:
    """产物目录准入（preview / diff 两模式共用同一套写侧物理防御）。
    v3 (Codex 三轮 H1): 先验祖先链无 symlink **再** mkdir —— 否则 mkdir 会先穿过
    symlink 在物理目标处创建目录, 形成「拒绝但已写」。"""
    if not out_dir.parent.exists():
        raise SystemExit(f"✗ 输出目录的父目录不存在, 拒绝创建祖先链: {out_dir.parent}")
    assert_symlink_free(out_dir.parent)
    if not out_dir.exists():
        out_dir.mkdir(exist_ok=True)  # 单级创建, 不静默造祖先 (H1)
    assert_symlink_free(out_dir)
    return out_dir


def run_preview_mode(args: argparse.Namespace) -> int:
    if not args.vault or not args.board:
        raise SystemExit(
            "✗ preview 模式必须同时给 --vault 与 --board（比对两份 preview 请用 --diff OLD.json NEW.json）"
        )
    if args.max_units < 1:
        raise SystemExit(f"✗ --max-units 必须是正整数, 实得 {args.max_units}")
    validate_board_name(args.board)
    validate_product_filename(args.board, "split-preview-")
    vault = Path(args.vault).resolve()
    if not (vault / "原白板").is_dir():
        raise SystemExit(f"✗ 不是合法 vault（缺 原白板/）: {vault}")

    data = build_preview(vault, args.board, args.max_units)
    md = render_md(data)
    for c in data["candidates"]:
        c.pop("_heading_raw", None)
        c.pop("_heading_level", None)

    out_dir = prepare_out_dir(Path(args.out_dir) if args.out_dir else vault / "outputs")
    json_path = out_dir / f"split-preview-{args.board}.json"
    md_path = out_dir / f"split-preview-{args.board}.md"
    write_pair_atomically_checked(
        [
            (json_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n"),
            (md_path, md),
        ]
    )
    print(f"✓ preview 已生成（只读引擎, 未动 vault 既有文件）: {json_path} / {md_path}")
    print(
        f"  候选 {data['scale_gate']['kept']}/{data['scale_gate']['total_candidates']}"
        f"{' · ⚠ 已截断' if data['scale_gate']['over_threshold'] else ''}"
        f"{' · 纯脚手架 0 单元' if data['scaffold_only'] else ''}"
    )
    return 0


def run_diff_mode(args: argparse.Namespace) -> int:
    """⛔ 次序铁律：全部输入守卫跑完**再**碰 out-dir —— 拒绝路径必须零产物
    （与 preview 侧「拒绝但已写」同一条教训）。"""
    old_path, new_path = Path(args.diff[0]), Path(args.diff[1])
    old = load_preview_json(old_path, "旧")
    new = load_preview_json(new_path, "新")
    # 产物里只落「上一级目录/文件名」: 绝对路径不进产物, 但两份 preview 通常**同名不同目录**
    # (run1/ 与 run2/), 只落 basename 会让读 diff 的人分不清哪份是旧的 —— 一级父目录刚好够分辨
    d = build_diff(old, new, _short_src(old_path), _short_src(new_path))

    # ⛔ 板名来自 JSON（外部可编辑）→ 校验必须在 prepare_out_dir **之前**。
    # 自查实测: 反过来会「拒绝但已建空目录」——与 G5-2 Codex 三轮 H1 同型的次序错误。
    board = d["board"]
    validate_board_name(board)
    validate_product_filename(board, "split-diff-")
    # ⛔ 两份产物**都渲染完**再动 out-dir: 渲染期抛异常时若 JSON 已落盘,
    # 留下的是「新 JSON + 旧 MD」的错配对（Codex round-1 MEDIUM 实证）。
    payload_json = json.dumps(d, ensure_ascii=False, indent=2) + "\n"
    payload_md = render_diff_md(d)
    out_dir = prepare_out_dir(Path(args.out_dir) if args.out_dir else new_path.parent)
    json_path = out_dir / f"split-diff-{board}.json"
    md_path = out_dir / f"split-diff-{board}.md"
    write_pair_atomically_checked([(json_path, payload_json), (md_path, payload_md)])
    s = d["summary"]
    print(
        f"✓ diff 已生成（只比对两份 JSON, 未读 vault、未动任何既有文件）: {json_path} / {md_path}"
    )
    print(
        f"  新增 {s['added']} · 内容变更 {s['changed']} · 移动 {s['moved']} · "
        f"移除 {s['removed']} · 未变 {s['unchanged']}"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="拆分建议 preview（只读, CARD-G5-2）+ 稳定 ID 与四态 diff（CARD-G5-3）"
    )
    ap.add_argument("--vault", help="preview 模式必填")
    ap.add_argument("--board", help="preview 模式必填（板名 stem）")
    ap.add_argument(
        "--diff",
        nargs=2,
        metavar=("OLD_JSON", "NEW_JSON"),
        help="比对模式：两份 preview JSON（schema_version ≥ 2）→ added/changed/removed/moved",
    )
    ap.add_argument(
        "--out-dir",
        default=None,
        help="产物目录（preview 缺省 <vault>/outputs；diff 缺省 NEW_JSON 所在目录；父目录必须已存在）",
    )
    ap.add_argument("--max-units", type=int, default=DEFAULT_MAX_UNITS)
    args = ap.parse_args()

    if args.diff:
        if args.vault or args.board:
            raise SystemExit(
                "✗ --diff 与 --vault/--board 互斥：比对模式只读两份 JSON, 不碰 vault"
            )
        return run_diff_mode(args)
    return run_preview_mode(args)


if __name__ == "__main__":
    raise SystemExit(main())
