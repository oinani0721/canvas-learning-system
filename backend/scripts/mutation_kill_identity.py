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

* `syntax_check()` —— 施加变异后、跑门**之前**先编译。不通过 ⇒ 第三种裁决
  `SYNTAX-INVALID`：既不算 KILLED 也不算 SURVIVED，因为它照出的是**负控自己
  坏了**，不是被测物坏了。
* `kill_identity_ok()` —— 击杀必须落在**声称的那一条断言**上。

## 判据面为什么取 `-rf` 短摘要，而不是整份 stdout / `E ` 行

* 整份 stdout：pytest 的 long traceback 会把**整个测试函数的源码**打出来，于是
  该函数里每一条断言的消息串都出现在输出里 —— `expect_msg in out` 等于恒真，
  「判据被自己要找的东西喂饱」。
* `E ` 行：pytest 会给多行断言消息的**每一行**都加 `E ` 前缀。一条内嵌了子进程
  输出(`{out}` / `{err}`)的**前提断言**一旦红，被测进程的整份输出就灌进判据面；
  被测进程只要在运行期把期望片段拼出来打到 stderr，「目标断言其实没红」照样判
  KILLED。
* `-rf` 短摘要行 `FAILED <nodeid> - <reason>`：reason 只取失败断言消息的**第一
  行**，内嵌插值(都在换行之后)进不来。这是三者里唯一能把「哪一条断言红了」问
  清楚的面。

⚠️ 配套硬约束（少一条判据就退化成恒不命中的**假 SURVIVED**）：
  1. harness 的 pytest 命令必须带 `-rf`（否则根本没有短摘要行）；
  2. 必须设 `COLUMNS` 足够大 —— 80 列下 `FAILED … - <reason>` 的 reason 会被
     截成空串；用 `judge_env()` 拿这份环境。
  两条都由 `judge_surface_missing()` 在**每次判定前**当场检查，缺了就报 harness
  失败，而不是安静地把所有变异记成 SURVIVED。

## `expect_msg` 的取值纪律

必须在它绑定的**门文件**里恰好出现 1 次（`check_expect_msg_unique()` 是门，不是
建议）：不唯一 ⇒ 「红在哪一条断言上」不再可证。且必须是断言消息的**首行字面
片段** —— 绑到第一个 `{}` 插值之后的内容，短摘要里根本没有，判据恒不命中。
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = [
    "PYEOF_RE",
    "check_expect_msg_unique",
    "failed_reasons",
    "gate_hit",
    "judge_env",
    "judge_surface_missing",
    "kill_identity_ok",
    "parse_failed_nodeids",
    "syntax_check",
]

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
PYEOF_RE = re.compile(r"<<'PYEOF'\n(.*?)\nPYEOF", re.DOTALL)

#: `-rf` 短摘要行。reason 可缺失(没有断言消息时 pytest 只打 `FAILED <nodeid>`)。
_FAILED_RE = re.compile(r"^FAILED (\S+?)(?: - (.*))?$", re.M)


def judge_env() -> dict[str, str]:
    """判据面成立所需的环境变量增量。

    ⛔ `COLUMNS` 必须给足：pytest 的 `-rf` 短摘要按终端宽度截断，80 列下
    `FAILED … - <reason>` 的 reason 会被截成空串 ⇒ `expect_msg` 恒不命中 ⇒
    全部报 SURVIVED。那种坏法看起来跟「门全都不承重」一模一样。
    """
    return {"COLUMNS": "1000", "PYTHONDONTWRITEBYTECODE": "1"}


