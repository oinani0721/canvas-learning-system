"""CARD-SKILL-PORT-LINT — vault skill 可移植性三层基线门 (BATCH-2026-09-07-第十三批)。

被测物: `canvas-vault/.claude/` 下随 vault 部署的 9 份 SKILL.md + 7 份 scripts/*.py
(仓根 `.claude/skills/` 那 6 份**不**随 vault 部署, 不在本门覆盖面; `board-split`
与 `clear-inbox` 只有 scripts 没有 SKILL.md, 只进层 3)。

## 为什么要这道门

决策页 §四 曾按四个数字描述可移植性面, 2026-09-07 主干 `da690bf8` 实测**四个都不对**:
`mcp__` 32 → **33**、相对路径 12 → **16**(口径含 `.claude/scripts/`)、`/tmp/*.json`
9 → **8**、`UserPromptSubmit` 「注入 26 行」→ **0 命中**。更要紧的是当时**没有任何门**
锁住这个面 —— 谁新写一处 `/tmp/`、一个写死的 8011、一段绝对路径, 都不会有人发现。
本门把现状逐份逐指标钉死: **新增命中即红, 减少也红**(减少 = 有人整改却没登记基线,
必须同步改常量, 基线改动本身就是验收单条目)。

## 三层

层 1 frontmatter — 键集精确相等 + `name` == 目录名且 kebab-case + `description` 非空
                   + `allowed-tools` 形态(现状: 非空 YAML list)。
层 2 正文 grep   — 9 份 × 9 指标精确计数(`/tmp` 与 8011 各钉 all/ns **两端**)。
层 3 scripts     — `skills/*/scripts/*.py` + `scripts/*.py` × 3 指标精确计数, **文件集合本身也钉**
                   (新增脚本 = 红, 逼人登记)。
越界判据       — 每份 SKILL.md 的越界 `/tmp` normpath 多重集精确相等(见下方专段)。

## 层 2 的「裸」口径, 以及**为什么钉两端而不是钉裸值**

「裸」的语义是 **总数 − 放行形态数**, 与卡文 §二.2 的 shell 裁判逐字同源:

    bare_tmp  = count("/tmp/")  − count("/tmp/cls-exam/")
    bare_8011 = count("8011")   − count(":-http://localhost:8011")

⛔ 不得只数总数: `/tmp/cls-exam/x` 仍含 `/tmp/`、`${CLS_BACKEND_URL:-http://localhost:8011}`
仍含 `8011` —— 只数总数则整改在指标上**不可见**。也不得在这里另写一套正则(口径分叉)。

⛔⛔ **但基线钉的是 `tmp_all` / `tmp_ns` / `p8011_all` / `p8011_ns` 四个数, 不是两个差值。**
只钉差值有一个真实的假绿面 —— 差值对「一增一减」完全失明。2026-09-08 实测:
把 `:435` 那处裸 `/tmp/exam-created-event.json` 改进命名空间(ns +1), 同时另加一行
全新的裸 `/tmp/attacker-new-file.json`(all +1), 则 `all=7 ns=5 ⇒ bare 仍 = 2`,
门**照绿**, 而新增的那处裸 `/tmp/` 完全不可见。那正是本门存在的理由被击穿。

钉住两端 ⇒ 自动钉住它们的差, 反之不成立。`bare_tmp()` / `bare_8011()` 保留为派生
算式, 供断言消息与「对账卡文 §二.2 裸值」那条用例引用。

放行的是**写死的字面量**, 不是「`cls-` 前缀类」: 这样 `/tmp/clsx.json`(无 `-`)、
`/tmp/cls-x/y.json`(`cls-` 后是别的东西)、`/tmp/cls-exam.json`(无尾斜杠, 不是目录
命名空间)、`/tmp/a/../cls-exam/`(写法不是钦定形态) 全部照旧计入裸值报红。同理 8011
只放行 `:-http://localhost:8011` 这一个缺省形态, `${X:-8011}` / `${X-8011}`(单破折号,
语义不同: 只在**未定义**时用缺省, 空串时展开成空) 之类一律报红。

## 第四条判据: 越界路径 (normpath)

子串计数天生看不见路径语义。`/tmp/cls-exam/../x` 含 `/tmp/` 一次 + `/tmp/cls-exam/`
一次 ⇒ 裸值 0 ⇒ **计数判据放行**, 而它规范化之后是 `/tmp/x`, 已经越出命名空间
(Codex round-1 HIGH, 2026-09-08)。`check_escaping_tmp()` 把每份的越界 normpath
**多重集**钉死, 与计数判据分工互补:

  计数判据 —— 命中数变没变(与 shell 裁判逐字同源)
  越界判据 —— 命中的那个路径规范化后指向哪里

⚠️ 两条判据对同一输入可以给出**不同**结论, 那是分工不是矛盾: `/tmp/a/../cls-exam/z`
在计数下报红(写法不是钦定形态), 在越界判据下放行(规范化后确实落在命名空间内)。

越界基线现状 6 处, 全是「只钉不改」的已知项: start-exam-board `:430/:435` 的
exam-created-event(被 tests/regression 钉死) + quiz-answer 4 处(E-2 归 U5-B)。

## `UserPromptSubmit` 为什么不进指标

决策页称它「注入 26 行」。9 份 SKILL.md 里 **0 命中** —— 但那不是「口径不可复现」,
是**找错了地方**: 2026-09-08 实测它在 `canvas-vault/.claude/settings.json`(`:3` 键名 +
`:9` 降级 payload), 是一个真实的 hook, 调 `/api/v1/chat/rag/enrich-hook` 往每轮对话里
注入笔记片段。

那个文件**不在本门的覆盖面内**(见下方「本门测量不到的面」), 归 U3-C。「26 行」这个数
仍未证实(要证得跑后端看它实际注入多少行, 本卡禁连) ⇒ 不纳入指标, 差异登记在验收单。

## 本门测量不到的面 (如实声明, 不是遗漏)

覆盖面 = `skills/*/SKILL.md` + `skills/*/scripts/*.py` + `scripts/*.py`。
2026-09-08 实测, `canvas-vault/.claude/` 下**剩余**的 git-tracked 文件里确实还有债:

    hooks/session-end-archive.py:21   1 处 8011
    mcp.json:5 (URL) + :13 (说明文字)  2 处 8011
    settings.json:9                   1 处 8011  ← 同时是上面那个 UserPromptSubmit hook

合计 **4 处 8011**, 全部归 **U3-C 步 3**(模板化), 本卡不碰也测不到。
`skills/configure-whiteboard/templates/whiteboard.md.template` 也在覆盖面外, 实测 0 债。

⚠️ 卡文 §〇 把这 4 处记成「`.claude/mcp.json:5` / 仓根 `.mcp.json:5`」—— 实测**仓根
`.mcp.json` 没有 8011**, 而 `canvas-vault/.claude/mcp.json` 有**两处**。总数对, 分布不对。

## 交接

`QUIZ_ANSWER_BASELINE` 与 `U6_SCRIPTS_BASELINE` **单列**在下方各自的常量段,
不混进主 dict —— 这样 U5-B / U6 各自只改自己那一段, diff 一眼可见。

## 本门不做什么 (档 B, 只钉不改)

- **相对路径改写**(把 `python3 "<vault 绝对路径>/.claude/skills/board-recap/scripts/recap_scan.py"`
  写成 `scripts/recap_scan.py`): 成立与否**完全取决于 Claude Code 执行 Bash 时的 cwd**,
  若 cwd = vault 根则该相对路径根本不存在。**解锁条件 = Bash cwd 实证** —— 在探针 vault
  放一份只跑 `pwd` 的 skill, 由 Claude Code 真实触发一次并落盘; 证据到手前一律不做。
  且目标形态对 10 个点位里的 6 个根本不适用(1 个是 templates 不是 scripts, 5 个是跨
  skill 的 SKILL.md 参照, 无等价相对写法) ⇒ `claude_dir_ref` 指标**只钉现状**。
- `argument-hint` / `model` 挪进 `metadata`、`allowed-tools` 列表→字符串、替换
  `AskUserQuestion`、改 `mcp__` 名: 全是 Claude Code 行为面(E-1 一线不得损失可用性),
  且对字符串形态 `allowed-tools` 的解析无本地证据 ⇒ 只钉不改, 二线转正后再议。
- `quiz-answer/SKILL.md` 的 `harness_tree` 解析(E-2)归 U5-B, 本门只钉它的现状计数。
- start-exam-board `:430/:435` 的 `/tmp/exam-created-event.json`: 该字面量被
  `backend/tests/regression/test_g3_3_cas.py:49`(**模块级** assert, 改了整个文件
  collect 期 ERROR)、`:144`、`test_learning_events_schema_contract.py:1013/:1017`
  逐字钉死 ⇒ 只钉不改, 归第十四批 `tests/regression` 解耦卡。
"""

