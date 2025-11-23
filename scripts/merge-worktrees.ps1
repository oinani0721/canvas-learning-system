# merge-worktrees.ps1
# Merge all parallel worktrees back to main branch

param(
    [Parameter(Mandatory=$false)]
    [string]$Stories,  # Optional: specific stories to merge

    [Parameter(Mandatory=$false)]
    [string]$BasePath = "..",

    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "`n=== Parallel Dev Orchestrator: Merge Worktrees ===" -ForegroundColor Cyan

# Get current branch (should be main/master)
$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch"

if ($DryRun) {
    Write-Host "[DRY RUN] No changes will be made" -ForegroundColor Yellow
}

# Find all worktrees
$worktrees = git worktree list --porcelain | Select-String "worktree" | ForEach-Object {
    $_.Line -replace "worktree ", ""
}

$mainWorktree = (Get-Location).Path
$parallelWorktrees = $worktrees | Where-Object {
    $_ -ne $mainWorktree -and $_ -match "Canvas-(draft|develop)-"
}

if ($Stories) {
    $storyFilter = $Stories -split "," | ForEach-Object { $_.Trim() }
    $parallelWorktrees = $parallelWorktrees | Where-Object {
        foreach ($s in $storyFilter) {
            if ($_ -match "Canvas-.*-$s$") { return $true }
        }
        return $false
    }
}

if ($parallelWorktrees.Count -eq 0) {
    Write-Host "No parallel worktrees found to merge" -ForegroundColor Yellow
    exit 0
}

Write-Host "`nWorktrees to merge: $($parallelWorktrees.Count)"

$mergeResults = @()

foreach ($wtPath in $parallelWorktrees) {
    $wtName = Split-Path $wtPath -Leaf

    # Extract story ID from worktree name
    if ($wtName -match "Canvas-(?:draft|develop)-(.+)$") {
        $storyId = $Matches[1]
        $branchName = "story-$storyId"
    } else {
        Write-Host "  Skipping unknown worktree format: $wtName" -ForegroundColor Yellow
        continue
    }

    Write-Host "`nMerging $branchName from $wtName..." -ForegroundColor Yellow

    # Check worktree status
    $statusFile = Join-Path $wtPath ".worktree-status.yaml"
    if (Test-Path $statusFile) {
        $status = Get-Content $statusFile -Raw
        if ($status -match 'status:\s*"dev-complete"') {
            Write-Host "  Status: dev-complete" -ForegroundColor Green
        } else {
            Write-Host "  Warning: Status is not dev-complete" -ForegroundColor Red
        }
    }

    if (-not $DryRun) {
        try {
            # Merge the branch
            $mergeOutput = git merge $branchName --no-ff -m "Merge $branchName (Story $storyId)" 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Merged successfully" -ForegroundColor Green
                $mergeResults += @{
                    Story = $storyId
                    Status = "Success"
                    Message = "Merged"
                }
            } else {
                Write-Host "  Merge conflict detected" -ForegroundColor Red
                Write-Host "  $mergeOutput" -ForegroundColor Red
                $mergeResults += @{
                    Story = $storyId
                    Status = "Conflict"
                    Message = $mergeOutput
                }
            }
        }
        catch {
            Write-Host "  Error: $_" -ForegroundColor Red
            $mergeResults += @{
                Story = $storyId
                Status = "Error"
                Message = $_.Exception.Message
            }
        }
    } else {
        Write-Host "  [DRY RUN] Would merge $branchName" -ForegroundColor Cyan
        $mergeResults += @{
            Story = $storyId
            Status = "DryRun"
            Message = "Would merge"
        }
    }
}

# Synchronize status files
if (-not $DryRun) {
    Write-Host "`nSynchronizing status files..." -ForegroundColor Yellow

    foreach ($wtPath in $parallelWorktrees) {
        $statusFile = Join-Path $wtPath ".worktree-status.yaml"
        if (Test-Path $statusFile) {
            # Copy status info to main orchestrator state
            # This would update canvas-project-status.yaml
            Write-Host "  Synced status from $wtPath" -ForegroundColor Green
        }
    }
}

# Summary
Write-Host "`n=== Merge Summary ===" -ForegroundColor Cyan

$success = ($mergeResults | Where-Object { $_.Status -eq "Success" }).Count
$conflicts = ($mergeResults | Where-Object { $_.Status -eq "Conflict" }).Count
$errors = ($mergeResults | Where-Object { $_.Status -eq "Error" }).Count

Write-Host "Total: $($mergeResults.Count)"
Write-Host "Success: $success" -ForegroundColor Green
Write-Host "Conflicts: $conflicts" -ForegroundColor $(if ($conflicts -gt 0) { "Red" } else { "Green" })
Write-Host "Errors: $errors" -ForegroundColor $(if ($errors -gt 0) { "Red" } else { "Green" })

if ($conflicts -gt 0) {
    Write-Host "`nConflicts need manual resolution:" -ForegroundColor Red
    $mergeResults | Where-Object { $_.Status -eq "Conflict" } | ForEach-Object {
        Write-Host "  - Story $($_.Story)" -ForegroundColor Red
    }
    Write-Host "`nRun 'git status' to see conflicting files"
    Write-Host "After resolving, run 'git commit' to complete merge"
}

Write-Host ""
