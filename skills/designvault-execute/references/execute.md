# /execute

Use `/execute` when design is already locked and one implementation plan is the main source of truth for the run.

## Default Sequence

1. Read the plan.
2. Run a preflight.
3. Execute phases linearly.
4. Verify each phase with the narrowest valid evidence.
5. Write back changed truth.
6. Finish with one execution log and a compact human summary.

## Preflight Checklist

- linked wiki truth exists
- current implementation scope is understandable
- verification entry points are known
- environment blockers are identified before phase work starts

## Phase Rules

Each phase should make these things clear:

- what changes now
- what does not change yet
- which truth pages to read
- which code or assets matter
- how success is checked
- which pages may need writeback
- which conditions must stop execution and ask the human

## Stop Conditions

Stop and return a short decision packet when:

- the plan and current truth diverge
- the implementation path is unclear enough that the model should not decide alone
- the issue is really a design problem instead of an execution problem
