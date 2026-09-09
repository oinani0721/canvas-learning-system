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

## 三层 + 两条附加判据

层 1 frontmatter — 键集精确相等 + `name` == 目录名且 kebab-case + `description` 非空
                   + `allowed-tools` 形态(现状: 非空 YAML list)。
层 2 正文 grep   — 9 份 × 9 指标精确计数(`/tmp` 与 8011 各钉 all/ns **两端**)。
层 3 scripts     — `skills/*/scripts/*.py` + `scripts/*.py` × 3 指标精确计数, **文件集合本身也钉**
                   (新增脚本 = 红, 逼人登记)。
越界判据 v3    — 每份 SKILL.md 的越界 `/tmp` normpath **集合**精确相等(ast/shlex 真解析)。
可疑行判据     — `/tmp` 与 `..` 或 `$` 同一**逻辑行**的行号集合精确相等(字面证据档)。
动态拼接判据   — fence 内「含 `/tmp` 的常量参与了动态拼接/格式化」的行号集合精确相等
                   (`ast` 层面的证据档; 现状全 9 份皆空 = 零余量)。

⚠️ 后两条是**同一处置的两个触发面**: 落点静态不可判 ⇒ 要人登记, 不假装能算出来。
它们互补 —— `"/tmp/cls-exam/" + PARENT + "/x"` 既无 `..` 也无 `$`, 只有动态拼接
判据看得见; `P="/tmp/cls-exam/$1"` 的 `$` 只有可疑行判据看得见。

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

## 第四条判据: 越界路径 (normpath, v3 真解析)

子串计数天生看不见路径语义。`/tmp/cls-exam/../x` 含 `/tmp/` 一次 + `/tmp/cls-exam/`
一次 ⇒ 裸值 0 ⇒ **计数判据放行**, 而它规范化之后是 `/tmp/x`, 已经越出命名空间
(Codex round-1 HIGH, 2026-09-08)。`check_escaping_tmp()` 把每份的越界 normpath
**集合**钉死, 与计数判据分工互补:

  计数判据 —— 命中数变没变(与 shell 裁判逐字同源)
  越界判据 —— 命中的那个路径规范化后指向哪里

r1→r5 每轮都出现新的切分绕过(逗号截断 → 冒充子串 → 白名单边界 → 跨行拼接 →
引号内空格/开括号冒充 → 混合引号/点号拼接 → **拼组遮蔽 / 三引号 / `\x2e` 转义 /
`r` 前缀 / `+` 拼接 / shell 单引号 / `~~~` 围栏**)。根因始终是同一个:
**手写切分器在模拟解析器, 而模拟得不够像**。

v3 不再模拟, 直接调用真解析器: fence 整块试 `ast.parse`(隐式拼接在解析期就被折成
单个 `Constant`, 三引号 / 前缀 / 转义全部还原; 显式 `+` 常量链另行折叠), 整块非
Python 时逐行降级到单行 `ast` → `shlex.split(posix=True)`; 裸 token 正则始终再扫;
散文只认 markdown backtick span。详见 `_FENCE_RE` 上方 v3 注释。

**每个 `Constant` / shell 词是独立候选** ⇒ 不会像 v2 那样把两个函数参数拼成一串而
互相遮蔽(r5 HIGH-1 是 v2 引入的回归, v3 一并消除)。

⚠️ 两条判据对同一输入可以给出**不同**结论, 那是分工不是矛盾: `/tmp/a/../cls-exam/z`
在计数下报红(写法不是钦定形态), 在越界判据下放行(规范化后确实落在命名空间内)。

越界基线现状(2026-09-08 v2 实测) 全是「只钉不改」的已知项: start-exam-board 的
exam-created-event(被 tests/regression 钉死)、`:128` 裸 `/tmp` 提法、`:188` 变更行
backtick 命令 span; quiz-answer 两形态(E-2 归 U5-B); board-recap `:58` 裸 `/tmp` 提法。

## 第五条判据: 可疑行(不依赖解析的兜底) + 已知的保守误报方向

v3 之后越界判据已走真解析, 但**运行期展开静态不可判**: `P="/tmp/cls-exam/$1"`
(位置参数)、`P="/tmp/cls-exam/"$REL`(引号外拼接)—— `ast`/`shlex` 只看得到源码,
看不到 `$1` 的值。`check_suspicious_tmp_lines()` 只问「这一**逻辑行**值不值得人
看一眼」(`/tmp` 且有 `..` 或 `$`), 因此不受任何解析能力所限, 是最后一道。
逻辑行 = fence 内经反斜杠续行与「行尾引号 + 次行引号开头」合并(散文行不参与)。

**登记的保守误报方向(Codex r3 LOW-7 / r4 LOW-7·9 等, 不修)**: 判据在下列形态上
会**多**报红(判成债), 方向安全 —— `P=/tmp/x` 无空格赋值、`>/tmp/x` 重定向、
`curl -o/tmp/cls-exam/x` 短选项连写、`file:///tmp/…`、全角标点紧贴(`路径：/tmp/…`、
`路径，/tmp/…` 计入端 ns=0); fence 裸 token 会把紧邻的 ASCII 逗号并进条目
(`/tmp/x.json, then…` 的越界条目带尾逗号)。树上无这些形态; 真要用时写成分隔符
隔开的形式(`-o /tmp/…`)即可。另: 覆盖表末尾的「整字面量 normpath」断言是纵深
防御 —— 对合规行退回 `startswith` 不会被现有行抓住(不存在前缀失败而 normpath
成立的合规形态), 如实声明不强辩。

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
`skills/configure-whiteboard/templates/whiteboard.md.template` 也在覆盖面外 —— 九项里
`claude_dir_ref` 实测 **2**(其余八项 0), 且该模板被逐字复制进每张新白板 md ⇒ 传播源头
在覆盖面外。(本文件初稿写「实测 0 债」, 2026-09-09 自查更正。)

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

import ast
import codeop
import functools
import hashlib
import posixpath
import re
import shlex
import shutil
import textwrap
import time
import warnings
from collections import Counter
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

#: ⛔ **放行侧要窄, 计入侧可以宽**(Codex round-2 HIGH-c, 2026-09-08)。
#:
#: `tmp_ns` 是**放行**端 —— 它每 +1 就抵消一个 `tmp_all`。用裸子串
#: `count("/tmp/cls-exam/")` 会被 `/var/cache/tmp/cls-exam/x.json` 骗过: 那个路径**根本
#: 不在 `/tmp` 下**, 却同时给 `tmp_all` 与 `tmp_ns` 各 +1, 于是「把一处真命名空间路径
#: 替换成这个冒充版」四端全不变 ⇒ 两条判据一起漏网(实测 c' 场景)。放行端因此必须要求
#: `/tmp/` 是**绝对路径起点**。
#:
#: `tmp_all` 是**计入**端, 保持裸子串: `/var/cache/tmp/x` 让它 +1 = 把一个别的绝对路径
#: 债也算进来, 偏保守 —— 保守在计入端是安全的, 在放行端才是漏洞。
#:
#: ⛔⛔ **黑名单式边界不够**(Codex round-3 HIGH-1, 2026-09-08): 排除
#: `[A-Za-z0-9_.~$-]` 漏了 `/`、`+`、非 ASCII 等**路径字符** ——
#: `/var/cache//tmp/cls-exam/x`(双斜杠)、`/var/cache+/tmp/…`、`/var/缓存/tmp/…`
#: 里 `/tmp` 前的字符不在黑名单 ⇒ 照样被当作绝对路径起点 ⇒ 冒充仍然成立。
#: 改成**分隔符白名单**(更窄): `/tmp` 前只允许 空白/引号/反引号/开括号,
#: 其余一律不算路径起点。代价是少量保守误报(`P=/tmp/x` 无空格赋值、
#: `>/tmp/x` 重定向、`-o/tmp/x` 连写、`file:///tmp/…` 会被判成债)——
#: 误报方向 = 计入债 = 安全; 树上无这些形态, 基线不变。
#:
#: ⚠️ 与 §二.2 shell 裁判(`grep -oF '/tmp/cls-exam/'`)的口径差**只在有人写冒充路径时
#: 才出现**; 树上现状无冒充路径, 两侧同为 4。`test_ns_counting_agrees_with_shell_judge`
#: 把这个「当前一致」钉住 —— 将来两侧分叉, 恰恰说明有人写了冒充路径, 正是要抓的。
_TMP_NS_RE = re.compile(r'(?<![^\s"`\'(\[{（【])/tmp/cls-exam/')

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


