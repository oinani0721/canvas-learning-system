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

    [string]$BasePath = "C:\Users\ROG\托福",

    [int]$MaxTurns = 200,

    [switch]$DryRun
)

# Prompt template for full Dev+QA workflow
$promptTemplate = @"
Execute complete Dev+QA workflow for Story {STORY_ID}:

## Phase 1: Development
1. Read the .ai-context.md file to understand the Story context
2. Activate Developer Agent: /dev
3. Implement the Story: *develop-story {STORY_ID}
4. Run all tests: *run-tests

## Phase 2: Quality Assurance
5. Activate QA Agent: /qa
6. Perform code review: *review {STORY_ID}
7. Make quality gate decision: *gate {STORY_ID}

## Phase 3: Update Status
8. Update .worktree-status.yaml with:
   - status: "ready-to-merge" if gate=PASS, else "qa-reviewing"
   - tests_passed: true/false
   - qa_reviewed: true
   - qa_gate: PASS/CONCERNS/FAIL

Important:
- Follow all coding standards in CLAUDE.md
- Ensure tests pass before QA review
- Document any issues found in the review
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

# Launch sessions
Write-Host "Launching $($Stories.Count) parallel sessions..." -ForegroundColor Green
Write-Host ""

foreach ($story in $Stories) {
    $worktreePath = Join-Path $BasePath "Canvas-develop-$story"
    $logFile = Join-Path $worktreePath "dev-qa-output.log"

    # Replace placeholder in prompt
    $prompt = $promptTemplate -replace '\{STORY_ID\}', $story

    # Escape quotes for PowerShell command
    $escapedPrompt = $prompt -replace '"', '\"'

    # Build Claude command
    $claudeCmd = @(
        "claude",
        "-p `"$escapedPrompt`"",
        "--dangerously-skip-permissions",
        "--allowedTools `"$allowedTools`"",
        "--max-turns $MaxTurns"
    ) -join " "

    # Full command with logging
    $fullCmd = "cd '$worktreePath'; $claudeCmd 2>&1 | Tee-Object -FilePath '$logFile'"

    Write-Host "Story $story" -ForegroundColor Yellow
    Write-Host "  Path: $worktreePath"
    Write-Host "  Log: $logFile"

    if ($DryRun) {
        Write-Host "  Command: $fullCmd" -ForegroundColor DarkGray
    } else {
        # Launch in new PowerShell window
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            $fullCmd
        )
        Write-Host "  Status: Launched" -ForegroundColor Green
    }
    Write-Host ""
}

if ($DryRun) {
    Write-Host "DRY RUN - No sessions launched" -ForegroundColor Yellow
} else {
    Write-Host "All sessions launched!" -ForegroundColor Green
    Write-Host ""
    Write-Host "## Next Steps" -ForegroundColor Cyan
    Write-Host "1. Monitor progress in each terminal window"
    Write-Host "2. Check logs: Canvas-develop-{story}/dev-qa-output.log"
    Write-Host "3. Return to main repo and run: /parallel *status"
    Write-Host "4. Merge completed work: /parallel *merge --all"
}
