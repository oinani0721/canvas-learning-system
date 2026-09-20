# Canvas Learning System — PYRIGHT-TAIL 行为门
# [BATCH-2026-09-18-第十五批 / CARD-PYRIGHT-TAIL-BEHAVIOR]
#
# 本文件锁住 census `2026-09-13-PYRIGHT-TAIL-census.md` §四 七项「被 `# pyright: ignore`
# 掩盖的真缺陷」改成真行为之后的运行期语义,以及 §九.4 的 `TYPE_CHECKING` 声明一致性。
#
# ── 替身清单(协议要求;本文件逐条如实) ────────────────────────────────────────
#   本文件 **零 mock / 零 monkeypatch / 零替身**。所有断言都打在真对象上:
#     · 真 `asyncio.CancelledError` 实例 + 真 `asyncio.gather(return_exceptions=True)`
#     · 真 obsidiantools `Vault(tmp_path).connect()`(经 `WikilinkGraphService.build()` 真路径)
#     · 真 `RuntimeModelConfigManager` 单例 + 真 `SystemModelConfig` / `ModelTaskConfig`
#     · 真 `AgentType` 枚举、真 `Misconception` pydantic 模型
#     · 真 `IntelligentParallelService()` / 真 `MultimodalService(storage_base_path=tmp)` 默认实例
#   零连库(不触任何 Neo4j Bolt 端口, 也不起测试容器)、零 live vault 读写;
#   落盘只用 `tmp_path`。
#   ⚠️ 「零网络」如实收窄: 本文件自身不发任何网络请求, 但 import 服务模块会拉起
#   既有的 import 链(RAGService → LiteLLM), LiteLLM 在首次 import 时会**尝试**拉取
#   远端 model cost map, 失败后回落本地备份。那是既有行为、非本卡引入, 但它是一次
#   真实的联网尝试, 不能记成「零网络」(本卡 Codex round-1 指出)。
#   `RuntimeModelConfigManager` 是进程级单例 ⇒ 用 fixture 保存/还原它的 config,
#   这是隔离既有进程状态,不是替身。
#
# ── 先红形态(改代码前跑一次的实测,见验收单 (b)) ───────────────────────────────
#   依赖本卡新增纯函数(`_resolve_intent_model` / `_build_misconception` /
#   `_classify_gather_result`)的用例,改前形态 = **符号缺席**(ImportError),非行为断言;
#   其余用例改前红在各自指定断言上。故新符号一律在**用例函数体内** import,
#   避免模块级 collect error 把「红在断言」的证据一并吞掉。

import asyncio
import ast
import logging
from pathlib import Path

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# T-new-3 — agent_routing_engine: 恒 ImportError 降级写死模型 → 真接线
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def runtime_model_config():
    """真 `RuntimeModelConfigManager` 单例;用后还原,避免污染同进程其它用例。

    `__new__` 建单例时就把 `_config` 设成 `SystemModelConfig()`,property `config`
    恒非 None ⇒ 不写 `or SystemModelConfig()` 那种永不执行的兜底分支。
    """
    from app.core.litellm_config import RuntimeModelConfigManager

    manager = RuntimeModelConfigManager()
    original = manager.config
    assert original is not None, "单例的 config 应恒非 None(建实例时即已赋值)"
    try:
        yield manager
    finally:
        manager.update(original)


def test_resolve_intent_model_uses_configured_scoring_model(runtime_model_config):
    """配置了 scoring 模型时,意图分类必须用它,而不是写死的 fallback。

    改前:`_llm_classify_intent` import 一个**不存在**的 `get_litellm_config`
    ⇒ 恒 ImportError ⇒ 无论用户怎么配都跑 `gemini/gemini-2.0-flash`。
    """
    from app.core.litellm_config import (
        ModelTaskConfig,
        SystemModelConfig,
        format_litellm_model,
    )
    from app.services.agent_routing_engine import _resolve_intent_model

    runtime_model_config.update(
        SystemModelConfig(scoring=ModelTaskConfig(provider="anthropic", model_name="claude-sonnet-5", api_key=""))
    )

    resolved = _resolve_intent_model(runtime_model_config)

    assert resolved == format_litellm_model("anthropic", "claude-sonnet-5"), "配置了 scoring 模型时必须解析出该模型串"


