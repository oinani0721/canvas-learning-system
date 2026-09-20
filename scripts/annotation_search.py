#!/usr/bin/env python3
"""批注只读检索（CARD-G1-1）。

按关键词 / Story ID 在 Markdown 里找回「用户说过的话」，输出 ``file:line`` + 摘录 +
日期（带 ``date_source``）+ 来源类别。

覆盖面（契约 ``2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md`` §4.1 的 T1 全部
与 T2 的粗体 / blockquote / 行内三形态）：

* 粗体 User 族：``**User：`` / ``**User:`` / ``**User ：`` / ``**User2：`` /
  ``**User 修正：`` / ``**User Comment:`` 等（契约 ``:134``）。
* 中文容器头族（H1 整改，2026-09-19；ZCode r2 → r3 两轮复核）：契约 ``:130/:134`` 的
  「明确中文『用户批注/反馈/修正/原话』」。覆盖冒号两形态——冒号在粗体内
  （``**用户批注原文（这是本轮要回答的靶心）：**``）与冒号在粗体外
  （``**用户批注（步骤 1，line 125）**：``）——外加限定词（原文/触发）、定位符
  （``**用户批注 L128**:``）与括注（≤30 字符）。
  真数据 4 处真容器头：``_bmad-output/审查/2026-08-02-…:23``、
  ``_bmad-output/验收单/Story-2.1-…:429``、``_bmad-output/research/round-23-…:13``、
  ``_bmad-output/implementation-artifacts/epic-1/1-8-vault-switch-runtime-api.md:174``。
  ⚠️ 不带粗体的裸中文形态（``用户批注：``）多系转述（T3 面），不纳入。
* callout 族：``[!question]+`` / ``[!error]+`` / ``[!tip]+`` / ``[!note]+`` /
  ``[!warning]+`` / ``[!hint]+`` / ``[!info]+`` / ``[!BMAD-ANNO]``，blockquote
  （``> [!x]+``）与行内两种形态都算。

**不做**（如实声明，非遗漏）：契约 ``:132`` 的 T3 broad discovery（``user``/``USer``
异常大小写、role 字段、转述、无冒号编号）须人工分类，不进本脚本；契约 ``:82`` 的非
Markdown 容器（Canvas JSON / JSONL / YAML / 对话导出）不解析；修正链去重 /
atomization（契约 §4.2 末条）不做。

**只读**：本脚本自身除 stdout / stderr 外零写——不建目录、不改被扫文件。唯一子进程
是 ``git log -1 --format=%cs``（只读查询），且仅在 frontmatter 与文件名都给不出日期
时才调用；该子进程拿到的是**剃掉全部 ``GIT_*`` 的环境**（见 ``git_env``），否则
``GIT_DIR`` 会让它回答另一个仓库、``GIT_TRACE*`` 会让它自己往文件里写。

⚠️ 一处如实声明：以 ``python3 scripts/annotation_search.py`` 方式跑时不产生任何缓存
（``__main__`` 不写字节码）；但被 ``import`` 进别的进程时，**Python 解释器**可能在
``scripts/__pycache__`` 写 ``.pyc``。那是解释器行为不是本脚本的写调用，所以全部裁判
一律带 ``PYTHONDONTWRITEBYTECODE=1``。

**私人 root**：默认排除的私人根**不写死在本文件里**，而是从 A01
(``A01-source-boundary-draft.json``) 的 ``source_roots`` 算出——``privacy_ceiling``
∈ {P3-high-sensitive, P4-secret} 的 root，加上 ``proposed_action`` 含
``private-locator`` 的 root。A01 读不到 / 结构不对 ⇒ 退出码 2（fail-closed），
**不**降级成「当作没有私人 root 继续扫」。
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = str(Path(__file__).resolve().parents[1])

DEFAULT_ROOT = os.path.join(REPO_ROOT, "_bmad-output")
DEFAULT_A01 = os.path.join(
    REPO_ROOT,
    "_bmad-output",
    "审查",
    "phase0a-annotation-truth",
    "A01-source-boundary-draft.json",
)

PRUNE_DIRS = frozenset({".obsidian", "__pycache__", "node_modules", ".git"})

# --- marker 表 -------------------------------------------------------------
# name -> 正则。两族粗体（ASCII User 族 / 中文容器头族）+ 九个 callout 类型，
# 逐条可数（len(MARKERS) == 11；callout 九个 = question/error/tip/note/warning/hint/info/todo/BMAD-ANNO）。
# `\*{0,2}` 覆盖契约 :131 T2 的「marker 被粗体符号拆开」形态（`**User**：`，
# 真数据 1 处：`验收单/Story-2.1-Phase1-成熟度升级-2026-05-03.md:279`）。
# callout 一律 IGNORECASE —— Obsidian 的 callout 类型本就大小写不敏感，
# 真数据里 `[!WARNING]` / `[!NOTE]` 共 3 处，逐字小写匹配会漏掉。
MARKERS = {
    "user_bold": re.compile(r"\*\*User(?:\s?\d)?\s?(?:修正|Comment)?\*{0,2}\s?[：:]"),
    # H1 整改（ZCode r2 HIGH-1 → r3 HIGH-1R）：中文粗体容器头。两形态 = 冒号在粗体内
    # (`**用户批注原文（…）：**`) / 冒号在粗体外 (`**用户批注（步骤 1，line 125）**：`)；
    # 限定词只收真数据出现过的「原文 / 触发」与定位符 ` L<n>`（`**用户批注 L128**:`
    # 形态，epic-1/1-8 真数据）；括注 ≤30 字符覆盖 `（步骤 1，line 125)` 这类行号引用。
    # ⚠️ 刻意**不**收 Claude 自述语（`**用户原话 3 个 callout…**` 这类关键词与冒号间
    # 夹长正文、无括注的形态）与裸中文转述（T3 面）。
    # 真数据 4 处真容器头：审查/2026-08-02-…:23、验收单/Story-2.1-…:429、
    # research/round-23-…:13、implementation-artifacts/epic-1/1-8-…:174。
    "user_bold_zh": re.compile(
        r"\*\*用户(?:批注|反馈|原话|修正)(?:原文|触发)?(?:\s?L\d+)?(?:[（(][^*]{0,30}?[）)])?\*{0,2}[：:]"
    ),
    "callout_question": re.compile(r"\[!question\][+-]?", re.I),
    "callout_error": re.compile(r"\[!error\][+-]?", re.I),
    "callout_tip": re.compile(r"\[!tip\][+-]?", re.I),
    "callout_note": re.compile(r"\[!note\][+-]?", re.I),
    "callout_warning": re.compile(r"\[!warning\][+-]?", re.I),
    "callout_hint": re.compile(r"\[!hint\][+-]?", re.I),
    "callout_info": re.compile(r"\[!info\][+-]?", re.I),
    # `[!todo]+ 📝 批注区（直接写 **User：**）` 是本仓批注区的标准容器形态，
    # 真数据 10 处 —— 漏掉它等于漏掉「批注区」这个入口本身。
    "callout_todo": re.compile(r"\[!todo\][+-]?", re.I),
    "callout_BMAD-ANNO": re.compile(r"\[!BMAD-ANNO\][+-]?", re.I),
}

CALLOUT_PREFIX = "callout_"

# --- Story ID 形态 ---------------------------------------------------------
# 只用于回填 `story_ids` 字段；`--story` 的匹配本身是大小写敏感的子串包含。
STORY_ID_PATTERNS = (
    re.compile(r"CARD-[A-Za-z0-9][A-Za-z0-9\-]*"),
    re.compile(r"Story[\- ]\d+\.\d+[A-Za-z0-9.]*"),
    re.compile(r"DEBT-\d+"),
    re.compile(r"T-new-\d+"),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{1,2}\d{1,2}-[A-Za-z0-9]{1,3}(?![A-Za-z0-9])"),
)

# --- 来源类别（路径前缀口径）------------------------------------------------
CATEGORIES = (
    "验收单批注区",
    "批注回复",
    "审查",
    "研究",
    "goal-cards",
    "planning-artifacts",
    "决策批注",
    "其他",
)

# --- 私人 root 的路径映射 ---------------------------------------------------
# A01 只声明 root_id / privacy_ceiling，**没有 path 字段**，所以 root_id -> 路径
# 的映射只能由本脚本自带。A01 若将来补上 path 字段，这里要同步。
#
# 相对形态锚在「每个扫描根及其各级祖先」与仓根上做 realpath 前缀比较；
# 组件形态（路径里出现名为 canvas-vault 的目录段）与 basename 形态是安全网，
# 挡住前缀比较覆盖不到的位置（例如 <root>/sub/canvas-vault/）。
PRIVATE_RELATIVE_PATHS = {
    "ROOT-ACTIVE-VAULT": ("canvas-vault",),
    "ROOT-ANCHORED-PRD": (
        os.path.join(".gdr", "_external"),
        os.path.join("docs", "scheme-a-planning", "14-scheme-a-implementation-prd.md"),
    ),
}
PRIVATE_ABSOLUTE_PATHS = {
    "ROOT-ACTIVE-VAULT": ("/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault",),
    "ROOT-ANCHORED-PRD": ("/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md",),
}
# ⚠️ 下面两张表的**键**是拿来和 fold_path() 的输出比对的，所以必须写成
# NFC + casefold 后的形态（全小写）。单测 test_private_lookup_keys_are_prefolded
# 把这条不变量钉成门——写错大小写会静默漏判，不是报错。
PRIVATE_COMPONENT_ROOTS = {"canvas-vault": "ROOT-ACTIVE-VAULT"}
PRIVATE_BASENAME_ROOTS = {"14-scheme-a-implementation-prd.md": "ROOT-ANCHORED-PRD"}

PRIVATE_CEILINGS = frozenset({"p3-high-sensitive", "p4-secret"})
# 明确判定为**非**私人的 ceiling。凡不在这张表也不在 PRIVATE_CEILINGS 的取值
# （拼写变体、前后空白、将来新增的 P5…）一律按私人处理 —— 这是 fail-closed：
# 认不出的敏感级别当敏感，而不是当公开。
PUBLIC_CEILINGS = frozenset({"p0-public", "p1-project-internal", "p2-personal"})
PRIVATE_ACTION_TOKEN = "private-locator"

# 围栏代码块识别（契约 §4.2 :139 要求「用状态机识别 fenced code」）。
# ⚠️ 识别 ≠ 排除：本仓 12.7%（148/1167 实测 2026-09-19）的 marker 行落在围栏内，
# 其中既有真批注被引用进代码块（如 obsidian-qa-round11:618 的 `**User：以下是 ChatGpt 调研结果**`），
# 也有纯格式示例（如 obsidian-qa-round3:554 的 `> [!error]+ ❌ 错误`）。排除会丢真阳性，
# 所以照常召回，但每条记录带 in_fenced_code 标注、汇总行报计数，让人一眼能筛。
FENCE_RE = re.compile(r"^\s{0,3}(?:```|~~~)")

# HTML 注释同理（契约 :134 的「至少覆盖」清单含「HTML 注释、模板/示例/引用」，
# :139 要求状态机识别 HTML comment）。真数据 26 行 / 6 文件落在注释区内，
# 样例是被注释掉的填写模板（验收单/Story-2.5.X-progressive-confirmation.md:781-787）。
# 同样是**标注不排除**：注释掉的也可能是真批注，删了就找不回来。
HTML_COMMENT_OPEN = "<!--"
HTML_COMMENT_CLOSE = "-->"

# 续行遇到「另一个人开口」就停。真数据里批注区的标准写法是
# `> **User：** …` / `>` / `> **Claude（2026-07-20）：** …`（研究/ 下 2 处实测），
# 引用块里的「空行」是一个光秃秃的 `>`，用 str.strip() 判不出来，于是 Claude 的
# 回复会被 append 进 User 那条记录，工具就把别人的话当成「用户说过的话」返回。
SPEAKER_LABEL_RE = re.compile(r"^\s*>*\s*\*\*[^*]{1,24}?[：:]")
QUOTE_BLANK_RE = re.compile(r"^[>\s]*$")

FRONTMATTER_KEYS = ("date", "created", "updated")
# frontmatter 的扫描上界。没有这个界，首行那个 `---` 其实是正文分隔线时，
# 解析会一路扫到 EOF，把正文里（甚至围栏代码块里）的 `date:` 当成 frontmatter，
# 于是报出一个**看起来权威**的错日期（2026-09-19 实测：围栏内的 `date: 1999-01-01`
# 被报成 `date_source=frontmatter`）。
FRONTMATTER_MAX_LINES = 200

# ⚠️ 两侧的 `(?<!\d)` / `(?!\d)` 不可省：没有边界时 `ticket-1234-56-7890.md` 会被
# 抠出 `1234-56-78`（月 56 日 78），而且因为 filename 档排在 git 档之前，这个假值会
# **挡掉**本来能给出真实提交日期的那一档——报出来的不是「定不了日期」而是一个假日期。
DATE_RE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
EXCERPT_LINE_LIMIT = 200


class A01Error(Exception):
    """A01 缺失 / 结构不合约 —— fail-closed，调用方须以退出码 2 结束。"""


class PrivateRootRefused(Exception):
    """`--root` 指向 A01 声明的私人 root —— 退出码 2。"""


# --------------------------------------------------------------------------
# A01
# --------------------------------------------------------------------------
def load_private_root_ids(a01_path):
    """从 A01 算出私人 root_id 集合。任何读不到 / 结构不对都抛 A01Error。"""
    try:
        with open(a01_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise A01Error(f"A01 边界声明读不到：{a01_path}") from exc
    except OSError as exc:
        raise A01Error(f"A01 边界声明打不开：{a01_path}（{exc}）") from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise A01Error(f"A01 边界声明不是合法 JSON：{a01_path}（{exc}）") from exc

    if not isinstance(data, dict):
        raise A01Error(f"A01 顶层不是 JSON object：{a01_path}")
    roots = data.get("source_roots")
    if not isinstance(roots, list) or not roots:
        raise A01Error(f"A01 顶层缺 source_roots 列表：{a01_path}")

    private = set()
    declared = []
    for idx, entry in enumerate(roots):
        if not isinstance(entry, dict):
            raise A01Error(f"A01 source_roots[{idx}] 不是 object：{a01_path}")
        root_id = entry.get("root_id")
        ceiling = entry.get("privacy_ceiling")
        if not isinstance(root_id, str) or not root_id:
            raise A01Error(f"A01 source_roots[{idx}] 缺 root_id：{a01_path}")
        if not isinstance(ceiling, str) or not ceiling:
            raise A01Error(f"A01 source_roots[{idx}]（{root_id}）缺 privacy_ceiling：{a01_path}")
        declared.append(root_id)
        action = entry.get("proposed_action")
        normalized = ceiling.strip().casefold()
        if normalized in PRIVATE_CEILINGS:
            private.add(root_id)
        elif normalized not in PUBLIC_CEILINGS:
            # 认不出的敏感级别按私人处理，并把这件事说出来（不静默）。
            print(
                f"annotation_search.py: A01 的 {root_id} privacy_ceiling={ceiling!r} 不在已知取值里，"
                "按私人 root 处理（fail-closed）。",
                file=sys.stderr,
            )
            private.add(root_id)
        elif isinstance(action, str) and PRIVATE_ACTION_TOKEN in action.casefold():
            private.add(root_id)
    return private, declared


def build_private_paths(private_root_ids, scan_roots):
    """root_id -> realpath 前缀列表。

    基点 = 仓根 ∪ 每个扫描根本身及其各级祖先。这样 tmp fixture 里的
    ``<fixture>/canvas-vault`` 与 ``--root <fixture>/canvas-vault`` 都能被同一套
    前缀规则判出，不必把 fixture 路径写进脚本。
    """
    bases = {os.path.realpath(REPO_ROOT)}
    for root in scan_roots:
        current = os.path.realpath(root)
        while True:
            bases.add(current)
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

    mapping = {}
    for root_id in sorted(private_root_ids):
        found = []
        for rel in PRIVATE_RELATIVE_PATHS.get(root_id, ()):
            for base in bases:
                found.append(os.path.realpath(os.path.join(base, rel)))
        for absolute in PRIVATE_ABSOLUTE_PATHS.get(root_id, ()):
            found.append(os.path.realpath(absolute))
        mapping[root_id] = sorted(set(found))
    return mapping


def fold_path(value):
    """路径比较的归一口径：NFC + casefold。

    ⚠️ 单靠 ``os.path.realpath`` 不够：它解软链、解 ``..``，但**不归一大小写**，
    而本机 macOS APFS（以及 Windows）默认大小写不敏感——``<base>/Canvas-Vault`` 与
    ``<base>/canvas-vault`` 是同一个目录，逐字节比较却判成两个。2026-09-19 实测：
    未做 casefold 前，``Canvas-Vault/`` 下的批注会被原样返回，即私人面泄漏。
    NFC 同理挡住 macOS 上分解形态（NFD）与预组合形态写法不同的同一个目录名。

    代价（如实声明）：在大小写敏感的文件系统上，一个**确实另有其物**、只是恰好叫
    ``Canvas-Vault`` 的目录也会被一并排除。这是刻意选的 fail-safe 方向——本工具的
    默认立场是宁可少看也不碰私人面，需要时用 ``--include-private`` 显式解除。
    """
    return unicodedata.normalize("NFC", value).casefold()


def private_root_of(path, private_paths):
    """path（任意形态）落在哪个私人 root 下；不落则返回 None。

    realpath 口径 + ``fold_path`` 归一（见该函数 docstring 里的实测理由）。
    """
    real = fold_path(os.path.realpath(path))
    for root_id, prefixes in private_paths.items():
        for prefix in prefixes:
            folded = fold_path(prefix)
            if real == folded or real.startswith(folded + os.sep):
                return root_id
    for part in real.split(os.sep):
        hit = PRIVATE_COMPONENT_ROOTS.get(part)
        if hit is not None and hit in private_paths:
            return hit
    hit = PRIVATE_BASENAME_ROOTS.get(os.path.basename(real))
    if hit is not None and hit in private_paths:
        return hit
    return None


# --------------------------------------------------------------------------
# 扫描
# --------------------------------------------------------------------------
def iter_markdown_files(scan_roots, private_paths, include_private, pruned, unwalkable):
    """产出待扫的 .md realpath，去重、确定序。私人子树跳过并登记进 pruned。

    ``os.walk`` 默认把 ``scandir`` 的 OSError **直接吞掉**，于是一棵列不出来的子树
    （权限不足 / 挂载点掉线 / 路径过长）连同它下面所有 .md 一起从输入面消失，
    ``files_scanned`` 只是变小，没有任何人会知道。契约 :142 的口径是「不能静默当 0」，
    所以这里传 ``onerror`` 把它们收进 ``unwalkable`` 桶并在汇总行报数。
    """
    seen = set()
    out = []

    def on_walk_error(err):
        unwalkable.append(getattr(err, "filename", None) or str(err))

    for root in scan_roots:
        real_root = os.path.realpath(root)
        if os.path.isfile(real_root):
            if real_root.endswith(".md") and real_root not in seen:
                seen.add(real_root)
                out.append(real_root)
            continue
        for dirpath, dirnames, filenames in os.walk(real_root, onerror=on_walk_error):
            keep = []
            for name in sorted(dirnames):
                if name in PRUNE_DIRS:
                    continue
                child = os.path.join(dirpath, name)
                if not include_private:
                    owner = private_root_of(child, private_paths)
                    if owner is not None:
                        pruned.add((owner, child))
                        continue
                keep.append(name)
            dirnames[:] = keep
            for name in sorted(filenames):
                if not name.endswith(".md"):
                    continue
                full = os.path.join(dirpath, name)
                if not include_private and private_root_of(full, private_paths) is not None:
                    pruned.add((private_root_of(full, private_paths), full))
                    continue
                real = os.path.realpath(full)
                if real in seen:
                    continue
                seen.add(real)
                out.append(real)
    return sorted(out, key=sort_key_path)


def sort_key_path(path):
    """NFC 归一后再比，避免同名文件在 NFD / NFC 文件系统上排序不同。"""
    return (unicodedata.normalize("NFC", path), path)


def read_text(path):
    """严格 UTF-8 读取。含 NUL 或解码失败 → 返回 None（进 unreadable 桶）。"""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError:
        return None
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


# --------------------------------------------------------------------------
# 日期
# --------------------------------------------------------------------------
def find_date(text):
    """从文本里取第一个**日历上真实存在**的 `YYYY-MM-DD`，取不到返回 None。

    只用正则不够：`1234-56-78` 形状合法但不是日期，`2026-02-30` 亦然。报一个假日期
    比报 `unknown` 更坏——前者会被当成事实引用，后者只是承认不知道。
    """
    for match in DATE_RE.finditer(text):
        year, month, day = (int(g) for g in match.groups())
        try:
            datetime.date(year, month, day)
        except ValueError:
            continue
        return match.group(0)
    return None


def frontmatter_date(lines):
    """只认文件开头**闭合的** `---` 块里的 `key: value`，不引 PyYAML。

    「闭合」是硬条件：首行 `---` 若在 FRONTMATTER_MAX_LINES 内没有对应的收尾行，
    它就是一条正文分隔线而不是 frontmatter 开头，此时一个字段都不认。
    """
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for offset in range(1, min(len(lines), FRONTMATTER_MAX_LINES + 1)):
        if lines[offset].strip() in ("---", "..."):
            end = offset
            break
    if end is None:
        return None
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key = line[: line.index(":")].strip().lower()
        if key not in FRONTMATTER_KEYS:
            continue
        value = line[line.index(":") + 1 :].strip().strip("'\"")
        found = find_date(value)
        if found is not None:
            return found
    return None


def git_env():
    """给 git 子进程一份剃掉全部 ``GIT_*`` 的环境。

    不传 ``env=`` 就是把调用方环境整份继承给 git，两个后果都不是假想：

    * ``GIT_DIR`` 一旦存在，git 的仓库发现不再看 ``cwd`` ⇒ ``date`` 会变成
      **另一个仓库**对这条路径的答案，而 ``date_source`` 仍写 ``git``。
    * ``GIT_TRACE`` / ``GIT_TRACE2`` / ``GIT_TRACE2_EVENT`` 之类会让 git
      **往文件里写**——零写 AST 门只看得见 Python 源码里的写调用，看不见子进程。

    ``GIT_OPTIONAL_LOCKS=0`` 再挡一层：只读查询不去碰 index.lock。
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def git_commit_date(path):
    """`git log -1 --format=%cs` —— 只读查询；任何失败都降级返回 None。"""
    workdir = os.path.dirname(path)
    if not workdir:
        workdir = "."
    try:
        proc = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path],
            cwd=workdir,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=git_env(),
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError, ValueError):
        return None
    if proc.returncode != 0:
        return None
    return find_date(proc.stdout.strip())


