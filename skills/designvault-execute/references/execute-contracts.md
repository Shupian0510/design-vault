# /execute Contracts

Load this file when you need exact execution-log or handoff structure during `/execute`.
Use `execute-orchestration.md` when you need the parent-thread loop itself.

## Execution Log Minimum Contract

Frontmatter:

- `type: execution_log`
- `status: active | done | archived`
- `updated: YYYY-MM-DD`
- `source_plan: [[10 Studio/Execution Plans/<Plan Name>]]`
- `decision_needed: true | false`
- `decision_summary: ""`
- `playtest_focus: []`
- `risk_items: []`
- `writeback_pages: []`
- `related: []`

Body should at least preserve:

- preflight summary
- per-phase summary
- phase-to-phase handoff
- acceptance result
- final human summary

## Preflight Contract

Before Phase 1, the parent thread should gather and write back:

- `truth_readiness`
- `environment_baseline`
- `compile_console_baseline`
- `test_entry_points`

Use `build_preflight_result.py` to scan:

- missing truth pages
- related wiki resolution
- verification hints already declared in the plan

Use `update_preflight_section.py` to write these into the execution log instead of editing the section by hand.

## Phase Handoff Contract

Each completed phase should leave these fields for the next phase:

- `changed`
- `left_unchanged`
- `tests_run`
- `risks`
- `writeback_pages`
- `design_reasoning`
- `next_phase_watchouts`
- `playtest_focus` optional; use only when a phase creates a specific human-facing check later

## Phase Packet Contract

Before spawning a `phase_executor`, the parent thread should prepare a bounded phase packet.

Minimum fields:

- `plan_title`
- `phase_number`
- `phase_title`
- `goal`
- `non_goals`
- `dependencies`
- `required_wiki`
- `required_context`
- `scope`
- `implementation_notes`
- `success_criteria`
- `verification`
- `writeback_targets`
- `stop_conditions`

Prefer structured extraction from the plan instead of restating the whole plan by hand.

## Preferred Subagent

If optional custom agents are enabled, `/execute` can prefer:

- `phase_executor`
- `acceptance_executor`

Public example configs live under `assets/optional-agents/`.

## Fallback Subagent

If the live session cannot resolve those custom agents, fall back to:

- phase work: built-in `worker`
- acceptance: built-in `default`
- recommended model: `gpt-5.4`
- recommended reasoning: `high`

## Decision Packet Contract

See `decision-packet.md`.

## Acceptance Contract

Acceptance should compare:

- longform
- wiki truth
- final implementation
- test results

Default machine checks:

- compile
- console
- targeted tests appropriate to the repo

If acceptance fails because of design mismatch, stop with a decision packet instead of silently repairing the design.

Expected acceptance result fields:

- `acceptance_status`
- `machine_checks`
- `acceptance_summary`
- `playtest_focus`
- `risks`
- `updated_pages`
- `decision_packet_needed`
- `decision_packet`