def test_resolve_intent_model_falls_back_without_config(runtime_model_config):
    """完全没有配置时回落到既有常量(与改前的可见行为一致)。"""
    from app.core.litellm_config import SystemModelConfig
    from app.services.agent_routing_engine import (
        _INTENT_FALLBACK_MODEL,
        _resolve_intent_model,
    )

    runtime_model_config.update(SystemModelConfig())

    # ⚠️ 钉字面量而不是 `== _INTENT_FALLBACK_MODEL`:后者两侧同源(拿函数的输出比
    # 函数自己的常量),常量被改掉时门照样绿。这个字面量就是改前写死在
    # `_llm_classify_intent` 里的那个值,锁住「回落行为与改前一致」这个主张。
    assert _INTENT_FALLBACK_MODEL == "gemini/gemini-2.0-flash"
    assert _resolve_intent_model(runtime_model_config) == "gemini/gemini-2.0-flash"


def test_resolve_intent_model_reads_singleton_when_called_without_config(
    runtime_model_config,
):
    """生产调用形态是 `_resolve_intent_model()` —— 不传 config,走函数内延迟 import。

    ⚠️ 这条是本卡最该锁的那条路径:T-new-3 修的正是「import 了一个不存在的名字
    ⇒ 恒 ImportError ⇒ 恒降级」,而那个 import 只在 `config is None` 分支里执行。
    两条传 config 的门**根本走不到**它。
    """
    from app.core.litellm_config import (
        ModelTaskConfig,
        SystemModelConfig,
        format_litellm_model,
    )
    from app.services.agent_routing_engine import _resolve_intent_model

    runtime_model_config.update(
        SystemModelConfig(scoring=ModelTaskConfig(provider="openai", model_name="gpt-4o-mini", api_key=""))
    )

    # 无参调用:函数自己去 import get_runtime_model_config 并取同一个单例
    resolved = _resolve_intent_model()

    assert resolved == format_litellm_model("openai", "gpt-4o-mini")
    assert resolved != "gemini/gemini-2.0-flash", "无参形态必须真的读到了配置,而不是走降级回落"


def test_resolve_intent_model_falls_back_when_config_lookup_raises():
    """配置读取抛 `AttributeError` 时必须降级回落,而不是把异常抛给调用方。

    用一个真对象(不是 mock):一个 `get_scoring_model` 会抛 AttributeError 的轻量
    替身**不行**——DD-03 禁 mock 被测函数。这里改用真 `RuntimeModelConfigManager`
    的类型但把 `_config` 置成一个不具备所需属性的真对象,让属性访问真的抛。
    """
    from app.core.litellm_config import RuntimeModelConfigManager
    from app.services.agent_routing_engine import _resolve_intent_model

    manager = RuntimeModelConfigManager()
    original = manager.config
    try:
        # 真赋值:把 _config 换成一个真的没有 .scoring / .chat 的对象,
        # 于是 get_scoring_model() 内部的属性访问真的抛 AttributeError。
        manager._config = object()
        resolved = _resolve_intent_model(manager)
    finally:
        manager.update(original)

    assert resolved == "gemini/gemini-2.0-flash"


# ═══════════════════════════════════════════════════════════════════════════════
# T-new-1 — wikilink_graph_service: Vault 无 get_source_path 恒 AttributeError
# ═══════════════════════════════════════════════════════════════════════════════


def _write_vault(root: Path, files: dict[str, str]) -> Path:
    for rel, body in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return root


async def test_resolve_path_returns_vault_relative_path_for_nested_note(tmp_path):
    """嵌套目录的笔记必须解析出 vault 内相对路径,而不是恒回落 `<key>.md`。

    改前:`self._vault.get_source_path(...)` 在 obsidiantools 上不存在
    ⇒ AttributeError 被 `except Exception` 吞 ⇒ 邻居卡片的 path 恒是扁平的 `note.md`。
    """
    from app.services.wikilink_graph_service import WikilinkGraphService

    vault = _write_vault(
        tmp_path / "vault",
        {"sub/note.md": "# Note\n\nlinks to [[top]]\n", "top.md": "# Top\n"},
    )

    svc = WikilinkGraphService()
    await svc.build(str(vault))

    assert svc._resolve_path("note") == "sub/note.md"
    assert svc._resolve_path("top") == "top.md"


