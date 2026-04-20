# DesignVault Skills

Reusable Codex skill plus starter vault for teams that want a maintained design wiki, a working studio area, and lightweight scripts for search, lint, and writeback support.

## Skills

- `skills/designvault-design/`
  - focused `/design` lane
- `skills/designvault-execute/`
  - focused `/execute` lane
- `skills/designvault-bug/`
  - focused `/bug` lane
- `skills/designvault-wiki-maintain/`
  - starter-vault packaging plus maintenance scripts

## What This Repo Does Not Ship

- private current-truth pages from AgentMarket
- project-specific execution automation that depends on local subagents, local Unity setup, or hidden repo conventions
- user-state Obsidian workspace settings

## Install

Clone or copy this repo anywhere you like. Then either:

1. Use the skills in place from this repo.
2. Copy the `skills/` subfolders you want into your Codex skills directory.

Typical Codex local install target:

```text
$CODEX_HOME/skills
```

If `CODEX_HOME` is unset, use:

```text
~/.codex/skills
```

Minimal install options:

- Use only `designvault-design`, `designvault-execute`, and `designvault-bug` if your repo already has a vault and you do not need the packaged scripts.
- Add `designvault-wiki-maintain` if you want the starter vault, lint, trace, and writeback scripts.

## Starter Vault

1. Copy `skills/designvault-wiki-maintain/assets/starter-vault/` into the destination repo.
2. Keep that copied folder as your vault root, or set `DESIGNVAULT_ROOT` to its location.
3. Use the split skills directly:
   `designvault-design`, `designvault-execute`, `designvault-bug`, `designvault-wiki-maintain`
4. Run maintenance scripts from `skills/designvault-wiki-maintain/scripts/` with `-VaultRoot <path>`.

Example:

```powershell
pwsh -File .\skills\designvault-wiki-maintain\scripts\wiki_lint.ps1 -VaultRoot .\Docs\DesignVault
pwsh -File .\skills\designvault-wiki-maintain\scripts\wiki_search.ps1 -VaultRoot .\Docs\DesignVault -Query "HUD"
pwsh -File .\skills\designvault-wiki-maintain\scripts\wiki_suggest_writeback.ps1 -VaultRoot .\Docs\DesignVault -SourcePath ".\Docs\DesignVault\10 Studio\Execution Plans\样例 - 示例功能计划.md"
```

## From Zero

Example: start from a fresh local repo and run the first lint.

```powershell
# 1. Create a new repo
mkdir my-game
cd my-game
git init -b main

# 2. Copy the skills you want into Codex local skills
#    Example target: $env:USERPROFILE\.codex\skills
Copy-Item -Recurse -Force <path-to-designvault-skills>\skills\designvault-design $env:USERPROFILE\.codex\skills\
Copy-Item -Recurse -Force <path-to-designvault-skills>\skills\designvault-execute $env:USERPROFILE\.codex\skills\
Copy-Item -Recurse -Force <path-to-designvault-skills>\skills\designvault-bug $env:USERPROFILE\.codex\skills\
Copy-Item -Recurse -Force <path-to-designvault-skills>\skills\designvault-wiki-maintain $env:USERPROFILE\.codex\skills\

# 3. Copy the starter vault into the repo
Copy-Item -Recurse -Force <path-to-designvault-skills>\skills\designvault-wiki-maintain\assets\starter-vault .\Docs\DesignVault

# 4. Run the first lint
pwsh -File $env:USERPROFILE\.codex\skills\designvault-wiki-maintain\scripts\wiki_lint.ps1 -VaultRoot .\Docs\DesignVault
```

Expected result for the packaged starter vault:

- `issues 0`
- `warnings 0`

After that, the normal next steps are:

1. Replace the sample truth pages with your own project truth.
2. Use `designvault-design` to shape the first real task into a plan.
3. Use `designvault-execute` or `designvault-bug` once the repo has real work to run.

## Public Standard

The packaged default assumes:

- `00 Wiki/` is current truth
- `10 Studio/` is the working area
- recommended operator lanes are `/design`, `/execute`, and `/bug`
- execution state lives in execution logs, change review, and dashboards instead of page-level implementation flags

You can rename or extend the structure, but the shipped scripts and starter vault assume that baseline.

## Release Prep

Before publishing to GitHub, verify these points:

1. All four skills pass `quick_validate.py`.
2. `designvault-wiki-maintain/scripts/wiki_lint.ps1` passes against the packaged starter vault.
3. No private truth pages, local workspace state, API keys, or project-specific automation remain.
4. Example content is clearly sample content, not live project state.
5. README install paths and script examples still match the current repo layout.

This repo is currently prepared around those checks.

## License

MIT
