# A4 Verification Runbook — FR-KG-04 Hardening

> **Purpose**: Step-by-step guide to verify the A4 `verification_service` hardening fixes are actually working end-to-end. Designed for **both human users and Claude Code agents**.
>
> **Context**: The A4 exploration surfaced two core doubts about `verification_service`:
> - **A4-Q1**: Does it use real AI scoring, or emit predetermined scores?
> - **A4-Q2**: Does it actually call Graphiti in parallel (3-path fetch), or stub it?
>
> Phase 17.1 + 17.2 patched those issues (see `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/specs/verification-service/spec.md`). This runbook lets anyone prove the patches are live on a running system.

---

## 📋 What this runbook verifies

| # | Check | Phase | Source |
|---|---|---|---|
| 1 | Backend is reachable | — | `/api/v1/health` |
| 2 | Session start returns real AI question | A4-Q1 | `review.py:1640` |
| 3 | Fail-closed emits `degraded=true` + sentinel values | 17.1 | `verification_service.py:1677` |
| 4 | `../../etc/passwd` does NOT read host file | 17.2 | `verification_service.py:_resolve_safe_canvas_path` |
| 5 | Graphiti 3-path is wired up | A4-Q2 | `verification_service.py:_get_enriched_context` |
| 6 | **GUI** — Review Dashboard → ReviewItem → VerificationModal works | UI wiring | `App.tsx` + `VerificationModal.tsx` |

---

## 🔧 Prerequisites

Before starting, you need:

1. **Docker** (for Neo4j)
2. **Python 3.12 + uv** (backend venv)
3. **Node.js 20+** (frontend)
4. **`jq`** (JSON parser for the bash script): `brew install jq`
5. **`curl`** (usually pre-installed)

---

## Step 1 — Start the backend stack

<table>
<tr>
<th>👤 Human user (GUI)</th>
<th>🤖 Claude Code agent (shell)</th>
</tr>
<tr>
<td valign="top">

Open 3 terminal tabs:

**Tab 1: Neo4j**
```bash
cd ~/Desktop/canvas/canvas-learning-system
docker-compose up -d neo4j
```
Wait until `docker ps` shows `canvas-learning-system-neo4j` as `(healthy)`.

**Tab 2: Backend**
```bash
cd backend
.venv/bin/uvicorn app.main:app --port 8001 --reload 2>&1 | tee /tmp/canvas-backend.log
```
Wait for: `Application startup complete.`

**Tab 3: Frontend** (for Step 6)
```bash
cd frontend
npm run tauri dev
```

</td>
<td valign="top">

Use the `Bash` tool with `run_in_background: true`:

```bash
# 1. Neo4j
docker-compose up -d neo4j

# 2. Wait for Neo4j
for i in {1..30}; do
  docker ps --filter "name=canvas-learning-system-neo4j" --format '{{.Status}}' \
    | grep -q "healthy" && break
  sleep 2
done

# 3. Backend (background + log to file for Check 5)
cd backend && \
  .venv/bin/uvicorn app.main:app --port 8001 \
  > /tmp/canvas-backend.log 2>&1 &

# 4. Wait for backend ready
for i in {1..30}; do
  curl -sf http://localhost:8001/api/v1/health && break
  sleep 1
done
```

Expected: Final `curl` emits JSON with `"status": "healthy"`.

</td>
</tr>
</table>

---

## Step 2 — Run the automated verification script

<table>
<tr>
<th>👤 Human user</th>
<th>🤖 Claude Code agent</th>
</tr>
<tr>
<td valign="top">

Run the one-liner:

```bash
./backend/scripts/verify-a4-fix.sh
```

**Expected output:**
```
=== Check 1: Backend Health ===
✅ PASS: Backend is reachable (status=healthy)

=== Check 2: A4-Q1 Session Start (normal path) ===
✅ PASS: Session started: id=..., concepts=2
ℹ️  First question: 请解释 BKT 模型...

=== Check 3: Phase 17.1 Fail-Closed Contract ===
✅ PASS: API contract OK (quality=..., score=..., degraded=...)

=== Check 4: Phase 17.2 Path Traversal Hardening ===
✅ PASS: Phase 17.2 OK — traversal resolved to sentinel '默认概念'

=== Check 5: A4-Q2 Graphiti 3-Path Evidence ===
✅ PASS: A4-Q2: Graphiti integration evidence found in /tmp/canvas-backend.log
```

</td>
<td valign="top">

```bash
BACKEND_LOG_FILE=/tmp/canvas-backend.log \
  ./backend/scripts/verify-a4-fix.sh
```

Match on output patterns:

| Pattern | Meaning |
|---|---|
| `PASS: Backend is reachable` | Check 1 ✓ |
| `PASS: Session started` | Check 2 ✓ |
| `PASS: Phase 17.1 fail-closed triggered` OR `API contract OK` | Check 3 ✓ |
| `PASS: Phase 17.2 OK` | Check 4 ✓ |
| `PASS: A4-Q2: Graphiti integration` | Check 5 ✓ |