async def test_resolve_path_falls_back_for_unknown_key(tmp_path):
    """索引里没有的键仍回落 `<key>.md`(保留既有兜底,不引入 None/异常)。

    ⚠️ 这条改前/改后都绿(旧实现异常后也回落同一个值),无判别力——
    它锁的是「修复没把兜底顺手弄丢」,不是「修复生效了」。
    """
    from app.services.wikilink_graph_service import WikilinkGraphService

    vault = _write_vault(tmp_path / "vault", {"top.md": "# Top\n"})

    svc = WikilinkGraphService()
    await svc.build(str(vault))

    assert svc._resolve_path("ghost") == "ghost.md"


async def test_resolve_path_disambiguates_duplicate_basenames(tmp_path):
    """同名不同目录:obsidiantools 自己用相对路径做键,图节点名同步跟随。

    这条门覆盖「两个 note.md」这一路径:实测 `md_file_index` 的键在无重名时是裸文件名
    (`note`),出现重名时自动变成去扩展名的相对路径(`sub/note` / `sub2/note`)。
    ⚠️ 这里**不**主张两个集合相等:图节点还会包含未解析的 wikilink 目标
    (见 `test_resolve_path_falls_back_for_unresolved_link_targets`),
    也不保证 `_resolve_path` 的入参一定来自图(函数本身不校验来源)。
    先前这里写的「两者同域」已按实测收窄(本卡 Codex round-2 指出)。

    ⚠️ 判别力说明:重名的那两个键(`sub/note` / `sub2/note`)其旧回落值 `f"{key}.md"`
    恰好等于真实路径,单靠它们**测不出改动**。因此同一 vault 内另放一个不重名的
    嵌套笔记 `sub/unique.md`——它的键是裸 `unique`,旧回落给出 `unique.md`,
    与真实的 `sub/unique.md` 不同,这条断言才是本用例的判别力所在。
    """
    from app.services.wikilink_graph_service import WikilinkGraphService

    vault = _write_vault(
        tmp_path / "vault",
        {
            "sub/note.md": "# A\n",
            "sub2/note.md": "# B\n",
            "sub/unique.md": "# U\n",
            "top.md": "# Top\n",
        },
    )

    svc = WikilinkGraphService()
    await svc.build(str(vault))

    # 重名两键各自指向正确路径(等价路径,无判别力,只锁「消歧后不串台」)
    assert svc._resolve_path("sub/note") == "sub/note.md"
    assert svc._resolve_path("sub2/note") == "sub2/note.md"
    assert set(svc._graph.nodes) >= {"sub/note", "sub2/note"}

    # 判别力断言:不重名的嵌套笔记,键是裸文件名,旧回落会给出扁平的 `unique.md`
    assert svc._resolve_path("unique") == "sub/unique.md"


async def test_resolved_path_is_actually_readable_by_neighbor_loader(tmp_path):
    """端到端:`_resolve_path` 的输出必须真的能被下游的邻居正文加载器读出来。

    ⚠️ 这条锁的是本卡**最大的用户可见收益**,而它此前没有任何门、也没被写进验收单。
    链路: `_resolve_path` → `NeighborNote.path` → `wikilink_context_service.
    _read_neighbor_md(n.path, vault_root)` → `_resolve_vault_md_path`,
    后者用 `root / raw` 再 `.resolve(strict=True)`。

    改前 `_resolve_path` 恒返回兜底 `f"{note_key}.md"`。**在本用例这种无重名的 vault 里**,
    嵌套笔记的键是裸文件名 ⇒ 兜底给出扁平 `note.md` ⇒ `root/note.md` 不存在 ⇒
    `strict=True` 抛 OSError ⇒ 被下游 `except (OSError, ValueError)` 吞掉 ⇒ 返回 None
    ⇒ 该邻居的 `content_summary` 与 callouts 为空,正文进不了 LLM 提示。
    改后解析出真实相对路径,正文才读得到。

    ⚠️ 影响面如实(不是「任何嵌套笔记都恒空」): 出现**同名不同目录**时键本身已是
    `sub/note` 这样的相对路径,旧兜底 `f"{key}.md"` 恰好等于真实路径 ⇒ 那种笔记改前
    也读得到。先前这里写「任何不在 vault 根目录的笔记…恒空」把一种情形说成了全部
    (本卡 Codex round-2 指出)。

    本门只 **import** `wikilink_context_service` 的两个函数(该文件不在本卡地盘,
    一字未改),用真 vault、真文件、真读取,零替身。
    """
    from app.services.wikilink_context_service import (
        _read_neighbor_md,
        _resolve_vault_md_path,
    )
    from app.services.wikilink_graph_service import WikilinkGraphService

    body = "# Note\n\n这是邻居正文,改前读不到。\n"
    vault = _write_vault(
        tmp_path / "vault",
        {"sub/note.md": body, "top.md": "# Top\n\nlinks [[note]]\n"},
    )
    vault_root = str(vault)

    svc = WikilinkGraphService()
    await svc.build(vault_root)

    resolved = svc._resolve_path("note")
    assert resolved == "sub/note.md"

    # 修复后的输出:下游真的解析得到、真的读得出正文
    assert _resolve_vault_md_path(resolved, vault_root) is not None
    assert _read_neighbor_md(resolved, vault_root) == body

    # 对照输入 = 改前的扁平输出:下游解析失败、正文恒空
    assert _resolve_vault_md_path("note.md", vault_root) is None
    assert _read_neighbor_md("note.md", vault_root) is None


