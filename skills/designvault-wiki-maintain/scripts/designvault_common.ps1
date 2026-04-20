function Join-DesignVaultPath {
    param(
        [Parameter(Mandatory)]
        [string]$BasePath,
        [Parameter(Mandatory)]
        [string]$RelativePath
    )

    $current = $BasePath
    foreach ($segment in ($RelativePath -split '[\\/]')) {
        if ([string]::IsNullOrWhiteSpace($segment)) {
            continue
        }

        $current = Join-Path $current $segment
    }

    return $current
}

function Test-DesignVaultRootCandidate {
    param(
        [AllowNull()]
        [string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    $resolved = [string](Resolve-Path -LiteralPath $Path)
    return (
        (Test-Path -LiteralPath (Join-Path $resolved 'index.md')) -and
        (Test-Path -LiteralPath (Join-Path $resolved '00 Wiki')) -and
        (Test-Path -LiteralPath (Join-Path $resolved '10 Studio'))
    )
}

function Resolve-DesignVaultRoot {
    param(
        [string]$VaultRoot,
        [string]$StartPath = (Get-Location).Path
    )

    if (-not [string]::IsNullOrWhiteSpace($VaultRoot)) {
        if (Test-DesignVaultRootCandidate -Path $VaultRoot) {
            return [string](Resolve-Path -LiteralPath $VaultRoot)
        }

        throw "Vault root not found or invalid: $VaultRoot"
    }

    if (-not [string]::IsNullOrWhiteSpace($env:DESIGNVAULT_ROOT)) {
        if (Test-DesignVaultRootCandidate -Path $env:DESIGNVAULT_ROOT) {
            return [string](Resolve-Path -LiteralPath $env:DESIGNVAULT_ROOT)
        }
    }

    $current = [System.IO.DirectoryInfo](Resolve-Path -LiteralPath $StartPath)
    while ($null -ne $current) {
        foreach ($candidate in @(
                $current.FullName,
                (Join-Path $current.FullName 'Docs\DesignVault'),
                (Join-Path $current.FullName 'DesignVault')
            )) {
            if (Test-DesignVaultRootCandidate -Path $candidate) {
                return [string](Resolve-Path -LiteralPath $candidate)
            }
        }

        $current = $current.Parent
    }

    throw 'Could not detect a DesignVault root. Pass -VaultRoot explicitly or set DESIGNVAULT_ROOT.'
}

function Get-DesignVaultPaths {
    param(
        [string]$VaultRoot,
        [string]$ScriptRoot = $PSScriptRoot,
        [string]$StartPath = (Get-Location).Path
    )

    $resolvedVaultRoot = Resolve-DesignVaultRoot -VaultRoot $VaultRoot -StartPath $StartPath
    $wikiRoot = Resolve-Path (Join-Path $resolvedVaultRoot '00 Wiki')
    $studioRoot = Resolve-Path (Join-Path $resolvedVaultRoot '10 Studio')
    $schemaPath = Resolve-Path (Join-Path $ScriptRoot 'designvault_schema.json')

    return [pscustomobject]@{
        VaultRoot = [string]$resolvedVaultRoot
        WikiRoot = [string]$wikiRoot
        StudioRoot = [string]$studioRoot
        SchemaPath = [string]$schemaPath
    }
}

function Get-DesignVaultRepositoryRoot {
    param(
        [string]$StartPath = (Get-Location).Path
    )

    $resolvedStart = [string](Resolve-Path -LiteralPath $StartPath)
    $repoRoot = $null

    try {
        $repoRoot = (& git -C $resolvedStart rev-parse --show-toplevel 2>$null)
    }
    catch {
        $repoRoot = $null
    }

    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace([string]$repoRoot)) {
        return ([string]$repoRoot).Trim()
    }

    return $resolvedStart
}

function ConvertTo-DesignVaultHashtable {
    param(
        [AllowNull()]
        [object]$Value
    )

    if ($null -eq $Value) {
        return $null
    }

    if ($Value -is [System.Collections.IDictionary]) {
        $table = @{}
        foreach ($key in $Value.Keys) {
            $table[$key] = ConvertTo-DesignVaultHashtable -Value $Value[$key]
        }
        return $table
    }

    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $table = @{}
        foreach ($property in $Value.PSObject.Properties) {
            $table[$property.Name] = ConvertTo-DesignVaultHashtable -Value $property.Value
        }
        return $table
    }

    if ($Value -is [System.Array]) {
        return @(
            foreach ($item in $Value) {
                ConvertTo-DesignVaultHashtable -Value $item
            }
        )
    }

    return $Value
}

