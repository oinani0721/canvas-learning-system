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
    assert has_diff(report, "picker.top_boards ↔ overview.boards", "board_order"), (
        f"负控②未红在指定差异行, 实得: {diffs_of(report)}"
    )
    row = next(d for d in diffs_of(report) if d["field"] == "board_order")
    assert row["a"] == ["甲板", "乙板"] and row["b"] == ["乙板", "甲板"]


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
