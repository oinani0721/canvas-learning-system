# CARD-R-SLO 独立补审请求（BATCH-2026-09-18-第十五批 · 车道 card-p10-docs 末张 · ZCode/GLM-5.3 通道）

你是独立复核者。只读审查：不要修改任何文件，不要连接任何数据库或网络服务。

仓库根（同时也是你的工作目录）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs`

- **审查绑定**：`e4ef1ebf`（A4 终轮）。PREV = `a03f0ce3`。
- **送审模式**：build 模式（无 Bash、无写工具）——「本卡改动全文」已**内嵌**在 §①；其余参考文件请用读文件工具在树内打开。
- **背景**：本卡 = 文档/证据卡（零 `.py`）。此前 4 轮 Codex（glm-5.3 同模型）：r1 0B/4H/1M/1L → r2 0B/1H/1M/1L → r3 0B/1H/1M/1L → **r4 0B/0H/0M/2L 通过**。本轮为 **ZCode 通道**交叉复核。

---

## ① 最小读取面（只读这些，不要泛读全仓）

**1. 本卡改动全文（PREV `a03f0ce3` → 审SHA `e4ef1ebf`，逐字节内嵌如下）：**

==== BEGIN EMBEDDED DIFF ====
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/base.nodeids" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/base.nodeids"
new file mode 100644
index 00000000..e44e1121
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/base.nodeids"
@@ -0,0 +1,33 @@
+FAILED tests/unit/test_agent_memory_injection.py::TestMemoryInjection::test_graceful_degradation_on_exception
+FAILED tests/unit/test_agent_service_neo4j_memory.py::TestEdgeCases::test_neo4j_query_error_returns_empty
+FAILED tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_difficulty_context_in_prompt
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_no_difficulty_map_no_extra_fields
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestGetDifficultyData::test_memory_service_unavailable_returns_none
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_chinese_vault_id_not_collapsed_to_default
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_subject_id_optional_backward_compat
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_emoji_stripped
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_provided_triggers_context_var_injection
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_with_special_chars_sanitized
+FAILED tests/unit/test_epic30_memory_pipeline.py::TestRecordTemporalEventLifecycle::test_p0_neo4j_write_failure_degrades_silently
+FAILED tests/unit/test_epic36_gap_coverage.py::TestGetRelatedMemoriesReturnStructure::test_query_exception_returns_empty
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestCancelEndpoint::test_cancel_nonexistent_session_404
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestErrorResponses::test_404_error_format
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestProgressEndpoint::test_progress_invalid_session_404
+FAILED tests/unit/test_neo4j_fulltext_index.py::TestEnsureFulltextIndex::test_ensure_fulltext_index_idempotent
+FAILED tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestMergedViewEdgeCases::test_merged_view_sort_newest_first
+FAILED tests/unit/test_rag_p0_doc_type_filter.py::test_strip_whiteboard_removes_admonition_callouts
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_normalizes_schema
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_passes_node_id_filter_to_search_memories
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_sorts_by_timestamp_desc
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_filter_post_merge
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_none_is_no_filter
+FAILED tests/unit/test_story_38_6_scoring_reliability.py::TestAC4MergedView::test_get_learning_history_merges_failed_scores
+FAILED tests/unit/test_vault_doc_roles.py::test_live_vault_enforce_clean
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_honors_nested_metadata_json_subject
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_physics_filters_to_physics_only
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_common_and_no_match_returns_empty
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_explicit_match_returns_only_common_notes
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_no_history_generates_standard_question
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_with_history_generates_alternative_question
+FAILED tests/unit/test_websocket_endpoints.py::TestWebSocketEndpoint::test_validate_session_handles_validator_error
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/close.nodeids" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/close.nodeids"
new file mode 100644
index 00000000..1354c1c3
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/close.nodeids"
@@ -0,0 +1,32 @@
+FAILED tests/unit/test_agent_memory_injection.py::TestMemoryInjection::test_graceful_degradation_on_exception
+FAILED tests/unit/test_agent_service_neo4j_memory.py::TestEdgeCases::test_neo4j_query_error_returns_empty
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_difficulty_context_in_prompt
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_no_difficulty_map_no_extra_fields
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestGetDifficultyData::test_memory_service_unavailable_returns_none
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_chinese_vault_id_not_collapsed_to_default
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_subject_id_optional_backward_compat
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_emoji_stripped
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_provided_triggers_context_var_injection
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_with_special_chars_sanitized
+FAILED tests/unit/test_epic30_memory_pipeline.py::TestRecordTemporalEventLifecycle::test_p0_neo4j_write_failure_degrades_silently
+FAILED tests/unit/test_epic36_gap_coverage.py::TestGetRelatedMemoriesReturnStructure::test_query_exception_returns_empty
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestCancelEndpoint::test_cancel_nonexistent_session_404
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestErrorResponses::test_404_error_format
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestProgressEndpoint::test_progress_invalid_session_404
+FAILED tests/unit/test_neo4j_fulltext_index.py::TestEnsureFulltextIndex::test_ensure_fulltext_index_idempotent
+FAILED tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestMergedViewEdgeCases::test_merged_view_sort_newest_first
+FAILED tests/unit/test_rag_p0_doc_type_filter.py::test_strip_whiteboard_removes_admonition_callouts
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_normalizes_schema
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_passes_node_id_filter_to_search_memories
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_sorts_by_timestamp_desc
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_filter_post_merge
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_none_is_no_filter
+FAILED tests/unit/test_story_38_6_scoring_reliability.py::TestAC4MergedView::test_get_learning_history_merges_failed_scores
+FAILED tests/unit/test_vault_doc_roles.py::test_live_vault_enforce_clean
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_honors_nested_metadata_json_subject
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_physics_filters_to_physics_only
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_common_and_no_match_returns_empty
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_explicit_match_returns_only_common_notes
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_no_history_generates_standard_question
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_with_history_generates_alternative_question
+FAILED tests/unit/test_websocket_endpoints.py::TestWebSocketEndpoint::test_validate_session_handles_validator_error
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/data-sha-20260919T171754.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/data-sha-20260919T171754.txt"
new file mode 100644
index 00000000..5565ffe7
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/data-sha-20260919T171754.txt"
@@ -0,0 +1,5 @@
+### data_sha CARD-R-SLO 2026-09-19T17:17:54-0700
+cmd: find <live> -name '*.md' -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256
+df036977f3d220b10d6be95c16cd83b1ff5241d066884e4b09e9060397551907  -
+md_count=214
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/desens-20260919T202508.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/desens-20260919T202508.txt"
new file mode 100644
index 00000000..f7853515
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/desens-20260919T202508.txt"
@@ -0,0 +1,5 @@
+### (m) 脱敏门 首版（已重写）
+首版标签里写了敏感字段名的字面（含等号），导致逐行 grep 判据把本文件自身当命中（计数=1，自指污染，非泄漏）。
+本文件已就地重写去 needle；最终版判据见 desens-<后续时间戳>.txt（标签不再含字面 needle）。
+首版其余判据输出（除自指那一条外的结论不变）：
+- yaml /Users/ 命中 0；fsrs_bridge/decay_beta 命中 0；live outputs 前后逐字同；measure-*.txt 写端点字样 0；INTERNAL_API_KEY 实测不在 backend/.env。
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/desens-final-20260919T202600.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/desens-final-20260919T202600.txt"
new file mode 100644
index 00000000..041b7a16
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/desens-final-20260919T202600.txt"
@@ -0,0 +1,18 @@
+### (m) 脱敏与只读门（最终版）2026-09-19T20:26:00-0700
+标签不含 needle 字面，避免自指污染；命令体不在档内回显。
+--- (m)1 yaml 内 /Users/ 绝对路径命中
+0
+--- (m)2 fsrs_bridge/decay_beta 命中
+0
+--- (m)3 内部 API key 检查（卡文口径）
+0（INTERNAL_API_KEY 实测不在 backend/.env，0 行 ⇒ 该项不适用；以补充检查代替）
+--- (m)3b 补充：敏感变量值全证据面命中数
+NEO4J_PASSWORD（值）命中=0
+GOOGLE_API_KEY（值）命中=0
+--- (m)4 敏感字段名字面（NEO4J 密码字段+等号）命中
+0
+--- (m)5 live outputs before/after
+identical=YES
+--- (m)6 measure-*.txt 中写端点字样命中
+0
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/docker-ps-open-20260919T165812.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/docker-ps-open-20260919T165812.txt"
new file mode 100644
index 00000000..0e3dc7cd
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/docker-ps-open-20260919T165812.txt"
@@ -0,0 +1,4 @@
+canvas-learning-system-backend Up 4 minutes (healthy)
+canvas-learning-system-neo4j-test Up 4 minutes (healthy)
+canvas-learning-system-neo4j Up 4 minutes (healthy)
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/env-probe-20260919T171108.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/env-probe-20260919T171108.txt"
new file mode 100644
index 00000000..22551f18
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/env-probe-20260919T171108.txt"
@@ -0,0 +1,20 @@
+### env-probe CARD-R-SLO 2026-09-20T00:11:08Z
+cpu_brand: Apple M5 Max
+mem_bytes: 137438953472
+os_version: 26.5
+arch: arm64
+python: Python 3.14.4
+git: git version 2.50.1 (Apple Git-155)
+tz_abbr: PDT
+tz_iana: America/Los_Angeles
+date_now: 2026-09-19T17:11:08-0700
+ollama_11434_http: 000
+llama_12341: {"models":[{"name":"qwen3.5-35b-a3b-q4_k_s","model":"qwen3.5-35b-a3b-q4_k_s","modified_at":"","size":"","digest":"","type":"model","description":"","tags":[""],"capabilities":["completion","multimodal"],"parameters":"","details":{"parent_model":"","format":"gguf","family":"","families":[""],"parameter_size":"","quantization_level":""}}],"object":"list","data":[{"id":"qwen3.5-35b-a3b-q4_k_s","aliases":["qwen3.5-35b-a3b-q4_k_s"],"tags":[],"object":"model","created":1789863068,"owned_by":"llamacpp","meta":{"vocab_type":true,"n_vocab":248320,"n_ctx":16384,"n_ctx_train":262144,"n_embd":2048,"n_params":35505251456,"size":21475369472,"ftype":"Q4_K - Small"}}]}
+rerank_18012: {"models":[{"name":"bge-reranker-v2-m3","model":"bge-reranker-v2-m3","modified_at":"","size":"","digest":"","type":"model","description":"","tags":[""],"capabilities":["completion"],"parameters":"","details":{"parent_model":"","format":"gguf","family":"","families":[""],"parameter_size":"","quantization_level":""}}],"object":"list","data":[{"id":"bge-reranker-v2-m3","aliases":["bge-reranker-v2-m3"],"tags":[],"object":"model","created":1789863068,"owned_by":"llamacpp","meta":{"vocab_type":true,"n_vocab":250002,"n_ctx":8192,"n_ctx_train":8192,"n_embd":1024,"n_params":567753729,"size":628833412,"ftype":"Q8_0"}}]}
+health_ai: {"status":"error","model":"gemini-3.1-flash-lite-preview","provider":"google","error":"AI client not configured. Check API key settings.","error_code":"LLM_AUTH_FAILED"}
+health_lancedb: {"status":"ok","table_count":4,"total_vectors":53,"embedding_model":"text-embedding-3-small","error":null}
+index_stats: {}
+kg: {"status":"ok","graph_stats":{"node_count":0,"edge_count":0,"episode_count":0},"last_episode_timestamp":null,"error":null}
+live_md_count: 214
+lane_sha: a03f0ce34de9a9c4652310d45eae283f78d11451
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/f12-struct-20260919T171903.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/f12-struct-20260919T171903.txt"
new file mode 100644
index 00000000..b9fddd67
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/f12-struct-20260919T171903.txt"
@@ -0,0 +1,9 @@
+### (f)①② 结构判据 2026-09-19T17:19:03-0700
+--- (f)① test -e slo-manifest.yaml; echo rc
+rc=0
+--- (f)② grep -c 'slo-manifest.yaml' README
+2
+--- (f)⑤ schema 指纹 vs 校验器常量
+4456e1ad629108d618284d6bd5b717f484a712aa8685615e31f940327922c547
+SCHEMA_SHA256 = "4456e1ad629108d618284d6bd5b717f484a712aa8685615e31f940327922c547"
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/live-outputs-after.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/live-outputs-after.txt"
new file mode 100644
index 00000000..12072b81
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/live-outputs-after.txt"
@@ -0,0 +1 @@
+105f563cf6ebef87acd99f81d0c9b3ce844aefb6c17cbc6d16bee4973a5e5a62  /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/outputs/今日复习.json
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/live-outputs-before.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/live-outputs-before.txt"
new file mode 100644
index 00000000..12072b81
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/live-outputs-before.txt"
@@ -0,0 +1 @@
+105f563cf6ebef87acd99f81d0c9b3ce844aefb6c17cbc6d16bee4973a5e5a62  /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/outputs/今日复习.json
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-kg_read-20260919T171134.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-kg_read-20260919T171134.txt"
new file mode 100644
index 00000000..f15abeea
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-kg_read-20260919T171134.txt"
@@ -0,0 +1,24 @@
+### kg_read x20 2026-09-19T17:11:34-0700
+200 0.003290 122
+200 0.003939 122
+200 0.010696 122
+200 0.002861 122
+200 0.002702 122
+200 0.014717 122
+200 0.002765 122
+200 0.003108 122
+200 0.003272 122
+200 0.003748 122
+200 0.003092 122
+200 0.004648 122
+200 0.007919 122
+200 0.003290 122
+200 0.002475 122
+200 0.003496 122
+200 0.004520 122
+200 0.013077 122
+200 0.027765 122
+200 0.004118 122
+--- counts ---
+{"status":"ok","graph_stats":{"node_count":0,"edge_count":0,"episode_count":0},"last_episode_timestamp":null,"error":null}
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-rag_cold-20260919T171226.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-rag_cold-20260919T171226.txt"
new file mode 100644
index 00000000..422e4796
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-rag_cold-20260919T171226.txt"
@@ -0,0 +1,22 @@
+### rag_cold x20 (distinct queries from seed file, sha=4dd05b33342dfdca) 2026-09-19T17:12:26-0700
+200 1.709473 448
+200 1.699436 452
+200 1.754692 448
+000 120.003677 0
+200 5.315191 450
+200 3.072309 449
+200 3.145738 450
+200 4.072881 451
+200 4.266706 449
+200 3.374540 450
+200 5.362801 449
+200 2.887182 450
+200 3.353240 451
+200 2.397395 421
+200 3.538252 448
+200 2.270886 447
+200 3.286965 451
+200 3.553592 451
+200 3.560713 446
+200 2.989816 448
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-rag_warm-20260919T171144.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-rag_warm-20260919T171144.txt"
new file mode 100644
index 00000000..b0dd5139
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-rag_warm-20260919T171144.txt"
@@ -0,0 +1,22 @@
+### rag_warm x20 (same query, qsha=4e4c15e3fd0bc81b) 2026-09-19T17:11:44-0700
+200 1.602569 451
+200 1.635702 450
+200 1.870227 449
+200 1.757139 451
+200 1.705799 448
+200 1.749649 448
+200 1.653685 452
+200 1.729361 449
+200 1.473018 449
+200 1.617105 450
+200 1.590428 449
+200 1.647044 450
+200 1.754054 451
+200 1.785738 451
+200 1.640694 450
+200 1.795764 450
+200 1.690687 450
+200 1.683675 449
+200 1.590654 451
+200 1.625162 450
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-review_overview_first_paint-20260919T171124.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-review_overview_first_paint-20260919T171124.txt"
new file mode 100644
index 00000000..9e5d0034
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-review_overview_first_paint-20260919T171124.txt"
@@ -0,0 +1,22 @@
+200 0.009188 30187
+200 0.010263 30187
+200 0.012744 30187
+200 0.006619 30187
+200 0.027280 30187
+200 0.009935 30187
+200 0.009887 30187
+200 0.028860 30187
+200 0.008343 30187
+200 0.039631 30187
+200 0.007544 30187
+200 0.010847 30187
+200 0.009390 30187
+200 0.016482 30187
+200 0.027656 30187
+200 0.010893 30187
+200 0.008131 30187
+200 0.009784 30187
+200 0.008127 30187
+200 0.009126 30187
+rc=0
+   30187
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-review_rebuild-20260919T171556.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-review_rebuild-20260919T171556.txt"
new file mode 100644
index 00000000..2a1b9219
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-review_rebuild-20260919T171556.txt"
@@ -0,0 +1,32 @@
+### review_rebuild N=5 2026-09-19T17:15:56-0700
+--- run 1 ---
+{"unassigned_nodes": [], "schema_version": 3, "vault_id": "canvas-vault", "display_tz": "America/Los_Angeles", "date": "2026-09-19", "generated_at": "2026-09-19T17:15:56-07:00", "top_boards": [{"board": "CS 61B", "top_node": "csm-tutoring-unit-credit", "priority": -0.0478, "pending": 2, "idle_days": 39, "difficulty": "6.4133", "next_due": "", "why_this_board": "2 个节点到期（其中 1 张新卡） · 最早的已逾期 39 天 · 最该考的已闲置 39 天 · 这块板从未被推荐过", "estimated_minutes": 8, "factors": {"due_total": 2, "due_new": 1, "due_scheduled": 1, "due_malformed": 0, "overdue_days": 39, "idle_days": 39, "never_recommended": true, "recommend_gap_days": null}}, {"board": "特征值与特征向量", "top_node": "Fundamentals", "priority": -0.0456, "pending": 2, "idle_days": 56, "difficulty": "", "next_due": "", "why_this_board": "2 个节点到期（其中 2 张新卡） · 最该考的已闲置 56 天 · 这块板从未被推荐过", "estimated_minutes": 10, "factors": {"due_total": 2, "due_new": 2, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": 56, "never_recommended": true, "recommend_gap_days": null}}, {"board": "CS188 lecture 2", "top_node": "lecture 2", "priority": 0.0709, "pending": 1, "idle_days": null, "difficulty": "", "next_due": "", "why_this_board": "1 个节点到期（其中 1 张新卡） · 最该考的从未考察 · 这块板从未被推荐过", "estimated_minutes": 5, "factors": {"due_total": 1, "due_new": 1, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": null, "never_recommended": true, "recommend_gap_days": null}}], "upcoming": [], "due_nodes": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "Fundamentals", "board": "特征值与特征向量", "state": "new", "pick": -0.0456, "fsrs_due": "", "due_reason": "new", "last_examined": "2026-07-25T02:53:46Z", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "idle_days": 56}, {"node": "cs-61b-csm", "board": "CS 61B", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "csm-tutoring-unit-credit", "board": "CS 61B", "state": "new", "pick": -0.0478, "fsrs_due": "2026-08-11T13:56:58Z", "due_reason": "scheduled", "last_examined": "2026-08-11T13:55:58Z", "difficulty": "6.4133", "bucket": "learning_queue", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "idle_days": 39}, {"node": "lecture 2", "board": "CS188 lecture 2", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}], "boards": [{"board": "CS 61B", "due": 2, "due_new": 1, "due_scheduled": 1, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": "2026-08-11T13:56:58Z"}, {"board": "CS188 lecture 2", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 7, "earliest_overdue": ""}, {"board": "特征值与特征向量", "due": 2, "due_new": 2, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 1, "earliest_overdue": ""}, {"board": "递归与分治 (Recursion & Divide-Conquer)", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": ""}], "buckets": {"new": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "Fundamentals", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "fsrs_due": ""}, {"node": "cs-61b-csm", "board": "CS 61B", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "lecture 2", "board": "CS188 lecture 2", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}], "learning_queue": [{"node": "csm-tutoring-unit-credit", "board": "CS 61B", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "fsrs_due": "2026-08-11T13:56:58Z"}], "due_now": [], "due_today": [], "future": []}, "ineligible": {"placeholder": ["Eigenvalues-are-special-vectors-that-sat", "代理决策分析-0303()", "代理函数-(Agent-Function)", "代理类型：反射与规划", "反射代理的局限性引出了规划代理-(Planning-Agents)-的需求", "理性代理-(Rational-Agent)", "规划代理的特点", "规划的分类-1549()"], "test_excluded": [], "corrupt": []}, "stats": {"new": 2, "legacy": 2, "none": 2, "ineligible": 8, "test_excluded": 0, "corrupt": 0, "unassigned": 0, "due_nodes": 6, "future_nodes": 0}, "notification": {"title": "📚 今日复习 · CS 61B", "body": "csm-tutoring-unit-credit 等 2 节点待巩固 · 已闲置 39 天", "group": "canvas复习", "id": "canvas-review-2026-09-19"}, "rank_manifest": {"version": 2, "sha256": "218c838f4aef8ab00136bce48078ab0be10c7be44ca25c36f12d56e965d06f4a"}, "truncated": {"top_boards": true, "upcoming": false}}
+real 0.05
+user 0.03
+sys 0.01
+run1_rc=0
+--- run 2 ---
+{"unassigned_nodes": [], "schema_version": 3, "vault_id": "canvas-vault", "display_tz": "America/Los_Angeles", "date": "2026-09-19", "generated_at": "2026-09-19T17:15:56-07:00", "top_boards": [{"board": "CS 61B", "top_node": "csm-tutoring-unit-credit", "priority": -0.0478, "pending": 2, "idle_days": 39, "difficulty": "6.4133", "next_due": "", "why_this_board": "2 个节点到期（其中 1 张新卡） · 最早的已逾期 39 天 · 最该考的已闲置 39 天 · 这块板从未被推荐过", "estimated_minutes": 8, "factors": {"due_total": 2, "due_new": 1, "due_scheduled": 1, "due_malformed": 0, "overdue_days": 39, "idle_days": 39, "never_recommended": true, "recommend_gap_days": null}}, {"board": "特征值与特征向量", "top_node": "Fundamentals", "priority": -0.0456, "pending": 2, "idle_days": 56, "difficulty": "", "next_due": "", "why_this_board": "2 个节点到期（其中 2 张新卡） · 最该考的已闲置 56 天 · 这块板从未被推荐过", "estimated_minutes": 10, "factors": {"due_total": 2, "due_new": 2, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": 56, "never_recommended": true, "recommend_gap_days": null}}, {"board": "CS188 lecture 2", "top_node": "lecture 2", "priority": 0.0709, "pending": 1, "idle_days": null, "difficulty": "", "next_due": "", "why_this_board": "1 个节点到期（其中 1 张新卡） · 最该考的从未考察 · 这块板从未被推荐过", "estimated_minutes": 5, "factors": {"due_total": 1, "due_new": 1, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": null, "never_recommended": true, "recommend_gap_days": null}}], "upcoming": [], "due_nodes": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "Fundamentals", "board": "特征值与特征向量", "state": "new", "pick": -0.0456, "fsrs_due": "", "due_reason": "new", "last_examined": "2026-07-25T02:53:46Z", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "idle_days": 56}, {"node": "cs-61b-csm", "board": "CS 61B", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "csm-tutoring-unit-credit", "board": "CS 61B", "state": "new", "pick": -0.0478, "fsrs_due": "2026-08-11T13:56:58Z", "due_reason": "scheduled", "last_examined": "2026-08-11T13:55:58Z", "difficulty": "6.4133", "bucket": "learning_queue", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "idle_days": 39}, {"node": "lecture 2", "board": "CS188 lecture 2", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}], "boards": [{"board": "CS 61B", "due": 2, "due_new": 1, "due_scheduled": 1, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": "2026-08-11T13:56:58Z"}, {"board": "CS188 lecture 2", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 7, "earliest_overdue": ""}, {"board": "特征值与特征向量", "due": 2, "due_new": 2, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 1, "earliest_overdue": ""}, {"board": "递归与分治 (Recursion & Divide-Conquer)", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": ""}], "buckets": {"new": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "Fundamentals", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "fsrs_due": ""}, {"node": "cs-61b-csm", "board": "CS 61B", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "lecture 2", "board": "CS188 lecture 2", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}], "learning_queue": [{"node": "csm-tutoring-unit-credit", "board": "CS 61B", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "fsrs_due": "2026-08-11T13:56:58Z"}], "due_now": [], "due_today": [], "future": []}, "ineligible": {"placeholder": ["Eigenvalues-are-special-vectors-that-sat", "代理决策分析-0303()", "代理函数-(Agent-Function)", "代理类型：反射与规划", "反射代理的局限性引出了规划代理-(Planning-Agents)-的需求", "理性代理-(Rational-Agent)", "规划代理的特点", "规划的分类-1549()"], "test_excluded": [], "corrupt": []}, "stats": {"new": 2, "legacy": 2, "none": 2, "ineligible": 8, "test_excluded": 0, "corrupt": 0, "unassigned": 0, "due_nodes": 6, "future_nodes": 0}, "notification": {"title": "📚 今日复习 · CS 61B", "body": "csm-tutoring-unit-credit 等 2 节点待巩固 · 已闲置 39 天", "group": "canvas复习", "id": "canvas-review-2026-09-19"}, "rank_manifest": {"version": 2, "sha256": "218c838f4aef8ab00136bce48078ab0be10c7be44ca25c36f12d56e965d06f4a"}, "truncated": {"top_boards": true, "upcoming": false}}
+real 0.05
+user 0.03
+sys 0.01
+run2_rc=0
+--- run 3 ---
+{"unassigned_nodes": [], "schema_version": 3, "vault_id": "canvas-vault", "display_tz": "America/Los_Angeles", "date": "2026-09-19", "generated_at": "2026-09-19T17:15:56-07:00", "top_boards": [{"board": "CS 61B", "top_node": "csm-tutoring-unit-credit", "priority": -0.0478, "pending": 2, "idle_days": 39, "difficulty": "6.4133", "next_due": "", "why_this_board": "2 个节点到期（其中 1 张新卡） · 最早的已逾期 39 天 · 最该考的已闲置 39 天 · 这块板从未被推荐过", "estimated_minutes": 8, "factors": {"due_total": 2, "due_new": 1, "due_scheduled": 1, "due_malformed": 0, "overdue_days": 39, "idle_days": 39, "never_recommended": true, "recommend_gap_days": null}}, {"board": "特征值与特征向量", "top_node": "Fundamentals", "priority": -0.0456, "pending": 2, "idle_days": 56, "difficulty": "", "next_due": "", "why_this_board": "2 个节点到期（其中 2 张新卡） · 最该考的已闲置 56 天 · 这块板从未被推荐过", "estimated_minutes": 10, "factors": {"due_total": 2, "due_new": 2, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": 56, "never_recommended": true, "recommend_gap_days": null}}, {"board": "CS188 lecture 2", "top_node": "lecture 2", "priority": 0.0709, "pending": 1, "idle_days": null, "difficulty": "", "next_due": "", "why_this_board": "1 个节点到期（其中 1 张新卡） · 最该考的从未考察 · 这块板从未被推荐过", "estimated_minutes": 5, "factors": {"due_total": 1, "due_new": 1, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": null, "never_recommended": true, "recommend_gap_days": null}}], "upcoming": [], "due_nodes": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "Fundamentals", "board": "特征值与特征向量", "state": "new", "pick": -0.0456, "fsrs_due": "", "due_reason": "new", "last_examined": "2026-07-25T02:53:46Z", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "idle_days": 56}, {"node": "cs-61b-csm", "board": "CS 61B", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "csm-tutoring-unit-credit", "board": "CS 61B", "state": "new", "pick": -0.0478, "fsrs_due": "2026-08-11T13:56:58Z", "due_reason": "scheduled", "last_examined": "2026-08-11T13:55:58Z", "difficulty": "6.4133", "bucket": "learning_queue", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "idle_days": 39}, {"node": "lecture 2", "board": "CS188 lecture 2", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}], "boards": [{"board": "CS 61B", "due": 2, "due_new": 1, "due_scheduled": 1, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": "2026-08-11T13:56:58Z"}, {"board": "CS188 lecture 2", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 7, "earliest_overdue": ""}, {"board": "特征值与特征向量", "due": 2, "due_new": 2, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 1, "earliest_overdue": ""}, {"board": "递归与分治 (Recursion & Divide-Conquer)", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": ""}], "buckets": {"new": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "Fundamentals", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "fsrs_due": ""}, {"node": "cs-61b-csm", "board": "CS 61B", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "lecture 2", "board": "CS188 lecture 2", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}], "learning_queue": [{"node": "csm-tutoring-unit-credit", "board": "CS 61B", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "fsrs_due": "2026-08-11T13:56:58Z"}], "due_now": [], "due_today": [], "future": []}, "ineligible": {"placeholder": ["Eigenvalues-are-special-vectors-that-sat", "代理决策分析-0303()", "代理函数-(Agent-Function)", "代理类型：反射与规划", "反射代理的局限性引出了规划代理-(Planning-Agents)-的需求", "理性代理-(Rational-Agent)", "规划代理的特点", "规划的分类-1549()"], "test_excluded": [], "corrupt": []}, "stats": {"new": 2, "legacy": 2, "none": 2, "ineligible": 8, "test_excluded": 0, "corrupt": 0, "unassigned": 0, "due_nodes": 6, "future_nodes": 0}, "notification": {"title": "📚 今日复习 · CS 61B", "body": "csm-tutoring-unit-credit 等 2 节点待巩固 · 已闲置 39 天", "group": "canvas复习", "id": "canvas-review-2026-09-19"}, "rank_manifest": {"version": 2, "sha256": "218c838f4aef8ab00136bce48078ab0be10c7be44ca25c36f12d56e965d06f4a"}, "truncated": {"top_boards": true, "upcoming": false}}
+real 0.05
+user 0.03
+sys 0.00
+run3_rc=0
+--- run 4 ---
+{"unassigned_nodes": [], "schema_version": 3, "vault_id": "canvas-vault", "display_tz": "America/Los_Angeles", "date": "2026-09-19", "generated_at": "2026-09-19T17:15:56-07:00", "top_boards": [{"board": "CS 61B", "top_node": "csm-tutoring-unit-credit", "priority": -0.0478, "pending": 2, "idle_days": 39, "difficulty": "6.4133", "next_due": "", "why_this_board": "2 个节点到期（其中 1 张新卡） · 最早的已逾期 39 天 · 最该考的已闲置 39 天 · 这块板从未被推荐过", "estimated_minutes": 8, "factors": {"due_total": 2, "due_new": 1, "due_scheduled": 1, "due_malformed": 0, "overdue_days": 39, "idle_days": 39, "never_recommended": true, "recommend_gap_days": null}}, {"board": "特征值与特征向量", "top_node": "Fundamentals", "priority": -0.0456, "pending": 2, "idle_days": 56, "difficulty": "", "next_due": "", "why_this_board": "2 个节点到期（其中 2 张新卡） · 最该考的已闲置 56 天 · 这块板从未被推荐过", "estimated_minutes": 10, "factors": {"due_total": 2, "due_new": 2, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": 56, "never_recommended": true, "recommend_gap_days": null}}, {"board": "CS188 lecture 2", "top_node": "lecture 2", "priority": 0.0709, "pending": 1, "idle_days": null, "difficulty": "", "next_due": "", "why_this_board": "1 个节点到期（其中 1 张新卡） · 最该考的从未考察 · 这块板从未被推荐过", "estimated_minutes": 5, "factors": {"due_total": 1, "due_new": 1, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": null, "never_recommended": true, "recommend_gap_days": null}}], "upcoming": [], "due_nodes": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "Fundamentals", "board": "特征值与特征向量", "state": "new", "pick": -0.0456, "fsrs_due": "", "due_reason": "new", "last_examined": "2026-07-25T02:53:46Z", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "idle_days": 56}, {"node": "cs-61b-csm", "board": "CS 61B", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "csm-tutoring-unit-credit", "board": "CS 61B", "state": "new", "pick": -0.0478, "fsrs_due": "2026-08-11T13:56:58Z", "due_reason": "scheduled", "last_examined": "2026-08-11T13:55:58Z", "difficulty": "6.4133", "bucket": "learning_queue", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "idle_days": 39}, {"node": "lecture 2", "board": "CS188 lecture 2", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}], "boards": [{"board": "CS 61B", "due": 2, "due_new": 1, "due_scheduled": 1, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": "2026-08-11T13:56:58Z"}, {"board": "CS188 lecture 2", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 7, "earliest_overdue": ""}, {"board": "特征值与特征向量", "due": 2, "due_new": 2, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 1, "earliest_overdue": ""}, {"board": "递归与分治 (Recursion & Divide-Conquer)", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": ""}], "buckets": {"new": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "Fundamentals", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "fsrs_due": ""}, {"node": "cs-61b-csm", "board": "CS 61B", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "lecture 2", "board": "CS188 lecture 2", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}], "learning_queue": [{"node": "csm-tutoring-unit-credit", "board": "CS 61B", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "fsrs_due": "2026-08-11T13:56:58Z"}], "due_now": [], "due_today": [], "future": []}, "ineligible": {"placeholder": ["Eigenvalues-are-special-vectors-that-sat", "代理决策分析-0303()", "代理函数-(Agent-Function)", "代理类型：反射与规划", "反射代理的局限性引出了规划代理-(Planning-Agents)-的需求", "理性代理-(Rational-Agent)", "规划代理的特点", "规划的分类-1549()"], "test_excluded": [], "corrupt": []}, "stats": {"new": 2, "legacy": 2, "none": 2, "ineligible": 8, "test_excluded": 0, "corrupt": 0, "unassigned": 0, "due_nodes": 6, "future_nodes": 0}, "notification": {"title": "📚 今日复习 · CS 61B", "body": "csm-tutoring-unit-credit 等 2 节点待巩固 · 已闲置 39 天", "group": "canvas复习", "id": "canvas-review-2026-09-19"}, "rank_manifest": {"version": 2, "sha256": "218c838f4aef8ab00136bce48078ab0be10c7be44ca25c36f12d56e965d06f4a"}, "truncated": {"top_boards": true, "upcoming": false}}
+real 0.04
+user 0.03
+sys 0.00
+run4_rc=0
+--- run 5 ---
+{"unassigned_nodes": [], "schema_version": 3, "vault_id": "canvas-vault", "display_tz": "America/Los_Angeles", "date": "2026-09-19", "generated_at": "2026-09-19T17:15:56-07:00", "top_boards": [{"board": "CS 61B", "top_node": "csm-tutoring-unit-credit", "priority": -0.0478, "pending": 2, "idle_days": 39, "difficulty": "6.4133", "next_due": "", "why_this_board": "2 个节点到期（其中 1 张新卡） · 最早的已逾期 39 天 · 最该考的已闲置 39 天 · 这块板从未被推荐过", "estimated_minutes": 8, "factors": {"due_total": 2, "due_new": 1, "due_scheduled": 1, "due_malformed": 0, "overdue_days": 39, "idle_days": 39, "never_recommended": true, "recommend_gap_days": null}}, {"board": "特征值与特征向量", "top_node": "Fundamentals", "priority": -0.0456, "pending": 2, "idle_days": 56, "difficulty": "", "next_due": "", "why_this_board": "2 个节点到期（其中 2 张新卡） · 最该考的已闲置 56 天 · 这块板从未被推荐过", "estimated_minutes": 10, "factors": {"due_total": 2, "due_new": 2, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": 56, "never_recommended": true, "recommend_gap_days": null}}, {"board": "CS188 lecture 2", "top_node": "lecture 2", "priority": 0.0709, "pending": 1, "idle_days": null, "difficulty": "", "next_due": "", "why_this_board": "1 个节点到期（其中 1 张新卡） · 最该考的从未考察 · 这块板从未被推荐过", "estimated_minutes": 5, "factors": {"due_total": 1, "due_new": 1, "due_scheduled": 0, "due_malformed": 0, "overdue_days": null, "idle_days": null, "never_recommended": true, "recommend_gap_days": null}}], "upcoming": [], "due_nodes": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "Fundamentals", "board": "特征值与特征向量", "state": "new", "pick": -0.0456, "fsrs_due": "", "due_reason": "new", "last_examined": "2026-07-25T02:53:46Z", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "idle_days": 56}, {"node": "cs-61b-csm", "board": "CS 61B", "state": "legacy", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "csm-tutoring-unit-credit", "board": "CS 61B", "state": "new", "pick": -0.0478, "fsrs_due": "2026-08-11T13:56:58Z", "due_reason": "scheduled", "last_examined": "2026-08-11T13:55:58Z", "difficulty": "6.4133", "bucket": "learning_queue", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "idle_days": 39}, {"node": "lecture 2", "board": "CS188 lecture 2", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "state": "none", "pick": 0.0709, "fsrs_due": "", "due_reason": "new", "last_examined": "", "difficulty": "", "bucket": "new", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "idle_days": null}], "boards": [{"board": "CS 61B", "due": 2, "due_new": 1, "due_scheduled": 1, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": "2026-08-11T13:56:58Z"}, {"board": "CS188 lecture 2", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 7, "earliest_overdue": ""}, {"board": "特征值与特征向量", "due": 2, "due_new": 2, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 1, "earliest_overdue": ""}, {"board": "递归与分治 (Recursion & Divide-Conquer)", "due": 1, "due_new": 1, "due_scheduled": 0, "future": 0, "next_due": "", "placeholder": 0, "earliest_overdue": ""}], "buckets": {"new": [{"node": "Characteristic-Equation-for-Eigenvalues", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "Fundamentals", "board": "特征值与特征向量", "why_due": "新卡未排期，视同即刻到期 · 已闲置 56 天", "fsrs_due": ""}, {"node": "cs-61b-csm", "board": "CS 61B", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "lecture 2", "board": "CS188 lecture 2", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}, {"node": "my-recursion-notes", "board": "递归与分治 (Recursion & Divide-Conquer)", "why_due": "新卡未排期，视同即刻到期 · 从未考察", "fsrs_due": ""}], "learning_queue": [{"node": "csm-tutoring-unit-credit", "board": "CS 61B", "why_due": "学习中 · 已逾期 39 天（8月11日到期） · 已闲置 39 天", "fsrs_due": "2026-08-11T13:56:58Z"}], "due_now": [], "due_today": [], "future": []}, "ineligible": {"placeholder": ["Eigenvalues-are-special-vectors-that-sat", "代理决策分析-0303()", "代理函数-(Agent-Function)", "代理类型：反射与规划", "反射代理的局限性引出了规划代理-(Planning-Agents)-的需求", "理性代理-(Rational-Agent)", "规划代理的特点", "规划的分类-1549()"], "test_excluded": [], "corrupt": []}, "stats": {"new": 2, "legacy": 2, "none": 2, "ineligible": 8, "test_excluded": 0, "corrupt": 0, "unassigned": 0, "due_nodes": 6, "future_nodes": 0}, "notification": {"title": "📚 今日复习 · CS 61B", "body": "csm-tutoring-unit-credit 等 2 节点待巩固 · 已闲置 39 天", "group": "canvas复习", "id": "canvas-review-2026-09-19"}, "rank_manifest": {"version": 2, "sha256": "218c838f4aef8ab00136bce48078ab0be10c7be44ca25c36f12d56e965d06f4a"}, "truncated": {"top_boards": true, "upcoming": false}}
+real 0.04
+user 0.03
+sys 0.00
+run5_rc=0
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-stats-summary-20260919T171634.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-stats-summary-20260919T171634.txt"
new file mode 100644
index 00000000..c3563eab
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/measure-stats-summary-20260919T171634.txt"
@@ -0,0 +1,23 @@
+### 实测统计汇总 CARD-R-SLO 2026-09-19T17:16:55-0700
+（本文件首版为 2026-09-19T17:16 的脚本误跑：zsh 不展开变量内 glob 导致空文件名 → traceback；
+ 已就地重写为修正版汇总，未改动任何测量样本、未剔除样本。）
+
+--- review_overview_first_paint: measure-review_overview_first_paint-20260919T171124.txt ---
+rows=20 ok200=20 non200=[]
+p50=0.0099 p95(quantiles n=20 [18])=0.0391 max=0.0396
+--- rag_warm: measure-rag_warm-20260919T171144.txt ---
+rows=20 ok200=20 non200=[]
+p50=1.6687 p95(quantiles n=20 [18])=1.8665 max=1.8702
+--- rag_cold: measure-rag_cold-20260919T171226.txt ---
+rows=20 ok200=19 non200=[['000', '120.003677', '0']]
+p50=3.2870 p95(quantiles n=20 [18])=5.3628 max=5.3628
+--- kg_read: measure-kg_read-20260919T171134.txt ---
+rows=20 ok200=20 non200=[]
+p50=0.0036 p95(quantiles n=20 [18])=0.0271 max=0.0278
+--- review_rebuild: measure-review_rebuild-20260919T171556.txt ---
+n=5 raw=[0.05, 0.05, 0.05, 0.04, 0.04]
+p50=0.0500 p95(quantiles n=20 [18])=0.0500 max=0.0500
+
+--- live outputs before/after 逐字同 ---
+identical=YES
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/named-close-20260919T203835.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/named-close-20260919T203835.txt"
new file mode 100644
index 00000000..4a92273c
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/named-close-20260919T203835.txt"
@@ -0,0 +1,4 @@
+-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
+NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
+====================== 208 passed, 10 warnings in 16.76s =======================
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/named-open-20260919T202409.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/named-open-20260919T202409.txt"
new file mode 100644
index 00000000..386cc0e5
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/named-open-20260919T202409.txt"
@@ -0,0 +1,57 @@
+============================= test session starts ==============================
+platform darwin -- Python 3.14.4, pytest-9.0.2, pluggy-1.6.0
+rootdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend
+configfile: pytest.ini
+plugins: hypothesis-6.151.10, cov-7.1.0, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, schemathesis-4.14.3, bdd-8.1.0, langsmith-0.7.24, anyio-4.13.0
+asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
+collected 208 items
+
+tests/unit/test_validate_release_manifest.py ........................... [ 12%]
+........................................................................ [ 47%]
+.....................................................................    [ 80%]
+tests/unit/test_freeze_release_candidate.py ............................ [ 94%]
+............                                                             [100%]
+
+=============================== warnings summary ===============================
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
+    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
+    from pydantic.v1.fields import FieldInfo as FieldInfoV1
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
+    class SearchInterface(BaseModel):
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
+    import pkg_resources
+
+<frozen importlib._bootstrap>:491
+  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute
+
+<frozen importlib._bootstrap>:491
+  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute
+
+app/api/v1/endpoints/chat.py:807
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/chat.py:807: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
+    class HookEnrichRequest(BaseModel):
+
+app/api/v1/endpoints/metadata.py:103
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/metadata.py:103: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
+    canvas_path: str = Query(
+
+app/api/v1/endpoints/metadata.py:177
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/metadata.py:177: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
+    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356: PydanticDeprecatedSince211: The `__get_pydantic_core_schema__` method of the `BaseModel` class is deprecated. If you are calling `super().__get_pydantic_core_schema__` when overriding the method on a Pydantic model, consider using `handler(source)` instead. However, note that overriding this method on models can lead to unexpected side effects. Deprecated in Pydantic V2.11 to be removed in V3.0.
+    schema = annotation_get_schema(source, get_inner_schema)
+
+-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
+NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
+====================== 208 passed, 10 warnings in 20.24s =======================
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/named-validate-alone-20260919T202507.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/named-validate-alone-20260919T202507.txt"
new file mode 100644
index 00000000..7b141814
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/named-validate-alone-20260919T202507.txt"
@@ -0,0 +1,4 @@
+-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
+NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
+======================= 168 passed, 10 warnings in 2.44s =======================
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/neo4j-ro-20260919T202618.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/neo4j-ro-20260919T202618.txt"
new file mode 100644
index 00000000..2bf77b78
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/neo4j-ro-20260919T202618.txt"
@@ -0,0 +1,19 @@
+### 7691 只读口径 CARD-R-SLO 2026-09-19T20:26:18-0700
+
+本卡对 7691（现网 Neo4j）的全部触达 = 经 8011 只读 GET：
+  GET /api/v1/health/knowledge-graph ×20（measure-kg_read-20260919T171134.txt）+ 环境探针 1 次（env-probe-20260919T201108*.txt 同形态）
+  ⇒ 白名单直连语句【未使用】（不需要）。
+
+白名单两条 execute_read 语句原文（如需直连复跑，形态如下；密码来自 backend/.env，⛔ 不 echo）：
+  1) RETURN 1
+  2) MATCH (n) RETURN count(n) AS c
+
+driver 形态（只读访问模式）：
+  from neo4j import GraphDatabase
+  driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))  # 值来自 backend/.env，不落档
+  with driver.session(database=NEO4J_DATABASE, default_access_mode=neo4j.READ_ACCESS) as s:
+      s.execute_read(lambda tx: tx.run("RETURN 1").single())
+  driver.close()
+
+禁连：7687（未触达）/ 7692（本卡不用）。写端点（POST /memory/episodes、/traces/replay-fallbacks、/index/refresh-changed、/overview/refresh）一个未打。
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/open.nodeids" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/open.nodeids"
new file mode 100644
index 00000000..1354c1c3
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/open.nodeids"
@@ -0,0 +1,32 @@
+FAILED tests/unit/test_agent_memory_injection.py::TestMemoryInjection::test_graceful_degradation_on_exception
+FAILED tests/unit/test_agent_service_neo4j_memory.py::TestEdgeCases::test_neo4j_query_error_returns_empty
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_difficulty_context_in_prompt
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_no_difficulty_map_no_extra_fields
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestGetDifficultyData::test_memory_service_unavailable_returns_none
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_chinese_vault_id_not_collapsed_to_default
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_subject_id_optional_backward_compat
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_emoji_stripped
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_provided_triggers_context_var_injection
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_with_special_chars_sanitized
+FAILED tests/unit/test_epic30_memory_pipeline.py::TestRecordTemporalEventLifecycle::test_p0_neo4j_write_failure_degrades_silently
+FAILED tests/unit/test_epic36_gap_coverage.py::TestGetRelatedMemoriesReturnStructure::test_query_exception_returns_empty
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestCancelEndpoint::test_cancel_nonexistent_session_404
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestErrorResponses::test_404_error_format
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestProgressEndpoint::test_progress_invalid_session_404
+FAILED tests/unit/test_neo4j_fulltext_index.py::TestEnsureFulltextIndex::test_ensure_fulltext_index_idempotent
+FAILED tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestMergedViewEdgeCases::test_merged_view_sort_newest_first
+FAILED tests/unit/test_rag_p0_doc_type_filter.py::test_strip_whiteboard_removes_admonition_callouts
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_normalizes_schema
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_passes_node_id_filter_to_search_memories
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_sorts_by_timestamp_desc
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_filter_post_merge
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_none_is_no_filter
+FAILED tests/unit/test_story_38_6_scoring_reliability.py::TestAC4MergedView::test_get_learning_history_merges_failed_scores
+FAILED tests/unit/test_vault_doc_roles.py::test_live_vault_enforce_clean
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_honors_nested_metadata_json_subject
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_physics_filters_to_physics_only
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_common_and_no_match_returns_empty
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_explicit_match_returns_only_common_notes
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_no_history_generates_standard_question
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_with_history_generates_alternative_question
+FAILED tests/unit/test_websocket_endpoints.py::TestWebSocketEndpoint::test_validate_session_handles_validator_error
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/pick-help.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/pick-help.txt"
new file mode 100644
index 00000000..1d94d065
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/pick-help.txt"
@@ -0,0 +1,13 @@
+usage: daily_review_pick.py [-h] --vault VAULT [--state STATE] [--now NOW]
+                            [--write]
+
+每日复习选板
+
+options:
+  -h, --help     show this help message and exit
+  --vault VAULT
+  --state STATE  daily-review.state.json (只读, 取 board_last_recommended /
+                 board_done / snoozed)
+  --now NOW      ISO 时间覆盖 (测试用)
+  --write        写 outputs/今日复习.md+json
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/pre-20260919T170257.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/pre-20260919T170257.txt"
new file mode 100644
index 00000000..d7b5b7ca
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/pre-20260919T170257.txt"
@@ -0,0 +1,9 @@
+### CARD-R-SLO 先红 (b)①-③  落档 2026-09-20T00:02:57Z
+--- (b)① git grep -n 'slo-manifest' -- docs backend/scripts scripts | wc -l
+       0
+--- (b)① 验伪锚: 同命令 -- backend/tests
+       2
+--- (b)② test -e docs/release-evidence/slo-manifest.yaml; echo rc
+rc=1
+--- (b)③ grep -c 'slo-manifest.yaml' docs/release-evidence/README.md
+0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/pre-consumer-20260919T171717.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/pre-consumer-20260919T171717.txt"
new file mode 100644
index 00000000..78f66ac3
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/pre-consumer-20260919T171717.txt"
@@ -0,0 +1,19 @@
+### (b)⑤ 消费契约先红 CARD-R-SLO 2026-09-19T17:17:17-0700
+tmp: $TMP=/tmp/rslo-p10c/consumer ；j08.json 为 symlink → /tmp/rslo-p10c/consumer/example-backfill-d5/journeys/J08/manifest.json
+（卡文 §二.5 用 $TMP/j08.json 裸路径——实测校验器 S6 要求 <rc>/journeys/<Jxx>/ 目录结构，裸文件按 [S6] 必红；
+ 故文件实体放在结构合规路径，j08.json symlink 指入；resolve() 跟 symlink ⇒ S6 通过。此为主路径之外的唯一形状修正。）
+
+--- A. validator（本卡新增 rev-check 尚不存在；校验器对该 tmp 件应绿）---
+✅ PASS /private/tmp/rslo-p10c/consumer/example-backfill-d5/journeys/J08/manifest.json
+
+合计 1 份 manifest, 失败 0 份。
+⚠️  已弃权 artifact checksum 真验 (--skip-artifact-verify)。
+A_rc=0
+
+--- B. 本卡新增对照脚本（yaml 尚不存在 → 必红 FileNotFoundError）---
+Traceback (most recent call last):
+  File "<string>", line 1, in <module>
+    import yaml,json,sys; y=yaml.safe_load(open('docs/release-evidence/slo-manifest.yaml')); m=json.load(open(sys.argv[1])); r=m['slo']['manifest_revision']; assert r==y['revision'], ('revision 不在 yaml', r, y['revision']); names={x['metric'] for x in y['metrics']}; bad=[x['metric'] for x in m['slo']['measurements'] if x['metric'] not in names]; assert not bad, ('metric 不在 yaml', bad); print('rev_check=OK', r, len(names))
+                                           ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+FileNotFoundError: [Errno 2] No such file or directory: 'docs/release-evidence/slo-manifest.yaml'
+B_rc=1
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/probe-cold4-replay-20260919T171547.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/probe-cold4-replay-20260919T171547.txt"
new file mode 100644
index 00000000..0b05226f
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/probe-cold4-replay-20260919T171547.txt"
@@ -0,0 +1,3 @@
+### cold #4 replay probe 2026-09-19T17:15:47-0700 (q_sha16=def863eced044422)
+200 1.672106 452
+curl_rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/rag-queries-seed-20260919T171124.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/rag-queries-seed-20260919T171124.txt"
new file mode 100644
index 00000000..64b65827
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/rag-queries-seed-20260919T171124.txt"
@@ -0,0 +1 @@
+4dd05b33342dfdcad3ddaa4de89834592fa45631b451b404b2f26676c91e2afa  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-rslo/rag-queries.txt
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/rag-queries.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/rag-queries.txt"
new file mode 100644
index 00000000..a51fdd33
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/rag-queries.txt"
@@ -0,0 +1,20 @@
+代理函数-(Agent-Function).md
+反射代理的局限性引出了规划代理-(Planning-Agents)-的需求.md
+理性代理-(Rational-Agent).md
+代理决策分析-0303().md
+规划的分类-1549().md
+规划代理的特点.md
+代理类型：反射与规划.md
+Characteristic-Equation-for-Eigenvalues.md
+cs-61b-csm.md
+csm-tutoring-unit-credit.md
+Eigenvalues-are-special-vectors-that-sat.md
+Fundamentals.md
+lecture 2.md
+my-recursion-notes.md
+递归与分治 (Recursion & Divide-Conquer).md
+特征值与特征向量.md
+线性代数.md
+CS 61B.md
+CS.md
+CS188 lecture 2.md
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/rev-check-post-20260919T171908.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/rev-check-post-20260919T171908.txt"
new file mode 100644
index 00000000..f2fdb9a6
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/rev-check-post-20260919T171908.txt"
@@ -0,0 +1,18 @@
+### (f)③ revision 对照脚本（改后）2026-09-19T17:19:08-0700
+--- 主判据 ---
+rev_check=OK slo-manifest@2026-09-19-r1 9
+main_rc=0
+
+--- 验伪锚: tmp revision 改成 slo-manifest@1999-01-01-r9 ---
+anchor patched
+Traceback (most recent call last):
+  File "<string>", line 1, in <module>
+    import yaml,json,sys; y=yaml.safe_load(open("docs/release-evidence/slo-manifest.yaml")); m=json.load(open(sys.argv[1])); r=m["slo"]["manifest_revision"]; assert r==y["revision"], ("revision 不在 yaml", r, y["revision"]); names={x["metric"] for x in y["metrics"]}; bad=[x["metric"] for x in m["slo"]["measurements"] if x["metric"] not in names]; assert not bad, ("metric 不在 yaml", bad); print("rev_check=OK", r, len(names))
+                                                                                                                                                                     ^^^^^^^^^^^^^^^^
+AssertionError: ('revision 不在 yaml', 'slo-manifest@1999-01-01-r9', 'slo-manifest@2026-09-19-r1')
+anchor_rc=1
+
+--- 还原 tmp revision 为 …-r1 ---
+restored
+rev_check=OK slo-manifest@2026-09-19-r1 9
+restored_rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-close-20260919T202638.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-close-20260919T202638.txt"
new file mode 100644
index 00000000..af494ef7
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-close-20260919T202638.txt"
@@ -0,0 +1,7 @@
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_common_and_no_match_returns_empty
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_honors_nested_metadata_json_subject
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_no_history_generates_standard_question
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_with_history_generates_alternative_question
+FAILED tests/unit/test_websocket_endpoints.py::TestWebSocketEndpoint::test_validate_session_handles_validator_error
+= 32 failed, 5771 passed, 44 skipped, 13 xfailed, 231 warnings in 342.28s (0:05:42) =
+rc=1
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-close-diff-20260919T203835.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-close-diff-20260919T203835.txt"
new file mode 100644
index 00000000..4045d1cf
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-close-diff-20260919T203835.txt"
@@ -0,0 +1,6 @@
+### unit 目录级 close vs 基线 diff 2026-09-19T20:38:35-0700
+base.nodeids=33 close.nodeids=32
+--- diff base close （只允许 < 行）---
+3d2
+< FAILED tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422
+diff_rc=1
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-close-full-20260919T203241.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-close-full-20260919T203241.txt"
new file mode 100644
index 00000000..2ff51419
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-close-full-20260919T203241.txt"
@@ -0,0 +1,926 @@
+============================= test session starts ==============================
+platform darwin -- Python 3.14.4, pytest-9.0.2, pluggy-1.6.0
+rootdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend
+configfile: pytest.ini
+plugins: hypothesis-6.151.10, cov-7.1.0, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, schemathesis-4.14.3, bdd-8.1.0, langsmith-0.7.24, anyio-4.13.0
+asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
+collected 5860 items
+
+tests/unit/grouping/test_analyze_canvas.py ........                      [  0%]
+tests/unit/grouping/test_factory_and_constants.py .............          [  0%]
+tests/unit/grouping/test_helpers.py .............                        [  0%]
+tests/unit/grouping/test_perform_clustering.py ...........               [  0%]
+tests/unit/test_a7_honest_failure.py ........                            [  0%]
+tests/unit/test_acp_prompt_externalization.py ...........                [  1%]
+tests/unit/test_agent_context_injection.py .....                         [  1%]
+tests/unit/test_agent_memory_injection.py ......F....                    [  1%]
+tests/unit/test_agent_memory_trigger.py ................................ [  1%]
+..........                                                               [  2%]
+tests/unit/test_agent_routing_engine.py ................................ [  2%]
+..........................                                               [  3%]
+tests/unit/test_agent_service_comparison.py ...............              [  3%]
+tests/unit/test_agent_service_extraction.py ............................ [  3%]
+.ss..                                                                    [  3%]
+tests/unit/test_agent_service_neo4j_memory.py ..................F....    [  4%]
+tests/unit/test_agent_service_user_understanding.py ...........          [  4%]
+tests/unit/test_agent_templates_smoke.py ............................... [  5%]
+...................                                                      [  5%]
+tests/unit/test_agentic_rag_vault_scope.py .......................       [  5%]
+tests/unit/test_agents_multimodal.py ....................                [  6%]
+tests/unit/test_archive_legacy_lance_tables_g24.py ..................... [  6%]
+.                                                                        [  6%]
+tests/unit/test_audit_guardian.py ...........                            [  6%]
+tests/unit/test_background_task_manager.py .....                         [  6%]
+tests/unit/test_batch_orchestrator.py .................................  [  7%]
+tests/unit/test_belief_version_chain.py .........                        [  7%]
+tests/unit/test_board_manifest_unreach_t5e.py ...........                [  7%]
+tests/unit/test_bug_tracker.py ......................                    [  7%]
+tests/unit/test_cache_configuration.py ....xx...x.x.                     [  8%]
+tests/unit/test_calibration_tracker.py ................................  [  8%]
+tests/unit/test_candidate_callout.py ............                        [  8%]
+tests/unit/test_candidate_expiry_service.py ....................         [  9%]
+tests/unit/test_candidate_service.py ..............                      [  9%]
+tests/unit/test_candidate_state_machine.py ............................. [ 10%]
+............                                                             [ 10%]
+tests/unit/test_candidate_writer.py ................                     [ 10%]
+tests/unit/test_canvas_edge_bulk_sync.py .........                       [ 10%]
+tests/unit/test_canvas_edge_sync.py .........                            [ 10%]
+tests/unit/test_canvas_episode_v1.py ...................                 [ 11%]
+tests/unit/test_canvas_memory_trigger.py ...................             [ 11%]
+tests/unit/test_canvas_projection_sync.py .............                  [ 11%]
+tests/unit/test_canvas_service_concurrency.py ................           [ 11%]
+tests/unit/test_canvas_validation.py ................                    [ 12%]
+tests/unit/test_card_state_concurrent_write.py ...                       [ 12%]
+tests/unit/test_chat_context_assembler.py .............................. [ 12%]
+....................                                                     [ 13%]
+tests/unit/test_chat_endpoint.py ................                        [ 13%]
+tests/unit/test_check_readme_claims.py ................................. [ 13%]
+........................................................................ [ 15%]
+...............                                                          [ 15%]
+tests/unit/test_circuit_breaker.py ............                          [ 15%]
+tests/unit/test_config_drift.py .........                                [ 15%]
+tests/unit/test_config_neo4j.py .............                            [ 16%]
+tests/unit/test_context_cache_key.py ....                                [ 16%]
+tests/unit/test_context_enrichment_2hop.py .................             [ 16%]
+tests/unit/test_context_enrichment_get_node_content.py ................. [ 16%]
+...                                                                      [ 16%]
+tests/unit/test_cost_tracker.py .....                                    [ 16%]
+tests/unit/test_create_fsrs_manager.py ..........                        [ 16%]
+tests/unit/test_cross_canvas_failsoft.py ...                             [ 17%]
+tests/unit/test_cross_canvas_removal.py .......                          [ 17%]
+tests/unit/test_cross_subject_bridge_group_isolation.py ..........       [ 17%]
+tests/unit/test_cypher_helpers.py ....................                   [ 17%]
+tests/unit/test_dashboard_statistics.py ...................              [ 18%]
+tests/unit/test_dead_letter_bounded_t6c.py ............................. [ 18%]
+..........                                                               [ 18%]
+tests/unit/test_deep_research_fallback.py ........................       [ 19%]
+tests/unit/test_degraded_flag_propagation.py .....                       [ 19%]
+tests/unit/test_deploy_vault_sh.py ..................................... [ 19%]
+..........sssss......................................................ss. [ 21%]
+...................ss................................................... [ 22%]
+........................................................................ [ 23%]
+...............................................                          [ 24%]
+tests/unit/test_difficulty_adaptive.py ................................. [ 24%]
+.........................                                                [ 25%]
+tests/unit/test_difficulty_canvas_integration.py .F...............FF.... [ 25%]
+                                                                         [ 25%]
+tests/unit/test_difficulty_matcher.py ...................                [ 25%]
+tests/unit/test_docker_compose_config.py ............                    [ 26%]
+tests/unit/test_edge_rationale_fallback.py ............                  [ 26%]
+tests/unit/test_embedder_factory.py .......                              [ 26%]
+tests/unit/test_enrich_context_vault_isolation.py ..FFF.FF               [ 26%]
+tests/unit/test_epic30_memory_pipeline.py ..............F............... [ 27%]
+..........                                                               [ 27%]
+tests/unit/test_epic32_p0_fixes.py .............                         [ 27%]
+tests/unit/test_epic36_gap_coverage.py ....F............                 [ 27%]
+tests/unit/test_episode_worker_coverage_epw.py ......................... [ 28%]
+......................                                                   [ 28%]
+tests/unit/test_episode_worker_retry.py .....                            [ 28%]
+tests/unit/test_error_aggregator.py ..................                   [ 29%]
+tests/unit/test_error_classification_mapping.py ........................ [ 29%]
+                                                                         [ 29%]
+tests/unit/test_error_extractor.py ............                          [ 29%]
+tests/unit/test_error_rebuild_service.py .............                   [ 29%]
+tests/unit/test_error_writer.py .................                        [ 30%]
+tests/unit/test_event_bus.py ...............................             [ 30%]
+tests/unit/test_exam_models_rubric_required_u2a.py ........              [ 30%]
+tests/unit/test_exam_sync_node_group_isolation.py .....                  [ 30%]
+tests/unit/test_extraction_validator.py ............                     [ 31%]
+tests/unit/test_failure_observability.py ...............sss...........   [ 31%]
+tests/unit/test_faithfulness_check.py ..............                     [ 31%]
+tests/unit/test_faithfulness_check_boundary.py .........                 [ 32%]
+tests/unit/test_four_state_injection.py ................................ [ 32%]
+.........                                                                [ 32%]
+tests/unit/test_freeze_release_candidate.py ............................ [ 33%]
+............                                                             [ 33%]
+tests/unit/test_frontmatter_signals.py ......                            [ 33%]
+tests/unit/test_fsrs_manager.py .....................................    [ 34%]
+tests/unit/test_fsrs_state_query.py ................                     [ 34%]
+tests/unit/test_fusion_report.py .........                               [ 34%]
+tests/unit/test_fusion_strategy_override.py ........                     [ 34%]
+tests/unit/test_g24_lance_legacy_table_removal.py ..........             [ 34%]
+tests/unit/test_g25_journal_namespace.py ...........................     [ 35%]
+tests/unit/test_graphiti_client.py ......................                [ 35%]
+tests/unit/test_graphiti_client_mock_performance.py .....                [ 35%]
+tests/unit/test_graphiti_client_unification.py ....                      [ 35%]
+tests/unit/test_graphiti_json_dual_write.py .......                      [ 35%]
+tests/unit/test_graphiti_memory_reader.py ......                         [ 36%]
+tests/unit/test_graphiti_neo4j_calls.py ......                           [ 36%]
+tests/unit/test_graphiti_structured_writer.py ....................       [ 36%]
+tests/unit/test_group_id_compat.py ...........................           [ 36%]
+tests/unit/test_group_id_dynamic_binding.py .....................        [ 37%]
+tests/unit/test_group_id_migration.py ................                   [ 37%]
+tests/unit/test_health_detailed.py ......                                [ 37%]
+tests/unit/test_hybrid_search_activation.py .......................      [ 38%]
+tests/unit/test_identity_registry.py .......                             [ 38%]
+tests/unit/test_intelligent_parallel_endpoints.py .........F.F...F...... [ 38%]
+......                                                                   [ 38%]
+tests/unit/test_internal_api_key_p0_2_hardening.py .............         [ 38%]
+tests/unit/test_kg_health.py .....                                       [ 39%]
+tests/unit/test_kg_relevance_weighted.py ........................        [ 39%]
+tests/unit/test_l1_llm_router.py ...............                         [ 39%]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py ...................... [ 40%]
+.............                                                            [ 40%]
+tests/unit/test_lancedb_isolation_assertions.py .............            [ 40%]
+tests/unit/test_lancedb_vault_isolation.py ...............               [ 40%]
+tests/unit/test_langgraph_async_conditional_edge_smoke.py ..             [ 40%]
+tests/unit/test_live_port_guard_contract.py ............................ [ 41%]
+........................................................................ [ 42%]
+....................................................                     [ 43%]
+tests/unit/test_llm_call_logger.py ..............................        [ 43%]
+tests/unit/test_markdown_image_extractor.py ............................ [ 44%]
+....                                                                     [ 44%]
+tests/unit/test_mastery_api.py ...........................               [ 44%]
+tests/unit/test_mastery_engine_bkt.py .......................            [ 45%]
+tests/unit/test_mastery_engine_effective.py ............                 [ 45%]
+tests/unit/test_mastery_engine_fsrs.py ..................                [ 45%]
+tests/unit/test_mastery_engine_level.py ..................               [ 46%]
+tests/unit/test_mastery_engine_misc.py ...............................   [ 46%]
+tests/unit/test_mastery_fsrs_projection_boundary.py ......               [ 46%]
+tests/unit/test_mastery_fusion.py ..........................             [ 47%]
+tests/unit/test_mastery_injection_memory_contract.py ............        [ 47%]
+tests/unit/test_mastery_property.py .......                              [ 47%]
+tests/unit/test_mastery_state.py ..............................          [ 48%]
+tests/unit/test_mastery_store.py .................                       [ 48%]
+tests/unit/test_mcp_switch_vault_tool.py ..                              [ 48%]
+tests/unit/test_memory_read_scope_g41a.py ........                       [ 48%]
+tests/unit/test_memory_service_batch.py ......                           [ 48%]
+tests/unit/test_memory_service_contextvar_leak.py ........               [ 48%]
+tests/unit/test_memory_service_structured_routing.py .........           [ 48%]
+tests/unit/test_memory_service_write_retry.py ssssssssssssssssss         [ 49%]
+tests/unit/test_migrate_canvas_group_isolation.py ....................   [ 49%]
+tests/unit/test_migrate_neo4j_data.py ...............................    [ 50%]
+tests/unit/test_mock_degradation_transparency.py ....................... [ 50%]
+.......                                                                  [ 50%]
+tests/unit/test_multimodal_fixes.py ......................               [ 50%]
+tests/unit/test_multimodal_path_security.py ................             [ 51%]
+tests/unit/test_mutation_kill_identity_r3.py ........................... [ 51%]
+.........................................................                [ 52%]
+tests/unit/test_neo4j_client.py ........................................ [ 53%]
+....................                                                     [ 53%]
+tests/unit/test_neo4j_field_consistency.py .......                       [ 53%]
+tests/unit/test_neo4j_fulltext_index.py ...F...                          [ 53%]
+tests/unit/test_neo4j_health.py ..........                               [ 54%]
+tests/unit/test_nfr_cache_bounds.py ..............                       [ 54%]
+tests/unit/test_observer_token_fail_closed.py ............               [ 54%]
+tests/unit/test_post_turn_request_vault_id.py .......                    [ 54%]
+tests/unit/test_profile_source_ids.py ...............                    [ 54%]
+tests/unit/test_prompt_injection_context.py ......s                      [ 55%]
+tests/unit/test_prompt_injection_guard.py .............................. [ 55%]
+                                                                         [ 55%]
+tests/unit/test_prompt_registry.py .................................     [ 56%]
+tests/unit/test_pydantic_contracts.py ....................               [ 56%]
+tests/unit/test_qa_38_4_dual_write_extra.py ........x.                   [ 56%]
+tests/unit/test_qa_38_5_fallback_extra.py .......                        [ 56%]
+tests/unit/test_qa_38_6_scoring_reliability_extra.py ........F.ss..      [ 56%]
+tests/unit/test_question_generator_mastery_data.py ...............       [ 57%]
+tests/unit/test_question_registry.py ........                            [ 57%]
+tests/unit/test_rag_multimodal_integration.py .........................  [ 57%]
+tests/unit/test_rag_p0_doc_type_filter.py ..........F......              [ 58%]
+tests/unit/test_react_agent.py ...                                       [ 58%]
+tests/unit/test_read_scope_callers_g41a.py ...............               [ 58%]
+tests/unit/test_recommendation_group_filter.py ..........                [ 58%]
+tests/unit/test_record_learning_memory_docstring.py .....                [ 58%]
+tests/unit/test_remediation_strategy.py ......................           [ 59%]
+tests/unit/test_rerank_service.py ..................                     [ 59%]
+tests/unit/test_retrieval_regression_metric_guard.py ..........          [ 59%]
+tests/unit/test_review_app.py .......................................... [ 60%]
+.........................................................                [ 61%]
+tests/unit/test_review_difficulty_adaptation.py .................        [ 61%]
+tests/unit/test_review_enrichment_signal.py ....                         [ 61%]
+tests/unit/test_review_history_pagination.py .................           [ 61%]
+tests/unit/test_review_mode_support.py ...............                   [ 62%]
+tests/unit/test_review_overview.py ..................................... [ 62%]
+........................................................................ [ 63%]
+........                                                                 [ 64%]
+tests/unit/test_review_service_error_handling.py ..........              [ 64%]
+tests/unit/test_review_service_fsrs.py ................................. [ 64%]
+..................                                                       [ 65%]
+tests/unit/test_s02_entity_types.py ............................         [ 65%]
+tests/unit/test_s02_search_upgrade.py ....................               [ 65%]
+tests/unit/test_safety_meta_rule_in_prompt.py ....                       [ 66%]
+tests/unit/test_schema_gate.py ....                                      [ 66%]
+tests/unit/test_scoring_faithfulness_not_applicable.py ..........        [ 66%]
+tests/unit/test_scoring_scale_fix.py ..................................  [ 66%]
+tests/unit/test_security_p0_vulnerabilities.py ........                  [ 66%]
+tests/unit/test_service_status_contract.py ............................  [ 67%]
+tests/unit/test_session_manager.py ..................................... [ 68%]
+                                                                         [ 68%]
+tests/unit/test_session_progress.py ..........                           [ 68%]
+tests/unit/test_sharpness_report.py ......                               [ 68%]
+tests/unit/test_source_description_contract.py ................          [ 68%]
+tests/unit/test_startup_health_check.py ................                 [ 68%]
+tests/unit/test_state_graph_l1_routing.py ........                       [ 69%]
+tests/unit/test_storage_health.py .......................                [ 69%]
+tests/unit/test_story_1_7_env_config.py .............                    [ 69%]
+tests/unit/test_story_2_3_error_reminders.py ..............F.FF.FF       [ 70%]
+tests/unit/test_story_30_10_idempotency.py ........sssssssss             [ 70%]
+tests/unit/test_story_30_11_batch_parallel.py ...........                [ 70%]
+tests/unit/test_story_30_12_agent_trigger.py .......                     [ 70%]
+tests/unit/test_story_30_13_batch_idempotency.py ...........             [ 70%]
+tests/unit/test_story_30_22_agent_trigger_deep.py ...................... [ 71%]
+...............................................                          [ 71%]
+tests/unit/test_story_30_24_boundary.py ...............................x [ 72%]
+xxxx                                                                     [ 72%]
+tests/unit/test_story_30_6_color_change.py ......                        [ 72%]
+tests/unit/test_story_30_7_plugin_init.py ........                       [ 72%]
+tests/unit/test_story_31a2_ac1_neo4j_priority.py .......                 [ 72%]
+tests/unit/test_story_31a2_ac2_client_method.py ..........               [ 73%]
+tests/unit/test_story_31a2_ac3_persistence.py ...                        [ 73%]
+tests/unit/test_story_31a2_ac4_pagination.py ................            [ 73%]
+tests/unit/test_story_31a2_ac5_api_injection.py .........                [ 73%]
+tests/unit/test_story_33_10_runtime_defects.py ..............            [ 73%]
+tests/unit/test_story_38_1_ac1_auto_trigger.py .........                 [ 73%]
+tests/unit/test_story_38_1_ac2_failure_handling.py ....                  [ 74%]
+tests/unit/test_story_38_1_ac3_startup_recovery.py ........              [ 74%]
+tests/unit/test_story_38_1_review_fixes.py ......                        [ 74%]
+tests/unit/test_story_38_2_episode_recovery.py ................          [ 74%]
+tests/unit/test_story_38_2_qa_supplement.py .................            [ 74%]
+tests/unit/test_story_38_3_edge_cases.py ...........                     [ 75%]
+tests/unit/test_story_38_3_fsrs_init_guarantee.py .....................  [ 75%]
+tests/unit/test_story_38_4_dual_write_default.py ..x.xx.                 [ 75%]
+tests/unit/test_story_38_5_canvas_crud_degradation.py .........          [ 75%]
+tests/unit/test_story_38_6_scoring_reliability.py .............F...      [ 75%]
+tests/unit/test_story_38_8_fallback_sync.py ............................ [ 76%]
+..                                                                       [ 76%]
+tests/unit/test_study_question_deep_mode.py ........                     [ 76%]
+tests/unit/test_subject_config_vault.py .....................            [ 76%]
+tests/unit/test_subject_isolation.py ..........................          [ 77%]
+tests/unit/test_subject_resolver.py .................................... [ 78%]
+...                                                                      [ 78%]
+tests/unit/test_subjects_group_isolation.py ........                     [ 78%]
+tests/unit/test_supplementary_reranker.py .............................. [ 78%]
+..........................                                               [ 79%]
+tests/unit/test_supplementary_search_service.py ........................ [ 79%]
+...............................                                          [ 80%]
+tests/unit/test_sync_batch_auth.py .......                               [ 80%]
+tests/unit/test_sync_exception_classification.py ......                  [ 80%]
+tests/unit/test_sync_group_isolation.py .............                    [ 80%]
+tests/unit/test_sync_payload_validation.py ...........                   [ 80%]
+tests/unit/test_sync_segment_commit.py ..................                [ 81%]
+tests/unit/test_system_endpoint_auth.py ............                     [ 81%]
+tests/unit/test_textbook_removal.py .............                        [ 81%]
+tests/unit/test_traces_backlog_t6c.py .................................. [ 82%]
+.                                                                        [ 82%]
+tests/unit/test_ttlcache_transparency.py ...........                     [ 82%]
+tests/unit/test_validate_release_manifest.py ........................... [ 82%]
+........................................................................ [ 83%]
+.....................................................................    [ 85%]
+tests/unit/test_vault_admission.py ..............                        [ 85%]
+tests/unit/test_vault_backfill.py ...........                            [ 85%]
+tests/unit/test_vault_doc_roles.py ........F............................ [ 86%]
+........................................................................ [ 87%]
+..........                                                               [ 87%]
+tests/unit/test_vault_identity_registry.py ........                      [ 87%]
+tests/unit/test_vault_init_service.py ........                           [ 87%]
+tests/unit/test_vault_install_manifest.py .............................. [ 88%]
+........................................................................ [ 89%]
+........................................................................ [ 90%]
+..                                                                       [ 90%]
+tests/unit/test_vault_lint.py .......................................... [ 91%]
+.................................................                        [ 92%]
+tests/unit/test_vault_notes_group_filter.py .FFF.F                       [ 92%]
+tests/unit/test_vault_scope_409.py ..................................... [ 93%]
+.                                                                        [ 93%]
+tests/unit/test_vault_scope_read_g41a.py ............................... [ 93%]
+......                                                                   [ 93%]
+tests/unit/test_vault_switch.py ..........................               [ 94%]
+tests/unit/test_vault_switch_coordinator.py .......                      [ 94%]
+tests/unit/test_vault_templates.py ...............                       [ 94%]
+tests/unit/test_verification_dedup.py FF.............                    [ 94%]
+tests/unit/test_verification_group_filter.py ..........                  [ 95%]
+tests/unit/test_verification_service_activation.py ...............       [ 95%]
+tests/unit/test_verification_service_injection.py .....                  [ 95%]
+tests/unit/test_w4_sentinel_rebind.py .................................. [ 95%]
+.................................                                        [ 96%]
+tests/unit/test_wave5_stageb_continued_vault_id_injection.py ........... [ 96%]
+.........................                                                [ 97%]
+tests/unit/test_wave5_stageb_vault_id_injection.py ..................... [ 97%]
+.......                                                                  [ 97%]
+tests/unit/test_websocket_endpoints.py .............................F... [ 98%]
+....                                                                     [ 98%]
+tests/unit/test_wikilink_context_service.py ............................ [ 98%]
+................                                                         [ 98%]
+tests/unit/test_wikilink_graph_service.py .............................. [ 99%]
+.....                                                                    [ 99%]
+tests/unit/test_wikilink_parser.py ........................              [100%]
+
+=================================== FAILURES ===================================
+__________ TestMemoryInjection.test_graceful_degradation_on_exception __________
+tests/unit/test_agent_memory_injection.py:273: in test_graceful_degradation_on_exception
+    result = await service._get_learning_memories(
+app/services/agent_service.py:2086: in _get_learning_memories
+    memories = await asyncio.wait_for(
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/tasks.py:488: in wait_for
+    return await fut
+           ^^^^^^^^^
+tests/unit/test_agent_memory_injection.py:63: in search_memories
+    raise Exception("Mock search failure")
+E   Exception: Mock search failure
+---------------------------- Captured stdout setup -----------------------------
+{"event": "AgentService initialized without configured AI client - API calls will fail", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T03:32:52.665048Z"}
+{"event": "AgentService will use LearningMemoryClient for historical context", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T03:32:52.665090Z"}
+{"event": "AgentService initialized without CanvasService - nodes will not be written to Canvas", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T03:32:52.665121Z"}
+{"event": "AgentService Phase 2: Tool calling disabled (ENABLE_TOOL_CALLING=false)", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T03:32:52.665146Z"}
+{"event": "AgentService Phase 4: React Agent ENABLED (ENABLE_REACT_AGENT=true)", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T03:32:52.665167Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.agent_service:agent_service.py:1400 {'event': 'AgentService initialized without configured AI client - API calls will fail', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T03:32:52.665048Z'}
+INFO     app.services.agent_service:agent_service.py:1405 {'event': 'AgentService will use LearningMemoryClient for historical context', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T03:32:52.665090Z'}
+WARNING  app.services.agent_service:agent_service.py:1427 {'event': 'AgentService initialized without CanvasService - nodes will not be written to Canvas', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T03:32:52.665121Z'}
+INFO     app.services.agent_service:agent_service.py:1444 {'event': 'AgentService Phase 2: Tool calling disabled (ENABLE_TOOL_CALLING=false)', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T03:32:52.665146Z'}
+INFO     app.services.agent_service:agent_service.py:1449 {'event': 'AgentService Phase 4: React Agent ENABLED (ENABLE_REACT_AGENT=true)', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T03:32:52.665167Z'}
+______________ TestEdgeCases.test_neo4j_query_error_returns_empty ______________
+tests/unit/test_agent_service_neo4j_memory.py:521: in test_neo4j_query_error_returns_empty
+    result = await agent_service_with_neo4j._get_learning_memories(
+app/services/agent_service.py:2074: in _get_learning_memories
+    result = await asyncio.wait_for(
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/tasks.py:488: in wait_for
+    return await fut
+           ^^^^^^^^^
+app/services/agent_service.py:2183: in _query_neo4j_memories
+    results = await self._neo4j_client.run_query(cypher_query, **params)
+              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:2333: in _execute_mock_call
+    raise effect
+E   Exception: Neo4j connection failed
+---------------------------- Captured stdout setup -----------------------------
+{"event": "AgentService initialized without configured AI client - API calls will fail", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T03:32:53.994769Z"}
+{"event": "AgentService initialized without LearningMemoryClient - historical context fallback unavailable when Neo4j is down", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T03:32:53.994809Z"}
+{"event": "AgentService will use Neo4jClient for learning memory queries", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T03:32:53.994875Z"}
+{"event": "AgentService initialized without CanvasService - nodes will not be written to Canvas", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T03:32:53.994904Z"}
+{"event": "AgentService Phase 2: Tool calling disabled (ENABLE_TOOL_CALLING=false)", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T03:32:53.994929Z"}
+{"event": "AgentService Phase 4: React Agent ENABLED (ENABLE_REACT_AGENT=true)", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T03:32:53.994951Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.agent_service:agent_service.py:1400 {'event': 'AgentService initialized without configured AI client - API calls will fail', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T03:32:53.994769Z'}
+WARNING  app.services.agent_service:agent_service.py:1409 {'event': 'AgentService initialized without LearningMemoryClient - historical context fallback unavailable when Neo4j is down', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T03:32:53.994809Z'}
+INFO     app.services.agent_service:agent_service.py:1416 {'event': 'AgentService will use Neo4jClient for learning memory queries', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T03:32:53.994875Z'}
+WARNING  app.services.agent_service:agent_service.py:1427 {'event': 'AgentService initialized without CanvasService - nodes will not be written to Canvas', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T03:32:53.994904Z'}
+INFO     app.services.agent_service:agent_service.py:1444 {'event': 'AgentService Phase 2: Tool calling disabled (ENABLE_TOOL_CALLING=false)', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T03:32:53.994929Z'}
+INFO     app.services.agent_service:agent_service.py:1449 {'event': 'AgentService Phase 4: React Agent ENABLED (ENABLE_REACT_AGENT=true)', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T03:32:53.994951Z'}
+______ TestGetDifficultyData.test_memory_service_unavailable_returns_none ______
+tests/unit/test_difficulty_canvas_integration.py:156: in test_memory_service_unavailable_returns_none
+    result = await _get_difficulty_data(sample_nodes, "test_canvas")
+             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+app/api/v1/endpoints/review.py:298: in _get_difficulty_data
+    memory_service = await get_memory_service()
+                     ^^^^^^^^^^^^^^^^^^^^^^^^^^
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:2333: in _execute_mock_call
+    raise effect
+E   Exception: MemoryService unavailable
+_____ TestAIQuestionDifficultyInjection.test_difficulty_context_in_prompt ______
+tests/unit/test_difficulty_canvas_integration.py:432: in test_difficulty_context_in_prompt
+    await review_mod._generate_ai_questions(sample_nodes, difficulty_map_mixed)
+app/api/v1/endpoints/review.py:467: in _generate_ai_questions
+    agent_service.call_agent(AgentType.VERIFICATION_QUESTION, prompt),
+                             ^^^^^^^^^
+E   NameError: name 'AgentType' is not defined
+___ TestAIQuestionDifficultyInjection.test_no_difficulty_map_no_extra_fields ___
+tests/unit/test_difficulty_canvas_integration.py:476: in test_no_difficulty_map_no_extra_fields
+    await review_mod._generate_ai_questions(sample_nodes, None)
+app/api/v1/endpoints/review.py:467: in _generate_ai_questions
+    agent_service.call_agent(AgentType.VERIFICATION_QUESTION, prompt),
+                             ^^^^^^^^^
+E   NameError: name 'AgentType' is not defined
+____________ test_vault_id_provided_triggers_context_var_injection _____________
+tests/unit/test_enrich_context_vault_isolation.py:113: in test_vault_id_provided_triggers_context_var_injection
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 4.86, "event": "request.completed", "request_id": "5628902672", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T03:35:45.284974Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 4.86, 'event': 'request.completed', 'request_id': '5628902672', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T03:35:45.284974Z'}
+________________ test_chinese_vault_id_not_collapsed_to_default ________________
+tests/unit/test_enrich_context_vault_isolation.py:142: in test_chinese_vault_id_not_collapsed_to_default
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 4.61, "event": "request.completed", "request_id": "5367255440", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T03:35:45.293426Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 4.61, 'event': 'request.completed', 'request_id': '5367255440', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T03:35:45.293426Z'}
+___________________ test_subject_id_optional_backward_compat ___________________
+tests/unit/test_enrich_context_vault_isolation.py:166: in test_subject_id_optional_backward_compat
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 4.83, "event": "request.completed", "request_id": "5367257360", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T03:35:45.301624Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 4.83, 'event': 'request.completed', 'request_id': '5367257360', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T03:35:45.301624Z'}
+__________________ test_vault_id_with_special_chars_sanitized __________________
+tests/unit/test_enrich_context_vault_isolation.py:233: in test_vault_id_with_special_chars_sanitized
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 4.89, "event": "request.completed", "request_id": "5367261968", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T03:35:45.322788Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 4.89, 'event': 'request.completed', 'request_id': '5367261968', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T03:35:45.322788Z'}
+_________________________ test_vault_id_emoji_stripped _________________________
+tests/unit/test_enrich_context_vault_isolation.py:255: in test_vault_id_emoji_stripped
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 4.71, "event": "request.completed", "request_id": "5367262160", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T03:35:45.331011Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 4.71, 'event': 'request.completed', 'request_id': '5367262160', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T03:35:45.331011Z'}
+_ TestRecordTemporalEventLifecycle.test_p0_neo4j_write_failure_degrades_silently _
+tests/unit/test_epic30_memory_pipeline.py:400: in test_p0_neo4j_write_failure_degrades_silently
+    event_id = await svc.record_temporal_event(
+app/services/memory_service.py:2627: in record_temporal_event
+    await self.neo4j.record_episode(
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:2333: in _execute_mock_call
+    raise effect
+E   Exception: Connection refused
+----------------------------- Captured stdout call -----------------------------
+{"event": "MemoryService: recovered 0 episodes from Neo4j (0 returned, 0 deduped)", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T03:35:45.366472Z"}
+{"event": "MemoryService initialized successfully", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T03:35:45.366527Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.memory_service:memory_service.py:431 {'event': 'MemoryService: recovered 0 episodes from Neo4j (0 returned, 0 deduped)', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T03:35:45.366472Z'}
+INFO     app.services.memory_service:memory_service.py:287 {'event': 'MemoryService initialized successfully', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T03:35:45.366527Z'}
+___ TestGetRelatedMemoriesReturnStructure.test_query_exception_returns_empty ___
+tests/unit/test_epic36_gap_coverage.py:150: in test_query_exception_returns_empty
+    results = await graphiti_client.get_related_memories(node_id="node-1")
+              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+app/clients/neo4j_edge_client.py:436: in get_related_memories
+    results = await self._neo4j.run_query(cypher_query, **params)
+              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:2333: in _execute_mock_call
+    raise effect
+E   Exception: Connection lost
+----------------------------- Captured stdout call -----------------------------
+{"event": "Neo4jEdgeClient initialized: neo4j_mode=BOLT", "logger": "app.clients.neo4j_learning_base", "level": "info", "timestamp": "2026-09-20T03:35:45.704722Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.clients.neo4j_learning_base:neo4j_learning_base.py:189 Neo4jEdgeClient initialized: neo4j_mode=BOLT
+____________ TestProgressEndpoint.test_progress_invalid_session_404 ____________
+tests/unit/test_intelligent_parallel_endpoints.py:437: in test_progress_invalid_session_404
+    assert response.status_code == status.HTTP_404_NOT_FOUND
+E   assert 500 == 404
+E    +  where 500 = <Response [500 Internal Server Error]>.status_code
+E    +  and   404 = status.HTTP_404_NOT_FOUND
+---------------------------- Captured stdout setup -----------------------------
+{"event": "IntelligentParallelService: batch_orchestrator not injected \u2014 batch execution will fail", "logger": "app.services.intelligent_parallel_service", "level": "warning", "timestamp": "2026-09-20T03:36:23.908335Z"}
+{"event": "IntelligentParallelService initialized with real service dependencies", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T03:36:23.908380Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.intelligent_parallel_service:intelligent_parallel_service.py:106 {'event': 'IntelligentParallelService: batch_orchestrator not injected — batch execution will fail', 'logger': 'app.services.intelligent_parallel_service', 'level': 'warning', 'timestamp': '2026-09-20T03:36:23.908335Z'}
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:121 {'event': 'IntelligentParallelService initialized with real service dependencies', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:23.908380Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "get_session_status called: session_id=nonexistent-session", "request_id": "5383103760", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T03:36:23.909033Z"}
+{"method": "GET", "path": "/api/v1/canvas/intelligent-parallel/nonexistent-session", "endpoint": "/api/v1/canvas/intelligent-parallel/nonexistent-session", "status": 500, "duration_ms": 0.45, "event": "request.completed", "request_id": "5383103760", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T03:36:23.909254Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:326 {'event': 'get_session_status called: session_id=nonexistent-session', 'request_id': '5383103760', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:23.909033Z'}
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'GET', 'path': '/api/v1/canvas/intelligent-parallel/nonexistent-session', 'endpoint': '/api/v1/canvas/intelligent-parallel/nonexistent-session', 'status': 500, 'duration_ms': 0.45, 'event': 'request.completed', 'request_id': '5383103760', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T03:36:23.909254Z'}
+____________ TestCancelEndpoint.test_cancel_nonexistent_session_404 ____________
+tests/unit/test_intelligent_parallel_endpoints.py:492: in test_cancel_nonexistent_session_404
+    assert response.status_code == status.HTTP_404_NOT_FOUND
+E   assert 500 == 404
+E    +  where 500 = <Response [500 Internal Server Error]>.status_code
+E    +  and   404 = status.HTTP_404_NOT_FOUND
+---------------------------- Captured stdout setup -----------------------------
+{"event": "IntelligentParallelService: batch_orchestrator not injected \u2014 batch execution will fail", "logger": "app.services.intelligent_parallel_service", "level": "warning", "timestamp": "2026-09-20T03:36:23.918680Z"}
+{"event": "IntelligentParallelService initialized with real service dependencies", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T03:36:23.918769Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.intelligent_parallel_service:intelligent_parallel_service.py:106 {'event': 'IntelligentParallelService: batch_orchestrator not injected — batch execution will fail', 'logger': 'app.services.intelligent_parallel_service', 'level': 'warning', 'timestamp': '2026-09-20T03:36:23.918680Z'}
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:121 {'event': 'IntelligentParallelService initialized with real service dependencies', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:23.918769Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "cancel_session called: session_id=nonexistent-session", "request_id": "5383107408", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T03:36:23.919601Z"}
+{"method": "POST", "path": "/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session", "endpoint": "/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session", "status": 500, "duration_ms": 0.5, "event": "request.completed", "request_id": "5383107408", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T03:36:23.919847Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:480 {'event': 'cancel_session called: session_id=nonexistent-session', 'request_id': '5383107408', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:23.919601Z'}
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session', 'endpoint': '/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session', 'status': 500, 'duration_ms': 0.5, 'event': 'request.completed', 'request_id': '5383107408', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T03:36:23.919847Z'}
+___________________ TestErrorResponses.test_404_error_format ___________________
+tests/unit/test_intelligent_parallel_endpoints.py:594: in test_404_error_format
+    assert response.status_code == status.HTTP_404_NOT_FOUND
+E   assert 500 == 404
+E    +  where 500 = <Response [500 Internal Server Error]>.status_code
+E    +  and   404 = status.HTTP_404_NOT_FOUND
+---------------------------- Captured stdout setup -----------------------------
+{"event": "IntelligentParallelService: batch_orchestrator not injected \u2014 batch execution will fail", "logger": "app.services.intelligent_parallel_service", "level": "warning", "timestamp": "2026-09-20T03:36:23.933694Z"}
+{"event": "IntelligentParallelService initialized with real service dependencies", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T03:36:23.933762Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.intelligent_parallel_service:intelligent_parallel_service.py:106 {'event': 'IntelligentParallelService: batch_orchestrator not injected — batch execution will fail', 'logger': 'app.services.intelligent_parallel_service', 'level': 'warning', 'timestamp': '2026-09-20T03:36:23.933694Z'}
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:121 {'event': 'IntelligentParallelService initialized with real service dependencies', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:23.933762Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "get_session_status called: session_id=nonexistent-session", "request_id": "5384901200", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T03:36:23.934506Z"}
+{"method": "GET", "path": "/api/v1/canvas/intelligent-parallel/nonexistent-session", "endpoint": "/api/v1/canvas/intelligent-parallel/nonexistent-session", "status": 500, "duration_ms": 0.48, "event": "request.completed", "request_id": "5384901200", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T03:36:23.934727Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:326 {'event': 'get_session_status called: session_id=nonexistent-session', 'request_id': '5384901200', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:23.934506Z'}
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'GET', 'path': '/api/v1/canvas/intelligent-parallel/nonexistent-session', 'endpoint': '/api/v1/canvas/intelligent-parallel/nonexistent-session', 'status': 500, 'duration_ms': 0.48, 'event': 'request.completed', 'request_id': '5384901200', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T03:36:23.934727Z'}
+________ TestEnsureFulltextIndex.test_ensure_fulltext_index_idempotent _________
+tests/unit/test_neo4j_fulltext_index.py:129: in test_ensure_fulltext_index_idempotent
+    assert create_count == 4, (
+E   AssertionError: Should execute CREATE FULLTEXT INDEX each time × 2 indexes (IF NOT EXISTS handles idempotency, Round-23 Patch 3 added node_search_unified)
+E   assert 2 == 4
+----------------------------- Captured stdout call -----------------------------
+{"event": "MemoryService: recovered 0 episodes from Neo4j (0 returned, 0 deduped)", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T03:36:31.980156Z"}
+{"event": "MemoryService initialized successfully", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T03:36:31.980213Z"}
+{"event": "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T03:36:31.980253Z"}
+{"event": "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T03:36:31.980287Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.memory_service:memory_service.py:431 {'event': 'MemoryService: recovered 0 episodes from Neo4j (0 returned, 0 deduped)', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:31.980156Z'}
+INFO     app.services.memory_service:memory_service.py:287 {'event': 'MemoryService initialized successfully', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:31.980213Z'}
+INFO     app.services.memory_service:memory_service.py:316 {'event': "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content", 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:31.980253Z'}
+INFO     app.services.memory_service:memory_service.py:316 {'event': "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content", 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:31.980287Z'}
+__________ TestMergedViewEdgeCases.test_merged_view_sort_newest_first __________
+tests/unit/test_qa_38_6_scoring_reliability_extra.py:293: in test_merged_view_sort_newest_first
+    assert len(items) == 3
+E   AssertionError: assert 1 == 3
+E    +  where 1 = len([{'concept': 'concept_mid', 'node_id': 'node_mid', 'score': 50.0, 'timestamp': '2026-02-06T10:00:00'}])
+______________ test_strip_whiteboard_removes_admonition_callouts _______________
+tests/unit/test_rag_p0_doc_type_filter.py:169: in test_strip_whiteboard_removes_admonition_callouts
+    assert "原白板说明" not in out
+E   assert '原白板说明' not in '\n> [!info]...= 节点关系**\n\n'
+E     
+E     '原白板说明' is contained here:
+E       
+E       > [!info]+ 原白板说明（扁平架构 · round-11）
+E     ?            +++++
+E       > 这是学习主题"线性代数"的原白板。
+E       >...
+E     
+E     ...Full output truncated (15 lines hidden), use '-vv' to show
+______________ test_search_error_memories_sorts_by_timestamp_desc ______________
+tests/unit/test_story_2_3_error_reminders.py:345: in test_search_error_memories_sorts_by_timestamp_desc
+    assert descriptions == ["newest", "middle", "old"]
+E   AssertionError: assert ['old', 'newest', 'middle'] == ['newest', 'middle', 'old']
+E     
+E     At index 0 diff: 'old' != 'newest'
+E     Use -v to get more diff
+_________________ test_search_error_memories_normalizes_schema _________________
+tests/unit/test_story_2_3_error_reminders.py:403: in test_search_error_memories_normalizes_schema
+    assert err["corrected_at"] == "2026-04-16T09:00:00"  # metadata wins over timestamp
+    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+E   AssertionError: assert '2026-04-15T12:34:56' == '2026-04-16T09:00:00'
+E     
+E     - 2026-04-16T09:00:00
+E     + 2026-04-15T12:34:56
+_____ test_search_error_memories_passes_node_id_filter_to_search_memories ______
+tests/unit/test_story_2_3_error_reminders.py:417: in test_search_error_memories_passes_node_id_filter_to_search_memories
+    await svc.search_error_memories(
+app/services/memory_service.py:2557: in search_error_memories
+    result = await self.search_error_memories_with_status(
+app/services/memory_service.py:2510: in search_error_memories_with_status
+    hits = search_result.items
+           ^^^^^^^^^^^^^^^^^^^
+E   AttributeError: 'list' object has no attribute 'items'
+________________ test_search_memories_node_id_filter_post_merge ________________
+tests/unit/test_story_2_3_error_reminders.py:470: in test_search_memories_node_id_filter_post_merge
+    assert len(all_results) == 2
+E   AssertionError: assert 1 == 2
+E    +  where 1 = len([{'content': 'b', 'episode_id': 'ep-8773', 'episode_type': 'error', 'group_id': 'vault:cs_61b', ...}])
+----------------------------- Captured stdout call -----------------------------
+{"event": "[search_memories] Tier 1: 1 results, Tier 2: 1 results, Tier 3: 0 results (deduped 1, floor=0.05, returned 1)", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T03:36:43.656846Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.memory_service:memory_service.py:2430 {'event': '[search_memories] Tier 1: 1 results, Tier 2: 1 results, Tier 3: 0 results (deduped 1, floor=0.05, returned 1)', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:43.656846Z'}
+________________ test_search_memories_node_id_none_is_no_filter ________________
+tests/unit/test_story_2_3_error_reminders.py:498: in test_search_memories_node_id_none_is_no_filter
+    assert len(results) == 3
+E   assert 0 == 3
+E    +  where 0 = len([])
+----------------------------- Captured stdout call -----------------------------
+{"event": "[search_memories] Tier 1: 3 results, Tier 2: 0 results, Tier 3: 0 results (deduped 3, floor=0.05, returned 0)", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T03:36:43.660860Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.memory_service:memory_service.py:2430 {'event': '[search_memories] Tier 1: 3 results, Tier 2: 0 results, Tier 3: 0 results (deduped 3, floor=0.05, returned 0)', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T03:36:43.660860Z'}
+_______ TestAC4MergedView.test_get_learning_history_merges_failed_scores _______
+tests/unit/test_story_38_6_scoring_reliability.py:465: in test_get_learning_history_merges_failed_scores
+    assert result["total"] == 2
+E   assert 1 == 2
+________________________ test_live_vault_enforce_clean _________________________
+tests/unit/test_vault_doc_roles.py:481: in test_live_vault_enforce_clean
+    assert proc.returncode == 0, proc.stdout + proc.stderr
+E   AssertionError: [2m台账[0m /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/vault_doc_roles.yaml
+E     [2mvault[0m /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault  (176 目录 / 326 文件, 只读)
+E     [2m双准入面实测分歧[0m 1 条: chatgpt-adversarial-review-Q1Q2Q3-2026-05-12.md
+E     [2m  info  .quarantine/UAT-2.5.X-test.md 的准入两列取自 any_level 行 root-uat-scratch(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-quarantine 为准[0m
+E     [2m  info  raw/CS188/CLAUDE.md 的准入两列取自 any_level 行 root-claude-md(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-raw 为准[0m
+E     [2m  info  raw/CS188/_misc/junk/未命名 1.md 的准入两列取自 any_level 行 root-untitled-scratch(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-misc-junk 为准[0m
+E     [2m  info  raw/CS188/_misc/junk/未命名.md 的准入两列取自 any_level 行 root-untitled-scratch(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-misc-junk 为准[0m
+E     [2m  info  raw/CS188/管道设计.md 的准入两列取自 any_level 行 root-pipeline-design(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-raw 为准[0m
+E     [2m  info  勘测快照漂移 total_files: 台账 324 → 实测 326[0m
+E     [91mG1[0m  3 条 (阻断 3)
+E         - backups
+E           live 目录未被任何 vault_entries.dir_glob 命中
+E         - backups
+E           文件 backups/fsrs_bridge.py.pre-deploy-2026-09-05T1052.bak 所在目录未被登记
+E         - backups
+E           文件 backups/fsrs_bridge.py.pre-deploy-2026-09-07T0328.bak 所在目录未被登记
+E     /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
+E       from pydantic.v1.fields import FieldInfo as FieldInfoV1
+E     /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
+E       import pkg_resources
+E     Building prefix dict from the default dictionary ...
+E     Loading model from cache /var/folders/vq/gssw8vy54671lh9nlqc_ft2w0000gn/T/jieba.cache
+E     Loading model cost 0.224 seconds.
+E     Prefix dict has been built successfully.
+E     2026-09-19 20:37:25 [info     ] RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True
+E     
+E   assert 1 == 0
+E    +  where 1 = CompletedProcess(args=['/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/...uccessfully.\n2026-09-19 20:37:25 [info     ] RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True\n").returncode
+________________ test_group_id_physics_filters_to_physics_only _________________
+tests/unit/test_vault_notes_group_filter.py:97: in test_group_id_physics_filters_to_physics_only
+    assert len(out) == 1
+E   AssertionError: assert 2 == 1
+E    +  where 2 = len([{'id': 'r_phys', 'metadata': {'source': 'vault_note', 'subject_id': 'physics'}, 'score': 0.8}, {'id': 'r_math', 'metadata': {'source': 'vault_note', 'subject_id': 'math'}, 'score': 0.8}])
+________ test_group_id_with_no_explicit_match_returns_only_common_notes ________
+tests/unit/test_vault_notes_group_filter.py:124: in test_group_id_with_no_explicit_match_returns_only_common_notes
+    assert ids == {"r_common"}
+E   AssertionError: assert {'r1', 'r2', 'r_common'} == {'r_common'}
+E     
+E     Extra items in the left set:
+E     'r1'
+E     'r2'
+E     Use -v to get more diff
+___________ test_group_id_with_no_common_and_no_match_returns_empty ____________
+tests/unit/test_vault_notes_group_filter.py:139: in test_group_id_with_no_common_and_no_match_returns_empty
+    assert out == []
+E   AssertionError: assert [{'id': 'r1',...'score': 0.8}] == []
+E     
+E     Left contains 2 more items, first extra item: {'id': 'r1', 'metadata': {'source': 'vault_note', 'subject_id': 'physics'}, 'score': 0.8}
+E     Use -v to get more diff
+______________ test_group_id_honors_nested_metadata_json_subject _______________
+tests/unit/test_vault_notes_group_filter.py:185: in test_group_id_honors_nested_metadata_json_subject
+    assert len(out) == 1
+E   AssertionError: assert 2 == 1
+E    +  where 2 = len([{'id': 'r_nested', 'metadata': {'file_path': 'r_nested.md', 'heading': None, 'line_end': None, 'line_start': None, .....etadata': {'file_path': 'r_math_nested.md', 'heading': None, 'line_end': None, 'line_start': None, ...}, 'score': 0.8}])
+______ TestVerificationDedup.test_no_history_generates_standard_question _______
+tests/unit/test_verification_dedup.py:49: in test_no_history_generates_standard_question
+    mock_graphiti_client.search_verification_questions.assert_called_once()
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:965: in assert_called_once
+    raise AssertionError(msg)
+E   AssertionError: Expected 'search_verification_questions' to have been called once. Called 0 times.
+---------------------------- Captured stdout setup -----------------------------
+{"event": "VerificationService initialized (RAG: False, Canvas: False, Agent: True, Graphiti: True, Memory: False, MockMode: False)", "logger": "app.services.verification_service", "level": "info", "timestamp": "2026-09-20T03:38:25.326753Z"}
+{"event": "VerificationService using IN-MEMORY TTLCache for session storage (maxsize=500, ttl=3600s). Sessions will be LOST on service restart. This is a known limitation \u2014 see Story 31.A.7.", "logger": "app.services.verification_service", "level": "warning", "timestamp": "2026-09-20T03:38:25.326835Z"}
+------------------------------ Captured log setup ------------------------------
+INFO     app.services.verification_service:verification_service.py:613 {'event': 'VerificationService initialized (RAG: False, Canvas: False, Agent: True, Graphiti: True, Memory: False, MockMode: False)', 'logger': 'app.services.verification_service', 'level': 'info', 'timestamp': '2026-09-20T03:38:25.326753Z'}
+WARNING  app.services.verification_service:verification_service.py:624 {'event': 'VerificationService using IN-MEMORY TTLCache for session storage (maxsize=500, ttl=3600s). Sessions will be LOST on service restart. This is a known limitation — see Story 31.A.7.', 'logger': 'app.services.verification_service', 'level': 'warning', 'timestamp': '2026-09-20T03:38:25.326835Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "No agent service available, using fallback question for \u9006\u5426\u547d\u9898", "logger": "app.services.verification_service", "level": "warning", "timestamp": "2026-09-20T03:38:25.327674Z"}
+------------------------------ Captured log call -------------------------------
+WARNING  app.services.verification_service:verification_service.py:2961 {'event': 'No agent service available, using fallback question for 逆否命题', 'logger': 'app.services.verification_service', 'level': 'warning', 'timestamp': '2026-09-20T03:38:25.327674Z'}
+____ TestVerificationDedup.test_with_history_generates_alternative_question ____
+tests/unit/test_verification_dedup.py:82: in test_with_history_generates_alternative_question
+    assert mock_graphiti_client.search_verification_questions.called
+E   AssertionError: assert False
+E    +  where False = <AsyncMock name='mock.search_verification_questions' id='5714243808'>.called
+E    +    where <AsyncMock name='mock.search_verification_questions' id='5714243808'> = <MagicMock id='5714242800'>.search_verification_questions
+---------------------------- Captured stdout setup -----------------------------
+{"event": "VerificationService initialized (RAG: False, Canvas: False, Agent: True, Graphiti: True, Memory: False, MockMode: False)", "logger": "app.services.verification_service", "level": "info", "timestamp": "2026-09-20T03:38:25.347269Z"}
+{"event": "VerificationService using IN-MEMORY TTLCache for session storage (maxsize=500, ttl=3600s). Sessions will be LOST on service restart. This is a known limitation \u2014 see Story 31.A.7.", "logger": "app.services.verification_service", "level": "warning", "timestamp": "2026-09-20T03:38:25.347362Z"}
+------------------------------ Captured log setup ------------------------------
+INFO     app.services.verification_service:verification_service.py:613 {'event': 'VerificationService initialized (RAG: False, Canvas: False, Agent: True, Graphiti: True, Memory: False, MockMode: False)', 'logger': 'app.services.verification_service', 'level': 'info', 'timestamp': '2026-09-20T03:38:25.347269Z'}
+WARNING  app.services.verification_service:verification_service.py:624 {'event': 'VerificationService using IN-MEMORY TTLCache for session storage (maxsize=500, ttl=3600s). Sessions will be LOST on service restart. This is a known limitation — see Story 31.A.7.', 'logger': 'app.services.verification_service', 'level': 'warning', 'timestamp': '2026-09-20T03:38:25.347362Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "No agent service available, using fallback question for \u9006\u5426\u547d\u9898", "logger": "app.services.verification_service", "level": "warning", "timestamp": "2026-09-20T03:38:25.348289Z"}
+------------------------------ Captured log call -------------------------------
+WARNING  app.services.verification_service:verification_service.py:2961 {'event': 'No agent service available, using fallback question for 逆否命题', 'logger': 'app.services.verification_service', 'level': 'warning', 'timestamp': '2026-09-20T03:38:25.348289Z'}
+_____ TestWebSocketEndpoint.test_validate_session_handles_validator_error ______
+tests/unit/test_websocket_endpoints.py:538: in test_validate_session_handles_validator_error
+    result = await validate_session("any-session")
+             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+app/api/v1/endpoints/websocket.py:80: in validate_session
+    return await _session_validator(session_id)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+tests/unit/test_websocket_endpoints.py:533: in failing_validator
+    raise Exception("Validator error")
+E   Exception: Validator error
+----------------------------- Captured stdout call -----------------------------
+{"event": "Session validator set for WebSocket endpoint", "logger": "app.api.v1.endpoints.websocket", "level": "info", "timestamp": "2026-09-20T03:38:25.517567Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.api.v1.endpoints.websocket:websocket.py:59 Session validator set for WebSocket endpoint
+=============================== warnings summary ===============================
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
+    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
+    from pydantic.v1.fields import FieldInfo as FieldInfoV1
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
+    class SearchInterface(BaseModel):
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
+    import pkg_resources
+
+<frozen importlib._bootstrap>:491
+  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute
+
+<frozen importlib._bootstrap>:491
+  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute
+
+app/api/v1/endpoints/chat.py:807
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/chat.py:807: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
+    class HookEnrichRequest(BaseModel):
+
+app/api/v1/endpoints/metadata.py:103
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/metadata.py:103: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
+    canvas_path: str = Query(
+
+app/api/v1/endpoints/metadata.py:177
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/metadata.py:177: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
+    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356: PydanticDeprecatedSince211: The `__get_pydantic_core_schema__` method of the `BaseModel` class is deprecated. If you are calling `super().__get_pydantic_core_schema__` when overriding the method on a Pydantic model, consider using `handler(source)` instead. However, note that overriding this method on models can lead to unexpected side effects. Deprecated in Pydantic V2.11 to be removed in V3.0.
+    schema = annotation_get_schema(source, get_inner_schema)
+
+tests/unit/test_agentic_rag_vault_scope.py::TestDualVaultIsolationOnTmpLanceDB::test_shared_db_precondition_tables_coexist
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_agentic_rag_vault_scope.py:499: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    names = set(self.db.table_names())
+
+tests/unit/test_agentic_rag_vault_scope.py: 1 warning
+tests/unit/test_g24_lance_legacy_table_removal.py: 17 warnings
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py: 56 warnings
+  /opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/events.py:94: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    self._context.run(self._callback, *self._args)
+
+tests/unit/test_batch_orchestrator.py::TestProgressBroadcasting::test_broadcast_calls_sync_callback
+tests/unit/test_batch_orchestrator.py::TestProgressBroadcasting::test_broadcast_calls_async_callback
+tests/unit/test_batch_orchestrator.py::TestProgressBroadcasting::test_broadcast_handles_callback_error
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/services/batch_orchestrator.py:968: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
+    if asyncio.iscoroutinefunction(self.progress_callback):
+
+tests/unit/test_canvas_memory_trigger.py: 2 warnings
+tests/unit/test_recommendation_group_filter.py: 11 warnings
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/pydantic/main.py:250: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
+    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
+
+tests/unit/test_canvas_projection_sync.py: 6 warnings
+tests/unit/test_frontmatter_signals.py: 6 warnings
+tests/unit/test_vault_backfill.py: 4 warnings
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/frontmatter/__init__.py:161: DeprecationWarning: codecs.open() is deprecated. Use open() instead.
+    with codecs.open(fd, "r", encoding) as f:
+
+tests/unit/test_edge_rationale_fallback.py::test_both_writes_succeed_returns_200
+tests/unit/test_edge_rationale_fallback.py::test_graphiti_ok_lancedb_fail_returns_207
+tests/unit/test_edge_rationale_fallback.py::test_lancedb_ok_graphiti_fail_returns_207
+tests/unit/test_edge_rationale_fallback.py::test_both_writes_fail_returns_500
+tests/unit/test_edge_rationale_fallback.py::test_graphiti_exception_does_not_block_lancedb
+tests/unit/test_edge_rationale_fallback.py::test_lancedb_exception_does_not_block_graphiti
+tests/unit/test_edge_rationale_fallback.py::test_partial_failure_includes_error_details
+tests/unit/test_edge_rationale_fallback.py::test_strategy_fields_accepted
+tests/unit/test_edge_rationale_fallback.py::test_strategy_fields_defaults
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/edges.py:411: DeprecationWarning: deprecated
+    legacy_group_id=rationale.group_id,
+
+tests/unit/test_edge_rationale_fallback.py: 12 warnings
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/models/edge_rationale.py:115: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
+    default_factory=lambda: datetime.utcnow().isoformat(),
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_bare_table_really_holds_other_vault_rows
+tests/unit/test_g24_lance_legacy_table_removal.py::test_default_vault_still_maps_to_bare_table
+tests/unit/test_g24_lance_legacy_table_removal.py::test_prefixed_missing_no_longer_falls_back_to_bare
+tests/unit/test_g24_lance_legacy_table_removal.py::test_search_raises_table_missing_and_never_opens_bare_table
+tests/unit/test_g24_lance_legacy_table_removal.py::test_table_missing_penetrates_enable_fallback_swallow_gate
+tests/unit/test_g24_lance_legacy_table_removal.py::test_search_supplementary_surfaces_unavailable
+tests/unit/test_g24_lance_legacy_table_removal.py::test_write_creates_prefixed_table_and_leaves_bare_byte_identical
+tests/unit/test_g24_lance_legacy_table_removal.py::test_is_table_absent_distinguishes_missing_from_unopenable
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:69: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert set(db.table_names()) == {"vault_notes"}
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_prefixed_missing_no_longer_falls_back_to_bare
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:122: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert "xvault_vault_notes" not in client._db.table_names()
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_prefixed_missing_no_longer_falls_back_to_bare
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:123: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert "vault_notes" in client._db.table_names()
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_write_creates_prefixed_table_and_leaves_bare_byte_identical
+tests/unit/test_g24_lance_legacy_table_removal.py::test_default_vault_write_still_targets_bare_table
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/lib/agentic_rag/clients/lancedb_client.py:4414: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    if data and table_name in self._db.table_names():
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_write_creates_prefixed_table_and_leaves_bare_byte_identical
+tests/unit/test_g24_lance_legacy_table_removal.py::test_default_vault_write_still_targets_bare_table
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/lib/agentic_rag/clients/lancedb_client.py:4423: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    if table_name in self._db.table_names():
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_write_creates_prefixed_table_and_leaves_bare_byte_identical
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:215: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert "xvault_vault_notes" in db.table_names(), "新 vault 的数据必须落进自己的表"
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_default_vault_write_still_targets_bare_table
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:246: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert db2.table_names() == ["vault_notes"], "default vault 不得凭空造 prefixed 表"
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_is_table_absent_sees_past_default_pagination
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:285: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert len(list(db.table_names())) == 10, "lancedb 默认分页行为变了, 本锁需重新校准"
+
+tests/unit/test_intelligent_parallel_endpoints.py::TestAnalyzeEndpoint::test_analyze_invalid_color
+tests/unit/test_intelligent_parallel_endpoints.py::TestConfirmEndpoint::test_confirm_timeout_validation
+  /opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/events.py:94: DeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
+    self._context.run(self._callback, *self._args)
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py: 47 warnings
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:109: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    return set(db.table_names(limit=10_000))
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_cache_tables_scans_beyond_default_page
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:355: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert len(db.table_names()) == 10, (
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_cache_tables_scans_beyond_default_page
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:359: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert "a_t11" not in set(db.table_names()), "前提失效: a_t11 不在默认分页的盲区里"
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:553: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    in_page = table in set(db.table_names())
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_fingerprint_baseline_readable_beyond_default_page
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1009: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert fp_name not in set(db.table_names()), (
+
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_targeted_mode_queries_graphiti
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_targeted_mode_queries_graphiti
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_targeted_mode_weight_distribution
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_targeted_mode_weight_distribution
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_custom_weights_applied
+tests/unit/test_review_mode_support.py::TestReviewModeFallback::test_targeted_mode_no_fallback_with_history
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/services/weight_calculator.py:181: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
+    days_since = (datetime.utcnow() - last_review).days
+
+tests/unit/test_sync_batch_auth.py: 2 warnings
+tests/unit/test_sync_exception_classification.py: 6 warnings
+tests/unit/test_sync_group_isolation.py: 1 warning
+tests/unit/test_vault_scope_409.py: 1 warning
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/sync.py:117: DeprecationWarning: deprecated
+    legacy_group_id=request.group_id,
+
+tests/unit/test_vault_scope_409.py::TestCodexRound1RectifiedEndpoints::test_inheritance_distill_mismatch_409
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/inheritance.py:83: DeprecationWarning: deprecated
+    request.vault_id, legacy_group_id=request.group_id
+
+tests/unit/test_wave5_stageb_continued_vault_id_injection.py::TestSyncBatchRequestVaultId::test_sync_batch_has_deprecated_group_id
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_wave5_stageb_continued_vault_id_injection.py:218: DeprecationWarning: deprecated
+    assert req.group_id == "cs188"
+
+-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
+NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
+=========================== short test summary info ============================
+FAILED tests/unit/test_agent_memory_injection.py::TestMemoryInjection::test_graceful_degradation_on_exception
+FAILED tests/unit/test_agent_service_neo4j_memory.py::TestEdgeCases::test_neo4j_query_error_returns_empty
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestGetDifficultyData::test_memory_service_unavailable_returns_none
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_difficulty_context_in_prompt
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_no_difficulty_map_no_extra_fields
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_provided_triggers_context_var_injection
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_chinese_vault_id_not_collapsed_to_default
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_subject_id_optional_backward_compat
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_with_special_chars_sanitized
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_emoji_stripped
+FAILED tests/unit/test_epic30_memory_pipeline.py::TestRecordTemporalEventLifecycle::test_p0_neo4j_write_failure_degrades_silently
+FAILED tests/unit/test_epic36_gap_coverage.py::TestGetRelatedMemoriesReturnStructure::test_query_exception_returns_empty
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestProgressEndpoint::test_progress_invalid_session_404
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestCancelEndpoint::test_cancel_nonexistent_session_404
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestErrorResponses::test_404_error_format
+FAILED tests/unit/test_neo4j_fulltext_index.py::TestEnsureFulltextIndex::test_ensure_fulltext_index_idempotent
+FAILED tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestMergedViewEdgeCases::test_merged_view_sort_newest_first
+FAILED tests/unit/test_rag_p0_doc_type_filter.py::test_strip_whiteboard_removes_admonition_callouts
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_sorts_by_timestamp_desc
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_normalizes_schema
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_passes_node_id_filter_to_search_memories
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_filter_post_merge
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_none_is_no_filter
+FAILED tests/unit/test_story_38_6_scoring_reliability.py::TestAC4MergedView::test_get_learning_history_merges_failed_scores
+FAILED tests/unit/test_vault_doc_roles.py::test_live_vault_enforce_clean - AssertionError: [2m台账[0m /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/vault_doc_roles.yaml
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_physics_filters_to_physics_only
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_explicit_match_returns_only_common_notes
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_common_and_no_match_returns_empty
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_honors_nested_metadata_json_subject
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_no_history_generates_standard_question
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_with_history_generates_alternative_question
+FAILED tests/unit/test_websocket_endpoints.py::TestWebSocketEndpoint::test_validate_session_handles_validator_error
+= 32 failed, 5771 passed, 44 skipped, 13 xfailed, 231 warnings in 339.09s (0:05:39) =
+rc=1
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-open-20260919T170315.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-open-20260919T170315.txt"
new file mode 100644
index 00000000..183f9ce6
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/unit-open-20260919T170315.txt"
@@ -0,0 +1,926 @@
+============================= test session starts ==============================
+platform darwin -- Python 3.14.4, pytest-9.0.2, pluggy-1.6.0
+rootdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend
+configfile: pytest.ini
+plugins: hypothesis-6.151.10, cov-7.1.0, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, schemathesis-4.14.3, bdd-8.1.0, langsmith-0.7.24, anyio-4.13.0
+asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
+collected 5860 items
+
+tests/unit/grouping/test_analyze_canvas.py ........                      [  0%]
+tests/unit/grouping/test_factory_and_constants.py .............          [  0%]
+tests/unit/grouping/test_helpers.py .............                        [  0%]
+tests/unit/grouping/test_perform_clustering.py ...........               [  0%]
+tests/unit/test_a7_honest_failure.py ........                            [  0%]
+tests/unit/test_acp_prompt_externalization.py ...........                [  1%]
+tests/unit/test_agent_context_injection.py .....                         [  1%]
+tests/unit/test_agent_memory_injection.py ......F....                    [  1%]
+tests/unit/test_agent_memory_trigger.py ................................ [  1%]
+..........                                                               [  2%]
+tests/unit/test_agent_routing_engine.py ................................ [  2%]
+..........................                                               [  3%]
+tests/unit/test_agent_service_comparison.py ...............              [  3%]
+tests/unit/test_agent_service_extraction.py ............................ [  3%]
+.ss..                                                                    [  3%]
+tests/unit/test_agent_service_neo4j_memory.py ..................F....    [  4%]
+tests/unit/test_agent_service_user_understanding.py ...........          [  4%]
+tests/unit/test_agent_templates_smoke.py ............................... [  5%]
+...................                                                      [  5%]
+tests/unit/test_agentic_rag_vault_scope.py .......................       [  5%]
+tests/unit/test_agents_multimodal.py ....................                [  6%]
+tests/unit/test_archive_legacy_lance_tables_g24.py ..................... [  6%]
+.                                                                        [  6%]
+tests/unit/test_audit_guardian.py ...........                            [  6%]
+tests/unit/test_background_task_manager.py .....                         [  6%]
+tests/unit/test_batch_orchestrator.py .................................  [  7%]
+tests/unit/test_belief_version_chain.py .........                        [  7%]
+tests/unit/test_board_manifest_unreach_t5e.py ...........                [  7%]
+tests/unit/test_bug_tracker.py ......................                    [  7%]
+tests/unit/test_cache_configuration.py ....xx...x.x.                     [  8%]
+tests/unit/test_calibration_tracker.py ................................  [  8%]
+tests/unit/test_candidate_callout.py ............                        [  8%]
+tests/unit/test_candidate_expiry_service.py ....................         [  9%]
+tests/unit/test_candidate_service.py ..............                      [  9%]
+tests/unit/test_candidate_state_machine.py ............................. [ 10%]
+............                                                             [ 10%]
+tests/unit/test_candidate_writer.py ................                     [ 10%]
+tests/unit/test_canvas_edge_bulk_sync.py .........                       [ 10%]
+tests/unit/test_canvas_edge_sync.py .........                            [ 10%]
+tests/unit/test_canvas_episode_v1.py ...................                 [ 11%]
+tests/unit/test_canvas_memory_trigger.py ...................             [ 11%]
+tests/unit/test_canvas_projection_sync.py .............                  [ 11%]
+tests/unit/test_canvas_service_concurrency.py ................           [ 11%]
+tests/unit/test_canvas_validation.py ................                    [ 12%]
+tests/unit/test_card_state_concurrent_write.py ...                       [ 12%]
+tests/unit/test_chat_context_assembler.py .............................. [ 12%]
+....................                                                     [ 13%]
+tests/unit/test_chat_endpoint.py ................                        [ 13%]
+tests/unit/test_check_readme_claims.py ................................. [ 13%]
+........................................................................ [ 15%]
+...............                                                          [ 15%]
+tests/unit/test_circuit_breaker.py ............                          [ 15%]
+tests/unit/test_config_drift.py .........                                [ 15%]
+tests/unit/test_config_neo4j.py .............                            [ 16%]
+tests/unit/test_context_cache_key.py ....                                [ 16%]
+tests/unit/test_context_enrichment_2hop.py .................             [ 16%]
+tests/unit/test_context_enrichment_get_node_content.py ................. [ 16%]
+...                                                                      [ 16%]
+tests/unit/test_cost_tracker.py .....                                    [ 16%]
+tests/unit/test_create_fsrs_manager.py ..........                        [ 16%]
+tests/unit/test_cross_canvas_failsoft.py ...                             [ 17%]
+tests/unit/test_cross_canvas_removal.py .......                          [ 17%]
+tests/unit/test_cross_subject_bridge_group_isolation.py ..........       [ 17%]
+tests/unit/test_cypher_helpers.py ....................                   [ 17%]
+tests/unit/test_dashboard_statistics.py ...................              [ 18%]
+tests/unit/test_dead_letter_bounded_t6c.py ............................. [ 18%]
+..........                                                               [ 18%]
+tests/unit/test_deep_research_fallback.py ........................       [ 19%]
+tests/unit/test_degraded_flag_propagation.py .....                       [ 19%]
+tests/unit/test_deploy_vault_sh.py ..................................... [ 19%]
+..........sssss......................................................ss. [ 21%]
+...................ss................................................... [ 22%]
+........................................................................ [ 23%]
+...............................................                          [ 24%]
+tests/unit/test_difficulty_adaptive.py ................................. [ 24%]
+.........................                                                [ 25%]
+tests/unit/test_difficulty_canvas_integration.py .F...............FF.... [ 25%]
+                                                                         [ 25%]
+tests/unit/test_difficulty_matcher.py ...................                [ 25%]
+tests/unit/test_docker_compose_config.py ............                    [ 26%]
+tests/unit/test_edge_rationale_fallback.py ............                  [ 26%]
+tests/unit/test_embedder_factory.py .......                              [ 26%]
+tests/unit/test_enrich_context_vault_isolation.py ..FFF.FF               [ 26%]
+tests/unit/test_epic30_memory_pipeline.py ..............F............... [ 27%]
+..........                                                               [ 27%]
+tests/unit/test_epic32_p0_fixes.py .............                         [ 27%]
+tests/unit/test_epic36_gap_coverage.py ....F............                 [ 27%]
+tests/unit/test_episode_worker_coverage_epw.py ......................... [ 28%]
+......................                                                   [ 28%]
+tests/unit/test_episode_worker_retry.py .....                            [ 28%]
+tests/unit/test_error_aggregator.py ..................                   [ 29%]
+tests/unit/test_error_classification_mapping.py ........................ [ 29%]
+                                                                         [ 29%]
+tests/unit/test_error_extractor.py ............                          [ 29%]
+tests/unit/test_error_rebuild_service.py .............                   [ 29%]
+tests/unit/test_error_writer.py .................                        [ 30%]
+tests/unit/test_event_bus.py ...............................             [ 30%]
+tests/unit/test_exam_models_rubric_required_u2a.py ........              [ 30%]
+tests/unit/test_exam_sync_node_group_isolation.py .....                  [ 30%]
+tests/unit/test_extraction_validator.py ............                     [ 31%]
+tests/unit/test_failure_observability.py ...............sss...........   [ 31%]
+tests/unit/test_faithfulness_check.py ..............                     [ 31%]
+tests/unit/test_faithfulness_check_boundary.py .........                 [ 32%]
+tests/unit/test_four_state_injection.py ................................ [ 32%]
+.........                                                                [ 32%]
+tests/unit/test_freeze_release_candidate.py ............................ [ 33%]
+............                                                             [ 33%]
+tests/unit/test_frontmatter_signals.py ......                            [ 33%]
+tests/unit/test_fsrs_manager.py .....................................    [ 34%]
+tests/unit/test_fsrs_state_query.py ................                     [ 34%]
+tests/unit/test_fusion_report.py .........                               [ 34%]
+tests/unit/test_fusion_strategy_override.py ........                     [ 34%]
+tests/unit/test_g24_lance_legacy_table_removal.py ..........             [ 34%]
+tests/unit/test_g25_journal_namespace.py ...........................     [ 35%]
+tests/unit/test_graphiti_client.py ......................                [ 35%]
+tests/unit/test_graphiti_client_mock_performance.py .....                [ 35%]
+tests/unit/test_graphiti_client_unification.py ....                      [ 35%]
+tests/unit/test_graphiti_json_dual_write.py .......                      [ 35%]
+tests/unit/test_graphiti_memory_reader.py ......                         [ 36%]
+tests/unit/test_graphiti_neo4j_calls.py ......                           [ 36%]
+tests/unit/test_graphiti_structured_writer.py ....................       [ 36%]
+tests/unit/test_group_id_compat.py ...........................           [ 36%]
+tests/unit/test_group_id_dynamic_binding.py .....................        [ 37%]
+tests/unit/test_group_id_migration.py ................                   [ 37%]
+tests/unit/test_health_detailed.py ......                                [ 37%]
+tests/unit/test_hybrid_search_activation.py .......................      [ 38%]
+tests/unit/test_identity_registry.py .......                             [ 38%]
+tests/unit/test_intelligent_parallel_endpoints.py .........F.F...F...... [ 38%]
+......                                                                   [ 38%]
+tests/unit/test_internal_api_key_p0_2_hardening.py .............         [ 38%]
+tests/unit/test_kg_health.py .....                                       [ 39%]
+tests/unit/test_kg_relevance_weighted.py ........................        [ 39%]
+tests/unit/test_l1_llm_router.py ...............                         [ 39%]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py ...................... [ 40%]
+.............                                                            [ 40%]
+tests/unit/test_lancedb_isolation_assertions.py .............            [ 40%]
+tests/unit/test_lancedb_vault_isolation.py ...............               [ 40%]
+tests/unit/test_langgraph_async_conditional_edge_smoke.py ..             [ 40%]
+tests/unit/test_live_port_guard_contract.py ............................ [ 41%]
+........................................................................ [ 42%]
+....................................................                     [ 43%]
+tests/unit/test_llm_call_logger.py ..............................        [ 43%]
+tests/unit/test_markdown_image_extractor.py ............................ [ 44%]
+....                                                                     [ 44%]
+tests/unit/test_mastery_api.py ...........................               [ 44%]
+tests/unit/test_mastery_engine_bkt.py .......................            [ 45%]
+tests/unit/test_mastery_engine_effective.py ............                 [ 45%]
+tests/unit/test_mastery_engine_fsrs.py ..................                [ 45%]
+tests/unit/test_mastery_engine_level.py ..................               [ 46%]
+tests/unit/test_mastery_engine_misc.py ...............................   [ 46%]
+tests/unit/test_mastery_fsrs_projection_boundary.py ......               [ 46%]
+tests/unit/test_mastery_fusion.py ..........................             [ 47%]
+tests/unit/test_mastery_injection_memory_contract.py ............        [ 47%]
+tests/unit/test_mastery_property.py .......                              [ 47%]
+tests/unit/test_mastery_state.py ..............................          [ 48%]
+tests/unit/test_mastery_store.py .................                       [ 48%]
+tests/unit/test_mcp_switch_vault_tool.py ..                              [ 48%]
+tests/unit/test_memory_read_scope_g41a.py ........                       [ 48%]
+tests/unit/test_memory_service_batch.py ......                           [ 48%]
+tests/unit/test_memory_service_contextvar_leak.py ........               [ 48%]
+tests/unit/test_memory_service_structured_routing.py .........           [ 48%]
+tests/unit/test_memory_service_write_retry.py ssssssssssssssssss         [ 49%]
+tests/unit/test_migrate_canvas_group_isolation.py ....................   [ 49%]
+tests/unit/test_migrate_neo4j_data.py ...............................    [ 50%]
+tests/unit/test_mock_degradation_transparency.py ....................... [ 50%]
+.......                                                                  [ 50%]
+tests/unit/test_multimodal_fixes.py ......................               [ 50%]
+tests/unit/test_multimodal_path_security.py ................             [ 51%]
+tests/unit/test_mutation_kill_identity_r3.py ........................... [ 51%]
+.........................................................                [ 52%]
+tests/unit/test_neo4j_client.py ........................................ [ 53%]
+....................                                                     [ 53%]
+tests/unit/test_neo4j_field_consistency.py .......                       [ 53%]
+tests/unit/test_neo4j_fulltext_index.py ...F...                          [ 53%]
+tests/unit/test_neo4j_health.py ..........                               [ 54%]
+tests/unit/test_nfr_cache_bounds.py ..............                       [ 54%]
+tests/unit/test_observer_token_fail_closed.py ............               [ 54%]
+tests/unit/test_post_turn_request_vault_id.py .......                    [ 54%]
+tests/unit/test_profile_source_ids.py ...............                    [ 54%]
+tests/unit/test_prompt_injection_context.py ......s                      [ 55%]
+tests/unit/test_prompt_injection_guard.py .............................. [ 55%]
+                                                                         [ 55%]
+tests/unit/test_prompt_registry.py .................................     [ 56%]
+tests/unit/test_pydantic_contracts.py ....................               [ 56%]
+tests/unit/test_qa_38_4_dual_write_extra.py ........x.                   [ 56%]
+tests/unit/test_qa_38_5_fallback_extra.py .......                        [ 56%]
+tests/unit/test_qa_38_6_scoring_reliability_extra.py ........F.ss..      [ 56%]
+tests/unit/test_question_generator_mastery_data.py ...............       [ 57%]
+tests/unit/test_question_registry.py ........                            [ 57%]
+tests/unit/test_rag_multimodal_integration.py .........................  [ 57%]
+tests/unit/test_rag_p0_doc_type_filter.py ..........F......              [ 58%]
+tests/unit/test_react_agent.py ...                                       [ 58%]
+tests/unit/test_read_scope_callers_g41a.py ...............               [ 58%]
+tests/unit/test_recommendation_group_filter.py ..........                [ 58%]
+tests/unit/test_record_learning_memory_docstring.py .....                [ 58%]
+tests/unit/test_remediation_strategy.py ......................           [ 59%]
+tests/unit/test_rerank_service.py ..................                     [ 59%]
+tests/unit/test_retrieval_regression_metric_guard.py ..........          [ 59%]
+tests/unit/test_review_app.py .......................................... [ 60%]
+.........................................................                [ 61%]
+tests/unit/test_review_difficulty_adaptation.py .................        [ 61%]
+tests/unit/test_review_enrichment_signal.py ....                         [ 61%]
+tests/unit/test_review_history_pagination.py .................           [ 61%]
+tests/unit/test_review_mode_support.py ...............                   [ 62%]
+tests/unit/test_review_overview.py ..................................... [ 62%]
+........................................................................ [ 63%]
+........                                                                 [ 64%]
+tests/unit/test_review_service_error_handling.py ..........              [ 64%]
+tests/unit/test_review_service_fsrs.py ................................. [ 64%]
+..................                                                       [ 65%]
+tests/unit/test_s02_entity_types.py ............................         [ 65%]
+tests/unit/test_s02_search_upgrade.py ....................               [ 65%]
+tests/unit/test_safety_meta_rule_in_prompt.py ....                       [ 66%]
+tests/unit/test_schema_gate.py ....                                      [ 66%]
+tests/unit/test_scoring_faithfulness_not_applicable.py ..........        [ 66%]
+tests/unit/test_scoring_scale_fix.py ..................................  [ 66%]
+tests/unit/test_security_p0_vulnerabilities.py ........                  [ 66%]
+tests/unit/test_service_status_contract.py ............................  [ 67%]
+tests/unit/test_session_manager.py ..................................... [ 68%]
+                                                                         [ 68%]
+tests/unit/test_session_progress.py ..........                           [ 68%]
+tests/unit/test_sharpness_report.py ......                               [ 68%]
+tests/unit/test_source_description_contract.py ................          [ 68%]
+tests/unit/test_startup_health_check.py ................                 [ 68%]
+tests/unit/test_state_graph_l1_routing.py ........                       [ 69%]
+tests/unit/test_storage_health.py .......................                [ 69%]
+tests/unit/test_story_1_7_env_config.py .............                    [ 69%]
+tests/unit/test_story_2_3_error_reminders.py ..............F.FF.FF       [ 70%]
+tests/unit/test_story_30_10_idempotency.py ........sssssssss             [ 70%]
+tests/unit/test_story_30_11_batch_parallel.py ...........                [ 70%]
+tests/unit/test_story_30_12_agent_trigger.py .......                     [ 70%]
+tests/unit/test_story_30_13_batch_idempotency.py ...........             [ 70%]
+tests/unit/test_story_30_22_agent_trigger_deep.py ...................... [ 71%]
+...............................................                          [ 71%]
+tests/unit/test_story_30_24_boundary.py ...............................x [ 72%]
+xxxx                                                                     [ 72%]
+tests/unit/test_story_30_6_color_change.py ......                        [ 72%]
+tests/unit/test_story_30_7_plugin_init.py ........                       [ 72%]
+tests/unit/test_story_31a2_ac1_neo4j_priority.py .......                 [ 72%]
+tests/unit/test_story_31a2_ac2_client_method.py ..........               [ 73%]
+tests/unit/test_story_31a2_ac3_persistence.py ...                        [ 73%]
+tests/unit/test_story_31a2_ac4_pagination.py ................            [ 73%]
+tests/unit/test_story_31a2_ac5_api_injection.py .........                [ 73%]
+tests/unit/test_story_33_10_runtime_defects.py ..............            [ 73%]
+tests/unit/test_story_38_1_ac1_auto_trigger.py .........                 [ 73%]
+tests/unit/test_story_38_1_ac2_failure_handling.py ....                  [ 74%]
+tests/unit/test_story_38_1_ac3_startup_recovery.py ........              [ 74%]
+tests/unit/test_story_38_1_review_fixes.py ......                        [ 74%]
+tests/unit/test_story_38_2_episode_recovery.py ................          [ 74%]
+tests/unit/test_story_38_2_qa_supplement.py .................            [ 74%]
+tests/unit/test_story_38_3_edge_cases.py ...........                     [ 75%]
+tests/unit/test_story_38_3_fsrs_init_guarantee.py .....................  [ 75%]
+tests/unit/test_story_38_4_dual_write_default.py ..x.xx.                 [ 75%]
+tests/unit/test_story_38_5_canvas_crud_degradation.py .........          [ 75%]
+tests/unit/test_story_38_6_scoring_reliability.py .............F...      [ 75%]
+tests/unit/test_story_38_8_fallback_sync.py ............................ [ 76%]
+..                                                                       [ 76%]
+tests/unit/test_study_question_deep_mode.py ........                     [ 76%]
+tests/unit/test_subject_config_vault.py .....................            [ 76%]
+tests/unit/test_subject_isolation.py ..........................          [ 77%]
+tests/unit/test_subject_resolver.py .................................... [ 78%]
+...                                                                      [ 78%]
+tests/unit/test_subjects_group_isolation.py ........                     [ 78%]
+tests/unit/test_supplementary_reranker.py .............................. [ 78%]
+..........................                                               [ 79%]
+tests/unit/test_supplementary_search_service.py ........................ [ 79%]
+...............................                                          [ 80%]
+tests/unit/test_sync_batch_auth.py .......                               [ 80%]
+tests/unit/test_sync_exception_classification.py ......                  [ 80%]
+tests/unit/test_sync_group_isolation.py .............                    [ 80%]
+tests/unit/test_sync_payload_validation.py ...........                   [ 80%]
+tests/unit/test_sync_segment_commit.py ..................                [ 81%]
+tests/unit/test_system_endpoint_auth.py ............                     [ 81%]
+tests/unit/test_textbook_removal.py .............                        [ 81%]
+tests/unit/test_traces_backlog_t6c.py .................................. [ 82%]
+.                                                                        [ 82%]
+tests/unit/test_ttlcache_transparency.py ...........                     [ 82%]
+tests/unit/test_validate_release_manifest.py ........................... [ 82%]
+........................................................................ [ 83%]
+.....................................................................    [ 85%]
+tests/unit/test_vault_admission.py ..............                        [ 85%]
+tests/unit/test_vault_backfill.py ...........                            [ 85%]
+tests/unit/test_vault_doc_roles.py ........F............................ [ 86%]
+........................................................................ [ 87%]
+..........                                                               [ 87%]
+tests/unit/test_vault_identity_registry.py ........                      [ 87%]
+tests/unit/test_vault_init_service.py ........                           [ 87%]
+tests/unit/test_vault_install_manifest.py .............................. [ 88%]
+........................................................................ [ 89%]
+........................................................................ [ 90%]
+..                                                                       [ 90%]
+tests/unit/test_vault_lint.py .......................................... [ 91%]
+.................................................                        [ 92%]
+tests/unit/test_vault_notes_group_filter.py .FFF.F                       [ 92%]
+tests/unit/test_vault_scope_409.py ..................................... [ 93%]
+.                                                                        [ 93%]
+tests/unit/test_vault_scope_read_g41a.py ............................... [ 93%]
+......                                                                   [ 93%]
+tests/unit/test_vault_switch.py ..........................               [ 94%]
+tests/unit/test_vault_switch_coordinator.py .......                      [ 94%]
+tests/unit/test_vault_templates.py ...............                       [ 94%]
+tests/unit/test_verification_dedup.py FF.............                    [ 94%]
+tests/unit/test_verification_group_filter.py ..........                  [ 95%]
+tests/unit/test_verification_service_activation.py ...............       [ 95%]
+tests/unit/test_verification_service_injection.py .....                  [ 95%]
+tests/unit/test_w4_sentinel_rebind.py .................................. [ 95%]
+.................................                                        [ 96%]
+tests/unit/test_wave5_stageb_continued_vault_id_injection.py ........... [ 96%]
+.........................                                                [ 97%]
+tests/unit/test_wave5_stageb_vault_id_injection.py ..................... [ 97%]
+.......                                                                  [ 97%]
+tests/unit/test_websocket_endpoints.py .............................F... [ 98%]
+....                                                                     [ 98%]
+tests/unit/test_wikilink_context_service.py ............................ [ 98%]
+................                                                         [ 98%]
+tests/unit/test_wikilink_graph_service.py .............................. [ 99%]
+.....                                                                    [ 99%]
+tests/unit/test_wikilink_parser.py ........................              [100%]
+
+=================================== FAILURES ===================================
+__________ TestMemoryInjection.test_graceful_degradation_on_exception __________
+tests/unit/test_agent_memory_injection.py:273: in test_graceful_degradation_on_exception
+    result = await service._get_learning_memories(
+app/services/agent_service.py:2086: in _get_learning_memories
+    memories = await asyncio.wait_for(
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/tasks.py:488: in wait_for
+    return await fut
+           ^^^^^^^^^
+tests/unit/test_agent_memory_injection.py:63: in search_memories
+    raise Exception("Mock search failure")
+E   Exception: Mock search failure
+---------------------------- Captured stdout setup -----------------------------
+{"event": "AgentService initialized without configured AI client - API calls will fail", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T00:03:32.388395Z"}
+{"event": "AgentService will use LearningMemoryClient for historical context", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T00:03:32.388528Z"}
+{"event": "AgentService initialized without CanvasService - nodes will not be written to Canvas", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T00:03:32.388589Z"}
+{"event": "AgentService Phase 2: Tool calling disabled (ENABLE_TOOL_CALLING=false)", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T00:03:32.388632Z"}
+{"event": "AgentService Phase 4: React Agent ENABLED (ENABLE_REACT_AGENT=true)", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T00:03:32.388669Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.agent_service:agent_service.py:1400 {'event': 'AgentService initialized without configured AI client - API calls will fail', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T00:03:32.388395Z'}
+INFO     app.services.agent_service:agent_service.py:1405 {'event': 'AgentService will use LearningMemoryClient for historical context', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T00:03:32.388528Z'}
+WARNING  app.services.agent_service:agent_service.py:1427 {'event': 'AgentService initialized without CanvasService - nodes will not be written to Canvas', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T00:03:32.388589Z'}
+INFO     app.services.agent_service:agent_service.py:1444 {'event': 'AgentService Phase 2: Tool calling disabled (ENABLE_TOOL_CALLING=false)', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T00:03:32.388632Z'}
+INFO     app.services.agent_service:agent_service.py:1449 {'event': 'AgentService Phase 4: React Agent ENABLED (ENABLE_REACT_AGENT=true)', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T00:03:32.388669Z'}
+______________ TestEdgeCases.test_neo4j_query_error_returns_empty ______________
+tests/unit/test_agent_service_neo4j_memory.py:521: in test_neo4j_query_error_returns_empty
+    result = await agent_service_with_neo4j._get_learning_memories(
+app/services/agent_service.py:2074: in _get_learning_memories
+    result = await asyncio.wait_for(
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/tasks.py:488: in wait_for
+    return await fut
+           ^^^^^^^^^
+app/services/agent_service.py:2183: in _query_neo4j_memories
+    results = await self._neo4j_client.run_query(cypher_query, **params)
+              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:2333: in _execute_mock_call
+    raise effect
+E   Exception: Neo4j connection failed
+---------------------------- Captured stdout setup -----------------------------
+{"event": "AgentService initialized without configured AI client - API calls will fail", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T00:03:34.234696Z"}
+{"event": "AgentService initialized without LearningMemoryClient - historical context fallback unavailable when Neo4j is down", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T00:03:34.234802Z"}
+{"event": "AgentService will use Neo4jClient for learning memory queries", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T00:03:34.234926Z"}
+{"event": "AgentService initialized without CanvasService - nodes will not be written to Canvas", "logger": "app.services.agent_service", "level": "warning", "timestamp": "2026-09-20T00:03:34.234974Z"}
+{"event": "AgentService Phase 2: Tool calling disabled (ENABLE_TOOL_CALLING=false)", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T00:03:34.235012Z"}
+{"event": "AgentService Phase 4: React Agent ENABLED (ENABLE_REACT_AGENT=true)", "logger": "app.services.agent_service", "level": "info", "timestamp": "2026-09-20T00:03:34.235044Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.agent_service:agent_service.py:1400 {'event': 'AgentService initialized without configured AI client - API calls will fail', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T00:03:34.234696Z'}
+WARNING  app.services.agent_service:agent_service.py:1409 {'event': 'AgentService initialized without LearningMemoryClient - historical context fallback unavailable when Neo4j is down', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T00:03:34.234802Z'}
+INFO     app.services.agent_service:agent_service.py:1416 {'event': 'AgentService will use Neo4jClient for learning memory queries', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T00:03:34.234926Z'}
+WARNING  app.services.agent_service:agent_service.py:1427 {'event': 'AgentService initialized without CanvasService - nodes will not be written to Canvas', 'logger': 'app.services.agent_service', 'level': 'warning', 'timestamp': '2026-09-20T00:03:34.234974Z'}
+INFO     app.services.agent_service:agent_service.py:1444 {'event': 'AgentService Phase 2: Tool calling disabled (ENABLE_TOOL_CALLING=false)', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T00:03:34.235012Z'}
+INFO     app.services.agent_service:agent_service.py:1449 {'event': 'AgentService Phase 4: React Agent ENABLED (ENABLE_REACT_AGENT=true)', 'logger': 'app.services.agent_service', 'level': 'info', 'timestamp': '2026-09-20T00:03:34.235044Z'}
+______ TestGetDifficultyData.test_memory_service_unavailable_returns_none ______
+tests/unit/test_difficulty_canvas_integration.py:156: in test_memory_service_unavailable_returns_none
+    result = await _get_difficulty_data(sample_nodes, "test_canvas")
+             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+app/api/v1/endpoints/review.py:298: in _get_difficulty_data
+    memory_service = await get_memory_service()
+                     ^^^^^^^^^^^^^^^^^^^^^^^^^^
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:2333: in _execute_mock_call
+    raise effect
+E   Exception: MemoryService unavailable
+_____ TestAIQuestionDifficultyInjection.test_difficulty_context_in_prompt ______
+tests/unit/test_difficulty_canvas_integration.py:432: in test_difficulty_context_in_prompt
+    await review_mod._generate_ai_questions(sample_nodes, difficulty_map_mixed)
+app/api/v1/endpoints/review.py:467: in _generate_ai_questions
+    agent_service.call_agent(AgentType.VERIFICATION_QUESTION, prompt),
+                             ^^^^^^^^^
+E   NameError: name 'AgentType' is not defined
+___ TestAIQuestionDifficultyInjection.test_no_difficulty_map_no_extra_fields ___
+tests/unit/test_difficulty_canvas_integration.py:476: in test_no_difficulty_map_no_extra_fields
+    await review_mod._generate_ai_questions(sample_nodes, None)
+app/api/v1/endpoints/review.py:467: in _generate_ai_questions
+    agent_service.call_agent(AgentType.VERIFICATION_QUESTION, prompt),
+                             ^^^^^^^^^
+E   NameError: name 'AgentType' is not defined
+____________ test_vault_id_provided_triggers_context_var_injection _____________
+tests/unit/test_enrich_context_vault_isolation.py:113: in test_vault_id_provided_triggers_context_var_injection
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 5.42, "event": "request.completed", "request_id": "5565136144", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T00:06:41.014711Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 5.42, 'event': 'request.completed', 'request_id': '5565136144', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T00:06:41.014711Z'}
+________________ test_chinese_vault_id_not_collapsed_to_default ________________
+tests/unit/test_enrich_context_vault_isolation.py:142: in test_chinese_vault_id_not_collapsed_to_default
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 5.5, "event": "request.completed", "request_id": "5520691600", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T00:06:41.025290Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 5.5, 'event': 'request.completed', 'request_id': '5520691600', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T00:06:41.025290Z'}
+___________________ test_subject_id_optional_backward_compat ___________________
+tests/unit/test_enrich_context_vault_isolation.py:166: in test_subject_id_optional_backward_compat
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 5.04, "event": "request.completed", "request_id": "5520693520", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T00:06:41.034051Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 5.04, 'event': 'request.completed', 'request_id': '5520693520', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T00:06:41.034051Z'}
+__________________ test_vault_id_with_special_chars_sanitized __________________
+tests/unit/test_enrich_context_vault_isolation.py:233: in test_vault_id_with_special_chars_sanitized
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 5.62, "event": "request.completed", "request_id": "5520698128", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T00:06:41.056636Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 5.62, 'event': 'request.completed', 'request_id': '5520698128', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T00:06:41.056636Z'}
+_________________________ test_vault_id_emoji_stripped _________________________
+tests/unit/test_enrich_context_vault_isolation.py:255: in test_vault_id_emoji_stripped
+    assert resp.status_code == 200
+E   assert 409 == 200
+E    +  where 409 = <Response [409 Conflict]>.status_code
+----------------------------- Captured stdout call -----------------------------
+{"method": "POST", "path": "/api/v1/chat/enrich-context", "endpoint": "/api/v1/chat/enrich-context", "status": 409, "duration_ms": 4.83, "event": "request.completed", "request_id": "5520698320", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T00:06:41.065759Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/chat/enrich-context', 'endpoint': '/api/v1/chat/enrich-context', 'status': 409, 'duration_ms': 4.83, 'event': 'request.completed', 'request_id': '5520698320', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T00:06:41.065759Z'}
+_ TestRecordTemporalEventLifecycle.test_p0_neo4j_write_failure_degrades_silently _
+tests/unit/test_epic30_memory_pipeline.py:400: in test_p0_neo4j_write_failure_degrades_silently
+    event_id = await svc.record_temporal_event(
+app/services/memory_service.py:2627: in record_temporal_event
+    await self.neo4j.record_episode(
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:2333: in _execute_mock_call
+    raise effect
+E   Exception: Connection refused
+----------------------------- Captured stdout call -----------------------------
+{"event": "MemoryService: recovered 0 episodes from Neo4j (0 returned, 0 deduped)", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T00:06:41.108941Z"}
+{"event": "MemoryService initialized successfully", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T00:06:41.109023Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.memory_service:memory_service.py:431 {'event': 'MemoryService: recovered 0 episodes from Neo4j (0 returned, 0 deduped)', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T00:06:41.108941Z'}
+INFO     app.services.memory_service:memory_service.py:287 {'event': 'MemoryService initialized successfully', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T00:06:41.109023Z'}
+___ TestGetRelatedMemoriesReturnStructure.test_query_exception_returns_empty ___
+tests/unit/test_epic36_gap_coverage.py:150: in test_query_exception_returns_empty
+    results = await graphiti_client.get_related_memories(node_id="node-1")
+              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+app/clients/neo4j_edge_client.py:436: in get_related_memories
+    results = await self._neo4j.run_query(cypher_query, **params)
+              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:2333: in _execute_mock_call
+    raise effect
+E   Exception: Connection lost
+----------------------------- Captured stdout call -----------------------------
+{"event": "Neo4jEdgeClient initialized: neo4j_mode=BOLT", "logger": "app.clients.neo4j_learning_base", "level": "info", "timestamp": "2026-09-20T00:06:41.468127Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.clients.neo4j_learning_base:neo4j_learning_base.py:189 Neo4jEdgeClient initialized: neo4j_mode=BOLT
+____________ TestProgressEndpoint.test_progress_invalid_session_404 ____________
+tests/unit/test_intelligent_parallel_endpoints.py:437: in test_progress_invalid_session_404
+    assert response.status_code == status.HTTP_404_NOT_FOUND
+E   assert 500 == 404
+E    +  where 500 = <Response [500 Internal Server Error]>.status_code
+E    +  and   404 = status.HTTP_404_NOT_FOUND
+---------------------------- Captured stdout setup -----------------------------
+{"event": "IntelligentParallelService: batch_orchestrator not injected \u2014 batch execution will fail", "logger": "app.services.intelligent_parallel_service", "level": "warning", "timestamp": "2026-09-20T00:07:20.884094Z"}
+{"event": "IntelligentParallelService initialized with real service dependencies", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T00:07:20.884185Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.intelligent_parallel_service:intelligent_parallel_service.py:106 {'event': 'IntelligentParallelService: batch_orchestrator not injected — batch execution will fail', 'logger': 'app.services.intelligent_parallel_service', 'level': 'warning', 'timestamp': '2026-09-20T00:07:20.884094Z'}
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:121 {'event': 'IntelligentParallelService initialized with real service dependencies', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:20.884185Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "get_session_status called: session_id=nonexistent-session", "request_id": "5536605456", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T00:07:20.885371Z"}
+{"method": "GET", "path": "/api/v1/canvas/intelligent-parallel/nonexistent-session", "endpoint": "/api/v1/canvas/intelligent-parallel/nonexistent-session", "status": 500, "duration_ms": 1.13, "event": "request.completed", "request_id": "5536605456", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T00:07:20.885998Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:326 {'event': 'get_session_status called: session_id=nonexistent-session', 'request_id': '5536605456', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:20.885371Z'}
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'GET', 'path': '/api/v1/canvas/intelligent-parallel/nonexistent-session', 'endpoint': '/api/v1/canvas/intelligent-parallel/nonexistent-session', 'status': 500, 'duration_ms': 1.13, 'event': 'request.completed', 'request_id': '5536605456', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T00:07:20.885998Z'}
+____________ TestCancelEndpoint.test_cancel_nonexistent_session_404 ____________
+tests/unit/test_intelligent_parallel_endpoints.py:492: in test_cancel_nonexistent_session_404
+    assert response.status_code == status.HTTP_404_NOT_FOUND
+E   assert 500 == 404
+E    +  where 500 = <Response [500 Internal Server Error]>.status_code
+E    +  and   404 = status.HTTP_404_NOT_FOUND
+---------------------------- Captured stdout setup -----------------------------
+{"event": "IntelligentParallelService: batch_orchestrator not injected \u2014 batch execution will fail", "logger": "app.services.intelligent_parallel_service", "level": "warning", "timestamp": "2026-09-20T00:07:20.899008Z"}
+{"event": "IntelligentParallelService initialized with real service dependencies", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T00:07:20.899114Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.intelligent_parallel_service:intelligent_parallel_service.py:106 {'event': 'IntelligentParallelService: batch_orchestrator not injected — batch execution will fail', 'logger': 'app.services.intelligent_parallel_service', 'level': 'warning', 'timestamp': '2026-09-20T00:07:20.899008Z'}
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:121 {'event': 'IntelligentParallelService initialized with real service dependencies', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:20.899114Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "cancel_session called: session_id=nonexistent-session", "request_id": "5536609104", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T00:07:20.900225Z"}
+{"method": "POST", "path": "/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session", "endpoint": "/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session", "status": 500, "duration_ms": 0.74, "event": "request.completed", "request_id": "5536609104", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T00:07:20.900581Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:480 {'event': 'cancel_session called: session_id=nonexistent-session', 'request_id': '5536609104', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:20.900225Z'}
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'POST', 'path': '/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session', 'endpoint': '/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session', 'status': 500, 'duration_ms': 0.74, 'event': 'request.completed', 'request_id': '5536609104', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T00:07:20.900581Z'}
+___________________ TestErrorResponses.test_404_error_format ___________________
+tests/unit/test_intelligent_parallel_endpoints.py:594: in test_404_error_format
+    assert response.status_code == status.HTTP_404_NOT_FOUND
+E   assert 500 == 404
+E    +  where 500 = <Response [500 Internal Server Error]>.status_code
+E    +  and   404 = status.HTTP_404_NOT_FOUND
+---------------------------- Captured stdout setup -----------------------------
+{"event": "IntelligentParallelService: batch_orchestrator not injected \u2014 batch execution will fail", "logger": "app.services.intelligent_parallel_service", "level": "warning", "timestamp": "2026-09-20T00:07:20.921502Z"}
+{"event": "IntelligentParallelService initialized with real service dependencies", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T00:07:20.921607Z"}
+------------------------------ Captured log setup ------------------------------
+WARNING  app.services.intelligent_parallel_service:intelligent_parallel_service.py:106 {'event': 'IntelligentParallelService: batch_orchestrator not injected — batch execution will fail', 'logger': 'app.services.intelligent_parallel_service', 'level': 'warning', 'timestamp': '2026-09-20T00:07:20.921502Z'}
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:121 {'event': 'IntelligentParallelService initialized with real service dependencies', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:20.921607Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "get_session_status called: session_id=nonexistent-session", "request_id": "5538452048", "logger": "app.services.intelligent_parallel_service", "level": "info", "timestamp": "2026-09-20T00:07:20.922665Z"}
+{"method": "GET", "path": "/api/v1/canvas/intelligent-parallel/nonexistent-session", "endpoint": "/api/v1/canvas/intelligent-parallel/nonexistent-session", "status": 500, "duration_ms": 0.7, "event": "request.completed", "request_id": "5538452048", "logger": "app.middleware.metrics", "level": "info", "timestamp": "2026-09-20T00:07:20.922962Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.intelligent_parallel_service:intelligent_parallel_service.py:326 {'event': 'get_session_status called: session_id=nonexistent-session', 'request_id': '5538452048', 'logger': 'app.services.intelligent_parallel_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:20.922665Z'}
+INFO     app.middleware.metrics:metrics.py:145 {'method': 'GET', 'path': '/api/v1/canvas/intelligent-parallel/nonexistent-session', 'endpoint': '/api/v1/canvas/intelligent-parallel/nonexistent-session', 'status': 500, 'duration_ms': 0.7, 'event': 'request.completed', 'request_id': '5538452048', 'logger': 'app.middleware.metrics', 'level': 'info', 'timestamp': '2026-09-20T00:07:20.922962Z'}
+________ TestEnsureFulltextIndex.test_ensure_fulltext_index_idempotent _________
+tests/unit/test_neo4j_fulltext_index.py:129: in test_ensure_fulltext_index_idempotent
+    assert create_count == 4, (
+E   AssertionError: Should execute CREATE FULLTEXT INDEX each time × 2 indexes (IF NOT EXISTS handles idempotency, Round-23 Patch 3 added node_search_unified)
+E   assert 2 == 4
+----------------------------- Captured stdout call -----------------------------
+{"event": "MemoryService: recovered 0 episodes from Neo4j (0 returned, 0 deduped)", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T00:07:30.510572Z"}
+{"event": "MemoryService initialized successfully", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T00:07:30.510681Z"}
+{"event": "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T00:07:30.510738Z"}
+{"event": "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T00:07:30.510778Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.memory_service:memory_service.py:431 {'event': 'MemoryService: recovered 0 episodes from Neo4j (0 returned, 0 deduped)', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:30.510572Z'}
+INFO     app.services.memory_service:memory_service.py:287 {'event': 'MemoryService initialized successfully', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:30.510681Z'}
+INFO     app.services.memory_service:memory_service.py:316 {'event': "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content", 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:30.510738Z'}
+INFO     app.services.memory_service:memory_service.py:316 {'event': "[Epic 4] Fulltext index 'episode_content' ensured on EpisodicNode.content", 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:30.510778Z'}
+__________ TestMergedViewEdgeCases.test_merged_view_sort_newest_first __________
+tests/unit/test_qa_38_6_scoring_reliability_extra.py:293: in test_merged_view_sort_newest_first
+    assert len(items) == 3
+E   AssertionError: assert 1 == 3
+E    +  where 1 = len([{'concept': 'concept_mid', 'node_id': 'node_mid', 'score': 50.0, 'timestamp': '2026-02-06T10:00:00'}])
+______________ test_strip_whiteboard_removes_admonition_callouts _______________
+tests/unit/test_rag_p0_doc_type_filter.py:169: in test_strip_whiteboard_removes_admonition_callouts
+    assert "原白板说明" not in out
+E   assert '原白板说明' not in '\n> [!info]...= 节点关系**\n\n'
+E     
+E     '原白板说明' is contained here:
+E       
+E       > [!info]+ 原白板说明（扁平架构 · round-11）
+E     ?            +++++
+E       > 这是学习主题"线性代数"的原白板。
+E       >...
+E     
+E     ...Full output truncated (15 lines hidden), use '-vv' to show
+______________ test_search_error_memories_sorts_by_timestamp_desc ______________
+tests/unit/test_story_2_3_error_reminders.py:345: in test_search_error_memories_sorts_by_timestamp_desc
+    assert descriptions == ["newest", "middle", "old"]
+E   AssertionError: assert ['old', 'newest', 'middle'] == ['newest', 'middle', 'old']
+E     
+E     At index 0 diff: 'old' != 'newest'
+E     Use -v to get more diff
+_________________ test_search_error_memories_normalizes_schema _________________
+tests/unit/test_story_2_3_error_reminders.py:403: in test_search_error_memories_normalizes_schema
+    assert err["corrected_at"] == "2026-04-16T09:00:00"  # metadata wins over timestamp
+    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+E   AssertionError: assert '2026-04-15T12:34:56' == '2026-04-16T09:00:00'
+E     
+E     - 2026-04-16T09:00:00
+E     + 2026-04-15T12:34:56
+_____ test_search_error_memories_passes_node_id_filter_to_search_memories ______
+tests/unit/test_story_2_3_error_reminders.py:417: in test_search_error_memories_passes_node_id_filter_to_search_memories
+    await svc.search_error_memories(
+app/services/memory_service.py:2557: in search_error_memories
+    result = await self.search_error_memories_with_status(
+app/services/memory_service.py:2510: in search_error_memories_with_status
+    hits = search_result.items
+           ^^^^^^^^^^^^^^^^^^^
+E   AttributeError: 'list' object has no attribute 'items'
+________________ test_search_memories_node_id_filter_post_merge ________________
+tests/unit/test_story_2_3_error_reminders.py:470: in test_search_memories_node_id_filter_post_merge
+    assert len(all_results) == 2
+E   AssertionError: assert 1 == 2
+E    +  where 1 = len([{'content': 'b', 'episode_id': 'ep-2e2d', 'episode_type': 'error', 'group_id': 'vault:cs_61b', ...}])
+----------------------------- Captured stdout call -----------------------------
+{"event": "[search_memories] Tier 1: 1 results, Tier 2: 1 results, Tier 3: 0 results (deduped 1, floor=0.05, returned 1)", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T00:07:44.114989Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.memory_service:memory_service.py:2430 {'event': '[search_memories] Tier 1: 1 results, Tier 2: 1 results, Tier 3: 0 results (deduped 1, floor=0.05, returned 1)', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:44.114989Z'}
+________________ test_search_memories_node_id_none_is_no_filter ________________
+tests/unit/test_story_2_3_error_reminders.py:498: in test_search_memories_node_id_none_is_no_filter
+    assert len(results) == 3
+E   assert 0 == 3
+E    +  where 0 = len([])
+----------------------------- Captured stdout call -----------------------------
+{"event": "[search_memories] Tier 1: 3 results, Tier 2: 0 results, Tier 3: 0 results (deduped 3, floor=0.05, returned 0)", "logger": "app.services.memory_service", "level": "info", "timestamp": "2026-09-20T00:07:44.120496Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.services.memory_service:memory_service.py:2430 {'event': '[search_memories] Tier 1: 3 results, Tier 2: 0 results, Tier 3: 0 results (deduped 3, floor=0.05, returned 0)', 'logger': 'app.services.memory_service', 'level': 'info', 'timestamp': '2026-09-20T00:07:44.120496Z'}
+_______ TestAC4MergedView.test_get_learning_history_merges_failed_scores _______
+tests/unit/test_story_38_6_scoring_reliability.py:465: in test_get_learning_history_merges_failed_scores
+    assert result["total"] == 2
+E   assert 1 == 2
+________________________ test_live_vault_enforce_clean _________________________
+tests/unit/test_vault_doc_roles.py:481: in test_live_vault_enforce_clean
+    assert proc.returncode == 0, proc.stdout + proc.stderr
+E   AssertionError: [2m台账[0m /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/vault_doc_roles.yaml
+E     [2mvault[0m /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault  (176 目录 / 326 文件, 只读)
+E     [2m双准入面实测分歧[0m 1 条: chatgpt-adversarial-review-Q1Q2Q3-2026-05-12.md
+E     [2m  info  .quarantine/UAT-2.5.X-test.md 的准入两列取自 any_level 行 root-uat-scratch(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-quarantine 为准[0m
+E     [2m  info  raw/CS188/CLAUDE.md 的准入两列取自 any_level 行 root-claude-md(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-raw 为准[0m
+E     [2m  info  raw/CS188/_misc/junk/未命名 1.md 的准入两列取自 any_level 行 root-untitled-scratch(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-misc-junk 为准[0m
+E     [2m  info  raw/CS188/_misc/junk/未命名.md 的准入两列取自 any_level 行 root-untitled-scratch(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-misc-junk 为准[0m
+E     [2m  info  raw/CS188/管道设计.md 的准入两列取自 any_level 行 root-pipeline-design(文件名黑名单盖过目录), 但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 dir-raw 为准[0m
+E     [2m  info  勘测快照漂移 total_files: 台账 324 → 实测 326[0m
+E     [91mG1[0m  3 条 (阻断 3)
+E         - backups
+E           live 目录未被任何 vault_entries.dir_glob 命中
+E         - backups
+E           文件 backups/fsrs_bridge.py.pre-deploy-2026-09-05T1052.bak 所在目录未被登记
+E         - backups
+E           文件 backups/fsrs_bridge.py.pre-deploy-2026-09-07T0328.bak 所在目录未被登记
+E     /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
+E       from pydantic.v1.fields import FieldInfo as FieldInfoV1
+E     /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
+E       import pkg_resources
+E     Building prefix dict from the default dictionary ...
+E     Loading model from cache /var/folders/vq/gssw8vy54671lh9nlqc_ft2w0000gn/T/jieba.cache
+E     Loading model cost 0.270 seconds.
+E     Prefix dict has been built successfully.
+E     2026-09-19 17:08:32 [info     ] RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True
+E     
+E   assert 1 == 0
+E    +  where 1 = CompletedProcess(args=['/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/...uccessfully.\n2026-09-19 17:08:32 [info     ] RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True\n").returncode
+________________ test_group_id_physics_filters_to_physics_only _________________
+tests/unit/test_vault_notes_group_filter.py:97: in test_group_id_physics_filters_to_physics_only
+    assert len(out) == 1
+E   AssertionError: assert 2 == 1
+E    +  where 2 = len([{'id': 'r_phys', 'metadata': {'source': 'vault_note', 'subject_id': 'physics'}, 'score': 0.8}, {'id': 'r_math', 'metadata': {'source': 'vault_note', 'subject_id': 'math'}, 'score': 0.8}])
+________ test_group_id_with_no_explicit_match_returns_only_common_notes ________
+tests/unit/test_vault_notes_group_filter.py:124: in test_group_id_with_no_explicit_match_returns_only_common_notes
+    assert ids == {"r_common"}
+E   AssertionError: assert {'r1', 'r2', 'r_common'} == {'r_common'}
+E     
+E     Extra items in the left set:
+E     'r2'
+E     'r1'
+E     Use -v to get more diff
+___________ test_group_id_with_no_common_and_no_match_returns_empty ____________
+tests/unit/test_vault_notes_group_filter.py:139: in test_group_id_with_no_common_and_no_match_returns_empty
+    assert out == []
+E   AssertionError: assert [{'id': 'r1',...'score': 0.8}] == []
+E     
+E     Left contains 2 more items, first extra item: {'id': 'r1', 'metadata': {'source': 'vault_note', 'subject_id': 'physics'}, 'score': 0.8}
+E     Use -v to get more diff
+______________ test_group_id_honors_nested_metadata_json_subject _______________
+tests/unit/test_vault_notes_group_filter.py:185: in test_group_id_honors_nested_metadata_json_subject
+    assert len(out) == 1
+E   AssertionError: assert 2 == 1
+E    +  where 2 = len([{'id': 'r_nested', 'metadata': {'file_path': 'r_nested.md', 'heading': None, 'line_end': None, 'line_start': None, .....etadata': {'file_path': 'r_math_nested.md', 'heading': None, 'line_end': None, 'line_start': None, ...}, 'score': 0.8}])
+______ TestVerificationDedup.test_no_history_generates_standard_question _______
+tests/unit/test_verification_dedup.py:49: in test_no_history_generates_standard_question
+    mock_graphiti_client.search_verification_questions.assert_called_once()
+/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/mock.py:965: in assert_called_once
+    raise AssertionError(msg)
+E   AssertionError: Expected 'search_verification_questions' to have been called once. Called 0 times.
+---------------------------- Captured stdout setup -----------------------------
+{"event": "VerificationService initialized (RAG: False, Canvas: False, Agent: True, Graphiti: True, Memory: False, MockMode: False)", "logger": "app.services.verification_service", "level": "info", "timestamp": "2026-09-20T00:09:46.448123Z"}
+{"event": "VerificationService using IN-MEMORY TTLCache for session storage (maxsize=500, ttl=3600s). Sessions will be LOST on service restart. This is a known limitation \u2014 see Story 31.A.7.", "logger": "app.services.verification_service", "level": "warning", "timestamp": "2026-09-20T00:09:46.448246Z"}
+------------------------------ Captured log setup ------------------------------
+INFO     app.services.verification_service:verification_service.py:613 {'event': 'VerificationService initialized (RAG: False, Canvas: False, Agent: True, Graphiti: True, Memory: False, MockMode: False)', 'logger': 'app.services.verification_service', 'level': 'info', 'timestamp': '2026-09-20T00:09:46.448123Z'}
+WARNING  app.services.verification_service:verification_service.py:624 {'event': 'VerificationService using IN-MEMORY TTLCache for session storage (maxsize=500, ttl=3600s). Sessions will be LOST on service restart. This is a known limitation — see Story 31.A.7.', 'logger': 'app.services.verification_service', 'level': 'warning', 'timestamp': '2026-09-20T00:09:46.448246Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "No agent service available, using fallback question for \u9006\u5426\u547d\u9898", "logger": "app.services.verification_service", "level": "warning", "timestamp": "2026-09-20T00:09:46.449276Z"}
+------------------------------ Captured log call -------------------------------
+WARNING  app.services.verification_service:verification_service.py:2961 {'event': 'No agent service available, using fallback question for 逆否命题', 'logger': 'app.services.verification_service', 'level': 'warning', 'timestamp': '2026-09-20T00:09:46.449276Z'}
+____ TestVerificationDedup.test_with_history_generates_alternative_question ____
+tests/unit/test_verification_dedup.py:82: in test_with_history_generates_alternative_question
+    assert mock_graphiti_client.search_verification_questions.called
+E   AssertionError: assert False
+E    +  where False = <AsyncMock name='mock.search_verification_questions' id='5646105104'>.called
+E    +    where <AsyncMock name='mock.search_verification_questions' id='5646105104'> = <MagicMock id='5646943632'>.search_verification_questions
+---------------------------- Captured stdout setup -----------------------------
+{"event": "VerificationService initialized (RAG: False, Canvas: False, Agent: True, Graphiti: True, Memory: False, MockMode: False)", "logger": "app.services.verification_service", "level": "info", "timestamp": "2026-09-20T00:09:46.471910Z"}
+{"event": "VerificationService using IN-MEMORY TTLCache for session storage (maxsize=500, ttl=3600s). Sessions will be LOST on service restart. This is a known limitation \u2014 see Story 31.A.7.", "logger": "app.services.verification_service", "level": "warning", "timestamp": "2026-09-20T00:09:46.472051Z"}
+------------------------------ Captured log setup ------------------------------
+INFO     app.services.verification_service:verification_service.py:613 {'event': 'VerificationService initialized (RAG: False, Canvas: False, Agent: True, Graphiti: True, Memory: False, MockMode: False)', 'logger': 'app.services.verification_service', 'level': 'info', 'timestamp': '2026-09-20T00:09:46.471910Z'}
+WARNING  app.services.verification_service:verification_service.py:624 {'event': 'VerificationService using IN-MEMORY TTLCache for session storage (maxsize=500, ttl=3600s). Sessions will be LOST on service restart. This is a known limitation — see Story 31.A.7.', 'logger': 'app.services.verification_service', 'level': 'warning', 'timestamp': '2026-09-20T00:09:46.472051Z'}
+----------------------------- Captured stdout call -----------------------------
+{"event": "No agent service available, using fallback question for \u9006\u5426\u547d\u9898", "logger": "app.services.verification_service", "level": "warning", "timestamp": "2026-09-20T00:09:46.473481Z"}
+------------------------------ Captured log call -------------------------------
+WARNING  app.services.verification_service:verification_service.py:2961 {'event': 'No agent service available, using fallback question for 逆否命题', 'logger': 'app.services.verification_service', 'level': 'warning', 'timestamp': '2026-09-20T00:09:46.473481Z'}
+_____ TestWebSocketEndpoint.test_validate_session_handles_validator_error ______
+tests/unit/test_websocket_endpoints.py:538: in test_validate_session_handles_validator_error
+    result = await validate_session("any-session")
+             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+app/api/v1/endpoints/websocket.py:80: in validate_session
+    return await _session_validator(session_id)
+           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+tests/unit/test_websocket_endpoints.py:533: in failing_validator
+    raise Exception("Validator error")
+E   Exception: Validator error
+----------------------------- Captured stdout call -----------------------------
+{"event": "Session validator set for WebSocket endpoint", "logger": "app.api.v1.endpoints.websocket", "level": "info", "timestamp": "2026-09-20T00:09:46.673791Z"}
+------------------------------ Captured log call -------------------------------
+INFO     app.api.v1.endpoints.websocket:websocket.py:59 Session validator set for WebSocket endpoint
+=============================== warnings summary ===============================
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/google/genai/types.py:43: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
+    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
+    from pydantic.v1.fields import FieldInfo as FieldInfoV1
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/graphiti_core/driver/search_interface/search_interface.py:22: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
+    class SearchInterface(BaseModel):
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/jieba/_compat.py:18: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
+    import pkg_resources
+
+<frozen importlib._bootstrap>:491
+  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute
+
+<frozen importlib._bootstrap>:491
+  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute
+
+app/api/v1/endpoints/chat.py:807
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/chat.py:807: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
+    class HookEnrichRequest(BaseModel):
+
+app/api/v1/endpoints/metadata.py:103
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/metadata.py:103: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
+    canvas_path: str = Query(
+
+app/api/v1/endpoints/metadata.py:177
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/metadata.py:177: FastAPIDeprecationWarning: `example` has been deprecated, please use `examples` instead
+    canvas_path: str = Query(..., description="Canvas file path", example="Math 54/离散数学.canvas"),
+
+../../card-v5-lance/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2356: PydanticDeprecatedSince211: The `__get_pydantic_core_schema__` method of the `BaseModel` class is deprecated. If you are calling `super().__get_pydantic_core_schema__` when overriding the method on a Pydantic model, consider using `handler(source)` instead. However, note that overriding this method on models can lead to unexpected side effects. Deprecated in Pydantic V2.11 to be removed in V3.0.
+    schema = annotation_get_schema(source, get_inner_schema)
+
+tests/unit/test_agentic_rag_vault_scope.py::TestDualVaultIsolationOnTmpLanceDB::test_shared_db_precondition_tables_coexist
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_agentic_rag_vault_scope.py:499: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    names = set(self.db.table_names())
+
+tests/unit/test_agentic_rag_vault_scope.py: 1 warning
+tests/unit/test_g24_lance_legacy_table_removal.py: 17 warnings
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py: 56 warnings
+  /opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/events.py:94: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    self._context.run(self._callback, *self._args)
+
+tests/unit/test_batch_orchestrator.py::TestProgressBroadcasting::test_broadcast_calls_sync_callback
+tests/unit/test_batch_orchestrator.py::TestProgressBroadcasting::test_broadcast_calls_async_callback
+tests/unit/test_batch_orchestrator.py::TestProgressBroadcasting::test_broadcast_handles_callback_error
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/services/batch_orchestrator.py:968: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
+    if asyncio.iscoroutinefunction(self.progress_callback):
+
+tests/unit/test_canvas_memory_trigger.py: 2 warnings
+tests/unit/test_recommendation_group_filter.py: 11 warnings
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/pydantic/main.py:250: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
+    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
+
+tests/unit/test_canvas_projection_sync.py: 6 warnings
+tests/unit/test_frontmatter_signals.py: 6 warnings
+tests/unit/test_vault_backfill.py: 4 warnings
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/lib/python3.14/site-packages/frontmatter/__init__.py:161: DeprecationWarning: codecs.open() is deprecated. Use open() instead.
+    with codecs.open(fd, "r", encoding) as f:
+
+tests/unit/test_edge_rationale_fallback.py::test_both_writes_succeed_returns_200
+tests/unit/test_edge_rationale_fallback.py::test_graphiti_ok_lancedb_fail_returns_207
+tests/unit/test_edge_rationale_fallback.py::test_lancedb_ok_graphiti_fail_returns_207
+tests/unit/test_edge_rationale_fallback.py::test_both_writes_fail_returns_500
+tests/unit/test_edge_rationale_fallback.py::test_graphiti_exception_does_not_block_lancedb
+tests/unit/test_edge_rationale_fallback.py::test_lancedb_exception_does_not_block_graphiti
+tests/unit/test_edge_rationale_fallback.py::test_partial_failure_includes_error_details
+tests/unit/test_edge_rationale_fallback.py::test_strategy_fields_accepted
+tests/unit/test_edge_rationale_fallback.py::test_strategy_fields_defaults
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/edges.py:411: DeprecationWarning: deprecated
+    legacy_group_id=rationale.group_id,
+
+tests/unit/test_edge_rationale_fallback.py: 12 warnings
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/models/edge_rationale.py:115: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
+    default_factory=lambda: datetime.utcnow().isoformat(),
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_bare_table_really_holds_other_vault_rows
+tests/unit/test_g24_lance_legacy_table_removal.py::test_default_vault_still_maps_to_bare_table
+tests/unit/test_g24_lance_legacy_table_removal.py::test_prefixed_missing_no_longer_falls_back_to_bare
+tests/unit/test_g24_lance_legacy_table_removal.py::test_search_raises_table_missing_and_never_opens_bare_table
+tests/unit/test_g24_lance_legacy_table_removal.py::test_table_missing_penetrates_enable_fallback_swallow_gate
+tests/unit/test_g24_lance_legacy_table_removal.py::test_search_supplementary_surfaces_unavailable
+tests/unit/test_g24_lance_legacy_table_removal.py::test_write_creates_prefixed_table_and_leaves_bare_byte_identical
+tests/unit/test_g24_lance_legacy_table_removal.py::test_is_table_absent_distinguishes_missing_from_unopenable
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:69: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert set(db.table_names()) == {"vault_notes"}
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_prefixed_missing_no_longer_falls_back_to_bare
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:122: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert "xvault_vault_notes" not in client._db.table_names()
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_prefixed_missing_no_longer_falls_back_to_bare
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:123: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert "vault_notes" in client._db.table_names()
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_write_creates_prefixed_table_and_leaves_bare_byte_identical
+tests/unit/test_g24_lance_legacy_table_removal.py::test_default_vault_write_still_targets_bare_table
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/lib/agentic_rag/clients/lancedb_client.py:4414: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    if data and table_name in self._db.table_names():
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_write_creates_prefixed_table_and_leaves_bare_byte_identical
+tests/unit/test_g24_lance_legacy_table_removal.py::test_default_vault_write_still_targets_bare_table
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/lib/agentic_rag/clients/lancedb_client.py:4423: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    if table_name in self._db.table_names():
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_write_creates_prefixed_table_and_leaves_bare_byte_identical
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:215: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert "xvault_vault_notes" in db.table_names(), "新 vault 的数据必须落进自己的表"
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_default_vault_write_still_targets_bare_table
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:246: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert db2.table_names() == ["vault_notes"], "default vault 不得凭空造 prefixed 表"
+
+tests/unit/test_g24_lance_legacy_table_removal.py::test_is_table_absent_sees_past_default_pagination
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_g24_lance_legacy_table_removal.py:285: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert len(list(db.table_names())) == 10, "lancedb 默认分页行为变了, 本锁需重新校准"
+
+tests/unit/test_intelligent_parallel_endpoints.py::TestAnalyzeEndpoint::test_analyze_invalid_color
+tests/unit/test_intelligent_parallel_endpoints.py::TestConfirmEndpoint::test_confirm_timeout_validation
+  /opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/asyncio/events.py:94: DeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
+    self._context.run(self._callback, *self._args)
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py: 47 warnings
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:109: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    return set(db.table_names(limit=10_000))
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_cache_tables_scans_beyond_default_page
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:355: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert len(db.table_names()) == 10, (
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_cache_tables_scans_beyond_default_page
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:359: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert "a_t11" not in set(db.table_names()), "前提失效: a_t11 不在默认分页的盲区里"
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_prefix_overlap_premises_hold[page-inner-0-cache-a_b_canvas_nodes]
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:553: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    in_page = table in set(db.table_names())
+
+tests/unit/test_lancedb_cross_vault_drop_g29f1.py::test_fingerprint_baseline_readable_beyond_default_page
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:1009: DeprecationWarning: table_names() is deprecated, use list_tables() instead
+    assert fp_name not in set(db.table_names()), (
+
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_targeted_mode_queries_graphiti
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_targeted_mode_queries_graphiti
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_targeted_mode_weight_distribution
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_targeted_mode_weight_distribution
+tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_custom_weights_applied
+tests/unit/test_review_mode_support.py::TestReviewModeFallback::test_targeted_mode_no_fallback_with_history
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/services/weight_calculator.py:181: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
+    days_since = (datetime.utcnow() - last_review).days
+
+tests/unit/test_sync_batch_auth.py: 2 warnings
+tests/unit/test_sync_exception_classification.py: 6 warnings
+tests/unit/test_sync_group_isolation.py: 1 warning
+tests/unit/test_vault_scope_409.py: 1 warning
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/sync.py:117: DeprecationWarning: deprecated
+    legacy_group_id=request.group_id,
+
+tests/unit/test_vault_scope_409.py::TestCodexRound1RectifiedEndpoints::test_inheritance_distill_mismatch_409
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/app/api/v1/endpoints/inheritance.py:83: DeprecationWarning: deprecated
+    request.vault_id, legacy_group_id=request.group_id
+
+tests/unit/test_wave5_stageb_continued_vault_id_injection.py::TestSyncBatchRequestVaultId::test_sync_batch_has_deprecated_group_id
+  /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/tests/unit/test_wave5_stageb_continued_vault_id_injection.py:218: DeprecationWarning: deprecated
+    assert req.group_id == "cs188"
+
+-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
+NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
+=========================== short test summary info ============================
+FAILED tests/unit/test_agent_memory_injection.py::TestMemoryInjection::test_graceful_degradation_on_exception
+FAILED tests/unit/test_agent_service_neo4j_memory.py::TestEdgeCases::test_neo4j_query_error_returns_empty
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestGetDifficultyData::test_memory_service_unavailable_returns_none
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_difficulty_context_in_prompt
+FAILED tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_no_difficulty_map_no_extra_fields
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_provided_triggers_context_var_injection
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_chinese_vault_id_not_collapsed_to_default
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_subject_id_optional_backward_compat
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_with_special_chars_sanitized
+FAILED tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_emoji_stripped
+FAILED tests/unit/test_epic30_memory_pipeline.py::TestRecordTemporalEventLifecycle::test_p0_neo4j_write_failure_degrades_silently
+FAILED tests/unit/test_epic36_gap_coverage.py::TestGetRelatedMemoriesReturnStructure::test_query_exception_returns_empty
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestProgressEndpoint::test_progress_invalid_session_404
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestCancelEndpoint::test_cancel_nonexistent_session_404
+FAILED tests/unit/test_intelligent_parallel_endpoints.py::TestErrorResponses::test_404_error_format
+FAILED tests/unit/test_neo4j_fulltext_index.py::TestEnsureFulltextIndex::test_ensure_fulltext_index_idempotent
+FAILED tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestMergedViewEdgeCases::test_merged_view_sort_newest_first
+FAILED tests/unit/test_rag_p0_doc_type_filter.py::test_strip_whiteboard_removes_admonition_callouts
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_sorts_by_timestamp_desc
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_normalizes_schema
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_passes_node_id_filter_to_search_memories
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_filter_post_merge
+FAILED tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_none_is_no_filter
+FAILED tests/unit/test_story_38_6_scoring_reliability.py::TestAC4MergedView::test_get_learning_history_merges_failed_scores
+FAILED tests/unit/test_vault_doc_roles.py::test_live_vault_enforce_clean - AssertionError: [2m台账[0m /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/backend/scripts/vault_doc_roles.yaml
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_physics_filters_to_physics_only
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_explicit_match_returns_only_common_notes
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_common_and_no_match_returns_empty
+FAILED tests/unit/test_vault_notes_group_filter.py::test_group_id_honors_nested_metadata_json_subject
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_no_history_generates_standard_question
+FAILED tests/unit/test_verification_dedup.py::TestVerificationDedup::test_with_history_generates_alternative_question
+FAILED tests/unit/test_websocket_endpoints.py::TestWebSocketEndpoint::test_validate_session_handles_validator_error
+= 32 failed, 5771 passed, 44 skipped, 13 xfailed, 231 warnings in 382.78s (0:06:22) =
+rc=1
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/validate-all-pre-20260919T170309.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/validate-all-pre-20260919T170309.txt"
new file mode 100644
index 00000000..f783fc2b
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/validate-all-pre-20260919T170309.txt"
@@ -0,0 +1,4 @@
+✅ PASS docs/release-evidence/example-backfill-d5/journeys/J08/manifest.json
+
+合计 1 份 manifest, 失败 0 份。
+rc=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/validate-export-e2-20260919T202340.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/validate-export-e2-20260919T202340.txt"
new file mode 100644
index 00000000..eabfdf7b
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/validate-export-e2-20260919T202340.txt"
@@ -0,0 +1,33 @@
+### (g)① 消费契约门 E2 2026-09-19T20:23:40-0700
+--- 导出（export_shape → 五键；落 $TMP/measurements.json）---
+exported 9 items -> $TMP/measurements.json; slo written into tmp j08
+   review_overview_first_paint_p95_ms meets= True
+   rag_query_warm_p95_ms meets= True
+   rag_query_cold_p95_ms meets= False
+   kg_read_p95_ms meets= True
+   review_rebuild_p95_s meets= True
+   first_index_seconds meets= False
+   graphiti_ack_ms meets= False
+   graphiti_replay_s meets= False
+   recovery_time_s meets= False
+
+--- 对照输入 A：J08 result 保持 partial（卡文原状）---
+❌ FAIL /private/tmp/rslo-p10c/consumer/example-backfill-d5/journeys/J08/manifest.json
+    [S9] slo.measurements[2] (rag_query_cold_p95_ms) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=partial 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+    [S9] slo.measurements[5] (first_index_seconds) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=partial 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+    [S9] slo.measurements[6] (graphiti_ack_ms) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=partial 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+    [S9] slo.measurements[7] (graphiti_replay_s) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=partial 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+    [S9] slo.measurements[8] (recovery_time_s) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=partial 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+
+合计 1 份 manifest, 失败 1 份。
+⚠️  已弃权 artifact checksum 真验 (--skip-artifact-verify)。
+A_rc=1
+
+--- 对照输入 B：按 §12.5「未达标只能判失败」把 result 改 fail 后 ---
+result -> fail
+✅ PASS /private/tmp/rslo-p10c/consumer/example-backfill-d5/journeys/J08/manifest.json
+
+合计 1 份 manifest, 失败 0 份。
+⚠️  已弃权 artifact checksum 真验 (--skip-artifact-verify)。
+B_rc=0
+grep_S_count=0
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/validate-export-e3-20260919T202346.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/validate-export-e3-20260919T202346.txt"
new file mode 100644
index 00000000..20bebdfa
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/validate-export-e3-20260919T202346.txt"
@@ -0,0 +1,25 @@
+### (g) E3 对照输入 2026-09-19T20:23:46-0700
+--- A：按卡文清单改造（evidence_level=E3 / mode=live / unproven=[] / dirty=false / result=pass / declared=false）---
+E3-literal patched
+❌ FAIL /private/tmp/rslo-p10c/consumer/example-backfill-d5/journeys/J08/manifest.json
+    [schema] provenance: {'mode': 'live', 'reconstructed_from': '_bmad-output/审查/d5-evidence-2026-08-27/ (D5-结案报告.md + before.txt + after-check.txt, 归档于 commit c823a35fa9cd91fae29b409ba7e000834b09f726) + 主仓 .git/worktrees/feature-obsidian-hybrid-dev/logs/HEAD 第 251-252 行 (执行期 HEAD 的直接证据) + 上述三份归档文件在 worktree .claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/d5-evidence-2026-08-27/ 下的 birth time (本仓 checkout 的副本 mtime 已是 checkout 时刻, 不可用)', 'unproven_fields': [], 'note': '本 manifest 是 CARD-R-EVD 的格式演示件, 由既有 D5 归档事后回填。语义规则 S10/S13/S17 因此把它锁在 E2、禁止签字、不计入 RC 门。真正的 RC 证据必须在执行期实录 (provenance.mode=live, unproven_fields 为空, dirty=false)。本文件经一轮红队 example-fidelity 审计逐条核对归档与 git 事实后重写, 修正了 11 处 overclaim (详见 known_limitations 与 _bmad-output/审查/revd-redteam-2026-08-28.md)。'} should not be valid under {'required': ['reconstructed_from']}
+
+合计 1 份 manifest, 失败 1 份。
+⚠️  已弃权 artifact checksum 真验 (--skip-artifact-verify)。
+A_rc=1
+
+--- B：清理 live 化残留（去 reconstructed_from + skips_or_mocks.items 置空）---
+E3-clean patched
+❌ FAIL /private/tmp/rslo-p10c/consumer/example-backfill-d5/journeys/J08/manifest.json
+    [S3] result=pass 与断言实况矛盾 — 非 pass 断言: D5-6
+    [S9] slo.measurements[2] (rag_query_cold_p95_ms) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=pass 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+    [S9] slo.measurements[5] (first_index_seconds) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=pass 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+    [S9] slo.measurements[6] (graphiti_ack_ms) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=pass 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+    [S9] slo.measurements[7] (graphiti_replay_s) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=pass 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+    [S9] slo.measurements[8] (recovery_time_s) 未达标 (阈值 (未定) vs 实测 not_measured), 而整体 result=pass 且无用户 waiver — §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制。
+
+合计 1 份 manifest, 失败 1 份。
+⚠️  已弃权 artifact checksum 真验 (--skip-artifact-verify)。
+B_rc=1
+grep_S9_count=5
+grep_S_other=1
diff --git "a/_bmad-output/\345\256\241\346\237\245/evidence-rslo/yaml-check-20260919T202309.txt" "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/yaml-check-20260919T202309.txt"
new file mode 100644
index 00000000..13cb5b89
--- /dev/null
+++ "b/_bmad-output/\345\256\241\346\237\245/evidence-rslo/yaml-check-20260919T202309.txt"
@@ -0,0 +1,11 @@
+### (f)④ yaml 自检 2026-09-19T20:23:09-0700
+--- 主判据 ---
+yaml_ok metrics=9 measured=4 not_measured=5 status=draft
+main_rc=0
+
+--- 验伪锚: $TMP 副本删掉一条 reason ---
+removed reason from rag_query_cold
+    assert ms.get("reason"), m["id"]
+           ~~~~~~^^^^^^^^^^
+AssertionError: rag_query_cold
+anchor_rc=1
diff --git "a/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-R-SLO-2026-09-19.md" "b/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-R-SLO-2026-09-19.md"
new file mode 100644
index 00000000..3b27a4b7
--- /dev/null
+++ "b/_bmad-output/\351\252\214\346\224\266\345\215\225/UAT-CARD-R-SLO-2026-09-19.md"
@@ -0,0 +1,266 @@
+# UAT · CARD-R-SLO — SLO manifest 起草 + README 反向引用 + 现网只读实测
+
+> **批次**：`[BATCH-2026-09-18-第十五批 / CARD-R-SLO]` · 车道 `card-p10-docs`（分支 `card/p10-docs`），本车道第 **3/3** 张（末张）
+> **`<PREV>`**（P10-B CARD-R-RC 末 commit）：`a03f0ce3`（`a03f0ce34de9a9c4652310d45eae283f78d11451`）
+> **最终代码 SHA**：`a03f0ce34de9a9c4652310d45eae283f78d11451`（本卡零代码：commit A/B 只改 `docs/release-evidence/` 与 `_bmad-output/`；代码面 SHA 恒等于 P10-B 末 commit）
+> **commit 数**：5（A = yaml + README + 本验收单 + evidence-rslo；A2 = 首轮整改；A3 = 次轮整改；A4 = 三轮整改（负控 3 输入侧证据 + 指针/澄清）；B = 负控 + Codex 存档 + 收工裁判；若用户当次锁版另有 C）
+> **Codex 轮次**：r1（绑 A）：0B/4H/1M/1L ⇒ 整改（A2）；r2（绑 A2）：0B/1H/1M/1L ⇒ 整改（A3）；r3（绑 A3）：0B/1H/1M/1L ⇒ 整改（A4）；r4（绑 A4）：见 §6 存档（绑定核在 B 后）。
+> **签字**：⛔「R-SLO 授权锁版」未发生 ⇒ `status: draft` + SKIP 登记（§12）
+
+---
+
+## 0 一句话
+
+整批 J manifest 卡在 E2 的那块拼图落成单文件 `docs/release-evidence/slo-manifest.yaml`：9 项指标、每项可复跑命令、**4 项现网只读实测**（首屏 / RAG warm / kg 读 / 复习重建）、1 项因样本含超时如实 `not_measured`（cold）、4 项写侧只读不可测项如实 `not_measured` + 指定 owner 卡；README 补 `slo.manifest_revision` 反向引用段与锁版规则，并加一条「S9 不查 draft/locked」的已知边界。阈值全部是 `candidate`（draft），等用户口令锁版。
+
+---
+
+## 1 第 0 分钟（完成条件 a）
+
+| 项 | 期望 | 实测 |
+|---|---|---|
+| `pwd` / 分支 | `…/worktrees/card-p10-docs` / `card/p10-docs` | ✅ 同 |
+| `HEAD` | P10-B 末 commit（message 含 `CARD-R-RC`） | ✅ `a03f0ce3` / `grep -c CARD-R-RC` = 1 |
+| `git status --porcelain` | 空 | ✅ 0 行 |
+| `merge-base --is-ancestor 9c4e7e82 HEAD` | rc=0 | ✅ 0；`a03f0ce3` 亦为 HEAD（`a03f0ce3..HEAD -- . ':(exclude)_bmad-output'` = 0 行） |
+| 基线 `grep -vc '^#' "$BASE"` | **33** | `33`（跑法头第 3 行逐字同） |
+| venv pytest / `.env` / pyright `test -x` / `import yaml` | 在场 / 6.x | ✅ 全部；`yaml 6.0.3`（失败即停的条款未触发） |
+| `docker ps` 只读存档 | —— | ✅ 三容器 healthy；**8011 在跑** ⇒ 现网只读实测执行（非 not_measured 整段） |
+
+**手册地盘核**（`grep -nF -e 'CARD-R-SLO' -e 'card-p10-docs' <手册>` 命中 P10 行，抄原文）：
+- 手册 `:38`：`| **P10 release-evidence** | `card-p10-docs（NEW @ B15_BASE（= 主干 ff 后 SHA，草案时点 9c4e7e82））` | G1-3（总账，8h） → R-RC（总账，5h） → R-SLO（总账，6h） | 19 |`
+- 手册 `:897`：`### P10-C（CARD-R-SLO）`；`:903`：「车道：…card-p10-docs…本车道第 3/3 张…前提：P10-B 已独立 commit 且工作树干净。」
+- ⛔ 未改手册（零写者）。
+
+### §〇 file:line 核对（README 经 P10-A/P10-B 已漂，按标题文本重定位）
+
+| 卡文引用 | 实测 | 说明 |
+|---|---|---|
+| schema `:475/:476/:485`；validator `:76/:430-439/:442-475/:323-326`；`SCHEMA_SHA256` `:63` | **未漂** | 逐条 `sed -n` 核过，内容与卡文一致；指纹 `4456e1ad…c547` 逐字同 |
+| 校验器测试 `:120/:668` 的 `slo-manifest@2026-08-28-r1` 形态；`def test_` = 147 | **未漂** | 供 revision 命名形态与计数口径 |
+| J08 示例件 `:177-180` `manifest_revision: null` | **未漂** | 本卡零改动 |
+| 8011 端点行号（health `:59-60/:423-424/:945/:947/:953-954/:1081-1082`；rag `:46/:49/:265-266/:277/:503-504/:565/:595`；review `:1185-1186/:1741-1742/:3064`；index `:81/:123`；router `:69/:151-152/:238/:467`） | **未漂** | `require_internal_api_key` 计数：health 0 / rag 0 / index 0 / review 1（docstring） |
+| README 卡文 `:59` / `:75` / `:94` / `:152` / `:164` / `:166` | 实测 `:151` / `:167` / `:186` / `:244` / `:256` / `:258` | P10-A/P10-B 插入段落后整体下移（`## 字段速查` 现 `:173`；`## 语义与产物规则` 现 `:192`） |
+| README `:34-36` 示例件说明 | 实测 `:36-38` | 同上 |
+
+---
+
+## 2 先红（完成条件 b；存档 `pre-20260919T170257.txt` / `pre-consumer-20260919T171717.txt`）
+
+| # | 判据 | 期望 | 实测 |
+|---|---|---|---|
+| ① | `git grep -n 'slo-manifest' -- docs backend/scripts scripts \| wc -l` | 0（验伪锚 `-- backend/tests` = 2） | `0` / 锚 `2` ✅ |
+| ② | `test -e docs/release-evidence/slo-manifest.yaml; echo rc` | 1 | `rc=1` ✅ |
+| ③ | `grep -c 'slo-manifest.yaml' README` | 0 | `0` ✅ |
+| ④ | `validate_release_manifest.py --all` | rc=0（份数如实） | `rc=0`，**1 份**（J08 一份；P10-B 未建 `<rc>/` 骨架）✅ |
+| ⑤ | 消费契约先红：tmp J08（首条指标五键）+ validator + 对照脚本 | validator 绿 / 对照脚本红 FileNotFoundError | ✅ 见下 |
+
+⑤ 明细（`pre-consumer-20260919T171717.txt`）：tmp J08 的 `slo` 换成 `{manifest_revision: slo-manifest@2026-09-19-r1, measurements:[review_overview_first_paint_p95_ms 五键]}` 后——
+- **validator 绿**（`rc=0`，仅 `⚠️ 已弃权 artifact checksum` 一行）——证明「校验器绿 ≠ revision 存在」；
+- **对照脚本必红**：`FileNotFoundError: docs/release-evidence/slo-manifest.yaml`（rc=1）——本卡新增的 revision↔yaml 对照门是唯一把两者钉在一起的门。
+
+⚠️ 形状修正（卡文 :X → 实测 :Y，详见 §9）：`$TMP/j08.json` 裸文件按校验器 S6 结构门必红，故文件实体放 `$TMP/example-backfill-d5/journeys/J08/manifest.json`（结构合规），`$TMP/j08.json` 以 symlink 指入——`resolve()` 跟 symlink，rev-check 与 validator 均按卡文命令路径执行。
+
+---
+
+## 3 实现 ①：`docs/release-evidence/slo-manifest.yaml`（9 指标）
+
+- `revision: slo-manifest@2026-09-19-r1` · `status: draft` · `decision.locked_by/locked_at: null` · `schema_version: 1.0.0`
+- 固定键齐：`id / metric / unit / description / threshold{locked,candidate,threshold_source} / method{command,repeat,statistic,environment_ref} / measured{status,value,p50,p95,n,at,reason?,evidence} / degrade_rule / owner_consumer`
+- `export_shape` 写死五键映射（metric / threshold（candidate 带 `(candidate)` 标记）/ measured（`p95=…` 或 `not_measured`）/ method / meets；unit 可选）
+- `environment`：Apple M5 Max / 128GiB / macOS 26.5 arm64 / Python 3.14.4 / git 2.50.1 / 模型栈各端自报（ollama unreachable；12341 qwen3.5-35b-a3b-q4_k_s；18012 bge-reranker-v2-m3；health/ai=LLM_AUTH_FAILED 自报）/ data_scale（md=214；index/stats `{}`；kg 0/0/0）/ `data_sha=df036977…` / **`code_sha: null` + 理由**（`evidence-b15/` 无 code_sha 公布，实测三件仅 docker-ps/lanes-created/unit-red-baseline）/ `lane_sha=a03f0ce3…` / 并发 1 / PDT(America/Los_Angeles) / seed=`rag-queries.txt` sha256 `4dd05b33…` / repeats 20·5 / 统计量 `median + quantiles(n=20)[18]` / adjudicator null
+- `not_in_scope`：索引 freshness → G2-10/G4-14；gold-set 七指标 → G4-14
+
+| 指标 | candidate | measured | n | p50 | p95 | 存档 |
+|---|---|---|---|---|---|---|
+| review_overview_first_paint_p95_ms | ≤ 500ms | **measured** | 20 | 9.9ms | 39.1ms | `measure-review_overview_first_paint-20260919T171124.txt` |
+| rag_query_warm_p95_ms | ≤ 5000ms | **measured** | 20 | 1668.7ms | 1866.5ms | `measure-rag_warm-20260919T171144.txt` |
+| rag_query_cold_p95_ms | null（无有效样本） | **not_measured** | —— | —— | —— | `measure-rag_cold-20260919T171226.txt` |
+| kg_read_p95_ms | ≤ 500ms | **measured** | 20 | 3.6ms | 27.1ms | `measure-kg_read-20260919T171134.txt` |
+| review_rebuild_p95_s | ≤ 30s | **measured** | 5 | 0.05s | 0.05s | `measure-review_rebuild-20260919T171556.txt` |
+| first_index_seconds | null | not_measured（G2-10） | —— | —— | —— | —— |
+| graphiti_ack_ms | null | not_measured（G4-14/7692） | —— | —— | —— | —— |
+| graphiti_replay_s | null | not_measured（R-J10） | —— | —— | —— | —— |
+| recovery_time_s | null | not_measured（R-J10） | —— | —— | —— | —— |
+
+实现 ②（实测）要点：
+- 8011 全部 **GET + `/rag/query` 一个 POST 读查询**；**20/20 全 200** 的项：首屏（body=30187B 非空锚）、warm、kg；重建 **5/5 rc=0**。
+- **cold 整项 why-not-measured**（规则内判定，不剔除样本）：20 条互异串的第 4 条 `http_code=000`（curl -m 120 → 120.0037s）；其余 19/20=200（p50≈3.29s、p95≈5.36s 仅作描述）；同串复打一次 1.67s 通过（`probe-cold4-replay-20260919T171547.txt`）⇒ 瞬态挂起。
+- 重建只写 **tmp rsync 副本**；live `outputs/今日复习.json` 前后 shasum 逐字同（`105f563c…` ×2，`live-outputs-before/after.txt`）；仓库树无意外写入（`git status` 唯一未跟踪项 = 本卡自己的 `evidence-rslo/`）。
+- 统计汇总 `measure-stats-summary-20260919T171634.txt`（首跑脚本 glob 失误的就地重写版，文件头已自述）。
+- 实测窗口 **2026-09-19 17:11–17:16 PDT**；门跑于 17:19–20:4x（其间约 3 小时墙钟间隔，系统时钟前后一致、无回拨，如实登记）。
+
+---
+
+## 4 实现 ③：README 反向引用段（`### SLO manifest（CARD-R-SLO）`，插在「字段速查」表后 /「语义与产物规则」前）
+
+含：① 位置；② `slo.manifest_revision` = yaml `revision` 字面（形态 `slo-manifest@<日期>-r<N>`）；③ 锁版规则（draft 只可被 ≤E2 引用；E3+ 需 locked + locked_by 非 null；⚠️ 无机器门）；④ 版本化（改阈值 = 新 r<N+1>、旧标 `superseded_by`）；⑤ 现网只读口径（8011 GET + 7691 白名单只读语句，不经 pytest、不写）；⑥ J08 示例 `null` 是 ≤E2 合法形态。
+「已知边界」段**新增一条**（纯追加）：R-SLO 锁版状态无机器门（S9 只查非 null）。
+README 改动 = **纯新增**（`-` 行数 = 0）。
+> P10-B 未在树内冻结 rc 名（无 `<rc>/` 目录入库，真 rc 由主 session 在候选 SHA 冻结）⇒ 本卡 README 段落不引用具体 rc，沿 README 既有 `<rc>` 约定。
+
+---
+
+## 5 结构判据 (f) / 消费契约门 (g) / 套件 (i)
+
+### (f)（权威组：`yaml-check-20260919T211540.txt` / `rev-check-post-20260919T211540.txt`（A3 轮重跑，r3 复核通过）；过程档 `f12-struct-…171903` / `yaml-check-…202309` / `rev-check-post-…171908`）
+
+| # | 判据 | 结果 |
+|---|---|---|
+| ① | `test -e …/slo-manifest.yaml` | `rc 1 → 0` ✅ |
+| ② | `grep -c 'slo-manifest.yaml' README` | `0 → 2`（≥1）✅ |
+| ③ | revision 对照脚本 | `rev_check=OK slo-manifest@2026-09-19-r1 9`（rc=0）；**验伪锚**：tmp revision 改 `…1999-01-01-r9` → 红在 `('revision 不在 yaml', …)`（rc=1）；还原后 rc=0 ✅ |
+| ④ | yaml 自检 | `yaml_ok metrics=9 measured=4 not_measured=5 status=draft`；**验伪锚**：删一条 `reason` 再跑 → 红（`AssertionError: rag_query_cold`）✅ |
+| ⑤ | schema 指纹 | `shasum` 与校验器 `SCHEMA_SHA256` 两值逐字同 `4456e1ad…c547` ✅ |
+
+### (g) ① 消费契约门（存档 `validate-export-e2-20260919T202340.txt` / `validate-export-e3-20260919T202346.txt`）
+
+- **E2·对照输入 A（J08 原状 result=partial）**：全量 9 项五键导出 → `[S9]×5`（cold + 4 写侧，`meets=false` 且无 waiver）rc=1 —— 即「携带 not_measured 项的 manifest 在 partial 下被 S9 拦」。
+- **E2·对照输入 B（§12.5 合法出口：result=fail）**：`rc=0`、`grep -c '[S'` = **0** —— 五键导出形态与 schema `additionalProperties:false` 相容、`measured: "not_measured"` 过 minLength（本轮达成卡文期望的 rc=0 零 `[S`；达成条件与卡文差异见 §9）。
+- **E3 变体·字面清单**（evidence_level=E3 / mode=live / unproven=[] / dirty=false / result=pass / declared=false）：撞 **schema 级**拒绝（`provenance` 残留 `reconstructed_from`，`mode=live` 不允许）——字面清单不足以完成 live 化。
+- **E3 变体·清理版**（另去 `reconstructed_from` + `skips_or_mocks.items` 置空）：`[S9]×5`，**全部**为「未达标（实测 not_measured）且无用户 waiver」相关；另 `[S3]×1` 为 J08 自身 D5-6 断言 `not_run` 的既有属性（与导出无关）→「E3 需 waiver 或全测」实证达成。
+
+### (i) 套件
+
+| 项 | 期望 | 实测 | 存档 |
+|---|---|---|---|
+| `tests/unit/test_validate_release_manifest.py` 显式路径 | 「147」 | **168 passed**（147 = `def test_` 计数口径；pytest 实收集含参数化）rc=0 | `named-validate-alone-20260919T202507.txt` |
+| + P10-B `test_freeze_release_candidate.py` 一并 | 0 failed | **208 passed**（168+40）rc=0，开工/收工各一次 | `named-open-20260919T202409.txt` / `named-close-20260919T203835.txt` |
+| `tests/unit` 目录级开工 | 差集只允许 `<` | 32 failed（基线 33），diff 仅 `<` 1 条（已知 flaky `…_422`） | `unit-open-20260919T170315.txt` / `open.nodeids` |
+| `tests/unit` 目录级收工 | 同上 | 32 failed（5771 passed），diff 仅 `<` 1 条（同 flaky） | `unit-close-full-20260919T203241.txt` / `close.nodeids` / `unit-close-diff-20260919T203835.txt` |
+
+> 注：`unit-close-20260919T202638.txt` 为同数据的 tail-6 摘要版（首个 tee 写法只截了尾部），规范归档以 `unit-close-full-*` 为准。
+> 注（权威组）：A3 轮重跑起为本表权威证据——`validate-export-e2/e3-20260919T211540.txt`、`named-close3-20260919T212159.txt`、`unit-close3-full-20260919T211555.txt` + `unit-close3-diff-20260919T212159.txt`；A4 轮（负控 3 输入侧证据）重跑组见 §6 指针。早期组仅作过程对照。
+
+### (j) openapi / pyright
+
+本卡不改端点（commit 不含 `backend/openapi.json`）；不改 `backend/app` ⇒ pyright 不适用（第 0 分钟环境自证通过即可）。
+
+---
+
+## 6 负控（k）与 Codex（n）—— 按卡片顺序在 **commit A 之后**执行，存档随 commit B 入库
+
+- **负控两段**（提交后对已跟踪文件做；`git show HEAD:<path>` 还原 + 前后 `shasum` 逐字同）：
+  - 段 1：yaml `revision` 末位 `r1→r7` → 重跑对照脚本 → 须红在 `('revision 不在 yaml', …)`；
+  - 段 2：`export_shape` 临时多导出一键（`note`）→ 重跑 E2 导出 + 校验器 → 须 rc=1 且含 `note`（schema 拒收），非 `[load]`/rc=2。
+  - 段 3（补充；回应 r1 H3 / r2 H-R2-1）：**未被拦下的输入**配对演示——固定 `result=partial`，同一导出只 A/B `meets`：`meets=false` 5 项 ⇒ `[S9]×5`；`meets=true` 5 项 ⇒ 0 条 `[S9]`（S9 放行路径，缺口归因于 meets 单变量）。首版（把 result 一并改 fail）不具区分度，已被 r2 判定并重做；两版存档并存。
+  - 存档（权威组）：`negctl-1/2/3-20260919T211541.txt`（配对版；绑定 A3）+ A4 轮重跑组（负控 3 含输入侧证据）；每组含还原后 `git status --porcelain -- docs/release-evidence` 输出，回应 L1。首版 `negctl-3-20260919T205702.txt` 仅作历史对照——r2 已判定其设计不具区分度，**不作承重证据**。
+- **Codex r2**：`glm-5.3` / `max`，审 SHA = A2（整改后树）；绑定核 `git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空（B 只动 `_bmad-output`）。
+  - 存档：`codex-review-CARD-R-SLO-r2.md`（+ prompt `prompts/codex-prompt-CARD-R-SLO-r2.md`），随 commit B 入库。
+- **地盘门 (l)** 亦于 commit A 后跑：`$PREV..HEAD -- . ':(exclude)_bmad-output'` 只列 `docs/release-evidence/slo-manifest.yaml`（新）+ `README.md`；README `-` 行数 = 0；`*.py`/schema/openapi/ledger 命中 0；验伪锚去掉 exclude 多出 `_bmad-output/`。存档 `landgate-*.txt`（随 B）。
+
+---
+
+## 7 脱敏与只读门 (m)（权威组：`desens-final-20260919T211549.txt`（A3 轮）；过程档 `desens-final-20260919T202600.txt`；`neo4j-ro-20260919T202618.txt`）
+
+| 判据 | 实测 |
+|---|---|
+| yaml 内用户主目录绝对路径（形如斜杠 U-s-e-r-s 的机器路径） | `0` ✅ |
+| `fsrs_bridge` / `decay_beta` 引用 | `0` ✅ |
+| 内部 API key 值泄漏（卡文口径 `INTERNAL_API_KEY`） | **实测该变量不在 `backend/.env`（0 行）⇒ 不适用**；补充：`NEO4J_PASSWORD` 值命中 0、`GOOGLE_API_KEY` 值命中 0 ✅ |
+| 敏感字段名字面（NEO4J 密码字段+等号） | `0`（首版脱敏档自指污染已就地重写，见 §9）✅ |
+| live outputs before/after | 逐字同 `105f563c…` ✅ |
+| `measure-*.txt` 内写端点字样 | `0`（写端点一个未打）✅ |
+| 7691 触达 | 全部经 8011 只读 GET；白名单直连语句**未使用**（存档贴语句原文与 `READ_ACCESS` 形态）；7687 未触达 / 7692 未用 ✅ |
+
+---
+
+## 8 执行侧收尾（o）
+
+- commit A：`docs(r-slo): SLO manifest 起草 + README 反向引用 + 现网只读实测 [BATCH-2026-09-18-第十五批 / CARD-R-SLO]`（yaml + README + 本验收单 + `evidence-rslo/**` 逐文件 `git add`，⛔ 非整目录）。
+- commit B：`docs(r-slo): 负控 + Codex 存档 …`（negctl 存档 + Codex 存档/prompt + landgate + 上述收尾裁判存档）。
+- `*.stderr*` 不入库（本卡 evidence 内实测 0 个）；0 字节文件不入库（实测 0 个）；不 push；末 commit 后工作树干净即收工（本卡全部产物随 A/B 入库，见 §6）。
+
+---
+
+## 9 卡文 :X → 实测 :Y 偏差表（须主 session 知悉）
+
+| # | 卡文 | 实测/处置 |
+|---|---|---|
+| 1 | README 行号 `:59/:75/:94/:152/:164/:166` | 实测 `:151/:167/:186/:244/:256/:258`（P10-A/B 插入所漂），按标题重定位，本单 §1 已列 |
+| 2 | §二.5 `$TMP/j08.json` 裸路径 | 校验器 **S6** 要求 `<rc>/journeys/<Jxx>/` 结构 ⇒ 实体放结构合规路径、`j08.json` symlink 指入（两条路径同一文件，已披露） |
+| 3 | §一(b)⑤ / §二.6 (g)① 预期「rc=0 零 `[S`」 | 全量导出保持 `partial` 时实测 `[S9]×5` rc=1（机器行为：`meets=false` 在任意等级触发 S9 链）；rc=0 零 `[S` 经 §12.5 合法出口 **result=fail** 达成（对照输入 A/B 两跑都落档）。E3 字面清单另撞 schema（`reconstructed_from` 残留），清理版得 `[S9]×5`（全部为 meets=false/无 waiver 相关） |
+| 4 | §一(g)③/§二.7「收集 147」 | 147 = `def test_` 计数；pytest 实收集 **168**（含参数化）；合并 freeze 文件共 **208 passed** |
+| 5 | §一(d)③ 查询串源 `节点/ head -20` | 该目录实测仅 **14** 文件 ⇒ 扩至 `节点×14 + 原白板×6 = 20` 条互异串（仍为 live vault 文件名只读；seed sha 见 yaml） |
+| 6 | §一(d)③ cold 预期 20/20；§一(g)② 任一非 200 ⇒ not_measured | 实测 19/20=200 + 1×000（120s 超时）⇒ **整项 not_measured**（样本不剔除）；复打 probe 1.67s |
+| 7 | §一(m) K=`INTERNAL_API_KEY` | 该变量实测不在 `backend/.env` ⇒ 子项不适用；以两个真实敏感值做同口径补充（命中皆 0） |
+| 8 | 收尾命令模型 | 手册 §三 P10-C 行仍写 `gpt-6-astra`（旧文）；按卡文 §四 + 协议 §2.4（D-43）执行 = **`glm-5.3` `max` 1 轮** |
+| 9 | —— | 实测窗口 17:11–17:16 与门跑 17:19–20:4x 之间有约 3 小时墙钟间隔（系统时钟一致、无回拨），非证据缺失 |
+| 10 | —— | 两处就地重写均已在文件头自述：`measure-stats-summary-…T171634.txt`（首跑 zsh glob 失误）、`desens-20260919T202508.txt`（首版标签自指污染） |
+
+### 9b 首轮 Codex（r1，绑 commit A）4×HIGH 的整改记录（落地于 commit A2）
+
+| 项 | r1 指摘 | 整改 |
+|---|---|---|
+| H1 | cold 非「20 条首见」（seed 第 1 条已先被 warm 预跑）；命令缺实际用的 `-m 120` | yaml `cache_state` / cold `description` 改为「20 条互异串各一次，实为 19 条首见+1 条已暖」；warm/cold 命令补 `-m 120`（首屏/ kg 各补 `-m 60`/`-m 30`，与实测一致） |
+| H2 | 「现网零写/只读」强于证据面（service 层未审、live 无全量前后 SHA） | README 新段与验收单收窄为「发起命令面 + 已核对锚点（outputs 前后同）」；service 层副作用与全量 SHA 列入未证明（§10） |
+| H3 | `not_measured+meets=true` 是门未覆盖路径；S9 不强制覆盖集；无对应演示 | 新增**负控段 3**（未被拦下的输入，演示 S9 放行）；yaml `export_shape` 补两条纪律说明；README「已知边界」新增一条 |
+| H4 | `(未定)` 三态未写进 `export_shape.mapping` | mapping 的 threshold 行补「两者皆 null ⇒ `(未定)`（占位, minLength=1）」；README 导出 bullet 同步 |
+| M1 | 写侧 `method.command` 是 sketch 而非可直接复跑 | 四项 command 均补 `method sketch：实参/实例由 owner 卡在其环境补全` 注记 |
+| L1 | 负控还原后 status 未落档 | 负控重跑组（绑定 A2）在存档内直接输出 `git status --porcelain -- docs/release-evidence` |
+
+### 9c 次轮 Codex（r2，绑 A2）1×HIGH + 1×MEDIUM + 1×LOW 的整改记录（落地于 commit A3）
+
+| 项 | r2 指摘 | 整改 |
+|---|---|---|
+| H-R2-1 | 负控 3 同时改了 `meets` 与 `result`，rc=0 不能归因于 `meets=true` | 重做为**配对演示**：固定 `result=partial`，仅 A/B `meets`（false ⇒ `[S9]×5`；true ⇒ 0 条 `[S9]`），新档 `negctl-3-*.txt`（新时间戳）；UAT §6 同步改述 |
+| M-R2-1 | cold「其余 19 条首见」过度确定（进程历史命中未证） | `cache_state` 与 cold `description` 改述为「19 条未由本卡 warm 环节预跑+1 条已暖；其余 19 条历史命中未证（只读约束拿不到查询历史）」 |
+| L-R2-1 | yaml 写「E3+ 至少一条实测」与机器语义有差 | `consumption_note` 改为「measurements 非空；『至少一条真实实测』是消费纪律、非机器门」 |
+
+### 9d 三轮 Codex（r3，绑 A3）1×HIGH + 1×MEDIUM + 1×LOW 的整改记录（落地于 commit A4）
+
+| 项 | r3 指摘 | 整改 |
+|---|---|---|
+| H-R3-1 | 配对负控 3 缺输入侧证据（A/B manifest、hash、逐字段 diff、pre-assert 输出） | A4 轮重跑为**输入落档版**：A/B 两份 manifest 写入证据区 + sha256 + 归一化逐字段 diff（应恰好 5 处 `meets` false→true）+ pre-assert 输出全部落档（新档 `negctl-3-*.txt`；`negctl-3-inputs-A/B.json`） |
+| M-R3-1 | UAT 指针仍指 A2 旧组 | 本单 §5/§6/§7 指针改为 A3/A4 权威组；首版 `205702` 明标「历史对照，不作承重」 |
+| L-R3-1 | README 既有行「至少一条实测」句式歧义 | 既有行受「纯新增（`-` 行数=0）」硬约束**不可删改**；在本卡新增 bullet 内加澄清一句 + 台账登记交主 session 批级统一句面 |
+
+---
+
+## 10 本卡未证明什么（≥4）
+
+1. **未证明任何阈值「合理」**——9 项阈值全是 `candidate` 起草值；锁版前没有一项是「生产力标准」，用户可逐项改。
+2. **写侧四项未实测**——首次索引 / Graphiti ACK / replay / 恢复时间只给了在指定环境（G2-10 / 7692 / R-J10）可复跑的命令与 owner 卡，`not_measured`，⛔ 未填估计值。
+3. **RAG「cold」是「进程未重启的首见串」口径**——未证明进程冷启动后的真实首查延迟（现网禁重启）；且本次 cold 因 1 次超时整体 `not_measured`，连该口径的结论也未成立。
+4. **单机 / 单时段 / 并发 1 / n=20（重建 n=5）**——不证明跨机、跨日、并发下的分布；也不证明「8011 当时运转的代码树 = 本车道树」（`code_sha: null`，主 session 未公布）。
+5. **`/rag/query` 的 service 层写点未审、且未做 live vault 全量跑前/跑后 SHA**——端点文件内无写点已核；service 层是否记录查询/学习事件未审（若有，本卡 40 次官方查询 + 2 次探针查询已在现网留痕），移交 G4-14 或 P8 census；「只读」目前只到发起命令面 + outputs 锚点（README 已同步收窄措辞）。
+6. **README 锁版规则没有机器门**——校验器 S9 只查非 null、不查 draft/locked 与 revision 存在性；靠 G1-6 审计链与 R-J0x 人工核。
+7. **重建耗时在 tmp 副本上测得**——未证明等于 live 目录上的耗时（磁盘/缓存位置不同）。
+8. **真实 J 卡消费未端到端证明**——(g) 契约门用 J08 演示件做载体（其 `[S3]`/schema 既有属性已单列）；A/B 两跑的 S9 语义结论对任何消费卡成立，但「某张真 R-J 卡引用本 revision 直到 E3」的全链未发生。
+9. **导出纪律无全量机器门**——`not_measured ⇒ meets=false` 与「9 项全导出」只是纪律：S9 在 `meets=true` 时直接放行、且只要求 ≥1 条测量；负控段 3 已把该未被拦下的输入落档（README 已知边界同登）。
+10. **cold 的唯一一次 120s 超时未定位到根因**——复打通过仅说明当时呈瞬态；其触发条件（并发/负载/特定串）未证明。
+11. **README 既有行（「三步操作」第 2 步）句面残留**——r3 L-R3-1：该句「至少一条实测」易被读成机器门；受本卡「纯新增（`-` 行数=0）」硬约束不可删改，已在本卡新增 bullet 内澄清并登记台账（批级统一句面修订项）。
+
+---
+
+## 11 台账待登记条目（≥4）
+
+1. `docs/release-evidence/slo-manifest.yaml`：`revision=slo-manifest@2026-09-19-r1`、`status=draft`、9 指标（4 measured / 5 not_measured）+ 每项 p95（首屏 39.1ms、warm 1866.5ms、kg 27.1ms、重建 0.05s）——供 G8-8 / G2-10 / G4-14 / G6-11 / R-J0x 引用。
+2. **锁版授权状态**：「R-SLO 授权锁版」**未发生** ⇒ 全批 J manifest 只能引用 draft revision ⇒ **E3 不可达**——批级事实，须写进第十五批复核裁定。
+3. 写侧四项 owner 回填：G2-10（首次索引）/ G4-14（ACK 在 7692）/ R-J10（replay + 恢复时间），并在总账对应卡「做什么」里回填「复用 R-SLO 条目 id」；cold 复测亦归 G4-14。
+4. 清单更正：`manifest.schema.json` 与 J08 示例件**零改动**；「查询 7691 只读」收窄为「经 8011 GET 或白名单两条 `execute_read`（本卡实际未用直连）」。
+5. `/rag/query` service 层写点未审 → 移交 G4-14 或 P8 census（本卡 42 次查询已在现网留痕，如 service 层记账则含本次）。
+6. README 行号漂移实测表（本单 §1）并入台账备注；「S9 不查 draft/locked」的已知边界已写进 README。
+7. Codex 1 轮（glm-5.3 max）存档路径、绑定 SHA（commit A）、B/H/M/L 计数。
+8. 卡文偏差表（本单 §9 共 10 条）需主 session 知悉；测时窗口与门跑之间的 3 小时墙钟间隔一并登记备查。
+9. README「三步操作」第 2 步既有句「至少一条实测」（受「纯新增」约束本卡未改）——批级统一句面修订时与 R-EVD 原文一并处理（r3 L-R3-1）。
+
+---
+
+## 12 锁版签字位（用户节点，手册 `:353` 原文：「【P10 R-SLO】SLO 阈值锁版需用户签字（卡可先开工做采集命令 + 一次现网只读实测；锁版环节等用户）」）
+
+> 口令：**「R-SLO 授权锁版」** + 逐项阈值裁定。
+> 授权后车道将：`threshold.locked` 逐项填实 → `status: locked` → `revision` 升 `r2` → `decision.locked_by/locked_at` 填实（带时区）→ commit C（+ Codex `-r2` 再送一轮绑最终 HEAD）。
+
+- ☐ 我同意以上阈值（可逐项批注修改）：________________________________
+- 签字（用户）：____________________　日期：________________
+- **未授权状态**：登记「**锁版 SKIP：等用户**」（本单随 commit A 入库时即为该状态）。
+
+---
+
+## 13 4-B 用户视角（零技术词）
+
+- 我打开复习总览页 → 一秒内就看到今天要复习什么 → 我感觉它是随时可用的，不是要等它想。
+- 我在白板里问一个概念 → 第二次问同一个问题明显比第一次快 → 我感觉它记住了我刚问过什么。
+- 我看到一张表，上面写着「这些速度要多快才算合格」、每一项旁边有今天量出来的真实数字、还有一个空着的「我签字」位 → 我感觉标准是我定的，不是它自己说自己达标。
+- 有几项写着「今天没量、原因是……、以后在哪儿量」 → 我感觉它没糊弄我。
diff --git a/docs/release-evidence/README.md b/docs/release-evidence/README.md
index c53d3e5b..743e3ba5 100644
--- a/docs/release-evidence/README.md
+++ b/docs/release-evidence/README.md
@@ -189,6 +189,16 @@ CI 侧由 `.github/workflows/release-evidence.yml` 在证据目录/校验器/sch
 | `evidence_level` | E0–E5（§12.5）。文件名含 e2e、CI 绿、fixture 都**不**自动升级 |
 | `result` | 整体判定 pass·fail·partial；任一断言非 pass、或回滚 fail 时不得写 pass |
 
+### SLO manifest（CARD-R-SLO）
+
+阈值本体的唯一真相源是 [`slo-manifest.yaml`](slo-manifest.yaml)（CARD-R-SLO 起草；`revision` 形态 `slo-manifest@<YYYY-MM-DD>-r<N>`）。J manifest 的 `slo.manifest_revision` **逐字**填它的 `revision` 值。⚠️ 校验器只检查该字段非 null（S9），**不核该 revision 是否存在、也不核 draft/locked**——把 revision 与实测对齐是消费卡的义务。
+
+- **锁版规则**：`status: draft` 的 revision 只可被 ≤E2 的 J manifest 引用；E3+ 引用的 revision 必须 `status: locked` 且 `decision.locked_by` 非 null。draft→locked 只在用户口令「R-SLO 授权锁版」+ 逐项阈值裁定后发生（`threshold.locked` 填实、revision 升 `r<N+1>`、`decision.locked_at` 带时区）。这条**没有机器门**，见「已知边界」。
+- **版本化**：改阈值 = 新 `r<N+1>`；旧 revision 不删，只标 `superseded_by` 指向新值。
+- **现网只读口径**（本文件实测沿此）：8011 只打 GET + `/rag/query` 一个读查询；7691 只经 8011 GET 或白名单两条只读语句（`RETURN 1` / `MATCH (n) RETURN count(n) AS c`，`driver.session(default_access_mode=READ_ACCESS)`；不经 pytest、不写）。写侧指标（首次索引 / Graphiti ACK / replay / 恢复时间）在只读约束下不可测，如实 `not_measured` + 指定 owner 卡与可复跑命令，⛔ 不填估计值。⚠️ 此「只读」= **发起命令面（GET/读查询）+ 已核对锚点（live outputs 前后逐字同）**的只读；**不证明 service 层零副作用**（记账/日志等未审）——需要更强保证的消费卡应做跑前/跑后全量 data SHA。
+- **导出**：本文件的 `export_shape` 写死到 J manifest `slo.measurements[]` 的五键映射（`metric` / `threshold`（locked 原样；candidate 带 `(candidate)` 标记；两者皆空导出 `(未定)` 占位）/ `measured`（`p95=<…>` 或字符串 `not_measured`）/ `method` / `meets`；可选 `unit`）。schema 的 `additionalProperties:false` 只认这五键 + `unit`/`waiver`。
+- **J08 示例件**的 `"manifest_revision": null` 是 ≤E2 的合法形态（reconstructed 演示件，S10/S13 已把它锁在 E2），不是「欠一个 revision」。
+
 ## 语义与产物规则（校验器实施，schema 表达不了的部分）
 
 | ID | 规则 | 依据 |
@@ -257,3 +267,5 @@ CI 侧由 `.github/workflows/release-evidence.yml` 在证据目录/校验器/sch
 - **skip/mock 的命令扫描是启发式**：S16 只按已知开关模式（`*_MOCK=1` / `SKIP_*=1` / `--ignore=` / `-m "not ..."` 等）在 E3+ 上报警，换个措辞就能躲开。它拦的是"命令里明摆着写了 mock 却声明零 mock"这种自相矛盾，不是所有 mock。
 - SLO 的 `threshold` / `measured` 是自由文本（如 `"≤ 2.5s"` / `"1.8s"`），校验器**不做数值比较**，`meets` 由填写者判定。机械门只保证"阈值、实测、达标结论、采集方法四者都在场，且未达标时不能悄悄判 pass"。数值口径的正确性归 R-SLO 与审计链。
 - `jsonschema` 目前不在 `backend/requirements.txt` 里（现为传递依赖，venv 内实测 4.26.0）。校验器缺它时**退出 2 报错，不降级放行**；CI workflow 显式安装。**交接项**：requirements.txt 该显式声明它——本卡开跑期间 CARD-DEBT-9 正在重建 venv 并独占该文件族，故不代改。
+- **R-SLO 锁版状态没有机器门**（CARD-R-SLO 实测，非红队清单）：校验器 S9 只查 `slo.manifest_revision` 非 null——**不查**它指向的 `slo-manifest.yaml` 是否存在、不查 revision 与 yaml `revision` 是否一致、也不查 yaml 的 `status: draft` 被 E3+ 引用。draft/locked 的引用规则（见「字段速查」后小节）由 G1-6 审计链与 R-J0x 人工核；`slo-manifest.yaml` 自身 `status`/`decision` 字段是唯一可核面。
+- **SLO 导出纪律没有全量机器门**（CARD-R-SLO 实测，非红队清单）：`not_measured ⇒ meets 必须 false` 与「导出应含全部指标」都是**消费纪律**——校验器 S9 在 `meets=true` 时直接放行（不回头检查 `measured="not_measured"`），且只要求 `measurements` ≥1 条、不检查覆盖集。未被拦下的输入演示见 `_bmad-output/审查/evidence-rslo/negctl-3-*.txt`（该存档随本卡 commit B 入库）。本页上方「三步操作」第 2 步既有句「至少一条实测」同旨（机器只查非空）；该句为既有行、本卡受「纯新增」约束不改动——歧义以本处与 `slo-manifest.yaml` 的 `consumption_note` 为准。
diff --git a/docs/release-evidence/slo-manifest.yaml b/docs/release-evidence/slo-manifest.yaml
new file mode 100644
index 00000000..98b6264a
--- /dev/null
+++ b/docs/release-evidence/slo-manifest.yaml
@@ -0,0 +1,269 @@
+# SLO manifest — versioned benchmark/SLO 的唯一定义 owner（CARD-R-SLO）
+# 上游: 计划书 §12.5 L592（E3 前锁定用户批准的 SLO，不得事后降门槛；J manifest 必须记录阈值与实测）
+#       + 总账 v2 :405-410（schema 字段唯一定义 owner = CARD-R-SLO；G8-8/G2-10/G4-14/G6-11 一律复用）
+# 消费: J manifest 的 slo.manifest_revision 逐字引用本文件 revision；五键导出映射见 export_shape。
+# 本版 status=draft（等用户「R-SLO 授权锁版」口令 + 逐项阈值裁定后才可改 locked 或升 r2）。
+revision: "slo-manifest@2026-09-19-r1"
+status: "draft"
+schema_version: "1.0.0"
+source:
+  - "计划书 §12.5 L592（阈值、参考环境、数据规模和降级规则写入 versioned benchmark/SLO manifest；J manifest 必须记录阈值与实测）"
+  - "总账 v2 :405-410 owner 裁定（本卡是 schema 字段的唯一定义 owner；G8-8/G2-10/G4-14/G6-11 复用不另造格式）"
+decision:
+  locked_by: null
+  locked_at: null
+  note: "锁版流程：用户在本车道说「R-SLO 授权锁版」并逐项裁定阈值 → threshold.locked 填实 / status 改 locked / revision 升 r<N+1> / locked_by、locked_at 填实（带时区）。未授权前一律 draft —— 本版本即 draft。"
+environment:
+  machine: "Apple M5 Max（sysctl -n machdep.cpu.brand_string；memsize=137438953472 bytes）"
+  os: "macOS 26.5（sw_vers -productVersion；arch=arm64）"
+  runtimes:
+    python: "3.14.4（backend/.venv/bin/python --version）"
+    git: "2.50.1 (Apple Git-155)"
+  models:
+    - "ollama：unreachable（OLLAMA_HOST 默认 http://localhost:11434/api/tags → HTTP 000；开工实测）"
+    - "GET /api/v1/health/ai 自报：model=gemini-3.1-flash-lite-preview provider=google status=error error_code=LLM_AUTH_FAILED（AI client not configured）"
+    - "local llama-server：http://127.0.0.1:12341/v1/models → name=qwen3.5-35b-a3b-q4_k_s digest=（空串自报）Q4_K - Small n_params=35505251456"
+    - "local reranker：http://127.0.0.1:18012/v1/models → name=bge-reranker-v2-m3 digest=（空串自报）Q8_0 n_params=567753729"
+    - "GET /api/v1/health/lancedb 自报：embedding_model=text-embedding-3-small table_count=4 total_vectors=53"
+  data_scale:
+    live_vault_md_files: 214
+    index_stats: {}
+    kg: {node_count: 0, edge_count: 0, episode_count: 0, last_episode_timestamp: null}
+  data_sha: "df036977f3d220b10d6be95c16cd83b1ff5241d066884e4b09e9060397551907（find <live> -name '*.md' -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256）"
+  code_sha: null
+  code_sha_null_reason: "主 session 未在 evidence-b15/ 公布 8011 进程代码树 SHA（该目录实测仅 docker-ps / lanes-created / unit-red-baseline 三件，无 code_sha 记录）；8011 运转的代码树与本车道树的对应关系未证明。"
+  lane_sha: "a03f0ce34de9a9c4652310d45eae283f78d11451（本车道树 HEAD = P10-B CARD-R-RC 末 commit；入库后为 P10-C 卡片自身 commit）"
+  cache_state: "warm=seed 第 1 条同串重复 20 次；cold=seed 全 20 条互异串各一次（其中第 1 条已被 warm 预跑 20 次 ⇒ 19 条未由本卡 warm 环节预跑+1 条已暖；其余 19 条在进程历史中是否曾被命中未证——只读约束下拿不到查询历史）；均为进程未重启口径；真冷启=重启后首查，不在本卡只读范围"
+  concurrency: 1
+  timezone: "PDT (America/Los_Angeles)"
+  seed: "rag-queries.txt sha256=4dd05b33342dfdcad3ddaa4de89834592fa45631b451b404b2f26676c91e2afa（evidence-rslo/rag-queries.txt；20 条互异串=live 节点×14 + 原白板×6 文件名）"
+  repeats: {http_metrics: 20, review_rebuild: 5}
+  statistic: "p50 = statistics.median(xs)；p95 = statistics.quantiles(xs, n=20)[18]（Python 3.14 statistics；review_rebuild 项 n=5 用同一公式）"
+  adjudicator: null
+metrics:
+  - id: review_overview_first_paint
+    metric: "review_overview_first_paint_p95_ms"
+    unit: "ms"
+    description: "GET /api/v1/review/overview/page 服务端首屏整页返回耗时（内联 HTML；body=30187B 非空锚）"
+    threshold:
+      locked: null
+      candidate: "p95 ≤ 500ms"
+      threshold_source: "实测 p95=39.1ms × ≈12.8 余量（本地服务端渲染页；本卡起草，待用户锁版）"
+    method:
+      command: 'B=http://127.0.0.1:8011/api/v1; for i in $(seq 20); do curl -s -o /dev/null -m 60 -w "%{http_code} %{time_total} %{size_download}\n" "$B/review/overview/page"; sleep 0.2; done'
+      repeat: 20
+      statistic: "p95 = quantiles(n=20)[18]"
+      environment_ref: "environment（本机参考环境；8011 现网只读）"
+    measured:
+      status: "measured"
+      value: "p95=39.1ms p50=9.9ms（n=20；http 20/20=200）"
+      p50: 9.9
+      p95: 39.1
+      n: 20
+      at: "2026-09-19T17:11:24-07:00"
+      evidence: "measure-review_overview_first_paint-20260919T171124.txt"
+    degrade_rule: "未达标只能判失败，或经用户事前/书面 waiver 降级为限制（README 字段速查 slo 行；§12.5 L592）。candidate 锁版前不构成发布判据。"
+    owner_consumer: "G6-11（复习链性能面在其环境正式测）；R-J0x 消费本 revision"
+  - id: rag_query_warm
+    metric: "rag_query_warm_p95_ms"
+    unit: "ms"
+    description: "POST /api/v1/rag/query 同一查询串重复 20 次的端到端耗时（warm=同串重复口径）"
+    threshold:
+      locked: null
+      candidate: "p95 ≤ 5000ms"
+      threshold_source: "实测 p95=1866.5ms × ≈2.7 余量（RAG 检索含 rerank；本卡起草，待用户锁版）"
+    method:
+      command: 'B=http://127.0.0.1:8011/api/v1; Q=$(head -1 "$EV/rag-queries.txt"); VID=<live vault_id>; for i in $(seq 20); do curl -s -o /dev/null -m 120 -w "%{http_code} %{time_total} %{size_download}\n" -H "Content-Type: application/json" -X POST "$B/rag/query" -d "{\"query\":\"$Q\",\"vault_id\":\"$VID\"}"; sleep 0.2; done'
+      repeat: 20
+      statistic: "p95 = quantiles(n=20)[18]"
+      environment_ref: "environment（本机参考环境；8011 现网只读）"
+    measured:
+      status: "measured"
+      value: "p95=1866.5ms p50=1668.7ms（n=20；http 20/20=200）"
+      p50: 1668.7
+      p95: 1866.5
+      n: 20
+      at: "2026-09-19T17:11:44-07:00"
+      evidence: "measure-rag_warm-20260919T171144.txt"
+    degrade_rule: "未达标只能判失败，或经用户事前/书面 waiver 降级为限制（README 字段速查 slo 行；§12.5 L592）。candidate 锁版前不构成发布判据。"
+    owner_consumer: "G4-14（gold-set 指标在其指定环境正式测）；R-J0x 消费本 revision"
+  - id: rag_query_cold
+    metric: "rag_query_cold_p95_ms"
+    unit: "ms"
+    description: "POST /api/v1/rag/query 的 20 条互异串各一次端到端耗时（其中第 1 条与 warm 同串、已被本卡 warm 环节预跑 20 次；其余 19 条的历史命中未证；进程未重启口径；真冷启=重启后首查，不在本卡范围）"
+    threshold:
+      locked: null
+      candidate: null
+      threshold_source: "本次运行无有效 cold 样本（见 measured.reason）⇒ 无数据依据；待复测后按 p95×余量起草，或由 G4-14 建议值。"
+    method:
+      command: 'B=http://127.0.0.1:8011/api/v1; VID=<live vault_id>; while read -r Q; do curl -s -o /dev/null -m 120 -w "%{http_code} %{time_total} %{size_download}\n" -H "Content-Type: application/json" -X POST "$B/rag/query" -d "{\"query\":\"$Q\",\"vault_id\":\"$VID\"}"; sleep 0.2; done < "$EV/rag-queries.txt"'
+      repeat: 20
+      statistic: "p95 = quantiles(n=20)[18]"
+      environment_ref: "environment（本机参考环境；8011 现网只读）"
+    measured:
+      status: "not_measured"
+      value: null
+      p50: null
+      p95: null
+      n: null
+      at: "2026-09-19T17:12:26-07:00"
+      reason: "20 条互异串各一次的第 4 条 120s 超时（curl -m 120 → http_code=000、120.0037s；样本不剔除）；其余 19/20=200（p50≈3.29s、p95≈5.36s，仅作描述不给结论）；同串复打一次 1.67s 通过（probe-cold4-replay-20260919T171547.txt）⇒ 瞬态挂起。按规则（任一非 200 ⇒ 整项 not_measured）整项 not_measured。"
+      evidence: "measure-rag_cold-20260919T171226.txt"
+    degrade_rule: "未达标只能判失败，或经用户事前/书面 waiver 降级为限制（README 字段速查 slo 行；§12.5 L592）。candidate 锁版前不构成发布判据。"
+    owner_consumer: "G4-14（gold-set 环境复测并定 candidate）；R-J0x 消费本 revision"
+  - id: kg_read
+    metric: "kg_read_p95_ms"
+    unit: "ms"
+    description: "GET /api/v1/health/knowledge-graph 图统计只读快照耗时（8011 → 7691 只读路径）"
+    threshold:
+      locked: null
+      candidate: "p95 ≤ 500ms"
+      threshold_source: "实测 p95=27.1ms × ≈18 余量（只读统计快照；本卡起草，待用户锁版）"
+    method:
+      command: 'B=http://127.0.0.1:8011/api/v1; for i in $(seq 20); do curl -s -o /dev/null -m 30 -w "%{http_code} %{time_total} %{size_download}\n" "$B/health/knowledge-graph"; sleep 0.2; done'
+      repeat: 20
+      statistic: "p95 = quantiles(n=20)[18]"
+      environment_ref: "environment（本机参考环境；8011→7691 只读）"
+    measured:
+      status: "measured"
+      value: "p95=27.1ms p50=3.6ms（n=20；http 20/20=200）"
+      p50: 3.6
+      p95: 27.1
+      n: 20
+      at: "2026-09-19T17:11:34-07:00"
+      evidence: "measure-kg_read-20260919T171134.txt"
+    degrade_rule: "未达标只能判失败，或经用户事前/书面 waiver 降级为限制（README 字段速查 slo 行；§12.5 L592）。candidate 锁版前不构成发布判据。"
+    owner_consumer: "G6-11（万节点量级复测）；R-J0x 消费本 revision"
+  - id: review_rebuild
+    metric: "review_rebuild_p95_s"
+    unit: "s"
+    description: "scripts/daily_review_pick.py --write 在 live vault 的 tmp rsync 副本上整次重建耗时（写只落副本；live outputs/今日复习.json 前后 shasum 同）"
+    threshold:
+      locked: null
+      candidate: "p95 ≤ 30s"
+      threshold_source: "实测 p95=0.05s × ≈600 余量（先例宽松起草，待用户锁版收紧/放宽）"
+    method:
+      command: 'TMP=<tmp>; rsync -a --exclude ".obsidian/plugins" <live>/ "$TMP/vaults/canvas-vault/"; (cd backend && for i in 1 2 3 4 5; do /usr/bin/time -p .venv/bin/python ../scripts/daily_review_pick.py --vault "$TMP/vaults/canvas-vault" --now "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --write; done)'
+      repeat: 5
+      statistic: "p95 = quantiles(n=20)[18]（n=5 同公式）"
+      environment_ref: "environment（本机参考环境；live 只读 rsync 副本）"
+    measured:
+      status: "measured"
+      value: "p95=0.05s（n=5；runs=0.05/0.05/0.05/0.04/0.04；5/5 rc=0）"
+      p50: 0.05
+      p95: 0.05
+      n: 5
+      at: "2026-09-19T17:15:56-07:00"
+      evidence: "measure-review_rebuild-20260919T171556.txt"
+    degrade_rule: "未达标只能判失败，或经用户事前/书面 waiver 降级为限制（README 字段速查 slo 行；§12.5 L592）。candidate 锁版前不构成发布判据。"
+    owner_consumer: "G6-11（复习链性能面在其环境正式测）；R-J0x 消费本 revision"
+  - id: first_index
+    metric: "first_index_seconds"
+    unit: "s"
+    description: "首次索引（new/adopt 配置与激活时间；计划书 L592 单列）总耗时——本卡现网只读约束下不可测"
+    threshold:
+      locked: null
+      candidate: null
+      threshold_source: "无依据（需先在该环境跑出首测）⇒ null；由 G2-10 首测后起草。"
+    method:
+      command: 'LANCEDB_DATA_PATH=<隔离目录>（独立进程/隔离实例）; B=http://127.0.0.1:<隔离实例端口>/api/v1; curl -s -o /dev/null -w "%{http_code} %{time_total}\n" -X POST "$B/index/refresh-changed" -H "Content-Type: application/json" -d "{}"  # ⛔ 现网 8011 不打写端点；指定环境=G2-10 千笔记 fixture；method sketch：实例启动与实参由 G2-10 补全（本卡现网只读，不可执行）'
+      repeat: 20
+      statistic: "p95 = quantiles(n=20)[18]"
+      environment_ref: "指定环境（隔离 LANCEDB_DATA_PATH + 独立进程；G2-10）"
+    measured:
+      status: "not_measured"
+      value: null
+      p50: null
+      p95: null
+      n: null
+      at: null
+      reason: "需写 LanceDB（LANCEDB_DATA_PATH 隔离 + 独立进程），归 G2-10 千笔记 fixture；本卡现网只读约束下不可测，禁填估计值。"
+      evidence: null
+    degrade_rule: "未达标只能判失败，或经用户事前/书面 waiver 降级为限制（README 字段速查 slo 行；§12.5 L592）。candidate 锁版前不构成发布判据。"
+    owner_consumer: "G2-10（千笔记 fixture 首测并起草 candidate）；R-J0x 消费本 revision"
+  - id: graphiti_ack
+    metric: "graphiti_ack_ms"
+    unit: "ms"
+    description: "写入图记忆的 ACK 往返耗时（POST /api/v1/memory/episodes）——本卡现网只读约束下不可测"
+    threshold:
+      locked: null
+      candidate: null
+      threshold_source: "无依据（需先在 7692 测试环境跑出首测）⇒ null；由 G4-14 首测后起草。"
+    method:
+      command: 'B=http://127.0.0.1:<实例>/api/v1; curl -s -o /dev/null -w "%{http_code} %{time_total}\n" -X POST "$B/memory/episodes" -H "Content-Type: application/json" -d "<episode 请求体见端点契约>"  # ⛔ 现网 7691 写端点不打；指定环境=7692（G4-14）；method sketch：请求体由 G4-14 按端点契约补全'
+      repeat: 20
+      statistic: "p95 = quantiles(n=20)[18]"
+      environment_ref: "指定环境（7692 测试容器；G4-14）"
+    measured:
+      status: "not_measured"
+      value: null
+      p50: null
+      p95: null
+      n: null
+      at: null
+      reason: "需 POST /memory/episodes 写 7691，归 G4-14 在 7692；本卡现网只读约束下不可测，禁填估计值。"
+      evidence: null
+    degrade_rule: "未达标只能判失败，或经用户事前/书面 waiver 降级为限制（README 字段速查 slo 行；§12.5 L592）。candidate 锁版前不构成发布判据。"
+    owner_consumer: "G4-14（在 7692 正式测并起草 candidate）；R-J0x 消费本 revision"
+  - id: graphiti_replay
+    metric: "graphiti_replay_s"
+    unit: "s"
+    description: "死信回放（POST /api/v1/traces/replay-fallbacks，T6-B）单轮耗时——本卡现网只读约束下不可测"
+    threshold:
+      locked: null
+      candidate: null
+      threshold_source: "无依据（恢复演练在 7692 首测后起草）⇒ null；归 R-J10。"
+    method:
+      command: 'B=http://127.0.0.1:<实例>/api/v1; curl -s -o /dev/null -w "%{http_code} %{time_total}\n" -X POST "$B/traces/replay-fallbacks" -H "Content-Type: application/json" -d "{}"  # ⛔ 现网 7691 写端点不打；指定环境=7692（R-J10 恢复演练）；method sketch：实例与实参由 R-J10 补全'
+      repeat: 20
+      statistic: "p95 = quantiles(n=20)[18]"
+      environment_ref: "指定环境（7692；R-J10 恢复演练）"
+    measured:
+      status: "not_measured"
+      value: null
+      p50: null
+      p95: null
+      n: null
+      at: null
+      reason: "需 POST /traces/replay-fallbacks（T6-B）写 7691，归 R-J10 / 恢复演练在 7692；本卡现网只读约束下不可测，禁填估计值。"
+      evidence: null
+    degrade_rule: "未达标只能判失败，或经用户事前/书面 waiver 降级为限制（README 字段速查 slo 行；§12.5 L592）。candidate 锁版前不构成发布判据。"
+    owner_consumer: "R-J10（恢复演练在 7692 正式测并起草 candidate）；R-J0x 消费本 revision"
+  - id: recovery_time
+    metric: "recovery_time_s"
+    unit: "s"
+    description: "backend 重启到 /health 恢复可用的耗时——本卡现网只读约束下不可测（禁起停容器）"
+    threshold:
+      locked: null
+      candidate: null
+      threshold_source: "无依据（恢复演练需授权重启）⇒ null；归 R-J10。"
+    method:
+      command: 'time (docker restart <cls 实例容器>; until curl -sf "http://127.0.0.1:<实例端口>/api/v1/health" >/dev/null; do sleep 0.5; done)  # 指定环境=R-J10 恢复演练（需用户授权重启；本卡零起停）；method sketch：容器名与端口由 R-J10 补全'
+      repeat: 20
+      statistic: "p95 = quantiles(n=20)[18]"
+      environment_ref: "指定环境（R-J10 恢复演练）"
+    measured:
+      status: "not_measured"
+      value: null
+      p50: null
+      p95: null
+      n: null
+      at: null
+      reason: "需重启 backend，归 R-J10 恢复演练；本卡现网只读约束下不可测，禁填估计值。"
+      evidence: null
+    degrade_rule: "未达标只能判失败，或经用户事前/书面 waiver 降级为限制（README 字段速查 slo 行；§12.5 L592）。candidate 锁版前不构成发布判据。"
+    owner_consumer: "R-J10（恢复演练正式测并起草 candidate）；R-J0x 消费本 revision"
+export_shape:
+  target: "J manifest 的 slo.measurements[]（manifest.schema.json :475-530；required 五键 = metric/threshold/measured/method/meets；additionalProperties:false，另有可选 unit/waiver）"
+  mapping: |
+    metric    ← metrics[].metric
+    threshold ← threshold.locked（已锁版原样）或 threshold.candidate 并追加 " (candidate)" 标记；两者皆 null ⇒ "(未定)"（占位, minLength=1；本版 cold 与写侧四项即此三态）
+    measured  ← measured.status=measured 时填 "p95=<p95><unit> (n=<n>)"；status=not_measured 时填字符串 "not_measured"
+    method    ← method.command
+    meets     ← 填写者判定（阈值与实测为同单位数字时校验器 S9 做尽力而为交叉核对，meets 必须与自身数字一致；not_measured 项 meets 只能填 false——⚠️ 此为填写纪律：校验器在 meets=true 时直接放行、不检查 measured=not_measured，见 evidence-rslo/negctl-3-*.txt）
+    覆盖纪律  ← 导出应含全部 9 项；校验器 S9 只要求 ≥1 条，不强制覆盖（门未覆盖的路径，登记于 README 已知边界）
+    unit      ← 可选；本卡导出不附加，保持恰五键
+  consumption_note: "not_measured 项被导出（meets=false）会在校验器 S9 触发未达标链：整体 result=fail、或获用户 waiver（并写 known_limitations）、或改为全测后再引用，三选一；E3+ 另需 revision 非 null 且 measurements 非空——「至少一条真实实测（measured≠not_measured）」是消费纪律、非机器门（机器不检查该项）（见 evidence-rslo/validate-export-e3-*.txt 实证）。反向缺口：not_measured 项误填 meets=true 时 S9 不拦（未被拦下的输入，配对实证见 negctl-3-*.txt；README 已知边界同登）。"
+not_in_scope:
+  - "索引 freshness 阈值 — 归 G2-10 / G4-14（/index/stats 与 /health/lancedb 已暴露时间戳）"
+  - "gold-set 七指标 — 归 G4-14（本文件只承载候选舱位，不代测）"
==== END EMBEDDED DIFF ====

**2. 树内可读参考（只读，不要泛读全仓）：**
- `docs/release-evidence/slo-manifest.yaml`（本卡主产物：9 项指标 / export_shape / decision / environment）
- `docs/release-evidence/README.md` 新增小节 `### SLO manifest（CARD-R-SLO）` + 「已知边界」新增 bullet
- `docs/release-evidence/manifest.schema.json` :475-530（`slo` 块 / `manifest_revision` / `measurements[]` 五键 / `additionalProperties:false`）
- `backend/scripts/validate_release_manifest.py` :76 / :430-439 / :442-475（S9 判据；本卡不改它）
- `_bmad-output/审查/evidence-rslo/`（实测组：`measure-*.txt`、`yaml-check/rev-check-post/validate-export-e2/e3-*`、`negctl-3-20260919T213522.txt` + `negctl-3-inputs-A/B-*.json`、`desens-final-*`、`neo4j-ro-*`、`landgate-*`）
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md`（含 §9b/§9c/§9d）
- 上下文（只读）：`../feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`（§12.5 L592）、`.../2026-08-28-主goal全量分goal总账-v2.md`（:405-410）

---

## ② 作者自述（请独立核对，不要默认接受）

- **A1** 本卡零 `.py`：`a03f0ce3..e4ef1ebf -- . ':(exclude)_bmad-output'` 仅 `docs/release-evidence/{README.md, slo-manifest.yaml}`；`manifest.schema.json` 与校验器指纹未动。
- **A2** yaml 的 `export_shape` 导出形态与 schema `measurements[]` 五键（+ 可选 unit）相容，`additionalProperties:false` 不拒；多一键必被拒。
- **A3** `revision`（`slo-manifest@<日期>-r<N>`）与 J manifest 的 `slo.manifest_revision` 唯一「钉在一起」的门是 `rev-check` 对照脚本（校验器本身不做数值比较）。
- **A4** 实测项数字只来自真 8011 只读 GET / tmp 副本上的真 picker；写侧不可测项一律 `not_measured` + reason + owner 卡，**无估计值**。
- **A5** 阈值全部 `candidate`（`status: draft`）；未获「R-SLO 授权锁版」⇒ `decision.locked_by/at` 为 null。
- **A6** 脱敏门成立：yaml 与 README 无 `/Users/` 绝对路径、无 API key、无 `NEO4J_PASSWORD=`。

---

## ③ 请按重要性排序回答的问题

- **Q0（最高）** `export_shape` 导出的五键与 schema `measurements[]`（`metric/threshold/measured/method/meets` + 可选 `unit`，`additionalProperties:false`）是否**恰**相容？`not_measured` 项把字符串 `"not_measured"` 填进 `measured` 键是否过 schema 的 `minLength`？多导出一键是否真的被拒（README 自己声称的边界）？
- **Q1** `rev-check` 对照脚本是否是唯一能把「校验器绿」与「revision 真存在于 yaml」钉在一起的门？把它换成「校验器 rc=0」会不会假绿（即 J manifest 引用了一个 yaml 里不存在的 revision 仍过）？
- **Q2** `status: draft` vs `locked` 的口径：README 声称「校验器 S9 只查 `manifest_revision` 非 null、**不查** draft/locked」——这个「已知边界」登记是否属实且足够警示？（若 E3+ 引用了 `draft` revision 会怎样？）
- **Q3** 4 项现网只读实测（首屏 / rag warm / rag cold / kg_read）的采样口径是否可复跑、样本是否被剔除（任一非 200 不得剔除样本）？`review_rebuild` 在 tmp 副本上计时是否真不写 live（live `/outputs` 前后 shasum 同）？
- **Q4** 负控 3 的输入侧证据（A/B 两份 manifest 除 5 处 `slo.measurements[i].meets` false→true 外逐字同构）是否足以完成**单变量归因**？
- **Q5** 是否仍存**未披露的强主张**，或与前几轮已收窄口径互相冲突（如 README 既有行被改 = 违反「纯新增」硬约束）？

---

## ④ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级，每条给 `文件:行`（或存档名）与最小证据；不要复述卡片摘要；无法核实的写 `UNVERIFIED` 并说明为什么。对 §② 的每条给出「成立 / 不成立 / 部分」结论。

---

## ⑤ 审查边界（请不要越过）

- 只读复核：不要执行任何写操作、不要改动任何文件。
- **不要评价** 阈值数值**定得对不对**（阈值锁版属用户签字决策，本卡只起草 `candidate`）。
- **不要评价** 是否应该对现网执行写侧指标测量（本卡在只读约束下如实 `not_measured` 并指定 owner 卡）。
- **不要评价** `manifest.schema.json` 本身的设计（它是上游 R-EVD 件，本卡零改动只引用）。
- 若某文件不可读，如实标注后继续。
