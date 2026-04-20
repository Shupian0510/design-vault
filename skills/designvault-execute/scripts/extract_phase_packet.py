#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Iterable


PHASE_HEADING_RE = re.compile(r"^(#{2,3})\s+Phase\s+(\d+)\s*[:：-]\s*(.+?)\s*$")
STOP_HEADING_RES = [
    re.compile(r"^(#{2,3})\s+Acceptance Phase\s*$"),
    re.compile(r"^(#{2,3})\s+Repair Loop\s*$"),
]

SECTION_ALIASES = {
    "goal": {"goal", "目标"},
    "non_goals": {"non-goals", "non goals", "非目标"},
    "dependencies": {"dependencies", "依赖"},
    "required_wiki": {"required wiki pages", "需要读取的 wiki 页面", "读取 wiki"},
    "required_context": {
        "读取代码 / scene / prefab / unity 入口",
        "read code / scene / prefab / unity entry points",
        "read code / scene / prefab / unity entry point",
        "required code context",
        "代码与 unity 未知项",
        "代码与 unity 未知",
        "required context",
    },
    "implementation_notes": {"implementation notes", "implementation note", "实施说明", "实施要点"},
    "scope": {"实施范围", "scope"},
    "success_criteria": {"成功条件", "success criteria"},
    "verification": {"verification", "验证", "验收方式"},
    "writeback_targets": {"wiki writeback targets", "wiki 回写目标", "wiki 回写"},
    "stop_conditions": {"stop conditions", "停机条件"},
}

BULLET_PREFIX_MAP = {
    "success_criteria": ["- 成功时应该看到：", "- 成功时应该看到什么："],
    "verification": ["- 验收方式：", "- 验证方式："],
    "writeback_targets": ["- 可能要回写哪些页面：", "- 写回页面："],
    "stop_conditions": ["- 什么情况必须停：", "- 什么情况必须停机：", "- 停机条件："],
    "required_context": ["- 还需要看什么代码 / scene / prefab / Unity 入口：", "- 还需要看什么代码 / 资源 / 编辑器入口："],
}


def normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().lower())


def map_section(label: str) -> str | None:
    norm = normalize_label(label)
    for canonical, aliases in SECTION_ALIASES.items():
        if norm in aliases:
            return canonical
    return None


def extract_phase_block(markdown: str, phase_number: int) -> tuple[str, list[str]]:
    lines = markdown.splitlines()
    started = False
    level = ""
    title = ""
    block: list[str] = []
    for line in lines:
        stripped = line.strip()
        match = PHASE_HEADING_RE.match(stripped)
        if match:
            if started:
                break
            if int(match.group(2)) == phase_number:
                started = True
                level = match.group(1)
                title = match.group(3).strip()
                continue
        if started:
            if any(p.match(stripped) for p in STOP_HEADING_RES):
                break
            if stripped.startswith(level + " ") and PHASE_HEADING_RE.match(stripped):
                break
            block.append(line)
    if not started:
        raise ValueError(f"Could not find Phase {phase_number} in the plan.")
    return title, block


def parse_phase_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_key = "body"
    sections[current_key] = []
    section_heading_re = re.compile(r"^(#{3,4})\s+(.+?)\s*$")

    for line in lines:
        stripped = line.strip()
        heading = section_heading_re.match(stripped)
        if heading:
            mapped = map_section(heading.group(2))
            if mapped:
                current_key = mapped
                sections.setdefault(current_key, [])
                continue
        sections.setdefault(current_key, []).append(line)

    return sections


def clean_block(lines: Iterable[str]) -> list[str]:
    raw = [line.rstrip() for line in lines]
    while raw and not raw[0].strip():
        raw.pop(0)
    while raw and not raw[-1].strip():
        raw.pop()
    return raw


def extract_wiki_links(lines: Iterable[str]) -> list[str]:
    links: list[str] = []
    for line in lines:
        links.extend(re.findall(r"\[\[[^\]]+\]\]", line))
    deduped: list[str] = []
    seen = set()
    for link in links:
        if link not in seen:
            seen.add(link)
            deduped.append(link)
    return deduped


def extract_frontmatter_links(markdown: str, key: str) -> list[str]:
    if not markdown.startswith("---\n"):
        return []
    end = markdown.find("\n---\n", 4)
    if end == -1:
        return []
    block = markdown[4:end]
    current_key = None
    values: list[str] = []
    for raw in block.splitlines():
        line = raw.rstrip()
        match = re.match(r"^(source_notes|related):\s*(.*)$", line)
        if match:
            current_key = match.group(1)
            if current_key != key:
                continue
            values.extend(re.findall(r"\[\[[^\]]+\]\]", match.group(2)))
            continue
        if current_key == key and re.match(r"^\s*-\s+", line):
            values.extend(re.findall(r"\[\[[^\]]+\]\]", line))
        else:
            current_key = None
    return values


