# DesignVault AGENTS

## Purpose

This vault separates stable truth from active working material.

- `00 Wiki/` holds current approved truth.
- `10 Studio/` holds drafts, plans, execution logs, change review, and other working pages.

## Core Rules

1. Read the smallest relevant wiki pages before changing behavior, scope, terminology, or workflow.
2. Keep unstable discussion in studio pages instead of wiki truth pages.
3. End design-affecting work by updating the wiki pages whose truth changed.
4. Keep execution state in execution logs and change review instead of page-level implementation flags.
5. Prefer one main execution plan page. Split phase pages only when handoff cost justifies it.

## Recommended Lanes

- `/design`: shape unstable design into longform, wiki truth, and one execution plan
- `/execute`: implement one approved plan, verify it, and write back truth
- `/bug`: start from an observed symptom, repair implementation, and escalate to `/design` if the problem is really design truth

## Public Maintenance Surface

- `index.md`
- `_Templates/`
- `10 Studio/Workflow.md`
- `10 Studio/规范 - Design 产物与交接.md`
- `10 Studio/规范 - Bug 产物与交接.md`
- `10 Studio/规范 - Wiki 回写与状态建议.md`
