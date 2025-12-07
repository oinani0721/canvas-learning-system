# Task: Resume Linear Development Daemon

## Purpose
Resume an interrupted daemon session from where it left off.

## Prerequisites
- Previous session exists (linear-progress.json)
- Session status is "halted" or daemon crashed
- Worktrees still exist

## Steps

### Step 1: Check Progress File

```powershell
$ProgressFile = "C:\Users\ROG\托福\Canvas\linear-progress.json"

if (-not (Test-Path $ProgressFile)) {
    Write-Host ""
    Write-Host "No linear-progress.json found." -ForegroundColor Yellow
    Write-Host "Use '*linear' to start a new daemon session." -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

$progress = Get-Content $ProgressFile -Raw | ConvertFrom-Json
```

### Step 2: Validate Session State

```powershell
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  Resuming Linear Development Daemon" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Check if daemon already running
if ($progress.status -eq "in_progress" -and $progress.daemon_pid) {
    $proc = Get-Process -Id $progress.daemon_pid -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "  Daemon already running!" -ForegroundColor Yellow
        Write-Host "    Session: $($progress.session_id)"
        Write-Host "    PID: $($progress.daemon_pid)"
        Write-Host ""
        Write-Host "  Use '*linear-status' to check progress." -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }
}

# Check if session completed
if ($progress.status -eq "completed") {
    Write-Host "  Session already completed!" -ForegroundColor Green
    Write-Host "    Session: $($progress.session_id)"
    Write-Host "    Stories: $($progress.completed_stories.Count)/$($progress.stories.Count)"
    Write-Host ""
    Write-Host "  Use '*linear' to start a new session." -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

# Show resumable session info
Write-Host "  Found resumable session:" -ForegroundColor White
Write-Host "    Session ID: $($progress.session_id)"
Write-Host "    Status: $($progress.status)" -ForegroundColor Yellow
Write-Host "    Completed: $($progress.completed_stories.Count)/$($progress.stories.Count) stories"

if ($progress.halt_reason) {
    Write-Host "    Halt Reason: $($progress.halt_reason)" -ForegroundColor DarkGray
}

$remaining = $progress.stories.Count - $progress.current_index
Write-Host ""
Write-Host "  Remaining Stories: $remaining" -ForegroundColor Cyan
for ($i = $progress.current_index; $i -lt $progress.stories.Count; $i++) {
    $storyId = $progress.stories[$i]
    if ($i -eq $progress.current_index) {
        Write-Host "    → $storyId (will restart)" -ForegroundColor Yellow
    } else {
        Write-Host "    ○ $storyId" -ForegroundColor DarkGray
    }
}

Write-Host ""
```

### Step 3: Validate Worktrees

```powershell
$BasePath = "C:\Users\ROG\托福"
$Missing = @()

for ($i = $progress.current_index; $i -lt $progress.stories.Count; $i++) {
    $storyId = $progress.stories[$i]
    $worktreePath = Join-Path $BasePath "Canvas-develop-$storyId"
    if (-not (Test-Path $worktreePath)) {
        $Missing += $storyId
    }
}

if ($Missing.Count -gt 0) {
    Write-Host "  ERROR: Missing worktrees for remaining Stories:" -ForegroundColor Red
    Write-Host "    $($Missing -join ', ')" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please run '*init' to recreate missing worktrees." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "  Worktrees: All present" -ForegroundColor Green
```

### Step 4: Start Daemon with Resume Flag

```powershell
$ScriptPath = "C:\Users\ROG\托福\Canvas\scripts\start-linear-daemon.ps1"
$Stories = $progress.stories -join ","
$MaxTurns = 200  # Default

# Start as hidden background process with -Resume flag
$ProcessArgs = "-NoProfile -WindowStyle Hidden -File `"$ScriptPath`" -Stories `"$Stories`" -Resume"

$Process = Start-Process powershell -ArgumentList $ProcessArgs -WindowStyle Hidden -PassThru

Write-Host ""
Write-Host "-" * 70
Write-Host ""
Write-Host "  Daemon Resumed!" -ForegroundColor Green
Write-Host "    New PID: $($Process.Id)"
Write-Host "    Continuing from Story: $($progress.stories[$progress.current_index])"
Write-Host ""
Write-Host "  Commands:" -ForegroundColor DarkGray
Write-Host "    *linear-status  - Check progress" -ForegroundColor DarkGray
Write-Host "    *linear-stop    - Stop daemon" -ForegroundColor DarkGray
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
```

## Output Format

### Success - Resumed
```
======================================================================
  Resuming Linear Development Daemon
======================================================================

  Found resumable session:
    Session ID: linear-20251127-143022
    Status: halted
    Completed: 3/6 stories
    Halt Reason: User requested stop via *linear-stop

  Remaining Stories: 3
    → 15.4 (will restart)
    ○ 15.5
    ○ 15.6

  Worktrees: All present

----------------------------------------------------------------------

  Daemon Resumed!
    New PID: 54321
    Continuing from Story: 15.4

  Commands:
    *linear-status  - Check progress
    *linear-stop    - Stop daemon

======================================================================
```

### Already Running
```
======================================================================
  Resuming Linear Development Daemon
======================================================================

  Daemon already running!
    Session: linear-20251127-143022
    PID: 12345

  Use '*linear-status' to check progress.
```

### Already Completed
```
======================================================================
  Resuming Linear Development Daemon
======================================================================

  Session already completed!
    Session: linear-20251127-143022
    Stories: 6/6

  Use '*linear' to start a new session.
```

### Missing Worktrees
```
======================================================================
  Resuming Linear Development Daemon
======================================================================

  Found resumable session:
    Session ID: linear-20251127-143022
    Status: halted
    Completed: 3/6 stories

  Remaining Stories: 3
    → 15.4 (will restart)
    ○ 15.5
    ○ 15.6

  ERROR: Missing worktrees for remaining Stories:
    15.5, 15.6

  Please run '*init' to recreate missing worktrees.
```

### No Session
```
No linear-progress.json found.
Use '*linear' to start a new daemon session.
```

## Notes

- Reads existing progress file to determine resume point
- Validates all remaining worktrees exist before resuming
- Daemon restarts the current Story from scratch (not mid-execution)
- Completed Stories are not re-executed
- Statistics are preserved and accumulated
