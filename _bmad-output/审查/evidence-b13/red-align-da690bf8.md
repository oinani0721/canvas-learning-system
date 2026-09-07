# RED-ALIGN · tests/unit 既有红 202 条 → 第十三批接收卡（基线 unit-red-integ-20260906T203713.txt @ 候选树 = 主干 da690bf8 代码等同）

> 采集：2026-09-07（RED-ALIGN agent，只读；未跑 pytest、未改任何文件）；分母 **202**（协议 §5 nodeid 口径：`grep -E '^(FAILED|ERROR) tests/' | sed 's/ - .*//' | sort -u`，FAILED 173 / ERROR 29）。
> 分诊来源：`_bmad-output/审查/evidence-red-triage/rows-final.json`（247 行，字段 `nodeid / kind / cat / card / identity / suspect_sha`，nodeid 集合与 `evidence-b12/unit-red-baseline-03ac8bf8.txt` 的 247 逐条相等）+ `_bmad-output/审查/2026-09-05-第十二批-tests-unit-红基线分诊-247.md`。
> 草案：`_bmad-output/审查/2026-09-05-第十二批-RED-第十三批卡草案.md` §〇.5（分派闭合表）；Codex round-1 HIGH-1 改判（5 条 C2→R）只写在草案 §〇.5，**`rows-final.json` 未回填**（那 5 条的 `card` 字段仍是 `CARD-RED-C2`），本文按草案口径套用。
> 旧基线对照：`evidence-b12/unit-red-baseline-03ac8bf8.txt`（247）；247 − 202 = **45**，全部为 Y4-D（`f19dcff6` Phase 2 定点抽取）造成：skip 掩盖 **43** / 真修 **2**（`2026-09-06-第十二批复核裁定与待裁决登记.md` §四 + Y4-D 验收单 `_bmad-output/验收单/UAT-CARD-TOOL-testinfra-salvage-2026-09-06.md` (e) 三列表），本文按 nodeid 逐条复核一致（§三）。
> 代码树核对：`.claude/worktrees/batch13-recon` HEAD = `da690bf8`；`git diff --stat da690bf8 HEAD -- . ':(exclude)_bmad-output'` 空、`status --porcelain` 空；`da690bf8` 与第十二批集成尾 `d209622d` 的非 `_bmad-output` 差异仅 `.claude/rules/card-batch-protocol.md`（2 行，非 backend 代码）⇒ 与采集 202 的候选树 backend 代码等同。202 条 nodeid 的文件与 `class`/`def` 符号在该树 `backend/tests/unit/` 下**全部存在**（202/202，见 §五）。
> 旁证（非本文判据来源）：主 session 在该树刚跑完的 `evidence-b13/dir-tests-unit-20260907T123925.txt`（汇总行 `173 failed, 4749 passed, 48 skipped, 29 errors`）按同口径抽出的 nodeid 集合与 202 基线 **逐条相同**（`diff` 空）⇒ A1-sentinel 12 条本轮未漂移。

## 一、闭合表

| 接收卡 | 车道 | 条数（202 口径） | 草案 §〇.5（247 口径） | 备注 |
|---|---|---|---|---|
| `CARD-RED-A1-auth` | U10-C | **37** | 37 | 不变。`test_chat_endpoint` 16 / `test_study_question_deep_mode` 8 / `test_enrich_context_vault_isolation` 7 / `test_sync_exception_classification` 6（A2 改归） |
| `CARD-RED-A1-sentinel` | U10-D | **12** | 12 | 不变。`test_startup_health_check` 6 / `test_health_detailed` 3 / `test_kg_health` 1 / `test_mock_degradation_transparency` 1 / `test_review_mode_support` 1。fresh run @da690bf8 仍是这 12 条（见首部旁证） |
| `CARD-RED-A2` | U10-E | **3** | 3 | 不变 |
| `CARD-RED-E` | U10-B | **9** | 9 | 不变 |
| `CARD-RED-C1` | U11-A | **10** | 43 | **−33**：全部被 Y4-D 模块级/类级 skip 掩盖（§三）。剩 10 条含草案 ②「桩值 vs 断言自相矛盾」3 条（`TestAC1TimeoutRetryAlignment`） |
| `CARD-RED-C2` | U11-B | **66** | 66 | 不变（已扣 MOCKFIX 38 与 Codex HIGH-1 改判 5） |
| `CARD-RED-NEW` | U11-C | **8** | 8 | 不变 |
| `CARD-RED-R` | U5-C | **26** | 27 | **−1**：`test_qa_38_6_scoring_reliability_extra.py::TestFullCycleIntegration::test_full_cycle_recovery_fails_then_merge` 被类级 skip 掩盖。含 Codex HIGH-1 改判 5 条（`test_vault_notes_group_filter` ×4 + `test_strip_whiteboard_removes_admonition_callouts`），5 条均在 202 内 |
| **第十三批 8 卡小计** | | **171** | 205 | |
| `CARD-RED-MOCKFIX` | 第十四批 | **27** | 38 | **−11**：9 条类级 skip 掩盖 + **2 条真修**（`test_id_format` / `test_batch_id_format`）。剩 27 条失败身份**完全同一**：`setup ERROR: TypeError: 'MagicMock' object can't be awaited @ memory_service.py:381`（`test_story_30_13_batch_idempotency` 11 / `test_story_30_11_batch_parallel` 10 / `test_memory_service_batch` 6）；kind 全为 ERROR |
| `CARD-RED-ENVDEP` | 第十四批 | **3** | 3 | 不变。`test_agent_service_extraction.py::TestDebugAgentResponseLogging` 3 条（ERROR 2 `fixture 'mocker' not found` + FAILED 1 读真 `.env`） |
| 部署线（不进 RED） | 部署线 | **1** | 1 | `test_vault_doc_roles.py::test_live_vault_enforce_clean` |
| 未分诊 | — | **0** | — | 202 ⊂ 247，无 Y4-D 之后新出现的 nodeid（`comm -13 b247 b202` 空） |
| **合计** | | **202** | 247 | 171 + 27 + 3 + 1 + 0 = 202 ✓（`sort -u | wc -l` 实测，见 §五） |

