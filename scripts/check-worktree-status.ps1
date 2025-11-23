# check-worktree-status.ps1
# Check status of all parallel development worktrees

param(
    [Parameter(Mandatory=$false)]
    [string]$BasePath = "..",

    [Parameter(Mandatory=$false)]
    [switch]$Watch,

    [Parameter(Mandatory=$false)]
    [int]$Interval = 30  # seconds
)

function Get-WorktreeStatuses {
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

    $statuses = @()

    foreach ($wtPath in $parallelWorktrees) {
        $wtName = Split-Path $wtPath -Leaf
        $statusFile = Join-Path $wtPath ".worktree-status.yaml"

        $statusObj = @{
            Name = $wtName
            Path = $wtPath
            Story = ""
            Phase = ""
            Status = "unknown"
            TestsPassed = $false
        }

        # Extract story ID
        if ($wtName -match "Canvas-(draft|develop)-(.+)$") {
            $statusObj.Phase = $Matches[1]
            $statusObj.Story = $Matches[2]
        }

        # Read status file (normalize path for Windows)
        $normalizedPath = $wtPath -replace '/', '\'
        $statusFile = Join-Path $normalizedPath ".worktree-status.yaml"
        if (Test-Path $statusFile) {
            # Read file lines and parse
            $lines = Get-Content $statusFile

            foreach ($line in $lines) {
                if ($line -match 'status:\s*"([^"]+)"') {
                    $statusObj.Status = $Matches[1]
                }
                if ($line -match 'tests_passed:\s*(true|false)') {
                    $statusObj.TestsPassed = $Matches[1] -eq "true"
                }
            }
        }

        $statuses += $statusObj
    }

    return $statuses
}

function Show-StatusTable {
    param($Statuses)

    Clear-Host
    Write-Host "`n=== Parallel Dev Orchestrator: Worktree Status ===" -ForegroundColor Cyan
    Write-Host "Updated: $(Get-Date -Format 'HH:mm:ss')`n"

    if ($Statuses.Count -eq 0) {
        Write-Host "No parallel worktrees found" -ForegroundColor Yellow
        return
    }

    # Header
    $format = "{0,-25} {1,-10} {2,-15} {3,-12}"
    Write-Host ($format -f "Worktree", "Story", "Status", "Tests") -ForegroundColor White
    Write-Host ("-" * 65)

    # Rows
    foreach ($s in $Statuses) {
        $statusColor = switch ($s.Status) {
            "completed" { "Green" }
            "dev-complete" { "Green" }
            "in-progress" { "Yellow" }
            "pending" { "Gray" }
            default { "Red" }
        }

        $testsDisplay = if ($s.TestsPassed) { "Passed" } else { "Not Run" }
        $testsColor = if ($s.TestsPassed) { "Green" } else { "Gray" }

        Write-Host -NoNewline ($format -f $s.Name, $s.Story, "", "")
        Write-Host -NoNewline $s.Status.PadRight(15) -ForegroundColor $statusColor
        Write-Host $testsDisplay -ForegroundColor $testsColor
    }

    # Summary
    $total = $Statuses.Count
    $completed = ($Statuses | Where-Object { $_.Status -in @("completed", "dev-complete") }).Count
    $inProgress = ($Statuses | Where-Object { $_.Status -eq "in-progress" }).Count
    $pending = ($Statuses | Where-Object { $_.Status -eq "pending" }).Count

    Write-Host "`n--- Summary ---"
    Write-Host "Total: $total | " -NoNewline
    Write-Host "Completed: $completed" -ForegroundColor Green -NoNewline
    Write-Host " | " -NoNewline
    Write-Host "In Progress: $inProgress" -ForegroundColor Yellow -NoNewline
    Write-Host " | " -NoNewline
    Write-Host "Pending: $pending" -ForegroundColor Gray

    # Check if all complete
    if ($completed -eq $total -and $total -gt 0) {
        Write-Host "`nAll worktrees complete! Ready for merge." -ForegroundColor Green
    }
}

# Main
if ($Watch) {
    Write-Host "Watching worktree status (Ctrl+C to stop)..." -ForegroundColor Cyan

    while ($true) {
        $statuses = Get-WorktreeStatuses
        Show-StatusTable $statuses

        Write-Host "`nRefreshing in $Interval seconds... (Ctrl+C to stop)" -ForegroundColor Gray
        Start-Sleep -Seconds $Interval
    }
} else {
    $statuses = Get-WorktreeStatuses
    Show-StatusTable $statuses
    Write-Host ""
}
