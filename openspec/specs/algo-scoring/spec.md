# algo-scoring Specification

## Purpose
TBD - created by archiving change fix-fr-kg-04-schema-drift-and-sync-hardening. Update Purpose after archive.
## Requirements
### Requirement: Learning Relationship Score Field Consistency

The backend SHALL use `r.score` as the single source of truth for a learning relationship's score value in Neo4j. Cypher queries that need to return the score under the name `last_score` (for API compatibility) SHALL use the alias form `RETURN r.score AS last_score` rather than reading a non-existent `r.last_score` property. The write path (`create_learning_relationship`) SHALL continue to set `r.score` and MUST additionally increment `r.review_count` on each update via `r.review_count = coalesce(r.review_count, 0) + 1`.

#### Scenario: get_review_suggestions returns non-null last_score

- **GIVEN** a `LEARNED` relationship in Neo4j written via `create_learning_relationship(user_id, concept, score=75.0)`
- **AND** the write persists `r.score = 75.0`
- **WHEN** `get_review_suggestions` runs its Cypher query aliasing `r.score AS last_score`
- **THEN** the returned row contains `last_score = 75.0`
- **AND** no downstream caller observes `null` for the score field
- **AND** the review scheduling algorithm receives a valid numeric input

#### Scenario: review_count increments on repeated scoring

- **GIVEN** a user who has scored the same concept three times with scores 50, 60, 70
- **WHEN** each scoring event triggers `create_learning_relationship`
- **THEN** after the third event the Neo4j `LEARNED` relationship has `r.review_count = 3`
- **AND** `r.score` equals the latest score (70)
- **AND** no additional relationships are created (MERGE is idempotent on user+concept pair)

#### Scenario: First-time scoring initializes review_count to 1

- **GIVEN** a user who has never scored a specific concept
- **WHEN** `create_learning_relationship` is called for the first time for that user+concept pair
- **THEN** a new `LEARNED` relationship is created with `r.score = <score>` and `r.review_count = 1`
- **AND** `coalesce(r.review_count, 0) + 1` evaluates to 1 because the previous value was null

