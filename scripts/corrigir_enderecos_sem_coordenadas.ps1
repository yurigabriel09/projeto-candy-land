[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Update-ProjectFile([string]$RelativePath, [scriptblock]$Transform) {
    $path = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Arquivo não encontrado: $RelativePath"
    }
    $content = [System.IO.File]::ReadAllText($path)
    $updated = & $Transform $content
    if ($updated -cne $content) {
        [System.IO.File]::WriteAllText($path, $updated, (New-Object System.Text.UTF8Encoding($false)))
        Write-Host "Atualizado: $RelativePath" -ForegroundColor Green
    } else {
        Write-Host "Sem mudanças necessárias: $RelativePath" -ForegroundColor DarkGray
    }
}

function Remove-RequiredPattern([string]$Content, [string]$Pattern, [string]$Label, [int]$Maximum = 1) {
    $found = [regex]::Matches($Content, $Pattern)
    if ($found.Count -gt $Maximum) {
        throw "Mais de um bloco '$Label' encontrado ($($found.Count)); arquivo não será salvo."
    }
    if ($found.Count -eq 0) { return $Content }
    return [regex]::Replace(
        $Content, $Pattern, '',
        [System.Text.RegularExpressions.RegexOptions]::Singleline,
        [TimeSpan]::FromSeconds(2)
    )
}

# A doceria não precisa iniciar uma geocodificação no React e repetir a
# mesma consulta ao salvar. O backend é a única fonte de coordenadas.
Update-ProjectFile 'frontend/src/pages/BusinessRegister.jsx' {
    param($content)
    $content = [regex]::Replace($content, '(?m)^\s*import\s+AddressCoordinates\s+from\s+"\.\./components/AddressCoordinates";\s*\r?\n', '')
    $content = [regex]::Replace($content, '(?m)^\s*import\s+useRestaurantAddressGeocoding\s+from\s+"\.\./hooks/useRestaurantAddressGeocoding";\s*\r?\n', '')
    $content = Remove-RequiredPattern $content 'const\s+geocodeState\s*=\s*useRestaurantAddressGeocoding\(\{[\s\S]*?\r?\n\s*\}\);\s*' 'hook de geocoding do cadastro comercial'
    $content = Remove-RequiredPattern $content 'if\s*\(loadingCep\s*\|\|\s*geocodeState\.geocoding\)\s*\{[\s\S]*?\r?\n\s*\}' 'espera da geocodificação no frontend'
    $content = $content.Replace('if (loadingCep || geocodeState.geocoding)', 'if (loadingCep)')
    $content = Remove-RequiredPattern $content 'if\s*\(geocodeState\.showManualCoordinates\s*&&\s*\(form\.latitude\s*==\s*null\s*\|\|\s*form\.longitude\s*==\s*null\)\)\s*\{[\s\S]*?\r?\n\s*\}' 'bloqueio por coordenadas manuais'
    $content = Remove-RequiredPattern $content '<div className="form-section">\s*<h3>Localização para cálculo de entrega</h3>[\s\S]*?<AddressCoordinates\b[\s\S]*?/>[\s\S]*?</div>' 'seção de localização e coordenadas do cadastro comercial'
    $content = [regex]::Replace($content, '(?m)^\s*latitude:\s*form\.latitude,?\s*\r?\n\s*longitude:\s*form\.longitude,?\s*\r?\n', '')
    $content = $content.Replace('disabled={loading || loadingCep || geocodeState.geocoding}', 'disabled={loading || loadingCep}')
    $content = $content.Replace('{loading ? "Criando empresa..." : geocodeState.geocoding ? "Localizando endereço..." : "Criar conta empresarial"}', '{loading ? "Criando empresa..." : "Criar conta empresarial"}')
    if ($content -match 'geocodeState|AddressCoordinates|latitude:\s*form\.latitude|longitude:\s*form\.longitude') {
        throw 'BusinessRegister.jsx ainda contém dependências de coordenadas manuais/geocoding no cliente.'
    }
    return $content
}

