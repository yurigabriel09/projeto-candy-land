param(
    [string]$OutputZip = "CandyLand_limpo.zip"
)

$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $PSCommandPath
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDirectory "..")).Path
$OutputPath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $OutputZip))
$OutputDirectory = Split-Path -Parent $OutputPath
$StagePath = Join-Path ([System.IO.Path]::GetTempPath()) ("CandyLand_zip_" + [guid]::NewGuid().ToString("N"))
$TempZip = "$OutputPath.tmp.zip"

# Não apaga nem modifica o projeto. Só copia os arquivos permitidos para uma área temporária.
$ExcludedDirectories = @(
    ".git", ".venv", "venv", "node_modules", "dist", "build",
    "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".cache",
    "coverage", "htmlcov", ".idea", "Credenciais", "credentials", "secrets",
    "instance", "temp", "tmp"
)
$ExcludedExtensions = @(".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".pem", ".p12", ".pfx", ".log")
$ExcludedFileNames = @("Thumbs.db", "desktop.ini", ".DS_Store")

function Test-ExcludedFile {
    param([System.IO.FileInfo]$File)

    if ($File.Name -in $ExcludedFileNames) { return $true }
    if ($File.Extension.ToLowerInvariant() -in $ExcludedExtensions) { return $true }
    if ($File.Name -eq ".env" -or $File.Name -eq ".env.local") { return $true }
    if ($File.Name -like ".env.*" -and $File.Name -notin @(".env.example", ".env.template")) { return $true }
    if ($File.Extension -eq ".zip") { return $true }
    if ($File.FullName -eq $OutputPath -or $File.FullName -eq $TempZip) { return $true }
    return $false
}

try {
    Write-Host "== CandyLand: gerar ZIP limpo (sem alterar o projeto) ==" -ForegroundColor Cyan
    Write-Host "Raiz detectada: $ProjectRoot"
    if (!(Test-Path -LiteralPath (Join-Path $ProjectRoot "backend\requirements.txt"))) {
        throw "Não encontrei backend\requirements.txt em '$ProjectRoot'. A raiz do projeto não foi detectada corretamente."
    }
    if (!(Test-Path -LiteralPath (Join-Path $ProjectRoot "frontend\package.json"))) {
        throw "Não encontrei frontend\package.json em '$ProjectRoot'. A raiz do projeto não foi detectada corretamente."
    }

    if (!(Test-Path -LiteralPath $OutputDirectory)) {
        New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    }
    New-Item -ItemType Directory -Path $StagePath -Force | Out-Null

    # Percorre as pastas manualmente para nunca descer em node_modules, .git, .venv etc.
    $pendingDirectories = [System.Collections.Generic.Stack[string]]::new()
    $pendingDirectories.Push($ProjectRoot)
    while ($pendingDirectories.Count -gt 0) {
        $currentDirectory = $pendingDirectories.Pop()
        foreach ($item in Get-ChildItem -LiteralPath $currentDirectory -Force) {
            # Não segue junctions/symlinks para fora do projeto ou para loops.
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }

            if ($item.PSIsContainer) {
                if ($item.Name -in $ExcludedDirectories) { continue }
                $pendingDirectories.Push($item.FullName)
                continue
            }

            if (Test-ExcludedFile -File $item) { continue }
            $relative = $item.FullName.Substring($ProjectRoot.Length).TrimStart('\', '/')
            $destination = Join-Path $StagePath $relative
            $destinationDirectory = Split-Path -Parent $destination
            if (!(Test-Path -LiteralPath $destinationDirectory)) {
                New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
            }
            Copy-Item -LiteralPath $item.FullName -Destination $destination -Force
        }
    }

    if (Test-Path -LiteralPath $TempZip) { Remove-Item -LiteralPath $TempZip -Force }

    # ZipFile inclui arquivos ocultos/dotfiles que um wildcard do Compress-Archive pode omitir.
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory(
        $StagePath,
        $TempZip,
        [System.IO.Compression.CompressionLevel]::Optimal,
        $false
    )

    # Confirma que ZIP foi aberto antes de substituir o destino definitivo.
    $archive = [System.IO.Compression.ZipFile]::OpenRead($TempZip)
    try {
        if ($archive.Entries.Count -eq 0) { throw "ZIP resultante está vazio." }
        $hasBackend = $archive.Entries | Where-Object { $_.FullName -replace '\\','/' -ieq "backend/requirements.txt" }
        $hasFrontend = $archive.Entries | Where-Object { $_.FullName -replace '\\','/' -ieq "frontend/package.json" }
        if (!$hasBackend -or !$hasFrontend) { throw "ZIP não contém as estruturas esperadas de backend e frontend." }
        $unsafe = @(
            foreach ($entry in $archive.Entries) {
                $parts = $entry.FullName -split '/'
                $leaf = $parts[-1]
                $badDirectory = $false
                foreach ($part in $parts) {
                    if ($part -in @('.git', '.venv', 'venv', 'node_modules', 'Credenciais', 'credentials', 'secrets', '__pycache__', '.pytest_cache', '.ruff_cache', '.mypy_cache', '.cache', 'dist', 'build', 'coverage', 'htmlcov', '.idea', 'instance', 'temp', 'tmp')) {
                        $badDirectory = $true
                        break
                    }
                }
                $badGeneratedFile = ($leaf -like '*.pyc') -or ($leaf -like '*.pyo') -or ($leaf -like '*.db') -or ($leaf -like '*.sqlite') -or ($leaf -like '*.sqlite3')
                $badEnvironmentFile = ($leaf -eq '.env') -or ($leaf -eq '.env.local') -or (($leaf -like '.env.*') -and ($leaf -notin @('.env.example', '.env.template')))
                if ($badDirectory -or $badEnvironmentFile -or $badGeneratedFile) { $entry }
            }
        )
        if ($unsafe.Count -gt 0) { throw "ZIP contém caminho que deveria ser excluído: $($unsafe[0].FullName)" }
    }
    finally { $archive.Dispose() }

    Move-Item -LiteralPath $TempZip -Destination $OutputPath -Force
    Write-Host ""
    Write-Host "ZIP criado e verificado: $OutputPath" -ForegroundColor Green
    Write-Host "Foram excluídos segredos .env, credenciais, bancos locais, .git, ambientes virtuais, node_modules, caches, builds e ZIPs anteriores."
    Write-Host "Dotfiles seguros como .gitignore e .env.example foram preservados."
    Write-Host "O projeto original não teve arquivos removidos nem alterados."
}
finally {
    if (Test-Path -LiteralPath $StagePath) { Remove-Item -LiteralPath $StagePath -Recurse -Force -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $TempZip) { Remove-Item -LiteralPath $TempZip -Force -ErrorAction SilentlyContinue }
}
