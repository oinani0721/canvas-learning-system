# init-worktrees.ps1
# Create multiple Git worktrees for parallel development

param(
    [Parameter(Mandatory=$true)]
    [string]$Stories,  # Comma-separated: "13.1,13.2,13.3"

    [Parameter(Mandatory=$false)]
    [ValidateSet("draft", "develop")]
    [string]$Phase = "develop",

    [Parameter(Mandatory=$false)]
    [string]$BasePath = ".."
)

$ErrorActionPreference = "Stop"

Write-Host "`n=== Parallel Dev Orchestrator: Init Worktrees ===" -ForegroundColor Cyan
Write-Host "Phase: $Phase"
Write-Host "Stories: $Stories"
Write-Host "Base Path: $BasePath"
Write-Host ""

$storyList = $Stories -split ","
$createdWorktrees = @()

foreach ($story in $storyList) {
    $story = $story.Trim()
    $worktreeName = "Canvas-$Phase-$story"
    $worktreePath = Join-Path $BasePath $worktreeName
    $branchName = "story-$story"

    Write-Host "Creating worktree for Story $story..." -ForegroundColor Yellow

    # Check if worktree already exists
    if (Test-Path $worktreePath) {
        Write-Host "  Warning: Worktree already exists at $worktreePath" -ForegroundColor Red
        Write-Host "  Run cleanup-worktrees.ps1 first or remove manually" -ForegroundColor Red
        continue
    }

    # Create Git worktree with new branch
    $oldErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $result = git worktree add $worktreePath -b $branchName 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $oldErrorAction

    if ($exitCode -ne 0) {
        # Branch might already exist, try without -b
        $ErrorActionPreference = "SilentlyContinue"
        $result = git worktree add $worktreePath $branchName 2>&1
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $oldErrorAction

        if ($exitCode -ne 0) {
            Write-Host "  Error creating worktree: $result" -ForegroundColor Red
            continue
        }
        Write-Host "  Created worktree (existing branch): $worktreePath" -ForegroundColor Green
    } else {
        Write-Host "  Created worktree: $worktreePath" -ForegroundColor Green
    }

    # Create .ai-context.md if template exists
    $templatePath = ".ai-context-template.md"
    $contextPath = Join-Path $worktreePath ".ai-context.md"

    if (Test-Path $templatePath) {
        $content = Get-Content $templatePath -Raw
        $content = $content -replace '\{story\}', $story
        $content = $content -replace '\{phase\}', $Phase
        $content | Out-File $contextPath -Encoding utf8
        Write-Host "  Created .ai-context.md" -ForegroundColor Green
    }

    # Create .worktree-status.yaml
    $statusPath = Join-Path $worktreePath ".worktree-status.yaml"
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

    @"
story: "$story"
phase: "$Phase"
status: "pending"
started_at: "$timestamp"
completed_at: null
affected_files: []
tests_passed: false
test_count: 0
test_failures: 0
"@ | Out-File $statusPath -Encoding utf8

    Write-Host "  Created .worktree-status.yaml" -ForegroundColor Green

    $createdWorktrees += @{
        Story = $story
        Path = $worktreePath
        Branch = $branchName
    }
}

# Output launch commands
Write-Host "`n=== Launch Commands ===" -ForegroundColor Cyan
Write-Host "Run each command in a separate terminal tab:`n"

$tabNum = 1
foreach ($wt in $createdWorktrees) {
    $command = if ($Phase -eq "draft") {
        "@sm *draft Story-$($wt.Story)"
    } else {
        "@dev *develop-story Story-$($wt.Story)"
    }

    Write-Host "[Tab $tabNum] cd `"$($wt.Path)`" && claude $command" -ForegroundColor White
    $tabNum++
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Created $($createdWorktrees.Count) worktrees"
Write-Host "Run 'check-worktree-status.ps1' to monitor progress"
Write-Host ""
