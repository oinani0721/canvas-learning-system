"""daily_review_pick 选板逻辑锁定 (DAILY-REVIEW-PUSH-2026-07-29, Code-Review M6)。

12 场景运行时矩阵之外的纯逻辑层: 病理日期不崩全轮 / wikilink 归一 /
占位符跳过 / tie-break 三级 / 脏数值进 corrupt / BOM 容忍。
CARD-G3-6a (BATCH-2026-08-29-第六批) 追加: 五桶划分律 (互斥+完备) /
why_due 6 模板 / 加性纯度金样 (pop 新字段后与引入前字面量深度全等)。
"""

import json
import os
import re
import shutil
import subprocess
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WT / "scripts"))

import daily_review_pick as picker  # noqa: E402

NOW = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)


_seq = iter(range(1000))


def _build(tmp_path, nodes: dict, blr: dict | None = None, now: datetime = NOW):
    vault = tmp_path / f"vault{next(_seq)}"  # 同一测试可多次调用, 各建独立 vault
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    for name, content in nodes.items():
        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
    return picker.build_payload(vault, now, blr or {}, picker.load_decay(vault))


def _node(board="普通板", extra=""):
    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'


def test_pathological_last_examined_does_not_kill_run(tmp_path):
    """Code-Review M2: 年份手滑成 0001 的节点不得崩掉整轮生成。"""
    payload, ranked = _build(
        tmp_path,
        {
            "病理": _node(extra="mastery_a: 2.0\nmastery_b: 3.0\nlast_examined: 0001-01-01T00:00:00Z\n"),
            "正常": _node(),
        },
    )
    assert payload["stats"]["corrupt"] == 0 and len(ranked) == 1
    assert all(r["priority"] == r["priority"] for r in ranked)  # 无 NaN


def test_wikilink_board_normalization(tmp_path):
    payload, ranked = _build(tmp_path, {"甲": _node(board="我的板")})
    assert ranked[0]["board"] == "我的板"
    assert "node 甲" in picker.render_md(payload, ranked)


def test_placeholder_node_skipped_empty_notification(tmp_path):
    payload, ranked = _build(
        tmp_path,
        {
            "占位": _node(extra="").replace("真实内容。", "> 你的 1-2 句精准定义"),
        },
    )
    assert payload["stats"]["ineligible"] == 1
    assert ranked == [] and payload["notification"] is None


def test_tiebreak_prefers_least_recently_recommended(tmp_path):
    nodes = {"a节点": _node(board="A板"), "b节点": _node(board="B板")}
    _, ranked = _build(tmp_path, nodes, blr={"A板": "2026-07-29"})
    assert ranked[0]["board"] == "B板", "同分时从未被推荐的板优先"
    _, ranked2 = _build(tmp_path, nodes)
    assert ranked2[0]["board"] == "A板", "全无记录时按板名稳定排序"


def test_negative_mastery_counted_corrupt_not_silent(tmp_path):
    """Code-Review L5: mastery_a: -3 必须进 corrupt, 不得静默当无字段。"""
    payload, ranked = _build(
        tmp_path,
        {
            "脏": _node(extra="mastery_a: -3\nmastery_b: 2\n"),
        },
    )
    assert payload["stats"]["corrupt"] == 1 and ranked == []


def test_bom_frontmatter_tolerated(tmp_path):
    payload, _ = _build(
        tmp_path,
        {
            "带bom": "﻿" + _node(extra="mastery_a: 1.0\nmastery_b: 1.0\n"),
        },
    )
    assert payload["stats"]["new"] == 1


# ── FSRS WHEN 语义 ([Decision-FSRS-2], FSRS-V2-2026-07-30) ──


def test_future_due_board_gets_rest_notification(tmp_path):
    """F1: 唯一板全员未到期 → 不进推荐榜, 推送改为诚实的放假消息。"""
    payload, ranked = _build(
        tmp_path,
        {
            "已排期": _node(extra="mastery_a: 2.0\nmastery_b: 2.0\nfsrs_due: 2026-08-15T01:00:00Z\n"),
        },
    )
    assert ranked == [] and payload["stats"]["future_nodes"] == 1
    noti = payload["notification"]
    assert "无到期" in noti["title"] and "2026-08-15" in noti["body"]
    assert payload["upcoming"][0]["board"] == "普通板"


def test_due_filter_beats_pick_within_board(tmp_path):
    """WHEN 先于 WHAT: 板内未到期节点即使 pick 更低也不能当 top_node。"""
    payload, ranked = _build(
        tmp_path,
        {
            "低分未到期": _node(extra="mastery_a: 0.1\nmastery_b: 5.0\nfsrs_due: 2026-08-15T01:00:00Z\n"),
            "到期节点": _node(extra="mastery_a: 3.0\nmastery_b: 1.0\nfsrs_due: 2026-07-29T01:00:00Z\n"),
        },
    )
    assert ranked[0]["top_node"] == "到期节点" and ranked[0]["pending"] == 1
    assert ranked[0]["next_due"] == "2026-08-15T01:00:00Z"


def test_no_fsrs_field_means_new_card_due_now(tmp_path):
    """零迁移: 无 fsrs_due 字段的存量节点 = New 卡即刻到期, 行为与 MVP 一致。"""
    payload, ranked = _build(tmp_path, {"存量": _node()})
    assert ranked[0]["pending"] == 1 and payload["stats"]["due_nodes"] == 1


def test_unassigned_nodes_named_in_md(tmp_path):
    """Code-Review M3: 无 source_board 节点点名可见, 不再只是个数字。"""
    payload, ranked = _build(
        tmp_path,
        {
            "孤儿": "---\ntype: concept\n---\n真实内容。\n",
            "正常": _node(),
        },
    )
    assert payload["unassigned_nodes"] == ["孤儿"]
    assert "孤儿" in picker.render_md(payload, ranked)


# ── Review Projection v3 (CARD-A2, BATCH-2026-08-24-复习闭环) ──
# daily_review_pick 为到期口径唯一裁判: Dashboard 消费 due_nodes 明细与
# ineligible 分桶, 不再独立重算 (live 实测 13 vs 6 口径分裂的修复锁定)。


