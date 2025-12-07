#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PostToolUse hook that detects when a story's status changes to "Ready for Review".

.DESCRIPTION
    This hook fires after Edit or Write operations on story files.
    When it detects "Status: Ready for Review", it injects QA workflow
    instructions into Claude's context via additionalContext.

.NOTES
    Hook Event: PostToolUse
    Matcher: Edit|Write
    Output: JSON with decision and hookSpecificOutput.additionalContext
#>

# Fix UTF-8 encoding for PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Read hook input from stdin
$stdinInput = ""
$toolName = ""
$toolInput = $null

try {
    if ([Console]::IsInputRedirected) {
        $stdinInput = [Console]::In.ReadToEnd()
        if ($stdinInput) {
            $hookInput = $stdinInput | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($hookInput) {
                $toolName = $hookInput.tool_name
                $toolInput = $hookInput.tool_input
            }
        }
    }
} catch {
    # Silent fail - don't block workflow
    exit 0
}

# Only process Edit or Write operations
if ($toolName -notin @("Edit", "Write")) {
    exit 0
}

# Extract file path from tool input
$filePath = ""
if ($toolInput.file_path) {
    $filePath = $toolInput.file_path
} elseif ($toolInput.path) {
    $filePath = $toolInput.path
}

# Check if it's a story file
# Pattern: docs/stories/*.story.md or docs\stories\*.story.md
if ($filePath -notmatch "docs[/\\]stories[/\\].*\.story\.md$") {
    exit 0
}

# Verify file exists
if (-not (Test-Path $filePath)) {
    exit 0
}

try {
    # Read the file content
    $content = Get-Content -Path $filePath -Raw -Encoding UTF8

    # Detect "Status: Ready for Review" pattern
    # Matches various formats:
    # ## Status\nReady for Review
    # # Status\n  Ready for Review
    # **Status**: Ready for Review
    $statusPatterns = @(
        "(?mi)^##?\s*Status\s*\n\s*Ready for Review",
        "(?mi)\*\*Status\*\*:\s*Ready for Review",
        "(?mi)Status:\s*Ready for Review"
    )

    $statusFound = $false
    foreach ($pattern in $statusPatterns) {
        if ($content -match $pattern) {
            $statusFound = $true
            break
        }
    }

    if ($statusFound) {
        # Extract story ID from filename
        $fileName = [System.IO.Path]::GetFileName($filePath)
        $storyId = $fileName -replace "\.story\.md$", "" -replace "^story-", ""

        # Build the additional context message
        $additionalContext = @"

===============================================================================
QA AUTOMATION TRIGGER DETECTED
===============================================================================

**Story Status Changed**: Story $storyId is now "Ready for Review"
**File**: $filePath
**Detected At**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

**RECOMMENDED QA WORKFLOW**:

The Dev Agent has completed Story $storyId. To ensure quality before merge,
please execute the full QA Agent workflow:

1. **Trace Requirements**: Verify AC coverage
   ``/qa``
   ``*trace $storyId``

2. **NFR Assessment**: Check non-functional requirements
   ``*nfr-assess $storyId``

3. **Comprehensive Review**: Full code and design review
   ``*review $storyId``

4. **Quality Gate**: Final gate decision
   ``*gate $storyId``

**Quick Command** (runs full QA sequence):
   ``/qa *review $storyId``

After QA completes with PASS or WAIVED, proceed to Git commit:
   ``git add -A``
   ``git commit -m "Story $storyId: [Description]"``

===============================================================================

"@

        # Output JSON response for Claude Code
        $output = @{
            decision = "approve"
            hookSpecificOutput = @{
                hookEventName = "PostToolUse"
                additionalContext = $additionalContext
            }
        } | ConvertTo-Json -Depth 10 -Compress

        Write-Output $output
    }
} catch {
    # Silent fail on errors - don't block workflow
    exit 0
}

exit 0
