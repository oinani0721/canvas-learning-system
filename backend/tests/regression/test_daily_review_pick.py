"""daily_review_pick 选板逻辑锁定 (DAILY-REVIEW-PUSH-2026-07-29, Code-Review M6)。

12 场景运行时矩阵之外的纯逻辑层: 病理日期不崩全轮 / wikilink 归一 /
占位符跳过 / tie-break 三级 / 脏数值进 corrupt / BOM 容忍。
"""

import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
    assert list(payload) == [k for k in golden if k != "boards"], "顶层键序漂移 (落盘 diff 稳定性)"
    assert [r["board"] for r in boards] == ["别板", "普通板"]