def find_section_body(markdown: str, headings: list[str]) -> list[str]:
    lines = markdown.splitlines()
    current = None
    level = None
    body: list[str] = []
    for line in lines:
        stripped = line.strip()
        match = re.match(r"^(#{2,4})\s+(.+?)\s*$", stripped)
        if match:
            heading = match.group(2)
            if current is None and heading in headings:
                current = heading
                level = len(match.group(1))
                continue
            if current is not None and len(match.group(1)) <= level:
                break
        if current is not None:
            body.append(line)
    return body


def first_meaningful_line(lines: list[str]) -> str:
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            return stripped[2:].strip()
        return stripped
    return ""


def extract_prefixed_values(lines: list[str], prefixes: list[str]) -> list[str]:
    values: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        for prefix in prefixes:
            if stripped.startswith(prefix):
                value = stripped[len(prefix) :].strip()
                if value:
                    values.append(value)
                break
    return values


def build_packet(plan_path: Path, phase_number: int) -> dict[str, object]:
    markdown = plan_path.read_text(encoding="utf-8")
    title, block = extract_phase_block(markdown, phase_number)
    sections = parse_phase_sections(block)

    required_wiki = extract_wiki_links(sections.get("required_wiki", []))
    if not required_wiki:
        truth_context = find_section_body(markdown, ["truth 与上下文", "truth and context"])
        required_wiki = extract_wiki_links(truth_context)
    if not required_wiki:
        required_wiki = extract_frontmatter_links(markdown, "related")

    writeback_targets = extract_wiki_links(sections.get("writeback_targets", []))
    if not writeback_targets:
        writeback_targets = extract_prefixed_values(sections.get("body", []), BULLET_PREFIX_MAP["writeback_targets"])

    success_criteria = "\n".join(clean_block(sections.get("success_criteria", [])))
    if not success_criteria:
        success_criteria = "\n".join(extract_prefixed_values(sections.get("body", []), BULLET_PREFIX_MAP["success_criteria"]))

    verification = "\n".join(clean_block(sections.get("verification", [])))
    if not verification:
        verification = "\n".join(extract_prefixed_values(sections.get("body", []), BULLET_PREFIX_MAP["verification"]))

    stop_conditions = "\n".join(clean_block(sections.get("stop_conditions", [])))
    if not stop_conditions:
        stop_conditions = "\n".join(extract_prefixed_values(sections.get("body", []), BULLET_PREFIX_MAP["stop_conditions"]))

    required_context = "\n".join(clean_block(sections.get("required_context", [])))
    if not required_context:
        required_context = "\n".join(extract_prefixed_values(sections.get("body", []), BULLET_PREFIX_MAP["required_context"]))

    goal = "\n".join(clean_block(sections.get("goal", [])))
    if not goal:
        goal = first_meaningful_line(sections.get("body", []))

    packet = {
        "plan_path": str(plan_path.resolve()),
        "plan_title": plan_path.stem,
        "phase_number": phase_number,
        "phase_title": title,
        "goal": goal,
        "non_goals": "\n".join(clean_block(sections.get("non_goals", []))),
        "dependencies": "\n".join(clean_block(sections.get("dependencies", []))),
        "required_wiki": required_wiki,
        "required_context": required_context,
        "scope": "\n".join(clean_block(sections.get("scope", []))) or goal,
        "implementation_notes": "\n".join(clean_block(sections.get("implementation_notes", []))),
        "success_criteria": success_criteria,
        "verification": verification,
        "writeback_targets": writeback_targets,
        "stop_conditions": stop_conditions,
        "raw_phase_markdown": "\n".join(clean_block(block)),
    }
    return packet


def render_markdown(packet: dict[str, object]) -> str:
    def bullet_list(items: list[str]) -> str:
        if not items:
            return "- 无"
        return "\n".join(f"- {item}" for item in items)

    return f"""# Phase Packet

## Source

- plan: `{packet["plan_title"]}`
- phase: `Phase {packet["phase_number"]} - {packet["phase_title"]}`

## Goal

{packet["goal"]}

## Non-goals

{packet["non_goals"]}

## Dependencies

{packet["dependencies"]}

## Required Wiki

{bullet_list(packet["required_wiki"])}

## Required Context

{packet["required_context"]}

## Scope

{packet["scope"]}

## Implementation Notes

{packet["implementation_notes"]}

## Success Criteria

{packet["success_criteria"]}

## Verification

{packet["verification"]}

## Writeback Targets

{bullet_list(packet["writeback_targets"])}

## Stop Conditions

{packet["stop_conditions"]}
"""


def resolve_plan_path(workspace: Path, plan_arg: str) -> Path:
    plan = Path(plan_arg)
    if not plan.is_absolute():
        plan = workspace / plan
    plan = plan.resolve()
    if not plan.exists():
        raise FileNotFoundError(f"Plan file does not exist: {plan}")
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract one DesignVault implementation-plan phase into a structured phase packet."
    )
    parser.add_argument("--plan", required=True, help="Path to the implementation plan markdown file.")
    parser.add_argument("--phase", required=True, type=int, help="Phase number to extract.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format. Defaults to json.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    plan_path = resolve_plan_path(workspace, args.plan)
    packet = build_packet(plan_path, args.phase)

    if args.format == "json":
        print(json.dumps(packet, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(packet))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
