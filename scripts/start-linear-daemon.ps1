#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Linear Development Daemon for 24/7 unattended sequential Story development.

.DESCRIPTION
    This script launches the Python Linear Development Daemon which:
    - Processes Stories sequentially (one at a time)
    - Automatically handles Claude session compact/restart
    - Retries failed Stories once
    - Persists progress for crash recovery
    - Runs 24/7 without user intervention

.PARAMETER Stories
    Comma-separated list of Story IDs to develop (e.g., "15.1,15.2,15.3")

.PARAMETER BasePath
    Base path where worktrees are located (default: C:\Users\ROG\托福)

.PARAMETER MaxTurns
    Maximum agentic turns per Claude session (default: 200)

.PARAMETER Resume
    Resume from existing progress file instead of starting fresh

.EXAMPLE
    .\start-linear-daemon.ps1 -Stories 15.1,15.2,15.3,15.4,15.5,15.6

.EXAMPLE
    .\start-linear-daemon.ps1 -Stories 15.1,15.2,15.3 -Resume

.EXAMPLE
    .\start-linear-daemon.ps1 -Stories 15.1,15.2 -MaxTurns 150

.NOTES
    After starting, you can leave the computer. The daemon will:
    - Automatically process each Story in order
    - Handle compact by restarting Claude sessions
    - Retry failures once before halting
    - Save progress to linear-progress.json

    To check progress:
    Get-Content .\linear-progress.json | ConvertFrom-Json

    To view current log:
    Get-Content "C:\Users\ROG\托福\Canvas-develop-15.X\dev-qa-output.log" -Tail 50 -Wait
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Stories,

    [string]$BasePath = "C:\Users\ROG\托福",

    [int]$MaxTurns = 200,

    [switch]$Resume,

    [switch]$UltraThink
)

$ErrorActionPreference = "Stop"

# Fix encoding for Chinese characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DaemonScript = Join-Path $ScriptDir "daemon\linear_develop_daemon.py"

# Verify daemon script exists
if (-not (Test-Path $DaemonScript)) {
    Write-Host "ERROR: Daemon script not found: $DaemonScript" -ForegroundColor Red
    exit 1
}

# Build arguments
$PythonArgs = @(
    $DaemonScript,
    "--stories", $Stories,
    "--base-path", $BasePath,
    "--max-turns", $MaxTurns
)

if ($Resume) {
    $PythonArgs += "--resume"
}

if ($UltraThink) {
    $PythonArgs += "--ultrathink"
}

# Display banner
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
if ($UltraThink) {
    Write-Host "  Linear Development Daemon - 24/7 UltraThink Mode" -ForegroundColor Magenta
} else {
    Write-Host "  Linear Development Daemon - 24/7 Unattended Mode" -ForegroundColor Cyan
}
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "  Stories: $Stories" -ForegroundColor Yellow
Write-Host "  Base Path: $BasePath"
Write-Host "  Max Turns: $MaxTurns"
Write-Host "  Resume: $Resume"
if ($UltraThink) {
    Write-Host "  UltraThink: Enabled" -ForegroundColor Magenta
}
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "  Starting daemon..." -ForegroundColor Green
Write-Host "  You can now leave the computer!" -ForegroundColor Green
Write-Host ""
Write-Host "  To check progress:" -ForegroundColor DarkGray
Write-Host "    Get-Content .\linear-progress.json | ConvertFrom-Json" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  To stop: Press Ctrl+C" -ForegroundColor DarkGray
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Start daemon
try {
    python @PythonArgs
    $ExitCode = $LASTEXITCODE
}
catch {
    Write-Host "ERROR: Failed to start daemon: $_" -ForegroundColor Red
    exit 1
}

# Report exit
if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "Daemon completed successfully!" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Daemon exited with code $ExitCode" -ForegroundColor Yellow
    Write-Host "Check linear-progress.json for details" -ForegroundColor Yellow
}

exit $ExitCode
