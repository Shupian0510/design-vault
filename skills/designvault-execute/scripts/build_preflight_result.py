#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from init_execution_log import find_vault_root
from extract_phase_packet import resolve_plan_path, build_packet


WIKI_LINK_RE = re.compile(r"\[\[(?P<target>[^\]|#]+)")


def extract_frontmatter_links(plan_text: str) -> dict[str, list[str]]:
    if not plan_text.startswith("---\n"):
        return {"source_notes": [], "related": []}
    end = plan_text.find("\n---\n", 4)
    if end == -1:
        return {"source_notes": [], "related": []}
    block = plan_text[4:end]
    current_key = None
    values: dict[str, list[str]] = {"source_notes": [], "related": []}
    for raw in block.splitlines():
        line = raw.rstrip()
        match = re.match(r"^(source_notes|related):\s*(.*)$", line)
        if match:
            current_key = match.group(1)
            rest = match.group(2).strip()
            if rest and rest != "[]":
                values[current_key].extend(WIKI_LINK_RE.findall(rest))
            continue
        if current_key and re.match(r"^\s*-\s+", line):
            values[current_key].extend(WIKI_LINK_RE.findall(line))
        else:
            current_key = None
    return values


def extract_phase_count(plan_text: str) -> int:
    return len(re.findall(r"^(#{2,3})\s+Phase\s+\d+\s*[:：-]\s*.+?$", plan_text, re.MULTILINE))


def extract_verification_hints(plan_path: Path) -> list[str]:
    markdown = plan_path.read_text(encoding="utf-8")
    phase_count = extract_phase_count(markdown)
    hints: list[str] = []
    for phase_index in range(1, phase_count + 1):
        packet = build_packet(plan_path, phase_index)
        verification = str(packet.get("verification", "")).strip()
        if verification:
            compact = re.sub(r"\s+", " ", verification)
            hints.append(f"Phase {phase_index}: {compact}")
    return hints


def resolve_wiki_link(vault_root: Path, link: str) -> Path | None:
    match = WIKI_LINK_RE.search(link)
    target = match.group("target").strip() if match else link.strip()
    if not target:
        return None

    candidates: list[Path] = []
    if target.endswith(".md"):
        target = target[:-3]

    direct = vault_root / f"{target}.md"
    candidates.append(direct)

    leaf = Path(target).name
    if leaf and direct.name != f"{leaf}.md":
        candidates.extend(vault_root.rglob(f"{leaf}.md"))

    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except FileNotFoundError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
    return None


def summarize_truth(links: list[str], vault_root: Path) -> tuple[str, list[str], list[str], bool]:
    resolved_links: list[str] = []
    missing_links: list[str] = []

    for link in links:
        resolved = resolve_wiki_link(vault_root, link)
        if resolved is None:
            missing_links.append(link)
        else:
            resolved_links.append(link)

    if missing_links:
        summary = f"truth 存在缺口：已解析 {len(resolved_links)} 项，缺失 {len(missing_links)} 项。"
    elif resolved_links:
        summary = f"truth 页面解析通过：{len(resolved_links)} 项。"
    else:
        summary = "plan 未显式列出 truth 页面，需要人工确认是否合理。"

    should_stop = bool(missing_links)
    return summary, resolved_links, missing_links, should_stop


def normalize_optional(value: str | None, fallback: str) -> str:
    return value.strip() if value and value.strip() else fallback


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a structured preflight result for DesignVault /execute from plan truth links plus optional environment baseline strings."
    )
    parser.add_argument("--plan", required=True, help="Path to the implementation plan markdown file.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--vault-root", help="Optional explicit DesignVault root. Defaults to auto-detect or DESIGNVAULT_ROOT.")
    parser.add_argument("--environment-baseline", help="Optional environment/editor baseline summary.")
    parser.add_argument("--unity-baseline", help=argparse.SUPPRESS)
    parser.add_argument("--compile-console-baseline", help="Optional compile/console baseline summary.")
    parser.add_argument("--test-entry-points", help="Optional explicit test entry point summary.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    vault_root = find_vault_root(workspace, args.vault_root)
    plan_path = resolve_plan_path(workspace, args.plan)
    plan_text = plan_path.read_text(encoding="utf-8")

    frontmatter_links = extract_frontmatter_links(plan_text)
    phase_count = extract_phase_count(plan_text)
    phase_links: list[str] = []
    for phase_index in range(1, phase_count + 1):
        packet = build_packet(plan_path, phase_index)
        phase_links.extend(packet.get("required_wiki", []))
        phase_links.extend(re.findall(r"\[\[[^\]]+\]\]", str(packet.get("dependencies", ""))))

    all_links = []
    seen = set()
    for link in frontmatter_links["related"] + phase_links:
        if link not in seen:
            seen.add(link)
            all_links.append(link)

    truth_readiness, resolved_links, missing_links, should_stop = summarize_truth(all_links, vault_root)
    verification_hints = extract_verification_hints(plan_path)

    environment_input = args.environment_baseline or args.unity_baseline
    environment_baseline = normalize_optional(
        environment_input,
        "待父线程通过项目使用的编辑器、运行桥接或本地工具链确认环境基线。",
    )
    compile_console_baseline = normalize_optional(
        args.compile_console_baseline,
        "待父线程刷新并读取 compile / console 基线。",
    )
    environment_pending = not bool(environment_input and environment_input.strip())
    compile_pending = not bool(args.compile_console_baseline and args.compile_console_baseline.strip())
    should_stop = should_stop or environment_pending or compile_pending
    stop_reasons = [f"缺失 truth 页面：{link}" for link in missing_links]
    if environment_pending:
        stop_reasons.append("environment / editor 基线尚未确认。")
    if compile_pending:
        stop_reasons.append("compile / console 基线尚未刷新并读取。")

    result: dict[str, Any] = {
        "truth_readiness": truth_readiness,
        "environment_baseline": environment_baseline,
        "compile_console_baseline": compile_console_baseline,
        "test_entry_points": normalize_optional(
            args.test_entry_points,
            "；".join(verification_hints) if verification_hints else "plan 未显式列出测试入口。",
        ),
        "resolved_truth_pages": resolved_links,
        "missing_truth_pages": missing_links,
        "verification_hints": verification_hints,
        "should_stop": should_stop,
        "stop_reasons": stop_reasons,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