from __future__ import annotations

import posixpath
import re
import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = REPO_ROOT / "canvas-vault" / ".claude"

# ── 层 1 基线 ───────────────────────────────────────────────────────────────
#: 9 份 vault skill 的 frontmatter 键集 (2026-09-08 主干实测: 9 份完全一致)。
FRONTMATTER_KEYS = frozenset({"name", "description", "argument-hint", "allowed-tools", "model"})

#: 随 vault 部署的 skill 全集 —— 少一份 / 多一份都算漂移。
EXPECTED_SKILLS = frozenset(
    {
        "ai-linked-doc",
        "board-recap",
        "chat-with-context",
        "configure-whiteboard",
        "exam-quick",
        "node-chat",
        "quiz-answer",
        "start-exam-board",
        "study-question",
    }
)

_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

# ── 层 2 指标定义 ───────────────────────────────────────────────────────────
#: 放行形态: 写死的字面量, **不是前缀类**(见模块 docstring「裸口径」段)。
TMP_NAMESPACE = "/tmp/cls-exam/"
URL_DEFAULT_FORM = ":-http://localhost:8011"

#: `.claude/(skills|scripts)/` 的 ERE 等价 —— 与 §二.2 的 `grep -oE` 逐字同源。
_CLAUDE_DIR_RE = re.compile(r"\.claude/(?:skills|scripts)/")

#: ⛔ **两端各钉一个数, 不是只钉差值** —— 见模块 docstring「为什么钉两端而不是钉裸值」。
BODY_METRICS = (
    "ask_user_question",
    "mcp_tool",
    "claude_dir_ref",
    "tmp_all",
    "tmp_ns",
    "p8011_all",
    "p8011_ns",
    "tree_name",
    "users_path",
)


#: 卡文 §二.2 与验收单以「裸值」为口径, 这里给出派生算式供断言消息与对账用例引用。
#: 钉住 all 与 ns 两端 ⇒ 自动钉住它们的差, 反之不成立。
def bare_tmp(counts: dict[str, int]) -> int:
    return counts["tmp_all"] - counts["tmp_ns"]


def bare_8011(counts: dict[str, int]) -> int:
    return counts["p8011_all"] - counts["p8011_ns"]


# ── 越界路径判据 (与上面的子串计数**互补**, 不是替代) ───────────────────────
#: 一个 `/tmp/…` 路径 token 的粗切分: 到空白、反引号、引号、括号、中文标点为止。
#: 宁可切多也不切少 —— 切多只会让 normpath 结果更长, 不会把越界路径变成合规路径。
_TMP_TOKEN_RE = re.compile(r"/tmp/[^\s`\"'()（）,，;；:：]*")


#: ⛔ **为什么光有子串计数不够**(Codex round-1 HIGH, 2026-09-08):
#: `/tmp/cls-exam/../x` 含 `/tmp/` 一次、`/tmp/cls-exam/` 一次 ⇒ 裸值 = 0 ⇒ 子串规则
#: **放行**, 而它 normpath 之后是 `/tmp/x`, 已经越出命名空间。作者原先的负控只覆盖了
#: 穿越发生在**进入命名空间之前**的 `/tmp/a/../cls-exam/`, 漏掉了发生在**之后**的
#: 对称变体。子串规则天生看不见路径语义 ⇒ 另立这条 normpath 判据。
#:
#: 两条判据分工: 计数判据管「有没有新增/减少命中」(与 shell 裁判逐字同源),
#: 本判据管「命中的那个路径到底指向哪里」。各自有自己的负控。
def escaping_tmp_paths(text: str) -> list[tuple[str, str]]:
    """返回 `(原始 token, normpath 结果)`, 只含 **normpath 后不在命名空间内**的那些。

    命名空间内 = 规范化后等于 `/tmp/cls-exam` 或以 `/tmp/cls-exam/` 开头。
    """
    ns = TMP_NAMESPACE.rstrip("/")
    out: list[tuple[str, str]] = []
    for tok in _TMP_TOKEN_RE.findall(text):
        norm = posixpath.normpath(tok)
        if norm != ns and not norm.startswith(ns + "/"):
            out.append((tok, norm))
    return out


