#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Worktree Watcher Daemon.

.DESCRIPTION
    Launches the Python daemon that monitors parallel development worktrees
    and automatically triggers QA sessions when dev-complete is detected.

.PARAMETER Background
    Run the daemon in the background (hidden window)

.PARAMETER MaxConcurrent
    Maximum concurrent QA sessions (default: 3)

.PARAMETER ScanInterval
    Seconds between worktree scans (default: 30)

.PARAMETER BasePath
    Base path where worktrees are located (default: C:\Users\ROG\托福)

.EXAMPLE
    .\start-watcher-daemon.ps1

.EXAMPLE
    .\start-watcher-daemon.ps1 -Background

.EXAMPLE
    .\start-watcher-daemon.ps1 -MaxConcurrent 5 -ScanInterval 60
#>

param(
    [switch]$Background,
    [int]$MaxConcurrent = 3,
    [int]$ScanInterval = 30,
    [string]$BasePath = "C:\Users\ROG\托福"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$daemonScript = Join-Path $scriptDir "daemon\worktree_watcher_daemon.py"
$projectDir = Join-Path $BasePath "Canvas"
$logFile = Join-Path $projectDir ".daemon-log.txt"

# Verify daemon script exists
if (-not (Test-Path $daemonScript)) {
    Write-Host "ERROR: Daemon script not found: $daemonScript" -ForegroundColor Red
    exit 1
}

# Build arguments
$pythonArgs = @(
    $daemonScript,
    "--base-path", $BasePath,
    "--max-concurrent", $MaxConcurrent,
    "--scan-interval", $ScanInterval
)

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                    WORKTREE WATCHER DAEMON                                 " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Daemon Script: $daemonScript"
Write-Host "  Base Path: $BasePath"
Write-Host "  Max Concurrent QA: $MaxConcurrent"
Write-Host "  Scan Interval: ${ScanInterval}s"
Write-Host ""

if ($Background) {
    Write-Host "Starting daemon in background..." -ForegroundColor Yellow
    Write-Host "  Log file: $logFile"
    Write-Host ""

    # Start in background with output redirection
    Start-Process python -ArgumentList $pythonArgs `
        -WindowStyle Hidden `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError $logFile

    Write-Host "Daemon started in background." -ForegroundColor Green
    Write-Host ""
    Write-Host "To view logs:" -ForegroundColor Cyan
    Write-Host "  Get-Content -Path '$logFile' -Tail 50 -Wait"
    Write-Host ""
    Write-Host "To stop the daemon:" -ForegroundColor Cyan
    Write-Host "  Get-Process python | Where-Object { `$_.CommandLine -like '*worktree_watcher*' } | Stop-Process"
    Write-Host ""
} else {
    Write-Host "Starting daemon in foreground (Ctrl+C to stop)..." -ForegroundColor Yellow
    Write-Host ""

    # Start in foreground
    & python @pythonArgs
}
