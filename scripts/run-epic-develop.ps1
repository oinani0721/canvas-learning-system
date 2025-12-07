# Epic Develop Launcher Script
# Sets proper encoding and PYTHONPATH for bmad_orchestrator

param(
    [Parameter(Mandatory=$true)]
    [string]$EpicId,

    [Parameter(Mandatory=$true)]
    [string]$Stories,

    [string]$Mode = "parallel",

    [switch]$DryRun,

    [switch]$Yes
)

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Set PYTHONPATH to include src directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $ProjectRoot "src"

Write-Host "========================================"
Write-Host "Epic Develop Launcher"
Write-Host "========================================"
Write-Host "Epic ID: $EpicId"
Write-Host "Stories: $Stories"
Write-Host "Mode: $Mode"
Write-Host "Dry Run: $DryRun"
Write-Host "PYTHONPATH: $env:PYTHONPATH"
Write-Host "========================================"

# Build arguments
$StoryList = $Stories -split "," | ForEach-Object { $_.Trim() }
$Args = @(
    "-m", "bmad_orchestrator",
    "epic-develop", $EpicId,
    "--stories"
) + $StoryList + @(
    "--mode", $Mode
)

if ($DryRun) {
    $Args += "--dry-run"
}

if ($Yes) {
    $Args += "--yes"
}

# Run the orchestrator
Set-Location $ProjectRoot
python @Args