# ── 越界路径判据 v3: 真解析 (与上面的子串计数**互补**, 不是替代) ─────────────
#: ⛔ **五轮教训: 手写切分器追不上语言语义**。r1→r5 每轮都被换一种坏法骗过 ——
#: r1 穿越在后 → r2 逗号截断 / 冒充子串 → r3 白名单边界 / 跨行拼接 →
#: r4 引号内空格与开括号冒充 / 混合引号拼接 / 单行点号拼接 →
#: r5 **拼组遮蔽**(两个独立参数被保守拼组连成一串, 反而掩盖了第二个的越界)、
#: 三引号 `\"\"\"…\"\"\"`、`\x2e\x2e` 源码级转义、`r"."` 前缀、`+` 拼接、
#: shell 单引号内 `\` 不转义、`~~~` fence、嵌套反引号 fence。
#:
#: 这些**全部**是「模拟解析器而模拟得不够像」的产物。v3 不再模拟, 直接调用真解析器:
#:   ① fenced block 整块试 `ast.parse` —— Python 在**解析期**就把隐式拼接折成单个
#:      `Constant`(`("/tmp/cls-exam/" r"." "./x")` 直接得到 `/tmp/cls-exam/../x`),
#:      三引号 / 各种前缀 / `\x2e` 转义也都由解析器还原; 显式 `+` 的常量链由
#:      `_fold_str()` 折叠。**每个 `Constant` 是独立候选** ⇒ 不会像 v2 那样把两个
#:      函数参数连成一串而互相遮蔽(r5 HIGH-1)。
#:   ② 整块不是合法 Python(SKILL.md 的 fence 多是 bash + heredoc) ⇒ 逐行降级:
#:      先试单行 `ast.parse`, 再试 `shlex.split(posix=True)` 取真 shell 词
#:      (单/双引号与反斜杠转义按 POSIX 语义, r5 HIGH-2 的吞尾由此消失)。
#:   ③ 裸 token 正则**始终**再扫一遍(散文与 fence 都扫): 覆盖 `mkdir -p /tmp/cls-exam/`
#:      这类未加引号的命令行片段。
#:   ④ 散文只认 markdown **backtick span**(单双引号在散文里是自然语言, 不是字面量)。
#:
#: 仍然做不到的(如实声明, 见模块 docstring「保守误报与残余盲区」):
#: 运行期变量展开(`$1` / `${REL}` —— 由可疑行判据要求登记)、symlink 落点、
#: 以及 `shlex` 也无法解析的畸形 shell(此时退回裸 token 与可疑行两道)。
#: fence **开启**标记: 允许列表项前缀(`- ` / `1. `)与引用前缀(`> `)——CommonMark 里
#: 列表项/引用块内的 fence 合法, 原先 `^\s*` 认不出 `- ```python` / `> ```python`。
#: r9 HIGH-3b: 列表与引用两种嵌套顺序都认(`- > ```py` 与 `> - ```py`)。
#: ⛔ r12 HIGH-4: 无容器前缀时缩进最多 3 空格 —— 4 空格起是**缩进代码块**, 不开 fence。
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(?:(?:>[ \t]{0,3})+|(?:[-*+][ \t]+|\d+[.)][ \t]+))*(`{3,}|~{3,})")
#: fence **闭合**标记: ⛔ r8 HIGH-3 —— 闭合**不允许**列表项前缀。普通 fence 里的
#: `- ``` ` 是内容行, 让它闭合围栏会把后面的真代码块推成散文(方向是漏检)。
#: ⛔ r11 HIGH-5b: CommonMark 规定 closing fence 缩进**最多 3 空格** —— `^\\s*` 会让
#: 普通 fence 内四空格缩进的 ``` 提前闭合围栏(那本该是内容)。
#: ⛔ r12 MEDIUM-1: 正则收**任意**前导空白, 相对阈值(`<= open_indent + 3`)在
#: `_fence_blocks` 的闭合条件里判 —— 写成绝对 `^ {0,3}` 会让 `10. ```python`
#: 这种多字符列表 marker 下的 closing(缩进 4)闭不上、把后面的正文吞进块。
_FENCE_CLOSE_RE = re.compile(r"^[ \t]*(?:>[ \t]{0,3})*(`{3,}|~{3,})")
_FENCE_RE = _FENCE_OPEN_RE  # 兼容旧引用点
#: markdown code span: N 个反引号开、N 个反引号闭(CommonMark)。r7 HIGH-1: 原先只认
#: 单反引号, 于是 ``cp "/tmp/cls-exam/"`printf .`"./x"`` 这种**双**反引号 span
#: (内部正好可以放命令替换)整类提取不出来。
_BACKTICK_SPAN_RE = re.compile(r"(?<!`)(`+)(?!`)([^\n]*?)(?<!`)\1(?!`)")
#: ⛔ r8 HIGH-2: 反斜杠**转义**的反引号不参与 run —— `\```x`` ` 里第一枚被转义,
#: 剩下两枚才是 opening。不掩码就会按三枚处理 ⇒ 整个 span 提不出来(**漏检**方向,
#: 不是保守误报)。掩码保持长度, 匹配后按位置回原串取内容。
_MD_ESCAPE_RE = re.compile(r"\\.")


def _backtick_spans(text: str) -> list[str]:
    r"""text 里的 markdown code span 内容。

    ⛔ r9 HIGH-2: 掩码**只用于定位 opening run** —— code span **内部**的反斜杠是
    普通字符, CommonMark 找 closing run 时不处理转义。上一版对全串掩码, 于是
    `` `/tmp/cls-exam/x\` `` 的末尾反引号被抹掉、整个 span 提不出来(**漏检**方向)。
    """
    masked = _MD_ESCAPE_RE.sub("\x00\x00", text)  # 只用来判「这枚反引号是不是被转义的」
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        if text[i] != "`" or masked[i] != "`":  # 被转义的反引号不开启 span
            i += 1
            continue
        run = 0
        while i + run < n and text[i + run] == "`" and masked[i + run] == "`":
            run += 1
        close = text.find("`" * run, i + run)  # closing 在**原串**上找, 不看转义
        # ⛔ r10 HIGH-1: closing run 必须**恰好**等长 —— 两端都要检查。只查右边界时
        # `` `p ```/var/cache(/tmp/…``` `` 会用三反引号串的**尾部**提前闭合单反引号,
        # 真正的路径 span 整个消失(漏检方向)。
        while close != -1 and (
            (close + run < n and text[close + run] == "`") or (close > 0 and text[close - 1] == "`")
        ):
            close = text.find("`" * run, close + 1)
        if close == -1:
            i += run
            continue
        out.append(text[i + run : close])
        i = close + run
    return out


#: 裸 token: 白名单左边界(r3 HIGH-1) + 中文标点停止(防散文拖尾)。
_TMP_TOKEN_RE = re.compile(r'(?<![^\s"`\'(\[{（【])/tmp/[^\s`"\'()（）；;：，、。]*')
_TMP_LINE_RE = re.compile(r"/tmp")
_QUOTE_TAIL_RE = re.compile(r"['\"`]\s*\Z")  # 行尾(可带尾随空白)的引号
_QUOTE_HEAD_RE = re.compile(r"^\s*['\"`]")


def _lines(text: str) -> list[str]:
    r"""只按 `\n` 切行, 顺手去掉行尾 `\r`。

    ⛔ r15 MEDIUM-4: `str.splitlines()` 还把 VT(U+000B)/FF/NEL/LS/PS 当换行, 而 shell
    不把它们当行分隔 —— `P="/tmp/cls-exam/"<VT>P="/etc/passwd"` 在 shell 里是**一个**
    赋值(路径合规), 换成 LF 才变成两个(最终值 `/etc/passwd`), 而 `splitlines()` 对两者
    给出完全相同的分块与指纹。
    """
    return [ln.rstrip("\r") for ln in text.split("\n")]


def _fence_blocks(text: str) -> list[tuple[int, list[str], bool]]:
    """把正文切成 `(起始行号, 行列表, is_fence)`。

    fence 标记支持 ``` 与 ~~~, 且**闭合必须同字符、长度 >= 开启**(r5 HIGH-4:
    四反引号块里的三反引号内容行不该切换状态)。标记行本身不进 body。

    ⚠️ r6 HIGH-4: 开启标记**同一行**若还有同字符、长度 >= 开启的 run, 它其实是
    **行内 code span**(``` `​``/tmp/cls-exam/../x`​`` ``` 之流), 不是 fence ——
    按 fence 处理会把整行连同路径一起删掉。CommonMark 亦规定反引号 fence 的
    info string 不得含反引号, 故此判定与规范同向。这类行退回散文, 由 ④ backtick
    span 与 ③ 裸 token 接管。
    """
    lines = _lines(text)
    out: list[tuple[int, list[str], bool]] = []
    i, n = 0, len(lines)
    while i < n:
        m = _FENCE_OPEN_RE.match(lines[i])
        if m and not _is_inline_span(m, lines[i]):
            mark = m.group(1)
            ch, width = mark[0], len(mark)
            # ⚠️ 标记行本身按**散文**产出而不是丢弃: ``` P = "/tmp/cls-exam/../x" 这类
            # 把路径写在 info string 位置的行, 丢掉标记行就等于让它对全部集合判据隐形。
            out.append((i + 1, [lines[i]], False))
            # r8 HIGH-3b: 引用块内的 fence —— body 每行带 `> ` 前缀, 不剥掉则 ast/shlex
            # 全都解析不了, 整块退化成只有裸 token。按开启行的引用深度剥。
            # 容器前缀的长度(>0 即「开启行在引用/列表里」); 闭合行的引用深度须与之相同。
            # ⛔ r12 MEDIUM-1: 基准取**fence marker 的列位置**而不是行首缩进 ——
            # `10. ```python` 的 marker 在第 4 列, closing 缩进 4; 用行首缩进(0)作基准
            # 会让它闭不上、把后面的正文吞进块(新增误报, 本轮自己引入的)。
            # ⛔ r13 HIGH-4: CommonMark 说 closing 缩进最多 **3 空格**(绝对), 而列表/引用
            # 内的 fence 只是整体右移了容器 marker 的宽度。所以阈值 = 3 + **marker 宽度**,
            # 不是 3 + 「fence 标记的列位置」—— 后者会把 opening 自身的缩进也当成额度,
            # 于是 3 空格 opening 配 4 空格 closing 被错判为闭合(r13 实测)。
            # ⛔ CommonMark 的额度算法(r13→r15 三轮才算对, 每轮都栽在同一处):
            #   closing 缩进 ≤ **容器内容基线** + 3。
            #   · 无容器时基线 = **0** —— opening 自己的缩进(≤3 也是合法的)**不给额度**,
            #     所以 `   ```py` 配 4 空格 closing 不闭合(r15 HIGH-1);
            #   · 有容器时基线 = 容器前缀的列宽 —— `   - ```py` 的基线是 5,
            #     配 6 空格 closing 要闭合(r14 MEDIUM-2)。
            #   两者都按 **tab 展开后的列数**算, 且要数**整个前缀**(含 `>`/`- `),
            #   只数 `>` 之前的缩进会让 `> \t\t```` 提前闭合(r15 HIGH-1 同根)。
            _open_m = _FENCE_OPEN_RE.match(lines[i])
            _prefix_raw = lines[i][: _open_m.start(1)]
            _has_container = bool(_prefix_raw.strip())
            open_indent = len(_prefix_raw.expandtabs(4)) if _has_container else 0
            _prefix = lines[i][: _FENCE_OPEN_RE.match(lines[i]).start(1)]
            quote_depth = len(_prefix.strip()) and _prefix.count(">")
            container_depth = 1 if _prefix.strip() else 0
            body: list[str] = []
            start = i + 2  # body 的首个物理行号
            closing: tuple[int, list[str], bool] | None = None
            i += 1
            while i < n:
                m2 = _FENCE_CLOSE_RE.match(lines[i])
                # ⚠️ r7 HIGH-2: CommonMark 规定**闭合** fence 行不得带 info string ——
                # ` ```not-a-close ` 不闭合任何东西, 原先却按闭合处理, 于是后面真正的
                # 代码块被当成散文。
                if (
                    m2
                    and m2.group(1)[0] == ch
                    and len(m2.group(1)) >= width
                    # r16 HIGH-1: 尾部只接受空格/tab —— `.strip()` 会放过 NBSP/VT/FF
                    and not lines[i][m2.end() :].strip(" \t")
                    # r9 HIGH-3a: closing 的引用深度必须**等于** opening 的
                    and lines[i][: m2.start(1)].count(">") == quote_depth
                    # r11 HIGH-5b: closing 缩进最多比 **opening** 多 3 空格(CommonMark)
                    and _indent_cols(lines[i]) <= open_indent + 3  # r14: 按展开后的列数比
                ):
                    closing = (i + 1, [lines[i]], False)
                    i += 1
                    break
                body.append(_strip_quote_prefix(lines[i], container_depth))
                i += 1
            out.append((start, body, True))
            if closing is not None:
                out.append(closing)
        else:
            out.append((i + 1, [lines[i]], False))
            i += 1
    return out


def _quiet_parse(src: str) -> ast.AST | None:
    """`ast.parse` 被测**语料**; 失败返 None, 并吞掉语料自身的 `SyntaxWarning`。

    判据解析的是别人写的任意文本 —— 语料里的 `"\\/"` 之类非法转义会让 CPython 冲
    测试输出打 warning。那是**被测对象的性质**(且正是第八条判据要登记的东西),
    不是本模块的缺陷, 不该污染裁判输出。
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            return ast.parse(src)
    except (SyntaxError, ValueError):  # ValueError: 源码含 NUL 等
        return None


#: span 两侧的「正常 markdown 分隔符」: 空白 + 中英文标点 + 强调号。
#: ⛔ 刻意**不含引号**(`"` `'`) —— 引号在 shell 里是词的一部分, 而
#: `P="/tmp/cls-exam/"`printf .`"./x"` 的 span 恰恰被引号夹住, 那正是要抓的特征。
#: ⛔ r9 HIGH-5a: **不含任何 ASCII 标点**。`_` `:` `,` 同样是合法 shell 词的一部分,
#: 留在表里就等于放行 ``cp "/tmp/cls-exam/"_`printf a`_ out`` 这种形态。
#: ⛔ r9 LOW-2: 补齐中文引号与括号(“”‘’『』〔〕), 它们在中文技术文档里包 span 很常见。
#: ⛔ r10 HIGH-5: 连 `*` 与中文引号也去掉 —— 它们同样能属于合法 shell 词
#: (`P="/tmp/cls-exam/"*`printf a`*` / 用 `“”` 包裹同理)。**只留空白与中文句读**:
#: 表里多一个字符就是多一条放行, 而遗漏只会造成误报(方向安全)。
#: ⛔ r11 HIGH-6: 连中文句读也去掉 —— `，`、`。`、NBSP、全角空格同样能属于合法
#: shell 词(`P="/tmp/cls-exam/"，`printf a`，`)。**只认真正的空白**(含 Unicode 空白),
#: 判据用 `str.isspace()`; 表留空是刻意的: 表里多一个字符就是多一条放行。
_SPAN_SEP_CHARS: frozenset[str] = frozenset()


def _is_span_sep(ch: str) -> bool:
    r"""这个字符能算 span 两侧的「安全分隔符」吗?

    ⛔ r12 HIGH-2: **只认 ASCII 空白**。`str.isspace()` 对 NBSP(U+00A0) 与全角空格
    (U+3000) 也返回 True, 但 shell 把它们留在**词内** ——
    `P="/var/cache""/tmp/cls-exam/"<NBSP>`printf a`<NBSP>` 的实际路径以 `/var/cache` 开头。
    """
    return ch in " \t" or ch in _SPAN_SEP_CHARS


#: 按 **ASCII 空白**切词, 但**不切引号内的空白** —— `line.split(" ")` 会把
#: `P="/var/cache /tmp/cls-exam/ "` 错拆成三段, 于是含 `/tmp` 的那段丢了上下文(r12 HIGH-2)。
_SHELL_WORD_RE = re.compile(r"""(?:[^\s"']|"[^"]*"|'[^']*')+""")


def _shell_words(line: str) -> list[str]:
    """把一行按 shell 的词边界切开(引号内的空白不算边界)。"""
    return _SHELL_WORD_RE.findall(line)


def _has_embedded_span_near_tmp(line: str) -> bool:
    r"""行内有没有「紧贴非空白的 code span」且它与某个含 `/tmp` 的词相交?

    markdown 正常写法里 span 两侧是空白或标点(`⛔ 不落 `/tmp` 等 vault 外临时文件`);
    shell 命令替换则**嵌在词中间**(`P="/tmp/cls-exam/"`printf .`"./x"`)。后者才需要登记。
    """
    masked = _MD_ESCAPE_RE.sub("\x00\x00", line)
    embedded: list[tuple[int, int]] = []
    for m in _BACKTICK_SPAN_RE.finditer(masked):
        before = line[m.start() - 1] if m.start() > 0 else " "
        after = line[m.end()] if m.end() < len(line) else " "
        if not _is_span_sep(before) or not _is_span_sep(after):
            embedded.append((m.start(), m.end()))
    if not embedded:
        return False
    # ⛔ r13 HIGH-3: 用 `finditer` 拿**真实坐标** —— `pos += len(word) + 1` 假设词间恰好
    # 一个空格, 40 个空格时坐标就飘了, 嵌入式 span 与含 `/tmp` 的词算不出相交 ⇒ 漏检。
    for match in _SHELL_WORD_RE.finditer(line):
        word = match.group(0)
        span = (match.start(), match.end())
        if "/tmp" not in word:
            continue
        if any(s0 < span[1] and span[0] < e0 for s0, e0 in embedded):
            return True
    return False


#: bytes 字面量(含 `rb` / `bR` 等前缀) —— 预筛不能因为它不进 `_py_strings()` 就放行。
_BYTES_LITERAL_RE = re.compile(r"\b[rRbB]{1,2}['\"]")
#: ATX 标题(自成一块, 前后都是边界)。
_ATX_HEADING_RE = re.compile(r"^ {0,3}#{1,6}(\s|$)")
#: markdown 块边界(除空行外): ATX 标题、thematic break、setext 下划线。
#: ⛔ r12 HIGH-3: **列表项**同样是块边界 —— 相邻两个列表项各有独立的 code span,
#: 拼起来会让前一项的未闭合反引号夺走后一项的合法 opening。
_BLOCK_BREAK_RE = re.compile(
    r"^ {0,3}(#{1,6}(\s|$)|(\*\s*){3,}$|(-\s*){3,}$|(_\s*){3,}$|=+\s*$"
    # ⛔ r16 HIGH-2: 有序列表**只有 `1.`/`1)` 能打断段落**(CommonMark) —— 把 `2. `
    # 一律当新块会切断合法的跨行 code span。
    r"|[-*+][ \t]+|1[.)][ \t]+|<!--)"
)
#: 列表项 marker(供 `_strip_quote_prefix` 迭代剥用)。
_LIST_MARKER_RE = re.compile(r"[-*+][ \t]+|\d+[.)][ \t]+")
#: 容器前缀(引用 / 列表, 任意嵌套顺序) —— 只用于 `_FENCE_OPEN_RE` 的深度判定。
#: ⛔ r10 HIGH-2: `>` 后**只吃一个空格** —— CommonMark 规定 block quote marker 后至多
#: 一个空格属于标记, 再多就是内容缩进。原先写 `>\s*` 会把 Python 的真实缩进一并删掉,
#: `>     pass` 变成 `pass`, 函数体没了、整段解析失败(漏检方向)。
_CONTAINER_PREFIX_RE = re.compile(r"^[ \t]*(?:(?:> ?)+|(?:[-*+][ \t]+|\d+[.)][ \t]+))*")


def _prose_segments(text: str) -> list[tuple[int, list[str]]]:
    r"""把**连续的散文行**并成段, 返回 `[(段首物理行号, 行列表)]`。

    ⛔ r9 HIGH-5c: `_fence_blocks()` 对散文是**逐行**产出的(每块 body 只有一行),
    于是跨物理行的 code span(CommonMark 把换行当空格)两行都拿不到完整 span。
    要按 CommonMark 语义找 span, 就得先把散文拼回段。fence 是天然的段边界。
    """
    out: list[tuple[int, list[str]]] = []
    cur_start: int | None = None
    cur: list[str] = []

    def flush() -> None:
        nonlocal cur_start, cur
        if cur and cur_start is not None:
            out.append((cur_start, cur))
        cur_start, cur = None, []

    for start, body, is_fence in _fence_blocks(text):
        # ⛔ fence **标记行**虽按散文产出(为了让裸 token 扫到 info string 上的路径),
        # 但它不是散文正文 —— 并进段会让相邻两个 ``` 凑成一个假的跨行 span(树上实测
        # 误报 board-recap `:135` / quiz-answer `:165`)。它同时也是段边界。
        marker = _FENCE_OPEN_RE.match(body[0]) if len(body) == 1 else None
        if is_fence or (marker is not None and not _is_inline_span(marker, body[0])):
            flush()  # fence 与其标记行都是段边界(标记行只为裸 token 而按散文产出)
            continue
        for line in body:
            # ⛔ r10 HIGH-4: **空行是 markdown 块边界**。不断段的话, 前一段里一个
            # 未闭合的反引号会夺走后一段的合法 opening(实测整段 span 消失), 反方向
            # 还会跨空行拼出不存在的 span(误报)。
            # ⛔ r11 HIGH-4: 空行之外, ATX 标题(`# …`)与 setext 下划线同样是块边界。
            # ⛔ r16 HIGH-2: 空行判定只认空格/tab —— NBSP-only 行在 CommonMark 里**不是**
            # 空行, 当成空行会拆断合法 span 并放过后段改动。
            if not line.strip(" \t"):
                flush()
                continue
            if _BLOCK_BREAK_RE.match(line):
                # ⛔ 块边界行**本身是新块的第一行** —— flush 之后要留下它, 不能 continue
                # 掉(r12 整改时踩到: 列表项的第一行被丢掉, 那一项的 span 就提不出来了)。
                flush()
                if _ATX_HEADING_RE.match(line):
                    # ⛔ r15 HIGH-2: ATX 标题**自成一块** —— 它前后都是边界。只在标题前
                    # 断段的话, 标题里一个未闭合的反引号会夺走后面正文的 span opening。
                    cur_start, cur = start + body.index(line), [line]
                    flush()
                    continue
            if cur_start is None:
                cur_start = start + body.index(line)
            cur.append(line)
    flush()
    return out


def _indent_cols(line: str) -> int:
    r"""这一行 fence 标记**之前**的全部内容的列数(tab 展开为 4)。

    ⛔ r16 HIGH-1: 原先只数**首个 `>` 之前**的缩进, 于是 `> \t\t~~~` 算成 0 列、
    错误闭合了引用块内的围栏。CommonMark 按列算, 而且引用标记**之后**的缩进同样算数。
    """
    m = _FENCE_CLOSE_RE.match(line)
    prefix = line[: m.start(1)] if m else line[: len(line) - len(line.lstrip(" \t"))]
    return len(prefix.expandtabs(4))


def _strip_quote_prefix(line: str, depth: int) -> str:
    r"""剥掉 fence body 行的**容器前缀**。`depth=0`(开启行无容器前缀)时原样返回。

    ⛔ r9 HIGH-3b: 只剥 `>` 不够 —— `- > ```python` 的 body 是 `- > P = …`,
    留着 `- ` 一样解析不了。按 `_FENCE_OPEN_RE` 的同一套前缀模式整体剥。
    ⛔ 只在开启行**确实带容器前缀**时才剥, 否则普通 fence 里的 `- foo` 会被误剥。
    """
    if depth <= 0:
        return line
    # ⛔ r11 HIGH-2: 正则一次性剥不了 `>  > `(marker 之间可以有额外空白, CommonMark
    # 允许 ≤3 空格的内容缩进)。改**迭代**剥: 每轮先 lstrip 探一下, 是 `>` 就剥一个
    # 并只吃**一个**空格(marker 后至多一个空格属于标记), 是列表 marker 就剥掉;
    # 都不是就返回**上一轮的结果** —— 这样代码缩进不会被 lstrip 顺手吃掉。
    out = line
    while True:
        probe = out.lstrip(" \t")
        if probe.startswith(">"):
            out = probe[1:]
            if out.startswith(" "):
                out = out[1:]
            continue
        mark = _LIST_MARKER_RE.match(probe)
        if mark:
            out = probe[mark.end() :]
            continue
        return out


def _is_inline_span(m: re.Match[str], line: str) -> bool:
    r"""这个 fence 标记其实是**行内 code span** 而不是围栏开启？

    ``` ```/tmp/cls-exam/../x``` ``` 整行是一个 code span; 按围栏处理会把整行连同
    路径一起删掉(r6 HIGH-4)。判据 = 同一行里标记之后还有同字符、长度 >= 开启的 run。

    ⛔ r7 HIGH-2: **只对反引号成立**。CommonMark 只禁止反引号 fence 的 info string
    含反引号; 波浪线 fence 的 info string 允许含 `~`, 于是合法的 ` ~~~python title=~~~ `
    被这条判成行内 span、整块代码落回散文 —— 那是误伤, 方向是漏检。
    """
    mark = m.group(1)
    if mark[0] != "`":
        return False
    # ⛔ r11 HIGH-5a: CommonMark 规定反引号 fence 的 info string **不得含任何反引号**
    # —— 原先只拒绝长度 >= opening 的 run, 于是 ``` ``` text `label` ``` 被当成 fence 开启,
    # 后面的真代码块跟着错位(漏检方向)。任何反引号都说明这不是 fence 开启行。
    return "`" in line[m.end() :]


def _fold_str(node: ast.AST) -> str | None:
    """`Constant` 或 `BinOp(+)` 常量链 → 字符串; 不可折返回 None。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _fold_str(node.left), _fold_str(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _py_strings(src: str) -> list[str] | None:
    """`ast` 解析出的全部字符串值(含折叠的 `+` 链); 解析失败返回 None。

    折进 `+` 链的 `Constant` 不再单独计一次 —— 否则同一处会产生两个候选。
    """
    tree = _quiet_parse(src)
    if tree is None:
        return None
    out: list[str] = []
    folded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            value = _fold_str(node)
            if value is not None:
                out.append(value)
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                        folded.add(id(sub))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in folded:
            out.append(node.value)
    return out


#: 复合语句的**续接子句**: 单元不能切在它们前面, 否则孤立的 `elif` 头再也解析不了。
#: ⛔ r9 HIGH-1a: `if False:`␊`    pass`␊`elif (P := "/tmp/…" + "." * 2 + "/x"):` ——
#: 贪心「第一次成功即认」会把 `if False: pass` 认走, 剩下的 `elif` 头转交 shlex, 拼接丢失。
#: ⛔ r14 LOW-5: `case` 是**软关键字** —— `case = 0` 是普通赋值。要求它后面跟模式且
#: 行尾是冒号, 否则 200 行独立的 `case = 0` 会被合成一个单元(实测 0.072s vs 0.0016s)。
#: ⛔ r15 HIGH-3: 续接子句**必须带冒号**。合法的 shell heredoc 结束标记可以恰好叫
#: `else`/`elif`/`except`/`finally`(`python3 - <<'else'` … `else`), 不带冒号时它是
#: 结束标记而不是 Python 续接; 误当续接会让已经解析成功的整段被丢弃、降级到 shlex。
#: `else` / `try` / `finally` 自己就是完整子句 ⇒ **必须**紧跟冒号, 否则它是 heredoc
#: 结束标记(`python3 - <<'else'` … `else`, r15 HIGH-3)。
#: `elif` / `except` / `case` 后面**必带内容** ⇒ 只要求「后面还有非空白」——
#: 冒号可能在续行上(`elif ("/tmp/…" +`␊`    "a" + "/x") == q:`), 强求同行冒号会把
#: 多行子句头切断。单独一个 `elif`/`except` 仍判为结束标记。
#: ⛔ 已知保守面: `case = 0`(软关键字当变量名)会被判为续接 —— 误报方向, 树上无此写法。
#: 「看起来像续接子句」的**触发器** —— 它不再需要判准, 因为歧义由 `_parse_units`
#: 的**并集**处理(短单元与长单元的候选都收)。宁可宽, 不可窄。
_PY_CONTINUATION_RE = re.compile(r"^\s*(?:elif|else|except|finally|case)\b")


def _py_needs_more(src: str) -> bool:
    r"""这段 Python 是「还没写完」(再给几行就能解析)还是「根本不是 Python」?

    ⛔ r8 HIGH-1: 上一版用**纯文本**数括号深度与引号奇偶来定单元边界, 而那判不了
    语言语义 —— `P = ( # )` 里注释中的 `)` 抵消真实开括号、字符串里的 `)` 同样、
    三引号起手再加一个引号(共四个双引号)会被奇偶判成已闭合。三处都让边界**定短**
    (漏检方向), 而
    上一版 docstring 却声称「只会定长(误报方向)」—— 那个声明是错的。

    `codeop.compile_command()` 是标准库为 REPL 写的**语句完整性**判据(真解析器):
    返回 code ⇒ 完整; 返回 None ⇒ 还没写完; 抛 `SyntaxError` ⇒ 根本不对。
    用它当累加的终止条件, 语义正确的同时也解决了性能: SKILL.md 的 fence 大多是
    bash, 每行都立刻判「语法错误」⇒ 不累加 ⇒ O(n), 不是 O(n²)。
    (`quiz-answer` 有个 2746 行的 fence 块, 穷举窗口时单次 35.9 秒。)
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            return codeop.compile_command(src, symbol="exec") is None
    except (SyntaxError, ValueError):
        return False


def _sh_needs_more(chunk: str) -> bool:
    """`shlex` 失败是因为**引号跨行没闭合**(再给几行就好)还是别的畸形?"""
    try:
        shlex.split(chunk, posix=True)
    except ValueError as exc:
        return "quotation" in str(exc).lower()
    return False


def _has_continuation_after(body: list[str], i: int, j: int, end: int) -> bool:
    r"""`body[i:j+1]` 之后**紧跟的那个非空行**, 是不是本语句的合法续接子句?

    ⛔ r9 HIGH-1a / r10 HIGH-3 / r11 HIGH-1 三轮才收敛到这个写法, 前两版都在**猜缩进**:
      · r9 只看紧邻下一行 ⇒ 分支里有多行时, 第一个 `pass` 后就切开了;
      · r10 改成「跳过缩进块再看同级行」⇒ 嵌套的 `elif` 缩进更深, 扫不到;
      · r11 改成「凡缩进 >= base 的续接子句都继续」⇒ **太宽**: `if dup is None:` 那段里
        每隔几行就有一个属于**内层已闭合**语句的 `else:`, 于是一路吞到 545 行
        (最长单元 278 → 545、整套测试 15s → 66s,
        `test_parse_unit_length_on_current_tree` 当场抓到)。

    现在不猜缩进, 交给解析器: 拿 chunk + 那一行 + 一个占位 `pass` 去 `ast.parse`,
    **能解析就是合法续接**。缩进关系由 Python 自己判, 不由我复现。
    """
    base = len(body[i]) - len(body[i].lstrip())
    for k in range(j + 1, end + 1):
        line = body[k]
        if not line.strip():
            continue  # 空行不结束复合语句
        if line.lstrip().startswith("#"):
            continue  # r12 HIGH-1: 同级注释同样不结束复合语句
        if len(line) - len(line.lstrip()) > base:
            return True  # 仍在本语句的体内(`if x:` + 两个 `pass`)
        # ⛔ r12 HIGH-1: r11 版在这里放了个「chunk + 该行 + 占位 pass」的探针, 它拒绝
        # **多行**的 `elif` 头(`elif (P := "…" +`␊`    "." * 2 + "/x"):`)和单行 suite
        # (`elif …: pass` 再补缩进 pass 就是非法缩进) ⇒ 红转漏。探针是多余的:
        # 直接继续累加即可, `_py_strings` 自己会在整条复合语句完整时成功,
        # `_py_needs_more` 会在「根本不是 Python」时叫停。
        return _PY_CONTINUATION_RE.match(line) is not None
    return False


def _parse_units(body: list[str]) -> list[tuple[int, str, list[str] | None]]:
    """`_parse_units_uncached` 的带缓存包装 —— 同一段 body 会被多条判据反复解析。"""
    cached = _parse_units_cached("\n".join(body))
    return [(off, chunk, list(vals) if vals is not None else None) for off, chunk, vals in cached]


@functools.lru_cache(maxsize=512)
def _parse_units_cached(block: str) -> tuple[tuple[int, str, tuple[str, ...] | None], ...]:
    return tuple(
        (off, chunk, tuple(vals) if vals is not None else None)
        for off, chunk, vals in _parse_units_uncached(block.split("\n"))
    )


def _parse_units_uncached(body: list[str]) -> list[tuple[int, str, list[str] | None]]:
    r"""fence 体 → `[(块内偏移, 源码块, 解析出的字符串或 None)]` —— 按语法单元切。

    ⛔ **歧义点取并集**(r16 HIGH-3, 同一处被推翻三次之后的结论):
    在一段混合 shell + python 的文本里, 一行 `else:` 到底是 **Python 续接子句** 还是
    **恰好长这样的 heredoc 终止符**(`python3 - <<'else:'` … `else:`), **静态区分不了**。
    r13→r15 我三次改规则去猜:
      · 「后面有非空白就算续接」⇒ heredoc 的 `else` 被当续接, 已解析的整段被丢弃;
      · 「一律要求带冒号」⇒ 多行 `elif` 头被切断;
      · 「else 要冒号、elif 要有内容」⇒ `else:` 形态的 heredoc 终止符又被当续接,
        而合法的 `else \`␊`:` 显式续行反被拒(Codex 给了双向反例)。
    猜不出来就**不猜**: 歧义点上把**短单元**(在此切断)与**长单元**(继续累加)的候选
    **都收进来**。代价是候选变多(误报方向、且都要人登记), 收益是这一类不再漏。
    """
    out: list[tuple[int, str, list[str] | None]] = []
    i, n = 0, len(body)
    while i < n:
        end = n - 1
        unit: tuple[int, str, list[str] | None] | None = None
        for j in range(i, end + 1):
            chunk = textwrap.dedent("\n".join(body[i : j + 1]))
            values = _py_strings(chunk)
            if values is not None:
                unit = (i, "\n".join(body[i : j + 1]), values)
                # ⛔ 歧义: 后面若还跟着**看起来像**续接子句的行, 长单元也要试 ——
                # 两种解释都可能, 两种的候选都收(见 docstring)。
                base = len(body[i]) - len(body[i].lstrip())
                for k in range(j + 1, min(end, j + 40) + 1):
                    nxt = body[k]
                    if not nxt.strip() or nxt.lstrip().startswith("#"):
                        continue  # 空行/注释不结束复合语句
                    if not _PY_CONTINUATION_RE.match(nxt):
                        if len(nxt) - len(nxt.lstrip()) > base:
                            continue  # 仍在本语句体内(`if x:` + 多个 `pass`), 继续往后找
                        break  # 同级且非续接 ⇒ 本语句真的结束了
                    # 续接子句头本身可以跨行(`elif (…` + 续行), 所以从这里**继续累加**
                    # 直到解析成功, 而不是只试它那一行。
                    for kk in range(k, min(end, k + 40) + 1):
                        merged = textwrap.dedent("\n".join(body[i : kk + 1]))
                        longer = _py_strings(merged)
                        if longer is not None:
                            out.append((i, "\n".join(body[i : kk + 1]), longer))
                            # ⛔ 收了长单元就**跳到它之后** —— 否则被它覆盖的那几行会再被
                            # 当成独立单元走 shell 分词, `elif ("/tmp/cls-exam/" +` 会被
                            # `shlex` 切出 `(/tmp/cls-exam/` 这种带括号的假候选(实测:
                            # 四个安全对照因此全被越界判据误报)。
                            j = kk
                            break
                        if not _py_needs_more(merged):
                            break
                    break
                i = j + 1
                break
            if not _py_needs_more(chunk):
                break
        if unit is None:
            for j in range(i, end + 1):
                chunk = "\n".join(body[i : j + 1])
                words = _sh_words(chunk)
                if words is not None:
                    unit = (i, chunk, words)
                    i = j + 1
                    break
                if not _sh_needs_more(chunk):
                    break
        if unit is None:
            unit = (i, body[i], None)
            i += 1
        out.append(unit)
    return out


def _sh_words(line: str) -> list[str] | None:
    """`shlex` 按 POSIX 语义切出的词; 引号不闭合等畸形输入返回 None。"""
    try:
        return shlex.split(line, posix=True)
    except ValueError:
        return None


def escaping_tmp_paths(text: str) -> list[tuple[str, str]]:
    """返回 `(候选, normpath 结果)`, 只含**含 `/tmp` 且 normpath 后不在命名空间内**的。

    候选来源见上方 v3 注释 ①~④。**多重集语义 —— 不去重**。
    命名空间内 = 规范化后等于 `/tmp/cls-exam` 或以 `/tmp/cls-exam/` 开头。

    ⛔ r5 MEDIUM / r7 MEDIUM: 早先按 `(候选, normpath)` **去重**, 于是每个已登记的
    越界项都成了**可复用盲槽** —— 正文里已有一处 `/tmp` 声明, 再往 fence 里写
    `P = "/tmp"` 就完全静默(计数只数带斜杠的 `/tmp/`, 候选又被去重掉);
    `A,A,B → A,B,B` 这种次数重分配同样不可见。改多重集后两者都红。
    (断言消息一直写的是「多重集」, 实现却在去重 —— 顺带修掉这处名实不符。)

    ⛔ r8 MEDIUM: normpath 前**带来源前缀**(`fence:` / `prose:`)。只钉裸 normpath 时,
    「把散文里的 `` `/tmp` `` 去掉反引号(候选 −1)」可以**抵消**「往 fence 里加一处
    `P = "/tmp"`(候选 +1)」—— 多重集总量不变, 门照绿。Counter 没算错, 错在两个来源
    共用一个额度。分开钉之后, 一增一减各自报红。(同「/tmp 与 8011 各钉两端」一个道理:
    钉两端自动钉住差, 反之不成立。)
    """
    ns = TMP_NAMESPACE.rstrip("/")
    out: list[tuple[str, str]] = []

    def add(cand: str, source: str) -> None:
        if not isinstance(cand, str) or "/tmp" not in cand:
            return
        norm = posixpath.normpath(cand)
        if norm != ns and not norm.startswith(ns + "/"):
            out.append((cand, f"{source}:{norm}"))

    for _start, body, is_fence in _fence_blocks(text):
        source = "fence" if is_fence else "prose"
        if is_fence:
            block = "\n".join(body)
            values = _py_strings(block)  # ① 整块 Python
            if values is None:
                values = _py_strings(textwrap.dedent(block))  # ①' 整块缩进
            if values is None:
                values = []
                for _off, chunk, parsed in _parse_units(body):  # ② 语法单元: Python → shell
                    values.extend(parsed if parsed is not None else (_sh_words(chunk) or []))
            for value in values:
                add(value, source)
        else:
            for content in _backtick_spans("\n".join(body)):  # ④ 散文 backtick span
                add(content, source)
        for line in body:  # ③ 裸 token 始终扫
            for tok in _TMP_TOKEN_RE.findall(line):
                add(tok, source)
    # ⑤ ⛔ r9 HIGH-5c: 跨物理行的 code span —— CommonMark 把 span 内的换行当空格,
    # 逐行扫时两行都拿不到完整 span。只补**跨行**的那些(单行的已由 ④ 覆盖)。
    for _seg_start, seg in _prose_segments(text):
        for content in _backtick_spans("\n".join(seg)):
            if "\n" in content:
                add(content, "prose")
    return out


def _logical_lines(text: str) -> list[tuple[int, str, bool]]:
    """物理行 → 逻辑行, 返回 `(起始行号, 合并后行, in_fence)`, 供可疑行判据用。

    **只在 fence 内合并**(r4 LOW-8: 散文行尾加个引号就足以搬动行号基线, 散文不该
    参与拼接语义): 反斜杠续行 + 「行尾引号 → 次行以引号开头」。合并次数有界(6)。

    ⚠️ 这条**只服务可疑行判据**(它要问「`/tmp` 与 `..`/`$` 是否同一逻辑行」)。
    越界判据不再依赖它 —— v3 走真解析, 拼接由 `ast` 处理。
    """
    flat: list[tuple[int, str, bool]] = []
    for start, body, is_fence in _fence_blocks(text):
        for offset, line in enumerate(body):
            flat.append((start + offset, line, is_fence))

    out: list[tuple[int, str, bool]] = []
    i = 0
    while i < len(flat):
        ln, line, fence = flat[i]
        i += 1
        if not fence:
            out.append((ln, line, fence))
            continue
        buf = line
        # ⛔ r15 MEDIUM-2: 去掉「最多 6 次」的上限 —— 七次反斜杠续行就静默了(实测)。
        # 与 `_parse_units` 同理: 固定上限只是把缺口挪个位置。
        while True:
            if i >= len(flat) or not flat[i][2]:
                break
            nxt = flat[i][1]
            if buf.rstrip().endswith("\\"):  # 反斜杠续行
                buf = buf.rstrip()[:-1] + nxt
                i += 1
            elif _QUOTE_TAIL_RE.search(buf) and _QUOTE_HEAD_RE.match(nxt):  # 行尾引号+次行引号
                buf = buf + nxt
                i += 1
            else:
                break
        out.append((ln, buf, fence))
    return out


#: 走到这些节点就说明「这个常量一路都是可折的」, 停止上溯。
#: ⛔ r7 HIGH-4: **`AugAssign` 不在名单里** —— `P += "/tmp/cls-exam/x"` 的 `+=`
#: 本身就是拼接, 抵达该语句节点**证明不了**「纯静态字面量」(`P` 之前是什么完全未知,
#: 实测 `P = "/var/cache"` 在前时真实值是 `/var/cache/tmp/cls-exam/x`)。
#: ⛔ r9 HIGH-4: **`Expr` 不在名单里** —— `"/tmp/cls-exam/x"; P = "/etc/passwd"` 里
#: 那个常量是个**无用表达式**, 实际赋值是别的; 抵达 `Expr` 证明不了它是这条语句的落点。
#: 树上实测 0 处受影响(fence 内没有含 `/tmp` 的孤立字符串表达式)。
_STATEMENT_NODES = (ast.Assign, ast.AnnAssign, ast.Return)
#: ⛔ r8 HIGH-4: `P: "/tmp/cls-exam/x" = "/etc/passwd"` —— 常量只是**注解**,
#: 实际值是别的。抵达 `AnnAssign` 不能一概判「纯静态字面量」, 要看常量落在
#: `.annotation` 还是 `.value` 上。


def _has_dynamic_tmp_join(src: str) -> bool:
    r"""该源码里是否存在「含 `/tmp` 的字符串常量**参与了静态折不出来的运算**」。

    口径(2026-09-09 由一次 50-agent 独立复核逼出的重写): 原先是**节点类型白名单**
    (`BinOp(+/%)` / `JoinedStr` / `Call`), 于是 `IfExp` / `Subscript` / `Tuple` /
    `List` / bytes 字面量整类漏掉 —— 而 `P = "/tmp/cls-exam/x" if 0 else "/etc/passwd"`
    的真实落点是 `/etc/passwd`, 计数还一动不动(左边那个字面量仍在, `tmp_all`/`tmp_ns`
    都不变), 越界判据又因 `"/tmp" not in "/etc/passwd"` 早退。

    现在改成**完备的取反口径**: 从每个含 `/tmp` 的常量向上走父链, 只要祖先还能被
    `_fold_str()` **完全折成一个字符串**就继续上走; 一路折到语句层 ⇒ 这是纯静态字面量
    (越界判据已能定论); 中途遇到折不出来的祖先 ⇒ 这个常量参与了动态运算, **要求登记**。

    这样不再依赖「我想得到哪些节点类型」: 任何新的表达式形态默认落进「折不出来」一侧。
    bytes 常量同样纳入(`b"/tmp/…".decode()` 原先被 `isinstance(..., str)` 整个丢掉)。
    """
    tree = next(
        (t for t in (_quiet_parse(c) for c in (src, src.strip(), textwrap.dedent(src))) if t is not None),
        None,
    )
    if tree is None:
        return False

    parent: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[id(child)] = node

    # ⛔ r11 HIGH-9: 同一单元内对同一名字**重复赋值** —— `P = "/tmp/cls-exam/x"; P = "/var/…"`
    # 的最终值是静态确定的, 而合规常量还在, 九项计数与全部集合都不变。
    # ⛔ r12 LOW-3: 只统计**目标名**的赋值次数不够精细 —— `N=1; N=2; P="/tmp/…"` 会误报。
    # 现在只在「同一个名字被赋值多次, 且**其中至少一次的值里含 `/tmp`**」时才登记。
    # ⛔ r12 HIGH-5: `AnnAssign`(`P: str = "/var/cache/x"`)同样是赋值, 一并计入。
    assigned: Counter[str] = Counter()
    tmp_targets: set[str] = set()
    for node in ast.walk(tree):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        for tgt in targets:
            if not isinstance(tgt, ast.Name):
                continue
            assigned[tgt.id] += 1
            value = node.value
            if value is not None and any(
                isinstance(n, ast.Constant)
                and isinstance(n.value, (str, bytes))
                and "/tmp" in (n.value if isinstance(n.value, str) else n.value.decode("utf-8", "replace"))
                for n in ast.walk(value)
            ):
                tmp_targets.add(tgt.id)
    if any(assigned[name] > 1 for name in tmp_targets):
        return True

    # ⛔ r11 HIGH-8: 起点不能只取**叶**常量 —— `("/t" + "mp/cls-exam/") + "." * 2 + "/x"`
    # 的两个叶都不含 `/tmp`, 但折叠后的子树含。凡 `_fold_str()` 折得出且含 `/tmp` 的
    # 节点都作为起点(叶常量是它的特例)。
    starts: list[ast.AST] = []
    for node in ast.walk(tree):
        folded = _fold_str(node)
        if folded is not None and "/tmp" in folded:
            starts.append(node)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, bytes)
            and "/tmp" in node.value.decode("utf-8", "replace")
        ):
            starts.append(node)
    for node in starts:
        cur: ast.AST = node
        while True:
            par = parent.get(id(cur))
            if isinstance(par, ast.AnnAssign) and cur is par.annotation:
                return True  # r8 HIGH-4: 注解里的常量不是这条语句的实际值
            if par is None or isinstance(par, _STATEMENT_NODES):
                break  # 一路可折到语句层 ⇒ 纯静态, 交给越界判据
            if _fold_str(par) is not None:
                cur = par  # 祖先仍完全可折, 继续上溯
                continue
            return True  # 折不出来 ⇒ 落点静态不可判
    return False


def dynamic_tmp_join_lines(text: str) -> list[tuple[int, str]]:
    """fence 内「含 `/tmp` 且存在动态拼接/格式化」的行 —— 返回 `(行号, 行)`。

    与 `suspicious_tmp_lines` 同属「静态不可判 ⇒ 要人登记」这一档, 但触发面互补:
    那条看的是行内有没有 `..` / `$` 的**字面证据**, 这条看的是 `ast` 层面有没有
    **动态参与** —— 变量拼接既没有 `..` 也没有 `$`, 只有这条看得见。
    """
    out: list[tuple[int, str]] = []
    for start, body, is_fence in _fence_blocks(text):
        if not is_fence:
            continue
        for offset, chunk, parsed in _parse_units(body):  # 按语法单元, 不按物理行
            # ⛔ r10 HIGH-6: 预筛不能只看**源码字面**含不含 `/tmp` ——
            # `P = "/t" "mp/cls-exam/" + "." * 2 + "/x"` 的源码里没有 `/tmp` 三个字符
            # 连在一起, 但 `ast` 折完隐式拼接后有。改用**解析出的字符串**做预筛,
            # 源码字面只作为兜底(解析失败时)。
            if not (
                (parsed and any("/tmp" in v for v in parsed))
                or "/tmp" in chunk
                # ⛔ r11 HIGH-7: bytes 字面量不进 `_py_strings()`(它只收 str), 于是
                # `P = b"/t" b"mp/cls-exam/" + b"." * 2 + b"/x"` 的 parsed 是 `[]`、
                # 源码里也没有 `/tmp` 三字连写 ⇒ 预筛整类挡掉。见 bytes 就不预筛。
                or _BYTES_LITERAL_RE.search(chunk)
            ):
                continue
            if _has_dynamic_tmp_join(chunk):
                out.append((start + offset, chunk.splitlines()[0].strip()))
    return out


#: fence 内使「这条路径的字面值」跨语言不可判的记号(r6 HIGH-1/2/3 的共同根因)。
#: · 反引号 —— fence 内已不可能是 markdown span, 只能是 shell 命令替换 `cmd`;
#: · 反斜杠 —— 转义序列的含义由**读它的那门语言**决定(JSON 的 `\/` 是 `/`,
#:   Python 的 `\/` 是两个字符), 且行尾反斜杠还是续行, 逐行降级会把它切断。
_OPAQUE_TMP_RE = re.compile(r"[`\\]")


def opaque_tmp_lines(text: str) -> list[tuple[int, str]]:
    r"""fence 内「含 `/tmp` 且带跨语言不可判记号」的行 —— 返回 `(行号, 行)`。

    r6 的 HIGH-1(shell 命令替换)、HIGH-2(JSON `\u002e\u002e\/`、shell 反斜杠
    续行)、HIGH-3(heredoc 内续行)是**同一根因**: v3 的真解析解决了「字面量怎么
    写」, 但一段文本到底按哪门语言解析、其中的反斜杠算不算转义, 静态判不了 ——
    `ast` 把 `"\u002e"` 读成 `.`(恰好对), 把 `"\/"` 读成 `\/`(错, JSON 里是 `/`)。

    处置与第六条 `dynamic_tmp_join_lines`、兜底的 `suspicious_tmp_lines` 完全同档:
    **不猜它指向哪, 只要求登记**。三条判据触发面互补 ——
      · 本条: 反引号 / 反斜杠(语言歧义);
      · 第六条: `ast` 层面的动态参与(变量、f-string、`.format`);
      · 兜底: 行内 `..` 或 `$` 的字面证据。

    fence **内**看整行(那里的反引号只能是命令替换); fence **外**只看 backtick span
    的**内容**(散文里反引号是 markdown 语法, 看整行会全树误报, 但 span 内部的反引号
    仍只可能是命令替换 —— r7 HIGH-1)。

    按**行尾反斜杠续行组**扫(链长上限 6): r6 的 shell `P='\\`␊`/tmp/…'` 把反斜杠
    留在上一行、`/tmp` 留在下一行, 物理行粒度两边都不触发。`_logical_lines` 合并时
    会**擦掉**反斜杠(那是它的活), 所以这里自己拼、原样保留。
    2026-09-09 开工实测: 9 份 SKILL.md + 7 份 scripts **全树命中 0**, 故基线全空 ——
    登记成本为零, 而任何新写的此类形态都必须先被人看见。
    """
    out: list[tuple[int, str]] = []
    # ⛔ r9 HIGH-5c: 跨物理行的 code span —— 先把连续散文并成段再找 span, 行号取段内偏移。
    # 逐行扫时两行都拿不到完整 span（CommonMark 把 span 内的换行当空格）。
    for seg_start, seg in _prose_segments(text):
        joined = "\n".join(seg)
        for content in _backtick_spans(joined):
            if "\n" in content and "/tmp" in content and _OPAQUE_TMP_RE.search(content):
                off = joined[: joined.find(content)].count("\n")
                entry = (seg_start + off, seg[off].strip())
                if entry not in out:
                    out.append(entry)
    for start, body, is_fence in _fence_blocks(text):
        if not is_fence:
            # ⛔ r7 HIGH-1: 散文侧只看 **backtick span 的内容** —— 整行不行(散文里反引号
            # 是 markdown 语法, 认了会全树误报), 但 span 内部的反引号只可能是 shell
            # 命令替换: ``cp "/tmp/cls-exam/"`printf .`"./x" out`` 是合法的双反引号
            # code span, 内部那对单反引号真跑起来会展开。全树实测命中 0。
            for offset, line in enumerate(body):
                if "/tmp" not in line:
                    continue
                # ⛔ r8 HIGH-5: 除了「span 内容里有记号」, 还要覆盖「散文里裸写的 shell」
                # —— `P="/tmp/cls-exam/"`printf .`"./x"` 唯一能提出来的 span 是
                # `printf .`(不含 /tmp), 按 span 逐个看就整类漏掉。
                # ⛔ 判据是「**嵌入式** span」而不是「行内有反引号」: markdown 正常用法
                # 里 span 两侧是空白(`⛔ 不落 `/tmp` 等…`), 而命令替换的反引号**紧贴**
                # 前后的非空白字符 —— 后者才可能是 shell。只问「行内有没有反引号」会把
                # board-recap `:58`/`:139`、quiz-answer `:98`/`:205` 全部误报(实测踩到)。
                # ⛔ r9 HIGH-5b: 散文里裸写、连反引号都没有的形态
                # (`P="/tmp/cls-exam/"\.\./x`) —— 含 `/tmp` 的**词里带反斜杠**即登记。
                if (
                    any("/tmp" in c and _OPAQUE_TMP_RE.search(c) for c in _backtick_spans(line))
                    or _has_embedded_span_near_tmp(line)
                    or any("/tmp" in w and "\\" in w for w in _shell_words(line))
                    # ⛔ r12 HIGH-6: 散文里裸写的**相邻引号拼接**
                    # (`P="/var/cache""/tmp/cls-exam/x"`) —— shell 会把它们拼成一个词,
                    # 而这行没有反引号/反斜杠/`..`/`$`, 五条判据全静默。
                    or any("/tmp" in w and w.count('"') + w.count("'") > 2 for w in _shell_words(line))
                ):
                    out.append((start + offset, line))  # r14 MEDIUM-1: 存**原文**, 指纹才有意义
            continue
        i = 0
        while i < len(body):
            j = i  # 行尾反斜杠续行链: 整组一起看
            # ⛔ r7 HIGH-6: 链长**不设小上限**。原先上限 6, 于是 7 条连接时前七行切成
            # 一组(不含 `/tmp`)、第八行单独成组(含 `/tmp` 但无记号)⇒ 漏; 实测边界呈
            # 模 7 锯齿(6 抓 / 7 漏 / 8 抓 / 14 漏)。切窗切断的正是「记号与 `/tmp`
            # 属于同一条逻辑行」这个关联, 而那关联就是本判据的全部内容。
            while j + 1 < len(body) and body[j].rstrip().endswith("\\"):
                j += 1
            joined = "\n".join(body[i : j + 1])  # ⛔ 原样拼, 不擦反斜杠(它正是证据)
            if "/tmp" in joined and _OPAQUE_TMP_RE.search(joined):
                out.append((start + i, body[i]))
            i = j + 1
    return out


def suspicious_tmp_lines(text: str) -> list[tuple[int, str]]:
    """**不依赖解析**的保守兜底: 同一**逻辑行**里 `/tmp` 与 `..` 或 `$` 同时出现。

    返回 `(1-based 起始行号, 该逻辑行 strip 后的内容)`。

    v3 之后越界判据已走真解析, 但**运行期展开仍然静态不可判**:
    `P="/tmp/cls-exam/$1"`(位置参数)、`P="/tmp/cls-exam/"$REL`(引号外拼接)——
    `ast`/`shlex` 都只能看到源码, 看不到 `$1` 的值。这条判据只问「这一行值不值得
    人看一眼」, 因此不受任何解析能力所限, 是最后一道。

    触发条件: `/tmp` 在行内 且 (`..` 在行内 或 `$` 在行内)。代价是含
    `${CLS_BACKEND_URL:-…}` 等无害展开的 `/tmp` 行也要登记(现状见基线注释)。
    """
    out: list[tuple[int, str]] = []
    for lineno, line, _fence in _logical_lines(text):
        if not _TMP_LINE_RE.search(line):
            continue
        if ".." in line or "$" in line:
            out.append((lineno, line.strip()))
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

# ── 越界路径基线 (v2 引号感知, 2026-09-08 实测; 按 skill 钉 normpath **集合**) ──
#: ⛔ **多重集语义(不去重)** —— r7 起。去重会把每个已登记项变成可复用盲槽
#: (见 `escaping_tmp_paths` docstring)。次数变化同样要红。
#: 现状全部是「只钉不改」的已知项:
#:   · quiz-answer 两形态各 4 次(散文 backtick + fence 字面量, 多处重复; E-2 归 U5-B);
#:   · start-exam-board `:430/:435` 的 exam-created-event(被 tests/regression 钉死)、
#:     `:128` 散文 backtick 的裸 `/tmp` 提法、`:188` 变更行 backtick 整段命令
#:     `Bash: mkdir -p /tmp/cls-exam`(含 /tmp 的非路径 span, 保守登记);
#:   · board-recap `:58` 散文 backtick 的裸 `/tmp` 提法("禁写 /tmp"声明)。
#: **新增任何越界候选 = 红**, 这正是子串计数看不见的那一面。
ESCAPING_TMP_BASELINE: dict[str, list[str]] = {
    "ai-linked-doc": [],
    "board-recap": ["prose:/tmp"],
    "chat-with-context": [],
    "configure-whiteboard": [],
    "exam-quick": [],
    "node-chat": [],
    # 两形态 × 散文/fence 两来源 × 各 2 次(E-2 归 U5-B)。
    "quiz-answer": [
        "fence:/tmp/quiz-answer-incr.json",
        "fence:/tmp/quiz-answer-incr.json",
        "fence:/tmp/quiz-answer-payload.json",
        "fence:/tmp/quiz-answer-payload.json",
        "prose:/tmp/quiz-answer-incr.json",
        "prose:/tmp/quiz-answer-incr.json",
        "prose:/tmp/quiz-answer-payload.json",
        "prose:/tmp/quiz-answer-payload.json",
    ],
    # `:430/:435` exam-created-event（被 tests/regression 逐字钉死，本卡只钉不改）;
    # `:128` 散文裸 `/tmp` 提法; `:188` 变更行 backtick 整段命令（含 /tmp 的非路径 span，保守登记）。
    "start-exam-board": [
        "fence:/tmp/exam-created-event.json",
        "fence:/tmp/exam-created-event.json",
        "prose:/tmp",
        "prose:/tmp/exam-created-event.json",
        "prose:/tmp/exam-created-event.json",
        "prose:Bash: mkdir -p /tmp/cls-exam",
    ],
    "study-question": [],
}


#: 「同时含 `/tmp` 与 `..`(或变量展开)」的行号 —— 保守判据的基线(2026-09-08 实测)。
#: 现状只有 quiz-answer `:98` 一行, 且它是**误报友好**的那类: 该行写的是
#: `按 Step 4a 格式拼 callout 列表`, `..` 来自省略号/中文标点而非路径穿越。
#: 保留它进基线而不是放宽判据 —— 放宽会把真的穿越一起放过去; 登记一行的成本远更低。
SUSPICIOUS_TMP_LINES_BASELINE: dict[str, list[int]] = {
    "ai-linked-doc": [],
    "board-recap": [],
    "chat-with-context": [],
    "configure-whiteboard": [],
    "exam-quick": [],
    "node-chat": [],
    # :98 的 `..` 来自散文省略号(误报友好项); r3 后 `$` 也触发, 但该行无 `$`。
    "quiz-answer": [98],
    # :577 = 本卡「变更记录」行, 含 `${CLS_BACKEND_URL:-…}` —— 无害展开, 照样登记
    # (r3 MEDIUM-3 起 `$` 任意位置触发; 保守面换零漏报)。
    "start-exam-board": [577],
    "study-question": [],
}

#: 「含 `/tmp` 且存在动态拼接/格式化」的行号 —— 第六条判据的基线(2026-09-09 实测)。
#: **全 9 份皆空 = 零余量**: 树上没有任何一处用变量拼临时路径, 新增一处即红。
#: 与 `SUSPICIOUS_TMP_LINES_BASELINE` 互补 —— 那条看行内有没有 `..`/`$` 的字面证据,
#: 这条看 `ast` 层面有没有动态参与(变量拼接两样都没有, 只有这条看得见)。
DYNAMIC_TMP_JOIN_BASELINE: dict[str, list[int]] = {
    "ai-linked-doc": [],
    "board-recap": [],
    "chat-with-context": [],
    "configure-whiteboard": [],
    "exam-quick": [],
    "node-chat": [],
    "quiz-answer": [],
    "start-exam-board": [],
    "study-question": [],
}

#: 散文里「`/tmp` + 父目录语义」的行号 —— 第七条判据基线(2026-09-09 实测全空)。
#: 层 2 附加⑤(r6 三类 HIGH 的同因收口): fence 内 `/tmp` 行带反引号/反斜杠的行号。
#: 全树实测 0 —— 空基线意味着**任何**此类新写法都要先登记, 代价为零。
OPAQUE_TMP_BASELINE: dict[str, list[str]] = {
    "ai-linked-doc": [],
    "board-recap": [],
    "chat-with-context": [],
    "configure-whiteboard": [],
    "exam-quick": [],
    "node-chat": [],
    # ⛔ 保守误报, 不是债: markdown 的 `**粗体**` 或中文标点紧贴 code span 边界, 被
    # 「嵌入式 span」判据当成了 shell 命令替换。`_SPAN_SEP_CHARS` 已清空(只认 ASCII
    # 空白)——因为任何标点都可能是合法 shell 词的一部分。方向取舍: 漏检不可接受,
    # 误报可以登记。⛔ 登记项带**内容指纹**(r11 HIGH-3), 16 位、不 strip(r14)。
    "quiz-answer": ["98:918de56473d5be1b", "205:44b7655dd97c27b7"],
    "start-exam-board": [
        "188:65b99234f2075b8f",
        "430:6df0e9ca43fe93e0",
        "577:249fe6bc3d886700",
    ],
    "study-question": [],
}

#: 层 2 附加⑥(r9 MEDIUM-2): fence 内给 `CLS_BACKEND_URL` 赋值的行号。全树实测 0。
#: 层 2 附加⑦(第十条判据 = 兜底网): 含 `/tmp` 的 fence 块整块指纹 / 散文行指纹。
#: ⛔ **这条不做语义分析** —— 见 `tmp_block_fingerprints` 的 docstring: 立它的理由是
#: 七轮 Codex 复核的数据(判据 ④~⑨ 每轮被找出 5~9 条 HIGH, 我自己整改引入的新回归
#: 占比 33%→83%)。它与那九条互补: 那九条说「是哪一类问题」, 这条保证「块变了就红」。
#: 代价: 块内**任何**改动(包括无关措辞)都要同步指纹 —— 这正是「增红减也红」的精神。
TMP_BLOCK_BASELINE: dict[str, list[str]] = {
    "ai-linked-doc": [],
    "board-recap": ["S54:e4e9abc1df909943", "S139:0f6b5a2ff16914cd"],
    "chat-with-context": [],
    "configure-whiteboard": [],
    "exam-quick": [],
    "node-chat": [],
    "quiz-answer": [
        "B104:53c5e24e48a924de",
        "B229:1ece4b165eaff4e8",
        "S96:b55afbca27229028",
        "S205:44b7655dd97c27b7",
    ],
    "start-exam-board": [
        "B195:49bbb79cdd7750a1",
        "B433:abad24172c59e1c3",
        "S128:3d332975e351d095",
        "S188:35c02f61a9f9604b",
        "S430:6df0e9ca43fe93e0",
        "S577:249fe6bc3d886700",
    ],
    "study-question": [],
}

URL_OVERRIDE_BASELINE: dict[str, list[int]] = {
    "ai-linked-doc": [],
    "board-recap": [],
    "chat-with-context": [],
    "configure-whiteboard": [],
    "exam-quick": [],
    "node-chat": [],
    "quiz-answer": [],
    "start-exam-board": [],
    "study-question": [],
}

PARENT_DIR_PROSE_BASELINE: dict[str, list[int]] = {
    "ai-linked-doc": [],
    "board-recap": [],
    "chat-with-context": [],
    "configure-whiteboard": [],
    "exam-quick": [],
    "node-chat": [],
    "quiz-answer": [],
    "start-exam-board": [],
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
SCRIPT_METRICS = ("tmp", "p8011_all", "p8011_ns", "localhost", "users_path", "tree_name")

#: 非 U6 地盘的 5 份。路径相对 root(`canvas-vault/.claude`), posix 写法。
#: `scripts/fsrs_bridge.py` 的 `/Users/` 1 + 树名 1 是**零写者**的写死路径, 只钉不改
#: (本卡硬边界: 禁碰 `fsrs_bridge.py` / `decay_beta.py`)。
SCRIPTS_BASELINE: dict[str, dict[str, int]] = {
    "skills/board-recap/scripts/recap_scan.py": {
        "tmp": 1,
        "p8011_all": 0,
        "p8011_ns": 0,
        "localhost": 0,
        "users_path": 0,
        "tree_name": 0,
    },
    "skills/board-split/scripts/split_preview.py": {
        "tmp": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "localhost": 0,
        "users_path": 0,
        "tree_name": 0,
    },
    "scripts/decay_beta.py": {"tmp": 0, "p8011_all": 0, "p8011_ns": 0, "localhost": 0, "users_path": 0, "tree_name": 0},
    "scripts/fsrs_bridge.py": {
        "tmp": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "localhost": 0,
        "users_path": 1,
        "tree_name": 1,
    },
    "scripts/sync_board_concepts.py": {
        "tmp": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "localhost": 0,
        "users_path": 0,
        "tree_name": 0,
    },
}

# ── 交接常量 ② ─────────────────────────────────────────────────────────────
#: **U6-A / U6-B / U6-C (CARD-G6-9c / G6-7-R / G6-6) 改 `board-recap` 或 `clear-inbox`
#: 的 scripts、或在这两个 skill 下新增脚本, 必须同步更新此常量**(本层同时钉文件集合,
#: 新增脚本本身也会红)。
#:
#: U4-B 在合并队列**第 2 组**、U6 在**第 3 组** ⇒ U6 rebase 到含本卡的候选树后自查此常量。
#: 三项计数实测均 0 = **零余量**, 加任何一处 `/tmp` / `/Users/` / 树名即红。
U6_SCRIPTS_BASELINE: dict[str, dict[str, int]] = {
    "skills/board-recap/scripts/recap_exam_build.py": {
        "tmp": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "localhost": 0,
        "users_path": 0,
        "tree_name": 0,
    },
    "skills/clear-inbox/scripts/inbox_preview.py": {
        "tmp": 0,
        "p8011_all": 0,
        "p8011_ns": 0,
        "localhost": 0,
        "users_path": 0,
        "tree_name": 0,
    },
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
        # 放行端用带左边界的正则, 不是裸子串 —— 见 `_TMP_NS_RE` 上方注释。
        "tmp_ns": len(_TMP_NS_RE.findall(text)),
        "p8011_all": _count(text, "8011"),
        "p8011_ns": _count(text, URL_DEFAULT_FORM),
        "tree_name": _count(text, "feature-obsidian-hybrid-dev"),
        "users_path": _count(text, "/Users/"),
    }


def _script_counts(text: str) -> dict[str, int]:
    """一份 scripts/*.py 的 5 项指标实测值。

    ⛔ 层 3 的 `tmp` 口径是 `/tmp`(**无**尾斜杠) —— 脚本里 `/tmp` 常以
    `os.path.join("/tmp", x)` 或散文形态出现, 带尾斜杠会漏。

    ⛔ `p8011_all` / `p8011_ns` 是 2026-09-09 补的(一次 50-agent 独立复核指出):
    层 2 对 SKILL.md 把 8011 钉了 all/ns 两端, 层 3 原先**一个端口指标都没有** ——
    口径分叉, 于是「往受覆盖的 scripts 里搬一行 `BACKEND_URL = "http://…:8011/…"`」
    在层 3 三项计数上完全等值。7 份实测全 0, 补进来零维护成本。
    `localhost` 一并纳入: 端口换成别的数字(8012/8000)时 `p8011_*` 是瞎的。
    """
    return {
        "tmp": _count(text, "/tmp"),
        "p8011_all": _count(text, "8011"),
        "p8011_ns": _count(text, URL_DEFAULT_FORM),
        "localhost": _count(text, "localhost") + _count(text, "127.0.0.1"),
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
    """越界路径判据(v3 真解析): 每份 SKILL.md 的越界 normpath **多重集**精确相等。

    与 `check_body` 的子串计数**互补**: 计数管「命中数变没变」, 这里管「命中的那个
    路径规范化之后指向哪里」。`/tmp/cls-exam/../x` 在计数下裸值为 0(放行), 在这里
    normpath 成 `/tmp/x` ⇒ 越界 ⇒ 红。⛔ **多重集(不去重)** —— 去重会把每个已登记项
    变成可复用盲槽(r5/r7 MEDIUM), 次数重分配 `A,A,B → A,B,B` 也会隐形。
    ⛔ 钉的是 **normpath 那一端**, 不是候选原串 —— 基线值要按 normpath 填
    (`Bash: mkdir -p /tmp/cls-exam/` 的 normpath 无尾斜杠, 整改期间填错过一次)。
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
            # ⛔ 用 Counter 比**次数**, 不是 `in`(Codex round-2 LOW): 期望 [x,x] 实测 [x]
            # 时, `p not in actual` 恒假 ⇒ 消息显示「缺失=[]」, 明明少了一处却说不出少了什么。
            ca, cw = Counter(actual), Counter(want)
            extra = sorted((ca - cw).elements())
            missing = sorted((cw - ca).elements())
            problems.append(
                f"[越界] {name}: 越出 {TMP_NAMESPACE} 的路径多重集不等 "
                f"期望={want} 实测={actual} (新增={extra} 缺失={missing}) —— "
                f"⚠️ `fence:` / `prose:` 是**提取来源**: 同一处路径从 inline 挪进 fence 会让"
                f"一边缺失、另一边新增, 那是来源翻转**不是**物理债增减(r9 LOW-3); "
                f"新增即债; 缺失说明有人整改却没同步 ESCAPING_TMP_BASELINE"
            )
    return problems


def check_suspicious_tmp_lines(root: Path, baseline: dict[str, list[int]]) -> list[str]:
    """保守判据: 每份 SKILL.md 里「同时含 `/tmp` 与 `..`/变量展开」的**行号集合**钉死。

    不依赖 token 切分 ⇒ 切分正则怎么错都影响不到它(见 `_TMP_LINE_RE` 上方注释)。
    """
    problems: list[str] = []
    skills_dir = root / "skills"
    for name in sorted(baseline):
        f = skills_dir / name / "SKILL.md"
        if not f.exists():
            problems.append(f"[可疑行] {name}: SKILL.md 不存在 (基线要求存在) path={f}")
            continue
        found = suspicious_tmp_lines(f.read_text(encoding="utf-8"))
        actual = sorted(ln for ln, _txt in found)
        want = sorted(baseline[name])
        if actual != want:
            by_line = dict(found)
            ca, cw = Counter(actual), Counter(want)
            extra = sorted((ca - cw).elements())
            problems.append(
                f"[可疑行] {name}: `/tmp` 与 `..`(或变量展开) 同行的行号集合不等 "
                f"期望={want} 实测={actual} (新增={extra} 缺失={sorted((cw - ca).elements())})\n"
                + "".join(f"        :{ln}  {by_line.get(ln, '')[:100]}\n" for ln in extra)
                + "        —— 临时路径里的 `..` 与变量展开一律要人看一眼: 静态门证不出它们展开后落在哪"
            )
    return problems


def check_dynamic_tmp_joins(root: Path, baseline: dict[str, list[int]]) -> list[str]:
    """动态拼接判据: 每份 SKILL.md 里「含 `/tmp` 且动态拼接」的**行号集合**精确相等。

    现状全 0 —— 树上没有这种写法。**零余量**: 任何人往 fence 里写
    `"/tmp/…" + VAR` / `% var` / `.format()` / `os.path.join(...)` 都会立刻红,
    必须登记（因为静态证不出它最终指向哪里）。
    """
    problems: list[str] = []
    skills_dir = root / "skills"
    for name in sorted(baseline):
        f = skills_dir / name / "SKILL.md"
        if not f.exists():
            problems.append(f"[动态拼接] {name}: SKILL.md 不存在 (基线要求存在) path={f}")
            continue
        found = dynamic_tmp_join_lines(f.read_text(encoding="utf-8"))
        actual = sorted(ln for ln, _txt in found)
        want = sorted(baseline[name])
        if actual != want:
            by_line = dict(found)
            ca, cw = Counter(actual), Counter(want)
            extra = sorted((ca - cw).elements())
            problems.append(
                f"[动态拼接] {name}: 含 `/tmp` 的动态拼接行号集合不等 "
                f"期望={want} 实测={actual} (新增={extra} 缺失={sorted((cw - ca).elements())})\n"
                + "".join(f"        :{ln}  {by_line.get(ln, '')[:100]}\n" for ln in extra)
                + "        —— 变量拼接/格式化后的落点静态不可判(`ast` 折不了非常量), 必须登记"
            )
    return problems


#: 把 `${CLS_BACKEND_URL:-…}` 的缺省形态**架空**的写法: 同一 fence 块里给该变量赋空/别的值。
#: ⛔ r9 MEDIUM-2: `CLS_BACKEND_URL=; curl "${CLS_BACKEND_URL:-http://localhost:8011}/…"`
#: 九项计数与五个集合全部不变, 但外部配置被清空、命令无条件走 localhost:8011 ——
#: 「改成缺省形态」这项整改被就地取消, 而门看不见。这是可静态确定的等计数缺口。
#: ⛔ r10 MEDIUM: `unset` 同样确定性清空配置, 与赋值同根。
#: ⛔ r11/r12 MEDIUM: `unset -v` / `unset --` / `unset OTHER CLS_BACKEND_URL` 都确定性清空;
#: 但 `unset -f CLS_BACKEND_URL` 只删同名**函数**, 不动环境变量 ⇒ 排除, 否则是误报。
#: ⛔ 残余(登记不修): `unset C'LS'_BACKEND_URL` 这类**引号拼接出的变量名**正则认不出,
#: 与 §六 里「散文/shell 侧的字面量拼接」同一档。
#: 赋值形态。
_URL_ASSIGN_RE = re.compile(r"(?<![{$:])\bCLS_BACKEND_URL\s*=")
#: `unset` 形态: 选项**只看紧跟其后的那些**(`-v` / `--`), 变量列表止于命令分隔符。
#: ⛔ r13 MEDIUM-1: 原先写 `(?![^\n;]*\s-{1,2}f\b)` 会越过命令边界 ——
#: `unset CLS_BACKEND_URL && curl -f "…"` 里 curl 的 `-f` 被当成 `unset -f` ⇒ 漏检。
_URL_UNSET_RE = re.compile(r"\bunset\b(?P<opts>(?:\s+-{1,2}[a-zA-Z]*)*)(?P<vars>(?:\s+[\w'\"]+)*)")


def _url_override_hit(line: str) -> bool:
    r"""这一行有没有把 `${CLS_BACKEND_URL:-…}` 的缺省形态**架空**?

    两种形态: 直接赋值, 或 `unset` 掉它。
    ⛔ `unset -f X` 只删同名**函数**, 不动环境变量 ⇒ 不算(否则误报); 但选项只认
    **紧跟 `unset` 的那些**, 变量列表止于命令分隔符 —— 否则
    `unset CLS_BACKEND_URL && curl -f "…"` 里 curl 的 `-f` 会被当成 `unset -f`(r13 MEDIUM-1)。
    ⛔ 残余(登记不修): `unset C'LS'_BACKEND_URL` 这类**引号拼接出的变量名**认不出,
    与 §六 里「散文/shell 侧的字面量拼接」同一档。
    """
    if _URL_ASSIGN_RE.search(line):
        return True
    # ⛔ r13 MEDIUM-2: 写死端口而**没用约定变量**(`${OTHER:-http://localhost:8011}`)
    # 等于整改没做 —— 用户配了 `CLS_BACKEND_URL` 也不会生效。九项计数与全部集合不变。
    # ⛔ r14 MEDIUM-3: 用**词边界** —— `${CLS_BACKEND_URL_OTHER:-…}` 里虽然出现了
    # `CLS_BACKEND_URL` 这个子串, 但它不是约定变量, 用户配了也不生效。
    # ⛔ r15/r16 MEDIUM-1: 要绑「变量被展开**在写死端口的那个串里**」——
    # `curl "${OTHER:-…:8011}/x"; : "${CLS_BACKEND_URL}"` 里名字确实展开了, 但没用于
    # curl; 放进注释同理。所以只看**含 8011 的那一段**(按 shell 词切)里有没有它。
    for word in _shell_words(line):
        if "8011" in word and not re.search(r"\$\{CLS_BACKEND_URL\b", word):
            return True
    # ⛔ r16 MEDIUM-1: `env -u CLS_BACKEND_URL …` 会确定性删除传入配置, 与赋值/unset 同根。
    if re.search(r"\benv\b[^;&|\n]*\s-u[= ]\s*[\'\"]?CLS_BACKEND_URL\b", line):
        return True
    for segment in re.split(r"[;&|\n]+", line):
        m = _URL_UNSET_RE.search(segment)
        if not m:
            continue
        if "f" in (m.group("opts") or "").replace("-", ""):
            continue  # `unset -f` 只删函数
        if re.search(r"\bCLS_BACKEND_URL\b", m.group("vars") or ""):
            return True
    return False


def url_default_overridden_lines(text: str) -> list[tuple[int, str]]:
    """fence 内「给 `CLS_BACKEND_URL` 赋值」的行 —— 返回 `(行号, 行)`。全树实测 0。"""
    # ⛔ r14 MEDIUM-4: 走**逻辑行** —— `unset -v \`␊`CLS_BACKEND_URL; curl …` 是合法的
    # shell 续行, 逐物理行看的话 `unset -v` 与变量名分处两行, 两边都判不出来。
    out: list[tuple[int, str]] = []
    for lineno, line, in_fence in _logical_lines(text):
        if in_fence and _url_override_hit(line):
            out.append((lineno, line))
    return out


def tmp_block_fingerprints(text: str) -> list[str]:
    r"""含 `/tmp` 的每个 fence 块 → 整块指纹; 含 `/tmp` 的散文行 → 行指纹。

    ⛔ **第十条判据 = 兜底网, 不做任何语义分析**(2026-09-09, r13 后加)。

    立它的理由是七轮 Codex 复核的**数据**, 不是又一个想法: r7→r13 每轮都在
    「判断这条路径最终指向哪」这件事上被找出 5~9 条 HIGH, 其中我自己整改引入的
    新回归占比 33%→83%——判据 ④~⑨ 要做的事(把 markdown + shell + python 三层语义
    在手写代码里复现)本质上需要三个真解析器, 而每补一个边界就开一个新边界。

    这条判据反过来: **不问路径指向哪, 只问这块文本变没变**。
      · 没有解析、没有正则边界、没有缩进猜测 ⇒ 几乎没有回归空间;
      · 对形态表 51 个反例实测 **45 个可区分**(其余 6 个是 URL/`unset` 类,
        不含 `/tmp`, 归第九条判据);
      · 树上代价 12 项(逐块/逐行), 见 `TMP_BLOCK_BASELINE`。

    与 ④~⑨ 的关系是**互补而非取代**: 那九条告诉你「是哪一类问题」(报错信息里有
    形态名), 这条保证「不管什么形态, 块变了就红」。r13 MEDIUM-3 指出的
    「多行 opaque 记录只绑首行 ⇒ 换第二行仍静默」也由它直接封住。
    """
    out: list[str] = []
    raw_lines = _lines(text)
    for start, body, is_fence in _fence_blocks(text):
        blob = "\n".join(body)
        if "/tmp" not in blob:
            continue
        if is_fence:
            # ⛔ r14 HIGH-1B: 用**原文行**(含容器前缀), 不用剥过前缀的 body ——
            # `> P = …` 与 `P = …` 剥完前缀后完全一样, 于是「把一行移进/移出引用块」
            # (CommonMark 下这会改变它在不在代码块里)对指纹完全静默。
            # ⛔ r15 MEDIUM-3: 把**开启标记行**一并纳入 —— info string 决定执行者用哪个
            # 解释器, 而 `P="/tmp/cls-exam/"'\\x2e\\x2e/x'` 在 sh 下合规、在 python 下越界。
            # 只把 `sh` 改成 `python` 时块体一字未变, 不纳入标记行就完全静默。
            raw = "\n".join(raw_lines[max(start - 2, 0) : start - 1 + len(body)])
            out.append(f"B{start}:{_line_fingerprint(raw)}")
    # ⛔ r15 HIGH-2: 散文侧按**段**取指纹, 不逐行 —— 一个跨行 code span 的第二行可能
    # 不含 `/tmp`(`执行 \`P = ("/tmp/cls-exam/"`␊`"../x")\``), 逐行绑就完全静默。
    for seg_start, seg in _prose_segments(text):
        blob = "\n".join(seg)
        if "/tmp" in blob:
            out.append(f"S{seg_start}:{_line_fingerprint(blob)}")
    return sorted(out)


def check_tmp_blocks(root: Path, baseline: dict[str, list[str]]) -> list[str]:
    """第十条判据: 每份 SKILL.md 里「含 `/tmp` 的块/行」的指纹集合精确相等。"""
    problems: list[str] = []
    skills_dir = root / "skills"
    for name in sorted(baseline):
        f = skills_dir / name / "SKILL.md"
        if not f.exists():
            problems.append(f"[块指纹] {name}: SKILL.md 不存在 (基线要求存在) path={f}")
            continue
        actual = tmp_block_fingerprints(f.read_text(encoding="utf-8"))
        want = sorted(baseline[name])
        if actual != want:
            ca, cw = Counter(actual), Counter(want)
            problems.append(
                f"[块指纹] {name}: 含 `/tmp` 的块/行指纹集合不等 "
                f"期望={want} 实测={actual}\n"
                f"        新增={sorted((ca - cw).elements())} 缺失={sorted((cw - ca).elements())}\n"
                f"        —— `B<行号>` 是 fence 块整块指纹, `L<行号>` 是散文行指纹。这条**不做语义"
                f"分析**, 只问「含 /tmp 的那块文本变没变」: 改了就要人看一眼并同步基线"
            )
    return problems


def check_url_override(root: Path, baseline: dict[str, list[int]]) -> list[str]:
    """URL 覆盖判据: 每份 SKILL.md 里给 `CLS_BACKEND_URL` 赋值的行号集合精确相等（现状全 0）。"""
    problems: list[str] = []
    skills_dir = root / "skills"
    for name in sorted(baseline):
        f = skills_dir / name / "SKILL.md"
        if not f.exists():
            problems.append(f"[URL 覆盖] {name}: SKILL.md 不存在 (基线要求存在) path={f}")
            continue
        found = url_default_overridden_lines(f.read_text(encoding="utf-8"))
        actual = sorted(ln for ln, _t in found)
        want = sorted(baseline[name])
        if actual != want:
            by_line = dict(found)
            ca, cw = Counter(actual), Counter(want)
            extra = sorted((ca - cw).elements())
            problems.append(
                f"[URL 覆盖] {name}: 给 CLS_BACKEND_URL 赋值的行号集合不等 "
                f"期望={want} 实测={actual} (新增={extra} 缺失={sorted((cw - ca).elements())})\n"
                + "".join(f"        :{ln}  {by_line.get(ln, '')[:100]}\n" for ln in extra)
                + "        —— 给它赋值就把 `${CLS_BACKEND_URL:-…}` 的缺省形态架空了, 等于取消了本卡的整改"
            )
    return problems


def _line_fingerprint(text: str) -> str:
    r"""内容摘要 —— 让「已登记的行/块」不能被换成别的内容。

    ⛔ r14 LOW-2: 取 **16 位**不是 8 位。Codex 用 32 位摘要真的撞出了一对
    「安全/坏」内容(`# 133530` vs `# 19218` 同摘要), 虽未撞中现有基线, 但登记项越多
    撞上的机会越大, 而摘要长度是零成本的。
    ⛔ r14 MEDIUM-1: **不 `strip()`**。行尾空白在 shell 里有语义 ——
    `P="/tmp/cls-exam/.."\ ` 末尾那个空格删掉后, 反斜杠变成续行、路径规范化成 `/tmp`,
    而 `strip()` 让两者摘要相同。只归一化行尾换行符, 不动其余空白。
    """
    return hashlib.sha256(text.rstrip("\r\n").encode("utf-8")).hexdigest()[:16]


def check_opaque_tmp(root: Path, baseline: dict[str, list[str]]) -> list[str]:
    r"""不透明记号判据: 每份 SKILL.md 里「含 `/tmp` 且带反引号/反斜杠」的行号集合精确相等。

    现状全 0 —— **零余量**。往 fence 里写 ``P="/tmp/cls-exam/"`printf .`"./x"``、
    JSON 的 `"\u002e\u002e\/x"`、或任何反斜杠续行, 都会立刻红并要求登记:
    这段文本按哪门语言解析、其中反斜杠算不算转义, 静态判不了。
    """
    problems: list[str] = []
    skills_dir = root / "skills"
    for name in sorted(baseline):
        f = skills_dir / name / "SKILL.md"
        if not f.exists():
            problems.append(f"[不透明记号] {name}: SKILL.md 不存在 (基线要求存在) path={f}")
            continue
        found = [(f"{ln}:{_line_fingerprint(txt)}", txt) for ln, txt in opaque_tmp_lines(f.read_text(encoding="utf-8"))]
        # ⛔ r11 HIGH-3: 只钉**行号**不够 —— 登记一条保守误报, 就等于把那个行号变成
        # 一个可以塞真实债的槽(把 `` `/tmp/cls-exam/` `` 换成
        # ``P="/tmp/cls-exam/"`printf .`"./x"`` 后, opaque 仍是同一行号、其余判据全空,
        # 完全静默)。所以登记项带**内容指纹**: 行号 + 该行 strip 后的 sha8。
        actual = sorted(key for key, _txt in found)
        want = sorted(baseline[name])
        if actual != want:
            by_line = dict(found)
            ca, cw = Counter(actual), Counter(want)
            extra = sorted((ca - cw).elements())
            problems.append(
                f"[不透明记号] {name}: 含 `/tmp` 的反引号/反斜杠行号集合不等 "
                f"期望={want} 实测={actual} (新增={extra} 缺失={sorted((cw - ca).elements())})\n"
                + "".join(f"        :{ln}  {by_line.get(ln, '')[:100]}\n" for ln in extra)
                + "        —— 命令替换与转义序列的含义由读它的那门语言决定, 静态门不猜, 要人登记"
            )
    return problems


#: 散文里把「上一级 / 父目录」写成**自然语言**的关键词(中英)。
#: SKILL.md 的散文**就是给 agent 的执行指令** —— Step 3 第 4 步用 `Write` 工具落文件,
#: 落点由那句散文决定。把越界的那一段搬到反引号**外面**, 它就成了自然语言:
#:     把剩余候选写到 `/tmp/cls-exam/` **的上一级目录**下的 exam-candidates.json
#: backtick span 只剩 `/tmp/cls-exam/`(合规), 计数四端不动, 无 `..` 无 `$` ⇒ 六条全绿,
#: 而 agent 会把文件写到 `/tmp/exam-candidates.json`。
_PARENT_DIR_PROSE_RE = re.compile(
    r"上一级|上級|父目录|父目錄|父级|父級|同级目录|同級目錄|平级|平級"
    r"|parent directory|parent dir|\bpardir\b"
)


def parent_dir_prose_lines(text: str) -> list[tuple[int, str]]:
    """**散文**里同时出现 `/tmp` 与「父目录/上一级」语义词的行 —— `(行号, 行)`。

    只扫 fence **之外**(fence 内的同类由第六条判据从 `ast` 层面管)。
    """
    out: list[tuple[int, str]] = []
    for start, body, is_fence in _fence_blocks(text):
        if is_fence:
            continue
        for offset, line in enumerate(body):
            if "/tmp" in line and _PARENT_DIR_PROSE_RE.search(line):
                out.append((start + offset, line.strip()))
    return out


def check_parent_dir_prose(root: Path, baseline: dict[str, list[int]]) -> list[str]:
    """第七条判据: 散文里的「父目录」语义行号集合精确相等(现状全 9 份皆空)。

    ⛔ 这条与前六条的区别: 前六条问「**这串文本**指向哪里」, 它问「**这句指令**
    会让 agent 把文件放在哪里」。判据能证明的是前者, 而 SKILL.md 的效力在后者 ——
    这个落差正是 finding #2 的根因, 补这条是承认落差、要求登记, 不是假装能推断语义。
    """
    problems: list[str] = []
    skills_dir = root / "skills"
    for name in sorted(baseline):
        f = skills_dir / name / "SKILL.md"
        if not f.exists():
            problems.append(f"[散文父目录] {name}: SKILL.md 不存在 (基线要求存在) path={f}")
            continue
        found = parent_dir_prose_lines(f.read_text(encoding="utf-8"))
        actual = sorted(ln for ln, _txt in found)
        want = sorted(baseline[name])
        if actual != want:
            by_line = dict(found)
            ca, cw = Counter(actual), Counter(want)
            extra = sorted((ca - cw).elements())
            problems.append(
                f"[散文父目录] {name}: 散文里 `/tmp` 与「父目录/上一级」同行的行号集合不等 "
                f"期望={want} 实测={actual} (新增={extra} 缺失={sorted((cw - ca).elements())})\n"
                + "".join(f"        :{ln}  {by_line.get(ln, '')[:100]}\n" for ln in extra)
                + "        —— 散文是给 agent 的执行指令: 落点写在反引号外面时判据看不见路径, 必须登记"
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


#: U6 地盘的两个 scripts 目录 —— 手册 §一 明列。
U6_SEED = frozenset(
    {
        "skills/board-recap/scripts/recap_exam_build.py",
        "skills/clear-inbox/scripts/inbox_preview.py",
    }
)
U6_DIRS = ("skills/board-recap/scripts/", "skills/clear-inbox/scripts/")


def check_handoff_constants(
    main_body_baseline: dict[str, dict[str, int]],
    scripts_baseline: dict[str, dict[str, int]],
    u6_baseline: dict[str, dict[str, int]],
) -> list[str]:
    """交接常量的**正式判据** —— 单列 / 不重叠 / U6 只收自己地盘且新登记零余量。

    ⛔ 三个基线都走参数(而不是直接读模块全局), 这样负控能把变异后的常量喂进来。
    用例**必须调用本函数**, 不许自己重写一份集合判断(Codex round-2 MEDIUM-6):
    自己重写时, 即使正式判据退回旧版, 用例照绿 —— 它声称防守的回归根本抓不到。
    """
    problems: list[str] = []

    if "quiz-answer" in main_body_baseline:
        problems.append("quiz-answer 必须单列在 QUIZ_ANSWER_BASELINE, 不得进主 BASELINE")

    overlap = set(scripts_baseline) & set(u6_baseline)
    if overlap:
        problems.append(f"U6 两份必须单列, 不得同时出现在 SCRIPTS_BASELINE: {sorted(overlap)}")

    # ⛔ seed 允许**迁移**而非只能留驻(Codex round-4 MEDIUM-5): U6 给 seed 脚本加了债
    # ⇒ 该条目必须挪进 SCRIPTS_BASELINE 走人工审阅 —— 若此处仍要求 seed ⊆ u6, 那条
    # 「合法迁移」的路就被堵死(留 U6 报零余量, 挪过去又报"被删", 怎么做都错)。
    # 判据改为: seed 每份至少在**两张表之一**登记, 且不允许两张表同时登记(上方的
    # overlap 检查管后者)。
    missing_seed = U6_SEED - set(u6_baseline) - set(scripts_baseline)
    if missing_seed:
        problems.append(
            f"U6 交接项被删 —— 手册 §一 明列这两份属 U6 地盘, 必须留在 U6_SCRIPTS_BASELINE"
            f"(带债时迁去 SCRIPTS_BASELINE 亦可, 两处都不在才算删): 缺={sorted(missing_seed)}"
        )

    # ⛔ 只收 U6 地盘: 不许把别处(尤其是主基线里已有)的脚本挂到 U6 名下换维护归属。
    stray = sorted(p for p in u6_baseline if not p.startswith(U6_DIRS))
    if stray:
        problems.append(
            f"U6_SCRIPTS_BASELINE 只收 U6 地盘({' / '.join(U6_DIRS)})下的脚本, 别处的请登记进 SCRIPTS_BASELINE: {stray}"
        )

    # ⛔ 新登记项必须**零余量**(Codex round-2 MEDIUM-3): 目录约束只保证「登记在对的地方」,
    # 挡不住「登记的同时把新债一起带进来」。U6 要加脚本可以, 但那脚本不许自带
    # /tmp / /Users/ / 树名 —— 带债的必须走 SCRIPTS_BASELINE 的人工审阅。
    # ⛔ 零余量覆盖**全部**条目, seed 不豁免(Codex round-3 MEDIUM-6): r2 版跳过 seed,
    # 于是 `inbox_preview.py` 登记成 tmp=1 也能过 —— 原两份同样锁不住。U6 若真要给
    # 这两份加 /tmp, 把该条目**挪去 SCRIPTS_BASELINE**(人工审阅), 不要留在交接常量里。
    for path, counts in sorted(u6_baseline.items()):
        nonzero = {k: v for k, v in counts.items() if v}
        if nonzero:
            problems.append(
                f"U6 新登记的 {path} 必须零余量, 实测带债 {nonzero} —— "
                f"带债的脚本请走 SCRIPTS_BASELINE(人工审阅), 不要经 U6 交接常量放进来"
            )
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


def test_suspicious_tmp_lines_match_baseline():
    """保守判据(正控): `/tmp` 与 `..`/变量展开同行的行号集合 == 基线。"""
    problems = check_suspicious_tmp_lines(DEFAULT_ROOT, SUSPICIOUS_TMP_LINES_BASELINE)
    assert not problems, "可疑行基线漂移:\n" + "\n".join(problems)


def test_dynamic_tmp_joins_match_baseline():
    """第六条判据(正控): 含 `/tmp` 的动态拼接行号集合 == 基线(现状全 9 份皆空)。"""
    problems = check_dynamic_tmp_joins(DEFAULT_ROOT, DYNAMIC_TMP_JOIN_BASELINE)
    assert not problems, "动态拼接基线漂移:\n" + "\n".join(problems)


def test_parent_dir_prose_matches_baseline():
    """第七条判据(正控): 散文「父目录」语义行号集合 == 基线(现状全 9 份皆空)。"""
    problems = check_parent_dir_prose(DEFAULT_ROOT, PARENT_DIR_PROSE_BASELINE)
    assert not problems, "散文父目录基线漂移:\n" + "\n".join(problems)


def test_opaque_tmp_lines_match_baseline():
    """第八条判据(正控): 含 `/tmp` 的反引号/反斜杠行号集合 == 基线(现状全 9 份皆空)。"""
    problems = check_opaque_tmp(DEFAULT_ROOT, OPAQUE_TMP_BASELINE)
    assert not problems, "不透明记号基线漂移:\n" + "\n".join(problems)


def test_url_override_lines_match_baseline():
    """第九条判据(正控): 给 `CLS_BACKEND_URL` 赋值的行号集合 == 基线(现状全 9 份皆空)。"""
    problems = check_url_override(DEFAULT_ROOT, URL_OVERRIDE_BASELINE)
    assert not problems, "URL 覆盖基线漂移:\n" + "\n".join(problems)


def test_fence_indent_budget_has_no_allowance_without_container():
    r"""⛔ 局部回归断言: **无容器时 opening 自身的缩进不给 closing 额度**(r15 HIGH-1)。

    r16 LOW-1 指出这处修复**没有断言钉住** —— 内存恢复「无容器也给额度」后, 51 条
    指名形态 + 8 条兜底形态仍 59/59 通过。局部修复要有局部断言, 不能指望形态表兜。

    `   ```py` 的 opening 缩进 3(合法), closing 缩进 4 ⇒ CommonMark **不闭合**;
    若错误地把 opening 的 3 也算成额度(3+3=6 ≥ 4), 就会提前闭合、把后文推成散文。
    """
    text = "   ```python\nA = 1\n    ```\nP = 2\n   ```"
    fenced = [b for b in _fence_blocks(text) if b[2]]
    assert len(fenced) == 1, f"缩进 4 的 ``` 不该闭合缩进 3 的 opening, 实得: {_fence_blocks(text)}"
    assert any("P = 2" in ln for ln in fenced[0][1]), f"后文应留在围栏内(否则就是提前闭合了): {fenced[0][1]}"
    # 有容器时**要**给额度: `10. ```py` 的内容基线是 4, closing 缩进 4 应当闭合。
    listed = [b for b in _fence_blocks("10. ```python\n    A = 1\n    ```\nX") if b[2]]
    assert len(listed) == 1 and not any("X" in ln for ln in listed[0][1]), (
        f"列表内的 fence 应当正常闭合(容器 marker 宽度要给额度): {listed}"
    )


def test_continuation_ambiguity_is_resolved_by_union_not_by_guessing():
    r"""⛔ 局部回归断言: 续接歧义走**并集**(r16 HIGH-3), 不靠正则猜。

    r16 LOW-1 同样指出这处没有断言 —— 恢复旧续接正则后 59/59 仍通过。
    这里直接对 `_parse_units()` 发问: heredoc 终止符**恰好叫 `else`** 时, 既要有
    「在此切断」的短单元, 也要有「继续累加」的长单元 —— 因为静态区分不了哪种对。
    """
    body = [
        "if False:",
        "    pass",
        'elif ("/tmp/cls-exam/" ".." "/x") == q:',
        "    pass",
        "else",  # 既可能是 Python 续接, 也可能是 heredoc 终止符
    ]
    units = _parse_units(body)
    joined = [chunk for _off, chunk, parsed in units if parsed]
    assert any("elif" in c and c.count("\n") >= 2 for c in joined), (
        f"歧义点上必须同时产出**长单元**(含 elif 的整段), 实得: {[c[:40] for c in joined]}"
    )
    # 并集的收益: 长单元里 `ast` 能折出越界路径, 而短单元的解释下它会降级到 shlex。
    assert any("/tmp/cls-exam/../x" in v for _o, _c, p in units if p for v in p), (
        f"长单元应折出 `/tmp/cls-exam/../x`(并集的全部意义所在), 实得: {units}"
    )


def test_opaque_baseline_entries_are_content_bound():
    r"""⛔ **登记项必须绑内容, 不能只绑行号**(r11 HIGH-3)。

    登记一条保守误报, 若基线只钉行号, 就等于把那个行号变成**可以塞真实债的槽**:
    把 start-exam-board `:577` 里的 `` `/tmp/cls-exam/` `` 换成
    ``P="/tmp/cls-exam/"`printf .`"./x"``(真命令替换, 落点 `/tmp/x`), opaque 仍报
    同一行号、其余判据全空 ⇒ 完全静默。r10 我写「零余量不变」是错的。

    ⛔ 这条测试本身在 r11 整改时写过、又在重写形态表时被误删, 而 commit message 里
    声称加了它 —— r12 LOW-2 抓到。补回并记下: **声称加了断言就要能 grep 到**。
    """
    assert all(
        ":" in entry and len(entry.rsplit(":", 1)[-1]) == 16
        for entries in OPAQUE_TMP_BASELINE.values()
        for entry in entries
    ), f"登记项必须是 `行号:sha16` 形态(r14 LOW-2 把摘要从 8 位加长到 16 位): {OPAQUE_TMP_BASELINE}"

    registered = "- **CARD**：候选池临时文件改用固定命名空间 `/tmp/cls-exam/`（Step 3）"
    swapped = registered.replace("`/tmp/cls-exam/`", 'P="/tmp/cls-exam/"`printf .`"./x"')
    assert _line_fingerprint(registered) != _line_fingerprint(swapped), (
        "把登记行换成真实债后指纹必须变 —— 否则登记行就是一个静默槽"
    )
    assert opaque_tmp_lines(swapped), "换上去的那行本身必须被第八条看见(否则这条负控考错了对象)"

    # ⛔ r13 LOW-2: 上一版只证明「摘要函数会变」, 没证明**门用了摘要**。这里直接对
    # `check_opaque_tmp()` 发问: 给一份「行号对、指纹错」的基线, 它必须红。
    fake = {name: [f"{e.split(':')[0]}:deadbeef" for e in entries] for name, entries in OPAQUE_TMP_BASELINE.items()}
    assert check_opaque_tmp(DEFAULT_ROOT, fake), (
        "把基线里的指纹换成假值后 `check_opaque_tmp()` 仍绿 —— 说明它只比行号、没用指纹"
    )


def test_parse_unit_cost_on_current_tree():
    r"""钉住 `_parse_units()` 在**当前树上的真实成本** —— 不是返回单元的长度。

    ⛔ r10 LOW-3 / r11 LOW: 去掉行数上限后, 单元内每加一行都要重解析一次 ⇒ **O(k²)**。
    上一版只量「返回单元的最长行数」, Codex 指出它不承重: 窗口尝试到块尾后**回退成
    单行单元**, 返回的最长单元恒为 1, 而二次成本已经发生。所以这里直接量**耗时**。

    这条哨兵在整改中当场发挥过两次作用:
      · r11 把 closing fence 缩进写成绝对 `^ {0,3}` ⇒ 缩进的 fence 闭不上、块被吞成
        一整段 ⇒ 最长单元 278 → 545、整套测试 15s → 66s;
      · r11 的续接判定一度写成「凡缩进 >= base 的续接子句都继续」⇒ 同样吞块。
    两次都是它先红, 而不是等到某天整套测试莫名其妙变慢。

    阈值取得宽(10s vs 实测 ~1.5s)是刻意的: 它要抓的是**数量级退化**, 不是机器快慢。
    """
    _parse_units_cached.cache_clear()  # r12 LOW-1: 不清缓存的话前面的检查已预热, 量的是暖路径
    start = time.perf_counter()
    longest, where = 0, ""
    for name in sorted(EXPECTED_SKILLS):
        text = (DEFAULT_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        for _start, body, is_fence in _fence_blocks(text):
            if not is_fence:
                continue
            for _off, chunk, _parsed in _parse_units(body):
                n = len(chunk.splitlines())
                if n > longest:
                    longest, where = n, name
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0, (
        f"9 份 SKILL.md 跑一遍 `_parse_units()` 用了 {elapsed:.1f}s(最长单元 {longest} 行, "
        f"在 {where}) —— 单元内是 O(k²), 这个耗时说明解析边界判错了、把整块吞成一个单元。"
        f"先看那个单元的首行是什么, 别直接放宽阈值"
    )


def test_tmp_block_fingerprints_match_baseline():
    """第十条判据(正控): 含 `/tmp` 的块/行指纹集合 == 基线。

    ⛔ 这是**兜底网**: 前九条判据各自回答「是哪一类问题」, 这条只回答「块变了没有」。
    它对形态表 51 个反例实测 45 个可区分(其余 6 个不含 `/tmp`, 归第九条 URL 判据),
    而判据本身没有解析、没有正则边界、没有缩进猜测 —— 几乎没有回归空间。
    """
    problems = check_tmp_blocks(DEFAULT_ROOT, TMP_BLOCK_BASELINE)
    assert not problems, "块指纹基线漂移:\n" + "\n".join(problems)


#: Codex round-13 的形态: **九条判据全部看不见, 只有第十条兜底网能区分**。
#: 这张表是立第十条判据的**直接证据** —— 它们全是「块内文本变了、但九条判据的
#: 语义分析各自够不着」的形态(heredoc 标记撞关键字 / NBSP 分词 / 转义引号 /
#: 标题里的未闭合反引号 / 十位数字非 marker / 跨单元赋值覆盖 / 解构赋值 / 注释吸收)。
_NET_ONLY_FORMS: list[tuple[str, str, str]] = [
    (
        "heredoc 结束标记恰好是 `else`",
        '```sh\npython3 - <<\'else\'\nif False:\n    pass\nelif P := "/tmp/cls-exam/" "." "./x":\n    pass\nelse\necho done\n```',
        '```sh\npython3 - <<\'else\'\nif False:\n    pass\nelif P := "/tmp/cls-exam/" "a" "/x":\n    pass\nelse\necho done\n```',
    ),
    # ⛔ r15 LOW: 这里必须是**真 NBSP**(U+00A0)。上一版写成了 ASCII 空格, 于是这条
    # 负控根本没在考 NBSP —— 用 `\u00a0` 转义写出来, 顺带避免它在编辑中被静默改回空格。
    (
        "NBSP 分隔的两段引号",
        '执行 P="/var/cache"\u00a0"/tmp/cls-exam/x"',
        '执行 P="/tmp/cls-exam/x"',
    ),
    ('转义引号 `\\"` 被误当闭合', '执行 P="/var/cache \\" /tmp/cls-exam/x"', '执行 P="/tmp/cls-exam/x"'),
    (
        "标题里的未闭合反引号",
        "# 标题 `未闭合\n执行 `/var/cache(\n/tmp/cls-exam/x`",
        "# 标题 `未闭合\n执行 `/tmp/cls-exam/x\n`",
    ),
    (
        "十位数字不是列表 marker",
        "执行 `/var/cache(\n1234567890. /tmp/cls-exam/x`",
        "执行 `/tmp/cls-exam/x\n1234567890. y`",
    ),
    (
        "跨语法单元的赋值覆盖",
        '```python\nP = "/tmp/cls-exam/x"\nP = "/var/cache/x"\n```',
        '```python\nP = "/tmp/cls-exam/x"\nQ = "/var/cache/x"\n```',
    ),
    (
        "解构赋值覆盖",
        '```python\nP = "/tmp/cls-exam/x"; P, = "/var/cache/x",\n```',
        '```python\nP = "/tmp/cls-exam/x"; Q, = "/var/cache/x",\n```',
    ),
    (
        "合规串移进注释",
        '```python\nP = "/var/cache/x"  # "/tmp/cls-exam/x"\n```',
        '```python\nP = "/tmp/cls-exam/x"\n```',
    ),
]


@pytest.mark.parametrize("why,bad,safe", _NET_ONLY_FORMS, ids=[w[:22] for w, _b, _s in _NET_ONLY_FORMS])
def test_net_only_forms_are_caught_by_the_tenth_judge(why: str, bad: str, safe: str):
    """⑳ **只有兜底网接得住的形态** —— 九条判据全瞎, 第十条必须能区分。

    ⛔ 这条同时是**反向断言**: 若哪天九条判据里有谁能抓住其中某个形态, 这条不会红
    (它只要求兜底网能区分), 但那说明语义判据的覆盖面变宽了, 是好事。
    真正要防的是**兜底网自己失效** —— 那时这里立刻红。
    """
    if "NBSP" in why:
        assert "\u00a0" in bad, "标为 NBSP 的样本里必须真的有 U+00A0(r15 LOW: 上一版写成了 ASCII 空格)"
    assert tmp_block_fingerprints(bad) != tmp_block_fingerprints(safe), (
        f"兜底网分不开这对形态({why}) —— 九条判据对它们也全瞎, 那就是一个完全静默的面"
    )


def test_tmp_block_net_catches_what_the_nine_judges_may_miss():
    """⛔ 兜底网的**承重**证明: 对形态表里的坏/安全形态, 块指纹应当能区分绝大多数。

    这条把「45/51」这个数字钉成断言 —— 它是立第十条判据的**依据**, 不能只写在
    docstring 里(§六 ⑫ 的教训: 未经验证的声明比没有声明更危险)。
    ⛔ r14 LOW-4 更正: 分不开的六例**不是**「全归 URL/unset」——Codex 实测是
    **四例 URL/`unset`** + **两例 Python 里 `"/t"`+`"mp/…"` 拼接**(源码字面没有 `/tmp`,
    由第六条动态拼接判据检出)。所以这里的断言改成: 分不开的形态必须**能被别的判据
    接住**, 而不是「必须不含 `/tmp`」——后者是我原来写错的归因。
    """
    indistinguishable = [
        (bad, why)
        for bad, safe, _judge, why in _R7_HIGH_FORMS
        if tmp_block_fingerprints(bad) == tmp_block_fingerprints(safe)
    ]
    for bad, why in indistinguishable:
        covered = (
            escaping_tmp_paths(bad)
            or suspicious_tmp_lines(bad)
            or dynamic_tmp_join_lines(bad)
            or opaque_tmp_lines(bad)
            or url_default_overridden_lines(bad)
        )
        assert covered, f"块指纹分不开、九条判据也全瞎 ⇒ 完全静默的面: {why[:70]}"
    # ⛔ r14 LOW-1: 也要验**正式消费端** —— 上一版把 `check_tmp_blocks()` 改成恒返 []
    # 后, 正控与这条都照过, 承重的只有摘要函数。给一份「键对、指纹错」的基线, 门必须红。
    fake = {n: [f"{e.split(':')[0]}:deadbeefdeadbeef" for e in v] for n, v in TMP_BLOCK_BASELINE.items()}
    assert check_tmp_blocks(DEFAULT_ROOT, fake), "把基线里的指纹换成假值后 `check_tmp_blocks()` 仍绿 —— 说明门没用指纹"

    distinguishable = len(_R7_HIGH_FORMS) - len(indistinguishable)
    assert distinguishable >= 45, (
        f"块指纹只区分了 {distinguishable}/{len(_R7_HIGH_FORMS)} 个形态(基线 45) —— "
        f"兜底网的覆盖面掉了, 先看是不是 `_fence_blocks` 的分块变了"
    )


def test_every_per_skill_baseline_covers_all_nine_skills():
    """⛔ **每个按 skill 分的基线都必须恰好覆盖 9 份**(Codex round-2 MEDIUM-2)。

    没有这条时: 删掉 `ESCAPING_TMP_BASELINE["start-exam-board"]` 后, `check_escaping_tmp`
    只遍历 `baseline` 的键 ⇒ 那份 skill **静默不再被检查**, 而所有既有断言照绿。
    随后把它的命名空间路径换成 `/tmp/cls-exam/../x`(四端计数不变) 就完全无人发现。

    「少一份就静默失明」是按键遍历的判据的通病 —— 三个基线一起钉。
    """
    for label, baseline in (
        ("BASELINE + QUIZ_ANSWER_BASELINE", set(_merged_body_baseline())),
        ("ESCAPING_TMP_BASELINE", set(ESCAPING_TMP_BASELINE)),
        ("SUSPICIOUS_TMP_LINES_BASELINE", set(SUSPICIOUS_TMP_LINES_BASELINE)),
        ("DYNAMIC_TMP_JOIN_BASELINE", set(DYNAMIC_TMP_JOIN_BASELINE)),
        ("PARENT_DIR_PROSE_BASELINE", set(PARENT_DIR_PROSE_BASELINE)),
        ("OPAQUE_TMP_BASELINE", set(OPAQUE_TMP_BASELINE)),
        ("URL_OVERRIDE_BASELINE", set(URL_OVERRIDE_BASELINE)),
        ("TMP_BLOCK_BASELINE", set(TMP_BLOCK_BASELINE)),
    ):
        assert baseline == set(EXPECTED_SKILLS), (
            f"{label} 覆盖面必须恰好 == 9 份 vault skill "
            f"(缺={sorted(set(EXPECTED_SKILLS) - baseline)} 多={sorted(baseline - set(EXPECTED_SKILLS))}) —— "
            f"少一份 = 那份 skill 静默不再被检查"
        )


def test_ns_counting_agrees_with_shell_judge_on_current_tree():
    """放行端口径与卡文 §二.2 的 shell 裁判在**当前树上**一致。

    测试侧 `tmp_ns` 用带左边界的正则(放行端要窄), shell 侧是 `grep -oF '/tmp/cls-exam/'`
    裸子串。两者**只在有人写 `/var/cache/tmp/cls-exam/…` 这类冒充路径时**才会分叉。

    这条钉住「当前不分叉」: 将来它红了, 说明树上出现了冒充路径 —— 那正是要抓的东西,
    而不是判据坏了。⛔ 不要因为它红就把左边界删掉。
    """
    skills_dir = DEFAULT_ROOT / "skills"
    for name in sorted(EXPECTED_SKILLS):
        text = (skills_dir / name / "SKILL.md").read_text(encoding="utf-8")
        strict = len(_TMP_NS_RE.findall(text))
        shell_like = text.count(TMP_NAMESPACE)
        assert strict == shell_like, (
            f"{name}: 放行端严格计数={strict} 与 shell 裸子串计数={shell_like} 分叉 —— "
            f"树上出现了形如 `/var/cache{TMP_NAMESPACE}…` 的冒充路径, 请查看该文件"
        )


@pytest.mark.parametrize(
    "literal,bare_delta,escapes,suspicious,why",
    [
        # 真正合规的两个 —— 三列全放行是**应该**的
        ("/tmp/cls-exam/", 0, False, False, "钦定形态本身"),
        ("/tmp/cls-exam/x.json", 0, False, False, "命名空间内的文件"),
        # 只被计数拦下
        ("/tmp/cls-exam", 1, False, False, "无尾斜杠: 写法不是钦定形态(计数红), 指向就是命名空间本身(不越界)"),
        ("/tmp/other.json", 1, True, False, "普通裸路径: 计数与越界都红"),
        # 计数看不见, 靠越界/可疑行拦下
        ("/tmp/cls-exam/../x", 0, True, True, "穿越在后: 计数裸值 0, 越界与可疑行都红"),
        ("/tmp/a/../cls-exam/z", 1, False, True, "穿越在前: 计数红(写法不合规), 规范化后仍在命名空间内"),
        # ⛔ Codex round-2 找到的 —— 它们是这张表存在的理由
        (
            "/tmp/cls-exam/a,b/../../x.json",
            0,
            True,
            True,
            "ASCII 逗号入 token 后整段进 normpath ⇒ 越界也红(r3 前 token 被截只剩可疑行)",
        ),
        ("/tmp/cls-exam/..,x", 0, False, True, "`..,x` 是单一路径段不解析 ⇒ 越界放行, 可疑行红(保守)"),
        ('P="/tmp/cls-exam/${REL}"', 0, False, True, "shell 变量展开: 静态证不出落点 ⇒ 要人登记"),
        # ⛔ Codex round-3 找到的 —— 同上
        (
            "/var/cache//tmp/cls-exam/x.json",
            1,
            False,
            False,
            "双斜杠冒充: 白名单边界拒绝把内层 /tmp 当起点 ⇒ ns 掉 ⇒ 计数红",
        ),
        ('P="/tmp/cls-exam/$1"', 0, False, True, "位置参数: `$` 任意位置触发可疑行"),
        (
            '```\nP = ("/tmp/cls-exam/"\n     "../x")\n```',
            0,
            True,
            True,
            "相邻字面量拼接(r3 HIGH-2): fence 逻辑行合并后可疑行红, 拼接组求值后越界也红",
        ),
        # ⛔ Codex round-4 找到的 —— v2 引号感知封住的四类
        (
            '```\nP = "/var/cache /tmp/cls-exam/exam-candidates.json"\n```',
            0,
            True,
            False,
            "引号内空格冒充(r4 HIGH-1): 字面量原子化 ⇒ 整串进 normpath ⇒ 越界红",
        ),
        (
            '```\nP = "/var/cache(/tmp/cls-exam/exam-candidates.json"\n```',
            0,
            True,
            False,
            "引号内开括号冒充(r4 HIGH-1): 同上",
        ),
        (
            '```\nP = ("/tmp/cls-exam/" "." "./exam-candidates.json")\n```',
            0,
            True,
            False,
            "单行点号拼接(r4 HIGH-2): 源码无连续 `..`, 拼接组求值后越界红",
        ),
        (
            # ⛔ r7 LOW-2: 原载体是 `/tmp/quiz-answer-incr.json;sub/../../x` —— 它**截断后
            # 也越界**(前半 `/tmp/quiz-answer-incr.json` 本就不在命名空间), 于是「在分号处
            # 截断」这个变异照样红, 这一行证明不了「尾巴没被截断」。换成前半**合规**的载体:
            # 截断 ⇒ `/tmp/cls-exam/a`(命名空间内, 不越界); 不截断 ⇒ normpath `/x`(越界)。
            '```\nP = "/tmp/cls-exam/a;sub/../../../x"\n```',
            0,
            True,
            True,
            "引号内分号变质(r4 MEDIUM-3): 截断即合规、整串才越界 ⇒ 这一行真的钉住「不截断」",
        ),
    ],
)
def test_three_judges_cover_each_other_without_gap(
    literal: str, bare_delta: int, escapes: bool, suspicious: bool, why: str
):
    """**三条判据的分工表** —— 每个不合规形态都必须至少被其中一条拦下。

    这张表本身就是判据: 将来若有人放宽任一条(把放行改成 `cls-` 前缀类、删掉左边界、
    删掉越界或可疑行判据), 对应行会立刻翻转。

    ⛔ 某一列 `False` **不是漏网** —— 只要同一行还有别的列拦着就行。真正危险的是
    **三列全放行**的行; 表里只有前两行, 且断言它们必须真在命名空间内。

    ⛔ `/var/cache/tmp/cls-exam/x.json` 那个形态**不在这张表里**, 因为它是「等计数替换」
    才成立的攻击(单看一个字面量看不出来), 由
    `test_negative_control_equal_count_swap_with_fake_namespace_must_redden` 覆盖。
    """
    counts = _body_counts(literal)
    assert bool(suspicious_tmp_lines(literal)) is suspicious, (
        f"{literal!r} ({why}): 可疑行期望={suspicious} 实测={suspicious_tmp_lines(literal)}"
    )
    assert bare_tmp(counts) == bare_delta, (
        f"{literal!r} ({why}): 子串裸值期望={bare_delta} 实测={bare_tmp(counts)} "
        f"(all={counts['tmp_all']} ns={counts['tmp_ns']})"
    )
    assert bool(escaping_tmp_paths(literal)) is escapes, (
        f"{literal!r} ({why}): 越界期望={escapes} 实测={escaping_tmp_paths(literal)}"
    )
    if bare_delta == 0 and not escapes and not suspicious:
        # ⛔ r3 HIGH-2b: `startswith` 会被「内嵌真换行 + ..」的字面量骗过
        # (`"/tmp/cls-exam/a\nb/../../x"` 以命名空间开头, 但 normpath 后越界)。
        # 改成对**整字面量**做 normpath —— 与越界判据同一"在命名空间内"定义。
        ns = TMP_NAMESPACE.rstrip("/")
        norm = posixpath.normpath(literal)
        assert norm == ns or norm.startswith(ns + "/"), (
            f"⛔ {literal!r} 被**三条判据一起**放行, 但整字面量规范化后是 {norm!r}, "
            f"不在 {TMP_NAMESPACE} 下 —— 这就是缺口"
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


def _discover_out_of_scope_8011(root: Path) -> dict[str, int]:
    """动态发现: 覆盖面**之外**、`canvas-vault/.claude/` 之下所有含 `8011` 的文件及次数。

    ⛔ r3 MEDIUM-5: 只遍历常量自己的键 ⇒ 删条目 = 该文件静默失明。改成**全树扫描**,
    常量与发现结果做**集合级**对照 —— 删条目 / 清空常量 / 新增债文件 / U3-C 模板化,
    四个方向全部会红。
    """
    covered = (
        {p.relative_to(root).as_posix() for p in (root / "skills").glob("*/SKILL.md")}
        | {p.relative_to(root).as_posix() for p in (root / "skills").glob("*/scripts/*.py")}
        | {p.relative_to(root).as_posix() for p in (root / "scripts").glob("*.py")}
    )
    found: dict[str, int] = {}
    skip_names = {".DS_Store"}
    skip_dirs = {"__pycache__", ".git"}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if not p.is_file() or rel in covered:
            continue
        # ⛔ r4 MEDIUM-6 的条件性副作用加固: 符号链接可能把扫描根指向树外 —— 不跟随;
        # 超大文件(备份/日志/缓存)不整读; 系统杂物按名跳过。
        if p.is_symlink() or p.stat().st_size > 1_000_000:
            continue
        if any(part in skip_names or part in skip_dirs for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):  # 二进制/不可读文件不在此门范围
            continue
        n = text.count("8011")
        if n:
            found[rel] = n
    return found


def test_out_of_scope_hardcoded_ports_are_registered():
    """本门覆盖面**之外**的 8011 债: 与**动态全树扫描**对照(归 U3-C, 本卡不碰)。

    ⛔ 这条**不是**在测本门的判据, 是在钉「本门测不到什么」这个声明本身 —— 且声明
    由扫描支撑, 不是一份会静默过期的清单:
      · 删条目/清空常量 ⇒ 发现集 ⊄ 常量键 ⇒ 红
      · 有人往覆盖面外文件新写 8011 ⇒ 红
      · U3-C 模板化 ⇒ 常量键 ⊄ 发现集 ⇒ 红(回来删对应项)
    """
    discovered = _discover_out_of_scope_8011(DEFAULT_ROOT)
    assert discovered == OUT_OF_SCOPE_8011, (
        f"覆盖面外的 8011 债与登记不符: 全树实测={discovered} 常量={OUT_OF_SCOPE_8011} —— "
        f"多={ {k: v for k, v in discovered.items() if OUT_OF_SCOPE_8011.get(k) != v} } "
        f"少/删={ {k: v for k, v in OUT_OF_SCOPE_8011.items() if discovered.get(k) != v} }"
    )


def test_baseline_constants_are_disjoint_and_complete():
    """交接常量(正控): 走**正式判据** `check_handoff_constants`, 不在这里重写逻辑。"""
    problems = check_handoff_constants(BASELINE, SCRIPTS_BASELINE, U6_SCRIPTS_BASELINE)
    assert not problems, "交接常量漂移:\n" + "\n".join(problems)
    assert set(_merged_body_baseline()) == EXPECTED_SKILLS, (
        f"层 2 基线覆盖面必须恰好 == 9 份 vault skill "
        f"期望={sorted(EXPECTED_SKILLS)} 实测={sorted(_merged_body_baseline())}"
    )
    # ⛔ 指标键集合精确相等(Codex round-4 LOW-11): 多出的键不被任何循环消费 ⇒ 加了
    # 也白加(假登记); 少了则 KeyError。每张 per-file 表都钉一次。
    for name, counts in _merged_body_baseline().items():
        assert set(counts) == set(BODY_METRICS), (
            f"{name}: 层 2 基线指标键漂移 期望={sorted(BODY_METRICS)} 实测={sorted(counts)}"
        )
    for rel, counts in _merged_scripts_baseline().items():
        assert set(counts) == set(SCRIPT_METRICS), (
            f"{rel}: 层 3 基线指标键漂移 期望={sorted(SCRIPT_METRICS)} 实测={sorted(counts)}"
        )


@pytest.mark.parametrize(
    "mutate,must_mention,why",
    [
        (
            lambda b, s, u: (
                b,
                s,
                {
                    **u,
                    "skills/clear-inbox/scripts/new_u6_tool.py": {
                        "tmp": 0,
                        "p8011_all": 0,
                        "p8011_ns": 0,
                        "localhost": 0,
                        "users_path": 0,
                        "tree_name": 0,
                    },
                },
            ),
            None,
            "U6 在自己地盘登记零余量新脚本 ⇒ **必须放行**(注释叫人这么做, 判据就不能拦)",
        ),
        (
            lambda b, s, u: (b, s, {k: v for k, v in u.items() if k != "skills/clear-inbox/scripts/inbox_preview.py"}),
            "U6 交接项被删",
            "删掉交接项 ⇒ 拦",
        ),
        (
            lambda b, s, u: (
                b,
                s,
                {
                    **u,
                    "scripts/fsrs_bridge.py": {
                        "tmp": 0,
                        "p8011_all": 0,
                        "p8011_ns": 0,
                        "localhost": 0,
                        "users_path": 1,
                        "tree_name": 1,
                    },
                },
            ),
            "只收 U6 地盘",
            "把别人地盘的脚本挂到 U6 名下换维护归属 ⇒ 拦",
        ),
        (
            lambda b, s, u: (
                b,
                s,
                {
                    **u,
                    "skills/clear-inbox/scripts/new_u6_tool.py": {
                        "tmp": 1,
                        "p8011_all": 0,
                        "p8011_ns": 0,
                        "localhost": 0,
                        "users_path": 1,
                        "tree_name": 0,
                    },
                },
            ),
            "必须零余量",
            "登记位置对, 但顺手把新债一起带进来 ⇒ 拦(Codex round-2 MEDIUM-3)",
        ),
        (
            lambda b, s, u: ({**b, "quiz-answer": QUIZ_ANSWER_BASELINE}, s, u),
            "必须单列",
            "把 quiz-answer 并回主 dict ⇒ 拦(U5-B 的 rebase diff 会混进无关行)",
        ),
        (
            lambda b, s, u: (
                b,
                {
                    **s,
                    "skills/clear-inbox/scripts/inbox_preview.py": {
                        "tmp": 0,
                        "p8011_all": 0,
                        "p8011_ns": 0,
                        "localhost": 0,
                        "users_path": 0,
                        "tree_name": 0,
                    },
                },
                u,
            ),
            "不得同时出现",
            "同一份脚本两个基线都登记 ⇒ 拦(改一处另一处静默失效)",
        ),
        (
            lambda b, s, u: (
                b,
                {
                    **s,
                    "skills/clear-inbox/scripts/inbox_preview.py": {
                        "tmp": 1,
                        "p8011_all": 0,
                        "p8011_ns": 0,
                        "localhost": 0,
                        "users_path": 0,
                        "tree_name": 0,
                    },
                },
                {k: v for k, v in u.items() if k != "skills/clear-inbox/scripts/inbox_preview.py"},
            ),
            None,
            "seed 脚本带债 ⇒ **迁去 SCRIPTS_BASELINE 必须放行**(r4 MEDIUM-5 的人工审阅迁移路径)",
        ),
        (
            lambda b, s, u: (
                b,
                s,
                {
                    **u,
                    "skills/clear-inbox/scripts/inbox_preview.py": {
                        "tmp": 1,
                        "p8011_all": 0,
                        "p8011_ns": 0,
                        "localhost": 0,
                        "users_path": 0,
                        "tree_name": 0,
                    },
                },
            ),
            "必须零余量",
            "seed 脚本带债仍留 U6 表 ⇒ 拦(r4 MEDIUM-6; 此例同时抓住 r2 版『seed 豁免』的回退)",
        ),
    ],
)
def test_handoff_judge_is_load_bearing(mutate, must_mention, why):
    """交接判据的正反负控 —— **全部经由正式判据函数**。

    ⛔ 这是 Codex round-2 MEDIUM-6 的整改: 原先这两条用例自己重写了集合判断, 于是
    正式判据即使退回 round-1 的 `== u6_seed`, 用例也照绿 —— 它声称防守的那个回归
    (「U6 照注释办事被门拦住」)根本抓不到。现在两者共用同一个函数, 判据一退化,
    第一行那条「必须放行」的用例立刻红。
    """
    problems = check_handoff_constants(*mutate(BASELINE, SCRIPTS_BASELINE, U6_SCRIPTS_BASELINE))
    if must_mention is None:
        assert not problems, f"{why} —— 实得: {problems}"
    else:
        joined = "\n".join(problems)
        assert any(must_mention in p for p in problems), f"{why} —— 期望消息含 {must_mention!r}, 实得: {joined}"


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
    """④ 对照组: 未改副本**五条判据全绿** —— 证明负控的「红」来自变异而非副本本身。"""
    assert not check_frontmatter(sandbox), check_frontmatter(sandbox)
    assert not check_body(sandbox, _merged_body_baseline()), check_body(sandbox, _merged_body_baseline())
    assert not check_scripts(sandbox, _merged_scripts_baseline()), check_scripts(sandbox, _merged_scripts_baseline())
    assert not check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE), check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)
    assert not check_suspicious_tmp_lines(sandbox, SUSPICIOUS_TMP_LINES_BASELINE), check_suspicious_tmp_lines(
        sandbox, SUSPICIOUS_TMP_LINES_BASELINE
    )


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
        "skills/board-split/scripts/probe.py": {
            "tmp": 0,
            "p8011_all": 0,
            "p8011_ns": 0,
            "localhost": 0,
            "users_path": 0,
            "tree_name": 0,
        },
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
    _swap_in_start_exam_board(sandbox, "/tmp/cls-exam/exam-candidates.json", literal)

    # ⛔ 前提必须是**计数判据放行**, 而且要**实际断言**它放行(Codex round-2 MEDIUM-5):
    # 原先这条用的是「追加」+ 只看裸值不变 —— 但追加会让 tmp_all/tmp_ns 双双 +1,
    # 计数判据其实**也会红**, 于是「证明了越界判据承重」就成了空话。改成等计数替换,
    # 四端纹丝不动, 再断言 check_body 为空, 红是谁给的才没有歧义。
    body = check_body(sandbox, _merged_body_baseline())
    assert not body, f"本用例的前提是**计数判据放行**(否则考的不是越界判据), 实得: {body}"

    problems = check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)
    joined = "\n".join(problems)
    assert any("start-exam-board" in p and "[越界]" in p for p in problems), (
        f"{literal} 必须被越界判据抓到, 实得: {joined}"
    )
    assert norm in joined, f"消息里应给出 normpath 结果 {norm}, 实得: {joined}"


def _swap_in_start_exam_board(sandbox: Path, old: str, new: str) -> None:
    """在副本的 start-exam-board 上做**等计数替换** —— 不是追加。

    ⛔ 追加和替换考的不是一回事(Codex round-2 MEDIUM-5): 追加一处 `/tmp/…` 会让
    `tmp_all` 与 `tmp_ns` 双双变化 ⇒ **计数判据也会红**, 于是「这条负控证明了越界判据
    承重」就成了空话 —— 红可能是计数那一层给的。只有替换掉一处**已有**命中, 才能让
    四端计数纹丝不动, 从而干净地考「计数看不见时, 别的判据看不看得见」。
    """
    f = sandbox / "skills" / "start-exam-board" / "SKILL.md"
    text = f.read_text(encoding="utf-8")
    swapped = text.replace(old, new, 1)
    assert swapped != text, f"预置失败: 副本里找不到要替换的 {old!r}"
    f.write_text(swapped, encoding="utf-8")


def test_negative_control_comma_truncated_escape_caught_by_line_judge(sandbox: Path):
    """⑨ **Codex round-2 HIGH(a) → r3 整改后两条都抓** —— 逗号路径。

    r2 时 `/tmp/cls-exam/a,b/../../w.json` 被 ASCII 逗号截成 `/tmp/cls-exam/a`, 计数与
    越界两条都看不见, 只剩可疑行。r3 起 ASCII 逗号**入 token**(中文标点仍截断防散文
    污染), 整段路径进 normpath ⇒ 越界判据也红 —— 两条各拦一次, 互为冗余。
    """
    _swap_in_start_exam_board(sandbox, "/tmp/cls-exam/exam-candidates.json", "/tmp/cls-exam/a,b/../../w.json")

    assert not check_body(sandbox, _merged_body_baseline()), "前提: 计数判据放行"
    esc = check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)
    assert any("start-exam-board" in p and "/tmp/w.json" in p for p in esc), (
        f"逗号入 token 后越界判据必须抓到 normpath=/tmp/w.json, 实得: {esc}"
    )
    problems = check_suspicious_tmp_lines(sandbox, SUSPICIOUS_TMP_LINES_BASELINE)
    joined = "\n".join(problems)
    assert any("start-exam-board" in p and "[可疑行]" in p for p in problems), f"可疑行判据也必须抓到, 实得: {joined}"


def test_negative_control_registered_line_comma_rot_must_redden(sandbox: Path):
    """⑨' **Codex round-3 MEDIUM-4** —— 已登记可疑行在逗号后静默变质。

    quiz-answer `:98` 已登记为可疑行; 把它行内的路径尾巴追加 `,sub/../../x` 后,
    r2 版的提取结果与基线逐字相同(逗号截断), 行号也不变 ⇒ 三个判据全绿。
    r3 起 ASCII 逗号入 token ⇒ 该 token 的 normpath 变成 `/x` ⇒ 越界多重集红。
    """
    f = sandbox / "skills" / "quiz-answer" / "SKILL.md"
    text = f.read_text(encoding="utf-8")
    swapped = text.replace("/tmp/quiz-answer-incr.json", "/tmp/quiz-answer-incr.json,sub/../../x", 1)
    assert swapped != text, "预置失败: 副本里找不到 quiz-answer 的 /tmp 路径"
    f.write_text(swapped, encoding="utf-8")

    assert not check_body(sandbox, _merged_body_baseline()), "前提: 计数判据放行(等计数替换)"
    esc = check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)
    assert any("quiz-answer" in p and "[越界]" in p and "/x" in p for p in esc), (
        f"逗号后的变质尾巴必须改变越界多重集(normpath=/x), 实得: {esc}"
    )


