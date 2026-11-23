param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectRoot
)
$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { $Python = (Get-Command python -ErrorAction Stop).Source }
& $Python (Join-Path $ScriptDir 'corrigir_falhas_v2.py') --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "A correção v2 falhou (código $LASTEXITCODE). Nenhuma gravação deve ocorrer antes da validação dos trechos." }
