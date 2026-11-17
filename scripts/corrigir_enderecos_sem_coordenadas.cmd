@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0corrigir_enderecos_sem_coordenadas.ps1" %*
exit /b %ERRORLEVEL%
