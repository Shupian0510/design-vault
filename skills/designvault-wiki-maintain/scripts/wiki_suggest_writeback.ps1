param(
    [string[]]$ChangedPath,
    [string[]]$SourcePath,
    [string]$Since = 'HEAD',
    [switch]$AsJson,
    [string]$VaultRoot
)

. (Join-Path $PSScriptRoot 'designvault_common.ps1')

$paths = Get-DesignVaultPaths -VaultRoot $VaultRoot -ScriptRoot $PSScriptRoot -StartPath (Get-Location).Path
$schema = Get-DesignVaultSchema -SchemaPath $paths.SchemaPath
$repoRoot = Get-DesignVaultRepositoryRoot -StartPath (Get-Location).Path
$wikiRecords = Get-DesignVaultWikiTruthRecords -WikiRoot $paths.WikiRoot -Schema $schema -VaultRoot $paths.VaultRoot
$recordByStem = @{}

foreach ($record in $wikiRecords) {
    if (-not $recordByStem.ContainsKey($record.Stem)) {
        $recordByStem[$record.Stem] = New-Object System.Collections.Generic.List[object]
    }

    $recordByStem[$record.Stem].Add($record)
}

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

function Add-ReasonedRecord {
    param(
        [hashtable]$Map,
        [object]$Record,
        [string]$Reason
    )

    if ($null -eq $Record) {
        return
    }

    if (-not $Map.ContainsKey($Record.Path)) {
        $Map[$Record.Path] = [ordered]@{
            record = $Record
            reasons = New-Object System.Collections.Generic.HashSet[string]([System.StringComparer]::OrdinalIgnoreCase)
            changed_paths = New-Object System.Collections.Generic.HashSet[string]([System.StringComparer]::OrdinalIgnoreCase)
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($Reason)) {
        [void]$Map[$Record.Path].reasons.Add($Reason)
    }
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

function Resolve-SourceTargets {
    param(
        [string[]]$Inputs,
        [hashtable]$StemMap,
        [string]$RepoRootPath,
        [string]$WikiRootPath
    )

    $result = [ordered]@{
        Records = @()
        ResolvedSources = @()
    }

    $resolvedMap = @{}
    $resolvedSources = New-Object System.Collections.Generic.List[string]

    foreach ($input in @($Inputs)) {
        if ([string]::IsNullOrWhiteSpace($input)) {
            continue
        }

        $trimmedInput = $input.Trim()
        $resolvedPath = $null
        if (Test-Path -LiteralPath $trimmedInput) {
            $resolvedPath = [string](Resolve-Path -LiteralPath $trimmedInput)
            $resolvedSources.Add((Convert-DesignVaultToRepoRelativePath -Path $resolvedPath -RepoRoot $RepoRootPath))
        }

        if ($null -ne $resolvedPath -and $resolvedPath.StartsWith($WikiRootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
            $stem = [System.IO.Path]::GetFileNameWithoutExtension($resolvedPath)
            foreach ($candidate in @($StemMap[$stem])) {
                if ($candidate.Path.Equals($resolvedPath, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $resolvedMap[$candidate.Path] = $candidate
                }
            }
            continue
        }

        if ($null -ne $resolvedPath) {
            $parsed = Get-DesignVaultFrontmatter -Path $resolvedPath
            $links = New-Object System.Collections.Generic.List[string]

            foreach ($field in @('links', 'related', 'source_notes')) {
                foreach ($entry in (Get-DesignVaultRequiredArray -Frontmatter $parsed.Frontmatter -Name $field)) {
                    $leaf = Get-DesignVaultWikiLinkLeaf -Value $entry
                    if ($leaf) {
                        $links.Add($leaf)
                    }
                }
            }

            foreach ($leaf in (Get-DesignVaultWikiLinks -Content $parsed.Body)) {
                $links.Add($leaf)
            }

            foreach ($leaf in ($links | Sort-Object -Unique)) {
                if (-not $StemMap.ContainsKey($leaf)) {
                    continue
                }

                foreach ($candidate in $StemMap[$leaf]) {
                    if ($null -eq $candidate -or [string]::IsNullOrWhiteSpace([string]$candidate.Path)) {
                        continue
                    }
                    $resolvedMap[$candidate.Path] = $candidate
                }
            }

            continue
        }

        $leaf = Get-DesignVaultWikiLinkLeaf -Value $trimmedInput
        if ($leaf -and $StemMap.ContainsKey($leaf)) {
            foreach ($candidate in $StemMap[$leaf]) {
                if ($null -eq $candidate -or [string]::IsNullOrWhiteSpace([string]$candidate.Path)) {
                    continue
                }
                $resolvedMap[$candidate.Path] = $candidate
            }
        }
    }

    $result.Records = @($resolvedMap.Values)
    $result.ResolvedSources = @($resolvedSources | Sort-Object -Unique)
    return [pscustomobject]$result
}

$changedPaths = Get-NormalizedChangedPaths -InputPaths $ChangedPath -DiffBase $Since -RepoRootPath $repoRoot
$sourceResolution = Resolve-SourceTargets -Inputs $SourcePath -StemMap $recordByStem -RepoRootPath $repoRoot -WikiRootPath $paths.WikiRoot
$suggestionMap = @{}

foreach ($record in $sourceResolution.Records) {
    Add-ReasonedRecord -Map $suggestionMap -Record $record -Reason 'linked_from_source'
}

foreach ($record in $wikiRecords) {
    foreach ($rawCodeRef in (Get-DesignVaultRequiredArray -Frontmatter $record.Frontmatter -Name 'code_refs')) {
        $codeRefPath = Get-DesignVaultCodeRefPath -CodeRef $rawCodeRef -RepoRoot $repoRoot
        if ([string]::IsNullOrWhiteSpace($codeRefPath)) {
            continue
        }

        foreach ($changed in $changedPaths) {
            if (-not (Test-CodeRefMatch -Changed $changed -CodeRefPath $codeRefPath)) {
                continue
            }

            Add-ReasonedRecord -Map $suggestionMap -Record $record -Reason ("code_ref_match:{0}" -f $changed)
            [void]$suggestionMap[$record.Path].changed_paths.Add($changed)
        }
    }
}

foreach ($record in $sourceResolution.Records) {
    foreach ($changed in $changedPaths) {
        [void]$suggestionMap[$record.Path].changed_paths.Add($changed)
    }
}

$suggestions = New-Object System.Collections.Generic.List[object]

foreach ($entry in $suggestionMap.GetEnumerator() | Sort-Object Name) {
    $record = $entry.Value.record
    $frontmatter = $record.Frontmatter
    $currentCodeRefs = @(
        Get-DesignVaultRequiredArray -Frontmatter $frontmatter -Name 'code_refs' |
            ForEach-Object { Get-DesignVaultCodeRefPath -CodeRef $_ -RepoRoot $repoRoot } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique
    )
    $changedForPage = @($entry.Value.changed_paths | Sort-Object)
    $suggestedCodeRefs = @(
        $changedForPage |
            Where-Object { $currentCodeRefs -notcontains $_ } |
            Sort-Object -Unique
    )
    $writebackGuidance = if ($changedForPage.Count -gt 0) {
        'Inspect this page and update it only if current design truth, terminology, formula, UI behavior, or player-facing understanding actually changed.'
    }
    else {
        'This page was selected from source links. Review only if the task meaningfully changed its truth.'
    }
    $humanReviewNote = if ($suggestedCodeRefs.Count -gt 0) {
        'Consider adding new code_refs while reviewing whether truth changed.'
    }
    else {
        'No code_ref additions detected. Review truth change directly.'
    }

    $suggestions.Add([pscustomobject]@{
            wiki_path = $record.Path
            wiki_stem = $record.Stem
            wiki_type = $record.Type
            reasons = @($entry.Value.reasons | Sort-Object)
            changed_paths = $changedForPage
            current_code_refs = $currentCodeRefs
            suggested_code_refs = $suggestedCodeRefs
            writeback_guidance = $writebackGuidance
            human_review_note = $humanReviewNote
        })
}

$explicitWikiPages = @(
    $sourceResolution.Records |
        Sort-Object Path |
        ForEach-Object { $_.Path }
)

if ($AsJson) {
    @{
        changed_paths = @($changedPaths)
        source_paths = @($sourceResolution.ResolvedSources)
        explicit_wiki_pages = @($explicitWikiPages)
        suggestions = @($suggestions | ForEach-Object { $_ })
    } | ConvertTo-Json -Depth 8
    exit 0
}

Write-Output "DesignVault writeback suggestions"
Write-Output ("changed_paths`t{0}" -f $changedPaths.Count)
Write-Output ("source_paths`t{0}" -f $sourceResolution.ResolvedSources.Count)
Write-Output ("suggestions`t{0}" -f $suggestions.Count)

if ($changedPaths.Count -gt 0) {
    Write-Output ''
    Write-Output '[changed_paths]'
    $changedPaths | ForEach-Object { Write-Output $_ }
}

if ($sourceResolution.ResolvedSources.Count -gt 0) {
    Write-Output ''
    Write-Output '[source_paths]'
    $sourceResolution.ResolvedSources | ForEach-Object { Write-Output $_ }
}

if ($suggestions.Count -gt 0) {
    Write-Output ''
    Write-Output '[suggestions]'
    foreach ($suggestion in $suggestions) {
        Write-Output ("wiki`t{0}" -f $suggestion.wiki_path)
        Write-Output ("reasons`t{0}" -f ($suggestion.reasons -join ' | '))
        if ($suggestion.suggested_code_refs.Count -gt 0) {
            Write-Output ("code_refs_add`t{0}" -f ($suggestion.suggested_code_refs -join ' | '))
        }
        if ($suggestion.changed_paths.Count -gt 0) {
            Write-Output ("changed_paths`t{0}" -f ($suggestion.changed_paths -join ' | '))
        }
        Write-Output ("note`t{0}" -f $suggestion.writeback_guidance)
        Write-Output ("review_note`t{0}" -f $suggestion.human_review_note)
        Write-Output ''
    }
}
