<#
.SYNOPSIS
    Wave-Based Parallel + Sequential Development Engine for Epic Development

.DESCRIPTION
    Executes Epic stories in waves, supporting both parallel and sequential execution
    with integrated BMad QA workflow.

.PARAMETER Epic
    Epic number to develop (e.g., "12")

.PARAMETER StartWave
    Starting wave number (default: auto-detect first incomplete)

.PARAMETER EndWave
    Ending wave number (default: all waves)

.PARAMETER QAMode
    QA mode: "integrated" (per-story) or "batch" (per-wave)

.PARAMETER MaxParallel
    Maximum concurrent worktrees (default: 3)

.PARAMETER UltraThink
    Enable extended thinking mode

.PARAMETER StatusOnly
    Only show status, don't execute

.EXAMPLE
    .\wave-develop.ps1 -Epic 12 -StartWave 2 -UltraThink
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Epic,

    [int]$StartWave = 0,

    [int]$EndWave = 0,

    [ValidateSet("integrated", "batch")]
    [string]$QAMode = "integrated",

    [int]$MaxParallel = 3,

    [switch]$UltraThink,

    [switch]$StatusOnly
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

# Configuration
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptsDir = $PSScriptRoot
$ConfigFile = Join-Path $ScriptsDir "wave-config-epic$Epic.json"
$ProgressFile = Join-Path $ScriptsDir "wave-progress.json"
$MaxTurns = 300
$TimeoutSeconds = 7200  # 2 hours

# ============================================================================
# Helper Functions
# ============================================================================

function Write-WaveLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO" { "Cyan" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Get-WaveConfig {
    if (-not (Test-Path $ConfigFile)) {
        Write-WaveLog "Wave config not found, generating default for Epic $Epic..." "WARNING"
        New-DefaultWaveConfig
    }
    return Get-Content $ConfigFile -Raw | ConvertFrom-Json
}

function New-DefaultWaveConfig {
    # Generate default wave config for Epic 12
    $config = @{
        epic = [int]$Epic
        created = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        waves = @(
            @{
                id = 1
                stories = @("12.1", "12.2", "12.4")
                mode = "parallel"
                status = "completed"
                description = "Foundation Layer: Graphiti, LanceDB POC, Temporal Memory"
            },
            @{
                id = 2
                stories = @("12.3", "12.5")
                mode = "parallel"
                status = "pending"
                description = "Migration & StateGraph: ChromaDB→LanceDB, LangGraph基础"
                dependencies = @{
                    "12.3" = @("12.2")
                    "12.5" = @("12.1")
                }
            },
            @{
                id = 3
                stories = @("12.6")
                mode = "sequential"
                status = "pending"
                description = "Parallel Retrieval: Send模式并行检索"
                dependencies = @{
                    "12.6" = @("12.5")
                }
            },
            @{
                id = 4
                stories = @("12.7", "12.8")
                mode = "parallel"
                status = "pending"
                description = "Fusion & Reranking: 3种融合算法 + 混合Reranking"
                dependencies = @{
                    "12.7" = @("12.6")
                    "12.8" = @("12.6", "12.4")
                }
            },
            @{
                id = 5
                stories = @("12.9")
                mode = "sequential"
                status = "pending"
                description = "Quality Control: 质量控制循环"
                dependencies = @{
                    "12.9" = @("12.7", "12.8")
                }
            },
            @{
                id = 6
                stories = @("12.10")
                mode = "sequential"
                status = "pending"
                description = "Canvas Integration: 检验白板生成集成"
                dependencies = @{
                    "12.10" = @("12.9")
                }
            }
        )
    }

    $config | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile -Encoding UTF8
    Write-WaveLog "Created default wave config: $ConfigFile" "SUCCESS"
}

function Get-WaveProgress {
    if (Test-Path $ProgressFile) {
        return Get-Content $ProgressFile -Raw | ConvertFrom-Json
    }
    return @{
        epic = [int]$Epic
        startTime = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        stories = @{}
        totalCost = 0.0
    }
}