def test_projection_v3_due_nodes_and_ineligible_buckets(tmp_path):
    """5 类口径分歧节点全覆盖: 明细集合与 stats 数字必须同源自洽。

    ① 占位符未剖析 → ineligible.placeholder 单独成桶 (不静默吞掉)
    ② 无 type 字段 → picker 口径照收 (旧 Dashboard type==concept 反向漏掉的那类)
    ③ 无 source_board → 不计入 due_nodes, 点名在 unassigned_nodes
    ④ TEST_MARKERS 文件名 → ineligible.test_excluded 桶
    ⑤ 脏 fsrs_due (带时区偏移) → fail-open 视同到期, 进 due_nodes

    另锁 due 边界 (对抗性验证 M2): fsrs_due==now 判到期 (<= 语义),
    now+1h 判未到期 — 词法比较改 < 或引入时区漂移都会红。
    """
    payload, _ = _build(
        tmp_path,
        {
            "占位": _node().replace("真实内容。", "> 你的 1-2 句精准定义"),
            "无type": '---\nsource_board: "[[原白板/B板]]"\n---\n真实内容。\n',
            "孤儿": "---\ntype: concept\n---\n真实内容。\n",
            "TestConcept-伪节点": _node(),
            "脏due": _node(extra="fsrs_due: 2026-07-29T01:00:00+08:00\n"),
            "非法日期": _node(extra="fsrs_due: 2026-13-01T00:00:00Z\n"),
            "规范到期": _node(extra="fsrs_due: 2026-07-29T01:00:00Z\n"),
            "边界到期": _node(extra="fsrs_due: 2026-07-30T01:00:00Z\n"),
            "小时级未到期": _node(extra="fsrs_due: 2026-07-30T02:00:00Z\n"),
            "未到期": _node(extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
            "损坏": _node(extra="mastery_a: -3\nmastery_b: 2\n"),
        },
    )
    assert payload["schema_version"] == 3
    assert {d["node"] for d in payload["due_nodes"]} == {"无type", "脏due", "非法日期", "规范到期", "边界到期"}
    assert len(payload["due_nodes"]) == payload["stats"]["due_nodes"]
    for row in payload["due_nodes"]:
        assert set(row) >= {"node", "board", "state", "fsrs_due", "due_reason"}
    rows = {d["node"]: d for d in payload["due_nodes"]}
    assert rows["无type"]["board"] == "B板" and rows["规范到期"]["board"] == "普通板"
    # fail-open 清空语义锁定: Dashboard 的"新卡视同到期"计数依赖 fsrs_due==""
    assert rows["脏due"]["fsrs_due"] == ""
    # Codex-A2 M1/M2: 消费方可区分真新卡 / 已调度 / fail-open 脏日期
    # (含"形状对但月份 13"的日历非法值, 不得被词法比较误判成未来)
    assert rows["脏due"]["due_reason"] == "malformed"
    assert rows["非法日期"]["due_reason"] == "malformed"
    assert rows["无type"]["due_reason"] == "new"
    assert rows["规范到期"]["due_reason"] == "scheduled"

    ineligible = payload["ineligible"]
    assert set(ineligible) >= {"placeholder", "test_excluded", "corrupt"}
    assert ineligible["placeholder"] == ["占位"]
    assert ineligible["test_excluded"] == ["TestConcept-伪节点"]
    assert ineligible["corrupt"] == ["损坏"]
    assert len(ineligible["placeholder"]) == payload["stats"]["ineligible"]
    assert len(ineligible["test_excluded"]) == payload["stats"]["test_excluded"]
    assert len(ineligible["corrupt"]) == payload["stats"]["corrupt"]
    assert payload["unassigned_nodes"] == ["孤儿"]


def test_projection_v3_purely_additive_keeps_v2_contract(tmp_path):
    """推送链被动性守卫: v2 既有字段一个不少、语义不变 (daily_review_run /
    send_bark 只读 notification, 但全字段名保留是加性承诺的下界)。
    顶层键集合恒等锁定 (Codex-C1a M3): 再新增任何键必须显式改本断言 —
    「加性」的上界也是契约, 不许静默漂移。"""
    payload, ranked = _build(tmp_path, {"存量": _node()})
    assert set(payload) == {
        "unassigned_nodes",
        "schema_version",
        "vault_id",  # CARD-C1a 加性新增
        "date",
        "generated_at",
        "top_boards",
        "upcoming",
        "due_nodes",
        "boards",  # CARD-D1 P1 加性新增 (板级全量 rollup, 本断言显式扩)
        "buckets",  # CARD-G3-6a 加性新增 (五桶节点级分组, 本断言显式扩)
        "ineligible",
        "stats",
        "notification",
        "rank_manifest",  # CARD-G3-6b 加性新增 (S5 系数版本+指纹, 本断言显式扩)
        "truncated",  # CARD-G3-6b 加性新增 (S6 榜被截过的显式声明, 同上)
    }
    for key in (
        "new",
        "legacy",
        "none",
        "ineligible",
        "test_excluded",
        "corrupt",
        "unassigned",
        "due_nodes",
        "future_nodes",
    ):
        assert isinstance(payload["stats"][key], int)
    # CARD-C1a: 顶层 vault_id 加性新增 (send 侧组合有效通知 id 的数据源)
    assert isinstance(payload["vault_id"], str) and payload["vault_id"]
    # Bark 推送硬依赖 notification 四键 (send_bark.py 直接下标访问, 缺键即崩)
    # ⚠ 键集合与 id/group/title/body 落盘值全部精确锁定 (A2 冻结契约 +
    # Codex-C1a M3): 均不含 vault 维度, vault 维度只在 send 侧组合
    noti = payload["notification"]
    assert set(noti) == {"title", "body", "group", "id"}
    assert noti["id"] == f"canvas-review-{payload['date']}"
    assert noti["group"] == "canvas复习"
    assert noti["title"] == "📚 今日复习 · 普通板"
    assert noti["body"] == "存量 待巩固 · 从未考察"
    assert ranked[0]["board"] == "普通板"


def test_nonfinite_pick_goes_corrupt_not_nan_json(tmp_path):
    """Codex-A2 H1: 巨值 mastery 产出 NaN pick 不抛异常 — v3 起全部到期节点
    的 pick 进 JSON, 单个 NaN 会让整个投影文件非法。必须进 corrupt 桶。"""
    import json as _json

    payload, ranked = _build(
        tmp_path,
        {
            "溢出": _node(extra=f"mastery_a: {'9' * 400}\nmastery_b: 2\n"),
            "正常": _node(),
        },
    )
    assert payload["ineligible"]["corrupt"] == ["溢出"]
    assert payload["stats"]["corrupt"] == 1
    assert {d["node"] for d in payload["due_nodes"]} == {"正常"}
    # 全 payload 必须能严格 JSON 序列化 (裸 NaN = Dashboard JSON.parse 直接炸)
    _json.dumps(payload, ensure_ascii=False, allow_nan=False)


def test_due_boundary_survives_local_timezone_now(tmp_path):
    """Codex-A2 M3: now 为 +08:00 本地时区表示时, UTC 词法边界不得漂移
    (根因场景: 本地时区当前时间 vs UTC due 的比较)。"""
    now_local = NOW.astimezone(timezone(timedelta(hours=8)))  # 同一时刻, 非 UTC 表示
    payload, _ = _build(
        tmp_path,
        {
            "边界": _node(extra="fsrs_due: 2026-07-30T01:00:00Z\n"),
            "过一秒": _node(extra="fsrs_due: 2026-07-30T01:00:01Z\n"),
        },
        now=now_local,
    )
    assert {d["node"] for d in payload["due_nodes"]} == {"边界"}
    assert payload["stats"]["future_nodes"] == 1


def test_projection_v3_empty_vault_keeps_contract_keys(tmp_path):
    """空 vault 契约完整性: 分桶与明细键必须恒在 (Dashboard 不做存在性分支)。"""
    payload, ranked = _build(tmp_path, {})
    assert ranked == [] and payload["due_nodes"] == []
    assert set(payload["ineligible"]) == {"placeholder", "test_excluded", "corrupt"}
    assert all(v == [] for v in payload["ineligible"].values())
    assert payload["notification"] is None
    assert payload["boards"] == []  # CARD-D1 P1: rollup 键恒在, 空 vault 为空数组


# ── CARD-D1 P1: 顶层 boards 全量 rollup (BATCH-2026-08-27-Anki化与诚实收尾) ──
# 结构性缺口修复: top_boards/upcoming 各截 [:3]、placeholder 板级无归属 —
# rollup 提供全量板行。schema_version 保持 3, 既有字段零改动。


def test_boards_rollup_full_coverage(tmp_path):
    """boards rollup 全量语义: due 三分 (new/scheduled/malformed 隐含) /
    future / next_due / earliest_overdue / placeholder 归板; 计数与 stats
    合计自洽; 无 source_board 的占位符只留扁平列表, 不虚构归属。"""
    payload, _ = _build(
        tmp_path,
        {
            "新卡": _node(board="A板"),
            "逾期": _node(board="A板", extra="fsrs_due: 2026-07-28T01:00:00Z\n"),
            "更早逾期": _node(board="A板", extra="fsrs_due: 2026-07-20T01:00:00Z\n"),
            "未来": _node(board="A板", extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
            "全未来": _node(board="B板", extra="fsrs_due: 2026-09-01T01:00:00Z\n"),
            "脏日期": _node(board="C板", extra="fsrs_due: 2026-13-01T00:00:00Z\n"),
            "欠定义": _node(board="D板").replace("真实内容。", "> 你的 1-2 句精准定义"),
            "无主欠定义": "---\ntype: concept\n---\n> 你的 1-2 句精准定义\n",
        },
    )
    rollup = payload["boards"]
    assert [r["board"] for r in rollup] == ["A板", "B板", "C板", "D板"], "全量板行按板名稳定排序"
    for r in rollup:
        assert set(r) == {
            "board",
            "due",
            "due_new",
            "due_scheduled",
            "future",
            "next_due",
            "placeholder",
            "earliest_overdue",
        }
    by = {r["board"]: r for r in rollup}
    a = by["A板"]
    assert a["due"] == 3 and a["due_new"] == 1 and a["due_scheduled"] == 2
    assert a["future"] == 1 and a["next_due"] == "2026-08-15T01:00:00Z"
    assert a["earliest_overdue"] == "2026-07-20T01:00:00Z"
    assert a["placeholder"] == 0
    b = by["B板"]
    assert b["due"] == 0 and b["future"] == 1 and b["next_due"] == "2026-09-01T01:00:00Z"
    assert b["earliest_overdue"] == "" and b["next_due"][:4] == "2026"
    c = by["C板"]  # fail-open 脏日期: 到期但既非真新卡也非已排期 (malformed)
    assert c["due"] == 1 and c["due_new"] == 0 and c["due_scheduled"] == 0
    assert c["earliest_overdue"] == ""
    d = by["D板"]  # 占位符专属板: 无可复习成员, 仅欠定义归属
    assert d["due"] == 0 and d["future"] == 0 and d["placeholder"] == 1
    assert sum(r["due"] for r in rollup) == payload["stats"]["due_nodes"]
    assert sum(r["future"] for r in rollup) == payload["stats"]["future_nodes"]
    assert set(payload["ineligible"]["placeholder"]) == {"欠定义", "无主欠定义"}, "扁平列表零改动"
    assert sum(r["placeholder"] for r in rollup) == 1, "无主占位符不得虚构归属"


def test_boards_rollup_additive_old_fields_untouched(tmp_path):
    """加性纯度 (A2 冻结投影守卫): 旧字段逐一在位、值与 rollup 引入前
    逐字段等价 — ineligible.placeholder / notification / top_boards /
    upcoming / due_nodes / stats 零改动。"""
    payload, ranked = _build(
        tmp_path,
        {
            "存量": _node(),
            "已排期": _node(board="别板", extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
            "占位": _node().replace("真实内容。", "> 你的 1-2 句精准定义"),
        },
    )
    assert payload["schema_version"] == 3, "rollup 是加性字段, 不许抬版本"
    assert payload["ineligible"]["placeholder"] == ["占位"]
    assert payload["top_boards"] == ranked[:3]
    assert payload["upcoming"] == [{"board": "别板", "next_due": "2026-08-15T01:00:00Z", "node": "已排期"}]
    assert {d["node"] for d in payload["due_nodes"]} == {"存量"}
    noti = payload["notification"]
    assert set(noti) == {"title", "body", "group", "id"}
    assert noti["title"] == "📚 今日复习 · 普通板"
    assert payload["stats"]["due_nodes"] == 1 and payload["stats"]["future_nodes"] == 1
    assert payload["stats"]["ineligible"] == 1
    # rollup 自身: 占位归属到普通板, 别板纯未来
    by = {r["board"]: r for r in payload["boards"]}
    assert by["普通板"]["placeholder"] == 1 and by["普通板"]["due"] == 1
    assert by["别板"]["due"] == 0 and by["别板"]["next_due"] == "2026-08-15T01:00:00Z"


def test_boards_rollup_golden_old_fields_frozen(tmp_path):
    """P1 加性纯度金样 (Codex-D1 M2): 冻结 rollup 引入前的完整 payload
    字面量, 删掉新增 boards 键后深度全等 + 顶层键序恒等 — 旧字段任何
    值/键序/嵌套漂移都在此翻车 (逐字段断言无法发现的同步漂移)。
    generated_at/date 按 NOW.astimezone() 计算 (跟随机器时区, 非被测逻辑);
    vault 名固定 goldenvault 保 vault_id 确定性。"""
    vault = tmp_path / "goldenvault"
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    for name, content in {
        "存量": _node(),
        "已排期": _node(board="别板", extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
        "占位": _node().replace("真实内容。", "> 你的 1-2 句精准定义"),
    }.items():
        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
    payload, _ = picker.build_payload(vault, NOW, {}, picker.load_decay(vault))

    boards = payload.pop("boards")  # CARD-D1 P1 唯一新增 — 摘掉后与金样全等
    # CARD-G3-6a 后续加性: 顶层 buckets + due_nodes 行内 bucket/why_due。
    # 本测试守的是「rollup 引入前」那份金样, 故新一轮加性字段同样摘掉 —
    # 摘完仍须与 D1 之前的字面量深度全等 (累积冻结, 每轮加性都在此复核)。
    payload.pop("buckets")
    # CARD-G3-6b 再一轮加性: 顶层 rank_manifest/truncated + top_boards 行内
    # 三件套 + due_nodes 行内 idle_days (同一条累积冻结纪律)
    payload.pop("rank_manifest")
    payload.pop("truncated")
    for _tb in payload["top_boards"]:
        _tb.pop("why_this_board")
        _tb.pop("estimated_minutes")
        _tb.pop("factors")
    for _row in payload["due_nodes"]:
        _row.pop("bucket")
        _row.pop("why_due")
        _row.pop("idle_days")
    golden = {
        "unassigned_nodes": [],
        "schema_version": 3,
        "vault_id": "goldenvault",
        "date": NOW.astimezone().date().isoformat(),
        "generated_at": NOW.astimezone().isoformat(timespec="seconds"),
        "top_boards": [
            {
                "board": "普通板",
                "top_node": "存量",
                "priority": 0.0709,
                "pending": 1,
                "idle_days": None,
                "difficulty": "",
                "next_due": "",
            }
        ],
        "upcoming": [{"board": "别板", "next_due": "2026-08-15T01:00:00Z", "node": "已排期"}],
        "due_nodes": [
            {
                "node": "存量",
                "board": "普通板",
                "state": "none",
                "pick": 0.0709,
                "fsrs_due": "",
                "due_reason": "new",
                "last_examined": "",
                "difficulty": "",
            }
        ],
        "ineligible": {"placeholder": ["占位"], "test_excluded": [], "corrupt": []},
        "stats": {
            "new": 0,
            "legacy": 0,
            "none": 2,
            "ineligible": 1,
            "test_excluded": 0,
            "corrupt": 0,
            "unassigned": 0,
            "due_nodes": 1,
            "future_nodes": 1,
        },
        "notification": {
            "title": "📚 今日复习 · 普通板",
            "body": "存量 待巩固 · 从未考察",
            "group": "canvas复习",
            "id": "canvas-review-2026-07-30",
        },
    }
    assert payload == golden, "旧字段深度全等被打破 — P1 不再是纯加性"
    assert list(payload) == list(golden), "顶层键序漂移 (落盘 diff 稳定性)"
    assert [r["board"] for r in boards] == ["别板", "普通板"]


# ── CARD-G3-6a: 五桶位与 why_due (BATCH-2026-08-29-第六批) ──
# S1 划分律: 级联 new > learning_queue > due_now > due_today > future,
#    划分域 = 已归板且非 ineligible, 恰好一桶 (互斥+完备)。
# S2 加标签不搬移: 节点仍留在 due_nodes 内, stats 口径分毫不动 (R2 高风险面 —
#    搬移会同时改动 review_overview 权威计数与 Dashboard dv.io.load 数字)。
# S3 why_due: 6 个确定性模板, 恒非空, 槽位只填投影内已有的真实数据。


def _bucket_names(payload):
    """{桶名: [节点名]} — 桶内序 = 扫描序 (sorted stem)。"""
    return {b: [r["node"] for r in rows] for b, rows in payload["buckets"].items()}


def _why_map(payload):
    """{节点名: why_due} — 跨全部五桶展平 (S1 互斥保证键不冲突)。"""
    return {r["node"]: r["why_due"] for rows in payload["buckets"].values() for r in rows}


def test_buckets_five_way_partition_each_bucket_covered(tmp_path):
    """五桶各一 + S1 划分律: 键序恒定 / 两两不交 / 并集==已归板节点 /
    到期三桶合计==stats.due_nodes / 非到期两桶合计==stats.future_nodes。"""
    payload, _ = _build(
        tmp_path,
        {
            "真新卡": _node(board="A板"),
            "学习中": _node(board="A板", extra="fsrs_due: 2026-07-28T01:00:00Z\nfsrs_state: 1\n"),
            "普通到期": _node(board="A板", extra="fsrs_due: 2026-07-28T01:00:00Z\nfsrs_state: 2\n"),
            "今天晚些": _node(board="B板", extra="fsrs_due: 2026-07-30T13:00:00Z\n"),
            "远期": _node(board="B板", extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
        },
    )
    assert list(payload["buckets"]) == [
        "new",
        "learning_queue",
        "due_now",
        "due_today",
        "future",
    ], "落盘键序 = S1 级联优先级顺序"
    assert _bucket_names(payload) == {
        "new": ["真新卡"],
        "learning_queue": ["学习中"],
        "due_now": ["普通到期"],
        "due_today": ["今天晚些"],
        "future": ["远期"],
    }
    rows = [r for rs in payload["buckets"].values() for r in rs]
    names = [r["node"] for r in rows]
    assert len(names) == len(set(names)), "S1 互斥: 同一节点不得落两桶"
    assert set(names) == {"真新卡", "学习中", "普通到期", "今天晚些", "远期"}, "S1 完备: 已归板节点全覆盖"
    assert all(r["why_due"] for r in rows), "S3: why_due 恒非空"
    assert all(set(r) == {"node", "board", "why_due", "fsrs_due"} for r in rows)
    b, s = payload["buckets"], payload["stats"]
    assert len(b["new"]) + len(b["learning_queue"]) + len(b["due_now"]) == s["due_nodes"] == 3
    assert len(b["due_today"]) + len(b["future"]) == s["future_nodes"] == 2


def test_buckets_due_today_uses_shanghai_day_not_utc_day(tmp_path):
    """跨上海日边界 (S1 第 4 桶): NOW=2026-07-30T01:00Z = 上海 07-30 09:00。
    13:00Z / 15:59:59Z / 16:00Z 同属 UTC 07-30, 但上海侧前两个仍是 07-30、
    第三个已是 07-31 —— 用 UTC 日判会把 16:00Z 错判进 due_today。
    并锁 now 表示无关性: 同一时刻以 +08:00 表示时判桶结果逐字相同。"""
    nodes = {
        "上海今天": _node(extra="fsrs_due: 2026-07-30T13:00:00Z\n"),
        "上海日末": _node(extra="fsrs_due: 2026-07-30T15:59:59Z\n"),
        "上海跨日": _node(extra="fsrs_due: 2026-07-30T16:00:00Z\n"),
    }
    payload, _ = _build(tmp_path, nodes)
    b = _bucket_names(payload)
    assert set(b["due_today"]) == {"上海今天", "上海日末"}
    assert b["future"] == ["上海跨日"]
    why = _why_map(payload)
    assert why["上海今天"] == "今天 21:00 到期（尚未到点）"
    assert why["上海日末"] == "今天 23:59 到期（尚未到点）"
    assert why["上海跨日"] == "明天 7月31日 00:00 到期"
    local = _build(tmp_path, nodes, now=NOW.astimezone(timezone(timedelta(hours=8))))[0]
    assert _bucket_names(local) == b and _why_map(local) == why, "now 用本地时区表示不得改判"


def test_buckets_malformed_fail_open_and_new_card_edges(tmp_path):
    """边界: malformed fail-open 落 due_now 并在 why_due 里点名原值 (不装
    能解析); 无 fsrs_due 落 new; 闲置片段源自 last_examined。
    S2 同步锁定: 四个节点全部仍在 due_nodes 内, stats.due_nodes 不因分桶变化。"""
    payload, _ = _build(
        tmp_path,
        {
            "脏日期": _node(extra="fsrs_due: 2026-13-01T00:00:00Z\n"),
            "带偏移": _node(extra="fsrs_due: 2026-07-29T01:00:00+08:00\n"),
            "无字段": _node(),
            "考过的新卡": _node(extra="last_examined: 2026-07-20T01:00:00Z\n"),
        },
    )
    b = _bucket_names(payload)
    assert set(b["due_now"]) == {"脏日期", "带偏移"}
    assert set(b["new"]) == {"无字段", "考过的新卡"}
    why = _why_map(payload)
    assert why["脏日期"] == "到期待复习 · 到期时间无法解析(2026-13-01T00:00:00Z)，保守视同到期 · 从未考察"
    assert why["带偏移"] == "到期待复习 · 到期时间无法解析(2026-07-29T01:00:00+08:00)，保守视同到期 · 从未考察"
    assert why["无字段"] == "新卡未排期，视同即刻到期 · 从未考察"
    assert why["考过的新卡"] == "新卡未排期，视同即刻到期 · 已闲置 10 天"
    assert {d["node"] for d in payload["due_nodes"]} == {"脏日期", "带偏移", "无字段", "考过的新卡"}
    assert payload["stats"]["due_nodes"] == 4, "S2: 加标签不改到期口径"


def test_buckets_learning_states_and_unknown_state_fallback(tmp_path):
    """S1 fsrs_state 裁定: py-fsrs v6 Learning=1 / Relearning=3, 历史哨兵 0
    按 fsrs_bridge 读侧归一同口径并入 learning_queue; Review=2 / 非整数 /
    无法解析一律不享分层, 落 due_now (未知值不吞节点)。
    learning_queue 另要求「已到期」—— 学习态但未到期的仍按时间落 future。"""
    due = "fsrs_due: 2026-07-28T01:00:00Z\n"
    payload, _ = _build(
        tmp_path,
        {
            "学习1": _node(extra=due + "fsrs_state: 1\n"),
            "重学3": _node(extra=due + "fsrs_state: 3\n"),
            "哨兵0": _node(extra=due + "fsrs_state: 0\n"),
            "复习2": _node(extra=due + "fsrs_state: 2\n"),
            "垃圾值": _node(extra=due + "fsrs_state: abc\n"),
            "小数值": _node(extra=due + "fsrs_state: 1.5\n"),
            "学习态未到期": _node(extra="fsrs_due: 2026-08-15T01:00:00Z\nfsrs_state: 1\n"),
        },
    )
    b = _bucket_names(payload)
    assert set(b["learning_queue"]) == {"学习1", "重学3", "哨兵0"}
    assert set(b["due_now"]) == {"复习2", "垃圾值", "小数值"}
    assert b["future"] == ["学习态未到期"]
    why = _why_map(payload)
    assert why["学习1"] == "学习中 · 已逾期 2 天（7月28日到期） · 从未考察"
    assert why["哨兵0"] == "学习中 · 已逾期 2 天（7月28日到期） · 从未考察"
    assert why["重学3"] == "重学中 · 已逾期 2 天（7月28日到期） · 从未考察"
    assert why["复习2"] == "到期待复习 · 已逾期 2 天（7月28日到期） · 从未考察"
    assert why["学习态未到期"] == "16 天后 8月15日 09:00 到期"


def test_buckets_same_day_overdue_reads_as_clock_time(tmp_path):
    """S3 到期片段 delta==0 分支: 上海同日但已过点 → 说「今天 HH:MM 到期」
    而不是「已逾期 0 天」。"""
    payload, _ = _build(tmp_path, {"今早到期": _node(extra="fsrs_due: 2026-07-30T00:00:00Z\n")})
    assert _bucket_names(payload)["due_now"] == ["今早到期"]
    assert _why_map(payload)["今早到期"] == "到期待复习 · 今天 08:00 到期 · 从未考察"


def test_buckets_domain_excludes_unassigned_and_ineligible(tmp_path):
    """S1 划分域: 未归板 (unassigned_nodes 已点名) 与 ineligible 三类
    (placeholder/test_excluded/corrupt 已点名) 一律不进桶 —— 不重复点名,
    也不静默吞。"""
    payload, _ = _build(
        tmp_path,
        {
            "孤儿": "---\ntype: concept\n---\n真实内容。\n",
            "占位": _node().replace("真实内容。", "> 你的 1-2 句精准定义"),
            "TestConcept-伪": _node(),
            "损坏": _node(extra="mastery_a: -3\nmastery_b: 2\n"),
            "正常": _node(),
        },
    )
    assert [r["node"] for rs in payload["buckets"].values() for r in rs] == ["正常"]
    assert payload["unassigned_nodes"] == ["孤儿"]
    assert payload["ineligible"]["placeholder"] == ["占位"]
    assert payload["ineligible"]["test_excluded"] == ["TestConcept-伪"]
    assert payload["ineligible"]["corrupt"] == ["损坏"]


def test_buckets_empty_vault_keys_always_present(tmp_path):
    """空 vault 契约: 五键恒在 (与 ineligible 同风格, 消费方不做存在性分支)。"""
    payload, _ = _build(tmp_path, {})
    assert payload["buckets"] == {
        "new": [],
        "learning_queue": [],
        "due_now": [],
        "due_today": [],
        "future": [],
    }


def test_buckets_due_rows_mirror_bucket_grouping(tmp_path):
    """S2 加标签不搬移 (R2 硬判据): 到期三桶的成员集合必须逐个仍在
    due_nodes 内, 且行内 bucket/why_due 与 buckets 分组同源逐字相等 ——
    任何「把 new/learning_queue 搬出 due_nodes」的改法都在此翻车 (它会
    同时改动 review_overview 的 stats.due_nodes 权威计数与 Dashboard 的
    dv.io.load 明细)。"""
    payload, _ = _build(
        tmp_path,
        {
            "新": _node(),
            "学": _node(extra="fsrs_due: 2026-07-28T01:00:00Z\nfsrs_state: 3\n"),
            "到": _node(extra="fsrs_due: 2026-07-28T01:00:00Z\n"),
            "未": _node(extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
        },
    )
    b = payload["buckets"]
    due_bucket_rows = b["new"] + b["learning_queue"] + b["due_now"]
    assert {r["node"] for r in due_bucket_rows} == {d["node"] for d in payload["due_nodes"]}
    assert len(payload["due_nodes"]) == payload["stats"]["due_nodes"] == 3
    by_row = {d["node"]: (d["bucket"], d["why_due"], d["fsrs_due"]) for d in payload["due_nodes"]}
    for name, rows in (("new", b["new"]), ("learning_queue", b["learning_queue"]), ("due_now", b["due_now"])):
        for r in rows:
            assert by_row[r["node"]] == (name, r["why_due"], r["fsrs_due"]), "两处表示必须同源"
    assert by_row["新"][0] == "new" and by_row["学"][0] == "learning_queue"
    assert by_row["到"][0] == "due_now"
    # 未到期节点不得混进 due_nodes (划分只贴标签, 不搬人)
    assert "未" not in by_row and b["future"] == [
        {
            "node": "未",
            "board": "普通板",
            "why_due": "16 天后 8月15日 09:00 到期",
            "fsrs_due": "2026-08-15T01:00:00Z",
        }
    ]


def test_buckets_golden_pre_g36a_fields_frozen(tmp_path):
    """G3-6a 加性纯度金样 (仿 D1 test_boards_rollup_golden_old_fields_frozen):
    冻结 G3-6a 引入前的完整 payload 字面量 (含 D1 的 boards rollup), 摘掉本卡
    新增的顶层 buckets 与 due_nodes 行内 bucket/why_due 后深度全等 + 顶层键序
    恒等 —— 旧字段任何值/键序/嵌套漂移都在此翻车。
    generated_at/date 按 NOW.astimezone() 计算 (跟随机器时区, 非被测逻辑);
    vault 名固定 g36avault 保 vault_id 确定性。"""
    vault = tmp_path / "g36avault"
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    for name, content in {
        "存量": _node(),
        "已排期": _node(board="别板", extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
        "占位": _node().replace("真实内容。", "> 你的 1-2 句精准定义"),
    }.items():
        (vault / "节点" / f"{name}.md").write_text(content, encoding="utf-8")
    payload, _ = picker.build_payload(vault, NOW, {}, picker.load_decay(vault))

    buckets = payload.pop("buckets")  # G3-6a 唯一新增顶层键
    row_add = [(r.pop("bucket"), r.pop("why_due")) for r in payload["due_nodes"]]  # 行内两字段
    # CARD-G3-6b 加性字段同样摘掉 (累积冻结: 本测试守的是「G3-6a 引入前」那份
    # 金样, 每轮新加性都要在此证明自己没动旧字段/旧键序)
    payload.pop("rank_manifest")
    payload.pop("truncated")
    for _tb in payload["top_boards"]:
        _tb.pop("why_this_board")
        _tb.pop("estimated_minutes")
        _tb.pop("factors")
    for _row in payload["due_nodes"]:
        _row.pop("idle_days")
    golden = {
        "unassigned_nodes": [],
        "schema_version": 3,
        "vault_id": "g36avault",
        "date": NOW.astimezone().date().isoformat(),
        "generated_at": NOW.astimezone().isoformat(timespec="seconds"),
        "top_boards": [
            {
                "board": "普通板",
                "top_node": "存量",
                "priority": 0.0709,
                "pending": 1,
                "idle_days": None,
                "difficulty": "",
                "next_due": "",
            }
        ],
        "upcoming": [{"board": "别板", "next_due": "2026-08-15T01:00:00Z", "node": "已排期"}],
        "due_nodes": [
            {
                "node": "存量",
                "board": "普通板",
                "state": "none",
                "pick": 0.0709,
                "fsrs_due": "",
                "due_reason": "new",
                "last_examined": "",
                "difficulty": "",
            }
        ],
        "boards": [
            {
                "board": "别板",
                "due": 0,
                "due_new": 0,
                "due_scheduled": 0,
                "future": 1,
                "next_due": "2026-08-15T01:00:00Z",
                "placeholder": 0,
                "earliest_overdue": "",
            },
            {
                "board": "普通板",
                "due": 1,
                "due_new": 1,
                "due_scheduled": 0,
                "future": 0,
                "next_due": "",
                "placeholder": 1,
                "earliest_overdue": "",
            },
        ],
        "ineligible": {"placeholder": ["占位"], "test_excluded": [], "corrupt": []},
        "stats": {
            "new": 0,
            "legacy": 0,
            "none": 2,
            "ineligible": 1,
            "test_excluded": 0,
            "corrupt": 0,
            "unassigned": 0,
            "due_nodes": 1,
            "future_nodes": 1,
        },
        "notification": {
            "title": "📚 今日复习 · 普通板",
            "body": "存量 待巩固 · 从未考察",
            "group": "canvas复习",
            "id": "canvas-review-2026-07-30",
        },
    }
    assert payload == golden, "G3-6a 引入前的字段深度全等被打破 — 不再是纯加性"
    assert list(payload) == list(golden), "顶层键序漂移 (落盘 diff 稳定性)"
    # Codex round-1 LOW: dict 深度相等不查嵌套键序 — 嵌套对象逐个补键序断言,
    # 否则 due_nodes 行 / boards 行 / stats 的旧键重排不会翻车
    assert list(payload["due_nodes"][0]) == list(golden["due_nodes"][0]), "due_nodes 行键序漂移"
    assert [list(r) for r in payload["boards"]] == [list(r) for r in golden["boards"]], "boards 行键序漂移"
    assert list(payload["stats"]) == list(golden["stats"]), "stats 键序漂移"
    assert list(payload["ineligible"]) == list(golden["ineligible"]), "ineligible 键序漂移"
    assert list(payload["notification"]) == list(golden["notification"]), "notification 键序漂移"
    assert list(payload["top_boards"][0]) == list(golden["top_boards"][0]), "top_boards 行键序漂移"
    assert list(payload["upcoming"][0]) == list(golden["upcoming"][0]), "upcoming 行键序漂移"
    assert row_add == [("new", "新卡未排期，视同即刻到期 · 从未考察")]
    assert buckets["new"] == [
        {"node": "存量", "board": "普通板", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}
    ]
    assert buckets["future"] == [
        {
            "node": "已排期",
            "board": "别板",
            "why_due": "16 天后 8月15日 09:00 到期",
            "fsrs_due": "2026-08-15T01:00:00Z",
        }
    ]
    assert buckets["learning_queue"] == buckets["due_now"] == buckets["due_today"] == []


def test_render_md_appends_bucket_section(tmp_path):
    """用户可感面: 人读清单末尾多出「分层队列」段 (计数行 + 每节点桶位标签
    与 why_due); 原表格 / 一键开考段零改动。"""
    payload, ranked = _build(
        tmp_path,
        {
            "新卡节点": _node(),
            "学习节点": _node(extra="fsrs_due: 2026-07-28T01:00:00Z\nfsrs_state: 1\n"),
            "未来节点": _node(board="别板", extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
        },
    )
    md = picker.render_md(payload, ranked)
    assert "## 分层队列" in md
    assert "新卡 1 · 学习中 1 · 到期待复习 0 · 今天晚些到期 0 · 未来排期 1" in md
    assert "- 学习节点 · 普通板 — 学习中 · 已逾期 2 天（7月28日到期） · 从未考察" in md
    assert "- 未来节点 · 别板 — 16 天后 8月15日 09:00 到期" in md
    # 既有段落不受影响 (加性: 只在末尾追加)
    assert "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |" in md
    assert "`/start-exam-board from 普通板 node 学习节点`" in md, "命令段仍绑定 pick 最低节点, 不受分桶影响"


# ── Codex round-1 整改回归 (CARD-G3-6a) ──


def test_dirty_fsrs_due_raw_is_sanitized_in_why_due(tmp_path):
    """Codex round-1 MEDIUM: why_due 会被拼进人读 md 并可能被下游 HTML 渲染。
    脏 fsrs_due 原值必须先过 ISO-8601 白名单 (非白名单字符 → "?") 再截 40 字,
    不得把 frontmatter 里的任意串原样接进渲染面。"""
    payload, ranked = _build(
        tmp_path,
        {"注入": _node(extra="fsrs_due: bad|<img src=x onerror=alert(1)>\n")},
    )
    why = _why_map(payload)["注入"]
    assert why == "到期待复习 · 到期时间无法解析(bad??img src?x onerror?alert?1??)，保守视同到期 · 从未考察"
    # 模板自带的圆括号是定界符, 危险字符只看摘录本身
    excerpt = why.split("(", 1)[1].split(")", 1)[0]
    for ch in "|<>=()":
        assert ch not in excerpt, f"危险字符 {ch!r} 未被安全化"
    assert why in picker.render_md(payload, ranked), "人读清单里落的是同一条安全化字符串"
    # 超长原值截断 (白名单内字符也不例外)
    long_payload, _ = _build(tmp_path, {"超长": _node(extra="fsrs_due: " + "9" * 200 + "\n")})
    assert "(" + "9" * 40 + ")" in _why_map(long_payload)["超长"]


def test_extreme_now_falls_back_instead_of_crashing():
    """Codex round-1 HIGH: 极值 now 的上海日换算会 OverflowError。判桶层必须
    退化 (今天基准回落 UTC 日, 时间槽位用极值兜底文案), 不得抛异常中断整轮。
    直测 assign_bucket: build_payload 在同样输入下会先崩在 HEAD 起就存在的
    payload["date"] = now.astimezone() 上, 那条不属本卡改动面。"""
    now = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    node = {
        "node": "极值",
        "board": "B板",
        "due_now": True,
        "fsrs_due": "9999-12-31T23:59:59Z",
        "due_fail_open": False,
        "fsrs_due_raw": "9999-12-31T23:59:59Z",
        "fsrs_state": None,
        "idle_days": None,
    }
    bucket, why = picker.assign_bucket(node, now)
    assert bucket == "due_now"
    assert why == "到期待复习 · 到期时刻超出可显示范围 · 从未考察"
    # 未到期侧的极值兜底 (归 future, 不猜日期)
    future_node = {**node, "due_now": False}
    assert picker.assign_bucket(future_node, datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)) == (
        "future",
        "到期时刻超出可显示范围，按未来排期处理",
    )
    # 今天基准退化为 UTC 日 (不崩)
    assert picker._today_sh(now) == now.date()


def test_cli_rejects_unconvertible_now_with_clear_error(tmp_path):
    """Codex round-1 HIGH: 极值 --now 在 HEAD 起就会抛 OverflowError traceback
    中断整轮 (崩在 payload["date"])。入口改为明确拒绝 —— 退出码非 0、给人话
    原因、不吐 traceback; 正常 --now 不受影响。"""
    import json
    import subprocess

    vault = tmp_path / "clivault"
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    (vault / "节点" / "存量.md").write_text(_node(), encoding="utf-8")
    cmd = [sys.executable, str(WT / "scripts" / "daily_review_pick.py"), "--vault", str(vault), "--now"]

    bad = subprocess.run([*cmd, "9999-12-31T23:59:59Z"], capture_output=True, text=True)
    assert bad.returncode != 0
    assert "--now 超出可换算范围" in bad.stderr
    assert "Traceback" not in bad.stderr, "极值输入不得吐 traceback"

    ok = subprocess.run([*cmd, "2026-07-30T01:00:00Z"], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    assert json.loads(ok.stdout)["stats"]["due_nodes"] == 1


def test_today_sh_three_tier_fallback_never_raises():
    """Codex round-2 MEDIUM: UTC 回退本身也可能溢出 (year=1 且 offset=+14,
    换算需减 14 小时 → 年份下溢)。三档兜底必须保证本函数对任何 aware
    datetime 都不抛。"""
    up = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    assert picker._today_sh(up) == up.date(), "上界: 上海换算溢出 → 退 UTC 日"
    low = datetime(1, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=14)))
    assert picker._today_sh(low) == low.date(), "下界: 上海与 UTC 换算双溢出 → 退自身表示日"
    normal = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)
    assert picker._today_sh(normal).isoformat() == "2026-07-30", "常规值仍走上海日"


# ════════════════════════════════════════════════════════════════════
# CARD-G6-1 (BATCH-2026-08-31-第七批) atomic_write tmp 唯一化
# ════════════════════════════════════════════════════════════════════


def test_atomic_write_abandons_legacy_fixed_tmp_name(tmp_path):
    """旧实现固定用 `<原名>.tmp`, 两个并发写者共享同一个 tmp —— 各按自己的
    offset 落盘, 内容交错, 总长等于较长那份 (wc -c 看不出), 随后双方
    os.replace 发布同一个拼接损坏物。

    这里在那个固定名上放一个**目录**: 只要实现还在用它, write_text 必炸
    (IsADirectoryError); 唯一化后的实现根本不碰它, 照常发布。确定性门,
    不靠赛跑概率。
    """
    target = tmp_path / "今日复习.json"
    legacy_tmp = tmp_path / "今日复习.json.tmp"  # 旧实现: with_suffix(".json.tmp")
    legacy_tmp.mkdir()

    picker.atomic_write(target, '{"schema_version": 3}\n')

    assert target.read_text(encoding="utf-8") == '{"schema_version": 3}\n'
    assert legacy_tmp.is_dir(), "旧固定名不该被碰"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["今日复习.json", "今日复习.json.tmp"], (
        "发布后不得残留任何 tmp"
    )


def _pin_tmp_name(monkeypatch, hex8: str = "deadbeef"):
    """把 picker 内的 uuid 换成定值, 让 tmp 名可预测 —— 只替换 picker 模块里
    的那个引用 (monkeypatch.setattr(picker, "uuid", ...)), 不动全局 uuid 模块。
    返回给定 target 的确切 tmp 路径。"""
    monkeypatch.setattr(picker, "uuid", types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex=hex8 + "0" * 24)))
    return lambda target: target.with_name(f"{target.name}.{os.getpid()}.{hex8}.tmp")


def test_atomic_write_refuses_to_reuse_an_existing_tmp(tmp_path, monkeypatch):
    """O_EXCL: tmp 名万一撞上已存在的文件, 必须直接失败, **不能**打开它接着写
    —— 那等于两个写者又共享了同一个 tmp, 正是本改动要消灭的东西。
    且不许把别人的那个文件删掉或截断 (它不是我们建的)。

    观测手段: 把 picker 内的 uuid 钉成定值让 tmp 名可预测 —— 不打桩
    os.replace / os.open (patch 进程内共享的 os 属性会连 pathlib 内部一起拦)。
    """
    tmp_of = _pin_tmp_name(monkeypatch)
    target = tmp_path / "今日复习.json"
    squatter = tmp_of(target)
    squatter.write_text("别人的在途内容\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        picker.atomic_write(target, '{"schema_version": 3}\n')

    assert squatter.read_text(encoding="utf-8") == "别人的在途内容\n", "不许截断/删除别人的 tmp"
    assert not target.exists(), "失败就不该发布任何东西"


def test_atomic_write_does_not_follow_a_symlinked_tmp(tmp_path, monkeypatch):
    """tmp 名被抢先建成一条指向库外的软链时, 必须直接失败, 不许把内容写到库外。

    ⚠ 如实说明这条测试**实际证的是什么**（收官审计抓到, 原 docstring 名不副实）:
    它证的是 `O_EXCL`, 不是 `O_NOFOLLOW`。实测: 对一个软链路径调
    `os.open(p, O_WRONLY|O_CREAT|O_EXCL)` —— **不带** O_NOFOLLOW —— 同样抛
    `FileExistsError(17)`, 因为 O_CREAT|O_EXCL 遇到任何已存在的名字（软链也算
    一个名字）都失败。也就是说在本调用形态下 O_NOFOLLOW 被 O_EXCL 完全遮蔽,
    是纵深防御而非承重件, 单独删掉它这条用例照样绿。
    保留 O_NOFOLLOW 的理由: 若将来有人把 O_EXCL 去掉（比如为了"tmp 残留时能
    覆盖"），O_NOFOLLOW 是仅剩的那道挡软链的门 —— 但届时必须补一条真能打红
    它的用例, 不能沿用这一条。
    """
    tmp_of = _pin_tmp_name(monkeypatch)
    target = tmp_path / "今日复习.json"
    outside = tmp_path / "库外落点.txt"
    tmp_of(target).symlink_to(outside)

    with pytest.raises(OSError):
        picker.atomic_write(target, "机密内容\n")

    assert not outside.exists(), "内容不许顺着软链写到库外"
    assert not target.exists()


def test_atomic_write_publishes_and_leaves_no_residue(tmp_path):
    """正常路径 (真随机 tmp 名): 两个不同 target 各自发布成功, 目录里不留残渣。"""
    picker.atomic_write(tmp_path / "今日复习.json", "a\n")
    picker.atomic_write(tmp_path / "今日复习.md", "b\n")
    assert (tmp_path / "今日复习.json").read_text(encoding="utf-8") == "a\n"
    assert (tmp_path / "今日复习.md").read_text(encoding="utf-8") == "b\n"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["今日复习.json", "今日复习.md"]


def test_atomic_write_cleans_tmp_when_publish_fails(tmp_path):
    """发布失败必须清掉半截 tmp —— 留在 vault 里同样是写面污染 (且会被
    Obsidian 同步 / 备份链一路带走)。target 是目录时 os.replace 必失败。"""
    target = tmp_path / "今日复习.json"
    target.mkdir()

    with pytest.raises(OSError):
        picker.atomic_write(target, "内容\n")

    assert list(tmp_path.glob("今日复习.json.*.tmp")) == [], "失败路径必须清掉 tmp 残渣"
    assert target.is_dir(), "失败不该把 target 改成别的东西"


# ── CARD-G3-6b: 板级 why_this_board 与系数版本化 (BATCH-2026-09-01-第八批) ──
# S4 排序因子清单显式化 + why_this_board 由 factors 单向复算 (禁 LLM / 禁 UI 再算)
# S5 系数 manifest: authoritative(改了真生效) vs recorded(改了只告警);
#    sha256 摘的是「运行时生效值」而不是 manifest 文件字节
# S6 无归属 / 一节点多板 / 同名板 / 上限 / 去重 五条裁定各配独立测试

#: 本卡开工基线 (worktree 分叉点) —— 排序金样对比的「改动前」版本。
#: ⚠ 用固定 SHA 而不是 HEAD: 本卡一旦提交, HEAD 就是改动后的版本, 拿它当基准
#: 等于自己跟自己比 —— 那是一道恒绿的假门。
_BASELINE_SHA = "9af18b27"

#: manifest 真文件 (生产默认加载的那一份)
_REAL_MANIFEST = WT / "scripts" / "review_rank_manifest.json"


def _fake_decay(**over):
    """只带 S5 六个系数的假 decay —— effective_rank_config 只 getattr 这六个。"""
    base = {"PRIOR_A": 0.9, "PRIOR_B": 2.1, "GAMMA": 0.9, "BETA_EXPLORE": 1.0, "FLOOR": 0.05, "GAMMA_DAILY": 0.99}
    base.update(over)
    return types.SimpleNamespace(**base)


def _sha_of(decay=None, version=1, minutes=None):
    return picker.build_rank_manifest(decay or _fake_decay(), version, minutes or dict(picker.DEFAULT_MINUTES), {})[
        "sha256"
    ]


def _write_manifest(tmp_path, obj, name="manifest.json") -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return p


def _mk_min_vault(tmp_path, name: str, nodes: dict):
    """带 decay_beta 的最小 vault (需要显式传 manifest_path 的用例用)。"""
    vault = tmp_path / name
    (vault / ".claude" / "scripts").mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", vault / ".claude" / "scripts")
    for stem, content in nodes.items():
        (vault / "节点" / f"{stem}.md").write_text(content, encoding="utf-8")
    return vault


# ── S4: why_this_board 由 factors 复算 ──


def test_g36b_why_this_board_recomputes_from_factors(tmp_path):
    """S4 核心契约: 把落盘的 factors 原样喂回 why_this_board(), 必须逐字得到
    落盘的那句话 —— 解释与数字之间没有第二条通路。

    多形态同时在场 (纯新卡板 / 逾期板 / 脏日期板 / 有冷却记录的板), 让模板的
    多个分支同时成立, 而不是只验一条最顺的路径。"""
    payload, _ = _build(
        tmp_path,
        {
            "新甲": _node(board="全新板"),
            "逾期乙": _node(
                board="逾期板", extra="fsrs_due: 2026-07-01T01:00:00Z\nlast_examined: 2026-07-10T01:00:00Z\n"
            ),
            "脏丙": _node(board="脏板", extra="fsrs_due: 2026-13-01T00:00:00Z\n"),
            "冷丁": _node(board="冷却板"),
        },
        blr={"冷却板": "2026-07-25"},
    )
    assert len(payload["top_boards"]) == 3, "四块板到期, top_boards 截 3"
    for row in payload["top_boards"]:
        f = row["factors"]
        assert picker.why_this_board(f) == row["why_this_board"], (
            f"{row['board']}: factors 代回模板与落盘不符 — 解释脱离了数字"
        )
        assert row["estimated_minutes"] == picker.estimated_minutes(f, picker.DEFAULT_MINUTES)
        assert row["why_this_board"], "why_this_board 恒非空"


def test_g36b_why_this_board_char_whitelist_holds(tmp_path):
    """S4 字符白名单: 成句只含 中文/数字/·/空格/全角括号。

    敌对板名与节点名在场 —— 它们**不进句**正是本门要证的事 (板名已在同行的
    board 字段里; 拼进解释既冗余, 又把 frontmatter 自由文本引进渲染面)。"""
    hostile = "<script>alert(1)</script>"
    payload, _ = _build(
        tmp_path,
        {
            "恶意<img src=x>": _node(board=hostile),
            "正常": _node(board="普通板"),
        },
    )
    assert len(payload["top_boards"]) == 2
    for row in payload["top_boards"]:
        why = row["why_this_board"]
        assert picker._WHY_BOARD_UNSAFE.sub("?", why) == why, f"白名单外字符: {why!r}"
        assert "<" not in why and ">" not in why
        assert hostile not in why and "恶意" not in why, "板名/节点名不许进解释句"


def test_g36b_factors_three_way_split_is_exhaustive_and_matches_rollup(tmp_path):
    """S4: due_new + due_scheduled + due_malformed 恒 == due_total, 且与 boards
    rollup 的 due 三分同一条判据 (不另立第二套口径)。"""
    payload, _ = _build(
        tmp_path,
        {
            "新卡": _node(board="混合板"),
            "已排期": _node(board="混合板", extra="fsrs_due: 2026-07-01T01:00:00Z\n"),
            "脏日期": _node(board="混合板", extra="fsrs_due: 2026-13-01T00:00:00Z\n"),
        },
    )
    f = payload["top_boards"][0]["factors"]
    assert f["due_new"] + f["due_scheduled"] + f["due_malformed"] == f["due_total"] == 3
    assert (f["due_new"], f["due_scheduled"], f["due_malformed"]) == (1, 1, 1)
    rollup = {r["board"]: r for r in payload["boards"]}["混合板"]
    assert f["due_total"] == rollup["due"], "与 rollup 的 due 计数同源"
    assert f["due_new"] == rollup["due_new"] and f["due_scheduled"] == rollup["due_scheduled"]


def test_g36b_factors_share_source_with_existing_row_fields(tmp_path):
    """S4: factors 不是第二份数据 —— due_total == pending, idle_days == 同行
    idle_days。两者漂移意味着解释在说另一块板的事。"""
    payload, _ = _build(
        tmp_path,
        {
            "老节点": _node(extra="mastery_a: 2.0\nmastery_b: 3.0\nlast_examined: 2026-07-10T01:00:00Z\n"),
            "同板另一个": _node(),
        },
    )
    row = payload["top_boards"][0]
    assert row["factors"]["due_total"] == row["pending"] == 2
    assert row["factors"]["idle_days"] == row["idle_days"]


def test_g36b_template_covers_every_branch():
    """S4 模板 6 组分支逐条锁定 (纯函数直测, 不经 vault)。

    含两条「没有 vs 算不出」的区分: due_scheduled==0 时整个紧迫段消失 (全新卡
    的板没有"逾期"可言); due_scheduled>0 而 overdue_days is None 时如实说
    "超出可显示范围", 不假装 0 天。"""
    base = {
        "due_total": 1,
        "due_new": 0,
        "due_scheduled": 1,
        "due_malformed": 0,
        "overdue_days": 5,
        "idle_days": 3,
        "never_recommended": False,
        "recommend_gap_days": 2,
    }

    def why(**over):
        return picker.why_this_board({**base, **over})

    assert why() == "1 个节点到期 · 最早的已逾期 5 天 · 最该考的已闲置 3 天 · 距上次推荐 2 天"
    assert why(due_total=4, due_new=2).startswith("4 个节点到期（其中 2 张新卡）")
    assert "最早的今天到期" in why(overdue_days=0)
    assert "最早到期时刻超出可显示范围" in why(overdue_days=None)
    no_sched = why(due_scheduled=0, overdue_days=None)
    assert "逾期" not in no_sched and "到期时刻" not in no_sched, "无已排期节点则紧迫段整段省略"
    assert "含 2 个到期时间无法解析的节点" in why(due_malformed=2)
    assert "最该考的从未考察" in why(idle_days=None)
    assert "这块板从未被推荐过" in why(never_recommended=True)
    assert "今天已推荐过" in why(recommend_gap_days=0)
    assert "上次推荐日期无法解析" in why(recommend_gap_days=None)
    assert "上次推荐日期晚于今天" in why(recommend_gap_days=-3), "记录晚于今天必须说异常, 不许 clamp 成 0"


def test_g36b_corrupt_recommend_date_is_not_mistaken_for_never(tmp_path):
    """S4: state 里的推荐日期损坏 → 如实说"算不出", 绝不当成"从未推荐过"
    (那会让一块刚推过的板伪装成冷板, 拿到不该有的解释)。"""
    payload, _ = _build(tmp_path, {"甲": _node(board="A板")}, blr={"A板": "不是日期"})
    row = payload["top_boards"][0]
    assert row["factors"]["never_recommended"] is False
    assert row["factors"]["recommend_gap_days"] is None
    assert "上次推荐日期无法解析" in row["why_this_board"]
    assert "从未被推荐" not in row["why_this_board"]


def test_g36b_estimated_minutes_weights_new_cards_higher(tmp_path):
    """S5: 新卡按 per_new_node(5), 其余到期按 per_due_node(3) —— 三分互斥完备
    使这两类恰好覆盖全部到期节点。"""
    payload, _ = _build(
        tmp_path,
        {
            "新一": _node(board="板"),
            "新二": _node(board="板"),
            "排期": _node(board="板", extra="fsrs_due: 2026-07-01T01:00:00Z\n"),
        },
    )
    row = payload["top_boards"][0]
    assert row["factors"]["due_new"] == 2 and row["factors"]["due_scheduled"] == 1
    assert row["estimated_minutes"] == 2 * 5 + 1 * 3 == 13


# ── S5: 系数 manifest 与指纹 ──


def test_g36b_rank_manifest_version_and_sha_in_payload(tmp_path):
    """S5: payload 顶层 rank_manifest = {version, sha256}, 两键恒在。"""
    payload, _ = _build(tmp_path, {"甲": _node()})
    rm = payload["rank_manifest"]
    assert set(rm) == {"version", "sha256"}
    assert rm["version"] == 1, "生产 manifest 当前 version=1"
    assert re.fullmatch(r"[0-9a-f]{64}", rm["sha256"]), "sha256 十六进制定长"


def test_g36b_sha_changes_for_every_single_coefficient(monkeypatch):
    """S5 逐项变异: 任何一个系数变了, 指纹必须变 —— 一项都不能漏。

    漏掉任何一项 = 那个系数被改了而版本化毫无察觉, 版本化就成了摆设。"""
    baseline = _sha_of()
    assert _sha_of(version=2) != baseline, "version"
    assert _sha_of(minutes={"per_due_node": 4, "per_new_node": 5}) != baseline, "per_due_node"
    assert _sha_of(minutes={"per_due_node": 3, "per_new_node": 6}) != baseline, "per_new_node"
    for name in picker.DECAY_CONSTANT_NAMES:
        assert _sha_of(decay=_fake_decay(**{name: 12.5})) != baseline, f"decay 常量 {name} 变了指纹却没动"

    class _Missing:  # 模块被删了五个常量 —— 缺了也是变了
        PRIOR_A = 0.9

    assert _sha_of(decay=_Missing()) != baseline, "decay 常量缺失"

    # Codex round-2 HIGH: 可执行取值规则 (精度/因子序) 也必须进指纹
    monkeypatch.setattr(picker, "TIE_PICK_ROUND_DIGITS", 7)
    assert _sha_of() != baseline, "pick 取整精度变了指纹却没动"
    monkeypatch.setattr(
        picker, "TIE_FACTOR_KEYS", ("priority_pick", "board", "min_last_examined", "board_last_recommended")
    )
    assert _sha_of() != baseline, "因子序变了指纹却没动"


def test_g36b_sha_digests_effective_values_not_file_bytes(tmp_path):
    """S5 本卡最容易做假的一条, 正反双向验:

    正向 — 一个字节都不碰 manifest 文件, 只改 decay 模块的系数 → sha 必须变。
           (「对 manifest 文件取 hash」的实现在这里恒绿 —— 那正是本门的靶子。)
    反向 — 只改文件里的说明文字, 生效值一个没变 → sha 必须不变。
           (「把整个文件塞进摘要」的实现在这里会红。)
    """
    real = json.loads(_REAL_MANIFEST.read_text(encoding="utf-8"))
    v, minutes, recorded = picker.load_rank_manifest(_REAL_MANIFEST)
    baseline = picker.build_rank_manifest(_fake_decay(), v, minutes, recorded)["sha256"]

    moved = picker.build_rank_manifest(_fake_decay(GAMMA=0.5), v, minutes, recorded)["sha256"]
    assert moved != baseline, "改 decay 系数(不碰文件) 指纹必须变"

    chatty = json.loads(json.dumps(real))
    chatty["_说明"] = "改一段与生效值无关的说明文字"
    chatty["recorded"]["_说明"] = "同上"
    v2, m2, r2 = picker.load_rank_manifest(_write_manifest(tmp_path, chatty))
    same = picker.build_rank_manifest(_fake_decay(), v2, m2, r2)["sha256"]
    assert same == baseline, "只改说明文字, 生效值没变, 指纹不该变"


def test_g36b_recorded_decay_snapshot_matches_real_module(tmp_path):
    """S5: manifest 登记的 decay 六常量必须与 vault 内 decay_beta.py 实际值一致。

    登记抄错 = 指纹旁边挂着一份指向不存在配置的说明, 且漂移告警会天天刷。
    decay_beta.py 将来被改而 manifest 忘了同步时, 本门变红 —— 那正是它该
    说话的时刻。"""
    decay = picker.load_decay(_mk_min_vault(tmp_path, "snapshot_v", {}))
    _, _, recorded = picker.load_rank_manifest(_REAL_MANIFEST)
    claimed = picker._recorded_claim(recorded, "decay_beta_constants")
    actual = {k: getattr(decay, k) for k in picker.DECAY_CONSTANT_NAMES}
    assert claimed == actual, "manifest 登记的 decay 常量与 decay_beta.py 实际值不符"


def test_g36b_recorded_ranking_and_limits_match_code():
    """S5: recorded 的因子序与上限必须与代码真相源一致 (同上, 登记不许过期)。"""
    _, _, recorded = picker.load_rank_manifest(_REAL_MANIFEST)
    assert picker._recorded_claim(recorded, "ranking_factors", "order") == list(picker.TIE_FACTOR_KEYS)
    assert picker._recorded_claim(recorded, "limits") == {
        "top_boards": picker.TOP_BOARDS_LIMIT,
        "upcoming": picker.UPCOMING_LIMIT,
    }


def test_g36b_authoritative_minutes_actually_take_effect(tmp_path):
    """S5 authoritative 名副其实: 改 manifest 的分钟常量, 下一轮真的按新值算。

    这是「拍脑袋值请用户改」那句承诺的可执行形态 —— 改了不生效就是假配置。"""
    mp = _write_manifest(
        tmp_path,
        {
            "version": 7,
            "authoritative": {"estimated_minutes": {"per_due_node": 10, "per_new_node": 20}},
        },
    )
    vault = _mk_min_vault(
        tmp_path,
        "auth_v",
        {
            "新一": _node(board="板"),
            "排期": _node(board="板", extra="fsrs_due: 2026-07-01T01:00:00Z\n"),
        },
    )
    payload, _ = picker.build_payload(vault, NOW, {}, picker.load_decay(vault), manifest_path=mp)
    assert payload["rank_manifest"]["version"] == 7
    assert payload["top_boards"][0]["estimated_minutes"] == 1 * 20 + 1 * 10 == 30


def test_g36b_missing_or_corrupt_manifest_degrades_honestly(tmp_path, capsys):
    """S5: 清单缺失/损坏 → version=None (诚实说"没有版本") + stderr 点名 +
    内置默认继续算。绝不静默 (静默 = 把配置断裂伪装成"就该是这个数"),
    也绝不让每日推送整轮失败。"""
    v, minutes, recorded = picker.load_rank_manifest(tmp_path / "不存在.json")
    assert v is None and minutes == picker.DEFAULT_MINUTES and recorded == {}
    assert "系数清单不可用" in capsys.readouterr().err

    broken = tmp_path / "broken.json"
    broken.write_text("{ 这不是 json", encoding="utf-8")
    v2, m2, _ = picker.load_rank_manifest(broken)
    assert v2 is None and m2 == picker.DEFAULT_MINUTES
    assert "系数清单不可用" in capsys.readouterr().err

    v3, _, _ = picker.load_rank_manifest(_write_manifest(tmp_path, [1, 2, 3], "arr.json"))
    assert v3 is None and "不是 object" in capsys.readouterr().err

    bad_minutes = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "authoritative": {"estimated_minutes": {"per_due_node": -5, "per_new_node": "十"}},
        },
        "badmin.json",
    )
    v4, m4, _ = picker.load_rank_manifest(bad_minutes)
    assert v4 == 1 and m4 == picker.DEFAULT_MINUTES, "非法分钟逐项回落内置默认"
    err = capsys.readouterr().err
    assert "per_due_node 缺失或非法" in err and "per_new_node 缺失或非法" in err

    # Codex round-1 MEDIUM: 缺键与非法值同等待遇 —— 只写一半的配置不许静默
    half = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "authoritative": {"estimated_minutes": {"per_due_node": 8}},
        },
        "half.json",
    )
    v4b, m4b, _ = picker.load_rank_manifest(half)
    assert v4b == 1 and m4b["per_due_node"] == 8 and m4b["per_new_node"] == 5
    assert "per_new_node 缺失或非法" in capsys.readouterr().err, "缺键必须点名, 不许静默回落"

    v5, _, _ = picker.load_rank_manifest(_write_manifest(tmp_path, {"version": "一"}, "badver.json"))
    assert v5 is None and "version 非整数" in capsys.readouterr().err


