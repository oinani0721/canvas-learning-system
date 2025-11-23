# analyze-dependencies.ps1
# Analyze affected_files across stories to detect conflicts

param(
    [Parameter(Mandatory=$false)]
    [string]$StoriesPath = "docs/stories",

    [Parameter(Mandatory=$false)]
    [string]$Stories  # Optional: specific stories to analyze "13.1,13.2,13.3"
)

$ErrorActionPreference = "Stop"

Write-Host "`n=== Parallel Dev Orchestrator: Dependency Analysis ===" -ForegroundColor Cyan

# Find story files
$storyFiles = @()

if ($Stories) {
    $storyIds = $Stories -split "," | ForEach-Object { $_.Trim() }
    foreach ($id in $storyIds) {
        $pattern = Join-Path $StoriesPath "story-$id*.md"
        $files = Get-ChildItem $pattern -ErrorAction SilentlyContinue
        $storyFiles += $files
    }
} else {
    $storyFiles = Get-ChildItem (Join-Path $StoriesPath "story-*.md") -ErrorAction SilentlyContinue
}

if ($storyFiles.Count -eq 0) {
    Write-Host "No story files found in $StoriesPath" -ForegroundColor Yellow
    Write-Host "Make sure stories have been drafted with @sm *draft" -ForegroundColor Yellow
    exit 1
}

Write-Host "Analyzing $($storyFiles.Count) story file(s)...`n"

# Parse affected_files from each story
$fileMap = @{}  # file -> ArrayList of stories
$storyMap = @{}  # story -> list of files

foreach ($file in $storyFiles) {
    $content = Get-Content $file.FullName -Raw
    $storyId = ""

    # Extract story ID from filename (supports both numeric and text IDs)
    if ($file.Name -match "story-([^.]+)\.md$") {
        $storyId = $Matches[1]
    } elseif ($file.Name -match "story-([0-9.]+)") {
        $storyId = $Matches[1]
    }

    # Find affected_files section
    $affectedFiles = @()

    # YAML-style: affected_files:
    if ($content -match '(?ms)affected_files:\s*\n((?:\s*-\s*[^\n]+\n?)+)') {
        $filesList = $Matches[1]
        $affectedFiles = [regex]::Matches($filesList, '-\s*([^\n]+)') | ForEach-Object {
            $_.Groups[1].Value.Trim().Trim('"').Trim("'")
        }
    }

    # Markdown-style: ## Affected Files
    elseif ($content -match '(?ms)##\s*Affected Files\s*\n((?:-\s*[^\n]+\n?)+)') {
        $filesList = $Matches[1]
        $affectedFiles = [regex]::Matches($filesList, '-\s*`?([^`\n]+)`?') | ForEach-Object {
            $_.Groups[1].Value.Trim()
        }
    }

    if ($affectedFiles.Count -eq 0) {
        Write-Host "Warning: Story $storyId has no affected_files defined" -ForegroundColor Yellow
        continue
    }

    $storyMap[$storyId] = $affectedFiles

    foreach ($af in $affectedFiles) {
        if (-not $fileMap.ContainsKey($af)) {
            $fileMap[$af] = [System.Collections.ArrayList]::new()
        }
        [void]$fileMap[$af].Add($storyId)
    }
}

# Detect conflicts
$conflicts = [System.Collections.ArrayList]@()

$allFiles = @($fileMap.Keys)
foreach ($file in $allFiles) {
    $storiesArray = [array]$fileMap[$file]
    $storyCount = $storiesArray.Length
    if ($storyCount -gt 1) {
        [void]$conflicts.Add(@{
            File = $file
            Stories = $storiesArray
        })
    }
}

# Output results
Write-Host "=== Dependency Map ===" -ForegroundColor Cyan

foreach ($storyId in ($storyMap.Keys | Sort-Object)) {
    $files = $storyMap[$storyId]
    Write-Host "`nStory $storyId" -ForegroundColor White
    foreach ($f in $files) {
        $conflicting = $fileMap[$f].Count -gt 1
        $color = if ($conflicting) { "Red" } else { "Green" }
        $marker = if ($conflicting) { " [CONFLICT]" } else { "" }
        Write-Host "  - $f$marker" -ForegroundColor $color
    }
}

Write-Host "`n=== Conflict Analysis ===" -ForegroundColor Cyan

if ($conflicts.Count -eq 0) {
    Write-Host "No conflicts detected! All stories can run in parallel." -ForegroundColor Green
} else {
    Write-Host "$($conflicts.Count) conflict(s) detected:`n" -ForegroundColor Red

    foreach ($c in $conflicts) {
        Write-Host "File: $($c.File)" -ForegroundColor Red
        Write-Host "  Modified by: $($c.Stories -join ', ')" -ForegroundColor Yellow
        Write-Host ""
    }

    Write-Host "Recommendations:" -ForegroundColor Yellow
    Write-Host "  1. Defer one story to next batch"
    Write-Host "  2. Develop conflicting stories sequentially"
    Write-Host "  3. Allow conflicts and resolve during merge"
}

# Generate non-conflicting groups
$allStories = $storyMap.Keys | Sort-Object
$conflictingStories = $conflicts | ForEach-Object { $_.Stories } | Select-Object -Unique | Sort-Object
$safeStories = $allStories | Where-Object { $_ -notin $conflictingStories }

Write-Host "`n=== Parallel Groups ===" -ForegroundColor Cyan
Write-Host "Safe to parallelize: $($safeStories -join ', ')" -ForegroundColor Green

if ($conflictingStories.Count -gt 0) {
    Write-Host "Needs sequential/deferred: $($conflictingStories -join ', ')" -ForegroundColor Yellow
}

Write-Host ""