function Save-WaveProgress {
    param($Progress)
    $Progress | ConvertTo-Json -Depth 10 | Set-Content $ProgressFile -Encoding UTF8
}

function Show-WaveStatus {
    param($Config, $Progress)

    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host " 📊 Wave Development Status - Epic $Epic" -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

    foreach ($wave in $Config.waves) {
        $waveStatus = switch ($wave.status) {
            "completed" { "✅ COMPLETED" }
            "in_progress" { "🔄 IN_PROGRESS" }
            "pending" { "⏳ PENDING" }
            "failed" { "❌ FAILED" }
            default { "❓ UNKNOWN" }
        }

        $statusColor = switch ($wave.status) {
            "completed" { "Green" }
            "in_progress" { "Yellow" }
            "pending" { "DarkGray" }
            "failed" { "Red" }
            default { "Gray" }
        }

        Write-Host ""
        Write-Host "Wave $($wave.id): $waveStatus" -ForegroundColor $statusColor
        Write-Host "  $($wave.description)" -ForegroundColor DarkGray

        foreach ($story in $wave.stories) {
            $storyProgress = $Progress.stories.$story
            if ($storyProgress) {
                $devStatus = $storyProgress.devStatus ?? "pending"
                $qaStatus = $storyProgress.qaStatus ?? "pending"
                $storyLine = "  ├─ $story`: "

                $devIcon = switch ($devStatus) {
                    "completed" { "✅" }
                    "in_progress" { "🔄" }
                    "failed" { "❌" }
                    default { "⏳" }
                }

                $qaIcon = switch ($qaStatus) {
                    "pass" { "✅" }
                    "concerns" { "⚠️" }
                    "fail" { "❌" }
                    "pending" { "⏳" }
                    default { "⏳" }
                }

                Write-Host "$storyLine$devIcon DEV → $qaIcon QA" -ForegroundColor $statusColor
            } else {
                Write-Host "  ├─ $story`: ⏳ PENDING" -ForegroundColor DarkGray
            }
        }
    }

    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

    $totalCost = $Progress.totalCost ?? 0
    $startTime = $Progress.startTime
    if ($startTime) {
        $elapsed = (Get-Date) - [datetime]$startTime
        $elapsedStr = "{0:hh\:mm\:ss}" -f $elapsed
    } else {
        $elapsedStr = "N/A"
    }

    Write-Host " 💰 Cost: `$$([math]::Round($totalCost, 2)) | ⏱️ Elapsed: $elapsedStr" -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
}

function New-Worktree {
    param([string]$StoryId)

    $worktreeName = "Canvas-develop-$StoryId"
    $worktreePath = Join-Path (Split-Path $ProjectRoot -Parent) $worktreeName

    if (Test-Path $worktreePath) {
        Write-WaveLog "Worktree already exists: $worktreePath" "INFO"
        return $worktreePath
    }

    $branchName = "develop-story-$StoryId"

    Push-Location $ProjectRoot
    try {
        # Create branch if not exists
        $branchExists = git branch --list $branchName 2>$null
        if (-not $branchExists) {
            git branch $branchName main 2>&1 | Out-Null
        }

        # Create worktree
        git worktree add $worktreePath $branchName 2>&1 | Out-Null
        Write-WaveLog "Created worktree: $worktreePath" "SUCCESS"
    }
    catch {
        Write-WaveLog "Failed to create worktree: $_" "ERROR"
        return $null
    }
    finally {
        Pop-Location
    }

    return $worktreePath
}

