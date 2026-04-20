#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from extract_phase_packet import build_packet, resolve_plan_path, render_markdown


PHASE_HEADING_RE = re.compile(r"^###\s+Phase\s+(\d+)\s*-\s*(.+?)\s*$")
HANDOFF_PREFIXES = {
    "- 完成摘要：": "changed",
    "- 未改动：": "left_unchanged",
    "- tests：": "tests_run",
    "- 风险：": "risks",
    "- 设计保留 / 修改原因：": "design_reasoning",
    "- 写回页面：": "writeback_pages",
    "- 下一 phase 注意点：": "next_phase_watchouts",
}


def resolve_path(workspace: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = workspace / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")
    return path


def extract_previous_handoff(log_path: Path, phase_number: int) -> dict[str, str] | None:
    previous_phase = phase_number - 1
    if previous_phase < 1:
        return None

    lines = log_path.read_text(encoding="utf-8").splitlines()
    start_idx = None
    end_idx = None

    for idx, line in enumerate(lines):
        match = PHASE_HEADING_RE.match(line.strip())
        if match and int(match.group(1)) == previous_phase:
            start_idx = idx + 1
            continue
        if start_idx is not None and (PHASE_HEADING_RE.match(line.strip()) or line.strip().startswith("## ")):
            end_idx = idx
            break

    if start_idx is None:
        return None
    if end_idx is None:
        end_idx = len(lines)

    handoff: dict[str, str] = {}
    for raw in lines[start_idx:end_idx]:
        stripped = raw.strip()
        for prefix, key in HANDOFF_PREFIXES.items():
            if stripped.startswith(prefix):
                handoff[key] = stripped[len(prefix) :].strip()
                break

    return handoff or None


def render_handoff(handoff: dict[str, str] | None) -> str:
    if not handoff:
        return "- 无上一 phase handoff。当前 phase 直接从 plan packet 启动。"

    ordered = [
        ("changed", "完成摘要"),
        ("left_unchanged", "未改动"),
        ("tests_run", "tests"),
        ("risks", "风险"),
        ("design_reasoning", "设计保留 / 修改原因"),
        ("writeback_pages", "写回页面"),
        ("next_phase_watchouts", "下一 phase 注意点"),
    ]
    lines: list[str] = []
    for key, label in ordered:
        value = handoff.get(key, "")
        lines.append(f"- {label}：{value or '无'}")
    return "\n".join(lines)


def build_prompt(packet: dict[str, object], previous_handoff: dict[str, str] | None) -> str:
    return f"""你现在作为 DesignVault /execute 的单 phase 执行子代理工作。

只处理一个 phase。
不改设计。
不扩到后续 phase。
不并行。

执行约束：
- phase packet 提供的是最小保证上下文，不是思考上限。
- 先读取 phase packet 指定的 truth、代码和编辑器/资源上下文。
- 如果为了把当前 phase 做对，需要再看紧邻的本地代码、相邻 wiki truth 或直接相关的编辑器/资源上下文，可以自己继续查，但不能借此扩到后续 phase 或擅自改设计。
- 把 implementation plan 当作执行合同，不当第二设计源。
- 小范围实现与测试失败可以自修。
- `plan / wiki` 语义不一致、资源/编辑器 wiring 不确定、或任务本质已变成设计问题时，必须停止并回主线程。
- 你的工作能力应等同于一次单独开的高质量执行线程。限制的是 phase 边界，不是你的推理深度。

正式完成时必须保留这些 handoff 字段：
- changed
- left_unchanged
- tests_run
- risks
- writeback_pages
- design_reasoning
- next_phase_watchouts

如果当前任务只是只读预演，也要按同一思路返回风险与停机点。

最终只返回一个 JSON 对象。
不要加 Markdown code fence。
不要加解释文字。
不要返回 JSON 以外的任何内容。

{render_markdown(packet)}

## Previous Phase Handoff

{render_handoff(previous_handoff)}
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render the standard DesignVault phase-worker prompt from one implementation-plan phase."
    )
    parser.add_argument("--plan", required=True, help="Path to the implementation plan markdown file.")
    parser.add_argument("--phase", required=True, type=int, help="Phase number to render.")
    parser.add_argument("--log", help="Optional execution log path for reading the previous phase handoff.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    plan_path = resolve_plan_path(workspace, args.plan)
    packet = build_packet(plan_path, args.phase)
    previous_handoff = None
    if args.log:
        log_path = resolve_path(workspace, args.log)
        previous_handoff = extract_previous_handoff(log_path, args.phase)
    print(build_prompt(packet, previous_handoff))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