# ── 层 2 基线 (2026-09-08 开工实测; start-exam-board 为**整改后**目标值) ────
#: ⛔ 精确相等, 不是 ≤ —— 增红是防新债, 减红是逼人登记整改。
BASELINE: dict[str, dict[str, int]] = {
    "ai-linked-doc": {
        "ask_user_question": 4,
        "mcp_tool": 2,
        "claude_dir_ref": 2,
        "tmp_all": 0,
        "tmp_ns": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "tree_name": 0,
        "users_path": 0,
    },
    "board-recap": {
        "ask_user_question": 5,
        "mcp_tool": 3,
        "claude_dir_ref": 5,
        "tmp_all": 0,
        "tmp_ns": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "tree_name": 0,
        "users_path": 0,
    },
    "chat-with-context": {
        "ask_user_question": 0,
        "mcp_tool": 9,
        "claude_dir_ref": 0,
        "tmp_all": 0,
        "tmp_ns": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "tree_name": 0,
        "users_path": 0,
    },
    "configure-whiteboard": {
        "ask_user_question": 15,
        "mcp_tool": 2,
        "claude_dir_ref": 2,
        "tmp_all": 0,
        "tmp_ns": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "tree_name": 0,
        "users_path": 0,
    },
    "exam-quick": {
        "ask_user_question": 0,
        "mcp_tool": 1,
        "claude_dir_ref": 0,
        "tmp_all": 0,
        "tmp_ns": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "tree_name": 0,
        "users_path": 0,
    },
    "node-chat": {
        "ask_user_question": 0,
        "mcp_tool": 2,
        "claude_dir_ref": 0,
        "tmp_all": 0,
        "tmp_ns": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "tree_name": 0,
        "users_path": 0,
    },
    # ⛔ start-exam-board 是本卡**唯一有整改**的一份, 下面是整改**后**的目标值:
    #   `:188/:198` 的 `/tmp/exam-candidates.json` → `/tmp/cls-exam/exam-candidates.json`
    #   (`:188` 另加一条 `mkdir -p /tmp/cls-exam/` —— 命名空间目录首次运行时不存在,
    #    而写入方是 Write 工具、不是那段 python(它只读 + `os.remove`), 所以建目录
    #    必须落在 Write **之前**; 该字面量带尾斜杠 ⇒ 同时计入 tmpAll 与 tmpNS,
    #    裸值不受影响)
    #   ⇒ 收工实测 tmp_all 4→6 / tmp_ns 0→4 / **裸 4→2**(剩 `:430/:435`, 归第十四批解耦卡)
    #   (6/4 而非卡文预估的 5/3: 文件末尾的「变更记录」小节自身也写了一次
    #    `/tmp/cls-exam/`, 同时进 all 与 ns ⇒ 裸值不受影响。)
    #   ⛔ 基线钉的是 **all 与 ns 两端**, 不是裸值 —— 见模块 docstring
    #   「为什么钉两端而不是钉裸值」: 只钉裸值时「一增一减」不可见。
    #   `:304` 的 `http://localhost:8011` → `${CLS_BACKEND_URL:-http://localhost:8011}`
    #   ⇒ p8011All 1 / p8011NS 1 / **裸 1→0**
    "start-exam-board": {
        "ask_user_question": 4,
        "mcp_tool": 3,
        "claude_dir_ref": 3,
        "tmp_all": 6,
        "tmp_ns": 4,
        "p8011_all": 1,
        "p8011_ns": 1,
        "tree_name": 0,
        "users_path": 0,
    },
    "study-question": {
        "ask_user_question": 0,
        "mcp_tool": 10,
        "claude_dir_ref": 0,
        "tmp_all": 0,
        "tmp_ns": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "tree_name": 0,
        "users_path": 0,
    },
}

# ── 越界路径基线 (normpath 口径; 按 skill 的**多重集**钉, 不只钉数量) ────────
#: 用多重集(排序后的列表)而不是个数 —— 换掉一个越界路径而个数不变时也要红。
#: 现状全部是「只钉不改」的已知项:
#:   start-exam-board `:430/:435` 的 exam-created-event(被 tests/regression 钉死),
#:   quiz-answer 的 4 处(E-2 归 U5-B)。
#: **新增任何越界路径 = 红**, 这正是子串计数看不见的那一面。
ESCAPING_TMP_BASELINE: dict[str, list[str]] = {
    "ai-linked-doc": [],
    "board-recap": [],
    "chat-with-context": [],
    "configure-whiteboard": [],
    "exam-quick": [],
    "node-chat": [],
    "quiz-answer": [
        "/tmp/quiz-answer-incr.json",
        "/tmp/quiz-answer-incr.json",
        "/tmp/quiz-answer-payload.json",
        "/tmp/quiz-answer-payload.json",
    ],
    "start-exam-board": [
        "/tmp/exam-created-event.json",
        "/tmp/exam-created-event.json",
    ],
    "study-question": [],
}


# ── 交接常量 ① ─────────────────────────────────────────────────────────────
#: **U5-B (CARD-G3-3-R2) 独占更新**; rebase 时保 lint 绿。
#:
#: quiz-answer 的 `harness_tree` 解析(E-2)归 U5-B, 本卡只钉现状、一个字节都不改。
#: U5-B 改 `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 后**必须**同步改这一段
#: (它的 4 处裸 `/tmp/` 在 `:98/:106/:205/:233`, 4 处 `claude_dir_ref` 在
#: `:74/:2977/:2985/:3076`)。单列在这里就是为了让那次 diff 一眼可见。
QUIZ_ANSWER_BASELINE: dict[str, int] = {
    "ask_user_question": 2,
    "mcp_tool": 1,
    "claude_dir_ref": 4,
    "tmp_all": 4,
    "tmp_ns": 0,
    "p8011_all": 0,
    "p8011_ns": 0,
    "tree_name": 0,
    "users_path": 0,
}

# ── 层 3 基线 ───────────────────────────────────────────────────────────────
SCRIPT_METRICS = ("tmp", "users_path", "tree_name")

#: 非 U6 地盘的 5 份。路径相对 root(`canvas-vault/.claude`), posix 写法。
#: `scripts/fsrs_bridge.py` 的 `/Users/` 1 + 树名 1 是**零写者**的写死路径, 只钉不改
#: (本卡硬边界: 禁碰 `fsrs_bridge.py` / `decay_beta.py`)。
SCRIPTS_BASELINE: dict[str, dict[str, int]] = {
    "skills/board-recap/scripts/recap_scan.py": {"tmp": 1, "users_path": 0, "tree_name": 0},
    "skills/board-split/scripts/split_preview.py": {"tmp": 0, "users_path": 0, "tree_name": 0},
    "scripts/decay_beta.py": {"tmp": 0, "users_path": 0, "tree_name": 0},
    "scripts/fsrs_bridge.py": {"tmp": 0, "users_path": 1, "tree_name": 1},
    "scripts/sync_board_concepts.py": {"tmp": 0, "users_path": 0, "tree_name": 0},
}

# ── 交接常量 ② ─────────────────────────────────────────────────────────────
#: **U6-A / U6-B / U6-C (CARD-G6-9c / G6-7-R / G6-6) 改 `board-recap` 或 `clear-inbox`
#: 的 scripts、或在这两个 skill 下新增脚本, 必须同步更新此常量**(本层同时钉文件集合,
#: 新增脚本本身也会红)。
#:
#: U4-B 在合并队列**第 2 组**、U6 在**第 3 组** ⇒ U6 rebase 到含本卡的候选树后自查此常量。
#: 三项计数实测均 0 = **零余量**, 加任何一处 `/tmp` / `/Users/` / 树名即红。
U6_SCRIPTS_BASELINE: dict[str, dict[str, int]] = {
    "skills/board-recap/scripts/recap_exam_build.py": {"tmp": 0, "users_path": 0, "tree_name": 0},
    "skills/clear-inbox/scripts/inbox_preview.py": {"tmp": 0, "users_path": 0, "tree_name": 0},
}


