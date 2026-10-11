param(
    [string]$OutputZip = "CandyLand_limpo.zip"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSCommandPath
$GeneratorPath = Join-Path $ProjectRoot "scripts\gerar_zip_limpo.ps1"

if (!(Test-Path -LiteralPath $GeneratorPath -PathType Leaf)) {
    throw "Não encontrei scripts\gerar_zip_limpo.ps1 em '$ProjectRoot'. Verifique se o projeto foi atualizado pela branch dev."
}

Write-Host "== CandyLand: gerar ZIP limpo sem apagar arquivos locais ==" -ForegroundColor Cyan
Write-Host "Este atalho é compatível com o nome antigo do script. Ele NÃO remove .venv, node_modules, bancos ou arquivos .env."

& $GeneratorPath -OutputZip $OutputZip
if (!$?) {
    throw "A geração do ZIP falhou. Consulte as mensagens acima; o projeto original foi preservado."
}
