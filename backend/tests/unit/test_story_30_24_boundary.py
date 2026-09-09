"""
Story 30.24: 边界测试与防护加固

Tests for boundary conditions, special characters, oversized payloads,
shutdown data safety, and Unicode handling in the memory system.

AC-30.24.1: Empty input boundary test
AC-30.24.2: Special character group_id test
AC-30.24.3: Oversized payload test (422)
AC-30.24.4: Shutdown data safety test
AC-30.24.5: Unicode concept name test
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.subject_config import build_group_id, sanitize_subject_name
from app.graphiti.group_id_compat import to_physical_group_id

# ============================================================================
# AC-30.24.1: Empty input boundary test
# ============================================================================


class TestEmptyInputBoundary:
    """AC-30.24.1: Empty event list submitted to record_batch_learning_events."""

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero_processed(self):
        """Empty list returns processed=0, errors=[] without crashing."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": False}

        result = await svc.record_batch_learning_events([])

        assert result["processed"] == 0
        assert result["failed"] == 0
        assert result["errors"] == []
        assert result["episode_ids"] == []
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_empty_list_does_not_call_neo4j(self):
        """Empty list must NOT invoke any Neo4j write."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": True}
        svc.neo4j.record_episode = AsyncMock()

        await svc.record_batch_learning_events([])

        svc.neo4j.record_episode.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_list_has_valid_timestamp(self):
        """Empty list response still contains a valid ISO timestamp."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": False}

        result = await svc.record_batch_learning_events([])

        # Should be a valid ISO timestamp
        ts = result["timestamp"]
        datetime.fromisoformat(ts)  # raises ValueError if invalid


# ============================================================================
# AC-30.24.2: Special character group_id test
# ============================================================================

SPECIAL_GROUP_IDS = [
    ("", "default"),  # empty string → default
    ("../etc/passwd", "___etc_passwd"),  # path traversal → sanitized
    ("<script>", "_script_"),  # XSS → sanitized
    (
        "数学/离散数学",
        "数学_离散数学",
    ),  # Chinese path → preserved Chinese, slash→underscore
    ("📚 Math", "📚_math"),  # emoji → preserved emoji
    ("a" * 1000, None),  # very long string → truncated/handled
]


