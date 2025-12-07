# Task Complete Notification Hook
# Play sound and optionally show notification when task completes

param(
    [string]$Message = "Task completed!"
)

# Play ascending tones to indicate success
[console]::beep(600, 200)
[console]::beep(800, 200)
[console]::beep(1000, 200)
[console]::beep(1200, 400)

# Optional: Show Windows toast notification
try {
    Add-Type -AssemblyName System.Windows.Forms
    $balloon = New-Object System.Windows.Forms.NotifyIcon
    $balloon.Icon = [System.Drawing.SystemIcons]::Information
    $balloon.BalloonTipIcon = "Info"
    $balloon.BalloonTipTitle = "Claude Code"
    $balloon.BalloonTipText = $Message
    $balloon.Visible = $true
    $balloon.ShowBalloonTip(5000)
    Start-Sleep -Milliseconds 5100
    $balloon.Dispose()
} catch {
    # Fallback: just use beep if toast fails
    Write-Host "Task completed!" -ForegroundColor Green
}
