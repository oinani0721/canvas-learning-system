// Migration 001: Canvas Neo4j constraints and indexes
//
// FR-KG-04 Phase 4 Task 4.3 + Phase 8 Task 8.3:
// Establishes the schema guarantees that protect the canvas graph from
// duplicate nodes, duplicate boards, and unindexed canvasId lookups.
//
// All statements use `IF NOT EXISTS` so this migration is idempotent and
// can be re-run safely on existing databases.
//
// To apply manually:
//   cypher-shell -u neo4j -p <password> -a bolt://localhost:7689 \
//     -d neo4j -f backend/migrations/001_canvas_constraints.cypher

// ─────────────────────────────────────────────────────────────────────────
// CONSTRAINT 1: CanvasNode primary key uniqueness
// ─────────────────────────────────────────────────────────────────────────
// SyncService._upsert_node uses MERGE (n:CanvasNode {id: $entity_id}); this
// constraint guarantees that two different frontend clients cannot ever
// race-create two CanvasNodes with the same id. Without this, the MERGE
// only relies on its own WHERE clause, which is not atomic across sessions.
//
CREATE CONSTRAINT canvasnode_id_unique IF NOT EXISTS
FOR (n:CanvasNode) REQUIRE n.id IS UNIQUE;

// ─────────────────────────────────────────────────────────────────────────
// CONSTRAINT 2: CanvasBoard (subjectId, name) composite uniqueness
// ─────────────────────────────────────────────────────────────────────────
// Phase 8 Task 8.3: prevent two boards with the same name inside the same
// subject. Different subjects can still have boards named "default".
//
// Before applying in production, run the conflict check from Task 8.1:
//   MATCH (b1:CanvasBoard), (b2:CanvasBoard)
//   WHERE b1.subjectId = b2.subjectId
//     AND b1.name = b2.name
//     AND elementId(b1) < elementId(b2)
//   RETURN b1, b2 LIMIT 10
//
// and manually resolve any hits, otherwise the CREATE CONSTRAINT call will
// abort with ConstraintValidationFailed.
//
CREATE CONSTRAINT canvasboard_subject_name_unique IF NOT EXISTS
FOR (b:CanvasBoard) REQUIRE (b.subjectId, b.name) IS UNIQUE;

// ─────────────────────────────────────────────────────────────────────────
// INDEX 1: CanvasNode.canvasId
// ─────────────────────────────────────────────────────────────────────────
// question_generator._get_kg_relevance filters on neighbor.canvasId in
// the weighted-edge formula. Without an index, that Cypher scans every
// CanvasNode in the graph. With this index, Neo4j EXPLAIN shows
// NodeIndexSeek and the query runs in O(neighbours) instead of O(|V|).
//
CREATE INDEX canvasnode_canvasid IF NOT EXISTS
FOR (n:CanvasNode) ON (n.canvasId);

// ─────────────────────────────────────────────────────────────────────────
// VERIFICATION (run manually after migration)
// ─────────────────────────────────────────────────────────────────────────
//
//   SHOW CONSTRAINTS
//     WHERE name IN [
//       'canvasnode_id_unique',
//       'canvasboard_subject_name_unique'
//     ];
//
//   SHOW INDEXES
//     WHERE name = 'canvasnode_canvasid';
//
// Both should return one row each.
