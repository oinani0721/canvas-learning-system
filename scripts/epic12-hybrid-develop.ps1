# Epic 12 Hybrid Development Script (Parallel + Sequential)
# Usage: .\scripts\epic12-hybrid-develop.ps1 [-Mode "parallel"|"linear"|"hybrid"]
#
# Modes:
#   parallel - Launch 3 parallel windows for Wave 1 (12.1, 12.2, 12.4)
#   linear   - Sequential development 12.1-12.10 in optimal order
#   hybrid   - 3 parallel tracks, each doing sequential development

param(
    [ValidateSet("parallel", "linear", "hybrid")]
    [string]$Mode = "hybrid",
    [switch]$UltraThink,
    [string]$StopAt = "12.10"
)

# 动态获取项目根目录，避免中文路径编码问题
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Dependency-aware optimal order
$OptimalOrder = @(
    "12.1",  # Wave 1 - No dependency
    "12.2",  # Wave 1 - No dependency
    "12.4",  # Wave 1 - No dependency
    "12.3",  # Depends on 12.2
    "12.5",  # Depends on 12.1
    "12.6",  # Depends on 12.5
    "12.7",  # Depends on 12.6 (can parallel with 12.8)
    "12.8",  # Depends on 12.6 (can parallel with 12.7)
    "12.9",  # Depends on 12.7, 12.8
    "12.10"  # Depends on 12.9
)

# Track definitions for hybrid mode
$Track1 = @("12.1", "12.5", "12.6", "12.7", "12.9", "12.10")  # Main critical path
$Track2 = @("12.2", "12.3")                                    # LanceDB track
$Track3 = @("12.4", "12.8")                                    # Temporal + Reranking

# Phase 1 Fix: Use prompt file to avoid nested quote issues
function Start-ClaudeSession {
    param(
        [string]$StoryId,
        [string]$WorktreePath,
        [switch]$Hidden
    )

    # 1. Create prompt file (avoid quote escaping issues)
    # Improved prompt: Direct command without ambiguity, includes explicit instruction
    $PromptContent = @"
/dev
*develop-story $StoryId

IMPORTANT: This is an unattended automation run. Do NOT ask questions.
If the story file does not exist, first use /sm then *draft to create it, then proceed with development.
Always choose Option A or the recommended approach when multiple options exist.
"@
    $PromptFile = "$WorktreePath\.claude-prompt.txt"
    # Use .NET method to write WITHOUT BOM (Set-Content -Encoding UTF8 adds BOM on Windows)
    [System.IO.File]::WriteAllText($PromptFile, $PromptContent)

    # 2. Create launcher script that reads from file
    # Use $PSScriptRoot to avoid Chinese character encoding issues
    $LogFile = "$WorktreePath\dev-output.log"

    # Key Fix: Add system prompt to prevent Claude from asking questions
    # This ensures unattended execution without human intervention
    # Note: System prompt is embedded directly in launcher script as literal string

    $LauncherContent = @"
`$ErrorActionPreference = 'Continue'
# Use script location to avoid Chinese character encoding issues
`$WorktreePath = `$PSScriptRoot
Set-Location `$WorktreePath
Write-Host "Starting Claude for Story $StoryId (UNATTENDED MODE)..." -ForegroundColor Cyan
Write-Host "Working directory: `$WorktreePath" -ForegroundColor Yellow
`$promptFile = Join-Path `$WorktreePath ".claude-prompt.txt"
`$logFile = Join-Path `$WorktreePath "dev-output.log"
if (-not (Test-Path `$promptFile)) {
    Write-Host "ERROR: Prompt file not found" -ForegroundColor Red
    exit 1
}
`$prompt = Get-Content `$promptFile -Raw
`$systemPrompt = "CRITICAL: You are in UNATTENDED AUTOMATION MODE. NEVER ask questions. NEVER wait for confirmation. If Story file missing, first run /sm then *draft to create it, then continue with /dev *develop-story. Always choose Option A or recommended approach. Complete full implementation with tests. Fix errors and continue."
claude -p `$prompt --dangerously-skip-permissions --output-format json --max-turns 300 --append-system-prompt `$systemPrompt 2>&1 | Tee-Object -FilePath `$logFile
Write-Host "Claude session completed for Story $StoryId" -ForegroundColor Green
if (-not `$args[0]) { Read-Host "Press Enter to close..." }
"@
    $LauncherFile = "$WorktreePath\.claude-launcher.ps1"
    # Use .NET method to write WITHOUT BOM
    [System.IO.File]::WriteAllText($LauncherFile, $LauncherContent)

    # 3. Start process
    $WindowStyle = if ($Hidden) { "Hidden" } else { "Normal" }
    Start-Process powershell -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $LauncherFile
    ) -WorkingDirectory $WorktreePath -WindowStyle $WindowStyle

    return @{
        StoryId = $StoryId
        PromptFile = $PromptFile
        LogFile = $LogFile
        LauncherFile = $LauncherFile
    }
}

