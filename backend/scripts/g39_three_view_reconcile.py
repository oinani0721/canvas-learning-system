#!/usr/bin/env python3
"""CARD-G3-9 [BATCH-2026-09-11-第十四批] — picker / Dashboard / 总览页 三面机器对账。

G3 退出门收口: 验「三面从**同一份** `今日复习.json` 派生出的卡片数 / 板集 /
板级到期数 / 排序逐项相同」。三面定义:

  ① picker   = `scripts/daily_review_pick.py` 产出的 `<vault>/outputs/今日复习.json`
               (schema v3)。本脚本只**读**该文件, 不跑生产器。
  ② Dashboard= `canvas-vault/Dashboard.md` 的 DataviewJS 归约块 —— 本脚本在
               Python 里**重算**它 (见 `dashboard_recompute`), 因为 md 里的 JS
               只在 Obsidian 运行期存在, 机器对账拿不到它的运行结果。
  ③ overview = `GET /api/v1/review/overview` (`review_overview.py`) 的 per-vault
               entry。只对**已在运行**的后端只读 GET; 本脚本不启动后端。

⛔ 只读 / 零库连接: 全文件只用标准库, 不导入后端应用包, 不连图数据库 / 向量库
   (禁用端口与库名见卡文 §三 硬边界), 不启动后端进程。唯一写口是 `--out` 指定的
   报告文件。⚠️ 本文件**刻意不出现**那些库名/端口的字面量 —— 车道的只读静态核是
   逐字 grep, 散文里提一嘴也会被计成命中, 那会让判据失去"命中即真违规"的含义。

rc 语义: `semantic_diff` 为空 ⇒ rc=0; 非空 ⇒ rc=1。`known_scope_note` 永不影响 rc。

⚠️ **独立性分级** (本脚本每条判据自带 `independence` 字段, 后人勿把空转当第三源):
  - `cross-source`            两侧由**不同规则**从数据派生, 能真翻转。
  - `reimplementation`        **同一条契约的两个独立实现** (如 overview 的 group-by 与本脚本
                              的 group-by)。能抓任一侧的**实现漂移**, 但两侧共享同一份规格 ⇒
                              规格本身错了它一概发现不了, **不得**当作第三个独立派生源。
                              (Codex r1 MEDIUM-6 指出原先误标成 cross-source。)
  - `structurally-guaranteed` 当前实现下恒真 (纯透传 / 上游网关已内部断言),
                              保留是为了守**未来改动**, 不得冒充独立第三源。
  典型: `review_overview._gate_boards_rollup`(:283) 在网关内部已断言「rollup 的
  到期板集合+计数 ≡ due_nodes group-by 派生」, 不等即 raise → entry 变 corrupt。
  所以 overview **成功返回 entry 时**该子项在 overview 侧恒真; 真正能翻转它的只有
  picker 自身的两源 (`boards` rollup vs `due_nodes` group-by), 那一条本脚本直接
  在 picker JSON 上算, 不假手 overview —— 否则 overview 一 corrupt 就没人算了。
"""

from __future__ import annotations

import argparse
import errno
import json
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

#: Dashboard 面在结构降级时的取值标记 —— ⛔ 不是 0。
#: `Dashboard.md:65-66` 结构校验不过时**明确不出数字**("⚠️ 投影结构异常"), 记 0
#: 等于把结构损坏伪装成"三面一致的 0 到期"。not-comparable 是**值**的标记,
#: 不是豁免: 它照样进 semantic_diff (见 `reconcile`)。
NOT_COMPARABLE = "not-comparable"

#: `/overview` 的相对路径 (与 review_overview.py 的路由前缀 + "/overview" 一致)。
OVERVIEW_PATH = "/api/v1/review/overview"

#: overview entry 中"可比"的状态。`corrupt` / `no_projection` 不在此列 —— 我们手上
#: 有 picker 投影却被对面判成损坏/缺失, 那是差异本身, 不是"取不到"。
#: `stale` 可比: `_vault_entry` 在 stale 分支照样落 `entry["projection"] = summary`。
OVERVIEW_COMPARABLE_STATUS = ("ok", "stale")

#: ⛔ `known_scope_note` 的**白名单**(穷举)。不在此列的一切情况默认进 `semantic_diff`。
#: 这条白名单是"不把真缺陷塞进口径差"的唯一闸门 —— 加条目必须附代码实证。
SCOPE_NOTE_CODES = (
    # N1: Dashboard 的板数取 `dv.pages('"原白板"').where(type==="whiteboard")`
    #     (Dashboard.md:21) = **全部**原白板; picker 的 boards rollup 只收
    #     `set(members_by_board) | set(placeholder_boards)` (daily_review_pick.py:1072)
    #     = **有成员或有占位符**的板。两个口径本就不同, 且 Dashboard 的板数不消费
    #     投影(本脚本只读 json, 读不到也不该读 vault 的 md)。
    "N1_dashboard_board_scope",
    # N2: picker `due_nodes` 是**扫描序**(daily_review_pick.py:1057, nodes 出自
    #     sorted(glob("*.md"))); overview `_node_rows`(review_overview.py:985) 按
    #     **紧迫度**重排并在 docstring 写明理由。两者不共享行序契约, 直接比恒红。
    #     本脚本改为对账 ①板内节点身份集合 ②overview 行序 ≡ 独立复算的紧迫度序。
    "N2_row_order_contract_differs",
    # N3: overview 连不上(连接被拒/超时/DNS) —— **仅此一种**。连上但 entry corrupt、
    #     非 2xx、响应不是 JSON, 一律进 semantic_diff。
    "N3_overview_not_fetched",
    # N4: picker 投影无 `boards` 顶层键 = 旧投影合法形态 (CARD-D1 之前),
    #     `_gate_boards_rollup` docstring 明文"可选顶层键: 旧投影缺省走纯派生路径"。
    #     该子项 not-applicable, 不是差异。
    #     ⚠️ 仅当 `buckets` 也缺席才算合法旧形态 —— `review_overview.py:869-872` 明文
    #     "有 buckets 无 boards 不是任何历史形态"(Codex r2 MEDIUM-4)。
    "N4_picker_rollup_absent",
    # N5: **根本没要求取** overview (未给 --overview-url / --overview-json) —— 与 N3
    #     「试过但连不上」是两回事 (Codex r2 LOW-11)。把没试过写成 "backend down"
    #     会让读者以为探测过后端。
    "N5_overview_not_requested",
)

#: 判为「连不上」(N3 豁免) 的**连接层**失败。⛔ 只列能**证明**连接没建立起来的那几种;
#: 超时 / 连接重置 / 协议错误一律不算 —— 它们可能发生在**连上之后**(如对端收下 GET 却
#: 不返回响应头, Codex r2 HIGH-1 实测过这条路径), 含糊的一律计入 semantic_diff (fail-closed)。
#: ⛔ Codex r3 MEDIUM-2: 必须用**当前平台**的 errno **名字**取值 —— 把两个平台的数字
#: 并成一张表, 在 macOS 上会把 `ETIME=101` 误收成连接失败, 又漏掉 `ENETDOWN=50`;
#: 在 Linux 上则漏掉 `EHOSTDOWN=112` / `ENETDOWN=100`。数字跨平台不可移植, 名字才是。
_CONNECT_FAILURE_ERRNOS = frozenset(
    getattr(errno, _n)
    for _n in ("ECONNREFUSED", "EHOSTUNREACH", "ENETUNREACH", "EHOSTDOWN", "ENETDOWN", "EADDRNOTAVAIL")
    if hasattr(errno, _n)
)


# --------------------------------------------------------------------------
# Dashboard 面: 逐字镜像 canvas-vault/Dashboard.md 的归约块
# --------------------------------------------------------------------------


def _is_js_number(v: Any) -> bool:
    """JS `typeof v === "number"` 的 Python 等价。

    ⛔ 不能写 `isinstance(v, (int, float))`: Python 的 `bool` 是 `int` 子类, JSON
    `true` 会被判成 number 并当 1 用 —— 而 JS 里 `typeof true === "boolean"`。
    方向相反的偏差: 投影里 `stats.due_nodes: true` 在 Dashboard 走**降级**(不出数字),
    朴素镜像却会伪造出"1 张到期"。`type(True) is bool` ⇒ 下式自动排除。
    """
    return type(v) is int or type(v) is float


