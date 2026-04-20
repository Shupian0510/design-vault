#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


PHASE_REQUIRED_KEYS = {
    "changed",
    "left_unchanged",
    "tests_run",
    "risks",
    "writeback_pages",
    "design_reasoning",
    "next_phase_watchouts",
}

ACCEPTANCE_REQUIRED_KEYS = {
    "acceptance_status",
    "machine_checks",
    "acceptance_summary",
    "playtest_focus",
    "risks",
    "updated_pages",
    "decision_packet_needed",
    "decision_packet",
}


def resolve_path(workspace: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = workspace / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")
    return path


def read_raw_text(raw_text: str | None, raw_file: str | None, workspace: Path) -> str:
    if raw_text is not None:
        return raw_text
    if raw_file:
        return resolve_path(workspace, raw_file).read_text(encoding="utf-8")
    raise ValueError("Provide either --raw-text or --raw-file.")


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            stripped = "\n".join(lines[1:-1]).strip()

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        start = None
        depth = 0
        for index, char in enumerate(text):
            if char == "{":
                if start is None:
                    start = index
                depth += 1
            elif char == "}":
                if start is None:
                    continue
                depth -= 1
                if depth == 0:
                    candidate = text[start : index + 1]
                    try:
                        data = json.loads(candidate)
                        break
                    except json.JSONDecodeError:
                        start = None
        else:
            raise ValueError("Could not extract a valid JSON object from agent output.")

    if not isinstance(data, dict):
        raise ValueError("Agent result must be a JSON object.")
    return data


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_scalar(v) for v in value if normalize_scalar(v)]
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    normalized = normalize_scalar(value)
    return [normalized] if normalized else []


def normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        if {"name", "status", "reason"}.issubset(value.keys()):
            name = str(value.get("name", "")).strip()
            status = str(value.get("status", "")).strip()
            reason = str(value.get("reason", "")).strip()
            parts = [name]
            if status:
                parts.append(f"[{status}]")
            if reason:
                parts.append(f": {reason}")
            return " ".join(part for part in parts if part).replace(" ]", "]").strip()
        if {"name", "status", "details"}.issubset(value.keys()):
            name = str(value.get("name", "")).strip()
            status = str(value.get("status", "")).strip()
            details = str(value.get("details", "")).strip()
            parts = [name]
            if status:
                parts.append(f"[{status}]")
            if details:
                parts.append(f": {details}")
            return " ".join(part for part in parts if part).replace(" ]", "]").strip()
        if {"name", "result", "notes"}.issubset(value.keys()):
            name = str(value.get("name", "")).strip()
            result = str(value.get("result", "")).strip()
            notes = str(value.get("notes", "")).strip()
            parts = [name]
            if result:
                parts.append(f"[{result}]")
            if notes:
                parts.append(f": {notes}")
            return " ".join(part for part in parts if part).replace(" ]", "]").strip()
        if {"page", "status", "reason"}.issubset(value.keys()):
            page = str(value.get("page", "")).strip()
            status = str(value.get("status", "")).strip()
            reason = str(value.get("reason", "")).strip()
            parts = [page]
            if status:
                parts.append(f"[{status}]")
            if reason:
                parts.append(f": {reason}")
            return " ".join(part for part in parts if part).replace(" ]", "]").strip()
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def normalize_phase(data: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(PHASE_REQUIRED_KEYS - set(data.keys()))
    if missing:
        raise ValueError(f"Phase result is missing required keys: {', '.join(missing)}")
    changed = normalize_list(data.get("changed"))
    if not changed:
        summary = normalize_scalar(data.get("summary"))
        if summary:
            changed = [summary]
    stop_reason = normalize_scalar(data.get("stop_reason"))
    decision_packet = data.get("decision_packet")
    should_stop = bool(stop_reason) or decision_packet is not None
    return {
        "changed": changed,
        "left_unchanged": normalize_list(data.get("left_unchanged")),
        "tests_run": normalize_list(data.get("tests_run")),
        "risks": normalize_list(data.get("risks")),
        "writeback_pages": normalize_list(data.get("writeback_pages")),
        "design_reasoning": normalize_list(data.get("design_reasoning")),
        "next_phase_watchouts": normalize_list(data.get("next_phase_watchouts")),
        "playtest_focus": normalize_list(data.get("playtest_focus")),
        "decision_packet": decision_packet,
        "stop_reason": stop_reason,
        "should_stop": should_stop,
    }


def normalize_acceptance(data: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(ACCEPTANCE_REQUIRED_KEYS - set(data.keys()))
    if missing:
        raise ValueError(f"Acceptance result is missing required keys: {', '.join(missing)}")

    acceptance_status = str(data.get("acceptance_status", "")).strip()
    if acceptance_status not in {"accepted", "needs_decision"}:
        raise ValueError("acceptance_status must be 'accepted' or 'needs_decision'.")

    decision_needed = data.get("decision_packet_needed")
    if not isinstance(decision_needed, bool):
        raise ValueError("decision_packet_needed must be a boolean.")

    return {
        "acceptance_status": acceptance_status,
        "machine_checks": normalize_list(data.get("machine_checks")),
        "acceptance_summary": str(data.get("acceptance_summary", "")).strip(),
        "playtest_focus": normalize_list(data.get("playtest_focus")),
        "risks": normalize_list(data.get("risks")),
        "updated_pages": normalize_list(data.get("updated_pages")),
        "decision_packet_needed": decision_needed,
        "decision_packet": data.get("decision_packet"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract, validate, and normalize DesignVault /execute child-agent JSON results."
    )
    parser.add_argument("--mode", required=True, choices=("phase", "acceptance"), help="Result schema to validate.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--raw-text", help="Inline raw child-agent output.")
    parser.add_argument("--raw-file", help="Path to a file containing raw child-agent output.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    raw_text = read_raw_text(args.raw_text, args.raw_file, workspace)
    parsed = extract_json_object(raw_text)
    normalized = normalize_phase(parsed) if args.mode == "phase" else normalize_acceptance(parsed)
    print(json.dumps(normalized, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