# ── 纯函数: 三层检查 (root 可注入, 便于负控在 tmp 副本上做) ─────────────────
def _count(text: str, needle: str) -> int:
    """字面量非重叠计数 —— 与 `grep -oF <needle> | wc -l` 同语义。

    模式不含换行 ⇒ grep 的「按行匹配」与这里的「按全文匹配」逐字等价。
    """
    return text.count(needle)


def _body_counts(text: str) -> dict[str, int]:
    """一份 SKILL.md 正文的 7 项指标实测值 (裸口径 = 总数 − 放行形态数)。"""
    return {
        "ask_user_question": _count(text, "AskUserQuestion"),
        "mcp_tool": _count(text, "mcp__canvas-learning-mcp__"),
        "claude_dir_ref": len(_CLAUDE_DIR_RE.findall(text)),
        "tmp_all": _count(text, "/tmp/"),
        "tmp_ns": _count(text, TMP_NAMESPACE),
        "p8011_all": _count(text, "8011"),
        "p8011_ns": _count(text, URL_DEFAULT_FORM),
        "tree_name": _count(text, "feature-obsidian-hybrid-dev"),
        "users_path": _count(text, "/Users/"),
    }


def _script_counts(text: str) -> dict[str, int]:
    """一份 scripts/*.py 的 3 项指标实测值。

    ⛔ 层 3 的 `tmp` 口径是 `/tmp`(**无**尾斜杠) —— 脚本里 `/tmp` 常以
    `os.path.join("/tmp", x)` 或散文形态出现, 带尾斜杠会漏。
    """
    return {
        "tmp": _count(text, "/tmp"),
        "users_path": _count(text, "/Users/"),
        "tree_name": _count(text, "feature-obsidian-hybrid-dev"),
    }


def check_frontmatter(root: Path) -> list[str]:
    """层 1: 返回违规描述列表 (空 = 全绿)。"""
    problems: list[str] = []
    skills_dir = root / "skills"
    found = {d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()}
    if found != EXPECTED_SKILLS:
        problems.append(
            f"[层1] skill 集合漂移: 期望={sorted(EXPECTED_SKILLS)} 实测={sorted(found)} "
            f"(多={sorted(found - EXPECTED_SKILLS)} 少={sorted(EXPECTED_SKILLS - found)})"
        )
    for name in sorted(found):
        f = skills_dir / name / "SKILL.md"
        text = f.read_text(encoding="utf-8")
        m = _FRONTMATTER_RE.match(text)
        if not m:
            problems.append(f"[层1] {name}: 缺 frontmatter (`---` 块必须在文件最开头)")
            continue
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError as e:  # pragma: no cover - 树上不该出现
            problems.append(f"[层1] {name}: frontmatter YAML 解析失败: {e}")
            continue
        if not isinstance(fm, dict):
            problems.append(f"[层1] {name}: frontmatter 不是映射, 实测类型={type(fm).__name__}")
            continue
        keys = frozenset(fm)
        if keys != FRONTMATTER_KEYS:
            problems.append(
                f"[层1] {name}: 键集不等 期望={sorted(FRONTMATTER_KEYS)} 实测={sorted(keys)} "
                f"(多={sorted(keys - FRONTMATTER_KEYS)} 少={sorted(FRONTMATTER_KEYS - keys)})"
            )
        if fm.get("name") != name:
            problems.append(f"[层1] {name}: name 必须 == 目录名 期望={name!r} 实测={fm.get('name')!r}")
        if not (isinstance(fm.get("name"), str) and _KEBAB_RE.match(fm["name"])):
            problems.append(f"[层1] {name}: name 必须 kebab-case 期望匹配={_KEBAB_RE.pattern} 实测={fm.get('name')!r}")
        desc = fm.get("description")
        if not (isinstance(desc, str) and desc.strip()):
            problems.append(f"[层1] {name}: description 必须非空字符串 实测={desc!r}")
        at = fm.get("allowed-tools")
        if not (isinstance(at, list) and at and all(isinstance(x, str) for x in at)):
            problems.append(
                f"[层1] {name}: allowed-tools 形态漂移 期望=非空 YAML 列表(元素为 str) "
                f"实测类型={type(at).__name__} 值={at!r}"
            )
    return problems


def check_body(root: Path, baseline: dict[str, dict[str, int]]) -> list[str]:
    """层 2: 返回违规描述列表 (空 = 全绿)。每条含 skill + 指标 + 期望 + 实测。"""
    problems: list[str] = []
    skills_dir = root / "skills"
    for name in sorted(baseline):
        f = skills_dir / name / "SKILL.md"
        if not f.exists():
            problems.append(f"[层2] {name}: SKILL.md 不存在 (基线要求存在) path={f}")
            continue
        actual = _body_counts(f.read_text(encoding="utf-8"))
        for metric in BODY_METRICS:
            want, got = baseline[name][metric], actual[metric]
            if want != got:
                problems.append(
                    f"[层2] {name}: 指标 {metric} 期望={want} 实测={got} "
                    f"({'新增' if got > want else '减少'} {abs(got - want)} 处 —— "
                    f"新增即债, 减少说明有人整改却没同步基线常量)"
                )
    return problems


def check_escaping_tmp(root: Path, baseline: dict[str, list[str]]) -> list[str]:
    """越界路径判据: 每份 SKILL.md 的越界 normpath **多重集**精确相等。

    与 `check_body` 的子串计数**互补**: 计数管「命中数变没变」, 这里管「命中的那个
    路径规范化之后指向哪里」。`/tmp/cls-exam/../x` 在计数下裸值为 0(放行), 在这里
    normpath 成 `/tmp/x` ⇒ 越界 ⇒ 红。
    """
    problems: list[str] = []
    skills_dir = root / "skills"
    for name in sorted(baseline):
        f = skills_dir / name / "SKILL.md"
        if not f.exists():
            problems.append(f"[越界] {name}: SKILL.md 不存在 (基线要求存在) path={f}")
            continue
        actual = sorted(norm for _tok, norm in escaping_tmp_paths(f.read_text(encoding="utf-8")))
        want = sorted(baseline[name])
        if actual != want:
            extra = [p for p in actual if actual.count(p) > want.count(p) or p not in want]
            missing = [p for p in want if p not in actual]
            problems.append(
                f"[越界] {name}: 越出 {TMP_NAMESPACE} 的路径多重集不等 "
                f"期望={want} 实测={actual} (新增={sorted(set(extra))} 缺失={sorted(set(missing))}) —— "
                f"新增即债; 缺失说明有人整改却没同步 ESCAPING_TMP_BASELINE"
            )
    return problems


