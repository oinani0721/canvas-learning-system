# g32b 全量杀灭表（138 条）— CARD-G3-2c-D

> 来源 `evidence-g32b/g32b-full-run.txt`（单进程串行一次跑完，`nohup`）。
> **KILLED 134 / SURVIVED 0 / ANCHOR-ERROR 4，合计 138**。
> 判定口径：g32b 自身的 `rc==1 且指定门红`；ANCHOR-ERROR = 锚点命中数 ≠ 1，**变异未写入 ⇒ 该条什么都没测**。
>
> ⛔ **脚本整体判定是 `变异验证 FAIL:`**（`g32b-full-run.txt:191`），不是 PASS。
> FAIL 由 7 行构成：上表的 4 条 ANCHOR-ERROR，加 3 行**层声明**问题——
> `M100-no-tri-instant-binding`（日志 `:174`）与 `M151-exam-board-bare-json-in-yaml`（`:184`）
> 报「声明为 complete 但变异体单独即可杀 ⇒ 层是多余的」，以及 `M157` 的空变异对照锚点异常。
> **层声明过度 ≠ 生产防线缺陷**（Codex 独立复核确认），但它是脚本自检的真实输出，
> 不能只看 134 这个数字。两条均**移交**，本卡不改（硬边界：不改 g32b 判据/定义）。