def _js_str(v: Any) -> str:
    """把值渲染成 JS `String(v)` 的结果 —— 用户在界面上**看到的那个字样**。

    ⛔ Codex r4 #8: 上一轮用「Python 类型严格相等」比计数, 结果把 `0.0` 与 `0` 报成差异,
    可 JS 两边都显示 `0` —— 那是**假红**。对账工具报假红比漏报更伤信任。
    ⛔ Codex r4 #4: 反过来 `False` 与 `0` 在 Python 里相等, 但 JS 显示 `false` vs `0`,
    那是**真差异**。两条都只有一个正确口径: **比显示字符串**。

    JS 的数字渲染会丢掉整数值 float 的小数点 (`String(2.0) === "2"`), 布尔渲染成
    `"true"/"false"`, null 渲染成 `"null"`。
    """
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if type(v) is float and v.is_integer():
        return str(int(v))
    return str(v)


def _js_interp_throws(v: Any) -> bool:
    """JS 模板字符串 `${v}` 是否会抛 TypeError (Codex r2 MEDIUM-7 / r3 MEDIUM-4)。

    `String(v)` 对对象先试 `toString`、再试 `valueOf`。JSON 解出来的普通对象继承
    `Object.prototype.toString` ⇒ 得 "[object Object]", 不抛; **但** 若对象自带
    `"toString"` 键, 该键的值在 JSON 里永远不可能是函数, 于是两步都拿不到原始值 ⇒ 抛。

    ⛔ Codex r3 MEDIUM-4: **数组会把元素的字符串化异常传播出来** ——
    `Array.prototype.toString` 走 `join`, 对每个元素再做一次 `String()`。
    所以 `[{"toString": null}]` 同样抛, 嵌套数组亦然。必须递归。

    Dashboard `:76-83` 把 `generated_at` / `unassigned` / `backlogCnt` 等值插进模板 ——
    抛出后落到 `:87` "投影损坏"、**不出数字**。镜像必须跟到这一层, 否则脚本算出数字
    而界面上什么都不显示, 两面各说各话却报"一致"。
    """
    # ⛔ Codex r4 #2: 用**显式栈**而不是递归 —— 深嵌套数组是合法 JSON、JS 插值也正常,
    # 递归实现却会抛 RecursionError 打断整次报告 (自己造的崩溃比漏检更糟)。
    stack = [v]
    seen = 0
    while stack:
        cur = stack.pop()
        seen += 1
        if seen > 100_000:  # 防御: 极端输入不让遍历自己变成挂起
            return True
        if isinstance(cur, dict):
            if "toString" in cur:
                return True
        elif isinstance(cur, list):
            stack.extend(cur)
    return False


def _same_count(a: Any, b: Any) -> bool:
    """两个计数在**界面上显示成同一个字样**吗 (Codex r3 MEDIUM-6 / r4 #4 #8)。

    ⛔ 既不能用 Python 的 `==`(`False == 0` 会把「显示 false」和「显示 0」判成一致),
    也不能用「类型严格相等」(会把 `0.0` 与 `0` 判成不同, 可 JS 两边都显示 `0` = 假红)。
    唯一正确的口径是比 `String(v)` 的结果 —— 用户看到的就是那个。
    """
    return _js_str(a) == _js_str(b)


def _strict_count(v: Any) -> int | None:
    """严格计数: 只接受真 `int`。⛔ Codex r2 MEDIUM-6。

    Python 的 `False == 0` / `2.0 == 2` 会让**损坏的计数**与正常值比较时相等,
    于是 `due: false` 的板被当成"正常的零到期板"放行。返回 None = 类型不合法。
    (与 `review_overview._strict_int` 同口径: bool 不是 int。)
    """
    return v if type(v) is int else None


def dashboard_recompute(payload: Any) -> dict:
    """重算 `canvas-vault/Dashboard.md` 的 `dv.io.load("outputs/今日复习.json")`
    → `fsrsLine = ...` 归约块 (本次实测 `:57`–`:83`)。

    逐行对照 (md 行号: 本脚本对应):
      :62 `const sv = proj?.schema_version`                       → sv
      :63 `hasDetail = Array.isArray(proj?.due_nodes)`            → has_detail
      :64 `statsDueOk = typeof proj?.stats?.due_nodes === "number"`→ stats_due_ok
      :65 结构校验 4 条或 → 降级 (:66 "投影结构异常", 不出数字)     → NOT_COMPARABLE
      :68 `dueCnt = hasDetail ? proj.due_nodes.length : proj.stats.due_nodes`
      :73 `backlogNames = Array.isArray(proj.ineligible?.placeholder) ? ... : []`
      :74 `backlogCnt = backlogNames.length || (proj.stats?.ineligible ?? 0)`
          ⛔ 必须抄到 `:74` 的 `||` 回退: 只抄 `:73` 的 len(placeholder), 会在
          placeholder 空/缺而 stats.ineligible>0 时与 Dashboard 显示值分叉。

    `:56 if (raw)` / `:87 catch` 两条(文件缺失、JSON 解析失败)由调用方在读文件时
    处理: 读不到就没有这一面可对, 不走本函数。

    差异声明 (如实): md `:65` 的 `typeof proj !== "object"` 在 JS 里放行顶层数组
    (`typeof [] === "object"`), 随后 `proj.schema_version` 为 undefined → 仍然降级;
    本函数用 `isinstance(payload, dict)` 在更早一步降级。**路径不同, 结论相同**。
    """
    if not isinstance(payload, dict):
        return {
            "due_count": NOT_COMPARABLE,
            "backlog_count": NOT_COMPARABLE,
            "degraded_reason": "投影根节点不是 object (Dashboard.md:65 结构校验降级)",
        }
    sv = payload.get("schema_version")
    due_nodes = payload.get("due_nodes")
    stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else None
    has_detail = isinstance(due_nodes, list)
    stats_due = stats.get("due_nodes") if stats is not None else None
    stats_due_ok = _is_js_number(stats_due)
    if not _is_js_number(sv) or sv < 2 or not (has_detail or stats_due_ok):
        return {
            "due_count": NOT_COMPARABLE,
            "backlog_count": NOT_COMPARABLE,
            "degraded_reason": (
                f"Dashboard.md:65 结构校验降级 (schema_version={sv!r}, "
                f"due_nodes 为数组={has_detail}, stats.due_nodes 为 number={stats_due_ok})"
            ),
        }
    # Codex r1 MEDIUM-7: `:70-72` 对**每一行**取属性 —— `reasonOf = d => d.due_reason ?? ...`
    # 在 `d` 为 null 时抛 TypeError, 被 `:86` 的 catch 接住 → `:87` 显示"投影损坏"、不出数字。
    # 只镜像 `:68` 的 `length` 会把 `due_nodes=[null]` 记成"1 张到期", 而界面上其实什么都没有。
    # (字符串/数字行不抛: JS 对它们取不存在的属性只得 undefined, 故只拦 None。)
    if has_detail and any(r is None for r in due_nodes):
        return {
            "due_count": NOT_COMPARABLE,
            "backlog_count": NOT_COMPARABLE,
            "degraded_reason": "Dashboard.md:70-72 逐行取属性遇 null → :87 投影损坏 (不出数字)",
        }
    # Codex r2 MEDIUM-7: `:79-83` 把 generated_at / stats.unassigned 插进模板字符串,
    # 值是「带 toString 键的对象」时 JS 抛 TypeError → `:87` 投影损坏、不出数字。
    for fld, val in (
        ("generated_at", payload.get("generated_at")),
        ("stats.unassigned", (stats or {}).get("unassigned")),
    ):
        if _js_interp_throws(val):
            return {
                "due_count": NOT_COMPARABLE,
                "backlog_count": NOT_COMPARABLE,
                "degraded_reason": f"Dashboard.md:79-83 模板插值 {fld} 抛 TypeError → :87 投影损坏 (不出数字)",
            }
    due_cnt = len(due_nodes) if has_detail else stats_due  # :68
    ineligible = payload.get("ineligible")
    placeholder = ineligible.get("placeholder") if isinstance(ineligible, dict) else None
    backlog_names = placeholder if isinstance(placeholder, list) else []  # :73
    fallback = stats.get("ineligible") if stats is not None else None  # :74 `?? 0`
    fallback = 0 if fallback is None else fallback
    backlog_cnt = len(backlog_names) or fallback  # :74 `||` — 左值 int, 与 JS 同语义
    # ⛔ Codex r3 MEDIUM-5: `backlogCnt` 自己也被插进模板 (`:78`) —— `stats.ineligible`
    # 是带 toString 键的对象时, `||` 回退把它原样交给模板, Dashboard 当场抛错不出数字。
    # 漏掉这一条会在 overview 缺席时形成**两面假绿**。
    if _js_interp_throws(backlog_cnt):
        return {
            "due_count": NOT_COMPARABLE,
            "backlog_count": NOT_COMPARABLE,
            "degraded_reason": "Dashboard.md:78 模板插值 backlogCnt 抛 TypeError → :87 投影损坏 (不出数字)",
        }
    return {"due_count": due_cnt, "backlog_count": backlog_cnt, "degraded_reason": None}