def resolve_date(path, lines, cache):
    """frontmatter → 文件名 → git → unknown。返回 (date, date_source)。

    ⚠️ 三种来源都是**文件级**的，不是「批注写下的时刻」——所以 date_source 必须
    随日期一起输出，不把 git 提交日期冒充成用户落笔时间。
    """
    if path in cache:
        return cache[path]
    value = frontmatter_date(lines)
    if value is not None:
        result = (value, "frontmatter")
    else:
        found = find_date(os.path.basename(path))
        if found is not None:
            result = (found, "filename")
        else:
            value = git_commit_date(path)
            if value is not None:
                result = (value, "git")
            else:
                result = ("unknown", "unknown")
    cache[path] = result
    return result


# --------------------------------------------------------------------------
# 类别
# --------------------------------------------------------------------------
def relative_label(path, scan_roots):
    """展示用相对路径：`_bmad-output` 段之后；没有该段则相对仓根 / 扫描根。"""
    real = os.path.realpath(path)
    parts = real.split(os.sep)
    if "_bmad-output" in parts:
        idx = len(parts) - 1 - parts[::-1].index("_bmad-output")
        return "/".join(parts[idx + 1 :])
    for root in scan_roots:
        real_root = os.path.realpath(root)
        if real == real_root or real.startswith(real_root + os.sep):
            return os.path.relpath(real, real_root)
    return os.path.basename(real)


