$ErrorActionPreference = 'Continue'
# Use script location to avoid Chinese character encoding issues
$WorktreePath = $PSScriptRoot
Set-Location $WorktreePath
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Story 21.5.1.2 - Dev+QA Workflow" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Working directory: $WorktreePath" -ForegroundColor Yellow
$promptFile = Join-Path $WorktreePath ".claude-prompt.txt"
$logFile = Join-Path $WorktreePath "dev-qa-output.log"
if (-not (Test-Path $promptFile)) {
    Write-Host "ERROR: Prompt file not found" -ForegroundColor Red
    exit 1
}
Write-Host "Log file: $logFile" -ForegroundColor Yellow
Write-Host ""

# Execute claude by piping prompt via stdin (works better for long prompts)
Write-Host "Starting Claude session..." -ForegroundColor Green
Get-Content $promptFile -Raw -Encoding UTF8 | claude -p --dangerously-skip-permissions --output-format json 2>&1 | Tee-Object -FilePath $logFile
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Story 21.5.1.2 - Claude Session Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Phase 6: Post-Processing - Dev-QA Auto-Record Pipeline
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Story 21.5.1.2 - Post-Processing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if .worktree-result.json exists and outcome is SUCCESS
$resultFile = Join-Path $WorktreePath ".worktree-result.json"
if (Test-Path $resultFile) {
    try {
        $resultContent = Get-Content $resultFile -Raw | ConvertFrom-Json
        if ($resultContent.outcome -eq "SUCCESS") {
            Write-Host "Running post-process hook for Story file update and QA Gate generation..." -ForegroundColor Yellow

            # Call the Python post-process hook
            $daemonPath = Join-Path (Split-Path -Parent $WorktreePath) "Canvas\scripts\daemon"
            $hookScript = Join-Path $daemonPath "post_process_hook.py"

            if (Test-Path $hookScript) {
                python $hookScript --story-id "21.5.1.2" --worktree-path $WorktreePath --session-id "parallel-21.5.1.2"
                Write-Host "Post-processing complete!" -ForegroundColor Green
            } else {
                Write-Host "Warning: post_process_hook.py not found at: $hookScript" -ForegroundColor Yellow
            }
        } else {
            Write-Host "Skipping post-processing (outcome: $($resultContent.outcome))" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Warning: Could not parse result file: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "Warning: No result file found, skipping post-processing" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Story 21.5.1.2 - Workflow Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
if (-not $args[0]) { Read-Host "Press Enter to close..." }
