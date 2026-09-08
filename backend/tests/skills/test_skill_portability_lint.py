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
越界判据       — 每份 SKILL.md 的越界 `/tmp` normpath 多重集精确相等(见下方专段)。
可疑行判据     — `/tmp` 与 `..` 或 `$` 同一**逻辑行**(续行/相邻字面量拼接已合并)的
                   行号集合精确相等 —— 不依赖 token 切分的兜底。

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

## 第四条判据: 越界路径 (normpath, v2 引号感知)

子串计数天生看不见路径语义。`/tmp/cls-exam/../x` 含 `/tmp/` 一次 + `/tmp/cls-exam/`
一次 ⇒ 裸值 0 ⇒ **计数判据放行**, 而它规范化之后是 `/tmp/x`, 已经越出命名空间
(Codex round-1 HIGH, 2026-09-08)。`check_escaping_tmp()` 把每份的越界 normpath
**集合**钉死, 与计数判据分工互补:

  计数判据 —— 命中数变没变(与 shell 裁判逐字同源)
  越界判据 —— 命中的那个路径规范化后指向哪里

r1→r4 每轮都出现新的切分绕过(逗号截断 → 冒充子串 → 白名单边界 → 跨行拼接 →
**引号内的空格/开括号冒充** → 混合引号拼接 → 单行点号拼接), 根因是正则看不见
引号上下文 ⇒ v2 改为**字面量原子化**: 引号内是一个整体; fence 内相邻字面量拼接组
整组求值; 裸 token 沿用白名单边界正则。详见 `_TMP_TOKEN_RE` 上方 v2 注释。

⚠️ 两条判据对同一输入可以给出**不同**结论, 那是分工不是矛盾: `/tmp/a/../cls-exam/z`
在计数下报红(写法不是钦定形态), 在越界判据下放行(规范化后确实落在命名空间内)。

越界基线现状(2026-09-08 v2 实测) 全是「只钉不改」的已知项: start-exam-board 的
exam-created-event(被 tests/regression 钉死)、`:128` 裸 `/tmp` 提法、`:188` 变更行
backtick 命令 span; quiz-answer 两形态(E-2 归 U5-B); board-recap `:58` 裸 `/tmp` 提法。

## 第五条判据: 可疑行(不依赖切分的兜底) + 已知的保守误报方向

切分是启发式 —— r2 被逗号截断、r3 被跨行拼接骗过。`check_suspicious_tmp_lines()`
只问「这一**逻辑行**值不值得人看一眼」(`/tmp` 且有 `..` 或 `$`), 不问路径是哪一段,
因此不会被切分错误带偏。逻辑行 = 物理行经反斜杠续行与相邻同引号字面量拼接合并。

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


# ── 越界路径判据 v2: 引号感知 (与上面的子串计数**互补**, 不是替代) ───────────
#: r1→r4 的教训: 用正则从自由文本切 `/tmp` token, 每一轮都被换一种坏法骗过
#: (r1 穿越在后 → r2 逗号截断/冒充子串 → r3 白名单边界/跨行拼接 → r4 **引号内的
#: 空格与开括号冒充**、混合引号拼接、单行点号拼接 `"." "./x"`)。
#: 根因是**看不见引号上下文**。v2 改为字面量原子化:
#:   · 引号(backtick/单/双)里的内容是**一个整体** —— 引号内的空格、括号、逗号、
#:     分号、中文标点都是路径字符, 不再是「路径起点/截断」的证据(r4 HIGH-1 与
#:     MEDIUM-3 的引号内变质由此封住);
#:   · fenced code 内的**相邻字面量拼接组**(Python 隐式拼接, 任意引号可混用;
#:     反斜杠续行与「行尾引号 + 次行引号开头」先并回同一逻辑行)整组求值 ——
#:     `"." "./x"` 在源码里没有连续 `..`, 拼起来才有(r4 HIGH-2 由此封住);
#:   · **裸 token**(如 `mkdir -p /tmp/cls-exam/`)沿用 r3 的白名单边界正则, 全文适用
#:     —— 未加引号的 `/var/cache /tmp/cls-exam/x` 是两个 shell 词, 后者本就在命名
#:     空间内, 不是攻击; 攻击必须把整串放进引号, 而引号内已由字面量原子性接管;
#:   · 散文里的引号只认 **backtick 代码 span**(markdown 语义); 单双引号在散文里是
#:     自然语言, 不当字面量。
_FENCE_MARK = "```"
_QUOTE_CHARS = "'\"`"
_BACKTICK_SPAN_RE = re.compile(r"`([^`\n]*)`")
#: 裸 token: 白名单左边界(r3 HIGH-1) + 中文标点停止(防散文拖尾)。
_TMP_TOKEN_RE = re.compile(r'(?<![^\s"`\'(\[{（【])/tmp/[^\s`"\'()（）；;：，、。]*')
_TMP_LINE_RE = re.compile(r"/tmp")
_QUOTE_TAIL_RE = re.compile(r"['\"`]\s*\Z")  # 行尾(可带尾随空白)的引号
_QUOTE_HEAD_RE = re.compile(r"^\s*['\"`]")
#: 相邻字面量之间的**隐式拼接间隙**: 只许空白与括号 —— 逗号是元组分隔符, 不是拼接。
_CONCAT_GAP_RE = re.compile(r"^[\s()\[\]{}+]*$")


