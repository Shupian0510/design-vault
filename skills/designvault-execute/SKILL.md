---
name: designvault-execute
description: Run the DesignVault `/execute` lane from one approved implementation plan. Use when Codex needs to read a plan, run preflight, execute phases in order, verify results with the narrowest valid evidence, write back changed wiki truth, and finish with one execution log.
---

# DesignVault Execute

Use this skill when design is already locked and the job is execution. The plan is the execution map; wiki pages remain the truth source.

## Read Order

1. Read `references/workflow.md`.
2. Read `references/execute.md`.
3. Read `references/execute-contracts.md` and `references/execute-orchestration.md` when the task is a real end-to-end `/execute` run instead of a lightweight explanation.
4. Read `references/decision-packet.md`, `references/repair-loop.md`, and `references/handbook.md` when acceptance, stop conditions, or public operator guidance matter.
5. Read the owning execution plan.
6. Read only the wiki and implementation context named by the current phase.

## Default Flow

1. Run preflight.
2. Execute phases linearly.
3. Verify each phase with the narrowest valid evidence.
4. Write back changed truth.
5. Finish with one execution log and a compact human summary.

## Optional Assets

- `scripts/`
  - deterministic `/execute` orchestration helpers, log writers, prompt renderers, and result normalizers
- `assets/optional-agents/`
  - example `phase_executor` and `acceptance_executor` configs you can adopt or adapt per repo

## Guardrails

- Do not re-design silently inside execution.
- Do not widen scope beyond the plan without making that explicit.
- Stop with a short decision packet when the plan and truth diverge or the model should not decide alone.