def classify(rel):
    if rel.startswith("验收单/批注回复/"):
        return "批注回复"
    if rel.startswith("研究/") and "批注回复" in os.path.basename(rel):
        return "批注回复"
    if rel.startswith("验收单/"):
        return "验收单批注区"
    if rel.startswith("审查/"):
        return "审查"
    if rel.startswith("研究/"):
        return "研究"
    if rel.startswith("implementation-artifacts/goal-cards/"):
        return "goal-cards"
    if rel.startswith("planning-artifacts/"):
        return "planning-artifacts"
    if rel.startswith("决策批注/"):
        return "决策批注"
    return "其他"


def display_path(path):
    real = os.path.realpath(path)
    repo = os.path.realpath(REPO_ROOT)
    if real == repo or real.startswith(repo + os.sep):
        return os.path.relpath(real, repo)
    return real


# --------------------------------------------------------------------------
# 块
# --------------------------------------------------------------------------
def stops_block(line):
    """这一行是否该终止上一条批注的续行收集。

    三类都算「批注到此为止」：

    * 真空行；
    * **引用块里的空行**——那是一个光秃秃的 ``>``，``str.strip()`` 判不出来。
      漏掉这条，``> **User：**`` 的块会一路吃到下面 ``> **Claude（日期）：**``，
      工具就把别人的话当成「用户说过的话」返回（真数据 2 处）；
    * **另一个人开口**——任何以粗体标签开头的行（``**X：``），以及任何本身就命中
      marker 的行（下一条批注的起点）。
    """
    if QUOTE_BLANK_RE.match(line):
        return True
    if SPEAKER_LABEL_RE.match(line):
        return True
    return bool(find_markers(line))