def syntax_check(path: Path, text: str) -> str | None:
    """变异后的文本能不能编译？返回错误串；`None` = 通过。

    `.py` 直接编译；`.md` 逐个 PYEOF 块编译(写点本体就在块里，SKILL.md 的其余
    部分是散文，不该拿去编译)；其它后缀(如规格 `.md` 里没有 PYEOF 块)自然返回
    `None` —— 无可执行块 = 无编译期风险。

    ⛔ 这道自检是**假杀的结构性封堵**：语法不合法的变异体会让被测进程在编译期
    就死，于是「防线被拆掉之后本该发生的坏事」根本没机会发生，而门却因为**别的
    断言**红了被记成 KILLED。它照出的是负控自己坏了 —— 所以调用方必须单列第三种
    裁决，不并进 KILLED / SURVIVED 任何一边。
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


def parse_failed_nodeids(out: str) -> set[str]:
    """从 `-rf` 短摘要解析失败的 nodeid 集合。

    ⛔ 用短摘要而不是「输出里有没有 FAILED 字样」：「某处有失败」不能证明**指定
    的那道门**红了 —— 拿粗判据判 KILLED 是假杀的经典形态。
    """
    return {m[0] for m in _FAILED_RE.findall(out)}


def failed_reasons(out: str) -> list[tuple[str, str]]:
    """`-rf` 短摘要的 `(nodeid, reason)` 列表；无 reason 的记成空串。"""
    return [(m[0], m[1]) for m in _FAILED_RE.findall(out)]


def gate_hit(nodeid: str, failed: set[str]) -> bool:
    """声明的 nodeid 是否命中失败集 —— **含参数化用例**。

    ⛔ 实测教训：声明 `…::test_x` 而 pytest 报的是 `…::test_x[1]`，直接用
    `nodeid in failed` 会把真 KILLED 误报成 SURVIVED —— 判据自己坏了，长得却
    跟「门不承重」一模一样。
    """
    return any(f == nodeid or f.startswith(nodeid + "[") for f in failed)


def judge_surface_missing(rc: int, out: str) -> str | None:
    """判据面本身是否成立？返回问题描述；`None` = 成立。

    ⛔ 这道检查的方向是「**判据不可用**」而不是「变异没杀死」。两者的处置完全
    不同：前者要把 harness 判失败并让人去修命令行，后者才是关于被测物的结论。
    没有它的话，忘了给 `-rf` 会让 `parse_failed_nodeids()` 恒返空集 ⇒ 每一条都
    报 SURVIVED ⇒ 报告长得跟「所有门都不承重」一模一样(而真相是 harness 坏了)。
    """
    if rc == 1 and not _FAILED_RE.search(out):
        return "rc=1(有测试失败)但输出里没有 `-rf` 短摘要行 —— pytest 命令缺 `-rf`，判据面不存在"
    return None


def kill_identity_ok(rc: int, out: str, nodeid: str, expect_msg: str | None = None) -> bool:
    """KILLED 判据：`rc == 1` **且** 指定的那道门在失败集里 **且** 指定的那条断言真的抛了。

    * `rc == 1` 而不是 `rc != 0`：pytest 的 `2`=中断、`3`=内部错、`4`=用法错
      (门名打错 / nodeid 不存在)、`5`=零收集。这些非 1 的码在 `rc != 0` 判据下
      会被当成 KILLED —— 门名一打错，整份变异报告就全绿而毫无意义。
    * 只判 rc 会被**别的门**红了喂饱；只判 nodeid 会被**同一个门里别的断言**
      喂饱 —— 后者正是 M15 假杀的形态。
    * `expect_msg is None` 只在调用方把该条**显式**登记进豁免表时才允许出现；
      本函数不替调用方判断这件事(它看不见豁免表)，登记与否由各 harness 的
      `EXPECT_MSG_EXEMPT` 表加它自己的自检负责。
    """
    if rc != 1:
        return False
    failed = parse_failed_nodeids(out)
    if not gate_hit(nodeid, failed):
        return False
    if expect_msg is None:
        return True
    reasons = [r for nid, r in failed_reasons(out) if gate_hit(nodeid, {nid})]
    return any(expect_msg in r for r in reasons)


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
    cache: dict[str, str] = {}
    # ⛔ 生产侧扫描面**只读一遍**再复用：原实现对**每一条** expect_msg 都把整个
    # `canvas-vault` + `backend/app` 重扫一遍（约 1200 个文件）。18 条时只是慢，
    # 138 条时就成了「太慢所以干脆不开这道检查」——判据因为代价被关掉，和没有
    # 判据是一回事。
    prod_blobs: list[tuple[Path, bytes]] = []
    for root in prod_roots:
        # `prod_roots` 收**目录或单个文件**：被变异的生产文件里有一部分
        # (`validate_learning_events.py`) 就住在 `backend/scripts/` —— 而那个目录
        # 同时装着 harness 自己, 后者的 `EXPECT_MSG` 表里逐字写着这些片段。
        # 整目录扫会把「表里写了」误报成「生产里也有」⇒ 判据自指。
        candidates = [root] if root.is_file() else list(root.rglob("*"))
        for f in candidates:
            if f.is_symlink() or not f.is_file():
                continue
            try:
                prod_blobs.append((f, f.read_bytes()))
            except OSError:
                continue
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