# --------------------------------------------------------------------------
# picker 面: 两条各自独立的板级派生
# --------------------------------------------------------------------------


def picker_group_by_board(due_nodes: Any) -> dict[str, list[dict]]:
    """picker `due_nodes` 按 `board` group-by —— 与 `_gate_due_groups` 同一条规则,
    但在本脚本里独立实现 (overview corrupt 时这一源仍然算得出来)。

    行形状不合法 (非 object / board 非非空字符串) 的行归入 `""` 桶, 由调用方按
    差异报出 —— ⛔ 不静默丢行: 丢行会让板级合计悄悄 != stats。
    """
    groups: dict[str, list[dict]] = {}
    for row in due_nodes if isinstance(due_nodes, list) else []:
        if not isinstance(row, dict):
            groups.setdefault("", []).append({"node": "", "fsrs_due": "", "_malformed": repr(row)[:80]})
            continue
        board = row.get("board")
        key = board if isinstance(board, str) and board else ""
        groups.setdefault(key, []).append(row)
    return groups


def picker_rollup_due(payload: dict) -> tuple[dict[str, int] | None, str | None]:
    """picker 顶层 `boards` rollup 的逐板 `due` (daily_review_pick.py:1071-1088)。

    返回 `(逐板 due, 损坏原因)`：
      - `(None, None)`  = **键不存在** ⇒ 旧投影合法形态 (SCOPE_NOTE_CODES N4)
      - `(None, 原因)`  = 键在但**类型损坏** ⇒ 这是差异, 不是口径差
      - `({...}, None)` = 正常

    ⛔ Codex r1 MEDIUM-5: 原实现把「键在但为 null / 字符串 / 对象」也归成 N4, 于是
    一份**已经读到的损坏投影**会在 overview 缺席时被报成"两面一致"。缺键与损坏必须分开。
    """
    if "boards" not in payload:
        return None, None
    rollup = payload.get("boards")
    if not isinstance(rollup, list):
        return None, f"boards 顶层键在, 但不是数组 (实为 {type(rollup).__name__})"
    out: dict[str, int] = {}
    for i, r in enumerate(rollup):
        if not isinstance(r, dict):
            return None, f"boards[{i}] 不是 object (实为 {type(r).__name__})"
        board = r.get("board")
        if not isinstance(board, str) or not board:
            return None, f"boards[{i}].board 不是非空字符串 (实为 {board!r})"
        if board in out:
            return None, f"boards[{i}].board 重复: {board!r}"
        # ⛔ Codex r2 MEDIUM-6: `due` 必须是真 int。`False == 0` / `2.0 == 2` 会让
        # 损坏计数在后续比较里与正常值相等, 于是 `due: false` 的板被当成正常零到期板。
        due = _strict_count(r.get("due"))
        if due is None:
            return None, f"boards[{i}].due 不是整数 (实为 {r.get('due')!r})"
        # ⛔ Codex r4 #3: `next_due` 损坏时排序侧会把它归一掉 —— 归一是为了不让排序抛错,
        # **不是**为了放过它。损坏本身必须在这里报出来, 否则归一就成了掩盖。
        nd = r.get("next_due")
        if nd is not None and not isinstance(nd, str):
            return None, f"boards[{i}].next_due 不是字符串 (实为 {type(nd).__name__})"
        out[board] = due
    return out, None


def picker_upcoming_boards(payload: dict) -> tuple[dict[str, Any], list[str]]:
    """`upcoming` 里的板 → `next_due`（Codex r2 MEDIUM-5）。

    ⚠️ 这不是可选项: `boards` rollup **缺席**时 overview 的零到期行改从 `upcoming` 追加
    (`review_overview.py:928-940`)。板集若不含 upcoming, 合法旧投影会被误报成
    「overview 多出一块板」。
    """
    up = payload.get("upcoming")
    out: dict[str, Any] = {}
    bad: list[str] = []
    # ⛔ Codex r4 #5: `upcoming` 是 null / 对象 / 字符串 / 数字时, 原实现静默当成空数组 ——
    # 一份**已经损坏的投影**于是全绿。键不在场是合法旧形态, 键在但不是数组就是损坏。
    if "upcoming" in payload and not isinstance(up, list):
        bad.append(f"upcoming 键在但不是数组 (实为 {type(up).__name__})")
    for i, u in enumerate(up if isinstance(up, list) else []):
        if not (isinstance(u, dict) and isinstance(u.get("board"), str) and u["board"]):
            bad.append(f"upcoming[{i}] 形状非法")
            continue
        b = u["board"]
        # ⛔ Codex r3 MEDIUM-11: 同名 upcoming 会被字典覆盖 ⇒ 多出来的那条隐形。
        if b in out:
            bad.append(f"upcoming[{i}].board 重复: {b!r}")
        nd = u.get("next_due")
        # ⛔ 非字符串 next_due 不得被悄悄归一成空排序键 —— 那会让损坏值参与排序还全绿。
        if not isinstance(nd, str):
            bad.append(f"upcoming[{i}].next_due 不是字符串 (实为 {type(nd).__name__})")
        out[b] = nd
    return out, bad


def picker_rollup_boards(payload: dict) -> dict[str, dict] | None:
    """rollup 的**完整板行**（含 `due=0` 的零到期板）。

    ⛔ Codex r1 HIGH-1: 板集对账只看「到期板」会漏掉合法的零到期板 —— 例如
    `丙板 due=0 / future=1` 在 picker rollup 里在场, overview 端由 `rollup_zero`
    渲染成零到期行; 若 overview 把它整块漏掉, 总览页就少显示一块板, 而只比到期板的
    判据全绿。零到期板必须进板集对账。
    """
    if "boards" not in payload or not isinstance(payload.get("boards"), list):
        return None
    out: dict[str, dict] = {}
    for r in payload["boards"]:
        if isinstance(r, dict) and isinstance(r.get("board"), str) and r["board"]:
            out[r["board"]] = r
    return out