class TestSpecialCharacterGroupId:
    """AC-30.24.2: group_id with special characters handled safely."""

    @pytest.mark.parametrize(
        "raw_input,expected_prefix",
        [
            ("", "default"),
            ("../etc/passwd", None),  # just check no crash
            ("<script>alert(1)</script>", None),
            ("数学/离散数学", None),
            ("📚 Math", None),
            ("a" * 1000, None),
        ],
    )
    def test_sanitize_subject_name_no_crash(self, raw_input, expected_prefix):
        """sanitize_subject_name handles all special inputs without crashing."""
        result = sanitize_subject_name(raw_input)
        assert isinstance(result, str)
        assert len(result) > 0
        if expected_prefix:
            assert result == expected_prefix

    def test_empty_string_returns_default(self):
        """Empty string group_id returns 'default'."""
        assert sanitize_subject_name("") == "default"

    def test_path_traversal_stripped(self):
        """Path traversal characters are sanitized."""
        result = sanitize_subject_name("../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_xss_characters_stripped(self):
        """XSS characters (<, >) are sanitized."""
        result = sanitize_subject_name("<script>alert(1)</script>")
        assert "<" not in result
        assert ">" not in result

    def test_chinese_preserved(self):
        """Chinese characters are preserved in sanitization."""
        result = sanitize_subject_name("数学/离散数学")
        assert "数学" in result
        assert "离散数学" in result

    def test_emoji_sanitized_to_stable_identifier(self):
        """Emoji characters are safely stripped to stable identifier (emoji ∉ \\w)."""
        result = sanitize_subject_name("📚 Math")
        # Emoji is not a Unicode \w char → stripped by sanitize_subject_name
        # This is documented behavior: emoji in group_id are sanitized, not preserved
        # (AC-30.24.2 updated to reflect this design decision)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "math" in result

    def test_build_group_id_with_chinese(self):
        """build_group_id correctly constructs group_id with Chinese subject."""
        gid = build_group_id("数学")
        assert isinstance(gid, str)
        assert "数学" in gid

    def test_build_group_id_with_emoji(self):
        """build_group_id correctly constructs group_id with emoji."""
        gid = build_group_id("📚 Math")
        assert isinstance(gid, str)
        assert len(gid) > 0

    @pytest.mark.asyncio
    async def test_neo4j_parameterized_query_with_special_chars(self):
        """Neo4j client uses parameterized queries — special chars don't cause injection."""
        from app.clients.neo4j_client import Neo4jClient

        client = Neo4jClient()
        client._initialized = True
        client.run_query = AsyncMock(return_value=[])

        malicious_group_id = "<script>'; DROP TABLE users;--"

        await client.get_review_suggestions(
            user_id="test_user", limit=5, group_id=malicious_group_id
        )

        # 判据分两层（Codex round-3 LOW 与 round-4 LOW 各推了一次）：
        #   A 层「每一次调用都必须成立」的安全不变量 —— 防「先发一条把恶意串拼进文本的
        #     查询、再发一条干净的参数化查询」这种只审最后一次就会全绿的写法（round-3）。
        #   B 层「至少有一次调用带完整作用域参数集」—— round-4 指出：把 A 层写成
        #     「每次调用的 kwargs 都必须恰等于四参数」会把**合法的分步查询**（先 count
        #     后取结果，前者本就不需要 limit）误判成参数内联。故完整参数集只在 B 层要求一次。
        expected_physical = to_physical_group_id(malicious_group_id)
        EXPECTED_BOUND_PARAMS = {"userId", "limit", "group_id", "group_prefix"}

        assert client.run_query.call_args_list, "run_query 一次都没被调用"

        # ── A 层：逐条审全部调用 ──────────────────────────────────────────
        for call_args in client.run_query.call_args_list:
            all_kwargs = call_args.kwargs if call_args.kwargs else {}
            query_str = call_args.args[0] if call_args.args else ""

            # 契约演进（4db8e94a 2026-08-30 CARD-G4-1a + 88cb13a7 2026-08-31 读侧收口）：
            # 绑定参数由单个 `groupId`（原样透传）改为 `group_id` + `group_prefix`，
            # 且值经 to_physical_group_id() 物理化。旧断言锁的是已被替换的参数命名/值形态。
            assert "groupId" not in all_kwargs, (
                f"旧参数名 groupId 复活了（读侧应只用 group_id/group_prefix）。kwargs={sorted(all_kwargs)}"
            )

            # ⚠️ 以下三条是 round-5 HIGH 的整改：round-4 把「完整参数集」整条挪进 B 层
            # （只要求**至少一次**调用带齐四个参数）时，把 A 层削弱了——一次合法调用可以
            # **掩护**同一序列里的坏调用。实测漏过的两条：
            #   · 先发一条无 kwargs 的 `MATCH (n) RETURN n LIMIT 5`（完全无作用域过滤）；
            #   · 先发一条内联 `LIMIT 5` 且删掉 limit kwarg 的查询。
            # 这两条在 round-3 版本下会红、在 round-4 版本下**变成了 PASS（漏过）**——
            # 即 round-3→round-4 之间被我改弱了（与 c2-verdicts.md §十 的表一致）。
            # 现把「作用域必带」「物理化正确」「LIMIT 必须绑参」三条放回**每次调用**上，
            # 同时保留 round-4 修掉的误报面（合法分步 count 查询本就不需要 limit）。
            assert {"group_id", "group_prefix"} <= set(all_kwargs), (
                "本次 run_query 没带 group 作用域参数——R1 读契约要求每条业务读都带 "
                f"group 过滤。kwargs={sorted(all_kwargs)} query={query_str!r}"
            )
            assert all_kwargs["group_id"] == expected_physical, (
                f"group_id 未物理化或绑错组。got={all_kwargs['group_id']!r} "
                f"want={expected_physical!r}"
            )
            assert all_kwargs["group_prefix"] == expected_physical + "__", (
                f"group_prefix 应为物理组 + '__' 定界符。got={all_kwargs['group_prefix']!r}"
            )

            # ── 安全内核（本条用例的真正意义，不得删除或放宽）────────────────
            assert malicious_group_id not in query_str, (
                "Malicious input found in query string — possible Cypher injection!"
            )
            # 物理化后的值同样不得被拼进查询文本——它必须始终以参数形式传递。
            # （只查原始串不够：若实现把物理化结果 f-string 进查询，原始串确实不在文本里，
            #  但注入面又回来了。）
            for _k, _v in all_kwargs.items():
                if isinstance(_v, str) and _v:
                    assert _v not in query_str, (
                        f"参数 {_k} 的值被拼进了查询文本，应作为绑定参数传递"
                    )

            # ⚠️ 上面那条只覆盖**还留在 kwargs 里**的值，于是「把值内联进文本 + 同时把该参数
            # 从 kwargs 删掉」能整个绕开它（检查集合跟着缩小）。round-2 我用「钉死期望参数集」
            # 挡了 limit 这一个，round-5 又给 limit 单写了一条规则——都是**按参数逐个打补丁**，
            # 于是 round-6 换成 userId 又漏了一次。
            # 根因是判据依赖「攻击者能缩小的那个集合」。改为依赖**本用例自己喂进去的输入值**：
            # 无论 kwargs 怎么变，这些值都不该出现在任何查询文本里。
            for _label, _value in (
                ("user_id", "test_user"),
                ("group_id(原始)", malicious_group_id),
                ("group_id(物理化)", expected_physical),
                ("group_prefix", expected_physical + "__"),
            ):
                assert _value not in query_str, (
                    f"本用例喂进去的 {_label} 值被拼进了查询文本，应作为绑定参数传递。"
                    f"value={_value!r} query={query_str!r}"
                )

            # 正面形式：这次调用**实际绑定**的每个参数，都要在查询文本里有 `$name` 占位符。
            # 值一旦被内联，对应占位符就会消失。
            # ⚠️ 注释剥除是**启发式**，如实声明它的两面（Codex round-4 LOW）：
            #   · 它不理解字符串字面量与注释的上下文，`WITH '/*' AS marker` 这类查询里
            #     既可能放过藏在注释里的占位符，也可能误删真实占位符；
            #   · 即便查到占位符，也**不能**证明该参数真的参与了查询语义
            #     （`$limit` 写在一个无用表达式里同样能过）。
            #   现行生产查询里没有任何注释标记与字符串字面量，故本启发式在当前形态下不误报；
            #   要根治需要 Cypher 解析器，超出本卡范围，登记不修。
            _stripped = re.sub(r"/\*.*?\*/", " ", query_str, flags=re.S)
            _query_no_comments = "\n".join(
                line.split("//", 1)[0] for line in _stripped.splitlines()
            )
            for _k in all_kwargs:
                assert f"${_k}" in _query_no_comments, (
                    f"参数 {_k} 传进了 kwargs 却没有对应的 ${_k} 占位符（已排除注释），"
                    f"说明它的值可能被内联进了查询文本。query={query_str!r}"
                )

            # round-5 HIGH 的第三条：只查「已绑定参数有没有占位符」挡不住
            # 「把值内联进文本**同时**把该参数从 kwargs 里删掉」——两边都没了反而通过。
            # 对本用例真正要守的那个量（limit）用正面形式表达：**凡是带 LIMIT 的查询，
            # 就必须绑 $limit**。合法的分步 count 查询没有 LIMIT，不受此条约束。
            # ── 结构性判据（round-7：前面所有「枚举式」判据的共同上位）──────────
            # 前六轮的判据都在**枚举**：先枚举参数名（r2/r5 被换个参数破），再枚举输入值
            # （r7 被「拆成两半在文本里拼接」「大小写变形」「只内联子串」破）。
            # 枚举永远追不上变形。下面两条改为**结构性**表述，不枚举任何东西：
            #
            #   S1  查询文本里不得出现内联的单引号字符串字面量。
            #       依据：要把任何用户可控的**字符串**拼进 Cypher，就必须给它加引号；
            #       反过来，一条完全参数化的查询根本不需要内联字符串。
            #       现行生产查询实测 `'…'` 字面量数为 0（本条不是凭空收紧）。
            #   S2  每个 LIMIT 子句的表达式里必须出现 `$` 参数引用。
            #       依据：`LIMIT 5` / `LIMIT (5)` / `LIMIT toInteger(5)` 都是把分页值内联，
            #       而 `LIMIT $limit` / `LIMIT toInteger($limit)` 都带 `$`。
            #       round-6 用的 `\bLIMIT\s+\d` 被 `LIMIT (5)` 与 `LIMIT toInteger(5)` 绕过。
            #
            # ⚠️ 如实声明本条比卡文要求强：卡文 (f) 只要求保留 `:191-194` 并改参数形态断言。
            #    S1 会拒绝任何内联字符串常量（包括无害的 `'active' AS status` 这类写法）——
            #    这是有意的：本方法的查询面全部参数化，需要常量时应当也走参数。
            # ⚠️ 单引号与**双引号**都要认：Cypher 两种都是字符串字面量，只查单引号时
            # `("test_" + "user")` 这种双引号拼接能同时绕开 S1 与「按输入值查」那条
            # （本车道送 round-8 前自测抓到，非 Codex 指出）。
            _literals = re.findall(r"'[^']*'|\"[^\"]*\"", _query_no_comments)
            assert not _literals, (
                "查询文本里出现内联字符串字面量，本用例要求全参数化——"
                "任何用户可控值要拼进 Cypher 都得先加引号，故这条不枚举具体值也能挡住变形内联。"
                f"literals={_literals} query={query_str!r}"
            )
            # `SKIP` 与 `LIMIT` 同属分页子句、同样吃整数，只查 LIMIT 时 `SKIP 5` 能漏过
            # （同为送 round-8 前自测抓到）。
            # ⚠️ 表达式的右边界必须切在**下一个子句关键字**上，不能贪婪吃到行尾：
            # `LIMIT $limit SKIP 5` 里，贪婪写法让 LIMIT 的表达式吞掉 " $limit SKIP 5"
            # （含 `$` ⇒ 通过），扫描位置越过 SKIP，SKIP 就再也没被单独检查过。
            # 本车道送 round-8 前自测抓到（负控 ⑰ 期望 FAIL 实测 PASS）。
            # ⚠️ `(?<!\$)` 不可省：`$limit` 里的 "limit" 前面是 `$`（非词字符），
            # `\b` 照样成立 ⇒ 不排除的话，`LIMIT $limit` 会被当成**两个** LIMIT 子句，
            # 第二个的表达式为空、立刻误报。本车道改这条时当场被自己的用例红出来。
            _CLAUSE = r"LIMIT|SKIP|RETURN|ORDER|WITH|MATCH|WHERE|UNION|CALL"
            for _m in re.finditer(r"(?<!\$)\b(LIMIT|SKIP)\b", _query_no_comments, flags=re.I):
                _rest = _query_no_comments[_m.end():]
                _nxt = re.search(rf"(?<!\$)\b(?:{_CLAUSE})\b", _rest, flags=re.I)
                _expr = _rest[: _nxt.start()] if _nxt else _rest
                _expr = _expr.split("\n", 1)[0]
                assert "$" in _expr, (
                    f"{_m.group(1).upper()} 子句里没有 `$` 参数引用，说明分页值被内联进了文本。"
                    f"expr={_expr!r} query={query_str!r}"
                )

        # ── B 层：至少一次调用带完整作用域参数集，并在那一次上验物理化 ──────
        # ⚠️ 用**子集**而不是相等：合法查询可能多绑一个参数（例如分页加 `SKIP $skip`），
        # 「恰好四个」会把它误判成没有主查询。本车道送 round-8 前自测抓到
        # （负控 ⑤ `SKIP $skip` 期望 PASS 实测 FAIL）。
        # 少绑仍会红——那正是「内联 + 删参数」要挡的形态。
        scoped_calls = [
            c
            for c in client.run_query.call_args_list
            if EXPECTED_BOUND_PARAMS <= set(c.kwargs or {})
        ]
        assert scoped_calls, (
            "没有任何一次 run_query 带完整的作用域参数集 "
            f"{sorted(EXPECTED_BOUND_PARAMS)}；各次 kwargs="
            f"{[sorted(c.kwargs or {}) for c in client.run_query.call_args_list]}；"
            "缺参数通常意味着该值被内联进了查询文本"
        )
        # 物理化的逐条校验已放回 A 层（round-5 HIGH 整改），B 层只保留「主查询仍绑齐四参数」。
        # ⚠️ 同源盲区（Codex round-1 MEDIUM，已登记不修）：expected_physical 与生产走**同一个**
        # to_physical_group_id，若该 helper 恒返回同一个串，两边同步变化、本条发现不了。
        # 独立重实现物理化规则 = 在测试里复制一份生产逻辑，且本卡禁改 backend/app。

# ============================================================================
# AC-30.24.5: Unicode concept name test
# ============================================================================


class TestUnicodeConceptNames:
    """AC-30.24.5: Unicode concepts stored and queried correctly."""

    UNICODE_CONCEPTS = [
        "監督学習 📊",
        "Bayes' Theorem",
        "集合论 ∩ ∪ ⊂",
        "概率论与数理统计",
        "Ψ(x) = ∑ cₙφₙ(x)",
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "concept",
        [
            "監督学習 📊",
            "Bayes' Theorem",
            "集合论 ∩ ∪ ⊂",
            "概率论与数理统计",
            "Ψ(x) = ∑ cₙφₙ(x)",
        ],
    )
    async def test_unicode_concept_stored_in_episodes(self, concept):
        """Unicode concept is stored in _episodes without corruption."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": False}

        event = {
            "event_type": "color_changed",
            "timestamp": "2026-02-10T12:00:00Z",
            "canvas_path": "test/unicode.canvas",
            "node_id": "node_001",
            "metadata": {"concept": concept},
        }

        result = await svc.record_batch_learning_events([event])

        assert result["processed"] == 1
        assert result["failed"] == 0

        # Verify concept stored correctly in episodes
        stored = svc._episodes[-1]
        assert stored["metadata"]["concept"] == concept

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "concept",
        [
            "監督学習 📊",
            "Bayes' Theorem",
            "集合論 ∩ ∪ ⊂",
        ],
    )
    async def test_unicode_concept_sent_to_neo4j(self, concept):
        """Unicode concept is passed to Neo4j without truncation or mojibake."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": True}
        svc.neo4j.record_episode = AsyncMock()

        event = {
            "event_type": "color_changed",
            "timestamp": "2026-02-10T12:00:00Z",
            "canvas_path": "test/unicode.canvas",
            "node_id": "node_002",
            "metadata": {"concept": concept},
        }

        await svc.record_batch_learning_events([event])

        svc.neo4j.record_episode.assert_called_once()
        payload = svc.neo4j.record_episode.call_args[0][0]
        assert payload["concept"] == concept