kind 分布核对：C2 66F / A1-auth 37F / MOCKFIX 27E / R 26F / A1-sentinel 12F / C1 10F / E 9F / NEW 8F / A2 3F / ENVDEP 2E+1F / 部署线 1F ⇒ F 173 / E 29，与基线文件 `awk '{print $1}' | uniq -c` 一致。

## 二、逐卡 nodeid 列表（sort 序；卡文直接引用本节）

### CARD-RED-A1-auth（37）

```
tests/unit/test_chat_endpoint.py::test_enrich_context_accepts_user_question_and_mode_answer
tests/unit/test_chat_endpoint.py::test_enrich_context_answer_mode_uses_lazy_init_path
tests/unit/test_chat_endpoint.py::test_enrich_context_assembler_budget_field
tests/unit/test_chat_endpoint.py::test_enrich_context_default_frontmatter
tests/unit/test_chat_endpoint.py::test_enrich_context_degraded_appends_notice
tests/unit/test_chat_endpoint.py::test_enrich_context_empty_node_path_rejected
tests/unit/test_chat_endpoint.py::test_enrich_context_happy_path
tests/unit/test_chat_endpoint.py::test_enrich_context_max_hops_validation
tests/unit/test_chat_endpoint.py::test_enrich_context_preload_mode_skips_supplementary
tests/unit/test_chat_endpoint.py::test_enrich_context_rejects_invalid_mode
tests/unit/test_chat_endpoint.py::test_enrich_context_response_includes_elapsed_ms
tests/unit/test_chat_endpoint.py::test_enrich_context_returns_retrieval_trace
tests/unit/test_chat_endpoint.py::test_enrich_context_trace_includes_degradation_when_graph_unbuilt
tests/unit/test_chat_endpoint.py::test_rag_enrich_hook_lazy_init_returns_none_injects_degraded_marker
tests/unit/test_chat_endpoint.py::test_rag_enrich_hook_short_prompt_skips_lazy_init
tests/unit/test_chat_endpoint.py::test_rag_enrich_hook_uses_lazy_init
tests/unit/test_enrich_context_vault_isolation.py::test_chinese_vault_id_not_collapsed_to_default
tests/unit/test_enrich_context_vault_isolation.py::test_subject_id_optional_backward_compat
tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_emoji_stripped
tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_empty_string_rejected_422
tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_missing_rejected_422
tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_provided_triggers_context_var_injection
tests/unit/test_enrich_context_vault_isolation.py::test_vault_id_with_special_chars_sanitized
tests/unit/test_study_question_deep_mode.py::test_mode_answer_keeps_top_k_20_and_hard_cap_15
tests/unit/test_study_question_deep_mode.py::test_mode_deep_accepted_by_request_model
tests/unit/test_study_question_deep_mode.py::test_mode_deep_empty_user_question_skips_search
tests/unit/test_study_question_deep_mode.py::test_mode_deep_uses_top_k_30_and_hard_cap_20
tests/unit/test_study_question_deep_mode.py::test_mode_deep_without_user_question_skips_search
tests/unit/test_study_question_deep_mode.py::test_mode_default_is_preload
tests/unit/test_study_question_deep_mode.py::test_mode_invalid_rejected_by_pydantic
tests/unit/test_study_question_deep_mode.py::test_mode_preload_with_user_question_still_skips_search
tests/unit/test_sync_exception_classification.py::TestInfrastructureErrors::test_auth_error_returns_503
tests/unit/test_sync_exception_classification.py::TestInfrastructureErrors::test_connection_error_returns_503
tests/unit/test_sync_exception_classification.py::TestInfrastructureErrors::test_service_unavailable_returns_503
tests/unit/test_sync_exception_classification.py::TestLogicErrors::test_generic_exception_returns_500
tests/unit/test_sync_exception_classification.py::TestLogicErrors::test_type_error_returns_500
tests/unit/test_sync_exception_classification.py::TestLogicErrors::test_value_error_returns_500
```

### CARD-RED-A1-sentinel（12）

```
tests/unit/test_health_detailed.py::TestDetailedHealthEndpoint::test_component_has_required_fields
tests/unit/test_health_detailed.py::TestDetailedHealthEndpoint::test_returns_components
tests/unit/test_health_detailed.py::TestDetailedHealthEndpoint::test_unavailable_core_returns_503
tests/unit/test_kg_health.py::TestKGHealthEndpoint::test_endpoint_returns_200
tests/unit/test_mock_degradation_transparency.py::TestMockScoringWarningLogs::test_mock_mode_logs_warning
tests/unit/test_review_mode_support.py::TestReviewModeSupport::test_fresh_mode_parameter_accepted
tests/unit/test_startup_health_check.py::TestSetupWizard::test_endpoint_exists
tests/unit/test_startup_health_check.py::TestSetupWizard::test_returns_structured_report
tests/unit/test_startup_health_check.py::TestStartupCheck::test_checks_neo4j_ollama_fastapi_mcp
tests/unit/test_startup_health_check.py::TestStartupCheck::test_each_check_has_required_fields
tests/unit/test_startup_health_check.py::TestStartupCheck::test_endpoint_exists
tests/unit/test_startup_health_check.py::TestStartupCheck::test_returns_structured_response
```

### CARD-RED-A2（3）

