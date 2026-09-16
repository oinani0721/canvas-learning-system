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

import pytest
import yaml

from tests.skills.skill_portability_lint import (
    BASELINE,
    BODY_METRICS,
    DEFAULT_ROOT,
    DYNAMIC_TMP_JOIN_BASELINE,
    ESCAPING_TMP_BASELINE,
    EXPECTED_SKILLS,
    MANAGED_FILE_DIGESTS,
    OPAQUE_TMP_BASELINE,
    PARENT_DIR_PROSE_BASELINE,
    QUIZ_ANSWER_BASELINE,
    SCRIPTS_BASELINE,
    SCRIPT_METRICS,
    SUSPICIOUS_TMP_LINES_BASELINE,
    TMP_BLOCK_BASELINE,
    TMP_NAMESPACE,
    U6_SCRIPTS_BASELINE,
    URL_OVERRIDE_BASELINE,
    _TMP_NS_RE,
    _backtick_spans,
    _body_counts,
    _fence_blocks,
    _has_dynamic_tmp_join,
    _line_fingerprint,
    _merged_body_baseline,
    _merged_scripts_baseline,
    _parse_units,
    _parse_units_cached,
    _py_strings_cached,
    _url_override_hit,
    bare_8011,
    bare_tmp,
    check_body,
    check_dynamic_tmp_joins,
    check_escaping_tmp,
    check_frontmatter,
    check_handoff_constants,
    check_managed_files,
    check_opaque_tmp,
    check_parent_dir_prose,
    check_scripts,
    check_suspicious_tmp_lines,
    check_tmp_blocks,
    check_url_override,
    dynamic_tmp_join_lines,
    escaping_tmp_paths,
    managed_file_digests,
    opaque_tmp_lines,
    parent_dir_prose_lines,
    suspicious_tmp_lines,
    tmp_block_fingerprints,
    url_default_overridden_lines,
)


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
    # ⛔ r17 LOW-1: 还要钉住**短单元也在** —— 只保留长单元的话, 「heredoc 终止符」那种
    # 解释就丢了, 而并集的定义就是两种都留。
    assert any(c.count("\n") == 1 and "elif" not in c for _o, c, p in units if p is not None), (
        f"短单元(在此切断的那种解释)也必须保留, 实得: {[c[:30] for _o, c, _p in units]}"
    )
    # ⛔ 并且要真的检验合法的 `else \`␊`:` 显式续行 —— 上一版只测了长单元的存在。
    cont = _parse_units(["if False:", "    pass", "else \\", ":", '    P = "/tmp/cls-exam/" ".." "/x"'])
    assert any(v == "/tmp/cls-exam/../x" for _o, _c, p in cont if p for v in p), (
        f"`else \\`␊`:` 是合法 Python 显式续行, 必须能折出常量链, 实得: {cont}"
    )


def test_union_expansion_is_looped_unbounded_and_deduplicated():
    r"""⛔ 局部回归断言: 并集扩张的**三处**关键性质各自可被单独证伪(r18 LOW-1)。

    Codex 连续三轮指出「整改没有断言锁住」—— 内存回退掉修复后 78 项断言仍全过。
    这条把三处性质分别钉死, 每条都能被对应的回退单独打红:

    ① **候选取多重集差**: 重叠部分不能计两次 —— 计两次的话, 登记后就成了可以抵消
       新增路径的额度(r17 MEDIUM-1);
    ② **扩张是循环的**: 连续多个 `elif` 时每一段都要被覆盖(r17 HIGH-1);
    ③ **不设固定窗口**: 跨几十行的续接链照样要提取(r17 HIGH-1)。
    """
    # ① 一处路径只该贡献一个候选(回退成"长短各计一次"时会变成两个)
    one = _parse_units(["if True:", '    P = "/t" "mp/one.json"', "else:", "    pass"])
    cands = [v for _o, _c, p_ in one if p_ for v in p_ if "/tmp" in v]
    assert cands.count("/tmp/one.json") == 1, f"重叠部分的候选被计了多次 ⇒ 登记后可抵消新增路径, 实得: {cands}"

    # ② 连续两个 elif: 第二个里的常量链也必须被折出(只扩张一次时它会退给 shlex)
    two = _parse_units(
        [
            "if False:",
            "    pass",
            "elif False:",
            "    pass",
            'elif ("/tmp/cls-exam/" ".." "/x") == q:',
            "    pass",
        ]
    )
    assert any("/tmp/cls-exam/../x" in v for _o, _c, p_ in two if p_ for v in p_), (
        f"第二个 `elif` 里的常量链没被折出 ⇒ 扩张只做了一次, 实得: {two}"
    )

    # ③ 续接链跨 60 行仍要提取(固定 40 行窗口时这里会漏)
    long_body = (
        ["if False:", "    pass"]
        + ["    pass"] * 60
        + [
            'elif ("/tmp/cls-exam/" ".." "/y") == q:',
            "    pass",
        ]
    )
    assert any("/tmp/cls-exam/../y" in v for _o, _c, p_ in _parse_units(long_body) if p_ for v in p_), (
        "跨 60 行的续接链没被提取 ⇒ 找续接词的固定窗口回来了"
    )

    # ③' 续接子句**头本身**跨 45 行(内层累加也不能有固定窗口)
    wide_head = (
        ["if False:", "    pass", "elif ("]
        + ["    # c"] * 45
        + [
            '    "/tmp/cls-exam/" ".." "/z") == q:',
            "    pass",
        ]
    )
    assert any("/tmp/cls-exam/../z" in v for _o, _c, p_ in _parse_units(wide_head) if p_ for v in p_), (
        "跨 45 行的续接子句头没被提取 ⇒ 内层累加的固定窗口回来了"
    )

    # ④ delta 为空的长单元, **源码**也要保留(r18 HIGH-1) —— `dynamic_tmp_join_lines`
    # 看的是 chunk 文本而不是候选列表, 丢掉源码那几行就再也没人看。
    # 用一个**候选确实为空**的长单元(没有任何字符串常量)来考「源码无条件保留」。
    empty_delta = _parse_units(["if False:", "    pass", "else:", "    x += 1"])
    assert any("else:" in c for _o, c, p_ in empty_delta if p_ is not None), (
        f"候选为空的长单元被丢弃了, 而 `cur_j` 照样前进 ⇒ 那几行再也没人看(r18 HIGH-1): "
        f"{[c[:28] for _o, c, _p in empty_delta]}"
    )


def test_constant_chain_and_bytes_handling_are_load_bearing():
    r"""⛔ 局部回归断言: 「只收最外层折叠链」与「bytes 一并折/收」各自可被单独证伪。

    r19 LOW 指出这两处整改仍没有断言锁住(撤销后 93 次现有调用仍全过)。这条把它们
    分别钉死 —— 判据的正确性不该靠「碰巧别的机制补上了」。
    """
    # ① 嵌套 `+` 链只收最外层: `"/t" + "mp" + ""` 是**一处**路径, 只该贡献一个候选。
    #    收内层子链的话会贡献两个, 登记后就成了可以抵消新增路径的额度(r18 MEDIUM-1)。
    one = [n for _c, n in escaping_tmp_paths('```python\nP = "/t" + "mp" + ""\n```')]
    assert one.count("fence:/tmp") == 1, f"嵌套常量链重复贡献了候选: {one}"

    # ② bytes 的显式 `+` 链要能折出整条路径(r19 HIGH-3) —— 单块、合法 Python、
    #    普通常量加法, 只折 str 的话整类漏检。
    bad = '```python\nP = b"/t" + b"mp/cls-exam/" + b".." + b"/x"\n```'
    assert any(n == "fence:/tmp/x" for _c, n in escaping_tmp_paths(bad)), (
        f"bytes 常量链没被折出越界路径: {escaping_tmp_paths(bad)}"
    )
    safe = bad.replace('b".."', 'b"ok"')
    assert not escaping_tmp_paths(safe), f"对照的合规 bytes 链不该报越界: {escaping_tmp_paths(safe)}"

    # ③ bytes **叶**常量的收集(r18 HIGH-2)与②是两处代码: ②是 `_fold_str()` 折显式 `+`,
    #    这里是 `_py_strings()` 收 `Constant` 叶。`ast` 把**隐式相邻拼接**在解析期就合成
    #    一个 bytes `Constant`, 所以它走不到 `+` 那条路。r20 LOW-1: 撤掉这处收集后 94 次
    #    现有纯函数断言仍全过, 只有下面这条会红。
    implicit = '```python\nP = b"/t" b"mp/cls-exam/" b".." b"/x"\n```'
    assert any(name == "fence:/tmp/x" for _c, name in escaping_tmp_paths(implicit)), (
        f"bytes 叶常量(隐式相邻拼接)没被收进候选: {escaping_tmp_paths(implicit)}"
    )

    # ④ bytes 解码必须**先折完再解一次**且不丢身份(r20 MEDIUM-4)。`replace` 会把不同的
    #    不可解码字节压成同一个 U+FFFD ⇒ 登记一条后另一条可静默顶替它(基线是多重集);
    #    逐叶解码把 `b"\xc3" + b"\xa9"` 解成两个 U+FFFD 而不是 `é` —— 与运行时不是同一条路径。
    ff = [n for _c, n in escaping_tmp_paths('```python\nP = b"/t" + b"mp/\\xff/x"\n```')]
    fe = [n for _c, n in escaping_tmp_paths('```python\nP = b"/t" + b"mp/\\xfe/x"\n```')]
    assert ff and fe and ff != fe, f"两个不同的不可解码字节折成了同一个候选: {ff} vs {fe}"
    utf8 = [n for _c, n in escaping_tmp_paths('```python\nP = b"/t" + b"mp/" + b"\\xc3" + b"\\xa9" + b"/x"\n```')]
    assert utf8 == ["fence:/tmp/é/x"], f"bytes 链被逐叶解码了(应先拼完整条再解一次): {utf8}"


