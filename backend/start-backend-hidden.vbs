' Canvas Learning System - Backend Auto-Start Script
' This script starts the backend server in the background (no window)
'
' Usage:
'   1. Double-click to start backend manually
'   2. Place shortcut in Windows Startup folder for auto-start on boot
'
' To add to Windows Startup:
'   1. Press Win+R, type: shell:startup
'   2. Create shortcut to this file in the opened folder

Set WshShell = CreateObject("WScript.Shell")

' Get the directory where this script is located
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Change to backend directory and start server
' 0 = Hide window, False = Don't wait for completion
WshShell.CurrentDirectory = scriptDir
WshShell.Run "cmd /c python start_server.py", 0, False

' Optional: Show notification (comment out if not needed)
' WshShell.Popup "Canvas Learning System Backend Started!", 2, "Canvas Backend", 64
