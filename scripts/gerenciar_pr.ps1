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
$ExpectedOriginPattern = 'github\.com[:/]yurigabriel09/projeto-candy-land(\.git)?$'

function Get-GhCommand {
    return Get-Command gh -ErrorAction SilentlyContinue
}

function Assert-GhInstalled {
    if (-not (Get-GhCommand)) {
        throw "GitHub CLI (gh) não foi encontrado no PATH. Execute primeiro: .\scripts\gerenciar_pr.ps1 -Acao Instalar. Depois feche todos os terminais e abra um PowerShell novo."
    }
}

function Assert-GhAuthenticated {
    Assert-GhInstalled
    & gh auth status --hostname github.com
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub CLI ainda não está autenticado. Execute: .\scripts\gerenciar_pr.ps1 -Acao Autenticar"
    }
}

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & git -C $ProjectRoot @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Falha no comando git: git $($Arguments -join ' ')"
    }
}

function Get-CurrentBranch {
    $branch = (& git -C $ProjectRoot branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($branch)) {
        throw 'Não consegui identificar a branch atual.'
    }
    if ($branch -in @('main', 'dev')) {
        throw "Por segurança, não abra nem mescle PR a partir da branch '$branch'. Mude para sua branch feature/fix/docs."
    }
    return $branch
}

function Get-CurrentPullRequest {
    param([Parameter(Mandatory = $true)][string]$Branch)
    $json = & gh pr view $Branch --json number,url,title,state,baseRefName,headRefName,reviewDecision,mergeStateStatus 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($json -join ''))) {
        throw "Não encontrei um Pull Request para a branch '$Branch'. Crie-o com: .\scripts\gerenciar_pr.ps1 -Acao CriarPR"
    }
    return ($json -join "`n") | ConvertFrom-Json
}

switch ($Acao) {
    'Instalar' {
        if (Get-GhCommand) {
            Write-Host 'GitHub CLI já está instalado:' -ForegroundColor Green
            & gh --version
            Write-Host 'Se ainda não autenticou, execute: .\scripts\gerenciar_pr.ps1 -Acao Autenticar'
            return
        }

        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if (-not $winget) {
            throw 'winget não foi encontrado. Instale/atualize o App Installer do Windows e tente novamente, ou siga https://github.com/cli/cli/blob/trunk/docs/install_windows.md.'
        }

        Write-Host 'Instalando GitHub CLI pelo WinGet...' -ForegroundColor Cyan
        & $winget.Source install --id GitHub.cli --source winget --exact --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            throw 'A instalação do GitHub CLI falhou. Leia a mensagem do WinGet e tente novamente.'
        }

        Write-Host ''
        Write-Host 'Instalação concluída. Feche TODAS as janelas do PowerShell/Windows Terminal e abra uma nova.' -ForegroundColor Green
        Write-Host 'Depois execute: .\scripts\gerenciar_pr.ps1 -Acao Autenticar'
        return
    }

    'Atualizar' {
        if (-not (Get-GhCommand)) {
            throw "GitHub CLI não está instalado. Execute: .\scripts\gerenciar_pr.ps1 -Acao Instalar"
        }
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if (-not $winget) {
            throw 'winget não foi encontrado. Atualize o GitHub CLI pelo instalador oficial: https://cli.github.com/.'
        }
        & $winget.Source upgrade --id GitHub.cli --source winget --exact --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            throw 'A atualização do GitHub CLI falhou. Confira a mensagem do WinGet.'
        }
        Write-Host 'Verifique a versão do gh em um terminal novo: gh --version' -ForegroundColor Green
        return
    }

    'Autenticar' {
        Assert-GhInstalled
        & gh auth status --hostname github.com
        if ($LASTEXITCODE -eq 0) {
            Write-Host 'Você já está autenticado no GitHub.' -ForegroundColor Green
            return
        }

        & gh auth login --hostname github.com --git-protocol https --web
        if ($LASTEXITCODE -ne 0) {
            throw 'A autenticação não foi concluída. Execute novamente esta ação e finalize o fluxo no navegador.'
        }
        & gh auth status --hostname github.com
        if ($LASTEXITCODE -ne 0) {
            throw 'O GitHub CLI ainda não confirma a autenticação.'
        }
        return
    }

    default {
        Assert-GhAuthenticated
    }
}

$originUrl = (& git -C $ProjectRoot remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $originUrl -notmatch $ExpectedOriginPattern) {
    throw "O remote 'origin' não aponta para yurigabriel09/projeto-candy-land. URL detectada: '$originUrl'. Nenhuma ação foi executada."
}

