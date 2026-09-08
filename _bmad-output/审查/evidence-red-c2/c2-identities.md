# CARD-RED-C2 — 66 条开工失败身份原文（自 identity-open-20260908T080533.txt 解析）

> 逐条来源 = `-rA --tb=short` 的 FAILURES 段 `E ` 行；nodeid 集合来自 `c2-nodeids.txt`（66 条），
> 不是解析结果——解析只负责配原文，配不上的显式列为「未解析到」而不是静默少一行。


## `tests/unit/grouping/test_analyze_canvas.py`

### `TestSubjectIsolation::test_group_id_extraction_chinese`

- **tb 尾行**：
  - `AssertionError: assert 'vault:default:数学' == '数学:离散数学'`
  - ``
  - `- 数学:离散数学`
  - `+ vault:default:数学`

### `TestSubjectIsolation::test_group_id_with_skip_directories`

- **tb 尾行**：
  - `AssertionError: assert 'vault:default:物理' == '物理:力学'`
  - ``
  - `- 物理:力学`
  - `+ vault:default:物理`


## `tests/unit/test_agent_context_injection.py`

### `TestGraphitiSearchDelegation::test_search_calls_graphiti_service`

- **tb 尾行**：
  - `AttributeError: 'ContextEnrichmentService' object has no attribute '_search_graphiti_relations'. Did you mean: '_search_learning_relations'?`

### `TestGraphitiSearchDelegation::test_search_returns_empty_without_graphiti_service`

- **tb 尾行**：
  - `AttributeError: 'ContextEnrichmentService' object has no attribute '_search_graphiti_relations'. Did you mean: '_search_learning_relations'?`

### `TestRelevanceSorting::test_search_graceful_on_exception`

- **tb 尾行**：
  - `AttributeError: 'ContextEnrichmentService' object has no attribute '_search_graphiti_relations'. Did you mean: '_search_learning_relations'?`

### `TestRelevanceSorting::test_search_limits_to_top_5`

- **tb 尾行**：
  - `AttributeError: 'ContextEnrichmentService' object has no attribute '_search_graphiti_relations'. Did you mean: '_search_learning_relations'?`


## `tests/unit/test_agent_memory_trigger.py`

### `TestAgentMemoryMapping::test_all_14_agents_are_mapped`

- **tb 尾行**：
  - `AssertionError: assert 15 == 14`
  - `+  where 15 = len({'basic-decomposition', 'canvas-orchestrator', 'clarification-path', 'comparison-table', 'deep-decomposition', 'example-teaching', ...})`


## `tests/unit/test_agent_service_comparison.py`

### `TestCallExplanationComparisonFormat::test_clarification_agent_receives_concept_string`

- **tb 尾行**：
  - `TypeError: TestCallExplanationComparisonFormat.test_clarification_agent_receives_concept_string.<locals>.mock_call_agent() got an unexpected keyword argument 'canvas_name'`

### `TestCallExplanationComparisonFormat::test_comparison_table_receives_concepts_array`

- **tb 尾行**：
  - `TypeError: TestCallExplanationComparisonFormat.test_comparison_table_receives_concepts_array.<locals>.mock_call_agent() got an unexpected keyword argument 'canvas_name'`

### `TestCallExplanationComparisonFormat::test_example_agent_receives_concept_string`

- **tb 尾行**：
  - `TypeError: TestCallExplanationComparisonFormat.test_example_agent_receives_concept_string.<locals>.mock_call_agent() got an unexpected keyword argument 'canvas_name'`

### `TestCallExplanationComparisonFormat::test_four_level_agent_receives_concept_string`

- **tb 尾行**：
  - `TypeError: TestCallExplanationComparisonFormat.test_four_level_agent_receives_concept_string.<locals>.mock_call_agent() got an unexpected keyword argument 'canvas_name'`

### `TestCallExplanationComparisonFormat::test_memory_agent_receives_concept_string`

- **tb 尾行**：
  - `TypeError: TestCallExplanationComparisonFormat.test_memory_agent_receives_concept_string.<locals>.mock_call_agent() got an unexpected keyword argument 'canvas_name'`

### `TestCallExplanationComparisonFormat::test_oral_agent_receives_concept_string`

- **tb 尾行**：
  - `TypeError: TestCallExplanationComparisonFormat.test_oral_agent_receives_concept_string.<locals>.mock_call_agent() got an unexpected keyword argument 'canvas_name'`