async def test_resolve_path_handles_unicode_and_spaced_filenames(tmp_path):
    """中文路径 / 含空格 / 多点文件名都必须解析出真实相对路径。

    三条断言各自有判别力:旧实现对它们一律给扁平的 `<key>.md`。
    """
    from app.services.wikilink_graph_service import WikilinkGraphService

    vault = _write_vault(
        tmp_path / "vault",
        {
            "深层/子目录/中文笔记.md": "# CN\n",
            "plain/with space.md": "# Space\n",
            "plain/a.b.md": "# Dot\n",
            "root.md": "# Root\n",
        },
    )

    svc = WikilinkGraphService()
    await svc.build(str(vault))

    assert svc._resolve_path("中文笔记") == "深层/子目录/中文笔记.md"
    assert svc._resolve_path("with space") == "plain/with space.md"
    assert svc._resolve_path("a.b") == "plain/a.b.md"


async def test_resolve_path_falls_back_for_unresolved_link_targets(tmp_path):
    """图节点是索引键的**超集**——多出来的那些必须走兜底,不得抛异常。

    obsidiantools 的图节点 = `md_file_index` 键 ∪ 正文 wikilink 的目标文本。
    后者包含「指向不存在笔记的链接」与「非 .md 的链接目标」,它们在索引里查不到。
    这条门锁住那条路径,并同时把「图节点 ⊋ 索引键」这个集合关系本身钉住——
    docstring 先前写的「两者同域」就是在这里被推翻的。
    """
    from app.services.wikilink_graph_service import WikilinkGraphService

    vault = _write_vault(
        tmp_path / "vault",
        {
            "sub/note.md": "# A\n",
            "sub2/note.md": "# B\n",
            "hub.md": "# Hub\n\n链接到裸名 [[note]] 以及 [[data.txt]]\n",
        },
    )

    svc = WikilinkGraphService()
    await svc.build(str(vault))

    index_keys = set(svc._vault.md_file_index)
    nodes = set(svc._graph.nodes)

    # 集合关系:图节点严格包含索引键(⊋,不是 ==)
    assert index_keys < nodes, "图节点应是索引键的真超集"
    assert {"note", "data.txt"} <= (nodes - index_keys), (
        "未解析的裸名链接与非 .md 链接目标都应作为图节点出现,却不在索引里"
    )

    # 这些多出来的键走兜底,不抛异常
    assert svc._resolve_path("note") == "note.md"
    assert svc._resolve_path("data.txt") == "data.txt.md"
    # 而真实存在的重名笔记仍各自解析正确
    assert svc._resolve_path("sub/note") == "sub/note.md"
    assert svc._resolve_path("sub2/note") == "sub2/note.md"


# ═══════════════════════════════════════════════════════════════════════════════
# T-new-2 — error_classifier: 旧字段名被 pydantic 静默丢弃
# ═══════════════════════════════════════════════════════════════════════════════


