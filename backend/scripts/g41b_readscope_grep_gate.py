#!/usr/bin/env python3
"""CARD-G4-1b grep 门 — `neo4j_client.py` 内不得残留"无 group 的业务读"。

> 批次: BATCH-2026-08-31-第七批 / 车道 V1
> 契约: `.claude/rules/cypher-read-contract.md` R1 / R4

为什么不是一行 `grep`
--------------------
卡文要求的判据是"**业务读**是否带 group 过滤"。裸 grep 做不到三件事:

1. **区分读与写**。写侧归 `cypher-write-contract.md` 的 W1-W5 管, 用同一条
   grep 会把 `MERGE (c:Concept {name, group_id})` 也报成违规;
2. **认出 f-string 拼进去的过滤**。本卡的过滤片段来自
   `read_group_filter(alias)`, 在源码里是 `{read_group_filter("c")}` 而不是
   字面的 `c.group_id = $group_id` —— 按后者 grep 会**全部漏报**(0 命中被
   当成"没有违规", 正是"把没有发生当成验证通过"的经典假绿);
3. **认出显式豁免**。`@allow_cross_vault` 标注的跨 vault 读是合规的。

所以本门走 AST: 找出模块里所有含 `MATCH (` 的查询字符串 (含 f-string),
判定它是读还是写, 读的那些必须在**所属方法内**出现 group 过滤证据
(方法级而非字符串级 —— 增量拼接的查询过滤在后续语句里)。

用法
----
    cd backend && .venv/bin/python scripts/g41b_readscope_grep_gate.py
    # 退出码 0 = 无违规; 1 = 有违规(逐条打印); 2 = 门自身失效

自检 (门自身的验伪)
------------------
"报了 0 违规"可能有两种原因: 真的没有违规, 或者**门根本没扫到那条查询**。
后者实测发生过 (裸子串 CREATE 命中 created_at, 整条读查询被当成写跳过)。
所以门不只看违规数, 还锁死**它究竟检查了哪些方法**: 扫描结果的方法名集合
必须与 `EXPECTED_READ_METHODS` 逐字相等, 不等即退出码 2。新增/删除读方法时
必须同步这份清单 —— 这正是让人"意识到自己动了读面"的地方。
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
TARGET = BACKEND / "app" / "clients" / "neo4j_client.py"

#: 业务数据标签/关系类型 —— 出现即视为"读了业务数据"。
BUSINESS_TOKENS = (
    ":Concept",
    ":Canvas",
    ":Node",
    ":Episode",
    ":LearningNode",
    ":EntityNode",
    ":LEARNED",
    ":ASSOCIATED_WITH",
    ":CONTAINS_NODE",
    ":CONTAINS",
    ":HAS_CONCEPT",
    ":SCORED",
)

#: 写关键字 —— 含之即归写契约 (W1-W5) 管辖, 不在本读门范围。
#:
#: ⚠️ **必须按词边界匹配**。自检时实测: 裸子串 `"CREATE" in query.upper()` 会被
#: `RETURN r.created_at as created_at` 里的 `CREATED_AT` 命中, 于是
#: `get_canvas_associations` 整条**读**查询被误判成"写"而**静默跳过**读门 ——
#: 门报了 0 违规, 但它根本没检查那条查询。判据自身的假阳/假阴必须单独验伪,
#: 不能只看它报了 0 (MEMORY: 写门的五个陷阱 —— 把"没有发生"当成"验证通过")。
WRITE_KEYWORD_RE = re.compile(r"\b(MERGE|CREATE|DELETE|SET)\b")

#: 门自身的验伪锚 —— 本门**应当**检查到的业务读方法全集 (CARD-G4-1b 收口后)。
#: 集合不等即判门失真: 要么有人新增了读方法没登记, 要么判据把某条读漏掉了。
EXPECTED_READ_METHODS = frozenset(
    {
        "get_review_suggestions",
        "get_concept_history",
        "get_learning_history",
        "get_concept_score_history",
        "get_canvas_associations",
        "get_canvas_concepts",
        "find_common_concepts",
        "get_all_recent_episodes",
    }
)

#: group 过滤的证据形态 (两种都算合规, 见 R1「实现手段不限, 语义等价即合规」)。
FILTER_EVIDENCE = (
    "read_group_filter(",  # 本卡统一形态 (f-string 拼接)
    ".group_id = $group_id",  # 等价手写 WHERE
    "group_id: $group",  # map 形式 {group_id: $groupId}
    "group_id: $g",
)


def _literal_parts(node: ast.AST) -> str:
    """把 Constant / JoinedStr 还原成"源码可见的文本"。

    f-string 里的 `{read_group_filter("c")}` 在 AST 里是 FormattedValue,
    没有字面文本 —— 用 ast.unparse 还原表达式源码, 这样 FILTER_EVIDENCE 才
    认得出它。漏掉这一步会让所有 f-string 查询被判成"无过滤"(假红) 或
    在只匹配字面量时被整体跳过(假绿)。
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                out.append(part.value)
            elif isinstance(part, ast.FormattedValue):
                out.append("{" + ast.unparse(part.value) + "}")
        return "".join(out)
    return ""