## `tests/unit/test_agent_service_neo4j_memory.py`

### `TestAC2Neo4jQuery::test_cypher_query_structure`

- **tb 尾行**：
  - `AssertionError: assert 'MATCH (m:LearningMemory)' in '\n        MATCH (m:EntityNode)\n        WHERE m.group_id = $group_id\n          AND (toLower(m.text) CONTAINS toLower...n,\n  `

### `TestAC3RelevanceSorting::test_cypher_query_has_order_by_relevance`

- **tb 尾行**：
  - `AssertionError: assert 'ORDER BY m.relevance DESC' in '\n        MATCH (m:EntityNode)\n        WHERE m.group_id = $group_id\n          AND (toLower(m.text) CONTAINS toLower...n,\n `

### `TestMemoryFormatting::test_format_memory_with_none_score`

- **tb 尾行**：
  - `AssertionError: assert 'N/A' in '## 历史学习记忆\n- [2026-01-15]  未评分概念: '`

### `TestMemoryFormatting::test_format_single_memory`

- **tb 尾行**：
  - `AssertionError: assert '85%' in '## 历史学习记忆\n- [2026-01-15]  测试概念: '`


## `tests/unit/test_cache_configuration.py`

### `TestDefaultValuesBackwardCompatible::test_enrichment_extreme_maxsize_1`

- **tb 尾行**：
  - `TypeError: ContextEnrichmentService.__init__() got an unexpected keyword argument 'association_cache_maxsize'`

### `TestDIPathPropagation::test_enrichment_service_di_passes_cache_config`

- **tb 尾行**：
  - `AssertionError: dependencies.py must pass ENRICHMENT_CACHE_MAXSIZE to ContextEnrichmentService`
  - `assert 'ENRICHMENT_CACHE_MAXSIZE' in 'async def get_context_enrichment_service(\n    canvas_service: CanvasServiceDep, settings: SettingsDep\n) -> AsyncGen...n\n    try:\n        y`

### `TestEnrichmentCacheFromSettings::test_cache_default_maxsize`

- **tb 尾行**：
  - `AttributeError: 'ContextEnrichmentService' object has no attribute '_association_cache'`

### `TestEnrichmentCacheFromSettings::test_cache_uses_custom_maxsize`

- **tb 尾行**：
  - `TypeError: ContextEnrichmentService.__init__() got an unexpected keyword argument 'association_cache_maxsize'`


## `tests/unit/test_config_neo4j.py`

### `TestNeo4jSettingsDefaults::test_neo4j_database_default`

- **tb 尾行**：
  - `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`
  - `Value error, NEO4J_PASSWORD must be set explicitly outside local dev. Set env var or disable NEO4J_ENABLED. [type=value_error, input_value={}, input_type=dict]`
  - `For further information visit https://errors.pydantic.dev/2.12/v/value_error`

### `TestNeo4jSettingsDefaults::test_neo4j_enabled_default_true`

- **tb 尾行**：
  - `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`
  - `Value error, INTERNAL_API_KEY required outside local dev. Set env var or enable DEBUG with localhost CORS. [type=value_error, input_value={'NEO4J_PASSWORD': 'test'}, input_type=dic`
  - `For further information visit https://errors.pydantic.dev/2.12/v/value_error`

### `TestNeo4jSettingsDefaults::test_neo4j_password_empty_default`

- **tb 尾行**：
  - `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`
  - `Value error, NEO4J_PASSWORD must be set explicitly outside local dev. Set env var or disable NEO4J_ENABLED. [type=value_error, input_value={}, input_type=dict]`
  - `For further information visit https://errors.pydantic.dev/2.12/v/value_error`

### `TestNeo4jSettingsDefaults::test_neo4j_uri_default`

- **tb 尾行**：
  - `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`
  - `Value error, NEO4J_PASSWORD must be set explicitly outside local dev. Set env var or disable NEO4J_ENABLED. [type=value_error, input_value={}, input_type=dict]`
  - `For further information visit https://errors.pydantic.dev/2.12/v/value_error`

### `TestNeo4jSettingsDefaults::test_neo4j_user_default`

- **tb 尾行**：
  - `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`
  - `Value error, NEO4J_PASSWORD must be set explicitly outside local dev. Set env var or disable NEO4J_ENABLED. [type=value_error, input_value={}, input_type=dict]`
  - `For further information visit https://errors.pydantic.dev/2.12/v/value_error`