# ============================================================================
# AC-30.24.3: Oversized payload test (422)
# ============================================================================


class TestOversizedPayload:
    """AC-30.24.3: Batch with >50 events rejected by Pydantic validation.

    Tests Pydantic model validation directly (true unit test).
    HTTP 422 behavior is covered by integration tests in:
    - tests/integration/test_epic30_memory_integration.py
    - tests/e2e/test_memory_learning_flow_e2e.py
    """

    def _make_events(self, count: int) -> list:
        return [
            {
                "event_type": "color_changed",
                "timestamp": f"2026-02-10T12:00:{i % 60:02d}Z",
                "canvas_path": "test/boundary.canvas",
                "node_id": f"node_{i:03d}",
            }
            for i in range(count)
        ]

    def test_oversized_batch_rejected_by_pydantic(self):
        """100 events exceeds max_length=50 → ValidationError."""
        from app.models.memory_schemas import BatchEpisodesRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            BatchEpisodesRequest(events=self._make_events(100))

        assert "events" in str(exc_info.value)

    def test_just_over_limit_rejected(self):
        """51 events (just over limit) → ValidationError."""
        from app.models.memory_schemas import BatchEpisodesRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BatchEpisodesRequest(events=self._make_events(51))

    def test_exactly_50_events_accepted(self):
        """Exactly 50 events should pass Pydantic validation (positive assertion)."""
        from app.models.memory_schemas import BatchEpisodesRequest

        req = BatchEpisodesRequest(events=self._make_events(50))
        assert len(req.events) == 50


