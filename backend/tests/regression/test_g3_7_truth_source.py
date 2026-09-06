# CARD-G3-7 回归锁定 (BATCH-2026-09-05-第十二批)
# [Source: _bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y9-B.md]
# [Source: _bmad-output/审查/evidence-g37/decision.md]
"""FSRS 真相源收敛回归测试 —— frontmatter 是唯一 current state。

被锁定的裁定 (decision.md)：
  ① PUT /review/record  → 改造：写点降格为投影缓存，加 truth_source 信号，
                           分歧时 degraded_reason 追加 truth_source_divergence，
                           但**不覆盖** next_review_date（它是本次计算结果，
                           不是"该节点当前该何时复习"的声明）。
  ② GET /fsrs-state     → 保留 + 门锁边界：该 concept 在 frontmatter 侧有真相源
                           时，一律不写盘、不推进 _card_states，且 due 以
                           frontmatter 为准。
  ③ mastery grade / ④ save_card_state → 隔离（仅注释，无行为改动，不在本文件覆盖）。

D0 修订 §五 T1：「frontmatter 与任何后端状态不一致时，以 frontmatter 为准，
分歧须以 degraded 信号如实透出」。

自证封堵（卡文 (c)④「fixture 形态 ≠ 生产形态」教训）：
  - 种子 .md 的 frontmatter **逐字抄 live 节点实测形态**
    (canvas-vault/节点/csm-tutoring-unit-credit.md：fsrs_due 未加引号、UTC-Z 秒级)；
  - test_production_reader_reads_seeded_frontmatter 先用**生产 reader** 断言
    种子真的产生了目标形态，再去测消费方——不用 mock reader 自证。

假绿封堵（"跑前跑后没变"可能是门锁做的，也可能是这条路径本来就写不动）：
  - test_gate_blocks_write_when_truth_source_exists（负例：不该写）与
    test_gate_allows_write_when_no_truth_source（**正控**：该写就得写）成对，
    只有两条同时成立才证明"不写"是门锁的功劳。

零写门（卡文 (g)）：本文件全部用例经 module 级 autouse fixture 把
_CARD_STATES_FILE 重定向到 tmp_path，禁写树内 backend/data。
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── live 实测形态（canvas-vault/节点/csm-tutoring-unit-credit.md 逐字抄）──────
# fsrs_bridge.py::FIELD_ORDER 同序；ISO UTC-Z 秒级；**未加引号**（PyYAML 会把它
# 解析成 datetime，而 daily_review_pick / fsrs_bridge 的生产口径是纯 stdlib 正则
# 取字符串——本卡 reader 沿用后者，见 review_service._read_frontmatter_fsrs）。
_FM_DUE = "2026-08-11T13:56:58Z"

_NODE_MD = """---
type: concept
mastery_score: 0.01
last_examined: 2026-08-11T13:55:58Z
fsrs_due: {due}
fsrs_state: 1
fsrs_step: 0
fsrs_stability: 0.212
fsrs_difficulty: 6.4133
fsrs_last_review: 2026-08-11T13:55:58Z
title: G3-7 分歧注入节点
---
# G3-7 分歧注入节点
"""

_NODE_MD_NO_FSRS = """---
type: concept
title: G3-7 无 FSRS 字段节点
---
# G3-7 无 FSRS 字段节点
"""


# ══════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def isolate_card_states(tmp_path, monkeypatch):
    """卡文 (c)③ + (g)：全部用例把 _CARD_STATES_FILE 重定向到 tmp。

    车道树 backend/data/ 下无 fsrs_card_states.json 且被 .gitignore:8 忽略 ——
    未 patch 的测试会静默生成它而 git 判据看不见（卡文 §〇「live 文件与假绿面」）。
    """
    from app.services import review_service as rs_module

    target = tmp_path / "card_states" / "fsrs_card_states.json"
    monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", target)
    return target


@pytest.fixture
def tmp_vault(tmp_path, monkeypatch):
    """真 vault 目录 + 重定向 CANVAS_BASE_PATH。

    frontmatter_signals._node_md_path() 运行时读 settings.CANVAS_BASE_PATH，
    故 monkeypatch 单例属性即可生效；monkeypatch 负责用例后还原。
    """
    from app.config import settings

    vault = tmp_path / "vault"
    (vault / "节点").mkdir(parents=True)
    monkeypatch.setattr(settings, "CANVAS_BASE_PATH", str(vault))
    return vault


def _seed_node(vault, node_id: str, body: str) -> None:
    (vault / "节点" / f"{node_id}.md").write_text(body, encoding="utf-8")


@pytest.fixture
def svc():
    """ReviewService + mock 依赖（同 tests/unit/conftest.py::review_service_factory）。"""
    from app.services.review_service import ReviewService

    canvas = MagicMock()
    canvas.get_canvas = AsyncMock(return_value={"nodes": [], "edges": []})
    tasks = MagicMock()
    tasks.submit_task = MagicMock(return_value="task_g37")
    service = ReviewService(canvas_service=canvas, task_manager=tasks)
    if service._fsrs_manager is None:
        pytest.skip("FSRS manager 不可用——本文件锁定的是 FSRS 路径的真相源语义")
    return service


def _seed_backend_card(service, concept_id: str) -> datetime:
    """在后端缓存里放一张**真** FSRS 卡，返回它的 due（= 分歧的 Y 侧）。

    禁 mock：卡由生产 FSRSManager 造 + 序列化，与 _card_states 的真实内容同形态。
    """
    card = service._fsrs_manager.create_card()
    service._card_states[concept_id] = service._fsrs_manager.serialize_card(card)
    return service._fsrs_manager.get_due_date(card)


# ══════════════════════════════════════════════════════════════════════════
# 0. 自证封堵：种子必须经生产 reader 读得出
# ══════════════════════════════════════════════════════════════════════════


def test_production_reader_reads_seeded_frontmatter(tmp_vault):
    """卡文 (c)④：先证明预置真的产生了目标形态，再去测消费方。

    这条若红，后面所有"以 frontmatter 为准"的断言都失去意义——它们会因为
    reader 读不出东西而走"无真相源"分支，看起来像被测语义没实现。
    """
    from app.services.review_service import _read_frontmatter_fsrs

    _seed_node(tmp_vault, "g37-reader", _NODE_MD.format(due=_FM_DUE))
    got = _read_frontmatter_fsrs("g37-reader")

    assert got["found"] is True, "生产 reader 没找到种子节点"
    assert got["fsrs_due"] == _FM_DUE, f"生产 reader 取出的 fsrs_due 与种子不符: {got['fsrs_due']!r}"
    assert got["due"] == datetime(2026, 8, 11, 13, 56, 58, tzinfo=timezone.utc)

    # 反向：无该节点时必须如实说没有，而不是造一个默认值
    absent = _read_frontmatter_fsrs("g37-does-not-exist")
    assert absent["found"] is False
    assert absent["due"] is None


# ══════════════════════════════════════════════════════════════════════════
# 1. (c)① 分歧注入 —— 读侧以 frontmatter 为准 + degraded 如实透出
# ══════════════════════════════════════════════════════════════════════════


async def test_get_fsrs_state_frontmatter_wins_on_divergence(svc, tmp_vault):
    """T1 核心：frontmatter due=X、后端缓存 due=Y(≠X) → 返回 X 并标分歧。

    断言的是**字段值**，不是"字段非空"（卡文 (c)① 明令）。
    """
    cid = "g37-diverge"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=_FM_DUE))
    backend_due = _seed_backend_card(svc, cid)

    expected = datetime(2026, 8, 11, 13, 56, 58, tzinfo=timezone.utc)
    assert backend_due != expected, "前提不成立：后端缓存 due 必须与 frontmatter 不同"

    result = await svc.get_fsrs_state(cid)

    assert result["found"] is True
    assert result["due"] == expected, "读侧未以 frontmatter 为准（T1 违规）——返回的是后端缓存的 due"
    assert result["truth_source"] == "frontmatter"
    assert result["degraded_reason"] == "truth_source_divergence"


async def test_get_fsrs_state_agreement_is_not_reported_as_divergence(svc, tmp_vault):
    """禁假降级：两侧一致时不得谎报分歧（degraded 信号必须可证伪）。"""
    cid = "g37-agree"
    backend_due = _seed_backend_card(svc, cid)
    agreed = backend_due.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=agreed))

    result = await svc.get_fsrs_state(cid)

    assert result["truth_source"] == "frontmatter"
    assert result.get("degraded_reason") is None, f"两侧一致却报了分歧: {result.get('degraded_reason')!r}"


async def test_get_fsrs_state_without_truth_source_is_labeled_projection(svc, tmp_vault):
    """无 frontmatter 真相源时禁止谎称 frontmatter —— 如实标 projection-cache。"""
    result = await svc.get_fsrs_state("g37-no-node")

    assert result["found"] is True
    assert result["truth_source"] == "projection-cache"


# ══════════════════════════════════════════════════════════════════════════
# 2. (c)② 门锁边界 —— 有真相源则 GET 不推进状态（配正控）
# ══════════════════════════════════════════════════════════════════════════


async def test_gate_blocks_write_when_truth_source_exists(svc, tmp_vault, isolate_card_states):
    """裁定 ②：有 frontmatter 真相源 → GET 不写盘、不改 _card_states。"""
    cid = "g37-gated"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=_FM_DUE))

    before_mem = dict(svc._card_states)
    assert cid not in before_mem, "前提不成立：门锁用例必须从「缓存无此 concept」起跑"
    assert not isolate_card_states.exists()

    await svc.get_fsrs_state(cid)

    assert svc._card_states == before_mem, "门锁失效：GET 推进了 _card_states（第二真相源仍在独立推进）"
    assert not isolate_card_states.exists(), "门锁失效：GET 写了 fsrs_card_states.json"


async def test_gate_allows_write_when_no_truth_source(svc, isolate_card_states, tmp_vault):
    """**正控**：无真相源时 auto-create 写盘必须照常发生。

    没有这条，上一条的"跑前跑后没变"可能只是因为这条路径本来就写不动
    （fsrs_manager 为 None、提前 return 等），判据会恒真。
    """
    cid = "g37-ungated"

    result = await svc.get_fsrs_state(cid)

    assert result["found"] is True
    assert cid in svc._card_states, "正控失败：无真相源时 auto-create 未写内存"
    assert isolate_card_states.exists(), "正控失败：无真相源时 auto-create 未落盘"
    assert cid in json.loads(isolate_card_states.read_text("utf-8"))
    assert result["persisted"] is True


async def test_gate_blocks_write_on_malformed_fsrs_due(svc, tmp_vault, isolate_card_states):
    """门锁边界（越界输入被拒）：真相源存在但 fsrs_due 读不出时刻。

    此时**不得**放行写盘——真相源存在这一事实已足以禁止第二真相源推进；
    读不出的时刻如实标 truth_source_unparsable，不编造 due。
    """
    cid = "g37-malformed"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due="2026/08/11 13:56"))

    before_mem = dict(svc._card_states)
    result = await svc.get_fsrs_state(cid)

    assert svc._card_states == before_mem, "畸形 fsrs_due 不得放行写盘"
    assert not isolate_card_states.exists()
    assert result["truth_source"] == "frontmatter"
    assert result["degraded_reason"] == "truth_source_unparsable"
    # 禁假成功：读不出真相源的时刻就不给 due，不拿投影值冒充 frontmatter 值
    assert result["due"] is None, "读不出 frontmatter 时刻却给了一个 due（假成功）"


async def test_node_without_fsrs_due_is_treated_as_no_truth_source(svc, tmp_vault):
    """.md 存在但无 fsrs_due = 新卡语义（对齐 daily_review_pick:435「无 fsrs_due 即真新卡」）。

    这属于"真相源说不出话"，门锁放行，但仍如实标 projection-cache。
    """
    cid = "g37-nofield"
    _seed_node(tmp_vault, cid, _NODE_MD_NO_FSRS)

    result = await svc.get_fsrs_state(cid)

    assert result["truth_source"] == "projection-cache"
    assert cid in svc._card_states


# ══════════════════════════════════════════════════════════════════════════
# 3. (c)① 写侧 —— PUT /record 不自称真相源，分歧如实透出且不覆盖计算结果
# ══════════════════════════════════════════════════════════════════════════


def test_record_review_labels_write_as_projection_cache(svc, tmp_vault):
    """裁定 ①：PUT /review/record 的响应必须如实自述"这次写的是投影缓存"。

    断言点在**端点层**而不是 service 层，有两个理由：
      1. service 返回 dict 的键集合被 tests/regression/
         test_debt8_fsrs_fallback_honest.py:185-189 精确锁死（CARD-DEBT-8
         Codex round-1 M3 用它杀「夹带新键」变异），truth_source 不能加在那里；
      2. truth_source 对本端点恒为 "projection-cache"（裁定表 ①：此处只写投影，
         从不写真相源），是常量不是计算结果 —— 端点层才是它的正确归属。
    顺带覆盖 schemas.RecordReviewResponse 的加性字段真的能序列化出去。
    """
    from unittest.mock import AsyncMock, patch

    from app.main import app
    from fastapi.testclient import TestClient
    from tests.support.lifespan import no_lifespan

    with patch(
        "app.api.v1.endpoints.review._get_review_service_singleton",
        AsyncMock(return_value=svc),
    ):
        with no_lifespan(app), TestClient(app) as client:
            resp = client.put(
                "/api/v1/review/record",
                json={
                    "canvas_name": "g37.canvas",
                    "node_id": "g37-rec-plain",
                    "rating": 3,
                },
            )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["card_state_persisted"] is True
    assert data["truth_source"] == "projection-cache"
    assert data["degraded_reason"] is None


async def test_record_review_service_keys_stay_frozen(svc, tmp_vault):
    """CARD-DEBT-8 契约不被本卡破坏：service 返回键集合逐字不变。

    与上一条成对——truth_source 搬去端点层这件事必须有门看着，否则将来有人
    "顺手补回 service 层"就会静默打红 test_debt8_fsrs_fallback_honest。
    """
    result = await svc.record_review_result(canvas_name="g37.canvas", concept_id="g37-rec-keys", rating=3)

    assert sorted(result.keys()) == sorted(
        [
            "canvas_name",
            "concept_id",
            "rating",
            "score",
            "next_review",
            "interval_days",
            "fsrs_state",
            "card_data",
            "details",
            "recorded_at",
            "status",
            "algorithm",
            "card_state_persisted",
            "degraded_reason",
        ]
    ), f"service 返回键集合漂移: {sorted(result.keys())}"
    assert result["card_state_persisted"] is True
    assert result["degraded_reason"] is None


async def test_record_review_flags_divergence_but_keeps_computed_schedule(svc, tmp_vault):
    """裁定 ① 的关键边界：分歧时报信号，但**不**把新算的排期换成 frontmatter 的旧值。

    此刻 frontmatter 里还是旧 due（vault 侧 quiz-answer × fsrs_bridge 的写是
    另一条链、另一时刻）。用它覆盖 = 用 T1 的名义制造错误。
    """
    cid = "g37-rec-diverge"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=_FM_DUE))

    result = await svc.record_review_result(canvas_name="g37.canvas", concept_id=cid, rating=3)

    assert result["degraded_reason"] == "truth_source_divergence"

    # 计算结果必须留着：新排期在未来，绝不是 frontmatter 那个 2026-08-11 旧值
    next_review = datetime.fromisoformat(result["next_review"])
    stale = datetime(2026, 8, 11, 13, 56, 58, tzinfo=timezone.utc)
    assert next_review != stale, "PUT 侧被 frontmatter 旧值覆盖了本次计算结果"
    assert next_review > datetime.now(timezone.utc) - timedelta(days=1)


async def test_record_review_degraded_reasons_are_additive(svc, tmp_vault, monkeypatch):
    """禁假成功：持久化失败与真相源分歧并存时，两个降级原因都要在，谁也不冲掉谁。

    （沿用 record_review_result 既有的逗号拼接先例，见 review_service.py:1102-1111。）
    """
    from pathlib import Path

    from app.services import review_service as rs_module

    cid = "g37-rec-both"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=_FM_DUE))
    monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", Path("/dev/null/card-states.json"))

    result = await svc.record_review_result(canvas_name="g37.canvas", concept_id=cid, rating=3)

    assert result["card_state_persisted"] is False
    reasons = set((result["degraded_reason"] or "").split(","))
    assert "card_state_write_failed" in reasons, f"持久化失败被冲掉了: {reasons}"
    assert "truth_source_divergence" in reasons, f"真相源分歧被冲掉了: {reasons}"
