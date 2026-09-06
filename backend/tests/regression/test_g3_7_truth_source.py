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


async def test_get_fsrs_state_frontmatter_wins_on_divergence(svc, tmp_vault, isolate_card_states):
    """T1 核心：frontmatter due=X、后端缓存 due=Y(≠X) → 返回 X 并标分歧。

    断言的是**字段值**，不是"字段非空"（卡文 (c)① 明令）。
    """
    cid = "g37-diverge"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=_FM_DUE))
    backend_due = _seed_backend_card(svc, cid)

    expected = datetime(2026, 8, 11, 13, 56, 58, tzinfo=timezone.utc)
    assert backend_due != expected, "前提不成立：后端缓存 due 必须与 frontmatter 不同"
    before_cache = svc._card_states[cid]

    result = await svc.get_fsrs_state(cid)

    assert result["found"] is True
    assert result["due"] == expected, "读侧未以 frontmatter 为准（T1 违规）——返回的是后端缓存的 due"
    assert result["truth_source"] == "frontmatter"
    assert result["degraded_reason"] == "truth_source_divergence"
    # Codex r2：缓存命中链此前只锁了 due 与信号，没锁「有没有副作用」——
    # 读一次不得改动投影缓存或落盘。
    assert svc._card_states[cid] == before_cache, "缓存命中的读路径改动了 _card_states"
    assert not isolate_card_states.exists(), "缓存命中的读路径写了 fsrs_card_states.json"


async def test_get_fsrs_state_agreement_is_not_reported_as_divergence(svc, tmp_vault):
    """禁假降级：两侧一致时不得谎报分歧（degraded 信号必须可证伪）。"""
    cid = "g37-agree"
    backend_due = _seed_backend_card(svc, cid)
    # Codex r2：若投影 due 恰好是整秒，删掉生产侧的 due 覆盖后本条仍会通过
    # （两边字面相同）。强制投影带微秒，让「返回的是 frontmatter 那一份」
    # 这个断言真正承重。
    import json as _json

    _card = _json.loads(svc._card_states[cid])
    _card["due"] = backend_due.replace(microsecond=123456).isoformat()
    svc._card_states[cid] = _json.dumps(_card)
    backend_due = backend_due.replace(microsecond=123456)
    assert backend_due.microsecond != 0, "前提不成立：投影 due 必须带微秒"

    agreed = backend_due.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=agreed))

    result = await svc.get_fsrs_state(cid)

    assert result["truth_source"] == "frontmatter"
    assert result.get("degraded_reason") is None, f"两侧一致却报了分歧: {result.get('degraded_reason')!r}"
    # Codex r1 LOW-7：不断言 due 的话，删掉生产侧的 due 覆盖（返回带微秒的投影
    # 值）这条也会通过 —— 一致分支同样要证明返回的是**真相源那一份**。
    assert result["due"] == datetime.strptime(agreed, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc), (
        "一致分支返回的不是 frontmatter 的整秒值（可能是投影侧的带微秒值）"
    )


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

    result = await svc.get_fsrs_state(cid)

    assert svc._card_states == before_mem, "门锁失效：GET 推进了 _card_states（第二真相源仍在独立推进）"
    assert not isolate_card_states.exists(), "门锁失效：GET 写了 fsrs_card_states.json"
    # Codex r1 MEDIUM-6：只断言"没写"的话，删掉生产侧 gate_blocked=True 这条
    # 仍会通过（门照样不写，但 reason 会退回 auto_created_not_persisted =
    # 谎报一次并不存在的写失败）。诚实信号本身必须被锁住。
    assert result["persisted"] is False
    assert result["reason"] == "truth_source_gate_no_projection_write", (
        f"门锁拦下的未持久化被描述成了写失败: {result['reason']!r}"
    )


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


