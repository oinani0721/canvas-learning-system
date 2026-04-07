// Migration 002: Unify CanvasNode primary key from {uuid} to {id}
//
// FR-KG-04 Phase 1 Task 1.2:
// Historical exam_service_ext.py wrote CanvasNode with {uuid: $node_id, canvas_id: $canvas_id}
// (snake_case), while SyncService writes {id: $entity_id, canvasId: $canvas_id} (camelCase).
// This split caused question_generator._get_kg_relevance to silently return 0.5 forever.
//
// This migration:
//   1. Inspects how many legacy uuid-based nodes exist (DRY RUN)
//   2. Backfills n.id from n.uuid where missing
//   3. Renames n.canvas_id → n.canvasId
//   4. Removes the legacy n.uuid property after backfill
//
// Idempotency: COALESCE + IS NOT NULL guards make repeated runs safe.

// === STEP 0: DRY RUN — count legacy nodes (Task 1.1) ===
//
// Run this query first to assess scope:
//
//   MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL RETURN count(n) AS legacy_count;
//
// If legacy_count is 0, the rest of this migration is a no-op.
// If legacy_count > 0, proceed with the SET/REMOVE statements below.

// === STEP 1: Backfill n.id from n.uuid where id is missing ===
MATCH (n:CanvasNode)
WHERE n.uuid IS NOT NULL AND n.id IS NULL
SET n.id = n.uuid;

// === STEP 2: Backfill n.canvasId from n.canvas_id where canvasId is missing ===
MATCH (n:CanvasNode)
WHERE n.canvas_id IS NOT NULL AND n.canvasId IS NULL
SET n.canvasId = n.canvas_id;

// === STEP 3: Remove legacy properties (uuid + canvas_id) ===
//
// Only run after STEP 1 + STEP 2 confirmed all rows have id + canvasId.
// Verify with:
//
//   MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL AND n.id IS NULL RETURN count(n);
//   -- expected: 0
//
MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL REMOVE n.uuid;
MATCH (n:CanvasNode) WHERE n.canvas_id IS NOT NULL REMOVE n.canvas_id;

// === STEP 4: Verify migration ===
//
//   MATCH (n:CanvasNode) WHERE n.uuid IS NOT NULL RETURN count(n) AS uuid_remaining;
//   MATCH (n:CanvasNode) WHERE n.canvas_id IS NOT NULL RETURN count(n) AS snake_remaining;
//   -- both expected: 0
//
//   MATCH (n:CanvasNode) WHERE n.id IS NULL RETURN count(n) AS missing_id;
//   MATCH (n:CanvasNode) WHERE n.canvasId IS NULL RETURN count(n) AS missing_canvasId;
//   -- both expected: 0

// === ROLLBACK (emergency only) ===
//
// If a regression forces rollback BEFORE removing uuid:
//
//   MATCH (n:CanvasNode) WHERE n.uuid IS NULL AND n.id IS NOT NULL SET n.uuid = n.id;
//
// After STEP 3 the rollback is destructive — only restore from Neo4j backup.
