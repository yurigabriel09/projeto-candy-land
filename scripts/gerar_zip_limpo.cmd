@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0gerar_zip_limpo.ps1" %*
exit /b %ERRORLEVEL%
