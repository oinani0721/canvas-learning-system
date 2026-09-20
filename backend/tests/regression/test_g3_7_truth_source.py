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
  ③ mastery grade / ④ 已退役的公共单卡保存入口 → 隔离（仅注释，无行为改动，不在本文件覆盖）。

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
    # CARD-G3-5: 落盘按 vault 分桶 ⇒ 顶层是 vault_id, cid 在二层。本正控原意
    # (无真相源时门放行、确实落了盘) 一字不减。
    #
    # ⚠️ Codex r1 MEDIUM-2 整改: 绑**正确身份 (vault, concept)** 而不是"某处
    # 出现过 cid"。旧写法 `any(cid in bucket for ...)` 有两个弱点: 落进错误
    # vault 也通过; bucket 若是字符串, `in` 会退化成子串匹配而恒真。这里向 svc
    # 问它当前解析到的 vault, 定点查那个桶, 且显式断言桶是 dict。
    on_disk = json.loads(isolate_card_states.read_text("utf-8"))
    current_vault = svc._dirty_key(cid)[0]
    assert current_vault is not None, "作用域应能解析出来, 否则 auto-create 不会落盘"
    assert isinstance(on_disk.get(current_vault), dict), f"落盘顶层应是 vault 桶 (dict), 实得 {on_disk!r}"
    assert cid in on_disk[current_vault], f"正控失败：无真相源时 auto-create 未进**本 vault** 的桶: {on_disk!r}"
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


# ══════════════════════════════════════════════════════════════════════════
# 4. CARD-CARD-STATES-ATOMIC-WRITE —— concept-identity Scenario 回归门
#    [BATCH-2026-09-18-第十五批 / CARD-CARD-STATES-ATOMIC-WRITE]
#
# `openspec/specs/concept-identity/spec.md` 的 Requirement「FSRS Card State
# Projection Snapshot Persistence」自 T4-C 归档以来**一条自动化断言都没有**
# (`git grep concept-identity -- backend/tests` = 0)，于是 spec 与实现各走各
# 的：spec 承诺「原子写」，实现是 `write_text → Path.replace`——无 fsync、无
# finally、无 tmp 清理。本段把 6 个 Scenario 逐条落成断言（S6 为本卡新增）。
#
# ⚠️ 本段任何用例都**不得**调用 `monkeypatch.undo()`：那会把 module 级
# autouse fixture `isolate_card_states` 的 `_CARD_STATES_FILE` 重定向一起撤
# 掉，后续写入会落到车道树 `backend/data/`（零写门破）。探针一律留到用例
# teardown 由 monkeypatch 自己还原。
# ══════════════════════════════════════════════════════════════════════════

from contextlib import contextmanager  # 段内 `_vault_scope` 所需；放段首而非
# 文件头，是为了让本卡的 diff 严格落在文件尾部，不动既有 21 个 test 与
# :74-85 的 autouse fixture。


@contextmanager
def _vault_scope(vault_id: str):
    """把 per-request 作用域切到 `vault_id`，退出时还原。

    逐行复制自 `tests/regression/test_g3_5_vault_keyed_card_states.py:36-54`
    ——跨测试模块 import 会让两份回归门互相绑死，复制这 12 行更便宜。
    与生产注入点同源：`review.py::_resolve_vault_group_id` 末行调的就是
    `set_current_subject_id(<D16 group_id>)`。
    """
    from app.core.subject_config import (
        build_vault_group_id,
        get_current_subject_id,
        set_current_subject_id,
    )

    prev = get_current_subject_id()
    set_current_subject_id(build_vault_group_id(vault_id))
    try:
        yield
    finally:
        set_current_subject_id(prev)


