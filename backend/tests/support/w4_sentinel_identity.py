"""CARD-W4-SENTINEL-REBIND [BATCH-2026-09-11-第十四批] —— W4 哨兵身份的两个不变量。

⛔ **这个工具存在的理由**：W4 哨兵红此前用 pytest 的 ``FAILED`` nodeid 集合当身份，
但同一份代码**原样重跑两次**，红会挂到**不同的 nodeid** 上（U10-A 实测
``candidate422`` ↔ ``mock_warning``）—— 因为哨兵红归属取决于哪个用例恰好触发了那次
lifespan 健康检查，与代码无关。逐 nodeid diff 因此自带 flaky，比它等于在精确地测量噪声。

改绑到两个**跨跑恒定**的量：

* 不变量① **被拦下的次数**（``blocked=``，外加整条汇总四元组）；
* 不变量② **失败正文身份**（地址 + 线程**类别**，去掉 owner、抹掉线程对象地址）。

判据设计的通用检查：把候选身份串里的**每一个字段**逐个问「它跨跑恒定吗」。
``('::1', 7691, 0, 0)`` 恒定、``MainThread`` 恒定、``asyncio-portal-<hex>`` **不恒定**
（hex 是对象地址）、``owner=<nodeid>`` **不恒定**。漏问一个字段，判据就白改。

────────────────────────────────────────────────────────────────────────────
口径更正（与卡文字面冲突，依据落在
``_bmad-output/审查/evidence-w4-sentinel-rebind/coverage-corrections-*.txt``）
────────────────────────────────────────────────────────────────────────────

**更正③ 失败正文产出点是 3 处不是 2 处**（实测）：

* ``tests/support/live_port_guard.py:1551``（4 空格缩进，``_final_accounting``）
* ``tests/support/live_port_guard.py:1595``（2 空格缩进，``format_sentinel``）
* ``tests/conftest.py:184``（4 空格缩进，``pytest_sessionfinish``）——卡文与本卡首版
  锚点表**都漏了它**。同一条未结账记录可被印**两次** ⇒ 正文行条数 ≠ ``blocked``
  ⇒ 本模块**只判集合、不判条数**。

**更正④ 线程名含每跑不同的对象地址** ⇒ 身份必须归一，见 :func:`normalise_thread`。

**更正⑤ 两个 ``blocked=`` 产出点的值不必然相等，且不等是合法的**：``blocked`` 是
**单调**计数器（``live_port_guard.py:282`` 归零、``:355``/``:361`` 只 ``+= 1``，全文件无减法），
两个产出点是它的**两个时刻**——``summary_line`` 由 ``tests/conftest.py:227`` 在
``pytest_terminal_summary`` 取，``_final_accounting`` 由 ``live_port_guard.py:934`` 注册的
atexit 在更晚取。卡文 (d)① 要求「多处取值必须一致」会在门**正常工作**的那天把它判成工具错误。
本模块的不变量是 ``final >= summary``；只有 ``final < summary``（计数器倒退）才是冲突。

**更正⑥ ``advisory`` 是「只记不拦」= 放行**（``live_port_guard.py:230`` 逐字）——那几次
原 ``connect`` 照常被执行（门没拦），**是否真的连上取决于对端**；无论成败，「到现网端口的连接
尝试被放行了」这件事本身就是该看见的差异。只判 ``blocked`` 会把真连当没事，所以 CLI 比对的是
整条**四元组**并带算术自洽门 ``total == blocked + advisory``。

**更正⑦ 退出码不占用 3**：3 是 ``live_port_guard.FINAL_EXIT_CODE``，且逐字印在被读的
存档正文里；本工具占它会让「这个 3 是谁的」永久说不清。本模块用 0 / 1 / 2。

────────────────────────────────────────────────────────────────────────────

⛔ 本模块不 import ``app.*``、不起任何网络连接、不写任何文件（只读传入的路径）。
"""

from __future__ import annotations

import re
import sys