def expected_board_order(
    top_names: list[str], group_due: dict[str, int], rollup_rows: dict | None, upcoming: dict[str, Any]
) -> list[str]:
    """按 `review_overview` 的**完整**板序契约独立复算总览页板表的顺序。

    ⛔ Codex r2 HIGH-2: 只比「推荐前缀」会漏掉其后的全部板序 —— `top=[乙]` 而
    overview 返回 `[乙, 丁, 甲]`(应为 `[乙, 甲, 丁]`) 时前缀判据全绿; `top=[]` 时
    更是整张板表的顺序都没人看。

    契约两段 (逐字对照实现):
      ① 到期板: `board_rows.sort(key=(prio.get(b, len(prio)), -due, board))` (`:911`),
         `prio[b] = i` 取自 top_boards 下标 (`:831`)。
      ② 零到期板追加在后 (`:942 board_rows += zero_rows`), 且来源二选一:
         - rollup **在场** → 取 rollup 里 `due == 0` 的板, 排序键
           `(earliest is None, earliest or "", board)`, 其中 earliest = `next_due or None` (`:918-925`);
         - rollup **缺席** → 取 `upcoming` 的板, 排序键 `(earliest, board)` (`:928-940`)。
         两种来源都**排除已在到期板里的板**。

    独立性: 这是同一条契约的**另一个实现** ⇒ `reimplementation` 档 —— 能抓任一侧的
    实现漂移, 抓不到契约本身写错。
    """
    prio = {b: i for i, b in enumerate(top_names)}
    due_boards = sorted(group_due, key=lambda b: (prio.get(b, len(prio)), -group_due[b], b))

    # ⛔ Codex r3 MEDIUM-10: 排序键里的时间值可能是**损坏的**(如 dict) —— 直接比较会抛
    # `TypeError: '<' not supported between 'str' and 'dict'`, 整次报告中断、差异表都不出。
    # 非字符串一律先归到一个**可排序且可辨认**的位置, 损坏本身由调用方按差异报出。
    def _ts(v: Any) -> str | None:
        return v if isinstance(v, str) else None

    if rollup_rows is not None:
        zero = [
            (b, (_ts(r.get("next_due")) or None)) for b, r in rollup_rows.items() if _strict_count(r.get("due")) == 0
        ]
        zero = [(b, e) for b, e in zero if b not in group_due]
        zero.sort(key=lambda t: (t[1] is None, t[1] or "", t[0]))
    else:
        zero = [(b, _ts(e)) for b, e in upcoming.items() if b not in group_due]
        zero.sort(key=lambda t: (t[1] is None, t[1] or "", t[0]))
    return due_boards + [b for b, _ in zero]


def urgency_sorted_nodes(rows: list[dict]) -> list[str]:
    """按 `review_overview._node_rows`(:985) 在 docstring 里写明的**紧迫度契约**
    独立复算板内节点行序, 作用在 **picker 的行**上。

    契约原文: 已排期的到期时刻恒在过去, 越早越紧迫 ⇒ 先按非空时间戳升序; 新卡的
    `fsrs_due` 是空串(语义=现在), 排在已逾期节点**之后** —— 字典序把 "" 当最小会让
    "逾期 3 天"被"现在"盖掉, 那正是 CARD-D1 复核抓过的低估紧迫度缺陷。同刻按节点名
    稳定排序 (防同分随机漂)。

    ⚠️ 独立性如实声明: 这是照 **docstring 契约**复算, 不是照实现抄。若实现与它写明的
    契约分叉, 本判据变红 —— 那正是想要的结果。
    `_due_ts`(:159) 对合法值是**原样返回**(只校验不归一), 所以拿 picker 行里的原始
    `fsrs_due` 字符串排序与 overview 侧逐字同值。
    """

    def key(r: dict) -> tuple:
        fd = r.get("fsrs_due")
        fd = fd if isinstance(fd, str) else ""
        node = r.get("node")
        node = node if isinstance(node, str) else ""
        return (fd == "", fd, node)

    return [r.get("node") if isinstance(r.get("node"), str) else "" for r in sorted(rows, key=key)]


# --------------------------------------------------------------------------
# overview 面: 只读 GET + 甲支(vault 维度)取数
# --------------------------------------------------------------------------


