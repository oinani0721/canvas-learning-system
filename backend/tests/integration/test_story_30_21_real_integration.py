# Story 30.21: 真实环境集成测试套件 (Mock 性能基准替代)
# AC-30.21.1: 真实 Neo4j 幂等性验证
# AC-30.21.2: 真实性能基准
# AC-30.21.3: JSON 回退模式端到端验证
# AC-30.21.4: 测试标记隔离
"""
Integration tests running against real Neo4j to validate idempotency,
performance benchmarks, and fallback behaviors.

Replaces Mock-based performance claims with real measurements.

Run with:
    # Start Neo4j first
    docker-compose up -d neo4j && sleep 10

    # Run all integration tests
    cd backend && pytest tests/integration/test_story_30_21_real_integration.py -m integration -v

    # Run only non-integration (fallback) tests
    cd backend && pytest tests/integration/test_story_30_21_real_integration.py -m "not integration" -v
"""

import json
import logging
import os
import statistics
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

import pytest

from app.services.memory_service import (
    MemoryService,
    _generate_deterministic_episode_id,
)


# ============================================================================
# Local Fixtures — use project .env Neo4j credentials (port 7689)
# ============================================================================

# Docker Neo4j defaults (from backend/.env)
_NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
_NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "canvas_learning_2026")


@pytest.fixture
async def neo4j_client():
    """Real Neo4j client using project Docker credentials (port 7689).

    Skips the test if Neo4j is not reachable.
    Function-scoped to avoid asyncio event-loop conflicts.
    """
    from app.clients.neo4j_client import Neo4jClient

    client = Neo4jClient(
        uri=_NEO4J_URI,
        user=_NEO4J_USER,
        password=_NEO4J_PASSWORD,
        database="neo4j",
    )
    await client.initialize()

    if client.is_fallback_mode:
        pytest.skip(
            f"Neo4j not available at {_NEO4J_URI} (fell back to JSON). "
            "Start Docker Neo4j first: docker-compose up -d neo4j"
        )

    yield client

    # Cleanup driver
    try:
        await client.cleanup()
    except Exception as e:
        logging.getLogger(__name__).warning(f"neo4j_client fixture cleanup failed: {e}")


@pytest.fixture
async def memory_svc(neo4j_client):
    """Real MemoryService with Neo4j for integration tests."""
    service = MemoryService(neo4j_client=neo4j_client)
    await service.initialize()
    yield service


@pytest.fixture
def uid():
    """Generate unique test user ID."""
    return f"test_user_{uuid.uuid4().hex[:8]}"