def check_scripts(root: Path, baseline: dict[str, dict[str, int]]) -> list[str]:
    """层 3: 返回违规描述列表 (空 = 全绿)。文件集合本身也钉。"""
    problems: list[str] = []
    found = {
        p.relative_to(root).as_posix()
        for p in sorted([*(root / "skills").glob("*/scripts/*.py"), *(root / "scripts").glob("*.py")])
    }
    expected = frozenset(baseline)
    if found != expected:
        problems.append(
            f"[层3] scripts 文件集合漂移: 期望 {len(expected)} 份 实测 {len(found)} 份 "
            f"(新增={sorted(found - expected)} 缺失={sorted(expected - found)}) —— "
            f"新增脚本必须登记进 SCRIPTS_BASELINE 或 U6_SCRIPTS_BASELINE"
        )
    for rel in sorted(expected & found):
        actual = _script_counts((root / rel).read_text(encoding="utf-8"))
        for metric in SCRIPT_METRICS:
            want, got = baseline[rel][metric], actual[metric]
            if want != got:
                problems.append(f"[层3] {rel}: 指标 {metric} 期望={want} 实测={got}")
    return problems


def _merged_body_baseline() -> dict[str, dict[str, int]]:
    """主 dict + 单列的 quiz-answer 段 —— 单列是为了让 U5-B 的 diff 一眼可见。"""
    return {**BASELINE, "quiz-answer": QUIZ_ANSWER_BASELINE}


def _merged_scripts_baseline() -> dict[str, dict[str, int]]:
    """主 dict + 单列的 U6 段 —— 单列是为了让 U6 的 diff 一眼可见。"""
    return {**SCRIPTS_BASELINE, **U6_SCRIPTS_BASELINE}


# ── 对树 (正控) ─────────────────────────────────────────────────────────────
def test_layer1_frontmatter_matches_baseline():
    """层 1: 9 份 frontmatter 键集精确相等 + name == 目录名且 kebab-case + description 非空。"""
    problems = check_frontmatter(DEFAULT_ROOT)
    assert not problems, "frontmatter 基线漂移:\n" + "\n".join(problems)


def test_layer2_body_counts_match_baseline():
    """层 2: 9 份 × 9 指标精确计数 (`/tmp` 与 8011 各钉 all/ns 两端, 不只钉差值)。"""
    problems = check_body(DEFAULT_ROOT, _merged_body_baseline())
    assert not problems, "正文指标基线漂移:\n" + "\n".join(problems)


def test_bare_values_match_card_expectations():
    """与卡文 §二.2 / 验收单的**裸值**口径对账 —— 那两份文档以裸值叙述, 这里把
    派生算式显式钉一次, 免得「基线钉的是四端」与「文档写的是裸值」两套说法漂开。

    整改目标: start-exam-board 裸 `/tmp/` 4 → **2**(剩 `:430/:435`)、裸 8011 1 → **0**。
    """
    skills_dir = DEFAULT_ROOT / "skills"
    seb = _body_counts((skills_dir / "start-exam-board" / "SKILL.md").read_text(encoding="utf-8"))
    assert bare_tmp(seb) == 2, (
        f"start-exam-board 裸 /tmp/ 期望=2 实测={bare_tmp(seb)} "
        f"(all={seb['tmp_all']} ns={seb['tmp_ns']}); 剩的两处是 :430/:435 的 exam-created-event"
    )
    assert bare_8011(seb) == 0, (
        f"start-exam-board 裸 8011 期望=0 实测={bare_8011(seb)} (all={seb['p8011_all']} ns={seb['p8011_ns']})"
    )
    qa = _body_counts((skills_dir / "quiz-answer" / "SKILL.md").read_text(encoding="utf-8"))
    assert bare_tmp(qa) == 4, f"quiz-answer 裸 /tmp/ 期望=4(只钉不改, 归 U5-B) 实测={bare_tmp(qa)}"


def test_escaping_tmp_paths_match_baseline():
    """越界判据(正控): 9 份的越界路径多重集 == 基线(只钉不改的 6 处已知项)。"""
    problems = check_escaping_tmp(DEFAULT_ROOT, ESCAPING_TMP_BASELINE)
    assert not problems, "越界路径基线漂移:\n" + "\n".join(problems)


@pytest.mark.parametrize(
    "literal,bare_delta,escapes,why",
    [
        ("/tmp/cls-exam/", 0, False, "钦定形态本身 —— 两条都放行"),
        ("/tmp/cls-exam/x.json", 0, False, "命名空间内的文件 —— 两条都放行"),
        ("/tmp/cls-exam", 1, False, "无尾斜杠: 写法不是钦定形态(子串红), 但指向就是命名空间本身(不越界)"),
        ("/tmp/a/../cls-exam/z", 1, False, "穿越在**前**: 写法不合规(子串红), 规范化后仍落在命名空间内(不越界)"),
        ("/tmp/cls-exam/../x", 0, True, "穿越在**后**: 子串看不见(裸值 0), 规范化后越界(越界红)"),
        ("/tmp/other.json", 1, True, "普通裸路径 —— 两条都红"),
    ],
)
def test_two_judges_cover_each_other_without_gap(literal: str, bare_delta: int, escapes: bool, why: str):
    """**两条判据的分工表** —— 每个不合规形态都必须至少被其中一条拦下。

    这张表本身就是判据: 将来若有人放宽任一条(比如把放行改成 `cls-` 前缀类, 或删掉
    越界判据), 对应行会立刻翻转。⛔ 注意第 3、4 行的 `escapes=False` **不是漏网**
    —— 它们由子串那一列的 `bare_delta=1` 拦下; 真正危险的是**两列都是 0/False**
    的行, 那才是放行, 表里只有前两行, 且都是真正合规的形态。
    """
    counts = _body_counts(literal)
    assert bare_tmp(counts) == bare_delta, (
        f"{literal!r} ({why}): 子串裸值期望={bare_delta} 实测={bare_tmp(counts)} "
        f"(all={counts['tmp_all']} ns={counts['tmp_ns']})"
    )
    assert bool(escaping_tmp_paths(literal)) is escapes, (
        f"{literal!r} ({why}): 越界期望={escapes} 实测={escaping_tmp_paths(literal)}"
    )
    if bare_delta == 0 and not escapes:
        assert literal.startswith(TMP_NAMESPACE), (
            f"⛔ {literal!r} 被两条判据一起放行, 但它不在 {TMP_NAMESPACE} 下 —— 这就是缺口"
        )


def test_layer3_scripts_counts_and_fileset_match_baseline():
    """层 3: scripts 文件集合 + 3 指标精确计数 (含 U6 地盘两份)。"""
    problems = check_scripts(DEFAULT_ROOT, _merged_scripts_baseline())
    assert not problems, "scripts 基线漂移:\n" + "\n".join(problems)