def test_g36b_degraded_manifest_still_produces_usable_payload(tmp_path):
    """S5: 清单丢了, 投影仍然完整可用 —— version 为 None, 其余一切照常。"""
    vault = _mk_min_vault(tmp_path, "degraded_v", {"甲": _node()})
    payload, _ = picker.build_payload(
        vault, NOW, {}, picker.load_decay(vault), manifest_path=tmp_path / "没有这个文件.json"
    )
    assert payload["rank_manifest"]["version"] is None
    assert re.fullmatch(r"[0-9a-f]{64}", payload["rank_manifest"]["sha256"])
    assert payload["top_boards"][0]["why_this_board"]
    assert payload["top_boards"][0]["estimated_minutes"] == 5
    json.dumps(payload, ensure_ascii=False, allow_nan=False)


def test_g36b_recorded_drift_warns_but_actual_value_wins(tmp_path, capsys):
    """S5 recorded 是快照不是配置: 登记值与实际不符 → 出声告警, 但一律以实际
    为准。特别是 limits —— 改登记不该偷偷改变 A2 冻结的榜长。"""
    mp = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "recorded": {
                "limits": {"top_boards": 99, "upcoming": 99},
                "ranking_factors": {"order": ["瞎写的"]},
                "decay_beta_constants": {"GAMMA": 0.123},
            },
        },
    )
    v, minutes, recorded = picker.load_rank_manifest(mp)
    picker.build_rank_manifest(_fake_decay(), v, minutes, recorded)
    err = capsys.readouterr().err
    assert "recorded.limits 与实际生效值不符" in err
    assert "recorded.ranking_factors.order 与实际生效值不符" in err
    assert "recorded.decay_beta_constants 与实际生效值不符" in err
    assert "以实际为准" in err
    assert picker.TOP_BOARDS_LIMIT == 3 and picker.UPCOMING_LIMIT == 3, "登记的 99 不改变实际行为"


