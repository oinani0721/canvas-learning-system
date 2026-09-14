"""CARD-G3-9 [BATCH-2026-09-11-第十四批] — 三面对账脚本的先红后绿门。

夹具驱动, **零现网依赖 / 零库连接 / 不起后端**: 全部输入是本文件构造的 JSON。

结构:
  绿例   —— 自洽三面 ⇒ semantic_diff 为空, rc=0。
  负控×3 —— 各只篡改**一面一项**, 断言红在**指定差异行**(点名 pair+field),
            不接受"任意失败"(那种断言会被任何无关报错满足, 等于没测)。
  验伪锚×2(方向相反) ——
    ① known_scope_note **不**进 semantic_diff (证明脚本没把口径差误报成缺陷);
    ② overview entry corrupt / 结构降级 **必**进 semantic_diff 且 rc=1
       (证明脚本没把网关抓到的不一致读成"对账通过")。

期望值纪律 (沿用 test_daily_review_pick.py): 期望值一律**独立字面量**写死,
⛔ 禁从被测物取常量 —— 期望与被测量同源, 缺陷会让两边一起退化。
"""

import json
import sys
from pathlib import Path

import pytest

WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WT / "backend" / "scripts"))

import g39_three_view_reconcile as g39  # noqa: E402  # pyright: ignore[reportMissingImports]

#: 期望值独立字面量 —— 与被测脚本的同名常量**不共享来源**。
#: 若脚本把 NOT_COMPARABLE 改成别的字面量, 下面的断言必须红。
EXPECT_NOT_COMPARABLE = "not-comparable"


def build_picker() -> dict:
    """自洽的 picker 投影 (schema v3)。

    ⚠️ due_nodes 的**扫描序**被刻意造成与**紧迫度序**不同 —— 否则"行序对账"
    会在扫描序恰好等于紧迫度序时空转, 测不出排序判据是否真的在比。
      甲板 扫描序 [n2(空串=新卡), n1(2026-09-10)] / 紧迫度序 [n1, n2]
      乙板 扫描序 [n3(09-12),     n4(09-11)]      / 紧迫度序 [n4, n3]
    """
    return {
        "schema_version": 3,
        "vault_id": "fx-vault",
        "date": "2026-09-14",
        "generated_at": "2026-09-14T09:05:00+08:00",
        "display_tz": "Asia/Shanghai",
        "stats": {"due_nodes": 4, "ineligible": 2},
        "due_nodes": [
            {"node": "n2", "board": "甲板", "fsrs_due": "", "due_reason": "new", "bucket": "new", "why_due": "新卡"},
            {
                "node": "n1",
                "board": "甲板",
                "fsrs_due": "2026-09-10T01:00:00Z",
                "due_reason": "scheduled",
                "bucket": "due_now",
                "why_due": "已逾期",
            },
            {
                "node": "n3",
                "board": "乙板",
                "fsrs_due": "2026-09-12T02:00:00Z",
                "due_reason": "scheduled",
                "bucket": "due_now",
                "why_due": "已逾期",
            },
            {
                "node": "n4",
                "board": "乙板",
                "fsrs_due": "2026-09-11T03:00:00Z",
                "due_reason": "scheduled",
                "bucket": "due_now",
                "why_due": "已逾期",
            },
        ],
        "boards": [
            {
                "board": "甲板",
                "due": 2,
                "due_new": 1,
                "due_scheduled": 1,
                "future": 0,
                "next_due": "",
                "placeholder": 0,
                "earliest_overdue": "2026-09-10T01:00:00Z",
            },
            {
                "board": "乙板",
                "due": 2,
                "due_new": 0,
                "due_scheduled": 2,
                "future": 0,
                "next_due": "",
                "placeholder": 2,
                "earliest_overdue": "2026-09-11T03:00:00Z",
            },
        ],
        # top_boards 刻意**非字典序**(乙板在前) —— 板序判据若退化成"按板名排序"
        # 也能被这条夹具抓到。
        "top_boards": [
            {"board": "乙板", "top_node": "n4", "priority": 0.11, "pending": 2},
            {"board": "甲板", "top_node": "n1", "priority": 0.22, "pending": 2},
        ],
        "upcoming": [],
        "ineligible": {"placeholder": ["p1", "p2"], "test_excluded": [], "corrupt": []},
        "notification": None,
        "truncated": {"top_boards": False, "upcoming": False},
    }


def build_overview() -> dict:
    """与 build_picker() 自洽的 `/overview` 响应 (per-vault entry 形态)。

    板序 = top_boards 原序 (乙板, 甲板), 与 `review_overview.py:911` 的
    `prio` 排序一致; 板内节点序 = 紧迫度序 (`_node_rows` 契约)。
    """
    return {
        "generated_at": "2026-09-14T09:30:00+08:00",
        "display_tz": "Asia/Shanghai",
        "vaults_root": "/fx",
        "active_vault": "fx-vault",
        "vaults": [
            {
                "vault_id": "fx-vault",
                "path": "/fx/fx-vault",
                "status": "ok",
                "error": None,
                "board_done": [],
                "snoozed": {},
                "projection": {
                    "schema_version": 3,
                    "vault_id": "fx-vault",
                    "date": "2026-09-14",
                    "due_count": 4,
                    "placeholder_backlog": 2,
                    "recommended_board": "乙板",
                    "boards": [
                        {
                            "board": "乙板",
                            "due": 2,
                            "due_new": 0,
                            "placeholder": 2,
                            "earliest": "2026-09-11T03:00:00Z",
                            "nodes": [
                                {"node": "n4", "due_reason": "scheduled", "fsrs_due": "2026-09-11T03:00:00Z"},
                                {"node": "n3", "due_reason": "scheduled", "fsrs_due": "2026-09-12T02:00:00Z"},
                            ],
                        },
                        {
                            "board": "甲板",
                            "due": 2,
                            "due_new": 1,
                            "placeholder": 0,
                            "earliest": "2026-09-10T01:00:00Z",
                            "nodes": [
                                {"node": "n1", "due_reason": "scheduled", "fsrs_due": "2026-09-10T01:00:00Z"},
                                {"node": "n2", "due_reason": "new", "fsrs_due": ""},
                            ],
                        },
                    ],
                },
            }
        ],
    }


