# Workflow

## 核心原则

- `Wiki` 是唯一设计真相源
- `Studio` 主要服务人类阅读和推进
- `Longform` 负责设计推敲
- `Execution Plan` 负责工程实施
- `Execution Log` 负责 `/execute` 的工作历史和 phase handoff
- execution state 统一放在 execution log、change review 和 dashboard 摘要里

## 推荐入口

- `/design`
  - 先 grill 提问把设计问清楚，再走到 `Longform + Wiki + Execution Plan`
- `/execute`
  - 从一个 `Execution Plan` 自动跑到实现、验收、回写、执行日志
- `/bug`
  - 从现象出发修复实现问题；如果本质是设计问题，则回到 `/design`

## 默认工作流

`/design -> /execute -> 人类反馈需要时走 /bug`

## 大任务通道

`/design -> Execution Plan -> /execute -> Acceptance Phase -> wiki writeback -> execution log`

## 小任务通道

`/bug -> 读 wiki -> 实现 -> 验证 -> 轻量写回`
