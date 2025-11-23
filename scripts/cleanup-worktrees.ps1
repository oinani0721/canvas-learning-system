# cleanup-worktrees.ps1
# Remove all parallel development worktrees

param(
    [Parameter(Mandatory=$false)]
    [string]$BasePath = "..",

    [Parameter(Mandatory=$false)]
    [switch]$Force,

    [Parameter(Mandatory=$false)]
    [switch]$DeleteBranches
)

$ErrorActionPreference = "Stop"

Write-Host "`n=== Parallel Dev Orchestrator: Cleanup Worktrees ===" -ForegroundColor Cyan

# Find all worktrees (handle encoding for non-ASCII paths)
$oldEncoding = [Console]::OutputEncoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$worktrees = git worktree list --porcelain | Select-String "worktree" | ForEach-Object {
    $_.Line -replace "worktree ", ""
}
[Console]::OutputEncoding = $oldEncoding

$mainWorktree = (Get-Location).Path
$parallelWorktrees = $worktrees | Where-Object {
    $_ -ne $mainWorktree -and $_ -match "Canvas-(draft|develop)-"
}

if ($parallelWorktrees.Count -eq 0) {
    Write-Host "No parallel worktrees found to clean up" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($parallelWorktrees.Count) parallel worktree(s) to remove:`n"

foreach ($wtPath in $parallelWorktrees) {
    Write-Host "  - $wtPath"
}

if (-not $Force) {
    Write-Host "`nThis will remove the above worktrees and their files." -ForegroundColor Yellow
    $confirm = Read-Host "Continue? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Cancelled" -ForegroundColor Red
        exit 0
    }
}

$branchesToDelete = @()

foreach ($wtPath in $parallelWorktrees) {
    $wtName = Split-Path $wtPath -Leaf

    Write-Host "`nRemoving worktree: $wtName..." -ForegroundColor Yellow

    # Extract branch name
    if ($wtName -match "Canvas-(?:draft|develop)-(.+)$") {
        $storyId = $Matches[1]
        $branchName = "story-$storyId"
        $branchesToDelete += $branchName
    }

    # Normalize path for Windows
    $normalizedPath = $wtPath -replace '/', '\'

    # Suppress errors for git commands
    $oldErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"

    # Remove worktree
    $result = git worktree remove $normalizedPath --force 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $oldErrorAction

    if ($exitCode -eq 0) {
        Write-Host "  Removed worktree" -ForegroundColor Green
    } else {
        Write-Host "  Error removing worktree: $result" -ForegroundColor Red
    }

    # Clean up directory if it still exists
    if (Test-Path $normalizedPath) {
        Remove-Item $normalizedPath -Recurse -Force
        Write-Host "  Cleaned up directory" -ForegroundColor Green
    }
}

# Prune worktree list
Write-Host "`nPruning worktree list..." -ForegroundColor Yellow
git worktree prune
Write-Host "  Pruned" -ForegroundColor Green

# Optionally delete branches
if ($DeleteBranches -and $branchesToDelete.Count -gt 0) {
    Write-Host "`nDeleting story branches..." -ForegroundColor Yellow

    foreach ($branch in $branchesToDelete) {
        try {
            git branch -D $branch 2>&1 | Out-Null
            Write-Host "  Deleted branch: $branch" -ForegroundColor Green
        }
        catch {
            Write-Host "  Could not delete branch $branch (may be merged or current)" -ForegroundColor Yellow
        }
    }
} elseif ($branchesToDelete.Count -gt 0) {
    Write-Host "`nNote: Story branches were kept. To delete them, run:" -ForegroundColor Yellow
    Write-Host "  .\cleanup-worktrees.ps1 -DeleteBranches"
}

Write-Host "`n=== Cleanup Complete ===" -ForegroundColor Cyan
Write-Host "Removed $($parallelWorktrees.Count) worktree(s)"
Write-Host ""