def extract_block(lines, index, marker_name, marker_end, context):
    """marker 行 + 续行。callout 取后续 ``>`` 开头的行；粗体 User 取到收尾 ``**``
    或空行为止。

    返回 ``(block, rest, has_continuation)``。

    ⚠️ ``has_continuation`` 是**独立于** ``--context`` 的事实：续行到底存不存在，
    不该由「显示几行」这个参数决定。所以扫描的下限恒为 1 行，``--context`` 只截
    ``block`` 的长度。2026-09-19 实测：早先版本把两者混成一个上限，``--context 0``
    会让所有换行续写的批注被判成空槽从而默认不列——参数改的是显示，结果却改了语义。
    """
    line = lines[index]
    rest = line[marker_end:]
    limit = max(context, 1)
    collected = []

    if marker_name.startswith(CALLOUT_PREFIX):
        cursor = index + 1
        while cursor < len(lines) and len(collected) < limit:
            nxt = lines[cursor]
            if not nxt.lstrip().startswith(">") or stops_block(nxt):
                break
            collected.append(nxt)
            cursor += 1
    elif re.sub(r"[*\s]", "", rest) != "":
        # 形态 A —— `**User：正文……**`：粗体包住正文本身，收尾靠 `**` **配对**判定。
        # marker 自带一个开启 `**`，所以从奇数起算，累计个数变回偶数 = 该粗体段闭合。
        # ⚠️ 不能写成「见到 `**` 就停」：续行里的**行内加粗**是成对的，奇偶不变却会
        # 骗停，把同一条批注的剩余正文变成检索不到的面。反过来，闭合即停也正好挡住
        # 紧跟其后的 Claude 回复被算进「用户说过的话」。
        pairs = 1 + rest.count("**")
        if pairs % 2 != 0:
            cursor = index + 1
            while cursor < len(lines) and len(collected) < limit:
                nxt = lines[cursor]
                if stops_block(nxt):
                    break
                collected.append(nxt)
                pairs += nxt.count("**")
                if pairs % 2 == 0:
                    break
                cursor += 1
    else:
        # 形态 B —— `**User2：**` 这类**只有标签**的行：粗体包的是标签不是正文，
        # 标签行自身已经配平，正文在后续行，到空行为止。用形态 A 的配对规则会在
        # 第一条续行就收尾（2026-09-19 实测：三行的批注只取到两行）。
        cursor = index + 1
        while cursor < len(lines) and len(collected) < limit:
            nxt = lines[cursor]
            if stops_block(nxt):
                break
            collected.append(nxt)
            cursor += 1
        if not collected and marker_name == "user_bold_zh":
            # H1 整改：中文容器头的真数据布局之一是「标签行 + 空行 + blockquote 引用
            # 用户原话」（审查/2026-08-02-规模化结构检索-审查请求-给ChatGPT.md:23）。
            # 紧邻续行被那个空行截断 ⇒ 整条会被判空槽、默认不列——marker 修好了却仍然
            # 「看不见」。只对该族、且仅在紧邻无续行时：跨**一个**空行，且下一行必须是
            # `>` 引用，收该引用块。不跨更多空行、不收非引用文本（没有证据，不猜）。
            peek = cursor
            if peek < len(lines) and QUOTE_BLANK_RE.match(lines[peek]):
                peek += 1
                if peek < len(lines) and lines[peek].lstrip().startswith(">"):
                    while peek < len(lines) and len(collected) < limit:
                        nxt = lines[peek]
                        if not nxt.lstrip().startswith(">") or stops_block(nxt):
                            break
                        collected.append(nxt)
                        peek += 1

    return [line] + collected[:context], rest, len(collected) > 0


