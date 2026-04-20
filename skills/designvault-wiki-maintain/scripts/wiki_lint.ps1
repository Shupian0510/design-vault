param(
    [switch]$FailOnIssues,
    [string]$VaultRoot
)

. (Join-Path $PSScriptRoot 'designvault_common.ps1')

$paths = Get-DesignVaultPaths -VaultRoot $VaultRoot -ScriptRoot $PSScriptRoot -StartPath (Get-Location).Path
$schema = Get-DesignVaultSchema -SchemaPath $paths.SchemaPath
$indexPath = Join-Path $paths.VaultRoot 'index.md'
$wikiHomePath = Join-Path $paths.WikiRoot 'Home.md'
$wikiFiles = Get-DesignVaultWikiTruthFiles -WikiRoot $paths.WikiRoot -Schema $schema -VaultRoot $paths.VaultRoot
$studioFiles = Get-DesignVaultTrackedStudioFiles -VaultRoot $paths.VaultRoot -Schema $schema
$longformRoot = Join-DesignVaultPath -BasePath $paths.StudioRoot -RelativePath 'Todo - Design/Longform'
$longformFiles = @(
    $studioFiles | Where-Object { Test-DesignVaultPathUnderRoot -Path $_.FullName -Root $longformRoot }
)

function Get-FileContent {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return ''
    }

    return Get-Content -LiteralPath $Path -Raw
}

function Test-RequiredFieldValue {
    param(
        [Parameter(Mandatory)]
        [hashtable]$Frontmatter,
        [Parameter(Mandatory)]
        [string]$Name
    )

    if (-not $Frontmatter.Contains($Name)) {
        return $false
    }

    $value = $Frontmatter[$Name]
    if ($value -is [System.Array]) {
        return $true
    }

    return -not [string]::IsNullOrWhiteSpace([string]$value)
}

function Get-NormalizedOwnershipKey {
    param(
        [Parameter(Mandatory)]
        [string]$Type,
        [Parameter(Mandatory)]
        [string]$FileName
    )

    $stem = [System.IO.Path]::GetFileNameWithoutExtension($FileName)
    switch ($Type) {
        'system' { return ($stem -replace '^系统 -\s*', '').Trim().ToLowerInvariant() }
        'concept' { return ($stem -replace '^概念 -\s*', '').Trim().ToLowerInvariant() }
        'surface' { return ($stem -replace '^界面 -\s*', '').Trim().ToLowerInvariant() }
        default { return $null }
    }
}

function Add-FrontmatterValidationIssues {
    param(
        [Parameter(Mandatory)]
        [object]$Issues,
        [Parameter(Mandatory)]
        [hashtable]$Frontmatter,
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [hashtable]$PageSpec
    )

    foreach ($field in $PageSpec.required_fields) {
        if (-not (Test-RequiredFieldValue -Frontmatter $Frontmatter -Name $field)) {
            $Issues.Add("missing_field`t$field`t$Path")
        }
    }

    foreach ($field in $PageSpec.array_fields) {
        if ($Frontmatter.Contains($field) -and -not ($Frontmatter[$field] -is [System.Array])) {
            $Issues.Add("field_not_array`t$field`t$Path")
        }
    }
}

function Test-AllowedValue {
    param(
        [AllowNull()]
        [string]$Value,
        [AllowNull()]
        [object[]]$AllowedValues
    )

    if ([string]::IsNullOrWhiteSpace($Value) -or $null -eq $AllowedValues) {
        return $true
    }

    return $AllowedValues -contains $Value
}

$entryContent = (Get-FileContent -Path $indexPath) + "`n" + (Get-FileContent -Path $wikiHomePath)
$linkedNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

foreach ($name in (Get-DesignVaultWikiLinks -Content $entryContent)) {
    [void]$linkedNames.Add($name)
}

foreach ($file in $wikiFiles) {
    foreach ($name in (Get-DesignVaultWikiLinks -Content (Get-FileContent -Path $file.FullName))) {
        [void]$linkedNames.Add($name)
    }
}

$issues = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$definitionOwnership = @{}
$surfaceOwnership = @{}
$longformReferenceMap = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