def run(picker: dict, overview: dict | None, tmp_path: Path) -> tuple[int, dict]:
    """把夹具落盘后跑 `main()` —— 走的是真实 CLI 入口 (含 rc 语义), 不是只调内部函数。"""
    pj = tmp_path / "picker.json"
    pj.write_text(json.dumps(picker, ensure_ascii=False), encoding="utf-8")
    argv = ["--picker-json", str(pj), "--out", str(tmp_path / "report.json")]
    if overview is not None:
        oj = tmp_path / "overview.json"
        oj.write_text(json.dumps(overview, ensure_ascii=False), encoding="utf-8")
        argv += ["--overview-json", str(oj)]
    rc = g39.main(argv)
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    return rc, report


def diffs_of(report: dict) -> list[dict]:
    return [d for v in report["vaults"] for d in v["semantic_diff"]]


def notes_of(report: dict) -> list[dict]:
    return [n for v in report["vaults"] for n in v["known_scope_note"]]


def has_diff(report: dict, pair: str, field: str) -> bool:
    """差异行是否**点名**了这个 (视图对, 字段) —— 负控断言只认这个, 不认"有失败"。"""
    return any(d["pair"] == pair and d["field"] == field for d in diffs_of(report))


# ---------------------------------------------------------------- 绿例


def test_green_three_views_zero_diff(tmp_path):
    """自洽三面 ⇒ semantic_diff 空、rc=0、且**确实对满了三面**。"""
    rc, report = run(build_picker(), build_overview(), tmp_path)
    assert diffs_of(report) == [], f"自洽夹具不应有 semantic_diff: {diffs_of(report)}"
    assert rc == 0
    assert report["vaults"][0]["compared_views"] == ["picker", "dashboard", "overview"]
    assert report["vaults_without_overview"] == []


# ---------------------------------------------------------------- 负控三段


def test_negctl_overview_board_due_plus_one(tmp_path):
    """负控①: 只把 overview 某板的 due 计数 +1 ⇒ 红在 `boards[甲板].due` 这一行。"""
    ov = build_overview()
    ov["vaults"][0]["projection"]["boards"][1]["due"] = 3  # 甲板 2 → 3
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 1
    assert has_diff(report, "overview ↔ picker.due_nodes", "boards[甲板].due"), (
        f"负控①未红在指定差异行, 实得: {diffs_of(report)}"
    )
    row = next(d for d in diffs_of(report) if d["field"] == "boards[甲板].due")
    assert (row["a"], row["b"]) == (3, 2)
    # 篡改的是板级计数, 不应牵连到期总数那一行 (否则说明判据串了)
    assert not has_diff(report, "dashboard ↔ overview", "due_count")


def test_negctl_picker_top_boards_order_swapped(tmp_path):
    """负控②: 只把 picker `top_boards` 板序逆一对 ⇒ 红在 `board_order` 这一行。"""
    pk = build_picker()
    pk["top_boards"] = [pk["top_boards"][1], pk["top_boards"][0]]  # 乙,甲 → 甲,乙
    rc, report = run(pk, build_overview(), tmp_path)
    assert rc == 1
    assert has_diff(report, "overview.boards ↔ 复算板序", "board_order"), (
        f"负控②未红在指定差异行, 实得: {diffs_of(report)}"
    )
    row = next(d for d in diffs_of(report) if d["field"] == "board_order")
    # a = overview 实际板序；b = 按 top_boards 逆序后复算出来的应有板序
    assert row["a"] == ["乙板", "甲板"] and row["b"] == ["甲板", "乙板"]


def test_negctl_stats_due_nodes_mismatch(tmp_path):
    """负控③: 只把 picker `stats.due_nodes` 改得与 `len(due_nodes)` 不等。

    ⇒ 红在 `picker.stats ↔ picker.due_nodes / due_count`, 且**同时**红在
    `dashboard ↔ overview / due_count` —— 后者正是用户在两个界面上看到的两个
    不同数字 (Dashboard 读明细长度, 总览页读 stats)。
    """
    pk = build_picker()
    pk["stats"]["due_nodes"] = 9  # len(due_nodes) 仍为 4
    rc, report = run(pk, build_overview(), tmp_path)
    assert rc == 1
    assert has_diff(report, "picker.stats ↔ picker.due_nodes", "due_count"), (
        f"负控③未红在指定差异行, 实得: {diffs_of(report)}"
    )
    row = next(d for d in diffs_of(report) if d["pair"] == "picker.stats ↔ picker.due_nodes")
    assert (row["a"], row["b"]) == (9, 4)


# ---------------------------------------------------------------- 验伪锚（方向相反的两例）


def test_falsify_anchor_scope_note_stays_out_of_semantic_diff(tmp_path):
    """验伪锚①: `known_scope_note` 登记但**不**进 semantic_diff、不影响 rc。

    覆盖两类 note 同时在场: N1(Dashboard 全板 vs picker 有成员板的口径差)、
    N2(扫描序 vs 紧迫度序)、N4(旧投影无 boards 顶层键)。
    ⛔ 反向也要守: note 非空**不得**让 rc 变 1; 且 note 的 code 必须在白名单内。
    """
    pk = build_picker()
    del pk["boards"]  # 旧投影合法形态 ⇒ 触发 N4
    rc, report = run(pk, build_overview(), tmp_path)
    codes = {n["code"] for n in notes_of(report)}
    assert {"N1_dashboard_board_scope", "N2_row_order_contract_differs", "N4_picker_rollup_absent"} <= codes, (
        f"期望的口径差未被登记: {codes}"
    )
    assert codes <= set(g39.SCOPE_NOTE_CODES), f"白名单外的 note code: {codes}"
    assert diffs_of(report) == [], f"口径差被误报成缺陷: {diffs_of(report)}"
    assert rc == 0


