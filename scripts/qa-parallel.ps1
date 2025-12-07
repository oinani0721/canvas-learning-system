<#
.SYNOPSIS
    Parallel QA Execution for Wave-Based Development

.DESCRIPTION
    Runs BMad QA workflow (*review, *gate) for multiple stories in parallel.
    Supports retry on failure and generates QA reports.

.PARAMETER Stories
    Array of story IDs to QA (e.g., "12.1", "12.2", "12.4")

.PARAMETER MaxParallel
    Maximum concurrent QA sessions (default: 3)

.PARAMETER RetryOnFail
    Retry QA once if initial gate fails (default: true)

.EXAMPLE
    .\qa-parallel.ps1 -Stories @("12.1", "12.2", "12.4")
#>

param(
    [Parameter(Mandatory=$true)]
    [string[]]$Stories,

    [int]$MaxParallel = 3,

    [switch]$RetryOnFail = $true
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

# Configuration
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptsDir = $PSScriptRoot
$ProgressFile = Join-Path $ScriptsDir "wave-progress.json"
$QAReportDir = Join-Path $ProjectRoot "qa-reports"

# Ensure QA report directory exists
if (-not (Test-Path $QAReportDir)) {
    New-Item -ItemType Directory -Path $QAReportDir -Force | Out-Null
}

# ============================================================================
# Helper Functions
# ============================================================================

function Write-QALog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO" { "Cyan" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        "QA_PASS" { "Green" }
        "QA_CONCERNS" { "Yellow" }
        "QA_FAIL" { "Red" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Get-WaveProgress {
    if (Test-Path $ProgressFile) {
        return Get-Content $ProgressFile -Raw | ConvertFrom-Json
    }
    return @{
        epic = 12
        stories = @{}
    }
}

function Save-WaveProgress {
    param($Progress)
    $Progress | ConvertTo-Json -Depth 10 | Set-Content $ProgressFile -Encoding UTF8
}

function Start-StoryQA {
    param(
        [string]$StoryId
    )

    $worktreeName = "Canvas-develop-$StoryId"
    $worktreePath = Join-Path (Split-Path $ProjectRoot -Parent) $worktreeName

    if (-not (Test-Path $worktreePath)) {
        Write-QALog "Worktree not found for Story $StoryId" "ERROR"
        return @{
            StoryId = $StoryId
            Status = "error"
            Message = "Worktree not found"
        }
    }

    Write-QALog "Starting QA for Story $StoryId..." "INFO"

    # Create QA prompt
    $qaPrompt = @"
/qa
*review $StoryId
*gate $StoryId

IMPORTANT: This is an unattended QA run.
1. Run comprehensive review of the story implementation
2. Check all acceptance criteria
3. Verify test coverage
4. Provide clear PASS, CONCERNS, or FAIL decision
5. If CONCERNS, list the non-blocking issues
6. If FAIL, list the critical issues that must be fixed
"@

    $qaPromptFile = Join-Path $worktreePath ".claude-qa-prompt.txt"
    [System.IO.File]::WriteAllText($qaPromptFile, $qaPrompt, [System.Text.UTF8Encoding]::new($false))

    $qaLogFile = Join-Path $worktreePath "qa-output.log"
    $qaReportFile = Join-Path $QAReportDir "qa-report-$StoryId-$(Get-Date -Format 'yyyyMMdd-HHmmss').md"

    # Create QA launcher script
    $qaLauncherContent = @"
`$ErrorActionPreference = 'Continue'
`$WorktreePath = "$worktreePath"
Set-Location `$WorktreePath
Write-Host "Starting QA for Story $StoryId..." -ForegroundColor Cyan
`$qaPromptFile = Join-Path `$WorktreePath ".claude-qa-prompt.txt"
`$qaLogFile = Join-Path `$WorktreePath "qa-output.log"
`$prompt = Get-Content `$qaPromptFile -Raw
`$systemPrompt = "CRITICAL: You are QA Agent Quinn. Run comprehensive review. Provide PASS, CONCERNS, or FAIL decision. Be thorough but efficient. Do NOT ask questions."
claude -p `$prompt --dangerously-skip-permissions --output-format json --max-turns 50 --append-system-prompt `$systemPrompt 2>&1 | Tee-Object -FilePath `$qaLogFile
Write-Host "QA completed for Story $StoryId" -ForegroundColor Green
"@

    $qaLauncherFile = Join-Path $worktreePath ".claude-qa-launcher.ps1"
    [System.IO.File]::WriteAllText($qaLauncherFile, $qaLauncherContent, [System.Text.UTF8Encoding]::new($false))

    # Run QA
    $process = Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $qaLauncherFile -PassThru -Wait -WorkingDirectory $worktreePath

    # Parse QA result
    $qaStatus = "unknown"
    $qaDetails = ""

    if (Test-Path $qaLogFile) {
        $qaContent = Get-Content $qaLogFile -Raw -ErrorAction SilentlyContinue

        if ($qaContent -match "PASS") {
            $qaStatus = "pass"
        }
        elseif ($qaContent -match "CONCERNS") {
            $qaStatus = "concerns"
            # Extract concerns
            if ($qaContent -match "CONCERNS[:\s]*(.+?)(?:PASS|FAIL|$)") {
                $qaDetails = $Matches[1].Trim()
            }
        }
        elseif ($qaContent -match "FAIL") {
            $qaStatus = "fail"
            # Extract failure reasons
            if ($qaContent -match "FAIL[:\s]*(.+?)(?:PASS|CONCERNS|$)") {
                $qaDetails = $Matches[1].Trim()
            }
        }

        # Generate QA report
        $reportContent = @"
# QA Report: Story $StoryId

**Date**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Status**: $($qaStatus.ToUpper())

## Decision
$qaDetails

## Full QA Output
\`\`\`
$qaContent
\`\`\`
"@
        [System.IO.File]::WriteAllText($qaReportFile, $reportContent, [System.Text.UTF8Encoding]::new($false))
    }

    return @{
        StoryId = $StoryId
        Status = $qaStatus
        Details = $qaDetails
        ReportFile = $qaReportFile
    }
}

# ============================================================================
# Main Execution
# ============================================================================

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host " 🧪 Parallel QA Execution Engine v1.0" -ForegroundColor White
Write-Host " Stories: $($Stories -join ', ')" -ForegroundColor DarkGray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""

$progress = Get-WaveProgress
$results = @()
$failedStories = @()

# Process stories in parallel batches
$storyQueue = [System.Collections.Queue]::new($Stories)
$runningJobs = @{}

while ($storyQueue.Count -gt 0 -or $runningJobs.Count -gt 0) {
    # Start new jobs if slots available
    while ($storyQueue.Count -gt 0 -and $runningJobs.Count -lt $MaxParallel) {
        $storyId = $storyQueue.Dequeue()
        Write-QALog "Queuing QA for Story $storyId" "INFO"

        $result = Start-StoryQA -StoryId $storyId

        # Update progress
        if ($progress.stories.$storyId) {
            $progress.stories.$storyId.qaStatus = $result.Status
            $progress.stories.$storyId.qaCompletedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        }
        Save-WaveProgress $progress

        $results += $result

        $statusLevel = switch ($result.Status) {
            "pass" { "QA_PASS" }
            "concerns" { "QA_CONCERNS" }
            "fail" { "QA_FAIL" }
            default { "WARNING" }
        }

        $icon = switch ($result.Status) {
            "pass" { "✅" }
            "concerns" { "⚠️" }
            "fail" { "❌" }
            default { "❓" }
        }

        Write-QALog "$icon Story $storyId QA: $($result.Status.ToUpper())" $statusLevel

        if ($result.Status -eq "fail") {
            $failedStories += $storyId
        }
    }
}

# Retry failed stories if enabled
if ($RetryOnFail -and $failedStories.Count -gt 0) {
    Write-Host ""
    Write-QALog "Retrying $($failedStories.Count) failed stories..." "WARNING"

    foreach ($storyId in $failedStories) {
        Write-QALog "Retry QA for Story $storyId" "INFO"
        $result = Start-StoryQA -StoryId $storyId

        # Update progress
        if ($progress.stories.$storyId) {
            $progress.stories.$storyId.qaStatus = $result.Status
            $progress.stories.$storyId.qaRetried = $true
            $progress.stories.$storyId.qaRetriedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        }
        Save-WaveProgress $progress

        $icon = switch ($result.Status) {
            "pass" { "✅" }
            "concerns" { "⚠️" }
            "fail" { "❌" }
            default { "❓" }
        }

        Write-QALog "$icon Story $storyId QA Retry: $($result.Status.ToUpper())" $(if ($result.Status -eq "pass") { "SUCCESS" } else { "ERROR" })
    }
}

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host " 📊 QA Summary" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$passCount = ($results | Where-Object { $_.Status -eq "pass" }).Count
$concernsCount = ($results | Where-Object { $_.Status -eq "concerns" }).Count
$failCount = ($results | Where-Object { $_.Status -eq "fail" }).Count

Write-Host " ✅ PASS: $passCount" -ForegroundColor Green
Write-Host " ⚠️ CONCERNS: $concernsCount" -ForegroundColor Yellow
Write-Host " ❌ FAIL: $failCount" -ForegroundColor Red
Write-Host ""
Write-Host " 📁 Reports: $QAReportDir" -ForegroundColor DarkGray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Return results
return $results