def test_negative_control_double_slash_fake_namespace_must_redden(sandbox: Path):
    """⑩ **Codex round-3 HIGH-1** —— `/var/cache//tmp/cls-exam/…` 双斜杠冒充。

    黑名单式左边界(排除 `[A-Za-z0-9_.~$-]`)看不见 `/`: 内层 `/tmp/` 前是 `/`,
    不在黑名单 ⇒ 照样当路径起点 ⇒ ns 计数照加 ⇒ 等计数替换四端不变。
    白名单式边界(只允许空白/引号/反引号/开括号)把 `/` 挡下 ⇒ ns 少一个 ⇒ 计数红。
    """
    _swap_in_start_exam_board(
        sandbox, "/tmp/cls-exam/exam-candidates.json", "/var/cache//tmp/cls-exam/exam-candidates.json"
    )
    problems = check_body(sandbox, _merged_body_baseline())
    joined = "\n".join(problems)
    assert any("start-exam-board" in p and "tmp_ns" in p for p in problems), (
        f"双斜杠冒充必须让放行端计数下降并报红, 实得: {joined}"
    )


def test_negative_control_multiline_concat_escape_must_redden(sandbox: Path):
    """⑩' **Codex round-3 HIGH-2** —— 相邻字面量跨行拼接。

    `P = ("/tmp/cls-exam/"` + 下一行 `"../x")` 是合法 Python 隐式拼接; 物理行上
    `/tmp` 与 `..` 不同行 ⇒ 行级判据失明, token 又在引号处截断 ⇒ 越界也看不见。
    逻辑行合并(行尾闭引号 + 次行同引号开头)后可疑行判据红。
    """
    f = sandbox / "skills" / "start-exam-board" / "SKILL.md"
    text = f.read_text(encoding="utf-8")
    swapped = text.replace(
        'P = "/tmp/cls-exam/exam-candidates.json"',
        'P = ("/tmp/cls-exam/"\n     "../exam-candidates.json")',
        1,
    )
    assert swapped != text, "预置失败: 副本里找不到 P = 赋值行"
    f.write_text(swapped, encoding="utf-8")

    assert not check_body(sandbox, _merged_body_baseline()), "前提: 计数判据放行(等计数替换)"

    # ⛔ r4 MEDIUM-4 的归因整改: 本替换会把 :577 挤到 :578, **行号基线无论判据在不在
    # 都会红** ⇒ 只断言「可疑行报红」考不出解析层是否在场(不承重)。改为对**越界判据**
    # 发问, 并要求新增项里出现命名空间片段。
    # v3 下这段 fence 是 bash 块 ⇒ 整块 ast 解析失败 ⇒ 逐行降级, `shlex` 把
    # `("/tmp/cls-exam/"` 切成一个词, 其 normpath 越出命名空间 ⇒ 越界集合改变。
    # 归因干净: 解析层(ast / shlex 两条路)都不在时, 这里得到的就是原基线 ⇒ 立刻红。
    esc = check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)
    assert any("start-exam-board" in p and "新增=" in p and "/tmp/cls-exam" in p for p in esc), (
        f"跨行拼接必须改变越界集合(新增含 /tmp/cls-exam 的候选), 实得: {esc}"
    )
    # 可疑行同样报红(冗余的第二道)—— 但它单独不足以证明解析层在场, 见上方注释。
    assert check_suspicious_tmp_lines(sandbox, SUSPICIOUS_TMP_LINES_BASELINE), "可疑行判据也应报红"


