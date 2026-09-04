"""Tests for mastery API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.mastery_state import ConceptState, MasteryConfig
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_singletons():
    import app.api.v1.endpoints.mastery as mastery_mod

    mastery_mod._engine = None
    mastery_mod._store = None
    yield
    mastery_mod._engine = None
    mastery_mod._store = None


def _stub_store():
    store = MagicMock()
    store.get_all_concepts = AsyncMock(return_value=[])
    store.get_concept = AsyncMock(return_value=None)
    store.save_concept = AsyncMock(return_value=None)
    store.get_or_create_concept = AsyncMock(return_value=ConceptState(concept_id="test-c", topic="Search", name="BFS"))
    store.record_interaction_event = AsyncMock(return_value=None)
    store.record_override_event = AsyncMock(return_value=None)
    store.record_self_assess_event = AsyncMock(return_value=None)
    store.find_concept_by_name = AsyncMock(return_value=None)
    return store


@pytest.fixture
def patched_client():
    from app.services import mastery_engine as mastery_engine_mod
    from app.services.mastery_engine import load_mastery_config

    store = _stub_store()
    engine = mastery_engine_mod.MasteryEngine(load_mastery_config())

    from app.main import app

    from tests.support.lifespan import no_lifespan

    # CARD-TEST-isolate-lifespan: 端点的 _get_store() 委托的是
    # mastery_store.get_mastery_store() 单例（mastery_mod._store 是端点已不读的
    # 历史遗留），不打桩的话首个请求会经真 store 惰性初始化 Neo4j client
    # （health_check 连 NEO4J_URI）。engine 走 service 层惰性真引擎——它的
    # concept_to_response/apply_grade 等是真逻辑、无库依赖；只是把进程级单例
    # 置 None 并在退出时恢复，保证每个用例拿到干净的引擎、且不污染同会话
    # 后续测试（Codex round-1 MEDIUM 的保存/恢复要求）。
    saved_instance = mastery_engine_mod._engine_instance
    mastery_engine_mod._engine_instance = None
    try:
        with patch("app.api.v1.endpoints.mastery.get_mastery_store", return_value=store):
            with no_lifespan(app), TestClient(app) as client:
                yield client, store, engine
    finally:
        mastery_engine_mod._engine_instance = saved_instance


class TestBatchEndpoint:
    def test_empty_result(self, patched_client):
        client, store, _ = patched_client
        resp = client.get("/api/v1/mastery/batch?group_id=test")
        assert resp.status_code == 200
        body = resp.json()
        assert body["concepts"] == []

    def test_with_concepts(self, patched_client):
        client, store, _ = patched_client
        store.get_all_concepts = AsyncMock(
            return_value=[
                ConceptState(
                    concept_id="c1",
                    topic="Search",
                    name="BFS",
                    p_mastery=0.7,
                    interaction_count=5,
                    last_interaction_ts=datetime.now(timezone.utc),
                    fsrs_stability=100.0,
                ),
            ]
        )
        resp = client.get("/api/v1/mastery/batch?group_id=test")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["concepts"]) == 1


class TestGradeEndpoint:
    @pytest.mark.parametrize("grade", [1, 2, 3, 4])
    def test_valid_grades(self, patched_client, grade):
        client, store, _ = patched_client
        resp = client.post(
            "/api/v1/mastery/test-c/grade?group_id=test",
            json={"grade": grade},
        )
        assert resp.status_code == 200

    def test_grade_out_of_range(self, patched_client):
        client, _, _ = patched_client
        resp = client.post("/api/v1/mastery/test-c/grade?group_id=test", json={"grade": 5})
        assert resp.status_code == 422

    def test_grade_zero(self, patched_client):
        client, _, _ = patched_client
        resp = client.post("/api/v1/mastery/test-c/grade?group_id=test", json={"grade": 0})
        assert resp.status_code == 422

    def test_grade_updates_mastery(self, patched_client):
        client, store, _ = patched_client
        resp = client.post(
            "/api/v1/mastery/test-c/grade?group_id=test",
            json={"grade": 3, "topic": "Search", "name": "BFS"},
        )
        assert resp.status_code == 200
        store.save_concept.assert_called_once()


class TestOverrideEndpoint:
    @pytest.mark.parametrize("level", ["shaky", "developing", "proficient", "mastered"])
    def test_valid_levels(self, patched_client, level):
        client, _, _ = patched_client
        resp = client.post(
            "/api/v1/mastery/test-c/override?group_id=test",
            json={"level": level},
        )
        assert resp.status_code == 200

    def test_invalid_level(self, patched_client):
        client, _, _ = patched_client
        resp = client.post(
            "/api/v1/mastery/test-c/override?group_id=test",
            json={"level": "invalid"},
        )
        assert resp.status_code == 400


class TestDeleteOverrideEndpoint:
    def test_delete_existing(self, patched_client):
        client, store, _ = patched_client
        store.get_concept = AsyncMock(
            return_value=ConceptState(
                concept_id="test-c",
                topic="T",
                name="N",
                override_value=0.8,
                override_ts=datetime.now(timezone.utc),
            )
        )
        resp = client.delete("/api/v1/mastery/test-c/override?group_id=test")
        assert resp.status_code == 200
        body = resp.json()
        assert body["override_active"] is False

    def test_delete_not_found(self, patched_client):
        client, store, _ = patched_client
        store.get_concept = AsyncMock(return_value=None)
        resp = client.delete("/api/v1/mastery/test-c/override?group_id=test")
        assert resp.status_code == 404


class TestSelfAssessEndpoint:
    @pytest.mark.parametrize("color", ["1", "2", "3", "4", "5", "6"])
    def test_valid_colors(self, patched_client, color):
        client, _, _ = patched_client
        resp = client.post(
            "/api/v1/mastery/test-c/self-assess?group_id=test",
            json={"color": color},
        )
        assert resp.status_code == 200


class TestGraphitiSyncEndpoint:
    @pytest.mark.parametrize("signal", ["misconception", "problem_trap", "guided_thinking_correct"])
    def test_valid_signals(self, patched_client, signal):
        client, store, _ = patched_client
        resp = client.post(
            "/api/v1/mastery/graphiti-sync?group_id=test",
            json={"concept_name": "BFS", "signal": signal, "severity": 0.1},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["matched"] is True

    def test_invalid_signal(self, patched_client):
        client, _, _ = patched_client
        resp = client.post(
            "/api/v1/mastery/graphiti-sync?group_id=test",
            json={"concept_name": "BFS", "signal": "invalid_signal", "severity": 0.1},
        )
        assert resp.status_code == 400

    def test_existing_concept_matched(self, patched_client):
        client, store, _ = patched_client
        existing = ConceptState(
            concept_id="c1",
            topic="Search",
            name="BFS",
            p_mastery=0.8,
            interaction_count=5,
            last_interaction_ts=datetime.now(timezone.utc),
            fsrs_stability=100.0,
        )
        store.find_concept_by_name = AsyncMock(return_value=existing)
        resp = client.post(
            "/api/v1/mastery/graphiti-sync?group_id=test",
            json={"concept_name": "BFS", "signal": "misconception", "severity": 0.2},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["adjustment"]["old_p_mastery"] == 0.8
