# Content Consistency Report

**Generated**: 2025-12-13 21:30:25
**Status**: FAIL

---

## Summary

| Metric | Value |
|--------|-------|
| PRD Models | 0 |
| JSON Schema Models | 49 |
| OpenAPI Models | 60 |
| Inconsistencies | 78 |
| Critical Issues | 78 |

---

## SoT Hierarchy Reference

When conflicts are detected, resolve according to Source of Truth hierarchy:

1. **PRD** (Level 1) - Highest authority, defines WHAT
2. **Architecture** (Level 2) - Defines HOW
3. **JSON Schema** (Level 3) - Data structure contracts
4. **OpenAPI Spec** (Level 4) - API behavior contracts
5. **Stories** (Level 5) - Implementation details
6. **Code** (Level 6) - Must comply with all above

---

## Inconsistencies Found (78)

| Model | Field | Type | Sources | Recommendation |
|-------|-------|------|---------|----------------|
| ReviewProgressResponse | scored_count | field_missing | schema:{'type': 'integer', 'required': False}, openapi:NOT EXISTS | Field 'scored_count' in schema not found in openapi |
| ReviewProgressResponse | color_distribution | field_missing | schema:{'type': 'object', 'required': False}, openapi:NOT EXISTS | Field 'color_distribution' in schema not found in openapi |
| ReviewProgressResponse | total_questions | field_missing | schema:{'type': 'integer', 'required': True}, openapi:NOT EXISTS | Field 'total_questions' in schema not found in openapi |
| ReviewProgressResponse | nodes | field_missing | schema:NOT EXISTS, openapi:{'type': 'array', 'required': False} | Add field 'nodes' to openapi (aligns with schema) |
| ReviewProgressResponse | updated_at | field_missing | schema:NOT EXISTS, openapi:{'type': 'string', 'required': False} | Add field 'updated_at' to openapi (aligns with schema) |
| ReviewProgressResponse | review_canvas_path | field_missing | schema:NOT EXISTS, openapi:{'type': 'string', 'required': False} | Add field 'review_canvas_path' to openapi (aligns with schema) |
| ReviewProgressResponse | canvas_name | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'canvas_name' in schema not found in openapi |
| ReviewProgressResponse | original_canvas_path | field_missing | schema:NOT EXISTS, openapi:{'type': 'string', 'required': False} | Add field 'original_canvas_path' to openapi (aligns with schema) |
| ReviewProgressResponse | last_updated | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'last_updated' in schema not found in openapi |
| ReviewProgressResponse | total_concepts | field_missing | schema:NOT EXISTS, openapi:{'type': 'integer', 'required': False} | Add field 'total_concepts' to openapi (aligns with schema) |
| ReviewProgressResponse | pass_count | field_missing | schema:{'type': 'integer', 'required': False}, openapi:NOT EXISTS | Field 'pass_count' in schema not found in openapi |
| ReviewProgressResponse | answered_count | field_missing | schema:{'type': 'integer', 'required': False}, openapi:NOT EXISTS | Field 'answered_count' in schema not found in openapi |
| ReviewProgressResponse | progress | field_missing | schema:NOT EXISTS, openapi:{'type': 'object', 'required': False} | Add field 'progress' to openapi (aligns with schema) |
| ReviewProgressResponse | progress_percentage | field_missing | schema:{'type': 'number', 'required': True}, openapi:NOT EXISTS | Field 'progress_percentage' in schema not found in openapi |
| Alert | triggered_at | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| Alert | resolved_at | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'resolved_at' in schema not found in openapi |
| Alert | acknowledged_by | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'acknowledged_by' in schema not found in openapi |
| Alert | id | field_missing | schema:NOT EXISTS, openapi:{'type': 'string', 'required': False} | Add field 'id' to openapi (aligns with schema) |
| Alert | value | field_missing | schema:NOT EXISTS, openapi:{'type': 'number', 'required': False} | Add field 'value' to openapi (aligns with schema) |
| Alert | name | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| Alert | description | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'description' in schema not found in openapi |
| Alert | notification_sent | field_missing | schema:{'type': 'boolean', 'required': False}, openapi:NOT EXISTS | Field 'notification_sent' in schema not found in openapi |
| Alert | status | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'status' in schema not found in openapi |
| Alert | current_value | field_missing | schema:{'type': 'number', 'required': False}, openapi:NOT EXISTS | Field 'current_value' in schema not found in openapi |
| Alert | message | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| Alert | severity | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| Alert | comparison | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'comparison' in schema not found in openapi |
| Alert | alert_id | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'alert_id' in schema not found in openapi |
| Alert | metric_name | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'metric_name' in schema not found in openapi |
| NodeCreate | label | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'label' in schema not found in openapi |
| ScoreRequest | batch_mode | field_missing | schema:{'type': 'boolean', 'required': False}, openapi:NOT EXISTS | Field 'batch_mode' in schema not found in openapi |
| ScoreResponse | summary | field_missing | schema:{'type': 'object', 'required': False}, openapi:NOT EXISTS | Field 'summary' in schema not found in openapi |
| EdgeRead | toEnd | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'toEnd' in schema not found in openapi |
| EdgeRead | fromEnd | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'fromEnd' in schema not found in openapi |
| EdgeRead | color | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'color' in schema not found in openapi |
| NodeRead | height | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| NodeRead | width | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| NodeRead | label | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'label' in schema not found in openapi |
| MetricsSummary | timestamp | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| AgentResponse | agent_type | field_missing | schema:NOT EXISTS, openapi:{'type': 'string', 'required': False} | Add field 'agent_type' to openapi (aligns with schema) |
| AgentResponse | execution_time_ms | field_missing | schema:NOT EXISTS, openapi:{'type': 'number', 'required': False} | Add field 'execution_time_ms' to openapi (aligns with schema) |
| AgentResponse | timestamp | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'timestamp' in schema not found in openapi |
| AgentResponse | metadata | field_missing | schema:{'type': 'object', 'required': False}, openapi:NOT EXISTS | Field 'metadata' in schema not found in openapi |
| AgentResponse | success | field_missing | schema:NOT EXISTS, openapi:{'type': 'boolean', 'required': False} | Add field 'success' to openapi (aligns with schema) |
| AgentResponse | agent_name | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'agent_name' in schema not found in openapi |
| AgentResponse | status | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'status' in schema not found in openapi |
| AgentResponse | duration_ms | field_missing | schema:{'type': 'integer', 'required': False}, openapi:NOT EXISTS | Field 'duration_ms' in schema not found in openapi |
| CanvasNode | id | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasNode | x | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasNode | type | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasNode | y | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasResponse | nodes | field_missing | schema:NOT EXISTS, openapi:{'type': 'array', 'required': True} | Add field 'nodes' to openapi (aligns with schema) |
| CanvasResponse | meta | field_missing | schema:{'type': '$ref:canvas-meta.schema.json', 'required': True}, openapi:NOT EXISTS | Field 'meta' in schema not found in openapi |
| CanvasResponse | data | field_missing | schema:{'type': '$ref:canvas-data.schema.json', 'required': True}, openapi:NOT EXISTS | Field 'data' in schema not found in openapi |
| CanvasResponse | name | field_missing | schema:NOT EXISTS, openapi:{'type': 'string', 'required': True} | Add field 'name' to openapi (aligns with schema) |
| CanvasResponse | edges | field_missing | schema:NOT EXISTS, openapi:{'type': 'array', 'required': True} | Add field 'edges' to openapi (aligns with schema) |
| CanvasEdge | id | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasEdge | label | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'label' in schema not found in openapi |
| CanvasEdge | fromNode | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasEdge | toNode | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasAssociation | id | field_missing | schema:NOT EXISTS, openapi:{'type': 'string', 'required': False} | Add field 'id' to openapi (aligns with schema) |
| CanvasAssociation | target_canvas | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasAssociation | association_type | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasAssociation | source_canvas | required_mismatch | schema:required, openapi:optional | Update openapi to match schema |
| CanvasAssociation | bidirectional | field_missing | schema:{'type': 'boolean', 'required': False}, openapi:NOT EXISTS | Field 'bidirectional' in schema not found in openapi |
| CanvasAssociation | relevance_score | field_missing | schema:{'type': 'number', 'required': False}, openapi:NOT EXISTS | Field 'relevance_score' in schema not found in openapi |
| CanvasAssociation | auto_generated | field_missing | schema:{'type': 'boolean', 'required': False}, openapi:NOT EXISTS | Field 'auto_generated' in schema not found in openapi |
| CanvasAssociation | association_id | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'association_id' in schema not found in openapi |
| ExplainRequest | explain_type | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'explain_type' in schema not found in openapi |
| ExplainRequest | context | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'context' in schema not found in openapi |
| ExplainResponse | content | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'content' in schema not found in openapi |
| ExplainResponse | file_node | field_missing | schema:{'type': 'object', 'required': False}, openapi:NOT EXISTS | Field 'file_node' in schema not found in openapi |
| ExplainResponse | explain_type | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'explain_type' in schema not found in openapi |
| ExplainResponse | created_node_id | field_missing | schema:NOT EXISTS, openapi:{'type': 'string', 'required': True} | Add field 'created_node_id' to openapi (aligns with schema) |
| ExplainResponse | word_count | field_missing | schema:{'type': 'integer', 'required': False}, openapi:NOT EXISTS | Field 'word_count' in schema not found in openapi |
| ExplainResponse | node_id | field_missing | schema:{'type': 'string', 'required': True}, openapi:NOT EXISTS | Field 'node_id' in schema not found in openapi |
| ExplainResponse | explanation | field_missing | schema:NOT EXISTS, openapi:{'type': 'string', 'required': True} | Add field 'explanation' to openapi (aligns with schema) |
| ExplainResponse | created_at | field_missing | schema:{'type': 'string', 'required': False}, openapi:NOT EXISTS | Field 'created_at' in schema not found in openapi |

