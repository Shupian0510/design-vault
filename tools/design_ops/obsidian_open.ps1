param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$resolved = Resolve-Path $Path
$escaped = [System.Uri]::EscapeDataString($resolved.Path)
Start-Process "obsidian://open?path=$escaped"
