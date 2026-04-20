---
name: designvault-ui-handoff
description: Plan DesignVault UI implementation boundaries so logic lives in implementation while visual style remains editable for later design polish. Use when Codex needs UI workflow guidance, handoff-ready surface rules, or editability constraints that prevent hardcoding final presentation in code.
---

# DesignVault UI Handoff

Use this skill when the task involves UI architecture, not final art direction.

## Goals

- keep UI logic in implementation
- keep final visual style editable by humans
- make later Figma-driven or design-tool-driven polish practical

## Read Order

1. Read the relevant wiki surface and rule pages first.
2. Read the current implementation plan or implementation boundary notes.
3. Use this skill to decide what belongs in code versus editable assets.

## Rules

- code owns behavior, state, and interaction logic
- final style should not be hardcoded in code
- final style should not depend on runtime-only generation
- prefer prefab, scene, serialized asset, style config, or other editor-visible assets for visual configuration
- wiki should explain UI intent, player-facing behavior, and interaction logic

## Handoff Checks

- which UI behavior belongs in code
- which visual properties should stay editable
- which wiki pages define the surface and its rules
- which assets a later design pass will likely touch
- whether the current implementation would make later polish unnecessarily expensive

## Output Shape

When this skill is used inside planning or review, the useful output is usually:

- code-owned UI responsibilities
- asset-owned or design-owned responsibilities
- handoff risks
- recommended boundary adjustments
