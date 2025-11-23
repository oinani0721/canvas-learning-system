# SessionStart Snapshot Manager
# Auto-load snapshots < 2 hours, auto-cleanup snapshots > 2 hours
# Workaround for GitHub Issue #4017: Force reload CLAUDE.md after compression

# ✅ Suppress ALL error streams and redirect to controlled output
$ErrorActionPreference = 'SilentlyContinue'
$WarningPreference = 'SilentlyContinue'
$VerbosePreference = 'SilentlyContinue'
$DebugPreference = 'SilentlyContinue'

# ✅ Fix UTF-8 encoding for Chinese paths
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# ✅ Read SessionStart hook input from stdin to get source parameter
$source = "unknown"
try {
    if ([Console]::IsInputRedirected) {
        $stdinInput = [Console]::In.ReadToEnd()
        if ($stdinInput) {
            $hookInput = $stdinInput | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($hookInput.source) {
                $source = $hookInput.source
                Write-Output "DEBUG: SessionStart source: $source"
            }
        }
    }
} catch {
    Write-Output "DEBUG: Could not read stdin (not an error): $_"
}

# ✅ Enhanced path resolution using $PSScriptRoot
try {
    # Use $PSScriptRoot which is more reliable
    if ($PSScriptRoot) {
        $scriptDir = $PSScriptRoot
    } else {
        # Fallback for older PowerShell versions
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    }

    # Get the project root (two levels up from .claude/hooks/)
    $projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
    $claudemd = Join-Path $projectRoot "CLAUDE.md"

    # ✅ Debug output for troubleshooting
    Write-Output "DEBUG: Script directory: $scriptDir"
    Write-Output "DEBUG: Project root: $projectRoot"
    Write-Output "DEBUG: CLAUDE.md path: $claudemd"
    Write-Output "DEBUG: Current working directory: $PWD"

} catch {
    Write-Output "ERROR: Failed to resolve paths: $_"
    Write-Output "DEBUG: ScriptDir=$scriptDir, PSScriptRoot=$PSScriptRoot"
    Write-Output "SNAPSHOT_ACTION=ERROR"
    exit 0  # ✅ Changed to exit 0 to prevent hook error
}

# ============================================================================
# STEP 1: Load Canvas Project Status First (BMad YAML Status Tracking)
# This must run BEFORE snapshot processing so status can be merged into context
# ============================================================================
Write-Output ""
Write-Output "INFO: Loading Canvas Project Status..."

$statusYaml = Join-Path $projectRoot ".bmad-core\data\canvas-project-status.yaml"

