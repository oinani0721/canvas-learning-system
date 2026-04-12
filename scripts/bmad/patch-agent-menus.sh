#!/usr/bin/env bash
# patch-agent-menus.sh — Re-inject Canvas custom commands into BMAD agent menus
# Run after: npx bmad-method install (which overwrites agent .md files)
#
# Idempotent: skips injection if custom items already present.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SM_FILE="$PROJECT_ROOT/_bmad/bmm/agents/sm.md"
DEV_FILE="$PROJECT_ROOT/_bmad/bmm/agents/dev.md"

patch_sm() {
  if grep -q 'cmd="SX' "$SM_FILE" 2>/dev/null; then
    echo "[SM] SX already present — skipped"
    return
  fi

  if ! grep -q 'cmd="CS' "$SM_FILE"; then
    echo "[SM] ERROR: CS menu item not found — cannot inject SX"
    return 1
  fi

  sed -i '' '/\[CS\] Context Story:/a\
    <item cmd="SX or fuzzy match on create-story-extended" workflow="{project-root}/_bmad/custom-bmm-ext/workflows/create-story-ext/workflow.yaml">[SX] Create Story Extended: 扩展版 Story（含 UAT Script + Automated Checkpoints + User Feedback）— 替代 CS</item>' "$SM_FILE"

  echo "[SM] Injected SX after CS"
}

patch_dev() {
  if grep -q 'cmd="AF' "$DEV_FILE" 2>/dev/null; then
    echo "[Dev] AF already present — skipped"
    return
  fi

  if ! grep -q 'cmd="CR' "$DEV_FILE"; then
    echo "[Dev] ERROR: CR menu item not found — cannot inject AF/LB"
    return 1
  fi

  sed -i '' '/\[CR\] Code Review:/a\
    <item cmd="AF or fuzzy match on apply-feedback" workflow="{project-root}/_bmad/custom-bmm-ext/workflows/apply-feedback/workflow.yaml">[AF] Apply Feedback: 按 intent 分发用户批注（minor 直改 / moderate 调 correct-course / major 升级）</item>\
    <item cmd="LB or fuzzy match on locate-bug" workflow="{project-root}/_bmad/custom-bmm-ext/workflows/locate-by-bug/workflow.yaml">[LB] Locate Bug: 从 BugID 追溯到 DecisionID → Story → 代码文件 + UAT 复现步骤</item>' "$DEV_FILE"

  echo "[Dev] Injected AF + LB after CR"
}

echo "=== Canvas BMAD Agent Menu Patch ==="
echo "Project: $PROJECT_ROOT"
echo ""

patch_sm
patch_dev

echo ""
echo "Done. Verify with: grep -n 'SX\|AF\|LB' $SM_FILE $DEV_FILE"
