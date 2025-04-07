@echo off
echo Removing all window borders...
powershell -ExecutionPolicy Bypass -File "%~dp0borderless.ps1"
pause