if (Test-Path $statusYaml) {
    try {
        # Read YAML file line-by-line
        $lines = @(Get-Content -Path $statusYaml -Encoding UTF8 -ErrorAction Stop)

        # Parse key information
        $currentPhase = ""
        $lastUpdated = ""
        $completedCount = 0
        $inProgressCount = 0
        $nextActions = @()
        $inNextActionsSection = $false

        foreach ($line in $lines) {
            $cleanLine = $line -replace '#.*$', ''
            $cleanLine = $cleanLine.Trim()

            if ($cleanLine -match '^current_phase:\s*(.+)') {
                $currentPhase = $matches[1].Trim()
            }
            if ($cleanLine -match '^last_updated:\s*(.+)') {
                $lastUpdated = $matches[1].Trim()
            }
            if ($cleanLine -match 'status:\s*completed') {
                $completedCount++
            }
            if ($cleanLine -match 'status:\s*in-progress') {
                $inProgressCount++
            }
            if ($cleanLine -match '^next_actions:') {
                $inNextActionsSection = $true
                continue
            }
            if ($inNextActionsSection) {
                if ($cleanLine -match '^\s*-\s*(.+)') {
                    $nextActions += $matches[1].Trim()
                } elseif ($cleanLine -match '^\S' -and $cleanLine.Length -gt 0) {
                    $inNextActionsSection = $false
                }
            }
        }

        # Build status summary for later merging (no emojis - PowerShell encoding issues)
        $statusContent = ""
        $statusContent += "`n"
        $statusContent += "===========================================================`n"
        $statusContent += "Canvas Learning System - BMad YAML Status`n"
        $statusContent += "===========================================================`n"
        $statusContent += "`n"
        $statusContent += "Current Phase: $currentPhase (BMad Phase 4: Implementation)`n"
        $statusContent += "Last Updated: $lastUpdated`n"
        $statusContent += "`n"
        $statusContent += "Epic Summary:`n"
        $statusContent += "- Completed Epics: $completedCount`n"
        $statusContent += "- In-Progress Epics: $inProgressCount`n"
        $statusContent += "`n"
        $statusContent += "Priority Next Actions:`n"

        $global:canvasStatusSummary = $statusContent

        $displayCount = [Math]::Min(3, $nextActions.Count)
        for ($i = 0; $i -lt $displayCount; $i++) {
            $global:canvasStatusSummary += "`n  $($i + 1). $($nextActions[$i])"
        }

        $global:canvasStatusSummary += "`n===========================================================`n"

        # ✅ VERIFICATION MARKER - Unique string to test additionalContext injection
        # This marker will ONLY exist if additionalContext is successfully injected into Claude's context
        $global:canvasStatusSummary += "`n`n"
        $global:canvasStatusSummary += "--- VERIFICATION MARKER ---`n"
        $global:canvasStatusSummary += "YAML_ADDITIONALCONTEXT_INJECTION_TEST_XYZ789ABC456`n"
        $global:canvasStatusSummary += "If Claude can see this marker, additionalContext injection is confirmed working.`n"
        $global:canvasStatusSummary += "--- END MARKER ---`n"

        Write-Output "SUCCESS: Canvas project status loaded from YAML (will merge into context)"

    } catch {
        Write-Output "WARNING: Failed to read Canvas status: $($_.Exception.Message)"
        $global:canvasStatusSummary = $null
    }
} else {
    Write-Output "INFO: Canvas status file not found (expected at: $statusYaml)"
    $global:canvasStatusSummary = $null
}

# ============================================================================
# STEP 2: Process CLAUDE.md and Snapshot
# ============================================================================

# Check if CLAUDE.md exists
if (-Not (Test-Path $claudemd)) {
    Write-Output "INFO: CLAUDE.md not found at: $claudemd"
    Write-Output "INFO: Skipping snapshot check"
    Write-Output "SNAPSHOT_ACTION=NONE"
    exit 0
}

# Read CLAUDE.md
try {
    Write-Output "DEBUG: Reading CLAUDE.md..."
    $claudeContent = Get-Content -Path $claudemd -Raw -Encoding UTF8 -ErrorAction Stop
    Write-Output "DEBUG: Successfully read CLAUDE.md (length: $($claudeContent.Length) chars)"
} catch {
    Write-Output "ERROR: Failed to read CLAUDE.md at: $claudemd"
    Write-Output "ERROR: Exception: $_"
    Write-Output "SNAPSHOT_ACTION=ERROR"
    exit 0  # ✅ Changed to exit 0 to prevent hook error
}