def test_legacy_created_at_kwarg_is_silently_dropped_by_model():
    """缺陷机理门(改前/改后都绿):`Misconception` 对旧名 `created_at=` 静默丢弃。

    锁住「为什么必须改 kwarg 名」——不是风格问题:pydantic v2 默认 `extra='ignore'`,
    传旧名不报错、值直接丢,字段回落 default_factory。
    """
    from app.graphiti.entity_types import (
        ERROR_TYPE_TO_REMEDY,
        ErrorType,
        Misconception,
    )

    sentinel = "2026-01-01T00:00:00+00:00"
    entity = Misconception(
        misconception_id="m-1",
        error_type=ErrorType.KNOWLEDGE_GAP,
        description="d",
        remedy_strategy=ERROR_TYPE_TO_REMEDY[ErrorType.KNOWLEDGE_GAP],
        node_id="n-1",
        created_at=sentinel,  # type: ignore[call-arg]  # 旧名,故意传入以证明被丢弃
    )

    assert entity.misconception_created_at != sentinel, "旧 kwarg 名必须被模型丢弃——这正是本卡要改掉它的原因"


def test_build_misconception_preserves_caller_timestamp():
    """抽出的建实体纯函数必须把调用方给的时间戳真正写进实体。"""
    from app.graphiti.entity_types import ERROR_TYPE_TO_REMEDY, ErrorType
    from app.services.error_classifier import _build_misconception

    sentinel = "2026-01-01T00:00:00+00:00"
    entity = _build_misconception(
        error_type=ErrorType.KNOWLEDGE_GAP,
        description="学生把收敛和有界搞混了",
        context="ctx",
        remedy=ERROR_TYPE_TO_REMEDY[ErrorType.KNOWLEDGE_GAP],
        node_id="node-1",
        session_id="sess-1",
        created_at=sentinel,
    )

    assert entity.misconception_created_at == sentinel
    assert entity.description == "学生把收敛和有界搞混了"
    assert entity.node_id == "node-1"


# ═══════════════════════════════════════════════════════════════════════════════
# T-new-5 — batch_orchestrator: CancelledError 被当业务结果
# ═══════════════════════════════════════════════════════════════════════════════


async def test_gather_return_exceptions_surfaces_cancellation_as_non_exception():
    """输入面真实性门:真 `gather(return_exceptions=True)` 确实把 `CancelledError`
    放进结果列表,且 `isinstance(result, Exception)` 对它是 **False**。

    这条不依赖本卡任何新符号——它证明既有两处 `isinstance(result, Exception)` 分支
    筛不掉取消,缺陷输入面不是假想出来的。
    """

    async def _never_finishes():
        await asyncio.sleep(3600)

    task = asyncio.ensure_future(_never_finishes())
    await asyncio.sleep(0)
    task.cancel()

    results = await asyncio.gather(task, return_exceptions=True)

    assert isinstance(results[0], asyncio.CancelledError)
    assert isinstance(results[0], BaseException)
    assert not isinstance(results[0], Exception), "CancelledError 继承 BaseException 而非 Exception ⇒ 旧分支筛不掉它"


def test_classify_gather_result_separates_cancellation_from_failure():
    """取消必须与普通失败区分开,两者都不得被当成业务结果。"""
    from app.services.batch_orchestrator import _classify_gather_result

    assert _classify_gather_result(asyncio.CancelledError()) == "cancelled"
    assert _classify_gather_result(RuntimeError("boom")) == "failed"
    assert _classify_gather_result(ValueError("bad")) == "failed"