def is_empty_slot(rest, has_continuation):
    """marker 后正文（去 ``**`` 与空白）为空且无续行 ⇒ 空槽。"""
    return re.sub(r"[*\s]", "", rest) == "" and not has_continuation


def extract_story_ids(text):
    found = set()
    for pattern in STORY_ID_PATTERNS:
        for match in pattern.finditer(text):
            found.add(match.group(0))
    return sorted(found)


def find_markers(line):
    """一行上所有 marker 命中，按起点排序：[(name, matched_text, end), ...]"""
    hits = []
    for name, pattern in MARKERS.items():
        for match in pattern.finditer(line):
            hits.append((match.start(), name, match.group(0), match.end()))
    hits.sort(key=lambda item: (item[0], item[1]))
    return [(name, text, end) for _, name, text, end in hits]


def search(
    scan_roots,
    keywords=(),
    stories=(),
    categories=(),
    context=5,
    include_empty=False,
    include_private=False,
    a01_path=DEFAULT_A01,
):
    """返回 (records, stats)。records 已按 (path, line) 确定序排好。

    抛 A01Error（A01 不合约）/ PrivateRootRefused（--root 落进私人 root）。
    """
    private_root_ids, declared_roots = load_private_root_ids(a01_path)
    scan_roots = list(scan_roots)
    private_paths = build_private_paths(private_root_ids, scan_roots)
    # 有路径可拦的 root（其余只是 A01 声明过、仓内无落地路径，不能算「已排除」）。
    enforced_root_ids = {rid for rid, paths in private_paths.items() if paths}

    if not include_private:
        for root in scan_roots:
            owner = private_root_of(root, private_paths)
            if owner is not None:
                raise PrivateRootRefused(f"按 A01 {owner} 私人 root 拒扫：{root}；需要请 --include-private 并自负授权")

    pruned = set()
    unwalkable = []
    files = iter_markdown_files(scan_roots, private_paths, include_private, pruned, unwalkable)

    lowered_keywords = [kw.lower() for kw in keywords]
    wanted_categories = set(categories)

    records = []
    date_cache = {}
    marker_hits = 0
    fenced_hits = 0
    html_comment_hits = 0
    empty_count = 0
    unreadable = []

    for path in files:
        text = read_text(path)
        if text is None:
            unreadable.append(path)
            continue
        lines = text.split("\n")
        rel = relative_label(path, scan_roots)
        category = classify(rel)
        shown_path = display_path(path)
        fenced = False
        commented = False
        for index, line in enumerate(lines):
            if FENCE_RE.match(line):
                fenced = not fenced
                continue
            # HTML 注释状态：开合可能在同一行，所以先看开、行末再看合。
            opens = HTML_COMMENT_OPEN in line
            closes = HTML_COMMENT_CLOSE in line
            in_comment = commented or opens
            if opens and not closes:
                commented = True
            elif closes:
                commented = False
            for marker_name, marker_text, marker_end in find_markers(line):
                marker_hits += 1
                if fenced:
                    fenced_hits += 1
                if in_comment:
                    html_comment_hits += 1
                block, rest, has_continuation = extract_block(lines, index, marker_name, marker_end, context)
                empty = is_empty_slot(rest, has_continuation)
                if empty:
                    empty_count += 1
                    if not include_empty:
                        continue
                if wanted_categories and category not in wanted_categories:
                    continue
                block_text = "\n".join(block)
                matched = False
                if lowered_keywords:
                    low = block_text.lower()
                    for kw in lowered_keywords:
                        if kw in low:
                            matched = True
                            break
                if not matched and stories:
                    for story in stories:
                        if story in block_text or story in shown_path:
                            matched = True
                            break
                if not matched:
                    continue
                date, date_source = resolve_date(path, lines, date_cache)
                records.append(
                    {
                        "path": shown_path,
                        "line": index + 1,
                        "category": category,
                        "date": date,
                        "date_source": date_source,
                        "marker": marker_text,
                        "in_fenced_code": fenced,
                        "in_html_comment": in_comment,
                        "story_ids": extract_story_ids(block_text + "\n" + shown_path),
                        "excerpt": block_text,
                        "empty": empty,
                    }
                )

    records.sort(key=lambda rec: (sort_key_path(rec["path"]), rec["line"], rec["marker"]))
    stats = {
        "files_scanned": len(files),
        "marker_hits": marker_hits,
        "fenced_hits": fenced_hits,
        "html_comment_hits": html_comment_hits,
        "shown": len(records),
        "empty": empty_count,
        "unreadable": len(unreadable),
        "unreadable_paths": sorted(unreadable, key=sort_key_path),
        # ⚠️ 只报**真的有路径映射、真的在拦**的 root。A01 算出 6 个私人 root，
        # 但仓内只有 2 个有落地路径（见 PRIVATE_RELATIVE_PATHS / PRIVATE_ABSOLUTE_PATHS）；
        # 把另外 4 个（含两个 P4-secret）一并写进 excluded_ 会读成「它们也被拦住了」，
        # 而实际上它们是**没有可拦的路径**，不是「已排除」。两者分开报。
        "excluded_private_roots": [] if include_private else sorted(enforced_root_ids),
        "private_roots_without_path": sorted(private_root_ids - enforced_root_ids),
        "declared_roots": declared_roots,
        "unwalkable": sorted(set(unwalkable)),
        "pruned_private_paths": sorted({item[1] for item in pruned}, key=sort_key_path),
    }
    return records, stats


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="annotation_search.py",
        description="批注只读检索：关键词 / Story ID → file:line + 摘录 + 日期 + 来源类别。",
    )
    parser.add_argument(
        "--keyword", action="append", default=[], help="关键词，可重复，大小写不敏感，块内任一行命中即算"
    )
    parser.add_argument(
        "--story", action="append", default=[], help="Story / 卡号，可重复，大小写敏感，路径或块文本含即命中"
    )
    parser.add_argument("--root", action="append", default=[], help=f"扫描根，可重复，默认 {DEFAULT_ROOT}")
    parser.add_argument("--a01", default=DEFAULT_A01, help="A01 边界声明 JSON 路径")
    parser.add_argument(
        "--category", action="append", default=[], choices=list(CATEGORIES), help="只看某些来源类别，可重复"
    )
    parser.add_argument("--context", type=int, default=5, help="摘录续行上限，默认 5")
    parser.add_argument("--include-empty", action="store_true", help="把空槽也列出来（默认只计数）")
    parser.add_argument("--include-private", action="store_true", help="解除 A01 私人 root 排除（自负授权）")
    parser.add_argument("--json", action="store_true", dest="as_json", help="stdout 输出 JSON 数组")
    return parser