@pytest.mark.parametrize(
    "line",
    [
        'P="/tmp/cls-exam/$1"',
        'REL=../x\nP="/tmp/cls-exam/"$REL',
    ],
)
def test_negative_control_positional_and_outer_quote_vars_must_redden(sandbox: Path, line: str):
    """⑩'' **Codex round-3 MEDIUM-3** —— 位置参数 `$1` 与引号外拼接 `$REL`。

    两者都是「运行期才知道落点」的形态: `$1` 是位置参数; 引号外拼接在 token 的引号
    处截断, 原变量展开正则够不到。r3 起可疑行触发放宽到**行内任意 `$`** ⇒ 都要登记。
    """
    _append_body(sandbox, "exam-quick", line)
    problems = check_suspicious_tmp_lines(sandbox, SUSPICIOUS_TMP_LINES_BASELINE)
    joined = "\n".join(problems)
    assert any("exam-quick" in p and "[可疑行]" in p for p in problems), f"含 `$` 的 /tmp 行必须登记, 实得: {joined}"


@pytest.mark.parametrize(
    "replacement,why",
    [
        # r5 HIGH-2: 三引号 / 源码级转义 / shell 单引号内反斜杠不转义
        ('P = """/var/cache"/tmp/cls-exam/x.json"""', "r5 HIGH-2 三引号: ast 还原真值"),
        (r'P = "/tmp/cls-exam/\x2e\x2e/x.json"', "r5 HIGH-2 \\x2e 转义: ast 还原成 .."),
        # r5 HIGH-3: 字符串前缀与显式 + 阻断手写拼接
        ('P = ("/tmp/cls-exam/" r"." "./x")', "r5 HIGH-3 r 前缀: ast 在解析期折叠隐式拼接"),
        ('P = ("/tmp/cls-exam/" + "." "./x")', "r5 HIGH-3 显式 +: _fold_str 折叠常量链"),
    ],
)
def test_negative_control_r5_parser_class_escapes_must_redden(sandbox: Path, replacement: str, why: str):
    """⑪ **Codex round-5 HIGH-1/2/3** —— 手写切分器追不上语言语义的那一类。

    这些形态在 v2(手写字面量扫描 + 保守拼组)下**全部放行**: 三引号被错误闭合、
    `\x2e` 停留在源码形态、`r` 前缀阻断间隙匹配、独立参数被拼组遮蔽。
    v3 改走真解析(`ast` 整块 → 逐行 `ast` → `shlex`)后逐个封住。

    ⛔ 用**等计数替换**: 九项计数纹丝不动 ⇒ 计数判据放行 ⇒ 红只可能来自越界判据,
    归因干净。
    """
    _swap_in_start_exam_board(sandbox, 'P = "/tmp/cls-exam/exam-candidates.json"', replacement)

    assert not check_body(sandbox, _merged_body_baseline()), f"前提: 计数判据放行({why})"
    esc = check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)
    assert any("start-exam-board" in p and "[越界]" in p for p in esc), f"{why} —— 越界判据必须抓到, 实得: {esc}"