### `TestNeo4jSettingsFromEnv::test_neo4j_enabled_case_insensitive`

- **tb 尾行**：
  - `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`
  - `Value error, INTERNAL_API_KEY required outside local dev. Set env var or enable DEBUG with localhost CORS. [type=value_error, input_value={'NEO4J_ENABLED': 'False'}, input_type=dic`
  - `For further information visit https://errors.pydantic.dev/2.12/v/value_error`

### `TestNeo4jSettingsFromEnv::test_neo4j_enabled_false_from_env`

- **tb 尾行**：
  - `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`
  - `Value error, INTERNAL_API_KEY required outside local dev. Set env var or enable DEBUG with localhost CORS. [type=value_error, input_value={'NEO4J_ENABLED': 'false'}, input_type=dic`
  - `For further information visit https://errors.pydantic.dev/2.12/v/value_error`

### `TestNeo4jSettingsFromEnv::test_neo4j_settings_from_env`

- **tb 尾行**：
  - `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`
  - `Value error, INTERNAL_API_KEY required outside local dev. Set env var or enable DEBUG with localhost CORS. [type=value_error, input_value={'NEO4J_ENABLED': 'true',..._DATABASE': 'c`
  - `For further information visit https://errors.pydantic.dev/2.12/v/value_error`

### `TestNeo4jSettingsFromEnv::test_neo4j_uri_with_different_port`

- **tb 尾行**：
  - `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`
  - `Value error, NEO4J_PASSWORD must be set explicitly outside local dev. Set env var or disable NEO4J_ENABLED. [type=value_error, input_value={'NEO4J_URI': 'bolt://localhost:7689'}, i`
  - `For further information visit https://errors.pydantic.dev/2.12/v/value_error`


## `tests/unit/test_context_enrichment_2hop.py`

### `TestEnrichWithAdjacentNodes2Hop::test_enrich_with_2hop_adjacent_nodes`

- **tb 尾行**：
  - `TypeError: ContextEnrichmentService.enrich_with_adjacent_nodes() got an unexpected keyword argument 'include_graphiti'`

### `TestEnrichWithAdjacentNodes2Hop::test_enriched_context_contains_2hop_labels`

- **tb 尾行**：
  - `TypeError: ContextEnrichmentService.enrich_with_adjacent_nodes() got an unexpected keyword argument 'include_graphiti'`


## `tests/unit/test_degraded_flag_propagation.py`

### `TestDegradedResponseFormat::test_degraded_score_is_reasonable`

- **tb 尾行**：
  - `assert 0.0 < 0.0`


## `tests/unit/test_intelligent_parallel_endpoints.py`

### `TestCancelEndpoint::test_cancel_running_session`

- **tb 尾行**：
  - `assert 409 == 200`
  - `+  where 409 = <Response [409 Conflict]>.status_code`
  - `+  and   200 = status.HTTP_200_OK`


## `tests/unit/test_neo4j_health.py`

### `TestNeo4jHealthEndpoint::test_neo4j_connection_timeout`

- **tb 尾行**：
  - `AssertionError: assert 'Connection t...ut (>30000ms)' == 'Connection timeout (>500ms)'`
  - ``
  - `- Connection timeout (>500ms)`
  - `?                      ^`
  - `+ Connection timeout (>30000ms)`
  - `?                      ^^^`


## `tests/unit/test_rag_multimodal_integration.py`

### `TestRRFMultimodalFusion::test_rrf_fusion_with_multimodal_results`

- **tb 尾行**：
  - `ImportError: cannot import name '_fuse_rrf_multi_source' from 'agentic_rag.nodes' (/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/li`

### `TestRRFMultimodalFusion::test_rrf_multimodal_score_contribution`

- **tb 尾行**：
  - `ImportError: cannot import name '_fuse_rrf_multi_source' from 'agentic_rag.nodes' (/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/li`

### `TestRRFMultimodalFusion::test_weighted_fusion_with_multimodal`

- **tb 尾行**：
  - `ImportError: cannot import name '_fuse_weighted_multi_source' from 'agentic_rag.nodes' (/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backe`

### `TestStateGraphMultimodalIntegration::test_fan_out_retrieval_includes_multimodal`

- **tb 尾行**：
  - `TypeError: object of type 'coroutine' has no len()`


## `tests/unit/test_s02_entity_types.py`

### `TestProcessEpisodeForwarding::test_forwards_entity_and_edge_types`

