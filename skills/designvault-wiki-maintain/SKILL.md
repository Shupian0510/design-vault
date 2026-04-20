---
name: designvault-wiki-maintain
description: Maintain DesignVault health and writeback quality. Use when Codex needs to scaffold a starter vault, search current truth, lint vault structure, trace changed files back to wiki pages, generate conservative writeback suggestions, draft change-review pages, or perform maintenance-only cleanup on a DesignVault repo.
---

# DesignVault Wiki Maintain

Use this skill for maintenance-only tasks and for bootstrapping a repo with the public starter vault.

## Read Order

1. Read `references/workflow.md`.
2. Read `references/maintenance.md`.
3. Read `references/starter-vault.md` when setting up a new vault or explaining the packaged template.

## Assets

- `assets/starter-vault/`
  - copy this into a repo to bootstrap a reusable DesignVault layout

## Scripts

All scripts accept `-VaultRoot`.

- `scripts/wiki_search.ps1`
- `scripts/wiki_status.ps1`
- `scripts/wiki_lint.ps1`
- `scripts/wiki_trace.ps1`
- `scripts/wiki_suggest_writeback.ps1`
- `scripts/change_review_draft.ps1`
- `scripts/studio_next.ps1`

## Guardrails

- Prefer targeted fixes over broad rewrites.
- Keep wiki pages optimized for retrieval and stable truth.
- Keep execution state in execution logs and change review instead of reintroducing page-level implementation flags.
