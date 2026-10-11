param(
    [string]$OutputZip = "CandyLand_limpo.zip"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputPath = Join-Path $ProjectRoot $OutputZip
$StagePath = Join-Path ([System.IO.Path]::GetTempPath()) ("CandyLand_clean_" + [guid]::NewGuid().ToString("N"))

Write-Host "== CandyLand: limpeza + Ruff + ZIP limpo ==" -ForegroundColor Cyan

# 1. Remover artefatos locais que não pertencem ao código-fonte.
$removeDirs = @(
    ".venv", "venv", "node_modules", "dist", "build",
    "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".coverage", "htmlcov"
)

foreach ($dirName in $removeDirs) {
    Get-ChildItem -Path $ProjectRoot -Directory -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq $dirName } |
        ForEach-Object {
            Write-Host "Removendo: $($_.FullName)"
            Remove-Item $_.FullName -Recurse -Force
        }
}

# 2. Remover arquivos locais/sensíveis e bancos de desenvolvimento.
Get-ChildItem -Path $ProjectRoot -File -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -in @(".env", ".env.local") -or
        $_.Extension -in @(".pyc", ".pyo", ".db", ".sqlite", ".sqlite3")
    } |
    ForEach-Object {
        Write-Host "Removendo arquivo local: $($_.FullName)"
        Remove-Item $_.FullName -Force
    }

# 3. O ZIP de avaliação não deve carregar histórico Git nem documentação de credenciais.
$excludeDirs = @(
    (Join-Path $ProjectRoot ".git"),
    (Join-Path $ProjectRoot "docs\Credenciais")
)

# 4. Garantir Ruff no ambiente virtual e executar correção/formatação.
$venvPath = Join-Path $ProjectRoot ".venv"
if (!(Test-Path $venvPath)) {
    python -m venv $venvPath
}

$python = Join-Path $venvPath "Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install ruff

Write-Host "Executando Ruff..." -ForegroundColor Yellow
& $python -m ruff check backend --fix
if ($LASTEXITCODE -ne 0) {
    Write-Warning "O Ruff encontrou problemas que não puderam ser corrigidos automaticamente."
}
& $python -m ruff format backend
if ($LASTEXITCODE -ne 0) {
    throw "ruff format falhou."
}

Write-Host "Rechecando Ruff..." -ForegroundColor Yellow
& $python -m ruff check backend
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Ainda existem avisos/erros do Ruff. O ZIP será criado, mas revise a saída acima."
}

# 5. Criar área temporária somente com o código/documentação segura.
New-Item -ItemType Directory -Path $StagePath | Out-Null

$items = Get-ChildItem -Path $ProjectRoot -Force |
    Where-Object {
        $_.FullName -ne $OutputPath -and
        $_.FullName -ne $StagePath -and
        $_.Name -notin @(".git", ".venv", "venv", "node_modules", ".ruff_cache")
    }

foreach ($item in $items) {
    if ($item.PSIsContainer -and $item.Name -eq "docs") {
        Copy-Item $item.FullName (Join-Path $StagePath $item.Name) -Recurse -Force
        $cred = Join-Path $StagePath "docs\Credenciais"
        if (Test-Path $cred) { Remove-Item $cred -Recurse -Force }
    }
    elseif ($item.Name -notin @(".env", ".env.local")) {
        Copy-Item $item.FullName (Join-Path $StagePath $item.Name) -Recurse -Force
    }
}

# 6. Garantir que artefatos sensíveis não entraram no staging.
Get-ChildItem -Path $StagePath -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -in @(".env", ".env.local", ".git") -or
        $_.Extension -in @(".db", ".sqlite", ".sqlite3", ".pyc")
    } |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force }

# 7. Apagar ZIP anterior e gerar o novo.
if (Test-Path $OutputPath) {
    Remove-Item $OutputPath -Force
}

Compress-Archive -Path (Join-Path $StagePath "*") -DestinationPath $OutputPath -CompressionLevel Optimal

Remove-Item $StagePath -Recurse -Force

Write-Host ""
Write-Host "ZIP criado:" -ForegroundColor Green
Write-Host $OutputPath
Write-Host ""
Write-Host "O ZIP não inclui .git, .env, banco SQLite, caches, venv, node_modules ou docs/Credenciais."
