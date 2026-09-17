"""CARD-G6-8 — 五面复习视图一致性契约门（BATCH-2026-09-11-第十四批）。

锁定的性质: 同一份 state 输入下, 复习视图的五个面对每块板给出的
桶位 / 显示日 / 推迟 / 完成结论逐字段相等; 任一面的口径被改动, 本门必红。

⛔ 本门跑**子进程**而不是在进程内调 `contract.run()`: 契约脚本要在 import
被测模块**之前**设置 `CANVAS_TZ` / `VAULTS_ROOT`（picker 的 `_DISPLAY_TZ` 是
模块级常量, import 那一刻就固化）。同一个 pytest 进程里换时区再 import 拿到的
是第一次的值 —— 那会让「换时区跑」这一半用例静默失效（假绿）。子进程每次从
干净解释器起, 是唯一能真跑到「换了时区」的形态。
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

WT = Path(__file__).resolve().parents[3]
SCRIPT = WT / "backend" / "scripts" / "g68_five_view_contract.py"
PY = sys.executable

sys.path.insert(0, str(WT / "backend" / "scripts"))
import g68_five_view_contract as contract  # noqa: E402  # pyright: ignore[reportMissingImports]

#: 契约跑的基准时刻 —— 带偏移, 且当地时刻 < 20:00（tonight_available 为真的那一档）。
NOW_EARLY = "2026-09-12T03:00:00+00:00"  # Asia/Shanghai 当地 11:00
#: 当地时刻 ≥ 20:00 的那一档（同日, 上海 21:00）。
NOW_LATE = "2026-09-12T13:00:00+00:00"

TZ_SH = "Asia/Shanghai"
TZ_LA = "America/Los_Angeles"


def _run(tmp_path: Path, now: str = NOW_EARLY, tz: str = TZ_SH, name: str = "r") -> tuple[int, dict, str, str]:
    """跑一次契约脚本, 返回 (rc, 报告 JSON, stdout, stderr)。

    ⛔ stderr 也要带出来（Codex r3 LOW-8）: 契约判红时把计算期被测模块的 stdout
    回放到 stderr, 丢掉它等于「直接跑 CLI 看得到诊断、经本门跑就看不到」。
    """
    out = tmp_path / f"{name}.json"
    proc = subprocess.run(
        [PY, str(SCRIPT), "--now", now, "--tz", tz, "--json", str(out)],
        capture_output=True,
        text=True,
        cwd=str(WT / "backend"),
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert out.is_file(), f"契约脚本没有产出报告\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    return proc.returncode, json.loads(out.read_text(encoding="utf-8")), proc.stdout, proc.stderr


# ───────────────────────────── (d)① 主断言 ─────────────────────────────


def test_five_view_matrix_is_field_wise_consistent(tmp_path):
    """五面矩阵逐板逐字段全等（已登记分歧除外）。"""
    rc, report, _, err = _run(tmp_path)
    assert report["undeclared_divergences"] == [], (
        "五面出现未登记的口径分歧:\n"
        # ⛔ 每行带**结构化判据码**（Codex r4 MEDIUM-7）: 负控的文本锚绑在这个码上,
        #    而不是「面=picker」这类人话 —— 被测模块的诊断输出经 stderr / 断言消息
        #    回流后也会带 `E ` 前缀与字段名字样, 拿人话当锚就分不清「门抓到了」和
        #    「日志里恰好有这个词」。这串码只有本判据会产出。
        + "\n".join(
            f"  {contract.diff_code(r)} 板={r['board']} 字段={r['field']} 面={r['face']} "
            f"值={r['value']} ≠ 多数派{r['majority_faces']}={r['majority_value']}"
            for r in report["undeclared_divergences"]
        )
        # ⛔ 把契约的 stderr 一起贴出来（Codex r3 LOW-8）: 判红时契约会把计算期
        #    被测模块的 stdout 回放到 stderr, 而 `_run()` 原先把它丢掉 ——
        #    直接跑 CLI 看得到诊断、经本门跑就看不到, 排障的人拿不到同一份信息。
        + (f"\n── 契约 stderr ──\n{err}" if err.strip() else "")
    )
    assert report["verdict"] == "PASS", f"verdict={report['verdict']}\n── 契约 stderr ──\n{err}"
    assert rc == 0


def test_matrix_actually_compares_something(tmp_path):
    """验伪锚: 矩阵不是恒绿 —— 至少两个面在至少一个字段上真的被比过。

    ⛔ 没有这条, 「零分歧」既可能是真一致, 也可能是「所有面都不产出任何字段」
    （矩阵全是 NOT_PRODUCED, 比对循环一次都没进去）。
    """
    _, report, _, _ = _run(tmp_path)
    compared = 0
    for board in report["boards"]:
        for field in contract.FIELDS:
            producing = [f for f, v in report["matrix"][board][field].items() if v != contract.NOT_PRODUCED]
            if len(producing) >= 2:
                compared += 1
    assert compared > 0, "矩阵里没有任何一格被两个以上的面同时产出 —— 判据是恒绿的"
    # 桶位这一列必须是被真比过的那一格（它是本契约的核心）
    bucket_compared = [
        b
        for b in report["boards"]
        if len([f for f, v in report["matrix"][b]["bucket"].items() if v != contract.NOT_PRODUCED]) >= 2
    ]
    assert bucket_compared, "没有任何一块板的 bucket 被两个面同时产出 —— 桶位一致性根本没被测"


# ─────────────────────── 已登记分歧：按身份钉死 ───────────────────────


def test_declared_divergences_are_pinned_by_identity(tmp_path):
    """白名单按**身份**钉死, 不是「允许 N 条」。

    ⛔ 计数式白名单（「≤1 条分歧就放行」）挡不住等长替换: 换一条别的分歧进来、
    数量不变就蒙混过关。这里把 (面, 字段) 对逐个写死在测试侧。
    """
    assert {(r["face"], r["field"]) for r in contract.DECLARED_DIVERGENCES} == {
        ("skill_inbox", "display_day"),
    }, "已登记分歧集合变了 —— 新增/删除必须同时更新验收单台账与本断言"

    _, report, _, _ = _run(tmp_path)
    for row in report["declared_divergences"]:
        assert (row["face"], row["field"]) in {("skill_inbox", "display_day")}


def test_declared_divergence_is_a_predicate_not_a_blank_cheque():
    """豁免只认「那一种已知取值」, 不是「那一格随便怎么错都行」。

    ⛔ Codex r1 HIGH-2: 原先只按 (面, 字段) 匹配 —— 把 inbox 的日期改成 2099 年、
    甚至让它整块板缺席, 都照样落进「已登记」而不判红。白名单一旦不带谓词, 它豁免
    的就不是那条已知分歧, 而是那一整格。
    """
    now = datetime(2026, 9, 12, 3, 0, tzinfo=timezone.utc)
    ctx = {"now": now}
    right = now.astimezone(timezone(timedelta(hours=8))).date().isoformat()
    assert contract._is_declared("skill_inbox", "display_day", right, ctx) is True
    for wrong in ("2099-01-01", "1970-01-01", contract.MISSING, contract.NOT_PRODUCED, None):
        assert contract._is_declared("skill_inbox", "display_day", wrong, ctx) is False, f"{wrong!r} 不该落进已登记豁免"
    # 其它面/字段一律不在豁免范围内
    assert contract._is_declared("picker", "display_day", right, ctx) is False
    assert contract._is_declared("skill_inbox", "bucket", right, ctx) is False
    # 谓词取不到上下文时按未登记处理（宁可多判红也不吞）
    assert contract._is_declared("skill_inbox", "display_day", right, {}) is False


def test_declared_producer_may_not_hand_back_not_produced():
    """声明产出方交出 NOT_PRODUCED ⇒ 当场抛, 不许整格退出比较。

    ⛔ Codex r1 HIGH-1: 通知缺席时那一面原先返回 NOT_PRODUCED, 被比对循环过滤掉,
    于是「今天根本没发通知」在矩阵里表现为零分歧。
    """
    per_face = {
        "review_overview": {"板A": {"display_day": "2026-09-12"}},
        "picker": {"板A": {"display_day": "2026-09-12"}},
        "skill_inbox": {"板A": {"display_day": "2026-09-12"}},
        "notification": {"板A": {"display_day": contract.NOT_PRODUCED}},
    }
    for field in ("bucket", "projection_day", "snoozed", "done"):
        for face in ("review_overview", "picker"):
            per_face[face]["板A"][field] = "x"
        per_face["notification"]["板A"].setdefault("projection_day", "x")
    with pytest.raises(contract.ContractError, match="NOT_PRODUCED"):
        contract.check_producers_declaration(per_face, ["板A"])


def test_field_producers_pinned_by_identity():
    """`FIELD_PRODUCERS` 按**身份**钉死, 不只是「数量 ≥ 2」。

    ⛔ Codex r1 MEDIUM-5 → r2 MEDIUM-4: 只查数量下限的话, 把 overview 的
    `projection_day` 声明与实现**一起**删掉仍然全绿; `("picker", "picker")`
    这种同名重复也满足数量检查。逐列写死产出方集合。
    """
    assert contract.FIELD_PRODUCERS == {
        "bucket": ("review_overview", "picker"),
        "display_day": ("review_overview", "picker", "skill_inbox", "notification"),
        "projection_day": ("review_overview", "picker", "notification"),
        "snoozed": ("review_overview", "picker"),
        "done": ("review_overview", "picker"),
    }, "产出方声明变了 —— 改动必须同时更新验收单 census 与本断言"
    for field, producers in contract.FIELD_PRODUCERS.items():
        assert len(set(producers)) >= 2, f"{field} 的产出方去重后不足两个"
        assert set(producers) <= set(contract.FACES), f"{field} 声明了不存在的面"
    assert set(contract.FIELD_PRODUCERS) == set(contract.FIELDS)


def test_missing_never_counts_as_agreement():
    """两个产出方**同时**缺同一块板 ⇒ 仍要判红, 不许当成「一致」。

    ⛔ Codex r2 HIGH-1: `MISSING` 原先只是个普通取值 —— 两面同缺时取值集合只剩
    一个元素, 于是零分歧; 缺值多数派还能把唯一真实分歧挤成少数派。
    """
    both_missing = {
        "板Z": _blank(
            "bucket",
            {
                "review_overview": contract.MISSING,
                "picker": contract.MISSING,
                "review_app": contract.NOT_PRODUCED,
                "skill_recap": contract.NOT_PRODUCED,
                "skill_inbox": contract.NOT_PRODUCED,
                "notification": contract.NOT_PRODUCED,
            },
        )
    }
    undeclared, declared = contract.diff_matrix(both_missing)
    assert declared == []
    assert {r["face"] for r in undeclared} == {"review_overview", "picker"}, (
        "两面同时缺一块板被当成了「一致」—— MISSING 混进了取值比较"
    )

    # 缺值多数派不得把唯一的真实分歧挤成少数派而免于上报
    majority_missing = {
        "板W": _blank(
            "display_day",
            {
                "review_overview": contract.MISSING,
                "picker": contract.MISSING,
                "notification": contract.MISSING,
                "skill_inbox": "2026-09-12",
                "review_app": contract.NOT_PRODUCED,
                "skill_recap": contract.NOT_PRODUCED,
            },
        )
    }
    undeclared2, _ = contract.diff_matrix(majority_missing)
    assert {r["face"] for r in undeclared2} == {"review_overview", "picker", "notification"}, (
        "缺值被当成多数派了 —— 三个缺值反而成了参照"
    )


def test_bucket_node_identity_is_anchored_on_the_fixture():
    """板级锚之外还有**节点级**锚: 板还在、板级清单也完整时, 少一个节点必须判红。

    ⛔ Codex r3 HIGH-2: 两面同时丢掉板内的**一个节点**, 板级锚毫无反应。
    """
    full = {
        face: {
            board: {"bucket": tuple(sorted((n, "due_now") for b, n in contract.FIXTURE_BUCKET_NODES if b == board))}
            for board in contract.FIXTURE_BOARDS
        }
        for face in contract.FIELD_PRODUCERS["bucket"]
    }
    contract.check_bucket_node_identity(full)  # 完整时不抛

    short = {face: {b: dict(r) for b, r in rows.items()} for face, rows in full.items()}
    for rows in short.values():
        rows["板-到期"]["bucket"] = tuple(p for p in rows["板-到期"]["bucket"] if p[0] != "同板未来")
    with pytest.raises(contract.ContractError, match="与 fixture 不符"):
        contract.check_bucket_node_identity(short)


def test_board_index_does_not_come_from_the_faces():
    """矩阵行索引有**独立于被测面**的锚（fixture 自报的板清单）。

    ⛔ Codex r2 HIGH-1 的更深一层: 行索引若从各面反推, 一块板从**所有面同时**
    消失时它整行都不存在 —— 连个可比的格子都没有, 判据看起来绿得很干净。
    """
    assert contract.FIXTURE_BOARDS, "fixture 板清单为空 —— 行索引又退回从面反推了"
    # 清单必须与 fixture 真造出来的板对得上（脚本内部也有同款对账, 这里是外部复证）
    now = datetime(2026, 9, 12, 3, 0, tzinfo=timezone.utc)
    nodes = contract.build_nodes(now, timezone(timedelta(hours=8)))
    declared = {
        line.split("原白板/", 1)[1].split("]]", 1)[0]
        for md in nodes.values()
        for line in md.splitlines()
        if "原白板/" in line
    }
    assert contract.FIXTURE_BOARDS <= declared, (
        f"FIXTURE_BOARDS 与 fixture 脱钩: {sorted(contract.FIXTURE_BOARDS - declared)}"
    )


def test_ranked_completeness_is_checked():
    """空队列 / 队列成员与期望集合不符, 都要当场抛。

    ⛔ Codex r2 MEDIUM-5 → r3 MEDIUM-4: `ranked=[]` 原先照样过; 而「只要求点名的
    那几块在场」时, 把队列砍到只剩让位板仍然全过 —— 分区条件在那种队列上退化成
    恒真。判据改成**集合相等**: 少一块（让位判定对它空转）、多一块（混进不该在的
    板）两侧都要说话。
    """
    with pytest.raises(contract.ContractError, match="ranked 为空"):
        contract.check_ranked_yield_partition([], {"A"})
    # 少一块
    with pytest.raises(contract.ContractError, match="板集合与期望不符"):
        contract.check_ranked_yield_partition([{"board": "A"}], {"B"}, require_exact_boards={"A", "B"})
    # 多一块
    with pytest.raises(contract.ContractError, match="板集合与期望不符"):
        contract.check_ranked_yield_partition([{"board": "A"}, {"board": "X"}], {"A"}, require_exact_boards={"A"})
    # 恰好相等时不抛（且让位板在后）
    contract.check_ranked_yield_partition([{"board": "A"}, {"board": "B"}], {"B"}, require_exact_boards={"A", "B"})


def test_inbox_date_divergence_is_really_detected(tmp_path):
    """非 +08:00 时区下, inbox 的「今天」确实与其余面分叉, 且被契约**看见**。

    这条同时是 `DECLARED_DIVERGENCES` 的验伪锚: 如果 inbox 这一面根本没进矩阵,
    白名单就是在给一件不存在的事发豁免。
    """
    rc, report, _, _ = _run(tmp_path, tz=TZ_LA, name="la")
    board = report["boards"][0]
    inbox_day = report["matrix"][board]["display_day"]["skill_inbox"]
    picker_day = report["matrix"][board]["display_day"]["picker"]
    assert inbox_day != contract.NOT_PRODUCED, "inbox 这一面没有产出日期结论"
    assert inbox_day != picker_day, (
        f"在 {TZ_LA} 下 inbox（固定 +08:00）与 picker 的日期竟然相同 —— "
        "要么 --now 恰好落在两者同日的窗口, 要么 inbox 不再用固定偏移"
    )
    assert any(r["face"] == "skill_inbox" and r["field"] == "display_day" for r in report["declared_divergences"]), (
        "分叉存在却没进已登记清单 —— 它会被当成未登记分歧或被静默吞掉"
    )
    assert report["undeclared_divergences"] == []
    assert rc == 0


# ──────────────────── (d)③ review_app 无独立 due 算法 ────────────────────


def test_review_app_has_no_independent_due_algorithm():
    """review_app 只 import 共享桶序常量, 不自造 due 算法。"""
    result = contract.assert_review_app_has_no_due_algorithm(
        WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_app.py"
    )
    assert set(result["imported_shared"]) == set(contract._APP_SHARED_IMPORTS)


def test_review_app_static_gate_catches_a_bare_due_calculation(tmp_path):
    """验伪锚: 往 review_app 里塞一处裸 due 计算, 上面那条断言必须抓到。

    ⛔ 改的是 tmp 里的**副本**, 不动生产文件。
    """
    src = (WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_app.py").read_text(encoding="utf-8")
    tainted = tmp_path / "review_app_tainted.py"
    tainted.write_text(
        src + "\n\ndef _bare_due(node):\n    fsrs_due = node.get('fsrs_due')\n    return bool(fsrs_due)\n",
        encoding="utf-8",
    )
    with pytest.raises(contract.ContractError, match="独立 due 算法"):
        contract.assert_review_app_has_no_due_algorithm(tainted)


@pytest.mark.parametrize(
    "injected",
    [
        pytest.param('def _d(n, t):\n    return n["fsrs_due"] <= t\n', id="下标"),
        pytest.param('def _d(n):\n    return n.get("due_reason") == "scheduled"\n', id="get"),
        pytest.param('def _d(n):\n    return n.pop("fsrs_state", None)\n', id="pop"),
        # ── Codex r3 HIGH-1: 字段名只是**子串** / 藏在默认参数 / getattr 实参 ──
        pytest.param(
            'import re as _r\n\ndef _d(t):\n    return _r.search(r"^fsrs_due: *(.*)$", t, _r.M)\n',
            id="正则子串",
        ),
        pytest.param('def _d(n, key="fsrs_due"):\n    return n.get(key)\n', id="默认参数"),
        pytest.param('def _d(n):\n    return getattr(n, "fsrs_state", None)\n', id="getattr"),
        # ── Codex r4: 边界规则失效的正则 / 形参遮蔽 / bytes 字面量 ──
        pytest.param(
            'import re as _r\n\ndef _d(raw):\n    return _r.search(r"\\bfsrs_due\\b: *(.*)$", raw, _r.M)\n',
            id="边界正则",
        ),
        pytest.param('def _d(_BUCKET_ORDER=("future", "new")):\n    return list(_BUCKET_ORDER)\n', id="形参遮蔽"),
        pytest.param('def _d(raw):\n    return raw.split(b"fsrs_due")\n', id="bytes字面量"),
    ],
)
def test_review_app_gate_catches_dict_key_due_reads(tmp_path, injected):
    """字段名写成**字符串常量**的读法同样算自造算法。

    ⛔ Codex r1 HIGH-3: `node["fsrs_due"]` / `node.get("fsrs_due")` 里字段名既不是
    `ast.Name` 也不是 `ast.Attribute`, 原先的 AST 门整条走过去; 当轮的负控之所以
    能红, 只是因为它恰好把局部变量也命名成了 `fsrs_due`。
    """
    src = (WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_app.py").read_text(encoding="utf-8")
    tainted = tmp_path / "review_app_dictread.py"
    tainted.write_text(src + "\n\n" + injected, encoding="utf-8")
    with pytest.raises(contract.ContractError, match="独立 due 算法"):
        contract.assert_review_app_has_no_due_algorithm(tainted)


def test_template_due_callsites_are_frozen_by_identity(tmp_path):
    """页面模板里碰 due 字段的调用点按**身份冻结**；多一处必须红。

    ⛔ Codex r4 HIGH-2 的处置, 连同它的**覆盖面上限**一并钉住: 这道检查
    **不声称**模板里的 JS 是纯消费方 —— 同一个标识符既能用于把到期时刻渲染成人话,
    也能用于自造到期判定, 区分靠语义, 而 JS 的语义在 Python AST 门的射程之外。
    它声称的是「这些调用点没有变过」。
    """
    app = WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_app.py"
    result = contract.assert_review_app_has_no_due_algorithm(app)
    assert set(result["template_due_callsites"]) == set(contract._TEMPLATE_DUE_CALLSITES)
    # 现状就是两处「渲染成人话」的调用, 写死在这里让它可见
    assert result["template_due_callsites"] == [
        "const due = humanizeDue(n.fsrs_due, nowMs);",
        "const due = humanizeDue(r.fsrs_due, nowMs);",
    ]

    tainted = tmp_path / "review_app_js_due.py"
    tainted.write_text(
        app.read_text(encoding="utf-8").replace(
            "const due = humanizeDue(n.fsrs_due, nowMs);",
            "const due = humanizeDue(n.fsrs_due, nowMs);\n"
            "const negctlDue = rows.filter(r => Date.parse(r.fsrs_due) <= nowMs);",
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(contract.ContractError, match="碰 due 字段的调用点变了"):
        contract.assert_review_app_has_no_due_algorithm(tainted)


def test_function_docstring_mentioning_due_is_not_an_offender(tmp_path):
    """普通函数的**说明文字**里提到 due 字段不算违约（它在描述不做什么）。

    ⛔ Codex r4 LOW-9: 原先只豁免模块 docstring, 于是一个诚实的函数注释会被误红。
    """
    app = WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_app.py"
    ok = tmp_path / "review_app_doc.py"
    ok.write_text(
        app.read_text(encoding="utf-8")
        + '\n\ndef _negctl_doc():\n    """显示投影里的 fsrs_due 字段, 不计算到期。"""\n    return None\n',
        encoding="utf-8",
    )
    contract.assert_review_app_has_no_due_algorithm(ok)  # 不抛


def test_shared_order_placeholder_is_not_an_offender():
    """`__BUCKET_ORDER_JSON__` 这个注入占位符**不算**违约。

    ⛔ 它恰恰是「共享不复制」的体现（review_app 把 import 来的桶序注进页面模板）。
    判据用**词边界**而不是裸包含, 就是为了放过它 —— 这条是词边界那一改的验伪锚:
    改回裸包含, 生产文件当场误报。
    """
    result = contract.assert_review_app_has_no_due_algorithm(
        WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_app.py"
    )
    assert result["offenders"] == []
    # 豁免面摊开可见（按身份, 不按长度）
    assert [n for n, _ in result["exempted_strings"]] == ["_PAGE_TEMPLATE"]
    assert result["docstring_len"] > 0


def test_review_app_static_gate_catches_losing_the_shared_import(tmp_path):
    """验伪锚之二: 断掉「共享不复制」的 import, 静态断言必须说话。"""
    src = (WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_app.py").read_text(encoding="utf-8")
    tainted = tmp_path / "review_app_noimport.py"
    tainted.write_text(src.replace("    _BUCKET_ORDER,\n", "", 1), encoding="utf-8")
    with pytest.raises(contract.ContractError, match="共享桶序常量"):
        contract.assert_review_app_has_no_due_algorithm(tainted)


# ──────────── (f) snooze / done / tonight_available 五面一致 ────────────


def test_snoozed_and_done_agree_across_faces(tmp_path):
    """推迟 / 完成两列在产出它们的面之间逐板相等。"""
    _, report, _, _ = _run(tmp_path)
    for board in report["boards"]:
        for field in ("snoozed", "done"):
            cells = report["matrix"][board][field]
            values = {
                json.dumps(v, ensure_ascii=False, sort_keys=True) for v in cells.values() if v != contract.NOT_PRODUCED
            }
            assert len(values) <= 1, f"板 {board} 的 {field} 跨面不一致: {cells}"
    # 验伪: fixture 必须真的造出「一块板被推迟」「一块板今天完成」两态,
    # 否则上面的循环比的全是 False == False。
    snoozed_boards = [b for b in report["boards"] if report["matrix"][b]["snoozed"].get("picker") is True]
    done_boards = [b for b in report["boards"] if report["matrix"][b]["done"].get("picker") is True]
    assert snoozed_boards, "fixture 没有造出任何被推迟的板 —— snoozed 这一列是恒 False 的假绿"
    assert done_boards, "fixture 没有造出任何今天完成的板 —— done 这一列是恒 False 的假绿"


def test_ranked_yield_partition_is_observed_not_recomputed():
    """snooze/done 的**消费后果**（让位分区）被观察到, 而不是只从输入重算一遍。

    ⛔ Codex r1 MEDIUM-6: 契约原先丢弃 `ranked`, 于是「让已完成板排回榜首」这种
    消费失效完全看不见。
    ⚠ 覆盖面如实声明: 本条只证「让位板整体靠后」, **不证**已完成与已推迟两者之间
    的先后（U6-C 登记、D-37 按现状不改的那条顺序）。
    """
    good = [{"board": "A"}, {"board": "B"}, {"board": "让位1"}, {"board": "让位2"}]
    contract.check_ranked_yield_partition(good, {"让位1", "让位2"})  # 不抛

    broken = [{"board": "让位1"}, {"board": "A"}, {"board": "B"}]
    with pytest.raises(contract.ContractError, match="让位分区被破坏"):
        contract.check_ranked_yield_partition(broken, {"让位1"})

    # 退化情形如实声明: 全部让位 / 无让位 时分区恒等, 本条不构成判据
    contract.check_ranked_yield_partition([{"board": "x"}], set())
    contract.check_ranked_yield_partition([{"board": "x"}], {"x"})


@pytest.mark.parametrize(
    ("now", "expect_tonight"),
    [(NOW_EARLY, True), (NOW_LATE, False)],
)
def test_tonight_available_tracks_now_hour_lt_20(tmp_path, now, expect_tonight):
    """`tonight_available` 恒等于「显示时区本地时 now.hour < 20」。

    两档都跑: 只测一档的话, 把判定写成恒 True / 恒 False 都能过。
    """
    _, report, _, _ = _run(tmp_path, now=now, name=f"t{expect_tonight}")
    t = report["tonight_available"]
    assert t["expected_now_hour_lt_20"] is expect_tonight, f"fixture 没落在预期档: 当地 hour={t['now_local_hour']}"
    assert t["from_overview"] is expect_tonight
    assert t["ok"] is True


# ─────────────────── 分歧归属：平局时不得任意指认 ───────────────────


def _blank(except_field: str, cells: dict) -> dict:
    """造一块板的四字段格子: 只有 `except_field` 有值, 其余结构性缺席。"""
    out = {f: {face: contract.NOT_PRODUCED for face in contract.FACES} for f in contract.FIELDS}
    out[except_field] = cells
    return out


def test_tie_reports_every_producer_not_an_arbitrary_one():
    """两个面各执一词（1:1 平局）时, **两个都**要报, 不许挑一个当「多数派」。

    ⛔ 这条是负控 `RO_BUCKET_SWAP` 逼出来的: `bucket` 只有 review_overview 与
    picker 两个面产出, 早期版本用 `max(分组, key=len)` 取「第一个最大组」, 于是
    归属完全由 `FACES` 的书写顺序决定 —— 改的是 review_overview, 报出来的却是
    picker。只看「红没红」的判据会放过这种错误归属。
    """
    matrix = {
        "板X": _blank(
            "bucket",
            {
                "review_overview": (("n", "new"),),
                "picker": (("n", "due_now"),),
                "review_app": contract.NOT_PRODUCED,
                "skill_recap": contract.NOT_PRODUCED,
                "skill_inbox": contract.NOT_PRODUCED,
                "notification": contract.NOT_PRODUCED,
            },
        )
    }
    undeclared, declared = contract.diff_matrix(matrix)
    assert declared == []
    assert {r["face"] for r in undeclared} == {"review_overview", "picker"}, (
        "平局下只报了一个面 —— 归属是按书写顺序任意指认的"
    )
    assert all(r["majority_faces"] == [] for r in undeclared), "平局下不该宣称存在多数派"


def test_strict_majority_still_names_only_the_outlier():
    """三比一时仍然只报那个少数派（否则每条分歧都会变成四条噪音）。

    这里同时走通已登记分歧的**谓词**通道: `now` 在 +08:00 下是 09-12, 与 inbox 的
    取值一致 ⇒ 落进已登记; 换成别的日期就会落进未登记（上面那条测试证）。
    """
    now = datetime(2026, 9, 12, 3, 0, tzinfo=timezone.utc)  # LA 侧是 09-11, +08:00 侧是 09-12
    matrix = {
        "板Y": _blank(
            "display_day",
            {
                "review_overview": "2026-09-11",
                "picker": "2026-09-11",
                "notification": "2026-09-11",
                "skill_inbox": "2026-09-12",
                "review_app": contract.NOT_PRODUCED,
                "skill_recap": contract.NOT_PRODUCED,
            },
        )
    }
    undeclared, declared = contract.diff_matrix(matrix, ctx={"now": now})
    assert undeclared == []
    assert [r["face"] for r in declared] == ["skill_inbox"]
    assert sorted(declared[0]["majority_faces"]) == ["notification", "picker", "review_overview"]


# ───────────────────────────── 确定性 ─────────────────────────────


def test_two_runs_are_byte_identical(tmp_path):
    """同一输入二跑输出逐字节相等（禁止把时刻 / 临时路径 / 内存地址打进报告）。"""
    _, _, out1, _ = _run(tmp_path, name="d1")
    _, _, out2, _ = _run(tmp_path, name="d2")
    assert out1 == out2, "契约脚本输出不确定 —— 它不能当回归判据"


# ─────────────────── picker 只读面的分歧登记（如有）───────────────────
#
# 本卡对 picker 只读: 若矩阵暴露 picker 侧的桶位/日期/顺序分歧, 在此
# `xfail(strict=True)` 锁住并移交 T4, **不得**放宽上面的主断言。
# 2026-09-16 实测: 未出现 picker 侧分歧 ⇒ 本节暂无 xfail 条目。
# （U6-C 已登记的「done + snooze 并存顺序」按 D-37 现状不改, 它表达在
#  `ranked` 的分区次序上, 不落 payload 字段, 故不在本矩阵的四个字段内 ——
#  如实声明: 本门不覆盖那条顺序。）