function Test-DesignVaultPathUnderRoot {
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [string]$Root
    )

    if (-not (Test-Path -LiteralPath $Path) -or -not (Test-Path -LiteralPath $Root)) {
        return $false
    }

    $resolvedPath = [string](Resolve-Path -LiteralPath $Path)
    $resolvedRoot = ([string](Resolve-Path -LiteralPath $Root)).TrimEnd('\', '/')
    return $resolvedPath.StartsWith(($resolvedRoot + [System.IO.Path]::DirectorySeparatorChar), [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-DesignVaultSchema {
    param(
        [string]$SchemaPath
    )

    $resolvedPath = if ([string]::IsNullOrWhiteSpace($SchemaPath)) {
        (Get-DesignVaultPaths).SchemaPath
    }
    else {
        [string](Resolve-Path $SchemaPath)
    }

    $schemaObject = Get-Content -LiteralPath $resolvedPath -Raw | ConvertFrom-Json
    return ConvertTo-DesignVaultHashtable -Value $schemaObject
}

function Convert-DesignVaultScalarValue {
    param(
        [AllowNull()]
        [string]$Value
    )

    if ($null -eq $Value) {
        return $null
    }

    $trimmed = $Value.Trim()
    if ($trimmed -eq '[]') {
        return , @()
    }

    if ($trimmed -match '^\[(?<items>.*)\]$') {
        $items = ([string]$Matches.items).Trim()
        if ([string]::IsNullOrWhiteSpace($items)) {
            return , @()
        }

        return , @(
            $items.Split(',') |
                ForEach-Object { Convert-DesignVaultScalarValue -Value $_ } |
                Where-Object { $null -ne $_ }
        )
    }

    if (
        ($trimmed.StartsWith('"') -and $trimmed.EndsWith('"')) -or
        ($trimmed.StartsWith("'") -and $trimmed.EndsWith("'"))
    ) {
        return $trimmed.Substring(1, $trimmed.Length - 2)
    }

    return $trimmed
}

function Get-DesignVaultFrontmatter {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    $content = Get-Content -LiteralPath $Path -Raw
    $normalized = $content -replace "`r`n", "`n"
    $result = [ordered]@{
        Path = $Path
        Content = $content
        Body = $normalized
        HasFrontmatter = $false
        Frontmatter = [ordered]@{}
        Errors = New-Object System.Collections.Generic.List[string]
    }

    if (-not $normalized.StartsWith("---`n")) {
        return [pscustomobject]$result
    }

    $closingIndex = $normalized.IndexOf("`n---`n", 4)
    if ($closingIndex -lt 0) {
        $result.Errors.Add('unterminated_frontmatter')
        return [pscustomobject]$result
    }

    $frontmatterBlock = $normalized.Substring(4, $closingIndex - 4)
    $result.Body = $normalized.Substring($closingIndex + 5)
    $result.HasFrontmatter = $true

    $frontmatter = [ordered]@{}
    $currentKey = $null

    foreach ($rawLine in ($frontmatterBlock -split "`n")) {
        $line = $rawLine.TrimEnd()

        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        if ($line -match '^(?<key>[A-Za-z0-9_]+):\s*(?<value>.*)$') {
            $currentKey = [string]$Matches.key
            $value = [string]$Matches.value

            if ([string]::IsNullOrWhiteSpace($value)) {
                $frontmatter[$currentKey] = @()
            }
            else {
                $frontmatter[$currentKey] = Convert-DesignVaultScalarValue -Value $value
                if ($frontmatter[$currentKey] -is [System.Array]) {
                    $currentKey = $null
                }
            }

            continue
        }

        if ($line -match '^\s*-\s*(?<value>.*)$') {
            if ([string]::IsNullOrWhiteSpace($currentKey)) {
                $result.Errors.Add("orphan_list_item::$line")
                continue
            }

            if (-not ($frontmatter[$currentKey] -is [System.Array])) {
                $frontmatter[$currentKey] = @()
            }

            $frontmatter[$currentKey] += Convert-DesignVaultScalarValue -Value ([string]$Matches.value)
            continue
        }

        $result.Errors.Add("unparsed_frontmatter_line::$line")
    }

    $result.Frontmatter = $frontmatter
    return [pscustomobject]$result
}

function Convert-DesignVaultToRepoRelativePath {
    param(
        [AllowNull()]
        [string]$Path,
        [string]$RepoRoot = (Get-DesignVaultRepositoryRoot)
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }

    $trimmedPath = $Path.Trim()
    $normalizedRepoRoot = [string](Resolve-Path -LiteralPath $RepoRoot)
    $comparisonPath = $trimmedPath

    if (Test-Path -LiteralPath $trimmedPath) {
        $comparisonPath = [string](Resolve-Path -LiteralPath $trimmedPath)
    }

    if ($comparisonPath.StartsWith($normalizedRepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        $relative = $comparisonPath.Substring($normalizedRepoRoot.Length).TrimStart('\', '/')
        return $relative.Replace('\', '/')
    }

    return $trimmedPath.Replace('\', '/')
}

function Get-DesignVaultCodeRefPath {
    param(
        [AllowNull()]
        [object]$CodeRef,
        [string]$RepoRoot = (Get-DesignVaultRepositoryRoot)
    )

    if ($null -eq $CodeRef) {
        return $null
    }

    $text = [string]$CodeRef
    if ([string]::IsNullOrWhiteSpace($text)) {
        return $null
    }

    $candidate = $text.Trim()
    if (
        ($candidate.StartsWith('"') -and $candidate.EndsWith('"')) -or
        ($candidate.StartsWith("'") -and $candidate.EndsWith("'"))
    ) {
        $candidate = $candidate.Substring(1, $candidate.Length - 2)
    }

    $candidate = $candidate -replace ':[0-9]+$', ''
    $candidate = $candidate -replace '#.+$', ''
    $candidate = $candidate.Trim()

    if ([string]::IsNullOrWhiteSpace($candidate)) {
        return $null
    }

    return Convert-DesignVaultToRepoRelativePath -Path $candidate -RepoRoot $RepoRoot
}

function Get-DesignVaultWikiLinkLeaf {
    param(
        [AllowNull()]
        [object]$Value
    )

    if ($null -eq $Value) {
        return $null
    }

    $text = [string]$Value
    if ($text -match '\[\[(?<target>[^\]|#]+)') {
        $target = ([string]$Matches.target).Trim()
    }
    else {
        $target = $text.Trim()
    }

    if ([string]::IsNullOrWhiteSpace($target)) {
        return $null
    }

    $leaf = Split-Path $target -Leaf
    if ([string]::IsNullOrWhiteSpace($leaf)) {
        return $null
    }

    return [System.IO.Path]::GetFileNameWithoutExtension($leaf)
}

function Get-DesignVaultWikiLinks {
    param(
        [AllowNull()]
        [string]$Content
    )

    if ([string]::IsNullOrWhiteSpace($Content)) {
        return @()
    }

    $matches = [regex]::Matches($Content, '\[\[(?<target>[^\]|#]+)')
    return @(
        foreach ($match in $matches) {
            $target = $match.Groups['target'].Value.Trim()
            if ([string]::IsNullOrWhiteSpace($target)) {
                continue
            }

            $leaf = Split-Path $target -Leaf
            if (-not [string]::IsNullOrWhiteSpace($leaf)) {
                [System.IO.Path]::GetFileNameWithoutExtension($leaf)
            }
        }
    )
}

function Test-DesignVaultStructuralWikiPage {
    param(
        [Parameter(Mandatory)]
        [System.IO.FileInfo]$File,
        [Parameter(Mandatory)]
        [hashtable]$Schema,
        [Parameter(Mandatory)]
        [string]$VaultRoot
    )

    $relativePath = $File.FullName.Substring($VaultRoot.Length + 1).Replace('\', '/')
    foreach ($pattern in $Schema.wiki.structural_paths) {
        if ($pattern.EndsWith('/')) {
            if ($relativePath.StartsWith($pattern, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
        }
        elseif ($relativePath.Equals($pattern, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    return $false
}

function Get-DesignVaultWikiTruthFiles {
    param(
        [Parameter(Mandatory)]
        [string]$WikiRoot,
        [Parameter(Mandatory)]
        [hashtable]$Schema,
        [Parameter(Mandatory)]
        [string]$VaultRoot
    )

    return @(
        Get-ChildItem -LiteralPath $WikiRoot -Recurse -Filter *.md |
            Where-Object { -not (Test-DesignVaultStructuralWikiPage -File $_ -Schema $Schema -VaultRoot $VaultRoot) }
    )
}

function Get-DesignVaultWikiTruthRecords {
    param(
        [Parameter(Mandatory)]
        [string]$WikiRoot,
        [Parameter(Mandatory)]
        [hashtable]$Schema,
        [Parameter(Mandatory)]
        [string]$VaultRoot
    )

    return @(
        foreach ($file in (Get-DesignVaultWikiTruthFiles -WikiRoot $WikiRoot -Schema $Schema -VaultRoot $VaultRoot)) {
            $parsed = Get-DesignVaultFrontmatter -Path $file.FullName
            $frontmatter = $parsed.Frontmatter
            $type = if ($frontmatter.Contains('type')) { [string]$frontmatter.type } else { $null }

            [pscustomobject]@{
                File = $file
                Path = $file.FullName
                Stem = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
                Parsed = $parsed
                Frontmatter = $frontmatter
                Type = $type
            }
        }
    )
}

function Get-DesignVaultTrackedStudioFiles {
    param(
        [Parameter(Mandatory)]
        [string]$VaultRoot,
        [Parameter(Mandatory)]
        [hashtable]$Schema
    )

    $files = New-Object System.Collections.Generic.List[System.IO.FileInfo]

    foreach ($relativeRoot in $Schema.studio.tracked_roots) {
        $absoluteRoot = Join-DesignVaultPath -BasePath $VaultRoot -RelativePath $relativeRoot
        if (-not (Test-Path -LiteralPath $absoluteRoot)) {
            continue
        }

        foreach ($file in (Get-ChildItem -LiteralPath $absoluteRoot -Recurse -Filter *.md)) {
            if ($Schema.studio.ignored_filenames -contains $file.Name) {
                continue
            }

            $ignoredPrefix = $false
            foreach ($prefix in $Schema.studio.ignored_prefixes) {
                if ($file.BaseName.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $ignoredPrefix = $true
                    break
                }
            }

            if (-not $ignoredPrefix) {
                $files.Add($file)
            }
        }
    }

    return @($files)
}

function Get-DesignVaultRequiredArray {
    param(
        [Parameter(Mandatory)]
        [hashtable]$Frontmatter,
        [Parameter(Mandatory)]
        [string]$Name
    )

    if (-not $Frontmatter.Contains($Name)) {
        return , @()
    }

    $value = $Frontmatter[$Name]
    if ($value -is [System.Array]) {
        return , @($value)
    }

    if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
        return , @()
    }

    return , @([string]$value)
}
