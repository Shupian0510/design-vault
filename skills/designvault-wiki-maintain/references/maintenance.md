# Maintenance

Use maintenance-only work to keep the vault searchable, lintable, and easy to write back into.

## Common Commands

```powershell
pwsh -File .\wiki_lint.ps1 -VaultRoot <vault-root>
pwsh -File .\wiki_search.ps1 -VaultRoot <vault-root> -Query "keyword"
pwsh -File .\wiki_trace.ps1 -VaultRoot <vault-root> -ChangedPath src\feature.cs
pwsh -File .\wiki_suggest_writeback.ps1 -VaultRoot <vault-root> -SourcePath ".\10 Studio\Execution Plans\计划 - Example.md"
pwsh -File .\change_review_draft.ps1 -VaultRoot <vault-root> -Title "Change Review - Example" -SourcePath ".\10 Studio\Execution Plans\计划 - Example.md"
```

## Intended Outcomes

- find relevant wiki truth quickly
- detect schema and linkage problems
- map changed files back to likely truth pages
- draft conservative writeback suggestions
- draft a change review page instead of hand-writing the whole first pass