- **tb 尾行**：
  - `AssertionError: assert 'math-group__semantic' == 'math-group'`
  - ``
  - `- math-group`
  - `+ math-group__semantic`


## `tests/unit/test_s02_search_upgrade.py`

### `test_search_recipes_all_5_mapped`

- **tb 尾行**：
  - ``
  - `Extra items in the left set:`
  - `'edge_mmr'`
  - `'node_mmr'`
  - `'combined_mmr'`
  - `Use -v to get more diff`


## `tests/unit/test_story_1_7_env_config.py`

### `TestDockerComposeVariableization::test_no_hardcoded_user_paths`

- **tb 尾行**：
  - `AssertionError: Hardcoded user paths found: ['/Users/Heishing/', '/Users/Heishing/', '/Users/Heishing/']`
  - `assert not ['/Users/Heishing/', '/Users/Heishing/', '/Users/Heishing/']`


## `tests/unit/test_story_30_24_boundary.py`

### `TestSpecialCharacterGroupId::test_neo4j_parameterized_query_with_special_chars`

- **tb 尾行**：
  - `AssertionError: groupId not passed as keyword param. kwargs={'userId': 'test_user', 'limit': 5, 'group_id': 'vault__script_drop_table_users', 'group_prefix': 'vault__script_drop_ta`
  - `assert None == "<script>'; DROP TABLE users;--"`
  - `+  where None = <built-in method get of dict object at 0x13a2be780>('groupId')`
  - `+    where <built-in method get of dict object at 0x13a2be780> = {'group_id': 'vault__script_drop_table_users', 'group_prefix': 'vault__script_drop_table_users__', 'limit': 5, 'use`

### `TestVaultVerifyExitCode::test_package_json_verify_command_correct`

- **tb 尾行**：
  - `AssertionError: assert False`
  - `+  where False = exists()`
  - `+    where exists = PosixPath('/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/canvas-progress-tracker/obsidian-plugin/package.json').exists`

### `TestVaultVerifyExitCode::test_verify_script_exists`

- **tb 尾行**：
  - `AssertionError: verify script not found: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/canvas-progress-tracker/obsidian-plugin/scripts/veri`
  - `assert False`
  - `+  where False = exists()`
  - `+    where exists = PosixPath('/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/canvas-progress-tracker/obsidian-plugin/scripts/verify-vault.m`
  - `+      where PosixPath('/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/canvas-progress-tracker/obsidian-plugin/scripts/verify-vault.mjs') = `

### `TestVaultVerifyExitCode::test_verify_script_exits_nonzero_when_file_not_found`

- **tb 尾行**：
  - `assert 'NOT FOUND' in "node:internal/modules/cjs/loader:1503\n  throw err;\n  ^\n\nError: Cannot find module '/Users/Heishing/Desktop/canvas...t node:internal/main/run_main_module:`

### `TestVaultVerifyExitCode::test_verify_script_exits_nonzero_when_stale`

- **tb 尾行**：
  - `assert 'STALE' in (('' or ''))`
  - `+  where '' = CompletedProcess(args=['node', '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c... node:internal/main/run_main_module:33:47 {\n`

### `TestVaultVerifyExitCode::test_verify_script_exits_zero_when_fresh`

- **tb 尾行**：
  - `assert 1 == 0`
  - `+  where 1 = CompletedProcess(args=['node', '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c... node:internal/main/run_main_module:33:47 {\n `


## `tests/unit/test_story_38_1_review_fixes.py`

### `TestDoIndexCoverage::test_do_index_raises_file_not_found`

- **tb 尾行**：
  - `TypeError: 'MagicMock' object can't be awaited`

### `TestDoIndexCoverage::test_do_index_reads_canvas_and_calls_index`

- **tb 尾行**：
  - `TypeError: 'MagicMock' object can't be awaited`


## `tests/unit/test_story_38_4_dual_write_default.py`

### `TestAC1SafeDefault::test_startup_log_dual_write_enabled_default`

- **tb 尾行**：
  - `AttributeError: <module 'app.main' from '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/app/main.py'> does not have the attribute 's`

### `TestAC2ExplicitDisable::test_startup_log_dual_write_disabled_explicit`

- **tb 尾行**：
  - `AttributeError: <module 'app.main' from '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/app/main.py'> does not have the attribute 's`

### `TestAC2ExplicitDisable::test_warning_log_data_loss_risk_when_disabled`