def format_summary(stats):
    return (
        "# files_scanned={files_scanned} marker_hits={marker_hits} shown={shown} "
        "empty={empty} fenced={fenced_hits} html_comment={html_comment_hits} "
        "unreadable={unreadable} unwalkable={unwalkable_count} "
        "excluded_private_roots={excluded_private_roots}".format(unwalkable_count=len(stats["unwalkable"]), **stats)
    )


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.keyword and not args.story:
        parser.print_usage(sys.stderr)
        print("annotation_search.py: 至少需要一个 --keyword 或 --story", file=sys.stderr)
        return 2
    if args.context < 0:
        parser.print_usage(sys.stderr)
        print("annotation_search.py: --context 不能为负", file=sys.stderr)
        return 2

    scan_roots = args.root if args.root else [DEFAULT_ROOT]

    try:
        records, stats = search(
            scan_roots,
            keywords=args.keyword,
            stories=args.story,
            categories=args.category,
            context=args.context,
            include_empty=args.include_empty,
            include_private=args.include_private,
            a01_path=args.a01,
        )
    except A01Error as exc:
        print(f"annotation_search.py: {exc}", file=sys.stderr)
        print("annotation_search.py: A01 不可用即拒扫（fail-closed），不降级为「没有私人 root」。", file=sys.stderr)
        return 2
    except PrivateRootRefused as exc:
        print(f"annotation_search.py: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for rec in records:
            head = rec["excerpt"].split("\n")[0].strip()
            if len(head) > EXCERPT_LINE_LIMIT:
                head = head[:EXCERPT_LINE_LIMIT] + "…"
            print("{path}:{line} | {category} | {date}({date_source}) | {marker} | {head}".format(head=head, **rec))

    print(format_summary(stats), file=sys.stderr)
    if stats["pruned_private_paths"]:
        print(f"# pruned_private_paths={stats['pruned_private_paths']}", file=sys.stderr)
    if stats["unreadable_paths"]:
        print(f"# unreadable_paths={stats['unreadable_paths']}", file=sys.stderr)
    if stats["unwalkable"]:
        print(f"# unwalkable_dirs={stats['unwalkable']}", file=sys.stderr)
    if stats["private_roots_without_path"]:
        print(
            f"# private_roots_without_path={stats['private_roots_without_path']}"
            "（A01 声明为私人，但仓内无落地路径可拦——不等于那里没有批注）",
            file=sys.stderr,
        )
    return 0 if records else 1


if __name__ == "__main__":
    raise SystemExit(main())
