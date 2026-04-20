# design_ops

This folder contains public helper material for a DesignVault-style repo.

## What lives here

- `obsidian_open.ps1`
  - opens a vault file in Obsidian through the `obsidian://` URL scheme

## Where the main maintenance scripts live

The canonical public maintenance scripts are packaged in:

- `skills/designvault-wiki-maintain/scripts/`

That is where you should run:

- `wiki_lint.ps1`
- `wiki_search.ps1`
- `wiki_status.ps1`
- `wiki_trace.ps1`
- `wiki_suggest_writeback.ps1`
- `change_review_draft.ps1`
- `studio_next.ps1`

## Why this folder exists

The original AgentMarket repo used `tools/design_ops/` as its local operator surface.
This public repo keeps the reusable logic in the skill package instead, but still ships the Obsidian helper and this note so the operating model stays easy to understand.