def test_gather_result_loops_screen_on_baseexception_not_exception():
    """锁住 T-new-5 的**真修复点**:两个结果处理循环筛的是 `BaseException`。

    ⚠️ 为什么需要这条:`_classify_gather_result` 的返回值在生产里只用来挑日志文案
    (`kind == "cancelled"` 只决定 logger.error/warning 的措辞);真正决定「取消会不会
    被当成业务结果 append」的,是两个 for 循环里那句 isinstance 的第二个实参。
    只给纯函数落门,等于修复点本身无人看管——把 isinstance 改回 `Exception` 时
    纯函数的三条断言照样全绿。
    """
    src = (_SERVICES / "batch_orchestrator.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    checked = {}
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if fn.name not in ("_execute_all_groups", "_execute_group"):
            continue
        for node in ast.walk(fn):
            # 找 `for ... in enumerate(results)` 循环体里的 `if isinstance(result, X)`
            if not isinstance(node, ast.If):
                continue
            test = node.test
            if not (
                isinstance(test, ast.Call)
                and isinstance(test.func, ast.Name)
                and test.func.id == "isinstance"
                and len(test.args) == 2
                and isinstance(test.args[0], ast.Name)
                and test.args[0].id == "result"
            ):
                continue
            checked.setdefault(fn.name, []).append(ast.unparse(test.args[1]))

    assert set(checked) == {"_execute_all_groups", "_execute_group"}, (
        f"两个结果处理函数都应有 isinstance(result, …) 判定,实测 {sorted(checked)}"
    )
    for fname, kinds in checked.items():
        assert kinds == ["BaseException"], (
            f"{fname} 的结果筛选必须用 BaseException(才筛得掉 CancelledError),实测 {kinds}"
        )


def test_classify_call_site_uses_build_misconception_helper():
    """锁住 T-new-2 的**真修复点**:`classify()` 走 helper,不再直接构造实体。

    ⚠️ 为什么需要这条:缺陷行是 `classify()` 里用错 kwarg 名那一句,修复是让它改调
    `_build_misconception`。只给 helper 落门的话,把 `classify()` 改回直接
    `Misconception(created_at=…)` 时 helper 的断言照样全绿。
    """
    tree = ast.parse((_SERVICES / "error_classifier.py").read_text(encoding="utf-8"))

    classify = next(
        (
            fn
            for fn in ast.walk(tree)
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) and fn.name == "classify"
        ),
        None,
    )
    assert classify is not None, "error_classifier.py 应有 classify()"

    called = {
        node.func.id for node in ast.walk(classify) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_build_misconception" in called, "classify() 必须经由 helper 建实体"
    assert "Misconception" not in called, "classify() 不得再直接构造 Misconception"

    # 全文件层面:任何 Misconception(...) 构造都不得再用旧 kwarg 名
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Misconception":
            kwargs = {k.arg for k in node.keywords if k.arg}
            assert "created_at" not in kwargs, "旧 kwarg 名会被 pydantic 静默丢弃"
            assert "misconception_created_at" in kwargs, "必须写模型的真实字段名"


def test_classify_gather_result_treats_real_result_as_ok():
    """真业务结果对象仍归 `"ok"`——修复不得把正常结果误判成失败。"""
    from app.services.batch_orchestrator import (
        NodeExecutionResult,
        _classify_gather_result,
    )

    real = NodeExecutionResult(node_id="n-1", success=True)

    assert _classify_gather_result(real) == "ok"


# ═══════════════════════════════════════════════════════════════════════════════
# T-new-6 — intelligent_parallel_service: str 未转 AgentType
# ═══════════════════════════════════════════════════════════════════════════════


def test_agent_type_accepts_alias_values_and_rejects_unknown():
    """枚举别名可用,未知值必须抛 `ValueError`。

    ⚠️ 这条**无判别力**:它断言的只是 `app/services/agent_service.py` 里
    `AgentType` 枚举自身的行为——那是本卡硬边界内的零改动文件,改前改后都绿,
    也不在验收单 (b) 的先红名单里。它的作用是给下一条门交代前提
    (「`AgentType(...)` 这个转换本身确实能区分合法与非法取值」),
    真正锁住 T-new-6 修复的是下面那条 `retry_single_node` 的门。
    ⚠️ docstring 先前写的是「(转换是有判别力的)」——把「转换有判别力」误写成了
    「这条门有判别力」,已改正(本卡内部对抗复核完整性批评者指出)。
    """
    from app.services.agent_service import AgentType

    assert AgentType("four-level") is AgentType.FOUR_LEVEL
    assert AgentType("comparison-table") is AgentType.COMPARISON_TABLE

    with pytest.raises(ValueError):
        AgentType("nope")


async def test_retry_single_node_rejects_unknown_agent_type_before_dispatch(tmp_path):
    """未知 agent_type 必须当场报错返回,而不是一路传到 `call_agent` 再静默失败。

    用真默认实例(未注入 agent_service)——校验发生在依赖检查之前,
    因此这条门不需要任何替身。
    """
    from app.models.intelligent_parallel_models import SingleAgentStatus
    from app.services.intelligent_parallel_service import IntelligentParallelService

    svc = IntelligentParallelService()

    resp = await svc.retry_single_node(
        node_id="node-1",
        agent_type="nope",
        canvas_path=str(tmp_path / "x.canvas"),
    )

    assert resp.status == SingleAgentStatus.failed
    assert resp.node_id == "node-1"
    assert "unknown agent_type" in (resp.error_message or "")


# ═══════════════════════════════════════════════════════════════════════════════
# T-new-8 — multimodal_service: 死 import 退役(用户可见行为不变)
# ═══════════════════════════════════════════════════════════════════════════════


async def test_generate_embedding_reports_missing_service_without_import_error(tmp_path, caplog):
    """退役死 import 后仍返回 None、仍写「降级为文本搜索」,但不再谎称 ImportError。"""
    from app.services.multimodal_service import MultimodalService

    svc = MultimodalService(storage_base_path=str(tmp_path / "storage"))

    with caplog.at_level(logging.WARNING):
        vector = await svc._generate_embedding("任意查询")

    assert vector is None

    messages = [rec.message for rec in caplog.records]
    assert any("降级为文本搜索" in m for m in messages), "文本降级的用户可见口径必须保留"
    assert not any("ImportError" in m for m in messages), "已无死 import ⇒ 不得再把原因写成 ImportError"

    # ⚠️ 上面三条里有两条改前改后都真(`vector is None` —— 旧代码的 ImportError 分支
    # 同样 return None;「降级为文本搜索」—— 旧日志文案里也有这六个字)。判别力原本
    # 全压在 `"ImportError"` 这个英文字面量上:把旧文案换个说法再还原死 import,
    # 门就绿了。下面用**结构**而不是文案再钉一道——死 import 与其 except 分支
    # 已整段退役,所以函数体里不该再有任何 import 语句、也不该再有 try/except。
    import inspect
    import textwrap

    fn_ast = ast.parse(textwrap.dedent(inspect.getsource(MultimodalService._generate_embedding))).body[0]
    kinds = {type(n).__name__ for n in ast.walk(fn_ast)}
    assert not {"Import", "ImportFrom"} & kinds, "_generate_embedding 里不应再有任何 import(死 import 已退役)"
    assert "Try" not in kinds, "_generate_embedding 里不应再有 try/except(那是死 import 的 except 分支)"


# ═══════════════════════════════════════════════════════════════════════════════
# census §九.4 — exam_service TYPE_CHECKING 11 声明 ↔ exam_service_ext 真实签名
# ═══════════════════════════════════════════════════════════════════════════════

_SERVICES = Path(__file__).resolve().parents[2] / "app" / "services"


def _signature_of(fn) -> tuple:
    """签名比较元组。

    含 `decorator_list`:给某一侧的方法加装饰器会改变绑定语义(例如包一层
    `staticmethod` 或缓存),只比 args/returns 的话门看不出这种差异。
    """
    return (
        isinstance(fn, ast.AsyncFunctionDef),
        ast.unparse(fn.args),
        ast.unparse(fn.returns) if fn.returns else None,
        tuple(ast.unparse(d) for d in fn.decorator_list),
    )


def _type_checking_block():
    """返回 `ExamService` 类体内那个 `if TYPE_CHECKING:` 节点(没有则 None)。"""
    tree = ast.parse((_SERVICES / "exam_service.py").read_text(encoding="utf-8"))
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef) or cls.name != "ExamService":
            continue
        for node in cls.body:
            if isinstance(node, ast.If) and "TYPE_CHECKING" in ast.unparse(node.test):
                return node
    return None