def test_falsify_anchor_overview_corrupt_counts_as_semantic_diff(tmp_path):
    """验伪锚②(方向相反): overview entry 为 corrupt ⇒ **必**进 semantic_diff 且 rc=1。

    ⛔ 不得落进 `not-fetched` 豁免分支。网关判 corrupt 的原因恰恰是它内部抓到了
    不一致 (`_gate_boards_rollup` 断言 rollup ≡ group-by), 跳过它等于把缺陷读成通过。
    """
    ov = build_overview()
    ov["vaults"][0]["status"] = "corrupt"
    ov["vaults"][0]["projection"] = None
    ov["vaults"][0]["error"] = "ValueError: boards[0] 全零板"
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 1
    assert has_diff(report, "overview ↔ picker", "status"), (
        f"corrupt entry 未进 semantic_diff, 实得: {diffs_of(report)}"
    )
    assert "N3_overview_not_fetched" not in {n["code"] for n in notes_of(report)}, (
        "corrupt 被误分类成 not-fetched (假绿面)"
    )
    # 仍算"对了三面"—— 连上了, 差异就是差异
    assert report["vaults"][0]["compared_views"] == ["picker", "dashboard", "overview"]


# ---------------------------------------------------------------- 加固（镜像保真 / 降级不伪装）


def test_dashboard_structural_degradation_is_not_zero(tmp_path):
    """Dashboard 结构降级 ⇒ 记 `not-comparable` 并进 semantic_diff, ⛔ 不记 0。

    记 0 会把"结构损坏"伪装成"三面一致的 0 到期"(卡文 §一(b) 点名的假绿)。
    """
    pk = build_picker()
    pk["schema_version"] = 1  # < 2 ⇒ Dashboard.md:65 降级分支
    rc, report = run(pk, build_overview(), tmp_path)
    assert rc == 1
    dash = report["vaults"][0]["views"]["dashboard"]
    assert dash["due_count"] == EXPECT_NOT_COMPARABLE
    assert dash["due_count"] != 0
    assert has_diff(report, "dashboard ↔ picker", "due_count")


def test_dashboard_bool_is_not_a_js_number(tmp_path):
    """JS `typeof true === "boolean"` 的镜像保真。

    投影里 `stats.due_nodes: true` 且无 due_nodes 明细 ⇒ Dashboard 走**降级**,
    ⛔ 不得因 Python `isinstance(True, int)` 为真而伪造出"1 张到期"。
    """
    pk = build_picker()
    del pk["due_nodes"]  # 无明细 ⇒ 只能看 stats.due_nodes
    pk["stats"]["due_nodes"] = True
    dash = g39.dashboard_recompute(pk)
    assert dash["due_count"] == EXPECT_NOT_COMPARABLE, f"bool 被当成 number, 伪造了到期数: {dash}"


def test_dashboard_backlog_falls_back_to_stats_ineligible():
    """Dashboard `:74` 的 `|| stats.ineligible` 回退必须抄到。

    placeholder 为空数组而 stats.ineligible=7 时, Dashboard 显示 7;
    只抄 `:73` 的 len(placeholder) 会显示 0 —— 与界面分叉。
    """
    pk = build_picker()
    pk["ineligible"]["placeholder"] = []
    pk["stats"]["ineligible"] = 7
    assert g39.dashboard_recompute(pk)["backlog_count"] == 7


def test_overview_non_2xx_is_a_diff_not_not_fetched(tmp_path):
    """连上了但非 2xx ⇒ semantic_diff, ⛔ 不是 not-fetched。

    `not-fetched` 只给"连不上"。把 500 读成"取不到"会静默豁免掉后端缺陷。
    """
    rc, report = run(build_picker(), {"__http_error__": "HTTP 500"}, tmp_path)
    assert rc == 1
    assert has_diff(report, "overview ↔ picker", "entry")
    assert "N3_overview_not_fetched" not in {n["code"] for n in notes_of(report)}


def test_overview_missing_vault_entry_is_a_diff(tmp_path):
    """甲支(vault 维度)取数: 响应里没有本 vault 的 entry ⇒ 差异, 不是豁免。

    ⛔ R-B14-12: 按 vault_id 定位 entry, 禁止跨 vault 合并计数 (乙支扁平读法)。
    """
    ov = build_overview()
    ov["vaults"][0]["vault_id"] = "别的库"
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 1
    row = next(d for d in diffs_of(report) if d["field"] == "entry")
    assert "fx-vault" in str(row["a"])


def test_vault_dimension_keying_does_not_leak_across_vaults(tmp_path):
    """甲支验证: 响应里有**另一个** vault 的数字时, 不得把它算进本 vault。

    乙支扁平读法(合并各 vault 计数)会让 due_count 变成 4+99, 本用例即红。
    """
    ov = build_overview()
    other = json.loads(json.dumps(ov["vaults"][0]))
    other["vault_id"] = "另一个库"
    other["projection"]["due_count"] = 99
    other["projection"]["boards"] = []
    ov["vaults"].insert(0, other)  # 放在前面, 顺带测"取第一条"式的错误实现
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 0, f"跨 vault 数据污染了本 vault 的对账: {diffs_of(report)}"
    assert report["vaults"][0]["views"]["overview"]["due_count"] == 4


def test_node_order_mirrors_urgency_not_scan_order(tmp_path):
    """行序判据确实在比**紧迫度序**, 而不是退化成扫描序或集合比较。

    把 overview 的板内节点序改成 picker 的扫描序 ⇒ 必须红在 `node_order`。
    (若判据退化成集合比较, 本用例会绿 —— 那正是要防的空转。)
    """
    ov = build_overview()
    b = ov["vaults"][0]["projection"]["boards"][0]  # 乙板: 紧迫度序 [n4, n3]
    b["nodes"] = [b["nodes"][1], b["nodes"][0]]  # 改成 [n3, n4] = 扫描序
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 1
    assert has_diff(report, "overview ↔ urgency(picker.due_nodes)", "boards[乙板].node_order"), (
        f"行序判据空转, 实得: {diffs_of(report)}"
    )
    row = next(d for d in diffs_of(report) if d["field"] == "boards[乙板].node_order")
    assert row["a"] == ["n3", "n4"] and row["b"] == ["n4", "n3"]