__all__ = [
    "W4LedgerConflict",
    "blocked_count",
    "failure_body_identities",
    "naive_failed_nodeids",
    "normalise_thread",
    "summary_quad",
]


class W4LedgerConflict(RuntimeError):
    """存档自相矛盾或混了多次运行 —— 调用方必须停下，不得挑一个值继续。"""


# ── 锚 ────────────────────────────────────────────────────────────────────
# 整行匹配，不用 re.search 的子串命中：存档里到处是把上一轮判据输出抄进去的回显行，
# 子串锚会把回显当产出。数字用 [0-9] 不用 \d —— 实测 \d 会吃全角数字（'１２' 命中且
# int() 得 12），而生产者是 int 的 f-string，不可能产全角；用 [0-9] 把伪造串挡在外面。
# '0|[1-9][0-9]*' 拒前导零：f"{int}" 永不产 '007'。

_SUMMARY_RE = re.compile(
    r"^NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=(0|[1-9][0-9]*) "
    r"\(blocked=(0|[1-9][0-9]*), advisory=(0|[1-9][0-9]*), "
    r"unaccounted=(0|[1-9][0-9]*)\)$",
    re.ASCII,
)

# ⛔ 必须含逐字「最终总账：」。不能拿 BLOCK_REASON 当锚——它在一次跑里有 5 个产出点
#    （每条被拦连接的 RuntimeError 文案 / 迟到分支 / 哨兵首行 / sessionfinish / 总账），
#    拿它做段落锚会锚到非总账段。
# reported_status 用 (\S+?)：ledger["reported_status"] 是 int | None，脚本直跑（非 pytest）
#    时逐字输出 'reported_status=None'；写成 (\d+) 会恒不匹配。
_FINAL_RE = re.compile(
    r"^\*\*\* live Neo4j port connect attempted —— 最终总账："
    r"blocked=(0|[1-9][0-9]*) unaccounted=(0|[1-9][0-9]*) reported_status=(\S+?)；",
    re.ASCII,
)

#: 失败正文记录行。三个产出点的缩进是 2 或 4 空格，这里一律先 strip 再认 ``- ``。
#: 地址段用**非贪婪**并从左锚 ``on thread``：owner（nodeid）是用户可控的、最长最靠后的字段，
#: 贪婪从右切会把 owner 切进身份里 —— 而 owner 正是要甩掉的那个会漂的量。
#:
#: ⛔ 线程名用 ``.+?`` 而不是 ``\S+``（Codex round-1 HIGH-3）：``threading.Thread(name=...)``
#: 允许**含空格**的线程名（实测 ``Thread-1 (worker)``）。``\S+`` 匹配不上时整行会被
#: ``if m:`` **静默丢弃**，身份集变空、CLI 照样判一致 —— 那是假绿。
_BODY_RE = re.compile(r"^- (?P<addr>.+?) on thread (?P<thread>.+?) \(owner=", re.ASCII)

#: 记录**块抬头**：三个产出点都在遍历记录之前**自报本块条数**。这是本模块唯一
#: 用来定位记录的锚 —— 不再扫全文猜「哪行像记录 / 哪行像坏掉的记录」。
#:
#: ⛔ 为什么换掉前两版的「痕迹判定」（Codex round-1/2/3 连打三轮同一处）：
#: r1 用 ``\S+`` ⇒ 含空格线程名静默丢失；r2 用「像不像记录」的宽松候选 ⇒ 普通日志假红
#: （MEDIUM-3）；r3 用「截断痕迹 + 孤儿痕迹」⇒ ``worker\n- continued``、空线程名、
#: ``地址\n- 续段``、owner 前截断 **四类**仍然两条痕迹都不命中 ⇒ 假绿。
#: 三轮都栽在同一件事上：**开放式地判断「这行坏没坏」永远补不完**。
#: 换成闭合判据：**只读被自报过条数的块，那 N 行必须逐行解析成功**，
#: 少一行、多一行、有一行解析不出 —— 一律拒判；块外的行根本不看（假红也一并消失）。
#:
#: 抬头 A（``live_port_guard`` 最终总账）：条数 = ``unaccounted``，即 :data:`_FINAL_RE` 第 2 组。
#: 抬头 B（根 ``conftest`` 无人结账）与 C（``format_sentinel`` 本用例）：条数在抬头自身。
#: ⛔ B 锚死 ``BLOCK_REASON``（Codex round-4 MEDIUM-4：原来的 ``.*?`` 让普通输出
#: ``*** cache —— 1 次拦截无人结账`` 被当成正式块 ⇒ 假红），且**只依赖到「N 次拦截」为止** ——
#: 判据依赖的文案越短，产出方在其后改字就越不会误伤它（round-4 MEDIUM-3）。
_BLOCK_HEAD_B_RE = re.compile(r"^\*\*\* live Neo4j port connect attempted —— (0|[1-9][0-9]*) 次拦截", re.ASCII)
_BLOCK_HEAD_C_RE = re.compile(
    r"^live Neo4j port connect attempted —— 本用例期间有 (0|[1-9][0-9]*) "
    r"次到现网 Neo4j 的连接尝试被拦下。$",
    re.ASCII,
)