# Check for snapshot reference
Write-Output "DEBUG: Checking for snapshot markers..."
if ($claudeContent -notmatch '<!-- TEMP_COMPACT_SNAPSHOT_START -->') {
    Write-Output "INFO: No snapshot reference found in CLAUDE.md"
    Write-Output "INFO: Skipping snapshot check"
    Write-Output "SNAPSHOT_ACTION=NONE"
    # ✅ Don't exit here - continue to Canvas status injection at the end
} else {
    # Process snapshot only if marker exists
    Write-Output "DEBUG: Found snapshot marker, extracting details..."

# Extract snapshot timestamp
if ($claudeContent -match '\*\*Snapshot Time\*\*: (.+)') {
    $snapshotTimeStr = $matches[1]
} else {
    Write-Output "ERROR: Cannot extract snapshot timestamp"
    Write-Output "SNAPSHOT_ACTION=ERROR"
    exit 0  # ✅ Changed to exit 0 to prevent hook error
}

# Extract snapshot file path
if ($claudeContent -match '\*\*Snapshot File\*\*: (.+)') {
    $snapshotFileRelative = $matches[1].Trim()
    $snapshotFile = Join-Path $projectRoot $snapshotFileRelative
} else {
    Write-Output "ERROR: Cannot extract snapshot file path"
    Write-Output "SNAPSHOT_ACTION=ERROR"
    exit 0  # ✅ Changed to exit 0 to prevent hook error
}

# Parse timestamp
try {
    $snapshotTime = [DateTime]::ParseExact($snapshotTimeStr, "yyyy-MM-dd HH:mm:ss", $null)
    $currentTime = Get-Date
    $timeDiff = ($currentTime - $snapshotTime).TotalHours

    Write-Output "INFO: Snapshot timestamp: $snapshotTimeStr"
    Write-Output "INFO: Current time: $($currentTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Output "INFO: Time difference: $([math]::Round($timeDiff, 2)) hours"
} catch {
    Write-Output "ERROR: Failed to parse timestamp: $_"
    Write-Output "SNAPSHOT_ACTION=ERROR"
    exit 0  # ✅ Changed to exit 0 to prevent hook error
}

# Decision: LOAD or CLEANUP
if ($timeDiff -lt 2) {
    # Load snapshot
    $snapshotAction = "LOAD"  # ← Fix Bug #1: Set PowerShell variable for use in line 205
    Write-Output "SNAPSHOT_ACTION=LOAD"
    Write-Output "SNAPSHOT_FILE=$snapshotFile"
    Write-Output "SUCCESS: Detected continuation conversation (time diff < 2 hours)"
    Write-Output "CLAUDE_INSTRUCTION=Use Read tool to load snapshot file: $snapshotFile"
} else {
    # Cleanup snapshot
    $snapshotAction = "CLEANUP"  # ← Fix Bug #1: Set PowerShell variable
    Write-Output "SNAPSHOT_ACTION=CLEANUP"
    Write-Output "WARNING: Detected new conversation (time diff > 2 hours), cleaning up"

    # Delete snapshot file
    if (Test-Path $snapshotFile) {
        try {
            Remove-Item -Path $snapshotFile -Force -ErrorAction Stop
            Write-Output "SUCCESS: Deleted expired snapshot file: $snapshotFile"
        } catch {
            Write-Output "ERROR: Failed to delete snapshot file: $_"
        }
    } else {
        Write-Output "INFO: Snapshot file not found, skipping deletion: $snapshotFile"
    }

    # Remove reference from CLAUDE.md
    try {
        # Find the start and end markers
        $startMarker = "<!-- TEMP_COMPACT_SNAPSHOT_START -->"
        $endMarker = "<!-- TEMP_COMPACT_SNAPSHOT_END -->"

        $startIndex = $claudeContent.IndexOf($startMarker)
        $endIndex = $claudeContent.IndexOf($endMarker)

        if ($startIndex -ge 0 -and $endIndex -ge 0) {
            # Find the end of the reference block (after the closing ---)
            $afterEnd = $claudeContent.IndexOf([System.Environment]::NewLine + "---", $endIndex)
            if ($afterEnd -ge 0) {
                $removeEnd = $afterEnd + ([System.Environment]::NewLine + "---" + [System.Environment]::NewLine).Length
            } else {
                $removeEnd = $endIndex + $endMarker.Length
            }

            # Remove the reference block
            $before = $claudeContent.Substring(0, $startIndex)
            $after = $claudeContent.Substring($removeEnd)
            $claudeContent = $before + $after

            # Save updated CLAUDE.md using UTF8 without BOM
            $utf8NoBom = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText($claudemd, $claudeContent, $utf8NoBom)
            Write-Output "SUCCESS: Removed snapshot reference from CLAUDE.md"
        } else {
            Write-Output "WARNING: Could not find snapshot markers in CLAUDE.md"
        }
    } catch {
        Write-Output "ERROR: Failed to update CLAUDE.md: $_"
    }
}

# ============================================================================
# ✅ Issue #4017 Real Solution: Force inject CLAUDE.md + Snapshot via additionalContext
# ============================================================================
# Based on research: SessionStart "compact" matcher is the official post-compression
# reload mechanism (Issue #580 COMPLETED). We use additionalContext to FORCE inject
# full context, not just suggest Claude to read files.
# ============================================================================
if ($source -eq "compact") {
    Write-Output "INFO: Detected compression event (source=compact)"
    Write-Output "WORKAROUND_ISSUE_4017=true"

    try {
        # Read full CLAUDE.md content
        $claudeFullContent = ""
        if (Test-Path $claudemd) {
            $claudeFullContent = Get-Content -Path $claudemd -Raw -Encoding UTF8
            Write-Output "SUCCESS: Read CLAUDE.md for forced injection ($($claudeFullContent.Length) chars)"
        } else {
            Write-Output "WARNING: CLAUDE.md not found at: $claudemd"
        }

        # Read snapshot file if exists and valid (<2 hours)
        $snapshotFullContent = ""
        if ($snapshotAction -eq "LOAD" -and (Test-Path $snapshotFile)) {
            $snapshotFullContent = Get-Content -Path $snapshotFile -Raw -Encoding UTF8
            Write-Output "SUCCESS: Read snapshot for forced injection ($($snapshotFullContent.Length) chars)"
        }

        # Create combined context for forced injection
        $combinedContext = @"
═══════════════════════════════════════════════════════════════════
⚠️ POST-COMPRESSION CONTEXT RELOAD (Issue #4017 Workaround)
═══════════════════════════════════════════════════════════════════

**Mechanism**: SessionStart hook with source="compact" (Official pattern, Issue #580 COMPLETED)
**Method**: additionalContext forced injection (Guaranteed visibility to model)
**Timestamp**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

═══════════════════════════════════════════════════════════════════
SECTION 1: CLAUDE.MD FULL INSTRUCTIONS (Reloaded)
═══════════════════════════════════════════════════════════════════

$claudeFullContent

═══════════════════════════════════════════════════════════════════
SECTION 2: SNAPSHOT BEFORE COMPRESSION (Reloaded)
═══════════════════════════════════════════════════════════════════

$snapshotFullContent

═══════════════════════════════════════════════════════════════════
END OF RELOADED CONTEXT
═══════════════════════════════════════════════════════════════════

**Note**: This context was forcefully injected via SessionStart hook's additionalContext
to ensure CLAUDE.md instructions and pre-compression snapshot are fully restored after
conversation compression. This is the official pattern for Issue #4017 workaround.

"@

        # ✅ Append Canvas YAML status if it was loaded
        if ($global:canvasStatusSummary) {
            $combinedContext += "`n`n"
            $combinedContext += $global:canvasStatusSummary
        }

        # Output as JSON with additionalContext (Official hook output format)
        # This ensures the model MUST see this content in its context
        $hookOutput = @{
            additionalContext = $combinedContext
            workaround = "issue_4017_official_pattern"
            mechanism = "SessionStart_compact_matcher"
            timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
            claudemd_size = $claudeFullContent.Length
            snapshot_size = $snapshotFullContent.Length
            canvas_status_included = ($null -ne $global:canvasStatusSummary)
        } | ConvertTo-Json -Depth 10 -Compress

        Write-Output $hookOutput
        Write-Output "SUCCESS: Forced context injection via additionalContext complete"

    } catch {
        Write-Output "ERROR: Failed to prepare forced context injection: $_"
        # Fallback to suggestion method
        Write-Output "CLAUDE_INSTRUCTION=⚠️ Compression detected. Use Read tool to reload CLAUDE.md. Path: $claudemd"
    }
}
} # End of else block (snapshot marker exists)

# ============================================================================
# Canvas Status Injection (BMad YAML Status Tracking)
# ============================================================================
# Output Canvas status via additionalContext regardless of source type
# This ensures Claude always knows the project status on every session start
# ============================================================================
if ($global:canvasStatusSummary) {
    Write-Output ""
    Write-Output "INFO: Injecting Canvas project status into context..."

    $canvasContextOutput = @{
        additionalContext = $global:canvasStatusSummary
        mechanism = "Canvas_BMad_YAML_Status_Tracking"
        timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    } | ConvertTo-Json -Depth 10 -Compress

    Write-Output $canvasContextOutput
    Write-Output "SUCCESS: Canvas status injected via additionalContext"

    # ✅ Create flag file to trigger Claude's active status display (Option 2)
    # This ensures user sees a beautiful formatted status box in conversation
    $flagFile = Join-Path $scriptDir ".show-status-flag"
    try {
        "trigger" | Out-File -FilePath $flagFile -Encoding UTF8 -Force
        Write-Output "SUCCESS: Created status display flag for Claude: $flagFile"
    } catch {
        Write-Output "WARNING: Failed to create status flag: $_"
    }
}

# ✅ Always exit with 0 to prevent hook errors
exit 0