---

## Resolution Steps

For each conflict listed above:

1. **Identify the higher-priority source** (use SoT hierarchy)
2. **Update the lower-priority document** to match
3. **Re-run validation** to confirm resolution
4. **Commit changes** with reference to this report

### Missing Fields

- **ReviewProgressResponse.scored_count**: Field 'scored_count' in schema not found in openapi
- **ReviewProgressResponse.color_distribution**: Field 'color_distribution' in schema not found in openapi
- **ReviewProgressResponse.total_questions**: Field 'total_questions' in schema not found in openapi
- **ReviewProgressResponse.nodes**: Add field 'nodes' to openapi (aligns with schema)
- **ReviewProgressResponse.updated_at**: Add field 'updated_at' to openapi (aligns with schema)
- ... and 56 more

### Required/Optional Mismatches

- **Alert.triggered_at**: {'schema': 'required', 'openapi': 'optional'}
  → Update openapi to match schema
- **Alert.name**: {'schema': 'required', 'openapi': 'optional'}
  → Update openapi to match schema
- **Alert.message**: {'schema': 'required', 'openapi': 'optional'}
  → Update openapi to match schema
- **Alert.severity**: {'schema': 'required', 'openapi': 'optional'}
  → Update openapi to match schema
- **NodeRead.height**: {'schema': 'required', 'openapi': 'optional'}
  → Update openapi to match schema
- ... and 12 more

---

**Report generated by**: scripts/validate-content-consistency.py
**Reference**: Section 16.5.4 of planning document
