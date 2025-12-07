#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Monitor parallel development sessions and aggregate results.

.DESCRIPTION
    Polls worktrees for .worktree-result.json files and displays real-time
    progress. Generates a summary report when all sessions complete.

.PARAMETER Stories
    Array of Story IDs being developed in parallel (e.g., "13.1", "13.2")

.PARAMETER BasePath
    Base path where worktrees are located (default: C:\Users\ROG\托福)

.PARAMETER PollInterval
    Seconds between status checks (default: 30)

.PARAMETER Timeout
    Maximum seconds to wait for completion (default: 7200 = 2 hours)

.PARAMETER ReportOnly
    Don't poll, just show current status and exit

.EXAMPLE
    .\parallel-monitor-and-report.ps1 -Stories 13.1,13.2,13.4

.EXAMPLE
    .\parallel-monitor-and-report.ps1 -Stories 13.1,13.2 -PollInterval 10 -Timeout 3600

.EXAMPLE
    .\parallel-monitor-and-report.ps1 -Stories 13.1,13.2 -ReportOnly
#>

param(
    [Parameter(Mandatory=$true)]
    [string[]]$Stories,

    [string]$BasePath = "C:\Users\ROG\托福",

    [int]$PollInterval = 30,

    [int]$Timeout = 7200,

    [switch]$ReportOnly
)

$startTime = Get-Date
$results = @{}
$projectPath = Join-Path $BasePath "Canvas"

function Get-WorktreeStatus {
    param([string]$WorktreePath)

    $statusFile = Join-Path $WorktreePath ".worktree-status.yaml"
    $resultFile = Join-Path $WorktreePath ".worktree-result.json"

    $status = @{
        exists = Test-Path $WorktreePath
        statusYaml = $null
        resultJson = $null
        isComplete = $false
    }

    if ($status.exists) {
        # Read YAML status (simple parsing)
        if (Test-Path $statusFile) {
            $content = Get-Content $statusFile -Raw
            $status.statusYaml = @{}

            # Parse key: value pairs
            $content -split "`n" | ForEach-Object {
                if ($_ -match "^\s*(\w+):\s*(.+?)\s*$") {
                    $status.statusYaml[$matches[1]] = $matches[2].Trim('"', "'")
                }
            }
        }

        # Read JSON result
        if (Test-Path $resultFile) {
            try {
                $status.resultJson = Get-Content $resultFile -Raw | ConvertFrom-Json
                $status.isComplete = $true
            } catch {
                $status.resultJson = $null
            }
        }
    }

    return $status
}

function Show-StatusTable {
    param([hashtable]$Results, [string[]]$Stories)

    Clear-Host
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "                    PARALLEL DEVELOPMENT MONITOR                            " -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host "Elapsed: $([math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)) minutes"
    Write-Host ""

    # Table header
    $header = "| {0,-10} | {1,-15} | {2,-8} | {3,-10} | {4,-8} |" -f "Story", "Status", "Tests", "QA Gate", "Ready"
    $separator = "|" + ("-" * 12) + "|" + ("-" * 17) + "|" + ("-" * 10) + "|" + ("-" * 12) + "|" + ("-" * 10) + "|"

    Write-Host $separator
    Write-Host $header -ForegroundColor White
    Write-Host $separator

    foreach ($story in $Stories) {
        $worktreePath = Join-Path $BasePath "Canvas-develop-$story"
        $status = Get-WorktreeStatus -WorktreePath $worktreePath

        $storyStatus = "Pending"
        $testsStatus = "-"
        $qaGate = "-"
        $ready = "❌"
        $color = "Gray"

        if ($status.resultJson) {
            # Completed - use result file
            $storyStatus = $status.resultJson.outcome
            $testsStatus = if ($status.resultJson.tests_passed) { "✅ Pass" } else { "❌ Fail" }
            $qaGate = if ($status.resultJson.qa_gate) { $status.resultJson.qa_gate } else { "-" }

            switch ($status.resultJson.outcome) {
                "SUCCESS" {
                    $ready = "✅"
                    $color = "Green"
                }
                "DEV_BLOCKED" {
                    $ready = "❌"
                    $color = "Red"
                }
                "QA_BLOCKED" {
                    $ready = "❌"
                    $color = "Red"
                }
                "QA_CONCERNS_UNFIXED" {
                    $ready = "⚠️"
                    $color = "Yellow"
                }
            }

            $Results[$story] = $status.resultJson
        }
        elseif ($status.statusYaml) {
            # In progress - use status YAML
            $storyStatus = $status.statusYaml.status
            $testsStatus = if ($status.statusYaml.tests_passed -eq "true") { "✅ Pass" }
                          elseif ($status.statusYaml.tests_passed -eq "false") { "❌ Fail" }
                          else { "⏳" }
            $qaGate = if ($status.statusYaml.qa_gate) { $status.statusYaml.qa_gate } else { "-" }

            switch ($storyStatus) {
                "initialized" { $color = "Gray"; $storyStatus = "Initializing" }
                "in-progress" { $color = "Yellow"; $storyStatus = "Developing" }
                "dev-complete" { $color = "Cyan"; $storyStatus = "QA Review" }
                "dev-blocked" { $color = "Red"; $storyStatus = "Dev Blocked" }
                "qa-reviewing" { $color = "Cyan"; $storyStatus = "QA Review" }
                "qa-blocked" { $color = "Red"; $storyStatus = "QA Blocked" }
                "ready-to-merge" { $color = "Green"; $ready = "✅" }
            }
        }
        else {
            $storyStatus = "Not Found"
            $color = "DarkGray"
        }

        $row = "| {0,-10} | {1,-15} | {2,-8} | {3,-10} | {4,-8} |" -f $story, $storyStatus, $testsStatus, $qaGate, $ready
        Write-Host $row -ForegroundColor $color
    }

    Write-Host $separator
    Write-Host ""
}

