#!/bin/bash
#
# verify-a4-fix.sh — End-to-end verification of the A4 verification_service fix
#
# Purpose:
#   Verify that all 5 A4 hardening fixes are actually wired up and working
#   on a running backend (not just passing pytest mocks):
#
#     1. Health check                 — backend is reachable on :8001
#     2. A4-Q1 session start          — POST /session/start returns 200 + first_question
#     3. Phase 17.1 fail-closed       — submitting noise returns degraded=true under mock mode
#     4. Phase 17.2 path traversal    — "../../etc/passwd" resolves to sentinel, NOT /etc/passwd
#     5. A4-Q2 Graphiti 3-path        — backend log contains evidence of Graphiti fetches
#
# Prerequisites:
#   - Backend running on http://localhost:8001 (uvicorn)
#   - For Phase 17.1 fail-closed test: export USE_MOCK_VERIFICATION=true BEFORE starting backend,
#     OR run against a backend where scoring-agent is unconfigured (so all scoring fails gracefully).
#   - A canvas file exists in CANVAS_BASE_PATH (default: ./笔记库). If not, the script creates one.
#
# Usage:
#   ./backend/scripts/verify-a4-fix.sh                  # Run against http://localhost:8001
#   BACKEND_URL=http://localhost:8002 ./verify-a4-fix.sh
#   CANVAS_NAME=MyTest ./verify-a4-fix.sh               # Use specific canvas
#
# Exit codes:
#   0 = all 5 checks passed (or skipped with a warning)
#   N = N checks failed
#
# See: docs/runbooks/a4-verification.md
# Related: openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/
#

set -e
cd "$(dirname "$0")/.."  # cd to backend/

BACKEND_URL="${BACKEND_URL:-http://localhost:8001}"
CANVAS_NAME="${CANVAS_NAME:-a4_verification_test}"
CANVAS_BASE_PATH="${CANVAS_BASE_PATH:-$(cd .. && pwd)/笔记库}"
CANVAS_FILE="${CANVAS_BASE_PATH}/${CANVAS_NAME}.canvas"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

pass() { echo -e "${GREEN}✅ PASS${RESET}: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail() { echo -e "${RED}❌ FAIL${RESET}: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }
warn() { echo -e "${YELLOW}⚠️  WARN${RESET}: $1"; WARN_COUNT=$((WARN_COUNT+1)); }
info() { echo -e "${BLUE}ℹ️  INFO${RESET}: $1"; }
section() { echo -e "\n${BLUE}=== $1 ===${RESET}"; }

