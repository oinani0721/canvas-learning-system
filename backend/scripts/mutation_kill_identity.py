#!/usr/bin/env python3
"""变异负控的**击杀身份**判据 —— 四套 harness 共用的那一层。

## 它解决的问题

本仓已经发生过**两次假杀**，两次都过了当时的全部裁判：

1. `Z2 第一版 M1` —— 击杀由**同时施加的层**贡献，变异体本身毫无鉴别力；
2. `Z2 HEAD 的 M15` —— 变异体两行、缩进错位，写点子进程在**编译期**就死。
   于是「防线被拆掉之后本该发生的坏事」根本没机会发生，账本 0 行，
   卡文声称的那条断言(`同 event_id 被写了两遍`)**反而通过**，真正红的是
   另一条(`拒因不对`)。门红了、`rc == 1`、nodeid 也在失败集里 —— 三条
   老判据全都成立，而结论是错的。

共同的根：`rc == 1 and <门名> in out and "failed" in out` 这种判据只能回答
「**有没有**红」，回答不了「红在**哪一条断言**上」。本模块把 CARD-G3-3-R1 在
`g33_mutation_gates.py` 上做出的两道封堵抽成共用件，供 g32b / g32cb / g32ccr1
/ g33 一起调用：

* `syntax_check()` —— 施加变异后、跑门**之前**先编译。不通过 ⇒ 裁决
  `SYNTAX-INVALID`：既不算 KILLED 也不算 SURVIVED，因为它照出的是**负控自己
  坏了**，不是被测物坏了。
* `kill_identity()` / `kill_identity_ok()` —— 击杀必须落在**声称的那一条断言**上。

## round-19（CARD-DEBT-mutkill-R2）：判据从「消息子串」改成「断言源位置」

Y1-B 外审两条 HIGH 在本树上**当场复现**（证据
`_bmad-output/审查/evidence-mutkill-r2/`，pytest 9.0.2）：

* **HIGH-1「前提断言把子进程输出插进首行」**：做一个门函数，前提断言写成
  `assert r.returncode == 0, r.stderr[:250]`（第 12 行），目标断言
  `assert False, "不得再推进"`（第 14 行）。被测子进程往 stderr 打
  `"不得再推进" + "水位线"` 并 rc=1 ⇒ 前提断言先红、目标断言**根本没执行**，
  而 `-rf` 短摘要是
  `FAILED …::test - AssertionError: 不得再推进水位线 extra tail`
  —— `EXPECT_MSG["M142-dup-uses-global-w"] == "不得再推进水位线"` 逐字命中。
  ⛔ 换 `^E ` 行**也救不了**：实测 `--tb=line` 同样打 `E   AssertionError:
  不得再推进水位线 extra tail`，那一行的内容同样是子进程拼出来的。
  ⇒ **任何基于消息文本的判据都分不开前提断言与目标断言**。能分开的只有
  **位置**：短摘要之外 pytest 还打一行 `<门文件>:12: AssertionError: …`，
  12 是前提断言、14 才是目标断言。这就是 `expect_loc` 的由来。
* **HIGH-2「captured 区伪 FAILED 行」**：门函数把
  `FAILED <nodeid> - <expect_msg>` 打进 stdout，pytest 在
  `--- Captured stdout call ---` 区原样回显 ⇒ 旧的 `findall(整份输出)` 把它
  收进失败集。实测该行落在 `=== short test summary info ===` 分隔线**之前**
  ⇒ 只在摘要区 `findall` 即可拒掉。

配套两道结构性收紧：

* `judge_flags()` 统一四套的 pytest 命令行，其中 `--show-capture=no` 让
  captured 区**根本不产生**。
  ⛔ **口径更正（Codex round-7 LOW）**：此前这句写「判据面里不再有任何被测进程可控的
  字节」——**说宽了**，且与 `judge_flags()` 里已改好的说明自相矛盾。它只关掉 captured 区；
  被测进程的文字仍可经**别的**路子进 FAILURES 区（门里自己写的
  `assert r.returncode == 0, r.stderr[:250]` 就把子进程 stderr 塞进了断言消息）。
  真正兜住「伪造判据面」的是 `summary_region()` 只取摘要区 + `expect_loc` 的位置绑定，
  本开关只是把最便宜的一条路堵掉。
  （代价如实说：SURVIVED 诊断时看不到子进程原文，要人工重跑一次。）
* `PYEOF_RE` 的终止符收紧为**行首锚定 + 只许尾随空白**（见该常量的注释）。

## 判据面为什么取 `-rf` 短摘要 + `--tb=line` 位置行

* 整份 stdout：pytest 的 long traceback 会把**整个测试函数的源码**打出来，于是
  该函数里每一条断言的消息串都出现在输出里 —— `expect_msg in out` 等于恒真，
  「判据被自己要找的东西喂饱」。
* `E ` 行 / 短摘要 reason：都只是**消息文本**，被上面的 HIGH-1 证明不足以定身份。
  它们仍然保留在判据里（`expect_msg`），但只作为**与位置 AND 起来**的第二维，
  ⛔ 绝不是「消息或位置二选一」。
* `--tb=line` 位置行 `<file>:<lineno>: <Exc>: <msg>`：pytest 自己算出来的失败
  语句位置，被测进程改不了它。这是唯一能把「红在哪一条断言上」问清楚的面。

⚠️ 配套硬约束（少一条判据就退化成恒不命中的**假 SURVIVED**）：
  1. harness 的 pytest 命令必须带 **`-rfE`**（Codex round-8 LOW：此前这条硬约束写的是
     裸 `-rf`，照它配会**再次漏掉 ERROR 行** —— `-r` 的字符串是**替换**默认 `fE` 的，
     见 `judge_flags()` 里那段实测。没有短摘要行则判据面整个不存在）；
  2. 必须带 `--tb=line`（否则没有位置行，`expect_loc` 恒不命中）；
  3. 必须设 `COLUMNS` 足够大 —— 80 列下 `FAILED … - <reason>` 的 reason 会被
     截成空串；用 `judge_env()` 拿这份环境。
  ⛔ **口径更正（Codex round-7 LOW）**：此前这句写「三条都由 `judge_surface_missing()`
  在每次判定前当场检查」——**只有前两条是**。它查的是「摘要区在不在 / 有没有 FAILED 行 /
  （需要时）有没有位置行」；**第 3 条（`COLUMNS` 够不够宽）它根本不查** —— reason 被截断
  时摘要行仍然完好，判据面看起来是成立的，只是 `expect_msg` 恒不命中 ⇒ 静静地报 SURVIVED。
  兜住第 3 条的是 `judge_env()` 把 `COLUMNS=1000` 发下去（四套都从这里取），
  **不是**一道运行期检查。⚠️ 这意味着：谁绕过 `judge_env()` 自己拼环境，这条就失守。

## `expect_msg` 的取值纪律

必须在它绑定的**门文件**里恰好出现 1 次（`check_expect_msg_unique()` 是门，不是
建议）：不唯一 ⇒ 「红在哪一条断言上」不再可证。且必须是断言消息的**首行字面
片段** —— 绑到第一个 `{}` 插值之后的内容，短摘要里根本没有，判据恒不命中。

## `expect_loc` 的取值纪律

取值形如 `"stmt:<12 位十六进制>"`：门文件里那条**语句**经 `ast.dump(...,
include_attributes=False)` 规范化后的 sha256 前 12 位。

* **与行号无关** ⇒ 门文件上下插入行不会让它失配（MEMORY:
  `reference_line_numbers_must_be_remeasured_not_extrapolated` 的反面）；
* **与注释、空白无关** ⇒ 给断言加注释不会失配；
* 语句本体一旦被改写，门文件里就**找不到**这个指纹 ⇒ 判 `HARNESS-ERROR`
  「锚漂了」，而**不是**静默 SURVIVED（后者会把「门被别的卡改了」伪装成
  「防线失效」）；
* `check_expect_loc_unique()` 要求每个指纹在门文件里**恰好命中 1 条语句** ——
  同一份代码写两遍时身份不可证。

⚠️ 落在**门文件之外**的失败（如变异让门以未捕获异常死在第三方库里）**没有**位置身份
可绑：`expect_loc` 留空 + 消息/位置两张豁免表都写理由 ⇒ 判 `KILLED-UNBOUND`。
（`loc_token_for()` 仍会产出 `file:<basename>` 形态的 token，但那只是 probe 的观察
输出与 mismatch 诊断，**不是**可登记的期望值。）
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import os
import re
import signal
import traceback
from pathlib import Path

__all__ = [
    "PYEOF_RE",
    "RESTORE_SIGNALS",
    "RestoreGuard",
    "VERDICTS",
    "check_expect_loc_unique",
    "check_expect_msg_unique",
    "failed_locations",
    "exactly_one_failed",
    "failed_reasons",
    "failure_records",
    "failures_region",
    "gate_hit",
    "judge_env",
    "judge_flags",
    "judge_surface_missing",
    "kill_identity",
    "kill_identity_ok",
    "loc_token_for",
    "matched_loc_tokens",
    "parse_failed_nodeids",
    "unparsed_failure_lines",
    "line_stmt_ambiguous",
    "stmt_fingerprints",
    "summary_region",
    "syntax_check",
]

#: 四套 harness 统一的裁决枚举（CARD-DEBT-mutkill-R2 (g)，用户裁定 D-28 六档）。
#:
#: ⛔ 六档**一个都不能并**：
#:   · `ANCHOR-ERROR`   —— 变异**根本没打进去**（锚点命中数 != 1）。并进 KILLED
#:     就是把「没施加」读成「杀了」，并进 SURVIVED 就是读成「防线失效」；
#:   · `SYNTAX-INVALID` —— 变异体编译期就死，门是被**别的**断言打红的（假杀的
#:     结构性形态，Z2 M15 就是它）；
#:   · `HARNESS-ERROR`  —— rc 不是 1，或判据面本身不存在。这是**负控自己坏了**，
#:     不是关于被测物的结论；
#:   · `KILLED-UNBOUND` —— 门红了，但没绑上「红在哪一条断言上」。它证明的东西
#:     **比 KILLED 少**，合并上报就是把结论说得比证据宽（Y1-B HIGH-3）。
VERDICTS: tuple[str, ...] = (
    "KILLED",
    "KILLED-UNBOUND",
    "SURVIVED",
    "HARNESS-ERROR",
    "ANCHOR-ERROR",
    "SYNTAX-INVALID",
)

#: SKILL.md 里可执行写点的提取正则。
#:
#: ⚠️ 这里**故意比** `test_g3_3_cas.py:36`(以及 `g33_mutation_gates.py` 原实现)
#: 的 `python3 - <<'PYEOF'` **宽**：`start-exam-board/SKILL.md:246` 的引导行是
#: `python3 - "节点/<target>.md" <<'PYEOF'`(中间带参数)，窄正则**匹配不到**，
#: 那一整块从来没被编译自检覆盖过。窄正则漏掉的块正是「变异体编译期就死」最容易
#: 藏身的地方 —— 自检的覆盖面比门本身的覆盖面窄，等于自检有个洞。
#: 2026-09-06 实测：两个 SKILL.md 在**未变异**状态下，广义提取到的全部 5 块
#: (quiz-answer 2 + start-exam-board 3) 逐块 `compile()` 均通过 ⇒ 放宽不会把
#: 干净的树误判成 SYNTAX-INVALID。
#:
#: ⛔ round-19 (CARD-DEBT-mutkill-R2 (i)) 修 Y1-B LOW-9 的边界洞。
#: ⚠️ 洞的形态**以实测为准**（`evidence-mutkill-r2/pyeof-negctl-*.txt` 六形态对照）——
#: 本条注释的初稿写的是「终止行带尾随空格会匹配不上」，实测**不成立**（旧写法
#: `\nPYEOF` 没有结尾锚，`PYEOF  \n` 照样匹配）。真正量到的三个洞是：
#:   ① 块内出现**行首**以 `PYEOF` 开头但不是终止符的行（如 `PYEOFX = 2`）⇒ 旧版
#:      在那里**提前截断**，后半段代码逃出编译自检 —— 假杀正好藏在没被编译的那半段；
#:   ② 引导行 `<<'PYEOF'` 之后带**尾随空白** ⇒ 旧版整块**匹配不到**，`findall`
#:      返回空 ⇒ 那一块的编译自检**恒通过**（假绿，比 ① 更隐蔽）；
#:   ③ CRLF 行尾 ⇒ 旧版同样整块匹配不到（与 ② 同一个假绿面）。
#: 现在：引导行允许尾随空白与 `\r`；终止符必须**独占一行**（`^` + `re.M`）且其后
#: 只许空白到行尾。⇒ ① 不再提前截断，②③ 不再静默漏掉整块。
PYEOF_RE = re.compile(r"<<'PYEOF'[ \t]*\r?\n(.*?)\r?\n^PYEOF[ \t]*\r?$", re.DOTALL | re.MULTILINE)

#: `-rf` 短摘要行。reason 可缺失(没有断言消息时 pytest 只打 `FAILED <nodeid>`)。
#: ⛔ round-19：只在 `summary_region()` 里 findall，不再对整份输出扫（HIGH-2）。
_FAILED_RE = re.compile(r"^(?P<status>FAILED|ERROR) (?P<nodeid>\S+?)(?: - (?P<reason>.*))?$", re.M)


def _nodeid_shaped(s: str) -> bool:
    r"""`s` 能否**整体**读成一个合法的 pytest nodeid（= 一种「无 reason」读法）。

    nodeid 的结构约束只有两条，⛔ 都只能锚**两端**、不能锚内部：
      · 参数段之前那截（`path::test_name`）**不含空白**；
      · 有参数段时，它从最后一个 `::` 之后那截里的**第一个** `[` 起、到整串**末尾的
        `]`** 止 —— 参数 ID 内部什么字符都可能出现（空格、` - `、`[`、`]`），内部不可约束。

    ⛔ **参数段起点只能"存在量化"，不能固定取某一个 `[`**。两次固定取法都被反例打掉：
      · 取**整串第一个 `[`** —— 路径段本身可含方括号（`tests/test_[x].py::test_x` 是合法
        nodeid），于是「不以 `]` 收尾」⇒ 判它不是 nodeid 形 ⇒ 一条**合法的无 reason 摘要
        行**被打成不可判定 ⇒ 假 HARNESS-ERROR（Codex round-1 MEDIUM）；
      · 取**最后一个 `::` 之后** —— 参数 ID 里可以有 `::`（`…::test_x[case] - EXPECT[x :: y]]`
        的参数 ID 是 `case] - EXPECT[x :: y]`），于是 `rpartition("::")` 切在参数内部、
        前缀含空白 ⇒ 这条**真实的参数读法被漏掉** ⇒ 二义行重新被判唯一 ⇒ 假 KILLED
        （Codex round-2 HIGH，本函数上一版引入的回归）。
    ⇒ 判据写成：以 `]` 收尾时，**存在某个 `[`** 使它之前那截同时满足
      ① 不含空白；② 含 `::`；③ **最后一个 `::` 之后那截（= 测试名）非空**。

    ②（Codex round-3 MEDIUM）不可省：参数段是挂在**测试名**上的，而测试名必然在 `::` 之后。
    少了它，`tests/test_[x].py::test_x - AssertionError: [1, 2]` 会拿路径里那个 `[` 当参数段
    起点（前缀 `tests/test_` 无空白）⇒ 整行被误收进「无 reason」候选 ⇒ 合法行判成二义 ⇒
    假 HARNESS-ERROR。而 `tests/test_` 里没有 `::`，它当不了「path::test」。

    ③（Codex round-6 MEDIUM）也不可省：**路径本身可以含 `::`**。
    `tests/foo::[x]/test_gate.py::test_x - AssertionError: [1, 2]` 里，`[x]` 前面那截
    `tests/foo::` 既无空白又含 `::`，②单独放它过 ⇒ 整行又被误收进候选 ⇒ 同一种假
    HARNESS-ERROR 换了个入口。加上③之后 `tests/foo::` 的测试名是**空**的，它当不了
    `path::test[param]`，于是被拒。
    ⚠️ ③ **不能**退化成「取最后一个 `::` 之后的那个 `[`」—— 参数 ID 里也可以有 `::`
    （`…::test_target[case] - EXPECT[x :: y]]`，Codex round-2 HIGH）。「存在某个 `[`」这层
    存在量化必须保留；③ 只是给**每个**候选 `[` 各自加一条前缀合法性检查。

    ⚠️ 如实声明这条的剩余面：**以 `]` 收尾且不含 `::` 的纯路径**（如 `ERROR a/[b]`）会被判
    不是 nodeid 形。pytest 的收集错误行落在 `.py` 文件上（不以 `]` 收尾），本树未见该形态；
    真出现时表现为保守的 HARNESS-ERROR，不是假杀。

    ⚠️ 这与 `_boundary_ok` 的「方括号成对」是**两条不同**的判据，不是同义改写：
    `a::b[[c]` 括号不成对却是合法 nodeid（参数 ID = `[c`），`a::b[c] - d` 括号成对却**不是**
    合法 nodeid（不以 `]` 收尾）。两族各自能捞到对方漏掉的读法，所以 `_split_unique`
    取**并集**而不是二选一。
    """
    if not s:
        return False
    if not s.endswith("]"):
        # 无参数段：整串就是 `path` 或 `path::test`，唯一约束是不含空白。
        return not any(ch.isspace() for ch in s)
    for i, ch in enumerate(s):
        if ch.isspace():
            # 前缀一旦出现空白，其后任何 `[` 的前缀都含空白 —— 不必再找。
            return False
        if ch == "[" and i > 0:
            head = s[:i]
            # ③ 前缀必须形如 `<path>::<非空测试名>` —— 路径自身也可以含 `::`，所以要看
            #   **最后一个** `::` 之后还剩不剩东西（`tests/foo::` 剩空 ⇒ 当不了 path::test）。
            marker = head.rfind("::")
            if marker >= 0 and head[marker + 2 :]:
                return True
    return False


def _split_unique(line: str, nodeid: str) -> bool:
    r"""整行的 `nodeid - reason` 切分是否**唯一可判定**。

    ⛔ **本函数修的是「边界不可判定」这个性质，不是某一条输入**（UAT §31 元教训）：
    round-3 / round-4 连着两轮各补了「这一条反例」，下一轮换个参数 ID 又漏一类。
    所以判据的写法是**枚举读法空间、取并集**，不是「再加一个 if」。

    **读法空间（穷举；一行 `FAILED <body>` 的全部合法读法）**：
      · **完整 reason**    —— `<nodeid> - <reason>`，在某个 ` - ` 处切开；
      · **参数化**         —— 同上，nodeid 带 `[...]` 参数段；
      · **无 reason**      —— 整行 body 就是 nodeid（pytest 在断言没有消息时只打
        `FAILED <nodeid>`）；参数 ID 内部可含 ` - ` 与方括号，所以「整行」这一读法
        跟上面两类**可以同时成立**；
      · **括号闭合的二义形态** —— `…::test_x[case] - EXPECT[]`：既可读成
        「nodeid=`…test_x[case]` + reason=`EXPECT[]`」，也可读成「整行是一个无 reason
        的 nodeid，参数 ID = `case] - EXPECT[`」。两读并存 ⇒ 边界不可判定。

    ⛔ round-20（H1）：旧实现把「无 reason」放在 `if not cands:` 的**另一条分支**里，
    于是它**从不与**「截断 + reason」同台参与唯一性判定 —— `len(cands) == 1` 是在一个
    **残缺的候选集**上成立的恒真式。现在三类读法进**同一个** `cands`，多于一种 ⇒
    调用方判 HARNESS-ERROR。⛔ 仍不用贪婪 / `rsplit`（那只是把错误换个方向）。

    ⚠️ **如实声明改动方向：⛔ 本函数不是单调的，两族、两个方向都会翻。**
    （这句话本身被改过**两次**：初稿写「候选集只增不减 ⇒ 只会 True→False」，实测推翻；
    改成「只有无 ` - ` 那族会双向翻」，Codex round-1 LOW 又推翻。现按实测写第三版 ——
    ⛔ 后人若要再收窄这句，先跑反例，别照抄。）

      · **无 ` - ` 切点**那族（旧 `if not cands:` 分支）：判据从「整行方括号成对」换成
        「整行是 nodeid 形」，两者**互不包含**；
      · **有 ` - ` 切点**那族：候选判据虽是并集（`方括号成对 ∪ nodeid 形`）、候选集只增
        不减，但**候选集变大不等于返回值只会变 False** —— 旧版可能一条候选都没有而落到
        `if not cands:` 的旧回退上返回 False，新版捞到了那条唯一候选反而返回 True。

    两个方向各一条实测反例（都已进单测钉住）：
      - `FAILED a::b[c - d]`（nodeid=`a::b[c`）True→**False**：括号成对，但正则切出的
        nodeid 与唯一合法读法不符 ⇒ 本该拒 —— **收紧**，是想要的；
      - `FAILED a::b[[c] - boom`（nodeid=`a::b[[c]`）False→**True**：左侧 `a::b[[c]`
        括号不成对、旧版不收它 ⇒ 无候选 ⇒ 旧回退按整行括号数判 False；新版认出它是
        合法 nodeid 形（参数 ID = `[c`）⇒ 唯一候选 ⇒ True —— **放宽**。

    ⚠️ 两条放宽都**不影响端到端判据**：`_boundary_ok(nodeid)` 与本函数**并联**（见
    `failure_records` / `parse_failed_nodeids`），方括号不成对的 nodeid 仍会被它打进
    `unparsed_failure_lines` ⇒ 调用方照样判 HARNESS-ERROR。

    ⚠️ **保守性的代价也如实说**：参数化门 + reason 以 `]` 收尾（如
    `FAILED a::b[c] - AssertionError: [1, 2]`）现在判**不唯一** ⇒ HARNESS-ERROR。那**确实**
    是两种合法读法（读法 B 的参数 ID = `c] - AssertionError: [1, 2`），只看摘要行分不开。
    要把这类分开只能靠 `expect_loc` 绑到具体断言（D-28 延期，T8-C 的面），不能靠在这里
    挑一个「看起来更像」的读法 —— 那正是 round-3/4 两轮栽过的形态。
    """
    body = line.split(" ", 1)[1] if " " in line else line
    # ⛔ 候选 nodeid **允许含空格**：参数 ID 里本来就可能有（`test_x[case] - EXPECT[`
    # 正是这种）。结构约束取两族的**并集**（见 `_nodeid_shaped` 的 ⚠️ 段）—— 这恰恰让
    # 「截断读法」与「完整读法」同时合法，于是切分不唯一，必须拒。
    cands = []
    for i in range(len(body)):
        if body.startswith(" - ", i):
            left = body[:i]
            # ⛔⛔ 判据是**并集**（`方括号成对 ∪ nodeid 形`）。这一行被改过两次、回滚过一次，
            # 过程本身就是教训，完整记在这里免得后人第三次踩：
            #
            # round-8 曾把「方括号成对」那半**删掉**，理由是：
            #   `FAILED …::test_x - AssertionError: expected - actual` 的第二个切点左侧
            #   `…::test_x - AssertionError: expected` 括号数 0==0「成对」，但它**在括号外含
            #   空白**，「pytest 永远不会把它当 nodeid 打出来」⇒ 判二义是假 HARNESS-ERROR。
            # 两次独立复核（Codex round-7 MEDIUM + 一次 172-agent 多视角扫描的 HIGH）都这么说。
            #
            # ⛔ **那个共同前提是错的，2026-09-15 于 pytest 9.0.2 实测推翻**
            # （存档 `evidence-mutkill-r3/probe-nodeid-whitespace-*.txt`）：
            #   `globals()["test_x[case] - EXPECT"] = f` 这样注入的测试**能被正常收集**，
            #   `--collect-only` 打出 `…::test_x[case] - EXPECT`，短摘要打出
            #   `FAILED …::test_x[case] - EXPECT - AssertionError: OTHER`。
            # ⇒ nodeid **可以**含空白与 ` - `；上面那种行是**真二义**，判 HARNESS-ERROR 正确。
            # ⇒ round-8 的收紧开了一条**假 KILLED**（Codex round-8 HIGH 当场复现：同一输入
            #   在收紧前判 HARNESS-ERROR、收紧后判 KILLED），已回滚。
            #
            # ⚠️ 保守性的代价如实说：reason 里带 ` - `（`expected - actual`）的行会判
            # HARNESS-ERROR。那**不是**误判 —— 只看摘要行确实分不开。要分开只能靠
            # `expect_loc` 绑到具体断言（D-28 延期，T8-C 的面）。本树实测该形态零命中
            # （全部存档 1932 条裁决行里 0 条含 ASCII ` - `，断言消息一律用全角破折号）。
            if left and (left.count("[") == left.count("]") or _nodeid_shaped(left)):
                cands.append(left)
    # ⛔ H1：无 reason 读法（整行即 nodeid）也是**一种候选读法**，必须进同一个候选集。
    if _nodeid_shaped(body):
        cands.append(body)
    if not cands:
        # 一种合法读法都凑不出来（body 既切不出 nodeid 形的左侧，整行也不是 nodeid 形）
        # ⇒ 边界同样不可判定。⛔ 旧实现在这里回落到「整行方括号成对即可」，那把
        # 「读不出来」当成了「读法唯一」。
        return False
    return len(cands) == 1 and cands[0] == nodeid


def _boundary_ok(nodeid: str) -> bool:
    r"""nodeid 的切分边界是否可判定。

    ⛔ round-3 HIGH：`\S+?` 非贪婪 + `(?: - ...)` 让**参数 ID 里含 ` - `** 的行被切错：
    `FAILED tests/x.py::test_x[case - EXPECT] - AssertionError: other`
    解析成 nodeid=`tests/x.py::test_x[case`、reason=`EXPECT] - AssertionError: other`
    —— 整行匹配成功所以不进 `unparsed_failure_lines`，`startswith(nodeid + "[")`
    又接受这个截断值，于是**参数 ID 里的字样**就能满足消息判据。
    判据：方括号必须成对闭合；不闭合 = 切早了 = 边界不可判定 ⇒ 调用方判 HARNESS-ERROR。
    ⚠️ 不改成贪婪或 `rsplit` —— reason 本身也可能含 ` - `，那样只是把错误换个方向。
    """
    return nodeid.count("[") == nodeid.count("]")


#: 摘要区起始分隔线：`==== short test summary info ====`。
_SUMMARY_HEAD_RE = re.compile(r"^=+ short test summary info =+$", re.M)

#: 摘要区结束：pytest 的收尾统计行（`1 failed in 0.13s` / `= 1 failed in ... =`）。
_SUMMARY_TAIL_RE = re.compile(r"^=*\s*\d+ (?:failed|passed|error)", re.M)

#: `=== FAILURES ===` / `=== ERRORS ===` 起始分隔线。
_FAILURES_HEAD_RE = re.compile(r"^=+ (?:FAILURES|ERRORS) =+$", re.M)

#: `--tb=line` 的位置行：`<path>:<lineno>: <ExcName>[: <msg>]`。
#: ⚠️ 路径用非贪婪 + 要求以 `.py` 结尾：pytest 只对 Python 源打这种行；不加后缀
#: 约束的话 `1 failed in 0.13s` 之类也会被凑成 `path:lineno:`。
_LOC_RE = re.compile(r"^(?P<path>\S+\.py):(?P<line>\d+): (?P<rest>\S+.*)$", re.M)

#: 摘要区里「长得像失败行」的行（用来抓**解析不掉**的那种 —— Codex round-1 MEDIUM：
#: `_FAILED_RE` 的 nodeid 是 `\\S+?`，参数化 id 带空格（如 `test_x["a b"]`）就匹配不上，
#: 旧实现把这种行**静默丢掉**，`all(gate_hit)` 于是在一个不完整的集合上通过）。
_FAILEDISH_RE = re.compile(r"^(FAILED|ERROR) .+$")


def failure_records(out: str) -> list[tuple[str, str, str]]:
    """摘要区里的 `(status, nodeid, reason)` —— **保留 status 且不去重**。

    ⛔ round-3 MEDIUM：`parse_failed_nodeids` 用 `set` 去重且 FAILED/ERROR 同收，
    「同一 nodeid 各有一条 FAILED 与一条 ERROR」会被数成 1 条 ⇒ 「恰一条红」成立。
    要判「恰一条 FAILED 且零 ERROR」必须拿这个保留状态的列表。
    """
    region = summary_region(out)
    if region is None:
        return []
    return [
        (m.group("status"), m.group("nodeid"), m.group("reason") or "")
        for m in _FAILED_RE.finditer(region)
        if _boundary_ok(m.group("nodeid")) and _split_unique(m.group(0), m.group("nodeid"))
    ]


def exactly_one_failed(out: str, nodeid: str) -> bool:
    """摘要区里恰有 1 条 FAILED（属于目标门）、0 条 ERROR、且无未解析记录。"""
    if unparsed_failure_lines(out):
        return False
    recs = failure_records(out)
    fails = [r for r in recs if r[0] == "FAILED"]
    errs = [r for r in recs if r[0] == "ERROR"]
    return len(fails) == 1 and not errs and gate_hit(nodeid, {fails[0][1]})


def unparsed_failure_lines(out: str) -> list[str]:
    """摘要区里以 `FAILED `/`ERROR ` 开头却解析不出 nodeid 的行。

    非空 ⇒ 失败集合**不完整**，「摘要区里所有失败都属于目标门」这个前提不可证。
    调用方应判 HARNESS-ERROR，⛔ 不得当作「没有别的失败」。
    """
    region = summary_region(out) or ""
    bad = []
    for ln in region.splitlines():
        if not _FAILEDISH_RE.match(ln):
            continue
        m = _FAILED_RE.match(ln)
        # 匹配不上，或匹配上了但**切分边界不可判定**（方括号未闭合）—— 后者更危险：
        # 它整行匹配成功，不报出来就会带着错误的 nodeid/reason 进判据（round-3 HIGH）。
        if m is None or not _boundary_ok(m.group("nodeid")) or not _split_unique(ln, m.group("nodeid")):
            bad.append(ln)
    return bad


def judge_env() -> dict[str, str]:
    """判据面成立所需的环境变量增量。

    ⛔ `COLUMNS` 必须给足：pytest 的 `-rf` 短摘要按终端宽度截断，80 列下
    `FAILED … - <reason>` 的 reason 会被截成空串 ⇒ `expect_msg` 恒不命中 ⇒
    全部报 SURVIVED。那种坏法看起来跟「门全都不承重」一模一样。
    """
    return {"COLUMNS": "1000", "PYTHONDONTWRITEBYTECODE": "1"}


def judge_flags() -> list[str]:
    """判据面成立所需的 pytest 命令行开关 —— 四套统一从这里取，不各写各的。

    * `-q`                  安静模式（进度点 + 摘要）；
    * `-p no:cacheprovider` 不写 `.pytest_cache`（变异期间不留痕）；
    * `--tb=line`           每条失败一行 `<file>:<lineno>: <Exc>: <msg>` ——
                            `expect_loc` 的**唯一**来源；
    * `-rfE`                短摘要 `FAILED/ERROR <nodeid> - <reason>` —— nodeid 与
                            `expect_msg` 的唯一来源。
                            ⛔⛔ **`E` 不可省**（2026-09-15 实测，pytest 9.0.2）：
                            `-r` 的字符串**替换**默认值 `fE`，所以只写 `-rf` 会让
                            **ERROR 行整条不进短摘要**。三层后果，一层比一层重：
                            ① 目标门若是 **ERROR**（fixture / teardown 炸）而不是
                               FAILED，它的 nodeid 根本不在失败集里 ⇒ `gate_hit`
                               为假 ⇒ 判 **SURVIVED** —— 一个把门炸掉的变异被报成
                               「门没抓住」，是**假 SURVIVED**，方向最坏；
                            ② `failures_region()` 却把 `=== ERRORS ===` 段的位置行
                               一起收下 ⇒ 「所有失败属目标门」那道核在一个**看不见
                               ERROR** 的集合上**空真**通过，而位置行照借 —— H2 刚
                               堵住的跨门借位从 ERROR 那一半原样复活；
                            ③ `exactly_one_failed()` 里 round-3 MEDIUM 加的
                               「0 条 ERROR」守卫**结构性不可达** —— 修复被 harness
                               自己的开关废掉了，`failure_records()` 里那半个
                               `ERROR` 分支同样是死代码。
                            实测对照：同一份用例集，`-rf` 的摘要区只有 FAILED 一行，
                            `-rfE` 才多出 `ERROR …::test_errors - RuntimeError: …`。
    * `--show-capture=no`   ⛔ round-19 新增：不回显被测进程的 captured
                            stdout/stderr。实测（pytest 9.0.2）captured 区就在
                            `=== FAILURES ===` 与摘要分隔线之间，被测进程只要打一行
                            `FAILED <nodeid> - <expect_msg>` 就能伪造判据面
                            （Y1-B HIGH-2）。关掉它 = **captured 区**里不再有被测
                            进程可控的字节。
                            ⛔ **口径更正（Codex round-6 LOW）**：此前这句写的是
                            「那段区间里不再有任何被测进程可控的字节」——**说宽了**。
                            它只关掉 captured 区；被测进程的文字仍可经**别的**路子进
                            FAILURES 区，例如门里自己写的
                            `assert r.returncode == 0, r.stderr[:250]` 会把子进程
                            stderr 塞进断言消息，`--tb=line` 照样打出来。
                            真正兜住「伪造判据面」的是**摘要区取法**
                            （`summary_region()` 只取 `short test summary info` 那段）
                            与 `expect_loc` 的位置绑定，本开关只是把最便宜的一条路堵掉。
                            ⚠️ 这是**显示级**开关，不改变测试结果，也不改变 rc；
                            代价只是诊断时看不到子进程原文。
    """
    return ["-q", "-p", "no:cacheprovider", "--tb=line", "-rfE", "--show-capture=no"]


def syntax_check(path: Path, text: str) -> str | None:
    """变异后的文本能不能编译？返回错误串；`None` = 通过。

    `.py` 直接编译；`.md` 逐个 PYEOF 块编译(写点本体就在块里，SKILL.md 的其余
    部分是散文，不该拿去编译)；其它后缀(如规格 `.md` 里没有 PYEOF 块)自然返回
    `None` —— 无可执行块 = 无编译期风险。

    ⛔ 这道自检是**假杀的结构性封堵**：语法不合法的变异体会让被测进程在编译期
    就死，于是「防线被拆掉之后本该发生的坏事」根本没机会发生，而门却因为**别的
    断言**红了被记成 KILLED。它照出的是负控自己坏了 —— 所以调用方必须单列
    `SYNTAX-INVALID`，不并进 KILLED / SURVIVED 任何一边。
    """
    try:
        if path.suffix == ".md":
            for i, blk in enumerate(PYEOF_RE.findall(text)):
                compile(blk, f"<{path.name}#PYEOF{i}>", "exec")
        elif path.suffix == ".py":
            compile(text, str(path), "exec")
    except SyntaxError as exc:  # IndentationError / TabError 都是它的子类
        return f"{type(exc).__name__}: {exc}"
    return None


def summary_region(out: str) -> str | None:
    """`=== short test summary info ===` 之后到收尾统计行之间的那一段。

    ⛔ Y1-B HIGH-2 的封堵点：旧实现对**整份 stdout+stderr** 做 `findall`，于是
    被测进程只要把一行 `FAILED <nodeid> - <expect_msg>` 打进 stdout，pytest 就会
    在 `--- Captured stdout call ---` 区原样回显，判据把它当成真的失败记录收下。
    实测（pytest 9.0.2）那一行落在摘要分隔线**之前** ⇒ 只取摘要区即可拒掉。

    返回 `None` = 输出里根本没有摘要区（多半是漏了 `-rf`）—— 由
    `judge_surface_missing()` 报成 harness 失败，**不是**「没有失败」。
    """
    m = _SUMMARY_HEAD_RE.search(out)
    if not m:
        return None
    rest = out[m.end() :]
    tail = _SUMMARY_TAIL_RE.search(rest)
    return rest[: tail.start()] if tail else rest


def failures_region(out: str) -> str | None:
    """`=== FAILURES ===`（或 `=== ERRORS ===`）到摘要分隔线之间的那一段。

    `--tb=line` 的位置行就在这里。⚠️ 判据面里之所以敢用它，前提是 harness 带了
    `--show-capture=no`（见 `judge_flags()`）；没带的话这一段里会混进被测进程的
    captured 输出，位置行同样可被伪造。
    """
    m = _FAILURES_HEAD_RE.search(out)
    if not m:
        return None
    rest = out[m.end() :]
    head = _SUMMARY_HEAD_RE.search(rest)
    return rest[: head.start()] if head else rest


def parse_failed_nodeids(out: str) -> set[str]:
    """从 `-rf` 短摘要解析失败的 nodeid 集合（**只在摘要区里找**）。

    ⛔ 用短摘要而不是「输出里有没有 FAILED 字样」：「某处有失败」不能证明**指定
    的那道门**红了 —— 拿粗判据判 KILLED 是假杀的经典形态。
    ⛔ 且只在摘要区里找：整份输出里找会被 captured 区的伪 FAILED 行喂饱（HIGH-2）。
    """
    region = summary_region(out)
    if region is None:
        return set()
    return {
        m.group("nodeid")
        for m in _FAILED_RE.finditer(region)
        if _boundary_ok(m.group("nodeid")) and _split_unique(m.group(0), m.group("nodeid"))
    }


def failed_reasons(out: str) -> list[tuple[str, str]]:
    """摘要区里的 `(nodeid, reason)` 列表；无 reason 的记成空串。"""
    region = summary_region(out)
    if region is None:
        return []
    return [
        (m.group("nodeid"), m.group("reason") or "")
        for m in _FAILED_RE.finditer(region)
        if _boundary_ok(m.group("nodeid")) and _split_unique(m.group(0), m.group("nodeid"))
    ]


def failed_locations(out: str) -> list[tuple[str, int, str]]:
    """`--tb=line` 位置行 → `[(路径, 行号, 其余文本), ...]`（**只在 FAILURES 区里找**）。

    ⚠️ `--tb=line` 的位置行**不带 nodeid**，所以「哪一行属于哪个 nodeid」在多条
    失败时是不可判的。`kill_identity()` 因此要求「摘要区里的每一个失败 nodeid 都
    命中目标门」才肯把位置行归给目标；否则判 `HARNESS-ERROR`（归属不可证），
    而不是猜一个。
    """
    region = failures_region(out)
    if region is None:
        return []
    return [(m.group("path"), int(m.group("line")), m.group("rest")) for m in _LOC_RE.finditer(region)]


def gate_hit(nodeid: str, failed: set[str]) -> bool:
    """声明的 nodeid 是否命中失败集 —— **含参数化用例**。

    ⛔ 实测教训：声明 `…::test_x` 而 pytest 报的是 `…::test_x[1]`，直接用
    `nodeid in failed` 会把真 KILLED 误报成 SURVIVED —— 判据自己坏了，长得却
    跟「门不承重」一模一样。
    """
    return any(f == nodeid or f.startswith(nodeid + "[") for f in failed)


def judge_surface_missing(rc: int, out: str, *, need_location: bool = False) -> str | None:
    """判据面本身是否成立？返回问题描述；`None` = 成立。

    ⛔ 这道检查的方向是「**判据不可用**」而不是「变异没杀死」。两者的处置完全
    不同：前者要把 harness 判失败并让人去修命令行，后者才是关于被测物的结论。
    没有它的话，忘了给 `-rf` 会让 `parse_failed_nodeids()` 恒返空集 ⇒ 每一条都
    报 SURVIVED ⇒ 报告长得跟「所有门都不承重」一模一样(而真相是 harness 坏了)。

    `need_location=True` 时同时要求 `--tb=line` 的位置行存在 —— 缺 `--tb=line`
    会让 `expect_loc` 恒不命中，坏法与缺 `-rf` 同型（假 SURVIVED）。
    """
    if rc != 1:
        return None
    if summary_region(out) is None:
        return "rc=1(有测试失败)但输出里没有短摘要区 —— pytest 命令缺 `-rfE`，判据面不存在"
    if not _FAILED_RE.search(summary_region(out) or ""):
        return "rc=1(有测试失败)但摘要区里没有 `FAILED`/`ERROR` 行 —— 判据面不存在"
    if need_location and not failed_locations(out):
        return "rc=1 但 FAILURES 区里没有 `<file>:<line>:` 位置行 —— pytest 命令缺 `--tb=line`，位置判据面不存在"
    return None


# ── 断言源位置（`expect_loc`）────────────────────────────────────────────────

_FP_CACHE: dict[tuple[str, int], dict[str, list[int]]] = {}
_WALK_CACHE: dict[tuple[str, int], list[tuple[ast.stmt, str]]] = {}


def _stmts_with_scope(gate_file: str | Path) -> list[tuple[ast.stmt, str]]:
    """门文件里的每条语句 + 它所在的**函数/类作用域全名**（模块级记 `<module>`）。"""
    p = Path(gate_file)
    key = (str(p), p.stat().st_mtime_ns)
    if key in _WALK_CACHE:
        return _WALK_CACHE[key]
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    # ⛔ 用 `ast.walk` + 父链推作用域, **不**手写「遍历 body/orelse/finalbody/handlers」——
    # 手写就得把语句容器**枚举完整**，而那份名单一定会漏（初版就漏了 `match` 的 `cases`；
    # 本树的门文件恰好没有 `match` 语句，所以漏了也照样「覆盖一致」，属于最难发现的那种）。
    # 漏掉的语句算不出指纹 ⇒ 位置绑不上 ⇒ 假 SURVIVED。改成按父链推，覆盖面**恒等于**
    # `ast.walk`，没有容器名单可漏。
    parent: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[id(child)] = node

    def scope_of(node: ast.AST) -> str:
        names: list[str] = []
        cur = parent.get(id(node))
        while cur is not None:
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(cur.name)
            cur = parent.get(id(cur))
        return ".".join(reversed(names)) if names else "<module>"

    out: list[tuple[ast.stmt, str]] = [(node, scope_of(node)) for node in ast.walk(tree) if isinstance(node, ast.stmt)]
    _WALK_CACHE.clear()  # 只留一份：门文件一改，旧表必须作废
    _WALK_CACHE[key] = out
    return out


def _fp(node: ast.stmt, scope: str) -> str:
    """一条语句的身份指纹 = sha256(所在作用域全名 + 语句的 AST 规范化 dump)。

    ⛔ 作用域必须进哈希。本树实测：门文件 6672 行 / 2369 个不同的语句指纹里，有
    **244 个指纹对应 1271 处语句** —— 例如 `assert _write_face(vault) == face, "零写"`
    在 28 个不同的测试函数里逐字重复。只按语句文本做身份的话，这类断言的
    「恰好命中 1 条」永远不成立，138 条里相当一部分会被挤进「身份不可证」豁免，
    (f) 的收口就只剩个空壳。带上函数名之后，跨函数的同形断言各自有各自的身份。
    ⚠️ 代价如实说：**改测试函数名**会让指纹失配 ⇒ 判 HARNESS-ERROR「锚失效」。
    这是想要的方向（绑的就是「这个测试里的这一条断言」），但要知道它会这样。
    """
    return hashlib.sha256(f"{scope}\0{ast.dump(node, include_attributes=False)}".encode()).hexdigest()[:12]


def stmt_fingerprints(gate_file: str | Path) -> dict[str, list[int]]:
    """门文件里每条**语句**的身份指纹 → 它出现在哪些起始行。

    规范化用 `ast.dump(node, include_attributes=False)`：丢掉行号、列号、注释与
    空白，只留语法结构与字面量；再拼上所在函数的全名（见 `_fp`）。于是
      · 在断言上方插入注释 / 在文件上方插入 100 行  ⇒ 指纹不变（不会误报漂移）；
      · 把 `assert a == b, "x"` 改成 `assert a == b, "y"` ⇒ 指纹变（能报漂移）；
      · 两个不同测试里逐字相同的断言        ⇒ 指纹**不同**（身份可证）。

    ⚠️ 复合语句（`with` / `for` / `if`）的 dump 含其整个 body，所以指纹是
    「这条语句连同它的子树」。判定时取的是**覆盖失败行的最小语句**，通常就是
    那条 `assert` 本身。
    """
    p = Path(gate_file)
    key = (str(p), p.stat().st_mtime_ns)
    if key in _FP_CACHE:
        return _FP_CACHE[key]
    out: dict[str, list[int]] = {}
    for node, scope in _stmts_with_scope(p):
        out.setdefault(_fp(node, scope), []).append(node.lineno)
    _FP_CACHE.clear()  # 只留一份：门文件一改，旧指纹表必须作废
    _FP_CACHE[key] = out
    return out


def _smallest_stmts_at(gate_file: str | Path, lineno: int) -> list[tuple[ast.stmt, str]]:
    """覆盖 `lineno` 的**全部并列最小**语句节点 + 作用域（空 = 该行不属于任何语句）。

    ⛔ 「并列最小」必须整组返回（Codex round-1 HIGH）：两条语句写在同一行
    （`a; b` / 同行双 assert）时跨度相同，首版只留第一条 ⇒ 该行永远映射到第一条的
    指纹，第二条失败会被认成第一条。本树门文件实测 0 行多语句，但这条不能靠
    「今天没有」立住 —— 门一改就有了。
    """
    best: list[tuple[ast.stmt, str]] = []
    best_span = None
    for node, scope in _stmts_with_scope(gate_file):
        end = getattr(node, "end_lineno", None) or node.lineno
        if not (node.lineno <= lineno <= end):
            continue
        span = end - node.lineno
        if best_span is None or span < best_span:
            best, best_span = [(node, scope)], span
        elif span == best_span:
            best.append((node, scope))
    return best


def _smallest_stmt_at(gate_file: str | Path, lineno: int) -> tuple[ast.stmt, str] | None:
    """兼容旧接口：唯一最小语句；并列（同行多语句）时返回 `None`（归属不可证）。"""
    got = _smallest_stmts_at(gate_file, lineno)
    return got[0] if len(got) == 1 else None


def line_stmt_ambiguous(gate_file: str | Path, lineno: int) -> bool:
    """该行是否有多条并列最小语句（失败位置无法唯一归属到一条语句）。"""
    return len(_smallest_stmts_at(gate_file, lineno)) > 1


def _same_file(path: str, gate: Path) -> bool:
    """位置行里的路径是不是那个门文件？

    ⛔ 绝对路径才可以 `resolve()` 比对。**相对路径不行** —— `Path.resolve()` 会拿
    **harness 进程自己的 cwd** 去解，而位置行是被测 pytest 打的，它的 cwd 是
    `backend/`；两者不一定相同，解出来会是个不存在的路径，于是「位置在门文件里」
    这条判据静默恒假 ⇒ 全报 SURVIVED（假 SURVIVED，长得跟「门都不承重」一样）。
    本树实测 pytest 9.0.2 打的是绝对路径，但这一条不能靠「今天恰好是绝对路径」立住。
    相对路径改用**路径后缀**比对（`.../backend/tests/x.py` 以 `/tests/x.py` 结尾）。
    """
    p = Path(path)
    if p.is_absolute():
        try:
            return p.resolve() == gate
        except OSError:
            return False
    return gate.as_posix().endswith("/" + p.as_posix())


def loc_token_for(gate_file: str | Path, path: str, lineno: int) -> str | None:
    """把一条位置行折算成 `expect_loc` 取值；`None` = 折算不出来。

    * 位置落在门文件里 ⇒ `"stmt:<指纹>"`；
    * 落在别的文件里   ⇒ `"file:<basename>"`（身份更弱，调用方须逐条登记理由）。
    """
    gp = Path(gate_file).resolve()
    if not _same_file(path, gp):
        return f"file:{Path(path).name}"
    found = _smallest_stmt_at(gp, lineno)
    if found is None:
        return None
    return f"stmt:{_fp(*found)}"


def matched_loc_tokens(out: str, gate_file: str | Path) -> list[str | None]:
    """FAILURES 区里**每一条**位置行折算出的 token（保持原顺序）。

    ⛔ 判据侧用 `expect_loc in tokens`（任一命中即算），诊断/对照侧却曾固定取
    `locs[0]` —— 位置序列是「别的位置, 目标位置」时两边看的不是同一次失败
    （Codex round-1 HIGH）。空变异对照改用这个**全集**做交集判断。
    """
    return [loc_token_for(gate_file, p, ln) for p, ln, _ in failed_locations(out)]


def anchor_surface_broken(gate_file: str | Path | None, expect_loc: str | None) -> str | None:
    r"""位置锚**本身**还成不成立？返回问题描述；`None` = 成立（或本次不使用位置锚）。

    ⛔ M①（round-20）：这道检查必须跑在**任何关于被测物的结论之前**。收口前
    `kill_identity()` 里有两条早退排在锚检查前面 ——
      · `rc == 0 ⇒ SURVIVED`（「变异没被这道门抓住」）；
      · 「红在门文件之外 ⇒ SURVIVED」；
    于是「门文件被别的卡改写、`expect_loc` 已失效」会被读成**关于被测物的结论**，
    下一个人拿着这份报告去修一个根本没坏的门。判据面坏了就只能说「判据面坏了」。

    判据与跑门**之前**的 `check_expect_loc_unique()` 逐字同口径：`stmt:` 指纹必须在
    门文件里**恰好命中 1 条**（0 条 = 锚漂；>1 条 = 同形两处、身份不可唯一归属）。

    ⚠️ 边界：本函数**不改 rc 契约** —— 锚完好时 `rc == 0` 仍然是 SURVIVED（那是关于
    被测物的结论）。它只在「判据面本身求不了值」时抢在结论之前说话。
    """
    if expect_loc is None or not expect_loc.startswith("stmt:"):
        return None
    if gate_file is None:
        return "要求位置判据却没给 gate_file —— 位置锚无法求值"
    p = Path(gate_file)
    if not p.exists():
        return f"门文件不存在 {p} —— 位置锚无法求值"
    try:
        hits = stmt_fingerprints(p).get(expect_loc[5:], [])
    except (SyntaxError, OSError, ValueError) as exc:
        return f"门文件解析不了({exc}) —— 位置锚无法求值"
    if len(hits) != 1:
        return f"expect_loc {expect_loc} 在门文件里命中 {len(hits)} 条语句(应为 1)" + (
            "—— 门被改写，锚失效" if not hits else f" 行号 {hits} —— 同形两处，身份不可唯一归属"
        )
    return None


def _loc_identity(out: str, nodeid: str, gate_file: str | Path, expect_loc: str) -> tuple[bool, str]:
    """位置判据。返回 `(ok, 说明)`；说明以 `HARNESS:` 开头 = 判据面坏了，不是结论。"""
    failed = parse_failed_nodeids(out)
    if not all(gate_hit(nodeid, {f}) for f in failed):
        return False, f"HARNESS: 摘要区里有不属于目标门的失败 {sorted(failed)} —— 位置行归属不可证"
    locs = failed_locations(out)
    if not locs:
        return False, "HARNESS: FAILURES 区里没有位置行（缺 `--tb=line`）"
    if expect_loc.startswith("stmt:"):
        # ⛔ M①（round-20）：除「在不在」外**复核命中数恰为 1**，与跑门**之前**的
        # `check_expect_loc_unique()` 逐字同口径。只查存在性时，门文件在跑门**期间**
        # 被改写成同形两条（同一作用域里逐字重复的断言）⇒ 指纹照样「在」，命中 2 条
        # 的事实在运行期这一侧完全看不见，位置身份不可唯一归属却照判 KILLED。
        if len(hits := stmt_fingerprints(gate_file).get(expect_loc[5:], [])) != 1:
            # ⛔ 这里必须是 HARNESS-ERROR 而不是 SURVIVED：门文件被别的卡改写后，
            # 「找不到那条语句」说明**锚漂了**，不是「防线失效」。把两者混起来，
            # 下一个人会去修一个根本没坏的门。
            return False, (
                f"HARNESS: expect_loc {expect_loc} 在门文件里命中 {len(hits)} 条语句(应为 1)"
                + ("—— 门被改写，锚失效" if not hits else f" 行号 {hits} —— 同形两处，身份不可唯一归属")
            )
    tokens = [loc_token_for(gate_file, p, ln) for p, ln, _ in locs]
    # ⛔ 同行多语句 ⇒ 位置归属不可证（Codex round-1 HIGH）：两条并列最小语句共享一个
    # 行号，`--tb=line` 只给行号 ⇒ 到底哪条失败分不开。判 HARNESS-ERROR，不猜。
    amb = [
        f"{Path(p).name}:{ln}"
        for p, ln, _ in locs
        if line_stmt_ambiguous(gate_file, ln)
        if _same_file(p, Path(gate_file).resolve())
    ]
    if amb:
        return False, f"HARNESS: 失败行 {amb} 存在多条并列最小语句，位置无法唯一归属"
    if expect_loc in tokens:
        return True, f"位置命中 {expect_loc}"
    return False, f"位置不符: 期望 {expect_loc}, 实见 {tokens}"


def expect_msg_may_come_from_nodeid(out: str, nodeid: str, expect_msg: str) -> list[str]:
    r"""`expect_msg` 有没有可能是从**测试名**里读出来的（而不是 reason）？返回可疑读法。

    ⛔⛔ **这是第六次动 H1 那条线，但换了问法** —— 前五次都在问「哪一种切分是真的」，
    每次给一条新的 nodeid 形态启发式，然后被下一条反例打掉：
      整串第一个 `[` → 最后一个 `::` 之后 → 存在量化 → 前缀含 `::` →（round-8 收紧后回滚）。
    2026-09-15 实测（`evidence-mutkill-r3/probe-nodeid-whitespace-*.txt`）证明**测试名可以是
    任意字符串**（`globals()["任意名字"] = f` 就能被收集）⇒ **每一个** ` - ` 切点在原则上
    都是合法读法 ⇒ 一个「哪种切分唯一」的行级判据要么漏、要么把几乎所有行都判成不可判定。
    ⇒ 这条路走不通，别再加第六种启发式。

    **换的问法**：不问「哪种读法是真的」，只问「我正要下的那个结论，是不是对**所有**
    还说得通的读法都成立」。本函数只管 `expect_msg` 这一维的**具体**危害形态：
      解析器把 `FAILED <path>::test_x[case] - EXPECT]tail - AssertionError: OTHER` 切成
      nodeid=`…test_x[case]` + reason=`EXPECT]tail - AssertionError: OTHER`，于是 `EXPECT`
      「命中」了 —— 但真相可能是有个**名字叫** `test_x[case] - EXPECT]tail` 的测试，
      它的 reason 是 `AssertionError: OTHER`，**根本不含** `EXPECT`。
      `expect_msg` 是从**名字**里读出来的 ⇒ **假 KILLED**（Codex round-9 HIGH）。

    判据：在**更靠后**的 ` - ` 切点上还有别的读法，其 nodeid 仍命中目标门、且
    **nodeid 里含 `expect_msg` 而它自己的 reason 不含** ⇒ 这个「命中」不可归属 ⇒ 调用方
    判 HARNESS-ERROR。⚠️ 只看比解析结果**更长**的读法（整行无 reason 那种不算）——
    否则任何参数化行都会因为「整行里当然含它」而被误判。

    ⛔ **「只看更靠后」为什么是完备的**（2026-09-15 自核，答 Codex round-10 提问②）：
    `_FAILED_RE` 的 nodeid 是 `\\S+?` —— **非贪婪**，所以正则给出的就是**最短**的那个合法
    切分。⇒ 不存在「比解析结果更靠前、且仍命中目标门」的读法可漏。⚠️ 这条完备性**依赖
    那个 `\\S+?`**：谁把它改成贪婪或 `rsplit`，这里的「只看更靠后」当场失效，必须同改。
    """
    region = summary_region(out)
    if region is None:
        return []
    suspect: list[str] = []
    for ln in region.splitlines():
        if not _FAILEDISH_RE.match(ln):
            continue
        m = _FAILED_RE.match(ln)
        if m is None or not gate_hit(nodeid, {m.group("nodeid")}):
            continue
        body = ln.split(" ", 1)[1] if " " in ln else ln
        parsed_len = len(m.group("nodeid"))
        for i in range(parsed_len + 1, len(body)):
            if not body.startswith(" - ", i):
                continue
            alt_nodeid, alt_reason = body[:i], body[i + 3 :]
            if not gate_hit(nodeid, {alt_nodeid}):
                continue
            if expect_msg in alt_nodeid and expect_msg not in alt_reason:
                suspect.append(alt_nodeid)
    return suspect


def gate_identity_unprovable(out: str, nodeid: str) -> list[str]:
    r"""「**这道门**红了」这句话本身证明了没有？返回让它站不住的读法。

    ⛔ 与 `expect_msg_may_come_from_nodeid()` 是**同一形状的另一半**：
      · 那个问「`expect_msg` 会不会其实来自**测试名**」（消息维）；
      · 本函数问「还有没有别的读法，它的 nodeid **根本不属于这道门**」（**身份维**）。

    危害形态（Codex round-11 HIGH-2）：真实失败的是一个**名字叫** `test_x - suffix]tail`
    的测试 —— 它跟声明的 `test_x` **是两个测试**。但 `_FAILED_RE` 的 `\S+?` 非贪婪把它截成
    `test_x`，`gate_hit()` 于是「命中」，消息与位置也都对得上 ⇒ 判 KILLED。
    而**指定的那道门根本没红**。这是本模块开篇声明要封堵的「拿粗判据判 KILLED」的最深一层：
    连「红的是不是它」都没证明。

    判据：在比解析结果**更靠后**的 ` - ` 切点上还有读法，其 nodeid **不** `gate_hit` 目标门
    ⇒ 「红的是这道门」不可证 ⇒ 调用方判 HARNESS-ERROR。
    （完备性同 `expect_msg_may_come_from_nodeid`：`\S+?` 非贪婪 ⇒ 解析结果是最短切分，
    不存在更靠前的读法可漏。）

    ⚠️ 这仍**不是**根治 —— 根治要靠 `expect_loc` 把身份绑到门文件里的**那一条语句**上
    （D-28 延期，T8-C 的面）。本函数只保证：身份存疑时**说出来**，而不是悄悄判 KILLED。
    """
    region = summary_region(out)
    if region is None:
        return []
    suspect: list[str] = []
    for ln in region.splitlines():
        if not _FAILEDISH_RE.match(ln):
            continue
        m = _FAILED_RE.match(ln)
        if m is None or not gate_hit(nodeid, {m.group("nodeid")}):
            continue
        body = ln.split(" ", 1)[1] if " " in ln else ln
        for i in range(len(m.group("nodeid")) + 1, len(body)):
            if body.startswith(" - ", i) and not gate_hit(nodeid, {body[:i]}):
                suspect.append(body[:i])
    return suspect


def kill_identity(
    rc: int,
    out: str,
    nodeid: str,
    expect_msg: str | None = None,
    *,
    gate_file: str | Path | None = None,
    expect_loc: str | None = None,
    require_gate_file: bool = False,
) -> tuple[str, str]:
    """四套共用的裁决函数。返回 `(verdict, why)`，`verdict` ∈ `VERDICTS` 的前四档。

    `ANCHOR-ERROR` / `SYNTAX-INVALID` 由调用方在**跑门之前**决定（那两档说的是
    「变异没打进去 / 变异体自己编译不过」），本函数只处理「门跑完之后」的四档。

    判据是 **AND**，⛔ 不是二选一：
      1. `rc == 1` —— 4=用法错、5=零收集、2=中断、3=内部错都不算红；
      2. 目标 nodeid 在**摘要区**的失败集里（HIGH-2 的封堵：只看摘要区）；
      3. `require_gate_file=True` ⇒ pytest 报的失败**位置**必须落在被指定的那个
         门文件里（弱位置判据；防「红在 helper / 生产 / 第三方库里」）。⚠️ 它**挡不住**
         HIGH-1 —— 前提断言与目标断言同在门文件里；要分开那两者只能靠 `expect_loc`；
      4. 给了 `expect_loc` ⇒ pytest 报的失败**位置**必须就是它指名的那条语句
         （HIGH-1 的封堵：前提断言与目标断言的**消息**可以一样，**位置**不会一样）；
      5. 给了 `expect_msg` ⇒ 摘要区里该 nodeid 的 reason 必须含它。

    `expect_loc is None and expect_msg is None` ⇒ `KILLED-UNBOUND`：门确实红了，
    但没绑上是哪一条断言。它证明的东西比 `KILLED` 少，所以单列一档。

    ⛔ round-20（H2 / M①）两处收口，都属「判据面归属」而不是新判据：
      · **弱位置不得跨门借位**：`require_gate_file` 这一路（**无** `expect_loc`）原先
        只查「有**某条**失败落在门文件里」；而「所有失败 nodeid 都属于目标门」那道核
        只在 `_loc_identity()` 里、只有传 `expect_loc` 才跑 ⇒ 「目标门红在门文件外
        （消息命中）」+「另一道门红在门文件内（消息不命中）」可以凑成 KILLED，位置
        这一维是**借**来的。现在两路都核。⚠️ 这封堵的是**弱位置判据自己的承诺**
        （「红在这个门文件里」），**不触碰** D-28 延期的「具体断言绑定（`expect_loc`）」
        —— 后者是 T8-C 的面，本轮一条都不动；
      · **锚漂移优先**：`anchor_surface_broken()` 抢在 `rc==0 ⇒ SURVIVED` 与
        「红在门文件之外 ⇒ SURVIVED」两条早退**之前**判 HARNESS-ERROR。⛔ rc 契约不变：
        锚完好时 `rc == 0` 仍然是 SURVIVED。
    """
    surface = judge_surface_missing(rc, out, need_location=require_gate_file or expect_loc is not None)
    if surface:
        return "HARNESS-ERROR", f"⛔ 判据面不成立: {surface}"
    # ⛔ M①：锚检查必须排在下面两条 `SURVIVED` 早退**之前** —— 判据面坏了的时候，
    # 任何关于被测物的结论都是没有依据的（见 `anchor_surface_broken` 的 ⛔ 段）。
    if anchor_broken := anchor_surface_broken(gate_file, expect_loc):
        return "HARNESS-ERROR", f"⛔ 判据面不成立: {anchor_broken}"
    if rc == 0:
        # ⛔ rc=0 是**关于被测物的结论**：门全绿 = 变异没被这道门抓住 = SURVIVED。
        # 首版把它并进「rc != 1 ⇒ HARNESS-ERROR」—— 真·存活的变异被解释成
        # 「负控自己坏了」，诊断方向整个反掉（Codex round-1 MEDIUM 抓的正是 g33 的
        # 这条回归：基线记 SURVIVED，统一调用后变 HARNESS-ERROR ⇒ rc=2）。
        return "SURVIVED", "rc=0 门全绿 —— 变异未被这道门抓住"
    if rc != 1:
        return "HARNESS-ERROR", f"rc={rc}（非 0/1 = 负控没跑成；4=门名/用法错误 5=零收集 2=中断 3=内部错）"
    failed = parse_failed_nodeids(out)
    if bad_lines := unparsed_failure_lines(out):
        # ⛔ 失败集合不完整 ⇒ 「所有失败都属于目标门」不可证（Codex round-1 MEDIUM）。
        return "HARNESS-ERROR", f"摘要区有解析不掉的失败行(失败集合不完整): {bad_lines[:3]}"
    if not gate_hit(nodeid, failed):
        return "SURVIVED", f"rc=1 但失败的不是指定的那道门（摘要区失败集 {sorted(failed) or '∅'}）"

    if require_gate_file or expect_loc is not None:
        if gate_file is None:
            return "HARNESS-ERROR", "⛔ 要求位置判据却没给 gate_file —— 判据无法求值"
        locs = failed_locations(out)
        if not locs:
            return "HARNESS-ERROR", "⛔ 判据面不成立: FAILURES 区里没有位置行（缺 `--tb=line`）"
        # ⚠️ `expect_loc` 永不以 `file:` 开头 —— `check_expect_loc_unique` 把那个形态
        # 整个禁了(落在门文件外的条目 = expect_loc 留空 + 两张豁免表 ⇒ KILLED-UNBOUND)。
        # 首版这里有个「file: 跳过本检查」的分支, 是走不到的死代码, 已删(独立复核确认)。
        # ⛔ H2（round-20）：「所有失败 nodeid 都属于目标门」这道核**在弱位置路径上
        # 也必须跑**。`--tb=line` 的位置行**不带 nodeid**，失败集里一旦混进别的门，
        # 「这条位置行属于谁」在结构上就不可证 —— 此时无论位置落在门文件内还是外，
        # 得出的都不是关于被测物的结论。收口前这道核只在 `_loc_identity()` 里、只有传
        # `expect_loc` 才执行，于是弱位置那一路可以**借**另一道门的失败位置合成 KILLED
        # （目标门只有一条 reason 时，下面那道「位置与消息配对」保护也不触发）。
        if not all(gate_hit(nodeid, {f}) for f in failed):
            return "HARNESS-ERROR", (
                f"摘要区里有不属于目标门的失败 {sorted(failed)} —— "
                f"`--tb=line` 位置行不带 nodeid, 位置归属不可证（⛔ 弱位置判据不得借他门失败位置）"
            )
        gp = Path(gate_file).resolve()
        # ⛔ round-14（Codex round-11 HIGH-1）：目标门有**多条**失败时，`any(...)` 这条弱位置
        # 判据可以被**跨实例拼装**：位置从落在门内的那一条借、消息从另一条借，两维各由不同
        # 失败实例满足。`--tb=line` 的位置行不带 nodeid，多条时配对本就不可证 ⇒ 此时要求
        # 位置**全部**落在门文件里；有一条在门外就说明拼装面存在。
        # ⚠️ 只在多条时收紧 —— 单条失败仍用 `any`（那时不存在可借的第二条）。
        # ⛔ round-15（Codex round-12 HIGH）：数**失败记录**，不数去重后的 nodeid。
        # `failed` 是个 `set`，两条摘要行只要解析出的 nodeid 相同（长前缀 + 不同尾巴）
        # 就会被去重成 1 条 ⇒ 「多条失败」判假 ⇒ 这道守卫整条失效。
        # `failure_records()` 保留全部记录、不去重（它就是为这件事存在的）。
        gate_records = [r for st, nid, r in failure_records(out) if gate_hit(nodeid, {nid})]
        # ⛔ round-15（Codex round-12 MEDIUM）：只在**弱位置**那一路收紧。
        # 给了 `expect_loc` 时位置已绑到门文件里的**那一条语句**上，另一条失败落在 helper
        # 并不妨碍身份成立 —— 在那条路上套用本守卫会把**正当**的 KILLED 打成 HARNESS-ERROR。
        if expect_loc is None and len(gate_records) > 1 and not all(_same_file(p, gp) for p, _, _ in locs):
            outside = [(Path(p).name, ln) for p, ln, _ in locs if not _same_file(p, gp)]
            return "HARNESS-ERROR", (
                f"目标门有 {len(gate_records)} 条失败, 而位置行里有落在门文件**之外**的 {outside[:2]} —— "
                f"位置与消息可能由**不同**失败实例分别满足, 配对不可证"
            )
        if not any(_same_file(p, gp) for p, _, _ in locs):
            return "SURVIVED", (
                f"红在门文件之外: 实见 {[(Path(p).name, ln) for p, ln, _ in locs]} （期望落在 {gp.name} 里）"
            )

    if expect_loc is not None:
        ok, why = _loc_identity(out, nodeid, gate_file, expect_loc)
        if not ok:
            return ("HARNESS-ERROR" if why.startswith("HARNESS:") else "SURVIVED"), why

    # ⛔ round-14（Codex round-11 HIGH-2）：先问**最基础**的那件事 ——「红的是不是这道门」。
    # 它排在消息维之前：消息对得上、但红的根本是**另一个测试**，那是更深一层的假 KILLED。
    if ghost := gate_identity_unprovable(out, nodeid):
        return "HARNESS-ERROR", (
            f"摘要行还能读成**不属于目标门**的 nodeid {ghost[:2]} —— 「红的是这道门」不可证"
            f"（⛔ 测试名可含任意字符，非贪婪的 `\\S+?` 会把更长的真名截成目标门的样子；"
            f"根治要靠 expect_loc 绑到具体语句，D-28 延期）"
        )

    if expect_msg is not None:
        # ⛔ round-12（Codex round-9 HIGH）：先问「这个『命中』会不会其实来自**测试名**」。
        # 测试名可以是任意字符串 ⇒ 行级的「哪种切分唯一」判不出来；但「我要下的这个结论
        # 是否对所有还说得通的读法都成立」判得出来。见 `expect_msg_may_come_from_nodeid`。
        # ⛔ round-13（Codex round-10 HIGH）：**位置行是一条独立信源**，先拿它对一次。
        # `--tb=line` 打的是 `<file>:<lineno>: <Exc>: <msg>` —— 与摘要区的 reason **不是同一
        # 条来源**（一个来自 FAILURES 区、一个来自 short summary）。攻击形态
        # `FAILED …::test_x[<超长参数>] - EXPECT]tail`（长参数把 reason 挤没了，EXPECT 其实
        # 是**测试名**的一部分）在摘要侧「命中」，位置行侧却是 `AssertionError: OTHER`
        # —— 两个信源当场不一致 ⇒ 这个「命中」不可证。
        # ⚠️ 只在**有位置行**时才判（`require_gate_file` / `expect_loc` 这两路才保证有）；
        # 没有位置行时如实退回「只有摘要一个信源」，不假装核过。
        # ⛔ round-14（Codex round-11 MEDIUM）：这条交叉核**只在摘要侧确实命中时**才有意义。
        # 上一版把它排在「摘要有没有命中」之前，于是**两侧都不含** `expect_msg` 的那种正常
        # SURVIVED（变异没被这道门抓住）被改判成 HARNESS-ERROR，诊断还谎称「只在摘要区命中」。
        # 交叉核问的是「摘要命中了、另一条信源认不认」，摘要没命中就没有可对的东西。
        _summary_hit = any(expect_msg in r for nid, r in failed_reasons(out) if gate_hit(nodeid, {nid}))
        if _summary_hit and (locs_for_msg := failed_locations(out)):
            if not any(expect_msg in rest for _p, _ln, rest in locs_for_msg):
                return "HARNESS-ERROR", (
                    f"expect_msg={expect_msg!r} 只在**摘要区**命中，`--tb=line` 位置行里没有 —— "
                    f"两个独立信源不一致（位置行实见 {[r[:60] for _p, _l, r in locs_for_msg][:2]}）；"
                    f"⛔ 常见成因: 它其实是**测试名**的一部分而不是断言消息"
                )
        if from_name := expect_msg_may_come_from_nodeid(out, nodeid, expect_msg):
            return "HARNESS-ERROR", (
                f"expect_msg={expect_msg!r} 可能是从**测试名**里读出来的而不是 reason —— "
                f"还有这些同样命中目标门的读法把它算进了 nodeid: {from_name[:3]} "
                f"（⛔ 名字可含任意字符，摘要行分不开；要分开只能靠 expect_loc）"
            )
        gate_reasons = [r for nid, r in failed_reasons(out) if gate_hit(nodeid, {nid})]
        hits = [r for r in gate_reasons if expect_msg in r]
        if not hits:
            return "SURVIVED", f"红在别的断言上: expect_msg={expect_msg!r} 实见 {[r[:110] for r in gate_reasons]}"
        if len(gate_reasons) > 1 and len(hits) < len(gate_reasons) and (expect_loc is not None or require_gate_file):
            # ⛔ 位置与消息必须落在**同一次失败**上: 参数化门会出多条 FAILED, 若位置命中
            # 「不含期望消息」的那条、消息命中另一条, 两维各自由**不同**失败实例满足 ⇒
            # 单独看哪一维都不红、合起来却判 KILLED(独立复核 2026-09-08)。
            # `--tb=line` 的位置行不带 nodeid, 多条失败时**配对不可证** ⇒ 保守 HARNESS-ERROR。
            # ⛔ round-2 扩到 `require_gate_file`(三套弱位置判据)：那三套只要求「有**某条**
            # 失败落在门文件里」+「有**某条** reason 含消息」，两维可由**不同**失败实例
            # 分别满足 —— 「门内失败但消息不命中」与「门外失败但消息命中」凑成 KILLED。
            # 这突破的是弱位置判据自己的承诺，不属于 D-28 延期的「具体断言绑定」。
            return "HARNESS-ERROR", (
                f"目标门有 {len(gate_reasons)} 条失败, 其中仅 {len(hits)} 条含期望消息 —— "
                f"位置与消息可能落在不同失败实例上, 配对不可证"
            )

    if expect_loc is None and expect_msg is None:
        # ⚠️ 措辞要分清：`require_gate_file` 只把身份绑到**文件**，绑不到**哪一条断言**。
        # 说成「绑定了身份」就是把结论说得比证据宽。
        scope = "（位置只绑到门文件一级，绑不到具体哪条断言）" if require_gate_file else ""
        return "KILLED-UNBOUND", f"门红了，但未绑断言身份{scope}（判据退化成旧口径「指定门红了」）"
    bound = "位置" if expect_loc is not None else ""
    bound += (
        "+消息"
        if (expect_loc is not None and expect_msg is not None)
        else ("仅消息(位置未绑)" if expect_msg is not None else "")
    )
    claim = (
        "红在声称的那一条断言上"
        if expect_loc is not None
        else "红在含期望消息的断言上(仅消息维, 分不开同函数里的其它断言)"
    )
    return "KILLED", f"{claim}（绑定维度: {bound}）"


def kill_identity_ok(
    rc: int,
    out: str,
    nodeid: str,
    expect_msg: str | None = None,
    *,
    gate_file: str | Path | None = None,
    expect_loc: str | None = None,
    require_gate_file: bool = False,
) -> bool:
    """`kill_identity()` 的布尔外壳 —— `KILLED` 与 `KILLED-UNBOUND` 都算 True。

    ⚠️ 两者**不是同一个结论**（后者没绑断言身份），要分开上报的调用方请直接用
    `kill_identity()` 拿 verdict，别拿这个布尔值去数「N 条被指定断言杀死」。
    """
    verdict, _ = kill_identity(
        rc,
        out,
        nodeid,
        expect_msg,
        gate_file=gate_file,
        expect_loc=expect_loc,
        require_gate_file=require_gate_file,
    )
    return verdict.startswith("KILLED")


# ── 信号处置（四套统一，CARD-DEBT-mutkill-R2 (h)）─────────────────────────────

#: 四套统一要挂的信号。⛔ `SIGQUIT`（Ctrl-\）不可漏：它与 SIGTERM/SIGINT/SIGHUP
#: 一样，默认处置**不做栈展开** ⇒ `finally` 不执行 ⇒ 变异体留在生产文件里。
#: 收口前只有 g33 挂了它，g32b / g32cb / g32ccr1 三套都漏。
#: SIGKILL 挡不住 —— 如实声明：被 `-9` 打断时靠下一次启动的自愈还原兜底。
RESTORE_SIGNALS: tuple[int, ...] = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT)


class RestoreGuard:
    """「**先还原再退出**」+「还原期不可打断」的信号闩。

    收口前四套的三种写法各有各的洞：
      · g32b / g32cb / g32ccr1 —— handler 把信号转成异常让 `finally` 跑，但
        **漏了 SIGQUIT**；
      · g33 —— 四个信号齐全且先 `restore_all()` 再退出，但**还原循环本身**若被
        第二个信号打断，会停在「还原了一半」的状态：一部分目标文件已写回、
        另一部分还留着变异体 —— 而 harness 已经退出，没人再去补。

    本类把两边的长处合起来：
      1. 四个信号全挂；
      2. 收到信号先跑 `restore()`，再 `SystemExit(exit_code)`；
      3. `critical()` 区间内（= 还原循环本身）收到的信号**只记待办、不打断**，
         等还原做完再兑现。⇒ 「还原」这件事要么没开始，要么整个做完。

    ⚠️ 如实声明它挡不住什么：`SIGKILL` / `SIGSTOP` 不可捕获；进程被外部超时
    连同进程组一起 `-9` 时，变异体会留在文件里。g32b / g32cb / g32ccr1 靠下一次
    启动的 `_self_heal*` 兜底；**g33 没有自愈**，只剩跑前跑后的全文件 sha 对账。
    """

    def __init__(self, restore, *, exit_code: int = 130, log=None) -> None:
        self._restore = restore
        self._exit_code = exit_code
        # ⚠️ 默认带 flush：信号路径上的日志若卡在缓冲里，进程退出时可能根本没印出来，
        # 于是「还原过了吗」这件事在事后无从判断。
        _raw_log = log or (lambda msg: print(msg, flush=True))

        def _safe_log(msg: str) -> None:
            # ⛔ 日志**绝不能**挡住退出（Codex round-1 MEDIUM）：还原期 handler 登记
            # pending 后立即 log，失败/成功路径也都先 log 再 raise SystemExit ——
            # 日志一抛异常就到不了退出语句，而 `_finishing` 已置位 ⇒ 信号全体失效。
            # 写不出来就算了，退出码不依赖日志是否写成功。
            try:
                _raw_log(msg)
            except BaseException:  # noqa: BLE001  日志失败不改变控制流
                pass

        self._log = _safe_log
        self._in_critical = False
        self._pending: int | None = None
        # ⛔ 防重入：`_finish` 期间再收到信号，只能记待办、不能再起一次 `_finish`。
        # 首版没有它 —— 负控里「还原循环每跑一次就发一次 SIGTERM」当场把它打成无限
        # 递归（实测 RecursionError，rc=1 而不是 130）。真实场景里外部反复 `kill`
        # 同样能触发。
        self._finishing = False

    def install(self) -> None:
        for sig in RESTORE_SIGNALS:
            signal.signal(sig, self._handler)

    def _handler(self, signum, _frame):
        if self._in_critical:
            # ⛔ 不打断还原：只把信号记下来，等还原做完在 critical() 出口兑现。
            self._pending = signum
            self._log(f"\n⚠️ 还原进行中，收到信号 {signum} —— 记下待办，还原完再退出")
            return
        self._finish(signum)

    def _finish(self, signum: int):
        if self._finishing:
            # ⛔ 不静默丢弃: 退出展开期间兑现不了「还原完再退出」的承诺(再进一次 _finish
            # 会与进行中的还原互踩), 至少要把「丢弃」这件事说出来。
            self._log(f"\n⚠️ 退出展开期间收到信号 {signum} —— 已在退出流程中, 不再重启还原, 丢弃")
            return
        self._finishing = True
        # ⛔ 这一段被独立复核连打两次，两个方向都要顶住：
        #   ① 首版把 `raise SystemExit` 写在还原**后面** ⇒ 还原一出错就永不退出，而
        #      `_finishing` 已置位 ⇒ 此后四个信号**全部静默失效**，进程带着变异体跑到底；
        #   ② 第二版改成 `finally: raise SystemExit` ⇒ 退出是保证了，但那条 `raise`
        #      会把 `_restore()` 的异常**整个吞掉**：退出码照旧 130、stderr 一片空白，
        #      而变异体还留在生产文件里 —— 「还原失败」这件事一点痕迹都不留，比不退出更糟。
        # ⇒ 两条都要：异常先打出来（traceback 进 stderr），再用**不同的退出码**退出，
        #    让「还原成功后被中断」与「还原失败」在 rc 上就能分开。
        try:
            with self.critical():
                self._restore()
        except BaseException as exc:  # noqa: BLE001  故意兜住一切: 这是退出路径的最后一道
            # ⛔ 诊断输出也不能挡住退出（round-2 MEDIUM）：`traceback.print_exc()` 写
            # stderr 失败会让下面的 `raise SystemExit` 到不了，而 `_finishing` 已置位
            # ⇒ 后续信号只记录不退出。round-1 的 `_safe_log` 没覆盖这里。
            try:
                traceback.print_exc()
            except BaseException:  # noqa: BLE001  诊断失败不改变控制流
                pass
            self._log(
                f"\n⛔ 收到信号 {signum} 后**还原失败**: {type(exc).__name__}: {exc}\n"
                f"⛔ 变异体可能仍留在生产文件里 —— 立即人工核对全文件 sha, 不要提交"
            )
            raise SystemExit(self._exit_code + 1) from exc
        # ⚠️ 只声称**登记过的**文件: 三套的还原回调只覆盖 `_ACTIVE_SNAPSHOT`(当前变异
        # 碰过的文件), 不是「全部目标文件」—— 完整性由跑后的全文件 sha 对账说了算。
        self._log(f"\n⚠️ 收到信号 {signum}，已还原全部登记过的目标文件后退出（完整性以全文件 sha 对账为准）")
        raise SystemExit(self._exit_code)

    def exiting(self) -> bool:
        """是否已进入退出展开（`_finish` 已选定退出码）。

        ⛔ round-3 MEDIUM：`_finish` 抛 `SystemExit(131)` 后，调用方栈展开仍会进入
        各自的 `finally` 再还原一次；若还原持续遇到**同一个 I/O 错误**，第二次异常会
        **替换掉** `SystemExit(131)`，最终按未捕获异常退出 —— 约定的退出码丢了。
        调用方的 finally 应据此把二次还原的异常吞掉（还原尝试与诊断都保留）。
        """
        return self._finishing

    @contextlib.contextmanager
    def critical(self):
        """还原期：这一段里收到的信号不打断，出口再兑现。可嵌套。"""
        if self._in_critical:  # 已在还原期内（`_finish` → `critical` 的嵌套）
            yield
            return
        self._in_critical = True
        try:
            yield
        finally:
            self._in_critical = False
            pending, self._pending = self._pending, None
            if pending is not None:
                self._finish(pending)


# ── 表自检 ──────────────────────────────────────────────────────────────────


def _read_prod_blobs(prod_roots: tuple[Path, ...]) -> tuple[list[tuple[Path, bytes]], list[str]]:
    """把生产侧扫描面一次读进内存；返回 `(blobs, 扫描失败说明)`。

    ⛔ 用 `os.walk(onerror=...)` 而不是 `Path.rglob("*")`：`rglob` 会**在遍历内部
    吞掉 `PermissionError`** —— 一个读不进去的子目录会让扫描静默少看一片，而
    「生产侧命中 0 次」这条判据于是变成「我没看见」而不是「不存在」。假绿。
    外层再包 try/except 也够不着，异常在 rglob 里就没了。
    （2026-09-08 由 U10-A 车道在自己那道 AST 扫描门上实测出同一形态并交叉通报。）
    """
    blobs: list[tuple[Path, bytes]] = []
    errors: list[str] = []

    def _onerror(exc: OSError) -> None:
        errors.append(f"扫描面枚举失败: {exc}")

    for root in prod_roots:
        if root.is_file():
            candidates = [root]
        else:
            candidates = []
            for dirpath, _dirnames, filenames in os.walk(root, onerror=_onerror, followlinks=False):
                # ⛔ 目录符号链接：`followlinks=False` 让 os.walk **不进入**它，而
                # `_dirnames` 被丢掉 ⇒ 整棵子树既没扫也不进 errors（round-2 MEDIUM：
                # round-1 只补了文件链接）。这里显式记下来。
                for _d in _dirnames:
                    _dp = Path(dirpath) / _d
                    if _dp.is_symlink():
                        errors.append(
                            f"扫描面跳过**目录**符号链接 {_dp} —— 其子树未被扫描, 「生产侧命中 0 次」对该子树不成立"
                        )
                candidates.extend(Path(dirpath) / f for f in filenames)
        for f in candidates:
            # ⛔ 符号链接**不静默跳过**（Codex round-1 MEDIUM，撤回我此前对同型发现的
            # 误推翻）：跳过就意味着「expect_msg 生产侧 0 次」对链接目标**不成立**，
            # 而 errors 里一点痕迹没有 —— 与 rglob 吞 PermissionError 是同一个假绿面。
            # 现在把跳过记进 errors：自检消费方只看返回列表, 打印等于没说。
            if f.is_symlink():
                errors.append(
                    f"扫描面跳过符号链接 {f} —— 「生产侧命中 0 次」对其链接目标不成立, 须人工核或解引用后重扫"
                )
                continue
            if not f.is_file():
                continue
            try:
                blobs.append((f, f.read_bytes()))
            except OSError as exc:
                errors.append(f"读不了 {f}: {exc}")
    return blobs, errors


def check_expect_msg_unique(
    items: list[tuple[str, str, str | None]],
    *,
    exempt: dict[str, str] | None = None,
    prod_roots: tuple[Path, ...] = (),
) -> list[str]:
    """`expect_msg` 唯一性自检。`items` = `[(变异 id, 门文件路径, expect_msg), ...]`。

    返回违规说明列表(空 = 通过)。三条判据：

    1. 非豁免条目的 `expect_msg` 不得为空 —— 「不能一次补全」必须**显式**登记进
       豁免表并写理由，不得静默 `None`；
    2. `expect_msg` 在它绑定的**门文件**里恰好出现 1 次 —— 不唯一 ⇒ 「红在哪一条
       断言上」不再可证；
    3. `expect_msg` 在**生产文件**里出现 0 次 —— pytest 会给多行断言消息的每一行
       加 `E ` 前缀，一条内嵌子进程输出的前提断言红了就能把生产侧的字符串灌进
       判据面。命中 0 次，生产输出就喂不饱它。(`prod_roots` 为空则跳过这一条，
       并**不**声称检查过。)

    ⛔ 为什么写成门而不是「作者跑一次 grep 确认过」：手工查出来的不变量不写成
    判据 = 没查。CARD-G3-3-R1 当场就破过一次 —— 给断言加注释时把 `expect_msg`
    的原文复述进了注释，那条片段在门文件里变成 2 次。
    """
    exempt = exempt or {}
    problems: list[str] = []
    # ⛔ 「显式登记理由」得真的是判据: 空理由的登记等于没登记(独立复核 LOW)。
    for mid, why in exempt.items():
        if not str(why).strip():
            problems.append(f"{mid}: 豁免表里登记了**空理由** —— 显式登记必须写清为什么")
    cache: dict[str, str] = {}
    # ⛔ 生产侧扫描面**只读一遍**再复用：原实现对**每一条** expect_msg 都把整个
    # `canvas-vault` + `backend/app` 重扫一遍（约 1200 个文件）。18 条时只是慢，
    # 138 条时就成了「太慢所以干脆不开这道检查」——判据因为代价被关掉，和没有
    # 判据是一回事。
    # ⛔ `prod_roots` 收**目录或单个文件**：被变异的生产文件里有一部分
    # (`validate_learning_events.py`) 就住在 `backend/scripts/` —— 而那个目录
    # 同时装着 harness 自己, 后者的 `EXPECT_MSG` 表里逐字写着这些片段。
    # 整目录扫会把「表里写了」误报成「生产里也有」⇒ 判据自指。
    prod_blobs, scan_errors = _read_prod_blobs(prod_roots)
    problems.extend(scan_errors)
    for mid, gate_file, expect_msg in items:
        if expect_msg is None:
            if mid not in exempt:
                problems.append(f"{mid}: expect_msg 为空且不在豁免表里(须填实值或显式登记理由)")
            continue
        if mid in exempt:
            problems.append(f"{mid}: 既填了 expect_msg 又在豁免表里 —— 豁免表须只列真的填不出来的条目")
        if not expect_msg:
            problems.append(f"{mid}: expect_msg 是空串(恒命中) —— 等于没有判据")
            continue
        if gate_file not in cache:
            p = Path(gate_file)
            if not p.exists():
                problems.append(f"{mid}: 门文件不存在 {p}")
                continue
            cache[gate_file] = p.read_text(encoding="utf-8")
        n = cache[gate_file].count(expect_msg)
        if n != 1:
            problems.append(f"{mid}: expect_msg {expect_msg!r} 在门文件里出现 {n} 次(应为 1)")
        needle = expect_msg.encode()
        for f, blob in prod_blobs:
            if needle in blob:
                problems.append(f"{mid}: expect_msg {expect_msg!r} 也出现在生产文件 {f} 里(须 0 次)")
    return problems


def check_expect_loc_unique(
    items: list[tuple[str, str, str | None]],
    *,
    exempt: dict[str, str] | None = None,
) -> list[str]:
    """`expect_loc` 自检。`items` = `[(变异 id, 门文件路径, expect_loc), ...]`。

    三条判据（与 `check_expect_msg_unique` 同型，但判的是**位置身份**）：

    1. 非豁免条目不得为空 —— 绑不出来必须显式登记理由，不得静默 `None`；
    2. `"stmt:<指纹>"` 必须在门文件里**恰好命中 1 条语句** —— 命中 0 条 = 锚已
       漂（门被改写），命中 >1 条 = 同一份代码写了两遍、身份不可证；
    3. `"file:<名>"` 形态**不被支持** —— 落在门文件外的条目应 `expect_loc` 留空并
       登记两张豁免表（⇒ KILLED-UNBOUND），⛔ 不得当成与 `stmt:` 同等强度上报。
    """
    exempt = exempt or {}
    problems: list[str] = []
    for mid, why in exempt.items():
        if not str(why).strip():
            problems.append(f"{mid}: 位置豁免表里登记了**空理由** —— 显式登记必须写清为什么")
    fps_cache: dict[str, dict[str, list[int]]] = {}
    for mid, gate_file, expect_loc in items:
        if expect_loc is None:
            if mid not in exempt:
                problems.append(f"{mid}: expect_loc 为空且不在豁免表里(须填实值或显式登记理由)")
            continue
        if mid in exempt:
            problems.append(f"{mid}: 既填了 expect_loc 又在豁免表里 —— 豁免表须只列真的绑不出来的条目")
        if expect_loc.startswith("file:"):
            # ⛔ `file:` 形态**不支持**：登记进豁免表也过不了这道门(旧文案让人那么做，
            # 照做会再吃一条「既填了又在豁免表里」—— 不可执行的指引)。唯一正确做法:
            # expect_loc 留空 + 两张豁免表都写理由 ⇒ KILLED-UNBOUND。
            problems.append(
                f"{mid}: expect_loc {expect_loc!r} 是文件级弱身份, 不被支持 —— "
                f"落在门文件之外的条目应 expect_loc 留空并登记两张豁免表(⇒ KILLED-UNBOUND)"
            )
            continue
        if not expect_loc.startswith("stmt:"):
            problems.append(f"{mid}: expect_loc {expect_loc!r} 形态不认识(须 `stmt:<12 位十六进制>`)")
            continue
        p = Path(gate_file)
        if not p.exists():
            problems.append(f"{mid}: 门文件不存在 {p}")
            continue
        if gate_file not in fps_cache:
            fps_cache[gate_file] = stmt_fingerprints(p)
        hits = fps_cache[gate_file].get(expect_loc[5:], [])
        if len(hits) != 1:
            problems.append(
                f"{mid}: expect_loc {expect_loc!r} 在门文件里命中 {len(hits)} 条语句(应为 1)"
                f"{' —— 门被改写，锚失效' if not hits else f' 行号 {hits}'}"
            )
    return problems
