# Workflow

## 核心原则

- `Wiki` 是唯一设计真相源
- `Studio` 主要服务人类阅读和推进
- `Longform` 负责设计推敲
- `Execution Plan` 负责工程实施
- `Execution Log` 负责 `/execute` 的工作历史和 handoff

## 推荐入口

- `/design`
  - 先问清楚，再走到 `longform + wiki + execution plan`
- `/execute`
  - 从一个 plan 跑到实现、验收、回写、执行日志
- `/bug`
  - 从现象出发修复实现问题；如果本质是设计问题，则回到 `/design`

## 默认工作流

`/design -> /execute -> 人类反馈需要时走 /bug`