def _iter_lines_by_context(text: str):
    """yield `(行号, 行, in_fence)`; fence 标记行(``` 开头)自身被跳过。"""
    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(_FENCE_MARK):
            in_fence = not in_fence
            continue
        yield i, line, in_fence


def _literals_in(line: str) -> list[tuple[str, int, int]]:
    """扫描一行里的引号字面量, 返回 `(内容, 起始列, 结束列)`。

    同种引号闭合; 反斜杠转义; 未闭合(合并后理论上不该有)保守取到行尾 —— 方向是
    多抓不少放。**只在 fence 行上调用**(散文只扫 backtick span)。
    """
    lits: list[tuple[str, int, int]] = []
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c in _QUOTE_CHARS:
            j = i + 1
            while j < n:
                if line[j] == "\\":
                    j += 2
                    continue
                if line[j] == c:
                    break
                j += 1
            end = j if j < n else n
            lits.append((line[i + 1 : end], i, end))
            i = end + 1
        else:
            i += 1
    return lits


def _concat_groups_in(line: str) -> list[str]:
    """一行内的相邻字面量拼接组(Python 隐式拼接的保守超集): 组值 = 逐个字面量内容相连。

    span 约定: `(内容, 开引号列, 闭引号列)` ⇒ 相邻间隙 = `line[前闭引号+1 : 后开引号]`,
    即两条引号**之间**的原文 —— 只许空白与括号才算隐式拼接(逗号是元组分隔符)。
    """
    lits = _literals_in(line)
    groups: list[str] = []
    cur_val = ""
    cur_end = -1
    for content, s, e in lits:
        if cur_val and _CONCAT_GAP_RE.match(line[cur_end + 1 : s]):
            cur_val += content
        else:
            if cur_val:
                groups.append(cur_val)
            cur_val = content
        cur_end = e
    if cur_val:
        groups.append(cur_val)
    return groups


#: ⛔ **为什么光有子串计数不够**(Codex round-1 HIGH, 2026-09-08):
#: `/tmp/cls-exam/../x` 含 `/tmp/` 一次、`/tmp/cls-exam/` 一次 ⇒ 裸值 = 0 ⇒ 子串规则
#: **放行**, 而它 normpath 之后是 `/tmp/x`, 已经越出命名空间。子串规则天生看不见
#: 路径语义 ⇒ 另立这条 normpath 判据; r4 起它**引号感知**(见上方 v2 注释)。
#:
#: 两条判据分工: 计数判据管「有没有新增/减少命中」(与 shell 裁判逐字同源),
#: 本判据管「命中的那个路径到底指向哪里」。各自有自己的负控。
def escaping_tmp_paths(text: str) -> list[tuple[str, str]]:
    """返回 `(候选, normpath 结果)`, 只含**含 `/tmp` 且 normpath 后不在命名空间内**的。

    候选 = fence 内字面量拼接组 / 散文 backtick span / 全文裸 token。
    命名空间内 = 规范化后等于 `/tmp/cls-exam` 或以 `/tmp/cls-exam/` 开头。
    """
    ns = TMP_NAMESPACE.rstrip("/")
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(cand: str) -> None:
        if "/tmp" not in cand:
            return
        norm = posixpath.normpath(cand)
        if norm != ns and not norm.startswith(ns + "/") and (cand, norm) not in seen:
            seen.add((cand, norm))
            out.append((cand, norm))

    for _ln, line, fence in _logical_lines(text):
        if fence:
            for group in _concat_groups_in(line):
                add(group)
        else:
            for m in _BACKTICK_SPAN_RE.finditer(line):
                add(m.group(1))
        for tok in _TMP_TOKEN_RE.findall(line):  # 裸 token: fence 与散文都扫
            add(tok)
    return out