# ── S6: 无归属 / 一节点多板 / 同名板 / 上限 / 去重 (五裁定各配独立测试) ──


def test_g36b_unassigned_nodes_never_enter_any_board_surface(tmp_path):
    """S6 无归属 (HEAD 既有语义, 本卡独立锁定): 无 source_board 的节点不进
    任何板面 (top_boards / boards rollup / buckets), 点名在 unassigned_nodes
    —— 既不静默消失, 也不虚构归属。"""
    payload, ranked = _build(
        tmp_path,
        {
            "孤儿": "---\ntype: concept\n---\n真实内容。\n",
            "正常": _node(),
        },
    )
    assert payload["unassigned_nodes"] == ["孤儿"]
    assert payload["stats"]["unassigned"] == 1
    surfaces = (
        [r["board"] for r in payload["top_boards"]]
        + [r["board"] for r in payload["boards"]]
        + [r["board"] for r in payload["upcoming"]]
        + [row["board"] for rows in payload["buckets"].values() for row in rows]
    )
    assert "孤儿" not in surfaces, "无归属节点不得出现在任何板面"
    assert payload["stats"]["due_nodes"] == 1


def test_g36b_yaml_array_source_board_lands_unassigned(tmp_path):
    """S6 多板形态 a (2026-09-01 实测, 非推理): YAML 数组写法
    `source_board: ["[[A]]", "[[B]]"]` → _fm_str 的 `[^"\\n]+?` 跨不过内嵌
    引号 → 视同"无 source_board" → 进 unassigned_nodes 点名。现状锁定,
    不为现网不存在的形态发明多板归属语义。"""
    payload, _ = _build(
        tmp_path,
        {
            "数组板": '---\ntype: concept\nsource_board: ["[[原白板/A板]]", "[[原白板/B板]]"]\n---\n真实内容。\n',
            "正常": _node(),
        },
    )
    assert payload["unassigned_nodes"] == ["数组板"], "数组写法视同无归属并点名"
    assert [r["board"] for r in payload["top_boards"]] == ["普通板"]


