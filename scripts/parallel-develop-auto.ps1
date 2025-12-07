#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launch parallel Claude Code sessions for fully automated Story development.

.DESCRIPTION
    This script opens multiple Windows Terminal tabs, each running Claude Code
    in non-interactive mode (-p) to automatically execute the complete Dev+QA
    workflow for a Story.

.PARAMETER Stories
    Array of Story IDs to develop in parallel (e.g., "13.1", "13.2", "13.4")

.PARAMETER BasePath
    Base path where worktrees are located (default: C:\Users\ROG\托福)

.PARAMETER MaxTurns
    Maximum agentic turns per session (default: 200)

.PARAMETER DryRun
    Show commands without executing

.EXAMPLE
    .\parallel-develop-auto.ps1 -Stories 13.1,13.2,13.4

.EXAMPLE
    .\parallel-develop-auto.ps1 -Stories 13.1,13.2 -MaxTurns 100 -DryRun
#>

param(
    [Parameter(Mandatory=$true)]
    [string[]]$Stories,

    # 动态获取默认路径，避免中文编码问题
    [string]$BasePath = "",

    [int]$MaxTurns = 200,

    [switch]$DryRun,

    [switch]$Hidden  # Run windows hidden (background mode)
)

# 如果未指定 BasePath，动态获取（避免中文编码问题）
if (-not $BasePath) {
    # 脚本在 Canvas/scripts/ 下，所以父目录的父目录是 托福
    $BasePath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

# Prompt template for full Dev+QA+Git workflow with HALT decision points
$promptTemplate = @"
Execute complete Dev→QA→Git workflow for Story {STORY_ID}.

===============================================================================
STRICT WORKFLOW RULES - MUST FOLLOW EXACTLY
===============================================================================
1. ALWAYS read .ai-context.md first
2. HALT immediately if tests fail - do NOT proceed to QA
3. HALT immediately if QA Gate = FAIL - do NOT commit
4. If QA Gate = CONCERNS: attempt 1 fix cycle, re-run gate, then decide
5. ONLY commit if QA Gate = PASS or WAIVED
6. ALWAYS write .worktree-result.json at workflow end

===============================================================================
PHASE 1: DEVELOPMENT
===============================================================================
Step 1: Read .ai-context.md to understand Story context
Step 2: Activate Developer Agent: /dev
Step 3: Implement the Story: *develop-story {STORY_ID}
Step 4: Run all tests: *run-tests

**DECISION POINT A - TEST RESULTS**:
- If ALL tests PASS:
  - Update .worktree-status.yaml: status="dev-complete", tests_passed=true
  - PROCEED to Phase 2
- If ANY test FAILS:
  - Update .worktree-status.yaml: status="dev-blocked", tests_passed=false
  - Write .worktree-result.json with outcome="DEV_BLOCKED"
  - HALT WORKFLOW HERE - Do not proceed to QA

===============================================================================
PHASE 2: QUALITY ASSURANCE (Full QA Sequence)
===============================================================================
Step 5: Activate QA Agent: /qa
Step 6: Trace requirements coverage: *trace {STORY_ID}
Step 7: Assess non-functional requirements: *nfr-assess {STORY_ID}
Step 8: Comprehensive code review: *review {STORY_ID}
Step 9: Quality gate decision: *gate {STORY_ID}

**DECISION POINT B - QA GATE RESULT**:
- If gate = PASS:
  - Update .worktree-status.yaml: status="ready-to-merge", qa_gate="PASS"
  - PROCEED to Phase 3
- If gate = WAIVED:
  - Update .worktree-status.yaml: status="ready-to-merge", qa_gate="WAIVED"
  - PROCEED to Phase 3
- If gate = CONCERNS:
  - Attempt to fix the identified issues
  - Re-run tests: *run-tests
  - Re-run gate: *gate {STORY_ID}
  - If now PASS/WAIVED: PROCEED to Phase 3
  - If still CONCERNS or FAIL after 1 fix attempt:
    - Update status: qa_gate="CONCERNS"
    - Write .worktree-result.json with outcome="QA_CONCERNS_UNFIXED"
    - HALT WORKFLOW HERE
- If gate = FAIL:
  - Update .worktree-status.yaml: status="qa-blocked", qa_gate="FAIL"
  - Write .worktree-result.json with outcome="QA_BLOCKED"
  - HALT WORKFLOW HERE - Do not commit

===============================================================================
PHASE 3: GIT COMMIT (Only if QA Gate = PASS or WAIVED)
===============================================================================
Step 10: Stage all changes: git add -A
Step 11: Create commit with structured message:
         git commit -m "Story {STORY_ID}: [Brief Description]

         QA Gate: [PASS/WAIVED]
         Tests: [PASS]

         🤖 Generated with [Claude Code](https://claude.com/claude-code)
         Co-Authored-By: Claude <noreply@anthropic.com>"

Step 12: Update .worktree-status.yaml: status="ready-to-merge"

**Note**: Pre-commit hooks will automatically validate:
- JSON Schema syntax
- OpenAPI spec validity
- Gherkin syntax
- SDD coverage
- Content consistency

If pre-commit fails, fix issues and re-commit.

===============================================================================
PHASE 4: RESULT OUTPUT (ALWAYS Execute)
===============================================================================
Step 13: Write .worktree-result.json with ENHANCED status (include dev_record and qa_record):

{
  "story_id": "{STORY_ID}",
  "story_title": "[Story title from Story file]",
  "outcome": "SUCCESS|DEV_BLOCKED|QA_BLOCKED|QA_CONCERNS_UNFIXED",
  "tests_passed": true|false,
  "test_count": [number],
  "test_coverage": [percentage, e.g. 94.0],
  "qa_gate": "PASS|CONCERNS|FAIL|WAIVED"|null,
  "commit_sha": "[sha from git log -1 --format=%H]"|null,
  "blocking_reason": "[reason if blocked]"|null,
  "fix_attempts": 0|1,
  "timestamp": "[ISO-8601 timestamp]",
  "duration_seconds": [total seconds from start],

  "dev_record": {
    "agent_model": "Claude Code (claude-sonnet-4-5)",
    "duration_seconds": [seconds],
    "files_created": [
      {"path": "path/to/file.py", "description": "What was created"}
    ],
    "files_modified": [
      {"path": "path/to/existing.py", "description": "What changed"}
    ],
    "completion_notes": "[Brief summary of implementation]"
  },

  "qa_record": {
    "quality_score": [0-100],
    "ac_coverage": {
      "AC1": {"status": "PASS|FAIL", "evidence": "[test name or file]"},
      "AC2": {"status": "PASS|FAIL", "evidence": "[test name or file]"}
    },
    "issues_found": [
      {"severity": "low|medium|high", "description": "[issue]"}
    ],
    "recommendations": ["[recommendation 1]", "[recommendation 2]"]
  }
}

===============================================================================
PHASE 5: STORY FILE UPDATE (ALWAYS Execute After Phase 4)
===============================================================================
Step 14: Find and update Story file's "## Dev Agent Record" section:

    1. Locate Story file: docs/stories/{STORY_ID}.story.md or story-{STORY_ID}.md

    2. Replace "## Dev Agent Record" section content with:

       ### Agent Model Used
       Claude Code (claude-sonnet-4-5)

       ### Debug Log References
       - Session ID: [from progress file or auto-generated]
       - Process: Automated via `/parallel`

       ### Completion Notes List
       - [Summary of AC implementation]
       - Tests: PASS/FAIL ([test_count] tests, [coverage]% coverage)
       - QA Gate: [PASS/CONCERNS/FAIL/WAIVED]

       ### Commit Info
       - **Commit SHA**: `[sha]`
       - **Duration**: [seconds]s
       - **Completed At**: [ISO timestamp]
       - **Retry Count**: [0 or 1]

       ### File List
       **新创建:**
       - `path/file.py` - [description]
       **修改:**
       - `path/existing.py` - [what changed]

Step 15: Update Story file's "## QA Results" section:

    **验证方式**: `/parallel` 自动化验证流程
    **验证时间**: [YYYY-MM-DD]
    **验证状态**: ✅ PASSED / ⚠️ CONCERNS / ❌ FAILED

    ### Review Date: [YYYY-MM-DD]
    ### Reviewed By: Quinn (Test Architect) - Automated

    ### Gate Status
    **Gate: [PASS/CONCERNS/FAIL/WAIVED]**
    **Quality Score**: [score]/100

    ### AC Coverage
    | AC | Status | Evidence |
    |----|--------|----------|
    | AC1 | PASS/FAIL | [test or file reference] |

    ### Issues Found
    [list of issues or "无"]

    ### Gate File Reference
    `docs/qa/gates/{STORY_ID}-[slug].yml`

    **验证流程**:
    - [x] 单元测试通过
    - [x] *trace - 需求覆盖追溯
    - [x] *nfr-assess - 非功能需求评估
    - [x] *review - 综合审查
    - [x] *gate - 质量门禁 ([GATE STATUS])

Step 16: Set story_file_updated in .worktree-result.json:
    - If Story file was successfully updated: "story_file_updated": true
    - If update failed or skipped: "story_file_updated": false

===============================================================================
IMPORTANT REMINDERS
===============================================================================
- Follow all coding standards in CLAUDE.md
- Run tests BEFORE QA review
- Document any issues in the QA assessment files
- Do NOT push from worktree - orchestrator handles merge
- Update .worktree-status.yaml at EVERY decision point
"@

# Allowed tools for development
$allowedTools = "Bash,Read,Write,Edit,Grep,Glob,Task,TodoWrite"

Write-Host "## Parallel Development Auto-Launch" -ForegroundColor Cyan
Write-Host ""
Write-Host "Stories: $($Stories -join ', ')"
Write-Host "Base Path: $BasePath"
Write-Host "Max Turns: $MaxTurns"
Write-Host ""

# Validate worktrees exist
$missingWorktrees = @()
foreach ($story in $Stories) {
    $worktreePath = Join-Path $BasePath "Canvas-develop-$story"
    if (-not (Test-Path $worktreePath)) {
        $missingWorktrees += $story
    }
}

if ($missingWorktrees.Count -gt 0) {
    Write-Host "ERROR: Missing worktrees for Stories: $($missingWorktrees -join ', ')" -ForegroundColor Red
    Write-Host "Run '*init' in /parallel to create worktrees first." -ForegroundColor Yellow
    exit 1
}

# Clean up old result files before launching new sessions
Write-Host "Cleaning up previous result files..." -ForegroundColor Yellow
foreach ($story in $Stories) {
    $worktreePath = Join-Path $BasePath "Canvas-develop-$story"
    $resultFile = Join-Path $worktreePath ".worktree-result.json"
    if (Test-Path $resultFile) {
        Remove-Item $resultFile -Force
        Write-Host "  Removed: $resultFile" -ForegroundColor DarkGray
    }
}
Write-Host ""

# Launch sessions
Write-Host "Launching $($Stories.Count) parallel sessions..." -ForegroundColor Green
Write-Host ""

foreach ($story in $Stories) {
    $worktreePath = Join-Path $BasePath "Canvas-develop-$story"
    $logFile = Join-Path $worktreePath "dev-qa-output.log"

    # Replace placeholder in prompt
    $prompt = $promptTemplate -replace '\{STORY_ID\}', $story

    # Phase 1 Fix: Write prompt to file to avoid quote escaping issues
    $promptFile = Join-Path $worktreePath ".claude-prompt.txt"
    $prompt | Set-Content -Path $promptFile -Encoding UTF8

    # Create launcher script that reads from prompt file
    # Use $PSScriptRoot to avoid Chinese character encoding issues
    $launcherContent = @"
`$ErrorActionPreference = 'Continue'
# Use script location to avoid Chinese character encoding issues
`$WorktreePath = `$PSScriptRoot
Set-Location `$WorktreePath
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Story $story - Dev+QA Workflow" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Working directory: `$WorktreePath" -ForegroundColor Yellow
`$promptFile = Join-Path `$WorktreePath ".claude-prompt.txt"
`$logFile = Join-Path `$WorktreePath "dev-qa-output.log"
if (-not (Test-Path `$promptFile)) {
    Write-Host "ERROR: Prompt file not found" -ForegroundColor Red
    exit 1
}
Write-Host "Log file: `$logFile" -ForegroundColor Yellow
Write-Host ""
`$prompt = Get-Content `$promptFile -Raw
claude -p `$prompt --dangerously-skip-permissions --output-format json --max-turns $MaxTurns 2>&1 | Tee-Object -FilePath `$logFile
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Story $story - Claude Session Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Phase 6: Post-Processing - Dev-QA Auto-Record Pipeline
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Story $story - Post-Processing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if .worktree-result.json exists and outcome is SUCCESS
`$resultFile = Join-Path `$WorktreePath ".worktree-result.json"
if (Test-Path `$resultFile) {
    try {
        `$resultContent = Get-Content `$resultFile -Raw | ConvertFrom-Json
        if (`$resultContent.outcome -eq "SUCCESS") {
            Write-Host "Running post-process hook for Story file update and QA Gate generation..." -ForegroundColor Yellow

            # Call the Python post-process hook
            `$daemonPath = Join-Path (Split-Path -Parent `$WorktreePath) "Canvas\scripts\daemon"
            `$hookScript = Join-Path `$daemonPath "post_process_hook.py"

            if (Test-Path `$hookScript) {
                python `$hookScript --story-id "$story" --worktree-path `$WorktreePath --session-id "parallel-$story"
                Write-Host "Post-processing complete!" -ForegroundColor Green
            } else {
                Write-Host "Warning: post_process_hook.py not found at: `$hookScript" -ForegroundColor Yellow
            }
        } else {
            Write-Host "Skipping post-processing (outcome: `$(`$resultContent.outcome))" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Warning: Could not parse result file: `$_" -ForegroundColor Yellow
    }
} else {
    Write-Host "Warning: No result file found, skipping post-processing" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Story $story - Workflow Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
if (-not `$args[0]) { Read-Host "Press Enter to close..." }
"@
    $launcherFile = Join-Path $worktreePath ".claude-launcher.ps1"
    $launcherContent | Set-Content -Path $launcherFile -Encoding UTF8

    Write-Host "Story $story" -ForegroundColor Yellow
    Write-Host "  Path: $worktreePath"
    Write-Host "  Log: $logFile"
    Write-Host "  Prompt: $promptFile"

    if ($DryRun) {
        Write-Host "  Launcher: $launcherFile" -ForegroundColor DarkGray
    } else {
        # Launch in new PowerShell window
        $windowStyle = if ($Hidden) { "Hidden" } else { "Normal" }
        Start-Process powershell -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $launcherFile
        ) -WorkingDirectory $worktreePath -WindowStyle $windowStyle
        $modeLabel = if ($Hidden) { "(Hidden)" } else { "(Visible)" }
        Write-Host "  Status: Launched $modeLabel" -ForegroundColor Green
    }
    Write-Host ""
}

if ($DryRun) {
    Write-Host "DRY RUN - No sessions launched" -ForegroundColor Yellow
} else {
    Write-Host "All sessions launched!" -ForegroundColor Green
    Write-Host ""

    # Offer to launch monitor
    Write-Host "## Monitor Options" -ForegroundColor Cyan
    Write-Host "Option 1: Launch real-time monitor (recommended):"
    Write-Host "  .\scripts\parallel-monitor-and-report.ps1 -Stories $($Stories -join ',')" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 2: Manual monitoring:"
    Write-Host "  - Check terminal windows for progress"
    Write-Host "  - Check logs: Canvas-develop-{story}/dev-qa-output.log"
    Write-Host "  - Check results: Canvas-develop-{story}/.worktree-result.json"
    Write-Host ""
    Write-Host "## After Completion" -ForegroundColor Cyan
    Write-Host "1. Return to main repo: cd $BasePath\Canvas"
    Write-Host "2. Check status: /parallel *status"
    Write-Host "3. Merge completed: /parallel *merge --all"
    Write-Host "4. Cleanup: /parallel *cleanup --all"
    Write-Host ""
    Write-Host "## Workflow Summary" -ForegroundColor Cyan
    Write-Host "Each session will execute: Dev → QA(*trace→*nfr-assess→*review→*gate) → Git Commit"
    Write-Host "Pre-commit hooks will automatically validate on commit."
    Write-Host ""
    Write-Host "Result files (.worktree-result.json) will contain:"
    Write-Host "  - outcome: SUCCESS | DEV_BLOCKED | QA_BLOCKED | QA_CONCERNS_UNFIXED"
    Write-Host "  - qa_gate: PASS | CONCERNS | FAIL | WAIVED"
    Write-Host "  - commit_sha: (if committed)"
}
