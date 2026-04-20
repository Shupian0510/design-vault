# Decision Packet

Use a `decision packet` when `/execute` or `/bug` must stop and hand a real choice back to the user.

## Use It When

- plan and wiki truth no longer mean the same thing
- resource, scene, prefab, editor, or integration wiring is too uncertain to guess
- acceptance finds a mismatch that should not be silently repaired
- bug diagnosis shows the issue is really design truth, not just implementation

## Required Fields

- `problem`
- `why_stop`
- `recommended_fix`
- `affected_truth`

## Optional Fields

- `fallback_option`
- `recommended_next_command`

## Rules

- Return it in-thread by default instead of creating a durable page.
- Keep it short.
- Combine related uncertainty into one packet when possible.
