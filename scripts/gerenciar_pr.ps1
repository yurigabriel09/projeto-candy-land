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

$script:GhExe = $null
$script:RepoSlug = 'yurigabriel09/projeto-candy-land'

function Find-GhExecutable {
    $command = Get-Command gh -ErrorAction SilentlyContinue
    if ($command -and $command.Source -and (Test-Path -LiteralPath $command.Source -PathType Leaf)) {
        return $command.Source
    }

    $candidates = @()
    if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
        $candidates += (Join-Path $env:ProgramFiles 'GitHub CLI\gh.exe')
    }
    if (-not [string]::IsNullOrWhiteSpace(${env:ProgramFiles(x86)})) {
        $candidates += (Join-Path ${env:ProgramFiles(x86)} 'GitHub CLI\gh.exe')
    }
    if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\GitHub CLI\gh.exe')
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    return $null
}

function Test-PathContainsDirectory {
    param(
        [AllowNull()][string]$PathValue,
        [Parameter(Mandatory = $true)][string]$Directory
    )

    foreach ($entry in ($PathValue -split ';')) {
        $normalizedEntry = $entry.Trim().Trim('"').TrimEnd([char[]]@('\', '/'))
        $normalizedDirectory = $Directory.Trim().TrimEnd([char[]]@('\', '/'))
        if (-not [string]::IsNullOrWhiteSpace($normalizedEntry) -and $normalizedEntry -ieq $normalizedDirectory) {
            return $true
        }
    }
    return $false
}

function Add-GhDirectoryToPath {
    param([Parameter(Mandatory = $true)][string]$Directory)

    if (-not (Test-PathContainsDirectory -PathValue $env:Path -Directory $Directory)) {
        $env:Path = "$Directory;$env:Path"
    }

    # Persist for future terminals when possible. The script still invokes gh.exe
    # by its full path, so it does not depend on a stale PATH in VS Code/Windows Terminal.
    try {
        $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        if (-not (Test-PathContainsDirectory -PathValue $userPath -Directory $Directory)) {
            $userEntries = @($userPath -split ';' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
            $userEntries += $Directory
            [Environment]::SetEnvironmentVariable('Path', ($userEntries -join ';'), 'User')
            Write-Host 'Caminho do GitHub CLI salvo no PATH do usuario.' -ForegroundColor Green
        }
    }
    catch {
        Write-Warning 'Nao foi possivel atualizar o PATH permanente do usuario. O gerenciador continuara funcionando nesta execucao.'
    }
}

function Assert-GhInstalled {
    $ghPath = Find-GhExecutable
    if (-not $ghPath) {
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if (-not $winget) {
            throw 'GitHub CLI nao foi encontrado nem no PATH nem nos caminhos padrao, e winget nao esta disponivel. Instale o GitHub CLI em https://cli.github.com/.'
        }

        Write-Host 'GitHub CLI nao encontrado. Tentando instalar automaticamente pelo WinGet...' -ForegroundColor Cyan
        & $winget.Source install --id GitHub.cli --source winget --exact --accept-package-agreements --accept-source-agreements
        $installExitCode = $LASTEXITCODE
        $ghPath = Find-GhExecutable
        if (-not $ghPath) {
            if ($installExitCode -ne 0) {
                throw 'A instalacao do GitHub CLI falhou. Confira a mensagem do WinGet e tente novamente.'
            }
            throw 'O WinGet terminou, mas nao encontrei gh.exe nos caminhos esperados. Abra outro terminal ou instale pelo site https://cli.github.com/.'
        }
    }

    $script:GhExe = $ghPath
    Add-GhDirectoryToPath -Directory (Split-Path -Parent $ghPath)
}

function Assert-GhAuthenticated {
    Assert-GhInstalled

    & $script:GhExe auth status --hostname github.com *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Nao existe uma sessao GitHub ativa. Vou iniciar a autenticacao pelo navegador...' -ForegroundColor Yellow
        & $script:GhExe auth login --hostname github.com --git-protocol https --web
        if ($LASTEXITCODE -ne 0) {
            throw 'A autenticacao nao foi concluida. Repita a acao e finalize o fluxo no navegador.'
        }
    }

    & $script:GhExe auth status --hostname github.com
    if ($LASTEXITCODE -ne 0) {
        throw 'O GitHub CLI ainda nao confirma a autenticacao.'
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

    $json = & $script:GhExe pr list --head $Branch --state open --json number,url,title,state,baseRefName,headRefName,reviewDecision,mergeStateStatus --repo $script:RepoSlug 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Nao foi possivel consultar PRs abertos para '$Branch'. Confira sua conexao e o acesso ao repositorio."
    }

    $jsonText = ($json -join "`n").Trim()
    if ([string]::IsNullOrWhiteSpace($jsonText)) { return $null }

    $pullRequests = @($jsonText | ConvertFrom-Json)
    if ($pullRequests.Count -eq 0) { return $null }

    # Prefer the expected destination (dev); if the only open PR targets another
    # branch, return it so StatusPR can warn and MesclarPR can block it.
    $devPullRequests = @($pullRequests | Where-Object { $_.baseRefName -eq 'dev' })
    if ($devPullRequests.Count -gt 0) { return $devPullRequests[0] }
    return $pullRequests[0]
}

if ($Acao -eq 'Instalar') {
    Assert-GhInstalled
    Write-Host 'GitHub CLI pronto:' -ForegroundColor Green
    & $script:GhExe --version
    Write-Host 'A autenticacao e verificada automaticamente nas acoes de PR.'
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

# These steps are automatic for Autenticar, StatusPR, CriarPR and MesclarPR:
# locate/install gh.exe, expose it in this process and authenticate if necessary.
Assert-GhInstalled
if ($Acao -eq 'Autenticar') {
    Assert-GhAuthenticated
    Write-Host 'Voce esta autenticado no GitHub.' -ForegroundColor Green
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
        if (-not $pr) {
            Write-Host "Nao existe PR aberto para a branch '$branch'." -ForegroundColor Yellow
            Write-Host 'Para criar a PR com destino correto, execute:'
            Write-Host ('.\scripts\gerenciar_pr.cmd -Acao CriarPR -Titulo "feat: descreve a tarefa"')
            return
        }
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

        $mergedJson = & $script:GhExe pr list --head $branch --state merged --json number,title,url,baseRefName,headRefName --repo $script:RepoSlug 2>$null
        if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel verificar PRs anteriores desta branch.' }
        if (-not [string]::IsNullOrWhiteSpace(($mergedJson -join ''))) {
            $mergedPrs = @(($mergedJson -join "`n") | ConvertFrom-Json)
            $mergedIntoMain = @($mergedPrs | Where-Object { $_.baseRefName -eq 'main' })
            if ($mergedIntoMain.Count -gt 0) {
                throw "Esta branch ja foi integrada em main em um PR anterior. Nao crie outro PR vazio; sincronize main para dev ou crie uma nova branch a partir de dev."
            }
        }

        $existingJson = & $script:GhExe pr list --head $branch --state open --json number,title,url,baseRefName --repo $script:RepoSlug 2>$null
        if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel consultar PRs existentes com o GitHub CLI.' }
        $existing = @()
        if (-not [string]::IsNullOrWhiteSpace(($existingJson -join ''))) {
            $existing = @(($existingJson -join "`n") | ConvertFrom-Json)
        }
        if ($existing.Count -gt 0) {
            $existingForDev = @($existing | Where-Object { $_.baseRefName -eq 'dev' })
            if ($existingForDev.Count -gt 0) {
                Write-Host 'Ja existe um PR aberto desta branch com destino dev:' -ForegroundColor Yellow
                $existingForDev | Format-Table number, title, url -AutoSize
                return
            }
            $existing | Format-Table number, title, url, baseRefName -AutoSize
            throw 'Ja existe um PR aberto desta branch com outro destino. Corrija ou feche o PR existente antes de criar outro para dev.'
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
        & $script:GhExe pr create --repo $script:RepoSlug --base dev --head $branch --title $Titulo --body $Corpo
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
        if (-not $pr) { throw "Nao existe PR aberto para '$branch'. Crie-o primeiro com -Acao CriarPR." }
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

        & $script:GhExe pr merge $pr.number --repo $script:RepoSlug --merge --delete-branch
        if ($LASTEXITCODE -ne 0) { throw 'O GitHub nao integrou o PR. Confira as aprovacoes e verificacoes exigidas; nao force o merge.' }
        Write-Host 'PR integrado em dev. Atualize dev local e remova a branch local depois de confirmar:' -ForegroundColor Green
        Write-Host '  git switch dev'
        Write-Host '  git pull --ff-only origin dev'
        Write-Host ('  git branch -d {0}' -f $branch)
        return
    }
}
