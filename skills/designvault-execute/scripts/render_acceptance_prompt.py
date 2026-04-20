#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Any


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
        raise ValueError("Markdown file is missing YAML frontmatter.")
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


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return [str(value).strip()]


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


def find_first_section(body: str, headings: list[str]) -> str:
    for heading in headings:
        content = find_section(body, heading)
        if content:
            return content
    return ""


def build_prompt(plan_path: Path, log_path: Path) -> str:
    plan_fm, plan_body = split_frontmatter(plan_path.read_text(encoding="utf-8"))
    log_fm, log_body = split_frontmatter(log_path.read_text(encoding="utf-8"))
    plan_meta = parse_frontmatter(plan_fm)
    log_meta = parse_frontmatter(log_fm)

    source_notes = normalize_list(plan_meta.get("source_notes"))
    related = normalize_list(plan_meta.get("related"))
    playtest_focus = normalize_list(log_meta.get("playtest_focus"))
    risk_items = normalize_list(log_meta.get("risk_items"))
    writeback_pages = normalize_list(log_meta.get("writeback_pages"))
    phase_notes = find_section(log_body, "Phase 记录")
    acceptance_criteria = find_first_section(plan_body, ["Acceptance Phase", "总体验收标准", "验证计划"])

    return f"""你现在作为 DesignVault /execute 的 Acceptance 阶段工作。

只做 acceptance，不改代码，不改设计。
你要对照：
- longform
- wiki truth
- final implementation
- test results

如果发现的是实现偏差或设计偏差，不要静默修复，应该明确指出并建议 decision packet。

返回紧凑 JSON，键必须是：
- acceptance_status
- machine_checks
- acceptance_summary
- playtest_focus
- risks
- updated_pages
- decision_packet_needed
- decision_packet

其中：
- `acceptance_status` 用 `accepted` 或 `needs_decision`
- `machine_checks` 应总结 compile / console / tests
- `playtest_focus`、`risks`、`updated_pages` 都返回数组
- 如果不需要 decision packet，`decision_packet_needed` 返回 false，`decision_packet` 返回 null
- 最终只返回一个 JSON 对象，不要加 Markdown code fence，不要加解释文字

## Source Plan

- path: `{plan_path}`
- source_notes: {source_notes}
- related wiki: {related}

## Plan Acceptance Criteria

{acceptance_criteria or '未在 plan 中单独写出，请根据 longform / wiki truth / 实现与测试结果综合判断。'}

## Execution Log

- path: `{log_path}`
- playtest_focus: {playtest_focus}
- risk_items: {risk_items}
- writeback_pages: {writeback_pages}

## Phase Notes

{phase_notes}
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render the standard DesignVault acceptance prompt from one plan and one execution log."
    )
    parser.add_argument("--plan", required=True, help="Path to the implementation plan markdown file.")
    parser.add_argument("--log", required=True, help="Path to the execution log markdown file.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    plan_path = resolve_path(workspace, args.plan)
    log_path = resolve_path(workspace, args.log)
    print(build_prompt(plan_path, log_path))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
