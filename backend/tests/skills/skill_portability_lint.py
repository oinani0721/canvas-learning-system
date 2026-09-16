"""start-exam-board / vault skills 可移植性 lint —— 解析器与判据（纯函数，不依赖 pytest）。

本模块由 `test_skill_portability_lint.py` 于 BATCH-2026-09-11-第十四批
CARD-SKILL-PORT-LINT-PARSER 抽出，**纯搬迁、行为零漂移**：12 个 `check_*`、
正则/解析 helper、全部基线常量的**值逐字节未变**。判据函数是纯函数，可被
pytest 以外的静态面直接导入复用（`from tests.skills.skill_portability_lint import …`）。

⚠️ 交接登记（CARD-SKILL-PORT-LINT-PARSER (h)，doc-only，本卡未动手）：

(i) `canvas-vault/.claude/skills/start-exam-board/SKILL.md` 里 `/tmp/exam-created-event.json`
    尚有 **2 处裸 `/tmp/`** 残留（`Write` 的目标路径一处、`P = "…"` 赋值一处）。
    这不是新债——第十三批 U4 CARD-SKILL-PORT-LINT 收工时已把裸 `/tmp/` 从 4 降到 2，
    这 2 处是当时刻意留下的残留。层 2 基线 `BASELINE["start-exam-board"]` 的
    `tmp_all=6 / tmp_ns=4` ⇒ `bare_tmp()` = 2，与之一致。

(ii) 真把这 2 处改成 `/tmp/cls-exam/` 命名空间，必须**同批**改 **4 处 regression 硬钉点**
    （引用一律用「文件名 + 条目名」，不用行号——行号会随别的卡漂移）：
      · `backend/tests/regression/test_g3_3_cas.py` —— 两处，**作用域不同，别混为一谈**：
          - `_SEB_BLOCKS` 列表推导按 `'P = "/tmp/exam-created-event.json"'` 字面量过滤、
            紧随其后的 `assert len(_SEB_BLOCKS) == 1`、以及 `SEB_CODE = _SEB_BLOCKS[0]`
            —— 这三行在**模块级**（其上无任何 `def` / `class`），**导入期即执行**；
          - `_exam_board_code()` 里对同一字面量的 `.replace(...)` —— 这一处在**函数体内**，
            **不**在导入期执行；它消费的是上面那个模块级 `SEB_CODE`。
        ⛔ 归因只落在**模块级**那三行：改字面量 ⇒ `assert len(_SEB_BLOCKS) == 1` 在导入期
        就断言失败 = **collect-time ERROR、整个文件不可收集**（函数体内那处根本轮不到执行，
        所以它不是 collect-time 失败的原因，但解耦时同样要改，否则替换不到目标字面量）。
      · `backend/tests/regression/test_learning_events_schema_contract.py` —— 函数
        `test_real_producer_start_exam_board_writer` **体内**的 `matches` 列表推导
        （同一字面量）+ `assert len(matches) == 1`，以及同函数体内的 `.replace(...)`。
        这一侧在测试函数体内（有缩进）⇒ 改字面量 = **该条单测运行期断言红**，
        不是 collect-time ERROR。两侧破法不同，解耦时要分别处置。

(iii) 上述 2 个 regression 文件在第十四批设计稿 §3 **都不属任何车道**：
    `test_g3_3_cas.py` 无车道；`test_learning_events_schema_contract.py` 经裁定
    R-B14-8 只把 producer 提取锚一处放行给同车道前卡 T7-B。⇒
    **CARD-SKILL-PORT-LINT-PARSER 对这 2 个文件都无写权**，真解耦属跨地盘改动，
    须主 session 先裁「扩本卡地盘 / 另立带 regression 地盘的卡 / 维持残留登记」。
    本卡因此**只登记不动手**：SKILL.md 未改（digest 保持 `0f2c085a…`）、
    regression 未改、裸 `/tmp/` 仍为 2。
"""

from __future__ import annotations

import ast
import codeop
import functools
import hashlib
import os
import posixpath
import re
import shlex
import shutil
import textwrap
import time
import warnings
from collections import Counter
from typing import NamedTuple
from pathlib import Path

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


def _normalize_span(content: str) -> str:
    r"""CommonMark code span 内容归一化: 换行→空格, 再剥**一对**首尾空格。

    ⛔ r20 MEDIUM-5: `` ` /tmp/cls-exam/x ` `` 渲染出来就是合规路径, 不归一化的话模块
    报 `prose:/tmp/cls-exam/x `(带尾空格)—— **误报**方向, 而且这是很常见的写法。
    CommonMark 0.31 §6.1: 先把 line ending 换成空格; 若结果首尾都是空格且不全是空格,
    各剥掉一个。这一条不需要容器栈, 所以在本卡就地修, 不推给分块卡。
    """
    content = content.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    if len(content) >= 2 and content[0] == " " and content[-1] == " " and content.strip(" "):
        content = content[1:-1]
    return content