_owner_lineno: dict[int, int] = {}


def main() -> int:
    _owner_lineno.clear()
    src = TARGET.read_text()
    tree = ast.parse(src)

    # 每个 lineno 归属的**外层函数**信息:
    #   exempt      —— 该函数挂了 @allow_cross_vault (显式跨 vault 豁免)
    #   has_filter  —— 该函数体内**任何位置**出现过滤证据
    #
    # ⚠️ 判定单位是"方法"而不是"字符串", 因为 `get_learning_history` 这类是
    # **增量拼接**查询: 字面量里只有 `MATCH ... WHERE 1=1`, 过滤是后面
    # `query += f" AND {read_group_filter('r')} ..."` 加上去的。只看字符串会
    # 把它误报成违规。代价是本门管不到"逐 alias 是否齐全" —— 那由门 7 的
    # 逐 alias 行为门与单测的分段断言负责, 两者分工明确, 不重复也不留空。
    exempt_lines: set[int] = set()
    filtered_lines: set[int] = set()
    owner: dict[int, str] = {}
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body_src = ast.unparse(fn)
        marked = any("allow_cross_vault" in ast.unparse(d) for d in fn.decorator_list)
        has_filter = any(ev in body_src for ev in FILTER_EVIDENCE)
        for sub in ast.walk(fn):
            lineno = getattr(sub, "lineno", None)
            if lineno is None:
                continue
            # 嵌套函数: 最内层 (行数最大的 def) 覆盖外层, 与 Python 作用域一致
            if lineno not in owner or fn.lineno > _owner_lineno.get(lineno, -1):
                owner[lineno] = fn.name
                _owner_lineno[lineno] = fn.lineno
            if marked:
                exempt_lines.add(lineno)
            if has_filter:
                filtered_lines.add(lineno)

    # docstring 节点 (里面常有"示例 Cypher", 不是真的发出去的查询)
    docstrings: set[int] = set()
    for holder in ast.walk(tree):
        if isinstance(holder, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(holder, "body", None)
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                docstrings.add(id(body[0].value))

    # ⚠️ 必须**自顶向下且不下钻 JoinedStr**: `ast.walk` 会把 f-string 内部的
    # Constant 片段当成独立字符串再访问一次, 那些片段里当然没有
    # `{read_group_filter(...)}` —— 按片段判定会把每条合规的 f-string 查询
    # 都报成违规(假红), 反过来也可能因为片段太碎而漏掉整体(假绿)。
    candidates: list[ast.AST] = []

    def _collect(node: ast.AST) -> None:
        if isinstance(node, ast.JoinedStr):
            candidates.append(node)
            return  # 不下钻
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstrings:
                candidates.append(node)
            return
        for child in ast.iter_child_nodes(node):
            _collect(child)

    _collect(tree)

    reads = 0
    scanned_methods: set[str] = set()
    violations = []
    for node in candidates:
        text = _literal_parts(node)
        if "MATCH (" not in text:
            continue
        if not any(tok in text for tok in BUSINESS_TOKENS):
            continue
        if WRITE_KEYWORD_RE.search(text.upper()):
            continue  # 写查询 → 归 W1-W5
        reads += 1
        scanned_methods.add(owner.get(node.lineno, "<module>"))
        if node.lineno in exempt_lines:
            continue
        if any(ev in text for ev in FILTER_EVIDENCE):
            continue
        if node.lineno in filtered_lines:
            continue  # 增量拼接: 过滤在同一方法的后续语句里
        violations.append((node.lineno, text.strip().splitlines()[0][:100]))

    print(f"扫描 {TARGET.relative_to(BACKEND)}: 业务读查询 {reads} 条, 覆盖方法 {len(scanned_methods)} 个")
    if reads == 0:
        print(
            "⛔ 门失效: 一条业务读都没扫到 —— '零违规'不可信 (BUSINESS_TOKENS / 解析逻辑与源码脱节?)",
            file=sys.stderr,
        )
        return 2
    if scanned_methods != set(EXPECTED_READ_METHODS):
        print(
            "⛔ 门失真: 实际检查到的读方法集合与 EXPECTED_READ_METHODS 不符\n"
            f"   漏检(门没看到): {sorted(set(EXPECTED_READ_METHODS) - scanned_methods)}\n"
            f"   新增(未登记): {sorted(scanned_methods - set(EXPECTED_READ_METHODS))}",
            file=sys.stderr,
        )
        return 2
    if violations:
        print(f"⛔ 无 group 过滤的业务读 {len(violations)} 条:", file=sys.stderr)
        for lineno, head in violations:
            print(f"   {TARGET.name}:{lineno}  {head}", file=sys.stderr)
        return 1
    print("✅ 无残留: 每条业务读都带 group 过滤 (或已 @allow_cross_vault 显式豁免)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