def test_g36b_comma_multi_board_lands_on_last_segment(tmp_path):
    """S6 多板形态 b (实测锁定): 单串双 wikilink `"[[A]], [[B]]"` → 整串当一
    个板名, rsplit 归到**最后**一个路径段 (不是第一个)。该形态现网为 0;
    "会静默错归"的风险已登记验收单 —— 修它要动 _board_name 归一规则, 影响
    全部单值节点的板身份, 超出本卡加性边界。"""
    payload, _ = _build(
        tmp_path,
        {
            "双链": '---\ntype: concept\nsource_board: "[[原白板/A板]], [[原白板/B板]]"\n---\n真实内容。\n',
        },
    )
    assert payload["unassigned_nodes"] == []
    assert payload["top_boards"][0]["board"] == "B板"


def test_g36b_same_name_boards_from_different_paths_merge(tmp_path):
    """S6 同名板: [[原白板/X]] 与 [[别路径/X]] 归一后是同一块板。板名是全链路
    的板身份 (notification 标题 / obsidian 深链 / state 的 board_last_recommended
    键 / rollup 行键全按板名), 只在选点侧改成带路径身份会与其余四处不一致。"""
    payload, _ = _build(
        tmp_path,
        {
            "甲": '---\ntype: concept\nsource_board: "[[原白板/同板]]"\n---\n真实内容。\n',
            "乙": '---\ntype: concept\nsource_board: "[[别的路径/同板]]"\n---\n真实内容。\n',
        },
    )
    assert [r["board"] for r in payload["top_boards"]] == ["同板"]
    assert payload["top_boards"][0]["pending"] == 2
    assert payload["top_boards"][0]["factors"]["due_total"] == 2


