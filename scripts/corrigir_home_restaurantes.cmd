@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0corrigir_home_restaurantes.ps1" %*
exit /b %ERRORLEVEL%
