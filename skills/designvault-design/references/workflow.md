# Workflow

## Purpose

Use DesignVault to separate stable truth from active working material.

- `00 Wiki/` stores current approved truth.
- `10 Studio/` stores drafts, plans, execution logs, change review, and other working artifacts.

## Recommended Lanes

- `/design`
  - use when the design is not stable enough to implement
- `/execute`
  - use when one implementation plan is already approved and the job is execution
- `/bug`
  - use when the starting point is an observed symptom and the likely scope is narrow

## Core Rules

- Start by reading the smallest relevant wiki pages.
- End by updating the wiki only if durable truth changed.
- Keep unstable debate in studio pages instead of wiki pages.
- Keep execution status in execution logs and change review, not in wiki truth fields.
- Prefer one main execution plan page. Split phase pages only when handoff cost justifies them.

## Artifact Roles

- `longform`
  - shape the idea and preserve tradeoffs while the design is still unstable
- `wiki truth`
  - define the current stable player-facing or system-facing truth
- `execution plan`
  - define implementation order, scope, validation, writeback targets, and stop conditions
- `execution log`
  - record preflight, phase handoff, acceptance, and follow-up playtest focus
- `change review`
  - explain implementation deltas, risks, and likely writeback work

## Typical Flow

`/design -> /execute -> human feedback when needed -> /bug`