```
tests/unit/test_sync_batch_auth.py::TestProductionFailClosed::test_no_key_configured_fails_closed_503
tests/unit/test_system_endpoint_auth.py::TestSystemConfigAuth::test_prod_no_key_configured_503
tests/unit/test_system_endpoint_auth.py::TestSystemTestLLMAuth::test_prod_no_key_configured_503
```

### CARD-RED-E（9）

```
tests/unit/test_agent_templates_smoke.py::TestAgentTemplateFiles::test_agent_template_exists[canvas-orchestrator.md]
tests/unit/test_agent_templates_smoke.py::TestAgentTemplateFiles::test_agent_template_exists[graphiti-memory-agent.md]
tests/unit/test_agent_templates_smoke.py::TestAgentTemplateFiles::test_agent_template_exists[hint-generation.md]
tests/unit/test_agent_templates_smoke.py::TestAgentTemplateFiles::test_agent_template_exists[iteration-validator.md]
tests/unit/test_agent_templates_smoke.py::TestAgentTemplateFiles::test_agent_template_exists[parallel-dev-orchestrator.md]
tests/unit/test_agent_templates_smoke.py::TestAgentTemplateFiles::test_agent_template_exists[planning-orchestrator.md]
tests/unit/test_agent_templates_smoke.py::TestAgentTemplateFiles::test_agent_template_exists[review-board-agent-selector.md]
tests/unit/test_agent_templates_smoke.py::TestAgentTemplateFiles::test_hint_generation_template_exists
tests/unit/test_agent_templates_smoke.py::TestAgentTemplateFiles::test_minimum_template_count
```

### CARD-RED-C1（10）

```
tests/unit/test_cache_configuration.py::TestMemoryRetryDelayFromSettings::test_retry_delay_reads_settings
tests/unit/test_qa_38_4_dual_write_extra.py::TestQAGetAttrDefenseInDepth::test_memory_service_getattr_fallback_is_false
tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestStartupIntegration::test_fallback_sync_called_in_lifespan
tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestStartupIntegration::test_main_imports_fallback_sync
tests/unit/test_story_38_4_dual_write_default.py::TestAC1SafeDefault::test_lowercase_alias_returns_true_by_default
tests/unit/test_story_38_4_dual_write_default.py::TestAC1SafeDefault::test_settings_field_default_is_true
tests/unit/test_story_38_4_dual_write_default.py::TestAC3MissingEnvVar::test_missing_env_var_defaults_to_true
tests/unit/test_story_38_6_scoring_reliability.py::TestAC1TimeoutRetryAlignment::test_backoff_progression
tests/unit/test_story_38_6_scoring_reliability.py::TestAC1TimeoutRetryAlignment::test_inner_per_attempt_timeout_increased
tests/unit/test_story_38_6_scoring_reliability.py::TestAC1TimeoutRetryAlignment::test_retry_backoff_base_is_1_second
```

失败身份（自 `rows-final.json`）：`_retry_base_delay` AttributeError ×1（草案「残余改归 C1 的 1 条」）；`ENABLE_GRAPHITI_JSON_DUAL_WRITE` 默认值 False vs 期望 True ×4（`test_qa_38_4` 1 + `test_story_38_4` 3）；`app/main.py` 源码文本不含 `sync_all_fallbacks` / `get_fallback_sync_service` ×2；`assert 0.1 == 1.0` / `assert 0.5 >= 2.0` ×3（= 草案 ②「桩值 0.5/0.1 vs 断言 2.0/1.0」）。草案 ① 的 25 条 AttributeError（`_write_to_graphiti_json*`）与 ③ 的 TimeoutError 族**已全部被 skip 掩盖**（§三），本卡在 202 口径下**不再有 ①/③ 形态**。

### CARD-RED-C2（66）