async def test_body_line_is_not_mistaken_for_truth_source(svc, tmp_vault, isolate_card_states):
    """Codex r1 HIGH-2 回归：正文里顶格的 `fsrs_due:` 不得成为调度真相源。

    初版把字段正则作用在**整份 .md** 上（而两个生产 reader 拿到的是已切好的
    frontmatter 块），于是一个讲解「fsrs_due 怎么写」的文档节点会被自己的正文
    示例接管调度。实测复现：返回 due=2020-01-01 且 reason=None（毫无察觉）。

    教训：口径 = 正则 + **输入面**。正则逐字相同不足以证明解析语义相同。
    """
    from app.services.review_service import _read_frontmatter_fsrs

    cid = "g37-body-example"
    _seed_node(
        tmp_vault,
        cid,
        "---\ntype: concept\ntitle: 讲解 fsrs 字段的文档节点\n---\n"
        "# 复习字段怎么写\n\n"
        "在 frontmatter 里这样写：\n\n"
        "fsrs_due: 2020-01-01T00:00:00Z\n",
    )

    fm = _read_frontmatter_fsrs(cid)
    assert fm["found"] is True, "前提不成立：种子节点必须存在"
    assert fm["fsrs_due"] is None, f"正文行被当成了 frontmatter 字段: {fm['fsrs_due']!r}"
    assert fm["governed"] is False, "正文示例不得让该节点被判为「归 frontmatter 管」"
    assert fm["reason"] == "no_fsrs_due"

    # 消费侧：该节点应按新卡处理（门锁放行），而不是被 2020 年那个示例接管
    result = await svc.get_fsrs_state(cid)
    assert result["truth_source"] == "projection-cache"
    assert result["due"] != datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert cid in svc._card_states, "正文示例误判会让门锁把这条本该写的路径拦掉"


async def test_unreadable_node_file_fails_closed(svc, tmp_vault, isolate_card_states):
    """Codex r1 HIGH-1 回归：.md 存在但读不出来 → fail-closed，不得放行投影写。

    初版读取失败后 `return out`，留下 fsrs_due=None，门锁判据 `found and
    fsrs_due` 据此放行 —— 「节点确实有 fsrs_due、只是这一刻文件不可读」会让
    GET 推进投影缓存并落盘，直接推翻「有真相源时一律不推进」。
    附带 bug：reason 还停在初始的 'no_node_file'，谎报文件没找到。
    """
    from app.services.review_service import _read_frontmatter_fsrs

    cid = "g37-unreadable"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=_FM_DUE))
    path = tmp_vault / "节点" / f"{cid}.md"
    path.chmod(0o000)
    try:
        # 前提断言：这台机器上确实读不出来（root 跑测试时 chmod 拦不住）
        try:
            path.read_text(encoding="utf-8")
            pytest.skip("当前用户可无视 chmod 000，无法构造不可读文件")
        except OSError:
            pass

        fm = _read_frontmatter_fsrs(cid)
        assert fm["found"] is True
        assert fm["governed"] is True, "文件不可读时必须 fail-closed（内容未知 ≠ 没话说）"
        assert fm["reason"] == "node_file_unreadable", f"文件明明找到了却谎报: {fm['reason']!r}"

        before_mem = dict(svc._card_states)
        result = await svc.get_fsrs_state(cid)

        assert svc._card_states == before_mem, "不可读时放行了投影写（HIGH-1 复发）"
        assert not isolate_card_states.exists()
        assert result["truth_source"] == "frontmatter"
        assert result["degraded_reason"] == "truth_source_unreadable"
        assert result["due"] is None
    finally:
        path.chmod(0o644)


