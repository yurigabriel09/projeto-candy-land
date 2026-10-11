[CmdletBinding()]
param(
    [ValidateSet('Instalar', 'Atualizar', 'Autenticar', 'StatusPR', 'CriarPR', 'MesclarPR')]
    [string]$Acao = 'StatusPR',
    [string]$Titulo = '',
    [string]$Corpo = '',
    [switch]$ConfirmarMerge
)

$ErrorActionPreference = 'Stop'
$ScriptDirectory = Split-Path -Parent $PSCommandPath
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDirectory '..')).Path
$ExpectedOriginPattern = '^(https://github\.com/yurigabriel09/projeto-candy-land(\.git)?|git@github\.com:yurigabriel09/projeto-candy-land(\.git)?)$'

function Get-GhCommand {
    Get-Command gh -ErrorAction SilentlyContinue
}

function Assert-GhInstalled {
    if (-not (Get-GhCommand)) {
        throw 'GitHub CLI (gh) nao foi encontrado no PATH. Execute: .\scripts\gerenciar_pr.ps1 -Acao Instalar. Depois abra um PowerShell novo.'
    }
}

function Assert-GhAuthenticated {
    Assert-GhInstalled
    & gh auth status --hostname github.com
    if ($LASTEXITCODE -ne 0) {
        throw 'GitHub CLI nao esta autenticado. Execute: .\scripts\gerenciar_pr.ps1 -Acao Autenticar'
    }
}

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$GitArguments)
    & git -C $ProjectRoot @GitArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Falha no comando git: git $($GitArguments -join ' ')"
    }
}

function Get-CurrentBranch {
    $branch = (& git -C $ProjectRoot branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($branch)) {
        throw 'Nao consegui identificar a branch atual.'
    }
    if ($branch -in @('main', 'dev')) {
        throw "Por seguranca, nao abra nem mescle PR a partir de '$branch'. Use uma branch feature/fix/docs/chore."
    }
    return $branch
}

function Get-CurrentPullRequest {
    param([Parameter(Mandatory = $true)][string]$Branch)
    $json = & gh pr view $Branch --json number,url,title,state,baseRefName,headRefName,reviewDecision,mergeStateStatus 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($json -join ''))) {
        throw "Nao encontrei um Pull Request para '$Branch'. Execute: .\scripts\gerenciar_pr.ps1 -Acao CriarPR"
    }
    return (($json -join "`n") | ConvertFrom-Json)
}

if ($Acao -eq 'Instalar') {
    if (Get-GhCommand) {
        Write-Host 'GitHub CLI ja esta instalado:' -ForegroundColor Green
        & gh --version
        Write-Host 'Para autenticar, execute: .\scripts\gerenciar_pr.ps1 -Acao Autenticar'
        return
    }
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw 'winget nao foi encontrado. Instale/atualize o App Installer do Windows ou siga https://github.com/cli/cli/blob/trunk/docs/install_windows.md.'
    }
    Write-Host 'Instalando GitHub CLI pelo WinGet...' -ForegroundColor Cyan
    & $winget.Source install --id GitHub.cli --source winget --exact --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'A instalacao do GitHub CLI falhou. Confira a mensagem do WinGet.' }
    Write-Host 'Instalacao concluida. Feche os terminais e abra um PowerShell novo.' -ForegroundColor Green
    Write-Host 'Depois execute: .\scripts\gerenciar_pr.ps1 -Acao Autenticar'
    return
}

if ($Acao -eq 'Atualizar') {
    Assert-GhInstalled
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) { throw 'winget nao foi encontrado. Atualize o GitHub CLI pelo instalador oficial: https://cli.github.com/.' }
    & $winget.Source upgrade --id GitHub.cli --source winget --exact --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'A atualizacao do GitHub CLI falhou. Confira a mensagem do WinGet.' }
    return
}

if ($Acao -eq 'Autenticar') {
    Assert-GhInstalled
    & gh auth status --hostname github.com
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'Voce ja esta autenticado no GitHub.' -ForegroundColor Green
        return
    }
    & gh auth login --hostname github.com --git-protocol https --web
    if ($LASTEXITCODE -ne 0) { throw 'A autenticacao nao foi concluida. Repita a acao e finalize o fluxo no navegador.' }
    & gh auth status --hostname github.com
    if ($LASTEXITCODE -ne 0) { throw 'O GitHub CLI ainda nao confirma a autenticacao.' }
    return
}