```
tests/unit/grouping/test_analyze_canvas.py::TestSubjectIsolation::test_group_id_extraction_chinese
tests/unit/grouping/test_analyze_canvas.py::TestSubjectIsolation::test_group_id_with_skip_directories
tests/unit/test_agent_context_injection.py::TestGraphitiSearchDelegation::test_search_calls_graphiti_service
tests/unit/test_agent_context_injection.py::TestGraphitiSearchDelegation::test_search_returns_empty_without_graphiti_service
tests/unit/test_agent_context_injection.py::TestRelevanceSorting::test_search_graceful_on_exception
tests/unit/test_agent_context_injection.py::TestRelevanceSorting::test_search_limits_to_top_5
tests/unit/test_agent_memory_trigger.py::TestAgentMemoryMapping::test_all_14_agents_are_mapped
tests/unit/test_agent_service_comparison.py::TestCallExplanationComparisonFormat::test_clarification_agent_receives_concept_string
tests/unit/test_agent_service_comparison.py::TestCallExplanationComparisonFormat::test_comparison_table_receives_concepts_array
tests/unit/test_agent_service_comparison.py::TestCallExplanationComparisonFormat::test_example_agent_receives_concept_string
tests/unit/test_agent_service_comparison.py::TestCallExplanationComparisonFormat::test_four_level_agent_receives_concept_string
tests/unit/test_agent_service_comparison.py::TestCallExplanationComparisonFormat::test_memory_agent_receives_concept_string
tests/unit/test_agent_service_comparison.py::TestCallExplanationComparisonFormat::test_oral_agent_receives_concept_string
tests/unit/test_agent_service_neo4j_memory.py::TestAC2Neo4jQuery::test_cypher_query_structure
tests/unit/test_agent_service_neo4j_memory.py::TestAC3RelevanceSorting::test_cypher_query_has_order_by_relevance
tests/unit/test_agent_service_neo4j_memory.py::TestMemoryFormatting::test_format_memory_with_none_score
tests/unit/test_agent_service_neo4j_memory.py::TestMemoryFormatting::test_format_single_memory
tests/unit/test_cache_configuration.py::TestDefaultValuesBackwardCompatible::test_enrichment_extreme_maxsize_1
tests/unit/test_cache_configuration.py::TestDIPathPropagation::test_enrichment_service_di_passes_cache_config
tests/unit/test_cache_configuration.py::TestEnrichmentCacheFromSettings::test_cache_default_maxsize
tests/unit/test_cache_configuration.py::TestEnrichmentCacheFromSettings::test_cache_uses_custom_maxsize
tests/unit/test_config_neo4j.py::TestNeo4jSettingsDefaults::test_neo4j_database_default
tests/unit/test_config_neo4j.py::TestNeo4jSettingsDefaults::test_neo4j_enabled_default_true
tests/unit/test_config_neo4j.py::TestNeo4jSettingsDefaults::test_neo4j_password_empty_default
tests/unit/test_config_neo4j.py::TestNeo4jSettingsDefaults::test_neo4j_uri_default
tests/unit/test_config_neo4j.py::TestNeo4jSettingsDefaults::test_neo4j_user_default
tests/unit/test_config_neo4j.py::TestNeo4jSettingsFromEnv::test_neo4j_enabled_case_insensitive
tests/unit/test_config_neo4j.py::TestNeo4jSettingsFromEnv::test_neo4j_enabled_false_from_env
tests/unit/test_config_neo4j.py::TestNeo4jSettingsFromEnv::test_neo4j_settings_from_env
tests/unit/test_config_neo4j.py::TestNeo4jSettingsFromEnv::test_neo4j_uri_with_different_port
tests/unit/test_context_enrichment_2hop.py::TestEnrichWithAdjacentNodes2Hop::test_enrich_with_2hop_adjacent_nodes
tests/unit/test_context_enrichment_2hop.py::TestEnrichWithAdjacentNodes2Hop::test_enriched_context_contains_2hop_labels
tests/unit/test_degraded_flag_propagation.py::TestDegradedResponseFormat::test_degraded_score_is_reasonable
tests/unit/test_intelligent_parallel_endpoints.py::TestCancelEndpoint::test_cancel_running_session
tests/unit/test_neo4j_health.py::TestNeo4jHealthEndpoint::test_neo4j_connection_timeout
tests/unit/test_rag_multimodal_integration.py::TestRRFMultimodalFusion::test_rrf_fusion_with_multimodal_results
tests/unit/test_rag_multimodal_integration.py::TestRRFMultimodalFusion::test_rrf_multimodal_score_contribution
tests/unit/test_rag_multimodal_integration.py::TestRRFMultimodalFusion::test_weighted_fusion_with_multimodal
tests/unit/test_rag_multimodal_integration.py::TestStateGraphMultimodalIntegration::test_fan_out_retrieval_includes_multimodal
tests/unit/test_s02_entity_types.py::TestProcessEpisodeForwarding::test_forwards_entity_and_edge_types
tests/unit/test_s02_search_upgrade.py::test_search_recipes_all_5_mapped
tests/unit/test_story_1_7_env_config.py::TestDockerComposeVariableization::test_no_hardcoded_user_paths
tests/unit/test_story_30_24_boundary.py::TestSpecialCharacterGroupId::test_neo4j_parameterized_query_with_special_chars
tests/unit/test_story_30_24_boundary.py::TestVaultVerifyExitCode::test_package_json_verify_command_correct
tests/unit/test_story_30_24_boundary.py::TestVaultVerifyExitCode::test_verify_script_exists
tests/unit/test_story_30_24_boundary.py::TestVaultVerifyExitCode::test_verify_script_exits_nonzero_when_file_not_found
tests/unit/test_story_30_24_boundary.py::TestVaultVerifyExitCode::test_verify_script_exits_nonzero_when_stale
tests/unit/test_story_30_24_boundary.py::TestVaultVerifyExitCode::test_verify_script_exits_zero_when_fresh
tests/unit/test_story_38_1_review_fixes.py::TestDoIndexCoverage::test_do_index_raises_file_not_found
tests/unit/test_story_38_1_review_fixes.py::TestDoIndexCoverage::test_do_index_reads_canvas_and_calls_index
tests/unit/test_story_38_4_dual_write_default.py::TestAC1SafeDefault::test_startup_log_dual_write_enabled_default
tests/unit/test_story_38_4_dual_write_default.py::TestAC2ExplicitDisable::test_startup_log_dual_write_disabled_explicit
tests/unit/test_story_38_4_dual_write_default.py::TestAC2ExplicitDisable::test_warning_log_data_loss_risk_when_disabled
tests/unit/test_story_38_8_fallback_sync.py::TestAC5FileRotation::test_pending_entries_rewritten
tests/unit/test_subject_isolation.py::TestExtractSubjectFromCanvasPath::test_extract_subject_empty_path
tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_still_respects_top_k
tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_marks_first_material
tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_floor_triggered_when_kill_ratio_high
tests/unit/test_supplementary_reranker.py::TestFilterFloor::test_min_keep_zero_disables_floor
tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_all_review_returns_empty_list
tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_floor_no_taint_field_treated_as_clean
tests/unit/test_supplementary_reranker.py::TestFilterFloorTaintExclusion::test_min_keep_floor_excludes_review_taint
tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_note_mapped_to_canonical
tests/unit/test_supplementary_reranker.py::TestTypeWeightsIndexerTransition::test_indexer_video_transcript_mapped_to_canonical
tests/unit/test_verification_service_injection.py::TestDependenciesInjection::test_get_verification_service_injects_graphiti_client
tests/unit/test_wave5_stageb_continued_vault_id_injection.py::TestSharedResolverImportedByEndpoints::test_endpoint_imports_shared_resolver[app.api.v1.endpoints.agents]
```

