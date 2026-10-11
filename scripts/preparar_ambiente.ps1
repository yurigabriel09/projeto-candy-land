param(
    [switch]$SkipPython,
    [switch]$SkipNode
)

$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $PSCommandPath
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDirectory "..")).Path
$BackendPath = Join-Path $ProjectRoot "backend"
$FrontendPath = Join-Path $ProjectRoot "frontend"
$VenvPath = Join-Path $ProjectRoot ".venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"

Write-Host "== CandyLand: preparar ambiente local ==" -ForegroundColor Cyan
Write-Host "Raiz detectada: $ProjectRoot"
Write-Host "O script preserva arquivos .env existentes e não apaga dados locais."

if (!(Test-Path -LiteralPath (Join-Path $BackendPath "requirements.txt"))) {
    throw "Não encontrei backend\requirements.txt em '$ProjectRoot'. Execute o script dentro de uma cópia completa do CandyLand."
}
if (!(Test-Path -LiteralPath (Join-Path $FrontendPath "package.json"))) {
    throw "Não encontrei frontend\package.json em '$ProjectRoot'. Execute o script dentro de uma cópia completa do CandyLand."
}

# Criar arquivos de ambiente somente quando ausentes; nunca sobrescrever credenciais.
$backendEnv = Join-Path $BackendPath ".env"
$backendExample = Join-Path $BackendPath ".env.example"
if (!(Test-Path -LiteralPath $backendEnv) -and (Test-Path -LiteralPath $backendExample)) {
    Copy-Item -LiteralPath $backendExample -Destination $backendEnv
    Write-Warning "Criado backend\.env a partir do exemplo. Revise valores e insira credenciais locais válidas."
} elseif (Test-Path -LiteralPath $backendEnv) {
    Write-Host "backend\.env já existe; mantido sem alterações." -ForegroundColor Green
} else {
    Write-Warning "backend\.env.example não encontrado; crie o arquivo de ambiente manualmente."
}

$frontendEnv = Join-Path $FrontendPath ".env.local"
$frontendExample = Join-Path $FrontendPath ".env.example"
if (!(Test-Path -LiteralPath $frontendEnv) -and (Test-Path -LiteralPath $frontendExample)) {
    Copy-Item -LiteralPath $frontendExample -Destination $frontendEnv
    Write-Warning "Criado frontend\.env.local a partir do exemplo. Revise o client ID do Google se usar OAuth."
} elseif (Test-Path -LiteralPath $frontendEnv) {
    Write-Host "frontend\.env.local já existe; mantido sem alterações." -ForegroundColor Green
} else {
    Write-Warning "frontend\.env.example não encontrado; crie o arquivo de ambiente manualmente."
}

if (!$SkipPython) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (!$pythonCommand) {
        throw "Python não foi encontrado no PATH. Instale Python 3.10 ou superior e execute novamente."
    }

    $pythonVersionText = (& $pythonCommand.Source --version 2>&1 | Out-String).Trim()
    if ($pythonVersionText -notmatch 'Python\s+(\d+)\.(\d+)') {
        throw "Não consegui identificar a versão do Python: $pythonVersionText"
    }
    $pythonMajor = [int]$Matches[1]
    $pythonMinor = [int]$Matches[2]
    if (($pythonMajor -lt 3) -or ($pythonMajor -eq 3 -and $pythonMinor -lt 10)) {
        throw "Python 3.10+ é necessário. Detectado: $pythonVersionText"
    }

    if (!(Test-Path -LiteralPath $PythonPath)) {
        Write-Host "Criando ambiente virtual .venv..." -ForegroundColor Yellow
        & $pythonCommand.Source -m venv $VenvPath
        if ($LASTEXITCODE -ne 0) { throw "Falha ao criar .venv." }
    } else {
        Write-Host "Ambiente .venv existente; será reutilizado." -ForegroundColor Green
    }

    Write-Host "Atualizando pip..." -ForegroundColor Yellow
    & $PythonPath -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Falha ao atualizar pip." }

    $requirements = Join-Path $BackendPath "requirements.txt"
    Write-Host "Instalando dependências Python..." -ForegroundColor Yellow
    & $PythonPath -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar backend\requirements.txt." }
}

if (!$SkipNode) {
    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    $npmCommand = Get-Command npm -ErrorAction SilentlyContinue
    if (!$nodeCommand) { throw "Node.js não foi encontrado no PATH. Instale Node.js compatível com Vite 8 (20.19+ ou 22.12+) e execute novamente." }
    if (!$npmCommand) { throw "npm não foi encontrado no PATH. Reinstale/ajuste o Node.js." }

    $nodeVersionText = (& $nodeCommand.Source -p "process.versions.node" 2>&1 | Out-String).Trim()
    try { $nodeVersion = [version]$nodeVersionText } catch { throw "Não consegui identificar a versão do Node.js: $nodeVersionText" }
    $nodeCompatible = (($nodeVersion.Major -eq 20) -and ($nodeVersion -ge [version]"20.19.0")) -or (($nodeVersion.Major -eq 22) -and ($nodeVersion -ge [version]"22.12.0")) -or ($nodeVersion.Major -gt 22)
    if (!$nodeCompatible) { throw "A versão $nodeVersionText do Node.js não atende ao Vite 8. Use Node 20.19+ (linha 20) ou 22.12+." }

    Push-Location $FrontendPath
    try {
        if (Test-Path -LiteralPath (Join-Path $FrontendPath "package-lock.json")) {
            Write-Host "Instalando dependências Node com npm ci..." -ForegroundColor Yellow
            & $npmCommand.Source ci
        } else {
            Write-Warning "package-lock.json ausente; npm install será usado, mas gere e versione o lockfile antes do merge."
            & $npmCommand.Source install
        }
        if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependências do frontend." }

        Write-Host "Validando build do frontend..." -ForegroundColor Yellow
        & $npmCommand.Source run build
        if ($LASTEXITCODE -ne 0) { throw "O build do frontend falhou; corrija os erros antes de considerar o ambiente preparado." }
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Ambiente preparado com sucesso." -ForegroundColor Green
Write-Host "Backend (terminal 1):"
Write-Host "  Set-Location `"$BackendPath`""
Write-Host "  ..\.venv\Scripts\python.exe run.py"
Write-Host "Frontend (terminal 2):"
Write-Host "  Set-Location `"$FrontendPath`""
Write-Host "  npm run dev"
Write-Host ""
Write-Host "Nota: o run.py atual usa Flask com debug=True; não exponha esse modo em produção."
Write-Host "Nenhum .env existente foi sobrescrito ou removido."