def test_g36b_truncated_flags(tmp_path):
    """S6 上限: 4 块到期板 → truncated.top_boards=True 且榜仍 [:3] 不变;
    4 块纯未来板 → truncated.upcoming=True; 不足上限 → 双 False。
    截断行为 HEAD 起就有, 本门锁的是「把截过这件事说出真话」。"""
    payload, _ = _build(tmp_path, {f"节点{i}": _node(board=f"板{i}") for i in range(4)})
    assert len(payload["top_boards"]) == 3
    assert payload["truncated"] == {"top_boards": True, "upcoming": False}

    payload2, _ = _build(
        tmp_path,
        {f"未来{i}": _node(board=f"未板{i}", extra="fsrs_due: 2026-08-15T01:00:00Z\n") for i in range(4)},
    )
    assert len(payload2["upcoming"]) == 3 and payload2["top_boards"] == []
    assert payload2["truncated"] == {"top_boards": False, "upcoming": True}

    payload3, _ = _build(tmp_path, {"唯一": _node()})
    assert payload3["truncated"] == {"top_boards": False, "upcoming": False}


def test_g36b_no_board_appears_in_both_ranked_and_upcoming(tmp_path):
    """S6 去重: 板名在 ranked / upcoming 互斥 (有到期 → ranked, 全员未到期 →
    upcoming); 板级按 dict 键唯一, ranked 内无重复板名。"""
    payload, _ = _build(
        tmp_path,
        {
            "甲": _node(board="A板"),
            "丙": _node(board="A板", extra="fsrs_due: 2026-08-15T01:00:00Z\n"),  # A板 混合 → ranked
            "乙": _node(board="B板", extra="fsrs_due: 2026-08-15T01:00:00Z\n"),  # B板 纯未来 → upcoming
        },
    )
    ranked_names = [r["board"] for r in payload["top_boards"]]
    upcoming_names = [u["board"] for u in payload["upcoming"]]
    assert ranked_names == ["A板"] and upcoming_names == ["B板"]
    assert set(ranked_names) & set(upcoming_names) == set(), "同一板不得双列"
    assert len(ranked_names) == len(set(ranked_names)), "ranked 内无重复板名"


