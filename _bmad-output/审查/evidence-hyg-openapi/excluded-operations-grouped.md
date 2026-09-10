# 契约覆盖面收窄清单（CARD-HYGIENE-openapi）

来源：`comm -23 collect-before.txt collect-after.txt`，共 114 条。

## POST（96 条）

- `POST /api/v1/agents/decompose/basic`
- `POST /api/v1/agents/decompose/deep`
- `POST /api/v1/agents/decompose/question`
- `POST /api/v1/agents/explain/clarification`
- `POST /api/v1/agents/explain/comparison`
- `POST /api/v1/agents/explain/example`
- `POST /api/v1/agents/explain/four-level`
- `POST /api/v1/agents/explain/memory`
- `POST /api/v1/agents/explain/oral`
- `POST /api/v1/agents/recommend-action`
- `POST /api/v1/agents/score`
- `POST /api/v1/agents/verification/question`
- `POST /api/v1/archive/trigger`
- `POST /api/v1/boards/manifest`
- `POST /api/v1/canvas-meta/config/subject-mapping/add`
- `POST /api/v1/canvas-meta/index`
- `POST /api/v1/canvas-meta/index/batch`
- `POST /api/v1/canvas-meta/index/vault`
- `POST /api/v1/canvas-meta/index/vault/incremental`
- `POST /api/v1/canvas/{canvas_id}/recommendations`
- `POST /api/v1/canvas/{canvas_name}/edges`
- `POST /api/v1/canvas/{canvas_name}/nodes`
- `POST /api/v1/canvas/{canvas_name}/sync-edges`
- `POST /api/v1/canvas/intelligent-parallel/`
- `POST /api/v1/canvas/intelligent-parallel/cancel/{session_id}`
- `POST /api/v1/canvas/intelligent-parallel/confirm`
- `POST /api/v1/canvas/single-agent`
- `POST /api/v1/chat/{node_id}/distill`
- `POST /api/v1/chat/enrich-context`
- `POST /api/v1/chat/post-turn-extract`
- `POST /api/v1/chat/rag/enrich-hook`
- `POST /api/v1/config/ai`
- `POST /api/v1/edges/record-rationale`
- `POST /api/v1/errors/accept-candidate`
- `POST /api/v1/errors/dismiss-candidate`
- `POST /api/v1/errors/dispute-candidate`
- `POST /api/v1/errors/rebuild-graphiti`
- `POST /api/v1/exam/{exam_id}/complete`
- `POST /api/v1/exam/{exam_id}/hint`
- `POST /api/v1/exam/{exam_id}/pause`
- `POST /api/v1/exam/{exam_id}/resume`
- `POST /api/v1/exam/{exam_id}/skip`
- `POST /api/v1/exam/{exam_id}/sync-node`
- `POST /api/v1/exam/analyze-canvas`
- `POST /api/v1/exam/grade`
- `POST /api/v1/exam/quick`
- `POST /api/v1/exam/start`
- `POST /api/v1/exam/targeting-material`
- `POST /api/v1/health/storage/reset-counters`
- `POST /api/v1/index/image`
- `POST /api/v1/index/refresh-changed`
- `POST /api/v1/mastery/{concept_id}/calibration`
- `POST /api/v1/mastery/{concept_id}/grade`
- `POST /api/v1/mastery/{concept_id}/override`
- `POST /api/v1/mastery/{concept_id}/self-assess`
- `POST /api/v1/mastery/graphiti-sync`
- `POST /api/v1/memory/archive/session`
- `POST /api/v1/memory/episodes`
- `POST /api/v1/memory/episodes/batch`
- `POST /api/v1/memory/extract-conversation`
- `POST /api/v1/multimodal/search`
- `POST /api/v1/multimodal/upload-url`
- `POST /api/v1/multimodal/upload`
- `POST /api/v1/rag/query`
- `POST /api/v1/review/generate`
- `POST /api/v1/review/overview/board-done`
- `POST /api/v1/review/overview/refresh`
- `POST /api/v1/review/session/{session_id}/answer`
- `POST /api/v1/review/session/{session_id}/pause`
- `POST /api/v1/review/session/{session_id}/resume`
- `POST /api/v1/review/session/start`
- `POST /api/v1/rollback/rollback`
- `POST /api/v1/rollback/snapshot`
- `POST /api/v1/skills/refresh`
- `POST /api/v1/subjects/`
- `POST /api/v1/suggestions/relation`
- `POST /api/v1/sync/batch`
- `POST /api/v1/sync/relationships/by-node`
- `POST /api/v1/sync/relationships/vault`
- `POST /api/v1/system/config`
- `POST /api/v1/system/extraction-records/{record_id}/annotate`
- `POST /api/v1/system/setup-wizard`
- `POST /api/v1/system/test-llm`
- `POST /api/v1/tips`
- `POST /api/v1/tips/batch`
- `POST /api/v1/tips/callout-direct`
- `POST /api/v1/tips/relation`
- `POST /api/v1/vault/switch`
- `POST /api/v1/wikilink/build`
- `POST /api/v1/wikilink/refresh`
- `POST /mcp/tools/check_backend_health`
- `POST /mcp/tools/get_board_manifest`
- `POST /mcp/tools/get_neighbors`
- `POST /mcp/tools/read_note`
- `POST /mcp/tools/search_memories`
- `POST /mcp/tools/search_notes`

## DELETE（9 条）

- `DELETE /api/v1/canvas-meta/config/subject-mapping/remove`
- `DELETE /api/v1/canvas/{canvas_name}/edges/{edge_id}`
- `DELETE /api/v1/canvas/{canvas_name}/nodes/{node_id}`
- `DELETE /api/v1/index/{vault_id}`
- `DELETE /api/v1/mastery/{concept_id}/override`
- `DELETE /api/v1/multimodal/{content_id}`
- `DELETE /api/v1/subjects/{subject_id}`
- `DELETE /api/v1/system/extraction-records/{record_id}`
- `DELETE /api/v1/system/extraction-records/{record_id}/annotation`

## PUT（6 条）

- `PUT /api/v1/canvas-meta/config/subject-mapping`
- `PUT /api/v1/canvas/{canvas_name}/nodes/{node_id}`
- `PUT /api/v1/multimodal/{content_id}`
- `PUT /api/v1/rag/config`
- `PUT /api/v1/review/record`
- `PUT /api/v1/subjects/{subject_id}`

## PATCH（2 条）

- `PATCH /api/v1/exam/{exam_id}/status`
- `PATCH /api/v1/system/extraction-records/{record_id}`

## GET（1 条）

- `GET /api/v1/health/lancedb`