foreach ($file in $wikiFiles) {
    $parsed = Get-DesignVaultFrontmatter -Path $file.FullName
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)

    if (-not $parsed.HasFrontmatter) {
        $issues.Add("missing_frontmatter`t$($file.FullName)")
        continue
    }

    foreach ($parseError in $parsed.Errors) {
        $issues.Add("frontmatter_parse_error`t$parseError`t$($file.FullName)")
    }

    $frontmatter = $parsed.Frontmatter
    $type = if ($frontmatter.Contains('type')) { [string]$frontmatter.type } else { $null }
    if ([string]::IsNullOrWhiteSpace($type) -or -not $schema.wiki.page_types.ContainsKey($type)) {
        $typeLabel = if ([string]::IsNullOrWhiteSpace($type)) { 'missing' } else { $type }
        $issues.Add("invalid_type`t$typeLabel`t$($file.FullName)")
        continue
    }

    $pageSpec = $schema.wiki.page_types[$type]
    Add-FrontmatterValidationIssues -Issues $issues -Frontmatter $frontmatter -Path $file.FullName -PageSpec $pageSpec

    $status = if ($frontmatter.Contains('status')) { [string]$frontmatter.status } else { $null }
    if (-not (Test-AllowedValue -Value $status -AllowedValues $schema.wiki.status_values)) {
        $issues.Add("invalid_status`t$status`t$($file.FullName)")
    }

    $managedBy = if ($frontmatter.Contains('managed_by')) { [string]$frontmatter.managed_by } else { $null }
    if (-not (Test-AllowedValue -Value $managedBy -AllowedValues $schema.managed_by_values)) {
        $issues.Add("invalid_managed_by`t$managedBy`t$($file.FullName)")
    }

    $updated = if ($frontmatter.Contains('updated')) { [string]$frontmatter.updated } else { $null }
    if (-not [string]::IsNullOrWhiteSpace($updated) -and $updated -notmatch '^\d{4}-\d{2}-\d{2}$') {
        $issues.Add("invalid_updated_date`t$updated`t$($file.FullName)")
    }

    if (-not $linkedNames.Contains($stem)) {
        $issues.Add("orphan`t$($file.FullName)")
    }

    foreach ($sourceNote in (Get-DesignVaultRequiredArray -Frontmatter $frontmatter -Name 'source_notes')) {
        $leaf = Get-DesignVaultWikiLinkLeaf -Value $sourceNote
        if ($leaf) {
            [void]$longformReferenceMap.Add($leaf)
        }
    }

    $ownershipKey = Get-NormalizedOwnershipKey -Type $type -FileName $file.Name
    $ownershipFamily = $pageSpec.ownership_family
    if (-not [string]::IsNullOrWhiteSpace($ownershipKey)) {
        switch ($ownershipFamily) {
            'definition' {
                if (-not $definitionOwnership.ContainsKey($ownershipKey)) {
                    $definitionOwnership[$ownershipKey] = New-Object System.Collections.Generic.List[string]
                }
                $definitionOwnership[$ownershipKey].Add($file.FullName)
            }
            'surface' {
                if (-not $surfaceOwnership.ContainsKey($ownershipKey)) {
                    $surfaceOwnership[$ownershipKey] = New-Object System.Collections.Generic.List[string]
                }
                $surfaceOwnership[$ownershipKey].Add($file.FullName)
            }
        }
    }

    $keywords = Get-DesignVaultRequiredArray -Frontmatter $frontmatter -Name 'keywords'
    if ($status -eq 'active' -and $keywords.Count -eq 0) {
        $warnings.Add("active_page_without_keywords`t$($file.FullName)")
    }

    $playerQuestions = Get-DesignVaultRequiredArray -Frontmatter $frontmatter -Name 'player_questions'
    if ($status -eq 'active' -and ($type -eq 'system' -or $type -eq 'concept' -or $type -eq 'surface') -and $playerQuestions.Count -eq 0) {
        $warnings.Add("active_page_without_player_questions`t$($file.FullName)")
    }

    $lineCount = (Get-Content -LiteralPath $file.FullName | Measure-Object -Line).Lines
    if ($lineCount -gt 180) {
        $warnings.Add("possibly_bloated_page`t$lineCount`t$($file.FullName)")
    }
}

foreach ($entry in $definitionOwnership.GetEnumerator()) {
    if ($entry.Value.Count -gt 1) {
        $issues.Add("duplicate_primary_definition`t$($entry.Value -join ' | ')")
    }
}

foreach ($entry in $surfaceOwnership.GetEnumerator()) {
    if ($entry.Value.Count -gt 1) {
        $issues.Add("duplicate_surface_definition`t$($entry.Value -join ' | ')")
    }
}