按文件：`test_config_neo4j` 9 / `test_supplementary_reranker` 9 / `test_agent_service_comparison` 6 / `test_story_30_24_boundary` 6 / `test_agent_context_injection` 4 / `test_agent_service_neo4j_memory` 4 / `test_cache_configuration` 4 / `test_rag_multimodal_integration` 4 / `test_story_38_4_dual_write_default` 3 / `grouping/test_analyze_canvas` 2 / `test_context_enrichment_2hop` 2 / `test_story_38_1_review_fixes` 2 / 其余 11 文件各 1。草案「建议拆分」的三个锚（config 9 / reranker 9 / archived-path 6）在 202 里原样保留。

### CARD-RED-NEW（8）

```
tests/unit/test_calibration_tracker.py::TestCalibrationRating::test_over_confident_boundary
tests/unit/test_calibration_tracker.py::TestCalibrationRating::test_under_confident_boundary
tests/unit/test_canvas_memory_trigger.py::TestAddEdgeMemoryTrigger::test_add_edge_triggers_memory_event
tests/unit/test_difficulty_matcher.py::TestSlidingWindowStats::test_empty_window_stats
tests/unit/test_event_bus.py::TestTier2Important::test_tier2_all_retries_exhausted_writes_outbox
tests/unit/test_event_bus.py::TestTier2Important::test_tier2_retry_then_success
tests/unit/test_mastery_fusion.py::TestPearsonCorrelation::test_no_correlation
tests/unit/test_multimodal_path_security.py::TestValidateSafePath::test_path_traversal_windows_style
```

### CARD-RED-R（26）

```
tests/unit/test_agent_memory_injection.py::TestMemoryInjection::test_graceful_degradation_on_exception
tests/unit/test_agent_service_neo4j_memory.py::TestEdgeCases::test_neo4j_query_error_returns_empty
tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_difficulty_context_in_prompt
tests/unit/test_difficulty_canvas_integration.py::TestAIQuestionDifficultyInjection::test_no_difficulty_map_no_extra_fields
tests/unit/test_difficulty_canvas_integration.py::TestGetDifficultyData::test_memory_service_unavailable_returns_none
tests/unit/test_epic30_memory_pipeline.py::TestRecordTemporalEventLifecycle::test_p0_neo4j_write_failure_degrades_silently
tests/unit/test_epic36_gap_coverage.py::TestGetRelatedMemoriesReturnStructure::test_query_exception_returns_empty
tests/unit/test_intelligent_parallel_endpoints.py::TestCancelEndpoint::test_cancel_nonexistent_session_404
tests/unit/test_intelligent_parallel_endpoints.py::TestErrorResponses::test_404_error_format
tests/unit/test_intelligent_parallel_endpoints.py::TestProgressEndpoint::test_progress_invalid_session_404
tests/unit/test_neo4j_fulltext_index.py::TestEnsureFulltextIndex::test_ensure_fulltext_index_idempotent
tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestMergedViewEdgeCases::test_merged_view_sort_newest_first
tests/unit/test_rag_p0_doc_type_filter.py::test_strip_whiteboard_removes_admonition_callouts
tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_normalizes_schema
tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_passes_node_id_filter_to_search_memories
tests/unit/test_story_2_3_error_reminders.py::test_search_error_memories_sorts_by_timestamp_desc
tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_filter_post_merge
tests/unit/test_story_2_3_error_reminders.py::test_search_memories_node_id_none_is_no_filter
tests/unit/test_story_38_6_scoring_reliability.py::TestAC4MergedView::test_get_learning_history_merges_failed_scores
tests/unit/test_vault_notes_group_filter.py::test_group_id_honors_nested_metadata_json_subject
tests/unit/test_vault_notes_group_filter.py::test_group_id_physics_filters_to_physics_only
tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_common_and_no_match_returns_empty
tests/unit/test_vault_notes_group_filter.py::test_group_id_with_no_explicit_match_returns_only_common_notes
tests/unit/test_verification_dedup.py::TestVerificationDedup::test_no_history_generates_standard_question
tests/unit/test_verification_dedup.py::TestVerificationDedup::test_with_history_generates_alternative_question
tests/unit/test_websocket_endpoints.py::TestWebSocketEndpoint::test_validate_session_handles_validator_error
```

嫌疑 sha 分布（自 `rows-final.json`，仅嫌疑、无 bisect 实证）：`a9304c69` 9 / `3d10a02b` 5 / `—`（Codex HIGH-1 改判 5 条，无依据 sha）5 / `4867dd09` 2 / `e6fbd337` 2 / `1768c19d` 2 / `4236b12e` 1。

### CARD-RED-MOCKFIX（27 · 第十四批）