async def test_unreadable_node_dir_fails_closed(svc, tmp_vault, isolate_card_states):
    """Codex r2 HIGH 回归：**目录**不可读时同样 fail-closed。

    与 test_unreadable_node_file_fails_closed 的区别是缺陷在**更早一层**：
    `frontmatter_signals._node_md_path()` 用 `Path.exists()` 判存在，而
    `Path.exists()` 自己吞掉 OSError 返回 False —— 于是「确实没有这个节点」
    与「目录不可读所以看不见」在它的返回值里完全不可区分，两者都给 None。
    实测（2026-09-06）：`节点/` chmod 000 后 Path.exists() 返 False 不抛异常，
    门锁据此放行 = r1 HIGH-1 的同一缺陷在定位层复发。

    ⚠️ Codex r2 把成因归给 reader 里的 `except OSError` 分支；实测那条分支
    **根本没被触发**。本用例锁的是实测成因（定位返回 None）而非它的归因。
    """
    from app.services.review_service import _read_frontmatter_fsrs

    cid = "g37-dir-blinded"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=_FM_DUE))
    nodes_dir = tmp_vault / "节点"

    # 正控：目录可读时必须判为 governed（否则下面的对照没有意义）
    assert _read_frontmatter_fsrs(cid)["governed"] is True

    nodes_dir.chmod(0o000)
    try:
        try:
            (nodes_dir / f"{cid}.md").read_text(encoding="utf-8")
            pytest.skip("当前用户可无视目录 chmod 000，无法构造不可见目录")
        except OSError:
            pass

        fm = _read_frontmatter_fsrs(cid)
        assert fm["governed"] is True, "定位被蒙蔽时放行了投影写（r2 HIGH 复发）"
        assert fm["reason"] == "node_lookup_unreadable", f"「看不见」被当成「确实没有」: {fm['reason']!r}"

        before_mem = dict(svc._card_states)
        result = await svc.get_fsrs_state(cid)
        assert svc._card_states == before_mem
        assert not isolate_card_states.exists()
        assert result["truth_source"] == "frontmatter"
        assert result["degraded_reason"] == "truth_source_unreadable"
    finally:
        nodes_dir.chmod(0o755)


def test_unencodable_concept_id_is_absent_not_blinded(tmp_vault):
    """编码上不可能对应文件名的 concept_id 必须判「确实没有」，不是「看不见」。

    r2 整改新增的 `os.stat` 探针一度让 lone surrogate 的 UnicodeEncodeError
    （ValueError 子类，**不是** OSError）逃出捕获，冒泡到 record_review_result
    的宽 except，把整条 FSRS 路径降级成 ebbinghaus-fallback —— 实测打红既有
    test_surrogate_key_does_not_poison_subsequent_saves 与
    test_record_review_unicode_write_failure_stays_fsrs_and_honest。

    语义裁定：这类 id 在编码上就存不出文件名，所以「没有」是正确结论；
    判成「看不见」会让门锁永久拦死它们。同族问题见 CARD-D3 Codex HIGH-3。
    """
    from app.services.review_service import _node_lookup_is_blinded, _read_frontmatter_fsrs

    cid = "g37-\ud800-surrogate"  # lone surrogate，UTF-8 编不出来

    assert _node_lookup_is_blinded(cid) is False, "编码不可能的 id 被判成了「看不见」"

    fm = _read_frontmatter_fsrs(cid)  # 必须不抛异常
    assert fm["found"] is False
    assert fm["governed"] is False, "编码不可能的 id 触发了门锁 fail-closed"
    assert fm["reason"] == "no_node_file"


def test_missing_node_is_still_reported_as_absent(tmp_vault):
    """**正控**：目录可读时「确实没有这个节点」必须仍判 governed=False。

    没有这条，上一条的 fail-closed 可能是把**所有**查不到都判成了「看不见」，
    那样门锁会永久拦死一切新卡 —— 比原缺陷更糟。
    """
    from app.services.review_service import _read_frontmatter_fsrs

    fm = _read_frontmatter_fsrs("g37-truly-absent")

    assert fm["found"] is False
    assert fm["governed"] is False, "可读目录下的「真没有」被误判成「看不见」"
    assert fm["reason"] == "no_node_file"


async def test_node_without_fsrs_due_is_treated_as_no_truth_source(svc, tmp_vault):
    """.md 存在但无 fsrs_due = 新卡语义（对齐 daily_review_pick:435「无 fsrs_due 即真新卡」）。

    这属于"真相源说不出话"，门锁放行，但仍如实标 projection-cache。
    """
    cid = "g37-nofield"
    _seed_node(tmp_vault, cid, _NODE_MD_NO_FSRS)

    result = await svc.get_fsrs_state(cid)

    assert result["truth_source"] == "projection-cache"
    assert cid in svc._card_states


def _get_fsrs_state_over_http(svc, concept_id: str):
    """经真 HTTP 端点取 FSRS 状态（锁 review.py 的字段转发）。"""
    from unittest.mock import AsyncMock, patch

    from app.main import app
    from fastapi.testclient import TestClient
    from tests.support.lifespan import no_lifespan

    with patch(
        "app.api.v1.endpoints.review._get_review_service_singleton",
        AsyncMock(return_value=svc),
    ):
        with no_lifespan(app), TestClient(app) as client:
            return client.get(f"/api/v1/review/fsrs-state/{concept_id}")


