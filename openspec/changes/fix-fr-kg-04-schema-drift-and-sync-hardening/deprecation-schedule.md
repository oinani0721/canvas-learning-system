# Deprecation Schedule

FR-KG-04 Phase 7 Task 7.6 — tracks legacy code paths that are being removed
within this openspec change.

## CONNECTS_TO relationship write path

| Component | Status | Target version |
|-----------|--------|----------------|
| `canvas_service._sync_edge_to_neo4j` docstring | ⏳ marked DEPRECATED (2026-04-07) | removal in 0.X+1.0 |
| `neo4j_client.create_edge_relationship` (Cypher `MERGE ... CONNECTS_TO`) | ⏳ deprecated | removal in 0.X+1.0 |
| `neo4j_client.delete_edge_relationship` (Cypher `MATCH ...CONNECTS_TO... DELETE`) | ⏳ deprecated | removal in 0.X+1.0 |
| `neo4j_edge_client.py` CONNECTS_TO query helpers (lines 315, 324) | ⏳ deprecated | removal in 0.X+1.0 |
| `canvas_service.py:586,943` internal callers of `_sync_edge_to_neo4j` | ⏳ deprecated | removal in 0.X+1.0 |
| Historical `CONNECTS_TO` relationships in Neo4j | 🔶 migration | data cleanup `MATCH ()-[r:CONNECTS_TO]->() DELETE r` in removal commit |

## Replacement path

All edge writes that need to land in Neo4j MUST go through the
`/api/v1/sync/batch` endpoint:

1. Frontend pushes a `SyncOperation` to the Dexie `sync_outbox` table
2. `sync-engine.ts` drains the outbox and POSTs to the backend
3. `SyncService._upsert_edge` writes the canonical `CANVAS_EDGE` relationship
   with schema `{id, canvasId, label, createdAt, updatedAt}`
4. Downstream readers query `[r:CANVAS_EDGE]` exclusively

## Verification checklist before 0.X+1.0 removal

- [ ] `grep -rn "CONNECTS_TO" backend/app/` returns only comments or test fixtures
- [ ] No new reports of missing edges during the 1 minor version deprecation window
- [ ] All legacy `CONNECTS_TO` relationships in production Neo4j have been deleted
- [ ] Frontend writes 100% of edges through the SyncOperation path (no direct
      canvas_service calls that trigger `_sync_edge_to_neo4j`)