def _reject_js_nonstandard(const: str):
    """`json.loads(parse_constant=...)` 钩子 —— 让 Python 的解析器与 JS 同严格度。

    Python 默认把 `NaN` / `Infinity` / `-Infinity` 解析成 float; **JS 的 `JSON.parse`
    拒收它们**。Dashboard 走的是 `JSON.parse`(`Dashboard.md:59`), 失败会落到 `:87`
    显示"投影损坏"。所以镜像 Dashboard 不能只镜像归约逻辑, **解析器的严格度也得镜像**,
    否则同一份投影: 界面显示"损坏", 本脚本却算出一个数字, 还报"三面一致"。
    """
    raise ValueError(f"非标准 JSON 常量 {const} (JS JSON.parse 拒收)")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """⛔ Codex r3 HIGH-1: 关掉自动重定向。

    默认 opener 会跟 302 再连一跳。若**下一跳**连接被拒, 抛的是 `ConnectionRefusedError`,
    于是整次请求被判成「连不上」——可**第一跳后端明明已经响应过**。
    `/overview` 是本机后端上的一个纯 JSON GET, 出现重定向本身就是异常形态:
    不跟随, 让它变成 `HTTPError(302)` ⇒ 归「连上了但非 2xx」⇒ 计入 semantic_diff。
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        return None


def _is_connection_failure(e: BaseException) -> bool:
    """这个异常**能证明连接没建立起来**吗？(N3 豁免的唯一判据, Codex r2 HIGH-1)

    能证明的只有三类: 连接被拒 (`ConnectionRefusedError`)、主机/网络不可达 (errno)、
    DNS 解析不了 (`socket.gaierror`)。
    ⛔ 超时 / 连接重置 / 协议错误一律**不算** —— `opener.open()` 要等响应头到齐才返回,
    对端收下 GET 却不回响应头时抛的也是超时, 那是**已连接**的故障, 豁免它等于把后端
    「起来了但不响应」读成「后端没起」。含糊的一律 fail-closed 进 semantic_diff。
    未知 URL scheme (`ValueError`/`URLError("unknown url type")`) 同样不算连接失败。
    """
    inner = getattr(e, "reason", e)
    if isinstance(inner, socket.gaierror) or isinstance(inner, ConnectionRefusedError):
        return True
    if isinstance(inner, OSError) and not isinstance(inner, (TimeoutError, ConnectionResetError)):
        return inner.errno in _CONNECT_FAILURE_ERRNOS
    return False


def _direct_opener() -> urllib.request.OpenerDirector:
    """**不经代理**的 opener —— 本机后端的 GET 必须直连。

    ⛔ 这不是洁癖, 是判据正确性问题 (2026-09-14 本机实测):
    系统代理设在 `127.0.0.1:<某端口>` 时, `urllib` 默认会把 `http://127.0.0.1:8011/...`
    也交给代理; 后端**没起**的时候, 代理自己回一个 **503**。于是脚本读到的是
    「连上了, 但后端答 503」而不是「连不上」—— 唯一的豁免口 (not-fetched) 永远走不到,
    「后端没运行」会被报成「总览页有缺陷」。空 `ProxyHandler` 关掉这条路径后,
    同一次请求得到的是 `URLError(Connection refused)`, 分类才回到正确的那一档。
    """
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)


def fetch_overview(base_url: str, timeout: float = 10.0) -> tuple[Any, str | None]:
    """对**已在运行**的后端只读 GET `/api/v1/review/overview`。

    返回 `(响应对象, not_fetched_reason)`。⛔ `not_fetched_reason` 非 None **只**用于
    「连不上」(连接被拒 / 超时 / DNS) —— 那时 overview 这一面整体缺席。
    连上了但非 2xx / 响应不是 JSON ⇒ 两种都是**连上了**, 由调用方计入 semantic_diff
    (见 `reconcile` 的 overview_error 分支)。

    ⚠️ `urllib.error.HTTPError` 是 `URLError` 的子类, 必须**先**捕 HTTPError,
    否则一个 500 会被误判成"连不上"并静默豁免掉后端缺陷。
    ⚠️ 直连不走代理, 理由见 `_direct_opener`。
    """
    url = base_url.rstrip("/") + OVERVIEW_PATH
    # ⛔ Codex r1 HIGH-4 / MEDIUM-8: **连接阶段**与**读取阶段**必须分开捕获。
    # 原实现把整段包在一个 try 里, 于是 HTTP 200 之后 `resp.read()` 超时 / 连接重置
    # 也落进 not-fetched 豁免 —— 那是**连上了**之后的失败, 按声明应计入 semantic_diff;
    # 而正文非法 UTF-8 时 `decode()` 抛的 UnicodeDecodeError 根本没人接, CLI 直接中断、
    # 连报告都不产出。两者都不能留在豁免口里。
    try:
        # ⛔ Codex r4 #1: `Request()` **本身**会对畸形 URL 抛 ValueError —— 放在 try 外
        # 会让 `--overview-url 'http://[::1'` 这类输入直接打断 CLI、连差异表都不出。
        req = urllib.request.Request(url, method="GET")  # noqa: S310 — 固定 http(s) 本机地址
        resp = _direct_opener().open(req, timeout=timeout)  # noqa: S310
    except urllib.error.HTTPError as e:
        return {"__http_error__": f"HTTP {e.code}"}, None  # 连上了, 非 2xx
    except Exception as e:  # noqa: BLE001
        # ⛔ Codex r2 HIGH-1: `open()` 失败**不等于**连不上 —— 它要等到响应头到齐才返回,
        # 所以"对端收下了 GET 却不回响应头"这种**已连接**的故障也会在这里抛。
        # ⛔ Codex r3 MEDIUM-3: 捕获面必须是 `Exception` —— `BadStatusLine` / `LineTooLong`
        # (http.client) 与 `ValueError` / `InvalidURL` (未知 scheme / 非法端口 / 畸形 URL)
        # 都不是 OSError 子类, 窄捕获会让它们**逃出去**、连差异表都不出。
        # 唯一能豁免的是**能证明连接没建立**的那几种 (拒绝 / 不可达 / DNS);
        # 超时、重置、协议错误、URL 错误一律 fail-closed 计入 semantic_diff。
        if _is_connection_failure(e):
            return None, f"{type(e).__name__}: {str(e)[:160]}"  # ← 唯一的 not-fetched 出口
        return {"__open_error__": f"{type(e).__name__}: {str(e)[:160]}"}, None
    try:  # 以下全部属于"已连接", 任何失败都不再豁免
        with resp:
            body = resp.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001 — 已连接后的任意失败统一按差异呈现, 不豁免
        return {"__read_error__": f"{type(e).__name__}: {str(e)[:160]}"}, None
    try:
        # ⛔ Codex r1 HIGH-3: 与 JS `JSON.parse` 同严格度。Python 默认放行 NaN/Infinity,
        # JS 拒收 —— 不拦的话, 含 NaN 的投影在 Dashboard 上显示"投影损坏"(`Dashboard.md:87`)
        # 而本脚本却算出数字, 两面各说各话却报"一致"。`review_overview._summarize` 同款处理。
        return json.loads(body, parse_constant=_reject_js_nonstandard), None
    except ValueError as e:
        return {"__json_error__": f"{type(e).__name__}: {str(e)[:160]}"}, None


def select_vault_entry(resp: Any, vault_id: str) -> tuple[Any, str | None]:
    """按 **vault 维度键**从 `/overview` 响应里取该 vault 的 entry (甲支)。

    ⛔ R-B14-12 (主 session 2026-09-14 裁定): G3-5 走**甲**(service 侧按 vault 分桶
    `{vault_id: {concept_id: card}}`) 已合 (第十三批 U9-C `126531c7`)。本脚本随之
    **先按 vault_id 定位 entry, 再取字段** —— 禁止把各 vault 的计数合并后与单个
    vault 比 (那是乙支扁平读法, 等于跨 vault 污染: A 库的到期数会算进 B 库的对账)。

    找不到该 vault_id ⇒ 返回错误原因, 由调用方计入 semantic_diff (**不是** not-fetched:
    后端明明答了, 只是没有这个库, 那是真差异)。
    """
    if isinstance(resp, dict) and "__http_error__" in resp:
        return None, f"overview 返回非 2xx: {resp['__http_error__']}"
    if isinstance(resp, dict) and "__read_error__" in resp:
        return None, f"overview 已连接但正文读取失败: {resp['__read_error__']}"
    if isinstance(resp, dict) and "__open_error__" in resp:
        return None, f"overview 请求失败且无法证明连接未建立 (fail-closed): {resp['__open_error__']}"
    if isinstance(resp, dict) and "__json_error__" in resp:
        return None, f"overview 响应不是 JSON: {resp['__json_error__']}"
    if isinstance(resp, dict) and "vault_id" in resp and "vaults" not in resp:
        entries = [resp]  # 单 entry 形态 (离线夹具便利)
    elif isinstance(resp, dict) and isinstance(resp.get("vaults"), list):
        entries = resp["vaults"]
    elif isinstance(resp, list):
        entries = resp
    else:
        return None, f"overview 响应形状不可识别: {type(resp).__name__}"
    hits = [e for e in entries if isinstance(e, dict) and e.get("vault_id") == vault_id]
    if not hits:
        return None, f"overview 响应中无 vault_id={vault_id!r} 的 entry"
    if len(hits) > 1:
        # ⛔ Codex r1 LOW-9: 静默取首个会让 `[ok, corrupt]` 这种响应全绿 —— 挑一条
        # 好的、把坏的那条当没看见。当前端点每目录一条, 这是防御缺口不是现存缺陷。
        return None, f"overview 响应中 vault_id={vault_id!r} 有 {len(hits)} 条 entry (应唯一)"
    return hits[0], None


# --------------------------------------------------------------------------
# 对账
# --------------------------------------------------------------------------


def _diff(pair: str, field: str, a: Any, b: Any, independence: str) -> dict:
    return {"pair": pair, "field": field, "a": a, "b": b, "independence": independence}


def _note(code: str, detail: str) -> dict:
    assert code in SCOPE_NOTE_CODES, f"known_scope_note 白名单外的 code: {code!r}"
    return {"code": code, "detail": detail}


def reconcile(
    picker: Any,
    overview_entry: Any,
    *,
    not_fetched_reason: str | None = None,
    not_requested_reason: str | None = None,
    overview_error: str | None = None,
    vault_id: str | None = None,
) -> dict:
    """三面对账主体 —— 纯函数 (无 I/O, 无时钟), 便于夹具驱动测试。

    返回 `{"vault_id", "views", "semantic_diff": [...], "known_scope_note": [...]}`。
    """
    diffs: list[dict] = []
    notes: list[dict] = []
    vid = vault_id
    if vid is None:
        vid = picker.get("vault_id") if isinstance(picker, dict) else None

    dash = dashboard_recompute(picker)
    pk = picker if isinstance(picker, dict) else {}
    due_nodes = pk.get("due_nodes")
    stats = pk.get("stats") if isinstance(pk.get("stats"), dict) else {}
    p_stats_due = stats.get("due_nodes")
    p_len_due = len(due_nodes) if isinstance(due_nodes, list) else NOT_COMPARABLE
    groups = picker_group_by_board(due_nodes)
    group_due = {b: len(rows) for b, rows in groups.items()}
    rollup_due, rollup_corrupt = picker_rollup_due(pk)
    rollup_rows = picker_rollup_boards(pk)

    # ---- ① 到期卡片数 ----------------------------------------------------
    # picker 内两源: stats 权威计数 vs 明细长度。生成期 `stats["due_nodes"] =
    # len(due_rows)`(daily_review_pick.py:1060) 恒等, 但**消费侧拿到的是文件** ——
    # 手改/损坏的投影会让二者分叉, 而 Dashboard 读明细长度、overview 读 stats,
    # 于是两个界面显示不同数字。这是三面对账真正要抓的第一类缺陷。
    if not _same_count(p_stats_due, p_len_due):
        diffs.append(_diff("picker.stats ↔ picker.due_nodes", "due_count", p_stats_due, p_len_due, "cross-source"))

    if dash["due_count"] == NOT_COMPARABLE:
        # ⛔ 结构降级不是豁免: Dashboard 此时对用户**不出数字**, 与另两面"有数字"
        # 就是一处真实的界面分歧。记 0 或跳过都等于伪装成三面一致。
        diffs.append(_diff("dashboard ↔ picker", "due_count", NOT_COMPARABLE, p_len_due, "cross-source"))
        diffs.append(
            _diff("dashboard(structural)", "degraded_reason", dash["degraded_reason"], "(应可出数字)", "cross-source")
        )
    elif dash["due_count"] != p_len_due and isinstance(due_nodes, list):
        diffs.append(
            _diff("dashboard ↔ picker.due_nodes", "due_count", dash["due_count"], p_len_due, "structurally-guaranteed")
        )

    # ---- ② 板集与板级到期数 ---------------------------------------------
    if rollup_corrupt is not None:
        # ⛔ Codex r1 MEDIUM-5: 键在但类型损坏 = 差异, **不是** N4 口径差。
        diffs.append(
            _diff("picker.boards(self)", "structure", rollup_corrupt, "(应为合法 rollup 数组)", "cross-source")
        )
    elif rollup_due is None and "buckets" in pk:
        # ⛔ Codex r2 MEDIUM-4: `review_overview.py:869-872` 明文「有 buckets 无 boards
        # 不是任何历史形态」(二者同版一起落盘) ⇒ 这不是合法旧投影, 不能记 N4。
        diffs.append(
            _diff(
                "picker.boards(self)",
                "structure",
                "buckets 在场但 boards 缺席 — 非生产器产物",
                "(二者同版一起落盘)",
                "cross-source",
            )
        )
    elif rollup_due is None:
        notes.append(
            _note(
                "N4_picker_rollup_absent",
                f"vault={vid!r} 的投影无 boards 顶层键 (旧投影合法形态, 且 buckets 同样缺席); "
                "rollup ↔ group-by 子项 not-applicable",
            )
        )
    else:
        # α(rollup) vs β(group-by) —— 真·跨源: 生成器两条不同的派生路径。
        # overview 侧这一条被 `_gate_boards_rollup`(:283) 在网关内部断言过,
        # 所以它只在 **picker 自身**这里能翻转。
        rollup_nonzero = {b: d for b, d in rollup_due.items() if d != 0}
        for b in sorted(set(rollup_nonzero) | set(group_due)):
            a = rollup_due.get(b, "(rollup 无此板)")
            c = group_due.get(b, "(明细无此板)")
            if a != c:
                diffs.append(_diff("picker.boards ↔ picker.due_nodes", f"boards[{b}].due", a, c, "cross-source"))

    if "" in groups:
        diffs.append(_diff("picker.due_nodes(self)", "board", "(空/非法板名)", f"{len(groups[''])} 行", "cross-source"))

    # ---- picker 自检 (⛔ 与 overview 在不在场无关) ------------------------
    # ⛔ Codex r3 MEDIUM-7: 这些检查原先写在 `_reconcile_overview` 里, 于是 overview
    # 走 N3 / N5 时**根本不执行** —— 一条"只在第三方在场时才生效的自检"等于没有。
    for b in sorted(groups):
        # ⛔ Codex r4 #7: 只验类型不够 —— 空串 node 与**同板重名** node 都是垃圾,
        # 参照端点 `:201`/`:205` 分别拒收 (stem 全局唯一)。靠别的比较"间接发现"不算数。
        bad_nodes = [r for r in groups[b] if not isinstance(r.get("node"), str) or not r.get("node")]
        if bad_nodes:
            diffs.append(
                _diff(
                    "picker.due_nodes(self)",
                    f"boards[{b}].node",
                    f"{len(bad_nodes)} 行的 node 非非空字符串 (首个: {bad_nodes[0].get('node')!r})",
                    "(node 应为非空字符串)",
                    "cross-source",
                )
            )
        names = [r.get("node") for r in groups[b] if isinstance(r.get("node"), str) and r.get("node")]
        if len(names) != len(set(names)):
            dup = sorted({n for n in names if names.count(n) > 1})
            diffs.append(
                _diff(
                    "picker.due_nodes(self)",
                    f"boards[{b}].node_unique",
                    f"重复节点名: {dup}",
                    "(节点名应唯一)",
                    "cross-source",
                )
            )
        # ⛔ Codex r4 #6: `fsrs_due` 是排序原料 —— 非字符串会被排序侧归一成空串,
        # 于是一张"日期损坏"的卡悄悄排到新卡那一档还全绿。参照端点 `:165` 直接拒收。
        bad_due = [r for r in groups[b] if not isinstance(r.get("fsrs_due"), str)]
        if bad_due:
            diffs.append(
                _diff(
                    "picker.due_nodes(self)",
                    f"boards[{b}].fsrs_due",
                    f"{len(bad_due)} 行的 fsrs_due 不是字符串 (首个: {bad_due[0].get('fsrs_due')!r})",
                    "(fsrs_due 应为字符串, 空串=新卡)",
                    "cross-source",
                )
            )
    upcoming, upcoming_bad = picker_upcoming_boards(pk)
    for msg in upcoming_bad:
        diffs.append(
            _diff("picker.upcoming(self)", "structure", msg, "(upcoming 行应形状合法且板名唯一)", "cross-source")
        )

    # ---- ③ overview 面 ---------------------------------------------------
    ov_view: Any
    if not_requested_reason is not None:
        # N5: 根本没要求取 —— 与 N3「试过但连不上」分开 (Codex r2 LOW-11)。
        notes.append(_note("N5_overview_not_requested", not_requested_reason))
        ov_view = {"status": "not-requested", "reason": not_requested_reason}
    elif not_fetched_reason is not None:
        # ⛔ N3 是**唯一**的豁免口: 连不上 ⇒ overview 这一面整体缺席, 退化为
        # picker↔Dashboard 两面对账 (那两面仍须 0 semantic_diff)。
        notes.append(_note("N3_overview_not_fetched", f"overview 未取到 (backend down): {not_fetched_reason}"))
        ov_view = {"status": "not-fetched", "reason": not_fetched_reason}
    elif overview_error is not None:
        # 连上了但取不到该 vault 的 entry / 非 2xx / 非 JSON ⇒ 真差异。
        diffs.append(
            _diff("overview ↔ picker", "entry", overview_error, f"picker 有 vault_id={vid!r} 的投影", "cross-source")
        )
        ov_view = {"status": "error", "reason": overview_error}
    else:
        ov_view = _reconcile_overview(
            overview_entry, vid, p_stats_due, dash, group_due, groups, pk, rollup_rows, upcoming, diffs, notes
        )

    # ⛔ 实际对上的面 —— not-fetched 时只有两面, 报告与终端都必须如实说,
    # 否则"后端没起"会被读成"三面一致"(Codex 问题④的假绿面)。
    two_face_only = not_fetched_reason is not None or not_requested_reason is not None
    compared = ["picker", "dashboard"] if two_face_only else ["picker", "dashboard", "overview"]
    return {
        "vault_id": vid,
        "compared_views": compared,
        "views": {
            "picker": {
                "stats_due_nodes": p_stats_due,
                "len_due_nodes": p_len_due,
                "boards_group_by": group_due,
                "boards_rollup": rollup_due,
                "top_boards": _top_board_names(pk),
            },
            "dashboard": dash,
            "overview": ov_view,
        },
        "semantic_diff": diffs,
        "known_scope_note": notes,
    }


def _top_board_names(pk: dict) -> list[str]:
    tb = pk.get("top_boards")
    if not isinstance(tb, list):
        return []
    return [t.get("board") for t in tb if isinstance(t, dict) and isinstance(t.get("board"), str)]


def _reconcile_overview(
    entry: Any,
    vid: Any,
    p_stats_due: Any,
    dash: dict,
    group_due: dict,
    groups: dict,
    pk: dict,
    rollup_rows: dict | None,
    upcoming: dict,
    diffs: list,
    notes: list,
) -> dict:
    """overview entry 与另两面的逐项对账 (调用方已确认"连上了")。"""
    if not isinstance(entry, dict):
        diffs.append(
            _diff(
                "overview ↔ picker",
                "entry",
                f"entry 不是 object: {type(entry).__name__}",
                "(应为 object)",
                "cross-source",
            )
        )
        return {"status": "malformed"}
    status = entry.get("status")
    if status not in OVERVIEW_COMPARABLE_STATUS:
        # ⛔ 验伪锚②守的就是这里: 连上了但 entry 是 corrupt / no_projection ⇒
        # **必须**进 semantic_diff, 禁按"取不到"跳过。网关 raise 的原因恰恰是它
        # 内部抓到了 rollup ≢ group-by 之类的不一致 —— 跳过它 = 把网关抓到的缺陷
        # 读成"对账通过"。
        diffs.append(
            _diff("overview ↔ picker", "status", status, f"picker 有可读投影 (vault_id={vid!r})", "cross-source")
        )
        return {"status": status, "error": entry.get("error")}
    proj = entry.get("projection")
    if not isinstance(proj, dict):
        diffs.append(
            _diff(
                "overview ↔ picker",
                "projection",
                f"status={status!r} 但 projection 不是 object",
                "(应为 object)",
                "cross-source",
            )
        )
        return {"status": status, "projection": None}

    # 卡片数: overview `due_count = _strict_int(stats.get("due_nodes"))`(:963) —— 只读
    # stats, 明确"不退明细重数"。与 picker.stats 比属结构保证; 与 **Dashboard** 比才是
    # 用户在两个界面上看到的那两个数字 (mini-UAT 第⑤项就是肉眼版的这一条)。
    ov_due = proj.get("due_count")
    if not _same_count(ov_due, p_stats_due):
        diffs.append(_diff("overview ↔ picker.stats", "due_count", ov_due, p_stats_due, "structurally-guaranteed"))
    if not _same_count(dash["due_count"], ov_due):
        diffs.append(_diff("dashboard ↔ overview", "due_count", dash["due_count"], ov_due, "cross-source"))
    ov_backlog = proj.get("placeholder_backlog")
    # ⛔ Codex r3 MEDIUM-6: 类型也要相等 —— Dashboard 显示「积压 false 张」而总览页显示
    # 「0 张」时, `False == 0` 会让判据认为两个界面一致。
    if not _same_count(dash["backlog_count"], ov_backlog):
        # Dashboard `:74` 有 `|| stats.ineligible` 回退, overview 只取 len(placeholder)
        # ⇒ placeholder 空而 stats.ineligible>0 时两个界面显示不同积压数。真跨源。
        diffs.append(
            _diff("dashboard ↔ overview", "placeholder_backlog", dash["backlog_count"], ov_backlog, "cross-source")
        )

    # 板集与板级到期数: overview 的 boards 由 `_gate_due_groups`(:180) 对 due_nodes
    # group-by 派生。与本脚本的 group-by 是**同一条规则的两个实现** ⇒ 能抓实现漂移。
    ov_boards = proj.get("boards")
    ov_due_by_board: dict[str, Any] = {}
    ov_nodes_by_board: dict[str, list] = {}
    if isinstance(ov_boards, list):
        # ⛔ Codex r2 HIGH-3: 板行**重复**会被字典覆盖掉 —— `[乙, 甲, 甲]` 与 `[乙, 甲]`
        # 在 dict 里无法区分, 于是多出来的那一行在对账里完全隐形。先查唯一性。
        seen_boards: set[str] = set()
        for i, r in enumerate(ov_boards):
            # ⛔ Codex r3 MEDIUM-8: 非法板行原先被 `isinstance` 过滤掉 ⇒ 往板表里塞个
            # `null` 也是零差异。过滤 = 隐形, 必须先报出来。
            if not isinstance(r, dict) or not isinstance(r.get("board"), str) or not r["board"]:
                diffs.append(
                    _diff(
                        "overview(self)",
                        f"boards[{i}]",
                        f"板行形状非法: {type(r).__name__}",
                        "(应为带板名的 object)",
                        "reimplementation",
                    )
                )
                continue
            b = r["board"]
            if b in seen_boards:
                diffs.append(
                    _diff("overview(self)", f"boards[{b}]", "板行重复出现", "(板行应唯一)", "reimplementation")
                )
            seen_boards.add(b)
            ov_due_by_board[b] = r.get("due")
            ns = r.get("nodes")
            if not isinstance(ns, list):
                diffs.append(
                    _diff(
                        "overview(self)",
                        f"boards[{b}].nodes",
                        f"不是数组: {type(ns).__name__}",
                        "(应为数组)",
                        "reimplementation",
                    )
                )
                ns = []
            for j, n in enumerate(ns):
                if not isinstance(n, dict) or not isinstance(n.get("node"), str) or not n["node"]:
                    diffs.append(
                        _diff(
                            "overview(self)",
                            f"boards[{b}].nodes[{j}]",
                            f"节点行非法: {type(n).__name__}",
                            "(应为带 node 字符串的 object)",
                            "reimplementation",
                        )
                    )
            ov_nodes_by_board[b] = ns
    else:
        diffs.append(
            _diff(
                "overview ↔ picker",
                "boards",
                f"boards 不是数组: {type(ov_boards).__name__}",
                "(应为数组)",
                "cross-source",
            )
        )

    # ⛔ Codex r1 HIGH-1: 板集必须含**零到期板**。picker rollup 收「有成员或有占位符」的板
    # (含 due=0/future>0 的), overview 端由 `rollup_zero` 渲染成零到期行。只比到期板会让
    # 「overview 整块漏掉一块零到期板」全绿 —— 总览页少显示一块板, 判据却说三面一致。
    # ⛔ Codex r2 MEDIUM-5: rollup **缺席**时零到期行改从 `upcoming` 追加
    # (`review_overview.py:928-940`), 板集漏了 upcoming 会把**合法旧投影**误报成
    # 「overview 多出一块板」。(upcoming 由调用方在 picker 自检时算好并传入。)
    zero_source = set(rollup_rows) if rollup_rows is not None else set(upcoming)
    expected_boards = set(group_due) | zero_source
    for b in sorted(expected_boards | set(ov_due_by_board)):
        a = ov_due_by_board.get(b, "(overview 无此板)")
        c = group_due.get(b, 0 if b in zero_source else "(picker 明细无此板)")
        if not _same_count(a, c):
            # 独立性: overview 的板级 due 与本脚本的 group-by 是**同一条规则的两个实现**
            # (Codex r1 MEDIUM-6) —— 能抓实现漂移, 但**不是**第三个独立派生源。
            diffs.append(_diff("overview ↔ picker.due_nodes", f"boards[{b}].due", a, c, "reimplementation"))

    # 排序 A — 板序: 与 `expected_board_order()` 复算的**整张板表顺序**逐位比。
    # ⛔ Codex r1 HIGH-2 先把「子序列」纠成「前缀」; Codex r2 HIGH-2 进一步指出
    # **前缀之后的板序完全没人看** —— `top=[乙]` 而 overview 返回 `[乙, 丁, 甲]`
    # (应为 `[乙, 甲, 丁]`) 时前缀判据全绿, `top=[]` 时整张表的顺序都不查。
    top_names = _top_board_names(pk)
    ov_order = (
        [r["board"] for r in ov_boards if isinstance(r, dict) and isinstance(r.get("board"), str)]
        if isinstance(ov_boards, list)
        else []
    )
    exp_order = expected_board_order(top_names, group_due, rollup_rows, upcoming)
    if ov_order != exp_order:
        diffs.append(_diff("overview.boards ↔ 复算板序", "board_order", ov_order, exp_order, "reimplementation"))

    # 排序 B — 板内节点: ①身份集合 ②行序 ≡ 独立复算的紧迫度序 (见 N2)。
    notes.append(
        _note(
            "N2_row_order_contract_differs",
            "picker due_nodes 为扫描序 / overview _node_rows 为紧迫度序 —— "
            "两者不共享行序契约; 本脚本按 ①板内身份集合 ②overview 行序 ≡ "
            "独立复算的紧迫度序 两条判据对账, 不直接比原始行序",
        )
    )
    # ⛔ Codex r3 MEDIUM-9: 零到期板不在 `groups` 里 ⇒ 原循环根本不遍历它们, 往零到期板
    # 塞几个幽灵节点也是零差异。参照实现 `:919` 明写零到期行 `"nodes": []`。
    for b in sorted(set(ov_nodes_by_board) - set(groups)):
        if ov_nodes_by_board[b]:
            diffs.append(
                _diff(
                    "overview ↔ picker.due_nodes",
                    f"boards[{b}].nodes",
                    f"零到期板却有 {len(ov_nodes_by_board[b])} 个节点行",
                    "(零到期板的 nodes 应为空)",
                    "reimplementation",
                )
            )
    for b in sorted(set(ov_nodes_by_board) & set(groups)):
        # 非字符串 node 已由调用方的 picker 自检报出 (Codex r3 MEDIUM-7 上移); 这里跳过
        # 该板的跨面比较, 避免不可哈希值进集合抛 TypeError 打断整次报告。
        if any(not isinstance(r.get("node"), str) for r in groups[b]):
            continue
        ov_seq = [n.get("node") for n in ov_nodes_by_board[b] if isinstance(n, dict) and isinstance(n.get("node"), str)]
        # 独立性: 身份与行序两侧都源自同一份 due_nodes, 经**同一条契约的两个实现**
        # (overview `_gate_due_groups`+`_node_rows` / 本脚本) ⇒ reimplementation (Codex r2 MEDIUM-10)。
        if set(ov_seq) != {r["node"] for r in groups[b]}:
            diffs.append(
                _diff(
                    "overview ↔ picker.due_nodes",
                    f"boards[{b}].node_identity",
                    sorted(ov_seq),
                    sorted(r["node"] for r in groups[b]),
                    "reimplementation",
                )
            )
            continue
        expected = urgency_sorted_nodes(groups[b])
        if ov_seq != expected:
            diffs.append(
                _diff(
                    "overview ↔ urgency(picker.due_nodes)",
                    f"boards[{b}].node_order",
                    ov_seq,
                    expected,
                    "reimplementation",
                )
            )

    notes.append(
        _note(
            "N1_dashboard_board_scope",
            "Dashboard 板数取全部原白板 (Dashboard.md:21) / picker boards rollup 只收"
            "有成员或有占位符的板 (daily_review_pick.py:1072) —— 口径差, 不计 diff",
        )
    )
    return {
        "status": status,
        "due_count": ov_due,
        "placeholder_backlog": ov_backlog,
        "boards_due": ov_due_by_board,
        "board_order": ov_order,
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def list_vault_dirs(vaults_root: Path) -> list[Path]:
    """与 `review_overview._list_vault_dirs`(:779) 同一条候选规则: 非隐藏目录且含
    `.obsidian/`。⚠️ 隐藏目录被跳过 ⇒ 车道 worktree (`.claude/worktrees/...`) 天然
    不会被当成 vault, 即便它嵌在 VAULTS_ROOT 之下。"""
    dirs: list[Path] = []
    for entry in sorted(vaults_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if not (entry / ".obsidian").is_dir():
            continue
        dirs.append(entry)
    return dirs


def render_table(result: dict) -> str:
    """差异表: 每行 `视图对 | 字段 | 值A | 值B`。

    ⛔ 0 diff 的那句话必须点名**实际对了哪几面**: overview 缺席时只对了两面,
    写成"三面逐项相同"就是把「后端没起」悄悄读成「后端也对上了」。
    """
    lines = [f"## vault: {result['vault_id']}  [已对账面: {'+'.join(result['compared_views'])}]"]
    if result["semantic_diff"]:
        lines.append("视图对 | 字段 | 值A | 值B | 独立性")
        lines.append("--- | --- | --- | --- | ---")
        for d in result["semantic_diff"]:
            lines.append(f"{d['pair']} | {d['field']} | {d['a']!r} | {d['b']!r} | {d['independence']}")
    else:
        n = len(result["compared_views"])
        lines.append(
            f"semantic_diff: (空) — 本 vault {n} 面逐项相同" + ("" if n == 3 else "  ⚠️ overview 面缺席, 未覆盖总览页")
        )
    for n in result["known_scope_note"]:
        lines.append(f"note[{n['code']}]: {n['detail']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="CARD-G3-9 picker/Dashboard/总览 三面对账 (只读)")
    ap.add_argument(
        "--picker-json",
        action="append",
        default=[],
        help="picker 产出的 今日复习.json 路径 (可重复); 与 --vaults-root 二选一",
    )
    ap.add_argument("--vaults-root", help="现网 VAULTS_ROOT — 枚举各 vault 的 outputs/今日复习.json")
    ap.add_argument("--overview-json", help="离线 /overview 响应 JSON (测试用, 与 --overview-url 二选一)")
    ap.add_argument("--overview-url", help="已在运行的后端 base url, 如 http://127.0.0.1:8011")
    ap.add_argument("--out", help="报告 JSON 落盘路径 (唯一写口)")
    args = ap.parse_args(argv)

    picker_paths: list[Path] = [Path(p) for p in args.picker_json]
    if args.vaults_root:
        root = Path(args.vaults_root).resolve()
        if not root.is_dir():
            print(f"[g39] VAULTS_ROOT 不是目录: {root}", file=sys.stderr)
            return 2
        for v in list_vault_dirs(root):
            p = v / "outputs" / "今日复习.json"
            if p.is_file():
                picker_paths.append(p)
    if not picker_paths:
        print("[g39] 没有可对账的 picker 投影 (--picker-json / --vaults-root 均未给出可读文件)", file=sys.stderr)
        return 2

    ov_resp: Any = None
    not_fetched: str | None = None
    not_requested: str | None = None
    if args.overview_url:
        ov_resp, not_fetched = fetch_overview(args.overview_url)
    elif args.overview_json:
        # ⛔ Codex r2 MEDIUM-8: 离线入口的解析异常此前直接逃逸出 main(), 连差异表都不出。
        # 与 HTTP 入口同款分类: 读不了 / 解析不了 ⇒ 差异, 不是豁免。
        try:
            ov_resp = json.loads(
                Path(args.overview_json).read_text(encoding="utf-8"), parse_constant=_reject_js_nonstandard
            )
        except (OSError, ValueError) as e:
            ov_resp = {"__json_error__": f"{type(e).__name__}: {str(e)[:160]}"}
    else:
        # ⛔ Codex r2 LOW-11: 「根本没要求取」≠「试过但连不上」。写成 backend down
        # 会让读者以为探测过后端。用独立的 N5 口径码。
        not_requested = "未提供 --overview-url / --overview-json — 本次只做 picker↔Dashboard 两面对账"

    results = []
    for p in picker_paths:
        try:
            # ⛔ Codex r1 HIGH-3: 与 Dashboard 的 `JSON.parse`(`Dashboard.md:59`) **同严格度**。
            # Python 默认放行 NaN/Infinity, JS 拒收并落到 `:87`"投影损坏"。宽松解析会让
            # 含 NaN 的投影在本脚本里算出数字, 而界面上根本不出数字, 却报"两面一致"。
            payload = json.loads(p.read_text(encoding="utf-8"), parse_constant=_reject_js_nonstandard)
        except (OSError, ValueError) as e:
            # 读不到 / 解析不了 picker 投影 ⇒ 没有"同一数据集"可对账, 直接报差异行。
            # (含 JS 会拒、Python 默认会放行的非标准常量 —— 那正是一处真实的界面分歧。)
            results.append(
                {
                    "vault_id": p.parent.parent.name,
                    "views": {},
                    "compared_views": [],
                    "semantic_diff": [
                        _diff("picker(self)", "read", f"{type(e).__name__}: {str(e)[:120]}", str(p), "cross-source")
                    ],
                    "known_scope_note": [],
                }
            )
            continue
        vid = payload.get("vault_id") if isinstance(payload, dict) else None
        if not isinstance(vid, str) or not vid:
            vid = p.parent.parent.name
        entry, ov_err = (None, None)
        if not_fetched is None and not_requested is None:
            entry, ov_err = select_vault_entry(ov_resp, vid)
        results.append(
            reconcile(
                payload,
                entry,
                not_fetched_reason=not_fetched,
                not_requested_reason=not_requested,
                overview_error=ov_err,
                vault_id=vid,
            )
        )

    all_diffs = [d for r in results for d in r["semantic_diff"]]
    for r in results:
        print(render_table(r))
        print()
    two_face = [r["vault_id"] for r in results if len(r.get("compared_views") or []) < 3]
    print(
        f"[g39] semantic_diff 合计 = {len(all_diffs)}; "
        f"known_scope_note 合计 = {sum(len(r['known_scope_note']) for r in results)}"
    )
    if two_face:
        # rc 仍按 semantic_diff 判 (卡文 (b) 的 rc 语义), 但**必须**把"没对满三面"
        # 说在脸上 —— 否则 rc=0 会被读成"总览页也验过了"。
        print(f"[g39] ⚠️ 以下 vault 未对满三面 (overview 缺席), rc=0 不代表总览页已验: {two_face}")

    if args.out:
        report = {
            "schema": "g39-three-view-reconcile/1",
            "vaults": results,
            "semantic_diff_total": len(all_diffs),
            "vaults_without_overview": two_face,
        }
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[g39] 报告落盘: {out}")

    return 1 if all_diffs else 0


if __name__ == "__main__":
    sys.exit(main())