def test_http_get_forwards_truth_source_and_degraded(svc, tmp_vault):
    """Codex r1 MEDIUM-6：GET 侧此前只有直调 service 的用例。

    删掉 review.py 里 truth_source / degraded_reason 两个转发字段，原有那些
    用例照样全绿 —— 端点层的诚实信号完全没有门看着。本条走真 HTTP 栈，同时
    覆盖 schemas.FSRSStateQueryResponse 的两个加性字段能序列化出去。
    """
    cid = "g37-http-diverge"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=_FM_DUE))
    # 故意**不**播后端卡：走 auto-create 分支，这样一条用例同时覆盖
    # 门锁拦截（persisted/reason）与真相源分歧（due/degraded_reason）。
    # 缓存命中分支不推进状态，门锁本就不参与，见 test_gate_* 的分工。
    assert cid not in svc._card_states

    resp = _get_fsrs_state_over_http(svc, cid)

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["found"] is True
    assert data["truth_source"] == "frontmatter", "端点未转发 truth_source"
    assert data["degraded_reason"] == "truth_source_divergence", "端点未转发 degraded_reason"
    assert data["persisted"] is False
    assert data["reason"] == "truth_source_gate_no_projection_write"
    assert data["fsrs_state"]["due"].startswith("2026-08-11T13:56:58"), (
        f"HTTP 层返回的 due 不是 frontmatter 那一份: {data['fsrs_state']['due']!r}"
    )
    assert cid not in svc._card_states, "HTTP 路径上门锁失效"


def test_http_get_without_truth_source_reports_projection(svc, tmp_vault):
    """端点侧的**正控**：无真相源时必须如实标 projection-cache 且不报降级。

    没有这条，上一条的 'frontmatter' 可能只是端点把某个常量写死了。
    """
    resp = _get_fsrs_state_over_http(svc, "g37-http-plain")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["truth_source"] == "projection-cache"
    assert data["degraded_reason"] is None


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
    # Codex r1 LOW-7：只做集合包含检查排除不掉「多报原因 / 重复原因」。
    # 锁成**恰好等于**这两项（顺序也锁，逗号拼接是有序的）。
    assert result["degraded_reason"] == "card_state_write_failed,truth_source_divergence", (
        f"降级原因不是恰好这两项（可能多报或重复）: {result['degraded_reason']!r}"
    )


async def test_record_review_reports_unparsable_truth_source(svc, tmp_vault):
    """Codex r1 MEDIUM-4 回归：非法但非空的 fsrs_due 在 PUT 侧不得静默。

    初版只在 `fm_truth["due"] is not None and due_date is not None` 时比较，
    于是「真相源存在但形态不合规」拿到 degraded_reason=None —— 异常信号被整条
    吞掉，调用方看到的是一次干干净净的成功。
    """
    cid = "g37-rec-malformed"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due="2026/08/11 13:56"))

    result = await svc.record_review_result(canvas_name="g37.canvas", concept_id=cid, rating=3)

    assert result["card_state_persisted"] is True, "投影缓存本身确实写成功了"
    assert result["degraded_reason"] == "truth_source_unparsable", (
        f"形态不合规的真相源被静默: {result['degraded_reason']!r}"
    )


async def test_record_review_reports_unreadable_truth_source(svc, tmp_vault):
    """Codex r1 HIGH-1 的 PUT 侧对应面：文件不可读同样要出声。"""
    cid = "g37-rec-unreadable"
    _seed_node(tmp_vault, cid, _NODE_MD.format(due=_FM_DUE))
    path = tmp_vault / "节点" / f"{cid}.md"
    path.chmod(0o000)
    try:
        try:
            path.read_text(encoding="utf-8")
            pytest.skip("当前用户可无视 chmod 000，无法构造不可读文件")
        except OSError:
            pass

        result = await svc.record_review_result(canvas_name="g37.canvas", concept_id=cid, rating=3)

        assert result["degraded_reason"] == "truth_source_unreadable", (
            f"不可读的真相源被静默: {result['degraded_reason']!r}"
        )
    finally:
        path.chmod(0o644)