```
tests/unit/test_memory_service_batch.py::TestRecordBatchLearningEventsConcept::test_color_removed_event_type
tests/unit/test_memory_service_batch.py::TestRecordBatchLearningEventsConcept::test_concept_fallback_to_node_text
tests/unit/test_memory_service_batch.py::TestRecordBatchLearningEventsConcept::test_concept_fallback_to_unknown
tests/unit/test_memory_service_batch.py::TestRecordBatchLearningEventsConcept::test_concept_field_used_when_present
tests/unit/test_memory_service_batch.py::TestRecordBatchLearningEventsConcept::test_neo4j_disconnected_still_stores_in_memory
tests/unit/test_memory_service_batch.py::TestRecordBatchLearningEventsConcept::test_node_removed_event_type
tests/unit/test_story_30_11_batch_parallel.py::TestBatchIdempotencyCompat::test_duplicate_batch_no_duplicates
tests/unit/test_story_30_11_batch_parallel.py::TestBatchNeo4jDegradation::test_neo4j_unavailable_still_processes_to_memory
tests/unit/test_story_30_11_batch_parallel.py::TestBatchParallelExecution::test_50_events_all_processed
tests/unit/test_story_30_11_batch_parallel.py::TestBatchParallelExecution::test_neo4j_called_for_each_event
tests/unit/test_story_30_11_batch_parallel.py::TestBatchParallelExecution::test_parallel_faster_than_sequential
tests/unit/test_story_30_11_batch_parallel.py::TestBatchParallelExecution::test_performance_stats_recorded
tests/unit/test_story_30_11_batch_parallel.py::TestBatchPartialFailure::test_episode_ids_only_for_successful
tests/unit/test_story_30_11_batch_parallel.py::TestBatchPartialFailure::test_neo4j_failure_does_not_block_processing
tests/unit/test_story_30_11_batch_parallel.py::TestBatchPartialFailure::test_validation_failure_isolated
tests/unit/test_story_30_11_batch_parallel.py::TestBatchSemaphore::test_concurrency_limited_by_semaphore
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchIdempotency::test_different_events_not_deduplicated
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchIdempotency::test_duplicate_event_detection
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchIdempotency::test_idempotent_writes_across_retries
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchIdempotency::test_large_batch_idempotency
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchPartialFailureRecovery::test_event_ordering_preserved
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchPartialFailureRecovery::test_neo4j_unavailable_fallback
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchPartialFailureRecovery::test_partial_failure_recovery
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchPerformance::test_batch_1000_events_completion
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchPerformance::test_batch_50_events_under_500ms
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchPerformance::test_batch_memory_metrics
tests/unit/test_story_30_13_batch_idempotency.py::TestBatchPerformance::test_concurrent_batch_requests
```

草案 MOCKFIX 节点名的 3 条「修好后必须重看」（`test_neo4j_disconnected_still_stores_in_memory` / `test_neo4j_unavailable_still_processes_to_memory` / `test_neo4j_unavailable_fallback`）**全部仍在 27 内**。

### CARD-RED-ENVDEP（3 · 第十四批）

```
tests/unit/test_agent_service_extraction.py::TestDebugAgentResponseLogging::test_config_has_debug_agent_response_field
tests/unit/test_agent_service_extraction.py::TestDebugAgentResponseLogging::test_extract_with_debug_logging_enabled
tests/unit/test_agent_service_extraction.py::TestDebugAgentResponseLogging::test_extract_without_debug_logging
```

### 部署线（1 · 不进 RED）

```
tests/unit/test_vault_doc_roles.py::test_live_vault_enforce_clean
```

## 三、已不在基线（分诊表有、202 无）—— 45 条，按卡分组 + 原因

`comm -23 b247 b202` = 45 行；按 `rows-final.json`（套用 HIGH-1 改判后）归卡：**C1 33 / MOCKFIX 11 / R 1**。原因逐条对照 Y4-D 验收单 (e) 第一列（skip 43）与第二列（真修 2）：文件级条数 18/8/11/3/2/3 与 (e) 表 `test_memory_service_write_retry` 18 / `test_graphiti_json_dual_write` 8 / `test_story_30_10_idempotency` 9+2 / `test_failure_observability` 3 / `test_qa_38_6_scoring_reliability_extra` 2 / `test_story_38_6_scoring_reliability` 3 **逐文件一致**。这些**不进**任何本批卡的条数；它们的原始缺陷仍在（skip 是掩盖不是修复），退役/恢复归 C1 / MOCKFIX 卡在开工时按 skip reason 另行处置。

### CARD-RED-C1 —— 33 条，全部 skip 掩盖（Y4-D 模块级 `pytestmark` / 类级 skip）

```
tests/unit/test_failure_observability.py::TestMemoryServiceDualWriteFailure::test_dual_write_exception_increments_counter
tests/unit/test_failure_observability.py::TestMemoryServiceDualWriteFailure::test_dual_write_retry_failure_writes_dead_letter
tests/unit/test_failure_observability.py::TestMemoryServiceDualWriteFailure::test_dual_write_timeout_increments_counter
tests/unit/test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_config_flag_enables_dual_write
tests/unit/test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_dual_write_called_after_neo4j_success
tests/unit/test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_json_write_failure_doesnt_affect_main_flow
tests/unit/test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_learning_memory_dataclass_creation
tests/unit/test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_record_temporal_event_dual_write
tests/unit/test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_write_to_graphiti_json_failure_logging
tests/unit/test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_write_to_graphiti_json_success_logging
tests/unit/test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_write_to_graphiti_json_timeout_logging
tests/unit/test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_exception_failure_warning_includes_error_message
tests/unit/test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_exponential_backoff_all_failures
tests/unit/test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_exponential_backoff_delays
tests/unit/test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_mixed_timeout_then_exception_then_success
tests/unit/test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_record_temporal_event_uses_retry_method
tests/unit/test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_retry_creates_new_timestamp_each_attempt
tests/unit/test_memory_service_write_retry.py::TestWriteRetryStrictQA::test_timeout_failure_warning_includes_timeout_suffix
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_all_retries_failed_warning_logging
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_exception_triggers_retry
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_first_success_debug_logging
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_retry_success_logging
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_with_all_optional_params
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_fails_after_all_retries_exception
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_fails_after_all_retries_timeout
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_succeeds_after_one_retry
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_succeeds_after_two_retries
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_write_succeeds_first_attempt
tests/unit/test_memory_service_write_retry.py::TestWriteToGraphitiJsonWithRetry::test_zero_retries_single_attempt
tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestFullCycleIntegration::test_full_cycle_fail_record_recover_merge
tests/unit/test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_malformed_entries_preserved
tests/unit/test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_partial_failure
tests/unit/test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_successful_replay
```

按 skip 范围：`test_memory_service_write_retry` 模块级 18（`TestWriteRetryStrictQA` 7 + `TestWriteToGraphitiJsonWithRetry` 11）/ `test_graphiti_json_dual_write` 模块级 8 / `test_failure_observability::TestMemoryServiceDualWriteFailure` 类级 3 / `test_story_38_6::TestAC3StartupRecovery` 类级 3 / `test_qa_38_6_extra::TestFullCycleIntegration` 类级 1（该类另 1 条归 R，见下）。

