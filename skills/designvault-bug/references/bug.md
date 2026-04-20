# /bug

Use `/bug` when the job starts from an observed symptom and the likely scope is a narrow implementation repair.

## Default Sequence

1. Start from the symptom.
2. Read only the minimum wiki truth needed to understand intended behavior.
3. Diagnose the implementation.
4. Reproduce with a test when feasible.
5. Repair the implementation.
6. Verify with the narrowest relevant evidence.
7. Update only the wiki truth that actually changed.

## Escalation Rule

If the issue is really a design ambiguity or design mismatch:

- stop the bug lane
- do not silently redesign
- return a short correction package that can be fed into `/design`