function Start-StoryDevelopment {
    param(
        [string]$StoryId,
        [string]$WorktreePath
    )

    # Create prompt file (without BOM)
    $promptContent = @"
/dev
*develop-story $StoryId

IMPORTANT: This is an unattended automation run. Do NOT ask questions.
If the story file does not exist, first use /sm then *draft to create it, then proceed with development.
Always choose Option A or the recommended approach when multiple options exist.
"@

    $promptFile = Join-Path $WorktreePath ".claude-prompt.txt"
    [System.IO.File]::WriteAllText($promptFile, $promptContent, [System.Text.UTF8Encoding]::new($false))

    # Create launcher script
    $launcherContent = @"
`$ErrorActionPreference = 'Continue'
`$WorktreePath = `$PSScriptRoot
Set-Location `$WorktreePath
Write-Host "Starting Claude for Story $StoryId (UNATTENDED MODE)..." -ForegroundColor Cyan
`$promptFile = Join-Path `$WorktreePath ".claude-prompt.txt"
`$logFile = Join-Path `$WorktreePath "dev-output.log"
`$prompt = Get-Content `$promptFile -Raw
`$systemPrompt = "CRITICAL: You are in UNATTENDED AUTOMATION MODE. NEVER ask questions. NEVER wait for confirmation. If Story file missing, first run /sm then *draft to create it, then continue with /dev *develop-story. Always choose Option A or recommended approach. Complete full implementation with tests. Fix errors and continue."
claude -p `$prompt --dangerously-skip-permissions --output-format json --max-turns $MaxTurns --append-system-prompt `$systemPrompt 2>&1 | Tee-Object -FilePath `$logFile
Write-Host "Claude session completed for Story $StoryId" -ForegroundColor Green
"@

    $launcherFile = Join-Path $WorktreePath ".claude-launcher.ps1"
    [System.IO.File]::WriteAllText($launcherFile, $launcherContent, [System.Text.UTF8Encoding]::new($false))

    # Launch in new window
    $process = Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $launcherFile -PassThru -WorkingDirectory $WorktreePath

    Write-WaveLog "Launched Story $StoryId development (PID: $($process.Id))" "SUCCESS"

    return @{
        StoryId = $StoryId
        WorktreePath = $WorktreePath
        ProcessId = $process.Id
        StartTime = Get-Date
        LogFile = Join-Path $WorktreePath "dev-output.log"
    }
}

function Wait-StoryCompletion {
    param($Jobs, $Progress)

    $completed = @()
    $timeout = [datetime]::Now.AddSeconds($TimeoutSeconds)

    while ($Jobs.Count -gt 0 -and [datetime]::Now -lt $timeout) {
        foreach ($job in $Jobs) {
            $process = Get-Process -Id $job.ProcessId -ErrorAction SilentlyContinue

            if (-not $process -or $process.HasExited) {
                # Process completed
                $result = Get-StoryResult -Job $job

                $Progress.stories[$job.StoryId] = @{
                    devStatus = $result.status
                    devCost = $result.cost
                    devDuration = $result.duration
                    completedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                }

                $Progress.totalCost += $result.cost
                Save-WaveProgress $Progress

                $statusIcon = if ($result.status -eq "completed") { "✅" } else { "❌" }
                Write-WaveLog "$statusIcon Story $($job.StoryId) Dev: $($result.status) (Cost: `$$($result.cost))" $(if ($result.status -eq "completed") { "SUCCESS" } else { "ERROR" })

                $completed += $job
            }
        }

        # Remove completed jobs
        $Jobs = $Jobs | Where-Object { $_ -notin $completed }

        if ($Jobs.Count -gt 0) {
            Start-Sleep -Seconds 30
            Write-Host "." -NoNewline -ForegroundColor DarkGray
        }
    }

    Write-Host ""
    return $completed
}

