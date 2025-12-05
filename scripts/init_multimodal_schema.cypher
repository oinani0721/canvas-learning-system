// Neo4j Schema for Multimodal Content Storage
// Verified from Story 6.3 (AC 6.3.2): Neo4j Schema with Media nodes
//
// Usage:
//   cat scripts/init_multimodal_schema.cypher | cypher-shell -u neo4j -p password
//
// Or in Neo4j Browser:
//   Copy and paste the content

// ============================================================
// 1. Create Constraints (Unique IDs)
// ============================================================

// Media node constraint
CREATE CONSTRAINT media_id_unique IF NOT EXISTS
FOR (m:Media) REQUIRE m.id IS UNIQUE;

// Concept node constraint (if not exists from Epic 12)
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
FOR (c:Concept) REQUIRE c.id IS UNIQUE;

// ============================================================
// 2. Create Indexes for Performance
// ============================================================

// Index on media_type for filtering
CREATE INDEX media_type_index IF NOT EXISTS
FOR (m:Media) ON (m.media_type);

// Index on file_path for lookups
CREATE INDEX media_file_path_index IF NOT EXISTS
FOR (m:Media) ON (m.file_path);

// Index on created_at for sorting
CREATE INDEX media_created_at_index IF NOT EXISTS
FOR (m:Media) ON (m.created_at);

// Composite index for common queries
CREATE INDEX media_type_created_index IF NOT EXISTS
FOR (m:Media) ON (m.media_type, m.created_at);

// ============================================================
// 3. Relationship Type Documentation
// ============================================================

// HAS_MEDIA: Concept -[HAS_MEDIA]-> Media
//   Properties:
//     - relevance_score: float (0.0-1.0)
//     - created_at: datetime
//     - association_type: string (manual|auto)

// ILLUSTRATES: Media -[ILLUSTRATES]-> Concept
//   Used when media visually represents a concept
//   Properties:
//     - relevance_score: float

// REFERENCES: Media -[REFERENCES]-> Media
//   Used when one media references another (e.g., PDF references an image)
//   Properties:
//     - reference_type: string (citation|embed|link)

// ============================================================
// 4. Sample Node Creation (for testing)
// ============================================================

// Create sample Media node
// MERGE (m:Media {id: 'sample-media-001'})
// SET m.media_type = 'image',
//     m.file_path = '/path/to/sample.png',
//     m.description = 'Sample image for testing',
//     m.created_at = datetime(),
//     m.file_size = 12345,
//     m.mime_type = 'image/png'
// RETURN m;

// Create HAS_MEDIA relationship
// MATCH (c:Concept {id: 'sample-concept-001'})
// MATCH (m:Media {id: 'sample-media-001'})
// MERGE (c)-[r:HAS_MEDIA]->(m)
// SET r.relevance_score = 0.95,
//     r.created_at = datetime(),
//     r.association_type = 'manual'
// RETURN r;

// ============================================================
// 5. Utility Queries
// ============================================================

// Query: Get all media for a concept
// MATCH (c:Concept {id: $concept_id})-[r:HAS_MEDIA]->(m:Media)
// RETURN m, r.relevance_score AS score
// ORDER BY score DESC;

// Query: Get media by type
// MATCH (m:Media {media_type: $type})
// RETURN m
// ORDER BY m.created_at DESC
// LIMIT 100;

// Query: Get concepts illustrated by media
// MATCH (m:Media {id: $media_id})-[:ILLUSTRATES]->(c:Concept)
// RETURN c;

// Query: Count media by type
// MATCH (m:Media)
// RETURN m.media_type AS type, count(m) AS count
// ORDER BY count DESC;
