# Task: Start Linear Development Daemon

## Purpose
Start the background daemon for 24/7 unattended sequential Story development.

## Prerequisites
- Worktrees must already exist (run `*init` first)
- No daemon currently running
- Python 3.9+ available

## Input
- **Stories**: Comma-separated list of Story IDs (e.g., "15.1,15.2,15.3")
- **MaxTurns** (optional): Maximum turns per Claude session (default: 200)

## Steps

### Step 1: Validate Worktrees Exist

```powershell
# Check each Story has a worktree
$BasePath = "C:\Users\ROG\托福"
$Stories = $args[0] -split ","
$Missing = @()

foreach ($story in $Stories) {
    $story = $story.Trim()
    $worktreePath = Join-Path $BasePath "Canvas-develop-$story"
    if (-not (Test-Path $worktreePath)) {
        $Missing += $story
    }
}

if ($Missing.Count -gt 0) {
    Write-Host "ERROR: Missing worktrees for Stories: $($Missing -join ', ')" -ForegroundColor Red
    Write-Host "Please run '*init $($args[0])' first to create worktrees." -ForegroundColor Yellow
    exit 1
}
```

**Output**: If any worktrees missing, show error and exit.

### Step 2: Check Existing Daemon

```powershell
$ProgressFile = "C:\Users\ROG\托福\Canvas\linear-progress.json"

if (Test-Path $ProgressFile) {
    $progress = Get-Content $ProgressFile | ConvertFrom-Json
    if ($progress.status -eq "in_progress") {
        Write-Host "WARNING: Daemon already running!" -ForegroundColor Yellow
        Write-Host "  Session: $($progress.session_id)"
        Write-Host "  PID: $($progress.daemon_pid)"
        Write-Host ""
        Write-Host "Use '*linear-status' to check progress or '*linear-stop' to stop." -ForegroundColor Cyan
        exit 1
    }
}
```

**Output**: If daemon already running, show warning and exit.

### Step 3: Start Background Daemon

```powershell
$ScriptPath = "C:\Users\ROG\托福\Canvas\scripts\start-linear-daemon.ps1"
$Stories = $args[0]
$MaxTurns = if ($args[1]) { $args[1] } else { 200 }

# Start as hidden background process
$ProcessArgs = "-NoProfile -WindowStyle Hidden -File `"$ScriptPath`" -Stories `"$Stories`" -MaxTurns $MaxTurns"

$Process = Start-Process powershell -ArgumentList $ProcessArgs -WindowStyle Hidden -PassThru

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  Linear Development Daemon Started!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "  Stories: $Stories"
Write-Host "  Max Turns: $MaxTurns"
Write-Host "  Daemon PID: $($Process.Id)"
Write-Host ""
Write-Host "  The daemon is now running in the background." -ForegroundColor Green
Write-Host "  You can safely close this terminal or leave the computer!" -ForegroundColor Green
Write-Host ""
Write-Host "  Commands:" -ForegroundColor DarkGray
Write-Host "    *linear-status  - Check progress" -ForegroundColor DarkGray
Write-Host "    *linear-stop    - Stop daemon" -ForegroundColor DarkGray
Write-Host "    *linear-resume  - Resume if interrupted" -ForegroundColor DarkGray
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
```

## Output Format

### Success
```
======================================================================
  Linear Development Daemon Started!
======================================================================

  Stories: 15.1,15.2,15.3,15.4,15.5,15.6
  Max Turns: 200
  Daemon PID: 12345

  The daemon is now running in the background.
  You can safely close this terminal or leave the computer!

  Commands:
    *linear-status  - Check progress
    *linear-stop    - Stop daemon
    *linear-resume  - Resume if interrupted

======================================================================
```

### Error - Missing Worktrees
```
ERROR: Missing worktrees for Stories: 15.4, 15.5
Please run '*init 15.1,15.2,15.3,15.4,15.5,15.6' first to create worktrees.
```

### Error - Daemon Already Running
```
WARNING: Daemon already running!
  Session: linear-20251127-143022
  PID: 12345

Use '*linear-status' to check progress or '*linear-stop' to stop.
```

## Progress Tracking

The daemon writes progress to `linear-progress.json`:

```json
{
  "version": "2.0",
  "session_id": "linear-20251127-143022",
  "daemon_pid": 12345,
  "stories": ["15.1", "15.2", "15.3"],
  "current_index": 1,
  "status": "in_progress",
  "completed_stories": [
    {"story_id": "15.1", "outcome": "SUCCESS", "commit_sha": "abc1234"}
  ],
  "current_story": {
    "story_id": "15.2",
    "started_at": "2025-11-27T15:00:00Z"
  }
}
```

## Notes

- Daemon runs completely in background (no visible window)
- Handles Claude session compact/crash automatically
- Retries blocked Stories once before halting
- Progress persisted for crash recovery
- Circuit breaker: max 5 compact restarts per Story
