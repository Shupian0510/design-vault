# /execute Orchestration Loop

Load this file when the parent thread needs to actually walk an implementation plan end-to-end.

## Parent Thread Authority

The parent thread owns:

- plan selection
- execution-log creation
- preflight
- deciding which phase is next
- deciding whether to stop on a mismatch
- final acceptance
- final human summary

Do not let a phase worker decide plan ordering or acceptance.

## Actual Autopilot Loop

1. Bootstrap the execution log once with `init_execution_log.py --json`, or let `prepare_execute_step.py` create it automatically.
2. Ask `prepare_execute_step.py --include-prompt` what the next action is.
3. If `action == preflight`, first build the local preflight payload with `build_preflight_result.py`, then add real environment or editor findings, then write it back with `update_preflight_section.py`.
4. If `action == phase`, spawn one fresh child:
   - prefer `phase_executor` when available
   - otherwise use built-in `worker`
5. Wait for the child result.
6. If the child returns a stop condition or design mismatch, stop and return a decision packet in-thread.
7. Otherwise normalize the child output with `normalize_execute_result.py`.
8. If the normalized phase result has `should_stop == true`, stop the loop and return the stop reason or decision packet in-thread.
9. Write the normalized child result back with `update_execution_log.py`.
10. Loop back to `prepare_execute_step.py`.
11. If `action == acceptance`, prefer one bounded `acceptance_executor` child when available.
12. Normalize the acceptance output with `normalize_execute_result.py`.
13. Apply the acceptance result with `finalize_execution_log.py`.
14. If `action == complete`, write wiki changes, generate the summary, and stop.

## Runtime Fallback

If custom agents are unavailable:

- phase work: use built-in `worker`
- acceptance: use built-in `default`
- keep the same prompt and stop rules

## Repair Loop

If acceptance returns a real mismatch, do not silently keep coding.
Use `repair-loop.md` and let the user decide whether the next step is a bounded repair or a return to `/design`.