# Check dependencies
command -v curl >/dev/null 2>&1 || { echo "ERROR: curl is required"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required (brew install jq)"; exit 1; }

echo "=========================================="
echo "A4 Verification Script (FR-KG-04 Hardening)"
echo "Backend: $BACKEND_URL"
echo "Canvas base path: $CANVAS_BASE_PATH"
echo "Canvas name: $CANVAS_NAME"
echo "=========================================="

# ═══════════════════════════════════════════════════════════════════════════
# Setup: ensure test canvas file exists
# ═══════════════════════════════════════════════════════════════════════════
section "Setup: Test Canvas"

if [ ! -d "$CANVAS_BASE_PATH" ]; then
    info "Canvas base path does not exist — creating: $CANVAS_BASE_PATH"
    mkdir -p "$CANVAS_BASE_PATH"
fi

if [ ! -f "$CANVAS_FILE" ]; then
    info "Test canvas not found — creating: $CANVAS_FILE"
    cat > "$CANVAS_FILE" <<'CANVAS_EOF'
{
  "nodes": [
    {
      "id": "test_node_1",
      "type": "text",
      "text": "BKT 模型",
      "x": 0,
      "y": 0,
      "width": 200,
      "height": 60,
      "color": "3"
    },
    {
      "id": "test_node_2",
      "type": "text",
      "text": "FSRS 遗忘曲线",
      "x": 300,
      "y": 0,
      "width": 200,
      "height": 60,
      "color": "6"
    }
  ],
  "edges": []
}
CANVAS_EOF
    pass "Created test canvas at $CANVAS_FILE"
    CLEANUP_CANVAS=1
else
    info "Test canvas already exists: $CANVAS_FILE"
    CLEANUP_CANVAS=0
fi

# ═══════════════════════════════════════════════════════════════════════════
# Check 1: Health check
# ═══════════════════════════════════════════════════════════════════════════
section "Check 1: Backend Health"

HEALTH_JSON=$(curl -s -f -m 5 "$BACKEND_URL/api/v1/health" || echo "CURL_FAILED")

if [ "$HEALTH_JSON" = "CURL_FAILED" ]; then
    fail "Health endpoint unreachable at $BACKEND_URL/api/v1/health"
    echo ""
    echo "Start backend first:"
    echo "  cd backend && .venv/bin/uvicorn app.main:app --port 8001 --reload"
    echo ""
    exit 1
fi

HEALTH_STATUS=$(echo "$HEALTH_JSON" | jq -r '.data.status // .status // "unknown"' 2>/dev/null || echo "unknown")
if [ "$HEALTH_STATUS" = "healthy" ] || [ "$HEALTH_STATUS" = "degraded" ]; then
    pass "Backend is reachable (status=$HEALTH_STATUS)"
else
    fail "Backend health=$HEALTH_STATUS (expected healthy or degraded)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Check 2: A4-Q1 — Session start returns first question
# ═══════════════════════════════════════════════════════════════════════════
section "Check 2: A4-Q1 Session Start (normal path)"

START_PAYLOAD="{\"canvas_name\":\"${CANVAS_NAME}\",\"include_mastered\":true}"
START_RESPONSE=$(curl -s -m 30 -X POST "$BACKEND_URL/api/v1/review/session/start" \
    -H "Content-Type: application/json" \
    -d "$START_PAYLOAD" || echo "CURL_FAILED")

if [ "$START_RESPONSE" = "CURL_FAILED" ]; then
    fail "Session start request failed (network error or 5xx)"
    SESSION_ID=""
else
    SESSION_ID=$(echo "$START_RESPONSE" | jq -r '.data.session_id // .session_id // empty')
    FIRST_Q=$(echo "$START_RESPONSE" | jq -r '.data.first_question // .first_question // empty')
    TOTAL=$(echo "$START_RESPONSE" | jq -r '.data.total_concepts // .total_concepts // 0')

    if [ -n "$SESSION_ID" ] && [ -n "$FIRST_Q" ] && [ "$TOTAL" -gt 0 ]; then
        pass "Session started: id=${SESSION_ID:0:8}..., concepts=$TOTAL"
        info "First question: ${FIRST_Q:0:80}..."
    else
        fail "Session start response missing required fields"
        echo "Raw response: $START_RESPONSE" | head -c 300
        echo ""
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Check 3: Phase 17.1 — Submit noise, expect fail-closed contract fields
# ═══════════════════════════════════════════════════════════════════════════
section "Check 3: Phase 17.1 Fail-Closed Contract"

if [ -z "$SESSION_ID" ]; then
    warn "Skipping — no valid session_id from Check 2"
else
    # Submit 1000 chars of adversarial noise
    NOISE=$(printf 'x%.0s' $(seq 1 1000))
    ANSWER_PAYLOAD="{\"user_answer\":\"$NOISE\"}"

    ANSWER_RESPONSE=$(curl -s -m 30 -X POST "$BACKEND_URL/api/v1/review/session/$SESSION_ID/answer" \
        -H "Content-Type: application/json" \
        -d "$ANSWER_PAYLOAD" || echo "CURL_FAILED")

    if [ "$ANSWER_RESPONSE" = "CURL_FAILED" ]; then
        fail "Submit answer request failed"
    else
        QUALITY=$(echo "$ANSWER_RESPONSE" | jq -r '.data.quality // .quality // "missing"')
        SCORE=$(echo "$ANSWER_RESPONSE" | jq -r '.data.score // .score // -1')
        DEGRADED=$(echo "$ANSWER_RESPONSE" | jq -r '.data.degraded // .degraded // "missing"')
        WARNING=$(echo "$ANSWER_RESPONSE" | jq -r '.data.degraded_warning // .degraded_warning // empty')

        # API contract check: ALL fields must be present
        CONTRACT_OK=1
        [ "$QUALITY" = "missing" ] && { fail "Response missing 'quality' field"; CONTRACT_OK=0; }
        [ "$SCORE" = "-1" ] && { fail "Response missing 'score' field"; CONTRACT_OK=0; }
        [ "$DEGRADED" = "missing" ] && { fail "Response missing 'degraded' field"; CONTRACT_OK=0; }

        if [ $CONTRACT_OK -eq 1 ]; then
            pass "API contract OK (quality=$QUALITY, score=$SCORE, degraded=$DEGRADED)"

            # Semantic check: is fail-closed behavior actually triggered?
            if [ "$DEGRADED" = "true" ]; then
                if [ "$QUALITY" = "unknown" ] && [ "$SCORE" = "0" ]; then
                    pass "Phase 17.1 fail-closed triggered: quality=unknown, score=0"
                    if [ -n "$WARNING" ]; then
                        info "degraded_warning: $WARNING"
                    else
                        warn "degraded=true but degraded_warning is empty"
                    fi
                else
                    fail "degraded=true but quality=$QUALITY, score=$SCORE (expected unknown/0)"
                fi
            else
                warn "degraded=false — real scoring agent succeeded on 1000-char noise"
                warn "To test Phase 17.1, restart backend with USE_MOCK_VERIFICATION=true"
                info "Contract itself is OK (all fields present), just not triggered this run"
            fi
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Check 4: Phase 17.2 — Path traversal hardening
# ═══════════════════════════════════════════════════════════════════════════
section "Check 4: Phase 17.2 Path Traversal Hardening"

# Try to start a session with "../../etc/passwd" as canvas_name.
# Expected behavior (Phase 17.2):
#   - _resolve_safe_canvas_path rejects the traversal → returns None
#   - _do_extract_concepts falls back to ["默认概念"]
#   - Session starts with 1 sentinel concept, OR endpoint returns a safe error
# NOT acceptable:
#   - Any indication that /etc/passwd was actually read

EVIL_PAYLOAD='{"canvas_name":"../../etc/passwd","include_mastered":true}'
EVIL_RESPONSE=$(curl -s -m 10 -X POST "$BACKEND_URL/api/v1/review/session/start" \
    -H "Content-Type: application/json" \
    -d "$EVIL_PAYLOAD" || echo "CURL_FAILED")

if [ "$EVIL_RESPONSE" = "CURL_FAILED" ]; then
    fail "Path traversal test request failed"
else
    # Check 1: response must NOT contain suspicious content from /etc/passwd
    if echo "$EVIL_RESPONSE" | grep -qE 'root:|daemon:|/bin/bash|/bin/sh'; then
        fail "CRITICAL: /etc/passwd content leaked in response!"
        echo "$EVIL_RESPONSE" | head -c 500
    else
        # Check 2: response should be either sentinel concepts OR a safe error
        EVIL_CONCEPT=$(echo "$EVIL_RESPONSE" | jq -r '.data.current_concept // .current_concept // empty')
        EVIL_ERROR=$(echo "$EVIL_RESPONSE" | jq -r '.detail // empty')

        if [ "$EVIL_CONCEPT" = "默认概念" ]; then
            pass "Phase 17.2 OK — traversal resolved to sentinel '默认概念'"
        elif [ -n "$EVIL_ERROR" ]; then
            pass "Phase 17.2 OK — traversal rejected with safe error: ${EVIL_ERROR:0:80}"
        else
            # Even if it returned something else (e.g. mock mode default concepts),
            # as long as /etc/passwd content didn't leak, we consider it safe.
            warn "Phase 17.2 — traversal did not leak /etc/passwd but returned unexpected structure"
            info "Concept: $EVIL_CONCEPT"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Check 5: A4-Q2 — Graphiti 3-path parallel evidence in backend log
# ═══════════════════════════════════════════════════════════════════════════
section "Check 5: A4-Q2 Graphiti 3-Path Evidence"

# Look for evidence that the backend invoked Graphiti learning memories
# during the answer submission (Check 3 above).
# Common log signals:
#   - "fetch_learning_memories"
#   - "_get_enriched_context"
#   - "memory_service"
#   - "Graphiti"
#
# Note: This is best-effort. If the user isn't running with structlog to stdout
# or with a visible log file, we print a warning instead of failing.

LOG_HINTS=(
    "fetch_learning_memories"
    "_get_enriched_context"
    "Graphiti"
    "memory_service"
)

LOG_FILE="${BACKEND_LOG_FILE:-}"
if [ -z "$LOG_FILE" ]; then
    # Try common locations
    for candidate in ./backend.log ./logs/backend.log /tmp/canvas-backend.log; do
        if [ -f "$candidate" ]; then
            LOG_FILE="$candidate"
            break
        fi
    done
fi

if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
    FOUND=0
    for hint in "${LOG_HINTS[@]}"; do
        if tail -n 500 "$LOG_FILE" 2>/dev/null | grep -qi "$hint"; then
            info "Log contains '$hint' ✓"
            FOUND=1
        fi
    done
    if [ $FOUND -eq 1 ]; then
        pass "A4-Q2: Graphiti integration evidence found in $LOG_FILE"
    else
        warn "A4-Q2: No Graphiti hints found in $LOG_FILE (tail -n 500)"
        info "This may be OK if scoring was degraded (Phase 17.1 fail-closed skips enriched context)."
    fi
else
    warn "A4-Q2: No backend log file found at ./backend.log, ./logs/backend.log, or /tmp/canvas-backend.log"
    info "Export BACKEND_LOG_FILE=<path> to enable this check, or run backend with:"
    info "  uvicorn app.main:app --port 8001 2>&1 | tee /tmp/canvas-backend.log"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Cleanup
# ═══════════════════════════════════════════════════════════════════════════
if [ "$CLEANUP_CANVAS" = "1" ] && [ -f "$CANVAS_FILE" ]; then
    rm -f "$CANVAS_FILE"
    info "Removed test canvas: $CANVAS_FILE"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════
section "Summary"
echo "  Passed:   $PASS_COUNT"
echo "  Failed:   $FAIL_COUNT"
echo "  Warnings: $WARN_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}=== A4 verification: PASSED ===${RESET}"
    exit 0
else
    echo -e "${RED}=== A4 verification: $FAIL_COUNT failures ===${RESET}"
    exit $FAIL_COUNT
fi
