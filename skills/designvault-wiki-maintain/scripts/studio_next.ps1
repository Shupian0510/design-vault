param(
    [string]$VaultRoot
)

. (Join-Path $PSScriptRoot 'designvault_common.ps1')

$paths = Get-DesignVaultPaths -VaultRoot $VaultRoot -ScriptRoot $PSScriptRoot -StartPath (Get-Location).Path
$schema = Get-DesignVaultSchema -SchemaPath $paths.SchemaPath
$targets = @(
    'Todo - Design',
    'Todo - Programming',
    'Todo - Art',
    'Idea List'
)

$trackedFiles = Get-DesignVaultTrackedStudioFiles -VaultRoot $paths.VaultRoot -Schema $schema

foreach ($target in $targets) {
    $targetRoot = Join-DesignVaultPath -BasePath $paths.StudioRoot -RelativePath $target
    $count = @(
        $trackedFiles |
            Where-Object {
                Test-DesignVaultPathUnderRoot -Path $_.FullName -Root $targetRoot
            }
    ).Count

    Write-Output ("{0}`t{1}" -f $target, $count)
}
