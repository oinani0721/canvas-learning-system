# Canvas Learning System - Auto-Start Setup Script
# Run this script once to configure Windows auto-start

$ErrorActionPreference = "Stop"

Write-Host "Canvas Learning System - Backend Auto-Start Setup" -ForegroundColor Cyan
Write-Host "=" * 50

# Get paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$vbsPath = Join-Path $scriptDir "start-backend-hidden.vbs"
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Canvas-Backend.lnk"

# Verify VBS exists
if (-not (Test-Path $vbsPath)) {
    Write-Host "Error: start-backend-hidden.vbs not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "VBS Script: $vbsPath" -ForegroundColor Gray
Write-Host "Startup Folder: $startupFolder" -ForegroundColor Gray
Write-Host ""

# Create shortcut in Startup folder
$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $vbsPath
$shortcut.WorkingDirectory = $scriptDir
$shortcut.Description = "Canvas Learning System Backend Auto-Start"
$shortcut.Save()

Write-Host "Created startup shortcut: $shortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "Setup complete! Backend will start automatically on Windows login." -ForegroundColor Green
Write-Host ""
Write-Host "To remove auto-start:" -ForegroundColor Yellow
Write-Host "  1. Press Win+R, type: shell:startup" -ForegroundColor Yellow
Write-Host "  2. Delete 'Canvas-Backend.lnk'" -ForegroundColor Yellow
Write-Host ""

# Ask if user wants to start backend now
$response = Read-Host "Start backend now? (Y/n)"
if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
    Write-Host "Starting backend..." -ForegroundColor Cyan
    Start-Process wscript.exe -ArgumentList "`"$vbsPath`"" -WindowStyle Hidden
    Start-Sleep -Seconds 3

    # Check if backend is running
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/health" -TimeoutSec 5
        Write-Host "Backend started successfully!" -ForegroundColor Green
        Write-Host "  App: $($health.app_name)" -ForegroundColor Gray
        Write-Host "  Version: $($health.version)" -ForegroundColor Gray
    } catch {
        Write-Host "Backend may still be starting... Check http://127.0.0.1:8001/docs" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