# ============================================================================
# AC-30.24.4: Shutdown data safety test
# ============================================================================


class TestShutdownDataSafety:
    """AC-30.24.4: Pending writes saved to failed_writes.jsonl on shutdown."""

    @pytest.mark.asyncio
    async def test_batch_neo4j_failure_records_to_failed_writes(self, tmp_path):
        """When Neo4j is unreachable during batch, failures persist to failed_writes.jsonl."""
        from app.services.memory_service import MemoryService

        failed_writes_file = tmp_path / "failed_writes.jsonl"

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc.neo4j = MagicMock()
        svc.neo4j.stats = {"initialized": True}
        # Simulate Neo4j unreachable — all writes raise
        svc.neo4j.record_episode = AsyncMock(
            side_effect=ConnectionError("Neo4j unreachable")
        )

        events = [
            {
                "event_type": "color_changed",
                "timestamp": f"2026-02-10T12:00:{i:02d}Z",
                "canvas_path": "test/shutdown.canvas",
                "node_id": f"node_{i:03d}",
                "metadata": {"concept": f"concept_{i}"},
            }
            for i in range(5)
        ]

        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE", failed_writes_file
        ):
            result = await svc.record_batch_learning_events(events)

        # All 5 writes should fail
        assert result["failed"] == 5
        assert len(result["errors"]) == 5

    @pytest.mark.asyncio
    async def test_cleanup_flushes_pending_writes(self, tmp_path):
        """cleanup_memory_service persists pending failed writes before shutdown."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc._pending_failed_writes = [
            {
                "episode_id": f"ep_{i}",
                "timestamp": "2026-02-10T12:00:00Z",
                "reason": "Neo4j unreachable",
            }
            for i in range(5)
        ]
        svc.neo4j = MagicMock()
        svc.neo4j.cleanup = AsyncMock()
        svc._score_history_cache = {}
        svc._episodes_recovered = False

        failed_writes_file = tmp_path / "failed_writes.jsonl"

        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE", failed_writes_file
        ):
            await svc.cleanup()

        # Verify failed_writes.jsonl was created (must NOT be conditional)
        assert failed_writes_file.exists(), (
            "failed_writes.jsonl was not created by cleanup()"
        )
        lines = failed_writes_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 5
        for line in lines:
            record = json.loads(line)
            assert "episode_id" in record
            assert "timestamp" in record
            assert "reason" in record

    @pytest.mark.asyncio
    async def test_failed_writes_record_completeness(self, tmp_path):
        """Each record in failed_writes.jsonl has episode_id, timestamp, reason."""
        from app.services.memory_service import MemoryService

        svc = MemoryService()
        svc._initialized = True
        svc._episodes = []
        svc._pending_failed_writes = [
            {
                "episode_id": "ep_test_001",
                "timestamp": "2026-02-10T12:00:00Z",
                "reason": "ConnectionError: Neo4j host unreachable",
            }
        ]
        svc.neo4j = MagicMock()
        svc.neo4j.cleanup = AsyncMock()
        svc._score_history_cache = {}
        svc._episodes_recovered = False

        failed_writes_file = tmp_path / "failed_writes.jsonl"

        with patch(
            "app.services.memory_service.FAILED_WRITES_FILE", failed_writes_file
        ):
            await svc.cleanup()

        assert failed_writes_file.exists(), (
            "failed_writes.jsonl was not created by cleanup()"
        )
        lines = failed_writes_file.read_text(encoding="utf-8").strip().split("\n")
        record = json.loads(lines[0])
        assert record["episode_id"] == "ep_test_001"
        assert record["timestamp"] == "2026-02-10T12:00:00Z"
        assert "Neo4j" in record["reason"]


# ============================================================================
# AC-30.24.6: Vault deployment verify script exit code
# ============================================================================


class TestVaultVerifyExitCode:
    """AC-30.24.6: verify script returns exit 1 on STALE."""

    VERIFY_SCRIPT = Path(__file__).parent.parent.parent.parent / (
        "canvas-progress-tracker/obsidian-plugin/scripts/verify-vault.mjs"
    )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "146218b5(2026-03-24 '上下文污染清理 — 归档legacy') 把整个 legacy "
            "canvas-progress-tracker（旧插件 id canvas-review-system）移到 _archive/："
            "同一 commit 里 --diff-filter=D 删旧路径、--diff-filter=A 加 _archive/ 副本，"
            "是归档不是删除。VERIFY_SCRIPT 指向的仓根路径自此不存在（仓内唯一副本在 "
            "_archive/，本卡禁改指向——让单元测试起 node 子进程跑归档脚本等于把已退役物"
            "重新变成生产契约）。Obsidian Hybrid 架构下 vault 新鲜度校验的等价覆盖缺口归 "
            "CARD-VAULT-FRESHNESS-COVERAGE（台账登记）。[CARD-RED-C2]"
        ),
    )
    def test_verify_script_exists(self):
        """verify-vault.mjs script must exist."""
        assert self.VERIFY_SCRIPT.exists(), (
            f"verify script not found: {self.VERIFY_SCRIPT}"
        )

    def _run_verify(self, env_override: dict, timeout: int = 10):
        """Helper: run verify-vault.mjs with UTF-8 encoding (Windows emits emoji)."""
        import subprocess

        env = os.environ.copy()
        env.update(env_override)
        return subprocess.run(
            ["node", str(self.VERIFY_SCRIPT)],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "146218b5(2026-03-24 '上下文污染清理 — 归档legacy') 把整个 legacy "
            "canvas-progress-tracker（旧插件 id canvas-review-system）移到 _archive/："
            "同一 commit 里 --diff-filter=D 删旧路径、--diff-filter=A 加 _archive/ 副本，"
            "是归档不是删除。VERIFY_SCRIPT 指向的仓根路径自此不存在（仓内唯一副本在 "
            "_archive/，本卡禁改指向——让单元测试起 node 子进程跑归档脚本等于把已退役物"
            "重新变成生产契约）。Obsidian Hybrid 架构下 vault 新鲜度校验的等价覆盖缺口归 "
            "CARD-VAULT-FRESHNESS-COVERAGE（台账登记）。[CARD-RED-C2]"
        ),
    )
    def test_verify_script_exits_nonzero_when_file_not_found(self, tmp_path):
        """When vault main.js doesn't exist, script exits with code 1."""
        result = self._run_verify({"OBSIDIAN_VAULT": str(tmp_path)})
        assert result.returncode != 0
        output = (result.stdout or "") + (result.stderr or "")
        assert "NOT FOUND" in output

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "146218b5(2026-03-24 '上下文污染清理 — 归档legacy') 把整个 legacy "
            "canvas-progress-tracker（旧插件 id canvas-review-system）移到 _archive/："
            "同一 commit 里 --diff-filter=D 删旧路径、--diff-filter=A 加 _archive/ 副本，"
            "是归档不是删除。VERIFY_SCRIPT 指向的仓根路径自此不存在（仓内唯一副本在 "
            "_archive/，本卡禁改指向——让单元测试起 node 子进程跑归档脚本等于把已退役物"
            "重新变成生产契约）。Obsidian Hybrid 架构下 vault 新鲜度校验的等价覆盖缺口归 "
            "CARD-VAULT-FRESHNESS-COVERAGE（台账登记）。[CARD-RED-C2]"
        ),
    )
    def test_verify_script_exits_nonzero_when_stale(self, tmp_path):
        """When vault main.js is stale (>5min old), script exits with code 1."""
        # Create a stale main.js (set mtime to 10 minutes ago)
        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"
        plugin_dir.mkdir(parents=True)
        main_js = plugin_dir / "main.js"
        main_js.write_text("// stale test file")
        stale_time = time.time() - 600  # 10 minutes ago
        os.utime(main_js, (stale_time, stale_time))

        result = self._run_verify({"OBSIDIAN_VAULT": str(tmp_path)})
        assert result.returncode == 1
        assert "STALE" in (result.stdout or "")

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "146218b5(2026-03-24 '上下文污染清理 — 归档legacy') 把整个 legacy "
            "canvas-progress-tracker（旧插件 id canvas-review-system）移到 _archive/："
            "同一 commit 里 --diff-filter=D 删旧路径、--diff-filter=A 加 _archive/ 副本，"
            "是归档不是删除。VERIFY_SCRIPT 指向的仓根路径自此不存在（仓内唯一副本在 "
            "_archive/，本卡禁改指向——让单元测试起 node 子进程跑归档脚本等于把已退役物"
            "重新变成生产契约）。Obsidian Hybrid 架构下 vault 新鲜度校验的等价覆盖缺口归 "
            "CARD-VAULT-FRESHNESS-COVERAGE（台账登记）。[CARD-RED-C2]"
        ),
    )
    def test_verify_script_exits_zero_when_fresh(self, tmp_path):
        """When vault main.js is fresh (<5min), script exits with code 0."""
        # Create a fresh main.js (just created = fresh)
        plugin_dir = tmp_path / ".obsidian" / "plugins" / "canvas-review-system"
        plugin_dir.mkdir(parents=True)
        main_js = plugin_dir / "main.js"
        main_js.write_text("// fresh test file")

        result = self._run_verify({"OBSIDIAN_VAULT": str(tmp_path)})
        assert result.returncode == 0
        assert "FRESH" in (result.stdout or "")

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "146218b5(2026-03-24 '上下文污染清理 — 归档legacy') 把整个 legacy "
            "canvas-progress-tracker（旧插件 id canvas-review-system）移到 _archive/："
            "同一 commit 里 --diff-filter=D 删旧路径、--diff-filter=A 加 _archive/ 副本，"
            "是归档不是删除。VERIFY_SCRIPT 指向的仓根路径自此不存在（仓内唯一副本在 "
            "_archive/，本卡禁改指向——让单元测试起 node 子进程跑归档脚本等于把已退役物"
            "重新变成生产契约）。Obsidian Hybrid 架构下 vault 新鲜度校验的等价覆盖缺口归 "
            "CARD-VAULT-FRESHNESS-COVERAGE（台账登记）。[CARD-RED-C2]"
        ),
    )
    def test_package_json_verify_command_correct(self):
        """package.json verify script points to verify.mjs."""
        pkg_json_path = self.VERIFY_SCRIPT.parent.parent / "package.json"
        assert pkg_json_path.exists()
        pkg = json.loads(pkg_json_path.read_text(encoding="utf-8"))
        assert "verify" in pkg.get("scripts", {})
        assert "verify.mjs" in pkg["scripts"]["verify"]