foreach ($file in $studioFiles) {
    $parsed = Get-DesignVaultFrontmatter -Path $file.FullName
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)

    if (-not $parsed.HasFrontmatter) {
        $issues.Add("missing_frontmatter`t$($file.FullName)")

        if (Test-DesignVaultPathUnderRoot -Path $file.FullName -Root $longformRoot) {
            $warnings.Add("longform_not_ingested`t$($file.FullName)")
        }

        continue
    }

    foreach ($parseError in $parsed.Errors) {
        $issues.Add("frontmatter_parse_error`t$parseError`t$($file.FullName)")
    }

    $frontmatter = $parsed.Frontmatter
    $type = if ($frontmatter.Contains('type')) { [string]$frontmatter.type } else { $null }
    if ([string]::IsNullOrWhiteSpace($type) -or -not $schema.studio.page_types.ContainsKey($type)) {
        $typeLabel = if ([string]::IsNullOrWhiteSpace($type)) { 'missing' } else { $type }
        $issues.Add("invalid_type`t$typeLabel`t$($file.FullName)")
        continue
    }

    $pageSpec = $schema.studio.page_types[$type]
    Add-FrontmatterValidationIssues -Issues $issues -Frontmatter $frontmatter -Path $file.FullName -PageSpec $pageSpec

    $status = if ($frontmatter.Contains('status')) { [string]$frontmatter.status } else { $null }
    if (-not (Test-AllowedValue -Value $status -AllowedValues $pageSpec.status_values)) {
        $issues.Add("invalid_status`t$status`t$($file.FullName)")
    }

    $updated = if ($frontmatter.Contains('updated')) { [string]$frontmatter.updated } else { $null }
    if (-not [string]::IsNullOrWhiteSpace($updated) -and $updated -notmatch '^\d{4}-\d{2}-\d{2}$') {
        $issues.Add("invalid_updated_date`t$updated`t$($file.FullName)")
    }

    $managedBy = if ($frontmatter.Contains('managed_by')) { [string]$frontmatter.managed_by } else { $null }
    if (-not [string]::IsNullOrWhiteSpace($managedBy) -and -not (Test-AllowedValue -Value $managedBy -AllowedValues $schema.managed_by_values)) {
        $issues.Add("invalid_managed_by`t$managedBy`t$($file.FullName)")
    }

    $priority = if ($frontmatter.Contains('priority')) { [string]$frontmatter.priority } else { $null }
    if (-not [string]::IsNullOrWhiteSpace($priority) -and -not (Test-AllowedValue -Value $priority -AllowedValues $schema.priority_values)) {
        $issues.Add("invalid_priority`t$priority`t$($file.FullName)")
    }

    $ownerRole = if ($frontmatter.Contains('owner_role')) { [string]$frontmatter.owner_role } else { $null }
    if (-not [string]::IsNullOrWhiteSpace($ownerRole) -and -not (Test-AllowedValue -Value $ownerRole -AllowedValues $schema.owner_role_values)) {
        $issues.Add("invalid_owner_role`t$ownerRole`t$($file.FullName)")
    }

    if ($type -eq 'brainstorm') {
        $mode = if ($frontmatter.Contains('mode')) { [string]$frontmatter.mode } else { $null }
        if (-not (Test-AllowedValue -Value $mode -AllowedValues $pageSpec.mode_values)) {
            $issues.Add("invalid_brainstorm_mode`t$mode`t$($file.FullName)")
        }
    }

    if ((Test-DesignVaultPathUnderRoot -Path $file.FullName -Root $longformRoot) -and -not $longformReferenceMap.Contains($stem)) {
        $warnings.Add("longform_not_ingested`t$($file.FullName)")
    }
}

Write-Output "DesignVault lint"
Write-Output ("wiki_files`t{0}" -f $wikiFiles.Count)
Write-Output ("studio_files`t{0}" -f $studioFiles.Count)
Write-Output ("longform_files`t{0}" -f $longformFiles.Count)
Write-Output ("issues`t{0}" -f $issues.Count)
Write-Output ("warnings`t{0}" -f $warnings.Count)

if ($issues.Count -gt 0) {
    Write-Output ''
    Write-Output '[issues]'
    $issues | Sort-Object | ForEach-Object { Write-Output $_ }
}

if ($warnings.Count -gt 0) {
    Write-Output ''
    Write-Output '[warnings]'
    $warnings | Sort-Object | ForEach-Object { Write-Output $_ }
}

if ($FailOnIssues -and $issues.Count -gt 0) {
    exit 1
}
