[CmdletBinding()]
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
$ScriptDirectory = Split-Path -Parent $PSCommandPath
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDirectory '..')).Path
$BackendPath = Join-Path $ProjectRoot 'backend'
$FrontendPath = Join-Path $ProjectRoot 'frontend'
$VenvPath = Join-Path $ProjectRoot '.venv'
$PythonPath = Join-Path $VenvPath 'Scripts\python.exe'
$RequirementsPath = Join-Path $BackendPath 'requirements.txt'

Write-Host '== CandyLand: validar backend e frontend ==' -ForegroundColor Cyan
Write-Host "Raiz: $ProjectRoot"

if (!(Test-Path -LiteralPath $RequirementsPath)) {
    throw "Não encontrei backend\requirements.txt em '$ProjectRoot'."
}
if (!(Test-Path -LiteralPath (Join-Path $FrontendPath 'package.json'))) {
    throw "Não encontrei frontend\package.json em '$ProjectRoot'."
}

if (!(Test-Path -LiteralPath $PythonPath)) {
    if ($SkipInstall) {
        throw "Ambiente .venv não encontrado. Remova -SkipInstall ou execute scripts\preparar_ambiente.cmd primeiro."
    }
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (!$pythonCommand) {
        throw 'Python não encontrado no PATH. Instale Python 3.10+.'
    }
    Write-Host 'Criando ambiente virtual .venv...' -ForegroundColor Yellow
    & $pythonCommand.Source -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar .venv.' }
}

$versionText = (& $PythonPath --version 2>&1 | Out-String).Trim()
if ($versionText -notmatch 'Python\s+(\d+)\.(\d+)') {
    throw "Não consegui identificar a versão do Python do .venv: $versionText"
}
$major = [int]$Matches[1]
$minor = [int]$Matches[2]
if (($major -lt 3) -or ($major -eq 3 -and $minor -lt 10)) {
    throw "Python 3.10+ é necessário no .venv. Detectado: $versionText"
}
Write-Host "Interpretador selecionado: $PythonPath ($versionText)" -ForegroundColor Green

$npmCommand = Get-Command npm -ErrorAction SilentlyContinue
if (!$npmCommand) { throw 'npm não encontrado no PATH. Instale Node.js compatível com Vite 8.' }

if (!$SkipInstall) {
    Write-Host 'Instalando/atualizando dependências Python no .venv...' -ForegroundColor Yellow
    & $PythonPath -m pip install -r $RequirementsPath
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar backend\requirements.txt.' }

    Push-Location $FrontendPath
    try {
        if (!(Test-Path -LiteralPath (Join-Path $FrontendPath 'package-lock.json'))) {
            throw 'frontend\package-lock.json não encontrado; não é seguro instalar sem lockfile.'
        }
        Write-Host 'Instalando dependências frontend com npm ci...' -ForegroundColor Yellow
        & $npmCommand.Source ci
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependências frontend com npm ci.' }
    }
    finally {
        Pop-Location
    }
}

Write-Host ''
Write-Host 'Executando testes do backend...' -ForegroundColor Yellow
Push-Location $BackendPath
try {
    & $PythonPath -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "A suíte pytest falhou (código $LASTEXITCODE). Corrija os testes antes de publicar." }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Executando build do frontend...' -ForegroundColor Yellow
Push-Location $FrontendPath
try {
    & $npmCommand.Source run build
    if ($LASTEXITCODE -ne 0) { throw "O build Vite falhou (código $LASTEXITCODE). Corrija os erros antes de publicar." }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Validação concluída: pytest e build Vite passaram.' -ForegroundColor Green
