@echo off
"C:\Users\Murasame\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0LaunchMilestoneD1Playtest.ps1"
if errorlevel 1 pause
