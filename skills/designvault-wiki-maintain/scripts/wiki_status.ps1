param(
    [string]$Filter = '',
    [string]$VaultRoot
)

. (Join-Path $PSScriptRoot 'designvault_common.ps1')

$paths = Get-DesignVaultPaths -VaultRoot $VaultRoot -ScriptRoot $PSScriptRoot -StartPath (Get-Location).Path
$schema = Get-DesignVaultSchema -SchemaPath $paths.SchemaPath
$files = Get-DesignVaultWikiTruthFiles -WikiRoot $paths.WikiRoot -Schema $schema -VaultRoot $paths.VaultRoot | Where-Object {
    if ([string]::IsNullOrWhiteSpace($Filter)) { $true } else { $_.Name -like "*$Filter*" }
}

foreach ($file in $files) {
    $parsed = Get-DesignVaultFrontmatter -Path $file.FullName

    if (-not $parsed.HasFrontmatter) {
        Write-Output ("{0}`ttype=missing_frontmatter`tstatus=missing`tupdated=missing" -f $file.FullName)
        continue
    }

    $frontmatter = $parsed.Frontmatter
    $type = if ($frontmatter.Contains('type')) { [string]$frontmatter.type } else { 'missing' }
    $status = if ($frontmatter.Contains('status')) { [string]$frontmatter.status } else { 'missing' }
    $updated = if ($frontmatter.Contains('updated')) { [string]$frontmatter.updated } else { 'missing' }
    Write-Output ("{0}`ttype={1}`tstatus={2}`tupdated={3}" -f $file.FullName, $type, $status, $updated)
}
