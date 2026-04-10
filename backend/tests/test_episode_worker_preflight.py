"""L5-#1 regression: GraphitiEpisodeWorker.initialize_graphiti must pre-flight
Neo4j connectivity BEFORE constructing Graphiti, to prevent the
graphiti_core/driver/neo4j_driver.py:98 fire-and-forget task leak.

Bug history: graphiti-core v0.28.2's Neo4jDriver.__init__ contains:

    # graphiti_core/driver/neo4j_driver.py:91-101
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(self.build_indices_and_constraints())  # L98 - LEAKED
    except RuntimeError:
        pass

The created task is never awaited, never has a done-callback, and never has
an exception handler. When Neo4j is unreachable the task raises
ServiceUnavailable inside the loop, producing "Task exception was never
retrieved" stderr spam (1-3x per second).

Fix: probe connectivity with a bare neo4j AsyncGraphDatabase.driver before
instantiating Graphiti(...). If the probe fails, never construct Graphiti,
so the leaked task never starts.

Plan reference: Plan v25 Option C (L5-#1)
Pattern: neo4j-python-driver verify_connectivity() (official Bolt API)
"""

import asyncio

import pytest
from neo4j.exceptions import ServiceUnavailable

from app.services.episode_worker import GraphitiEpisodeWorker


@pytest.mark.asyncio
async def test_initialize_graphiti_preflight_fails(monkeypatch, tmp_path):
    """Unreachable Neo4j → return False, _graphiti stays None, Graphiti never instantiated."""
    fake_close_called = {"v": False}

    class _FakeDriver:
        async def verify_connectivity(self):
            raise ServiceUnavailable("simulated unreachable")

        async def close(self):
            fake_close_called["v"] = True

    def _fake_driver_factory(uri, auth):
        return _FakeDriver()

    import neo4j

    monkeypatch.setattr(
        neo4j.AsyncGraphDatabase, "driver", staticmethod(_fake_driver_factory)
    )

    instantiated = {"v": False}
    import app.services.episode_worker as ew

    real_graphiti = ew.Graphiti

    def _spy_graphiti(*a, **kw):
        instantiated["v"] = True
        return real_graphiti(*a, **kw)

    monkeypatch.setattr(ew, "Graphiti", _spy_graphiti)

    worker = GraphitiEpisodeWorker(
        maxsize=1, dead_letter_path=str(tmp_path / "dlq.jsonl")
    )
    ok = await worker.initialize_graphiti(
        neo4j_uri="bolt://localhost:1",
        neo4j_user="neo4j",
        neo4j_password="wrong",
        google_api_key="fake",
    )
    assert ok is False
    assert worker._graphiti is None
    assert instantiated["v"] is False, (
        "Graphiti must NOT be constructed when pre-flight fails"
    )
    assert fake_close_called["v"] is True, "temp_driver.close() must run in finally"


@pytest.mark.asyncio
async def test_initialize_graphiti_preflight_timeout(monkeypatch, tmp_path):
    """Slow Neo4j (>5s) → asyncio.TimeoutError → return False."""

    class _SlowDriver:
        async def verify_connectivity(self):
            await asyncio.sleep(10)

        async def close(self):
            pass

    import neo4j

    monkeypatch.setattr(
        neo4j.AsyncGraphDatabase,
        "driver",
        staticmethod(lambda uri, auth: _SlowDriver()),
    )

    worker = GraphitiEpisodeWorker(
        maxsize=1, dead_letter_path=str(tmp_path / "dlq2.jsonl")
    )
    ok = await worker.initialize_graphiti(
        neo4j_uri="bolt://localhost:1",
        neo4j_user="x",
        neo4j_password="x",
        google_api_key="fake",
    )
    assert ok is False
    assert worker._graphiti is None
