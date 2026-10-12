@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0gerenciar_pr.ps1" %*
exit /b %ERRORLEVEL%