def _declared_signatures() -> dict[str, tuple]:
    """抽 `ExamService` 类体 `if TYPE_CHECKING:` 块内的方法声明签名。"""
    block = _type_checking_block()
    if block is None:
        return {}
    return {fn.name: _signature_of(fn) for fn in block.body if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _ext_signatures() -> dict[str, tuple]:
    """抽 `exam_service_ext.py` 模块顶层真实 def 的签名。"""
    tree = ast.parse((_SERVICES / "exam_service_ext.py").read_text(encoding="utf-8"))
    return {fn.name: _signature_of(fn) for fn in tree.body if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _attach_bindings() -> dict[str, str]:
    """抽 `attach_to_exam_service()` **函数体顶层**的 `ExamService.<name> = <rhs>`。

    返回 ``{挂载到的属性名: 赋值右侧的源码文本}``。两个刻意的设计:

    1. **连右侧一起记**——只记左侧属性名的话,「挂了名字但挂错函数」
       (`ExamService.generate_hint = skip_question`)这类错误门完全看不见,
       而这恰恰是门自称要锁的「ext 是运行期真相」。
    2. **只看函数体顶层,不用 `ast.walk` 递归**——与 `_declared_signatures` /
       `_ext_signatures` 的非递归口径对齐。递归会把条件分支里的、或嵌套 def 里
       根本不执行的挂载语句也算成「已挂载」,两侧口径不对称会造成静默通过面。
    """
    tree = ast.parse((_SERVICES / "exam_service_ext.py").read_text(encoding="utf-8"))
    bindings: dict[str, str] = {}
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef) or fn.name != "attach_to_exam_service":
            continue
        for stmt in fn.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for target in stmt.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "ExamService"
                ):
                    bindings[target.attr] = ast.unparse(stmt.value)
    return bindings