# ── 金样: 本卡新增字段的完整冻结 + 与开工基线的排序逐字对比 ──


def test_g36b_golden_new_fields_frozen(tmp_path):
    """G3-6b 金样 (累积冻结链第三环): 本卡新增字段的值逐字冻结。旧字段的
    冻结由 D1 / G3-6a 两个累积金样承担 (它们已各自 pop 掉本卡字段后与各自
    时代之前的字面量全等) —— 本测试守的是「本卡加了什么」。下一轮加性卡
    应在本断言基础上 pop 自己的字段后与这份字面量全等。"""
    payload, _ = _build(
        tmp_path,
        {
            "存量": _node(),
            "已排期": _node(board="别板", extra="fsrs_due: 2026-08-15T01:00:00Z\n"),
            "占位": _node().replace("真实内容。", "> 你的 1-2 句精准定义"),
        },
    )
    tb = payload["top_boards"][0]
    assert list(tb) == [
        "board",
        "top_node",
        "priority",
        "pending",
        "idle_days",
        "difficulty",
        "next_due",
        "why_this_board",
        "estimated_minutes",
        "factors",
    ], "top_boards 行键序: 旧七字段在前, 本卡三件套行尾追加"
    assert tb["board"] == "普通板"
    assert tb["why_this_board"] == "1 个节点到期（其中 1 张新卡） · 最该考的从未考察 · 这块板从未被推荐过"
    assert tb["estimated_minutes"] == 5
    assert tb["factors"] == {
        "due_total": 1,
        "due_new": 1,
        "due_scheduled": 0,
        "due_malformed": 0,
        "overdue_days": None,
        "idle_days": None,
        "never_recommended": True,
        "recommend_gap_days": None,
    }
    assert list(tb["factors"]) == [
        "due_total",
        "due_new",
        "due_scheduled",
        "due_malformed",
        "overdue_days",
        "idle_days",
        "never_recommended",
        "recommend_gap_days",
    ], "factors 键序冻结 (落盘 diff 稳定性)"
    assert payload["truncated"] == {"top_boards": False, "upcoming": False}
    assert payload["rank_manifest"]["version"] == 1
    # sha 不冻结字面量 (用户改 manifest 分钟常量是预期内变更), 冻结「与复算一致」:
    # 拿生产 manifest 与生产 decay 重跑指纹函数, 必须逐字复得
    v, minutes, recorded = picker.load_rank_manifest(_REAL_MANIFEST)
    decay = picker.load_decay(_mk_min_vault(tmp_path, "sha_v", {}))
    assert payload["rank_manifest"]["sha256"] == picker.build_rank_manifest(decay, v, minutes, recorded)["sha256"]
    # due_nodes 行: idle_days 行尾追加 (None = 从未考察), 旧键序不动
    assert list(payload["due_nodes"][0]) == [
        "node",
        "board",
        "state",
        "pick",
        "fsrs_due",
        "due_reason",
        "last_examined",
        "difficulty",
        "bucket",
        "why_due",
        "idle_days",
    ]
    assert payload["due_nodes"][0]["idle_days"] is None
    assert list(payload)[-2:] == ["rank_manifest", "truncated"], "顶层键序: 本卡两键在行尾"


def _tie_fixture_vault(tmp_path) -> tuple[Path, Path]:
    """排序金样 fixture: 四块板 pick 全同 (同 mastery 无 fsrs_due), tie-break
    逐级可辨 —— 乙板有推荐记录 (blr 罚后), 其余三块按 板名 排。state 单独
    成文件供两个版本的 CLI 同参消费。"""
    vault = tmp_path / "tiefixture"
    (vault / ".claude" / "scripts").mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", vault / ".claude" / "scripts")
    for board in ("甲板", "乙板", "丙板", "丁板"):
        (vault / "节点" / f"{board}节点.md").write_text(
            "---\ntype: concept\n"
            f'source_board: "[[原白板/{board}]]"\n'
            "mastery_a: 2.0\nmastery_b: 3.0\n---\n真实内容。\n",
            encoding="utf-8",
        )
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"board_last_recommended": {"乙板": "2026-07-28"}}), encoding="utf-8")
    return vault, state