function Get-StoryResult {
    param($Job)

    $result = @{
        status = "unknown"
        cost = 0.0
        duration = 0
        tests = 0
    }

    if (Test-Path $Job.LogFile) {
        $logContent = Get-Content $Job.LogFile -Raw -ErrorAction SilentlyContinue

        # Parse JSON output for cost and status
        try {
            $lines = $logContent -split "`n"
            foreach ($line in $lines) {
                if ($line -match '"cost_usd":\s*([\d.]+)') {
                    $result.cost += [double]$Matches[1]
                }
                if ($line -match '"result":\s*"success"' -or $line -match 'PASS' -or $line -match 'completed successfully') {
                    $result.status = "completed"
                }
            }
        } catch { }

        if ($result.status -eq "unknown") {
            # Check for completion indicators
            if ($logContent -match "Story.*completed" -or $logContent -match "All tests passed") {
                $result.status = "completed"
            } else {
                $result.status = "failed"
            }
        }
    }

    $result.duration = ((Get-Date) - $Job.StartTime).TotalSeconds

    return $result
}

function Start-StoryQA {
    param(
        [string]$StoryId,
        [string]$WorktreePath
    )

    # Create QA prompt
    $qaPrompt = @"
/qa
*review $StoryId
*gate $StoryId

IMPORTANT: This is an unattended QA run. Provide PASS, CONCERNS, or FAIL decision.
"@

    $qaPromptFile = Join-Path $WorktreePath ".claude-qa-prompt.txt"
    [System.IO.File]::WriteAllText($qaPromptFile, $qaPrompt, [System.Text.UTF8Encoding]::new($false))

    $qaLogFile = Join-Path $WorktreePath "qa-output.log"

    # Run QA
    $qaResult = & claude -p $qaPrompt --dangerously-skip-permissions --output-format json --max-turns 50 2>&1 | Tee-Object -FilePath $qaLogFile

    # Parse QA result
    $qaStatus = "unknown"
    $qaContent = Get-Content $qaLogFile -Raw -ErrorAction SilentlyContinue

    if ($qaContent -match "PASS") { $qaStatus = "pass" }
    elseif ($qaContent -match "CONCERNS") { $qaStatus = "concerns" }
    elseif ($qaContent -match "FAIL") { $qaStatus = "fail" }

    return $qaStatus
}

function Invoke-Wave {
    param(
        $Wave,
        $Progress
    )

    Write-WaveLog "Starting Wave $($Wave.id): $($Wave.description)" "INFO"
    Write-WaveLog "Stories: $($Wave.stories -join ', ')" "INFO"

    # Update wave status
    $Wave.status = "in_progress"

    # Parallel execution
    if ($Wave.mode -eq "parallel") {
        $jobs = @()

        foreach ($story in $Wave.stories) {
            if ($jobs.Count -ge $MaxParallel) {
                Write-WaveLog "Waiting for slot (max parallel: $MaxParallel)..." "INFO"
                $completed = Wait-StoryCompletion -Jobs $jobs -Progress $Progress
                $jobs = $jobs | Where-Object { $_ -notin $completed }
            }

            $worktreePath = New-Worktree -StoryId $story
            if ($worktreePath) {
                $job = Start-StoryDevelopment -StoryId $story -WorktreePath $worktreePath
                $jobs += $job

                $Progress.stories[$story] = @{
                    devStatus = "in_progress"
                    startedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                }
                Save-WaveProgress $Progress
            }
        }

        # Wait for all remaining jobs
        if ($jobs.Count -gt 0) {
            Write-WaveLog "Waiting for $($jobs.Count) remaining stories..." "INFO"
            Wait-StoryCompletion -Jobs $jobs -Progress $Progress
        }
    }
    # Sequential execution
    else {
        foreach ($story in $Wave.stories) {
            $worktreePath = New-Worktree -StoryId $story
            if ($worktreePath) {
                $job = Start-StoryDevelopment -StoryId $story -WorktreePath $worktreePath

                $Progress.stories[$story] = @{
                    devStatus = "in_progress"
                    startedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                }
                Save-WaveProgress $Progress

                Wait-StoryCompletion -Jobs @($job) -Progress $Progress
            }
        }
    }

    # QA Phase (if integrated mode)
    if ($QAMode -eq "integrated") {
        Write-WaveLog "Starting QA phase for Wave $($Wave.id)..." "INFO"

        foreach ($story in $Wave.stories) {
            $storyProgress = $Progress.stories.$story
            if ($storyProgress.devStatus -eq "completed") {
                $worktreePath = Join-Path (Split-Path $ProjectRoot -Parent) "Canvas-develop-$story"

                Write-WaveLog "Running QA for Story $story..." "INFO"
                $qaStatus = Start-StoryQA -StoryId $story -WorktreePath $worktreePath

                $Progress.stories.$story.qaStatus = $qaStatus
                Save-WaveProgress $Progress

                $qaIcon = switch ($qaStatus) {
                    "pass" { "✅" }
                    "concerns" { "⚠️" }
                    "fail" { "❌" }
                    default { "❓" }
                }

                Write-WaveLog "$qaIcon Story $story QA: $qaStatus" $(if ($qaStatus -eq "pass" -or $qaStatus -eq "concerns") { "SUCCESS" } else { "WARNING" })

                # Retry once if failed
                if ($qaStatus -eq "fail") {
                    Write-WaveLog "Retrying QA for Story $story..." "WARNING"
                    $qaStatus = Start-StoryQA -StoryId $story -WorktreePath $worktreePath
                    $Progress.stories.$story.qaStatus = $qaStatus
                    Save-WaveProgress $Progress
                }
            }
        }
    }

    # Check wave completion
    $allPassed = $true
    foreach ($story in $Wave.stories) {
        $storyProgress = $Progress.stories.$story
        if ($storyProgress.devStatus -ne "completed") {
            $allPassed = $false
        }
        if ($QAMode -eq "integrated" -and $storyProgress.qaStatus -eq "fail") {
            $allPassed = $false
        }
    }

    $Wave.status = if ($allPassed) { "completed" } else { "failed" }

    return $allPassed
}