def test_r5_high1_independent_args_must_not_mask_each_other():
    """⑪ **Codex round-5 HIGH-1** —— 独立参数不得被拼组互相遮蔽。

    v2 把 fence 行内相邻字面量做「保守拼组」, 于是
    `cp "/tmp/cls-exam/a" "/var/cache(/tmp/cls-exam/x"` 的两个**独立参数**被连成
    `/tmp/cls-exam/a/var/cache(/tmp/cls-exam/x` —— 该串仍以命名空间开头 ⇒ 放行,
    第二个参数的真实越界被**掩盖**。这是 v2 引入的回归(比不拼更糟)。

    v3 走 `shlex.split`(整块非 Python ⇒ 逐行降级), 得到三个真词, 各自判 ⇒ 第二个
    参数的 normpath 是 `/var/cache(/tmp/cls-exam/x`, 越出命名空间 ⇒ 抓到。

    ⛔ 直接对纯函数发问: 它考的是「独立参数各自判」这一语义, 与副本文件无关;
    放进副本反而会因为多了一个 `/tmp/cls-exam/` 而改变计数, 让归因不干净。
    """
    text = '```sh\ncp "/tmp/cls-exam/a" "/var/cache(/tmp/cls-exam/x"\n```'
    escapes = escaping_tmp_paths(text)
    norms = [n for _c, n in escapes]
    assert "fence:/var/cache(/tmp/cls-exam/x" in norms, (
        f"第二个独立参数的越界必须被单独抓到(不得被第一个参数拼组遮蔽), 实得: {escapes}"
    )
    # 验伪锚: 合规的第一个参数不该被误报 —— 否则「抓到」可能只是整体误报
    assert (
        "fence:/tmp/cls-exam/a" not in norms
    )  # r9 LOW-1: 前缀漏更新会让这条空跑, f"命名空间内的第一个参数不应被判越界: {escapes}"