def test_new_card_sorts_after_overdue_not_before():
    """紧迫度契约的方向: 新卡(空串 fsrs_due)排在**已逾期之后**。

    字典序把 "" 当最小会让"逾期 3 天"被"现在"盖掉 —— CARD-D1 复核抓过的缺陷,
    这里钉死方向, 防它从对账脚本这一侧回归。
    """
    rows = [{"node": "新卡", "fsrs_due": ""}, {"node": "逾期", "fsrs_due": "2026-09-10T01:00:00Z"}]
    assert g39.urgency_sorted_nodes(rows) == ["逾期", "新卡"]


#: 对账脚本允许导入的模块 —— **允许清单**, 不是禁用清单。
#: 之所以不写禁用清单: ① 允许清单严格更强 (任何没想到的库也会被拦, 包括后端应用包);
#: ② 车道的只读静态核是对本文件逐字 grep 那些库名/端口, 把它们写进禁用清单会让
#: 判据自己命中自己, 于是"命中即真违规"这层含义就没了。
_ALLOWED_IMPORT_ROOTS = frozenset(
    {
        "__future__",
        "argparse",
        # errno: 只用于取**当前平台**的错误码常量名 (跨平台数字不可移植)。
        "errno",
        # socket: 只用于 `_is_connection_failure` 的**异常类型判定**(gaierror), 不建连接。
        "socket",
        "json",
        "sys",
        "urllib",
        "pathlib",
        "typing",
    }
)


def test_script_imports_only_stdlib_allowlist():
    """只读边界的**代码内**自证 (AST 级, 严于逐字 grep)。

    脚本只许导入允许清单内的标准库模块 ⇒ 后人加任何数据库客户端 / 后端应用包 /
    服务器进程库, 本用例立刻红。比 grep 强的地方: grep 只认它列出的那几个名字,
    允许清单连"没人想到的那个库"也拦得住。
    """
    import ast

    src = (WT / "backend" / "scripts" / "g39_three_view_reconcile.py").read_text(encoding="utf-8")
    roots: set[str] = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    assert roots <= _ALLOWED_IMPORT_ROOTS, f"脚本导入了允许清单外的模块: {sorted(roots - _ALLOWED_IMPORT_ROOTS)}"


def test_script_contains_no_service_port_literals():
    """脚本里不得出现任何服务端口字面量 (7xxx 段) —— 整段拦, 不点名具体端口。

    点名具体端口会让本文件被只读静态核 grep 命中 (见 `_ALLOWED_IMPORT_ROOTS` 注释);
    按**段**拦既避开这一点, 覆盖面又更宽 (图数据库 / 向量库 / 测试容器全在该段)。
    """
    import ast
    import re

    src = (WT / "backend" / "scripts" / "g39_three_view_reconcile.py").read_text(encoding="utf-8")
    bad_ints = [
        n.value
        for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.Constant) and type(n.value) is int and 7000 <= n.value < 8000
    ]
    assert bad_ints == [], f"脚本出现服务端口字面量: {bad_ints}"
    assert re.search(r"\b7\d{3}\b", src) is None, "脚本文本里出现 7xxx 端口字面量"


@pytest.mark.parametrize("code", list(g39.SCOPE_NOTE_CODES))
def test_scope_note_whitelist_is_closed(code):
    """`known_scope_note` 白名单是**闭集**: 白名单外的 code 必须当场炸。

    这是"不把真缺陷塞进口径差"的闸门 —— 若有人把新情况悄悄记成 note,
    `_note()` 的 assert 会拦下。
    """
    assert g39._note(code, "x")["code"] == code
    with pytest.raises(AssertionError):
        g39._note("N99_伪造的口径差", "x")


# ---------------------------------------------------------------- 代理旁路（连不上 vs 连上了）


def test_fetch_overview_opener_bypasses_system_proxy(monkeypatch):
    """本机后端的 GET 必须**直连**, 不经系统代理。

    2026-09-14 本机实测: 系统代理设在 127.0.0.1 时, urllib 默认把本机地址也交给代理;
    后端没起时代理自己回 503 ⇒ 脚本读成「连上了但后端答 503」而不是「连不上」,
    唯一的豁免口永远走不到, 「后端没运行」被报成「总览页有缺陷」。

    判据形态说明: `build_opener(ProxyHandler({}))` 传入的空 ProxyHandler **不会**
    出现在 `opener.handlers` 里 —— `ProxyHandler.__init__` 按 proxies 逐条动态挂
    `<scheme>_open` 方法, 空字典挂不出任何方法, `add_handler` 于是不收它。
    所以「**没有** ProxyHandler」正是「代理已关」的证明, 不是判据失效。

    **验伪锚**(同一函数内): 在同样的代理环境下, `urllib.request.build_opener()`
    这个默认 opener **必须**带上 ProxyHandler —— 证明本判据分得清两者, 不是恒真。
    """
    import urllib.request

    monkeypatch.setenv("http_proxy", "http://127.0.0.1:65534")
    monkeypatch.setenv("https_proxy", "http://127.0.0.1:65534")

    def proxy_handlers(op):
        return [h for h in op.handlers if isinstance(h, urllib.request.ProxyHandler)]

    # 验伪锚: 默认 opener 在此环境下会带代理
    assert proxy_handlers(urllib.request.build_opener()), "验伪锚不成立: 默认 opener 都没带代理, 本判据分不出差别"
    # 本体: 脚本的 opener 不带
    assert proxy_handlers(g39._direct_opener()) == [], "脚本的 opener 仍会走系统代理"


def test_fetch_overview_connection_failure_is_not_fetched(monkeypatch):
    """连不上(连接被拒) ⇒ 返回 not_fetched 原因, 走唯一豁免口。"""
    import urllib.error

    class _Boom:
        def open(self, req, timeout=None):
            raise urllib.error.URLError(ConnectionRefusedError(61, "Connection refused"))

    monkeypatch.setattr(g39, "_direct_opener", lambda: _Boom())
    resp, reason = g39.fetch_overview("http://127.0.0.1:1")
    assert resp is None
    assert reason is not None and "URLError" in reason