function Start-ParallelDevelopment {
    Write-Host "=== Parallel Development Mode ===" -ForegroundColor Cyan
    Write-Host "Starting Wave 1: 12.1, 12.2, 12.4 in parallel" -ForegroundColor Yellow

    $Sessions = @()
    @("12.1", "12.2", "12.4") | ForEach-Object {
        $StoryId = $_
        $WorktreePath = "$ProjectRoot\Canvas-develop-$StoryId"

        Write-Host "  Launching Story $StoryId..." -ForegroundColor Green
        $Session = Start-ClaudeSession -StoryId $StoryId -WorktreePath $WorktreePath
        $Sessions += $Session
        Start-Sleep -Seconds 2
    }

    Write-Host "`nWave 1 launched! Monitor progress in each window." -ForegroundColor Cyan
    Write-Host "Log files:" -ForegroundColor Yellow
    $Sessions | ForEach-Object { Write-Host "  $_($_.StoryId): $($_.LogFile)" }
}

function Start-LinearDevelopment {
    Write-Host "=== Linear Development Mode ===" -ForegroundColor Cyan
    Write-Host "Sequential order: $($OptimalOrder -join ' -> ')" -ForegroundColor Yellow

    # Filter stories up to StopAt
    $StopIndex = [Array]::IndexOf($OptimalOrder, $StopAt)
    if ($StopIndex -lt 0) { $StopIndex = $OptimalOrder.Length - 1 }
    $StoriesToDevelop = $OptimalOrder[0..$StopIndex]

    Write-Host "Will develop: $($StoriesToDevelop -join ', ')" -ForegroundColor Green

    # Generate linear daemon config
    $ConfigPath = "$ProjectRoot\.bmad-core\data\linear-progress.json"
    $Config = @{
        mode = "linear"
        stories = $StoriesToDevelop
        current_index = 0
        status = "initialized"
        ultrathink = $UltraThink.IsPresent
        started_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    }
    # Use .NET method to write WITHOUT BOM
    $ConfigJson = $Config | ConvertTo-Json
    [System.IO.File]::WriteAllText($ConfigPath, $ConfigJson)

    Write-Host "`nLinear config saved to: $ConfigPath" -ForegroundColor Cyan
    Write-Host "Run: python scripts/daemon/linear_develop_daemon.py" -ForegroundColor Yellow
}

function Start-HybridDevelopment {
    Write-Host "=== Hybrid Development Mode (3 Parallel Tracks) ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Track 1 (Critical Path): $($Track1 -join ' -> ')" -ForegroundColor Yellow
    Write-Host "Track 2 (LanceDB):       $($Track2 -join ' -> ')" -ForegroundColor Yellow
    Write-Host "Track 3 (Temporal+Rerank): $($Track3 -join ' -> ')" -ForegroundColor Yellow
    Write-Host ""

    # Launch 3 windows, each with its track
    $Tracks = @(
        @{ Name = "Track1-CriticalPath"; Stories = $Track1 },
        @{ Name = "Track2-LanceDB"; Stories = $Track2 },
        @{ Name = "Track3-TemporalRerank"; Stories = $Track3 }
    )

    $Sessions = @()
    foreach ($Track in $Tracks) {
        $TrackName = $Track.Name
        $Stories = $Track.Stories
        $FirstStory = $Stories[0]
        $WorktreePath = "$ProjectRoot\Canvas-develop-$FirstStory"

        # Create track config
        $TrackConfig = @{
            track_name = $TrackName
            stories = $Stories
            current_index = 0
            ultrathink = $UltraThink.IsPresent
        }
        $TrackConfigPath = "$WorktreePath\.track-config.json"
        try {
            # Use .NET method to write WITHOUT BOM
            $TrackConfigJson = $TrackConfig | ConvertTo-Json
            [System.IO.File]::WriteAllText($TrackConfigPath, $TrackConfigJson)
        } catch {
            Write-Host "  Warning: Could not write track config for $TrackName" -ForegroundColor Yellow
        }

        Write-Host "  Launching $TrackName (starting with $FirstStory)..." -ForegroundColor Green
        $Session = Start-ClaudeSession -StoryId $FirstStory -WorktreePath $WorktreePath
        $Sessions += $Session
        Start-Sleep -Seconds 3
    }

    Write-Host "`n3 Tracks launched! Each track will develop stories sequentially." -ForegroundColor Cyan
    Write-Host "Total parallelism: 3 Claude Code sessions" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Log files for monitoring:" -ForegroundColor Green
    $Sessions | ForEach-Object { Write-Host "  Story $($_.StoryId): $($_.LogFile)" }
}

# Main execution
Write-Host ""
Write-Host "============================================" -ForegroundColor Magenta
Write-Host " Epic 12 Development Launcher" -ForegroundColor Magenta
Write-Host " Mode: $Mode | UltraThink: $UltraThink | Stop At: $StopAt" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
Write-Host ""

switch ($Mode) {
    "parallel" { Start-ParallelDevelopment }
    "linear"   { Start-LinearDevelopment }
    "hybrid"   { Start-HybridDevelopment }
}

Write-Host ""
Write-Host "Done! Check opened PowerShell windows for progress." -ForegroundColor Green