def test_negative_control_r5_tilde_fence_must_redden(sandbox: Path):
    """⑪' **Codex round-5 HIGH-4** —— `~~~` 围栏。

    v2 的 fence 状态机只认 ```; 用合法的 `~~~python` 标记, 整块被当散文处理 ⇒
    字面量与拼组两层保护同时关闭。v3 的 `_fence_RE` 认 ``` 与 ~~~ 两种标记。
    """
    f = sandbox / "skills" / "start-exam-board" / "SKILL.md"
    text = f.read_text(encoding="utf-8")
    swapped = text + '\n\n~~~python\nP = "/var/cache(/tmp/cls-exam/x"\n~~~\n'
    f.write_text(swapped, encoding="utf-8")

    esc = check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)
    assert any("start-exam-board" in p and "/var/cache(" in p for p in esc), (
        f"~~~ 围栏内的冒充路径必须被越界判据抓到, 实得: {esc}"
    )


#: Codex round-7 / round-8 各类 HIGH 的形态表。每行 `(坏形态, 安全对照, 指名判据, 说明)`。
#: ⛔ 为什么是**纯函数**而不是 sandbox 三段归因: 这六类里五类要么改变 fence 结构、
#: 要么改变物理行数, 两者都会连带搬动 `SUSPICIOUS_TMP_LINES_BASELINE` 的 `[577]`,
#: 于是「② 其余判据都看不见」这个前提根本不成立(⑰ 那条负控实测踩到过)。
#: 对纯函数发问 + 每行配一个**安全对照**(必须全绿), 归因反而干净: 红来自形态本身,
#: 不来自「文件被改动了」。
_R7_HIGH_FORMS: list[tuple[str, str, str, str]] = [
    (
        '执行 ``cp "/tmp/cls-exam/"`printf .`"./x" out``',
        '执行 ``cp "/tmp/cls-exam/x" out``',
        "不透明记号",
        "HIGH-1 双反引号 code span 内的命令替换 —— 单反引号正则提取不出这种 span",
    ),
    (
        '~~~python title=~~~\nP = "/tmp/cls-exam/" + "." * 2 + "/x"\n~~~',
        '~~~python title=~~~\nP = "/tmp/cls-exam/x"\n~~~',
        "动态拼接",
        "HIGH-2a `~~~` 的 info string 允许含 `~`(CommonMark) —— 行内 span 判定只该对反引号生效",
    ),
    (
        '```python\nA = 1\n```not-a-close\nP = "/tmp/cls-exam/" + "." * 2 + "/x"\n```',
        '```python\nA = 1\n```not-a-close\nP = "/tmp/cls-exam/x"\n```',
        "动态拼接",
        "HIGH-2b 闭合 fence 行不得带 info string(CommonMark) —— 否则后面的真代码块被当散文",
    ),
    (
        '- ```python\n  P = "/tmp/cls-exam/" + "." * 2 + "/x"\n  ```',
        '- ```python\n  P = "/tmp/cls-exam/x"\n  ```',
        "动态拼接",
        "HIGH-2c 列表项内的 fence 是合法 markdown —— `^\\s*` 认不出 `- ```python`",
    ),
    (
        # ⛔ r8 LOW: 必须裹在 heredoc 里。纯 python fence 会走「整块 ast.parse 成功」
        # 那条路, 整个绕开 `_parse_units()` —— 实测把窗口限回 8 行, 那一版断言照样过。
        '```sh\npython3 - <<\'PYEOF\'\nP = (\n    "/tmp/cls-exam/"\n    + "."\n    + "."\n    + "/"\n    + "x"\n    + "."\n    + "json"\n)\nPYEOF\n```',
        '```sh\npython3 - <<\'PYEOF\'\nP = (\n    "/tmp/cls-exam/"\n    + "a"\n    + "b"\n    + "/"\n    + "x"\n    + "."\n    + "json"\n)\nPYEOF\n```',
        "越界",
        "HIGH-3 九行括号表达式（heredoc 内）—— 固定 8 行窗口下退回逐行, 拼接关系永久消失",
    ),
    (
        '```python\nP = "/var/cache"\nP += "/tmp/cls-exam/x"\n```',
        '```python\nP = "/var/cache"\nP = "/tmp/cls-exam/x"\n```',
        "动态拼接",
        "HIGH-4 `AugAssign` 的 `+=` 本身就是拼接 —— 抵达它证明不了「纯静态字面量」",
    ),
    (
        "```sh\nP='\n/tmp/cls-exam/x'\n```",
        "```sh\nP='/tmp/cls-exam/x'\n# 占位\n```",
        "越界",
        "HIGH-5 合法 shell 跨行引号 —— 逐行看两边都因引号未闭而弃权, 无反斜杠故第八条也不触发",
    ),
    (
        "```sh\nP='" + "\\\n" * 7 + "/tmp/cls-exam/x'\n```",
        "```sh\nP='/tmp/cls-exam/x'\n```",
        "不透明记号",
        "HIGH-6 七条反斜杠续行 —— 链长上限 6 把记号与 `/tmp` 切进不同组(边界呈模 7 锯齿)",
    ),
    # ── Codex round-12 六类 HIGH + 1 MEDIUM ───────────────────────────────
    (
        '```sh\npython3 - <<\'PYEOF\'\nif False:\n    pass\nelif ("/tmp/cls-exam/" +\n    ".." + "/x") == q:\n    pass\nPYEOF\n```',
        '```sh\npython3 - <<\'PYEOF\'\nif False:\n    pass\nelif ("/tmp/cls-exam/" +\n    "a" + "/x") == q:\n    pass\nPYEOF\n```',
        "越界",
        "r12HIGH-1 **多行**的 elif 头 —— r11 的「chunk+该行+占位 pass」探针拒绝它",
    ),
    (
        '```sh\npython3 - <<\'PYEOF\'\nif False:\n    pass\n# c\nelif ("/tmp/cls-exam/" "../x") == q:\n    pass\nPYEOF\n```',
        '```sh\npython3 - <<\'PYEOF\'\nif False:\n    pass\n# c\nelif ("/tmp/cls-exam/" "x") == q:\n    pass\nPYEOF\n```',
        "越界",
        "r12HIGH-1b 同级**注释**同样不结束复合语句",
    ),
    (
        '执行 P="/var/cache""/tmp/cls-exam/"\xa0`printf a`\xa0',
        '执行 P="/tmp/cls-exam/z"',
        "不透明记号",
        "r12HIGH-2 NBSP(U+00A0)/U+3000 的 isspace() 是 True, 但 shell 把它们留在词内",
    ),
    (
        '执行 P="/var/cache /tmp/cls-exam/ "`printf a`',
        '执行 P="/tmp/cls-exam/w"',
        "不透明记号",
        'r12HIGH-2b 引号内的空格不是词边界 —— `line.split(" ")` 会错拆',
    ),
    (
        "- 段尾 `未闭合\n- 执行 `/var/cache(\n  /tmp/cls-exam/x`",
        "- 段尾 `未闭合\n- 执行 `/tmp/cls-exam/x\n  `",
        "越界",
        "r12HIGH-3 相邻**列表项**各有独立 span; 且块边界行本身是新块首行, 不能丢",
    ),
    (
        '    ```python\nexample\n```\nP = "/tmp/cls-exam/" + "." * 2 + "/x"\n```',
        '    ```python\nexample\n```\nP = "/tmp/cls-exam/x"\n```',
        "动态拼接",
        "r12HIGH-4 无容器前缀时缩进 >=4 是**缩进代码块**, 不开 fence",
    ),
    (
        '```sh\npython3 - <<\'PYEOF\'\nP = "/tmp/cls-exam/x"; P: str = "/var/cache/x"\nPYEOF\n```',
        '```sh\npython3 - <<\'PYEOF\'\nP = "/tmp/cls-exam/x"; Q: str = "/var/cache/x"\nPYEOF\n```',
        "动态拼接",
        "r12HIGH-5 `AnnAssign` 也是赋值 —— 重复赋值计数要含它",
    ),
    (
        '越界：P="/var/cache""/tmp/cls-exam/x"',
        '越界：P="/tmp/cls-exam/x"',
        "不透明记号",
        "r12HIGH-6 散文里的**相邻引号拼接** —— 无反引号/反斜杠/`..`/`$`, 原先五条全静默",
    ),
    (
        '```sh\nunset OTHER CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"\n```',
        '```sh\nunset -f CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"\n```',
        "URL 覆盖",
        "r12MEDIUM `unset` 多变量算清空; 而 `unset -f` 只删同名函数, 不算(否则误报)",
    ),
    # ── Codex round-11 九类 HIGH + 1 MEDIUM ───────────────────────────────
    (
        '```sh\npython3 - <<\'PYEOF\'\nif True:\n    if False:\n        pass\n    elif ("/tmp/cls-exam/" "." "./x") == q:\n        pass\nPYEOF\n```',
        '```sh\npython3 - <<\'PYEOF\'\nif True:\n    if False:\n        pass\n    elif ("/tmp/cls-exam/" "a" "/x") == q:\n        pass\nPYEOF\n```',
        "越界",
        "r11HIGH-1 嵌套的续接子句 —— 缩进比外层深, 猜缩进的三版都栽在这里",
    ),
    (
        '>  > ```python\n>  > P = "/tmp/cls-exam/" + "." * 2 + "/x"\n>  > ```',
        '>  > ```python\n>  > P = "/tmp/cls-exam/x"\n>  > ```',
        "动态拼接",
        "r11HIGH-2 双层引用 marker 之间可以有额外空白, 正则一次剥不掉",
    ),
    (
        "段尾 `未闭合\n# 标题\n执行 `/var/cache(\n/tmp/cls-exam/x`",
        "段尾 `未闭合\n# 标题\n执行 `/tmp/cls-exam/x\n`",
        "越界",
        "r11HIGH-4 ATX 标题也是块边界 —— 只断空行不够",
    ),
    (
        '``` text `label`\n说明\n```\nP = "/tmp/cls-exam/" + "." * 2 + "/x"\n```',
        '``` text `label`\n说明\n```\nP = "/tmp/cls-exam/x"\n```',
        "动态拼接",
        "r11HIGH-5a 反引号 fence 的 info string 不得含任何反引号(CommonMark)",
    ),
    (
        '```python\nA = 1\n    ```\nP = "/tmp/cls-exam/" + "." * 2 + "/x"\n```',
        '```python\nA = 1\n    ```\nP = "/tmp/cls-exam/x"\n```',
        "动态拼接",
        "r11HIGH-5b closing 缩进最多比 opening 多 3 空格 —— 四空格的那行是内容",
    ),
    (
        '执行 P="/var/cache""/tmp/cls-exam/"，`printf a`，',
        '执行 P="/tmp/cls-exam/z"',
        "不透明记号",
        "r11HIGH-6 中文句读同样能属于 shell 词 —— 分隔符表最终清空, 只认真空白",
    ),
    (
        '```sh\npython3 - <<\'PYEOF\'\nP = b"/t" b"mp/cls-exam/" + b"." * 2 + b"/x"\nPYEOF\n```',
        "```sh\npython3 - <<'PYEOF'\nP = b\"/tmp/cls-exam/x\"\nPYEOF\n```",
        "动态拼接",
        "r11HIGH-7 bytes 不进 _py_strings() ⇒ 预筛整类挡掉(bytes 的任何拼接都判动态, 是保守误报方向)",
    ),
    (
        '```sh\npython3 - <<\'PYEOF\'\nP = ("/t" + "mp/cls-exam/") + "." * 2 + "/x"\nPYEOF\n```',
        '```sh\npython3 - <<\'PYEOF\'\nP = ("/t" + "mp/cls-exam/") + "a" + "/x"\nPYEOF\n```',
        "动态拼接",
        "r11HIGH-8 起点不能只取叶常量 —— 折叠后才出现 /tmp 的子树也要作起点",
    ),
    (
        '```sh\npython3 - <<\'PYEOF\'\nP = "/tmp/cls-exam/x"; P = "/var/cache/x"\nPYEOF\n```',
        "```sh\npython3 - <<'PYEOF'\nP = \"/tmp/cls-exam/x\"\nPYEOF\n```",
        "动态拼接",
        "r11HIGH-9 同单元内对同一名字重复赋值 —— 最终值静态确定, 合规常量还在",
    ),
    (
        '```sh\nunset -v CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"\n```',
        '```sh\ncurl "${CLS_BACKEND_URL:-http://localhost:8011}/x"\n```',
        "URL 覆盖",
        "r11MEDIUM unset 的选项与引号形态同样确定性清空配置",
    ),
    # ── Codex round-10 六类 HIGH + 1 MEDIUM ───────────────────────────────
    (
        "`p ```/var/cache(/tmp/cls-exam/x```",
        "`p ```/tmp/cls-exam/x```",
        "越界",
        "r10HIGH-1 closing run 必须**恰好**等长 —— 只查右边界会用长串的尾部提前闭合",
    ),
    (
        '> ```python\n> def f():\n>     P = "/tmp/cls-exam/" + "." * 2 + "/x"\n>     return P\n> ```',
        '> ```python\n> def f():\n>     P = "/tmp/cls-exam/x"\n>     return P\n> ```',
        "动态拼接",
        "r10HIGH-2 剥引用标记后只吃**一个**空格 —— `>\\s*` 会把 Python 的真实缩进一起删掉",
    ),
    (
        "段尾 `未闭合\n\n执行 `/var/cache(\n/tmp/cls-exam/x`",
        "段尾 `未闭合\n\n执行 `/tmp/cls-exam/x\n`",
        "越界",
        "r10HIGH-4 空行是 markdown 块边界 —— 不断段则前段的未闭反引号夺走后段的 opening",
    ),
    (
        '执行 P="/var/cache""/tmp/cls-exam/"*`printf a`*',
        '执行 P="/tmp/cls-exam/x"',
        "不透明记号",
        "r10HIGH-5a `*` 也能属于合法 shell 词 —— 分隔符表里多一个字符就是多一条放行",
    ),
    (
        '执行 P="/var/cache""/tmp/cls-exam/"“`printf a`”',
        '执行 P="/tmp/cls-exam/y"',
        "不透明记号",
        "r10HIGH-5b 中文引号同理 —— r9 为消误报把它们加进表, 反而开了一条放行",
    ),
    (
        '```python\nP = "/t" "mp/cls-exam/" + "." * 2 + "/x"\n```',
        '```python\nP = "/t" "mp/cls-exam/" + "a" + "/x"\n```',
        "动态拼接",
        "r10HIGH-6 预筛不能只看源码字面 —— 隐式拼接后才出现 `/tmp`, `ast` 折得出、预筛挡掉了",
    ),
    (
        '```sh\nunset CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/api/v1/ping"\n```',
        '```sh\ncurl "${CLS_BACKEND_URL:-http://localhost:8011}/api/v1/ping"\n```',
        "URL 覆盖",
        "r10MEDIUM `unset` 与赋值同根 —— 都确定性清空配置、让缺省形态无条件生效",
    ),
    # ── Codex round-9 五类 HIGH + 1 MEDIUM ────────────────────────────────
    (
        '```sh\npython3 - <<\'PYEOF\'\nif False:\n    pass\n    pass\nelif ("/tmp/cls-exam/" "../x") == q:\n    pass\nPYEOF\n```',
        '```sh\npython3 - <<\'PYEOF\'\nif False:\n    pass\n    pass\nelif ("/tmp/cls-exam/" "x") == q:\n    pass\nPYEOF\n```',
        "越界",
        "r9HIGH-1a/r10HIGH-3 续接子句 —— `elif` 头里的表达式**必须依附它**才能解析; 分支内多行时只看紧邻下一行不够",
    ),
    (
        "```sh\npython3 - <<'PYEOF'\nP = (\n    \"/tmp/cls-exam/\"\n"
        + "    # c\n" * 197
        + '    + "." + "./x"\n)\nPYEOF\n```',
        "```sh\npython3 - <<'PYEOF'\nP = (\n    \"/tmp/cls-exam/\"\n"
        + "    # c\n" * 197
        + '    + "a" + "/x"\n)\nPYEOF\n```',
        "越界",
        "r9HIGH-1b 201 行 —— 固定行数上限只是把缺口挪个位置(r8 已报, r8 整改时漏修)",
    ),
    (
        "执行 `/var/cache(/tmp/cls-exam/x\\`",
        "执行 `/tmp/cls-exam/x\\`",
        "越界",
        "r9HIGH-2 掩码毁 span 闭合 —— span **内部**的反斜杠是普通字符, closing 不看转义",
    ),
    (
        '```python\nA = 1\n> ```\nP = "/tmp/cls-exam/" + "." * 2 + "/x"\n```',
        '```python\nA = 1\n> ```\nP = "/tmp/cls-exam/x"\n```',
        "动态拼接",
        "r9HIGH-3a closing 的引用深度必须等于 opening 的 —— 否则 `> ``` ` 提前闭合",
    ),
    (
        '- > ```python\n  > P = "/tmp/cls-exam/" + "." * 2 + "/x"\n  > ```',
        '- > ```python\n  > P = "/tmp/cls-exam/x"\n  > ```',
        "动态拼接",
        "r9HIGH-3b 列表→引用嵌套 —— body 的容器前缀要整体剥, 只剥 `>` 不够",
    ),
    (
        '```python\n"/tmp/cls-exam/x"; P = "/etc/passwd"\n```',
        '```python\nP = "/tmp/cls-exam/x"\n```',
        "动态拼接",
        "r9HIGH-4 常量与实际赋值脱钩 —— `Expr` 不能算安全停止点",
    ),
    (
        '执行 cp "/var/cache""/tmp/cls-exam/"_`printf a`_ out',
        '执行 cp "/tmp/cls-exam/x" out',
        "不透明记号",
        "r9HIGH-5a `_` `:` 也是合法 shell 词的一部分 —— 分隔符表不能含 ASCII 标点",
    ),
    (
        '执行 P="/tmp/cls-exam/"\\.\\./x',
        '执行 P="/tmp/cls-exam/x"',
        "不透明记号",
        "r9HIGH-5b 散文里裸写、连反引号都没有 —— 含 `/tmp` 的词里带反斜杠即登记",
    ),
    (
        "执行 `/var/cache(\n/tmp/cls-exam/x`",
        "执行 `/tmp/cls-exam/x\n`",
        "越界",
        "r9HIGH-5c 跨物理行的 code span —— 散文要先并成段再找 span",
    ),
    (
        '```sh\nCLS_BACKEND_URL=; curl "${CLS_BACKEND_URL:-http://localhost:8011}/api/v1/ping"\n```',
        '```sh\ncurl "${CLS_BACKEND_URL:-http://localhost:8011}/api/v1/ping"\n```',
        "URL 覆盖",
        "r9MEDIUM-2 给变量赋值把缺省形态架空 —— 九项计数与五集合全不变",
    ),
    # ── Codex round-8 五类 HIGH ──────────────────────────────────────────
    (
        '```sh\npython3 - <<\'PYEOF\'\nP = ( # )\n    "/tmp/cls-exam/"\n    + "." + "./x"\n)\nPYEOF\n```',
        '```sh\npython3 - <<\'PYEOF\'\nP = ( # )\n    "/tmp/cls-exam/"\n    + "a" + "/x"\n)\nPYEOF\n```',
        "越界",
        "r8HIGH-1 注释里的 `)` —— 纯文本数括号会把单元边界**定短**(漏检方向)",
    ),
    (
        "执行 \\```/var/cache(/tmp/cls-exam/x``",
        "执行 \\```/tmp/cls-exam/x``",
        "越界",
        "r8HIGH-2 转义的 opening 反引号不参与 run —— 不掩码就整个 span 提不出来",
    ),
    (
        '```python\nA = 1\n- ```\nP = "/tmp/cls-exam/" + "." * 2 + "/x"\n```',
        '```python\nA = 1\n- ```\nP = "/tmp/cls-exam/x"\n```',
        "动态拼接",
        "r8HIGH-3a 列表前缀不得用于**闭合** —— 普通 fence 里的 `- ``` ` 是内容行",
    ),
    (
        '> ```python\n> P = "/tmp/cls-exam/" + "." * 2 + "/x"\n> ```',
        '> ```python\n> P = "/tmp/cls-exam/x"\n> ```',
        "动态拼接",
        "r8HIGH-3b 引用块内的 fence —— body 的 `> ` 前缀不剥则 ast/shlex 全解析不了",
    ),
    (
        '```python\nP: "/tmp/cls-exam/x" = "/etc/passwd"\n```',
        '```python\nP: str = "/tmp/cls-exam/x"\n```',
        "动态拼接",
        "r8HIGH-4 `AnnAssign` 的注解不是实际值 —— 抵达它不能一概判「纯静态字面量」",
    ),
    (
        '越界：P="/tmp/cls-exam/"`printf .`"./x"',
        '越界：P="/tmp/cls-exam/x"',
        "不透明记号",
        "r8HIGH-5a 散文里裸写的 shell —— 唯一能提的 span 是 `printf .`(不含 /tmp)",
    ),
    (
        '执行 ``cp\n"/tmp/cls-exam/"`printf .`"./x" out``',
        '执行 ``cp\n"/tmp/cls-exam/x" out``',
        "不透明记号",
        "r8HIGH-5b 跨物理行的 code span —— 散文按物理行切, 正则加 DOTALL 也不够",
    ),
]


