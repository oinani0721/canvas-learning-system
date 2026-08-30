"""daily_review_pick 选板逻辑锁定 (DAILY-REVIEW-PUSH-2026-07-29, Code-Review M6)。

12 场景运行时矩阵之外的纯逻辑层: 病理日期不崩全轮 / wikilink 归一 /
占位符跳过 / tie-break 三级 / 脏数值进 corrupt / BOM 容忍。
CARD-G3-6a (BATCH-2026-08-29-第六批) 追加: 五桶划分律 (互斥+完备) /
why_due 6 模板 / 加性纯度金样 (pop 新字段后与引入前字面量深度全等)。
"""

import os
import shutil
import sys
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
    for _row in payload["due_nodes"]:
        _row.pop("bucket")
        _row.pop("why_due")
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


def test_atomic_write_tmp_names_are_distinct_across_calls(tmp_path):
    """同目录下两个不同 target 各自的 tmp 名互不相同, 且都以 `<原名>.` 开头
    (与 outputs/今日复习.* 同前缀 —— 不给"只写今日复习.*"的写面审计新增
    可见面), 以 `.tmp` 收尾 (outputs/*.md 一类 glob 不会误吃)。

    观测手段: 在 write_text 落盘的一瞬间用目录快照抓 tmp 名 —— 不打桩
    os.replace (patch 进程内共享的 os 属性会连 pathlib 内部一起拦)。
    """
    seen: list[str] = []
    orig = picker.Path.write_text

    def _spy(self, *a, **kw):
        rc = orig(self, *a, **kw)
        seen.extend(p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp"))
        return rc

    picker.Path.write_text = _spy
    try:
        picker.atomic_write(tmp_path / "今日复习.json", "a\n")
        picker.atomic_write(tmp_path / "今日复习.md", "b\n")
    finally:
        picker.Path.write_text = orig

    assert len(seen) == 2 and len(set(seen)) == 2, f"两次落盘的 tmp 名必须互异: {seen}"
    assert seen[0].startswith("今日复习.json.") and seen[0].endswith(".tmp")
    assert seen[1].startswith("今日复习.md.") and seen[1].endswith(".tmp")
    assert str(os.getpid()) in seen[0], "tmp 名须含 pid — 跨进程并发才不撞"
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