### CARD-RED-MOCKFIX —— 11 条 = skip 掩盖 9 + 真修 2

skip 掩盖 9（`test_story_30_10_idempotency` 类级 ×3：`TestEpisodesDedup` 3 / `TestBatchEpisodesDedup` 2 / `TestGraphitiJsonWriteDedup` 4）：

```
tests/unit/test_story_30_10_idempotency.py::TestBatchEpisodesDedup::test_batch_deterministic_ids
tests/unit/test_story_30_10_idempotency.py::TestBatchEpisodesDedup::test_batch_duplicate_submission_dedup
tests/unit/test_story_30_10_idempotency.py::TestEpisodesDedup::test_different_events_both_stored
tests/unit/test_story_30_10_idempotency.py::TestEpisodesDedup::test_duplicate_event_single_episode
tests/unit/test_story_30_10_idempotency.py::TestEpisodesDedup::test_skip_existing_episode_on_dup
tests/unit/test_story_30_10_idempotency.py::TestGraphitiJsonWriteDedup::test_degrades_gracefully_on_search_error
tests/unit/test_story_30_10_idempotency.py::TestGraphitiJsonWriteDedup::test_degrades_when_learning_memory_uninitialized
tests/unit/test_story_30_10_idempotency.py::TestGraphitiJsonWriteDedup::test_skips_write_when_exists
tests/unit/test_story_30_10_idempotency.py::TestGraphitiJsonWriteDedup::test_writes_when_not_exists
```

真修 2（`0fd6d398`→`abc6fb78`，断言 hash 长度 16→32，Y4-D (e) 第二列单跑 PASSED）：

```
tests/unit/test_story_30_10_idempotency.py::TestBatchDeterministicEpisodeId::test_batch_id_format
tests/unit/test_story_30_10_idempotency.py::TestDeterministicEpisodeId::test_id_format
```

> ⚠️ 这 2 条在 `rows-final.json` 里 `card=CARD-RED-MOCKFIX / cat=C2`，但其 247 基线失败身份是 **FAILED `assert 38 == (6 + 16)` / `assert 40 == (8 + 16)`**（hash 长度断言），**不是** `mock_neo4j` 的 setup ERROR ⇒ 分诊时被误并入 MOCKFIX。这正是草案内部「MOCKFIX 节正文写 36 条、§〇.5 写 38 条」的 2 条差额：真正的 `mock_neo4j` 同源族 = 36；36 − 9（skip）= 27 = 202 口径下 MOCKFIX 的实数，27 条失败身份全同一（§一）。

### CARD-RED-R —— 1 条，skip 掩盖（类级 `TestFullCycleIntegration`）

```
tests/unit/test_qa_38_6_scoring_reliability_extra.py::TestFullCycleIntegration::test_full_cycle_recovery_fails_then_merge
```

247 基线失败身份 `assert 0 == 1（history['total']）`，嫌疑真实现回归；被 Y4-D 类级 skip 顺带盖住 ⇒ **一条回归候选从红名单上消失了但并未被确认或修复**，RED-R 开工时须把它从 skip 名单里点名捞回（否则 26 条 bisect 完了这条永远没人看）。

### 另：Y4-D 顺带关掉的 4 条「原本绿」

`test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::{test_config_flag_disables_dual_write, test_fire_and_forget_doesnt_block_return, test_timeout_protection}` + `test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_no_file`。它们**既不在 247 也不在 202**（本来就绿），不进本表任何行；登记为净覆盖损失（裁定 §四），归 C1 卡处置 skip 时一并恢复。

## 四、未分诊 / 与草案矛盾之处

