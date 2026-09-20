"""CARD-G8-4 — ``scripts/review_weekly_report.py`` 行为门.

[BATCH-2026-09-18-第十五批 / CARD-G8-4]

被测对象是**复习完成率周汇总**: 只读 per-vault state + frontmatter + 事件账,
机械算「当日到期 vs 实际复习」, 输出 md。

import 范式抄 ``backend/tests/unit/test_review_overview.py:1070``
(`sys.path.insert(0, str(WT / "scripts"))`)。

⚠️ **每个用例都不得触到主仓 ``backups/``**: ``daily_review_run`` 的 ``REPO`` /
``BACKUPS`` 是**模块 import 期**从 ``CANVAS_REPO`` 捕获的, 测试里再
``monkeypatch.setenv`` 已经晚了 (模块早在收集期就进了 ``sys.modules``)。
所以这里一律**显式传 ``--state``**; 默认派生那条路径由
:func:`test_default_state_path_is_derived_from_runner` 单独用
``monkeypatch.setattr(runner, "BACKUPS", …)`` 验证。

DD-03: 全部用真文件 + 真 ``tmp_path``, 不 mock 文件系统、不 mock 被测模块。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

_WT = Path(__file__).resolve().parents[3]
if str(_WT / "scripts") not in sys.path:
    sys.path.insert(0, str(_WT / "scripts"))

import daily_review_run as runner  # noqa: E402  # pyright: ignore[reportMissingImports]
import review_weekly_report as rwr  # noqa: E402  # pyright: ignore[reportMissingImports]

# ── fixture 工具 ────────────────────────────────────────────────────────────
_FUTURE_DUE = "2027-01-01T00:00:00Z"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(root: Path) -> dict:
    """{相对路径: sha256} —— 只读判据用 (比「文件还在」强: 等数量原地改写也看得出)。"""
    return {str(p.relative_to(root)): _sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


def _node(
    vault: Path,
    stem: str,
    *,
    fsrs_due: str | None = None,
    board: str | None = "[[原白板/CS 61B]]",
    last_examined: str | None = None,
    calibration_ts: list[str] | None = None,
) -> Path:
    """造一个节点 ``.md``（frontmatter 形态抄 live: UTC-Z 整秒 + wikilink 板名）。"""
    d = vault / "节点"
    d.mkdir(parents=True, exist_ok=True)
    lines = ["---", f"title: {stem}"]
    if board:
        lines.append(f"source_board: {board}")
    if fsrs_due:
        lines.append(f"fsrs_due: {fsrs_due}")
    if last_examined:
        lines.append(f"last_examined: {last_examined}")
    if calibration_ts:
        lines.append("calibration_log:")
        for i, ts in enumerate(calibration_ts, 1):
            lines += [f"  - event_id: CS61B-2026-09-18-1200#q{i}", f"    ts: {ts}", "    exam_board: 检验白板/CS61B.md"]
    lines += ["---", "", f"正文 {stem}", ""]
    p = d / f"{stem}.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _event(event_type: str, node_id: str, *, review_time: str | None, extra_text: str = "") -> str:
    payload: dict = {"concept_id": node_id, "rating": 3, "vault_id": "g84fix"}
    if review_time is not None:
        payload["schema_ext"] = "review/1"
        payload["review_time"] = review_time
    if extra_text:
        payload["note"] = extra_text
    return json.dumps(
        {"event_id": f"{event_type}-{node_id}", "event_type": event_type, "node_id": node_id, "payload": payload},
        ensure_ascii=False,
    )


def _write_events(path: Path, lines: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # 物理 LF 结尾, 与 learning_event_log._iter_lines 同语义
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _state(path: Path, *, board_done: dict | None = None, snoozed: dict | None = None, raw: str | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        path.write_text(raw, encoding="utf-8")
        return path
    path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "board_last_recommended": {},
                "board_done": board_done or {},
                "snoozed": snoozed or {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture(autouse=True)
def _pin_timezone(monkeypatch):
    """钉日界 —— 否则「今天」随跑测试的机器时区漂移 (D-18)。"""
    monkeypatch.setenv("CANVAS_TZ", "Asia/Shanghai")


def _argv(vault: Path, state: Path, **kw) -> list:
    argv = ["report", "--vault", str(vault), "--state", str(state)]
    for k, v in kw.items():
        if v is None:
            continue
        argv += [f"--{k.replace('_', '-')}", str(v)]
    return argv


def _run(capsys, argv: list) -> tuple[int, str]:
    rc = rwr.main(argv)
    return rc, capsys.readouterr().out


def _rows_by_date(report: dict) -> dict:
    return {r["date"]: r for r in report["days"]}


# ═══════════════════════════════════════════════════════════════════════════
# ① 日表逐格
# ═══════════════════════════════════════════════════════════════════════════
class TestDayTable:
    def test_day_table_cells_are_exact(self, tmp_path, capsys):
        """三来源 + 四条事件行 + state 的 board_done, 逐格断言**具体数字**。

        事件账四行里有两行必须被忽略 (``candidate_created`` 不在复习族;
        ``answer_scored`` 但 payload 没有 ``schema_ext`` 标记), 一行是含 U+2028
        的合法 ``review/1`` —— 若按 ``splitlines()`` 切行它会被切碎、两半都解析
        失败, 事件账列就会少 1。
        """
        vault = tmp_path / "vault"
        today = "2026-09-18"
        _node(vault, "n-new")  # 无 fsrs_due = New, 恒到期, 未复习
        _node(
            vault,
            "n-done",
            fsrs_due=_FUTURE_DUE,
            last_examined="2026-09-18T02:00:00Z",
            calibration_ts=["2026-09-18T02:00:00Z"],
        )
        _node(vault, "n-pending", fsrs_due=_FUTURE_DUE)
        _node(vault, "n-u2028", fsrs_due=_FUTURE_DUE)
        events = _write_events(
            vault / "learning_events.jsonl",
            [
                _event("candidate_created", "n-pending", review_time=None),
                json.dumps(
                    {
                        "event_id": "x",
                        "event_type": "answer_scored",
                        "node_id": "n-pending",
                        "payload": {"concept_id": "n-pending", "rating": 3},
                    },
                    ensure_ascii=False,
                ),
                _event("answer_scored", "n-done", review_time="2026-09-18T02:00:00Z"),
                _event("answer_abandoned", "n-u2028", review_time="2026-09-18T03:00:00Z", extra_text="含分隔符 的说明"),
            ],
        )
        state = _state(tmp_path / "st.json", board_done={"CS 61B": today})

        rc = rwr.main(
            _argv(
                vault,
                state,
                events=events,
                now=f"{today}T20:00:00",
                days=7,
                out=tmp_path / "r.md",
                **{"today_json": tmp_path / "缺.json"},
            )
        )
        assert rc == 0
        report = rwr.LAST_REPORT
        row = _rows_by_date(report)[today]
        assert row["reviewed"] == 2, "n-done 与 n-u2028 都复习了"
        assert row["due"] == 3, "reviewed ∪ {n-new(New 恒到期)}"
        assert row["from_events"] == 2
        assert row["from_calibration"] == 1
        assert row["from_last_examined"] == 1
        assert row["completion_rate"] == "66.7%"
        assert row["boards_done"] == ["CS 61B"]
        assert row["snoozed"] == []

    def test_u2028_event_line_is_not_split(self, tmp_path):
        """单独锁「按物理 LF 切行」——含 U+2028 的那条必须算作**一行一事件**。"""
        vault = tmp_path / "vault"
        _node(vault, "n-u2028", fsrs_due=_FUTURE_DUE)
        events = _write_events(
            vault / "learning_events.jsonl",
            [_event("answer_scored", "n-u2028", review_time="2026-09-18T03:00:00Z", extra_text="a b")],
        )
        parsed = rwr.read_review_events(events, rwr.report_timezone())
        assert parsed["total_lines"] == 1, "含 U+2028 的合法行被切碎了"
        assert parsed["bad_lines"] == 0
        assert len(parsed["rows"]) == 1
        assert parsed["rows"][0]["node_id"] == "n-u2028"


# ═══════════════════════════════════════════════════════════════════════════
# ② 三来源去重
# ═══════════════════════════════════════════════════════════════════════════
class TestSourceDedupe:
    def test_three_sources_same_node_same_day_dedupe_to_one(self, tmp_path):
        """同一节点同一天被三个来源各记一次 ⇒ `reviewed` 计 1, 分列各 1。"""
        vault = tmp_path / "vault"
        today = "2026-09-18"
        _node(
            vault,
            "solo",
            fsrs_due=_FUTURE_DUE,
            last_examined="2026-09-18T01:00:00Z",
            calibration_ts=["2026-09-18T02:00:00Z"],
        )
        events = _write_events(
            vault / "learning_events.jsonl",
            [_event("answer_scored", "solo", review_time="2026-09-18T03:00:00Z")],
        )
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    events=events,
                    now=f"{today}T20:00:00",
                    out=tmp_path / "r.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        row = _rows_by_date(rwr.LAST_REPORT)[today]
        assert row["reviewed"] == 1, "三来源同节点必须去重成 1"
        assert row["from_events"] == 1
        assert row["from_calibration"] == 1
        assert row["from_last_examined"] == 1
        assert row["due"] == 1
        assert row["completion_rate"] == "100.0%"


# ═══════════════════════════════════════════════════════════════════════════
# ③ 日界
# ═══════════════════════════════════════════════════════════════════════════
class TestDayBoundary:
    def test_same_review_time_lands_on_different_days_across_timezones(self, tmp_path, monkeypatch):
        """同一个 ``review_time`` 在上海与 UTC 下归**不同日** —— 日界真的在起作用。

        ``2026-09-18T20:00:00Z`` = 上海 2026-09-19 04:00 ⇒ 上海归 09-19, UTC 归 09-18。
        """
        vault = tmp_path / "vault"
        _node(vault, "n1", fsrs_due=_FUTURE_DUE)
        events = _write_events(
            vault / "learning_events.jsonl",
            [_event("answer_scored", "n1", review_time="2026-09-18T20:00:00Z")],
        )
        state = _state(tmp_path / "st.json")

        monkeypatch.setenv("CANVAS_TZ", "Asia/Shanghai")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    events=events,
                    now="2026-09-19T12:00:00",
                    out=tmp_path / "sh.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        sh = {d: r["from_events"] for d, r in _rows_by_date(rwr.LAST_REPORT).items()}

        monkeypatch.setenv("CANVAS_TZ", "UTC")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    events=events,
                    now="2026-09-19T12:00:00",
                    out=tmp_path / "utc.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        utc = {d: r["from_events"] for d, r in _rows_by_date(rwr.LAST_REPORT).items()}

        assert sh["2026-09-19"] == 1 and sh["2026-09-18"] == 0, f"上海归日不对: {sh}"
        assert utc["2026-09-18"] == 1 and utc["2026-09-19"] == 0, f"UTC 归日不对: {utc}"
        assert sh != utc, "两种时区给出了相同的日表 —— 日界判据是空的"


# ═══════════════════════════════════════════════════════════════════════════
# ④ 今日对账
# ═══════════════════════════════════════════════════════════════════════════
def _today_json(path: Path, date: str, due_nodes: list[str], *, buckets: dict | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    stats = {"due_nodes": len(due_nodes)}
    stats.update(buckets or {})
    path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "vault_id": "g84fix",
                "date": date,
                "due_nodes": [{"node_id": n} for n in due_nodes],
                "stats": stats,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


class TestTodayReconcile:
    def _scene(self, tmp_path):
        vault = tmp_path / "vault"
        _node(vault, "a")  # New ⇒ 到期
        _node(vault, "b")  # New ⇒ 到期
        _node(vault, "c", fsrs_due=_FUTURE_DUE)  # 未到期
        return vault, _state(tmp_path / "st.json")

    def test_consistent(self, tmp_path):
        vault, state = self._scene(tmp_path)
        tj = _today_json(tmp_path / "今日.json", "2026-09-18", ["a", "b"])
        assert (
            rwr.main(_argv(vault, state, now="2026-09-18T20:00:00", out=tmp_path / "r.md", **{"today_json": tj})) == 0
        )
        rec = rwr.LAST_REPORT["today_reconcile"]
        assert rec["status"] == "一致", rec
        assert rec["script"] == 2 and rec["snapshot"] == 2

    def test_inconsistent_reports_both_numbers_and_rc_is_still_zero(self, tmp_path):
        """不一致**只报不改**, rc 仍 0 —— 对账工具不该因为发现分歧就失败。"""
        vault, state = self._scene(tmp_path)
        tj = _today_json(tmp_path / "今日.json", "2026-09-18", ["a"])
        rc = rwr.main(_argv(vault, state, now="2026-09-18T20:00:00", out=tmp_path / "r.md", **{"today_json": tj}))
        assert rc == 0, "发现不一致不应改变 rc"
        rec = rwr.LAST_REPORT["today_reconcile"]
        assert rec["status"] == "不一致"
        assert rec["script"] == 2 and rec["snapshot"] == 1
        assert "2 vs 1" in (tmp_path / "r.md").read_text(encoding="utf-8")

    def test_snapshot_from_another_day_is_not_reconciled(self, tmp_path):
        vault, state = self._scene(tmp_path)
        tj = _today_json(tmp_path / "今日.json", "2026-09-01", ["a", "b"])
        assert (
            rwr.main(_argv(vault, state, now="2026-09-18T20:00:00", out=tmp_path / "r.md", **{"today_json": tj})) == 0
        )
        rec = rwr.LAST_REPORT["today_reconcile"]
        assert rec["status"] == "快照非当日"
        assert rec["snapshot_date"] == "2026-09-01"


# ═══════════════════════════════════════════════════════════════════════════
# ⑤⑥ 只读
# ═══════════════════════════════════════════════════════════════════════════
class TestReportSelfEvidence:
    """报告 ① 段是「我读了这些」的自证 —— 写错「存在」比不写更坏。"""

    def test_nodes_dir_source_is_reported_as_existing(self, tmp_path):
        """``节点/`` 是**目录**：只判 ``is_file()`` 会把它显示成「不存在」。"""
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    out=tmp_path / "r.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        src = {s["role"]: s for s in rwr.LAST_REPORT["sources"]}
        assert src["nodes_dir"]["exists"] is True, "目录型数据源被报成不存在"
        assert src["nodes_dir"]["lines"] == 1, "节点数没报出来"
        assert src["nodes_dir"]["sha256"] is None, "目录不该有单一 sha256"
        md = (tmp_path / "r.md").read_text(encoding="utf-8")
        assert "| nodes_dir |" in md

    def test_inconsistent_reconcile_shows_where_the_gap_went(self, tmp_path):
        """「不一致」必须能追下去 —— 把快照自己的分桶原样带出来，不重算。

        live 首份周报实测: 本脚本 14、快照 6, 差额 8 恰是快照自报的
        ``ineligible``(占位符)。只给两个对不上的数字, 读的人无从判断该追谁。
        """
        vault = tmp_path / "vault"
        _node(vault, "a")
        _node(vault, "b")
        _node(vault, "c")
        state = _state(tmp_path / "st.json")
        tj = _today_json(tmp_path / "今日.json", "2026-09-18", ["a"], buckets={"ineligible": 2, "corrupt": 0})
        assert (
            rwr.main(_argv(vault, state, now="2026-09-18T20:00:00", out=tmp_path / "r.md", **{"today_json": tj})) == 0
        )
        rec = rwr.LAST_REPORT["today_reconcile"]
        assert rec["status"] == "不一致"
        assert rec["script"] == 3 and rec["snapshot"] == 1
        assert rec["buckets"]["ineligible"] == 2
        md = (tmp_path / "r.md").read_text(encoding="utf-8")
        assert "`ineligible`=2" in md, "差额去向没显形"
        assert "corrupt" not in md.split("差额的去向")[1].split("\n")[0], "值为 0 的桶不该占版面"
        assert "口径差说明" in md


class TestReadOnly:
    def test_report_writes_nothing_beyond_out(self, tmp_path):
        """跑前 / 跑后 vault 与 state 目录的 **sha256 映射**逐键同 (不用「文件还在」)。"""
        vault = tmp_path / "vault"
        _node(vault, "a")
        _write_events(
            vault / "learning_events.jsonl", [_event("answer_scored", "a", review_time="2026-09-18T02:00:00Z")]
        )
        statedir = tmp_path / "backups"
        state = _state(statedir / "daily-review.vault.state.json", board_done={"B": "2026-09-18"})
        _today_json(vault / "outputs" / "今日复习.json", "2026-09-18", ["a"])
        outdir = tmp_path / "out"
        outdir.mkdir()

        before_vault, before_state = _tree(vault), _tree(statedir)
        before_names = sorted(os.listdir(statedir))
        assert rwr.main(_argv(vault, state, now="2026-09-18T20:00:00", out=outdir / "r.md")) == 0
        assert _tree(vault) == before_vault, "vault 被写了"
        assert _tree(statedir) == before_state, "state 目录被写了"
        assert sorted(os.listdir(statedir)) == before_names, "state 目录多了文件 (.lock / .corrupt-*)"

    def test_broken_state_is_marked_unreadable_and_left_untouched(self, tmp_path):
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(tmp_path / "st.json", raw="{ 这不是合法 JSON")
        before = state.read_bytes()
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    out=tmp_path / "r.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        assert rwr.LAST_REPORT["state"]["readable"] is False
        assert "state: 不可读" in (tmp_path / "r.md").read_text(encoding="utf-8")
        assert state.read_bytes() == before, "坏 state 被隔离/重建了 —— 破坏只读契约"

    def test_board_done_as_list_is_treated_as_no_completion_record(self, tmp_path):
        """形状错 (``board_done`` 是 list) 也走「不可读」, 不是崩溃也不是当空字典。"""
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(
            tmp_path / "st.json", raw=json.dumps({"schema_version": 3, "board_done": ["CS 61B"], "snoozed": {}})
        )
        before = state.read_bytes()
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    out=tmp_path / "r.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        assert rwr.LAST_REPORT["state"]["readable"] is False
        assert state.read_bytes() == before

    def test_default_state_path_is_derived_from_runner(self, tmp_path, monkeypatch):
        """不传 ``--state`` 时走 ``runner.state_path``。

        ⚠️ 这里 monkeypatch 的是 **runner 模块的 ``BACKUPS`` 属性**, 不是
        ``CANVAS_REPO`` 环境变量 —— 后者是 runner **import 期**读的, 用例里再设
        已经晚了, 那样写会让判据落到主仓 ``backups/`` 上 (碰 live)。
        """
        fake_backups = tmp_path / "fake-backups"
        fake_backups.mkdir()
        monkeypatch.setattr(runner, "BACKUPS", fake_backups)
        vault = tmp_path / "vault"
        _node(vault, "a")
        derived = runner.state_path(vault)
        assert derived.parent == fake_backups, "派生路径没落在替身目录上 —— 判据会碰 live"
        _state(derived, board_done={"B": "2026-09-18"})

        rc = rwr.main(
            [
                "report",
                "--vault",
                str(vault),
                "--now",
                "2026-09-18T20:00:00",
                "--out",
                str(tmp_path / "r.md"),
                "--today-json",
                str(tmp_path / "缺.json"),
            ]
        )
        assert rc == 0
        assert rwr.LAST_REPORT["state"]["readable"] is True
        assert rwr.LAST_REPORT["state"]["board_done"] == {"B": "2026-09-18"}


# ═══════════════════════════════════════════════════════════════════════════
# ⑦⑧ 人工修复登记 / 找材料时间自报
# ═══════════════════════════════════════════════════════════════════════════
class TestLedger:
    def test_log_fix_and_log_material_round_trip(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(
                [
                    "log-fix",
                    "--ledger",
                    str(ledger),
                    "--what",
                    "手动修了一次推送",
                    "--who",
                    "me",
                    "--now",
                    "2026-09-18T20:00:00",
                ]
            )
            == 0
        )
        assert (
            rwr.main(
                [
                    "log-fix",
                    "--ledger",
                    str(ledger),
                    "--what",
                    "又修了一次",
                    "--cmd",
                    "make fix",
                    "--now",
                    "2026-09-18T20:00:00",
                ]
            )
            == 0
        )
        assert (
            rwr.main(["log-material", "--ledger", str(ledger), "--minutes", "25", "--now", "2026-09-18T20:00:00"]) == 0
        )

        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    out=tmp_path / "r.md",
                    manual_ledger=ledger,
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        rep = rwr.LAST_REPORT
        assert rep["manual_fixes"]["count"] == 2
        assert rep["manual_fixes"]["bad_lines"] == 0
        assert [i["what"] for i in rep["manual_fixes"]["items"]] == ["手动修了一次推送", "又修了一次"]
        assert rep["material_minutes"]["value"] == 25

    def test_ledger_bad_line_is_counted_and_skipped(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        assert rwr.main(["log-fix", "--ledger", str(ledger), "--what", "好行", "--now", "2026-09-18T20:00:00"]) == 0
        with open(ledger, "a", encoding="utf-8") as fh:
            fh.write("{ 这行坏了\n")
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    out=tmp_path / "r.md",
                    manual_ledger=ledger,
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        assert rwr.LAST_REPORT["manual_fixes"]["count"] == 1
        assert rwr.LAST_REPORT["manual_fixes"]["bad_lines"] == 1

    def test_no_material_self_report_says_not_reported(self, tmp_path):
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    out=tmp_path / "r.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        assert rwr.LAST_REPORT["material_minutes"]["value"] is None
        assert "未自报" in (tmp_path / "r.md").read_text(encoding="utf-8")

    def test_log_fix_appends_exactly_one_physical_line(self, tmp_path):
        """append 必须是**单次写、一行**: 半行会被读侧算成一条坏行。"""
        ledger = tmp_path / "ledger.jsonl"
        assert (
            rwr.main(["log-fix", "--ledger", str(ledger), "--what", "含 分隔符的说明", "--now", "2026-09-18T20:00:00"])
            == 0
        )
        raw = ledger.read_bytes().decode("utf-8")
        assert raw.count("\n") == 1, "写出了不止一个物理换行"
        assert raw.endswith("\n")
        assert json.loads(raw.strip())["what"] == "含 分隔符的说明"

    def test_time_forward_week_rollover_stays_deterministic(self, tmp_path):
        """H-1 回归门（时间前进型）: 写入 W38、查询 W39 —— 结果只由**注入时钟**决定。

        旧实现登记侧用真实时钟落 ``week``: 2026-09-21（W39 周一）起, 写入是 W39
        而查询是注入的 W38, 账行被周过滤整行滤掉 —— 两个用例必红。本测试把两侧
        时钟都钉死, 并断言**写入行本身**（``week`` / ``ts``）吃到了注入值: 谁把
        注入改回真实时钟, ``ts`` 断言当天就红, 跨过周界后 ``week`` 断言红。
        """
        ledger = tmp_path / "ledger.jsonl"
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(["log-fix", "--ledger", str(ledger), "--what", "W38 的修复", "--now", "2026-09-18T20:00:00"]) == 0
        )
        assert (
            rwr.main(["log-fix", "--ledger", str(ledger), "--what", "W39 的修复", "--now", "2026-09-22T20:00:00"]) == 0
        )
        assert (
            rwr.main(["log-material", "--ledger", str(ledger), "--minutes", "25", "--now", "2026-09-22T20:00:00"]) == 0
        )

        lines = [json.loads(x) for x in ledger.read_text(encoding="utf-8").split("\n") if x.strip()]
        assert [rec["week"] for rec in lines] == ["2026-W38", "2026-W39", "2026-W39"], "写入侧没吃 --now（H-1 回归）"
        assert lines[0]["ts"] == "2026-09-18T12:00:00Z", "ts 不是注入时刻（20:00 上海 = 12:00Z）"

        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-22T21:00:00",
                    out=tmp_path / "r39.md",
                    manual_ledger=ledger,
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        rep39 = rwr.LAST_REPORT
        assert rep39["week"] == "2026-W39"
        assert [i["what"] for i in rep39["manual_fixes"]["items"]] == ["W39 的修复"], (
            "时间前进后 W38 的账行必须整行过滤"
        )
        assert rep39["manual_fixes"]["bad_lines"] == 0, "跨周过滤不是坏行"
        assert rep39["material_minutes"]["value"] == 25

        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T21:00:00",
                    out=tmp_path / "r38.md",
                    manual_ledger=ledger,
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        rep38 = rwr.LAST_REPORT
        assert rep38["week"] == "2026-W38"
        assert [i["what"] for i in rep38["manual_fixes"]["items"]] == ["W38 的修复"]
        assert rep38["material_minutes"]["value"] is None


# ═══════════════════════════════════════════════════════════════════════════
# ⑨⑩⑪ 边界
# ═══════════════════════════════════════════════════════════════════════════
class TestEdges:
    @pytest.mark.parametrize("bad_due", ["2026-13-01T00:00:00Z", "2026-09-18T00:00:00+08:00", "明天"])
    def test_malformed_fsrs_due_fails_open_as_due(self, tmp_path, bad_due):
        """非规范 ``fsrs_due`` 视同到期 —— 与 picker :547-555 同口径 (fail-open)。"""
        vault = tmp_path / "vault"
        _node(vault, "weird", fsrs_due=bad_due)
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    out=tmp_path / "r.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        assert _rows_by_date(rwr.LAST_REPORT)["2026-09-18"]["due"] == 1

    def test_default_out_prints_to_stdout_and_adds_no_file(self, tmp_path, capsys):
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(tmp_path / "st.json")
        before = sorted(os.listdir(vault))
        rc, out = _run(capsys, _argv(vault, state, now="2026-09-18T20:00:00", **{"today_json": tmp_path / "缺.json"}))
        assert rc == 0
        assert "2026-09-18" in out and "completion_rate" in out
        assert sorted(os.listdir(vault)) == before, "缺省 --out 也往 vault 里写了东西"

    def test_vault_not_a_directory_is_rc2(self, tmp_path):
        notdir = tmp_path / "not-a-dir"
        notdir.write_text("x", encoding="utf-8")
        state = _state(tmp_path / "st.json")
        assert rwr.main(["report", "--vault", str(notdir), "--state", str(state)]) == 2

    def test_missing_nodes_dir_is_rc2(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        state = _state(tmp_path / "st.json")
        assert rwr.main(["report", "--vault", str(vault), "--state", str(state)]) == 2

    def test_window_is_days_long_and_ends_today(self, tmp_path):
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    days=3,
                    out=tmp_path / "r.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        dates = [r["date"] for r in rwr.LAST_REPORT["days"]]
        assert dates == ["2026-09-16", "2026-09-17", "2026-09-18"]

    def test_report_declares_the_estimate_caveat(self, tmp_path):
        """回溯日的到期集是**估计**（M-1 整改）—— 必须双向声明, 不能只写方向性断言。"""
        vault = tmp_path / "vault"
        _node(vault, "a")
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    out=tmp_path / "r.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        md = (tmp_path / "r.md").read_text(encoding="utf-8")
        assert "回溯日的到期集是估计" in md
        assert "下界" not in md, "方向性表述（下界）必须已移除 —— M-1 整改"
        assert "低估" in md and "高估" in md, "双向偏差未如实声明"
        assert "只有" in md and "今日" in md, "未声明只有今日行可精确对账"

    def test_zero_due_day_shows_dash_not_zero_percent(self, tmp_path):
        """``due`` 为 0 记「—」不记 0% —— 0/0 不是 0。"""
        vault = tmp_path / "vault"
        _node(vault, "a", fsrs_due=_FUTURE_DUE)
        state = _state(tmp_path / "st.json")
        assert (
            rwr.main(
                _argv(
                    vault,
                    state,
                    now="2026-09-18T20:00:00",
                    days=2,
                    out=tmp_path / "r.md",
                    **{"today_json": tmp_path / "缺.json"},
                )
            )
            == 0
        )
        row = _rows_by_date(rwr.LAST_REPORT)["2026-09-17"]
        assert row["due"] == 0
        assert row["completion_rate"] == "—"