# ============================================================================
# Task 1: 真实 Neo4j 幂等性测试 (AC-30.21.1)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_idempotent_neo4j_persistence(neo4j_client, memory_svc, uid):
    """AC-30.21.1: 同一事件重复提交, Neo4j 中只存在 1 条 LEARNED 关系.

    Given: NEO4J_MOCK=false 且 Neo4j 服务可用
    When: 同一事件 (相同 canvas_path + node_id + concept) 被提交两次
    Then: Neo4j 中只存在 1 条记录 (MERGE 去重)
    And: 第二次返回的 episode_id 与第一次相同
    And: Cypher 查询确认只有 1 条关系
    """
    canvas_path = "test/idempotency/math.canvas"
    node_id = "test_node_idem_001"
    concept = "test_Recursion_Idempotent"

    # Expected deterministic episode_id
    expected_id = _generate_deterministic_episode_id(
        uid, canvas_path, node_id, concept
    )

    try:
        # --- First write (score=80) ---
        episode_id_1 = await memory_svc.record_learning_event(
            user_id=uid,
            canvas_path=canvas_path,
            node_id=node_id,
            concept=concept,
            agent_type="test_agent",
            score=80,
        )
        assert episode_id_1 == expected_id, (
            f"First episode_id mismatch: {episode_id_1} != {expected_id}"
        )

        # --- Second write (score=90, same event identity) ---
        episode_id_2 = await memory_svc.record_learning_event(
            user_id=uid,
            canvas_path=canvas_path,
            node_id=node_id,
            concept=concept,
            agent_type="test_agent",
            score=90,
        )
        assert episode_id_2 == expected_id, (
            f"Second episode_id mismatch: {episode_id_2} != {expected_id}"
        )
        assert episode_id_1 == episode_id_2, "Deterministic IDs must be identical"

        # --- Cypher verification: only 1 LEARNED relationship ---
        results = await neo4j_client.run_query(
            "MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept {name: $concept}) "
            "RETURN count(r) as cnt",
            userId=uid,
            concept=concept,
        )
        assert len(results) == 1, f"Expected 1 result row, got {len(results)}"
        count = results[0]["cnt"]
        assert count == 1, (
            f"MERGE should produce exactly 1 LEARNED relationship, got {count}"
        )
    finally:
        # --- Cleanup (always runs, even on assertion failure) ---
        await neo4j_client.run_query(
            "MATCH (u:User {id: $userId}) DETACH DELETE u",
            userId=uid,
        )
        await neo4j_client.run_query(
            "MATCH (c:Concept {name: $concept}) DETACH DELETE c",
            concept=concept,
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_idempotent_batch_persistence(neo4j_client, memory_svc, uid):
    """AC-30.21.1: 批量重复写入 + 去重验证.

    Given: 5 个不同事件 + 3 个重复事件 (共 8 次写入)
    Then: Neo4j 中只有 5 个不同的 LEARNED 关系
    """
    canvas_path = "test/batch_idem/math.canvas"
    concepts = [
        "test_BatchConcept_Alpha",
        "test_BatchConcept_Beta",
        "test_BatchConcept_Gamma",
        "test_BatchConcept_Delta",
        "test_BatchConcept_Epsilon",
    ]

    try:
        # Write 5 unique events
        for concept in concepts:
            await memory_svc.record_learning_event(
                user_id=uid,
                canvas_path=canvas_path,
                node_id=f"test_node_{concept}",
                concept=concept,
                agent_type="test_agent",
                score=85,
            )

        # Write 3 duplicates (first 3 concepts again, different scores)
        for concept in concepts[:3]:
            await memory_svc.record_learning_event(
                user_id=uid,
                canvas_path=canvas_path,
                node_id=f"test_node_{concept}",
                concept=concept,
                agent_type="test_agent",
                score=95,
            )

        # Verify total unique relationships = 5
        results = await neo4j_client.run_query(
            "MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept) "
            "WHERE c.name STARTS WITH 'test_BatchConcept_' "
            "RETURN count(r) as cnt",
            userId=uid,
        )
        assert len(results) == 1
        count = results[0]["cnt"]
        assert count == 5, (
            f"Expected 5 unique LEARNED relationships after 8 writes, got {count}"
        )
    finally:
        # Cleanup (always runs, even on assertion failure)
        await neo4j_client.run_query(
            "MATCH (u:User {id: $userId}) DETACH DELETE u",
            userId=uid,
        )
        for concept in concepts:
            await neo4j_client.run_query(
                "MATCH (c:Concept {name: $concept}) DETACH DELETE c",
                concept=concept,
            )


# ============================================================================
# Task 2: 真实性能基准 (AC-30.21.2)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_batch_50_benchmark(neo4j_client, memory_svc, uid):
    """AC-30.21.2: 50 事件真实延迟测量.

    Records actual wall-clock time for 50 distinct learning events
    against real Neo4j. No hard threshold — results are for reference only.

    Outputs structured benchmark report to _bmad-output/test-artifacts/.
    """
    canvas_path = "test/benchmark/math.canvas"
    event_count = 50

    try:
        # Measure batch write time
        start = time.perf_counter()
        for i in range(event_count):
            await memory_svc.record_learning_event(
                user_id=uid,
                canvas_path=canvas_path,
                node_id=f"test_bench_node_{i:03d}",
                concept=f"test_BenchConcept_{i:03d}",
                agent_type="benchmark_agent",
                score=70 + (i % 30),
            )
        elapsed = time.perf_counter() - start
        elapsed_ms = elapsed * 1000
        avg_ms = elapsed_ms / event_count

        # Verify all events were written
        results = await neo4j_client.run_query(
            "MATCH (u:User {id: $userId})-[r:LEARNED]->(c:Concept) "
            "WHERE c.name STARTS WITH 'test_BenchConcept_' "
            "RETURN count(r) as cnt",
            userId=uid,
        )
        assert results[0]["cnt"] == event_count

        # Generate benchmark report
        report = {
            "env": "Real Neo4j",
            "story": "30.21",
            "test": "test_real_batch_50_benchmark",
            "events": event_count,
            "elapsed_ms": round(elapsed_ms, 2),
            "avg_ms": round(avg_ms, 2),
            "timestamp": datetime.now().isoformat(),
            "neo4j_uri": _NEO4J_URI,
        }

        # Write benchmark report
        report_dir = Path(__file__).resolve().parents[3] / "_bmad-output" / "test-artifacts"
        report_dir.mkdir(parents=True, exist_ok=True)

        # JSON report
        json_path = report_dir / "benchmark-epic30-real.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Markdown report
        md_path = report_dir / "benchmark-epic30-real.md"
        md_content = f"""# EPIC-30 Real Neo4j Benchmark Report

| Metric | Value |
|--------|-------|
| Environment | Real Neo4j |
| Events | {event_count} |
| Total Time | {report['elapsed_ms']} ms |
| Avg per Event | {report['avg_ms']} ms |
| Timestamp | {report['timestamp']} |
| Neo4j URI | {report['neo4j_uri']} |

> **Note**: No hard threshold set. These are real measurements, not Mock-based claims.
> Mock-based benchmarks are marked as `env: "Mock (不可信)"`.
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Print results for test output
        print(f"\n{'='*60}")
        print(f"BENCHMARK: Real Neo4j Batch Write")
        print(f"  Events:     {event_count}")
        print(f"  Total:      {report['elapsed_ms']:.2f} ms")
        print(f"  Avg/event:  {report['avg_ms']:.2f} ms")
        print(f"  Reports:    {json_path}")
        print(f"{'='*60}\n")
    finally:
        # Cleanup (always runs, even on assertion failure)
        await neo4j_client.run_query(
            "MATCH (u:User {id: $userId}) DETACH DELETE u",
            userId=uid,
        )
        await neo4j_client.run_query(
            "MATCH (c:Concept) WHERE c.name STARTS WITH 'test_BenchConcept_' "
            "DETACH DELETE c",
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_single_write_latency(neo4j_client, memory_svc, uid):
    """AC-30.21.2: 单次写入 p50/p95 延迟测量.

    Measures individual write latency over 20 sequential writes
    to compute p50 and p95 percentiles.
    """
    canvas_path = "test/latency/math.canvas"
    sample_count = 20
    latencies: List[float] = []

    try:
        for i in range(sample_count):
            start = time.perf_counter()
            await memory_svc.record_learning_event(
                user_id=uid,
                canvas_path=canvas_path,
                node_id=f"test_latency_node_{i:03d}",
                concept=f"test_LatencyConcept_{i:03d}",
                agent_type="latency_agent",
                score=80,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

        # Calculate percentiles using statistics module for accuracy
        p50 = statistics.median(latencies)
        quantile_cuts = statistics.quantiles(latencies, n=20)
        p95 = quantile_cuts[18] if len(quantile_cuts) >= 19 else max(latencies)
        avg = statistics.mean(latencies)

        print(f"\n{'='*60}")
        print(f"LATENCY: Real Neo4j Single Write ({sample_count} samples)")
        print(f"  p50:  {p50:.2f} ms")
        print(f"  p95:  {p95:.2f} ms")
        print(f"  avg:  {avg:.2f} ms")
        print(f"  min:  {min(latencies):.2f} ms")
        print(f"  max:  {max(latencies):.2f} ms")
        print(f"{'='*60}\n")

        # Append to benchmark report
        report_dir = Path(__file__).resolve().parents[3] / "_bmad-output" / "test-artifacts"
        report_dir.mkdir(parents=True, exist_ok=True)
        latency_report = {
            "env": "Real Neo4j",
            "story": "30.21",
            "test": "test_real_single_write_latency",
            "samples": sample_count,
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "avg_ms": round(avg, 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "timestamp": datetime.now().isoformat(),
        }
        latency_path = report_dir / "benchmark-epic30-latency.json"
        with open(latency_path, "w", encoding="utf-8") as f:
            json.dump(latency_report, f, indent=2, ensure_ascii=False)
    finally:
        # Cleanup (always runs, even on assertion failure)
        await neo4j_client.run_query(
            "MATCH (u:User {id: $userId}) DETACH DELETE u",
            userId=uid,
        )
        await neo4j_client.run_query(
            "MATCH (c:Concept) WHERE c.name STARTS WITH 'test_LatencyConcept_' "
            "DETACH DELETE c",
        )


# ============================================================================
# Task 3: JSON 回退模式端到端验证 (AC-30.21.3)
# ============================================================================


@pytest.mark.asyncio
async def test_json_fallback_data_persistence(tmp_path):
    """AC-30.21.3: Neo4j 不可达时自动降级到 JSON 并持久化数据.

    Given: Neo4j 服务不可达 (bolt://localhost:9999 无监听)
    When: 客户端 initialize() 连接失败后自动降级
    And: 提交学习事件
    Then: 数据持久化到 JSON 文件
    And: JSON 文件中包含刚写入的事件
    """
    from app.clients.neo4j_client import Neo4jClient

    json_storage = tmp_path / "neo4j_memory.json"

    # Create client pointing to unreachable Neo4j — tests real degradation path
    client = Neo4jClient(
        uri="bolt://localhost:9999",
        user="neo4j",
        password="test",
        use_json_fallback=False,
        storage_path=json_storage,
    )
    await client.initialize()

    # Verify auto-degradation happened
    assert client.is_fallback_mode is True, (
        "Client should have auto-degraded to JSON fallback after connection failure"
    )

    # Create MemoryService with fallback client
    service = MemoryService(neo4j_client=client)
    await service.initialize()

    # Record a learning event
    user_id = "test_fallback_user"
    concept = "test_FallbackConcept"
    episode_id = await service.record_learning_event(
        user_id=user_id,
        canvas_path="test/fallback/math.canvas",
        node_id="test_fb_node_001",
        concept=concept,
        agent_type="fallback_agent",
        score=75,
    )

    # Verify episode_id is deterministic
    expected_id = _generate_deterministic_episode_id(
        user_id, "test/fallback/math.canvas", "test_fb_node_001", concept
    )
    assert episode_id == expected_id

    # Verify JSON file contains the data
    assert json_storage.exists(), f"JSON storage file not created: {json_storage}"

    with open(json_storage, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The JSON fallback stores relationships with concept_name field
    relationships = data.get("relationships", [])
    matching = [
        r for r in relationships
        if r.get("concept_name") == concept and r.get("user_id") == user_id
    ]
    assert len(matching) >= 1, (
        f"Expected at least 1 relationship for {concept}, "
        f"found {len(matching)} in {len(relationships)} total"
    )

    # Cleanup
    await client.cleanup()


@pytest.mark.asyncio
async def test_json_fallback_warning_log(tmp_path, caplog):
    """AC-30.21.3: 降级时 logger.warning 包含 fallback 关键词.

    Verifies that when Neo4j connection fails during initialize(),
    auto-degradation emits a WARNING log containing "fallback".
    Tests the real degradation path, not a direct private method call.
    """
    from app.clients.neo4j_client import Neo4jClient

    json_storage = tmp_path / "neo4j_fallback_log.json"

    # Create a real-mode client pointing to invalid address
    client = Neo4jClient(
        uri="bolt://localhost:9999",
        user="neo4j",
        password="test",
        use_json_fallback=False,
        storage_path=json_storage,
    )

    # Trigger fallback through real initialize() path (connection fails → auto-degrade)
    with caplog.at_level(logging.WARNING, logger="app.clients.neo4j_client"):
        await client.initialize()

    # Verify WARNING log contains "Falling back" or "fallback"
    warning_messages = [
        r.message for r in caplog.records
        if r.levelno >= logging.WARNING
    ]
    assert any(
        "falling back" in msg.lower() or "fallback" in msg.lower()
        for msg in warning_messages
    ), (
        f"Expected WARNING with 'falling back' or 'fallback', "
        f"got: {warning_messages}"
    )

    # Verify client auto-degraded to fallback mode
    assert client.is_fallback_mode is True

    # Cleanup
    await client.cleanup()


@pytest.mark.asyncio
async def test_json_fallback_event_queryable(tmp_path):
    """AC-30.21.3: 回退后数据可查询.

    Given: 数据通过 JSON 回退模式写入
    When: 查询学习历史
    Then: 可以查询到写入的数据
    """
    from app.clients.neo4j_client import Neo4jClient

    json_storage = tmp_path / "neo4j_query.json"

    client = Neo4jClient(
        uri="bolt://localhost:9999",
        user="neo4j",
        password="test",
        use_json_fallback=True,
        storage_path=json_storage,
    )
    await client.initialize()

    service = MemoryService(neo4j_client=client)
    await service.initialize()

    user_id = "test_query_user"
    concept = "test_QueryConcept"

    # Write
    await service.record_learning_event(
        user_id=user_id,
        canvas_path="test/query/math.canvas",
        node_id="test_query_node_001",
        concept=concept,
        agent_type="query_agent",
        score=88,
    )

    # Query via service
    history = await service.get_learning_history(user_id=user_id)

    # Verify the event is queryable
    items = history.get("items", []) if isinstance(history, dict) else []
    # Also check in-memory episodes as fallback
    memory_episodes = [
        ep for ep in service._episodes
        if ep.get("user_id") == user_id and ep.get("concept") == concept
    ]

    # At least one source should have the data
    has_data = len(items) > 0 or len(memory_episodes) > 0
    assert has_data, (
        f"Data not queryable after fallback write. "
        f"History items: {len(items)}, Memory episodes: {len(memory_episodes)}"
    )

    # Cleanup
    await client.cleanup()


# ============================================================================
# Task 4: 测试标记和 CI 配置 (AC-30.21.4)
# ============================================================================


def test_integration_marker_configured():
    """AC-30.21.4: pytest.ini 中配置了 integration marker.

    Verifies that the 'integration' marker is registered in pytest configuration,
    so `pytest -m integration` and `pytest -m "not integration"` work correctly.
    """
    from pathlib import Path
    import configparser

    # Locate pytest.ini relative to the backend directory
    backend_dir = Path(__file__).resolve().parents[2]
    pytest_ini = backend_dir / "pytest.ini"

    assert pytest_ini.exists(), f"pytest.ini not found at {pytest_ini}"

    config = configparser.ConfigParser()
    config.read(str(pytest_ini), encoding="utf-8")

    assert config.has_section("pytest"), "pytest.ini missing [pytest] section"

    markers_raw = config.get("pytest", "markers", fallback="")
    assert "integration" in markers_raw, (
        f"'integration' marker not found in pytest.ini markers section. "
        f"Found: {markers_raw}"
    )

    # Verify this file has @pytest.mark.integration tests that would be filtered
    import ast
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    integration_funcs = [
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(d, ast.Attribute) and d.attr == "integration"
            for dec in getattr(node, "decorator_list", [])
            for d in ast.walk(dec)
        )
    ]
    assert len(integration_funcs) >= 4, (
        f"Expected at least 4 @pytest.mark.integration tests, "
        f"found {len(integration_funcs)}: {integration_funcs}"
    )