Assert-GhAuthenticated
$originUrl = (& git -C $ProjectRoot remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $originUrl -notmatch $ExpectedOriginPattern) {
    throw "O remote origin nao aponta para yurigabriel09/projeto-candy-land. URL detectada: '$originUrl'. Nenhuma acao foi executada."
}

switch ($Acao) {
    'StatusPR' {
        $branch = Get-CurrentBranch
        $pr = Get-CurrentPullRequest -Branch $branch
        [pscustomobject]@{
            Titulo      = $pr.title
            URL         = $pr.url
            Estado      = $pr.state
            Base        = $pr.baseRefName
            Origem      = $pr.headRefName
            Revisao     = $pr.reviewDecision
            EstadoMerge = $pr.mergeStateStatus
        } | Format-List
        if ($pr.baseRefName -ne 'dev') {
            Write-Warning "Este PR nao aponta para dev (base atual: '$($pr.baseRefName)'). Nao mescle por este script."
        }
        return
    }

    'CriarPR' {
        $branch = Get-CurrentBranch
        Invoke-Git -GitArguments @('fetch', 'origin')

        $workingTree = (& git -C $ProjectRoot status --porcelain) -join "`n"
        if (-not [string]::IsNullOrWhiteSpace($workingTree)) {
            throw "A arvore de trabalho nao esta limpa. Faca commit ou guarde as alteracoes antes de criar o PR:`n$workingTree"
        }

        & git -C $ProjectRoot merge-base --is-ancestor origin/dev HEAD
        if ($LASTEXITCODE -ne 0) {
            throw 'Sua branch nao contem origin/dev como ancestral. Atualize/rebaseie a branch a partir de dev e rode os testes antes de abrir o PR.'
        }

        $aheadCount = (& git -C $ProjectRoot rev-list --count 'origin/dev..HEAD').Trim()
        if ($LASTEXITCODE -ne 0 -or [int]$aheadCount -lt 1) {
            throw 'A branch nao possui commits exclusivos em relacao a origin/dev; nao ha alteracoes para propor.'
        }

        $remoteLine = (& git -C $ProjectRoot ls-remote --heads origin $branch | Select-Object -First 1)
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteLine)) {
            throw "A branch '$branch' nao existe no origin. Envie-a primeiro: git push -u origin $branch"
        }
        $remoteSha = ($remoteLine -split '\s+')[0]
        $localSha = (& git -C $ProjectRoot rev-parse HEAD).Trim()
        if ($LASTEXITCODE -ne 0 -or $remoteSha -ne $localSha) {
            throw 'O commit local nao coincide com o topo remoto. Execute git push e tente novamente.'
        }

        $mergedJson = & gh pr list --head $branch --state merged --json number,title,url,baseRefName,headRefName 2>$null
        if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel verificar PRs anteriores desta branch.' }
        if (-not [string]::IsNullOrWhiteSpace(($mergedJson -join ''))) {
            $mergedPrs = @(($mergedJson -join "`n") | ConvertFrom-Json)
            $mergedIntoMain = @($mergedPrs | Where-Object { $_.baseRefName -eq 'main' })
            if ($mergedIntoMain.Count -gt 0) {
                throw "Esta branch ja foi integrada em main em um PR anterior. Nao crie outro PR vazio; sincronize main para dev ou crie uma nova branch a partir de dev."
            }
        }

        $existingJson = & gh pr list --head $branch --base dev --state open --json number,title,url 2>$null
        if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel consultar PRs existentes com o GitHub CLI.' }
        $existing = @()
        if (-not [string]::IsNullOrWhiteSpace(($existingJson -join ''))) {
            $existing = @(($existingJson -join "`n") | ConvertFrom-Json)
        }
        if ($existing.Count -gt 0) {
            Write-Host 'Ja existe um PR aberto desta branch com destino dev:' -ForegroundColor Yellow
            $existing | Format-Table number, title, url -AutoSize
            return
        }

        & git -C $ProjectRoot config "branch.$branch.gh-merge-base" 'dev'
        if ($LASTEXITCODE -ne 0) { throw 'Nao consegui configurar dev como base padrao desta branch.' }

        if ([string]::IsNullOrWhiteSpace($Titulo)) {
            if ($branch.StartsWith('feature/')) { $kind = 'feat' }
            elseif ($branch.StartsWith('fix/')) { $kind = 'fix' }
            elseif ($branch.StartsWith('docs/')) { $kind = 'docs' }
            else { $kind = 'chore' }
            $description = $branch -replace '^(feature|fix|docs|chore)/', '' -replace '[-_/]+', ' '
            $suggestedTitle = '{0}: {1}' -f $kind, $description
            $Titulo = Read-Host "Titulo do PR (sugestao: $suggestedTitle)"
            if ([string]::IsNullOrWhiteSpace($Titulo)) { $Titulo = $suggestedTitle }
        }

        if ([string]::IsNullOrWhiteSpace($Corpo)) {
            $bodyLines = @(
                '## Resumo',
                "Implementacao da branch $branch.",
                '',
                '## Validacao',
                '- Testes automatizados executados localmente antes do merge.',
                '- Build do frontend executado quando aplicavel.',
                '- Requisitos, regras de negocio e modelo de dados atualizados quando necessario.',
                '',
                '## Revisao',
                '- Conferir arquivos alterados e regras de negocio.',
                '- Confirmar que a base do PR e dev.'
            )
            $Corpo = $bodyLines -join [Environment]::NewLine
        }

        Write-Host "Criando PR: $branch -> dev" -ForegroundColor Cyan
        & gh pr create --base dev --head $branch --title $Titulo --body $Corpo
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o PR. Consulte a mensagem do GitHub CLI.' }
        Write-Host 'PR criado com base explicita em dev.' -ForegroundColor Green
        return
    }

    'MesclarPR' {
        if (-not $ConfirmarMerge) {
            throw 'O merge exige confirmacao. Revise com -Acao StatusPR e depois use -Acao MesclarPR -ConfirmarMerge.'
        }
        $branch = Get-CurrentBranch
        $pr = Get-CurrentPullRequest -Branch $branch
        if ($pr.state -ne 'OPEN') { throw "O PR esta no estado '$($pr.state)', nao OPEN." }
        if ($pr.baseRefName -ne 'dev') { throw "Bloqueado: a base do PR e '$($pr.baseRefName)', mas deve ser dev. Nenhum merge executado." }
        if ($pr.headRefName -ne $branch) { throw "Bloqueado: a branch do PR e '$($pr.headRefName)', mas a branch atual e '$branch'." }
        if ($pr.reviewDecision -eq 'CHANGES_REQUESTED') { throw 'O PR tem alteracoes solicitadas. Resolva-as antes do merge.' }
        if ($pr.mergeStateStatus -in @('DIRTY', 'BLOCKED')) { throw "O GitHub indica estado de merge '$($pr.mergeStateStatus)'. Resolva conflitos/regras antes de tentar novamente." }

        Write-Host "PR: #$($pr.number) - $($pr.title)" -ForegroundColor Cyan
        Write-Host "Origem: $($pr.headRefName) | Destino: $($pr.baseRefName) | Revisao: $($pr.reviewDecision)"
        if ($pr.reviewDecision -ne 'APPROVED') {
            Write-Warning 'O GitHub CLI nao indica aprovacao explicita. Confirme o aceite/revisoes exigidos pela equipe.'
        }
        $confirmation = Read-Host 'Para confirmar o merge em dev, digite MERGE'
        if ($confirmation -cne 'MERGE') {
            Write-Host 'Merge cancelado; nada foi integrado.' -ForegroundColor Yellow
            return
        }

        & gh pr merge $pr.number --merge --delete-branch
        if ($LASTEXITCODE -ne 0) { throw 'O GitHub nao integrou o PR. Confira as aprovacoes e verificacoes exigidas; nao force o merge.' }
        Write-Host 'PR integrado em dev. Atualize dev local e remova a branch local depois de confirmar:' -ForegroundColor Green
        Write-Host '  git switch dev'
        Write-Host '  git pull --ff-only origin dev'
        Write-Host ('  git branch -d {0}' -f $branch)
        return
    }
}
