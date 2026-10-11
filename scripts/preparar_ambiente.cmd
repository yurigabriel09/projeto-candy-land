@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0preparar_ambiente.ps1" %*
exit /b %ERRORLEVEL%
