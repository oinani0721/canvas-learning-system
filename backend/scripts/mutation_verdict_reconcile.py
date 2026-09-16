#!/usr/bin/env python3
"""跨套「六档处置表」逐档硬比 —— CARD-DEBT-mutkill-R3 MEDIUM③。

⛔ **这不是「读汇总段字段」，是「解析被测套自己印出来的裁决」**。两者差别必须说清：
四套变异 harness 里**只有 `g33`** 有 `--json` 并写结构化的 `verdict_counts`
（`g33_mutation_gates.py` 的 `--json` 选项与 `"verdict_counts": nv` 字段）；
`g32b` / `g32cb` / `g32ccr1` 三套**既无 `--json` 选项也无该字段**（2026-09-14 于
`B14_BASE` 树 `grep -cF 'verdict_counts'` / `grep -cF -- '--json'` 实测皆为 0），
它们的六档只出现在 **stdout 的汇总段**。所以本工具对三套是**按套写正则去解析人读
文本**，正则写错 = 本工具自己红（解析不到任一档即 `SystemExit`），⛔ 不得静默判「一致」。
「给三套补 `--json`/`verdict_counts`」已裁另立第十五批卡，不在本卡地盘。

⛔ **不自证**：本工具**不重新裁决**任何变异，也不统计自己解析出来的裁决结果去和
自己比 —— 那是恒真式。真正承重的独立判据是**分母**：每套「应有多少条变异」由本
工具**自己用 AST 从该套源码现算** `len(MUTATIONS)`，⛔ 不采信存档或 stdout 自称的
`total` / `M`。四个数必须全相等：

    ① reconcile 自己把解析到的六档相加      = sum(six)
    ② 该套**自己印出来**的「六档之和」      = T
    ③ 该套**自称**的分母                    = M
    ④ 本工具从源码 AST 现算的变异条数        = N

  · ①≠② ⇒ 存档里某一档的计数被改过 / 正则吃错了行；
  · ②≠③ ⇒ 有条目跑完没落进任何一档（该套自己的 `_sum_ok` 本该已经报，存档可能被改）；
  · ③≠④ ⇒ **部分跑冒充全量**，或 `MUTATIONS` 漂移 —— 这一条才是跨源独立判据。

只读：本工具只读存档与 tee 文件 + 用 `ast` 解析 harness 源码（⛔ 不 `import` 任何
harness 的 `main()`、不跑门、不改盘、不连任何库）。

用法::

    python3 scripts/mutation_verdict_reconcile.py \\
        --expect g32cb,g32ccr1 \\
        --stdout g32cb=<tee.txt> --stdout g32ccr1=<tee.txt>

`--expect` 是**声明式**的：声明了哪几套，就必须给哪几套的输入。声明了却没给输入 /
文件不存在 / 解析不到六档 ⇒ `SystemExit`（非零 rc）。
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import symtable
import sys
from pathlib import Path
from typing import NamedTuple

SCRIPTS = Path(__file__).resolve().parent

#: 六档口径与 `mutation_kill_identity.VERDICTS` 逐字一致。
#: ⛔ 这里**故意写死一份字面量**而不是 `from mutation_kill_identity import VERDICTS`：
#: 本工具是对账方，档名是它的**独立预期**。跟被对账方共用同一个常量，「档名漂了」
#: 这件事就再也对不出来了（两份手抄清单会漂移，但漂移正是这道门要抓的东西）。
VERDICT_NAMES: tuple[str, ...] = (
    "KILLED",
    "KILLED-UNBOUND",
    "SURVIVED",
    "HARNESS-ERROR",
    "ANCHOR-ERROR",
    "SYNTAX-INVALID",
)

#: `g32cb` / `g32ccr1` 的尾五档形态：`«2 空格»档名: N`。
#: ⚠️ **不适用于 g32b**（Codex round-7 LOW，此前这条注释把三套一起说了）：g32b 的
#: `KILLED-UNBOUND` 是 `档名 (说明): N`，所以它单列了 `_B_UNBOUND`；其余四档才是 `档名: N`。
_TAIL_FIVE = "KILLED-UNBOUND|SURVIVED|HARNESS-ERROR|ANCHOR-ERROR|SYNTAX-INVALID"


class Parsed(NamedTuple):
    """从一份存档里解析出来的东西（全部来自**被对账方自己的输出**）。"""

    counts: dict[str, int]
    printed_total: int  # 该套自己印的「六档之和」
    declared_m: int  # 该套自称的分母
    #: **逐条**裁决记录里各档的出现次数；`None` = 这份存档里没有逐条记录可数。
    #: ⛔ 它与 `counts` 是**两个来源**：`counts` 来自聚合行/聚合字段，本字段来自
    #: 该套逐条打印（或 JSON 的 `results[]`）的那些行。聚合被**补偿式篡改**
    #: （KILLED 9→8 同时 SURVIVED 0→1，和不变）时，四个数全对得上，只有它能看出来。
    per_item: dict[str, int] | None = None


class Suite(NamedTuple):
    source: str  # harness 源码文件名（AST 现算分母用）
    form: str  # "stdout" | "json"


SUITES: dict[str, Suite] = {
    # ⚠️ g32b 的汇总段**不缩进**，且多印一行「KILLED 合计」——那**不是**六档之一。
    "g32b": Suite("g32b_mutation_gates.py", "stdout"),
    "g32cb": Suite("g32cb_mutation_gates.py", "stdout"),
    "g32ccr1": Suite("g32ccr1_negative_controls.py", "stdout"),
    # ⚠️ 只有 g33 有 `--json` / `verdict_counts`（实测）。
    "g33": Suite("g33_mutation_gates.py", "json"),
}


class ReconcileError(Exception):
    """解析/对账失败。⛔ 一律上抛成非零 rc，不得降级成「一致」。"""


# ── 独立分母：AST 现算 ──────────────────────────────────────────────────────


def _literal_len(node: ast.AST, source_name: str, lineno: int) -> int:
    """字面量列表的条数；⛔ 任何数不出来的形态都抛（不返回估计值）。"""
    if not isinstance(node, ast.List):
        raise ReconcileError(f"{source_name}:{lineno} `MUTATIONS` 的值不是字面量列表，分母数不出来")
    starred = [e for e in node.elts if isinstance(e, ast.Starred)]
    if starred:
        # `MUTATIONS += [*OTHER, x]` —— `*OTHER` 展开几条要执行才知道。
        raise ReconcileError(f"{source_name}:{lineno} `MUTATIONS` 字面量里有 `*` 展开，条数数不出来")
    return len(node.elts)


def ast_mutation_count(source_name: str) -> int:
    """从 harness 源码 AST 现算 `len(MUTATIONS)`（**含所有 `MUTATIONS += [...]` 扩展**）。

    ⛔ 用 `ast.parse` 而不是 `import`：import 会执行模块级代码（含路径常量与可能的
    副作用），而本工具的承诺是**只读**。

    ⛔⛔ **必须把扩展算进去**（Codex round-4 MEDIUM）：`g32b_mutation_gates.py` 是
    `MUTATIONS = [6 条]` 之后跟着 **36 段** `MUTATIONS += [...]`（共 132 条）—— 真实分母是
    **138**（与它自己 `--list` 印的「共 138 条变异」一致）。上一版只取**第一个**
    `MUTATIONS = [...]` 就返回，于是 g32b 的「独立分母」恒为 6：一份只跑了 6 条的部分表
    能冒充全量通过对账 —— 这道本该是**唯一跨源独立判据**的门，对 g32b 从来就是错的。
    ⚠️ 连带更正：卡文 §〇 事实格写「g32b **6**」同样是只读了首个赋值，实测应为 **138**。

    ⛔⛔⛔ **fail-closed 覆盖到全树**（Codex round-5 MEDIUM）：上一版只扫 `tree.body`，于是
    **嵌套块里**的写入（`if True: MUTATIONS += [...]`、`for ...: MUTATIONS += [...]`、函数里
    `global MUTATIONS` 后赋值）既不计数、**也不报错** —— 又一次「少算而不出声」，正是这条
    判据连着两轮失效的同一个形态。现在的判据是**两段**：
      ① 只在**模块级顶层**认两种可数形态（`= [字面量]` / `+= [字面量]`）并计数；
      ② 全树扫描，凡是 `MUTATIONS` 的**写入位**（`Store`/`Del` 上下文的 Name）不在 ① 认下的
         那几个，或出现 `MUTATIONS.<就地改动方法>(...)`，一律**抛**。
    ⇒ 数不出来时给的是错误，**不是一个偏小的数**。

    ⚠️ 如实声明剩余面：`globals()["MUTATIONS"] = …` / `exec()` 之类的动态写入静态数不出来，
    本函数看不见（四套源码实测均无此形态）。

    ⛔⛔⛔ **本函数的威胁模型，写在这里免得后人（和复核者）一轮轮重打同一个地方**：
    它承诺的是**跨源一致性** —— 「部分表冒充全量」「`MUTATIONS` 漂移」「存档被改过」
    这三件事；它**不**承诺抵抗一个**蓄意改写自己源码**的 harness 作者。理由是那不成立：
    能改 harness 源码的人同样能改它印出来的六档与自称分母，多这一维不会更强。
    ⇒ 白名单的作用是「**静态数不出来就抛**」，⛔ 不是「证明这份源码在运行期改不了表」——
    后者在 Python 里**静态不可判定**（`exec` / `globals()` / 帧对象 / 描述符 / C 扩展 /
    `__init_subclass__` …），本函数从不声称做到了它。历轮被换入口打穿**八次**
    （`__imul__` → `__class__.__imul__` → `copy.__self__` → `__iter__().__reduce__()` →
    `list.append(MUTATIONS, 4)` / `alias = MUTATIONS` → `Sink()[MUTATIONS]` / 重定义 `len` →
    `match case len:` → `match case MUTATIONS:` → 生成器帧 `gi_frame.f_locals[".0"]`），
    每次都修了，但**判据的强度上限就在这里**：它能保证的是「凡是它数出来的，数法是那三种
    可数形态；凡是它数不出来的，它抛」，不是「运行期条数一定等于这个数」。
    """
    path = SCRIPTS / source_name
    if not path.exists():
        raise ReconcileError(f"harness 源码不存在，分母无法独立现算: {path}")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    total: int | None = None
    counted_targets: set[int] = set()  # ① 认下的那些写入位（按 Name 节点身份）
    for node in tree.body:  # ⛔ 只在**模块级顶层**认，嵌套块交给 ② 去抛
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MUTATIONS" for t in node.targets):
            if len(node.targets) != 1:
                # `MUTATIONS = OTHER = [...]` / `a, MUTATIONS = ...` —— 不认，交给 ② 抛。
                continue
            total = _literal_len(node.value, source_name, node.lineno)  # 重新赋值 ⇒ 从头计数
            counted_targets.add(id(node.targets[0]))
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) and node.target.id == "MUTATIONS":
            if not isinstance(node.op, ast.Add):
                raise ReconcileError(f"{source_name}:{node.lineno} `MUTATIONS` 的扩展不是 `+=`，分母数不出来")
            if total is None:
                raise ReconcileError(f"{source_name}:{node.lineno} 先 `+=` 后赋值？分母数不出来")
            total += _literal_len(node.value, source_name, node.lineno)
            counted_targets.add(id(node.target))

    # 父节点索引 —— ② 段判「这个 Load 出现在什么语境里」要用。
    parent: dict[int, ast.AST] = {}
    for _n in ast.walk(tree):
        for _c in ast.iter_child_nodes(_n):
            parent[id(_c)] = _n

    # ⛔ round-16（Codex round-13 MEDIUM）：白名单里的 `len(MUTATIONS)` 之前只核**名字**叫
    # `len`，没核它**绑到谁**。模块里 `def len(x): x.append(4); return 0` 之后，
    # `len(MUTATIONS)` 就是一次就地改表 —— 实测运行时 4 条、AST 数 3 条。
    #
    # ⛔⛔ round-17（Codex round-14 MEDIUM）：**不要自己手数「哪些节点算绑定」**。
    # 上一版手列了 `Name(Store/Del)` / `def` / `class` / `import` / `arg` / `global`，
    # 一轮就被 `match grow: case len:` 穿过去了（`ast.MatchAs.name` 不在名单里）——
    # 这是同一张卡里第**七**次「逐个堵入口」被换个入口绕开。绑定形态是**语言规范**的一部分，
    # 手抄的名单必然漂移（`MatchStar` / `MatchMapping.rest` / 海象 / `except as` / 推导式目标 /
    # `type X = …` 还有以后新加的语法）。⇒ 改问**编译器自己**：`symtable` 就是 CPython 用来
    # 决定作用域绑定的那张表，它认得全部绑定形态。
    # ⚠️ `symtable.symtable()` 只编译出符号表，**不执行**模块代码 —— 与 `ast.parse` 同级，
    # 本工具「只读」的承诺不变。
    # ⚠️ 收得比必要更紧（函数内的局部 `len` 也算）：这里的承诺是「静态数得出来」，
    # 而「这个 `len` 到底是哪个」静态上就是分辨不了的。实测四套源码 `len` 绑定 = 0。
    def _name_is_bound_anywhere(table: symtable.SymbolTable, name: str) -> bool:
        try:
            sym = table.lookup(name)
        except KeyError:
            sym = None
        if sym is not None and (sym.is_assigned() or sym.is_parameter() or sym.is_imported()):
            return True
        return any(_name_is_bound_anywhere(child, name) for child in table.get_children())

    try:
        _symtab = symtable.symtable(source, source_name, "exec")
    except SyntaxError as exc:  # 解析不了 ⇒ 数不出来，不是「没有绑定」
        raise ReconcileError(f"{source_name} 编译符号表失败({exc!r})，分母数不出来") from exc
    _len_is_builtin = not _name_is_bound_anywhere(_symtab, "len")

    # ② fail-closed 全树扫描：任何**没被 ① 数到**的写入/改动一律抛。
    #
    # ⛔ Codex round-6 MEDIUM：只看 `Name` 的 `Store`/`Del` **不够** —— `MUTATIONS[:0] = [9]`
    # 与 `del MUTATIONS[0]` 里的 `MUTATIONS` 是 **Load** 上下文（写入位是外层的 `Subscript`），
    # 于是切片增删又一次「少算而不出声」。这里补上三类：下标写入、下标删除、`del MUTATIONS`。
    # ⛔⛔⛔ round-18（Codex round-15 MEDIUM）：`MUTATIONS` **自己**也会被非 `Name` 的绑定
    # 形态重绑 —— `match [1,2,3,4]: case MUTATIONS:` 走 `ast.MatchAs.name`（一个**字符串**
    # 字段，不是 `Name` 节点）⇒ 下面那条按 `Name(Store/Del)` 的核**看不见**它，实测运行时 4 条、
    # 上一版 AST 数 3 条。⚠️ 这与 round-17 修的是**同一个洞的另一半**：那次修的是 `len`，
    # 这次是 `MUTATIONS` 本身 —— 改 `len` 时只想着「谁被调用」，没回头问「这张名字表对**它**
    # 自己成不成立」。
    # ⇒ 判据不按**节点类型**枚举（那条路已被换入口绕开七次），按**字段位置**：任何节点
    # （`Name` 与 `Constant` 除外）只要**自己的某个字符串字段**恰好是 `"MUTATIONS"`，
    # 就说明这个名字出现在一个**名字位**上而不是读取位 ⇒ 数不出来，抛。
    #   · 排除 `Name` —— 每一次**读** `MUTATIONS` 都是 `Name.id`，由下面的 ctx 分支与读白名单管；
    #   · 排除 `Constant` —— 文档串/消息里提到 `MUTATIONS` 不是绑定。
    # 这条规则**自动**覆盖 `MatchAs.name` / `MatchStar.name` / `MatchMapping.rest` /
    # `ExceptHandler.name` / `alias.asname` / `FunctionDef.name` / `Global.names` …
    # 以及以后新增的同形语法（它们都把名字放在字符串字段里）。
    # ⚠️ 实测四套源码命中 **0 处**（各 0/0/0/0），不挡任何现有合法写法。
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Name, ast.Constant)):
            for field in node._fields:
                value = getattr(node, field, None)
                if value == "MUTATIONS" or (isinstance(value, list) and any(v == "MUTATIONS" for v in value)):
                    # ⛔ round-19（Codex round-16 LOW）：措辞要跟判据一样宽，⛔ 不多不少。
                    # 这条规则**故意**连 `obj.MUTATIONS`（`Attribute.attr`）与 `f(MUTATIONS=7)`
                    # （`keyword.arg`）一起拒 —— 那两个**并不**重绑本模块的 `MUTATIONS`。
                    # 保持这么宽是有意的（实测四套命中 0 处，收紧只会重新打开面），但
                    # **不能把「一律不认」说成「它是一次重绑定」**。
                    raise ReconcileError(
                        f"{source_name}:{getattr(node, 'lineno', '?')} `MUTATIONS` 出现在 "
                        f"`{type(node).__name__}.{field}` 这个**名字位**上（不是读取位）—— "
                        f"⛔ 一律不认：这里**可能**是一次重绑定，也可能只是同名的属性/关键字名，"
                        f"本函数不去分辨（分辨不出来就数不出来）"
                    )
        if isinstance(node, ast.Name) and node.id == "MUTATIONS" and isinstance(node.ctx, (ast.Store, ast.Del)):
            if id(node) not in counted_targets:
                raise ReconcileError(
                    f"{source_name}:{node.lineno} 有**未被计数**的 `MUTATIONS` 写入"
                    f"（嵌套块 / 循环 / 函数内 / 链式赋值）—— 分母数不出来，⛔ 不得少算蒙混"
                )
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "MUTATIONS":
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                raise ReconcileError(
                    f"{source_name}:{node.lineno} 用 `MUTATIONS[...] = …` / `del MUTATIONS[...]` 改表，分母数不出来"
                )
        if isinstance(node, ast.Name) and node.id == "MUTATIONS" and isinstance(node.ctx, ast.Load):
            # ⛔⛔ round-15（Codex round-12 MEDIUM）：**读**也要按白名单收。
            # 上一轮只禁了 `MUTATIONS.<属性>`，于是换成**不经属性**的路子照样改表：
            #   `list.append(MUTATIONS, 4)`（把它当**实参**传给未绑定方法）
            #   `alias = MUTATIONS; alias.append(4)`（换个名字，根 Name 就不叫 MUTATIONS 了）
            # ⇒ 逐个堵入口这条路已经走到头（这是第五次换入口）。改成：**只认三种语境**，
            # 其余一律抛。实测四套源码对 `MUTATIONS` 的 Load 只有这三种（各 23/12/11 处）：
            #   · 推导式 / `for` 的迭代对象；· `len(MUTATIONS)`；· Load 下标。
            # ⛔ round-16（Codex round-13 MEDIUM）：上一版这两条白名单**没核操作数的位置**，
            # 于是同一个语法形状里换个位子就通：
            #   · `Sink()[MUTATIONS]` —— `MUTATIONS` 在**下标**位而不是被下标的对象，
            #     `Sink.__getitem__` 拿到的就是原列表（实测运行时 4 条、AST 数 3 条）；
            #   · `len(MUTATIONS)` —— `len` 被模块自己重定义（见上面 `bound_names`）。
            # ⇒ 两条都补上「这个 `MUTATIONS` 到底站在哪个操作数位」/「这个函数到底是谁」。
            # ⛔ round-19（Codex round-16 MEDIUM）：推导式这一条要分**急/惰**。
            # `[x for x in MUTATIONS]` / `{…}` / `{k: v …}` 是**当场求值**的，求完没有活着的帧；
            # 而**生成器表达式** `(x for x in MUTATIONS)` 把 `iter(MUTATIONS)` 存在自己的帧里
            # （`gi_frame.f_locals[".0"]`），于是
            #   `it = (x for x in MUTATIONS); it.gi_frame.f_locals[".0"].__reduce__()[1][0].append(4)`
            # 就能拿回原列表（实测运行时 4 条、上一版 AST 数 3 条）。
            # ⇒ 生成器表达式**只在它没有被绑走**时才认：父节点必须是 `Call`（当实参传出去、
            #   调用返回后那个生成器对象再也够不着）。`it = (…)` 的父节点是 `Assign` ⇒ 抛。
            # ⚠️ 实测四套的三处生成器表达式**全部**是直接实参（`sorted(…)` / `next(…)` /
            #   `collections.Counter(…)`），所以这条不挡现有写法；⚠️ 故意**不**再要求
            #   「被调用者是消耗型内建」—— `collections.Counter` 是 `Attribute`，那样写会把 g32b 打死。
            par = parent.get(id(node))
            _comp_owner = parent.get(id(par)) if isinstance(par, ast.comprehension) else None
            ok = (
                (
                    isinstance(par, ast.comprehension)
                    and par.iter is node
                    and (
                        isinstance(_comp_owner, (ast.ListComp, ast.SetComp, ast.DictComp))
                        or (
                            isinstance(_comp_owner, ast.GeneratorExp)
                            and isinstance(parent.get(id(_comp_owner)), ast.Call)
                        )
                    )
                )
                or (isinstance(par, ast.For) and par.iter is node)
                or (
                    isinstance(par, ast.Call)
                    and getattr(par.func, "id", None) == "len"
                    and _len_is_builtin
                    and node in par.args
                )
                or (isinstance(par, ast.Subscript) and isinstance(par.ctx, ast.Load) and par.value is node)
            )
            if not ok:
                raise ReconcileError(
                    f"{source_name}:{node.lineno} `MUTATIONS` 出现在**未白名单**的语境里"
                    f"（父节点 {type(par).__name__}）—— 它可能被传走/改名后就地改表，分母数不出来"
                )
        if isinstance(node, ast.Attribute):
            # ⛔⛔ round-14（Codex round-11 MEDIUM）：**对 `MUTATIONS` 的属性访问整族禁掉**。
            # 「白名单」这条路被连着绕开三次，每次换个入口：
            #   `MUTATIONS.__imul__` → `MUTATIONS.__class__.__imul__` →
            #   `MUTATIONS.copy.__self__` → `MUTATIONS.__iter__().__reduce__()[1][0]`
            # 最后那个的属性链**以调用表达式为根**，「顺链找根 Name」根本够不着 ——
            # 只要允许**任何**属性访问，就总能再找到一条通往原列表的路。
            # ⇒ 停止逐个堵入口，改封**整个面**：本函数的承诺是「静态数得出条数」，而
            # `MUTATIONS.<任何属性>` 都数不出来。
            # ⚠️ 实测四套源码对 `MUTATIONS` 的属性访问**各 0 处**（`len()` / `for m in
            # MUTATIONS` / 下标读都不走属性），所以这条禁令不挡任何现有合法写法。
            cur: ast.AST = node
            while isinstance(cur, ast.Attribute):
                cur = cur.value
            if isinstance(cur, ast.Name) and cur.id == "MUTATIONS":
                raise ReconcileError(
                    f"{source_name}:{node.lineno} 对 `MUTATIONS` 做了属性访问 —— "
                    f"⛔ 一律不认（任何属性都可能通往原列表），分母数不出来"
                )

    if total is None:
        raise ReconcileError(f"{source_name} 里找不到模块级 `MUTATIONS = [...]`，分母无法独立现算")
    return total


# ── 形态一：g32cb / g32ccr1 的 stdout 汇总段 ────────────────────────────────
#
# 实测形态（g32cb :582-603 / g32ccr1 :462-482），两空格缩进、**计数在档名之前**：
#     «2 空格»9/9 KILLED (绑定: 消息 + 失败位置在门文件内; …)
#     «2 空格»KILLED-UNBOUND: 0 (仅证明指定门红了)
#     …
#     «2 空格»六档之和: 9 (应 = 变异条数 9) ✓

_CB_KILLED = re.compile(r"^ {2}(?P<n>\d+)/(?P<m>\d+) KILLED \(", re.M)
#: ⛔ 计数必须是**整 token**：`(?=[\s(]|$)` 要求它后面紧跟空白 / `(` / 行尾。
#: 只写 `(?![\d.])`（round-2 的写法）挡得住 `0.5` 却挡不住 `0x10`（`x` 既非数字也非点）
#: —— `\d+` 仍取到前缀 `0`，非法 token 的整数前缀静默通过对账（Codex round-3 MEDIUM）。
#: `_nonneg_int` 只覆盖 JSON 那条路，stdout 这条只能靠正则自己把边界钉死。
_CB_FIVE = re.compile(rf"^ {{2}}(?P<name>{_TAIL_FIVE}): (?P<n>\d+)(?=[\s(]|$)", re.M)
_CB_SUM = re.compile(r"^ {2}六档之和: (?P<t>\d+) \(应 = 变异条数 (?P<m>\d+)\)", re.M)

# ── 形态二：g32b 的 stdout 汇总段 ───────────────────────────────────────────
#
# 实测形态（g32b :3019-3041），**不缩进**、计数在冒号之后：
#     KILLED (绑定断言身份: 位置 [+ 消息]): 6/6
#     KILLED-UNBOUND (仅证明指定门红了, 位置与消息都没绑): 0
#     KILLED 合计 (两者之和, **不等于**「全部被指定断言杀死」): 6/6   ⛔ 不是六档之一
#     SURVIVED: 0
#     …
#     六档之和: 6 (应 = 6) ✓            ⛔ 括注里**没有**「变异条数」字样

_B_KILLED = re.compile(r"^KILLED \(绑定断言身份: [^)]*\): (?P<n>\d+)/(?P<m>\d+)\s*$", re.M)
_B_UNBOUND = re.compile(r"^KILLED-UNBOUND \([^)]*\): (?P<n>\d+)\s*$", re.M)
_B_FOUR = re.compile(r"^(?P<name>SURVIVED|HARNESS-ERROR|ANCHOR-ERROR|SYNTAX-INVALID): (?P<n>\d+)(?=[\s(]|$)", re.M)
_B_SUM = re.compile(r"^六档之和: (?P<t>\d+) \(应 = (?P<m>\d+)\)", re.M)

#: 逐条裁决行里的档名 —— ⛔ **按套写**，与聚合段同理。
#: ⚠️ 准确说是**两组**（round-12 LOW）：`g32cb` / `g32ccr1` 同形，`g32b` 自成一组。
#:
#: ⛔ **必须锚到行结构**（Codex round-8 MEDIUM）：只锚一个 `⇒ <档名>` 会把 **why 里的
#: 诊断文字**也数进去 —— `⇒ SURVIVED (红在别的断言上: 实见 ['diagnostic ⇒ KILLED'])`
#: 会被数成 SURVIVED 1 + KILLED 1，于是**合法**存档反而对账失败（假红）。而 why 由被测
#: 进程的断言消息拼出来，**内容被测进程可控** —— 让它能影响计数本身就是个口子。
#: ⛔ `(?![\w-])` 收右边界，否则 `KILLED` 会把 `KILLED-UNBOUND` 吃掉一半。
_VERDICT_ALT = "KILLED-UNBOUND|KILLED|" + _TAIL_FIVE.split("|", 1)[1]

#: `g32cb` / `g32ccr1`：`«缩进»<nodeid> → rc=<n> ⇒ <档名> (<why>)`。
#: ⛔ **必须锚到行首**（`^` + `re.M`，Codex round-9 MEDIUM；⚠️ 只锚行首不锚行尾 ——
#: 行尾还有 `(why)`，锚 `$` 会一条都匹配不上。round-12 LOW 指出上一版注释写成
#: 「`^…$` 整行锚定」，说得比代码宽）：只锚 `rc=<n> ⇒` 仍可被
#: **why 里的诊断文字**注入 —— 断言消息里塞一句 `diagnostic rc=1 ⇒ KILLED` 就能让 9 条被
#: 数成 10 条，于是**合法**存档反而对账假红。why 由被测进程拼出、内容它可控，所以判据
#: 不能只靠「附近有没有某个片段」，必须靠**这一行整体长什么样**。
#: 形态：行首若干空格 + nodeid（无空白）+ ` → rc=<n> ⇒ <档名>` + 空格/`(`/行尾。
_PER_ITEM_CB = re.compile(rf"^\s*\S+ → rc=-?\d+ ⇒ (?P<name>{_VERDICT_ALT})(?=[ (]|$)", re.M)

#: `g32b`：`[<tag>] <gate> → <档名> …（本卡只读其源码实测 `_label` 的构造）。
#: ⛔ 它的形态与上面**完全不同**（`→` 不是 `⇒`、无 `rc=`），而且 `SURVIVED` 的标签里
#: **自带一个 `⇒`**（`SURVIVED ⇒ 假门 (…)`）—— 拿 `⇒` 去锚它会同时漏数和错数。
#: 上一版只有一条 `⇒` 正则 ⇒ 对 g32b **零命中** ⇒ 整个「聚合 vs 逐条」这一维**静默**
#: 降级成「未核」（Codex round-9 提问②指的就是这个面）。
_PER_ITEM_B = re.compile(rf"^\[[^\]]+\] \S+ → (?P<name>{_VERDICT_ALT})(?=[ (]|$)", re.M)


def _one(rx: re.Pattern[str], text: str, what: str, suite: str) -> re.Match[str]:
    """整份存档里该形态必须**恰好命中一次**。

    ⛔ 0 次 = 正则写错或该套没印出来 ⇒ 报错，不得当「缺省 0」；
    ⛔ >1 次 = 存档里混了两次跑的输出，逐档硬比会拿错一次的数字。
    """
    hits = rx.findall(text)
    if len(hits) != 1:
        raise ReconcileError(f"{suite}: 存档里「{what}」命中 {len(hits)} 次(应为 1) —— 正则 {rx.pattern!r}")
    m = rx.search(text)
    assert m is not None  # findall 命中 1 次 ⇒ search 必命中
    return m


def _nonneg_int(v: object, what: str, suite: str) -> int:
    """必须是**非负整数**（⛔ `bool` 不算 —— Python 里 `True` 是 `int` 的子类）。

    JSON 存档里的数字类型不受正则约束：`18.9` 被 `int()` 悄悄截断成 18、`-1` 原样收下
    并在求和时与别的档**互相抵消**，两种都能凑出与 AST 分母相等的假绿（Codex round-1 MEDIUM）。
    """
    if isinstance(v, bool) or not isinstance(v, int):
        raise ReconcileError(f"{suite}: `{what}` 不是整数（实得 {v!r}）—— ⛔ 不得 int() 截断后继续比")
    if v < 0:
        raise ReconcileError(f"{suite}: `{what}` 为负数 {v} —— ⛔ 负数会在求和时与别的档互相抵消")
    return v


def _put(counts: dict[str, int], name: str, value: str, suite: str) -> None:
    """记一档；⛔ **同一档出现第二次即报错，不得静默覆盖**。

    Codex round-1 MEDIUM：`finditer` 循环里直接 `counts[name] = ...` 时，存档里若混入
    第二条同形的 `SURVIVED: 7`（手改、或两次跑的输出被拼到一份 tee 里），后写的那条会
    **悄悄盖掉**前一条，对账照样通过 —— 这五档从来没经过 `_one()` 的「恰好一次」把关，
    于是「存档里有互相冲突的计数」这件事完全不显形。
    """
    if name in counts:
        raise ReconcileError(f"{suite}: 存档里「{name}」出现了不止一次(应恰好 1 次) —— ⛔ 冲突计数不得静默覆盖")
    counts[name] = int(value)


def parse_stdout(suite: str, text: str) -> Parsed:
    """解析三套 stdout 汇总段。

    ⛔ **口径更正（Codex round-6 LOW）**：此前写「三套形态互异」—— 实测是**两组**：
    `g32cb` 与 `g32ccr1` 的汇总段逐字同形（共用 `_CB_*` 正则），`g32b` 自成一组（`_B_*`）。
    分支仍按套写（省得下次某套改了格式时三套一起错），但**不得再声称三套互异**。
    """
    counts: dict[str, int] = {}
    if suite == "g32b":
        mk = _one(_B_KILLED, text, "KILLED 行", suite)
        counts["KILLED"] = int(mk.group("n"))
        declared_m = int(mk.group("m"))
        counts["KILLED-UNBOUND"] = int(_one(_B_UNBOUND, text, "KILLED-UNBOUND 行", suite).group("n"))
        for m in _B_FOUR.finditer(text):
            _put(counts, m.group("name"), m.group("n"), suite)
        ms = _one(_B_SUM, text, "六档之和行", suite)
    else:
        mk = _one(_CB_KILLED, text, "KILLED 行", suite)
        counts["KILLED"] = int(mk.group("n"))
        declared_m = int(mk.group("m"))
        for m in _CB_FIVE.finditer(text):
            _put(counts, m.group("name"), m.group("n"), suite)
        ms = _one(_CB_SUM, text, "六档之和行", suite)
    missing = [v for v in VERDICT_NAMES if v not in counts]
    if missing:
        raise ReconcileError(f"{suite}: 存档里解析不到这些档 {missing} —— ⛔ 缺档不得当成 0/「一致」")
    # ⚠️ KILLED 行与「六档之和」行各自带一个分母；两者不一致说明存档被改过。
    sum_m = int(ms.group("m"))
    if sum_m != declared_m:
        raise ReconcileError(f"{suite}: 该套自称的分母自相矛盾（KILLED 行 {declared_m} vs 六档之和行 {sum_m}）")
    # ⛔ 逐条裁决记录是**第二个来源**（见 `Parsed.per_item`）。存档里没有逐条行时留 None ——
    # ⚠️ 留 None 意味着这一维**没核**，绝不能当成「核过且一致」（那正是本工具在骂的那种话）。
    per = {v: 0 for v in VERDICT_NAMES}
    hits = (_PER_ITEM_B if suite == "g32b" else _PER_ITEM_CB).findall(text)
    for name in hits:
        per[name] += 1
    return Parsed(counts, int(ms.group("t")), declared_m, per if hits else None)


def parse_json(suite: str, text: str) -> Parsed:
    """解析 g33 的 `--json` 存档（实测只有 g33 有 `verdict_counts` / `total`）。"""

    def _no_dup(pairs: list[tuple[str, object]]) -> dict[str, object]:
        """⛔ JSON **重复键**不得被后值静默覆盖（Codex round-2 MEDIUM）。

        `json.loads` 默认保留最后一个同名键，于是 `"SURVIVED":5,"SURVIVED":0` 与
        `"total":5,"total":18` 都能悄悄凑出一份「自洽」的存档并通过逐档硬比 ——
        「存档里有互相冲突的数字」这件事完全不显形，与 stdout 侧的 `_put()` 同型。
        """
        seen: dict[str, object] = {}
        for k, v in pairs:
            if k in seen:
                raise ReconcileError(f"{suite}: JSON 存档里键 `{k}` 出现了不止一次 —— ⛔ 冲突值不得静默覆盖")
            seen[k] = v
        return seen

    try:
        data = json.loads(text, object_pairs_hook=_no_dup)
    except ReconcileError:
        raise
    except json.JSONDecodeError as exc:
        raise ReconcileError(f"{suite}: JSON 存档解析不了 —— {exc}") from exc
    if not isinstance(data, dict):
        raise ReconcileError(f"{suite}: JSON 存档顶层不是对象")
    raw = data.get("verdict_counts")
    if not isinstance(raw, dict):
        raise ReconcileError(f"{suite}: JSON 存档缺 `verdict_counts` 字段 —— ⛔ 缺字段不得当成「一致」")
    missing = [v for v in VERDICT_NAMES if v not in raw]
    if missing:
        raise ReconcileError(f"{suite}: `verdict_counts` 缺这些档 {missing} —— ⛔ 缺档不得当成 0/「一致」")
    # ⛔ round-14（Codex round-11 MEDIUM）：**多出来的档键也要抛**。上一版只按六个已知键
    # 取值，于是往存档里加一个 `"UNEXPECTED-VERDICT": 1` 就被**静默忽略** —— 存档自己的
    # 计数和是 19，本工具却按 18 去跟 AST 分母比，照样打 ✓。缺档不许当 0，多档同样不许
    # 当不存在：两边都是「没看见的东西当成没有」。
    extra = [k for k in raw if k not in VERDICT_NAMES]
    if extra:
        raise ReconcileError(
            f"{suite}: `verdict_counts` 里有**不认识**的档 {sorted(extra)} —— "
            f"⛔ 多出来的档不得静默忽略（它会让六档之和与存档实际计数对不上）"
        )
    total = _nonneg_int(data.get("total"), "total", suite)
    # ⛔ Codex round-1 MEDIUM：`int(raw[v])` 会把 `18.9` **截断**成 18、把 `-1` 原样收下，
    # 于是「KILLED=18.9」或「KILLED=19, SURVIVED=-1」都能凑出 AST 分母 18 而判绿。
    # 逐档硬比的前提是每一档本身就是个**非负整数**；不是就别往下比。
    counts = {v: _nonneg_int(raw[v], f"verdict_counts.{v}", suite) for v in VERDICT_NAMES}
    # g33 自己印的「六档之和」在 stdout；JSON 侧它把结论存成布尔 `verdict_sum_matches_total`。
    # ⛔ 不拿这个布尔当「六档之和」用 —— 它是该套**自己的结论**，不是可交叉核对的数字。
    # JSON 形态下「该套自己印出来的和」以 `sum(verdict_counts)` 为准（那是它写进存档的
    # 六个数字本身），独立性由 AST 分母那一维承担。
    declared_sum_ok = data.get("verdict_sum_matches_total")
    if declared_sum_ok is not None and not isinstance(declared_sum_ok, bool):
        raise ReconcileError(f"{suite}: `verdict_sum_matches_total` 形态不对（应为布尔）")
    # ⛔ JSON 形态下「该套自己印的和」只能取 `sum(counts)` ⇒ 判据①（逐档相加 == 印出来的和）
    # 对它是**恒真**的。这一维靠 `results[]` 里的逐条 `verdict` 补上（第二个来源）。
    # ⛔ Codex round-8 MEDIUM：「字段**缺席**」与「字段**在但形态错**」是两回事。
    # 上一版把两者一起降级成「未核」⇒ 把 `results` 改成 `"broken"` / `{}` 就能让这一维
    # 静默消失并照样打 ✓ —— 又一个「没检查到当成通过」。缺席 ⇒ 未核（如实说）；
    # 形态错 ⇒ **抛**。
    per: dict[str, int] | None = None
    if "results" in data:
        raw_results = data["results"]
        if not isinstance(raw_results, list):
            raise ReconcileError(
                f"{suite}: `results` 在但不是数组（实得 {type(raw_results).__name__}）—— 形态错不得降级成「未核」"
            )
        if raw_results:
            per = {v: 0 for v in VERDICT_NAMES}
            for item in raw_results:
                if not isinstance(item, dict):
                    raise ReconcileError(f"{suite}: `results[]` 里有非对象条目 {item!r}")
                v = item.get("verdict")
                if v not in per:
                    raise ReconcileError(f"{suite}: `results[]` 里有不认识的 verdict {v!r}")
                per[v] += 1
    return Parsed(counts, sum(counts.values()), total, per)


# ── 对账 ────────────────────────────────────────────────────────────────────


def reconcile_one(suite: str, path: Path) -> list[str]:
    """核一套；返回问题列表（空 = 该套对得上）。"""
    cfg = SUITES[suite]
    if not path.exists():
        raise ReconcileError(f"{suite}: 声明了要核，但输入文件不存在 {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_stdout(suite, text) if cfg.form == "stdout" else parse_json(suite, text)
    ast_n = ast_mutation_count(cfg.source)
    own_sum = sum(parsed.counts.values())
    problems: list[str] = []
    if own_sum != parsed.printed_total:
        problems.append(
            f"{suite}: 逐档相加 {own_sum} ≠ 该套印出来的六档之和 {parsed.printed_total} "
            f"—— 存档里某一档的计数与和行对不上"
        )
    if parsed.printed_total != parsed.declared_m:
        problems.append(
            f"{suite}: 六档之和 {parsed.printed_total} ≠ 该套自称的分母 {parsed.declared_m} —— 有条目跑完没落进任何一档"
        )
    if parsed.declared_m != ast_n:
        problems.append(
            f"{suite}: 该套自称的分母 {parsed.declared_m} ≠ 源码 AST 现算的变异条数 {ast_n} "
            f"—— 部分跑冒充全量, 或 MUTATIONS 已漂移（⛔ 这一条是唯一的跨源独立判据）"
        )
    # ⛔ 第五条：聚合 vs **逐条**。前四条全看聚合那一个来源，于是**补偿式篡改**
    # （KILLED 9→8 同时 SURVIVED 0→1，和不变）四数全对得上 —— 只有把逐条裁决记录
    # 数一遍才看得见。⚠️ 没有逐条记录时**如实说「未核」**，不得沉默略过。
    if parsed.per_item is None:
        print(f"     ⚠️ {suite}: 存档里没有逐条裁决记录 —— 「聚合 vs 逐条」这一维**未核**")
    else:
        mismatched = {
            v: (parsed.counts[v], parsed.per_item[v]) for v in VERDICT_NAMES if parsed.counts[v] != parsed.per_item[v]
        }
        if mismatched:
            problems.append(
                f"{suite}: 聚合计数与**逐条**裁决记录对不上 {mismatched}（格式 档: 聚合 vs 逐条）"
                f" —— 补偿式篡改只有这一维看得见"
            )
    print(f"── {suite}（{cfg.form} 形态, 存档 {path.name}）")
    for v in VERDICT_NAMES:
        print(f"     {v:15} {parsed.counts[v]}")
    print(
        f"     逐档相加={own_sum} 该套印的六档之和={parsed.printed_total} "
        f"该套自称分母={parsed.declared_m} AST 现算条数={ast_n} "
        f"逐条记录={sum(parsed.per_item.values()) if parsed.per_item else '未核'} "
        f"{'✓' if not problems else '⛔ 对不上'}"
    )
    return problems


def _kv(pairs: list[str], flag: str) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for raw in pairs:
        if "=" not in raw:
            raise SystemExit(f"⛔ {flag} 须写成 `<套名>=<路径>`，实得 {raw!r}")
        name, _, p = raw.partition("=")
        if name not in SUITES:
            raise SystemExit(f"⛔ {flag} 里的套名 {name!r} 不认识（可选: {', '.join(SUITES)}）")
        if name in out:
            raise SystemExit(f"⛔ {flag} 给了两次 {name!r}")
        out[name] = Path(p)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--expect", required=True, help="本次应核哪几套（逗号分隔）")
    ap.add_argument("--stdout", action="append", default=[], metavar="套名=路径", help="该套 run 的 tee .txt")
    ap.add_argument("--json", action="append", default=[], metavar="套名=路径", help="该套 --json 存档")
    args = ap.parse_args(argv)

    expect = [s.strip() for s in args.expect.split(",") if s.strip()]
    if not expect:
        raise SystemExit("⛔ --expect 不得为空 —— 空声明会让这道门变成恒真")
    unknown = [s for s in expect if s not in SUITES]
    if unknown:
        raise SystemExit(f"⛔ --expect 里的套名不认识: {unknown}（可选: {', '.join(SUITES)}）")
    # ⛔ Codex round-8 LOW：`--expect g33,g33` 会把**同一份来源**核两遍，然后报「2 套一致」——
    # 把覆盖面说得比实际宽。重复声明一律拒。
    dupes = sorted({x for x in expect if expect.count(x) > 1})
    if dupes:
        raise SystemExit(f"⛔ --expect 里重复声明了 {dupes} —— 同一来源核两遍不等于核了两套")

    stdout_in = _kv(args.stdout, "--stdout")
    json_in = _kv(args.json, "--json")
    inputs: dict[str, Path] = {}
    problems: list[str] = []
    for suite in expect:
        want = SUITES[suite].form
        given = stdout_in if want == "stdout" else json_in
        other = json_in if want == "stdout" else stdout_in
        if suite in other:
            # ⛔ 形态喂错必须报错而不是「试着解析看看」：g32b 没有 --json，
            # 拿 stdout 当 JSON 解析失败会被误读成「存档坏了」而不是「口径错了」。
            problems.append(f"{suite}: 该套是 {want} 形态，却用 --{'json' if want == 'stdout' else 'stdout'} 喂入")
            continue
        if suite not in given:
            # ⛔ MEDIUM③ 的核心：声明了却没给输入**不得**静默判「一致」。
            problems.append(f"{suite}: --expect 声明了要核，却没给 --{want} 输入 —— ⛔ 缺席不是「一致」")
            continue
        inputs[suite] = given[suite]

    extra = sorted((set(stdout_in) | set(json_in)) - set(expect))
    if extra:
        problems.append(f"给了输入却没在 --expect 里声明: {extra} —— 声明与输入必须一一对应")

    print(f"== 六档处置表跨套硬比（声明核 {len(expect)} 套: {', '.join(expect)}）==")
    for suite in expect:
        if suite not in inputs:
            continue
        try:
            problems.extend(reconcile_one(suite, inputs[suite]))
        except ReconcileError as exc:
            problems.append(str(exc))

    if problems:
        print("\n⛔ 对账不通过:")
        for p in problems:
            print(f"   · {p}")
        raise SystemExit(1)
    print(f"\n✓ {len(expect)} 套六档逐档硬比一致，且各套自称分母 == 源码 AST 现算条数")
    return 0


if __name__ == "__main__":
    sys.exit(main())
