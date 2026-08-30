#!/bin/bash
# CI 本地等价验证：完全复刻 .github/workflows/test.yml::Run tests 的 env/选择集/flags
# 唯一偏差：--junitxml 落到 scratchpad（避免在被 Codex 审阅的工作树里新建未跟踪 backend/reports/）
set -u
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend || exit 9
SP=/private/tmp/claude-501/-Users-Heishing-Desktop-canvas-canvas-learning-system--claude-worktrees-card-t2-closeout/57e3fd1f-13f5-4166-a291-af272063279b/scratchpad
export DEBUG="true"
export CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
export INTERNAL_API_KEY="ci-test-key-not-a-real-secret"

BASE_LIST=(
  tests/unit/test_kg_relevance_weighted.py
  tests/e2e/test_a11_kg_relevance_e2e.py
  tests/unit/test_mastery_injection_memory_contract.py
  tests/regression/test_board_manifest_contracts.py
  tests/regression/test_rag_stage1_index_contracts.py
  tests/regression/test_reference_config_fallback_contract.py
  tests/regression/test_snapshot_schema_migration_contract.py
  tests/regression/test_immutable_skip_dirs_contract.py
  tests/regression/test_vault_skip_files_scope_contract.py
  tests/regression/test_snapshot_v3_contract.py
  tests/regression/test_all_index_entrypoints_hostile_env.py
  tests/regression/test_tombstone_read_side_contract.py
  tests/regression/test_real_entrypoint_admission.py
  tests/unit/test_vault_admission.py
  tests/unit/test_memory_service_contextvar_leak.py
)
NEW_LIST=(
  tests/regression/test_fsrs_golden_vectors.py
  tests/regression/test_learning_events_schema_contract.py
)

echo "########## A) 现行 CI 清单（15 文件）基线 ##########"
caffeinate -i .venv/bin/python -m pytest "${BASE_LIST[@]}" \
  -m "not integration" -v --tb=short \
  --junitxml=$SP/ci-equiv-base.xml \
  -q --no-header -p no:cacheprovider --override-ini="addopts=" 2>&1 | tail -25
echo "EXIT_A=${PIPESTATUS[0]}"

echo
echo "########## B) 拟议 CI 清单（15+2 文件） ##########"
caffeinate -i .venv/bin/python -m pytest "${BASE_LIST[@]}" "${NEW_LIST[@]}" \
  -m "not integration" -v --tb=short \
  --junitxml=$SP/ci-equiv-new.xml \
  -q --no-header -p no:cacheprovider --override-ini="addopts=" 2>&1 | tail -25
echo "EXIT_B=${PIPESTATUS[0]}"

echo
echo "########## C) 仅两个新文件（隔离归因） ##########"
caffeinate -i .venv/bin/python -m pytest "${NEW_LIST[@]}" \
  -m "not integration" -v --tb=short \
  --junitxml=$SP/ci-equiv-only-new.xml \
  -q --no-header -p no:cacheprovider --override-ini="addopts=" 2>&1 | tail -15
echo "EXIT_C=${PIPESTATUS[0]}"
