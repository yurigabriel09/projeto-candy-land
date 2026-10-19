@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0limpar_e_gerar_zip.ps1" %*
exit /b %ERRORLEVEL%