# ============================================================================
# Main Execution
# ============================================================================

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host " 🌊 Wave-Based Development Engine v1.0" -ForegroundColor White
Write-Host " Epic $Epic | QA Mode: $QAMode | Max Parallel: $MaxParallel" -ForegroundColor DarkGray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""

# Load configuration
$config = Get-WaveConfig
$progress = Get-WaveProgress

# Status only mode
if ($StatusOnly) {
    Show-WaveStatus -Config $config -Progress $progress
    exit 0
}

# Find starting wave
if ($StartWave -eq 0) {
    foreach ($wave in $config.waves) {
        if ($wave.status -ne "completed") {
            $StartWave = $wave.id
            break
        }
    }
    if ($StartWave -eq 0) {
        Write-WaveLog "All waves completed!" "SUCCESS"
        Show-WaveStatus -Config $config -Progress $progress
        exit 0
    }
}

# Find ending wave
if ($EndWave -eq 0) {
    $EndWave = ($config.waves | Measure-Object -Property id -Maximum).Maximum
}

Write-WaveLog "Executing Waves $StartWave to $EndWave" "INFO"

# Execute waves
for ($waveNum = $StartWave; $waveNum -le $EndWave; $waveNum++) {
    $wave = $config.waves | Where-Object { $_.id -eq $waveNum }

    if (-not $wave) {
        Write-WaveLog "Wave $waveNum not found in config" "ERROR"
        continue
    }

    if ($wave.status -eq "completed") {
        Write-WaveLog "Wave $waveNum already completed, skipping..." "INFO"
        continue
    }

    $success = Invoke-Wave -Wave $wave -Progress $progress

    # Save updated config
    $config | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile -Encoding UTF8

    if (-not $success) {
        Write-WaveLog "Wave $waveNum failed, stopping execution" "ERROR"
        break
    }

    Write-WaveLog "Wave $waveNum completed successfully!" "SUCCESS"
}

# Final status
Show-WaveStatus -Config $config -Progress $progress

Write-WaveLog "Wave development completed!" "SUCCESS"
