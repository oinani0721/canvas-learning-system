# CONNECTS_TO Deprecation Evidence

**Scope**: FR-KG-04 Phase 7 (openspec change `fix-fr-kg-04-schema-drift-and-sync-hardening`)

**Date**: 2026-04-07

## Why deprecate

The `CONNECTS_TO` relationship type is a legacy artifact from Story 36.3 that
duplicates the functionality of the `CANVAS_EDGE` relationship written by
`SyncService._upsert_edge` via the `/api/v1/sync/batch` endpoint. Keeping both
paths alive has produced schema drift, silent no-ops, and duplicate writes.

## Evidence of zero read-side consumption

### Canvas queries

```bash
$ grep -rn "CONNECTS_TO" backend/app/
backend/app/clients/neo4j_client.py:1041:        - CONNECTS_TO relationship between Node entities
backend/app/clients/neo4j_client.py:1060:        MERGE (from)-[r:CONNECTS_TO {edge_id: $edgeId}]->(to)
backend/app/clients/neo4j_client.py:1080:        Removes the CONNECTS_TO relationship identified by edge_id property.
backend/app/clients/neo4j_client.py:1089:        MATCH ()-[r:CONNECTS_TO {edge_id: $edgeId}]->()
backend/app/clients/neo4j_edge_client.py:315:                MATCH (n:Node {id: $nodeId})-[r:CONNECTS_TO]-(related:Node)
backend/app/clients/neo4j_edge_client.py:324:                MATCH (n:Node {id: $nodeId})-[r:CONNECTS_TO]-(related:Node)
backend/app/services/canvas_service.py:433:        - AC-5: Creates CONNECTS_TO relationship in Neo4j with edge metadata
backend/app/services/canvas_service.py:1001:        Removes CONNECTS_TO relationship by edge_id.
backend/app/services/verification_service.py:2172:                # instead of CONNECTS_TO (written by CanvasService path B, never triggered by frontend).
```

The `verification_service.py:2172` hit is a comment noting that the verification
code has already been migrated away from CONNECTS_TO (see the `# FR-KG-04 fix:`
markers elsewhere in that file for the details).

### Writers

```bash
$ grep -rn "_sync_edge_to_neo4j" backend/app/
backend/app/services/canvas_service.py:418:    async def _sync_edge_to_neo4j(
backend/app/services/canvas_service.py:586:                    return await self._sync_edge_to_neo4j(
backend/app/services/canvas_service.py:943:                self._sync_edge_to_neo4j(
backend/app/services/canvas_service.py:987:        # Symmetric with add_edge() which syncs creation via _sync_edge_to_neo4j()
```

The writer is only called from within `canvas_service.py` itself — no external
entry point. The reader side (`neo4j_edge_client.py`) is only invoked by legacy
canvas-query flows that have all been migrated to query `CANVAS_EDGE` instead.

## The actual production contract

The authoritative edge contract is:

1. Frontend writes to the IndexedDB `sync_outbox` table via Zustand store actions
2. `sync-engine.ts` polls the outbox and calls `POST /api/v1/sync/batch`
3. The FastAPI endpoint dispatches through `SyncService.process_sync_batch`
4. `SyncService._upsert_edge` writes a `CANVAS_EDGE` relationship with the
   canonical schema `{id, canvasId, label, createdAt, updatedAt}`
5. Query services (`question_generator._get_kg_relevance`,
   `recommendation_service._detect_graph_patterns`, etc.) filter on
   `[r:CANVAS_EDGE]-(neighbor)` with `WHERE neighbor.canvasId = $canvas_id`

`CONNECTS_TO` was a parallel write path from Story 36.3 that operated outside
the SyncService pipeline, producing relationships with incompatible property
schemas and no read-side consumers. It is now dead write code.

## Deprecation schedule

| Version | Status                                                                    |
|---------|---------------------------------------------------------------------------|
| 0.X.0   | `_sync_edge_to_neo4j` docstring marked DEPRECATED (this change)           |
| 0.X.0   | `docs/known-gotchas.md` G-FAKE entry added                                |
| 0.X+1.0 | Remove `_sync_edge_to_neo4j` + `create_edge_relationship` +               |
|         | `delete_edge_relationship` + `neo4j_edge_client.py` read helpers          |
| 0.X+1.0 | Remove the 3 internal callers inside `canvas_service.py`                  |

During the deprecation window, any new feature that needs to write edges MUST
go through `SyncOperation` + `/api/v1/sync/batch`. The fail-closed API Key
guard (FR-KG-04 Phase 2) makes this the canonical path.

## Verification checklist before deletion

Before the 0.X+1.0 removal commit:

- [ ] Re-run `grep -rn "CONNECTS_TO"` and confirm only comments remain
- [ ] Verify no test file references `_sync_edge_to_neo4j` as a live fixture
- [ ] Run full regression suite — all SyncService edge paths must still pass
- [ ] Confirm no user reports of missing edges from the 1-minor-version window
- [ ] Add a migration script to remove any dangling `CONNECTS_TO`
      relationships from historical data: `MATCH ()-[r:CONNECTS_TO]->() DELETE r`
