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


def _run(tmp_path: Path, now: str = NOW_EARLY, tz: str = TZ_SH, name: str = "r") -> tuple[int, dict, str]:
    """跑一次契约脚本, 返回 (rc, 报告 JSON, stdout)。"""
    out = tmp_path / f"{name}.json"
    proc = subprocess.run(
        [PY, str(SCRIPT), "--now", now, "--tz", tz, "--json", str(out)],
        capture_output=True,
        text=True,
        cwd=str(WT / "backend"),
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert out.is_file(), f"契约脚本没有产出报告\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    return proc.returncode, json.loads(out.read_text(encoding="utf-8")), proc.stdout


# ───────────────────────────── (d)① 主断言 ─────────────────────────────


def test_five_view_matrix_is_field_wise_consistent(tmp_path):
    """五面矩阵逐板逐字段全等（已登记分歧除外）。"""
    rc, report, _ = _run(tmp_path)
    assert report["undeclared_divergences"] == [], "五面出现未登记的口径分歧:\n" + "\n".join(
        f"  板={r['board']} 字段={r['field']} 面={r['face']} "
        f"值={r['value']} ≠ 多数派{r['majority_faces']}={r['majority_value']}"
        for r in report["undeclared_divergences"]
    )
    assert report["verdict"] == "PASS"
    assert rc == 0


def test_matrix_actually_compares_something(tmp_path):
    """验伪锚: 矩阵不是恒绿 —— 至少两个面在至少一个字段上真的被比过。

    ⛔ 没有这条, 「零分歧」既可能是真一致, 也可能是「所有面都不产出任何字段」
    （矩阵全是 NOT_PRODUCED, 比对循环一次都没进去）。
    """
    _, report, _ = _run(tmp_path)
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
    assert {(face, field) for face, field, _ in contract.DECLARED_DIVERGENCES} == {
        ("skill_inbox", "display_day"),
    }, "已登记分歧集合变了 —— 新增/删除必须同时更新验收单台账与本断言"

    _, report, _ = _run(tmp_path)
    for row in report["declared_divergences"]:
        assert (row["face"], row["field"]) in {("skill_inbox", "display_day")}


def test_inbox_date_divergence_is_really_detected(tmp_path):
    """非 +08:00 时区下, inbox 的「今天」确实与其余面分叉, 且被契约**看见**。

    这条同时是 `DECLARED_DIVERGENCES` 的验伪锚: 如果 inbox 这一面根本没进矩阵,
    白名单就是在给一件不存在的事发豁免。
    """
    rc, report, _ = _run(tmp_path, tz=TZ_LA, name="la")
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
    _, report, _ = _run(tmp_path)
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


@pytest.mark.parametrize(
    ("now", "expect_tonight"),
    [(NOW_EARLY, True), (NOW_LATE, False)],
)
def test_tonight_available_tracks_now_hour_lt_20(tmp_path, now, expect_tonight):
    """`tonight_available` 恒等于「显示时区本地时 now.hour < 20」。

    两档都跑: 只测一档的话, 把判定写成恒 True / 恒 False 都能过。
    """
    _, report, _ = _run(tmp_path, now=now, name=f"t{expect_tonight}")
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
    """三比一时仍然只报那个少数派（否则每条分歧都会变成四条噪音）。"""
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
    undeclared, declared = contract.diff_matrix(matrix)
    assert undeclared == []
    assert [r["face"] for r in declared] == ["skill_inbox"]
    assert sorted(declared[0]["majority_faces"]) == ["notification", "picker", "review_overview"]


# ───────────────────────────── 确定性 ─────────────────────────────


def test_two_runs_are_byte_identical(tmp_path):
    """同一输入二跑输出逐字节相等（禁止把时刻 / 临时路径 / 内存地址打进报告）。"""
    _, _, out1 = _run(tmp_path, name="d1")
    _, _, out2 = _run(tmp_path, name="d2")
    assert out1 == out2, "契约脚本输出不确定 —— 它不能当回归判据"


# ─────────────────── picker 只读面的分歧登记（如有）───────────────────
#
# 本卡对 picker 只读: 若矩阵暴露 picker 侧的桶位/日期/顺序分歧, 在此
# `xfail(strict=True)` 锁住并移交 T4, **不得**放宽上面的主断言。
# 2026-09-16 实测: 未出现 picker 侧分歧 ⇒ 本节暂无 xfail 条目。
# （U6-C 已登记的「done + snooze 并存顺序」按 D-37 现状不改, 它表达在
#  `ranked` 的分区次序上, 不落 payload 字段, 故不在本矩阵的四个字段内 ——
#  如实声明: 本门不覆盖那条顺序。）
