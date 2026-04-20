param(
    [string]$Title,
    [string[]]$ChangedPath,
    [string[]]$SourcePath,
    [string]$Since = 'HEAD',
    [switch]$WriteFile,
    [string]$OutputPath,
    [string]$VaultRoot
)

. (Join-Path $PSScriptRoot 'designvault_common.ps1')

$paths = Get-DesignVaultPaths -VaultRoot $VaultRoot -ScriptRoot $PSScriptRoot -StartPath (Get-Location).Path

function Convert-ToWikiLink {
    param(
        [string]$Path,
        [string]$VaultRootPath
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }

    $resolved = [string](Resolve-Path -LiteralPath $Path)
    $relative = $resolved.Substring($VaultRootPath.Length + 1).Replace('\', '/')
    $withoutExtension = [System.IO.Path]::ChangeExtension($relative, $null).TrimEnd('.')
    return ('[[{0}]]' -f $withoutExtension)
}

function New-SafeLeafName {
    param(
        [string]$Value
    )

    $fallback = 'Change Review - ' + (Get-Date -Format 'yyyy-MM-dd HHmm')
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $fallback
    }

    $invalidChars = [System.IO.Path]::GetInvalidFileNameChars()
    $safe = $Value
    foreach ($char in $invalidChars) {
        $safe = $safe.Replace([string]$char, ' ')
    }

    $safe = ($safe -replace '\s+', ' ').Trim()
    if ([string]::IsNullOrWhiteSpace($safe)) {
        return $fallback
    }

    return $safe
}

$writebackScript = Join-Path $PSScriptRoot 'wiki_suggest_writeback.ps1'
$writebackJson = if ($ChangedPath -and $SourcePath) {
    & $writebackScript -ChangedPath $ChangedPath -SourcePath $SourcePath -Since $Since -AsJson -VaultRoot $paths.VaultRoot
}
elseif ($ChangedPath) {
    & $writebackScript -ChangedPath $ChangedPath -Since $Since -AsJson -VaultRoot $paths.VaultRoot
}
elseif ($SourcePath) {
    & $writebackScript -SourcePath $SourcePath -Since $Since -AsJson -VaultRoot $paths.VaultRoot
}
else {
    & $writebackScript -Since $Since -AsJson -VaultRoot $paths.VaultRoot
}

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace([string]$writebackJson)) {
    throw 'Failed to generate DesignVault writeback suggestions.'
}

$writeback = $writebackJson | ConvertFrom-Json -ErrorAction Stop
$resolvedTitle = New-SafeLeafName -Value $Title
$dateStamp = Get-Date -Format 'yyyy-MM-dd'
$wikiLinks = @(
    $writeback.suggestions |
        ForEach-Object { Convert-ToWikiLink -Path $_.wiki_path -VaultRootPath $paths.VaultRoot } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Sort-Object -Unique
)
$codeRefs = @(
    $writeback.changed_paths |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Sort-Object -Unique
)

$changeSummaryLines = New-Object System.Collections.Generic.List[string]
if ($writeback.source_paths.Count -gt 0) {
    $changeSummaryLines.Add('- 来源任务：')
    foreach ($source in $writeback.source_paths) {
        $changeSummaryLines.Add(('  - `{0}`' -f $source))
    }
}

if ($writeback.changed_paths.Count -gt 0) {
    $changeSummaryLines.Add('- 改动文件：')
    foreach ($changed in $writeback.changed_paths) {
        $changeSummaryLines.Add(('  - `{0}`' -f $changed))
    }
}

if ($changeSummaryLines.Count -eq 0) {
    $changeSummaryLines.Add('- 待补充本次改动范围')
}

$affectedPageLines = New-Object System.Collections.Generic.List[string]
foreach ($suggestion in @($writeback.suggestions | Where-Object { $null -ne $_ })) {
    $wikiLink = Convert-ToWikiLink -Path $suggestion.wiki_path -VaultRootPath $paths.VaultRoot
    $affectedPageLines.Add(('- {0}' -f $wikiLink))
    $affectedPageLines.Add(('  - 原因：{0}' -f ($suggestion.reasons -join ' / ')))
    if ($suggestion.suggested_code_refs.Count -gt 0) {
        $affectedPageLines.Add(('  - 建议补充 code_refs：`{0}`' -f (($suggestion.suggested_code_refs | Sort-Object -Unique) -join '`, `')))
    }
    $affectedPageLines.Add(('  - 回写建议：{0}' -f $suggestion.writeback_guidance))
}

if ($affectedPageLines.Count -eq 0) {
    $affectedPageLines.Add('- 待确认受影响的 wiki 页面')
}

$followUpLines = New-Object System.Collections.Generic.List[string]
foreach ($suggestion in @($writeback.suggestions | Where-Object { $null -ne $_ })) {
    if (-not [string]::IsNullOrWhiteSpace([string]$suggestion.human_review_note)) {
        $wikiLink = Convert-ToWikiLink -Path $suggestion.wiki_path -VaultRootPath $paths.VaultRoot
        $followUpLines.Add(('- {0}: {1}' -f $wikiLink, $suggestion.human_review_note))
    }
}

if ($followUpLines.Count -eq 0) {
    $followUpLines.Add('- 根据本次实现补充截图、测试说明或试玩关注点')
}

$content = @(
    '---'
    'type: change_review'
    'status: open'
    ('updated: {0}' -f $dateStamp)
    'managed_by: ai'
    $(if ($wikiLinks.Count -gt 0) {
            'links:'
            foreach ($wikiLink in $wikiLinks) { '  - ' + $wikiLink }
        }
        else {
            'links: []'
        })
    $(if ($codeRefs.Count -gt 0) {
            'code_refs:'
            foreach ($codeRef in $codeRefs) { '  - ' + $codeRef }
        }
        else {
            'code_refs: []'
        })
    'figma_refs: []'
    '---'
    ''
    ('# {0}' -f $resolvedTitle)
    ''
    '## 本次改动'
    $changeSummaryLines
    ''
    '## 影响到的 wiki 页面'
    $affectedPageLines
    ''
    '## 验收方式'
    '- 编译检查'
    '- 定向测试或运行验证'
    '- 需要时补截图或录屏'
    ''
    '## 机器证据'
    '- 待补充 compile / console / tests / screenshot 结果'
    ''
    '## 试玩关注点'
    '- 待补充需要人类重点看的功能点与风险'
    ''
    '## 后续问题 / 待决策'
    $followUpLines
    ''
) -join "`n"

if ($WriteFile) {
    $destination = if ([string]::IsNullOrWhiteSpace($OutputPath)) {
        Join-Path $paths.StudioRoot ('Change Review\{0}.md' -f $resolvedTitle)
    }
    else {
        $OutputPath
    }

    $destinationDirectory = Split-Path -Parent $destination
    if (-not (Test-Path -LiteralPath $destinationDirectory)) {
        New-Item -ItemType Directory -Path $destinationDirectory | Out-Null
    }

    Set-Content -LiteralPath $destination -Value $content -Encoding UTF8
    Write-Output $destination
    exit 0
}

Write-Output $content