function Show-Summary {
    param([hashtable]$Results, [string[]]$Stories)

    $success = ($Results.Values | Where-Object { $_.outcome -eq "SUCCESS" }).Count
    $blocked = ($Results.Values | Where-Object { $_.outcome -match "BLOCKED" }).Count
    $concerns = ($Results.Values | Where-Object { $_.outcome -eq "QA_CONCERNS_UNFIXED" }).Count
    $pending = $Stories.Count - $Results.Count

    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "                              SUMMARY                                       " -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Total Stories:  $($Stories.Count)"
    Write-Host "  ✅ Success:     $success" -ForegroundColor Green
    Write-Host "  ❌ Blocked:     $blocked" -ForegroundColor Red
    Write-Host "  ⚠️  Concerns:    $concerns" -ForegroundColor Yellow
    Write-Host "  ⏳ Pending:     $pending" -ForegroundColor Gray
    Write-Host ""

    # Show recommended actions
    if ($success -gt 0) {
        Write-Host "## Recommended Actions" -ForegroundColor Cyan
        Write-Host ""

        $successStories = $Results.Keys | Where-Object { $Results[$_].outcome -eq "SUCCESS" }
        Write-Host "Ready to merge:" -ForegroundColor Green
        foreach ($s in $successStories) {
            $sha = if ($Results[$s].commit_sha) { $Results[$s].commit_sha.Substring(0,7) } else { "N/A" }
            Write-Host "  ✅ Story $s (commit: $sha)"
        }
        Write-Host ""
        Write-Host "Run: /parallel *merge --all" -ForegroundColor Yellow
        Write-Host ""
    }

    if ($blocked -gt 0) {
        Write-Host "Blocked (need attention):" -ForegroundColor Red
        $blockedStories = $Results.Keys | Where-Object { $Results[$_].outcome -match "BLOCKED" }
        foreach ($s in $blockedStories) {
            $reason = if ($Results[$s].blocking_reason) { $Results[$s].blocking_reason } else { $Results[$s].outcome }
            Write-Host "  ❌ Story $s - $reason"
        }
        Write-Host ""
    }
}

function Save-Report {
    param([hashtable]$Results, [string[]]$Stories)

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $reportPath = Join-Path $projectPath "parallel-dev-report-$timestamp.json"

    $report = @{
        timestamp = (Get-Date).ToString("o")
        duration_minutes = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
        total = $Stories.Count
        success = ($Results.Values | Where-Object { $_.outcome -eq "SUCCESS" }).Count
        blocked = ($Results.Values | Where-Object { $_.outcome -match "BLOCKED" }).Count
        concerns = ($Results.Values | Where-Object { $_.outcome -eq "QA_CONCERNS_UNFIXED" }).Count
        stories = @{}
    }

    foreach ($key in $Results.Keys) {
        $report.stories[$key] = $Results[$key]
    }

    $report | ConvertTo-Json -Depth 5 | Set-Content $reportPath -Encoding UTF8

    Write-Host "Report saved: $reportPath" -ForegroundColor Cyan
    return $reportPath
}

# Main loop
Write-Host "Starting parallel development monitor..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor DarkGray
Write-Host ""

if ($ReportOnly) {
    Show-StatusTable -Results $results -Stories $Stories
    Show-Summary -Results $results -Stories $Stories
    exit 0
}

while ($true) {
    # Check timeout
    $elapsed = ((Get-Date) - $startTime).TotalSeconds
    if ($elapsed -gt $Timeout) {
        Write-Host ""
        Write-Host "TIMEOUT: Maximum wait time exceeded ($Timeout seconds)" -ForegroundColor Red
        Show-Summary -Results $results -Stories $Stories
        Save-Report -Results $results -Stories $Stories
        exit 1
    }

    # Show current status
    Show-StatusTable -Results $results -Stories $Stories

    # Check if all complete
    $allComplete = $true
    foreach ($story in $Stories) {
        if (-not $results.ContainsKey($story)) {
            $allComplete = $false
            break
        }
    }

    if ($allComplete) {
        Write-Host "All sessions complete!" -ForegroundColor Green
        Write-Host ""
        Show-Summary -Results $results -Stories $Stories
        $reportPath = Save-Report -Results $results -Stories $Stories
        Write-Host ""
        Write-Host "Monitor finished. See report: $reportPath" -ForegroundColor Cyan
        exit 0
    }

    # Wait before next poll
    Write-Host "Next check in $PollInterval seconds... (Ctrl+C to stop)" -ForegroundColor DarkGray
    Start-Sleep -Seconds $PollInterval
}
