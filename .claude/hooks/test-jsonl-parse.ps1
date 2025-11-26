# Test JSONL parsing (full file, extract last 20 with text content)
$transcriptPath = "C:\Users\ROG\.claude\projects\C--Users-ROG----Canvas\1bb98fb4-609b-4088-a490-a55b6bf34839.jsonl"
$lines = Get-Content -Path $transcriptPath -Encoding UTF8

# Parse all messages first
$allMessages = @()
foreach ($line in $lines) {
    if ($line.Trim()) {
        try {
            $msg = $line | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($msg) { $allMessages += $msg }
        } catch {}
    }
}
Write-Host "Total messages in transcript: $($allMessages.Count)"

# Extract last 20 turns WITH TEXT CONTENT
$conversationTurns = @()
$maxTurns = 20
$turnCount = 0

for ($i = $allMessages.Count - 1; $i -ge 0 -and $turnCount -lt $maxTurns; $i--) {
    $msg = $allMessages[$i]

    if ($msg.type -eq "user" -or $msg.type -eq "assistant") {
        $role = $msg.message.role
        $content = ""

        if ($msg.message.content -is [string]) {
            $content = $msg.message.content
        } else {
            # Extract text blocks from Object[]
            $textBlocks = @()
            foreach ($block in $msg.message.content) {
                if ($block.type -eq "text" -and $block.text) {
                    $textBlocks += $block.text
                }
            }
            $content = $textBlocks -join "`n"
        }

        # Skip messages with no text content
        if (-not $content -or $content.Trim() -eq "") {
            continue
        }

        # Truncate for display
        $displayContent = if ($content.Length -gt 100) { $content.Substring(0, 100) + "..." } else { $content }
        Write-Host "Turn $($maxTurns - $turnCount): $role - $displayContent"

        $conversationTurns = @(@{ Role = $role; Content = $content }) + $conversationTurns
        $turnCount++
    }
}

Write-Host "`nExtracted turns with text content: $($conversationTurns.Count)"
