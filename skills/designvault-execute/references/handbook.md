# Handbook

This is the compact operator manual for the public DesignVault workflow.

## One-Line Model

`Longform` shapes design, `Wiki` stores current truth, `Execution Plan` drives implementation.

## Core Lanes

- `/design`
  - read truth, grill for missing decisions, converge into longform plus wiki plus one plan
- `/execute`
  - read one plan, preflight, execute phases, accept, write back truth, record execution history
- `/bug`
  - start from a symptom, read minimum truth, repair implementation, escalate to design only when needed

## Why Phase-by-Phase Writeback

- when a phase changes durable truth, write the wiki back immediately
- when a phase only changes structure or implementation detail, update the log or change review instead
- keep wiki close to reality instead of paying the documentation debt at the very end

## Acceptance

- compare longform, wiki truth, implementation, and tests
- use compile, console, and targeted tests as the default machine gate
- if acceptance reveals a real mismatch, use `decision-packet.md`
- if the user confirms a correction, use `repair-loop.md`

## UI Boundary

- implementation owns behavior, state, and interaction logic
- final visual style should remain editable in assets, prefabs, scenes, or other editor-visible resources
- avoid hardcoding final style in runtime code when later design handoff matters