switch ($Acao) {
    'StatusPR' {
        $branch = Get-CurrentBranch
        $pr = Get-CurrentPullRequest -Branch $branch
        [pscustomobject]@{
            Titulo       = $pr.title
            URL          = $pr.url
            Estado       = $pr.state
            Base         = $pr.baseRefName
            Origem       = $pr.headRefName
            Revisao      = $pr.reviewDecision
            EstadoMerge  = $pr.mergeStateStatus
        } | Format-List
        if ($pr.baseRefName -ne 'dev') {
            Write-Warning "Este PR não está direcionado para dev (base atual: '$($pr.baseRefName)'). Não o mescle com este script."
        }
        return
    }

    'CriarPR' {
        $branch = Get-CurrentBranch
        Invoke-Git -Arguments @('fetch', 'origin')

        $workingTree = (& git -C $ProjectRoot status --porcelain) -join "`n"
        if (-not [string]::IsNullOrWhiteSpace($workingTree)) {
            throw "A árvore de trabalho não está limpa. Faça commit ou guarde as alterações antes de criar o PR:`n$workingTree"
        }

        & git -C $ProjectRoot merge-base --is-ancestor origin/dev HEAD
        if ($LASTEXITCODE -ne 0) {
            throw "Sua branch não contém o origin/dev mais recente. Atualize/rebaseie a branch de trabalho a partir de dev e rode os testes antes de abrir o PR."
        }

        $remoteLine = (& git -C $ProjectRoot ls-remote --heads origin $branch) | Select-Object -First 1
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteLine)) {
            throw "A branch '$branch' ainda não existe no origin. Envie-a primeiro com: git push -u origin $branch"
        }
        $remoteSha = ($remoteLine -split '\s+')[0]
        $localSha = (& git -C $ProjectRoot rev-parse HEAD).Trim()
        if ($remoteSha -ne $localSha) {
            throw "O commit local ($localSha) não coincide com o topo remoto ($remoteSha). Faça push e tente novamente."
        }

        $existingJson = & gh pr list --head $branch --base dev --state open --json number,title,url 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw 'Não foi possível consultar PRs existentes com o GitHub CLI.'
        }
        $existing = @()
        if (-not [string]::IsNullOrWhiteSpace(($existingJson -join ''))) {
            $existing = @((($existingJson -join "`n") | ConvertFrom-Json))
        }
        if ($existing.Count -gt 0) {
            Write-Host "Já existe um PR aberto para esta branch com destino dev:" -ForegroundColor Yellow
            $existing | Format-Table number, title, url -AutoSize
            return
        }

        # Grava a base padrão desta branch no Git local e também passa --base explicitamente.
        & git -C $ProjectRoot config "branch.$branch.gh-merge-base" 'dev'
        if ($LASTEXITCODE -ne 0) { throw 'Não consegui configurar dev como base padrão desta branch.' }

        if ([string]::IsNullOrWhiteSpace($Titulo)) {
            $kind = if ($branch.StartsWith('feature/')) { 'feat' } elseif ($branch.StartsWith('fix/')) { 'fix' } elseif ($branch.StartsWith('docs/')) { 'docs' } else { 'chore' }
            $description = $branch -replace '^(feature|fix|docs|chore)/', '' -replace '[-_/]+', ' '
            $Titulo = Read-Host "Título do PR (sugestão: $kind`: $description)"
            if ([string]::IsNullOrWhiteSpace($Titulo)) { $Titulo = "$kind`: $description" }
        }
        if ([string]::IsNullOrWhiteSpace($Corpo)) {
            $Corpo = @"
## Resumo
Implementação da branch `$branch`.

## Validação
- Testes automatizados executados localmente antes do merge.
- Build do frontend executado quando aplicável.
- Requisitos, regras de negócio e modelo de dados atualizados quando necessário.

## Revisão
- Conferir os arquivos alterados e as regras de negócio.
- Confirmar que a base do PR é `dev`.
"@
        }

        Write-Host "Criando PR: $branch -> dev" -ForegroundColor Cyan
        & gh pr create --base dev --head $branch --title $Titulo --body $Corpo
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o PR. Consulte a mensagem do GitHub CLI.' }
        Write-Host 'PR criado com base explícita em dev.' -ForegroundColor Green
        return
    }

    'MesclarPR' {
        if (-not $ConfirmarMerge) {
            throw 'O merge exige confirmação explícita. Revise primeiro com -Acao StatusPR; depois use -Acao MesclarPR -ConfirmarMerge.'
        }

        $branch = Get-CurrentBranch
        $pr = Get-CurrentPullRequest -Branch $branch
        if ($pr.state -ne 'OPEN') { throw "O PR está no estado '$($pr.state)', não OPEN." }
        if ($pr.baseRefName -ne 'dev') { throw "Bloqueado: a base do PR é '$($pr.baseRefName)', mas deve ser dev. Nenhum merge foi executado." }
        if ($pr.headRefName -ne $branch) { throw "Bloqueado: a branch do PR é '$($pr.headRefName)', mas a branch atual é '$branch'." }
        if ($pr.reviewDecision -eq 'CHANGES_REQUESTED') { throw 'O PR tem alterações solicitadas pela revisão. Resolva-as antes do merge.' }

        Write-Host "PR: #$($pr.number) — $($pr.title)" -ForegroundColor Cyan
        Write-Host "Origem: $($pr.headRefName) | Destino: $($pr.baseRefName) | Revisão: $($pr.reviewDecision)"
        if ($pr.reviewDecision -ne 'APPROVED') {
            Write-Warning 'O GitHub CLI não informa uma aprovação explícita. Confirme que a revisão/aceite exigidos pela equipe foram concluídos.'
        }
        $confirmation = Read-Host "Para confirmar o merge em dev, digite MERGE"
        if ($confirmation -cne 'MERGE') {
            Write-Host 'Merge cancelado; nenhuma alteração foi integrada.' -ForegroundColor Yellow
            return
        }

        & gh pr merge $pr.number --merge
        if ($LASTEXITCODE -ne 0) {
            throw 'O GitHub não integrou o PR. Confira as aprovações e verificações exigidas; não force o merge.'
        }
        Write-Host 'PR integrado. Atualize dev e só então remova a branch local:' -ForegroundColor Green
        Write-Host '  git switch dev'
        Write-Host '  git pull --ff-only origin dev'
        Write-Host "  git branch -d $branch"
        return
    }
}
