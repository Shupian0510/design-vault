#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from init_execution_log import derive_log_name, find_vault_root, extract_phases


PHASE_HEADING_RE = re.compile(r"^###\s+Phase\s+(\d+)\s*-\s*(.+?)\s*$")
FIELD_PREFIXES = {
    "- 完成摘要：": "summary",
    "- 实际完成摘要：": "summary",
    "- 风险：": "risks",
    "- 下一 phase 注意点：": "watchouts",
}


def resolve_path(workspace: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = workspace / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")
    return path


def resolve_log_path(workspace: Path, plan_path: Path, log_arg: str | None, vault_root_arg: str | None) -> Path | None:
    if log_arg:
        return resolve_path(workspace, log_arg)

    vault_root = find_vault_root(workspace, vault_root_arg)
    candidate = vault_root / "10 Studio" / "Execution Logs" / f"{derive_log_name(plan_path.stem)}.md"
    return candidate if candidate.exists() else None


def parse_phase_progress(log_text: str) -> dict[int, dict[str, str]]:
    lines = log_text.splitlines()
    progress: dict[int, dict[str, str]] = {}
    current_phase = None

    for raw in lines:
        stripped = raw.strip()
        heading = PHASE_HEADING_RE.match(stripped)
        if heading:
            current_phase = int(heading.group(1))
            progress.setdefault(current_phase, {})
            continue
        if current_phase is None:
            continue
        if stripped.startswith("## "):
            current_phase = None
            continue
        for prefix, key in FIELD_PREFIXES.items():
            if stripped.startswith(prefix):
                progress.setdefault(current_phase, {})[key] = stripped[len(prefix) :].strip()
                break

    return progress


def build_state(plan_path: Path, log_path: Path | None) -> dict[str, object]:
    phases = extract_phases(plan_path.read_text(encoding="utf-8"))
    progress = parse_phase_progress(log_path.read_text(encoding="utf-8")) if log_path else {}

    phase_states: list[dict[str, object]] = []
    next_phase: dict[str, object] | None = None
    completed = 0

    for phase in phases:
        index = int(phase["index"])
        title = str(phase["title"])
        phase_progress = progress.get(index, {})
        summary = phase_progress.get("summary", "")
        risks = phase_progress.get("risks", "")
        watchouts = phase_progress.get("watchouts", "")
        status = "completed" if summary else "pending"
        if status == "completed":
            completed += 1
        elif next_phase is None:
            next_phase = {"index": index, "title": title}

        phase_states.append(
            {
                "index": index,
                "title": title,
                "status": status,
                "summary": summary,
                "risks": risks,
                "watchouts": watchouts,
            }
        )

    return {
        "plan_path": str(plan_path),
        "log_path": str(log_path) if log_path else None,
        "phase_count": len(phases),
        "completed_phase_count": completed,
        "ready_for_acceptance": completed == len(phases) and len(phases) > 0,
        "next_phase": next_phase,
        "phases": phase_states,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read one DesignVault execution plan/log pair and summarize the current phase orchestration state."
    )
    parser.add_argument("--plan", required=True, help="Path to the implementation plan markdown file.")
    parser.add_argument("--log", help="Optional path to the execution log markdown file.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--vault-root", help="Optional explicit DesignVault root. Defaults to auto-detect or DESIGNVAULT_ROOT.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format. Defaults to json.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    plan_path = resolve_path(workspace, args.plan)
    log_path = resolve_log_path(workspace, plan_path, args.log, args.vault_root)
    state = build_state(plan_path, log_path)

    if args.format == "json":
        print(json.dumps(state, ensure_ascii=False, indent=2))
    else:
        lines = [
            "# Execution State",
            "",
            f"- plan: `{state['plan_path']}`",
            f"- log: `{state['log_path'] or 'none'}`",
            f"- completed: `{state['completed_phase_count']} / {state['phase_count']}`",
            f"- ready_for_acceptance: `{state['ready_for_acceptance']}`",
            f"- next_phase: `{state['next_phase']}`",
            "",
            "## Phases",
            "",
        ]
        for phase in state["phases"]:
            lines.append(
                f"- Phase {phase['index']} - {phase['title']} | {phase['status']} | summary: {phase['summary'] or '未完成'}"
            )
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
