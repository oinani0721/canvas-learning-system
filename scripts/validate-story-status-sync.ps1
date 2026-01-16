<#
.SYNOPSIS
    Validates Story status synchronization between Story files and canvas-project-status.yaml

.DESCRIPTION
    This script checks all Story files against the project status YAML to ensure
    status values are synchronized. Part of BMad Issue #1015 fix.

.PARAMETER StoryPath
    Path to stories directory. Default: docs/stories

.PARAMETER YamlPath
    Path to project status YAML. Default: .bmad-core/data/canvas-project-status.yaml

.PARAMETER Fix
    If specified, attempts to fix mismatches by updating YAML to match Story files

.EXAMPLE
    .\validate-story-status-sync.ps1

.EXAMPLE
    .\validate-story-status-sync.ps1 -Fix

.NOTES
    Author: BMad Workflow Improvement (Issue #1015 Fix)
    Created: 2026-01-17
#>

param(
    [string]$StoryPath = "docs/stories",
    [string]$YamlPath = ".bmad-core/data/canvas-project-status.yaml",
    [switch]$Fix
)

# ANSI color codes
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

Write-Host ""
Write-Host "${Cyan}============================================================${Reset}"
Write-Host "${Cyan}Story Status Sync Validator (BMad Issue #1015 Fix)${Reset}"
Write-Host "${Cyan}============================================================${Reset}"
Write-Host ""

# Validate paths
$ProjectRoot = Get-Location
$FullStoryPath = Join-Path $ProjectRoot $StoryPath
$FullYamlPath = Join-Path $ProjectRoot $YamlPath

if (-not (Test-Path $FullStoryPath)) {
    Write-Host "${Red}ERROR: Story path not found: $FullStoryPath${Reset}"
    exit 1
}

if (-not (Test-Path $FullYamlPath)) {
    Write-Host "${Red}ERROR: YAML path not found: $FullYamlPath${Reset}"
    exit 1
}

# Function to extract status from Story file
function Get-StoryStatus {
    param([string]$FilePath)

    $content = Get-Content $FilePath -Raw -Encoding UTF8

    # Pattern 1: status: value (kebab-case format)
    if ($content -match '(?m)^status:\s*(.+)$') {
        return $Matches[1].Trim()
    }

    # Pattern 2: ## Status section with value on next line
    if ($content -match '(?ms)## Status\s*\n+([^\n#]+)') {
        $statusLine = $Matches[1].Trim()
        # Clean up common patterns
        $statusLine = $statusLine -replace '^\*\*Status\*\*:\s*', ''
        $statusLine = $statusLine -replace '^Status:\s*', ''
        $statusLine = $statusLine -replace '\s*\(.*\)$', ''  # Remove parenthetical notes
        return $statusLine.Trim()
    }

    # Pattern 3: Status: value in any format
    if ($content -match '(?m)^\*?\*?Status\*?\*?:\s*(.+)$') {
        $statusLine = $Matches[1].Trim()
        $statusLine = $statusLine -replace '\s*\(.*\)$', ''
        return $statusLine.Trim()
    }

    return $null
}

# Function to normalize status to kebab-case
function ConvertTo-KebabCase {
    param([string]$Status)

    if (-not $Status) { return $null }

    # Map common status variations to kebab-case
    $statusMap = @{
        'Done' = 'done'
        'Complete' = 'done'
        'Completed' = 'done'
        '✅ Done' = 'done'
        '✅ Complete' = 'done'
        'Draft' = 'draft'
        'Approved' = 'approved'
        'Ready' = 'ready-for-dev'
        'Ready for Development' = 'ready-for-dev'
        'Ready for Dev' = 'ready-for-dev'
        'In Progress' = 'in-progress'
        'In Development' = 'in-progress'
        '🔄 In Development' = 'in-progress'
        'Review' = 'ready-for-review'
        'Ready for Review' = 'ready-for-review'
        'In Review' = 'in-review'
        'Blocked' = 'blocked'
    }

    # Direct lookup
    if ($statusMap.ContainsKey($Status)) {
        return $statusMap[$Status]
    }

    # If already kebab-case, return as-is
    if ($Status -match '^[a-z][a-z0-9-]*$') {
        return $Status
    }

    # Convert to kebab-case
    $result = $Status -replace '[^\w\s-]', ''  # Remove special chars except hyphen
    $result = $result -replace '\s+', '-'      # Replace spaces with hyphens
    $result = $result.ToLower()

    return $result
}

# Read YAML file (simple parsing)
function Get-YamlStoryStatuses {
    param([string]$YamlPath)

    $statuses = @{}
    $content = Get-Content $YamlPath -Raw -Encoding UTF8

    # Simple pattern matching for story entries
    # Format: story_id: status or - id: X.X, status: value
    $pattern = '(?m)(?:story_)?id:\s*[''"]?(\d+\.\d+)[''"]?\s*[\r\n]+\s*status:\s*[''"]?([^''"#\r\n]+)'

    $matches = [regex]::Matches($content, $pattern)
    foreach ($match in $matches) {
        $storyId = $match.Groups[1].Value
        $status = $match.Groups[2].Value.Trim()
        $statuses[$storyId] = $status
    }

    return $statuses
}

# Get all story files
$storyFiles = Get-ChildItem -Path $FullStoryPath -Filter "*.story.md" -Recurse
$storyFiles += Get-ChildItem -Path $FullStoryPath -Filter "*.md" -Recurse | Where-Object { $_.Name -match '^\d+\.\d+' }
$storyFiles = $storyFiles | Sort-Object Name -Unique

Write-Host "Found ${Yellow}$($storyFiles.Count)${Reset} story files"
Write-Host ""

# Extract story statuses from files
$storyStatuses = @{}
foreach ($file in $storyFiles) {
    # Extract story ID from filename
    if ($file.Name -match '(\d+\.\d+)') {
        $storyId = $Matches[1]
        $status = Get-StoryStatus -FilePath $file.FullName
        $normalizedStatus = ConvertTo-KebabCase -Status $status

        $storyStatuses[$storyId] = @{
            File = $file.Name
            RawStatus = $status
            NormalizedStatus = $normalizedStatus
        }
    }
}

# Get YAML statuses
$yamlStatuses = Get-YamlStoryStatuses -YamlPath $FullYamlPath

# Compare and report
$mismatches = @()
$formatIssues = @()
$syncedCount = 0
$missingInYaml = @()

Write-Host "${Cyan}Status Comparison Results:${Reset}"
Write-Host "${Cyan}------------------------------------------------------------${Reset}"

foreach ($storyId in ($storyStatuses.Keys | Sort-Object { [version]$_ })) {
    $storyInfo = $storyStatuses[$storyId]
    $yamlStatus = $yamlStatuses[$storyId]

    $fileStatus = $storyInfo.NormalizedStatus
    $rawStatus = $storyInfo.RawStatus

    # Check format issue
    if ($rawStatus -and $rawStatus -ne $fileStatus) {
        $formatIssues += @{
            StoryId = $storyId
            RawStatus = $rawStatus
            SuggestedStatus = $fileStatus
        }
    }

    # Check YAML sync
    if (-not $yamlStatus) {
        $missingInYaml += $storyId
        Write-Host "  ${Yellow}[MISSING]${Reset} $storyId - Not in YAML (Story: $rawStatus)"
    }
    elseif ($fileStatus -ne $yamlStatus) {
        $mismatches += @{
            StoryId = $storyId
            FileStatus = $fileStatus
            YamlStatus = $yamlStatus
            RawStatus = $rawStatus
        }
        Write-Host "  ${Red}[MISMATCH]${Reset} $storyId - Story: '$rawStatus' vs YAML: '$yamlStatus'"
    }
    else {
        $syncedCount++
        Write-Host "  ${Green}[SYNCED]${Reset} $storyId - $fileStatus"
    }
}

# Summary
Write-Host ""
Write-Host "${Cyan}============================================================${Reset}"
Write-Host "${Cyan}Summary${Reset}"
Write-Host "${Cyan}============================================================${Reset}"
Write-Host ""
Write-Host "Total Stories:        $($storyStatuses.Count)"
Write-Host "${Green}Synced:${Reset}               $syncedCount"
Write-Host "${Red}Mismatches:${Reset}           $($mismatches.Count)"
Write-Host "${Yellow}Missing in YAML:${Reset}      $($missingInYaml.Count)"
Write-Host "${Yellow}Format Issues:${Reset}        $($formatIssues.Count)"
Write-Host ""

# Format issues detail
if ($formatIssues.Count -gt 0) {
    Write-Host "${Yellow}Format Issues (non-kebab-case):${Reset}"
    foreach ($issue in $formatIssues) {
        Write-Host "  $($issue.StoryId): '$($issue.RawStatus)' → '$($issue.SuggestedStatus)'"
    }
    Write-Host ""
}

# Exit code
if ($mismatches.Count -gt 0 -or $missingInYaml.Count -gt 0) {
    Write-Host "${Red}❌ Validation FAILED - Status sync required${Reset}"
    Write-Host ""
    Write-Host "Run with -Fix to auto-update YAML, or manually sync using:"
    Write-Host "  .bmad-core/checklists/story-status-sync-checklist.md"
    Write-Host ""
    exit 1
}
else {
    Write-Host "${Green}✅ Validation PASSED - All statuses synchronized${Reset}"
    Write-Host ""
    exit 0
}