def test_r20_judge_branches_are_load_bearing():
    r"""⛔ 局部回归断言: r20 整改各自可被单独证伪(HIGH-1 / MEDIUM-1,2,3 / MEDIUM-5)。

    r20 LOW-2 指出上一轮的 URL **整体重写**一条回归断言都没有 —— 而重写恰恰是最该有
    断言的改法(补丁互相打架到第三次才重写, 说明这块的边界很容易改错)。每组都配一个
    **结构相同**的安全对照, 否则「坏形态被抓」可能只是判据对什么都报。
    """
    # ① HIGH-1: 重复赋值检查要用**折叠值**, 不能只看叶常量。两个叶都不含 `/tmp`,
    #    折完才含 ⇒ `P` 进不了 `tmp_targets`, 而最终路径已经是 `/etc/passwd`。
    bad = '```python\nP = "/t" + "mp/cls-exam/x"; P = "/etc/passwd"\n```'
    safe = '```python\nP = "/t" + "mp/cls-exam/x"; Q = "/etc/passwd"\n```'
    assert dynamic_tmp_join_lines(bad), "折叠常量的重复赋值没被抓到(判据还停在叶常量)"
    assert not dynamic_tmp_join_lines(safe), f"安全对照(换个名字)被误报: {dynamic_tmp_join_lines(safe)}"

    # ② MEDIUM-1: 注释剥离必须认引号 —— `printf "#"` 里的 `#` 不开启注释。
    assert _url_override_hit('printf "#"; unset CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'), (
        "引号内的 `#` 被当成注释开头, 后面真实的 `unset` 整条漏检"
    )
    assert not _url_override_hit('printf "#"; :; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'), (
        "安全对照(`unset` 换成 `:`)被误报 —— 说明上一条抓到的不是 `unset`"
    )
    assert _url_override_hit("echo ${#CLS_BACKEND_URL}; unset CLS_BACKEND_URL"), "`${#VAR}` 后面的 `unset` 漏检"
    assert not _url_override_hit('curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"  # unset CLS_BACKEND_URL'), (
        "真注释没被剥掉 ⇒ 误报"
    )

    # ③ MEDIUM-2: 变量必须**罩住端口号本身**才算控制地址; 落在 path 上不算。
    assert _url_override_hit('curl "${OTHER:-http://localhost:8011}/${CLS_BACKEND_URL}"'), (
        "地址由 `OTHER` 决定、目标变量只在 path 上, 判据却放行了"
    )
    assert not _url_override_hit('curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'), "整改形态本身被误报"
    assert _url_override_hit('curl "${CLS_BACKEND_URL:+http://localhost:8011}/x"'), "`:+` 语义相反, 应登记"

    # ④ MEDIUM-3: `env` 双向 —— 长选项/粘连要抓, 无关子进程与外层展开不能误报。
    for form in (
        "env --ignore-environment bash -c 'curl \"${CLS_BACKEND_URL:-http://localhost:8011}/x\"'",
        "env -uCLS_BACKEND_URL bash -c 'curl \"${CLS_BACKEND_URL:-http://localhost:8011}/x\"'",
    ):
        assert _url_override_hit(form), f"`env` 清环境形态漏检: {form}"
    for form in (
        "env -i bash -c 'true'; curl \"${CLS_BACKEND_URL:-http://localhost:8011}/x\"",
        "env -u OTHER sh -c 'curl \"${CLS_BACKEND_URL:-http://localhost:8011}/x\"'",
        'env -i bash -c "curl ${CLS_BACKEND_URL:-http://localhost:8011}/x"',
    ):
        assert not _url_override_hit(form), f"`env` 误报(清的不是这条命令的环境/外层已展开): {form}"

    # ⑤ MEDIUM-5: code span 空白按 CommonMark 归一化(换行→空格, 剥一对首尾空格)。
    assert _backtick_spans("见 ` /tmp/cls-exam/x ` 处") == ["/tmp/cls-exam/x"], "首尾各一个空格没剥掉 ⇒ 误报"
    assert _backtick_spans("见 ` /tmp/x` 处") == [" /tmp/x"], "只有一侧空格时不该剥(CommonMark 要求两侧都是)"
    assert _backtick_spans("`a\nb`") == ["a b"], "span 内的换行没换成空格"

    # ③ 动态判据的预筛要看**整段**解析出的字符串, 不是扣重后的 delta(r19 HIGH-2)。
    脱钩 = (
        '```python\nif True:\n    P = "/t" "mp/cls-exam/x"\n'
        '    if False:\n        pass\n    else:\n        P = "/etc/passwd"\n```'
    )
    assert dynamic_tmp_join_lines(脱钩), "合规常量与实际赋值脱钩, 动态判据必须要求登记"
    assert not dynamic_tmp_join_lines(脱钩.replace('        P = "/etc/passwd"', '        Q = "/etc/passwd"')), (
        "改成另一个变量名后不该报红(否则这条负控考错了对象)"
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


def test_r21_reassignment_targets_and_block_scope_are_load_bearing():
    r"""⛔ 局部回归断言: 重赋值判据的**写入目标识别**与**作用域**各自可被单独证伪。

    r21 两条 HIGH 都出在这一处判据上, 但它们是**两个不同的修点**:
      · HIGH-1 是「值的口径修好了, 写入目标的识别没补齐」——
        `P, = (…)` / `(P := …)` / `P += …` / `for P in …` 都是重绑, 只认 `Assign` 的
        直接 `Name` 就全漏;
      · HIGH-2 是「作用域太小」—— 同一个 fence 里两条**相邻**语句分处两个语法单元,
        两次写入从来不会同时被看见。这不是已声明的跨块边界。
    两条的坏形态源码里都**没有连续的 `/tmp`**, 所以块指纹兜底网也不进 —— 不能指望它。
    """
    good = 'P = "/t" + "mp/cls-exam/x"'
    # ① 写入目标: 六种重绑写法, 每种配一个「换个名字」的等结构安全对照。
    for label, second, swapped in (
        ("元组解包", 'P, = ("/etc/passwd",)', 'Q, = ("/etc/passwd",)'),
        ("walrus", '(P := "/etc/passwd")', '(Q := "/etc/passwd")'),
        ("增量赋值", 'P *= 0; P += "/etc/passwd"', 'Q *= 0; Q += "/etc/passwd"'),
        ("列表解包", '[P] = ["/etc/passwd"]', '[Q] = ["/etc/passwd"]'),
        ("星号解包", '*P, _ = ("/etc/passwd", 1)', '*Q, _ = ("/etc/passwd", 1)'),
    ):
        bad = f"```python\n{good}; {second}\n```"
        safe = f"```python\n{good}; {swapped}\n```"
        assert dynamic_tmp_join_lines(bad), f"{label}的重绑没被计为写入: {second}"
        assert not dynamic_tmp_join_lines(safe), f"{label}的安全对照被误报: {swapped}"
    loop_bad = f'```python\n{good}\nfor P in ["/etc/passwd"]:\n    pass\n```'
    loop_safe = loop_bad.replace("for P in", "for Q in")
    assert dynamic_tmp_join_lines(loop_bad), "`for P in …` 的重绑没被计为写入"
    assert not dynamic_tmp_join_lines(loop_safe), "`for Q in …` 的安全对照被误报"

    # ② 作用域: 同 fence 相邻语句(跨语法单元)。
    adj_bad = f'```python\n{good}\nP = "/etc/passwd"\n```'
    adj_safe = f'```python\n{good}\nQ = "/etc/passwd"\n```'
    assert dynamic_tmp_join_lines(adj_bad), "同 fence 相邻两行的重赋值没被看见(判据只在语法单元内跑)"
    assert not dynamic_tmp_join_lines(adj_safe), f"相邻两行的安全对照被误报: {dynamic_tmp_join_lines(adj_safe)}"
    spread = f'```python\n{good}\nX = 1\nY = 2\nP = "/etc/passwd"\n```'
    assert dynamic_tmp_join_lines(spread), "隔了几条语句的重赋值没被看见"
    # 顺序相反 ⇒ 最终值就是合规的那个, 不该报。
    assert not dynamic_tmp_join_lines(f'```python\nP = "/etc/passwd"\n{good}\n```'), (
        "先赋越界值、后赋合规值 —— 最终值合规, 不该登记"
    )


def test_r21_shell_lexer_branches_are_load_bearing():
    r"""⛔ 局部回归断言: 共用 shell 掩码 / URL 地址绑定 / 目标变量写入面 各自可被证伪。

    r20 的注释剥离与 r21 的分号切段**各错一次, 根因相同**: 两处都要回答「这个字符是
    结构字符还是数据」, 却各写了一份状态机。现在统一走 `_sh_protect_mask()`, 这条
    把两边的行为一起钉住。
    """
    d = 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'

    # ① 引号感知的命令段切分 + 子 shell 识别面(r21 MEDIUM-1)。
    assert _url_override_hit("env -i bash -c 'true; " + d + "'"), (
        "单引号脚本被从中间按 `;` 切开了 —— `env -i` 与目标变量分处两段, 关联丢失"
    )
    assert not _url_override_hit("env bash -c 'true; " + d + "'"), "安全对照(没有 -i)被误报"
    assert _url_override_hit("env -i bash -lc '" + d + "'"), "组合选项 `-lc` 没被识别"
    assert _url_override_hit("env -i bash -c $'" + d + "'"), "ANSI-C 引号脚本没被识别"
    # 双引号里**转义**的 `$` 留给子 shell 展开 —— 但抓到它的是**词级**判据而不是
    # `_env_clears_url()`: `\\` 挡在展开前面, 那个展开就不再是 URL token 的开头。
    # (曾为它写过一个 `env` 分支, 回退验证显示恒不决定结果, 已删。)
    assert _url_override_hit('env -i bash -c "curl \\${CLS_BACKEND_URL:-http://localhost:8011}/x"'), (
        "双引号里转义 `$` 的形态没被登记"
    )
    assert not _url_override_hit('env -i bash -c "' + d.replace('"', '\\"') + '"'), (
        "双引号未转义 ⇒ 外层 shell 已展开, `env` 撤销不了 ⇒ 不该报"
    )

    # ② 注释状态机: 参数展开 / ANSI-C 引号 / 嵌套命令替换里的 `#` 都不是注释。
    assert _url_override_hit(": ${OTHER:- #}; unset CLS_BACKEND_URL; " + d), (
        "`${…}` 里的 `#` 被当成注释开头, 后面真实的 `unset` 消失"
    )
    assert not _url_override_hit(": ${OTHER:- #}; :; " + d), "安全对照(`unset` 换成 `:`)被误报"
    assert _url_override_hit("echo $'a\\' #'; unset CLS_BACKEND_URL"), "ANSI-C 引号里的转义单引号被误当结束"
    assert _url_override_hit("""echo "$(printf '%s' " #")"; unset CLS_BACKEND_URL"""), (
        "命令替换内层的引号与外层混淆了 —— `$(…)` 需要独立的引号状态"
    )
    assert not _url_override_hit(d + "  # unset CLS_BACKEND_URL"), "真注释没被剥掉 ⇒ 误报"

    # ③ URL 地址绑定(r21 MEDIUM-3): 端口落在展开里 ≠ 展开控制主机。
    assert _url_override_hit('curl "${CLS_BACKEND_URL:-http://localhost:8011}@localhost/x"'), (
        "展开落进 userinfo, 真实主机是 `@` 后面那个"
    )
    assert _url_override_hit('curl "http://localhost:80/${CLS_BACKEND_URL:-http://localhost:8011}/x"'), (
        "展开整体在 path 上, 不控制地址"
    )
    assert not _url_override_hit(d), "整改形态本身被误报"
    assert not _url_override_hit("curl --url=${CLS_BACKEND_URL:-http://localhost:8011}/x"), (
        "`--url=` 前缀后的展开仍是 URL 开头, 不该报"
    )
    assert not _url_override_hit("env -u OTHER sh -c '" + d + "'"), (
        "判准写成「展开在**词**的开头」会在这里误报 —— 被引号包住的整条脚本也是一个词"
    )

    # ④ 目标变量的写入面(r21 MEDIUM-4): 数组下标赋值与 `printf -v` 同样清空配置。
    for bad, safe in (
        ("CLS_BACKEND_URL[0]=''; ", "OTHER[0]=''; "),
        ("printf -v CLS_BACKEND_URL %s ''; ", "printf -v OTHER %s ''; "),
    ):
        assert _url_override_hit(bad + d), f"目标变量写入形态漏检: {bad}"
        assert not _url_override_hit(safe + d), f"换个变量名的安全对照被误报: {safe}"

    # ⑤ bytes 编码必须单射(r21 MEDIUM-5): `backslashreplace` 生成的 `\xNN` 会与
    #    **原本就含字面反斜杠**的内容撞名, 所以要先把已有反斜杠转义掉。
    invalid = [n for _c, n in escaping_tmp_paths('```python\nP = b"/t" + b"mp/\\xff/x"\n```')]
    literal = [n for _c, n in escaping_tmp_paths('```python\nP = b"/t" + b"mp/\\\\xff/x"\n```')]
    assert invalid and literal and invalid != literal, f"无效字节与字面反斜杠折成了同一个候选: {invalid} vs {literal}"
    # r21 LOW-1: 叶常量分支要有自己的断言 —— 隐式相邻拼接走的不是 `_fold_str()` 那条路。
    li = [n for _c, n in escaping_tmp_paths('```python\nP = b"/t" b"mp/\\xff/x"\n```')]
    ll = [n for _c, n in escaping_tmp_paths('```python\nP = b"/t" b"mp/\\\\xff/x"\n```')]
    assert li and ll and li != ll, f"bytes **叶**常量分支的解码不单射: {li} vs {ll}"


def test_r22_reassignment_is_scope_aware_and_covers_all_bindings():
    r"""⛔ 局部回归断言: 重赋值判据的**作用域**与**绑定形式**全覆盖。

    本轮 Codex 在给出结论前用尽配额(见验收单 §五 round-22)。它中断时留在 stderr 里的是
    **探针输入**而不是裁定 —— 我把那些输入取出来自己跑, 实测出 3 条漏检 + 2 条误报,
    与后来补的形态一起钉在这里。**这条断言的依据是我自己的复现, 不是抢救来的结论。**

    · 漏检: `except … as P` / `import … as P` / `match: case P` —— 这三类的名字在 `ast`
      里是**裸字符串**(`ExceptHandler.name` / `alias.asname` / `MatchAs.name`),
      不是 `Name` 节点, 只按 `_target_names()` 找就整类看不见;
    · 误报: 上一版对整棵树 `ast.walk` 后**按名字**比, 于是函数体 / class 体里的同名
      局部变量被当成对模块级 `P` 的重赋值 —— 那是另一个绑定, 模块级的 `P` 一动没动。
    """
    good = 'P = "/t" + "mp/cls-exam/x"'
    fence = lambda body: f"```python\n{body}\n```"  # noqa: E731

    # ① 九种绑定形式都算写入, 每种配「换个名字」的等结构安全对照。
    for label, bad_tail, safe_tail in (
        (
            "except as",
            'try:\n    raise ValueError("/etc/passwd")\nexcept ValueError as P:\n    print(P)',
            'try:\n    raise ValueError("/etc/passwd")\nexcept ValueError as Q:\n    print(Q)',
        ),
        ("from-import as", "from pathlib import Path as P", "from pathlib import Path as Q"),
        ("import", "import P", "import Z"),
        (
            "match 捕获",
            'match "/etc/passwd":\n    case P:\n        print(P)',
            'match "/etc/passwd":\n    case Q:\n        print(Q)',
        ),
        ("match 星号", "match [1]:\n    case [*P]:\n        print(P)", "match [1]:\n    case [*Q]:\n        print(Q)"),
        ("def 同名", "def P():\n    pass", "def Z():\n    pass"),
        ("class 同名", "class P:\n    pass", "class Z:\n    pass"),
        (
            "global 后重绑",
            'def f():\n    global P\n    P = "/etc/passwd"',
            'def f():\n    global Q\n    Q = "/etc/passwd"',
        ),
        ("with as", "with ctx() as P:\n    pass", "with ctx() as Q:\n    pass"),
    ):
        assert dynamic_tmp_join_lines(fence(f"{good}\n{bad_tail}")), f"{label} 的重绑没被计为写入"
        assert not dynamic_tmp_join_lines(fence(f"{good}\n{safe_tail}")), f"{label} 的安全对照被误报"

    # ② 嵌套作用域里的同名变量是**另一个绑定**, 不是重赋值。
    for label, body in (
        ("函数体内同名", f'{good}\ndef f():\n    P = "/etc/passwd"\n    return P'),
        ("class 体内同名", f'{good}\nclass C:\n    P = "/etc/passwd"'),
        ("lambda 参数同名", f"{good}\ng = lambda P: P"),
        ("推导式变量", f'{good}\nQ = [P for P in ["/etc/passwd"]]'),
        ("嵌套函数局部", f'{good}\ndef f():\n    def g():\n        P = "/etc/passwd"\n    return g'),
    ):
        assert not dynamic_tmp_join_lines(fence(body)), f"{label} 被误报成重赋值(按名字比、没分作用域)"

    # ③ 刻意保留的保守面 —— 这三条**应该**报, 别当误报去修。
    assert dynamic_tmp_join_lines(fence(f'if c:\n    {good}\nelse:\n    P = "/etc/passwd"')), (
        "互斥分支的最终值静态不可判 —— 按本判据契约就该登记"
    )
    assert dynamic_tmp_join_lines(fence(f'def f():\n    {good}\n    P = "/etc/passwd"')), (
        "同一个函数作用域内的重赋值仍要抓"
    )
    assert dynamic_tmp_join_lines(fence(f'{good}\nQ = [(P := "/etc/passwd") for _ in [1]]')), (
        "PEP 572: 推导式内的海象绑在**外层**作用域 —— 所以推导式不能算作用域边界"
    )


def test_r22_reassignment_respects_control_flow_and_execution_regions():
    r"""⛔ 局部回归断言: 重赋值判据的**控制流三分法**与**执行区**边界。

    r22 复核给出的正确边界是「**同一执行区内的实际绑定与可达执行关系**」。它拆成三件事:
      · 绑定 —— 作用域(已由 `test_r22_…_covers_all_bindings` 钉住);
      · 可达执行关系 —— 源码行序**不等于**执行顺序, 见下面 ①;
      · 执行区 —— 一个 fence 里可能有多个(shell fence 内的 Python heredoc), 见 ③;
        而**相邻 fence 不能仅凭同名默认串联**(可能是不同示例、不同进程), 见 ③ 末条。
    """
    good = 'P = "/t" + "mp/cls-exam/x"'
    fence = lambda body, info="python": f"```{info}\n{body}\n```"  # noqa: E731
    hit = lambda body, info="python": bool(dynamic_tmp_join_lines(fence(body, info)))  # noqa: E731

    # ① 循环回边: 源码里越界那行在**前**, 但次轮才执行, 最终覆盖掉合规值。
    loop = f'for i in (0, 1):\n    if i:\n        P = "/etc/passwd"\n        break\n    {good}'
    assert hit(loop), "循环回边下按源码行序放行了 —— 源码行序不是执行顺序"
    assert not hit(loop.replace('        P = "/etc/passwd"', '        Q = "/etc/passwd"')), "循环安全对照被误报"
    assert hit(f'while c:\n    P = "/etc/passwd"\n    {good}'), "`while` 的回边同理"

    # ② 互斥分支: **两支都合规**时最终值必然合规 —— 上一版一律报, 那是误报。
    #    我曾把它辩护成「静态不可判 ⇒ 该报」, r22 复核指出该辩护不成立。
    assert not hit('if c:\n    P = "/tmp/cls-exam/a"\nelse:\n    P = "/tmp/cls-exam/b"'), (
        "互斥分支两支都合规, 走哪支最终值都合规 —— 不该登记"
    )
    assert hit(f'if c:\n    {good}\nelse:\n    P = "/etc/passwd"'), "一支合规一支越界 ⇒ 静态不可判, 要登记"
    assert hit(f'try:\n    {good}\nexcept E:\n    P = "/etc/passwd"'), "`try/except` 两支混合同理"
    # ⛔ 这一条才真正考「互斥」判定: 越界那支在**前**、合规那支在后, 直线规则会判成
    # 「先越界后合规 ⇒ 安全」, 但两支互斥, 走 `if` 分支时最终值就是越界的那个。
    assert hit(f'if c:\n    P = "/etc/passwd"\nelse:\n    {good}'), (
        "互斥分支下越界在前, 被直线规则误判成安全 —— 分支不能按源码先后看"
    )

    # ③ 直线代码里顺序**有**意义 —— 全顺序无关会把形态表的安全对照弄红(第一版踩到)。
    assert hit(f'{good}\nP = "/etc/passwd"'), "直线: 先合规、被后面改写 ⇒ 登记"
    assert not hit(f'P = "/etc/passwd"\n{good}'), "直线: 先越界后合规, 最终值合规 ⇒ 不登记"
    assert not hit('P = "/var/cache"\nP = "/tmp/cls-exam/x"'), "形态表 HIGH-4 的安全对照必须保持绿"
    # 位置比较用 `(行号, 列偏移)`: 分号写成一行时行号相同, 只比行号会让同样的内容
    # 因为写成一行还是两行而结果不同(r22 LOW)。
    for a, b in (
        (f'{good}; P="/etc/passwd"', f'{good}\nP="/etc/passwd"'),
        ('P="/etc/passwd"; ' + good, 'P="/etc/passwd"\n' + good),
    ):
        assert hit(a) == hit(b), f"同样的内容, 分号版与换行版结果不同: {a!r}"

    # ④ 执行区: shell fence 里的 Python heredoc 是**同一个** Python 执行区。
    hd = f"python3 - <<'PYEOF'\n{good}\nP = \"/etc/passwd\"\nPYEOF"
    assert hit(hd, "sh"), "shell fence 里的 Python heredoc 整类漏检(只认「整块是合法 Python」)"
    assert not hit(hd.replace('\nP = "/etc/passwd"', '\nQ = "/etc/passwd"'), "sh"), "heredoc 安全对照被误报"
    for opener, closer in (('<<"EOF"', "EOF"), ("<<EOF", "EOF"), ("<<-'T'", "T")):
        body = f'python3 - {opener}\n{good}\nP = "/etc/passwd"\n{closer}'
        assert hit(body, "sh"), f"heredoc 开启形态 {opener} 没被识别"
    # 相邻 fence 可能是不同示例/不同进程 —— 不得仅凭同名串联。
    assert not dynamic_tmp_join_lines(fence(good) + "\n" + fence('P = "/etc/passwd"')), (
        "跨 fence 按同名串联了 —— 相邻 fence 可能是不同进程, 这是误报方向"
    )


def test_r22_shell_lexer_and_url_boundary_are_load_bearing():
    r"""⛔ 局部回归断言: r22 的 shell 词法与 URL 地址绑定七处整改各自可被证伪。"""
    d = 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'

    # ① 被转义的字符**永远**是数据(与在不在引号里无关)。
    assert _url_override_hit("printf %s \\ #; unset CLS_BACKEND_URL; " + d), (
        "顶层的转义空格被当成词分隔符 ⇒ 后面的 `#` 被当注释、真实的 `unset` 消失"
    )
    assert not _url_override_hit("printf %s \\ #; :; " + d), "安全对照被误报"

    # ② 命令替换: `$( … )` 内的裸括号要配对; 反引号要自己一层。
    assert _url_override_hit('echo "$( (:) ; printf %s " #")"; unset CLS_BACKEND_URL'), (
        "`$( (:) … )` 里的裸 `)` 把命令替换提前闭掉了"
    )
    assert _url_override_hit("""echo "`printf '%s' " #"`"; unset CLS_BACKEND_URL"""), "反引号命令替换没有自己的层"
    assert not _url_override_hit("""echo "`printf '%s' " #"`"; :"""), "反引号安全对照被误报"

    # ③ URL 地址绑定必须在**剥掉引号后**判 —— 三种写法都能骗过按原串的字符判定。
    for label, line in (
        ("query 里的 `=`", 'curl "http://localhost:80/path?target=${CLS_BACKEND_URL:-http://localhost:8011}/x"'),
        ("相邻引号拼接", 'curl "http://localhost:80/""${CLS_BACKEND_URL:-http://localhost:8011}/x"'),
        ("引号后的 @userinfo", 'curl "${CLS_BACKEND_URL:-http://localhost:8011}"@localhost/x'),
    ):
        assert _url_override_hit(line), f"{label}: 地址不由目标变量决定, 判据却放行"
    assert not _url_override_hit(d), "整改形态本身被误报"
    assert not _url_override_hit("env -u OTHER sh -c '" + d + "'"), "被引号包住的整条脚本要剥到不动点再判"
    assert not _url_override_hit('env -i bash -c "curl \\"${CLS_BACKEND_URL:-http://localhost:8011}/x\\""'), (
        "双引号内的转义引号是**结构**转义(交给内层当定界符), 不是延后展开 —— 不该报"
    )

    # ④ 一处受控不能放行整词(第一处留给子 shell、第二处外层已展开)。
    assert _url_override_hit(
        'env -i bash -c "curl \\${CLS_BACKEND_URL:-http://localhost:8011}/x; '
        'curl ${CLS_BACKEND_URL:-http://localhost:8011}/y"'
    ), "同一个词里有两处 `8011`, 一处受控就整词放行了"

    # ⑤ `printf -v` 必须锚在命令段开头且在 `--` 之前。
    assert not _url_override_hit("printf '%s' x; test -v CLS_BACKEND_URL"), "`test -v` 只是查存在, 不是写变量"
    assert not _url_override_hit("printf -- -v CLS_BACKEND_URL"), "`--` 之后是参数文本, 不是选项"
    assert _url_override_hit("printf -v CLS_BACKEND_URL %s ''; " + d), "真正的 `printf -v` 写变量仍要抓"

    # ⑥ `env` 的参数边界: 选项可以分开写; `-c` 后**只有第一个词**是脚本。
    assert _url_override_hit("env -i bash -l -c '" + d + "'"), "`-l -c` 分开写没被识别"
    assert _url_override_hit("env -i /bin/bash -c '" + d + "'"), "shell 写全路径时没被识别"
    assert not _url_override_hit("""env -i bash -c 'true' "${CLS_BACKEND_URL:-http://localhost:8011}/x\""""), (
        "`-c` 后的**位置参数**被当成脚本内容 ⇒ 误报"
    )

    # ⑦ 身份编码在 str ∪ bytes **整个值域**上单射。
    b = [n for _c, n in escaping_tmp_paths('```python\nP = b"/t" + b"mp/\\xff/x"\n```')]
    r = [n for _c, n in escaping_tmp_paths('```python\nP = "/t" + r"mp/\\xff/x"\n```')]
    assert b and r and b != r, f"真 0xFF 字节与字面反斜杠折成了同一个候选: {b} vs {r}"


def test_r23_reassign_registers_unless_provably_safe():
    r"""⛔ 局部回归断言: 判据的**默认方向** —— 证明不了安全就登记。

    r23 指出前几轮的方向反了: 我一直在试图证明「这处是安全的」, 于是每补一种结构就
    漏一种新结构。Codex 给的口径是「**暂不支持的执行关系应明确触发登记, 不能因源码
    顺序或解析失败静默放行**」。现在只有同时满足「必经 + 非延迟求值 + 无共同循环 +
    源码在后 + 双方都不是 global/nonlocal 搬运」时才沉默。
    """
    good = 'P = "/t" + "mp/cls-exam/x"'
    bad = 'P = "/etc/passwd"'
    hit = lambda body: bool(dynamic_tmp_join_lines(f"```python\n{body}\n```"))  # noqa: E731

    # ① 必经性: 「源码在后 ⇒ 后执行」只有在后写必经时才成立。
    assert hit(f"{bad}\nif False:\n    {good}"), "`if` 里的合规写入未必执行, 却被当成最终值"
    assert not hit(f'{bad}\nif False:\n    Q = "/t" + "mp/cls-exam/x"'), "安全对照被误报"
    assert hit(f'g = ((P := "/etc/passwd") for _ in (1,))\n{good}\nnext(g)'), "生成器求值推迟到 `next()`"

    # ② 但**能**证明安全的仍要沉默 —— 否则形态表的安全对照会被弄红。
    assert not hit(f"{bad}\n{good}"), "直线先坏后好: 合规写入必经且在后 ⇒ 沉默"
    assert not hit('P = "/var/cache"\nP = "/tmp/cls-exam/x"'), "形态表 HIGH-4 的安全对照必须保持绿"
    assert not hit(f"for i in (1,):\n    {bad}\n{good}"), "循环之后的无条件合规写入必然最后执行 ⇒ 沉默"
    assert hit(f"for i in (0, 1):\n    if i:\n        {bad}\n        break\n    {good}"), (
        "共同循环的回边能让越界写入在合规写入之后再跑 ⇒ 登记"
    )

    # ③ `nonlocal` 绑最近的**外层函数**, 不是模块(与 `global` 不同目的地)。
    assert hit(
        f"def outer():\n    {good}\n    def inner():\n        nonlocal P\n        {bad}\n"
        "    inner()\n    return P\nouter()"
    ), "`nonlocal` 被并进模块 ⇒ 与 outer 的合规写入永远配不上对"
    assert not hit(f"def outer():\n    {good}\n    def inner():\n        {bad}\n    inner()\n    return P\nouter()"), (
        "inner 里没有 `nonlocal` 时那是它自己的局部变量 ⇒ 不该报"
    )

    # ④ 默认参数 / 基类 / 装饰器在**外层**作用域求值 —— 不能整个作用域节点截断。
    for label, tail in (
        ("默认参数", 'def f(x=(P := "/etc/passwd")):\n    pass'),
        ("lambda 默认参数", 'g = lambda x=(P := "/etc/passwd"): x'),
        ("class 基类", "class C((P := object)):\n    pass"),
        ("装饰器", "@(P := deco)\ndef f():\n    pass"),
    ):
        assert hit(f"{good}\n{tail}"), f"{label}在定义处求值, 已覆盖外层 `P`, 判据却没看见"
    assert not hit(f'{good}\ndef f(x=(Q := "/etc/passwd")):\n    pass'), "换个名字的安全对照被误报"
    assert not hit(f"{good}\ndef f():\n    {bad}"), "函数**体内**的同名局部仍是另一个绑定"

    # ⑤ `global` 搬运过来的记录: 父链不属于目的地、调用时机也未知 ⇒ 一律证不出。
    assert hit(f"def f():\n    global P\n    {bad}\n{good}\nf()"), "源码靠前的函数体实际最后执行"
    assert not hit(f"def f():\n    {bad}\n{good}\nf()"), "没有 `global` 时那是局部变量 ⇒ 不该报"


def test_r23_python_execution_regions_follow_shell_semantics():
    r"""⛔ 局部回归断言: 执行区提取遵循 heredoc 的定界、重定向与接收命令语义。"""
    good = 'P = "/t" + "mp/cls-exam/x"'
    bad = 'P = "/etc/passwd"'
    hit = lambda body: bool(dynamic_tmp_join_lines(f"```sh\n{body}\n```"))  # noqa: E731

    # ① 一行多个 heredoc: 正文按序跟随, 但 **stdin 只由最后一次重定向决定**。
    assert hit(f"python3 - <<'A' <<'B'\nX = 0\nA\n{good}\n{bad}\nB"), "两个 heredoc 时实际执行的是 B"
    assert not hit(f"python3 - <<'A' <<'B'\nX = 0\nA\n{good}\nQ = \"/etc/passwd\"\nB"), "B 段的安全对照被误报"
    assert not hit(f"python3 - <<'A' <<'B'\n{good}\n{bad}\nA\nX = 0\nB"), "A 段不被读取, 不该当成执行区"

    # ② 定界符可含 `-`; 结束标记按**整行相等**判(不能 strip); `<<-` 逐行剥前导 tab。
    assert hit(f"python3 - <<'PY-END'\n{good}\n{bad}\nPY-END"), "含连字符的定界符没被识别"
    # `PY ` 带尾随空格: `.strip()` 会把它当结束标记而提前闭区, 整行相等则不会。
    # 先 `PY = 0` 让那一行成为合法 Python 表达式语句, 这个区才解析得出来。
    assert hit(f"python3 - <<'PY'\nPY = 0\nPY \n{good}\n{bad}\nPY"), (
        "结束标记按 `.strip()` 判 ⇒ 正文里的 `PY ` 提前闭区, 后面的越界赋值藏到执行区外"
    )
    assert hit(f"python3 - <<-'T'\n\t{good}\n\t{bad}\n\tT"), "`<<-` 的前导 tab 没被剥掉"

    # ③ `python -c '字面脚本'` 也是执行区。
    assert hit(f"python3 -c '{good}; {bad}'"), "`-c` 的字面脚本不是执行区"
    assert not hit(f"python3 -c '{good}; Q = \"/etc/passwd\"'"), "`-c` 的安全对照被误报"

    # ④ 接收命令不读 stdin 时, 那段**不是** Python 执行区(否则是误报)。
    assert not hit(f"cat > /dev/null <<'PY'\n{good}\n{bad}\nPY"), "接收命令是 `cat`, 不该当成执行的 Python"
    assert not hit(f"python3 -c 'pass' <<'A'\n{good}\n{bad}\nA"), "`-c` 时 stdin 不被读取"


def test_r23_url_judge_edges_are_load_bearing():
    r"""⛔ 局部回归断言: r23 四条 shell/URL 边界整改各自可被证伪。

    ⛔ 这四条上一版**只用临时探针验过、没写进断言** —— 回退验证当场照出来: 撤掉整改后
    一条断言都不红。「验过」不等于「钉住」。
    """
    d = 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'

    # ① `printf -v` 的合法前缀 —— `builtin` / `{` / `then` 后面的 printf 一样写变量。
    for prefix in ("builtin ", "{ ", "then ", ""):
        assert _url_override_hit(f'{prefix}printf -v CLS_BACKEND_URL %s ""; {d}'), (
            f"`{prefix}printf -v` 没被识别 —— 段首锚太紧"
        )
    assert not _url_override_hit("printf '%s' x; test -v CLS_BACKEND_URL"), "`test -v` 只是查存在, 仍不该报"

    # ② `env -u "VAR"` 的**闭引号**要消费; `-cl` 与 `-lc` 都要认(`c` 不一定在选项串末尾)。
    assert _url_override_hit(f"""env -u "CLS_BACKEND_URL" bash -c '{d}'"""), "`-u` 后整体引用的变量名没被消费"
    assert _url_override_hit(f"env -i bash -cl '{d}'"), "`-cl` 顺序没被识别"
    assert not _url_override_hit(f"""env -u OTHER sh -c '{d}'"""), "删的不是目标变量 ⇒ 仍不该报"

    # ③ userinfo 要看整个 authority 段, 不只紧邻展开的那一个字符。
    assert _url_override_hit('curl "${CLS_BACKEND_URL:-http://localhost:8011}":pw@localhost/x'), (
        "紧邻展开的是 `:`, 但 `@` 之后才是真实主机"
    )
    assert _url_override_hit("curl ${CLS_BACKEND_URL:-http://localhost:8011}\\@localhost/x"), "未引用的 `@` 同根"
    assert not _url_override_hit(d), "整改形态本身被误报"

    # ④ 展开层里**双引号内**的字面 `(` 不该压进结构栈。
    assert not _url_override_hit('echo "$(printf %s "(")"; # unset CLS_BACKEND_URL'), (
        "双引号内的字面 `(` 压栈后, 后面真正的注释识别整体错位 ⇒ 误报"
    )
    assert _url_override_hit('echo "$( (:) ; printf %s " #")"; unset CLS_BACKEND_URL'), (
        "`$( (:) … )` 里**未被引用**的裸括号仍要配对"
    )


def test_r24_silence_requires_real_reachability():
    r"""⛔ 局部回归断言: 「必经」不是「祖先不在黑名单里」, 绑定归属也要找对。

    r24 确认**默认方向正确**, 但沉默条件不够严: 祖先黑名单证明不了必经。
    """
    good = 'P = "/t" + "mp/cls-exam/x"'
    bad = 'P = "/etc/passwd"'
    hit = lambda b: bool(dynamic_tmp_join_lines(f"```python\n{b}\n```"))  # noqa: E731

    # ① `with suppress(...)` 吞掉异常后 body 后半段整段不执行; `except*` 同理。
    assert hit(f"from contextlib import suppress\n{bad}\nwith suppress(E):\n    1 / 0\n    {good}"), (
        "`with suppress(...)` 里的合规写入未必执行"
    )
    assert not hit(
        f'from contextlib import suppress\n{bad}\nwith suppress(E):\n    1 / 0\n    Q = "/tmp/cls-exam/x"'
    ), "安全对照被误报"
    # `except*` 分支本身由 `ExceptHandler` 覆盖; 只有 **`try` 体**里的写入才考得出
    # `TryStar` 有没有进名单 —— 它的祖先是 `TryStar` 而不是 `Try`。
    assert hit(f"{bad}\ntry:\n    {good}\nexcept* E:\n    pass"), "`TryStar` 不在条件节点名单里"

    # ② 同一块里 `return`/`raise`/`break` 在它之前 ⇒ 后面的合规写入到不了。
    assert hit(f"def f():\n    {bad}\n    return P\n    {good}"), "`return` 之后的合规赋值根本执行不到"

    # ③ `nonlocal` 找的是**最近一个实际绑定该名字**的外层函数(含形参), 不是最近的函数。
    assert hit(
        f"def outer():\n    {good}\n    def middle():\n        def inner():\n"
        f"            nonlocal P\n            {bad}\n        inner()\n    middle()\n    return P"
    ), "`nonlocal` 被搬到没有绑定 `P` 的中间层 ⇒ 与 outer 的合规写入配不上对"
    # 中间层**既绑定 `P` 又声明 `nonlocal P`**: `inner` 的记录先落到 `middle`(它确实绑了 P),
    # 而 `middle` 早在前序遍历里处理完了 —— 不迭代到不动点, 那条记录就停在 middle,
    # 与 `outer` 的合规写入永远配不上对。
    # ⚠️ 中间层那次写入必须也是**合规**的(`/tmp/cls-exam/y`): 写成越界值的话, 它自己
    # 迁到 outer 就足以让 outer 报红, 这条断言就考不出「不动点」了(第一版实测踩到)。
    assert hit(
        f"def outer():\n    {good}\n    def middle():\n        nonlocal P\n"
        f'        P = "/tmp/cls-exam/y"\n        def inner():\n'
        f"            nonlocal P\n            {bad}\n        inner()\n    middle()\n    return P"
    ), "搬进**已处理过**的作用域后没有继续归并 ⇒ 迭代不到不动点"

    # 绑定查找必须含**形参**: `middle(P)` 用形参绑了自己的 `P`, `inner` 的 `nonlocal`
    # 应该落到 middle 而不是 outer —— 不看形参就会越过 middle、误报 outer 的合规值被改。
    assert not hit(
        f"def outer():\n    {good}\n    def middle(P):\n        def inner():\n"
        f"            nonlocal P\n            {bad}\n        inner()\n    middle(P)\n    return P"
    ), "`nonlocal` 越过了用**形参**绑定 `P` 的中间层 ⇒ 误报 outer 的合规值被改"
    assert not hit(
        f"def outer():\n    {good}\n    def middle():\n        def inner():\n            {bad}\n        inner()\n    middle()\n    return P"
    ), "inner 里没有 `nonlocal` 时那是它自己的局部变量"

    # ④ 绕过名字绑定直接改命名空间的写法 —— 静态判不出改的是谁 ⇒ 登记。
    for label, tail in (
        ("globals()[…]=", 'globals()["P"] = "/etc/passwd"'),
        ("globals().update", 'globals().update(P="/etc/passwd")'),
        ("exec", "exec('P = \"/etc/passwd\"')"),
    ):
        assert hit(f"{good}\n{tail}"), f"{label} 会真的覆盖, 判据却静默"
    assert not hit(f'{good}\nx = globals().get("P", "null")'), (
        "`globals().get(...)` 是**读** —— 一律当写会打破三条负控的前提(树上 quiz-answer 就是这个写法)"
    )
    assert hit(f"{good}\ntype P = int"), "`type P = int` 也重绑 `P`"

    # ⑤ 定义处表达式只归**外层**一次 —— 两边都收会被内层的 `global` 声明再搬走。
    assert not hit(
        f'{good}\ndef outer():\n    def f(x=(P := "/etc/passwd")):\n        global P\n        pass\nouter()'
    ), "默认参数写的是 `outer` 的局部 `P`, 模块 `P` 始终合规 ⇒ 误报"
    assert hit(f'{good}\ndef f(x=(P := "/etc/passwd")):\n    pass'), "真正覆盖模块 `P` 的默认参数仍要抓"


def test_r24_heredoc_attribution_follows_redirection_order():
    r"""⛔ 局部回归断言: heredoc 按**命令、fd 与重定向顺序**归属。"""
    good = 'P = "/t" + "mp/cls-exam/x"'
    bad = 'P = "/etc/passwd"'
    hit = lambda b: bool(dynamic_tmp_join_lines(f"```sh\n{b}\n```"))  # noqa: E731

    # ① fd 复制: 实际读的是 A, 不是整行最后一个 heredoc。
    assert hit(f"python3 - 3<<'A' <<'B' <&3\n{good}\n{bad}\nA\nX=0\nB"), "`<&3` 把 stdin 指回 A, 提取器却取了 B"
    assert not hit(f"python3 - 3<<'A' <<'B' <&3\n{good}\nQ = \"/etc/passwd\"\nA\nX=0\nB"), "安全对照被误报"
    assert hit(f"python3 - <<'A' 3<<'B'\n{good}\n{bad}\nA\nX=0\nB"), "`3<<` 落在 fd 3, stdin 仍是 A"

    # ② 管道两侧是两条命令, heredoc 各归各的。
    assert hit(f"python3 - <<'A' | cat <<'B'\n{good}\n{bad}\nA\nX=0\nB"), "A 归 python"
    assert not hit(f"python3 - <<'A' | cat <<'B'\nX=0\nA\n{good}\n{bad}\nB"), "B 归 cat, 不该当成执行的 Python"

    # ③ 后续的 `</dev/null` 覆盖 stdin ⇒ A 不被读取。
    assert not hit(f"python3 - <<'A' </dev/null\n{good}\n{bad}\nA"), "stdin 被重定向到 /dev/null, A 不执行"

    # ④ 解释器参数: `-W` 吃掉下一个词; 可执行词要去引号; 每条命令都要看; `-c'…'` 连写。
    assert hit(f"python3 -W ignore <<'A'\n{good}\n{bad}\nA"), "`ignore` 被误认成脚本文件名"
    assert hit(f"'python3' - <<'A'\n{good}\n{bad}\nA"), "带引号的可执行词没被归一化"
    assert hit(f"python3 -c 'pass'; python3 -c '{good}; {bad}'"), "只看了第一条 python 命令"
    assert hit(f"python3 -c'{good}; {bad}'"), "`-c` 与脚本连写没被识别"

    # ⑤ 注释里/引号里的假 heredoc 标记不能吞掉后面真正的执行区。
    assert hit(f"# <<'NO'\npython3 - <<'A'\n{good}\n{bad}\nA"), "注释里的 `<<'NO'` 被当成真重定向"
    assert hit(f"echo '<<NO'\npython3 - <<'A'\n{good}\n{bad}\nA"), "引号里的 `<<NO` 被当成真重定向"

    # ⑥ 「整块能被 `ast` 解析」不等于「整块是一个执行区」。
    assert not hit(f"cat <<'A'\n{good}\n{bad}\nA"), "`cat <<'A'` 恰好能解析成左移表达式 ⇒ 整块误报"
    assert not hit(f"python3 <<'A'\n{good}\nA\npython3 <<'B'\n{bad}\nB"), "两个独立进程被整块 AST 合并"

    # ⑦ `&` 在 `<&` / `>&` / `&>` 里不是命令分隔符。
    assert not _url_override_hit('curl "${CLS_BACKEND_URL:-http://localhost:8011}/x" 2>&1'), (
        "`2>&1` 的 `&` 被当成命令分隔符 ⇒ 切段错位"
    )
    assert not _url_override_hit('true && curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'), "`&&` 仍是分隔符"


def test_r25_regressions_from_r24_are_fixed():
    r"""⛔ 局部回归断言: r24 我自己引入的四条回归。

    这四条是 Codex r25 用**逐 commit 对照**找出来的(「`e22c6d27` 能抓、`cb4fa9f8` 漏掉」)。
    我在 r25 prompt 里主动把这个方向指给它 —— 上一轮它就是这样抓到我两条回归的。
    """
    good = 'P = "/t" + "mp/cls-exam/x"'
    bad = 'P = "/etc/passwd"'
    hit = lambda b, info="python": bool(dynamic_tmp_join_lines(f"```{info}\n{b}\n```"))  # noqa: E731

    # ① 重定向扫描要看引号掩码: `'<not-a-file'` 是普通 argv, 不是重定向。
    assert hit(f"python3 - <<'A' '<not-a-file'\n{good}\n{bad}\nA", "sh"), (
        "被引号包住的 `<…` 被当成 `<file` 覆盖了 fd 0, 真正的执行区整个消失"
    )
    assert not hit(f"python3 - <<'A' '<not-a-file'\n{good}\nQ = \"/etc/passwd\"\nA", "sh"), "安全对照被误报"

    # ② `c` 不一定在短选项串开头 —— `-Bc '脚本'` 是合法组合。
    assert hit(f"python3 -Bc '{good}; {bad}'", "sh"), "`-Bc` 的脚本内容被当成文件名"

    # ③ 左移运算不是 heredoc: 必须**验结束标记确实存在**。
    assert hit(f"{good}\nN = 1 << 2\n{bad}"), (
        "`N = 1 << 2` 被当成 heredoc 开启 ⇒ 整块执行区被取消, 三条独立语句又建立不起单元内关系"
    )
    assert not hit(f'{good}\nN = 1 << 2\nQ = "/etc/passwd"'), "安全对照被误报"

    # ④ 相邻的 `<`/`>` 必须是**未被转义**的, 否则 `&` 仍是分隔符。
    assert _url_override_hit(
        'true \\>& printf -v CLS_BACKEND_URL %s ""; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'
    ), "`\\>` 是普通参数, 后面的 `&` 应当分隔命令 —— 只看字符不看掩码会把 `printf` 拼进前段"
    assert not _url_override_hit('curl "${CLS_BACKEND_URL:-http://localhost:8011}/x" 2>&1'), "真正的 `2>&1` 仍不该切段"


def test_r25_early_exit_and_reflective_writes_are_load_bearing():
    r"""⛔ 局部回归断言: 裸提前离开语句与反射式命名空间写入。"""
    good = 'P = "/t" + "mp/cls-exam/x"'
    bad = 'P = "/etc/passwd"'
    hit = lambda b: bool(dynamic_tmp_join_lines(f"```python\n{b}\n```"))  # noqa: E731

    # ① 裸 `return` / `raise` / `break` **没有子节点**, 永远不出现在父表的**值**里。
    #    原用例写的是 `return P`, 恰好因为有 `Name` 子节点才被发现 —— 纯属巧合。
    for label, stmt in (("return", "return"), ("raise", "raise"), ("break", "break")):
        body = (
            f"def f():\n    for i in (1,):\n        {bad}\n        {stmt}\n        {good}"
            if stmt == "break"
            else f"def f():\n    {bad}\n    {stmt}\n    {good}"
        )
        assert hit(body), f"裸 `{label}` 之后的合规赋值到不了, 判据却当成最终值"
    assert not hit(f"def f():\n    {bad}\n    {good}"), "没有提前离开时, 直线先坏后好仍应沉默"

    # ② 反射式写入: 名单要覆盖**直接可见**的机制, 且写入目标要整棵走一遍。
    for label, tail in (
        ("元组解包目标", '(globals()["P"],) = ("/etc/passwd",)'),
        ("`for` 目标", 'for globals()["P"] in ["/etc/passwd"]:\n    pass'),
        ("dict.update(globals())", 'dict.update(globals(), P="/etc/passwd")'),
        ("setattr(sys.modules)", 'import sys\nsetattr(sys.modules[__name__], "P", "/etc/passwd")'),
        ("__dict__ 直取", 'import sys\nsys.modules[__name__].__dict__["P"] = "/etc/passwd"'),
        ("importlib.reload", "import importlib, sys\nimportlib.reload(sys.modules[__name__])"),
        ("from x import *", "from os.path import *"),
    ):
        assert hit(f"{good}\n{tail}"), f"{label} 会改模块命名空间, 判据却静默"
    assert not hit(f'{good}\nx = globals().get("P", "null")'), (
        "`globals().get(...)` 是**读** —— 一律当写会打破三条负控的前提"
    )

    # ③ 只有注解 / `del` 也让名字成为该作用域的局部绑定, `nonlocal` 不该越过。
    for label, mid in (("仅注解", "P: str"), ("del", "del P")):
        assert not hit(
            f"def outer():\n    {good}\n    def middle():\n        {mid}\n        def inner():\n"
            f"            nonlocal P\n            {bad}\n        inner()\n    middle()\n    return P"
        ), f"`nonlocal` 越过了用**{label}**绑定 `P` 的中间层 ⇒ 误报 outer 的合规值被改"
    assert hit(
        f"def outer():\n    {good}\n    def middle():\n        def inner():\n"
        f"            nonlocal P\n            {bad}\n        inner()\n    middle()\n    return P"
    ), "中间层确实不绑定 `P` 时仍要抓"

    # ④ 引号拼出来的变量名只是词法问题, 不是数据流问题。
    d = 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'
    assert _url_override_hit(f"unset C'LS'_BACKEND_URL; {d}"), "变量名被引号拆开就认不出了"
    assert not _url_override_hit(f"unset OTHER; {d}"), "删的不是目标变量 ⇒ 不该报"
    assert not _url_override_hit(f"unset -f CLS_BACKEND_URL; {d}"), "`unset -f` 删的是同名**函数**"


def test_r26_heredoc_discriminator_and_option_scan():
    r"""⛔ 局部回归断言: heredoc 判别用**引号**、短选项**按序**扫。

    r26 指出我 r25 的修法方向不对 ——「结束标记存在」既证明不了是 heredoc
    （正文里恰好有一行 `2` 就把 `N = 1 << 2` 认成 heredoc），
    也不该用来否定 heredoc（**真** heredoc 缺尾是示例里的常见写法）。
    """
    good = 'P = "/t" + "mp/cls-exam/x"'
    bad = 'P = "/etc/passwd"'
    sh = lambda b: bool(dynamic_tmp_join_lines(f"```sh\n{b}\n```"))  # noqa: E731
    py = lambda b: bool(dynamic_tmp_join_lines(f"```python\n{b}\n```"))  # noqa: E731

    # ① 带引号的定界符无歧义 —— 缺结束标记也照认, 正文取到块尾。
    assert sh(f"python3 - <<'END'\n{good}\n{bad}"), "真 heredoc 缺结束标记就被整个丢掉了"
    assert not sh(f"python3 - <<'END'\n{good}\nQ = \"/etc/passwd\""), "安全对照被误报"
    # ② 不带引号的才看这一行能不能当 Python 解析。
    assert py(f"{good}\nN = 1 << 2\n{bad}"), "`N = 1 << 2` 是左移运算, 不是 heredoc"
    assert py(f"{good}\nN = 1 << 2\n2\n{bad}"), "正文里恰好有一行 `2` 不该让左移变成 heredoc"
    assert sh(f"python3 - <<END\n{good}\n{bad}\nEND"), "不带引号的**真** heredoc 仍要认"
    assert not sh(f"cat <<'A'\n{good}\n{bad}\nA"), "`cat` 不是 python, 那段不是执行区"

    # ③ 短选项按序扫: 消费参数的选项之后, 余下字符是它的**参数**, 不再当选项。
    for label, opt in (("-W 的参数", "-Wignore::DeprecationWarning"), ("-X 的参数", "-Xpycache_prefix=/cache")):
        assert sh(f"python3 {opt} - <<'END'\n{good}\n{bad}\nEND"), f"{label}里的 `c` 被当成 `-c`, 真执行区被取消"
    assert sh(f"python3 -Bc '{good}; {bad}'"), "`-Bc` 的组合仍要认"
    assert sh(f"python3 -W ignore <<'A'\n{good}\n{bad}\nA"), "`-W ignore` 分开写仍要认"


def test_r26_reflective_detection_is_narrow_enough():
    r"""⛔ 局部回归断言: 反射式写入既要覆盖真形态, 也**不能**误伤普通业务代码。

    r26 给了五个普通写法的反例, 它们在 r25 版本上全部报红。这条把两个方向一起钉住。
    """
    good = 'P = "/t" + "mp/cls-exam/x"'
    py = lambda b: bool(dynamic_tmp_join_lines(f"```python\n{b}\n```"))  # noqa: E731

    # ① 真形态要抓。
    for label, tail in (
        ("`sys.modules[…].P =`（目标是 Attribute）", 'import sys\nsys.modules[__name__].P = "/etc/passwd"'),
        ("`globals().__ior__`", 'globals().__ior__({"P": "/etc/passwd"})'),
        ("`del globals()[…]`", 'del globals()["P"]'),
        ("`importlib.reload`", "import importlib, sys\nimportlib.reload(sys.modules[__name__])"),
        ("未绑定的 `dict.update(globals(), …)`", 'dict.update(globals(), P="/etc/passwd")'),
        ("`globals()[…] =`", 'globals()["P"] = "/etc/passwd"'),
        ("`sys.modules[…].__dict__[…]`", 'import sys\nsys.modules[__name__].__dict__["P"] = "/etc/passwd"'),
    ):
        assert py(f"{good}\n{tail}"), f"{label} 会改模块命名空间, 判据却静默"

    # ② 普通业务代码**不能**误伤。
    for label, tail in (
        ("任意 `.reload()`", "page.reload()"),
        ("读模块字典写进别处", "config = {}\nconfig.update(globals())"),
        ("`vars(x)` 带参数是对象字典", "config.update(vars(args))"),
        ("实例 `__dict__`", 'args.__dict__["verbose"] = True'),
        ("下标**键**里的 globals()（Load 上下文）", 'cache[globals()["P"]] = 1'),
        ("业务属性 `.modules[…]`", 'app.modules["x"].y = 1'),
        ("`globals().get(...)` 是读", 'x = globals().get("P", "null")'),
        ("`vars(x)[…] =` 写的是对象字典", 'vars(args)["P"] = "/etc/passwd"'),
    ):
        assert not py(f"{good}\n{tail}"), f"{label} 不改模块命名空间, 却被报红"

    # ④ `(P): str` 的 `AnnAssign.simple == 0` —— 它**不**产生局部绑定(树内 `symtable` 实证),
    #    所以 `nonlocal` 不该停在这一层。这条上一版只用临时探针验过、没写进断言。
    bad = 'P = "/etc/passwd"'
    assert py(
        f"def outer():\n    {good}\n    def middle():\n        (P): str\n        def inner():\n"
        f"            nonlocal P\n            {bad}\n        inner()\n    middle()\n    return P"
    ), "`(P): str` 被误收成局部绑定 ⇒ `nonlocal` 停错层, outer 的合规值被改却静默"
    assert not py(
        f"def outer():\n    {good}\n    def middle():\n        P: str\n        def inner():\n"
        f"            nonlocal P\n            {bad}\n        inner()\n    middle()\n    return P"
    ), "**不带**括号的 `P: str` 确实产生绑定 ⇒ 不该报"

    # ③ `unset` 必须是**命令词**, 选项词也要一起去引号。
    d = 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'
    assert not _url_override_hit(f"printf '%s %s' unset C'LS'_BACKEND_URL; {d}"), (
        "`unset` 只是 `printf` 的参数, 没有删除任何变量"
    )
    assert not _url_override_hit(f"unset '-f' C'LS'_BACKEND_URL; {d}"), "选项词没去引号 ⇒ `-f` 认不出来"
    assert _url_override_hit(f"unset C'LS'_BACKEND_URL; {d}"), "真正的 `unset` 仍要抓"
    assert _url_override_hit(f"VAR=1 unset CLS_BACKEND_URL; {d}"), "赋值前缀之后的 `unset` 仍是命令词"


def test_r27_heredoc_uses_fence_info_as_primary_signal():
    r"""⛔ 局部回归断言: heredoc 判别的**主信号是 fence 的 info string**。

    前两轮我先后用过「结束标记存在」(r25) 和「引号」(r26), **两个都被证伪**：
      · 带引号的 `(( 1 << "2" ))` 是**算术**, 不是 heredoc;
      · 不带引号的 `python3 -B <<EOF` 恰好能当 Python 的减法/左移解析。
    而 fence 早就写明了这块是什么语言 —— 那才是最直接的证据, 前几轮一直没用上。
    """
    good = 'P = "/t" + "mp/cls-exam/x"'
    bad = 'P = "/etc/passwd"'
    hit = lambda b, info: bool(dynamic_tmp_join_lines(f"```{info}\n{b}\n```"))  # noqa: E731

    assert hit(f"(( 1 << \"2\" ))\npython3 - <<'END'\n{good}\n{bad}\nEND", "sh"), (
        '带引号的算术 `(( 1 << "2" ))` 被当成 heredoc, 吞掉了后面真正的执行区'
    )
    assert hit(f"python3 -B <<EOF\n{good}\n{bad}\nEOF\necho done", "sh"), (
        "`python3 -B <<EOF` 恰好能当 Python 解析 ⇒ 真 heredoc 被跳过"
    )
    assert hit(f"{good}\nN = 1 << 2\n{bad}", "python"), "python fence 里的 `<<` 一定是左移"
    assert hit(f"{good}\nN = 1 << 2\n{bad}", ""), "没有 info 时回落到「这一行能不能当 Python 解析」"
    assert not hit(f"cat <<'A'\n{good}\n{bad}\nA", "sh"), "`cat` 不是 python, 那段不是执行区"
    assert hit(f"python3 - <<'END'\n{good}\n{bad}", "sh"), "缺结束标记时正文取到块尾, 不该整个丢掉"


def test_r27_namespace_aliases_and_binding_facts():
    r"""⛔ 局部回归断言: 命名空间**别名**、解包、删除、生成器暂停。"""
    good = 'P = "/t" + "mp/cls-exam/x"'
    bad = 'P = "/etc/passwd"'
    py = lambda b: bool(dynamic_tmp_join_lines(f"```python\n{b}\n```"))  # noqa: E731

    # ① 别名是**直接可见**的, 不需要跨过程分析。
    for label, tail in (
        ("`vars(模块)` 就是模块字典", 'import sys\nvars(sys.modules[__name__])["P"] = "/etc/passwd"'),
        ("`import sys as s`", 'import sys as s\ns.modules[__name__].__dict__["P"] = "/etc/passwd"'),
        ("`m = globals()`", 'm = globals()\nm["P"] = "/etc/passwd"'),
        ("`import importlib as imp`", "import importlib as imp, sys\nimp.reload(sys.modules[__name__])"),
    ):
        assert py(f"{good}\n{tail}"), f"{label} —— 别名没被识别"
    assert not py(f'{good}\nvars(args)["P"] = "/etc/passwd"'), "`vars(普通对象)` 是对象字典, 仍不该报"

    # ② 解包时目标只拿到右值的**一部分** —— `P, *_ = "/t"+"mp/cls-exam/x"` 之后 P 是 `"/"`。
    assert py(f'{bad}\nP, *_ = "/t" + "mp/cls-exam/x"'), "解包赋值被当成「P 拿到了整条合规路径」"
    assert not py(f"{bad}\n{good}"), "普通赋值仍能证明安全"

    # ③ `del P` 销毁绑定后, 读到的是**外层**的值。
    assert py(f"{bad}\nclass C:\n    {good}\n    del P\n    result = P"), "`del P` 没被计为一次写入"

    # ④ `yield` 会**暂停** —— `next(f())` 拿到的是 yield 之前那个坏值。
    assert py(f"def f():\n    {bad}\n    yield P\n    {good}\nresult = next(f())"), (
        "生成器在 `yield` 处暂停, 后面的合规赋值还没跑"
    )
    assert not py(f"def f():\n    {bad}\n    {good}"), "普通函数(无 yield)仍能证明安全"

    # ⑤ `unset` 的命令前缀; 后备正则删除后普通拼写的误报也消了。
    d = 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'
    for prefix in ("command ", "builtin ", "! ", ""):
        assert _url_override_hit(f"{prefix}unset CLS_BACKEND_URL; {d}"), f"`{prefix}unset` 没被识别"
    for probe in ("printf '%s %s' unset CLS_BACKEND_URL", "printf '%s %s' unset C'LS'_BACKEND_URL"):
        assert not _url_override_hit(f"{probe}; {d}"), f"`{probe}` 只是打印, 不该报"
    assert not _url_override_hit(f"unset -f CLS_BACKEND_URL; {d}"), "`unset -f` 删的是函数"


def test_managed_files_match_digest_baseline():
    r"""⛔ 第十一条(正控): 受管 16 份文件的**整文件字节摘要**与集合精确相等。

    这是本卡的**结构性收口**(Codex r28)。前十条判据都在回答「这条路径指向哪」——
    那需要在手写代码里复现三层语义, 八轮数据显示它不收敛。这一条不问内容,
    只保证**任何字节变化都留下可审查的痕迹**。

    ⚠️ 它与前十条的关系是**兜底而非取代**: 前十条给出「是哪一类问题」的诊断,
    这一条保证「不管什么形态, 文件变了就红」。⚠️ 反过来说, 它**绿**只意味着
    「这些文件一个字节都没动」, **不**证明任何路径构造安全。
    """
    problems = check_managed_files(DEFAULT_ROOT, MANAGED_FILE_DIGESTS)
    assert not problems, "受管文件基线漂移:\n" + "\n".join(problems)


def test_managed_file_gate_catches_what_semantic_judges_miss():
    r"""⛔ 负控: 第十一条要能接住**前十条全部静默**的那一类。

    r28 给的反例 —— 拆分常量根本进不了第⑩条的输入过滤器(它用**连续 `/tmp`** 筛):

        ROOT = "/t"
        P = ROOT + "mp/cls-exam/../x"

    这条断言先**证明前十条确实看不见它**(否则这个负控考错了对象), 再证明
    第十一条的摘要会变。
    """
    escaping = 'ROOT = "/t"\nP = ROOT + "mp/cls-exam/../x"'
    block = f"```python\n{escaping}\n```"
    silent = {
        "越界候选": escaping_tmp_paths(block),
        "可疑行": suspicious_tmp_lines(block),
        "动态拼接": dynamic_tmp_join_lines(block),
        "父目录散文": parent_dir_prose_lines(block),
        "opaque": opaque_tmp_lines(block),
        "URL 覆盖": url_default_overridden_lines(block),
        "块指纹": tmp_block_fingerprints(block),
    }
    assert not any(silent.values()), (
        "前提不成立: 前十条判据里有人看得见这个形态, 这条负控就考错了对象 —— "
        f"实测 { ({k: v for k, v in silent.items() if v}) }"
    )
    # ⛔ r29 MEDIUM-2: **计数前提**也要断言 —— 否则「前十条静默」可能只是因为层 2 的
    # 九项计数先把它抓走了, 那这条负控同样考错了对象。
    counts = _body_counts(escaping)
    assert not any(counts.values()), f"前提不成立: 层 2 的九项计数看得见这个形态 —— {counts}"
    # 第十一条只看字节: 同一份文件改掉任意一个字节, 摘要必变。
    original = (DEFAULT_ROOT / "skills" / "start-exam-board" / "SKILL.md").read_bytes()
    mutated = original + b"\n" + escaping.encode()
    assert hashlib.sha256(original).hexdigest()[:16] != hashlib.sha256(mutated).hexdigest()[:16], (
        "整文件摘要对追加内容不敏感 —— 那它兜不住任何东西"
    )


def _tiny_managed_tree(base: Path) -> tuple[Path, dict[str, str]]:
    """搭一棵**最小受管样本树**并返回它的基线。

    ⛔ r29 MEDIUM-2: 负控必须让四种情形**真正走一遍正式门禁**
    (`managed_file_digests()` / `check_managed_files()`) —— 上一版只比了两次
    `hashlib.sha256`, 正式检查退化成 `return []` 它照样绿。
    ⚠️ 只在 tmp 副本里搭, 绝不碰真实 vault(卡文硬边界: 负控只在 tmp 副本)。
    """
    root = base / ".claude"
    (root / "skills" / "demo").mkdir(parents=True)
    (root / "skills" / "demo" / "SKILL.md").write_bytes(b"---\nname: demo\n---\nbody\n")
    (root / "skills" / "demo" / "scripts").mkdir()
    (root / "skills" / "demo" / "scripts" / "run.py").write_bytes(b"X = 1\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "top.py").write_bytes(b"Y = 2\n")
    return root, managed_file_digests(root)


def test_managed_file_gate_is_load_bearing(tmp_path):
    r"""⛔ 正式门禁负控: 未改必绿; 新增/删除/改一个字节必红 —— 都走 `check_managed_files()`。

    ⛔ r29 MEDIUM-2 指出上一版负控的问题: 它只比两次 `sha256`, **没有调用正式门禁**,
    所以 `check_managed_files()` 若退化成 `return []`, 那两条测试仍然全过。
    """
    root, baseline = _tiny_managed_tree(tmp_path)
    assert len(baseline) == 3, f"样本树应有 3 份受管文件: {sorted(baseline)}"
    assert not check_managed_files(root, baseline), "未改快照必须绿"

    # ① 改一个字节
    target = root / "skills" / "demo" / "SKILL.md"
    original = target.read_bytes()
    target.write_bytes(original.replace(b"body", b"bodX"))
    problems = check_managed_files(root, baseline)
    assert any("内容变化" in p and "skills/demo/SKILL.md" in p for p in problems), f"改一个字节没有红: {problems}"
    target.write_bytes(original)
    assert not check_managed_files(root, baseline), "还原后应重新变绿"

    # ② 只改**行尾**(LF → CRLF): 字节变了就要红, 不做任何归一化
    target.write_bytes(original.replace(b"\n", b"\r\n"))
    assert check_managed_files(root, baseline), "只改行尾风格也必须红(摘要不做字节归一化)"
    target.write_bytes(original)

    # ③ 新增受管文件
    (root / "scripts" / "extra.py").write_bytes(b"Z = 3\n")
    problems = check_managed_files(root, baseline)
    assert any("新增" in p and "scripts/extra.py" in p for p in problems), f"新增受管文件没有红: {problems}"
    (root / "scripts" / "extra.py").unlink()

    # ④ 删除受管文件
    (root / "scripts" / "top.py").unlink()
    problems = check_managed_files(root, baseline)
    assert any("缺失" in p and "scripts/top.py" in p for p in problems), f"删除受管文件没有红: {problems}"


def test_managed_file_gate_rejects_symlinks_and_case_drift(tmp_path):
    r"""⛔ r29 MEDIUM-1: 符号链接与大小写改名不得静默。

    · 普通文件换成指向**相同内容**的符号链接 —— 摘要一模一样, 只有实际路径类型变了;
    · **目录分量**的符号链接能把读取引到受管根之外;
    · 大小写不敏感的文件系统上 `SKILL.md → skill.md`, 字面 glob 仍找得到, 键名却硬编码。
    """
    root, baseline = _tiny_managed_tree(tmp_path)
    # ⓪ **受管根本身**换成指向同内容目录的符号链接 —— 路径键与摘要一个都不变。
    moved_root = tmp_path / "claude-real"
    root.rename(moved_root)
    root.symlink_to(moved_root, target_is_directory=True)
    assert managed_file_digests(root) == baseline, (
        "前提: 沿根链接读出来的键与摘要**本来就应该一模一样** —— 否则这条负控考错了对象"
    )
    assert check_managed_files(root, baseline), "受管**根本身**是符号链接必须红"
    root.unlink()
    moved_root.rename(root)
    assert not check_managed_files(root, baseline), "还原根目录后应重新变绿"

    # ① 文件本身换成符号链接(内容一致)
    target = root / "scripts" / "top.py"
    payload = tmp_path / "elsewhere.py"
    payload.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(payload)
    assert check_managed_files(root, baseline), "受管文件换成符号链接(内容相同)必须红"
    target.unlink()
    target.write_bytes(payload.read_bytes())
    assert not check_managed_files(root, baseline), "换回普通文件后应重新变绿"

    # ② **目录分量**是符号链接
    real = root / "skills" / "demo"
    moved = tmp_path / "demo-real"
    real.rename(moved)
    real.symlink_to(moved, target_is_directory=True)
    assert check_managed_files(root, baseline), "受管路径的目录分量是符号链接必须红"
    real.unlink()
    moved.rename(real)
    assert not check_managed_files(root, baseline), "还原目录后应重新变绿"

    # ③ 大小写改名 —— 在大小写不敏感的文件系统上 `glob` 仍能找到, 但目录项名字变了。
    skill = root / "skills" / "demo" / "SKILL.md"
    skill.rename(root / "skills" / "demo" / "skill.md")
    assert check_managed_files(root, baseline), "受管文件大小写改名必须红(逐级按真实目录项核对)"


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

    ⛔ r20 LOW-3: 量的对象从 `_parse_units()` 换成**整条 `dynamic_tmp_join_lines()`** ——
    r19 给动态判据加的「整段源码预筛」每个单元多一次 `ast.parse` + 折叠遍历, 而上一版
    哨兵根本不调这条路径, 新增成本它一点都看不见。Codex 合成语料实测: 1000 个普通赋值
    单元 0.264ms → 9.420ms。数量级仍在, 但哨兵得能看见它。
    r21 LOW 指出「真实树耗时未验证」——**本轮实测**(9 份 SKILL.md, 动态判据全路径):
    冷缓存 **317ms** / 暖缓存 **46ms**(其中 `_parse_units()` 2.8ms), 阈值 10s 余量 >30x。
    `_py_strings` 缓存实测 hits=3281 / misses=1913, 命中率 63% —— 「每单元多一次 parse」
    这个说法只在冷缓存下成立。
    """
    _parse_units_cached.cache_clear()  # r12 LOW-1: 不清缓存的话前面的检查已预热, 量的是暖路径
    _py_strings_cached.cache_clear()
    start = time.perf_counter()
    longest, where = 0, ""
    for name in sorted(EXPECTED_SKILLS):
        text = (DEFAULT_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        dynamic_tmp_join_lines(text)  # 走完 预筛 + `_has_dynamic_tmp_join()` 的真实路径
        for _start, body, is_fence in _fence_blocks(text):
            if not is_fence:
                continue
            for _off, chunk, _parsed in _parse_units(body):
                n = len(chunk.splitlines())
                if n > longest:
                    longest, where = n, name
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0, (
        f"9 份 SKILL.md 跑一遍 动态判据全路径 用了 {elapsed:.1f}s(最长单元 {longest} 行, "
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