| # | tag | 绑定门 | 判定 | 失败身份 / 备注 |
|---|---|---|---|---|
| 1 | `M1-R1-candidate-spread` | `test_r1_unknown_durable_payload_key_conflicts` | **KILLED** | ======================== 1 failed, 10 warnings in 1.17s ============== |
| 2 | `M2b-R2-drop-utc-offset-check` | `test_r2_non_whole_second_durable_review_time_fail_closed` | **KILLED** | ======================== 1 failed, 10 warnings in 1.82s ============== |
| 3 | `M3-R3-attempt-uses-tip` | `test_r3_historical_event_replay_is_noop_not_conflict` | **KILLED** | ======================= 1 failed, 10 warnings in 11.90s ============== |
| 4 | `M4-R4-normal-path-uses-payload-ts` | `test_r4_recovery_byte_identical_with_idle_and_a3_bump` | **KILLED** | ======================== 1 failed, 10 warnings in 2.07s ============== |
| 5 | `M5-R5-drop-rating-consistency` | `test_r5_inconsistent_scored_rating_rejected_before_apply` | **KILLED** | ======================== 1 failed, 10 warnings in 1.03s ============== |
| 6 | `M7-R6-schema-drops-owner-clause` | `test_r6_schema_declares_identity_key_integrity_owner` | **KILLED** | ======================== 1 failed, 10 warnings in 0.70s ============== |
| 7 | `M8-6cell-cell4-allow-recovery` | `test_six_cell_state_machine_closed` | **KILLED** | ======================== 1 failed, 10 warnings in 1.85s ============== |
| 8 | `M9-6cell-cell2-drop-orphan-noop` | `test_six_cell_state_machine_closed` | **KILLED** | ======================== 1 failed, 10 warnings in 1.27s ============== |
| 9 | `M10-R2-value-not-literal` | `test_r2_non_whole_second_durable_review_time_fail_closed` | **KILLED** | ======================== 1 failed, 10 warnings in 0.88s ============== |
| 10 | `M11-N1-drop-out-of-order-semantic-gate` | `test_round1_followups_n1_to_n5` | **KILLED** | ======================== 1 failed, 10 warnings in 0.93s ============== |
| 11 | `M12-N1-drop-out-of-order-shape-gate` | `test_round1_followups_n1_to_n5` | **KILLED** | ======================== 1 failed, 10 warnings in 1.03s ============== |
| 12 | `M14-N3-drop-duplicate-key-hook` | `test_round1_followups_n1_to_n5` | **KILLED** | ======================== 1 failed, 10 warnings in 2.32s ============== |
| 13 | `M16-N5-hard-compute-attempt-across-pending` | `test_round1_followups_n1_to_n5` | **KILLED** | ======================== 1 failed, 10 warnings in 2.56s ============== |
| 14 | `M17-N1-schema-drops-writer-side-clause` | `test_r6_schema_declares_identity_key_integrity_owner` | **KILLED** | ======================== 1 failed, 10 warnings in 0.72s ============== |
| 15 | `M19-B1-drop-rating-completeness` | `test_internal_audit_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.16s ============== |
| 16 | `M20-B1-drop-gradenorm-completeness` | `test_internal_audit_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.72s ============== |
| 17 | `M21-B2-drop-attempt-sync-on-replay` | `test_internal_audit_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 2.47s ============== |
| 18 | `M23-C1-drop-event-type-gate` | `test_round11b_c1_event_type_narrow` | **KILLED** | ======================== 1 failed, 10 warnings in 1.04s ============== |
| 19 | `M24-C1-drop-concept-id-gate` | `test_round11b_c1_concept_id_narrow` | **KILLED** | ======================== 1 failed, 10 warnings in 1.08s ============== |
| 20 | `M25-C1-drop-vault-id-gate` | `test_round11b_c1_vault_id_narrow` | **KILLED** | ======================== 1 failed, 10 warnings in 1.07s ============== |
| 21 | `M26-C2-drop-eid-whitespace-gate` | `test_internal_audit_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 6.20s ============== |
| 22 | `M28-C4-mastery-uses-unrounded-gn` | `test_internal_audit_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 7.31s ============== |
| 23 | `M6b-R7-tail-ignores-lf-state` | `test_r7_corrupt_tail_line_with_lf_is_not_truncation` | **KILLED** | ======================== 1 failed, 10 warnings in 0.94s ============== |
| 24 | `M13b-N2-text-mode-read` | `test_round1_followups_n1_to_n5` | **KILLED** | ======================== 1 failed, 10 warnings in 1.99s ============== |
| 25 | `M15b-N4-decode-with-replace` | `test_round1_followups_n1_to_n5` | **KILLED** | ======================== 1 failed, 10 warnings in 2.20s ============== |
| 26 | `M18b-R7blank-judge-file-end-not-last-line` | `test_round2_lead_followups` | **KILLED** | ======================== 1 failed, 10 warnings in 1.22s ============== |
| 27 | `M29-R3-drop-event-version-gate` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 0.97s ============== |
| 28 | `M30-R3-drop-two-instant-consistency` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.03s ============== |
| 29 | `M31-R3-drop-attempt-required` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 3.19s ============== |
| 30 | `M32-R3-drop-payload-object-gate` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 3.83s ============== |
| 31 | `M33-R3-merge-recovery-and-append` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 3.96s ============== |
| 32 | `M34-R3-drop-routing-envelope-gate` | `test_round2_lead_followups` | **KILLED** | ======================== 1 failed, 10 warnings in 2.13s ============== |
| 33 | `M35-R3-effective-at-over-strict` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 2.27s ============== |
| 34 | `M38b-attempt-expectation-masked-by-max` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 8.56s ============== |
| 35 | `M43-f1-evaluated-after-calibration-replay` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.19s ============== |
| 36 | `M44-drop-looks-like-review-ext` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 8.89s ============== |
| 37 | `M45-allow-dup-and-foreign-same-round` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 9.38s ============== |
| 38 | `M46-yaml-single-quote-escape` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 9.61s ============== |
| 39 | `M39-attempt-regex-rejects-single-quote` | `test_round3_findings` | **KILLED** | ======================= 1 failed, 10 warnings in 10.10s ============== |
| 40 | `M42-late-unmarked-row-silently-skipped` | `test_round2_lead_followups` | **KILLED** | ======================== 1 failed, 10 warnings in 4.32s ============== |
| 41 | `M36b-replay-drops-mastery` | `test_round3_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.44s ============== |
| 42 | `M37c-replay-includes-dup-double-eats-ema` | `test_degraded_legacy_retry_restores_fsrs_without_double_ema` | **KILLED** | ======================== 1 failed, 10 warnings in 1.16s ============== |
| 43 | `M47-skip-validator-record-check` | `test_round4_writer_validator_verdict_parity` | **KILLED** | ======================== 1 failed, 10 warnings in 3.04s ============== |
| 44 | `M48-attribution-check-after-payload-skip` | `test_round4_writer_validator_verdict_parity` | **KILLED** | ======================== 1 failed, 10 warnings in 4.55s ============== |
| 45 | `M49-event-version-accepts-bool` | `test_round11b_parity_event_version_bool_narrow` | **KILLED** | ======================== 1 failed, 10 warnings in 1.38s ============== |
| 46 | `M50-non-object-line-silently-skipped` | `test_round11b_parity_toplevel_non_object_narrow` | **KILLED** | ======================== 1 failed, 10 warnings in 1.07s ============== |
| 47 | `M51-line-strip-washes-nonjson-whitespace` | `test_round4_writer_validator_verdict_parity` | **KILLED** | ======================== 1 failed, 10 warnings in 1.37s ============== |
| 48 | `M52-calibration-strips-quiz-prefix` | `test_round5_calibration_key_prefix_collision` | **KILLED** | ======================== 1 failed, 10 warnings in 1.59s ============== |
| 49 | `M53-f1-query-strips-prefix-only` | `test_round5_calibration_key_prefix_collision` | **KILLED** | ======================== 1 failed, 10 warnings in 1.95s ============== |
| 50 | `M54-f1-uses-bare-eid` | `test_round5_calibration_key_prefix_collision` | **KILLED** | ======================== 1 failed, 10 warnings in 1.54s ============== |
| 51 | `M56-full-validation-after-branching` | `test_round5_routing_order_and_input_literal` | **KILLED** | ======================== 1 failed, 10 warnings in 1.48s ============== |
| 52 | `M57-validate-without-golden-manifest` | `test_round5_routing_order_and_input_literal` | **KILLED** | ======================== 1 failed, 10 warnings in 1.91s ============== |
| 53 | `M58-input-ts-not-literally-checked` | `test_round5_routing_order_and_input_literal` | **KILLED** | ======================== 1 failed, 10 warnings in 1.92s ============== |
| 54 | `M59-ordinal-ignores-legacy-scored-rows` | `test_round5_legacy_scored_rows_break_ordinal_proof` | **KILLED** | ======================== 1 failed, 10 warnings in 1.43s ============== |
| 55 | `M60-normal-path-stores-bare-eid` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.03s ============== |
| 56 | `M61-durable-eid-whitespace-not-scanned` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.42s ============== |
| 57 | `M62-node-id-type-only` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.49s ============== |
| 58 | `M63-ts-match-not-fullmatch` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.93s ============== |
| 59 | `M64-dumps-allows-nan` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.96s ============== |
| 60 | `M65-loads-allows-nan` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 2.30s ============== |
| 61 | `M66-legacy-same-id-rejected` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 2.88s ============== |
| 62 | `M67-inline-calibration-not-normalized` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 3.15s ============== |
| 63 | `M68-blank-lines-tolerated` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 3.58s ============== |
| 64 | `M69-bom-tolerated` | `test_round6_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 3.87s ============== |
| 65 | `M70-ordinal-w-only-not-calibration` | `test_round6_ordinal_evidence` | **KILLED** | ======================== 1 failed, 10 warnings in 1.54s ============== |
| 66 | `M71-ignore-provable-legacy-ordinal` | `test_round6_ordinal_evidence` | **KILLED** | ======================== 1 failed, 10 warnings in 2.21s ============== |
| 67 | `M73-late-scan-after-early-exit` | `test_round7_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.68s ============== |
| 68 | `M74-candidate-copies-durable-rt` | `test_round7_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 2.11s ============== |
| 69 | `M75-w-fallback-restored` | `test_round11b_no_w_fallback_narrow` | **KILLED** | ======================== 1 failed, 10 warnings in 1.25s ============== |
| 70 | `M76-self-node-id-gate-dropped` | `test_round7_ordinal_gap_and_self_node_id` | **KILLED** | ======================== 1 failed, 10 warnings in 0.92s ============== |
| 71 | `M77-ordinal-fixed-minus-one` | `test_round7_ordinal_gap_and_self_node_id` | **KILLED** | ======================== 1 failed, 10 warnings in 1.66s ============== |
| 72 | `M78-first-write-uses-run-ts` | `test_round11b_fsrs_uses_stable_business_time` | **KILLED** | ======================== 1 failed, 10 warnings in 0.97s ============== |
| 73 | `M79-missing-scored-at-falls-back` | `test_round8_stable_scored_at` | **KILLED** | ======================== 1 failed, 10 warnings in 2.14s ============== |
| 74 | `M80-envelope-compares-adopted-rt` | `test_round8_stable_scored_at` | **KILLED** | ======================== 1 failed, 10 warnings in 1.85s ============== |
| 75 | `M81-legacy-out-of-order-honored` | `test_round8_high_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.61s ============== |
| 76 | `M82-calibration-header-no-comment` | `test_round8_high_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 2.88s ============== |
| 77 | `M83-whitespace-id-gate-global` | `test_round8_high_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 3.43s ============== |
| 78 | `M84-cross-node-id-collision-ignored` | `test_round9_identity_and_self_check` | **KILLED** | ======================== 1 failed, 10 warnings in 0.96s ============== |
| 79 | `M85-no-producer-self-check` | `test_round9_identity_and_self_check` | **KILLED** | ======================== 1 failed, 10 warnings in 1.16s ============== |
| 80 | `M86-f1-regex-not-yaml` | `test_round9_yaml_calibration_forms` | **KILLED** | ======================== 1 failed, 10 warnings in 2.45s ============== |
| 81 | `M88-degraded-uses-run-ts` | `test_round8_stable_scored_at` | **KILLED** | ======================== 1 failed, 10 warnings in 0.93s ============== |
| 82 | `M89-receipt-drops-scored-at` | `test_round9_structured_receipt` | **KILLED** | ======================== 1 failed, 10 warnings in 1.11s ============== |
| 83 | `M90-receipt-drops-attempt` | `test_round9_structured_receipt` | **KILLED** | ======================== 1 failed, 10 warnings in 1.09s ============== |
| 84 | `M91-f1-only-unconditional-noop` | `test_round9_structured_receipt` | **KILLED** | ======================== 1 failed, 10 warnings in 1.58s ============== |
| 85 | `M94-routing-raw-compare` | `test_round10_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 1.03s ============== |
| 86 | `M95-receipt-skips-abandoned` | `test_round12_abandoned_isolated_from_grade` | **KILLED** | ======================== 1 failed, 10 warnings in 1.43s ============== |
| 87 | `M96-adopted-time-unbound` | `test_round10_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 2.45s ============== |
| 88 | `M97-writeback-regex-only` | `test_round10_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 2.89s ============== |
| 89 | `M98-no-pre-append-dry-run` | `test_round10_findings` | **KILLED** | ======================== 1 failed, 10 warnings in 5.51s ============== |
| 90 | `M99-f1only-skips-fact-check` | `test_round11_unified_resolver` | **KILLED** | ======================== 1 failed, 10 warnings in 1.74s ============== |
| 91 | `M100-no-tri-instant-binding` | `test_round17_tri_instant_binding_narrow` | **KILLED** | ======================== 1 failed, 10 warnings in 1.13s ============== |  ⚠️ **另有层声明过度（脚本自检报「层多余」）—— 移交**
| 92 | `M102-receipt-attempt-type-only` | `test_round11_unified_resolver` | **KILLED** | ======================== 1 failed, 10 warnings in 2.78s ============== |
| 93 | `M103-receipt-ts-no-literal-gate` | `test_round11_unified_resolver` | **KILLED** | ======================== 1 failed, 10 warnings in 2.94s ============== |
| 94 | `M104-writeback-guess-by-text` | `test_round11_writeback_by_parse_result` | **KILLED** | ======================== 1 failed, 10 warnings in 1.46s ============== |
| 95 | `M110-reinline-duplicate-lookup` | `test_round11b_single_source_lookup` | **KILLED** | ======================== 1 failed, 10 warnings in 0.69s ============== |
| 96 | `M111-shared-impl-not-reused` | `test_round11b_single_source_lookup` | **KILLED** | ======================== 1 failed, 10 warnings in 0.71s ============== |
| 97 | `M112-compat-empty-source-rejects` | `test_round11b_both_paths_still_behave` | **KILLED** | ======================== 1 failed, 10 warnings in 1.07s ============== |
| 98 | `M113-facts-list-not-frozen` | `test_round12_facts_list_is_frozen` | **KILLED** | ======================== 1 failed, 10 warnings in 0.70s ============== |
| 99 | `M114-f1only-drops-exam-board` | `test_round12_b2_exam_board_in_facts` | **KILLED** | ======================== 1 failed, 10 warnings in 1.84s ============== |
| 100 | `M115-late-scan-presence-only` | `test_round12_b3_late_scan_checks_facts` | **KILLED** | ======================== 1 failed, 10 warnings in 1.87s ============== |
| 101 | `M116-receipt-no-provenance` | `test_round12_b1_receipt_provenance` | **KILLED** | ======================== 1 failed, 10 warnings in 0.97s ============== |
| 102 | `M117-empty-source-skips-provenance` | `test_round12_b1_receipt_provenance` | **KILLED** | ======================== 1 failed, 10 warnings in 1.16s ============== |
| 103 | `M118-empty-eid-allowed` | `test_round12_empty_eid_rejected_at_entry` | **KILLED** | ======================== 1 failed, 10 warnings in 0.94s ============== |
| 104 | `M119-crash-window-adopted-time-unproven` | `test_round12_high2_adopted_time_in_crash_window` | **KILLED** | ======================== 1 failed, 10 warnings in 1.25s ============== |
| 105 | `M120-legacy-row-generic-reason` | `test_round12_high3_legacy_row_missing_scored_at_is_actionable` | **KILLED** | ======================== 1 failed, 10 warnings in 2.32s ============== |
| 106 | `M121-consumer-rounds-grade` | `test_round13_consumer_must_not_reshape_values` | **KILLED** | ======================== 1 failed, 10 warnings in 1.49s ============== |
| 107 | `M122-consumer-coerces-board` | `test_round13_consumer_must_not_reshape_values` | **KILLED** | ======================== 1 failed, 10 warnings in 1.99s ============== |
| 108 | `M123-adopted-time-literal-compare` | `test_round13_adopted_time_recomputed_not_compared_literally` | **KILLED** | ======================== 1 failed, 10 warnings in 1.35s ============== |
| 109 | `M124-crash-window-only-when-w-empty` | `test_round13_adopted_time_recomputed_not_compared_literally` | **KILLED** | ======================== 1 failed, 10 warnings in 1.91s ============== |
| 110 | `M125-id-form-authorizes-bare-fallback` | `test_round13_id_form_only_proves_exact_hit` | **KILLED** | ======================== 1 failed, 10 warnings in 1.11s ============== |
| 111 | `M126-f1only-no-successor-discount` | `test_round13_f1only_ordinal_discounts_successors` | **KILLED** | ======================== 1 failed, 10 warnings in 1.53s ============== |
| 112 | `M127-facts-python-equality` | `test_round14_facts_compare_is_type_sensitive` | **KILLED** | ======================== 1 failed, 10 warnings in 1.06s ============== |
| 113 | `M128-id-form-not-at-candidate-stage` | `test_round14_id_form_checked_at_candidate_stage` | **KILLED** | ======================== 1 failed, 10 warnings in 1.23s ============== |
| 114 | `M129-missing-scored-at-warn-only` | `test_round14_missing_scored_at_is_fail_closed` | **KILLED** | ======================== 1 failed, 10 warnings in 1.01s ============== |
| 115 | `M130-pending-adopted-time-unproven` | `test_round14_every_pending_proves_adopted_time` | **KILLED** | ======================== 1 failed, 10 warnings in 1.28s ============== |
| 116 | `M132-candidate-always-rounded` | `test_round14_legacy_precision_identity` | **KILLED** | ======================== 1 failed, 10 warnings in 1.30s ============== |
| 117 | `M135-scored-at-not-in-ext-detection` | `test_round15_scored_at_in_ext_detection` | **KILLED** | ======================== 1 failed, 10 warnings in 1.15s ============== |
| 118 | `M136-w-coverage-as-applied-proof` | `test_round15_event_level_fsrs_applied` | **KILLED** | ======================== 1 failed, 10 warnings in 1.28s ============== |
| 119 | `M137-receipt-no-applied-flag` | `test_round15_event_level_fsrs_applied` | **KILLED** | ======================== 1 failed, 10 warnings in 0.91s ============== |
| 120 | `M138-board-string-only` | `test_round15_board_no_self_produced_rejection` | **KILLED** | ======================== 1 failed, 10 warnings in 1.19s ============== |
| 121 | `M139-source-lookup-both-ways` | `test_round15_source_lookup_respects_candidate_kind` | **KILLED** | ======================== 1 failed, 10 warnings in 1.19s ============== |
| 122 | `M140-bare-collision-no-own-judge` | `test_round15_bare_collision_has_own_judge` | **KILLED** | ======================== 1 failed, 10 warnings in 1.20s ============== |
| 123 | `M142-dup-uses-global-w` | `test_round16_fsrs_applied_across_all_branches` | **ANCHOR-ERROR** | 变异锚点命中 0 次 @ SKILL.md |
| 124 | `M143-missing-applied-flag-tolerated` | `test_round16_fsrs_applied_across_all_branches` | **ANCHOR-ERROR** | 变异锚点命中 0 次 @ SKILL.md |
| 125 | `M144-false-plus-w-not-contradiction` | `test_round16_fsrs_applied_across_all_branches` | **KILLED** | ======================== 1 failed, 10 warnings in 2.02s ============== |
| 126 | `M145-recovery-does-not-promote-flag` | `test_round16_fsrs_applied_across_all_branches` | **ANCHOR-ERROR** | 变异锚点命中 0 次 @ SKILL.md |
| 127 | `M146-canon-num-precision-loss` | `test_round16_canonical_tree_type_faithful` | **KILLED** | ======================== 1 failed, 10 warnings in 1.11s ============== |
| 128 | `M148-unmarked-exact-single-source` | `test_round16_unmarked_exact_enumerates_both_sources` | **KILLED** | ======================== 1 failed, 10 warnings in 1.23s ============== |
| 129 | `M149-adopted-two-values` | `test_round16_same_instant_rows_rejected_per_a3` | **KILLED** | ======================== 1 failed, 10 warnings in 1.39s ============== |
| 130 | `M150-all-ledger-ids-coerce-str` | `test_round16_foreign_nonstr_event_id_does_not_block` | **KILLED** | ======================== 1 failed, 10 warnings in 1.19s ============== |
| 131 | `M151-exam-board-bare-json-in-yaml` | `test_round16_exam_board_roundtrips_through_yaml` | **KILLED** | ======================== 1 failed, 10 warnings in 0.95s ============== |  ⚠️ **另有层声明过度（脚本自检报「层多余」）—— 移交**
| 132 | `M152-f1-ignores-write-order-anchor` | `test_round16_f1_only_uses_persisted_write_order_anchor` | **KILLED** | ======================== 1 failed, 10 warnings in 1.27s ============== |
| 133 | `M153-legacy-cursor-skips-ambiguity-proof` | `test_round16_legacy_receipt_without_anchor_says_unprovable` | **KILLED** | ======================== 1 failed, 10 warnings in 1.11s ============== |
| 134 | `M155-board-form-ignored` | `test_round17_legacy_receipt_without_board_form_still_read` | **KILLED** | ======================== 1 failed, 10 warnings in 1.09s ============== |
| 135 | `M156-anchor-miss-is-hard-error` | `test_round17_anchor_is_preferred_not_sole_evidence` | **KILLED** | ======================== 1 failed, 10 warnings in 1.57s ============== |
| 136 | `M157-anchor-direction-unchecked` | `test_round17_anchor_direction_is_verified` | **ANCHOR-ERROR** | 同层锚点命中 0 次 @ SKILL.md |
| 137 | `M158-fsrs-applied-truthiness` | `test_round17_fsrs_applied_must_be_strict_bool` | **KILLED** | ======================== 1 failed, 10 warnings in 1.11s ============== |
| 138 | `M161-foreign-no-credential-promotion` | `test_round17_foreign_degraded_recovery_converges` | **KILLED** | ======================== 1 failed, 10 warnings in 1.52s ============== |
