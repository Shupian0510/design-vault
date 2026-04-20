# Repair Loop

`Repair Loop` is the bounded correction path after `Acceptance Phase`.

## Default Sequence

1. Run acceptance first.
2. If acceptance finds a real mismatch, return a `decision packet`.
3. After the user confirms the correction, create one small `Repair Packet`.
4. Repair only the affected truth, code, and verification scope.
5. Re-run only the affected acceptance checks.

## Repair Packet

It is not a new large plan. It should say only:

- what mismatch to fix
- which truth, code, assets, or editor wiring are affected
- which checks must be rerun
- which acceptance segment the run should return to

## Stop Repairing

Do not keep looping forever when:

- the repair is now a design refactor
- the repair scope is now a new feature
- the original plan no longer describes the remaining work

At that point, stop and return to `/design`.
