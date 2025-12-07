# Task: Stop Linear Development Daemon

## Purpose
Gracefully stop the running Linear Development Daemon.

## Prerequisites
- Daemon must be running

## Steps

### Step 1: Read Progress File

```powershell
$ProgressFile = "C:\Users\ROG\托福\Canvas\linear-progress.json"

if (-not (Test-Path $ProgressFile)) {
    Write-Host ""
    Write-Host "No linear-progress.json found." -ForegroundColor Yellow
    Write-Host "No daemon to stop." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

$progress = Get-Content $ProgressFile -Raw | ConvertFrom-Json
```

### Step 2: Check Daemon Status

```powershell
if ($progress.status -ne "in_progress") {
    Write-Host ""
    Write-Host "Daemon is not running." -ForegroundColor Yellow
    Write-Host "  Status: $($progress.status)"
    Write-Host ""
    exit 0
}

if (-not $progress.daemon_pid) {
    Write-Host ""
    Write-Host "No daemon PID recorded." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
```

### Step 3: Stop Daemon Process

```powershell
$daemonPid = $progress.daemon_pid

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  Stopping Linear Development Daemon" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

try {
    # Check if daemon process exists
    $daemonProc = Get-Process -Id $daemonPid -ErrorAction SilentlyContinue

    if (-not $daemonProc) {
        Write-Host "  Daemon process (PID: $daemonPid) not found." -ForegroundColor Yellow
        Write-Host "  It may have already exited." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Updating progress file status..." -ForegroundColor DarkGray

        # Update status to halted
        $progress.status = "halted"
        $progress.halted_at = (Get-Date).ToString("o")
        $progress.halt_reason = "Daemon process not found - manual stop"
        $progress | ConvertTo-Json -Depth 10 | Set-Content $ProgressFile

        exit 0
    }

    # Also find and stop any child Claude processes
    $claudeProc = $null
    if ($progress.current_story -and $progress.current_story.claude_pid) {
        $claudePid = $progress.current_story.claude_pid
        $claudeProc = Get-Process -Id $claudePid -ErrorAction SilentlyContinue
    }

    Write-Host "  Sending termination signal..." -ForegroundColor Yellow
    Write-Host "    Daemon PID: $daemonPid"
    if ($claudeProc) {
        Write-Host "    Claude PID: $($claudeProc.Id)"
    }

    # Stop Claude first (if running)
    if ($claudeProc) {
        Write-Host ""
        Write-Host "  Stopping Claude session..." -ForegroundColor DarkGray
        Stop-Process -Id $claudeProc.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    # Stop daemon
    Write-Host "  Stopping daemon process..." -ForegroundColor DarkGray
    Stop-Process -Id $daemonPid -Force -ErrorAction SilentlyContinue

    # Wait for processes to terminate
    Start-Sleep -Seconds 3

    # Verify termination
    $stillRunning = Get-Process -Id $daemonPid -ErrorAction SilentlyContinue

    if ($stillRunning) {
        Write-Host ""
        Write-Host "  WARNING: Daemon may still be running!" -ForegroundColor Red
        Write-Host "  Try manually: Stop-Process -Id $daemonPid -Force" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "  Daemon stopped successfully!" -ForegroundColor Green
    }

    # Update progress file
    $progress.status = "halted"
    $progress.halted_at = (Get-Date).ToString("o")
    $progress.halt_reason = "User requested stop via *linear-stop"
    $progress | ConvertTo-Json -Depth 10 | Set-Content $ProgressFile

} catch {
    Write-Host ""
    Write-Host "  ERROR: Failed to stop daemon: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "-" * 70

# Show summary
Write-Host ""
Write-Host "  Summary:" -ForegroundColor White
Write-Host "    Session: $($progress.session_id)"
Write-Host "    Stories Completed: $($progress.completed_stories.Count)/$($progress.stories.Count)"
if ($progress.current_story) {
    Write-Host "    Story Interrupted: $($progress.current_story.story_id)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  To resume later: *linear-resume" -ForegroundColor Cyan
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
```

## Output Format

### Success
```
======================================================================
  Stopping Linear Development Daemon
======================================================================

  Sending termination signal...
    Daemon PID: 12345
    Claude PID: 67890

  Stopping Claude session...
  Stopping daemon process...

  Daemon stopped successfully!

----------------------------------------------------------------------

  Summary:
    Session: linear-20251127-143022
    Stories Completed: 3/6
    Story Interrupted: 15.4

  To resume later: *linear-resume

======================================================================
```

### Already Stopped
```
Daemon is not running.
  Status: completed
```

### No Session
```
No linear-progress.json found.
No daemon to stop.
```

### Process Not Found
```
======================================================================
  Stopping Linear Development Daemon
======================================================================

  Daemon process (PID: 12345) not found.
  It may have already exited.

  Updating progress file status...

======================================================================
```

## Notes

- Graceful shutdown: sends SIGTERM, waits, then force kills if needed
- Stops both daemon and any running Claude session
- Updates progress file with halt status
- Session can be resumed with `*linear-resume`
