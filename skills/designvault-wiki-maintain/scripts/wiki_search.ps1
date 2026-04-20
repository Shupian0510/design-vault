param(
    [Parameter(Mandatory = $true)]
    [string]$Query,
    [string]$VaultRoot
)

. (Join-Path $PSScriptRoot 'designvault_common.ps1')

$paths = Get-DesignVaultPaths -VaultRoot $VaultRoot -ScriptRoot $PSScriptRoot -StartPath (Get-Location).Path

if (Get-Command rg -ErrorAction SilentlyContinue) {
    & rg -n --glob "*.md" $Query $paths.WikiRoot
    exit $LASTEXITCODE
}

Get-ChildItem -LiteralPath $paths.WikiRoot -Recurse -Filter *.md |
    Select-String -Pattern $Query