def test_fetch_overview_http_error_is_connected_not_not_fetched(monkeypatch):
    """连上了但非 2xx ⇒ **不是** not-fetched; 由调用方计入 semantic_diff。

    ⛔ HTTPError 是 URLError 的子类, 捕获顺序写反就会把后端 500 静默豁免掉。
    """
    import urllib.error

    class _Five03:
        def open(self, req, timeout=None):
            raise urllib.error.HTTPError("http://x", 503, "Service Unavailable", {}, None)

    monkeypatch.setattr(g39, "_direct_opener", lambda: _Five03())
    resp, reason = g39.fetch_overview("http://127.0.0.1:1")
    assert reason is None, "非 2xx 被误判成『连不上』"
    assert resp == {"__http_error__": "HTTP 503"}


# ---------------------------------------------------------------- Codex r1 九条的回归钉


def test_r1_high1_zero_due_board_missing_from_overview_is_a_diff(tmp_path):
    """HIGH-1: picker rollup 里合法的**零到期板**若被 overview 整块漏掉 ⇒ 必须红。

    只比「到期板」会让总览页少显示一块板而判据全绿。
    """
    pk = build_picker()
    pk["boards"].append(
        {
            "board": "丙板",
            "due": 0,
            "due_new": 0,
            "due_scheduled": 0,
            "future": 1,
            "next_due": "2026-09-20T01:00:00Z",
            "placeholder": 0,
            "earliest_overdue": "",
        }
    )
    rc, report = run(pk, build_overview(), tmp_path)  # overview 没有丙板
    assert rc == 1
    assert has_diff(report, "overview ↔ picker.due_nodes", "boards[丙板].due"), (
        f"零到期板被 overview 漏掉却没红: {diffs_of(report)}"
    )


def test_r1_high2_board_order_is_prefix_not_subsequence(tmp_path):
    """HIGH-2: 板序必须比**前缀**。

    `top_boards=[乙板]` 而 overview 顺序为 `[甲板, 乙板]` —— 过滤成子序列仍等于 `[乙板]`
    会全绿, 可总览页的首板已经不是推荐首板了。
    """
    pk = build_picker()
    pk["top_boards"] = [pk["top_boards"][0]]  # 只留乙板
    ov = build_overview()
    b = ov["vaults"][0]["projection"]["boards"]
    ov["vaults"][0]["projection"]["boards"] = [b[1], b[0]]  # 甲板排到了最前
    rc, report = run(pk, ov, tmp_path)
    assert rc == 1
    assert has_diff(report, "overview.boards ↔ 复算板序", "board_order"), (
        f"首板被换掉却没红（子序列判据空转）: {diffs_of(report)}"
    )
    row = next(d for d in diffs_of(report) if d["field"] == "board_order")
    assert row["a"] == ["甲板", "乙板"] and row["b"] == ["乙板", "甲板"]


def test_r1_high3_nan_is_rejected_like_js_json_parse(tmp_path):
    """HIGH-3: 解析器严格度也要镜像 —— JS `JSON.parse` 拒收 NaN，Python 默认放行。

    投影里混进 NaN ⇒ Dashboard 显示"投影损坏"不出数字；脚本必须同样判为差异，
    ⛔ 不得算出一个数字还报"两面一致"。
    """
    pj = tmp_path / "picker.json"
    pj.write_text('{"schema_version": 3, "stats": {"due_nodes": 1}, "due_nodes": [], "extra": NaN}', encoding="utf-8")
    rc = g39.main(["--picker-json", str(pj), "--out", str(tmp_path / "r.json")])
    report = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert rc == 1, f"含 NaN 的投影被当成正常: {report}"
    assert any(d["pair"] == "picker(self)" for d in diffs_of(report))


def test_r1_high4_read_failure_after_connect_is_not_exempted(monkeypatch):
    """HIGH-4: HTTP 200 之后的读取失败 = **已连接**, 不得落进 not-fetched 豁免。"""
    import io

    class _Resp(io.RawIOBase):
        def read(self, *a):
            raise TimeoutError("read timed out")

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class _Op:
        def open(self, req, timeout=None):
            return _Resp()

    monkeypatch.setattr(g39, "_direct_opener", lambda: _Op())
    resp, reason = g39.fetch_overview("http://127.0.0.1:1")
    assert reason is None, "已连接后的读取失败被误判成『连不上』"
    assert "__read_error__" in resp


def test_r1_medium8_invalid_utf8_body_is_classified_not_crash(monkeypatch):
    """MEDIUM-8: 正文非法 UTF-8 时不得让 CLI 崩掉、连报告都不出。"""

    class _Resp:
        def read(self, *a):
            return b"\xff\xfe not utf-8"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class _Op:
        def open(self, req, timeout=None):
            return _Resp()

    monkeypatch.setattr(g39, "_direct_opener", lambda: _Op())
    resp, reason = g39.fetch_overview("http://127.0.0.1:1")
    assert reason is None
    assert "__read_error__" in resp and "UnicodeDecodeError" in resp["__read_error__"]


def test_r1_medium5_corrupt_boards_key_is_a_diff_not_scope_note(tmp_path):
    """MEDIUM-5: `boards` 键在但类型损坏 ⇒ 差异, ⛔ 不是 N4「旧投影无此键」口径差。"""
    for bad in (None, {}, "x", [1]):
        pk = build_picker()
        pk["boards"] = bad
        rc, report = run(pk, None, tmp_path)
        assert rc == 1, f"boards={bad!r} 被当成旧投影放过了"
        assert has_diff(report, "picker.boards(self)", "structure")
        assert "N4_picker_rollup_absent" not in {n["code"] for n in notes_of(report)}


def test_r1_medium5_missing_boards_key_is_still_a_scope_note(tmp_path):
    """MEDIUM-5 的反面: 键**真的不存在**仍是合法旧投影 ⇒ N4, 不进门。"""
    pk = build_picker()
    del pk["boards"]
    rc, report = run(pk, None, tmp_path)
    assert rc == 0
    assert "N4_picker_rollup_absent" in {n["code"] for n in notes_of(report)}


