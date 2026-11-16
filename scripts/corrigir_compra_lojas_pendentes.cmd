@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0corrigir_compra_lojas_pendentes.ps1" %*
exit /b %ERRORLEVEL%