- **tb 尾行**：
  - `AttributeError: <module 'app.main' from '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/app/main.py'> does not have the attribute 's`


## `tests/unit/test_story_38_8_fallback_sync.py`

### `TestAC5FileRotation::test_pending_entries_rewritten`

- **tb 尾行**：
  - `Exception: Neo4j connection lost`


## `tests/unit/test_subject_isolation.py`

### `TestExtractSubjectFromCanvasPath::test_extract_subject_empty_path`

- **tb 尾行**：
  - `AttributeError: 'str' object has no attribute 'value'`


## `tests/unit/test_supplementary_reranker.py`

### `TestFilterFloor::test_floor_still_respects_top_k`

- **tb 尾行**：
  - `AssertionError: assert None is True`
  - `+  where None = <built-in method get of dict object at 0x13ac96100>('filter_floor_triggered')`
  - `+    where <built-in method get of dict object at 0x13ac96100> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get`

### `TestFilterFloor::test_floor_triggered_marks_first_material`

- **tb 尾行**：
  - `AssertionError: assert None is True`
  - `+  where None = <built-in method get of dict object at 0x13ac3fdc0>('filter_floor_triggered')`
  - `+    where <built-in method get of dict object at 0x13ac3fdc0> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get`

### `TestFilterFloor::test_floor_triggered_when_kill_ratio_high`

- **tb 尾行**：
  - `AssertionError: assert None is True`
  - `+  where None = <built-in method get of dict object at 0x13acc8180>('filter_floor_triggered')`
  - `+    where <built-in method get of dict object at 0x13acc8180> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get`

### `TestFilterFloor::test_min_keep_zero_disables_floor`

- **tb 尾行**：
  - `AssertionError: assert 5 == 0`
  - `+  where 5 = len([{'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'query_overl...nk_score': 0.5, 'score': 0.5, ...}, {'hub_`

### `TestFilterFloorTaintExclusion::test_floor_all_review_returns_empty_list`

- **tb 尾行**：
  - `AssertionError: assert 5 == 0`
  - `+  where 5 = len([{'hub_penalty': 0.0, 'injection_risk': 0.6, 'query_overlap': 0.0, 'rerank_score': 0.5, ...}, {'hub_penalty': 0.0, 'in...'rerank_score': 0.5, ...}, {'hub_penalty':`

### `TestFilterFloorTaintExclusion::test_floor_no_taint_field_treated_as_clean`

- **tb 尾行**：
  - `AssertionError: assert None is True`
  - `+  where None = <built-in method get of dict object at 0x13acd20c0>('filter_floor_triggered')`
  - `+    where <built-in method get of dict object at 0x13acd20c0> = {'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}.get`

### `TestFilterFloorTaintExclusion::test_min_keep_floor_excludes_review_taint`

- **tb 尾行**：
  - `AssertionError: assert 3 == 2`
  - `+  where 3 = len([{'hub_penalty': 0.0, 'query_overlap': 0.0, 'rerank_score': 0.5, 'score': 0.5, ...}, {'hub_penalty': 0.0, 'query_overl... 0.5, 'score': 0.5, ...}, {'hub_penalty': `

### `TestTypeWeightsIndexerTransition::test_indexer_note_mapped_to_canonical`

- **tb 尾行**：
  - `assert 1.0 == 0.7`

### `TestTypeWeightsIndexerTransition::test_indexer_video_transcript_mapped_to_canonical`

- **tb 尾行**：
  - `AssertionError: assert 0.75 == 0.9`
  - `+  where 0.75 = <function get_type_weight at 0x13a6483b0>('video_transcript')`


## `tests/unit/test_verification_service_injection.py`

### `TestDependenciesInjection::test_get_verification_service_injects_graphiti_client`

- **tb 尾行**：
  - `AssertionError: Expected 'get_graphiti_temporal_client' to have been called once. Called 0 times.`


## `tests/unit/test_wave5_stageb_continued_vault_id_injection.py`

### `TestSharedResolverImportedByEndpoints::test_endpoint_imports_shared_resolver[app.api.v1.endpoints.agents]`

- **tb 尾行**：
  - `AssertionError: app.api.v1.endpoints.agents did not import resolve_vault_group_id from _vault_id_resolver`
  - `assert False`
  - `+  where False = hasattr(<module 'app.api.v1.endpoints.agents' from '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/app/api/v1/endpo`

