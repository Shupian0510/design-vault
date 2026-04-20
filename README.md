# DesignVault Skills

A reusable Codex skill pack for running a DesignVault-style workflow:
design in wiki truth, execute from implementation plans, repair bugs from observed symptoms, and keep UI work handoff-friendly.

This repo packages:

- focused skills for `/design`, `/execute`, `/bug`, UI handoff, and vault maintenance
- a starter vault with templates and sample pages
- deterministic `/execute` orchestration scripts
- optional child-agent configs for phase execution and acceptance

Use it when you want DesignVault as a reusable method, not as one project's private notes.

## Skills

- `skills/designvault-design/`
  - focused `/design` lane
- `skills/designvault-execute/`
  - focused `/execute` lane
  - includes deterministic execute orchestration scripts and optional child-agent configs
- `skills/designvault-bug/`
  - focused `/bug` lane
- `skills/designvault-ui-handoff/`
  - UI boundary guidance so implementation stays handoff-friendly
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
- Add `designvault-ui-handoff` if the repo has meaningful UI work and you want a clean implementation-versus-style boundary.
- Add `designvault-wiki-maintain` if you want the starter vault, lint, trace, and writeback scripts.

## Execute Automation

`designvault-execute` now includes:

- `scripts/`
  - execution-log bootstrap
  - phase packet extraction
  - prompt rendering
  - result normalization
  - deterministic parent-thread next-step selection
- `assets/optional-agents/`
  - example `phase_executor` and `acceptance_executor` configs for repos that want the same child-agent boundary model as the internal workflow

These are optional. The skill still works without custom agents by falling back to built-in agent types.

## Execute Script Examples

Example: bootstrap one execution log, build preflight, and ask the parent-thread helper for the next action.

```powershell
# Create the execution log for one plan
python .\skills\designvault-execute\scripts\init_execution_log.py `
  --workspace . `
  --vault-root .\Docs\DesignVault `
  --plan '.\Docs\DesignVault\10 Studio\Execution Plans\计划 - My Task.md' `
  --json

# Build a preflight payload
python .\skills\designvault-execute\scripts\build_preflight_result.py `
  --workspace . `
  --vault-root .\Docs\DesignVault `
  --plan '.\Docs\DesignVault\10 Studio\Execution Plans\计划 - My Task.md' `
  --environment-baseline 'editor ready' `
  --compile-console-baseline 'clean'

# Ask what the next deterministic parent-thread step should be
python .\skills\designvault-execute\scripts\prepare_execute_step.py `
  --workspace . `
  --vault-root .\Docs\DesignVault `
  --plan '.\Docs\DesignVault\10 Studio\Execution Plans\计划 - My Task.md' `
  --include-prompt
```

If you want custom child agents, copy the optional configs from:

- `skills/designvault-execute/assets/optional-agents/phase-executor.toml`
- `skills/designvault-execute/assets/optional-agents/acceptance-executor.toml`

If you do not want custom child agents, keep using the built-in fallback path.

## UI Handoff

Use `designvault-ui-handoff` when:

- the plan needs a clean UI logic versus style split
- the repo will later use Figma or another design pass for polish
- you want to prevent code from hardcoding the final visual presentation
- a UI review needs concrete handoff risks instead of generic design advice

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