def _logical_lines(text: str) -> list[tuple[int, str, bool]]:
    """物理行 → 逻辑行, 返回 `(起始行号, 合并后行, in_fence)`。

    **只在 fence 内容行内合并**(r4 LOW-8: 散文行尾加个引号就足以搬动行号基线,
    散文不该参与拼接语义): 反斜杠续行(原样拼接, 去掉续行符) + 「行尾引号 → 次行以
    引号开头」(任意引号混用, 原样拼接 —— 引号配对交给字面量扫描器)。合并次数有界(6)。
    """
    raw = list(_iter_lines_by_context(text))
    out: list[tuple[int, str, bool]] = []
    i = 0
    while i < len(raw):
        ln, line, fence = raw[i]
        i += 1
        if not fence:
            out.append((ln, line, fence))
            continue
        buf = line
        for _ in range(6):
            if i >= len(raw) or not raw[i][2]:
                break
            nxt = raw[i][1]
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


def suspicious_tmp_lines(text: str) -> list[tuple[int, str]]:
    """**不依赖 token 切分**的保守判据: 同一**逻辑行**里 `/tmp` 与 `..` 或 `$` 同时出现。

    返回 `(1-based 起始行号, 该逻辑行 strip 后的内容)`。

    存在的理由见 `_TMP_LINE_RE` 上方注释: 切路径是启发式, 逗号 / 括号 / 引号任一处
    切错就换一种坏法(漏检或误报)。这条判据只问「这一行值不值得人看一眼」, 不问
    「路径到底是哪一段」—— 因此不会被切分错误带偏。

    触发条件(r3 后加宽): `/tmp` 在行内 且 (`..` 在行内 或 `$` 在行内)。
    `$` 放宽到**任意位置**而非「紧跟命名空间」: `P="/tmp/cls-exam/$1"`(位置参数,
    r3 MEDIUM-3)与 `P="/tmp/cls-exam/"$REL`(引号外拼接, 同条)都必须登记 —— 静态门
    无法求解任何 `$` 的值, 保守面越大越安全。代价是含 `${CLS_BACKEND_URL:-…}`
    等无害展开的 `/tmp` 行也要登记(现状 1 行, 见基线注释)。

    **逻辑行合并只在 fence 内**(r4 LOW-8): 物理行上被换行拆开的 `"/tmp/cls-exam/"`
    + `"../x"` 先拼回再判 —— 否则 `/tmp` 与 `..` 不同行, 本判据跟着失明; 散文行
    不参与合并, 散文里的引号编辑不会无端搬动行号基线。
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
#: v2 对相同 (候选, normpath) **去重** ⇒ 这里是集合语义(排序列表), 不是多重集 ——
#: 换掉一个越界路径、或同一形态从散文挪进 fence, 都会改变集合 ⇒ 红。
#: 现状全部是「只钉不改」的已知项:
#:   · quiz-answer 两形态(散文 backtick 与 fence 字面量同串, 去重后各 1 条; E-2 归 U5-B);
#:   · start-exam-board `:430/:435` 的 exam-created-event(被 tests/regression 钉死)、
#:     `:128` 散文 backtick 的裸 `/tmp` 提法、`:188` 变更行 backtick 整段命令
#:     `Bash: mkdir -p /tmp/cls-exam`(含 /tmp 的非路径 span, 保守登记);
#:   · board-recap `:58` 散文 backtick 的裸 `/tmp` 提法("禁写 /tmp"声明)。
#: **新增任何越界候选 = 红**, 这正是子串计数看不见的那一面。
ESCAPING_TMP_BASELINE: dict[str, list[str]] = {
    "ai-linked-doc": [],
    "board-recap": ["/tmp"],
    "chat-with-context": [],
    "configure-whiteboard": [],
    "exam-quick": [],
    "node-chat": [],
    "quiz-answer": [
        "/tmp/quiz-answer-incr.json",
        "/tmp/quiz-answer-payload.json",
    ],
    "start-exam-board": [
        "/tmp",
        "/tmp/exam-created-event.json",
        "Bash: mkdir -p /tmp/cls-exam",
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
        # 放行端用带左边界的正则, 不是裸子串 —— 见 `_TMP_NS_RE` 上方注释。
        "tmp_ns": len(_TMP_NS_RE.findall(text)),
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
    """越界路径判据(v2 引号感知): 每份 SKILL.md 的越界 normpath **集合**精确相等。

    与 `check_body` 的子串计数**互补**: 计数管「命中数变没变」, 这里管「命中的那个
    路径规范化之后指向哪里」。`/tmp/cls-exam/../x` 在计数下裸值为 0(放行), 在这里
    normpath 成 `/tmp/x` ⇒ 越界 ⇒ 红。v2 对相同 (候选, normpath) 去重 ⇒ 集合语义。
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
            '```\nP = "/tmp/quiz-answer-incr.json;sub/../../x"\n```',
            1,
            True,
            True,
            "引号内分号变质(r4 MEDIUM-3): 字面量原子化 ⇒ 尾巴不再截断(裸 1: 本就不在命名空间)",
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
                {**u, "skills/clear-inbox/scripts/new_u6_tool.py": {"tmp": 0, "users_path": 0, "tree_name": 0}},
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
            lambda b, s, u: (b, s, {**u, "scripts/fsrs_bridge.py": {"tmp": 0, "users_path": 1, "tree_name": 1}}),
            "只收 U6 地盘",
            "把别人地盘的脚本挂到 U6 名下换维护归属 ⇒ 拦",
        ),
        (
            lambda b, s, u: (
                b,
                s,
                {**u, "skills/clear-inbox/scripts/new_u6_tool.py": {"tmp": 1, "users_path": 1, "tree_name": 0}},
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
                {**s, "skills/clear-inbox/scripts/inbox_preview.py": {"tmp": 0, "users_path": 0, "tree_name": 0}},
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
                    "skills/clear-inbox/scripts/inbox_preview.py": {"tmp": 1, "users_path": 0, "tree_name": 0},
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
                {**u, "skills/clear-inbox/scripts/inbox_preview.py": {"tmp": 1, "users_path": 0, "tree_name": 0}},
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

    # ⛔ r4 MEDIUM-4: 这条负控原先只对基线断言「含 skill 名 + [可疑行]」—— 而本替换
    # 会把 :577 挤到 :578, 行号基线**无论合并逻辑在不在都会红**, 于是它考的不是合并
    # 逻辑本身(不承重)。改为**直接函数断言**: 合并在 ⇒ 拼起来的逻辑行里有 `..`;
    # 合并不在 ⇒ /tmp 与 .. 分处两行, 函数返回空 ⇒ 这里立刻红 —— 归因干净。
    text2 = f.read_text(encoding="utf-8")
    flagged = [l for _ln, l, _f in _logical_lines(text2) if "/tmp" in l]
    assert any(".." in l for l in flagged), f"fence 逻辑行合并必须在场: 含 /tmp 的逻辑行应拼出 `..`, 实得: {flagged}"
    esc = check_escaping_tmp(sandbox, ESCAPING_TMP_BASELINE)
    assert any("start-exam-board" in p and "/tmp/exam-candidates.json" in p for p in esc), (
        f"拼接组求值必须让越界判据抓到 normpath=/tmp/exam-candidates.json, 实得: {esc}"
    )


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