def _spy_open(monkeypatch) -> list:
    """记录每一次 open 的 `(path, mode)` —— **两个绑定都要包**。

    `Path.write_text` / `Path.open` 走的是 `io.open`（CPython 3.14 pathlib
    实现），而 helper 里的裸 `open(...)` 走 `builtins.open`。两者指向同一个
    函数对象，却是**两个独立的模块属性**：只包 `builtins.open`，旧实现那次
    `write_text` 一次都抓不到，于是「目标从未以写模式打开」这条断言会绿在一
    个瞎掉的探针上（假绿）。探针存活由 S1 里的 `.json.tmp` 正控锚自证。
    """
    import builtins
    import io
    import os as _os

    calls: list = []

    def _wrap(real):
        def _spy(file, mode="r", *args, **kwargs):
            try:
                recorded = str(_os.fspath(file))
            except TypeError:  # 文件描述符等非路径对象
                recorded = repr(file)
            calls.append((recorded, mode))
            return real(file, mode, *args, **kwargs)

        return _spy

    monkeypatch.setattr(builtins, "open", _wrap(builtins.open))
    monkeypatch.setattr(io, "open", _wrap(io.open))
    return calls


def _write_modes(calls: list, path) -> list:
    """`calls` 里对 `path` 的写模式 open（`w`/`a`/`+`/`x` 任一字符即算）。"""
    target = str(path)
    return [(p, m) for p, m in calls if p == target and any(c in m for c in ("w", "a", "+", "x"))]


