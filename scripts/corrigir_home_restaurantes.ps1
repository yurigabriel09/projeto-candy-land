[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$LandingPath = Join-Path $ProjectRoot 'frontend/src/pages/Landing.jsx'
if (-not (Test-Path -LiteralPath $LandingPath -PathType Leaf)) {
    throw "Não encontrei frontend/src/pages/Landing.jsx em '$ProjectRoot'."
}

$content = [System.IO.File]::ReadAllText($LandingPath)
$oldFilter = 'loja\.ativo\s*&&\s*!\[\s*"EM_ANALISE"\s*,\s*"SUSPENSO"\s*\]\.includes\(\s*String\(loja\.status\s*\|\|\s*""\)\.toUpperCase\(\)\s*\)'
$newFilter = 'loja.ativo && String(loja.status || "").toUpperCase() !== "SUSPENSO"'

if ([regex]::IsMatch($content, $oldFilter)) {
    $content = [regex]::Replace($content, $oldFilter, $newFilter, 1)
} elseif (-not [regex]::IsMatch($content, 'loja\.ativo\s*&&\s*String\(loja\.status\s*\|\|\s*""\)\.toUpperCase\(\)\s*!==\s*"SUSPENSO"')) {
    throw 'Não encontrei o filtro de lojas esperado. Nenhuma mudança será salva; revise Landing.jsx.'
}

# Mostra lojas em análise e fechadas com o status correto.
$oldBadge = '\{String\(loja\.status \|\| ""\)\.toUpperCase\(\) === "FECHADO" && \(\s*<strong className="lp-status-fechado">Fechada</strong>\s*\)\}'
$newBadge = '{["FECHADO", "EM_ANALISE"].includes(String(loja.status || "").toUpperCase()) && ( <strong className="lp-status-fechado">{String(loja.status).toUpperCase() === "EM_ANALISE" ? "Em análise" : "Fechada"}</strong> )}'
if ([regex]::IsMatch($content, $oldBadge)) {
    $content = [regex]::Replace($content, $oldBadge, $newBadge, 1)
}

if ($content -match '!\[\s*"EM_ANALISE"\s*,\s*"SUSPENSO"' -or $content -notmatch 'EM_ANALISE.*Em análise') {
    throw 'O filtro ou o selo de loja em análise não foi corrigido. Nenhum arquivo foi salvo.'
}
[System.IO.File]::WriteAllText($LandingPath, $content, (New-Object System.Text.UTF8Encoding($false)))
Write-Host 'Home corrigida: docerias ativas EM_ANALISE aparecem como aguardando aprovação.' -ForegroundColor Green
Write-Host 'Lojas SUSPENSO continuam ocultas; o backend só permite pedidos quando status = ABERTO.'