def test_r1_medium6_overview_groupby_is_labelled_reimplementation(tmp_path):
    """MEDIUM-6: overview 的板级 group-by 与本脚本是同一契约的两个实现 ⇒
    独立性标 `reimplementation`, ⛔ 不得标成 `cross-source` 冒充第三个独立源。"""
    ov = build_overview()
    ov["vaults"][0]["projection"]["boards"][1]["due"] = 3
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 1
    row = next(d for d in diffs_of(report) if d["field"] == "boards[甲板].due")
    assert row["independence"] == "reimplementation", f"独立性标错: {row}"


def test_r1_medium7_null_row_makes_dashboard_not_comparable():
    """MEDIUM-7: `due_nodes=[null]` 时 Dashboard 逐行取属性抛错 → 显示"投影损坏"。

    镜像若只抄 `:68` 的 length 会记成"1 张到期", 而界面上其实什么都没有。
    """
    pk = build_picker()
    pk["due_nodes"] = [None]
    pk["stats"]["due_nodes"] = 1
    dash = g39.dashboard_recompute(pk)
    assert dash["due_count"] == EXPECT_NOT_COMPARABLE, f"null 行未触发降级: {dash}"


def test_r1_low9_duplicate_vault_entries_is_a_diff(tmp_path):
    """LOW-9: 同一 vault_id 出现多条 entry ⇒ 差异, ⛔ 不得静默取第一条。

    `[ok, corrupt]` 这种响应里挑好的那条 = 把坏的当没看见。
    """
    ov = build_overview()
    dup = json.loads(json.dumps(ov["vaults"][0]))
    dup["status"] = "corrupt"
    dup["projection"] = None
    ov["vaults"].append(dup)
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 1
    row = next(d for d in diffs_of(report) if d["field"] == "entry")
    assert "2 条 entry" in str(row["a"])


# ---------------------------------------------------------------- Codex r2 十一条的回归钉


def test_r2_high1_headerless_hang_is_not_exempted(monkeypatch):
    """r2 HIGH-1: 对端收下 GET 却不回响应头 ⇒ `open()` 超时，但那是**已连接**的故障。

    ⛔ 不得豁免成 not-fetched（后端「起来了但不响应」会被读成「后端没起」）。
    """
    import socket
    import urllib.error

    class _Op:
        def open(self, req, timeout=None):
            raise urllib.error.URLError(socket.timeout("timed out"))

    monkeypatch.setattr(g39, "_direct_opener", lambda: _Op())
    resp, reason = g39.fetch_overview("http://127.0.0.1:1")
    assert reason is None, "响应头阶段的超时被误豁免成『连不上』"
    assert "__open_error__" in resp


def test_r2_high1_connection_refused_still_exempted(monkeypatch):
    """r2 HIGH-1 的反面：真·连接被拒仍应豁免（否则「后端没起」会被报成缺陷）。"""
    import urllib.error

    class _Op:
        def open(self, req, timeout=None):
            raise urllib.error.URLError(ConnectionRefusedError(61, "Connection refused"))

    monkeypatch.setattr(g39, "_direct_opener", lambda: _Op())
    resp, reason = g39.fetch_overview("http://127.0.0.1:1")
    assert resp is None and reason is not None


def test_r2_high2_order_after_prefix_is_checked(tmp_path):
    """r2 HIGH-2: 推荐前缀**之后**的板序也必须查。

    `top=[乙]`、到期数 乙2/甲2/丁1 ⇒ 应为 `[乙, 甲, 丁]`；overview 给 `[乙, 丁, 甲]` 必红。
    """
    pk = build_picker()
    pk["top_boards"] = [pk["top_boards"][0]]  # 只留乙板
    pk["due_nodes"].append(
        {"node": "n5", "board": "丁板", "fsrs_due": "2026-09-13T01:00:00Z", "due_reason": "scheduled"}
    )
    pk["stats"]["due_nodes"] = 5
    pk["boards"].append(
        {
            "board": "丁板",
            "due": 1,
            "due_new": 0,
            "due_scheduled": 1,
            "future": 0,
            "next_due": "",
            "placeholder": 0,
            "earliest_overdue": "2026-09-13T01:00:00Z",
        }
    )
    ov = build_overview()
    b = ov["vaults"][0]["projection"]["boards"]
    ding = {
        "board": "丁板",
        "due": 1,
        "due_new": 0,
        "placeholder": 0,
        "earliest": "2026-09-13T01:00:00Z",
        "nodes": [{"node": "n5", "due_reason": "scheduled", "fsrs_due": "2026-09-13T01:00:00Z"}],
    }
    ov["vaults"][0]["projection"]["boards"] = [b[0], ding, b[1]]  # [乙, 丁, 甲] — 尾序错
    ov["vaults"][0]["projection"]["due_count"] = 5
    rc, report = run(pk, ov, tmp_path)
    assert rc == 1
    row = next(d for d in diffs_of(report) if d["field"] == "board_order")
    assert row["a"] == ["乙板", "丁板", "甲板"] and row["b"] == ["乙板", "甲板", "丁板"]


def test_r2_high3_duplicate_overview_board_row_is_a_diff(tmp_path):
    """r2 HIGH-3: overview 板行重复会被字典覆盖 ⇒ 必须先查唯一性。"""
    ov = build_overview()
    b = ov["vaults"][0]["projection"]["boards"]
    ov["vaults"][0]["projection"]["boards"] = [b[0], b[1], json.loads(json.dumps(b[1]))]  # [乙,甲,甲]
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 1
    assert has_diff(report, "overview(self)", "boards[甲板]"), f"重复板行没红: {diffs_of(report)}"


def test_r2_medium4_buckets_without_boards_is_not_legacy(tmp_path):
    """r2 MEDIUM-4: 「有 buckets 无 boards」不是任何历史形态 ⇒ 差异，不是 N4。"""
    pk = build_picker()
    del pk["boards"]
    pk["buckets"] = {"new": [], "learning": [], "due_now": [], "due_today": [], "future": []}
    rc, report = run(pk, None, tmp_path)
    assert rc == 1
    assert has_diff(report, "picker.boards(self)", "structure")
    assert "N4_picker_rollup_absent" not in {n["code"] for n in notes_of(report)}