Update-ProjectFile 'frontend/src/pages/RestaurantConfiguration.jsx' {
    param($content)
    $content = [regex]::Replace($content, '(?m)^\s*import\s+AddressCoordinates\s+from\s+"\.\./components/AddressCoordinates";\s*\r?\n', '')
    $content = [regex]::Replace($content, '(?m)^\s*import\s+useRestaurantAddressGeocoding\s+from\s+"\.\./hooks/useRestaurantAddressGeocoding";\s*\r?\n', '')
    $content = [regex]::Replace($content, '(?m)^import\s+\{\s*useCallback,\s*useEffect,\s*useRef,\s*useState\s*\}\s+from\s+"react";', 'import { useEffect, useRef, useState } from "react";')
    $content = Remove-RequiredPattern $content 'const\s+geocodeState\s*=\s*useRestaurantAddressGeocoding\(\{[\s\S]*?\r?\n\s*\}\);\s*' 'hook de geocoding da configuração comercial'
    $content = Remove-RequiredPattern $content 'const\s+handleLocationChange\s*=\s*useCallback\([\s\S]*?\r?\n\s*\},\s*\[\]\);\s*' 'handler das coordenadas manuais'
    $content = Remove-RequiredPattern $content 'if\s*\(geocodeState\.showManualCoordinates\s*&&\s*\(address\.latitude\s*==\s*null\s*\|\|\s*address\.longitude\s*==\s*null\)\)\s*\{[\s\S]*?\r?\n\s*\}' 'bloqueio de configuração por coordenadas manuais'
    $content = Remove-RequiredPattern $content '\s*\{geocodeState\.geocoding\s*&&\s*\([\s\S]*?\)\}\s*\{geocodeState\.geocodingError\s*&&\s*\([\s\S]*?\)\}\s*<AddressCoordinates\b[\s\S]*?/>\s*' 'bloco de coordenadas manuais na configuração'
    $content = [regex]::Replace($content, '(?m)^\s*latitude:\s*null,\s*\r?\n\s*longitude:\s*null,?\s*\r?\n', '')
    $content = [regex]::Replace($content, '(?m)^\s*latitude:\s*address\.latitude,?\s*\r?\n\s*longitude:\s*address\.longitude,?\s*\r?\n', '')
    $content = $content.Replace('disabled={saving || loadingCep || geocodeState.geocoding}', 'disabled={saving || loadingCep}')
    if ($content -match 'geocodeState|AddressCoordinates|useCallback') {
        throw 'RestaurantConfiguration.jsx ainda contém dependências de coordenadas manuais/geocoding no cliente.'
    }
    return $content
}

Update-ProjectFile 'frontend/src/pages/PersonalRegister.jsx' {
    param($content)
    $content = [regex]::Replace($content, '(?m)^\s*import\s+AddressCoordinates\s+from\s+"\.\./components/AddressCoordinates";\s*\r?\n', '')
    $content = [regex]::Replace($content, '(?m)^\s*latitude:\s*null,\s*\r?\n\s*longitude:\s*null,?\s*\r?\n', '')
    $content = [regex]::Replace($content, '(?m)^\s*latitude:\s*form\.latitude,?\s*\r?\n\s*longitude:\s*form\.longitude,?\s*\r?\n', '')
    $content = Remove-RequiredPattern $content '\s*<AddressCoordinates\b[\s\S]*?/>\s*' 'componente de coordenadas do cadastro do cliente'
    if ($content -match 'AddressCoordinates|latitude:\s*form\.latitude|longitude:\s*form\.longitude') {
        throw 'PersonalRegister.jsx ainda envia ou exibe coordenadas manuais.'
    }
    return $content
}

Update-ProjectFile 'frontend/src/pages/DadosPessoais.jsx' {
    param($content)
    $content = Remove-RequiredPattern $content 'async\s+function\s+obterCoordenadasEmSegundoPlano\([\s\S]*?\r?\n\}\s*\r?\n\s*(?=function\s+DadosPessoais\()' 'função client-side Nominatim'
    $content = Remove-RequiredPattern $content '\s*let\s+lat\s*=\s*formEndereco\.latitude;[\s\S]*?(?=\s*const\s+payload\s*=)' 'consulta de coordenadas no navegador'
    $content = [regex]::Replace($content, '(?m)^\s*latitude:\s*lat,?\s*\r?\n\s*longitude:\s*lng,?\s*\r?\n', '')
    $content = [regex]::Replace($content, '(?m)^\s*latitude:\s*null,\s*\r?\n\s*longitude:\s*null,?\s*\r?\n', '')
    $content = [regex]::Replace($content, '(?m)^\s*latitude:\s*end\.latitude\s*\?\?\s*null,?\s*\r?\n\s*longitude:\s*end\.longitude\s*\?\?\s*null,?\s*\r?\n', '')
    if ($content -match 'obterCoordenadasEmSegundoPlano|nominatim\.openstreetmap\.org|latitude:\s*lat|longitude:\s*lng') {
        throw 'DadosPessoais.jsx ainda geocodifica no cliente ou envia coordenadas.'
    }
    return $content
}

Write-Host ''
Write-Host 'Concluído: o frontend envia somente endereço e número; o backend resolve as coordenadas.' -ForegroundColor Green
Write-Host 'A chave Google permanece somente no backend/.env.'