**Exit code 0** = all checks passed.
**Exit code N** = N failures — inspect log output.

</td>
</tr>
</table>

---

## Step 3 — Manually trigger Phase 17.1 fail-closed (optional)

The script in Step 2 may show `degraded=false` if your backend has a real scoring agent running. To *force* the fail-closed path for testing:

<table>
<tr>
<th>👤 Human user</th>
<th>🤖 Claude Code agent</th>
</tr>
<tr>
<td valign="top">

1. Stop backend (Ctrl+C in Tab 2)
2. Restart with mock mode:
   ```bash
   cd backend
   USE_MOCK_VERIFICATION=true \
     .venv/bin/uvicorn app.main:app --port 8001 --reload
   ```
3. Re-run the verify script:
   ```bash
   ./backend/scripts/verify-a4-fix.sh
   ```

Now Check 3 should show:
```
✅ PASS: Phase 17.1 fail-closed triggered: quality=unknown, score=0
ℹ️  degraded_warning: 评分服务暂时不可用，本次回答不计分也不更新掌握度...
```

</td>
<td valign="top">

```bash
# Kill existing backend
pkill -f "uvicorn app.main:app" || true
sleep 2

# Restart in mock mode
cd backend && \
  USE_MOCK_VERIFICATION=true \
  .venv/bin/uvicorn app.main:app --port 8001 \
  > /tmp/canvas-backend-mock.log 2>&1 &

# Wait for ready
sleep 5
curl -sf http://localhost:8001/api/v1/health

# Re-run verify
BACKEND_LOG_FILE=/tmp/canvas-backend-mock.log \
  ./backend/scripts/verify-a4-fix.sh
```

Expected delta vs. Step 2: Check 3 now asserts the actual fail-closed values (`quality=unknown`, `score=0`), not just contract presence.

</td>
</tr>
</table>

---

## Step 4 — Manually verify Phase 17.2 via curl

<table>
<tr>
<th>👤 Human user</th>
<th>🤖 Claude Code agent</th>
</tr>
<tr>
<td valign="top">

Paste into terminal:

```bash
curl -s -X POST http://localhost:8001/api/v1/review/session/start \
  -H "Content-Type: application/json" \
  -d '{"canvas_name":"../../etc/passwd","include_mastered":true}' \
  | jq .
```

**Expected**: Response contains `"current_concept": "默认概念"` (the sentinel fallback), NOT the contents of `/etc/passwd`.

**If you see** `root:x:0:0:...` in the response → **🚨 report immediately**. Phase 17.2 is broken.

</td>
<td valign="top">

```bash
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/review/session/start \
  -H "Content-Type: application/json" \
  -d '{"canvas_name":"../../etc/passwd","include_mastered":true}')

# Assert no leaked system file contents
if echo "$RESPONSE" | grep -qE 'root:|daemon:|/bin/bash'; then
  echo "FAIL: /etc/passwd content leaked"
  exit 1
else
  echo "PASS: no leak"
fi

# Assert sentinel in response
echo "$RESPONSE" | jq -r '.data.current_concept // .current_concept'
# Expected: "默认概念"
```

</td>
</tr>
</table>

---

## Step 5 — Verify A4-Q2 Graphiti 3-path in backend logs

<table>
<tr>
<th>👤 Human user</th>
<th>🤖 Claude Code agent</th>
</tr>
<tr>
<td valign="top">

After Step 2's script submits an answer, check the backend log:

```bash
grep -E "fetch_learning_memories|Graphiti|_get_enriched_context" \
  /tmp/canvas-backend.log | tail -20
```

You should see at least one match. This proves `verification_service` actually calls Graphiti during scoring (A4-Q2 doubt resolved).

</td>
<td valign="top">

```bash
grep -cE "fetch_learning_memories|Graphiti|_get_enriched_context" \
  /tmp/canvas-backend.log
```

Non-zero count = PASS. Zero = either Graphiti was skipped (e.g., Phase 17.1 degraded path bypasses enriched context) or the integration is broken.

</td>
</tr>
</table>

---

## Step 6 — GUI verification (Tauri app)

This is the only step that requires the frontend to be running.

<table>
<tr>
<th>👤 Human user</th>
<th>🤖 Claude Code agent</th>
</tr>
<tr>
<td valign="top">

1. The Tauri window should be open from Step 1 Tab 3.
2. Click **Dashboard** button (top-left).
3. Click the **Review** tab.
4. You should see a list of `ReviewNode` items. If empty, open a canvas first and mark some nodes as red/yellow so they show up in the review queue.
5. **Click any ReviewItem** → `VerificationModal` should open.
6. Read the question, type an answer, click **Submit**.
7. Observe the scoring card:
   - If **`degraded=true`** (Phase 17.1): orange warning banner with Chinese text explaining the answer is not counted.
   - If normal: green/yellow/red card with score + quality.
8. Click **Next** → next question.
9. Click **Cancel** or press **Escape** to close.

**Pass criteria**:
- Modal opens on ReviewItem click
- First question loads (no infinite spinner)
- Submit button produces a visible result card
- Orange degraded banner appears when scoring fails
- No console errors