def test_g36b_top_boards_order_matches_head_baseline(tmp_path):
    """S4 排序金样锁: 本卡产出与开工基线 (9af18b27) 的 top_boards 顺序逐字
    相同 —— 本卡只加解释不改序, 改序另立卡。

    走真实 CLI 链路 (subprocess 双跑, 不 import 复刻): 导出基线版 pick.py,
    与工作区版用同一 vault/同一 --now/同一 --state 各跑一次, 对比 stdout
    JSON。本 fixture 让 tie-break 全级在场 (同分 + blr 记录 + 板名), 因此
    落在这几级上的排序改动会在此翻车 —— **不宣称**覆盖全部排序改动 (R1 轮
    HIGH: 改 decay_beta 函数体不经本文件, 见 _implementation_sha 边界第 2 条)。
    live 现网对比另由验收单探针承担, 本测试是 fixture 级常态门。"""
    show = subprocess.run(
        ["git", "-C", str(WT), "show", f"{_BASELINE_SHA}:scripts/daily_review_pick.py"], capture_output=True, text=True
    )
    if show.returncode != 0:
        pytest.skip(f"基线 {_BASELINE_SHA} 不可达 (git show 失败) — live 对比见验收单")
    head_pick = tmp_path / "head_pick.py"
    head_pick.write_text(show.stdout, encoding="utf-8")
    vault, state = _tie_fixture_vault(tmp_path)

    def run(script: Path) -> dict:
        r = subprocess.run(
            [
                sys.executable,
                str(script),
                "--vault",
                str(vault),
                "--now",
                "2026-07-30T01:00:00+00:00",
                "--state",
                str(state),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        assert r.returncode == 0, f"{script.name} 退出 {r.returncode}: {r.stderr[-400:]}"
        return json.loads(r.stdout)

    head_payload, ours_payload = run(head_pick), run(WT / "scripts" / "daily_review_pick.py")
    # 旧七字段逐行逐字相等 + 板序相等 —— 本卡三件套 (why/minutes/factors)
    # 只在 ours 里, 不参与对比
    assert [tb["board"] for tb in head_payload["top_boards"]] == [tb["board"] for tb in ours_payload["top_boards"]], (
        "板序漂移 — 排序被本卡改动"
    )
    for h, o in zip(head_payload["top_boards"], ours_payload["top_boards"]):
        assert h == {k: o[k] for k in h}, f"{h['board']}: 旧七字段值漂移"
    # upcoming / due_nodes / boards / buckets 同序同值 (rollup 与分桶也不许动)。
    # 基线已含 G3-6a (bucket/why_due/buckets 都在), due_nodes 行缺的只有本卡的
    # idle_days — 把 ours 投影到基线行的键集上逐行比
    assert head_payload["upcoming"] == ours_payload["upcoming"]
    assert len(head_payload["due_nodes"]) == len(ours_payload["due_nodes"])
    for h, r in zip(head_payload["due_nodes"], ours_payload["due_nodes"]):
        assert h == {k: r[k] for k in h}, f"due_nodes 行 {h['node']}: 旧字段值漂移"
    assert head_payload["boards"] == ours_payload["boards"]
    assert head_payload["buckets"] == ours_payload["buckets"]
    # 且 ours 的确带上了三件套 (对比不是空集对空集)
    assert all("why_this_board" in tb and "factors" in tb for tb in ours_payload["top_boards"])
    assert len(ours_payload["top_boards"]) == 3 and ours_payload["truncated"]["top_boards"] is True


def test_g36b_future_recommend_date_is_not_disguised_as_today(tmp_path):
    """Codex round-1 MEDIUM: blr 记录晚于 now → 如实说"晚于今天", 不许 clamp
    成 0 伪装成"今天刚推荐过" (S4 不虚构)。"""
    payload, _ = _build(tmp_path, {"甲": _node(board="A板")}, blr={"A板": "2026-08-01"})
    row = payload["top_boards"][0]
    assert row["factors"]["recommend_gap_days"] == -2, "NOW=07-30, 记录 08-01 → gap=-2 原样上抛"
    assert "上次推荐日期晚于今天" in row["why_this_board"]
    assert "今天已推荐过" not in row["why_this_board"]


def test_g36b_tie_keys_are_single_source(tmp_path, monkeypatch):
    """Codex round-1 HIGH 整改门: TIE_FACTOR_KEYS 同时驱动实际排序与 sha 指纹
    —— 交换/删除因子, 板序与指纹必须**同变**。

    Codex 的攻击场景: 因子序存在两份独立表达时, 内存里改 _tie 而 sha 纹丝
    不动, 版本化成摆设。本门锁定的是**本 fixture 上的单向观察**: 交换
    TIE_FACTOR_KEYS 位置后, 板序与 sha **同变**。

    ⚠ R1 收窄, 三处都不宣称 (原措辞"任何…必然…反之亦然"过宽):
    逆命题不成立 (追加重复 `board` 键 = sha 变而排序不变, round-2 LOW 实测);
    也不覆盖全部排序改动 (decay_beta 函数体不经本文件)。

    fixture 设计 (与 pick 级的数学耦合): pick 平要求 top 同参同 idle ⟹ top 的
    last 相同 ⟹ min_last 级在此 fixture 恒平 (两板各单节点, min_last 皆同);
    blr 与 board 的优劣刻意相反 (A 有记录罚后但字典序在前), 交换后才翻转。"""
    vault = _mk_min_vault(
        tmp_path,
        "tie_src",
        {
            # 两板 top 同参同 idle (a=2,b=3, last=07-25) → priority_pick 平;
            # A 板有 blr 记录 (罚后), B 从未 → 默认 [1] B 先;
            # board 字典序 A < B → 交换 blr/board 位置后 A 先 (优劣相反)
            "A1": _node(board="A板", extra="mastery_a: 2.0\nmastery_b: 3.0\nlast_examined: 2026-07-25T01:00:00Z\n"),
            "B1": _node(board="B板", extra="mastery_a: 2.0\nmastery_b: 3.0\nlast_examined: 2026-07-25T01:00:00Z\n"),
        },
    )
    blr = {"A板": "2026-07-28"}
    decay = picker.load_decay(vault)
    nodes = picker.scan_nodes(vault, NOW, decay)[0]

    order_default = [r["board"] for r in picker.rank_boards(nodes, blr, NOW)[0]]
    assert order_default == ["B板", "A板"], "默认序: blr 级先决 (B 从未被推荐)"

    _, minutes, _ = picker.load_rank_manifest(_REAL_MANIFEST)
    sha_before = picker.build_rank_manifest(decay, 1, minutes, {})["sha256"]

    keys = picker.TIE_FACTOR_KEYS
    # 交换位置 1 (blr) 与 3 (board): pick/min_last 平局下, board 级提前
    # 先决 → A板(字典序在前)翻到第一 —— 板序变; sha 同变
    swapped = (keys[0], keys[3], keys[2], keys[1])
    monkeypatch.setattr(picker, "TIE_FACTOR_KEYS", swapped)
    order_swapped = [r["board"] for r in picker.rank_boards(nodes, blr, NOW)[0]]
    assert order_swapped == ["A板", "B板"], "交换因子位置后板序必须随之变化 (单一真相源)"
    sha_after = picker.build_rank_manifest(decay, 1, minutes, {})["sha256"]
    assert sha_after != sha_before, "交换因子位置后 sha 必须同变"


def test_g36b_tie_removing_min_last_level_flips_order(tmp_path, monkeypatch):
    """Codex round-1 MEDIUM (金样覆盖不足) 补强: 删除第三因子 (min_last) 后
    板序必须翻转 —— 证明该因子级在此 fixture 里真实承重, 不是摆设。

    同款耦合说明: blr 级与 board 级的承重已由
    test_tiebreak_prefers_least_recently_recommended 与排序金样 (甲丙丁按
    板名) 承担; pick 级由 test_g36b_tie_pick_level_decides 承担。

    fixture 配平 (浮点精确): 两板 top 同参同 idle (a=2,b=3,last=07-25,
    pick≈0.15356) → pick 平; Z 板第二节点 (a=1.2,b=0.8,last=07-20) 的
    pick≈0.224 > 0.1536 不夺 top, 只把 min_last_Z 拉到 07-20 < min_last_Y
    (07-25) → [2] 先决 Z 先; 板名 Y<Z, 删除 [2] 后按板名 → 翻转。"""
    vault = _mk_min_vault(
        tmp_path,
        "tie_minlast",
        {
            "Z1": _node(board="Z板", extra="mastery_a: 2.0\nmastery_b: 3.0\nlast_examined: 2026-07-25T01:00:00Z\n"),
            "Z2": _node(board="Z板", extra="mastery_a: 1.2\nmastery_b: 0.8\nlast_examined: 2026-07-20T01:00:00Z\n"),
            "Y1": _node(board="Y板", extra="mastery_a: 2.0\nmastery_b: 3.0\nlast_examined: 2026-07-25T01:00:00Z\n"),
        },
    )
    decay = picker.load_decay(vault)
    nodes = picker.scan_nodes(vault, NOW, decay)[0]
    order_default = [r["board"] for r in picker.rank_boards(nodes, {}, NOW)[0]]
    assert order_default == ["Z板", "Y板"], "min_last 级先决 (Z 板最老考察更早)"

    monkeypatch.setattr(picker, "TIE_FACTOR_KEYS", ("priority_pick", "board_last_recommended", "board"))
    order_without = [r["board"] for r in picker.rank_boards(nodes, {}, NOW)[0]]
    assert order_without == ["Y板", "Z板"], "删除 min_last 因子后序必须翻转 (该因子承重)"


def test_g36b_tie_pick_level_decides(tmp_path, monkeypatch):
    """Codex round-2 MEDIUM 修复: pick 级 (首因子) 的决定性 + 承重。

    round-1 版缺陷: 低 pick 恰好落在字典序更早的 A板, 删掉 pick 因子后序
    不变 —— 门空转。现把低 pick 放在字典序**更晚**的 B板, 并断言删除首因子
    后按板名翻转 (证明该因子真实承重, 不是沾板名的光)。"""
    vault = _mk_min_vault(
        tmp_path,
        "tie_pick",
        {
            "A1": _node(board="A板", extra="mastery_a: 5.0\nmastery_b: 1.0\n"),  # 高 pick, 字典序早
            "B1": _node(board="B板", extra="mastery_a: 1.0\nmastery_b: 5.0\n"),  # 低 pick, 字典序晚
        },
    )
    decay = picker.load_decay(vault)
    nodes = picker.scan_nodes(vault, NOW, decay)[0]
    order = [r["board"] for r in picker.rank_boards(nodes, {}, NOW)[0]]
    assert order == ["B板", "A板"], "低 pick 板先 (B 板字典序更晚, 排除板名碰巧决定)"

    monkeypatch.setattr(picker, "TIE_FACTOR_KEYS", ("board_last_recommended", "min_last_examined", "board"))
    order_without = [r["board"] for r in picker.rank_boards(nodes, {}, NOW)[0]]
    assert order_without == ["A板", "B板"], "删除首因子后按板名翻转 — pick 级真实承重"


def test_g36b_tie_precision_is_versioned(tmp_path, monkeypatch):
    """Codex round-2 HIGH 补强: priority_pick 的取整精度是「可执行取值规则」
    的一部分 —— 收紧精度会让 8 位可分的近邻 pick 变同分而改排序, 故精度本身
    必须登记进指纹。

    本门断言两件事 (R1 补强: 原版只验了 sha 侧, **没有调用过排序**, 于是
    "改精度 → 排序变"这半句是空口 —— Codex R1 轮 MEDIUM 指出):
    a) 精度常量登记进被摘要对象, 改它 sha 变;
    b) **改它排序真的变** —— 近邻 pick 差 1e-8 时, 8 位可分而 7 位同分,
       同分后退到 blr 级先决, 板序翻转。"""
    vault = _mk_min_vault(
        tmp_path,
        "tie_prec",
        {
            "A1": _node(board="A板", extra="mastery_a: 2.0\nmastery_b: 3.0\n"),
            "B1": _node(board="B板", extra="mastery_a: 2.0\nmastery_b: 3.0\n"),
        },
    )
    decay = picker.load_decay(vault)
    _, minutes, _ = picker.load_rank_manifest(_REAL_MANIFEST)
    cfg = picker.effective_rank_config(decay, 1, minutes)
    assert cfg["tie_pick_round_digits"] == picker.TIE_PICK_ROUND_DIGITS == 8, "精度必须登记进指纹"

    monkeypatch.setattr(picker, "TIE_PICK_ROUND_DIGITS", 7)
    cfg7 = picker.effective_rank_config(decay, 1, minutes)
    assert cfg7["tie_pick_round_digits"] == 7
    import hashlib

    sha8 = hashlib.sha256(
        json.dumps({**cfg, "tie_pick_round_digits": 8}, sort_keys=True, ensure_ascii=False, allow_nan=False).encode(
            "utf-8"
        )
    ).hexdigest()
    sha7 = hashlib.sha256(
        json.dumps(cfg7, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()
    assert sha7 != sha8, "精度变了指纹必须变"

    # (b) 排序侧承重 (R1 补强 — Codex R1 轮 MEDIUM: 原版从头到尾没调用过
    # rank_boards, 「改精度会改排序」只存在于 docstring 里, 没有可执行形态)。
    # 近邻 pick 差 1e-8: round(_,8) 可分, round(_,7) 双双落到 0.2 而同分,
    # 同分后退到 blr 级先决 → 板序翻转。差值取 5e-8 不成立 (7 位下仍分成
    # 0.2000001 vs 0.2), 这是 fixture 的算术门槛, 不是被测性质。
    def _near(board: str, pick: float) -> dict:
        return {
            "board": board,
            "node": board[0],
            "pick": pick,
            "due_now": True,
            "idle_days": None,
            "difficulty": "",
            "fsrs_due": "",
            "due_fail_open": False,
            "last_examined": "2026-07-25T01:00:00Z",
        }

    near = [_near("A板", 0.20000001), _near("B板", 0.20000000)]
    blr = {"B板": "2026-07-28"}  # B 有推荐记录排后; A 空串排最前 —— 同分时 A 先
    monkeypatch.setattr(picker, "TIE_PICK_ROUND_DIGITS", 8)
    order8 = [r["board"] for r in picker.rank_boards(near, blr, NOW)[0]]
    monkeypatch.setattr(picker, "TIE_PICK_ROUND_DIGITS", 7)
    order7 = [r["board"] for r in picker.rank_boards(near, blr, NOW)[0]]
    assert order8 == ["B板", "A板"], f"8 位可分 → pick 更小的 B 先, 实得 {order8}"
    assert order7 == ["A板", "B板"], f"7 位同分 → 退 blr 级, 无记录的 A 先, 实得 {order7}"
    assert order8 != order7, "改精度必须真的改变排序 —— 否则本门空转"


def test_g36b_tie_keys_unique_and_anchored():
    """Codex round-2 LOW: 因子键唯一性 + board 恒为末级稳定锚 —
    追加重复键会「sha 变而排序不变」, 与版本化语义反向。"""
    keys = picker.TIE_FACTOR_KEYS
    assert len(set(keys)) == len(keys), "因子键不得重复 (重复 = sha 变而排序不变)"
    assert keys[-1] == "board", "board 恒为末级稳定锚"


def test_g36b_implementation_sha_is_registered_and_self_consistent(tmp_path):
    """Codex round-2 HIGH: 实现指纹兜住「改 pick.py **源文件**排序规则而指纹
    不动」(取值绑定无法全部数据化)。门锁三件事: 在场 / 自洽 / 变内容必变。

    ⚠ CARD-G3-6b-R1 收窄证明边界: 本门只证**源文件字节层**, 不证运行时
    完整性 —— 篡改 __pycache__/*.pyc 并伪造 mtime 可让排序变而本 sha 不变
    (round-3 实测复现), 该面明确排除在本卡威胁模型外。断言措辞不得回退成
    「任何改动必变」一类的绝对表述。"""
    cfg = picker.effective_rank_config(_fake_decay(), 1, dict(picker.DEFAULT_MINUTES))
    assert re.fullmatch(r"[0-9a-f]{64}", cfg["implementation_sha256"])
    assert cfg["implementation_sha256"] == picker._implementation_sha(), "与真文件自洽"
    # 同一实现的指纹可由任意路径副本复算 (摘的是字节不是身份)
    twin = tmp_path / "twin_pick.py"
    twin.write_bytes((WT / "scripts" / "daily_review_pick.py").read_bytes())
    assert picker._implementation_sha(twin) == cfg["implementation_sha256"]
    twin.write_bytes(b"# changed\n")
    assert picker._implementation_sha(twin) != cfg["implementation_sha256"], "内容变指纹必变"


def test_g36b_parent_section_missing_warns_not_silent(tmp_path, capsys):
    """Codex round-2 MEDIUM: authoritative 节 / estimated_minutes 子节缺失或
    null, 三种父级形状都必须点名回落, 不许静默。"""
    for i, obj in enumerate(
        (
            {"version": 1},  # 无 authoritative 节
            {"version": 1, "authoritative": {}},  # 子节缺失
            {"version": 1, "authoritative": {"estimated_minutes": None}},  # null
        )
    ):
        v, m, _ = picker.load_rank_manifest(_write_manifest(tmp_path, obj, f"p{i}.json"))
        err = capsys.readouterr().err
        assert v == 1 and m == picker.DEFAULT_MINUTES
        assert "缺失或形状不符" in err and "分钟用内置默认" in err, f"形状{i}必须点名"