def _backtick_spans(text: str, *, normalize: bool = True) -> list[str]:
    r"""text 里的 markdown code span 内容。

    `normalize=False` 给**要按原串定位**的调用点用(跨行 span 靠 `"\n" in content` 判定、
    靠 `joined.find(content)` 取行号, 归一化后两者都失效)。

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
        raw = text[i + run : close]
        out.append(_normalize_span(raw) if normalize else raw)
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
            # ⛔ CommonMark 的额度算法(r13→r17 五轮): closing 缩进 ≤ **容器内容基线** + 3。
            #   · 无容器 ⇒ 基线 0(opening 自己的缩进不给额度, r15 HIGH-1);
            #   · 有容器 ⇒ 基线 = **容器标记本身**的宽度, **不含**标记之后的内容缩进
            #     —— `>   ~~~py` 的基线是 `> ` 的 2 列而不是 4 列, 否则 `>\t  ~~~`
            #     会被 `6 <= 4+3` 提前闭合(r17 MEDIUM-3)。
            _open_m = _FENCE_OPEN_RE.match(lines[i])
            _prefix_raw = lines[i][: _open_m.start(1)]
            _marker_only = _CONTAINER_MARKER_RE.match(_prefix_raw)
            open_indent = len(_marker_only.group(0).expandtabs(4)) if _marker_only else 0
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
#: ⛔ r17 HIGH-2: `#` 后只接受**空格/tab 或行尾** —— `\s` 会把 `#<NBSP>x` 误认成标题。
_ATX_HEADING_RE = re.compile(r"^ {0,3}#{1,6}([ \t]|$)")
#: markdown 块边界(除空行外): ATX 标题、thematic break、setext 下划线。
#: ⛔ r12 HIGH-3: **列表项**同样是块边界 —— 相邻两个列表项各有独立的 code span,
#: 拼起来会让前一项的未闭合反引号夺走后一项的合法 opening。
_BLOCK_BREAK_RE = re.compile(
    r"^ {0,3}(#{1,6}([ \t]|$)|(\*[ \t]*){3,}$|(-[ \t]*){3,}$|(_[ \t]*){3,}$|=+[ \t]*$"
    # ⛔ r16 HIGH-2: 有序列表**只有 `1.`/`1)` 能打断段落**(CommonMark) —— 把 `2. `
    # 一律当新块会切断合法的跨行 code span。
    # ⛔ r17 HIGH-2: 列表 marker 后**必须有内容**才算新块 —— 空列表项(`+ ` 后什么都没有)
    # 在 CommonMark 里不能打断段落, 当成块边界会切断合法的跨行 code span。
    r"|[-*+][ \t]+\S|1[.)][ \t]+\S|<!--)"
)
#: 列表项 marker(供 `_strip_quote_prefix` 迭代剥用)。
_LIST_MARKER_RE = re.compile(r"[-*+][ \t]+|\d+[.)][ \t]+")
#: 容器**标记本身**(不含标记之后的内容缩进) —— 用于算 closing 的额度基线。
_CONTAINER_MARKER_RE = re.compile(r"^[ \t]{0,3}(?:(?:>[ \t]?)+|(?:[-*+][ \t]|\d+[.)][ \t]))+")
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


def _ident_text(value: str | bytes) -> str:
    r"""常量值 → **保身份**的文本; str 与 bytes 走同一套编码。

    ⛔ r22 MEDIUM-6: 单射性是**整个值域**(str ∪ bytes)上的性质, 不是一个类型内部的。
    r21 只做到「两个不同 bytes 不同名」, 而 `backslashreplace` 产出的 `\xNN` 恰好落进
    普通 str 本来就能表示的区域: `b"/tmp/\xff/x"`(真的 0xFF 字节)与
    `r"/tmp/\xff/x"`(字面反斜杠)解出同一个候选, 登记一条后另一条可静默顶替。
    统一规则: **先把已有反斜杠都转义成两个** ⇒ 不可解码字节产出的 `\xNN` 里那个 `\`
    永远是单个, 而任何文本里的 `\` 永远是双个, 两个像域不再相交。
    (可解码 bytes 与同内容 str 仍同名 —— 那是**对的**, 它们就是同一条路径。)
    """
    return value.replace("\\", "\\\\") if isinstance(value, str) else _decode_bytes(value)


def _decode_bytes(raw: bytes) -> str:
    r"""bytes → **保身份**的文本表示。

    ⛔ r20 MEDIUM-4: 用 `backslashreplace` 而非 `replace` —— 后者把不同的不可解码字节
    都压成 U+FFFD, 登记一条后另一条可静默顶替(基线是多重集)。
    ⛔ r21 MEDIUM-5: 光换 `backslashreplace` 还不够 —— 它产出的 `\xNN` 会与**原本就
    含字面反斜杠**的内容撞名: `b"/tmp/\xff/x"`(无效字节)与 `b"/tmp/\\xff/x"`(反斜杠+xff)
    解出同一个字符串。先把已有反斜杠转义成两个, 编码才是单射。
    """
    return raw.replace(b"\\", b"\\\\").decode("utf-8", "backslashreplace")


def _fold_const(node: ast.AST) -> str | bytes | None:
    """`Constant` 或 `BinOp(+)` 常量链 → 值本身, **保留 str/bytes 类型**; 不可折返回 None。

    分出这一层只为一件事: 让 bytes 链先按 bytes 拼完整, 再由 `_fold_str()` 解码**一次**。
    """
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, (str, bytes)) else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _fold_const(node.left), _fold_const(node.right)
        if left is None or right is None or type(left) is not type(right):
            return None  # `str + bytes` 在 Python 里本来就是 TypeError, 折不出任何值
        return left + right  # type: ignore[operator]
    return None


def _fold_str(node: ast.AST) -> str | None:
    r"""`Constant` 或 `BinOp(+)` 常量链 → 字符串; 不可折返回 None。

    ⛔ r19 HIGH-3: **bytes 也要折**。`b"/t" + b"mp/cls-exam/" + b".." + b"/x"` 是单块、
    合法 Python、普通常量加法, 只折 str 的话整条链折不出来, 越界判据只看到分散的叶常量,
    动态判据也找不到含 `/tmp` 的起点 ⇒ 完整漏检(不需要特殊转义或跨块分析)。
    ⛔ r20 MEDIUM-4: 解码得(a)**先折完整条链再解一次**, (b)用 `backslashreplace` 而不是
    `replace`。逐叶 `replace` 有两处**身份损失**: `b"/tmp/\xff/x"` 与 `b"/tmp/\xfe/x"`
    都解成 `/tmp/\ufffd/x` —— 登记了其中一条, 另一条就能静默顶替它(基线是多重集, 名字
    一样就抵消); 且 `b"\xc3" + b"\xa9"` 逐叶解出两个 U+FFFD, 整条解是 `é`, 与运行时的
    真实路径不是同一个字符串。`backslashreplace` 对不可解码字节产出 `\xNN`, 不同字节 ⇒
    不同文本, 身份不丢。
    """
    value = _fold_const(node)
    if value is None:
        return None
    return _ident_text(value)


def _py_strings(src: str) -> list[str] | None:
    """`ast` 解析出的全部字符串值(含折叠的 `+` 链); 解析失败返回 None。

    折进 `+` 链的 `Constant` 不再单独计一次 —— 否则同一处会产生两个候选。

    ⛔ r20 LOW-3 的成本面: r19 起动态判据对**每个**语法单元都要整段解析一次, 而
    `_parse_units()` 的窗口扩张本来就会对同一段源码反复调这里。缓存内部存 tuple、
    返回时复制成新 list —— `escaping_tmp_paths()` 那边拿到后会 `.extend()`, 直接
    把缓存对象交出去等于让调用方污染缓存。
    """
    cached = _py_strings_cached(src)
    return None if cached is None else list(cached)


@functools.lru_cache(maxsize=4096)
def _py_strings_cached(src: str) -> tuple[str, ...] | None:
    tree = _quiet_parse(src)
    if tree is None:
        return None
    out: list[str] = []
    folded: set[int] = set()
    # ⛔ r18 MEDIUM-1: 只收**最外层**可折的 `+` 链 —— `"/t" + "mp" + ""` 的内层
    # `"/t" + "mp"` 也可折, 两个都收就贡献了两个 `/tmp` 候选, 登记后成了可抵消的额度。
    nested: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) and _fold_str(node) is not None:
            for sub in ast.walk(node):
                if sub is not node and isinstance(sub, ast.BinOp):
                    nested.add(id(sub))
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) and id(node) not in nested:
            value = _fold_str(node)
            if value is not None:
                out.append(value)
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Constant) and isinstance(sub.value, (str, bytes)):
                        folded.add(id(sub))
    for node in ast.walk(tree):
        if id(node) in folded or not isinstance(node, ast.Constant):
            continue
        if isinstance(node.value, str):
            out.append(_ident_text(node.value))
        elif isinstance(node.value, bytes):
            # ⛔ r18 HIGH-2: bytes 字面量也是路径 —— `b"/t" b"mp/cls-exam/" b"." b"./x"`
            # 被 `ast` 合成 `b"/tmp/cls-exam/../x"`, 只收 str 的话越界判据整类看不到。
            # ⛔ r20 MEDIUM-4: 与 `_fold_str()` 同口径用 `backslashreplace` —— `replace`
            # 会把不同的不可解码字节压成同一个 U+FFFD, 登记后可被静默顶替。
            out.append(_ident_text(node.value))
    return tuple(out)


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


def _next_continuation(body: list[str], i: int, j: int, end: int) -> int | None:
    """`body[i:j+1]` 之后, 下一个「看起来像续接子句」的行号; 没有则 None。

    跳过空行、注释, 以及仍在本语句体内(缩进更深)的行; 遇到同级非续接行即结束。
    """
    base = len(body[i]) - len(body[i].lstrip())
    for k in range(j + 1, end + 1):
        nxt = body[k]
        if not nxt.strip() or nxt.lstrip().startswith("#"):
            continue
        if _PY_CONTINUATION_RE.match(nxt):
            return k
        if len(nxt) - len(nxt.lstrip()) > base:
            continue
        return None
    return None


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
    在混合 shell + python 的文本里, 一行 `else:` 到底是 **Python 续接子句** 还是
    **恰好长这样的 heredoc 终止符**(`python3 - <<'else:'` … `else:`), **静态区分不了**。
    r13→r15 三次改规则去猜, 三次被反例推翻(最后一次是双向反例)。猜不出来就**不猜**:
    把「在此切断」的短单元与「继续累加」的长单元**都收**。

    ⛔ 扩张必须**循环**(r17 HIGH-1): 连续多个 `elif` 时只扩一次的话, 第二个又会退给
    `shlex`, 拼接关系照样丢。也不设固定窗口 —— 固定上限只是把缺口挪个位置。
    ⛔ 长单元只贡献它**比上一版多出来的**候选(多重集差, r17 MEDIUM-1) —— 否则重叠
    部分被计两次, 登记之后就成了可以抵消新增路径的额度。
    """
    out: list[tuple[int, str, list[str] | None]] = []
    i, n = 0, len(body)
    while i < n:
        end = n - 1
        handled = False
        for j in range(i, end + 1):  # ① Python 窗口
            chunk = textwrap.dedent("\n".join(body[i : j + 1]))
            values = _py_strings(chunk)
            if values is not None:
                out.append((i, "\n".join(body[i : j + 1]), values))
                seen = Counter(values)
                cur_j = j
                while True:  # ② 循环扩张: 只要后面还有续接子句就继续
                    nxt_k = _next_continuation(body, i, cur_j, end)
                    if nxt_k is None:
                        break
                    grown: tuple[int, list[str]] | None = None
                    for kk in range(nxt_k, end + 1):
                        merged = textwrap.dedent("\n".join(body[i : kk + 1]))
                        got = _py_strings(merged)
                        if got is not None:
                            grown = (kk, got)
                            break
                        if not _py_needs_more(merged):
                            break
                    if grown is None:
                        break
                    kk, got = grown
                    # ⛔ r18 HIGH-1: 长单元的**源码**必须保留, 即使 delta 为空 ——
                    # `dynamic_tmp_join_lines` 看的是 chunk **文本**(它自己再 parse),
                    # 不是候选列表。我 r17 写成 `if delta:` 时, bytes 拼接这类
                    # 「候选为空但源码有料」的长单元整个不进 out, 而 `cur_j` 照样前进 ⇒
                    # 那几行再也没人看 ⇒ 完整漏检(我修 MEDIUM-1 时引入的新回归)。
                    delta = list((Counter(got) - seen).elements())
                    out.append((i, "\n".join(body[i : kk + 1]), delta))
                    seen = Counter(got)
                    cur_j = kk
                i = cur_j + 1
                handled = True
                break
            if not _py_needs_more(chunk):
                break
        if handled:
            continue

        unit: tuple[int, str, list[str] | None] | None = None
        for j in range(i, end + 1):  # ③ shell 窗口
            chunk = "\n".join(body[i : j + 1])
            words = _sh_words(chunk)
            if words is not None:
                unit = (i, chunk, words)
                i = j + 1
                break
            if not _sh_needs_more(chunk):
                break
        if unit is None:  # ④ 两种都解析不了 ⇒ 单行退回
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
        for content in _backtick_spans("\n".join(seg), normalize=False):
            if "\n" in content:
                add(_normalize_span(content), "prose")
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


#: 建立**新作用域**的节点 —— 里面的同名变量与外面不是同一个绑定。
#: ⚠️ 推导式不在这里: PEP 572 规定推导式内的海象赋值绑定在**外层**作用域。
_SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
#: 让「这条语句是否执行」不确定的祖先。
#: ⛔ r24 HIGH-1: `With` **要算** —— `with suppress(...):` 吞掉异常后, body 后半段整段
#: 不执行; `TryStar`(`except*`)同理, 上一版两者都不在名单里。
_CONDITIONAL_NODES = (
    ast.If,
    ast.IfExp,
    ast.Try,
    ast.ExceptHandler,
    ast.match_case,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
)
if hasattr(ast, "TryStar"):  # 3.11+
    _CONDITIONAL_NODES = (*_CONDITIONAL_NODES, ast.TryStar)
#: 求值**推迟**到别处的祖先 —— 生成器表达式直到 `next()` 才跑。
_DELAYED_NODES = (ast.GeneratorExp,)
#: 提前离开/暂停当前块的语句 —— 它之后的写入未必到得了。
#: ⛔ r27 HIGH-5: `yield` 也算 —— `next(f())` 停在 `yield` 上, 后面的合规赋值**还没跑**,
#: 调用方拿到的就是 `yield` 之前那个坏值。
_EARLY_EXIT_NODES = (ast.Return, ast.Raise, ast.Break, ast.Continue, ast.Yield, ast.YieldFrom)
#: 绕过普通名字绑定、直接改命名空间的写法。静态判不出改的是哪个名字 ⇒ 一律登记。
#: ⛔ r24 HIGH-6: `globals()["P"] = …` / `locals()[…] = …` / `globals().update(P=…)` /
#: `exec("P = …")` 都真的会覆盖, 而 `_assignments()` 一条都看不见。
#: 会**改**映射内容的字典方法(`get` / `keys` 这些只读的不算)。
_NS_MUTATORS = frozenset({"update", "setdefault", "pop", "popitem", "clear", "__setitem__", "__delitem__", "__ior__"})


def _namespace_aliases(tree: ast.AST) -> tuple[set[str], set[str]]:
    """`(模块别名, 命名空间别名)`。

    ⛔ r27 HIGH-2: 别名是**直接可见**的, 不需要跨过程分析 ——
    `import sys as s` 之后 `s.modules[…]` 就是模块表; `m = globals()` 之后 `m[…] = …`
    就是写模块字典。上一版只认字面的 `sys` / `globals()`, 这两类全漏。
    """
    mods: set[str] = {"sys"}
    ns: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in {"sys", "importlib"}:
                    mods.add(a.asname or a.name)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and _is_namespace_expr(node.value, mods, ns):
                    ns.add(tgt.id)
    return mods, ns


def _is_namespace_expr(node: ast.AST, mods: set[str] | None = None, ns: set[str] | None = None) -> bool:
    """这个表达式是不是**模块命名空间本身**。

    ⛔ r26 MEDIUM-1: 上一版太宽, 把下面这些普通代码都算了进去 ——
    `vars(args)`(**带参数**时是那个对象的字典)、`args.__dict__`(实例字典)、
    任意业务属性 `X.modules[…]`。收紧成三条:
      · `globals()` / `locals()` / `vars()` —— **必须无参数**;
      · `sys.modules[…]` —— 接收者必须就是名字 `sys`;
      · `<命名空间>.__dict__` —— 点在**已经是命名空间**的表达式上才算。
    """
    mods = mods if mods is not None else {"sys"}
    ns = ns or set()
    if isinstance(node, ast.Name):
        return node.id in ns  # `m = globals()` 之后的 `m`
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id not in {"globals", "locals", "vars"}:
            return False
        if not node.args and not node.keywords:
            return True
        # ⛔ r27 HIGH-2: `vars(模块)` 返回的**就是**模块字典, 不需要别名分析 ——
        # 参数本身就写着是哪个模块。`vars(普通对象)` 才是对象字典, 仍不算。
        return node.func.id == "vars" and len(node.args) == 1 and _is_namespace_expr(node.args[0], mods, ns)
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute):
        v = node.value
        return v.attr == "modules" and isinstance(v.value, ast.Name) and v.value.id in mods
    if isinstance(node, ast.Attribute) and node.attr == "__dict__":
        return _is_namespace_expr(node.value, mods, ns)
    return False


def _reflective_write_line(tree: ast.AST) -> int | None:  # noqa: C901
    """有没有「绕过名字绑定、直接改命名空间」的写法 ⇒ 返回行号。

    ⛔ r24/r25 HIGH: 这类写法静态判不出改的是**哪个**名字, 一律登记。
    ⛔ r26 HIGH-4: 写入目标不止 `Subscript` —— `sys.modules[__name__].P = …` 是
    `Attribute`; `globals().__ior__({…})` 也不在原来的方法名单里。
    ⛔ r26 MEDIUM-1: 同时要收窄, 否则普通业务代码全中 ——
      · `.reload(` 只认 `importlib.reload`, 不是任意 `page.reload()`;
      · 命名空间作为**参数**只在**未绑定**的 `dict.update(globals(), …)` 形态算写,
        `config.update(globals())` 是**读**模块字典、写进别的字典;
      · 目标里的下标/属性必须在 **Store/Del** 上下文, `cache[globals()["P"]] = 1`
        里那个下标是 **Load**(读键), 不是写命名空间。
    ⛔ 也不能把 `globals().get(...)` 算写 —— 树上 quiz-answer `:1431` 就是那个写法。
    """
    mods, ns = _namespace_aliases(tree)
    is_ns = lambda x: _is_namespace_expr(x, mods, ns)  # noqa: E731
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                if fn.id in {"exec", "eval"}:
                    return node.lineno
                if fn.id in {"setattr", "delattr", "reload"} and node.args and is_ns(node.args[0]):
                    return node.lineno
            if isinstance(fn, ast.Attribute):
                if fn.attr == "reload" and isinstance(fn.value, ast.Name) and fn.value.id in mods:
                    return node.lineno
                if fn.attr in _NS_MUTATORS and is_ns(fn.value):
                    return node.lineno
                # `dict.update(globals(), P=…)` —— **未绑定**方法, 第一个实参是命名空间
                if (
                    fn.attr in _NS_MUTATORS
                    and isinstance(fn.value, ast.Name)
                    and fn.value.id == "dict"
                    and node.args
                    and is_ns(node.args[0])
                ):
                    return node.lineno
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign, ast.For, ast.AsyncFor)):
            targets = [node.target]
        elif isinstance(node, ast.Delete):
            targets = list(node.targets)
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            targets = [node.optional_vars]
        for tgt in targets:
            for sub in ast.walk(tgt):
                if not isinstance(sub.__dict__.get("ctx"), (ast.Store, ast.Del)):
                    continue  # 只算真正被**写**的那个位置
                if isinstance(sub, (ast.Subscript, ast.Attribute)) and is_ns(sub.value):
                    return getattr(node, "lineno", sub.lineno)
        if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names):
            return node.lineno  # 覆盖了哪些名字取决于对方模块 ⇒ 未知写入
    return None


#: 嵌套作用域节点里**在外层求值**的字段 —— 从该作用域自己出发时要整个跳过。
_OUTER_EVAL_FIELDS = frozenset({"args", "decorator_list", "bases", "keywords", "returns", "type_params"})


def _outer_eval_children(node: ast.AST) -> list[ast.AST]:
    """嵌套作用域节点里, **在外层作用域求值**的那些子节点。

    ⛔ r23 HIGH-3: 「函数体建立新作用域」不能推广成「整个 `FunctionDef` 的子节点都属于
    新作用域」—— 默认参数、装饰器、注解、基类都在**定义处**求值。
    """
    out: list[ast.AST] = list(getattr(node, "decorator_list", []))
    args = getattr(node, "args", None)
    if args is not None:
        out += [d for d in args.defaults if d is not None]
        out += [d for d in args.kw_defaults if d is not None]
        every = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        every += [a for a in (args.vararg, args.kwarg) if a is not None]
        out += [a.annotation for a in every if a.annotation]
    if isinstance(node, ast.ClassDef):
        out += list(node.bases) + [k.value for k in node.keywords]
    if getattr(node, "returns", None) is not None:
        out.append(node.returns)
    return out


def _own_nodes(root: ast.AST) -> list[ast.AST]:
    """`root` 这一层作用域**自己**的节点。

    ⛔ r24 MEDIUM-1: 从 `root` 出发时要**跳过它自己的外层求值部分** —— 那些子节点属于
    `root` 的**外层**作用域(上面 `_outer_eval_children()` 已经把它们收进去了)。两边都收
    会让同一处默认参数写入被计两次, 再套用内层的 `global` 声明搬到模块, 变成误报。
    """
    # ⛔ 按**字段名**排除, 不能按「外层求值子节点的 id」—— 默认参数是挂在 `arguments`
    # 节点下面的, 而 `iter_child_nodes(root)` 直接产出的是 `args` 那个 `arguments`,
    # id 对不上, 于是照样下钻、把同一处写入计了两次(r24 MEDIUM-1 的实际成因)。
    skip: set[int] = set()
    if isinstance(root, _SCOPE_NODES):
        for field, value in ast.iter_fields(root):
            if field in _OUTER_EVAL_FIELDS:
                for v in value if isinstance(value, list) else [value]:
                    if isinstance(v, ast.AST):
                        skip.add(id(v))
    out: list[ast.AST] = []
    stack: list[ast.AST] = [c for c in ast.iter_child_nodes(root) if id(c) not in skip]
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(_outer_eval_children(node) if isinstance(node, _SCOPE_NODES) else ast.iter_child_nodes(node))
    return out


def _scope_chain(tree: ast.AST) -> list[tuple[ast.AST, ast.AST | None]]:
    """`(作用域节点, 直接外层作用域)`; 模块的外层是 None。"""
    out: list[tuple[ast.AST, ast.AST | None]] = [(tree, None)]

    def walk(node: ast.AST, enclosing: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _SCOPE_NODES):
                out.append((child, enclosing))
                walk(child, child)
            else:
                walk(child, enclosing)

    walk(tree, tree)
    return out


class _Write(NamedTuple):
    """一次名字绑定: `pos` 用 `(行号, 列偏移)` —— 分号写成一行时行号相同, 只比行号
    会让「同样内容写成一行还是两行」结果不同(r22 LOW)。`node` 留着判循环/分支归属。"""

    pos: tuple[int, int]
    name: str
    value: ast.expr | None
    node: ast.AST
    foreign: bool = False  # 由 `global`/`nonlocal` 搬运过来 ⇒ 父链与调用时机都不可信
    partial: bool = False  # 解包赋值 ⇒ 这个名字只拿到右值的**一部分**, 值不可信


def _target_names(node: ast.expr | None) -> list[str]:
    """一个赋值目标里**全部被写入的名字** —— 元组/列表解包、`*rest` 都要拆开。

    ⛔ r21 HIGH-1: 上一版写的是 `if not isinstance(tgt, ast.Name): continue`, 于是
    `P, = ("/etc/passwd",)` 的目标是 `Tuple[Name]`、整条跳过 ⇒ `P` 的第二次写入没被计数,
    重赋值判据静默, 而 `P` 已经从命名空间内变成 `/etc/passwd`。
    `Attribute` / `Subscript` 写的不是这个名字本身(`a.b = …` 不重绑 `a`), 故不收。
    """
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Starred):
        return _target_names(node.value)
    if isinstance(node, (ast.Tuple, ast.List)):
        return [n for elt in node.elts for n in _target_names(elt)]
    return []


def _assignments(scope_root: ast.AST) -> list[_Write]:
    """这一层作用域里的 `(行号, 被写入的名字, 这次写入的值)`。

    ⛔ r21 HIGH-1: 「写入」远不止 `Assign` —— `(P := …)` 是 `NamedExpr`,
    `P *= 0` 是 `AugAssign`, `for P in …` / `with … as P` 同样重绑。
    ⛔ r22 自查(接 Codex 中断前的探针): 还有三类同样是重绑而当时全漏 ——
    `except ValueError as P`(`ExceptHandler.name` 是**裸字符串**不是 `Name` 节点)、
    `import … as P` / `from … import X as P`(`alias`)、`match: case P`(`MatchAs`/
    `MatchStar`/`MatchMapping.rest`, 名字同样是裸字符串)。三者都把 `P` 绑到别的东西上。
    """
    out: list[_Write] = []
    for node in _own_nodes(scope_root):
        pos = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                # ⛔ r27 HIGH-3: 解包时每个名字只拿到右值的**一部分** ——
                # `P, *_ = "/t" + "mp/cls-exam/x"` 之后 `P == "/"`, 不是那条路径。
                # 值仍留着(它确实含 `/tmp`, 要能与越界写入配对), 但标 `partial`,
                # 由 `_provably_last()` 判为「证不出」。
                unpack = isinstance(tgt, (ast.Tuple, ast.List))
                out += [_Write(pos, nm, node.value, node, partial=unpack) for nm in _target_names(tgt)]
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            out += [_Write(pos, n, node.value, node) for n in _target_names(node.target)]
        elif isinstance(node, (ast.AugAssign, ast.NamedExpr)):
            out += [_Write(pos, n, node.value, node) for n in _target_names(node.target)]
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            out += [_Write(pos, n, None, node) for n in _target_names(node.target)]
        elif isinstance(node, ast.withitem):
            out += [
                _Write((getattr(node.context_expr, "lineno", 0), 0), n, None, node)
                for n in _target_names(node.optional_vars)
            ]
        elif isinstance(node, ast.ExceptHandler) and node.name:
            out.append(_Write(pos, node.name, None, node))
        elif isinstance(node, ast.alias):
            out.append(_Write(pos, (node.asname or node.name).split(".")[0], None, node))
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            out.append(_Write(pos, node.name, None, node))
        elif isinstance(node, ast.Delete):
            # ⛔ r27 HIGH-4: `del P` 销毁绑定后读到的是**外层**的值 ——
            # `class C: P = "/tmp/…"; del P; result = P` 的 `C.result` 是模块级的坏值。
            out += [_Write(pos, nm, None, node) for t in node.targets for nm in _target_names(t)]
        elif isinstance(node, getattr(ast, "TypeAlias", ())) and isinstance(node.name, ast.Name):
            out.append(_Write(pos, node.name.id, None, node))  # r24: `type P = int` 也重绑 P
        elif isinstance(node, ast.MatchMapping) and node.rest:
            out.append(_Write(pos, node.rest, None, node))
        elif isinstance(node, _SCOPE_NODES) and not isinstance(node, ast.Lambda):
            out.append(_Write(pos, node.name, None, node))  # `def f` / `class C` 也是一次写入
    return out


def _value_has_tmp(value: ast.expr | None) -> bool:
    """这次写入的值里有没有(折叠后)含 `/tmp` 的常量。r20 HIGH-1: 用折叠值, 不是叶常量。"""
    if value is None:
        return False
    return any((folded := _fold_str(n)) is not None and "/tmp" in folded for n in ast.walk(value))


def _has_ancestor(parent: dict[int, ast.AST], node: ast.AST, kinds: tuple[type, ...]) -> bool:
    cur = node
    while (par := parent.get(id(cur))) is not None:
        if isinstance(par, kinds):
            return True
        cur = par
    return False


def _risky_reassign(parent: dict[int, ast.AST], records: list[_Write], early: tuple[int, int] | None) -> int | None:
    """合规常量所在的名字会不会被改写成别的 —— 返回改写处的行号; 证明不了安全就登记。

    ⛔ r23 HIGH-1: 判据的**默认方向反了**。前几轮我一直在试图证明「这处是安全的」,
    于是每补一种结构就漏一种新结构:

    ```python
    P = "/etc/passwd"
    if False:
        P = "/t" + "mp/cls-exam/x"     # 源码在后, 但**根本不执行**
    ```
    「源码在后 ⇒ 后执行 ⇒ 最终值」这个推断只有在后写**必经**时才成立。
    生成器 `((P := "/etc/passwd") for _ in (1,))` 更直接: 求值推迟到 `next()`。

    改成 Codex r23 给的口径 ——「**暂不支持的执行关系应明确触发登记, 不能因源码顺序
    或解析失败静默放行**」: 只有能**证明**某个合规写入必然最后执行时才沉默。
    证明条件(全部满足):
      · 它**必经**(祖先里没有 `if`/`try`/`except`/`match`/循环 —— 循环体可能一次不进);
      · 它不在**延迟求值**结构里(生成器表达式);
      · 与每一处越界写入之间**没有共同循环**(有的话回边能让越界写入在它之后再跑);
      · 它在源码上**位于**每一处越界写入之后, 且那些写入也都不是延迟求值;
      · 双方都不是 `global`/`nonlocal` **搬运**过来的记录(见 `_Write.foreign`)。

    ⚠️ 刻意保留的保守面(按上面的口径, 登记而不是放行):
      · `try:` 体内写越界、`else:` 写合规 —— try 体抛异常时 `else` 不执行, 合规值不保证;
      · `match` 的 guard 失败后落到下一个 `case` —— guard 的副作用会留下。
    Codex 把这两条归为误报; 但它们的最终值确实取决于运行时, 按本判据契约应当登记。
    如实登记在验收单 §六。
    """
    # ⛔ r24 HIGH-1: 这一层作用域里最早的一处「提前离开」——`return P` 之后的合规赋值
    # 根本到不了, 而它满足当前实现检查的其余全部条件。
    early_exit = early
    by_name: dict[str, list[_Write]] = {}
    for rec in records:
        by_name.setdefault(rec.name, []).append(rec)
    hits: list[int] = []
    for ws in by_name.values():
        tmp = [w for w in ws if _value_has_tmp(w.value)]
        other = [w for w in ws if not _value_has_tmp(w.value)]
        if not tmp or not other:
            continue
        # ⛔ r23 LOW-1: 两两配对是 O(tmp×other)(合成语料实测每翻倍约 4 倍)。
        # 三个判据都能先在 `other` 上聚合: 位置只需最大值, 循环只需并集, foreign/延迟
        # 只需存在性 ⇒ 每个 `tw` 的判定降到 O(1), 总体 O(tmp+other)。
        summary = (
            max(w.pos for w in other),
            any(w.foreign or _has_ancestor(parent, w.node, _DELAYED_NODES) for w in other),
        )
        if any(_provably_last(parent, tw, summary, early_exit) for tw in tmp):
            continue
        hits.append(max(w.pos[0] for w in other))
    return min(hits) if hits else None


def _provably_last(
    parent: dict[int, ast.AST], tw: _Write, others: tuple[tuple[int, int], bool], early: tuple[int, int] | None
) -> bool:
    """能不能**证明** `tw`(合规写入)必然在全部越界写入之后执行。证不出就返回 False。

    `others` 是聚合过的 `(最大位置, 有没有 foreign/延迟求值)`。

    ⛔ 这里**没有**单独的「共同循环」判定。写过一版, 回退验证显示它**恒不决定结果**:
    `For`/`While` 本身就在 `_CONDITIONAL_NODES` 里, 循环体内的写入在上一步「必经性」
    就已经判掉了, 那个检查永远到不了。留着只会让人以为是它在承重(同 r21 那个 `env`
    分支的教训)。循环回边的覆盖由**必经性**提供, 用例见
    `test_r23_reassign_registers_unless_provably_safe` ②。
    """
    max_pos, others_unordered = others
    if tw.foreign or tw.partial or others_unordered:
        return False  # 搬运/解包: 父链、调用时机或**实际拿到的值**都不可信
    if not _unconditional(parent, tw.node) or _has_ancestor(parent, tw.node, _DELAYED_NODES):
        return False
    if early is not None and early < tw.pos:
        return False  # r24 HIGH-1: `return`/`raise`/`break`/`continue` 在它之前 ⇒ 未必到得了
    return tw.pos > max_pos


def _unconditional(parent: dict[int, ast.AST], node: ast.AST) -> bool:
    """这处写入是不是**必经** —— 祖先里没有任何让它可能被跳过的结构。"""
    return not _has_ancestor(parent, node, _CONDITIONAL_NODES)


def _bound_names(scope: ast.AST) -> set[str]:
    """这个作用域**实际绑定**的名字 —— `nonlocal` 要找的就是它。

    ⛔ r25 MEDIUM-1: 只看赋值目标与形参不够 —— **只有注解**(`P: str`)和 `del P` 同样
    让 `P` 成为该作用域的局部名字。漏掉它们会让 `nonlocal` 越过这一层、误报外层。
    """
    names = {rec.name for rec in _assignments(scope)}
    for node in _own_nodes(scope):
        # ⛔ r26 HIGH-3: `(P): str` 的 `AnnAssign.simple == 0` —— 它**不**产生局部绑定
        # (树内 `compile`/`symtable` 实证)。只看目标是不是 `Name` 会让 `nonlocal` 停错层。
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.simple:
            names.add(node.target.id)
        elif isinstance(node, ast.Delete):
            names |= {n for t in node.targets for n in _target_names(t)}
    args = getattr(scope, "args", None)
    if args is not None:
        every = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        every += [a for a in (args.vararg, args.kwarg) if a is not None]
        names |= {a.arg for a in every}
    return names


def _scoped_records(
    tree: ast.AST,
) -> list[tuple[dict[int, ast.AST], list[_Write], tuple[int, int] | None]]:
    """把写入记录**按作用域**分组; `global`/`nonlocal` 各自归到正确的目的地。

    ⛔ r23 HIGH-2 / r24 HIGH-2: `nonlocal` 绑的是**最近一个实际绑定该名字的外层函数**,
    不是「最近的函数」。`outer` 里绑了 `P`、中间隔一层没绑 `P` 的 `middle`、最内层
    `nonlocal P` —— 搬到 `middle` 就再也配不上 `outer` 的合规写入。查找面必须含**形参**。
    ⛔ r24 HIGH-2 第二半: 搬运要**迭代到不动点**。按前序一遍过时, 搬进一个**已经处理过**
    的作用域的记录不会再被那个作用域自己的 `nonlocal` 继续归并。
    ⛔ r23 HIGH-4: 搬过去的记录标 `foreign=True` —— 父指针属于原作用域, 在目的地父表里
    查不到祖先; 而且函数**何时被调用**本来就未知。
    """
    chain = _scope_chain(tree)
    enclosing = {id(scope): outer for scope, outer in chain}
    scopes = [scope for scope, _ in chain]
    parents: dict[int, dict[int, ast.AST]] = {}
    records: dict[int, list[_Write]] = {}
    bound: dict[int, set[str]] = {}
    for scope in scopes:
        pmap: dict[int, ast.AST] = {}
        for node in [scope, *_own_nodes(scope)]:
            for child in ast.iter_child_nodes(node):
                pmap[id(child)] = node
        parents[id(scope)] = pmap
        records[id(scope)] = _assignments(scope)
        bound[id(scope)] = _bound_names(scope)

    decl_global: dict[int, set[str]] = {}
    decl_nonlocal: dict[int, set[str]] = {}
    for scope in scopes:
        g: set[str] = set()
        nl: set[str] = set()
        for node in _own_nodes(scope):
            if isinstance(node, ast.Global):
                g.update(node.names)
            elif isinstance(node, ast.Nonlocal):
                nl.update(node.names)
        decl_global[id(scope)], decl_nonlocal[id(scope)] = g, nl

    def nonlocal_target(scope: ast.AST, name: str) -> ast.AST:
        cur = enclosing.get(id(scope))
        fallback: ast.AST | None = None
        while cur is not None:
            if not isinstance(cur, ast.ClassDef):
                if fallback is None:
                    fallback = cur
                if name in bound[id(cur)]:
                    return cur
            cur = enclosing.get(id(cur))
        return fallback if fallback is not None else tree

    for _ in range(len(scopes) + 1):  # 迭代到不动点
        moved = False
        for scope in scopes:
            if scope is tree or not (decl_global[id(scope)] or decl_nonlocal[id(scope)]):
                continue
            keep: list[_Write] = []
            for rec in records[id(scope)]:
                if rec.name in decl_global[id(scope)]:
                    records[id(tree)].append(rec._replace(foreign=True))
                    moved = True
                elif rec.name in decl_nonlocal[id(scope)]:
                    records[id(nonlocal_target(scope, rec.name))].append(rec._replace(foreign=True))
                    moved = True
                else:
                    keep.append(rec)
            records[id(scope)] = keep
        if not moved:
            break
    # ⛔ r25 HIGH-5: 提前离开语句要从**作用域自己的节点**里取 —— 裸 `return` / `raise`
    # 没有子节点, 永远不会出现在 `parent` 的**值**里(它们只当键)。现有用例里的
    # `return P` 恰好因为有 `Name` 子节点才被发现, 纯属巧合。
    out: list[tuple[dict[int, ast.AST], list[_Write], tuple[int, int] | None]] = []
    for scope in scopes:
        early = min(
            (
                (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
                for node in _own_nodes(scope)
                if isinstance(node, _EARLY_EXIT_NODES)
            ),
            default=None,
        )
        out.append((parents[id(scope)], records[id(scope)], early))
    return out


def _reassigned_after_tmp(tree: ast.AST) -> int | None:
    """这棵树里有没有「合规常量还在, 但持有它的名字被改写成别的」——返回改写处的行号。"""
    hits: list[int] = []
    for parent, records, early in _scoped_records(tree):
        hit = _risky_reassign(parent, records, early)
        if hit is not None:
            hits.append(hit)
    # ⛔ r24 HIGH-6: 反射式写入静态判不出改的是哪个名字 ⇒ 只要这段里有合规 `/tmp` 常量,
    # 就按「暂不支持的执行关系 ⇒ 登记」处理。
    refl = _reflective_write_line(tree)
    if refl is not None and any((f := _fold_str(n)) is not None and "/tmp" in f for n in ast.walk(tree)):
        hits.append(refl)
    return min(hits) if hits else None


#: heredoc 开启标记, 可带 fd 前缀(`3<<'B'`)。定界符可含 `-`(`<<'PY-END'`)。
_HEREDOC_RE = re.compile(r"(?P<fd>\d*)<<(?P<dash>-?)\s*(?P<q>['\"]?)(?P<tag>[^\s'\"<>|&;()]+)(?P=q)")
#: 输入重定向的三种形态: heredoc / 复制 fd(`<&3`) / 从文件(`</dev/null`)。
_REDIR_RE = re.compile(
    r"(?P<fd>\d*)(?:"
    r"(?P<here><<-?\s*['\"]?[^\s'\"<>|&;()]+['\"]?)"
    r"|<&\s*(?P<dupfd>\d+|-)"
    r"|<(?!<)\s*(?P<fname>[^\s;&|<>]+)"
    r")"
)
_PY_EXE_RE = re.compile(r"(?:\S*/)?python[\d.]*")
#: fence info string 指明的语言 —— 判别 `<<` 是不是 heredoc 的**主信号**。
#: ⛔ r27 HIGH-1: 引号判别不成立(带引号的 `(( 1 << "2" ))` 是算术; 不带引号的
#: `python3 -B <<EOF` 恰好能当 Python 解析)。而 fence 已经写明了这块是什么语言 ——
#: 那才是最直接的证据, 前面几轮一直没用上。
_PY_FENCE_INFO = frozenset({"python", "py", "python3", "py3", "pycon"})
_SH_FENCE_INFO = frozenset({"sh", "bash", "zsh", "shell", "console", "shell-session", "shellsession", "dash"})
#: 需要吃掉**下一个词**的解释器选项 —— 否则 `python3 -W ignore` 里的 `ignore` 会被
#: 当成脚本文件名, 整条命令被判成「不读 stdin」(r24 HIGH-4)。
_PY_OPT_WITH_ARG = frozenset({"-W", "-X", "-Q", "--check-hash-based-pycs"})


def _py_invocation(words: list[str]) -> tuple[bool, bool, str | None]:
    """`(是不是 python 命令, 读不读 stdin, -c 的字面脚本)`。

    ⛔ r24 HIGH-4: 可执行词要先**去引号**(`'python3' - <<'A'`); `-W`/`-X`/`-Q` 要吃掉
    下一个词; `-c'脚本'` 连写也要认。
    """
    norm = [_sh_strip_quotes(w) for w in words]
    idx = next((i for i, w in enumerate(norm) if _PY_EXE_RE.fullmatch(w)), None)
    if idx is None:
        return False, False, None
    i = idx + 1
    while i < len(norm):
        w = norm[i]
        if not w or w[0] in "<>" or _REDIR_RE.fullmatch(w):
            break  # 重定向之后不再是解释器参数
        if w == "-":
            return True, True, None
        if w.startswith("-"):
            if w in _PY_OPT_WITH_ARG:
                i += 2
                continue
            # ⛔ r25 HIGH-2: `c` 不一定在选项串开头(`-Bc '脚本'` 是合法组合)。
            # ⛔ r26 HIGH-2: 但也**不能整词搜** —— `-Wignore::DeprecationWarning` 里那个
            # `c` 属于 `-W` 的**参数**, 整词搜会把 `ationWarning` 当成脚本、取消真执行区。
            # 正确做法: 逐字符按序扫, 遇到消费参数的选项(`W`/`X`/`Q`)就停止把余下字符
            # 当选项看; 参数没粘在后面时它在下一个词。
            if w.startswith("--"):
                i += 1
                continue
            body = w[1:]
            k, skip_next, found = 0, False, None
            while k < len(body):
                ch = body[k]
                if ch in "cm":
                    found = (ch, body[k + 1 :])
                    break
                if ch in "WXQ":
                    skip_next = k + 1 == len(body)
                    break
                k += 1
            if found is not None:
                kind, rest = found
                arg = rest or (norm[i + 1] if i + 1 < len(norm) else "")
                return True, False, arg if kind == "c" else None
            i += 2 if skip_next else 1
            continue
        return True, False, None  # 给了脚本文件名 ⇒ 不读 stdin
    return True, True, None


def _sh_segment_spans(code: str) -> list[tuple[int, int]]:
    """命令段的 `(起, 止)` 偏移 —— 与 `_sh_segments()` 同口径, 但保留位置。"""
    mask = _sh_protect_mask(code)
    spans: list[tuple[int, int]] = []
    start = 0
    for i in range(len(code)):
        if _is_sh_separator(code, mask, i):
            spans.append((start, i))
            start = i + 1
    spans.append((start, len(code)))
    return [(a, b) for a, b in spans if code[a:b].strip()]


def _fence_info(opener: str) -> str:
    """从 fence 开启标记行取 info string 的第一个词(小写)。"""
    m = _FENCE_OPEN_RE.match(opener)
    rest = opener[m.end() :].strip() if m else ""
    return rest.split()[0].lower() if rest.split() else ""


def _python_regions(body: list[str], info: str = "") -> list[tuple[int, str]]:
    """这个 fence 块里的**Python 执行区** —— `(区首行偏移, 源码)`。

    ⛔ r22 HIGH-2: shell fence 里的 Python heredoc 也是执行区。
    ⛔ r23 HIGH-5: 结束标记按**整行相等**判、`<<-` 逐行剥 tab、定界符可含 `-`、
    `python -c '字面脚本'` 也是执行区、接收命令不读 stdin 时那段**不是**执行区。
    ⛔ r24 HIGH-3: heredoc 要按**命令、fd 与重定向顺序**归属, 不能取整行最后一份 ——
    `python3 - 3<<'A' <<'B' <&3` 实际读的是 A; `python3 - <<'A' 3<<'B'` 读 A;
    `python3 - <<'A' | cat <<'B'` 里 A 归 python、B 归 cat; `<</dev/null` 覆盖后 A 不读。
    ⛔ r24 HIGH-5: heredoc 扫描要用**去注释 + 引号感知**的版本 —— `# <<'NO'` 与
    `echo '<<NO'` 都不是真的重定向, 按原文扫会吞掉后面真正的执行区。
    ⛔ r24 MEDIUM-2: 「整块能被 `ast` 解析」不等于「整块是一个 Python 执行区」——
    `cat <<'A'` 恰好能解析成左移表达式。**块里只要出现真 heredoc 就不再取整块**。
    ⚠️ 刻意不跨 fence 串联: 相邻 fence 可能是不同示例、不同进程。
    """
    out: list[tuple[int, str]] = []
    i, n = 0, len(body)
    saw_heredoc = False
    while i < n:
        code = _strip_sh_comment(body[i])
        mask = _sh_protect_mask(code)
        words = _shell_words(code)
        # 正文按 `<<` 在**整行**里出现的顺序依次跟随。
        # ⛔ r25 HIGH-3: 必须**验结束标记确实存在** —— `N = 1 << 2` 也能匹配 heredoc 正则
        # (fd 空、tag `2`), 认下来就把整块执行区取消了, 而三条独立语句又建立不起
        # 单元内的重赋值关系 ⇒ 整类漏检。找不到结束标记就不算 heredoc, 也不消费行。
        j = i + 1
        ops: list[re.Match[str]] = []
        docs: list[tuple[int, str]] = []
        for mm in _HEREDOC_RE.finditer(code):
            if mask[mm.start()]:
                continue  # 引号里的 `<<` 不是重定向
            # ⛔ r27 HIGH-1: 判别的**主信号是 fence 的 info string** —— 这块写明了
            # 是什么语言, 那是最直接的证据。前几轮我先后用过「结束标记存在」和「引号」,
            # 两个都被证伪: 带引号的 `(( 1 << "2" ))` 是算术; 不带引号的
            # `python3 -B <<EOF` 恰好能当 Python 的减法/左移解析。
            #   · info 是 python 系  ⇒ `<<` 一定是左移, 不是 heredoc;
            #   · info 是 shell 系   ⇒ 是 heredoc(算术 `(( ))` 已由掩码挡在前面);
            #   · info 缺失/其它     ⇒ 回落到「这一行能不能当合法 Python 解析」。
            # ⚠️ **已登记的保守误报**(r29 LOW-3, 随 ④~⑨ 的诊断降级一并接受):
            # 无标签 fence 里, Python **三引号字符串内部**若写着 `python3 <<'END'` 与两次
            # 路径赋值, 这里会把字符串内容也当成执行候选 ⇒ 多报一处。方向是**误报**,
            # 代价是一条基线登记; 要消掉它需要先判「这段文本在哪个字符串里」——
            # 那正是 r28 判定不收敛的那类工作。
            # ⛔ r28: 只有 fence **声明**是 python 时才敢排除 heredoc 解释。
            # 「未知标签 / 声明不符 / 解析失败都要登记，不能用『Python 可解析』排除 shell」
            # —— `python3 <<'END'` 恰好能当 Python 解析, 无标签时按可解析性排除就整类漏。
            if info in _PY_FENCE_INFO:
                continue
            tag, dash = mm.group("tag"), bool(mm.group("dash"))
            end = j
            while end < n and (body[end].lstrip("\t") if dash else body[end]) != tag:
                end += 1
            # 找不到结束标记 ⇒ 正文取到**块尾**(示例经常省略结束标记), 不是不认这个区。
            raw = [x.lstrip("\t") for x in body[j:end]] if dash else body[j:end]
            docs.append((j, textwrap.dedent("\n".join(raw))))
            ops.append(mm)
            j = min(end + 1, n)
        if ops:
            saw_heredoc = True
        # 逐个命令段解析重定向, 看谁的 fd 0 最终拿到 heredoc
        consumed = 0
        for a, b in _sh_segment_spans(code):
            seg = code[a:b]
            seg_words = _shell_words(seg)
            is_py, reads_stdin, script = _py_invocation(seg_words)
            if is_py and script is not None and _quiet_parse(script) is not None:
                out.append((i, script))
            fdmap: dict[int, tuple[str, object]] = {}
            for rd in _REDIR_RE.finditer(seg):
                # ⛔ r25 HIGH-1: 重定向扫描也要看掩码 —— `python3 - <<'A' '<not-a-file'`
                # 里那个被引号包住的 `<…` 是普通 argv, 认成 `<file` 会覆盖 fd 0、
                # 让真正的执行区 A 整个消失。
                if mask[a + rd.start()]:
                    continue
                fd = int(rd.group("fd")) if rd.group("fd") else 0
                if rd.group("here"):
                    if consumed < len(docs):
                        fdmap[fd] = ("here", consumed)
                    consumed += 1
                elif rd.group("dupfd") is not None:
                    src = rd.group("dupfd")
                    fdmap[fd] = fdmap.get(int(src), ("closed", None)) if src != "-" else ("closed", None)
                else:
                    fdmap[fd] = ("file", rd.group("fname"))
            slot = fdmap.get(0)
            if is_py and reads_stdin and slot and slot[0] == "here":
                start, chunk = docs[slot[1]]  # type: ignore[index]
                if _quiet_parse(chunk) is not None:
                    out.append((start, chunk))
        i = j if ops else i + 1
    # ⛔ r28: 语言未声明时**两种解释都保留** —— heredoc 区照收, 整块区也照收。
    # 只有 fence 明确声明是 shell 时, 整块解释才确定不成立(`cat <<'A'` 那类)。
    if not (saw_heredoc and info in _SH_FENCE_INFO):
        whole = textwrap.dedent("\n".join(body))
        if _quiet_parse(whole) is not None:
            out.insert(0, (0, whole))
    return out


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
    # 重赋值检查与块级走**同一个**规则(`_risky_reassign()`), 否则同样的内容会因为
    # 写成一行还是两行而结果不同(r22 LOW 实测: 分号版报、换行版不报)。
    if _reassigned_after_tmp(tree) is not None:
        return True

    # ⛔ r11 HIGH-8: 起点不能只取**叶**常量 —— `("/t" + "mp/cls-exam/") + "." * 2 + "/x"`
    # 的两个叶都不含 `/tmp`, 但折叠后的子树含。凡 `_fold_str()` 折得出且含 `/tmp` 的
    # 节点都作为起点(叶常量是它的特例)。
    starts: list[ast.AST] = []
    for node in ast.walk(tree):
        folded = _fold_str(node)
        if folded is not None and "/tmp" in folded:
            starts.append(node)
        # (r21 清单: 原先这里还有一个「bytes 叶常量用 `replace` 解码」的分支 ——
        #  `_fold_str()` 现在覆盖了它的全部命中条件, 且用的是保身份的 `backslashreplace`,
        #  留着只会让同一个问题有两套解码口径。已删。)
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
    raw_lines = _lines(text)  # 取 fence 开启标记行的 info string(判别 heredoc 的主信号)
    for start, body, is_fence in _fence_blocks(text):
        if not is_fence:
            continue
        for offset, chunk, parsed in _parse_units(body):  # 按语法单元, 不按物理行
            # ⛔ r10 HIGH-6: 预筛不能只看**源码字面**含不含 `/tmp` ——
            # `P = "/t" "mp/cls-exam/" + "." * 2 + "/x"` 的源码里没有 `/tmp` 三个字符
            # 连在一起, 但 `ast` 折完隐式拼接后有。改用**解析出的字符串**做预筛,
            # 源码字面只作为兜底(解析失败时)。
            # ⛔ r19 HIGH-2: 预筛不能用**扣重后的 delta** —— 长单元的 delta 只含它比短
            # 单元多出来的那部分, 而动态判据要问的是「**整段**里有没有含 /tmp 的常量」。
            # `P = "/t" "mp/cls-exam/x"` 在短单元、`P = "/etc/passwd"` 在长单元 delta 里,
            # 两边都不含 `/tmp` ⇒ 整段被跳过, 而它正是「合规常量与实际赋值脱钩」那一类。
            whole = _py_strings(textwrap.dedent(chunk)) or []
            if not (
                (parsed and any("/tmp" in v for v in parsed))
                or any("/tmp" in v for v in whole)
                or "/tmp" in chunk
                # ⛔ r11 HIGH-7: bytes 字面量不进 `_py_strings()`(它只收 str), 于是
                # `P = b"/t" b"mp/cls-exam/" + b"." * 2 + b"/x"` 的 parsed 是 `[]`、
                # 源码里也没有 `/tmp` 三字连写 ⇒ 预筛整类挡掉。见 bytes 就不预筛。
                or _BYTES_LITERAL_RE.search(chunk)
            ):
                continue
            if _has_dynamic_tmp_join(chunk):
                out.append((start + offset, chunk.splitlines()[0].strip()))
        # ⛔ r21 HIGH-2: 再在**执行区**级别跑一次重赋值检查 —— 逐单元跑的话, 同一个
        # fence 里两条相邻赋值语句分处两个单元, 两次写入从来不会同时被看见。
        # ⛔ r22 HIGH-2: 执行区不只是「整块」—— shell fence 里的 Python heredoc 也是
        # 一个执行区, 只认整块的话它整类漏检(见 `_python_regions()`)。
        opener = raw_lines[start - 2] if start >= 2 else ""
        for region_off, region_src in _python_regions(body, _fence_info(opener)):
            tree = _quiet_parse(region_src)
            if tree is None:
                continue
            hit = _reassigned_after_tmp(tree)
            if hit is not None:
                idx = region_off + hit - 1
                entry = (start + idx, body[idx].strip())
                if entry not in out:
                    out.append(entry)
    return sorted(out)


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
        for content in _backtick_spans(joined, normalize=False):
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
        #: 2026-09-14 CARD-HARNESS-TREE-PARSE-REDO: `_harness_tree` 整体重做(逐行正则
        #: → `yaml.safe_load` 优先 + 缺库降级只收一种规范写法 + `realpath` 取代
        #: `normpath`)改动了主写点 PYEOF 块 ⇒ 块指纹随卡同步。块起始行仍是 `:229`,
        #: 只有整块哈希变: `571eb660…`(基线) → `664dd4d8…`(重做 round-1 版) →
        #: `094c1c37…`(按 Codex round-1 收紧降级扫描 + realpath 改 strict) →
        #: `c8120a7b…`(按 Codex round-2 + 本卡自查, 降级扫描改成「读不懂就停」) →
        #: `8b8ce50d…`(按 Codex round-3: 空白口径统一 + 非法字符判据 + 文档标记状态) →
        #: `7fae3bc35bccb988…`(按 Codex round-4: 三处措辞按实测更正为「已有反例」)。
        #: → `f753616790369913…`(round-5 纯措辞更正: `_breaks` 八字符分类 + 「只有两条路」
        #: 是假二分, 走 D-32 尾巴; 逻辑零变化, 主 session 可逐行等价核)。
        #: → `8d5ce8d4…`(用户 2026-09-14 裁定「缺 PyYAML 即拒写」: `_degraded_scan`
        #: 整段删除, 净减 134 行; 代价已实测并写进该函数 docstring, 见验收单 §五-septies)。
        #: → `543e37de58c7a214…`(Codex round-6 LOW: 缺库拒因补上本进程解释器路径与
        #: 绑定它的安装命令 —— 只说「请装 PyYAML」时用户很可能装进另一个环境)。
        #: → `6098a8a36ad9318e…`(Codex round-7 HIGH: 拿 PyYAML 与读 config 拆成两个 try ——
        #: 合在一起时导入自己抛的 OSError 会被当成「没有 config」而静默回退父目录)。
        #: → `df79074d06410577…`(Codex round-8: 「import 成功」≠「拿到 PyYAML」——
        #: 空的同名 yaml.py 照样导得进, 故改判 safe_load 在不在; 安装命令改 shlex.quote)。
        #: → `9a1ec16c27149217…`(Codex round-9 HIGH: 「打不开 config」与「打开了却解析失败」
        #: 拆成两个作用域; 并把「拿到 PyYAML」的判据从「可调用」升级为在已知输入上自证)。
        "B229:9a1ec16c27149217",
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
#: U5-B 改 `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 后**必须**同步改这一段。
#: 单列在这里就是为了让那次 diff 一眼可见。
#: 行号标注(2026-09-14 CARD-HARNESS-TREE-PARSE-REDO 实测): 4 处裸 `/tmp/` 在
#: `:98/:106/:205/:233`, 4 处 `claude_dir_ref` 在 `:74/:3104/:3112/:3203`。
#: ⚠️ 2026-09-15 复核: 这组数在本卡六个 commit 里一路漂到 `:3231` 又**恰好绕回**
#: `:3104`(删 `_degraded_scan` 后总行数正好回到 3204, 与 f7f10be4 同) —— 纯属巧合,
#: 别据此以为这组标注稳定。要现值就跑下面那条命令。
#: ⚠️ 这组行号**会漂, 别照抄**: 上一版标注的 `:74/:2977/:2985/:3076` 在 `08100483`
#: 上实测已是 `:74/:3086/:3094/:3185`(早于本卡就漂了 109 行), 本卡的 `_harness_tree`
#: 重做再 +18。计数(4/4)才是基线, 行号只是找它们的线索 —— 要现值就重测:
#:   python -c "import re,pathlib;t=pathlib.Path('canvas-vault/.claude/skills/quiz-answer/SKILL.md').read_text(encoding='utf-8');\
#:   print([i+1 for i,l in enumerate(t.split(chr(10))) for _ in re.finditer(r'[.]claude/(?:skills|scripts)/',l)])"
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
#: ⛔ r21 MEDIUM-4: `CLS_BACKEND_URL[0]=''` 也让随后的 `:-` 取缺省(bash 里 `${V}`
#: 就是 `${V[0]}`), 只认裸名 `=` 会漏。
_URL_ASSIGN_RE = re.compile(r"(?<![{$:])\bCLS_BACKEND_URL(?:\[[^\]]*\])?\s*=")
#: ⛔ r21 MEDIUM-4: `printf -v CLS_BACKEND_URL %s ''` 把结果写进变量, 同样确定性清空。
#: ⛔ r22 MEDIUM-7: 必须锚在**命令段开头**且 `-v` 在 `--` 之前 —— 上一版整行搜,
#: 于是 `printf '%s' x; test -v CLS_BACKEND_URL`(只是查变量存在)与
#: `printf -- -v CLS_BACKEND_URL`(那是**参数文本**)都被误报。
#: ⛔ r23 MEDIUM-1: 段首可以有合法前缀 —— `builtin printf`、`{ printf`、`then printf`
#: 都确实会写变量, 只锚 `^\s*printf` 会漏。
_URL_PRINTF_V_RE = re.compile(
    r"^\s*(?:[{(]\s*|(?:then|else|do|!|builtin|command|exec)\s+)*"
    r"printf\s+(?:-(?!-)[a-zA-Z]*\s+)*-v\s*['\"]?CLS_BACKEND_URL\b"
)
#: `unset` 形态: 选项**只看紧跟其后的那些**(`-v` / `--`), 变量列表止于命令分隔符。
#: ⛔ r13 MEDIUM-1: 原先写 `(?![^\n;]*\s-{1,2}f\b)` 会越过命令边界 ——
#: `unset CLS_BACKEND_URL && curl -f "…"` 里 curl 的 `-f` 被当成 `unset -f` ⇒ 漏检。
_URL_UNSET_RE = re.compile(r"\bunset\b(?P<opts>(?:\s+-{1,2}[a-zA-Z]*)*)(?P<vars>(?:\s+[\w'\"]+)*)")
#: `${CLS_BACKEND_URL…}` 的一次参数展开(允许缺省值里再嵌一层花括号)。
_URL_EXPANSION_RE = re.compile(r"\$\{CLS_BACKEND_URL(?:[^{}]|\{[^{}]*\})*\}")
#: 只有「**未设置时**取缺省」的形态才真让外部配置说了算; `:+` / `+` 的语义正好反过来。
_URL_DEFAULTING_RE = re.compile(r"^\$\{CLS_BACKEND_URL:?-")


def _sh_protect_mask(line: str) -> list[bool]:
    r"""逐字符标注「这个位置在引号内 / 参数展开内 / 命令替换内」。

    ⛔ r20 与 r21 各错一次, 根因相同: `_strip_sh_comment()` 与「按 `;` 切命令段」都要
    回答同一个问题「这个字符是结构字符还是数据」, 却各写了一份状态机。这里统一成一个
    掩码, 两边共用。
    · `${…}` / `$(…)` 里的 `#` 是长度展开、`;` 不是命令分隔符 ⇒ 算被保护;
    · `$(…)` 内部有**自己独立的引号状态**(`"$(printf '%s' " #")"` 的内层引号不该与
      外层配对), 所以用栈存「进入这一层前的引号」;
    · `$'…'` 是 ANSI-C 引号, 里面的 `\'` 是转义单引号, 不结束引用;
    · 单引号内反斜杠是普通字符, 其余上下文里 `\x` 转义下一个字符。
    ⛔ 已登记不修: 跨**物理行**的引号内容(状态每行重置)。`_logical_lines()` 只合并
    反斜杠续行, 不合并引号内的换行。
    """
    mask = [False] * len(line)
    stack: list[tuple[str, str | None]] = []  # (期待的结束符, 进入这层前的引号)
    quote: str | None = None  # "'" / '"' / "$'"
    i, n = 0, len(line)

    def protected() -> bool:
        return quote is not None or bool(stack)

    while i < n:
        ch = line[i]
        if ch == "\\" and quote != "'" and i + 1 < n:
            # ⛔ r22 MEDIUM-2: 被转义的字符**永远**是数据, 与当前在不在引号里无关。
            # 上一版顶层写 `protected()`(=False), 于是 `printf %s \ #; unset …` 里
            # 那个转义空格被当成词分隔符 ⇒ 后面的 `#` 被当注释、真实的 `unset` 消失;
            # 转义的 `;` 同理会被 `_sh_segments()` 错切。
            mask[i] = mask[i + 1] = True
            i += 2
            continue
        if quote is None:
            if line.startswith("$'", i):
                mask[i] = mask[i + 1] = protected()
                quote = "$'"
                i += 2
                continue
            if ch in "\"'":
                mask[i] = protected()
                quote = ch
                i += 1
                continue
        elif (quote == "$'" and ch == "'") or (quote in ("'", '"') and ch == quote):
            mask[i] = True
            quote = None
            i += 1
            continue
        if quote not in ("'", "$'"):  # 单引号内不做任何展开
            # ⛔ r22 MEDIUM-3: 反引号命令替换要自己一层 ——
            # ``echo "`printf '%s' " #"`"; unset …`` 里没有这一层就会提前恢复外层引号。
            if ch == "`":
                if stack and quote is None and stack[-1][0] == "`":
                    mask[i] = True
                    _, quote = stack.pop()
                else:
                    mask[i] = protected()
                    stack.append(("`", quote))
                    quote = None
                i += 1
                continue
            # ⛔ r22 MEDIUM-3: `$( (:) ; … )` 里的裸 `(` 必须配对, 否则它的 `)` 会把
            # `$(` 提前闭掉。只在**已经进了展开层**时跟踪裸括号 —— 顶层的 `(`
            # 可能来自 `case x)` 这类不配对写法, 跟踪它会让整行后面全被当成数据。
            # ⛔ r23 MEDIUM-4: 只在**未被引用**时跟踪裸括号 ——
            # `echo "$(printf %s "(")"` 里那个 `(` 是双引号内的字面量, 压栈会让后面
            # 真正的注释识别整体错位。
            if ch == "(" and stack and quote is None:
                mask[i] = True
                stack.append((")", quote))
                i += 1
                continue
            # ⛔ r27 HIGH-1: 顶层 `(( … ))` 是**算术求值**, 里面的 `<<` 是左移不是重定向。
            # `$(( … ))` 走下面的 `$(` 分支已被覆盖, 裸 `((` 之前没人管。
            # ⛔ r28: 只在**未被引用**时才当算术 —— `echo "(("` 里那对括号是字面量,
            # 压栈会把后面真正的 heredoc 整个遮住。
            if quote is None and line.startswith("((", i):
                mask[i] = mask[i + 1] = True
                stack.append(("))", quote))
                quote = None
                i += 2
                continue
            if stack and quote is None and stack[-1][0] == "))" and line.startswith("))", i):
                mask[i] = mask[i + 1] = True
                _, quote = stack.pop()
                i += 2
                continue
            if line.startswith("${", i) or line.startswith("$(", i):
                mask[i] = protected()
                mask[i + 1] = True
                stack.append(("}" if line[i + 1] == "{" else ")", quote))
                quote = None  # 子层引号状态独立
                i += 2
                continue
            if stack and quote is None and ch == stack[-1][0]:
                mask[i] = True
                _, quote = stack.pop()
                i += 1
                continue
        mask[i] = protected()
        i += 1
    return mask


def _strip_sh_comment(line: str) -> str:
    r"""剥掉 shell 行注释; 引号内、参数展开内、命令替换内的 `#` 都不是注释。

    ⛔ r20 MEDIUM-1: 旧的 `re.split(r"(?<![\w$])#", …)` 把
    `printf "#"; unset CLS_BACKEND_URL; curl …` 截成 `printf "`, 后面**真实存在**的
    `unset` 整条漏检。
    ⛔ r21 MEDIUM-2: 第一版状态机不跟踪参数展开, `: ${OTHER:- #}; unset …` 又被截掉。
    POSIX: `#` 只在**词首**(行首, 或紧跟未被引用的空白/命令分隔符)才开启注释。
    """
    mask = _sh_protect_mask(line)
    for i, ch in enumerate(line):
        if ch != "#" or mask[i]:
            continue
        if i == 0 or (line[i - 1] in " \t;&|()<>" and not mask[i - 1]):
            return line[:i]
    return line


def _is_sh_separator(code: str, mask: list[bool], i: int) -> bool:
    """`code[i]` 是不是**命令分隔符**。

    ⛔ r24: `&` 不总是分隔符 —— `<&3` / `2>&1` / `&>log` 里它是**重定向**的一部分。
    上一版按字符切, 于是 `python3 - 3<<'A' <<'B' <&3` 被从 `<&` 中间切成两段,
    `<&3` 再也关联不到前面的 fd(实测踩到)。两个切段函数共用这一个判定, 免得再分叉。
    """
    ch = code[i]
    if ch not in ";&|\n" or mask[i]:
        return False
    # ⛔ r25 HIGH-4: 相邻那个 `<`/`>` 必须是**未被转义**的 —— `true \>& printf …` 里
    # `\>` 是普通参数, 后面的 `&` 就是真的分隔符。只看字符不看掩码会把 `printf` 拼进前段。
    if ch == "&" and (
        (i and code[i - 1] in "<>" and not mask[i - 1]) or (code[i + 1 : i + 2] == ">" and not mask[i + 1])
    ):
        return False
    return True


def _sh_segments(code: str) -> list[str]:
    r"""按命令分隔符切段 —— **引号与展开内部的分隔符不算**。

    ⛔ r21 MEDIUM-1: 旧的 `re.split(r"[;&|\n]+", code)` 会从单引号脚本中间切开 ——
    `env -i bash -c 'true; curl "${CLS_BACKEND_URL:-…}"'` 第一段只剩 `env -i bash -c 'true`,
    第二段才有目标变量, 关联丢失 ⇒ 原本能抓的形态, 只加一个 `true;` 就漏。
    """
    mask = _sh_protect_mask(code)
    out: list[str] = []
    cur: list[str] = []
    for i, ch in enumerate(code):
        if _is_sh_separator(code, mask, i):
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return [seg for seg in out if seg.strip()]


def _sh_strip_quotes(word: str) -> str:
    r"""只去掉**引号定界符**, 保留其余一切(尤其是反斜杠)。

    ⛔ r22 MEDIUM-4: URL 边界不能在**带引号的原串**上判 —— 三种写法都会骗过它:
    `"http://h:80/path?target=${V:-…}/x"`(`=` 被当 token 分隔符)、
    `"http://h:80/""${V:-…}/x"`(相邻引号拼成同一个参数)、
    `"${V:-…}"@localhost/x`(结束引号隔断了 `@` 检查)。剥掉定界符后三者都现形。
    ⛔ **反斜杠必须留着**: `"curl \${V:-…}/x"` 里 `\$` 表示留给子 shell 展开,
    与外层直接展开的 `${V:-…}` 是两回事(r22 MEDIUM-5)。去转义会把两者抹平。
    """
    out: list[str] = []
    quote: str | None = None
    i, n = 0, len(word)
    while i < n:
        ch = word[i]
        if ch == "\\" and quote != "'" and i + 1 < n:
            nxt = word[i + 1]
            # POSIX: 双引号内 `\\` 只对 `$ \\ " 换行 反引号` 特殊, 其中两类含义不同 ——
            # `\\"` / `\\\\` 是**结构**(外层 shell 吃掉反斜杠, 那个引号交给内层当定界符),
            # `\\$` / `` \\` `` 是**延后展开**(留给子 shell 自己展开, 与外层直接展开是两回事)。
            # 只对前者去转义: 保住 r22 MEDIUM-5 那条区分, 同时让内层引号能被下一轮剥掉。
            if quote == '"' and nxt in '"\\':
                out.append(nxt)
            else:
                out.append(ch)
                out.append(nxt)
            i += 2
            continue
        if quote is None and ch in "\"'":
            quote = ch
        elif quote is not None and ch == quote:
            quote = None
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _url_token_is_controlled(token: str) -> bool:
    """这个含 `8011` 的**已剥引号的 token**, 地址是不是由 `${CLS_BACKEND_URL:-…}` 决定。

    判准: 剥掉可能的 `--opt=` / `NAME=` 前缀后, 该展开必须**从 token 的第 0 位开始**,
    且后面紧跟的不是 `@`(否则它落进 userinfo, 真实主机在 `@` 之后)。
    """
    body = re.sub(r"^(?:--?[\w-]+=|[A-Za-z_]\w*=)", "", token)
    for e in _URL_EXPANSION_RE.finditer(body):
        if e.start() != 0 or not _URL_DEFAULTING_RE.match(e.group(0)) or "8011" not in e.group(0):
            continue
        # ⛔ r23 MEDIUM-3: 只看**紧邻**展开的字符不够 ——
        # `"${V:-…}":pw@localhost/x` 里紧邻的是 `:`, 真正的主机仍是 `@` 之后的。
        # 判据改成: 展开之后、到第一个 `/` `?` `#` 之前的整段(= authority)里不得有 `@`。
        authority = re.split(r"[/?#]", body[e.end() :], maxsplit=1)[0]
        if "@" not in authority:
            return True
    return False


def _url_word_hits(word: str) -> bool:
    """这个词里有没有**任何一处** `8011` 不受目标变量控制。

    ⛔ r22 MEDIUM-5: 上一版「一处受控就放行整词」——
    `bash -c "curl \\${V:-…}/x; curl ${V:-…}/y"` 的第二处由外层展开、清环境管不着,
    却因为第一处受控而整词放行。改成**逐处**检查。
    """
    for tok in _sh_strip_quotes(word).split():
        # ⛔ 剥到**不动点**: 被引号包住的整条 shell 脚本本身还有自己的引号层 ——
        # `'curl "${V:-…}/x"'` 剥掉外层单引号后 token 仍是 `"${V:-…}/x"`,
        # 展开就不在第 0 位, 会把合规写法误报(实测踩到)。
        while (stripped := _sh_strip_quotes(tok)) != tok:
            tok = stripped
        if "8011" in tok and not _url_token_is_controlled(tok):
            return True
    return False


def _env_clears_url(segment: str) -> bool:
    r"""这一条命令是「`env` 清掉 `CLS_BACKEND_URL` 后由**子 shell 自己**再展开缺省 URL」?

    ⛔ r20 MEDIUM-3 是**双向**的:
    · 漏检 —— `--ignore-environment` 是 `-i` 的长名, `-uCLS_BACKEND_URL` 是**粘连**写法,
      上一版两者都认不出, 而两种都确定性清掉配置。
    · 误报 —— `env -i bash -c 'true'; curl "${CLS_BACKEND_URL:-…}"` 清的是**无关子进程**
      的环境, 跟后面那条 curl 没关系。所以本判据**逐命令段**跑(`_sh_segments()` 是引号
      感知的切法, r21 MEDIUM-1: 按原文切 `;` 会把单引号脚本从中间切开), 且要求 `-c`
      脚本里真的出现该变量。
    · 误报 —— `env -i bash -c "curl ${CLS_BACKEND_URL:-…}"` 用**双引号**, URL 由外层
      shell 先展开完了才交给 env, `env` 撤销不了已经在参数里的值。
    ⛔ r21 MEDIUM-1 的三处词法漏检一并补上: 组合选项 `bash -lc '…'`、ANSI-C 引号
    `bash -c $'…'`、以及双引号脚本里把 `$` **转义**留给子 shell 展开的 `"curl \${VAR:-…}"`。
    ⛔ 登记不修(需要数据流, 不是词法): `SCRIPT='curl …'` 后 `env -i bash -c "$SCRIPT"`
    —— 脚本正文在另一条语句里, 本判据只看这一段的字面。
    """
    m = re.search(
        # ⛔ r22: 选项的「空格分隔参数」只放给 `-u` / `--unset` —— 写成通用的
        # `[= ]\s*[\w'\"]+` 时, `env -i bash -l -c …` 里 `bash` 会被当成 `-i` 的参数吃掉,
        # `sh` 组于是捕到 `-l`, 整条判据静默(实测踩到)。
        # shell 名也放进正则参与回溯, 否则引擎在错误的切分上「匹配成功」就不再尝试。
        # ⛔ r23 MEDIUM-2: `-u "VAR"` 的**闭引号**也要消费掉, 否则整条匹配失败。
        r"\benv\b(?P<opts>(?:\s+(?:-u|--unset)[= ]\s*(?P<q1>['\"]?)\w+(?P=q1)|\s+-{1,2}[\w-]*(?:=['\"]?\w+['\"]?)?)*)"
        # ⛔ r23 MEDIUM-2: `-cl` 与 `-lc` 都要认 —— `c` 不一定在选项串末尾。
        r"\s+(?P<sh>\S*(?:sh|bash|zsh|dash))(?:\s+-(?!-)[a-zA-Z]*)*?\s+-[a-zA-Z]*c[a-zA-Z]*\s+(?P<rest>.*)$",
        segment,
    )
    if not m or not re.search(r"\b(?:sh|bash|zsh|dash)$", m.group("sh")):
        return False
    opts = m.group("opts") or ""
    cleared = any(opt in {"-i", "--ignore-environment"} for opt in opts.split()) or bool(
        re.search(r"(?:-u|--unset)[=\s]*['\"]?CLS_BACKEND_URL\b", opts)
    )
    if not cleared:
        return False
    # ⛔ r22 MEDIUM-8: `bash -c SCRIPT ARG0 ARG1 …` —— `-c` 后面**只有第一个词**是脚本,
    # 其余是位置参数($0/$1…)。上一版 `(?P<script>.*)$` 把参数也吃进来, 于是
    # `env -i bash -c 'true' "${CLS_BACKEND_URL:-…}/x"`(URL 由外层 shell 展开、
    # `env` 根本管不着)因为「脚本里出现了该变量」而误报。
    words = _shell_words(m.group("rest"))
    script = words[0].strip() if words else ""
    if "CLS_BACKEND_URL" not in script:
        return False
    # 只认单引号 / ANSI-C 引号: 整段原样交给子 shell, 由它展开。
    # 双引号脚本一律不认 —— 外层 shell 会先展开。
    # ⛔ 这里**没有**「双引号里 `$` 被转义就算」的分支: 写过一版, 回退验证发现它
    # **恒不决定结果** —— `\$` 出现在展开前面, 就使那个展开不再是 URL token 的开头,
    # 于是词级判据 `_url_word_is_controlled()` 必然已经报了。留着只会让人以为是它在承重。
    return script.startswith(("'", "$'"))


def _url_override_hit(line: str) -> bool:
    r"""这一行有没有把 `${CLS_BACKEND_URL:-…}` 的缺省形态**架空**?

    三类: 直接赋值 / `unset` 掉 / `env` 清环境后由**子 shell** 再展开。
    ⛔ 注释先剥掉(r19): `# unset CLS_BACKEND_URL` 之类不是命令, 三个分支都要剥,
    上一版只在 `env` 分支剥了。
    ⛔ `env -i curl "${X:-…}"` 的 URL 由**外层 shell** 先展开, `env` 撤销不了已在参数里
    的值 ⇒ 不算; 只有 `env -i sh -c '…'` / `bash -c '…'` 这种**清环境后子 shell 再展开**
    才算(r18 MEDIUM-6)。而 `env -u OTHER sh -c '…'` 删的不是目标变量 ⇒ 也不算(r19)。
    ⛔ 残余(登记不修): `unset C'LS'_BACKEND_URL` 这类引号拼接出的变量名认不出。
    """
    code = _strip_sh_comment(line)
    if _URL_ASSIGN_RE.search(code):
        return True
    if any(_URL_PRINTF_V_RE.match(seg) for seg in _sh_segments(code)):
        return True
    for segment in _sh_segments(code):
        for word in _shell_words(segment):
            if _url_word_hits(word):
                return True
    # ⛔ r25 MEDIUM-2: `unset C'LS'_BACKEND_URL` 的变量名完全由**字面词**确定, 只是被
    # 引号拆开了。按命令词定位 `unset` 后, 把后续词逐个去引号再比 —— 不整行去引号,
    # 免得把 `printf '%s' 'unset CLS_BACKEND_URL'` 这类**数据**也算成命令。
    for segment in _sh_segments(code):
        # ⛔ r26 MEDIUM-2: `unset` 必须是这一段的**命令词**(前面只允许 `VAR=值` 赋值前缀)。
        # 逐词找的话, `printf '%s %s' unset CLS_BACKEND_URL` 只是打印两个字符串, 却被
        # 当成删除变量 ⇒ 误报。选项词也要**一起**去引号, 否则 `unset '-f' …` 认不出 `-f`。
        # ⛔ r27 MEDIUM-1: 命令词前面除了 `VAR=值`, 还可以有 `command` / `builtin` /
        # `exec` / `!` 这些合法前缀, 以及前置重定向 —— 它们都不改变「这是一条 unset」。
        words = _shell_words(segment)
        k = 0
        while (
            k < len(words)
            and (
                re.fullmatch(r"[A-Za-z_]\w*=.*", words[k])
                # ⚠️ **已登记的保守误报**(r29 LOW-3): `"{" unset CLS_BACKEND_URL` 里那个
                # **被引号包住**的 `{` 是命令名而不是语法前缀, 这里去引号后当成前缀 ⇒ 多报。
                # 同上, 方向是误报, 代价是一条登记。
                # ⛔ r28: 复合命令的 `{` / `(` 也是前缀 —— `{ unset X; }` 里 `unset` 仍是命令词。
                or _sh_strip_quotes(words[k]) in {"command", "builtin", "exec", "!", "time", "nohup", "{", "("}
                or _REDIR_RE.fullmatch(words[k])
                or words[k][:1] in "<>"
            )
        ):
            k += 1
        if k < len(words) and _sh_strip_quotes(words[k]) == "unset":
            rest = [_sh_strip_quotes(x) for x in words[k + 1 :]]
            if not any("f" in x.lstrip("-") for x in rest if x.startswith("-")):
                if "CLS_BACKEND_URL" in rest:
                    return True
    # ⛔ r27 MEDIUM-2: 这里原本还有一遍 `_URL_UNSET_RE.search(segment)` 的**后备正则**,
    # 它没有位置约束, 于是 `printf '%s %s' unset CLS_BACKEND_URL`(只是打印两个字符串)
    # 照样报红 —— r26 我加的「命令词」检查被它整个绕过去了。上面那圈已经覆盖它的全部
    # 真形态(含引号拼接的变量名), 后备正则删除。
    for segment in _sh_segments(code):
        if _env_clears_url(segment):  # r20 MEDIUM-3: 逐段判, 别把无关子进程的清环境算上
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
      · 对**已取到的块**没有解析、没有正则边界、没有缩进猜测 ⇒ 那一段几乎没有回归空间
        (但取块本身仍依赖分块与 `/tmp` 筛选, 见下面的更正);
      · 对形态表 51 个反例实测 **45 个可区分**(其余 6 个是 URL/`unset` 类,
        不含 `/tmp`, 归第九条判据);
      · 树上代价 12 项(逐块/逐行), 见 `TMP_BLOCK_BASELINE`。

    与 ④~⑨ 的关系是**互补而非取代**: 那九条告诉你「是哪一类问题」(报错信息里有
    形态名), 这条保证「**在它取到的候选范围内**, 块变了就红」。r13 MEDIUM-3 指出的
    「多行 opaque 记录只绑首行 ⇒ 换第二行仍静默」也由它直接封住。

    ⛔⛔ r28 更正(本条 docstring 原先写的是「不管什么形态, 块变了就红」, **那句是错的**):
    这条判据在**输入过滤器**上就用**连续 `/tmp`** 筛 —— 于是
        ROOT = "/t"
        P = ROOT + "mp/cls-exam/../x"
    这类**拆分常量根本进不了指纹集合**, 前十条(含本条)全部静默。防线的覆盖面等于它的
    **输入面**, 不等于它的判定质量。这个盲区由**第十一条**(整文件字节摘要)收口。
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


#: ⛔⛔ **第十一条判据 = 结构性收口**(2026-09-09, Codex r28 建议)。
#:
#: 立它的理由是 r20~r27 八轮的数据: HIGH 数 2/2/3/3/5/6/6/4/5, **从未到 0**。
#: 判据 ④~⑨ 要做的事本质上是在手写代码里复现 Markdown + shell + Python 三层语义;
#: r13 加的第⑩条兜底网本该封住这一类, 但 r28 指出它**在输入过滤器上就有洞** ——
#: `tmp_block_fingerprints()` 用**连续 `/tmp`** 筛输入, 于是
#:
#:     ROOT = "/t"
#:     P = ROOT + "mp/cls-exam/../x"      # 把 `..` 换成 `a` 就是安全对照
#:
#: 这类拆分常量**根本进不了指纹集合**, 九项计数、五项路径判据、URL 判据、块指纹全空。
#:
#: 这一条反过来: **不看内容是什么, 只看这些文件有没有变**。
#:   · 整文件原始字节的 sha256, **不依赖** `/tmp`、语言标签、Markdown 分块、AST;
#:   · 文件集合精确钉死 —— 新增/删除受管文件同样红;
#:   · 代价明确: 普通文字修改也要更新快照。这是**刻意**的 —— 更新快照 = 接受一次
#:     人工审核, 不等于债务消除。
#:
#: ⚠️ 它**不**证明任何路径构造安全, 只保证「受管文件的路径集合与原始字节摘要一致」。
MANAGED_FILE_DIGESTS: dict[str, str] = {
    "skills/ai-linked-doc/SKILL.md": "f3673ca9529eaeff1358b50e11b4a9455a12f137cd676a4d1568f5f29b2ae176",
    "skills/board-recap/SKILL.md": "86ff0b3fa0179604816e9251ae35bcf0df6151f7cdc62a4ef88dd46bed4c3aa4",
    "skills/chat-with-context/SKILL.md": "cdd0472591e75860e947aa726dcbd46aa150e3eaa1ceef50be6dee332af2738c",
    "skills/configure-whiteboard/SKILL.md": "9eb21ecc6ac044a914ce11009025f8a84e51c5135221ec3b50f8c021ccfa2177",
    "skills/exam-quick/SKILL.md": "eb30e407a14145477710cbf439e7e85705afeb157c98c5993ee0b3616c324853",
    "skills/node-chat/SKILL.md": "3b15bc91dabea7e7b3876b75c2c0973e7a9284d48081e5d1b864623258b40fb7",
    "skills/quiz-answer/SKILL.md": "6ae2558f1def3e94588bf0a043bb2d9e4b5904a618de5ec4b5260f5c206601b0",
    "skills/start-exam-board/SKILL.md": "0f2c085a1bae12446dd74ab89cc1e6aa5c8bc34901dd3be7ac5d8521310d0dce",
    "skills/study-question/SKILL.md": "0142b7833ff3ab54c9307227d59ebaa7d5ff3f9c18a76b07344d0ab295fa22e4",
    "scripts/decay_beta.py": "3bf4ed9402a4c8edfde16630a79094a5d4518fd181fa60810319fe46d37abb90",
    "scripts/fsrs_bridge.py": "a766fbcc28e3ff917e740843c633e800aa8a75e949295f83efc90f55105f90f0",
    "scripts/sync_board_concepts.py": "282b7a968033f622cba03fae57e4330424c2465ad08d73f5abdc8f3162f6d123",
    "skills/board-recap/scripts/recap_exam_build.py": "cf6a60b5159e2627acea6814fed0c546a1e8f684c0ab38c1a63407f5b553e771",
    "skills/board-recap/scripts/recap_scan.py": "7ec79cba1e6b47f8463c138d2b26b7484d47c26f57928cc77c26387daf117e0e",
    "skills/board-split/scripts/split_preview.py": "d088c5e38f0c6eb0f9ca98a547bb4a06a9e45eed722dbdd604a7b578602ab7ad",
    "skills/clear-inbox/scripts/inbox_preview.py": "a2b97f068445d9b441262c4eb02f72071b06483e4f91d884e274b71eb631e565",
}


def _root_untrustworthy(root: Path) -> str | None:
    """受管**根本身**可信吗 —— 返回问题描述, `None` 表示可信。

    ⛔ r30 MEDIUM: `_real_relpath()` 逐级核对的是根**以下**的分量, 根自己没人查。
    把整个 `.claude` 换成指向同内容目录的符号链接时, `glob()` 与 `read_bytes()` 都会
    沿根链接走, **路径键与摘要一个都不变**, 门照绿。大小写不敏感文件系统上根名的
    大小写变化属同一个遗漏。
    """
    if root.is_symlink():
        return f"受管根本身是符号链接: {root}"
    try:
        entries = os.listdir(root.parent)
    except OSError as exc:
        return f"受管根的父目录读不出来: {root.parent} ({type(exc).__name__})"
    if root.name not in entries:
        return f"受管根的目录项名字不符(大小写?): 期望 {root.name!r}, 父目录里没有这个名字"
    return None


def _real_relpath(root: Path, path: Path) -> str | None:
    """按**实际目录项**拼出相对路径; 任一分量是符号链接则返回 None。

    ⛔ r29 MEDIUM-1: 只用 `glob` 的字面结果有三个静默面 ——
      · 普通文件换成指向同内容的**符号链接**, 摘要与键都不变;
      · **目录分量**也能用符号链接把读取引到受管根之外;
      · 大小写不敏感的文件系统上 `SKILL.md → skill.md` 改名后, 字面 glob 仍能找到它,
        而键名是硬编码的 `SKILL.md` ⇒ 改名静默。
    所以逐级用 `os.listdir()` 的**真实名字**核对大小写, 并拒绝任何一级符号链接。
    """
    parts: list[str] = []
    cur = root
    for want in path.relative_to(root).parts:
        try:
            entries = os.listdir(cur)
        except OSError:
            return None
        if want not in entries:  # 大小写不一致时 `glob` 找得到, 这里找不到
            return None
        cur = cur / want
        if cur.is_symlink():
            return None
        parts.append(want)
    return "/".join(parts)


def managed_file_digests(root: Path) -> dict[str, str]:
    """受管文件 → 整文件原始字节的 sha256(**全长**)。

    刻意**不读文本、不按行、不解码** —— 换行风格、BOM、尾随空白的任何变化都要留痕。
    ⛔ r29 LOW-2: 用全部 64 个十六进制字符。前 16 位只有 64 bit, 对固定基线的普通回归
    检测够用(误同约 `2^-64`), 但它**不是**完整 SHA-256, 不该写成「任何字节变化必红」。
    ⚠️ 文件**模式**(chmod)不属于字节, 明确不在本判据覆盖面内。
    """
    out: dict[str, str] = {}
    seen: list[Path] = [
        *root.glob("skills/*/SKILL.md"),
        *root.glob("skills/*/scripts/*.py"),
        *root.glob("scripts/*.py"),
    ]
    for f in sorted(seen):
        rel = _real_relpath(root, f)
        if rel is None:
            out[f"⚠️不可信路径:{f.relative_to(root)}"] = "符号链接或大小写不符"
            continue
        out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def check_managed_files(root: Path, baseline: dict[str, str]) -> list[str]:
    """第十一条判据: 受管文件集合与整文件摘要**精确相等**。"""
    problems: list[str] = []
    if (why := _root_untrustworthy(root)) is not None:
        # 根不可信时后面的枚举与摘要全都不能采信 —— 直接判红, 不再往下比。
        return [f"[受管文件] {why} —— 受管根必须是真实目录且名字逐字符相符"]
    actual = managed_file_digests(root)
    for rel in sorted(set(baseline) - set(actual)):
        problems.append(f"[受管文件] 缺失: {rel} —— 基线要求它存在")
    for rel in sorted(set(actual) - set(baseline)):
        problems.append(f"[受管文件] 新增: {rel} sha16={actual[rel]} —— 新文件必须先登记再纳管")
    for rel in sorted(set(baseline) & set(actual)):
        if baseline[rel] != actual[rel]:
            problems.append(
                f"[受管文件] 内容变化: {rel}\n"
                f"        基线 {baseline[rel]}  实测 {actual[rel]}\n"
                f"        —— 更新这个摘要表示**接受一次人工审核快照**, 不等于债务已消除"
            )
    return problems