def test_r2_medium5_legacy_upcoming_zero_board_is_not_a_false_diff(tmp_path):
    """r2 MEDIUM-5: rollup 缺席时零到期行来自 `upcoming` ⇒ 合法旧投影不得误报。"""
    pk = build_picker()
    del pk["boards"]
    pk["upcoming"] = [{"board": "丙板", "next_due": "2026-09-20T01:00:00Z", "node": "n9"}]
    ov = build_overview()
    ov["vaults"][0]["projection"]["boards"].append(
        {"board": "丙板", "due": 0, "due_new": 0, "placeholder": None, "earliest": "2026-09-20T01:00:00Z", "nodes": []}
    )
    rc, report = run(pk, ov, tmp_path)
    assert rc == 0, f"合法旧投影的 upcoming 零到期板被误报: {diffs_of(report)}"


def test_r2_medium6_rollup_due_type_is_strict(tmp_path):
    """r2 MEDIUM-6: `due: false` / `due: 2.0` 不得因 Python 的宽松相等被当成正常值。"""
    for bad in (False, True, 2.0):
        pk = build_picker()
        pk["boards"][0]["due"] = bad
        rc, report = run(pk, None, tmp_path)
        assert rc == 1, f"boards[0].due={bad!r} 被当成正常计数"
        assert has_diff(report, "picker.boards(self)", "structure")


def test_r2_medium7_generated_at_throwing_value_degrades_dashboard():
    """r2 MEDIUM-7: `generated_at` 带 toString 键 ⇒ JS 模板插值抛错 → 界面不出数字。"""
    pk = build_picker()
    pk["generated_at"] = {"toString": None}
    assert g39.dashboard_recompute(pk)["due_count"] == EXPECT_NOT_COMPARABLE


def test_r2_medium8_offline_overview_parse_error_is_classified(tmp_path):
    """r2 MEDIUM-8: `--overview-json` 解析失败不得逃逸出 main()，要出差异表。"""
    pj = tmp_path / "picker.json"
    pj.write_text(json.dumps(build_picker(), ensure_ascii=False), encoding="utf-8")
    oj = tmp_path / "ov.json"
    oj.write_text('{"vaults": [], "x": NaN}', encoding="utf-8")
    rc = g39.main(["--picker-json", str(pj), "--overview-json", str(oj), "--out", str(tmp_path / "r.json")])
    report = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert any("不是 JSON" in str(d["a"]) for d in diffs_of(report)), diffs_of(report)


def test_r2_medium9_unhashable_node_does_not_abort_reconcile(tmp_path):
    """r2 MEDIUM-9: `node: []` 不得让集合构造抛错打断对账、连差异表都不出。"""
    pk = build_picker()
    pk["due_nodes"][0]["node"] = []
    rc, report = run(pk, build_overview(), tmp_path)
    assert rc == 1
    assert has_diff(report, "picker.due_nodes(self)", "boards[甲板].node")


def test_r2_medium10_node_order_labelled_reimplementation(tmp_path):
    """r2 MEDIUM-10: 节点排序两侧同出一份契约 ⇒ 标 `reimplementation`。"""
    ov = build_overview()
    b = ov["vaults"][0]["projection"]["boards"][0]
    b["nodes"] = [b["nodes"][1], b["nodes"][0]]
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 1
    row = next(d for d in diffs_of(report) if d["field"] == "boards[乙板].node_order")
    assert row["independence"] == "reimplementation"


def test_r2_low11_not_requested_is_distinct_from_not_fetched(tmp_path):
    """r2 LOW-11: 「根本没要求取」用 N5，⛔ 不得写成 N3 的 backend down。"""
    pj = tmp_path / "picker.json"
    pj.write_text(json.dumps(build_picker(), ensure_ascii=False), encoding="utf-8")
    rc = g39.main(["--picker-json", str(pj), "--out", str(tmp_path / "r.json")])
    report = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert rc == 0
    codes = {n["code"] for n in notes_of(report)}
    assert "N5_overview_not_requested" in codes
    assert "N3_overview_not_fetched" not in codes, "没试过被写成了『连不上』"


# ---------------------------------------------------------------- Codex r3 十一条的回归钉


def test_r3_high1_redirect_is_not_followed(monkeypatch):
    """r3 HIGH-1: 不跟随重定向 —— 否则「首跳 302、次跳被拒」会整体判成连不上，
    可**第一跳后端明明已经响应过**。不跟随 ⇒ 302 变成非 2xx ⇒ 计入差异。"""
    import urllib.request

    handlers = [type(h).__name__ for h in g39._direct_opener().handlers]
    assert "_NoRedirect" in handlers, f"opener 仍会自动跟随重定向: {handlers}"
    # 验伪锚：默认 opener 带的是会跟随的 HTTPRedirectHandler
    default = [type(h).__name__ for h in urllib.request.build_opener().handlers]
    assert "HTTPRedirectHandler" in default and "_NoRedirect" not in default


def test_r3_medium2_errno_set_comes_from_current_platform():
    """r3 MEDIUM-2: errno 白名单必须取**当前平台**的常量，不能混两平台的数字。"""
    import errno

    assert errno.ECONNREFUSED in g39._CONNECT_FAILURE_ERRNOS
    assert errno.EHOSTUNREACH in g39._CONNECT_FAILURE_ERRNOS
    # ETIME 在 macOS 上是 101（Linux 的 ECONNREFUSED 也是 111 系），不得混进来
    if hasattr(errno, "ETIME"):
        assert errno.ETIME not in g39._CONNECT_FAILURE_ERRNOS, "把超时类 errno 收进了连接失败"
    if hasattr(errno, "ENETDOWN"):
        assert errno.ENETDOWN in g39._CONNECT_FAILURE_ERRNOS


