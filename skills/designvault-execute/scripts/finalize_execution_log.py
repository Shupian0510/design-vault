#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
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


def dump_frontmatter(data: dict[str, Any]) -> str:
    ordered_keys = [
        "type",
        "status",
        "updated",
        "source_plan",
        "decision_needed",
        "decision_summary",
        "playtest_focus",
        "risk_items",
        "writeback_pages",
        "related",
    ]
    lines: list[str] = []
    for key in ordered_keys:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    escaped = str(item).replace('"', '\\"')
                    lines.append(f'  - "{escaped}"')
        else:
            escaped = str(value).replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"' if key in {"source_plan", "decision_summary"} else f"{key}: {escaped}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return [str(value).strip()]


def merge_unique(existing: list[str], incoming: list[str]) -> list[str]:
    out = list(existing)
    seen = set(existing)
    for item in incoming:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def inline(value: Any) -> str:
    items = normalize_list(value)
    if items:
        return "；".join(items)
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def replace_section(body: str, heading: str, new_content: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(body)
    if not match:
        raise ValueError(f"Could not find section: {heading}")
    start = match.start()
    after_start = match.end()
    next_heading = re.search(r"^##\s+", body[after_start:], re.MULTILINE)
    end = after_start + next_heading.start() if next_heading else len(body)
    replacement = f"## {heading}\n\n{new_content.strip()}\n\n"
    return body[:start] + replacement + body[end:]


def load_result(result_json: str | None, result_file: str | None, workspace: Path) -> dict[str, Any]:
    if result_json:
        return json.loads(result_json)
    if result_file:
        path = resolve_path(workspace, result_file)
        return json.loads(path.read_text(encoding="utf-8"))
    raise ValueError("Provide either --result-json or --result-file.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply acceptance result JSON to a DesignVault execution log."
    )
    parser.add_argument("--log", required=True, help="Path to the execution log markdown file.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--result-json", help="Inline JSON payload with acceptance result fields.")
    parser.add_argument("--result-file", help="Path to a JSON file with acceptance result fields.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    log_path = resolve_path(workspace, args.log)
    result = load_result(args.result_json, args.result_file, workspace)

    text = log_path.read_text(encoding="utf-8")
    frontmatter_block, body = split_frontmatter(text)
    frontmatter = parse_frontmatter(frontmatter_block)

    frontmatter["updated"] = dt.date.today().isoformat()
    frontmatter["playtest_focus"] = merge_unique(
        normalize_list(frontmatter.get("playtest_focus")),
        normalize_list(result.get("playtest_focus")),
    )
    frontmatter["risk_items"] = merge_unique(
        normalize_list(frontmatter.get("risk_items")),
        normalize_list(result.get("risks")),
    )
    frontmatter["writeback_pages"] = merge_unique(
        normalize_list(frontmatter.get("writeback_pages")),
        normalize_list(result.get("updated_pages")),
    )
    frontmatter["related"] = merge_unique(
        normalize_list(frontmatter.get("related")),
        normalize_list(result.get("updated_pages")),
    )
    frontmatter["decision_needed"] = "true" if result.get("decision_packet_needed") else "false"
    frontmatter["decision_summary"] = inline(result.get("decision_packet"))

    if result.get("acceptance_status") == "accepted":
        frontmatter["status"] = "done"

    acceptance_block = "\n".join(
        [
            f"- 机器验收结果：{inline(result.get('machine_checks'))}",
            f"- acceptance 摘要：{inline(result.get('acceptance_summary'))}",
            f"- 是否需要 decision packet：{'是' if result.get('decision_packet_needed') else '否'}",
            f"- decision packet：{inline(result.get('decision_packet'))}",
        ]
    )
    final_summary_block = "\n".join(
        [
            f"- 完成了什么：{inline(result.get('acceptance_summary'))}",
            f"- 风险项：{inline(result.get('risks'))}",
            f"- 更新页面：{inline(result.get('updated_pages'))}",
            f"- 试玩关注点：{inline(result.get('playtest_focus'))}",
        ]
    )

    body = replace_section(body, "Acceptance", acceptance_block)
    body = replace_section(body, "最终摘要", final_summary_block)

    log_path.write_text(dump_frontmatter(frontmatter) + body, encoding="utf-8", newline="\n")
    print(log_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
