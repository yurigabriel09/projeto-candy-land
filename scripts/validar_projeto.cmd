@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0validar_projeto.ps1" %*
exit /b %ERRORLEVEL%
