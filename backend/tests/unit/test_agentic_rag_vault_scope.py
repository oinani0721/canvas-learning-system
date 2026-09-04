# CARD-G4-4 (BATCH-2026-09-01-第八批) — 内链请求级 VaultScope · 单元与双 vault 隔离
"""lib/agentic_rag/nodes.py 内链作用域测试 + tmp LanceDB 双 vault 隔离行为。

⚠️ import 路径 (同仓先例 reference): ``lib/agentic_rag/nodes`` 是 re-export
包, 真实模块以 ``agentic_rag._nodes_impl`` 名注册 (nodes/__init__.py 用
spec_from_file_location 固定名加载) — patch 私有成员必须打
``agentic_rag._nodes_impl`` 命名空间, 打包的 ``__init__`` 上无效。

锁三件事:

1. **内链请求级** — compress_context 的 memory_group_id 必须由
   ``app.core.vault_scope.current_vault_id()`` (请求级 ContextVar) 派生,
   不得再读进程级 active vault。判据用「两个来源注入不同值」: 请求级 =
   req_vault, 进程级 = proc_vault, 断言记忆注入收到 vault:req_vault ——
   若有人改回进程级读取, 本门变红。
2. **双 vault 隔离行为** — 同一个 tmp LanceDB 目录里预置 vault A / B
   两张命名空间表, B 表有「只有它在 B」的笔记 (含与 A 同名的不同内容
   笔记)。以 vault A 作用域检索: 0 条来自 B + 正向对照命中 A 独有笔记 +
   反向对称。判据按 doc_id/content 判来源, 防「全同组 fixture 假绿」
   (MEMORY: 全同组 fixture 杀不掉单 alias 变异)。
3. **subject 一致性哨兵** — state["subject"] 与请求级 VaultScope 二级
   分裂时必须告警 (检索链用 state, 记忆注入用 ContextVar, 分裂 = 两条
   链落不同作用域)。

与卡文的偏差 (如实声明):
   卡文完成条件 (b) 预写「vault:default 污染桶抛 VaultScopeUnresolved
   属预期, 测试覆盖」。核实 vault_scope.py:294-318: ``current_vault_id``
   **没有**形状校验、不抛 VaultScopeUnresolved —— 污染桶 fail-closed 是
   ``require_read_group`` (读侧) 的职责。本卡按 (b) 字面接
   current_vault_id, 本文件 TestCurrentVaultIdBehavior 按**真实行为**测
   试 (返回 "default" 段, 不抛), 不为凑卡文造一个校验层 (那会改
   vault_scope 本体, 违反禁改边界)。

本文件不比什么: 不证明 /rag/query HTTP 层的 422/409 (API 文件职责);
不证明 rag_service 全图执行 (防 LLM 外发副作用, 检索作用域链按「端点
注入 ContextVar → 节点读 ContextVar → 表名」两段真链拼合证明); 不证明
bge-m3 真实向量的语义质量 (embed 打桩为固定向量, 隔离判据靠表命名空
间而非向量相似度)。
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 真实节点模块 (re-export 包的本体) — patch 私有成员只能打这里
import agentic_rag._nodes_impl as nodes


# ═══════════════════════════════════════════════════════════════════════════
# 工具
# ═══════════════════════════════════════════════════════════════════════════


def _set_scope(group_id: str):
    """把请求级作用域注入 ContextVar, 返回 reset 用的 token。"""
    from app.core.subject_config import _current_subject_id

    return _current_subject_id.set(group_id)


def _reset_scope(token):
    from app.core.subject_config import _current_subject_id

    _current_subject_id.reset(token)


# ═══════════════════════════════════════════════════════════════════════════
# 1. 内链请求级 — compress_context 的 memory_group_id
# ═══════════════════════════════════════════════════════════════════════════


class TestInnerChainReadsRequestScope:
    def test_compress_context_memory_group_uses_request_scope(self, monkeypatch):
        """请求级与进程级注入**不同** vault 时, 记忆注入必须用请求级。"""
        import app.config as app_config_mod
        import app.core.vault_scope as vault_scope_mod

        monkeypatch.setattr(
            vault_scope_mod, "current_vault_id", lambda: "req_vault", raising=True
        )
        monkeypatch.setattr(
            app_config_mod, "get_current_vault_id", lambda: "proc_vault", raising=True
        )

        captured: dict = {}

        async def _capture_memories(**kwargs):
            captured["group_id"] = kwargs.get("group_id")
            return "", None

        # graphiti 客户端给活体 MagicMock; lancedb/temporal 客户端一律失败,
        # 让节点走各自的无害降级分支 (本测试只关心 Step 4 的 group_id)。
        monkeypatch.setattr(
            nodes, "_get_graphiti_client", AsyncMock(return_value=MagicMock())
        )
        monkeypatch.setattr(
            nodes,
            "_get_lancedb_client",
            AsyncMock(side_effect=RuntimeError("no lancedb in unit test")),
        )
        monkeypatch.setattr(
            nodes,
            "_get_temporal_client",
            AsyncMock(side_effect=RuntimeError("no temporal in unit test")),
        )
        with patch(
            "agentic_rag.mastery_injection.retrieve_learning_memories",
            new=_capture_memories,
        ):
            state = {"messages": [{"role": "user", "content": "q"}], "subject": None}

            asyncio.run(nodes.compress_context_node(state, None))

        assert captured.get("group_id") == "vault:req_vault", (
            f"记忆注入用了 {captured.get('group_id')!r} — "
            "内链仍在读进程级 active vault 而非请求级 VaultScope"
        )

    def test_falls_back_to_process_level_only_when_scope_absent(self, monkeypatch):
        """回落语义: 请求级未注入 (后台任务) 才读进程级 active vault ——
        与 G2-2 推导语义一致; 请求级在位时进程级值绝不参与。"""
        import app.config as app_config_mod
        import app.core.vault_scope as vault_scope_mod
        from app.core.subject_config import _current_subject_id

        monkeypatch.setattr(
            app_config_mod, "get_current_vault_id", lambda: "proc_vault", raising=True
        )

        token = _current_subject_id.set("general")  # 视作未注入
        try:
            assert vault_scope_mod.current_vault_id() == "proc_vault"
        finally:
            _current_subject_id.reset(token)


# ═══════════════════════════════════════════════════════════════════════════
# 2. current_vault_id 真实行为 (含与卡文预写的偏差文档)
# ═══════════════════════════════════════════════════════════════════════════


class TestCurrentVaultIdBehavior:
    def test_returns_vault_segment_of_injected_scope(self):
        token = _set_scope("vault:v1:algorithms")
        try:
            from app.core.vault_scope import current_vault_id

            assert current_vault_id() == "v1"
        finally:
            _reset_scope(token)

    def test_falls_back_to_process_active_vault_when_not_injected(self, monkeypatch):
        import app.config as app_config_mod
        from app.core.subject_config import DEFAULT_SUBJECT_ID, _current_subject_id
        from app.core.vault_scope import current_vault_id

        token = _current_subject_id.set(DEFAULT_SUBJECT_ID)
        try:
            monkeypatch.setattr(
                app_config_mod, "get_current_vault_id", lambda: "proc_v", raising=True
            )
            assert current_vault_id() == "proc_v"
        finally:
            _current_subject_id.reset(token)

    def test_pollution_bucket_returns_default_segment_without_raising(self):
        """⚠️ 文档化与卡文预写的偏差: current_vault_id **不抛**
        VaultScopeUnresolved — 它没有形状校验, 污染桶 fail-closed 属
        require_read_group (读侧) 的职责。这里锁真实行为, 防止后人误以为
        内链有抛错保护而在调用点省掉 try/except (compress_context 的
        except 分支依赖「解析可能失败」这个前提)。"""
        token = _set_scope("vault:default")
        try:
            from app.core.vault_scope import VaultScopeUnresolved, current_vault_id

            try:
                assert current_vault_id() == "default"
            except VaultScopeUnresolved:
                pytest.fail(
                    "current_vault_id 抛了 VaultScopeUnresolved — 行为漂移, "
                    "compress_context 的调用点契约需要重新评估"
                )
        finally:
            _reset_scope(token)


class TestAgentChainSubjectPassthrough:
    """总账 G4-4 判据「agent 链 subject 透传」— state["subject"] 必须真的
    传进 Graphiti 检索的 scoped group（math → math:<canvas>），不能在
    节点层丢失退化为裸 canvas。"""

    def test_subject_scopes_graphiti_search_group(self, monkeypatch):
        captured: dict = {}

        async def _capture_search(**kwargs):
            captured["canvas_file"] = kwargs.get("canvas_file")
            return []

        graphiti_stub = MagicMock()
        graphiti_stub.search_nodes = _capture_search
        monkeypatch.setattr(
            nodes, "_get_graphiti_client", AsyncMock(return_value=graphiti_stub)
        )

        state = {
            "messages": [{"role": "user", "content": "q"}],
            "canvas_file": "离散数学.canvas",
            "subject": "math",
        }
        asyncio.run(nodes.retrieve_graphiti(state, None))

        assert captured.get("canvas_file") == "math:离散数学_canvas", (
            f"Graphiti 检索收到的 scoped group = {captured.get('canvas_file')!r} — "
            "state['subject'] 在 agent 链透传断裂"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 3. subject 一致性哨兵
# ═══════════════════════════════════════════════════════════════════════════

_SENTINEL_LOGGER = "agentic_rag._nodes_impl"


class TestSubjectScopeSentinel:
    def test_mismatch_warns(self, caplog):
        token = _set_scope("vault:v1:math")
        try:
            with caplog.at_level(logging.WARNING, logger=_SENTINEL_LOGGER):
                nodes._warn_subject_scope_mismatch(
                    {"subject": "physics"}, logger_ctx="test_node"
                )
        finally:
            _reset_scope(token)

        assert any("不一致" in r.getMessage() for r in caplog.records), (
            "state.subject 与 VaultScope 二级分裂未告警 — 哨兵失灵"
        )

    def test_consistent_subject_does_not_warn(self, caplog):
        token = _set_scope("vault:v1:math")
        try:
            with caplog.at_level(logging.WARNING, logger=_SENTINEL_LOGGER):
                nodes._warn_subject_scope_mismatch(
                    {"subject": "math"}, logger_ctx="test_node"
                )
        finally:
            _reset_scope(token)

        assert not any("不一致" in r.getMessage() for r in caplog.records)

    def test_absent_subject_does_not_warn(self, caplog):
        token = _set_scope("vault:v1")
        try:
            with caplog.at_level(logging.WARNING, logger=_SENTINEL_LOGGER):
                nodes._warn_subject_scope_mismatch({"subject": None}, logger_ctx="t")
        finally:
            _reset_scope(token)

        assert not caplog.records

    def test_sentinel_never_raises(self):
        """哨兵自身不得成为业务失败源 — current_group_id 抛错时静默降级。"""
        import app.core.vault_scope as vault_scope_mod

        token = _set_scope("vault:v1:math")
        try:
            with patch.object(
                vault_scope_mod,
                "current_group_id",
                side_effect=RuntimeError("boom"),
            ):
                # 不抛即通过
                nodes._warn_subject_scope_mismatch({"subject": "math"}, logger_ctx="t")
        finally:
            _reset_scope(token)


# ═══════════════════════════════════════════════════════════════════════════
# 4. 双 vault 隔离行为 — tmp LanceDB 真库
# ═══════════════════════════════════════════════════════════════════════════

_DIM = 8


def _vec(seed: float) -> list:
    """固定向量 — 隔离判据靠表命名空间, 不靠向量相似度。"""
    return [seed] * _DIM


def _jieba_tokens(content: str) -> str:
    """与 client FTS 查询侧同一分词器, 保证 content_tokenized 形态一致。"""
    try:
        from agentic_rag.clients.lancedb_client import _jieba_tokenize

        return _jieba_tokenize(content)
    except Exception:
        return content


def _seed_dual_vault_db(tmp_path):
    """同一个 tmp 目录预置 vault_a / vault_b 两张命名空间表。

    「只有它在 B」笔记 (b_unique) 与 A/B 同名不同内容笔记 (same_name_*)
    是隔离判据的核心; A 表另放干扰行保证正向对照不是查空表。
    """
    import lancedb

    rows = {
        "vault_a_canvas_nodes": [
            {
                "doc_id": "a_unique",
                "subject": "math",
                "content": "红黑树旋转的颜色翻转规则 [[递归基础]] [[b秘密板]]",
                "vector": _vec(0.10),
                "content_tokenized": _jieba_tokens("红黑树旋转的颜色翻转规则"),
                "canvas_file": "a.canvas",
            },
            {
                "doc_id": "same_name_a",
                "subject": "math",
                "content": "递归的基础定义: 函数调用自身",
                "vector": _vec(0.20),
                "content_tokenized": _jieba_tokens("递归的基础定义: 函数调用自身"),
                "canvas_file": "a.canvas",
            },
            {
                "doc_id": "a_neighbor",
                "subject": "math",
                "content": "递归基础 A 库版本内容",
                "vector": _vec(0.30),
                "content_tokenized": _jieba_tokens("递归基础 A 库版本内容"),
                "canvas_file": "递归基础.canvas",
            },
        ],
        "vault_b_canvas_nodes": [
            {
                "doc_id": "b_unique",
                "subject": "cs",
                "content": "贝尔不等式的量子纠缠判据",
                "vector": _vec(0.10),
                "content_tokenized": _jieba_tokens("贝尔不等式的量子纠缠判据"),
                "canvas_file": "b.canvas",
            },
            {
                "doc_id": "same_name_b",
                "subject": "cs",
                "content": "递归的进阶定义: 尾递归优化与调用栈",
                "vector": _vec(0.20),
                "content_tokenized": _jieba_tokens("递归的进阶定义: 尾递归优化与调用栈"),
                "canvas_file": "b.canvas",
            },
        ],
        # 裸 legacy 表 (无 vault 前缀) — Codex round-1 BLOCKER-1 反例:
        # 邻居扩展若绕过作用域解析直接 open 裸表, B 的秘密内容会混进
        # vault A 的检索结果。本表只有 B 内容, 修复后 A 作用域永不触达。
        "vault_notes": [
            {
                "doc_id": "b_secret",
                "subject": "cs",
                "content": "B 库绝密量子隐形传态",
                "vector": _vec(0.10),
                "content_tokenized": _jieba_tokens("B 库绝密量子隐形传态"),
                "canvas_file": "b秘密板.canvas",
            },
        ],
    }
    # 干扰行 (近距): 把 a_neighbor 挤出主检索 top — Codex round-2 整改:
    # a_neighbor 原本就在主检索结果里, 扩展结果被 existing_doc_ids 去重,
    # neighbor_expansion 标记恒不出现 (Codex 恒等函数反例)。挤出后
    # a_neighbor 只能经 wiki-link 扩展进入, 活性门才成立。
    rows["vault_a_canvas_nodes"].extend(
        {
            "doc_id": f"a_filler_{i}",
            "subject": "math",
            "content": f"占位干扰内容第{i}号与查询词无关",
            "vector": _vec(0.12 + i * 0.001),
            "content_tokenized": _jieba_tokens(f"占位干扰内容第{i}号"),
            "canvas_file": f"a{i}.canvas",
        }
        for i in range(6)
    )

    db = lancedb.connect(str(tmp_path))
    for name, data in rows.items():
        db.create_table(name, data=data)
        try:  # FTS 索引尽力建 — 失败则 hybrid 降级 dense-only, 判据不受影响
            db.open_table(name).create_fts_index("content_tokenized", replace=True)
        except Exception:
            pass
    return db


def _make_client(tmp_path):
    """不带 vault override 的 client — 表名完全由 ContextVar 推导 (这是被测行为)。
    跳过 initialize() 的向量模型预载, 手动连 tmp 库。"""
    import lancedb
    from agentic_rag.clients.lancedb_client import LanceDBClient

    client = LanceDBClient(db_path=str(tmp_path), embedding_dim=_DIM)
    client._db = lancedb.connect(str(tmp_path))
    client._initialized = True
    return client


def _run_retrieve_lancedb(monkeypatch, tmp_path, *, vault: str, query: str):
    """以 vault 作用域跑真实 retrieve_lancedb 节点。

    返回 (doc_id, content, source_type) 三元组列表 —— source_type 来自
    metadata (expand_neighbors 标 neighbor_expansion), 活性门靠它区分
    「主检索带回」与「扩展带回」。
    """
    client = _make_client(tmp_path)
    monkeypatch.setattr(
        nodes, "_get_lancedb_client", AsyncMock(return_value=client), raising=True
    )
    monkeypatch.setattr(
        "agentic_rag.clients.lancedb_client.LanceDBClient.embed",
        AsyncMock(return_value=_vec(0.15)),
        raising=True,
    )

    token = _set_scope(f"vault:{vault}")
    try:
        state = {
            "messages": [{"role": "user", "content": query}],
            "canvas_file": None,
            "subject": None,
            "cross_subject": False,
        }
        update = asyncio.run(nodes.retrieve_lancedb(state, None))
    finally:
        _reset_scope(token)

    results = update.get("lancedb_results", [])
    return [
        (
            r.get("doc_id", ""),
            r.get("content", ""),
            (r.get("metadata") or {}).get("source_type", ""),
        )
        for r in results
    ]


class TestDualVaultIsolationOnTmpLanceDB:
    @pytest.fixture(autouse=True)
    def _seed_db(self, tmp_path):
        self.db = _seed_dual_vault_db(tmp_path)
        self.tmp_path = tmp_path

    def test_vault_a_query_has_zero_results_from_b(self, monkeypatch):
        pairs = _run_retrieve_lancedb(
            monkeypatch, self.tmp_path, vault="vault_a", query="贝尔不等式"
        )
        ids = [d for d, _, _ in pairs]
        assert not any(d.endswith("b_unique") for d in ids), (
            f"vault A 的检索结果混入了 vault B 独有笔记: {pairs} — 跨 vault 泄漏"
        )
        contents = " | ".join(c for _, c, _ in pairs)
        assert "贝尔不等式" not in contents, (
            f"vault A 检索到 B 的内容 (按 doc_id 之外的内容复核): {contents}"
        )

    def test_vault_a_positive_control_hits_a_unique(self, monkeypatch):
        """正向对照 — 隔离测试环境根本查不出数据时的假绿防线。"""
        pairs = _run_retrieve_lancedb(
            monkeypatch, self.tmp_path, vault="vault_a", query="红黑树"
        )
        ids = [d for d, _, _ in pairs]
        assert any(d.endswith("a_unique") for d in ids), f"正向对照失败: vault A 没查到自己的笔记 {pairs}"

    def test_same_name_note_returns_only_vault_a_version(self, monkeypatch):
        """同名不同内容笔记 — 防「全同组 fixture 假绿」: 隔离破了时
        B 表的同名版本会混进结果, content 断言立刻变红。"""
        pairs = _run_retrieve_lancedb(
            monkeypatch, self.tmp_path, vault="vault_a", query="递归"
        )
        contents = [c for _, c, _ in pairs]
        assert any("基础定义" in c for c in contents), (
            f"vault A 没查到自己的同名笔记 {pairs}"
        )
        assert not any("进阶定义" in c for c in contents), (
            f"vault A 的同名笔记检索混入了 vault B 版本: {pairs}"
        )

    def test_reverse_direction_vault_b_symmetric(self, monkeypatch):
        pairs = _run_retrieve_lancedb(
            monkeypatch, self.tmp_path, vault="vault_b", query="红黑树"
        )
        ids = [d for d, _, _ in pairs]
        assert not any(d.endswith("a_unique") for d in ids), f"反向泄漏: vault B 查到了 vault A 独有笔记 {pairs}"

    def test_shared_db_precondition_tables_coexist(self):
        """前置自证: 两张表物理共存于同一个库 — 排除「物理分库所以查不到」
        的平凡隔离, 证明的是命名空间隔离本身。"""
        names = set(self.db.table_names())
        assert {"vault_a_canvas_nodes", "vault_b_canvas_nodes", "vault_notes"} <= names

    def test_wikilink_neighbor_expansion_stays_in_vault(self, monkeypatch):
        """Codex round-1 BLOCKER-1 的门: 邻居扩展必须作用域内。

        a_unique 携带两个 wiki-link: [[递归基础]] (A 库内有对应板) 和
        [[b秘密板]] (只有裸 legacy 表有, 泄漏探针)。

        ⚠️ 活性判据 (Codex round-2 整改): 必须存在 metadata.source_type ==
        "neighbor_expansion" 的结果行 —— a_neighbor 本身也在主检索表里,
        只断言「结果含 a_neighbor」恒真 (把 expand_neighbors 换成恒等
        函数照样绿, Codex 实证)。只有扩展链活着才会产出 neighbor_
        expansion 标记, 该断言才能杀死「扩展静默失效」的假绿。
        """
        pairs = _run_retrieve_lancedb(
            monkeypatch, self.tmp_path, vault="vault_a", query="红黑树"
        )
        contents = " | ".join(c for _, c, _ in pairs)
        ids = [d for d, _, _ in pairs]
        sources = [s for _, _, s in pairs]

        assert any(s == "neighbor_expansion" for s in sources), (
            f"结果中没有任何 neighbor_expansion 标记行: {pairs} — "
            "wiki-link 邻居扩展链没活, 本门的隔离断言因此无效"
        )
        expanded = [c for _, c, s in pairs if s == "neighbor_expansion"]
        assert any("A 库版本" in c for c in expanded), (
            f"扩展带回的邻居不是 A 库版本: {expanded}"
        )
        assert not any(d.endswith("b_secret") for d in ids), (
            f"邻居扩展混入裸表 B 内容: {pairs} — 作用域旁路回来了"
        )
        assert "量子隐形传态" not in contents, (
            f"裸表内容按 doc_id 之外的复核也命中: {contents}"
        )

    @pytest.mark.xfail(
        reason=(
            "归 CARD-G4-4b: expand_neighbors 无 subject 过滤。已知边界 "
            "(Codex round-2 新发现 HIGH, 主干既有缺陷非本卡引入): "
            "expand_neighbors 不传 subject, LIKE 匹配整张 vault 表 — "
            "同 vault 内跨 subject 的邻居会被带回。收口面在 "
            "expand_neighbors 签名 (lancedb_client.py), 是 CARD-G4-4a 的 "
            "硬禁改面, 因此拆给 CARD-G4-4b; 4b 落地后本用例转正为门。"
            "strict=True: 意外修复 (XPASS) 视为失败, 提醒转正。"
        ),
        strict=True,
    )
    def test_neighbor_expansion_respects_subject_boundary(self, monkeypatch):
        """同 vault 跨 subject: math 请求的邻居不得带 physics 板内容。
        当前生产行为会带 (xfail 锁住已知缺陷, 防止无声回归为「更糟」)。"""
        import lancedb as _ldb

        # physics 板的机密只有 subject=physics 可见
        tbl = _ldb.connect(str(self.tmp_path)).open_table("vault_a_canvas_nodes")
        tbl.add(
            [
                {
                    "doc_id": "physics_secret",
                    "subject": "physics",
                    "content": "PHYSICS_SECRET 物理学机密内容",
                    "vector": _vec(0.30),
                    "content_tokenized": _jieba_tokens("PHYSICS_SECRET 物理学机密内容"),
                    "canvas_file": "物理板.canvas",
                }
            ]
        )
        try:
            tbl.create_fts_index("content_tokenized", replace=True)
        except Exception:
            pass

        # a_unique 加 [[物理板]] 链接 → 扩展会 LIKE 命中 physics 行
        _ldb.connect(str(self.tmp_path)).open_table(
            "vault_a_canvas_nodes"
        ).delete('doc_id == "a_unique"')
        tbl.add(
            [
                {
                    "doc_id": "a_unique",
                    "subject": "math",
                    "content": "红黑树旋转的颜色翻转规则 [[递归基础]] [[物理板]]",
                    "vector": _vec(0.10),
                    "content_tokenized": _jieba_tokens("红黑树旋转的颜色翻转规则"),
                    "canvas_file": "a.canvas",
                }
            ]
        )

        client = _make_client(self.tmp_path)
        monkeypatch.setattr(
            nodes, "_get_lancedb_client", AsyncMock(return_value=client), raising=True
        )
        monkeypatch.setattr(
            "agentic_rag.clients.lancedb_client.LanceDBClient.embed",
            AsyncMock(return_value=_vec(0.15)),
            raising=True,
        )

        # 请求作用域带 subject 二级 (贴生产: resolve_vault_scope(subject_id)
        # 注入 vault:<vid>:<subject>, 非基组 — Codex round-3 指出登记用例
        # 原来只注入基组, 形态低于生产)
        token = _set_scope("vault:vault_a:math")
        try:
            state = {
                "messages": [{"role": "user", "content": "红黑树"}],
                "canvas_file": None,
                "subject": "math",
                "cross_subject": False,
            }
            update = asyncio.run(nodes.retrieve_lancedb(state, None))
        finally:
            _reset_scope(token)

        contents = " | ".join(
            r.get("content", "") for r in update.get("lancedb_results", [])
        )
        assert "PHYSICS_SECRET" not in contents, (
            "math 请求的邻居扩展带入了 physics 板内容 (已知边界, 若此断言"
            "通过说明 expand 已收口 subject — 请把 xfail 转正为门)"
        )
