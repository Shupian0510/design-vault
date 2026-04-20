#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys

PHASE_HEADING_RE = re.compile(r"^(#{2,3})\s+Phase\s+(\d+)\s*[:：-]\s*(.+?)\s*$")
ACCEPTANCE_HEADING_RE = re.compile(r"^(#{2,3})\s+Acceptance Phase\s*$")
VAULT_CANDIDATE_SUFFIXES = (
    Path("Docs") / "DesignVault",
    Path("docs") / "DesignVault",
    Path("DesignVault"),
)


def is_vault_root(path: Path) -> bool:
    return (
        path.exists()
        and (path / "index.md").exists()
        and (path / "00 Wiki").exists()
        and (path / "10 Studio").exists()
    )


def find_vault_root(workspace: Path, vault_root_arg: str | None = None) -> Path:
    explicit = vault_root_arg or os.environ.get("DESIGNVAULT_ROOT")
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            candidate = workspace / candidate
        candidate = candidate.resolve()
        if is_vault_root(candidate):
            return candidate
        raise FileNotFoundError(f"Provided DesignVault root is invalid: {candidate}")

    current = workspace.resolve()
    search_roots = [current, *current.parents]
    for root in search_roots:
        if is_vault_root(root):
            return root
        for suffix in VAULT_CANDIDATE_SUFFIXES:
            candidate = (root / suffix).resolve()
            if is_vault_root(candidate):
                return candidate

    expected = [str(workspace / suffix) for suffix in VAULT_CANDIDATE_SUFFIXES]
    raise FileNotFoundError(
        f"Could not find DesignVault from {workspace}. Pass --vault-root or set DESIGNVAULT_ROOT. "
        f"Typical locations: {', '.join(expected)}"
    )


def resolve_plan_path(workspace: Path, plan_arg: str) -> Path:
    plan = Path(plan_arg)
    if not plan.is_absolute():
        plan = workspace / plan
    plan = plan.resolve()
    if not plan.exists():
        raise FileNotFoundError(f"Plan file does not exist: {plan}")
    return plan


def derive_log_name(plan_stem: str) -> str:
    if plan_stem.startswith("计划 - "):
        return "执行记录 - " + plan_stem[len("计划 - ") :]
    return "执行记录 - " + plan_stem


def make_wiki_link(vault_root: Path, target: Path) -> str:
    rel = target.resolve().relative_to(vault_root.resolve()).as_posix()
    if rel.endswith(".md"):
        rel = rel[:-3]
    return f"[[{rel}]]"


def extract_phases(markdown: str) -> list[dict[str, object]]:
    phases: list[dict[str, object]] = []
    lines = markdown.splitlines()
    current: dict[str, object] | None = None

    for line in lines:
        phase_match = PHASE_HEADING_RE.match(line.strip())
        if phase_match:
            if current:
                phases.append(current)
            current = {
                "index": int(phase_match.group(2)),
                "title": phase_match.group(3).strip(),
                "heading": line.strip(),
                "body": [],
            }
            continue

        if ACCEPTANCE_HEADING_RE.match(line.strip()):
            if current:
                phases.append(current)
                current = None
            break

        if current is not None:
            cast_body = current["body"]
            assert isinstance(cast_body, list)
            cast_body.append(line)

    if current:
        phases.append(current)

    return phases


def build_phase_sections(phases: list[dict[str, object]]) -> str:
    if not phases:
        return """### Phase 1 - <名称>

- 计划标题：
- 计划范围摘要：
- 实际完成摘要：
- tests：
- 风险：
- 设计保留 / 修改原因：
- 写回页面：
- 下一 phase 注意点：
"""

    blocks: list[str] = []
    for phase in phases:
        title = str(phase["title"])
        heading = str(phase["heading"])
        body = str("\n".join(phase["body"])).strip()
        summary = ""
        for raw in body.splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped in {"目标", "非目标", "验证", "Wiki 回写目标", "需要读取的 wiki 页面", "实施说明"}:
                continue
            if stripped.startswith("- 目标：") or stripped.startswith("- 非目标："):
                summary = stripped[2:].strip()
                break
            summary = stripped
            break
        blocks.append(
            f"""### Phase {phase["index"]} - {title}

- 计划标题：`{heading}`
- 计划范围摘要：{summary}
- 完成摘要：
- tests：
- 风险：
- 设计保留 / 修改原因：
- 写回页面：
- 下一 phase 注意点：
"""
        )
    return "\n".join(blocks).rstrip() + "\n"


def build_log_text(source_plan_link: str, today: str, title: str, phase_sections: str) -> str:
    return f"""---
type: execution_log
status: active
updated: {today}
source_plan: "{source_plan_link}"
decision_needed: false
decision_summary: ""
playtest_focus: []
risk_items: []
writeback_pages: []
related:
  - "{source_plan_link}"
---

# {title}

## 来源 Plan

- source_plan: {source_plan_link}

## Preflight

- wiki / plan 可读性：
- environment / editor 基线：
- compile / console 基线：
- 测试入口：

## Phase 记录

{phase_sections.rstrip()}

## Acceptance

- 对照 longform：
- 对照 wiki truth：
- 机器验收结果：
- 需要人类试玩关注的点：

## 最终摘要

- 完成了什么：
- 风险项：
- 更新页面：
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an execution log page for one DesignVault implementation plan."
    )
    parser.add_argument("--plan", required=True, help="Path to the implementation plan markdown file.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to the current working directory.")
    parser.add_argument("--vault-root", help="Optional explicit DesignVault root. Defaults to auto-detect or DESIGNVAULT_ROOT.")
    parser.add_argument("--force", action="store_true", help="Overwrite the target log file if it already exists.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of only the log path.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    vault_root = find_vault_root(workspace, args.vault_root)
    plan_path = resolve_plan_path(workspace, args.plan)
    logs_dir = vault_root / "10 Studio" / "Execution Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_title = derive_log_name(plan_path.stem)
    log_path = logs_dir / f"{log_title}.md"
    if log_path.exists() and not args.force:
        print(f"Refusing to overwrite existing log: {log_path}", file=sys.stderr)
        return 1

    today = dt.date.today().isoformat()
    source_plan_link = make_wiki_link(vault_root, plan_path)
    plan_text = plan_path.read_text(encoding="utf-8")
    phases = extract_phases(plan_text)
    phase_sections = build_phase_sections(phases)
    log_text = build_log_text(source_plan_link, today, log_title, phase_sections)
    log_path.write_text(log_text, encoding="utf-8", newline="\n")

    summary = {
        "plan_path": str(plan_path),
        "plan_link": source_plan_link,
        "log_path": str(log_path),
        "phase_count": len(phases),
        "phases": [
            {"index": phase["index"], "title": phase["title"], "heading": phase["heading"]}
            for phase in phases
        ],
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