#: 本门**测量不到**但确实存在的债 —— 全部归 U3-C 步 3(模板化)。
#: 路径相对 `canvas-vault/.claude/`; 值 = 该文件里 `8011` 的出现次数。
#: 钉住它是为了让「本门看不见这些」这句话有判据撑着, 而不是一句会过期的散文:
#:   · U3-C 真把它们模板化了 ⇒ 这里变红 ⇒ 逼人回来删掉这条(债已还清)
#:   · 有人往这些文件里再加一处写死端口 ⇒ 这里也变红 ⇒ 至少有人知道
OUT_OF_SCOPE_8011 = {
    "hooks/session-end-archive.py": 1,
    "mcp.json": 2,
    "settings.json": 1,
}


def test_out_of_scope_hardcoded_ports_are_registered():
    """本门覆盖面**之外**的 8011 债: 逐文件计数钉死(归 U3-C, 本卡不碰)。

    ⛔ 这条**不是**在测本门的判据, 是在钉「本门测不到什么」这个声明本身。
    覆盖面 = skills/*/SKILL.md + skills/*/scripts/*.py + scripts/*.py; 下面这些文件
    一个都不在里面, 所以前面四类判据对它们完全失明 —— 如实登记, 而不是假装干净。
    """
    root = DEFAULT_ROOT
    actual = {}
    for rel in sorted(OUT_OF_SCOPE_8011):
        f = root / rel
        assert f.exists(), f"登记的越界债文件不存在(路径漂移?): {f}"
        actual[rel] = f.read_text(encoding="utf-8").count("8011")
    assert actual == OUT_OF_SCOPE_8011, (
        f"覆盖面外的 8011 债漂移 期望={OUT_OF_SCOPE_8011} 实测={actual} —— "
        f"变少说明 U3-C 已模板化(请删掉本常量对应项), 变多说明有人新写了写死端口"
    )

    # 验伪锚: 确认这些文件真的不在本门四类判据的覆盖面内(否则这条用例是多余的)
    covered = (
        {p.relative_to(root).as_posix() for p in (root / "skills").glob("*/SKILL.md")}
        | {p.relative_to(root).as_posix() for p in (root / "skills").glob("*/scripts/*.py")}
        | {p.relative_to(root).as_posix() for p in (root / "scripts").glob("*.py")}
    )
    overlap = set(OUT_OF_SCOPE_8011) & covered
    assert not overlap, f"这些文件其实**在**覆盖面内, 本用例的前提不成立: {sorted(overlap)}"


def test_baseline_constants_are_disjoint_and_complete():
    """交接常量必须**单列**且不与主 dict 重叠 —— 防有人「顺手」把 quiz-answer /
    U6 两份并回主 dict, 那会让 U5-B / U6 的 rebase diff 混进无关行。"""
    assert "quiz-answer" not in BASELINE, "quiz-answer 必须单列在 QUIZ_ANSWER_BASELINE, 不得进主 BASELINE"
    overlap = set(SCRIPTS_BASELINE) & set(U6_SCRIPTS_BASELINE)
    assert not overlap, f"U6 两份必须单列, 不得同时出现在 SCRIPTS_BASELINE: {sorted(overlap)}"
    assert set(_merged_body_baseline()) == EXPECTED_SKILLS, (
        f"层 2 基线覆盖面必须恰好 == 9 份 vault skill "
        f"期望={sorted(EXPECTED_SKILLS)} 实测={sorted(_merged_body_baseline())}"
    )
    # ⛔ **不得写成 `== {那两份}`**(Codex round-1 MEDIUM, 2026-09-08): 该常量的注释
    # 要求「U6 新增脚本必须同步登记进来」, 而 `==` 会把照做的 U6 直接打红 —— 门的
    # 指令与门的判据自相矛盾, U6 无论怎么做都错。判据改为两条, 各自只管自己那面:
    #   (i) 原本那两份**必须仍在**(不许被人顺手删掉交接项);
    #   (ii) 新登记的条目**必须落在 U6 的两个 skill 目录下**(不许拿这个常量当垃圾桶,
    #        把别人地盘的脚本塞进来绕过 SCRIPTS_BASELINE 的审阅)。
    # 「未登记的新脚本立刻红」由层 3 的文件集合精确相等保证, 不靠这里。
    u6_seed = {
        "skills/board-recap/scripts/recap_exam_build.py",
        "skills/clear-inbox/scripts/inbox_preview.py",
    }
    assert u6_seed <= set(U6_SCRIPTS_BASELINE), (
        f"U6 交接项被删 —— 手册 §一 明列这两份属 U6 地盘, 必须留在 U6_SCRIPTS_BASELINE: "
        f"缺={sorted(u6_seed - set(U6_SCRIPTS_BASELINE))}"
    )
    u6_dirs = ("skills/board-recap/scripts/", "skills/clear-inbox/scripts/")
    stray = [p for p in U6_SCRIPTS_BASELINE if not p.startswith(u6_dirs)]
    assert not stray, (
        f"U6_SCRIPTS_BASELINE 只收 U6 地盘({' / '.join(u6_dirs)})下的脚本, "
        f"别处的请登记进 SCRIPTS_BASELINE: {sorted(stray)}"
    )


def test_u6_can_register_a_new_script_without_being_blocked():
    """⑨ **Codex round-1 MEDIUM** —— U6 照注释办事不得被本门自己拦住。

    场景: U6 在 `clear-inbox/scripts/` 下新增一个脚本, 按 `U6_SCRIPTS_BASELINE` 的
    注释把它登记进来。此时那条交接断言**必须放行**(否则门的指令与门的判据互相打架,
    U6 怎么做都错); 而「新增脚本不登记就红」仍由层 3 的文件集合保证 —— 见下一条。
    """
    extended = {
        **U6_SCRIPTS_BASELINE,
        "skills/clear-inbox/scripts/new_u6_tool.py": {"tmp": 0, "users_path": 0, "tree_name": 0},
    }
    u6_seed = {"skills/board-recap/scripts/recap_exam_build.py", "skills/clear-inbox/scripts/inbox_preview.py"}
    u6_dirs = ("skills/board-recap/scripts/", "skills/clear-inbox/scripts/")
    assert u6_seed <= set(extended), "登记新脚本后原两份仍在 ⇒ 该放行"
    assert not [p for p in extended if not p.startswith(u6_dirs)], "新脚本在 U6 地盘内 ⇒ 该放行"

    # 反向: 把别人地盘的脚本塞进 U6 常量 ⇒ 必须被拦(否则这个常量变成绕过审阅的垃圾桶)
    smuggled = {**U6_SCRIPTS_BASELINE, "scripts/fsrs_bridge.py": {"tmp": 0, "users_path": 1, "tree_name": 1}}
    assert [p for p in smuggled if not p.startswith(u6_dirs)] == ["scripts/fsrs_bridge.py"], (
        "非 U6 地盘的脚本混进 U6_SCRIPTS_BASELINE 必须被拦"
    )


