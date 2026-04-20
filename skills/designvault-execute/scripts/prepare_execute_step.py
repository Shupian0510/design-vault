#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from init_execution_log import derive_log_name, find_vault_root
from init_execution_log import resolve_plan_path as resolve_plan_path_init
from read_execution_state import build_state
from render_acceptance_prompt import build_prompt as build_acceptance_prompt
from render_phase_worker_prompt import build_prompt as build_phase_prompt
from render_phase_worker_prompt import extract_previous_handoff
from extract_phase_packet import build_packet


def resolve_path(workspace: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = workspace / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")
    return path


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("Execution log is missing YAML frontmatter.")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("Could not find the end of YAML frontmatter.")
    return text[4:end], text[end + 5 :]


def parse_frontmatter(block: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            items: list[str] = []
            j = i + 1
            while j < len(lines) and lines[j].startswith("  - "):
                items.append(lines[j][4:].strip().strip('"'))
                j += 1
            data[key] = items
            i = j
            continue
        if value == "[]":
            data[key] = []
        elif value.startswith('"') and value.endswith('"'):
            data[key] = value[1:-1]
        else:
            data[key] = value
        i += 1
    return data


def find_section(body: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", body[start:], re.MULTILINE)
    if next_heading:
        end = start + next_heading.start()
        return body[start:end].strip()
    return body[start:].strip()


def parse_preflight_status(log_path: Path) -> dict[str, Any]:
    text = log_path.read_text(encoding="utf-8")
    frontmatter_block, body = split_frontmatter(text)
    frontmatter = parse_frontmatter(frontmatter_block)
    preflight = find_section(body, "Preflight")
    entries = {
        "truth_readiness": "",
        "environment_baseline": "",
        "compile_console_baseline": "",
        "test_entry_points": "",
    }
    prefix_map = {
        "- wiki / plan 可读性：": "truth_readiness",
        "- environment / editor 基线：": "environment_baseline",
        "- Unity / Editor 基线：": "environment_baseline",
        "- compile / console 基线：": "compile_console_baseline",
        "- 测试入口：": "test_entry_points",
    }
    for raw in preflight.splitlines():
        stripped = raw.strip()
        for prefix, key in prefix_map.items():
            if stripped.startswith(prefix):
                entries[key] = stripped[len(prefix) :].strip()
                break
    complete = all(entries.values())
    return {"frontmatter": frontmatter, "entries": entries, "complete": complete}


def bootstrap_log_if_needed(
    workspace: Path,
    plan_path: Path,
    log_arg: str | None,
    vault_root_arg: str | None,
) -> tuple[Path, bool]:
    if log_arg:
        return resolve_path(workspace, log_arg), False

    vault_root = find_vault_root(workspace, vault_root_arg)
    candidate = vault_root / "10 Studio" / "Execution Logs" / f"{derive_log_name(plan_path.stem)}.md"
    if candidate.exists():
        return candidate, False

    import subprocess

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("init_execution_log.py")),
                "--plan",
                str(plan_path),
                "--workspace",
                str(workspace),
                "--vault-root",
                str(vault_root),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        if candidate.exists():
            return candidate, False
        raise
    created = Path(result.stdout.strip()).resolve()
    return created, True


def build_output(action: str, plan_path: Path, log_path: Path, log_initialized: bool, include_prompt: bool) -> dict[str, Any]:
    preflight = parse_preflight_status(log_path)
    frontmatter = preflight["frontmatter"]
    state = build_state(plan_path, log_path)

    output: dict[str, Any] = {
        "action": action,
        "plan_path": str(plan_path),
        "log_path": str(log_path),
        "log_initialized": log_initialized,
        "log_status": frontmatter.get("status", ""),
        "preflight_complete": preflight["complete"],
        "preflight_entries": preflight["entries"],
        "state": state,
    }

    if action == "preflight":
        output["preflight_builder"] = {
            "script": str(Path(__file__).with_name("build_preflight_result.py")),
            "notes": [
                "先用 build_preflight_result.py 扫描 plan truth 与 verification hints。",
                "再由父线程补充 environment / editor 与 compile / console 基线。",
                "最后用 update_preflight_section.py 把结果写回 execution log。",
            ],
        }
        output["required_result_fields"] = [
            "truth_readiness",
            "environment_baseline",
            "compile_console_baseline",
            "test_entry_points",
        ]
        return output

    if action == "phase":
        next_phase = state.get("next_phase")
        assert isinstance(next_phase, dict)
        phase_index = int(next_phase["index"])
        packet = build_packet(plan_path, phase_index)
        output["phase"] = {"index": phase_index, "title": next_phase["title"]}
        output["preferred_agent"] = {
            "agent_type": "phase_executor",
            "fallback_agent_type": "worker",
            "model": "gpt-5.4",
            "reasoning_effort": "high",
        }
        if include_prompt:
            previous_handoff = extract_previous_handoff(log_path, phase_index)
            output["prompt"] = build_phase_prompt(packet, previous_handoff)
        return output

    if action == "acceptance":
        output["preferred_agent"] = {
            "agent_type": "acceptance_executor",
            "fallback_agent_type": "default",
            "model": "gpt-5.4",
            "reasoning_effort": "high",
        }
        if include_prompt:
            output["prompt"] = build_acceptance_prompt(plan_path, log_path)
        return output

    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare the next deterministic parent-thread action for DesignVault /execute."
    )
    parser.add_argument("--plan", required=True, help="Path to the implementation plan markdown file.")
    parser.add_argument("--log", help="Optional path to the execution log markdown file.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--vault-root", help="Optional explicit DesignVault root. Defaults to auto-detect or DESIGNVAULT_ROOT.")
    parser.add_argument("--include-prompt", action="store_true", help="Include the rendered child or acceptance prompt.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    plan_path = resolve_plan_path_init(workspace, args.plan)
    log_path, log_initialized = bootstrap_log_if_needed(workspace, plan_path, args.log, args.vault_root)
    preflight = parse_preflight_status(log_path)

    if preflight["frontmatter"].get("status") == "done":
        action = "complete"
    elif not preflight["complete"]:
        action = "preflight"
    else:
        state = build_state(plan_path, log_path)
        action = "acceptance" if state["ready_for_acceptance"] else "phase"

    print(json.dumps(build_output(action, plan_path, log_path, log_initialized, args.include_prompt), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