@pytest.mark.parametrize(
    "bad,safe,judge,why", _R7_HIGH_FORMS, ids=[w.split(" ")[0] for _b, _s, _j, w in _R7_HIGH_FORMS]
)
def test_r7_high_forms_are_caught_and_safe_forms_are_not(bad: str, safe: str, judge: str, why: str):
    """⑲ **Codex round-7 六类 HIGH** —— 坏形态被**指名的那条判据**红, 安全对照不被它红。

    ⛔ 断言绑定的是「被哪一层拒的」, 不是「有人拒了」: 越界判据把**整个 backtick span
    当路径**(已登记的保守方向, 基线里 `Bash: mkdir -p /tmp/cls-exam` 就是这类), 所以
    HIGH-1 的安全对照也会被它红 —— 若只问「有没有人红」, 这一行就会用一个**错误的
    理由**通过。指名之后, 红绿之差只能归给被考的那个机制。

    同时仍断言坏形态「至少有人红」(整体有效性)、安全对照不被指名判据红(不是见
    `/tmp` 就红)。安全对照与坏形态**结构相同、只差那一处**。
    """
    judges = {
        "越界": escaping_tmp_paths,
        "可疑行": suspicious_tmp_lines,
        "动态拼接": dynamic_tmp_join_lines,
        "不透明记号": opaque_tmp_lines,
        "URL 覆盖": url_default_overridden_lines,
    }
    assert judges[judge](bad), f"{why} —— 坏形态未被**{judge}**判据抓到: {bad!r}"
    assert any(fn(bad) for fn in judges.values()), f"{why} —— 坏形态八条判据全盲: {bad!r}"
    assert not judges[judge](safe), f"{why} —— 安全对照被**{judge}**误报, 说明红不是来自那处差异: {safe!r}"


