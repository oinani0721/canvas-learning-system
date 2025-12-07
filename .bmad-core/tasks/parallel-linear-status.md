# Task: Show Linear Daemon Status

## Purpose
Display current daemon progress, statistics, and Story completion status.

## Prerequisites
- None (works even if no daemon running)

## Steps

### Step 1: Read Progress File

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

### Step 2: Check Daemon Process Status

```powershell
$daemonRunning = $false
if ($progress.daemon_pid) {
    try {
        $proc = Get-Process -Id $progress.daemon_pid -ErrorAction SilentlyContinue
        if ($proc) {
            $daemonRunning = $true
        }
    } catch {}
}
```

### Step 3: Display Status

```powershell
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  Linear Development Daemon Status" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Session Info
Write-Host "  Session: $($progress.session_id)" -ForegroundColor White
Write-Host "  Status: " -NoNewline
switch ($progress.status) {
    "in_progress" { Write-Host $progress.status -ForegroundColor Green }
    "completed" { Write-Host $progress.status -ForegroundColor Cyan }
    "halted" { Write-Host $progress.status -ForegroundColor Red }
    default { Write-Host $progress.status -ForegroundColor Yellow }
}

# Daemon Process
Write-Host "  Daemon: " -NoNewline
if ($daemonRunning) {
    Write-Host "Running (PID: $($progress.daemon_pid))" -ForegroundColor Green
} else {
    Write-Host "Not Running" -ForegroundColor Yellow
}

Write-Host ""

# Progress Bar
$total = $progress.stories.Count
$completed = $progress.completed_stories.Count
$current = $progress.current_index
$percent = [math]::Round(($completed / $total) * 100)

Write-Host "  Progress: [$completed/$total] $percent%" -ForegroundColor White
$barWidth = 50
$filled = [math]::Round(($completed / $total) * $barWidth)
$bar = ("█" * $filled) + ("░" * ($barWidth - $filled))
Write-Host "  [$bar]" -ForegroundColor Cyan

Write-Host ""
Write-Host "-" * 70

# Story Status
Write-Host ""
Write-Host "  Stories:" -ForegroundColor White

foreach ($storyId in $progress.stories) {
    $completedStory = $progress.completed_stories | Where-Object { $_.story_id -eq $storyId }

    if ($completedStory) {
        $icon = if ($completedStory.outcome -eq "SUCCESS") { "✓" } else { "✗" }
        $color = if ($completedStory.outcome -eq "SUCCESS") { "Green" } else { "Red" }
        Write-Host "    $icon $storyId : $($completedStory.outcome)" -ForegroundColor $color
        if ($completedStory.commit_sha) {
            Write-Host "      Commit: $($completedStory.commit_sha.Substring(0,7))" -ForegroundColor DarkGray
        }
    } elseif ($progress.current_story -and $progress.current_story.story_id -eq $storyId) {
        Write-Host "    ⏳ $storyId : IN PROGRESS" -ForegroundColor Yellow
        Write-Host "      Started: $($progress.current_story.started_at)" -ForegroundColor DarkGray
        if ($progress.current_story.retry_count -gt 0) {
            Write-Host "      Retries: $($progress.current_story.retry_count)" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "    ○ $storyId : PENDING" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "-" * 70

# Statistics
Write-Host ""
Write-Host "  Statistics:" -ForegroundColor White
Write-Host "    Succeeded: $($progress.statistics.stories_succeeded)" -ForegroundColor Green
Write-Host "    Failed: $($progress.statistics.stories_failed)" -ForegroundColor Red
Write-Host "    Total Retries: $($progress.statistics.total_retries)"
Write-Host "    Compact Restarts: $($progress.statistics.total_compact_restarts)"

if ($progress.statistics.total_duration_seconds) {
    $duration = [TimeSpan]::FromSeconds($progress.statistics.total_duration_seconds)
    Write-Host "    Total Duration: $($duration.ToString('hh\:mm\:ss'))"
}

# Halt Reason
if ($progress.halt_reason) {
    Write-Host ""
    Write-Host "  Halt Reason: $($progress.halt_reason)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
```

## Output Format

### Active Session
```
======================================================================
  Linear Development Daemon Status
======================================================================

  Session: linear-20251127-143022
  Status: in_progress
  Daemon: Running (PID: 12345)

  Progress: [2/6] 33%
  [████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]

----------------------------------------------------------------------

  Stories:
    ✓ 15.1 : SUCCESS
      Commit: abc1234
    ✓ 15.2 : SUCCESS
      Commit: def5678
    ⏳ 15.3 : IN PROGRESS
      Started: 2025-11-27T15:35:30Z
    ○ 15.4 : PENDING
    ○ 15.5 : PENDING
    ○ 15.6 : PENDING

----------------------------------------------------------------------

  Statistics:
    Succeeded: 2
    Failed: 0
    Total Retries: 0
    Compact Restarts: 1
    Total Duration: 01:05:00

======================================================================
```

### Completed Session
```
======================================================================
  Linear Development Daemon Status
======================================================================

  Session: linear-20251127-143022
  Status: completed
  Daemon: Not Running

  Progress: [6/6] 100%
  [██████████████████████████████████████████████████]

----------------------------------------------------------------------

  Stories:
    ✓ 15.1 : SUCCESS
    ✓ 15.2 : SUCCESS
    ✓ 15.3 : SUCCESS
    ✓ 15.4 : SUCCESS
    ✓ 15.5 : SUCCESS
    ✓ 15.6 : SUCCESS

----------------------------------------------------------------------

  Statistics:
    Succeeded: 6
    Failed: 0
    Total Retries: 1
    Compact Restarts: 2
    Total Duration: 08:32:15

======================================================================
```

### Halted Session
```
======================================================================
  Linear Development Daemon Status
======================================================================

  Session: linear-20251127-143022
  Status: halted
  Daemon: Not Running

  Progress: [3/6] 50%
  [█████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░]

----------------------------------------------------------------------

  Stories:
    ✓ 15.1 : SUCCESS
    ✓ 15.2 : SUCCESS
    ✓ 15.3 : SUCCESS
    ✗ 15.4 : DEV_BLOCKED
    ○ 15.5 : PENDING
    ○ 15.6 : PENDING

----------------------------------------------------------------------

  Statistics:
    Succeeded: 3
    Failed: 1
    Total Retries: 1
    Compact Restarts: 0
    Total Duration: 04:15:30

  Halt Reason: Story 15.4 blocked: Tests failed - 3 type errors

======================================================================
```

### No Session
```
No linear-progress.json found.
Use '*linear' to start a new daemon session.
```

## Notes

- Can be run anytime, even when daemon not running
- Shows real-time progress if daemon active
- Displays halt reason if session was interrupted
- Progress bar provides quick visual overview
