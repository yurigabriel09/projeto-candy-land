[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Path = Join-Path $ProjectRoot 'frontend/src/pages/Itens.jsx'
if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'frontend/src/pages/Itens.jsx não encontrado.' }

$content = [System.IO.File]::ReadAllText($Path)
$marker = 'Aguardando aprovação'
if ($content -notmatch [regex]::Escape($marker)) {
    $oldButton = @'
<button\s+className="btn-principal btn-pequeno"\s+disabled=\{!produto\.produto_disponivel\}\s+onClick=\{\(\)\s*=>\s*handleAdicionar\(produto\)\}\s*>\s*Adicionar\s*</button>
'@
    $newButton = @'
<button
                      className="btn-principal btn-pequeno"
                      disabled={!produto.produto_disponivel || String(lojas.find((loja) => loja.id === produto.id_restaurante)?.status || "").toUpperCase() !== "ABERTO"}
                      onClick={() => handleAdicionar(produto)}
                    >
                      {String(lojas.find((loja) => loja.id === produto.id_restaurante)?.status || "").toUpperCase() === "EM_ANALISE"
                        ? "Aguardando aprovação"
                        : String(lojas.find((loja) => loja.id === produto.id_restaurante)?.status || "").toUpperCase() === "ABERTO"
                          ? "Adicionar"
                          : "Loja fechada"}
                    </button>
'@
    $matches = [regex]::Matches($content, $oldButton, [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if ($matches.Count -ne 1) {
        throw "Esperava encontrar exatamente um botão Adicionar original em Itens.jsx; encontrei $($matches.Count). Nenhum arquivo foi salvo."
    }
    $content = [regex]::Replace(
        $content,
        $oldButton,
        [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $newButton },
        [System.Text.RegularExpressions.RegexOptions]::Singleline,
        [TimeSpan]::FromSeconds(2)
    )
}

if ($content -notmatch [regex]::Escape($marker) -or $content -notmatch 'produto\.id_restaurante[\s\S]*?status[\s\S]*?ABERTO') {
    throw 'A proteção de compra por status da doceria não foi aplicada. Nenhum arquivo foi salvo.'
}
[System.IO.File]::WriteAllText($Path, $content, (New-Object System.Text.UTF8Encoding($false)))
Write-Host 'Compra corrigida: somente docerias ABERTO permitem adicionar produtos ao carrinho.' -ForegroundColor Green