#: ``format_sentinel`` 抬头之后、记录之前的**固定说明行数**（``live_port_guard.py`` 内
#: ``lines = [抬头, "（连接处…", "  所以由本哨兵…）"]``）。判据按此常量定位记录起点，
#: 不做任何「向前找找看」。产出方增删说明行 ⇒ 首条「记录」解析不出 ⇒ 拒判（方向安全）。
_FORMAT_SENTINEL_PROSE_LINES = 2

#: ``asyncio-portal-<hex>``：hex 是对象地址，**每跑不同**。归一成类别名。
_PORTAL_RE = re.compile(r"^(asyncio-portal)-[0-9a-f]+$", re.ASCII)

#: 朴素旧判据用的 pytest 失败行（只作**验伪锚**，证明旧口径会漂；不参与新判定）。
_FAILED_RE = re.compile(r"^(?:FAILED|ERROR) (?P<nodeid>\S+)", re.ASCII)

#: ANSI 转义。``--color=yes`` / ``PY_COLORS=1`` 下整行锚会静默 0 命中，
#: 若再把「没命中」压成 0 就是假绿。
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _lines(text: str) -> list[str]:
    """切行。

    ⛔ 禁用 ``str.splitlines()``：它把 ``\\x0b`` / ``\\x0c`` / ``\\u2028`` 等也当换行，
    而记录行里的地址是 ``_safe_repr(address)`` 的**裸 repr**、内容由调用方的
    ``__repr__`` 决定（契约测试里就有返回任意串的地址对象）。一个含 ``\\x0b`` 的地址
    能在 ``splitlines()`` 下**伪造出一条合法汇总行**。只按真正的换行切。
    """
    return re.split(r"\r\n|\r|\n", _ANSI_RE.sub("", text))


def normalise_thread(thread: str) -> str:
    """把线程名里**每跑不同**的对象地址抹掉，保留线程**类别**。

    ``asyncio-portal-15f0ef460`` → ``asyncio-portal-<id>``；``MainThread`` 原样返回。

    ⛔ 只抹地址、不抹类别：``MainThread`` 与 ``asyncio-portal-<id>`` 必须仍可区分，
    否则判据又把一个真实差别抹平了（那是另一个方向的假绿）。
    """
    return _PORTAL_RE.sub(r"\1-<id>", thread)