</td>
<td valign="top">

Use the `mcp__claude-in-chrome__*` tools. **First** load the Tauri devtools window or a localhost URL in a Chrome tab.

```text
1. mcp__claude-in-chrome__tabs_context_mcp  # get current tabs
2. mcp__claude-in-chrome__tabs_create_mcp   # if needed, open http://localhost:1420 (or Tauri dev URL)
3. mcp__claude-in-chrome__find text "Dashboard"
4. mcp__claude-in-chrome__computer click <dashboard-button>
5. mcp__claude-in-chrome__find text "Review"
6. mcp__claude-in-chrome__computer click <review-tab>
7. mcp__claude-in-chrome__read_page    # inspect ReviewItem elements
8. mcp__claude-in-chrome__find selector "[data-review-item]" OR text matching a concept
9. mcp__claude-in-chrome__computer click <first ReviewItem>
10. mcp__claude-in-chrome__read_page   # should show VerificationModal header "Interactive Verification"
11. mcp__claude-in-chrome__form_input  # type answer into textarea
12. mcp__claude-in-chrome__computer click <Submit button>
13. mcp__claude-in-chrome__read_page   # should show quality/score card
14. mcp__claude-in-chrome__read_console_messages  # check for errors
```

**Note**: Tauri 2 may not expose the app window to Chrome. Fallback: navigate to `http://localhost:1420` (Vite dev server) in Chrome directly for browser-based testing of the same React code.

</td>
</tr>
</table>

---

## 🚨 Troubleshooting

### Backend unreachable

```
❌ FAIL: Health endpoint unreachable at http://localhost:8001/api/v1/health
```

- Check `docker ps` — is Neo4j healthy?
- Check Tab 2 for uvicorn errors (missing env vars, port conflict)
- Try a different port: `BACKEND_URL=http://localhost:8002 ./verify-a4-fix.sh`

### Session start returns 404

```
❌ FAIL: Session start response missing required fields
Raw response: {"detail":"No verifiable concepts found in canvas '...'"}
```

- The test canvas file was not created properly.
- Check `CANVAS_BASE_PATH` — it should be `./笔记库` relative to repo root.
- Manually create: `mkdir -p 笔记库 && echo '{"nodes":[{"id":"1","type":"text","text":"TestConcept","color":"3","x":0,"y":0,"width":100,"height":50}],"edges":[]}' > 笔记库/a4_verification_test.canvas`

### Phase 17.1 shows `degraded=false`

Not a failure — this means your backend has a working scoring agent. To *force* the fail-closed path, restart with `USE_MOCK_VERIFICATION=true` (see Step 3 above).

### Phase 17.2 leaked `/etc/passwd` content

**STOP. THIS IS A CRITICAL SECURITY REGRESSION.**
1. Abort the script.
2. Check `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/specs/verification-service/spec.md` "Hardened Path Resolution" requirement.
3. Run the unit test: `.venv/bin/pytest tests/unit/test_mock_degradation_transparency.py::TestPathTraversalHardening -v`
4. Report the regression with the captured response.

### Check 5 Graphiti log is empty

- Ensure Check 3 actually submitted an answer (not skipped).
- Make sure the backend log is being captured: `uvicorn ... 2>&1 | tee /tmp/canvas-backend.log`
- If Phase 17.1 degraded path was triggered, the enriched-context call is intentionally skipped. Re-run with a non-noise answer.

### VerificationModal does not open on click

- Open DevTools (Tauri: `Cmd+Opt+I`) and check Console for errors.
- Common cause: `ReviewItem onClick` prop was dropped during App.tsx wiring. Verify `frontend/src/App.tsx` has `onClick={(n) => { setVerificationNode(n); setShowVerificationModal(true); }}`.
- Verify `VerificationModal` is imported at the top of App.tsx.

---

## 📚 Related documents

- **Spec**: `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/specs/verification-service/spec.md`
- **Tests**: `backend/tests/unit/test_mock_degradation_transparency.py`
- **Gotchas**: `docs/known-gotchas.md` (G-MOCK-001/002, G-PATH-001)
- **Decision log**: `_decisions/decision-log.md` (2026-04-07 entries)
- **A4 original doubts**: `docs/project-status/fr-exploration/A4.md`

---

## ✅ Sign-off checklist

After a successful run, verify each of these has a visible ✅ in the script output or a screenshot of the GUI:

- [ ] Check 1: Backend health
- [ ] Check 2: Session start returns first question
- [ ] Check 3: Fail-closed contract (all fields present) — **and** actual `degraded=true` with `USE_MOCK_VERIFICATION=true` (Step 3)
- [ ] Check 4: Path traversal returns sentinel, no `/etc/passwd` leak
- [ ] Check 5: Graphiti log evidence (at least one match)
- [ ] Step 6: GUI modal opens, submits, shows result card

All six ✅ = A4 is end-to-end verified. OpenSpec tasks Phase 16.3, 16.4, 16.5, 17.3.5, 17.3.6 may be marked `[x]` in `tasks.md`.