1. **未分诊 = 0**。202 ⊂ 247（`comm -13` 空），`rows-final.json` 覆盖 247 全部 nodeid，故 202 条每条都有唯一 `card`。
2. **草案 §〇.5 与 202 口径的数字差**（只列变化的行）：`CARD-RED-C1` 43 → **10**；`CARD-RED-MOCKFIX` 38 → **27**；`CARD-RED-R` 27 → **26**；合计 247 → **202**。其余 8 行（A1-auth 37 / A1-sentinel 12 / A2 3 / E 9 / C2 66 / NEW 8 / ENVDEP 3 / 部署线 1）不变。「三条必须先读的事实修正」「精确机制」所涉的 A1-auth 37 / A1-sentinel 12 在 202 基线里**一条不少**，草案数字有效。
3. **草案 MOCKFIX 节正文「36 条 / 10 个 `mock_neo4j` fixture」与 §〇.5「38」的矛盾已定位**：差额 2 条 = `test_id_format` / `test_batch_id_format` 被误并入 MOCKFIX（失败身份是 hash 长度断言而非 setup ERROR）；Y4-D 已真修它们。202 口径下 MOCKFIX = 27，草案正文应改「27 条（原 36 条 mock_neo4j 同源族 − 9 条被 Y4-D 类级 skip 掩盖）」。
4. **草案 C1 节的子类分布（① 25 / ② 3 / ③ 14 + 改归 1 = 43）在 202 口径下失效**：① 的 `_write_to_graphiti_json*` AttributeError 族与 ③ 的 TimeoutError 族全部被 skip 掩盖，剩 10 条形态为：`_retry_base_delay` AttributeError 1 / `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 默认值 4 / `app/main.py` 源码文本断言 2 / ② 桩值 0.5/0.1 vs 2.0/1.0 的 3。C1 卡文的「无替代覆盖不许删 / xfail(strict=True) 交接」硬约束现在主要作用于**已被 skip 的 33 条**（它们的 skip reason 直指 `test_episode_worker_retry.py` 作等价覆盖），不是这 10 条。
5. **Codex round-1 HIGH-1 改判未回填到 `rows-final.json`**：5 条（§二 R 节 `test_vault_notes_group_filter` ×4 + `test_strip_whiteboard_removes_admonition_callouts`）的 `card` 字段仍是 `CARD-RED-C2`、`suspect_sha` 为空。本文按草案 §〇.5 口径归 R。若后续脚本直接消费 `rows-final.json` 会把它们算回 C2（66→71 / 26→21）——卡文请引用本文 §二 而不是 json。
6. **RED-R 的 1 条回归候选被 skip 掩盖**（§三 R 节）：`test_full_cycle_recovery_fails_then_merge` 不在 202 内但也没被确认 / 修复；RED-R 卡文应显式把它列为「skip 名单里的第 27 条」，否则「26 条 bisect 全做完」也不等于草案的 27 条闭合。
7. **A1-sentinel 归属漂移风险本轮未发生**：fresh run @da690bf8（`evidence-b13/dir-tests-unit-20260907T123925.txt`）与 202 基线 nodeid 集合逐条相同；但草案「按路径不按 nodeid 修」的警告仍成立，这是单次观察不是不变量。
8. 与 Codex HIGH-2「残余新 9 条无接收卡」的对照：`rows-final.json` 里 `cat=新` 共 12 = NEW 8 + ENVDEP 3 + 部署线 1，Codex 指的 9 = NEW 8 + 部署线 1，闭合表已覆盖，无遗漏。

## 五、命令清单（实际执行；全部只读，未跑 pytest、未写任何仓内文件；`$SP` = 本 session scratchpad）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查

# 分母与口径
wc -l evidence-b12-integ/unit-red-integ-20260906T203713.txt evidence-b12/unit-red-baseline-03ac8bf8.txt   # 202 / 253（247 + 6 行 # 头）
awk '{print $1}' evidence-b12-integ/unit-red-integ-20260906T203713.txt | sort | uniq -c                    # ERROR 29 / FAILED 173
grep -E '^(FAILED|ERROR) tests/' evidence-b12/unit-red-baseline-03ac8bf8.txt | awk '{print $2}' | sed 's/ - .*//' | sort -u > $SP/b247.txt   # 247
awk '{print $2}' evidence-b12-integ/unit-red-integ-20260906T203713.txt | sed 's/ - .*//' | sort -u > $SP/b202.txt                          # 202
comm -23 $SP/b247.txt $SP/b202.txt | tee $SP/gone45.txt | wc -l    # 45
comm -13 $SP/b247.txt $SP/b202.txt | wc -l                          # 0（无新 nodeid）
sed 's/::.*//' $SP/gone45.txt | sort | uniq -c                      # 3/8/18/2/11/3 逐文件 = Y4-D (e) 表

# 分诊表 → 卡（python3，读 evidence-red-triage/rows-final.json；断言 rows nodeid 集合 == b247；
#   套用草案 §〇.5 HIGH-1 改判：test_vault_notes_group_filter.py::* ×4 + test_strip_whiteboard_removes_admonition_callouts → CARD-RED-R；
#   校验套用后 247 口径 = 草案 §〇.5（C2 66 / R 27）；再按 b202 分卡，写 $SP/card-<卡>.txt，各卡 sort 后 wc -l 求和 = 202）
#   附带输出：gone45 按卡 {C1:33, MOCKFIX:11, R:1}；真修 2 条在 247 的 kind/identity（FAILED，hash 长度断言）；各卡 identity/suspect_sha/文件分布

# 5 条改判在 202 内
grep -nE 'test_vault_notes_group_filter|test_strip_whiteboard_removes_admonition_callouts' evidence-b12-integ/unit-red-integ-20260906T203713.txt   # 5 行

# nodeid 在 recon 树是否存在（python3：对 202 条逐条 os.path.isfile(<tree>/backend/<path>) + 正则找 ^\s*class <Cls>\b 与 ^\s*(async )?def <func>\(；参数化去掉 [..]）→ ok=202 / missing_file=0 / missing_sym=0

# 代码树等同
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/batch13-recon
git log -1 --format='%h %s'                                                             # da690bf8
git -c core.quotepath=false diff --stat da690bf8 HEAD -- . ':(exclude)_bmad-output'     # 空，rc=0
git -c core.quotepath=false status --porcelain -- . ':(exclude)_bmad-output' | wc -l    # 0
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev
git -c core.quotepath=false log --format='%h %ad %s' --date=short -4 da690bf8 -- . ':(exclude)_bmad-output'   # 最近含代码 = d209622d（集成修复）
git -c core.quotepath=false diff --stat d209622d da690bf8 -- . ':(exclude)_bmad-output'   # 仅 .claude/rules/card-batch-protocol.md 2 行

# 旁证：主 session 已完成的 fresh run 与 202 对照（只读该存档）
grep -E '^(FAILED|ERROR) tests/' evidence-b13/dir-tests-unit-20260907T123925.txt | awk '{print $2}' | sed 's/ - .*//' | sort -u > $SP/b13run.txt
wc -l < $SP/b13run.txt            # 202
diff $SP/b202.txt $SP/b13run.txt  # 空 ⇒ 逐条相同

# 佐证文档定位
grep -nE 'HIGH-1|test_vault_notes_group_filter|test_strip_whiteboard' codex-review-CARD-RED-TRIAGE.md
sed -n 98,101p 2026-09-06-第十二批复核裁定与待裁决登记.md
sed -n 290,385p ../验收单/UAT-CARD-TOOL-testinfra-salvage-2026-09-06.md
grep -nE 'HIGH-1|改判|回归候选' 2026-09-05-第十二批-tests-unit-红基线分诊-247.md   # 0 命中（改判只在草案 §〇.5）
```