def test_r3_medium3_protocol_and_url_errors_do_not_escape(monkeypatch):
    """r3 MEDIUM-3: `BadStatusLine` / `ValueError`（未知 scheme、非法端口）不得逃逸。"""
    import http.client

    for exc in (http.client.BadStatusLine("garbage"), ValueError("unknown url type"), http.client.InvalidURL("bad")):

        class _Op:
            def __init__(self, e):
                self.e = e

            def open(self, req, timeout=None):
                raise self.e

        monkeypatch.setattr(g39, "_direct_opener", lambda e=exc: _Op(e))
        resp, reason = g39.fetch_overview("http://127.0.0.1:1")
        assert reason is None, f"{type(exc).__name__} 被误判成『连不上』"
        assert "__open_error__" in resp, f"{type(exc).__name__} 逃逸了: {resp}"


def test_r3_medium4_array_propagates_element_throw():
    """r3 MEDIUM-4: 数组会把元素的字符串化异常传播出来（`join` 对每个元素再 String()）。"""
    assert g39._js_interp_throws([{"toString": None}]) is True
    assert g39._js_interp_throws([[{"toString": None}]]) is True
    assert g39._js_interp_throws([1, "x", {"a": 1}]) is False


def test_r3_medium5_backlog_interp_throw_degrades_dashboard():
    """r3 MEDIUM-5: `backlogCnt` 自己也被插值 ⇒ 回退值损坏时界面不出数字（两面假绿源头）。"""
    pk = build_picker()
    pk["ineligible"]["placeholder"] = []
    pk["stats"]["ineligible"] = {"toString": None}
    assert g39.dashboard_recompute(pk)["backlog_count"] == EXPECT_NOT_COMPARABLE


def test_r3_medium6_false_backlog_is_not_equal_to_zero(tmp_path):
    """r3 MEDIUM-6: Dashboard 显示「false 张」≠ 总览页显示「0 张」。"""
    pk = build_picker()
    pk["ineligible"]["placeholder"] = []
    pk["boards"][1]["placeholder"] = 0
    pk["stats"]["ineligible"] = False
    ov = build_overview()
    ov["vaults"][0]["projection"]["placeholder_backlog"] = 0
    ov["vaults"][0]["projection"]["boards"][0]["placeholder"] = 0
    rc, report = run(pk, ov, tmp_path)
    assert rc == 1
    assert has_diff(report, "dashboard ↔ overview", "placeholder_backlog"), diffs_of(report)


def test_r3_medium7_picker_self_check_runs_without_overview(tmp_path):
    """r3 MEDIUM-7: picker 自检**不依赖 overview 在场** —— 走 N5 两面时也必须执行。"""
    pk = build_picker()
    pk["due_nodes"][0]["node"] = []
    rc, report = run(pk, None, tmp_path)  # overview 缺席
    assert rc == 1, "overview 缺席时 picker 自检没跑（自检旁路）"
    assert has_diff(report, "picker.due_nodes(self)", "boards[甲板].node")


def test_r3_medium8_malformed_overview_rows_are_reported(tmp_path):
    """r3 MEDIUM-8: 被过滤掉的非法板行 / 节点行 = 隐形，必须报出来。"""
    ov = build_overview()
    ov["vaults"][0]["projection"]["boards"].append(None)
    rc, report = run(build_picker(), ov, tmp_path)
    assert rc == 1
    assert any(d["pair"] == "overview(self)" and "boards[2]" in d["field"] for d in diffs_of(report)), diffs_of(report)

    ov2 = build_overview()
    ov2["vaults"][0]["projection"]["boards"][0]["nodes"].append({"node": []})
    rc2, report2 = run(build_picker(), ov2, tmp_path)
    assert rc2 == 1
    assert any(d["pair"] == "overview(self)" and "nodes[2]" in d["field"] for d in diffs_of(report2)), diffs_of(report2)


def test_r3_medium9_zero_due_board_nodes_must_be_empty(tmp_path):
    """r3 MEDIUM-9: 零到期板的节点列表也要查 —— 塞幽灵节点不得全绿。"""
    pk = build_picker()
    pk["boards"].append(
        {
            "board": "丙板",
            "due": 0,
            "due_new": 0,
            "due_scheduled": 0,
            "future": 1,
            "next_due": "2026-09-20T01:00:00Z",
            "placeholder": 0,
            "earliest_overdue": "",
        }
    )
    ov = build_overview()
    ov["vaults"][0]["projection"]["boards"].append(
        {
            "board": "丙板",
            "due": 0,
            "due_new": 0,
            "placeholder": 0,
            "earliest": "2026-09-20T01:00:00Z",
            "nodes": [{"node": "phantom", "due_reason": "new", "fsrs_due": ""}],
        }
    )
    rc, report = run(pk, ov, tmp_path)
    assert rc == 1
    assert has_diff(report, "overview ↔ picker.due_nodes", "boards[丙板].nodes"), diffs_of(report)


def test_r3_medium10_corrupt_next_due_does_not_abort(tmp_path):
    """r3 MEDIUM-10: 损坏的 `next_due` 不得让排序抛 TypeError 打断整次报告。"""
    pk = build_picker()
    for b, nd in (("丙板", {"x": 1}), ("丁板", "2026-09-20T01:00:00Z")):
        pk["boards"].append(
            {
                "board": b,
                "due": 0,
                "due_new": 0,
                "due_scheduled": 0,
                "future": 1,
                "next_due": nd,
                "placeholder": 0,
                "earliest_overdue": "",
            }
        )
    rc, report = run(pk, build_overview(), tmp_path)  # 不抛异常即为通过
    assert rc == 1
    assert report["vaults"][0]["semantic_diff"], "损坏输入应产生差异行"


def test_r3_medium11_duplicate_upcoming_is_reported(tmp_path):
    """r3 MEDIUM-11: 同名 upcoming 会被字典覆盖 ⇒ 必须报出；非字符串 next_due 同理。"""
    pk = build_picker()
    del pk["boards"]
    pk["upcoming"] = [
        {"board": "丙板", "next_due": "2026-09-20T01:00:00Z", "node": "a"},
        {"board": "丙板", "next_due": "2026-09-21T01:00:00Z", "node": "b"},
    ]
    rc, report = run(pk, None, tmp_path)
    assert rc == 1
    assert has_diff(report, "picker.upcoming(self)", "structure"), diffs_of(report)
