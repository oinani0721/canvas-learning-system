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
  - `structurally-guaranteed` 当前实现下恒真 (同一规则 / 上游网关已内部断言),
                              保留是为了守**未来改动**, 不得冒充独立第三源。
  典型: `review_overview._gate_boards_rollup`(:283) 在网关内部已断言「rollup 的
  到期板集合+计数 ≡ due_nodes group-by 派生」, 不等即 raise → entry 变 corrupt。
  所以 overview **成功返回 entry 时**该子项在 overview 侧恒真; 真正能翻转它的只有
  picker 自身的两源 (`boards` rollup vs `due_nodes` group-by), 那一条本脚本直接
  在 picker JSON 上算, 不假手 overview —— 否则 overview 一 corrupt 就没人算了。
"""

from __future__ import annotations

import argparse
import json
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
    "N4_picker_rollup_absent",
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
    due_cnt = len(due_nodes) if has_detail else stats_due  # :68
    ineligible = payload.get("ineligible")
    placeholder = ineligible.get("placeholder") if isinstance(ineligible, dict) else None
    backlog_names = placeholder if isinstance(placeholder, list) else []  # :73
    fallback = stats.get("ineligible") if stats is not None else None  # :74 `?? 0`
    fallback = 0 if fallback is None else fallback
    backlog_cnt = len(backlog_names) or fallback  # :74 `||` — 左值 int, 与 JS 同语义
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


def picker_rollup_due(payload: dict) -> dict[str, int] | None:
    """picker 顶层 `boards` rollup 的逐板 `due` (daily_review_pick.py:1071-1088)。

    返回 None = 投影无 `boards` 顶层键 (旧投影合法形态, 见 SCOPE_NOTE_CODES N4)。
    """
    rollup = payload.get("boards")
    if "boards" not in payload or not isinstance(rollup, list):
        return None
    out: dict[str, int] = {}
    for r in rollup:
        if not isinstance(r, dict):
            continue
        board = r.get("board")
        if isinstance(board, str) and board:
            out[board] = r.get("due")
    return out


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


def fetch_overview(base_url: str, timeout: float = 10.0) -> tuple[Any, str | None]:
    """对**已在运行**的后端只读 GET `/api/v1/review/overview`。

    返回 `(响应对象, not_fetched_reason)`。⛔ `not_fetched_reason` 非 None **只**用于
    「连不上」(连接被拒 / 超时 / DNS) —— 那时 overview 这一面整体缺席。
    连上了但非 2xx / 响应不是 JSON ⇒ 抛回 `(None, None)` 之外的形态? 不: 这两种
    都是**连上了**, 由调用方计入 semantic_diff (见 `reconcile` 的 fetch_error 分支)。

    ⚠️ `urllib.error.HTTPError` 是 `URLError` 的子类, 必须**先**捕 HTTPError,
    否则一个 500 会被误判成"连不上"并静默豁免掉后端缺陷。
    """
    url = base_url.rstrip("/") + OVERVIEW_PATH
    req = urllib.request.Request(url, method="GET")  # noqa: S310 — 固定 http(s) 本机地址
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return {"__http_error__": f"HTTP {e.code}"}, None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return None, f"{type(e).__name__}: {str(e)[:160]}"
    try:
        return json.loads(body), None
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
    for e in entries:
        if isinstance(e, dict) and e.get("vault_id") == vault_id:
            return e, None
    return None, f"overview 响应中无 vault_id={vault_id!r} 的 entry"


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
    rollup_due = picker_rollup_due(pk)

    # ---- ① 到期卡片数 ----------------------------------------------------
    # picker 内两源: stats 权威计数 vs 明细长度。生成期 `stats["due_nodes"] =
    # len(due_rows)`(daily_review_pick.py:1060) 恒等, 但**消费侧拿到的是文件** ——
    # 手改/损坏的投影会让二者分叉, 而 Dashboard 读明细长度、overview 读 stats,
    # 于是两个界面显示不同数字。这是三面对账真正要抓的第一类缺陷。
    if p_stats_due != p_len_due:
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
    if rollup_due is None:
        notes.append(
            _note(
                "N4_picker_rollup_absent",
                f"vault={vid!r} 的投影无 boards 顶层键 (旧投影合法形态); rollup ↔ group-by 子项 not-applicable",
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

    # ---- ③ overview 面 ---------------------------------------------------
    ov_view: Any
    if not_fetched_reason is not None:
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
        ov_view = _reconcile_overview(overview_entry, vid, p_stats_due, dash, group_due, groups, pk, diffs, notes)

    # ⛔ 实际对上的面 —— not-fetched 时只有两面, 报告与终端都必须如实说,
    # 否则"后端没起"会被读成"三面一致"(Codex 问题④的假绿面)。
    compared = ["picker", "dashboard"] if not_fetched_reason is not None else ["picker", "dashboard", "overview"]
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
    if ov_due != p_stats_due:
        diffs.append(_diff("overview ↔ picker.stats", "due_count", ov_due, p_stats_due, "structurally-guaranteed"))
    if dash["due_count"] != ov_due:
        diffs.append(_diff("dashboard ↔ overview", "due_count", dash["due_count"], ov_due, "cross-source"))
    ov_backlog = proj.get("placeholder_backlog")
    if dash["backlog_count"] != ov_backlog:
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
        for r in ov_boards:
            if isinstance(r, dict) and isinstance(r.get("board"), str):
                ov_due_by_board[r["board"]] = r.get("due")
                ns = r.get("nodes")
                ov_nodes_by_board[r["board"]] = ns if isinstance(ns, list) else []
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

    ov_due_nonzero = {b: d for b, d in ov_due_by_board.items() if d != 0}
    for b in sorted(set(ov_due_nonzero) | set(group_due)):
        a = ov_due_by_board.get(b, "(overview 无此板)")
        c = group_due.get(b, "(picker 明细无此板)")
        if a != c:
            diffs.append(_diff("overview ↔ picker.due_nodes", f"boards[{b}].due", a, c, "cross-source"))

    # 排序 A — 板序: overview `board_rows.sort(key=(prio, -due, board))`(:911),
    # `prio[b]=i` 取自 top_boards 下标(:831) ⇒ 在榜板按 top_boards 原序排最前。
    top_names = _top_board_names(pk)
    ov_order = (
        [r["board"] for r in ov_boards if isinstance(r, dict) and isinstance(r.get("board"), str)]
        if isinstance(ov_boards, list)
        else []
    )
    ov_ranked_prefix = [b for b in ov_order if b in set(top_names)]
    if top_names and ov_ranked_prefix != top_names:
        diffs.append(
            _diff("picker.top_boards ↔ overview.boards", "board_order", top_names, ov_ranked_prefix, "cross-source")
        )

    # 排序 B — 板内节点: ①身份集合 ②行序 ≡ 独立复算的紧迫度序 (见 N2)。
    notes.append(
        _note(
            "N2_row_order_contract_differs",
            "picker due_nodes 为扫描序 / overview _node_rows 为紧迫度序 —— "
            "两者不共享行序契约; 本脚本按 ①板内身份集合 ②overview 行序 ≡ "
            "独立复算的紧迫度序 两条判据对账, 不直接比原始行序",
        )
    )
    for b in sorted(set(ov_nodes_by_board) & set(groups)):
        ov_seq = [n.get("node") for n in ov_nodes_by_board[b] if isinstance(n, dict)]
        if set(ov_seq) != {r.get("node") for r in groups[b]}:
            diffs.append(
                _diff(
                    "overview ↔ picker.due_nodes",
                    f"boards[{b}].node_identity",
                    sorted(x for x in ov_seq if isinstance(x, str)),
                    sorted(str(r.get("node")) for r in groups[b]),
                    "cross-source",
                )
            )
            continue
        expected = urgency_sorted_nodes(groups[b])
        if ov_seq != expected:
            diffs.append(
                _diff(
                    "overview ↔ urgency(picker.due_nodes)", f"boards[{b}].node_order", ov_seq, expected, "cross-source"
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
    if args.overview_url:
        ov_resp, not_fetched = fetch_overview(args.overview_url)
    elif args.overview_json:
        ov_resp = json.loads(Path(args.overview_json).read_text(encoding="utf-8"))
    else:
        not_fetched = "未提供 --overview-url / --overview-json (overview 面缺席)"

    results = []
    for p in picker_paths:
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            # 读不到 picker 投影 ⇒ 这一 vault 根本没有"同一数据集"可对账, 直接报错行。
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
        if not_fetched is None:
            entry, ov_err = select_vault_entry(ov_resp, vid)
        results.append(reconcile(payload, entry, not_fetched_reason=not_fetched, overview_error=ov_err, vault_id=vid))

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