def _attached_names() -> set[str]:
    return set(_attach_bindings())


def test_type_checking_declarations_match_ext_signatures():
    """11 条 `TYPE_CHECKING` 声明必须与 ext 的真实 def 逐条同签名。

    ext 是运行期真相(方法由 `attach_to_exam_service()` 真赋上去);声明只是给 pyright 看的。
    两侧漂移 = pyright 绿但运行期签名不同 ⇒ 静默的调用方错误。
    """
    declared = _declared_signatures()
    ext = _ext_signatures()

    assert len(declared) == 11, f"声明数应为 11,实测 {len(declared)}"

    mismatch = {k: (v, ext.get(k)) for k, v in declared.items() if v != ext.get(k)}
    assert mismatch == {}, f"声明与真实签名不一致: {mismatch}"


def test_type_checking_declaration_names_match_attach_assignments():
    """声明名集合必须恰好等于 `attach_to_exam_service()` 真正挂上去的名字集合。"""
    declared = set(_declared_signatures())
    attached = _attached_names()

    assert declared == attached, (
        f"声明但未挂载: {sorted(declared - attached)};挂载但未声明: {sorted(attached - declared)}"
    )


def test_attach_bindings_point_at_the_same_named_function():
    """每条 `ExamService.<name> = <rhs>` 的**右侧**必须就是同名的那个 def。

    ⚠️ 为什么需要这条:上面两条门只比「名字集合」和「签名」,都只看赋值左侧。
    把 `ExamService.generate_hint = skip_question` 这样挂错函数,
    左侧集合不变、两个签名又都真实存在于 ext ⇒ 两条门全绿,
    而运行期挂上去的是另一个函数。这正是门自称要锁的「ext 是运行期真相」。
    """
    bindings = _attach_bindings()
    ext = _ext_signatures()

    assert len(bindings) == 11, f"应有 11 条挂载,实测 {len(bindings)}"

    mismatched = {attr: rhs for attr, rhs in bindings.items() if rhs != attr}
    assert mismatched == {}, f"挂载右侧与属性名不一致(挂错了函数): {mismatched}"

    missing = sorted(rhs for rhs in bindings.values() if rhs not in ext)
    assert missing == [], f"挂载右侧引用了 ext 里不存在的名字: {missing}"


def test_type_checking_block_contains_only_method_declarations():
    """`if TYPE_CHECKING:` 块里除了 def 不得有别的语句。

    ⚠️ 为什么需要这条:`_declared_signatures` 只收 FunctionDef/AsyncFunctionDef,
    非 def 语句(变量注解、赋值、嵌套 if)会被**静默丢弃**,而 `len(declared) == 11`
    这条计数判据也只数 def ⇒ 往块里塞任何非 def 内容,两条既有门都看不见。
    这条门把「块内还有什么」这件事本身钉住。
    """
    block = _type_checking_block()
    assert block is not None, "ExamService 类体内应有 if TYPE_CHECKING: 块"

    non_defs = [
        ast.unparse(stmt)[:80] for stmt in block.body if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    assert non_defs == [], f"TYPE_CHECKING 块内出现非 def 语句(门看不见它们): {non_defs}"

    assert block.orelse == [], "TYPE_CHECKING 块不应有 else 分支"