async def test_concept_identity_s1_snapshot_published_by_atomic_replace(svc, isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: Snapshot is published by atomic replace, never by writing the destination
    """
    from app.services.review_service import _card_states_payload

    target = isolate_card_states
    tmp = target.with_suffix(".json.tmp")
    cid = "g37-s1-atomic"

    calls = _spy_open(monkeypatch)
    with _vault_scope("vault_s1"):
        persisted = await svc._save_card_states(pending=(cid, "card-s1"))
        expected = _card_states_payload(svc._card_states)

    assert persisted is True, "可序列化的快照必须落盘成功"
    assert _write_modes(calls, target) == [], (
        f"`_CARD_STATES_FILE` 不得被以写模式打开（快照只能由 os.replace 发布），实得 {_write_modes(calls, target)!r}"
    )
    assert _write_modes(calls, tmp), (
        "探针存活锚：本次落盘必须经由 `.json.tmp` 的写模式 open 发生——一次都没抓到说明 "
        f"open 探针瞎了（而不是目标没被写），实得末 5 条 {calls[-5:]!r}"
    )
    assert json.loads(target.read_text(encoding="utf-8")) == expected, (
        "落盘文档必须是 `_card_states_payload()` 的嵌套全量快照，不是部分/增量更新"
    )
    assert not tmp.exists(), f"成功路径上 `.json.tmp` 不得残留，实得 {tmp}"


async def test_concept_identity_s2_unresolvable_scope_fails_closed_without_fs_write(
    svc, isolate_card_states, monkeypatch
):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: Unresolvable vault scope fails closed without any filesystem write
    """
    from app.core import subject_config

    target = isolate_card_states
    cid = "g37-s2-failclosed"

    def _broken_derivation():
        raise RuntimeError("probe: active vault derivation broken")

    # 打断解析链两级（同 test_g3_5:180-182）：ContextVar 落到 DEFAULT，
    # active vault 推导抛错 ⇒ require_read_group(None) 抛 VaultScopeUnresolved。
    monkeypatch.setattr(subject_config, "get_current_subject_id", lambda: subject_config.DEFAULT_SUBJECT_ID)
    monkeypatch.setattr(subject_config, "default_vault_group_id", _broken_derivation)

    persisted = await svc._save_card_states(pending=(cid, "card-s2"))

    assert persisted is False, "作用域解析不出来时必须 fail-closed 返回 False"
    assert svc._dirty_key(cid) in svc._unpersisted_concepts, "fail-closed 仍要把 concept 记成未落盘"
    assert not target.parent.exists(), (
        "fail-closed 必须在 `try:` 之前返回——连父目录 mkdir 都不该跑；"
        f"实得 {target.parent} 已存在（= 走进了 try 块，spec 的「no filesystem call」被违反）"
    )
    assert not target.exists() and not target.with_suffix(".json.tmp").exists()


async def test_concept_identity_s3_encoding_failure_rolls_back_and_creates_no_tmp(
    svc, isolate_card_states, monkeypatch
):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: Serialization failure is normalized to False and the mutation is rolled back

    本卡新增的「`.json.tmp` 不存在」是先红项：旧实现 `Path.write_text` 先
    `open('w')` 建/截断 tmp 再编码，lone surrogate 的 `UnicodeEncodeError`
    因此在 tmp 已经存在之后才抛，留下一个 0 长度残留。
    """
    target = isolate_card_states
    tmp = target.with_suffix(".json.tmp")
    cid = "g37-s3-\ud800"

    calls = _spy_open(monkeypatch)
    with _vault_scope("vault_s3"):
        persisted = await svc._save_card_states(pending=(cid, "card-s3"))

        assert persisted is False, "UnicodeEncodeError（ValueError 族）必须归一为 False，不得冒泡"
        assert cid not in svc._card_states, "先前无值 ⇒ 回滚必须把 key 整个 pop 掉"
        assert svc._dirty_key(cid) in svc._unpersisted_concepts

    # Codex r1 MEDIUM：只断言「调用后不存在」分不清「从没建过」与「建了又被清掉」。
    assert _write_modes(calls, tmp) == [], (
        f"`.json.tmp` **从未被以写模式打开过**：编码必须发生在打开任何文件之前，实得 {_write_modes(calls, tmp)!r}"
    )
    size = tmp.stat().st_size if tmp.exists() else "n/a"
    assert not tmp.exists(), (
        f"`.json.tmp` 不存在：编码必须发生在打开任何文件之前（先编码再开文件），实得残留 {tmp}（size={size}）"
    )


async def test_concept_identity_s3_rollback_restores_previous_value(svc, isolate_card_states):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: Serialization failure is normalized to False and the mutation is rolled back
    （回滚的另一半：先前**有**值 ⇒ 恢复旧值，而不是 pop。）
    """
    cid = "g37-s3b-\ud800"

    with _vault_scope("vault_s3b"):
        svc._card_states[cid] = "card-old"

        persisted = await svc._save_card_states(pending=(cid, "card-new"))

        assert persisted is False
        assert svc._card_states[cid] == "card-old", (
            "先前有值 ⇒ 回滚必须恢复旧值（pop 掉等于替这次失败的写额外删了一条既有记录）"
        )
        assert svc._dirty_key(cid) in svc._unpersisted_concepts


async def test_concept_identity_s4_successful_snapshot_clears_every_dirty_marker(svc, isolate_card_states):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A successful snapshot clears every dirty marker without restoring lost values
    """
    target = isolate_card_states
    poisoned = "g37-s4-\ud800"
    clean = "g37-s4-clean"

    with _vault_scope("vault_s4"):
        assert await svc._save_card_states(pending=(poisoned, "card-poison")) is False
        assert svc._unpersisted_concepts, "前置：序列化失败必须先留下脏标记，否则下面这条断言恒绿"

        assert await svc._save_card_states(pending=(clean, "card-clean")) is True
        assert svc._unpersisted_concepts == set(), "成功的全量快照 clear 全部脏标记（含更早那条）"

    snapshot = json.loads(target.read_text(encoding="utf-8"))
    assert snapshot == {"vault_s4": {clean: "card-clean"}}, (
        f"被回滚出内存的值不得因为「脏标记被清掉」而回到快照里（清标记不是治愈数据），实得 {snapshot!r}"
    )
    assert not target.with_suffix(".json.tmp").exists()


async def test_concept_identity_s5_dirty_marker_is_vault_scoped(svc, isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A dirty marker in one vault does not make a same-named concept in another look unpersisted
    """
    import os as _os

    cid = "c"
    # spec 里的 vault「A」/「B」在这里写成小写：`build_vault_group_id()` 会过
    # `sanitize_subject_name()`，后者 **lower()**（subject_config.py:152），
    # 于是 "A" 落桶其实叫 "a"。硬写 ("A", cid) 断言的是一个永远不存在的键。
    vault_a, vault_b = "a", "b"

    def _refuse(src, dst, **kwargs):
        raise OSError("probe: replace refused for vault a")

    monkeypatch.setattr(_os, "replace", _refuse)

    with _vault_scope(vault_a):
        persisted = await svc._save_card_states(pending=(cid, "card-a"))
        assert persisted is False
        assert (vault_a, cid) in svc._unpersisted_concepts, "脏标记身份必须是 (vault_id, concept_id) 对"
        assert svc._is_unpersisted(cid) is True

    with _vault_scope(vault_b):
        # ⛔ 这里**不做成功保存**：成功快照会 clear 掉 vault a 的脏标记，把下面
        # 两条断言变成恒绿（判据被自己的前置动作掏空）。
        assert svc._dirty_key(cid) == (vault_b, cid)
        assert svc._is_unpersisted(cid) is False, (
            "跨 vault 误报：vault b 的同名 concept 不得因 vault a 的写失败被报成 persisted=False"
        )

    with _vault_scope(vault_a):
        assert svc._is_unpersisted(cid) is True, "vault a 自己的脏标记必须还在"


async def test_concept_identity_s6_failure_after_tmp_leaves_no_residue(svc, isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A failure after the temp file exists leaves no residue and keeps the destination unchanged
    （本卡新增；先红项 = 「`.json.tmp` 不存在」。）
    """
    import os as _os

    target = isolate_card_states
    tmp = target.with_suffix(".json.tmp")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"vault_s6": {"c": "old"}}, ensure_ascii=False, indent=2), encoding="utf-8")
    old_bytes = target.read_bytes()

    def _refuse(src, dst, **kwargs):
        raise OSError("probe: replace refused after the temp file exists")

    monkeypatch.setattr(_os, "replace", _refuse)

    with _vault_scope("vault_s6"):
        persisted = await svc._save_card_states(pending=("c", "card-new"))

        assert persisted is False, "OSError 必须归一为 False，不得冒泡"
        assert svc._dirty_key("c") in svc._unpersisted_concepts

    assert target.read_bytes() == old_bytes, (
        "replace 失败 ⇒ 目标必须逐字节保持旧快照（这条排除「目标被就地截断/半写」）"
    )
    assert not tmp.exists(), (
        f"`.json.tmp` 不存在：临时文件已经建出来之后的任何失败都必须由 finally 清掉，实得残留 {tmp}"
    )


async def test_concept_identity_s6_fsync_precedes_replace(svc, isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A failure after the temp file exists leaves no residue and keeps the destination unchanged
    （同一 Scenario 的持久顺序半边；本卡新增，先红项 = 「fsync 调用序列非空」。）
    """
    import os as _os

    target = isolate_card_states
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")

    ops: list = []
    sizes: list = []
    real_fsync = _os.fsync

    def _rec_fsync(fd):
        ops.append(("fsync", fd))
        sizes.append(_os.fstat(fd).st_size)  # Codex r2 MEDIUM：钉「flush 先于 fsync」
        return real_fsync(fd)

    def _rec_replace(src, dst, **kwargs):
        ops.append(("replace", str(src)))
        raise OSError("probe: replace refused")

    monkeypatch.setattr(_os, "fsync", _rec_fsync)
    monkeypatch.setattr(_os, "replace", _rec_replace)

    with _vault_scope("vault_s6b"):
        persisted = await svc._save_card_states(pending=("c6b", "card-6b"))

    assert persisted is False
    kinds = [op for op, _ in ops]
    assert "fsync" in kinds, (
        f"fsync 调用序列非空：发布前必须至少发生一次 os.fsync，实得调用序列 {ops!r}——"
        "无 fsync 时 rename 的元数据可先于数据落盘，掉电会留下一份 0 长度快照"
    )
    assert "replace" in kinds, "探针存活锚：本次必须真的走到 os.replace（否则上一条恒绿）"
    assert kinds.index("fsync") < kinds.index("replace"), f"os.fsync 必须发生在 os.replace **之前**，实得顺序 {kinds!r}"
    # Codex r2 MEDIUM：只断言「fsync 发生过」挡不住「删掉 fh.flush()」——缓冲数据会在
    # 退出 with 时才写出，内容断言照样过，但这次 fsync 同步的是一个空文件。
    from app.services.review_service import _card_states_payload

    expected = json.dumps(_card_states_payload(svc._card_states), ensure_ascii=False, indent=2).encode("utf-8")
    assert sizes[0] == len(expected), (
        f"fsync 发生时 `.json.tmp` 必须已经是完整 {len(expected)} 字节（flush 必须先于 fsync），"
        f"实得 {sizes[0]} 字节——为 0 说明数据还在用户态缓冲里"
    )


async def test_concept_identity_s6_write_phase_failure_leaves_no_residue(svc, isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A failure after the temp file exists leaves no residue and keeps the destination unchanged
    （写阶段那一半。）

    Codex r1 MEDIUM：另外两条 S6 都只让 `os.replace` 失败 ⇒ 一个把 try/finally
    缩到只包住 replace 及其后续步骤的负控输入仍能让 8 条全绿。本条让**文件
    fsync** 失败，把 finally 的覆盖范围钉到写阶段。
    """
    import os as _os

    target = isolate_card_states
    tmp = target.with_suffix(".json.tmp")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'{"kept": 1}')
    old_bytes = target.read_bytes()

    def _refuse_fsync(fd):
        raise OSError("probe: fsync refused during the write phase")

    monkeypatch.setattr(_os, "fsync", _refuse_fsync)

    with _vault_scope("vault_s6d"):
        persisted = await svc._save_card_states(pending=("c6d", "card-6d"))
        assert persisted is False
        assert svc._dirty_key("c6d") in svc._unpersisted_concepts

    assert target.read_bytes() == old_bytes, "写阶段失败 ⇒ 目标原封不动（replace 根本没跑到）"
    assert not tmp.exists(), (
        f"`.json.tmp` 不存在：finally 必须覆盖写阶段（open/write/flush/fsync），不只是 replace 之后；实得残留 {tmp}"
    )


async def test_concept_identity_s6_directory_fsync_failure_is_reported_not_swallowed(
    svc, isolate_card_states, monkeypatch
):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A failure after the temp file exists leaves no residue and keeps the destination unchanged
    （目录 fsync 那一半 —— 本卡的保守诚实口径。）

    目标其实**已经**被 replace 落位，但目录项还没落盘 ⇒ 返回 False + 保留脏标记。
    这条同时是「spec 那句『replace 成功即清全部脏标记』在本卡之后不再逐字成立」
    的可观测证据（该段在卡文硬约束下一字不动，已登记）。
    """
    import os as _os
    import stat

    target = isolate_card_states
    tmp = target.with_suffix(".json.tmp")
    target.parent.mkdir(parents=True, exist_ok=True)
    real_fsync = _os.fsync
    seen = []
    dir_ino = _os.stat(target.parent).st_ino

    def _fail_only_directory_fsync(fd):
        # Codex r2 MEDIUM：按 fd **指向的对象**判定，不按「第几次调用」。绑调用
        # 序号时，把 os.open(target.parent) 改成 os.open(target) 的变异体仍能全绿
        # （父目录从未 fsync），而实现若多一次文件 fsync 又会误红。
        st = _os.fstat(fd)
        is_dir = stat.S_ISDIR(st.st_mode)
        seen.append(("dir" if is_dir else "file", st.st_ino))
        if not is_dir:
            return real_fsync(fd)
        raise OSError("probe: directory fsync refused")

    monkeypatch.setattr(_os, "fsync", _fail_only_directory_fsync)

    with _vault_scope("vault_s6e"):
        persisted = await svc._save_card_states(pending=("c6e", "card-6e"))
        assert persisted is False, "目录 fsync 失败 ⇒ 保守诚实报未持久"
        assert svc._dirty_key("c6e") in svc._unpersisted_concepts
        assert svc._unpersisted_concepts, "clear() 没有跑到 —— 这正是那句 spec 的失真点"

    assert ("dir", dir_ino) in seen, f"探针存活锚：必须真的对**父目录本身**（inode {dir_ino}）fsync 过，实得 {seen!r}"
    assert seen and seen[0][0] == "file", f"文件 fsync 必须先于目录 fsync，实得 {seen!r}"
    assert json.loads(target.read_text(encoding="utf-8")) == {"vault_s6e": {"c6e": "card-6e"}}, (
        "如实面：replace 已经成功，目标**确实**是新快照，尽管返回 False"
    )
    assert not tmp.exists(), "目录 fsync 失败同样要清掉 tmp"


class _WriteRefusingFile:
    """真文件对象的**薄代理**：只让 `write` 抛 OSError，其余全部转发。

    DD-03 口径：这是在 I/O 边界上对**真**文件对象做失败注入（与包装 `os.replace`
    / `os.fsync` 同类），不是 mock `ReviewService` 的内部方法。
    """

    def __init__(self, fh):
        self._fh = fh

    def write(self, *args, **kwargs):
        raise OSError("probe: write refused")

    def __getattr__(self, name):
        return getattr(self._fh, name)

    def __enter__(self):
        self._fh.__enter__()
        return self

    def __exit__(self, *exc):
        return self._fh.__exit__(*exc)


async def test_concept_identity_s6_write_failure_leaves_no_residue(svc, isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A failure after the temp file exists leaves no residue and keeps the destination unchanged
    （`write` 本身失败的那一半。）

    Codex r2 MEDIUM：只让「文件 fsync」失败，挡不住「把 open/write/flush 挪到清理
    `try` 之外、只从 fsync 开始覆盖」的变异体。本条让 **`write` 自己**失败——此时
    tmp 已经被 open 建出来，清理若不覆盖 open/write 段就会留残留。
    """
    import builtins
    import io

    target = isolate_card_states
    tmp = target.with_suffix(".json.tmp")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'{"kept": 1}')
    old_bytes = target.read_bytes()
    real_builtins_open = builtins.open
    real_io_open = io.open

    def _wrap(real):
        def _opener(file, mode="r", *args, **kwargs):
            fh = real(file, mode, *args, **kwargs)
            if str(file) == str(tmp) and any(c in mode for c in ("w", "a", "+", "x")):
                return _WriteRefusingFile(fh)
            return fh

        return _opener

    monkeypatch.setattr(builtins, "open", _wrap(real_builtins_open))
    monkeypatch.setattr(io, "open", _wrap(real_io_open))

    with _vault_scope("vault_s6f"):
        persisted = await svc._save_card_states(pending=("c6f", "card-6f"))
        assert persisted is False, "write 失败（OSError）必须归一为 False"
        assert svc._dirty_key("c6f") in svc._unpersisted_concepts

    assert target.read_bytes() == old_bytes, "write 失败 ⇒ 目标原封不动"
    assert not tmp.exists(), f"`.json.tmp` 不存在：清理必须覆盖 open/write 段，不只是 fsync 之后；实得残留 {tmp}"


def test_concept_identity_s6_persist_is_serialized_across_threads(isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: The publish sequence is serialized within the process

    Codex r2 HIGH 回归门。`asyncio.Lock` 在协程被取消时**会释放**，而
    `asyncio.to_thread` 派出去的线程**取消不掉**（实测存档
    `_bmad-output/审查/evidence-card-states-atomic/probe-cancel-thread-*.txt`）
    ⇒ 两条线程能同时落在同一个确定性 `.json.tmp` 路径上：后来者的
    `open(tmp,"wb")` 会 **truncate 先到者正在用的同一个 inode**。
    `_card_states_file_lock` 让整段真正串行。

    ⚠️ 观测点取**锁本身**而不是「tmp 被打开」（Codex r4 MEDIUM 整改）：加了过期写
    丢弃之后，一次**合法**的丢弃会在锁内直接 return、根本不开文件，于是「四条线程
    都必须打开过 tmp」不再是不变量，那个存活锚自带 flaky。进出锁则是每次调用都发生
    的，`entered == 4` 因此是确定性的；重叠检测直接测的就是互斥本身。
    """
    import os as _os
    import threading
    import time

    from app.services import review_service as _rs

    target = isolate_card_states
    tmp = target.with_suffix(".json.tmp")
    target.parent.mkdir(parents=True, exist_ok=True)

    real_replace = _os.replace
    real_lock = _rs._card_states_file_lock
    guard = threading.Lock()
    held: list = []
    entered: list = []
    overlaps: list = []
    errors: list = []

    class _TrackingLock:
        """包一层真锁，只记录持有区间，不改变互斥语义。"""

        def __enter__(self):
            real_lock.__enter__()
            me = threading.current_thread().name
            with guard:
                entered.append(me)
                if held:
                    overlaps.append((me, tuple(held)))
                held.append(me)
            return self

        def __exit__(self, *exc):
            me = threading.current_thread().name
            with guard:
                if me in held:
                    held.remove(me)
            return real_lock.__exit__(*exc)

    def _slow_replace(src, dst, **kwargs):
        time.sleep(0.05)  # 撑开窗口：不串行的话必然重叠
        return real_replace(src, dst)

    monkeypatch.setattr(_rs, "_card_states_file_lock", _TrackingLock())
    monkeypatch.setattr(_os, "replace", _slow_replace)

    def _run(tag: str) -> None:
        try:
            _rs._persist_card_states_bytes(target, ('{"%s": 1}' % tag).encode("utf-8"), next(_rs._card_states_seq))
        except Exception as exc:  # noqa: BLE001 —— 任何线程异常都要让本门变红
            errors.append((tag, repr(exc)))

    threads = [threading.Thread(target=_run, args=(f"t{i}",), name=f"t{i}") for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not [t for t in threads if t.is_alive()], "线程未在 30s 内收敛（可能死锁）"
    assert errors == [], f"串行落盘不得抛异常，实得 {errors!r}"
    assert len(entered) == 4, f"探针存活锚：四条线程都必须真的进过临界区（无论是否因过期被丢弃），实得 {entered!r}"
    assert held == [], f"收工时不得还有人持锁，实得 {held!r}"
    assert overlaps == [], f"落盘整段必须在进程内串行：实测有 {len(overlaps)} 次临界区重叠 {overlaps!r}"
    assert not tmp.exists(), "串行跑完不得留 tmp"
    final_doc = json.loads(target.read_text(encoding="utf-8"))
    assert list(final_doc.keys()) in ([["t0"], ["t1"], ["t2"], ["t3"]]), (
        f"目标必须**恰好**是某一次完整的快照（单键），不是空文档、也不是交错写出的混合物，实得 {final_doc!r}"
    )


def test_concept_identity_s6_stale_publish_is_discarded(isolate_card_states):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A stale snapshot never overwrites a newer one that already landed

    Codex r3 HIGH 回归门。**互斥不等于顺序**：线程锁保证两条落盘线程不重叠，
    但不保证谁先。协程被取消后它那条线程仍会跑完，手里的 payload 序列化于较早
    时刻，却可能**晚于**一份更新的快照落盘——而更新的那次已经 `clear()` 掉脏
    标记，于是这次回退是**静默丢更新**。
    """
    from app.services import review_service as _rs

    target = isolate_card_states
    tmp = target.with_suffix(".json.tmp")
    target.parent.mkdir(parents=True, exist_ok=True)

    old_seq = next(_rs._card_states_seq)
    new_seq = next(_rs._card_states_seq)
    assert old_seq < new_seq, "前提：序号必须单调递增"

    _rs._persist_card_states_bytes(target, b'{"new": 1}', new_seq)
    assert json.loads(target.read_text(encoding="utf-8")) == {"new": 1}

    _rs._persist_card_states_bytes(target, b'{"old": 1}', old_seq)  # 过期写
    assert json.loads(target.read_text(encoding="utf-8")) == {"new": 1}, (
        "过期快照不得覆盖已落盘的更新快照（静默丢更新）"
    )
    assert not tmp.exists(), "被丢弃的过期写不得留下 tmp"

    # 探针存活锚：更新的序号必须真的落盘，否则上面那条会绿在「什么都不写」上。
    newer_seq = next(_rs._card_states_seq)
    _rs._persist_card_states_bytes(target, b'{"newer": 1}', newer_seq)
    assert json.loads(target.read_text(encoding="utf-8")) == {"newer": 1}, "探针存活锚：序号更大的快照必须真的落盘"


async def test_concept_identity_s6_cleanup_failure_is_normalized_not_swallowed(svc, isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A failure after the temp file exists leaves no residue and keeps the destination unchanged
    （清理**自身**失败的那一半。）

    Codex r3 MEDIUM：`finally` 里的 `unlink` 本身也是 I/O，它失败时
    `missing_ok=True` 吞不掉（那只吞 `FileNotFoundError`）。spec 写明这种失败按
    `OSError` 归一而不是被静默忽略——本门把那句话钉住。
    """
    import pathlib

    target = isolate_card_states
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".json.tmp")
    real_unlink = pathlib.Path.unlink

    def _refuse_unlink(self, *args, **kwargs):
        if str(self) == str(tmp):
            raise OSError("probe: unlink refused")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "unlink", _refuse_unlink)

    with _vault_scope("vault_s6g"):
        persisted = await svc._save_card_states(pending=("c6g", "card-6g"))
        assert persisted is False, "清理自身失败必须归一为 False，不得静默当成功"
        assert svc._dirty_key("c6g") in svc._unpersisted_concepts

    # 如实面：replace 其实已经成功，目标**确实**是新快照——报 False 是保守诚实。
    assert json.loads(target.read_text(encoding="utf-8")) == {"vault_s6g": {"c6g": "card-6g"}}


def test_concept_identity_s7_failed_publish_does_not_advance_the_watermark(isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A stale snapshot never overwrites a newer one that already landed
    （水位只在 `os.replace` **成功之后**推进。）

    Codex r4 MEDIUM：把 published 记账挪到 `os.replace` **之前**，一次失败的高序号
    发布就会把水位顶上去，后面那些序号更小、却从未发布过的快照会被全部误丢。
    """
    import os as _os

    from app.services import review_service as _rs

    target = isolate_card_states
    target.parent.mkdir(parents=True, exist_ok=True)
    real_replace = _os.replace

    small_seq = next(_rs._card_states_seq)
    large_seq = next(_rs._card_states_seq)
    assert small_seq < large_seq, "前提：序号单调递增"

    def _refuse(src, dst, **kwargs):
        raise OSError("probe: replace refused for the large-seq publish")

    monkeypatch.setattr(_os, "replace", _refuse)
    try:
        _rs._persist_card_states_bytes(target, b'{"failed": 1}', large_seq)
    except OSError:
        pass  # helper 不吞异常，归一由调用方做
    monkeypatch.setattr(_os, "replace", real_replace)

    # 序号更**小**、但从未发布过：只有在「失败的发布没有推进水位」时它才应当落盘。
    _rs._persist_card_states_bytes(target, b'{"kept": 1}', small_seq)
    assert json.loads(target.read_text(encoding="utf-8")) == {"kept": 1}, (
        "失败的发布不得推进已发布水位，否则后续从未发布过的快照会被全部误丢"
    )
    assert not target.with_suffix(".json.tmp").exists()


async def test_concept_identity_s7_seq_is_allocated_before_dispatch(svc, isolate_card_states, monkeypatch):
    """spec `openspec/specs/concept-identity/spec.md`
    Scenario: A stale snapshot never overwrites a newer one that already landed
    （取号必须发生在**派发线程之前**。）

    Codex r4 MEDIUM：把 `next(_card_states_seq)` 挪进线程里（或把 `to_thread` 改成
    同步直调），stale 门照样全绿——它是手工取号后直接调 helper 的。本门从**生产调用
    方**观测：`asyncio.to_thread` 必须被调到、被派发的必须是 helper、且 seq 必须已经
    是一个算好的 `int` 实参（挪进线程 ⇒ 实参会变成可调用对象或根本不存在）。
    """
    import asyncio as _aio

    real_to_thread = _aio.to_thread
    captured: list = []

    async def _recording_to_thread(fn, *args, **kwargs):
        captured.append((getattr(fn, "__name__", repr(fn)), args))
        return await real_to_thread(fn, *args, **kwargs)

    monkeypatch.setattr(_aio, "to_thread", _recording_to_thread)

    with _vault_scope("vault_s7d"):
        assert await svc._save_card_states(pending=("d1", "card-d1")) is True
        assert await svc._save_card_states(pending=("d2", "card-d2")) is True

    assert len(captured) == 2, (
        f"探针存活锚：两次落盘都必须经 asyncio.to_thread 派发（同步直调会让这里为空），实得 {captured!r}"
    )
    seqs = []
    for name, args in captured:
        assert name == "_persist_card_states_bytes", f"派发的必须是落盘 helper，实得 {name!r}"
        assert len(args) == 3, f"helper 必须收到 (target, payload, seq) 三个实参，实得 {len(args)} 个"
        assert isinstance(args[2], int), f"seq 必须在派发**之前**取好并作为 int 实参传入，实得 {type(args[2]).__name__}"
        seqs.append(args[2])
    assert seqs[0] < seqs[1], f"连续两次落盘的序号必须严格递增，实得 {seqs!r}"