def summary_quad(text: str) -> tuple[int, int, int, int] | None:
    """汇总行的四元组 ``(total, blocked, advisory, unaccounted)``；无命中返回 ``None``。

    ``None`` 的含义是 **unchecked（没查成）**，不是 ``(0, 0, 0, 0)``。
    """
    quads = [
        (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
        for m in (_SUMMARY_RE.match(ln.strip()) for ln in _lines(text))
        if m
    ]
    if not quads:
        return None
    if len(quads) > 1:
        raise W4LedgerConflict(f"一份存档里有 {len(quads)} 条汇总行 —— 混了多次运行，比它没有意义：{quads}")
    total, blocked, advisory, unaccounted = quads[0]
    if total != blocked + advisory:
        raise W4LedgerConflict(
            f"汇总行不自洽：total={total} != blocked={blocked} + advisory={advisory}"
            "（record() 每次尝试恰给 total 加一次、给 blocked/advisory 二选一加一次）"
        )
    return total, blocked, advisory, unaccounted


def _final_blocked(text: str) -> int | None:
    """最终总账行的 ``blocked``；无命中返回 ``None``。

    总账行**不是必选**：``_final_accounting`` 只在 ``unaccounted > 0 or
    (blocked > 0 and effective_status == 0)`` 时才打印，而迟到路径的 ``os._exit``
    会跳过所有 atexit。所以「没有总账行」既不蕴含 ``blocked == 0`` 也不蕴含出错。
    """
    finals = [int(m.group(1)) for m in (_FINAL_RE.match(ln.strip()) for ln in _lines(text)) if m]
    if not finals:
        return None
    if len(finals) > 1:
        raise W4LedgerConflict(
            f"一份存档里有 {len(finals)} 条最终总账行 —— 一进程至多一条，多条 = 混了多个进程：{finals}"
        )
    return finals[0]


def blocked_count(text: str) -> int | None:
    """本轮被 W4 门拦下的连接次数。

    :returns: ``int`` —— 检出门产出行并已交叉校验；
              ``None`` —— **unchecked（没查成）**：文本里找不到任何门产出行。**不是 0**。
    :raises W4LedgerConflict: 文本自相矛盾或混了多次运行。

    两个产出点在场时取**较晚**的那个（总账行），并核 ``final >= summary``
    （更正⑤：单调计数器的两个时刻，``final > summary`` 合法，``final < summary`` 不可能）。
    """
    quad = summary_quad(text)
    final = _final_blocked(text)
    if quad is None and final is None:
        return None
    if quad is None:
        return final
    if final is None:
        return quad[1]
    if final < quad[1]:
        raise W4LedgerConflict(
            f"计数器倒退：总账 blocked={final} < 汇总 blocked={quad[1]} —— "
            "blocked 只增不减，倒退说明这份存档混了不同的运行"
        )
    return final


def _declared_record_blocks(lines: list[str]) -> list[tuple[int, int, int]]:
    """找出全部「自报了条数的记录块」：返回 ``(抬头行下标, 自报条数, 记录起始偏移)``。

    三个产出点（更正③）各自的抬头见 :data:`_BLOCK_HEAD_B_RE` / :data:`_BLOCK_HEAD_C_RE`
    与 :data:`_FINAL_RE`。抬头 A 的条数是 ``unaccounted`` —— 它遍历的是
    ``ledger["unaccounted_records"]``，**不是** blocked 全集，别拿 blocked 去对。
    """
    heads: list[tuple[int, int, int]] = []
    for i, raw in enumerate(lines):
        line = raw.strip()
        m = _FINAL_RE.match(line)
        if m:
            heads.append((i, int(m.group(2)), 1))  # 第 2 组 = unaccounted；记录在下一行
            continue
        m = _BLOCK_HEAD_B_RE.match(line)
        if m:
            heads.append((i, int(m.group(1)), 1))
            continue
        m = _BLOCK_HEAD_C_RE.match(line)
        if m:
            # ``format_sentinel`` 抬头后**固定两行**说明，随后才是记录。
            heads.append((i, int(m.group(1)), 1 + _FORMAT_SENTINEL_PROSE_LINES))
    return heads


def failure_body_identities(text: str) -> set[str]:
    """失败正文的**身份**集合：``<address> on thread <归一后的线程名>``。

    去掉 ``- `` 前缀与 ``(owner=...)`` 段（owner 是会漂的 nodeid），
    并把线程名里每跑不同的对象地址归一（见 :func:`normalise_thread`）。

    只判**集合**不判条数：同一条记录可被三个产出点中的两个各印一次（更正③）。
    所以**跨块**不比条数；条数只在**块内**与该块抬头自报的数对账。

    ⛔ 判定方式（Codex round-3 HIGH-1 后重写，第三次改这里）：
    **只读被抬头自报过条数的块**，块内第一条 ``- `` 行起连取 N 行，这 N 行必须
    **逐行**匹配 :data:`_BODY_RE`；任何一行不匹配、或紧随其后还有一行也是记录，
    一律 :class:`W4LedgerConflict`（CLI rc=2）。块外的行**根本不看**。

    这条换掉了前三版「扫全文判断某行坏没坏」的开放式规则。那种规则被连续三轮
    各证伪一次（``\\S+`` / 宽松候选 / 截断+孤儿痕迹），每次都是「换个输入又活过来」：
    ``worker\n- continued`` 的续段以 ``- `` 开头逃过孤儿检查、空线程名两条痕迹都不命中、
    ``地址\n- 续段`` 让前半段消失而后半段自成一条合法记录、owner 前截断整行被丢。
    **开放式地枚举「坏法」补不完；闭合地要求「块内必须恰好 N 行且行行可解析」才补得完。**

    代价（如实写在这里）：抬头文案若被改动，本函数会**看不见**那个块 —— 方向是
    「记录消失」而不是「记录错认」，故末尾对 ``blocked > 0 却一个块都没有`` 另设拒判。
    """
    lines = _lines(text)
    out: set[str] = set()
    claimed: set[int] = set()
    blocks = _declared_record_blocks(lines)

    for head_idx, declared, prose in blocks:
        if declared == 0:
            # ⛔ 抬头 A 的第二个触发分支（``unaccounted > 0 or (blocked > 0 and status == 0)``）
            #    会打出 ``unaccounted=0`` 的抬头、后面零条记录。此时**不得向前扫** ——
            #    扫过去会撞上别处的记录行，判成「自报条数与实际不符」⇒ 假红。
            #    自报 0 条就是没有记录要读，也就没有什么要对账。
            continue
        # ⛔ 记录起始位置是**已知常量**，不是「向前找找看」（Codex round-4 HIGH-1）：
        #    上一版写成「扫到第一条 ``- `` 行」，于是 ``address="\\n- tail"`` 让首条记录退化成
        #    只剩 ``- ``（strip 后是 ``-``、不满足 ``startswith("- ")``）而被当说明行**跳过**，
        #    扫描继续前进落到后半段上并解析成功 ⇒ 两份不同的档判一致。
        #    **只要还有任何一处是「向前找找看」，它就还是开放式规则** —— 这是第四次栽在同一件事上。
        i = head_idx + prose
        taken = [lines[j].strip() for j in range(i, min(i + declared, len(lines)))]
        if len(taken) < declared:
            raise W4LedgerConflict(
                f"记录块自报 {declared} 条，但存档只剩 {len(taken)} 行 —— "
                f"存档被截断，不得当作『就这么多记录』：抬头={lines[head_idx].strip()[:80]!r}"
            )
        parsed = [_BODY_RE.match(ln) for ln in taken]
        if not all(parsed):
            bad = [ln for ln, m in zip(taken, parsed) if not m]
            raise W4LedgerConflict(
                f"记录块自报 {declared} 条，其中 {len(bad)} 行解析不出身份 —— "
                f"不得当作『没有这条记录』静默放过：{bad[:3]}"
            )
        nxt = i + declared
        if nxt < len(lines) and _BODY_RE.match(lines[nxt].strip()):
            raise W4LedgerConflict(
                f"记录块自报 {declared} 条，紧随其后还有一条记录行 —— 自报条数与实际不符：{lines[nxt].strip()[:80]!r}"
            )
        claimed.update(range(i, i + declared))
        for m in parsed:
            out.add(f"{m.group('addr')} on thread {normalise_thread(m.group('thread'))}")

    # ⛔ 每一行「无疑义地就是一条记录」的行，都必须被某个块认领（Codex round-4 MEDIUM-2）。
    #    原来的兜底只管「一个块都没有」，于是「有一个块正常、另一个块抬头漂了」时，
    #    漂掉那块的记录**静默消失**、两份不同的档判一致。
    #
    #    注意这**不是**回到「猜这行坏没坏」：这里只认**完整匹配 `_BODY_RE`** 的行
    #    （必须同时有 ``- `` 前缀、`` on thread ``、`` (owner=``）。普通日志
    #    （``cache refreshed (owner=worker)`` 缺 `` on thread ``、源码回显不以 ``- `` 开头）
    #    都不满足，所以 round-3 MEDIUM-2 的那几条假红不会回来。
    orphans = [ln.strip() for n, ln in enumerate(lines) if n not in claimed and _BODY_RE.match(ln.strip())]
    if orphans:
        raise W4LedgerConflict(
            f"有 {len(orphans)} 条完整的记录行不属于任何自报条数的记录块 —— "
            f"多半是某个块的抬头文案已漂、整块判据看不见它：{orphans[:3]}"
        )

    if not blocks:
        blocked = blocked_count(text)
        if blocked:
            raise W4LedgerConflict(
                f"账面记着 blocked={blocked}，却一个自报条数的记录块都没有 —— "
                "存档被截断或抬头文案已漂，身份集为空不代表没有记录"
            )
    return out


def naive_failed_nodeids(text: str) -> set[str]:
    """**验伪锚专用**：朴素的旧判据 —— pytest 的 ``FAILED``/``ERROR`` nodeid 集合。

    ⛔ 它**不是**本模块的判据，只用来在测试里证明「旧口径在同两份样本上会漂」。
    没有这条对照，「新判据两份相等」就只是「两份碰巧一样」，证明不了改绑的必要性。
    """
    return {m.group("nodeid") for m in (_FAILED_RE.match(ln.strip()) for ln in _lines(text)) if m}


# ── CLI ───────────────────────────────────────────────────────────────────
# 退出码：0 = 两个不变量跨文件一致；1 = 不一致；2 = 说不清（读不出/冲突/参数问题）。
# ⛔ 不占用 3（= live_port_guard.FINAL_EXIT_CODE，逐字印在被读的存档里）。
# ⛔ 失败方向是「说不清就非 0」，绝不「说不清就静默退 0」——这工具是判据，
#    一个能让它在真有问题时说「没问题」的出口，比十个误报严重。

_USAGE = "usage: python -m tests.support.w4_sentinel_identity <evidence.txt> [<evidence.txt> ...]"


def _describe(path: str) -> tuple[str, object, object, object]:
    """读一份存档，返回 ``(path, blocked, quad, bodies)``。

    ⛔ 必须把**四元组**也带出来（Codex round-1 HIGH-1）：初版只返回 ``blocked`` 与 bodies，
    于是 ``advisory=12``（12 次到现网的连接尝试**被放行**，是否连上取决于对端）与全零档被判成一致。
    我在 docstring 与验收单里写过「CLI 比对整条四元组」——那句话当时是**假的**：
    ``summary_quad`` 写了但从没接进 CLI。能力存在 ≠ 能力接上了。

    ⛔ 解码用 ``strict``（Codex round-3 MEDIUM-3）：初版用 ``errors="replace"``，
    两份线程名原始字节分别是 ``work\\x80er`` / ``work\\x81er`` 的存档会**双双**变成
    ``work\ufffder`` 而被判一致 —— 又一条「读不清却仍参与比较」。
    存档读不出来就是读不出来，拒判（rc=2），不许拿替换字符去凑相等。
    """
    try:
        with open(path, encoding="utf-8", errors="strict") as fh:
            text = fh.read()
    except UnicodeDecodeError as exc:
        raise W4LedgerConflict(f"存档不是合法 UTF-8，读不出原文，无法参与一致性比较: {path} ({exc})") from exc
    return path, blocked_count(text), summary_quad(text), failure_body_identities(text)


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("-")]
    if len(argv) != len(args):
        print(f"unknown arg: {[a for a in argv if a.startswith('-')][0]}\n{_USAGE}", file=sys.stderr)
        return 2
    if len(args) < 2:
        # ⛔ 1 份不是「一致」：没有可比对象时不得退 0（那会让
        #    `if tool a; then echo 判据通过; fi` 恒真）。
        print(f"需要至少 2 份存档才能比对，收到 {len(args)} 份\n{_USAGE}", file=sys.stderr)
        return 2

    rows = []
    for path in args:
        try:
            rows.append(_describe(path))
        except OSError as exc:
            print(f"W4-IDENTITY: UNREADABLE {path}: {exc}", file=sys.stderr)
            return 2
        except W4LedgerConflict as exc:
            print(f"W4-IDENTITY: CONFLICT {path}: {exc}", file=sys.stderr)
            return 2

    for path, blocked, quad, bodies in rows:
        shown = "unchecked(没查成)" if blocked is None else blocked
        print(f"{path}: blocked={shown} quad={quad} bodies={sorted(bodies)}")

    unchecked = [p for p, b, _, _ in rows if b is None]
    if unchecked:
        print(f"W4-IDENTITY: UNCHECKED 这些存档里找不到门产出行，比不了: {unchecked}", file=sys.stderr)
        return 2

    # ⛔ 缺四元组的档**不可比**（Codex round-2 HIGH-1）：初版把 None 从 quad_vals 里滤掉，
    #    于是「A 只有总账行（advisory 未知）+ B 有 advisory=12」被判一致。
    #    没有汇总行就不知道 advisory 是多少，而 advisory 是**被放行**的那些尝试 —— 说不清就非 0。
    no_quad = [p for p, _, q, _ in rows if q is None]
    if no_quad:
        print(
            f"W4-IDENTITY: UNCHECKED 这些存档没有汇总行、advisory 未知，比不了: {no_quad}",
            file=sys.stderr,
        )
        return 2

    blocked_vals = {b for _, b, _, _ in rows}
    quad_vals = {q for _, _, q, _ in rows}
    body_vals = {frozenset(s) for _, _, _, s in rows}
    if len(blocked_vals) > 1 or len(quad_vals) > 1 or len(body_vals) > 1:
        print(
            f"W4-IDENTITY: DIFFER blocked={sorted(blocked_vals)} "
            f"quad={sorted(quad_vals)} bodies={[sorted(s) for s in body_vals]}",
            file=sys.stderr,
        )
        return 1

    only = blocked_vals.pop()
    # ⛔ 「全零」必须按**整条四元组**判（Codex round-2 MEDIUM-4）：初版只看 blocked，
    #    于是 (12, 0, 12, 0) —— 12 次尝试被 advisory 放行 —— 也被打上「全零」标签。
    if only == 0 and quad_vals == {(0, 0, 0, 0)}:
        # ⛔ 全零不等于「门在位且本轮查完了」（Codex round-1 HIGH-2）。
        #    汇总行由 summary_line() 产，而它**不含 installed 字段**（账本 dict 有、汇总行没有）；
        #    pytest-xdist 下每个 worker 有独立 STATE，主进程那条全零汇总看不到 worker 的账。
        #    ⇒ 纯文本无从区分「门在位、零连接」与「门/记账缺席」。
        #    这里仍退 0（否则每一次干净跑都会红），但**必须把话说清**，不得让
        #    `W4-IDENTITY: CONSISTENT` 这个串在全零档上冒充「门证明了什么」。
        print(
            f"W4-IDENTITY: CONSISTENT-ZERO files={len(rows)} quad={sorted(quad_vals)}\n"
            "  ⚠️ 全零：本工具只能证明这几份存档**彼此一致**，"
            "不能证明门当时在位、也不能证明覆盖完整（汇总行不含 installed；xdist 每 worker 独立记账）。"
        )
        return 0

    print(f"W4-IDENTITY: CONSISTENT files={len(rows)} blocked={only} quad={sorted(quad_vals)}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI 入口
    sys.exit(main(sys.argv[1:]))
