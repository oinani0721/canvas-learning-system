"""Tests for MasteryStore Neo4j persistence layer."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.mastery_state import ConceptState
from app.services.mastery_store import MasteryStore


@pytest.fixture
def stub_neo4j():
    client = MagicMock()
    client.run_query = AsyncMock(return_value=None)
    return client

@pytest.fixture
def store(stub_neo4j):
    return MasteryStore(stub_neo4j)


class TestGetConcept:

    @pytest.mark.asyncio
    async def test_found(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(return_value=[
            {"props": {"mastery_concept_id": "c1", "mastery_topic": "T", "mastery_name": "N", "p_mastery": 0.5}}
        ])
        result = await store.get_concept("c1", group_id="test-group")
        assert result is not None
        assert result.concept_id == "c1"

    @pytest.mark.asyncio
    async def test_not_found(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(return_value=[])
        result = await store.get_concept("missing", group_id="test-group")
        assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(side_effect=RuntimeError("db error"))
        result = await store.get_concept("c1", group_id="test-group")
        assert result is None


class TestSaveConcept:

    @pytest.mark.asyncio
    async def test_save_calls_query(self, store, stub_neo4j):
        concept = ConceptState(concept_id="c1", topic="T", name="N")
        await store.save_concept(concept, group_id="test")
        stub_neo4j.run_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_exception_logged(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(side_effect=RuntimeError("write fail"))
        concept = ConceptState(concept_id="c1", topic="T", name="N")
        await store.save_concept(concept, group_id="test")


class TestGetAllConcepts:

    @pytest.mark.asyncio
    async def test_returns_list(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(return_value=[
            {"props": {"mastery_concept_id": "c1", "mastery_topic": "T", "mastery_name": "N1", "p_mastery": 0.3}},
            {"props": {"mastery_concept_id": "c2", "mastery_topic": "T", "mastery_name": "N2", "p_mastery": 0.7}},
        ])
        results = await store.get_all_concepts(group_id="test")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_empty_result(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(return_value=[])
        results = await store.get_all_concepts(group_id="test")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_exception_returns_empty(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(side_effect=RuntimeError("db error"))
        results = await store.get_all_concepts(group_id="test")
        assert len(results) == 0


class TestGetOrCreateConcept:

    @pytest.mark.asyncio
    async def test_existing_returned(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(return_value=[
            {"props": {"mastery_concept_id": "c1", "mastery_topic": "T", "mastery_name": "N", "p_mastery": 0.6}}
        ])
        result = await store.get_or_create_concept("c1", group_id="test")
        assert result.p_mastery == 0.6

    @pytest.mark.asyncio
    async def test_new_created(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(side_effect=[[], None])
        result = await store.get_or_create_concept(
            "new-c", topic="Search", name="DFS", group_id="test",
        )
        assert result.concept_id == "new-c"


class TestRecordEvents:

    @pytest.mark.asyncio
    async def test_record_interaction(self, store, stub_neo4j):
        await store.record_interaction_event("c1", grade=3, group_id="test")
        stub_neo4j.run_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_override(self, store, stub_neo4j):
        await store.record_override_event("c1", level="proficient", reason="manual", group_id="test")
        stub_neo4j.run_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_self_assess(self, store, stub_neo4j):
        await store.record_self_assess_event("c1", color="3", group_id="test")
        stub_neo4j.run_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_exception_does_not_raise(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(side_effect=RuntimeError("fail"))
        await store.record_interaction_event("c1", grade=1, group_id="test")


class TestFindConceptByName:

    @pytest.mark.asyncio
    async def test_found(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(return_value=[
            {"props": {"mastery_concept_id": "c1", "mastery_topic": "T", "mastery_name": "BFS", "p_mastery": 0.5}}
        ])
        result = await store.find_concept_by_name("BFS", group_id="test")
        assert result is not None
        assert result.name == "BFS"

    @pytest.mark.asyncio
    async def test_not_found(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(return_value=[])
        result = await store.find_concept_by_name("nonexistent", group_id="test")
        assert result is None


class TestGroupIdIsolation:

    @pytest.mark.asyncio
    async def test_different_groups_different_queries(self, store, stub_neo4j):
        stub_neo4j.run_query = AsyncMock(return_value=[])
        await store.get_concept("c1", group_id="group-A")
        await store.get_concept("c1", group_id="group-B")
        calls = stub_neo4j.run_query.call_args_list
        assert "group-A" in str(calls[0])
        assert "group-B" in str(calls[1])