# ── 对 tmp 副本 (负控) ──────────────────────────────────────────────────────
@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    """`canvas-vault/.claude` 的 skills/ + scripts/ 两个子树的 tmp 副本。

    ⛔ 负控一律在副本上做, 绝不在树上临时变异(变异残留会污染同批其它裁判)。
    """
    root = tmp_path / ".claude"
    shutil.copytree(DEFAULT_ROOT / "skills", root / "skills")
    shutil.copytree(DEFAULT_ROOT / "scripts", root / "scripts")
    return root


def _append_body(root: Path, skill: str, line: str) -> None:
    f = root / "skills" / skill / "SKILL.md"
    f.write_text(f.read_text(encoding="utf-8") + "\n" + line + "\n", encoding="utf-8")


def test_negative_control_untouched_copy_is_green(sandbox: Path):
    """④ 对照组: 未改副本三层全绿 —— 证明负控的「红」来自变异而非副本本身。"""
    assert not check_frontmatter(sandbox), check_frontmatter(sandbox)
    assert not check_body(sandbox, _merged_body_baseline()), check_body(sandbox, _merged_body_baseline())
    assert not check_scripts(sandbox, _merged_scripts_baseline()), check_scripts(sandbox, _merged_scripts_baseline())


def test_negative_control_new_bare_tmp_reddens_layer2(sandbox: Path):
    """① exam-quick 副本加一行裸 `/tmp/x.json` → 层 2 红, 消息含 skill 名与指标。"""
    _append_body(sandbox, "exam-quick", "临时写到 /tmp/x.json 再读回。")
    problems = check_body(sandbox, _merged_body_baseline())
    assert problems, "新增裸 /tmp/ 必须报红"
    joined = "\n".join(problems)
    assert "exam-quick" in joined and "tmp_all" in joined, joined
    assert "期望=0 实测=1" in joined, joined


def test_negative_control_extra_frontmatter_key_reddens_layer1(sandbox: Path):
    """② node-chat 副本 frontmatter 加 `foo: bar` → 层 1 红且消息含 foo。"""
    f = sandbox / "skills" / "node-chat" / "SKILL.md"
    text = f.read_text(encoding="utf-8")
    f.write_text(text.replace("---\n", "---\nfoo: bar\n", 1), encoding="utf-8")
    problems = check_frontmatter(sandbox)
    assert problems, "frontmatter 多一个键必须报红"
    joined = "\n".join(problems)
    assert "node-chat" in joined and "foo" in joined, joined


def test_negative_control_new_script_reddens_layer3_twice(sandbox: Path):
    """③ 副本 scripts/ 加 probe.py 含 `/Users/x` → 层 3 报**两条**: 文件集合 + 计数。

    ⛔ 两条都要 —— 只报文件集合的话, 「改了已登记脚本的内容」这类漂移看不见;
    只报计数的话, 「新增脚本」这类漂移看不见。
    """
    (sandbox / "skills" / "board-split" / "scripts" / "probe.py").write_text('P = "/Users/x"\n', encoding="utf-8")
    problems = check_scripts(sandbox, _merged_scripts_baseline())
    joined = "\n".join(problems)
    assert any("文件集合漂移" in p for p in problems), joined
    assert "probe.py" in joined, joined

    # 计数那一条: 把 probe.py 登记进基线后, 内容里的 /Users/ 仍必须被计数抓到
    baseline = {
        **_merged_scripts_baseline(),
        "skills/board-split/scripts/probe.py": {"tmp": 0, "users_path": 0, "tree_name": 0},
    }
    problems2 = check_scripts(sandbox, baseline)
    joined2 = "\n".join(problems2)
    assert any("probe.py" in p and "users_path" in p for p in problems2), joined2
    assert "期望=0 实测=1" in joined2, joined2


def test_negative_control_equal_count_swap_must_redden(sandbox: Path):
    """⑦ **差值判据的假绿面** —— 一增一减必须被抓到。

    攻击形态: 把一处原本裸的 `/tmp/` 改进命名空间(ns +1), 同时另加一处全新的裸
    `/tmp/`(all +1)。此时 `bare = all − ns` **不变**, 只钉差值的门会照绿, 而实际上
    新增了一处裸 `/tmp/` —— 那正是本门存在的理由被击穿。基线钉两端就能抓到。
    """
    f = sandbox / "skills" / "start-exam-board" / "SKILL.md"
    text = f.read_text(encoding="utf-8")
    swapped = text.replace('P = "/tmp/exam-created-event.json"', 'P = "/tmp/cls-exam/exam-created-event.json"', 1)
    assert swapped != text, "预置失败: 没找到要搬进命名空间的那处裸 /tmp/"
    f.write_text(swapped + "\n临时缓存写到 /tmp/attacker-new-file.json 再读回。\n", encoding="utf-8")

    counts = _body_counts(f.read_text(encoding="utf-8"))
    assert bare_tmp(counts) == BASELINE["start-exam-board"]["tmp_all"] - BASELINE["start-exam-board"]["tmp_ns"], (
        "本用例的前提是**裸值不变**(否则抓到的是别的东西, 不是这个假绿面): "
        f"实测裸值={bare_tmp(counts)} all={counts['tmp_all']} ns={counts['tmp_ns']}"
    )
    problems = check_body(sandbox, _merged_body_baseline())
    joined = "\n".join(problems)
    assert any("start-exam-board" in p and "tmp_all" in p for p in problems), (
        f"一增一减必须被 tmp_all 那一端抓到(裸值此时不变), 实得: {joined}"
    )


@pytest.mark.parametrize(
    "literal,norm",
    [
        ("/tmp/cls-exam/../x.json", "/tmp/x.json"),
        ("/tmp/cls-exam/a/../../y.json", "/tmp/y.json"),
        ("/tmp/cls-exam/./../z.json", "/tmp/z.json"),
    ],
)
def test_negative_control_escape_after_namespace_must_redden(sandbox: Path, literal: str, norm: str):
    """⑧ **Codex round-1 HIGH** —— 穿越发生在**进入命名空间之后**。

    这三个形态在子串计数下都是 `/tmp/` 一次 + `/tmp/cls-exam/` 一次 ⇒ **裸值 0, 计数
    判据放行**; 但 normpath 之后它们指向命名空间外。作者原先只测了穿越在**前**的
    `/tmp/a/../cls-exam/`, 漏了这个对称变体。

    本用例同时断言「计数判据看不见」与「越界判据看得见」—— 前者是为了钉住这条负控
    确实在考越界判据, 而不是被计数那一层顺手打红(判据必须绑定被哪一层拒的)。
    """
    f = sandbox / "skills" / "exam-quick" / "SKILL.md"
    before = _body_counts(f.read_text(encoding="utf-8"))
    _append_body(sandbox, "exam-quick", f"临时写到 {literal} 再读回。")
    after = _body_counts(f.read_text(encoding="utf-8"))

    assert bare_tmp(after) == bare_tmp(before), (
        f"本用例的前提是**计数判据看不见**(否则考的不是越界判据): 裸值 {bare_tmp(before)}→{bare_tmp(after)}"
    )
    problems = check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)
    joined = "\n".join(problems)
    assert any("exam-quick" in p and "[越界]" in p for p in problems), f"{literal} 必须被越界判据抓到, 实得: {joined}"
    assert norm in joined, f"消息里应给出 normpath 结果 {norm}, 实得: {joined}"


