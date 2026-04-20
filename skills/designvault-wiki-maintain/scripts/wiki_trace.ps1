param(
    [string[]]$ChangedPath,
    [string]$Since = 'HEAD',
    [switch]$AsJson,
    [string]$VaultRoot
)

. (Join-Path $PSScriptRoot 'designvault_common.ps1')

$paths = Get-DesignVaultPaths -VaultRoot $VaultRoot -ScriptRoot $PSScriptRoot -StartPath (Get-Location).Path
$schema = Get-DesignVaultSchema -SchemaPath $paths.SchemaPath
$repoRoot = Get-DesignVaultRepositoryRoot -StartPath (Get-Location).Path
$wikiRecords = Get-DesignVaultWikiTruthRecords -WikiRoot $paths.WikiRoot -Schema $schema -VaultRoot $paths.VaultRoot

function Get-NormalizedChangedPaths {
    param(
        [string[]]$InputPaths,
        [string]$DiffBase,
        [string]$RepoRootPath
    )

    if ($null -ne $InputPaths -and $InputPaths.Count -gt 0) {
        return @(
            $InputPaths |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
                ForEach-Object { Convert-DesignVaultToRepoRelativePath -Path $_ -RepoRoot $RepoRootPath } |
                Sort-Object -Unique
        )
    }

    $gitOutput = @(& git -C $RepoRootPath diff --name-only $DiffBase -- 2>$null)
    if ($LASTEXITCODE -ne 0) {
        return @()
    }

    return @(
        $gitOutput |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            ForEach-Object { $_.Trim().Replace('\', '/') } |
            Sort-Object -Unique
    )
}

function Test-CodeRefMatch {
    param(
        [string]$Changed,
        [string]$CodeRefPath
    )

    if ([string]::IsNullOrWhiteSpace($Changed) -or [string]::IsNullOrWhiteSpace($CodeRefPath)) {
        return $false
    }

    if ($Changed.Equals($CodeRefPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }

    if ($Changed.StartsWith(($CodeRefPath.TrimEnd('/') + '/'), [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }

    return $false
}

$changedPaths = Get-NormalizedChangedPaths -InputPaths $ChangedPath -DiffBase $Since -RepoRootPath $repoRoot
$matches = New-Object System.Collections.Generic.List[object]

foreach ($record in $wikiRecords) {
    $frontmatter = $record.Frontmatter

    foreach ($rawCodeRef in (Get-DesignVaultRequiredArray -Frontmatter $frontmatter -Name 'code_refs')) {
        $codeRefPath = Get-DesignVaultCodeRefPath -CodeRef $rawCodeRef -RepoRoot $repoRoot
        if ([string]::IsNullOrWhiteSpace($codeRefPath)) {
            continue
        }

        foreach ($changed in $changedPaths) {
            if (-not (Test-CodeRefMatch -Changed $changed -CodeRefPath $codeRefPath)) {
                continue
            }

            $matches.Add([pscustomobject]@{
                    wiki_path = $record.Path
                    wiki_stem = $record.Stem
                    wiki_type = $record.Type
                    matched_code_ref = $codeRefPath
                    changed_path = $changed
                })
        }
    }
}

if ($AsJson) {
    [pscustomobject]@{
        changed_paths = $changedPaths
        matches = @($matches)
    } | ConvertTo-Json -Depth 6
    exit 0
}

Write-Output "DesignVault wiki trace"
Write-Output ("changed_paths`t{0}" -f $changedPaths.Count)
Write-Output ("matches`t{0}" -f $matches.Count)

if ($changedPaths.Count -gt 0) {
    Write-Output ''
    Write-Output '[changed_paths]'
    $changedPaths | ForEach-Object { Write-Output $_ }
}

if ($matches.Count -gt 0) {
    Write-Output ''
    Write-Output '[matches]'
    $matches |
        Sort-Object wiki_stem, changed_path |
        ForEach-Object {
            Write-Output ("{0}`t{1}`t{2}" -f $_.wiki_path, $_.changed_path, $_.matched_code_ref)
        }
}