def test_fence_close_requires_same_char_and_width():
    """⑪'' **Codex round-5 HIGH-4 后半** —— 闭合必须**同字符**且**长度 >= 开启**。

    直接对纯函数发问(不经副本), 因为它考的是 `_fence_blocks` 的闭合规则本身。
    ⛔ r7 LOW-1 两处整改: ① 原先只考「长度」那一半 —— 在内存删掉**同字符**判断后
    该用例照样全过, 那一半不承重; 现在补上用 `~~~` 开、``` 试图闭合的用例。
    ② 去掉未使用的 `sandbox` 参数 —— 它什么都没考, 却每次触发一次整树复制。
    """
    # (a) 长度那一半: 四反引号块里的三反引号内容行不得切换状态
    text = '````md\n```\nP = "/var/cache(/tmp/cls-exam/x"\n```\n````\n'
    blocks = _fence_blocks(text)
    fenced = [b for b in blocks if b[2]]
    assert len(fenced) == 1, f"四反引号块应是**一个** fence, 内层三反引号不切换状态, 实得: {blocks}"
    assert any("/var/cache(" in line for line in fenced[0][1]), f"内层内容应留在同一块里: {fenced[0][1]}"
    assert any("/var/cache(" in c for c, _n in escaping_tmp_paths(text)), escaping_tmp_paths(text)

    # (b) 同字符那一半: ``` 不得闭合 ~~~ 开启的块 —— 删掉同字符判断这条就红
    mixed = '~~~md\nA\n```\nP = "/tmp/cls-exam/../y"\n~~~\n'
    mixed_fenced = [b for b in _fence_blocks(mixed) if b[2]]
    assert len(mixed_fenced) == 1, f"~~~ 块应只有一个, ``` 不闭合它, 实得: {_fence_blocks(mixed)}"
    assert any(line.strip() == "```" for line in mixed_fenced[0][1]), (
        f"``` 应作为**内容行**留在 ~~~ 块里(否则同字符判断失效): {mixed_fenced[0][1]}"
    )


@pytest.mark.parametrize(
    "replacement,why",
    [
        ('P = "/tmp/cls-exam/" + PARENT + "/x"', "变量拼接: ast 折不了非常量"),
        ('P = "/tmp/cls-exam/%s/x" % updir', "% 格式化 + 变量"),
        ('P = "/tmp/cls-exam/{}/x".format(updir)', ".format() + 变量"),
        # ⛔ 带尾斜杠: 无尾斜杠会让 tmp_ns 掉 1 而破坏「等计数」前提, 归因就不干净了
        ('P = os.path.join("/tmp/cls-exam/", updir, "x")', "os.path.join + 变量"),
        ('P = f"/tmp/cls-exam/{updir}/x"', "f-string 插值"),
    ],
)
def test_negative_control_dynamic_join_must_be_registered(sandbox: Path, replacement: str, why: str):
    """⑫ **第六条判据** —— 前五条全盲的那一类: 把落点藏进变量。

    这些形态没有 `..` 的字面证据、没有 `$`、`ast` 也折不出常量 ⇒ 越界判据只看到
    合规的 `/tmp/cls-exam/` 片段, 可疑行判据两个触发词都不命中, 计数判据更是不变。
    **五条判据一起放行** —— 这是本卡自查(非 Codex 报)找到的残余边界。

    第六条判据从 `ast` 层面问「有没有动态参与」, 命中即要求登记(不假装能算出落点)。

    ⛔ 三段归因: ① 计数判据放行(等计数替换) ② 越界与可疑行**都看不见**
    (证明这条负控考的确实是第六条, 不是被别人代打红) ③ 第六条报红。
    """
    _swap_in_start_exam_board(sandbox, 'P = "/tmp/cls-exam/exam-candidates.json"', replacement)

    assert not check_body(sandbox, _merged_body_baseline()), f"① 前提: 计数判据放行({why})"
    assert not check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE), (
        f"② 前提: 越界判据看不见({why}) —— 若它看得见, 这条负控考错了对象"
    )
    assert not check_suspicious_tmp_lines(sandbox, SUSPICIOUS_TMP_LINES_BASELINE), f"② 前提: 可疑行判据也看不见({why})"
    problems = check_dynamic_tmp_joins(sandbox, DYNAMIC_TMP_JOIN_BASELINE)
    joined = "\n".join(problems)
    assert any("start-exam-board" in p and "[动态拼接]" in p for p in problems), (
        f"③ {why} 必须被第六条判据要求登记, 实得: {joined}"
    )


# ⛔ 第八条判据(不透明记号)负控 —— Codex round-6 HIGH-1/2/3 的同因收口。
#: 等计数替换: 两种形态的 `/tmp` 与 `/tmp/cls-exam/` 各 1, 九项向量一字不动。
@pytest.mark.parametrize(
    "replacement,why",
    [
        (
            'P = "/tmp/cls-exam/`printf .`./exam-candidates.json"',
            "r6 HIGH-1: shell 命令替换 —— `ast` 把整串当常量读, 但真跑起来 `printf .` 会展开",
        ),
        (
            'P = "/tmp/cls-exam/\\u002e\\u002e\\/exam-candidates.json"',
            "r6 HIGH-2: JSON 语义 —— `\\/` 在 JSON 是 `/`, Python 读成两个字符, 谁对取决于读它的语言",
        ),
    ],
)
def test_negative_control_opaque_tmp_must_be_registered(sandbox: Path, replacement: str, why: str):
    """⑬ **第八条判据** —— 前七条全盲的那一类: 字面量的**含义**取决于读它的语言。

    v3 的真解析解决了「字面量怎么写」, 这两例暴露的是「字面量被谁读」: `ast` 能
    parse 出一个 `Constant`, 但那个值只在 Python 语义下成立。第八条不猜哪门语言,
    只认记号(反引号 / 反斜杠)并要求登记。

    ⛔ 三段归因: ① 计数判据放行(等计数替换) ② 越界/可疑行/动态拼接/散文四条**都
    看不见**(证明考的确实是第八条) ③ 第八条报红。
    """
    _swap_in_start_exam_board(sandbox, 'P = "/tmp/cls-exam/exam-candidates.json"', replacement)

    assert not check_body(sandbox, _merged_body_baseline()), f"① 前提: 计数判据放行({why})"
    for label, blind in (
        ("越界", check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)),
        ("可疑行", check_suspicious_tmp_lines(sandbox, SUSPICIOUS_TMP_LINES_BASELINE)),
        ("动态拼接", check_dynamic_tmp_joins(sandbox, DYNAMIC_TMP_JOIN_BASELINE)),
        ("散文父目录", check_parent_dir_prose(sandbox, PARENT_DIR_PROSE_BASELINE)),
    ):
        assert not blind, f"② 前提: {label}判据看不见({why}) —— 若它看得见, 这条负控考错了对象"

    problems = check_opaque_tmp(sandbox, OPAQUE_TMP_BASELINE)
    assert any("start-exam-board" in x and "[不透明记号]" in x for x in problems), (
        f"③ {why} 必须被第八条判据要求登记, 实得: {chr(10).join(problems)}"
    )


# ⛔ 语法单元(累积窗口)负控 —— 2026-09-09 一次 50-agent 独立复核实测出的根因。
#: **等行数**替换(两行换两行), 后续行号不移动 ⇒ 可疑行基线 `[577]` 不受牵连。
@pytest.mark.parametrize(
    "replacement,why",
    [
        (
            'P = os.path.join(\n    "/tmp/cls-exam/", updir, "x"); p = json.load(open(P, encoding="utf-8"))',
            "开括号换行: `black` 折长行的自然产物, 第一行不完整、第二行括号不平衡",
        ),
        (
            'P = os.path.join(\n    "/tmp/cls-exam/", f"{updir}", "x"); p = json.load(open(P, encoding="utf-8"))',
            "开括号换行 + f-string: 连第六条判据认的 `JoinedStr` 也躲在跨行结构里",
        ),
    ],
)
def test_negative_control_open_paren_continuation_must_be_registered(sandbox: Path, replacement: str, why: str):
    """⑮ **逐物理行降级的整类盲区** —— 跨物理行的语法结构。

    本仓每份 SKILL.md 的 python 都装在 ``python3 - <<'PYEOF'`` heredoc 里 ⇒ 整块
    `ast.parse` **恒失败** ⇒ 恒走降级。降级若按**物理行**做, 则任何跨行语法结构
    整类失明: 开括号换行的两行, 第一行不完整、第二行括号不平衡, `ast` 与 `shlex`
    双双弃权, 只剩裸 token 看到合规的 `/tmp/cls-exam/` 前缀。

    这一类**不带反斜杠也不带反引号**, 所以第八条也看不见 —— 只能靠 `_parse_units`
    按语法单元(累积窗口)重组后再 parse。

    ⛔ 三段归因: ① 计数判据放行(等计数**且等行数**替换) ② 越界/可疑行/不透明三条
    **都看不见**(证明考的确实是语法单元重组) ③ 第六条判据(动态拼接)报红。
    """
    _swap_in_start_exam_board(
        sandbox,
        'P = "/tmp/cls-exam/exam-candidates.json"\np = json.load(open(P, encoding="utf-8"))',
        replacement,
    )

    assert not check_body(sandbox, _merged_body_baseline()), f"① 前提: 计数判据放行({why})"
    for label, blind in (
        ("越界", check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)),
        ("可疑行", check_suspicious_tmp_lines(sandbox, SUSPICIOUS_TMP_LINES_BASELINE)),
        ("不透明记号", check_opaque_tmp(sandbox, OPAQUE_TMP_BASELINE)),
    ):
        assert not blind, f"② 前提: {label}判据看不见({why}) —— 若它看得见, 这条负控考错了对象"

    problems = check_dynamic_tmp_joins(sandbox, DYNAMIC_TMP_JOIN_BASELINE)
    assert any("start-exam-board" in x and "[动态拼接]" in x for x in problems), (
        f"③ {why} 必须被第六条判据要求登记, 实得: {chr(10).join(problems)}"
    )


# ⛔ 「表达式选择」类负控 —— 落点不是拼出来的, 是**从几个候选里挑一个**。
#: 这类的越界串(`/etc/passwd`)整个不含 `/tmp`, 越界判据的 `add()` 早退看不见;
#: 也没有反引号/反斜杠, 第八条看不见; 计数纹丝不动(左边那个合规字面量还在)。
@pytest.mark.parametrize(
    "replacement,why",
    [
        ('P = "/tmp/cls-exam/exam-candidates.json" if 0 else "/etc/passwd"', "IfExp: 三元表达式选另一支"),
        ('P = ["/tmp/cls-exam/exam-candidates.json", "/etc/passwd"][1]', "Subscript/List: 下标取另一个"),
        ('P = ("/tmp/cls-exam/exam-candidates.json", "/etc/passwd")[1]', "Subscript/Tuple: 同上, 元组形态"),
        ('P = b"/tmp/cls-exam/" + bytes([46, 46]) + b"/x"', "bytes: 原先 `isinstance(v, str)` 把它整个丢掉"),
    ],
)
def test_negative_control_selective_expression_must_be_registered(sandbox: Path, replacement: str, why: str):
    """⑯ **节点类型白名单的整类盲区** —— 第六条判据口径重写后才拦得住。

    原实现是白名单(`BinOp(+/%)` / `JoinedStr` / `Call`), `IfExp` / `Subscript` /
    `Tuple` / bytes 全在名单外。现在改成取反口径: 从含 `/tmp` 的常量往上走父链,
    只要祖先还能被 `_fold_str()` 完全折成一个字符串就继续; 中途折不出来 ⇒ 登记。
    新的表达式形态默认落进「折不出来」一侧, 不需要有人先想到它。

    ⛔ 三段归因: ① 计数放行 ② 越界/可疑行/不透明三条**都看不见** ③ 第六条报红。
    """
    _swap_in_start_exam_board(sandbox, 'P = "/tmp/cls-exam/exam-candidates.json"', replacement)

    assert not check_body(sandbox, _merged_body_baseline()), f"① 前提: 计数判据放行({why})"
    for label, blind in (
        ("越界", check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)),
        ("可疑行", check_suspicious_tmp_lines(sandbox, SUSPICIOUS_TMP_LINES_BASELINE)),
        ("不透明记号", check_opaque_tmp(sandbox, OPAQUE_TMP_BASELINE)),
    ):
        assert not blind, f"② 前提: {label}判据看不见({why}) —— 若它看得见, 这条负控考错了对象"

    problems = check_dynamic_tmp_joins(sandbox, DYNAMIC_TMP_JOIN_BASELINE)
    assert any("start-exam-board" in x and "[动态拼接]" in x for x in problems), (
        f"③ {why} 必须被第六条判据要求登记, 实得: {chr(10).join(problems)}"
    )


def test_negative_control_path_on_fence_marker_line_must_redden(sandbox: Path):
    r"""⑰ **fence 标记行**上的越界路径 —— 标记行原先整行不进 body ⇒ 对全部集合判据隐形。

    ` ``` P = "/tmp/cls-exam/../x" ` 这一行, markdown 渲染时 info string 那截不显示,
    但它**在文件里**, 而这道门钉的是文件内容。现在标记行按散文产出, 由裸 token 接管。

    ⛔ **归因如实**: 这个形态在整文件里会多开一个 fence, 把后续每个块的内外状态整体
    翻转(实测 `:430`/`:577` 两行随之落进 fence, 第八条也跟着红)。所以这里**不声称**
    「只有越界判据看得见」—— 那种三段归因在这个形态上不成立。改为对**纯函数**发问,
    并带验伪锚: 同一个 fence 结构、标记行上没有路径时必须绿, 证明红来自标记行的内容
    而不是来自 fence 结构本身。
    """
    dirty = '``` P = "/tmp/cls-exam/../exam-candidates.json"\nfoo\n```'
    clean = "```python\nfoo\n```"
    assert escaping_tmp_paths(dirty), "标记行上的越界路径未被越界判据看到"
    assert not escaping_tmp_paths(clean), "验伪锚失效: 标记行不含路径时也报越界 ⇒ 红来自 fence 结构而非标记行内容"
    assert _fence_blocks(dirty)[0] == (1, [dirty.splitlines()[0]], False), (
        f"标记行必须作为散文块产出(否则裸 token 扫不到): {_fence_blocks(dirty)[:1]}"
    )

    # 整文件侧: 只断言「门整体会红」, 不指定是哪一条(见上方归因说明)。
    _swap_in_start_exam_board(
        sandbox,
        'P = "/tmp/cls-exam/exam-candidates.json"',
        '``` P = "/tmp/cls-exam/../exam-candidates.json"',
    )
    assert check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE), "整文件替换后越界判据必须红"


def test_negative_control_hardcoded_port_in_script_reddens_layer3(sandbox: Path):
    """⑱ **层 3 的端口指标** —— 层 2 对 SKILL.md 钉了 8011 两端, 层 3 原先一个都没有。

    口径分叉的后果: 把仓内逐字存在的
    `BACKEND_URL = "http://localhost:8011/api/v1/memory/archive/session"`
    (现位于 `.claude/hooks/session-end-archive.py`, 本卡覆盖面外)搬进任意一份**受覆盖**
    的 scripts, 层 3 原三项计数完全等值 ⇒ 静默通过。补 `p8011_all` / `p8011_ns` /
    `localhost` 三项后必须红; `localhost` 单列是因为端口换成 8012/8000 时 `p8011_*` 是瞎的。
    """
    f = sandbox / "skills" / "board-recap" / "scripts" / "recap_scan.py"
    text = f.read_text(encoding="utf-8")
    f.write_text(
        text.replace(
            "import re\n",
            'import re\n\nBACKEND_URL = "http://localhost:8011/api/v1/memory/archive/session"\n',
            1,
        ),
        encoding="utf-8",
    )
    assert f.read_text(encoding="utf-8") != text, "预置失败: recap_scan.py 里没找到 `import re`"

    problems = check_scripts(sandbox, _merged_scripts_baseline())
    joined = "\n".join(problems)
    assert any("recap_scan.py" in x and "p8011_all" in x for x in problems), joined
    assert any("recap_scan.py" in x and "localhost" in x for x in problems), joined
    assert not any("文件集合漂移" in x for x in problems), f"改内容不该报文件集合漂移: {joined}"


def test_parse_units_splits_by_syntax_not_by_physical_line():
    r"""验伪锚: `_parse_units` 必须真的按语法单元切, 且不得把合规块切出多余候选。

    左: 开括号换行的两行**必须**合成一个单元(否则上面那条负控就是靠别的机制过的);
    右: 树上真实的 heredoc 形态**不得**因累积窗口多出越界候选(否则是误报机器)。
    """
    units = _parse_units(["P = os.path.join(", '    "/tmp/cls-exam/", updir, "x")'])
    assert len(units) == 1 and units[0][2] is not None, f"开括号换行未合成一个语法单元: {units}"

    heredoc = [
        "python3 - <<'PYEOF'",
        "import json, os, sys",
        'P = "/tmp/cls-exam/exam-candidates.json"',
        'p = json.load(open(P, encoding="utf-8"))',
        "PYEOF",
    ]
    assert not escaping_tmp_paths("```bash\n" + "\n".join(heredoc) + "\n```"), (
        "合规 heredoc 被累积窗口拼出了越界候选 —— 那样这条判据只是台误报机器"
    )


def test_opaque_judge_does_not_fire_on_plain_literals():
    """验伪锚: 第八条不得对**没有**反引号/反斜杠的合规写法报红 —— 否则它只是「见 /tmp 就红」。

    左边四例是树上真实出现过的合规形态; 右边两例带记号, 必须红。两侧一起断言,
    这条才同时钉住「不误报」与「真会红」。
    """
    for clean in (
        '```python\nP = "/tmp/cls-exam/exam-candidates.json"\n```',
        "```sh\nmkdir -p /tmp/cls-exam/\n```",
        '```python\nP = ("/tmp/cls-exam/" "exam.json")\n```',
        "不落 `/tmp` 等 vault 外临时文件",  # 散文带 backtick: fence 外不算
    ):
        assert not opaque_tmp_lines(clean), f"合规写法被误判为不透明: {clean!r}"
    for dirty in (
        '```sh\ncp "/tmp/cls-exam/"`printf .`"./x" out\n```',
        '```python\nP = "/tmp/cls-exam/\\x2e\\x2e/x"\n```',
    ):
        assert opaque_tmp_lines(dirty), f"带记号的写法未被抓到: {dirty!r}"


def test_negative_control_parent_dir_prose_must_be_registered(sandbox: Path):
    """⑭ **第七条判据** —— 散文侧的「上一级目录」指令。

    这一类不写 `..`、不进 fence、不动任何计数: 它靠**中文措辞**让执行者自己算出
    父目录。五条路径判据全部只看代码形态, 对散文里的 `上一级目录` 一无所知
    (2026-09-09 用一次 5 路 Workflow 独立找出, 非 Codex 报)。

    ⛔ 三段归因: ① 计数判据放行(等计数替换) ② 越界/可疑行/动态拼接/不透明四条
    **都看不见** ③ 第七条报红。
    """
    _swap_in_start_exam_board(
        sandbox,
        "逐节点 Grep 五种掌握度字段 → 写 `/tmp` json",
        "逐节点 Grep 五种掌握度字段 → 写 `/tmp` 上一级目录的 json",
    )

    assert not check_body(sandbox, _merged_body_baseline()), "① 前提: 计数判据放行(散文改词不动计数)"
    for label, blind in (
        ("越界", check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)),
        ("可疑行", check_suspicious_tmp_lines(sandbox, SUSPICIOUS_TMP_LINES_BASELINE)),
        ("动态拼接", check_dynamic_tmp_joins(sandbox, DYNAMIC_TMP_JOIN_BASELINE)),
        ("不透明记号", check_opaque_tmp(sandbox, OPAQUE_TMP_BASELINE)),
    ):
        assert not blind, f"② 前提: {label}判据看不见散文措辞 —— 若它看得见, 这条负控考错了对象"

    problems = check_parent_dir_prose(sandbox, PARENT_DIR_PROSE_BASELINE)
    assert any("start-exam-board" in x for x in problems), (
        f"③ 散文「上一级目录」必须被第七条判据要求登记, 实得: {chr(10).join(problems)}"
    )


def test_dynamic_join_judge_does_not_fire_on_constants():
    """⑫' 验伪锚: 第六条判据**不得**对纯常量与隐式拼接开火。

    否则它会把树上所有合规写法都拖进登记清单, 判据就退化成噪声 —— 而基线现状
    全 9 份皆空正是靠这一点成立的。
    """
    for src, why in [
        ('P = "/tmp/cls-exam/exam-candidates.json"', "纯常量"),
        ('P = ("/tmp/cls-exam/" "x.json")', "隐式拼接(ast 已折成单常量)"),
        ('P = "/tmp/cls-exam/" + "x.json"', "显式 + 常量链(_fold_str 可折)"),
    ]:
        assert not _has_dynamic_tmp_join(src), f"{why} 不该触发第六条判据: {src!r}"


def test_negative_control_fake_namespace_swap_must_redden(sandbox: Path):
    """⑩ **Codex round-2 HIGH(c)** —— 用「不在 `/tmp` 下」的冒充路径做等计数替换。

    `/var/cache/tmp/cls-exam/x.json` 含子串 `/tmp/` 与 `/tmp/cls-exam/` 各一次。放行端
    若用裸子串计数, 这个替换会让四端纹丝不动、越界判据也看不见(左边界让它不提取 token)
    ⇒ 两条判据一起漏网。放行端加左边界后 `tmp_ns` 少一个 ⇒ 计数判据报红。
    """
    _swap_in_start_exam_board(
        sandbox, "/tmp/cls-exam/exam-candidates.json", "/var/cache/tmp/cls-exam/exam-candidates.json"
    )
    problems = check_body(sandbox, _merged_body_baseline())
    joined = "\n".join(problems)
    assert any("start-exam-board" in p and "tmp_ns" in p for p in problems), (
        f"冒充命名空间的路径必须让放行端计数下降并报红, 实得: {joined}"
    )


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