def test_negative_control_namespace_form_does_not_raise_bare_value(sandbox: Path):
    """⑤ `/tmp/cls-exam/x.json` 加进副本 → **裸值不变**(证放行口径生效)。

    ⚠️ 注意与「不红」的区别: 基线钉的是 all/ns **两端**, 所以新增任何一处 `/tmp/`
    ——哪怕是合规的命名空间形态——都会让两端同时 +1 而报红, **这是设计如此**
    (新增即须登记基线)。放行口径要证的是「它不抬高**裸值**」, 不是「它不用登记」。
    对照 `test_negative_control_near_miss_tmp_forms_must_redden`: 那些形态只抬高
    `tmp_all` 一端, 裸值 +1。
    """
    before = _body_counts((sandbox / "skills" / "exam-quick" / "SKILL.md").read_text(encoding="utf-8"))
    _append_body(sandbox, "exam-quick", "临时写到 /tmp/cls-exam/x.json 再读回。")
    after = _body_counts((sandbox / "skills" / "exam-quick" / "SKILL.md").read_text(encoding="utf-8"))

    assert after["tmp_all"] == before["tmp_all"] + 1, "预置失败: 该形态没被 tmp_all 端计到"
    assert after["tmp_ns"] == before["tmp_ns"] + 1, "放行口径失效: 命名空间形态没被 tmp_ns 端计到"
    assert bare_tmp(after) == bare_tmp(before), (
        f"命名空间形态不得抬高裸值 期望={bare_tmp(before)} 实测={bare_tmp(after)} "
        f"(all {before['tmp_all']}→{after['tmp_all']} ns {before['tmp_ns']}→{after['tmp_ns']})"
    )


@pytest.mark.parametrize(
    "literal,why",
    [
        ("/tmp/clsx.json", "无 `-`, 不是 cls-exam 命名空间"),
        ("/tmp/cls-x/y.json", "`cls-` 后是别的东西"),
        ("/tmp/cls-exam.json", "无尾斜杠, 不是目录命名空间"),
        ("/tmp/a/../cls-exam/z.json", "路径穿越, 不是写死形态"),
    ],
)
def test_negative_control_near_miss_tmp_forms_must_redden(sandbox: Path, literal: str, why: str):
    """⑤' 反向: 放行口径是**写死的 `/tmp/cls-exam/`**, 不是「`cls-` 前缀类」。

    这四个形态各自差一处写法, 全部必须照旧计入**裸值**报红 —— 否则「含 cls- 就放」
    会把整类假放行放进来。

    ⛔ 判据盯**裸值 +1**, 不是盯「tmp_all 变了」: 合规的命名空间形态也会抬高 tmp_all
    (两端同涨), 只断言 tmp_all 变了区分不出这两类, 等于判据比它声称的宽。
    """
    f = sandbox / "skills" / "exam-quick" / "SKILL.md"
    before = _body_counts(f.read_text(encoding="utf-8"))
    _append_body(sandbox, "exam-quick", f"临时写到 {literal} 再读回。")
    after = _body_counts(f.read_text(encoding="utf-8"))

    assert bare_tmp(after) == bare_tmp(before) + 1, (
        f"{literal} ({why}) 必须被当作**裸**命中 期望裸值={bare_tmp(before) + 1} "
        f"实测={bare_tmp(after)} (all {before['tmp_all']}→{after['tmp_all']} "
        f"ns {before['tmp_ns']}→{after['tmp_ns']})"
    )
    problems = check_body(sandbox, _merged_body_baseline())
    joined = "\n".join(problems)
    assert any("exam-quick" in p and "tmp_all" in p for p in problems), f"{literal} ({why}) 必须报红, 实得: {joined}"


def test_negative_control_url_default_form_does_not_raise_bare_but_plain_does(sandbox: Path):
    """⑥ 缺省形态**不抬高裸 8011**; 裸 `http://localhost:8011` 抬高。

    与 ⑤ 同理: 两者都会让 `p8011_all` 变化并因此报红(新增即须登记), 区分点在**裸值**。
    """
    f = sandbox / "skills" / "exam-quick" / "SKILL.md"
    before = _body_counts(f.read_text(encoding="utf-8"))
    _append_body(sandbox, "exam-quick", 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/api/v1/ping"')
    after_ns = _body_counts(f.read_text(encoding="utf-8"))
    assert after_ns["p8011_all"] == before["p8011_all"] + 1, "预置失败: 该形态没被 p8011_all 端计到"
    assert after_ns["p8011_ns"] == before["p8011_ns"] + 1, "放行口径失效: 缺省形态没被 p8011_ns 端计到"
    assert bare_8011(after_ns) == bare_8011(before), (
        f"缺省形态不得抬高裸 8011 期望={bare_8011(before)} 实测={bare_8011(after_ns)}"
    )

    _append_body(sandbox, "exam-quick", "curl http://localhost:8011/api/v1/ping")
    after_bare = _body_counts(f.read_text(encoding="utf-8"))
    assert bare_8011(after_bare) == bare_8011(after_ns) + 1, (
        f"裸 URL 必须抬高裸 8011 期望={bare_8011(after_ns) + 1} 实测={bare_8011(after_bare)}"
    )
    problems = check_body(sandbox, _merged_body_baseline())
    joined = "\n".join(problems)
    assert any("exam-quick" in p and "p8011_all" in p for p in problems), joined


@pytest.mark.parametrize(
    "form", ["${X:-8011}", "PORT=8011", "http://127.0.0.1:8011", "${CLS_BACKEND_URL-http://localhost:8011}"]
)
def test_negative_control_other_8011_forms_raise_bare(sandbox: Path, form: str):
    """⑥' 只放行 `:-http://localhost:8011` 这**一个**缺省形态, 别的一律抬高裸值。

    末一条是 `${X-…}` **单破折号** —— 与 `:-` 语义不同(前者只在**未定义**时用缺省,
    变量被设成空串时会展开成空), 不在放行名单内。
    """
    f = sandbox / "skills" / "exam-quick" / "SKILL.md"
    before = _body_counts(f.read_text(encoding="utf-8"))
    _append_body(sandbox, "exam-quick", f"端口配置 {form}")
    after = _body_counts(f.read_text(encoding="utf-8"))
    assert bare_8011(after) == bare_8011(before) + 1, (
        f"{form} 必须被当作裸命中 期望裸值={bare_8011(before) + 1} 实测={bare_8011(after)}"
    )
