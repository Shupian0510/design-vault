---
name: designvault-bug
description: Run the DesignVault `/bug` lane for narrow implementation issues found during playtest, QA, or observation. Use when Codex needs to start from a reported symptom, read only the minimum wiki truth needed, diagnose the implementation, repair it, verify the fix, and escalate to `/design` only if the root cause is really design truth.
---

# DesignVault Bug

Use this skill when the starting point is a symptom, not a new feature plan. The goal is to repair implementation with the least possible workflow overhead.

## Read Order

1. Read `references/workflow.md`.
2. Read `references/bug.md`.
3. Read the smallest relevant wiki pages before reading code.
4. If the bug is likely to stop on a design ambiguity, also read `../designvault-execute/references/decision-packet.md`.

## Default Flow

1. Start from the symptom.
2. Diagnose with the minimum necessary context.
3. Reproduce with a test when feasible.
4. Repair the implementation.
5. Verify with the narrowest relevant evidence.
6. Update only the truth that actually changed.

## Guardrails

- Do not silently redesign.
- Do not expand a narrow bug into a full execute run unless the user redirects it.
- If the problem is actually design ambiguity, stop and hand back a short correction package for `/design`.
