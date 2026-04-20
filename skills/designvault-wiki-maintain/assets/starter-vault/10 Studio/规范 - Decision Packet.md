---
type: source_note
status: reference
updated: 2026-04-20
managed_by: ai
links:
  - "[[10 Studio/目标工作流 - 三入口自动执行工作流]]"
---

# 规范 - Decision Packet

`decision packet` 是 `/execute` 或 `/bug` 在必须停机时返回给人类的最小决策包。

## 使用时机

- `plan / wiki` 语义不一致
- 资源接线、scene、prefab 或 editor wiring 不确定
- bug 排查后确认根因是设计问题
- `Acceptance Phase` 发现偏差，且不能静默修复

## 固定字段

- `problem`
- `why_stop`
- `recommended_fix`
- `affected_truth`

## 可选字段

- `fallback_option`
- `recommended_next_command`

## 规则

- 默认只在线程里返回，不单独落页
- 描述要短，只给足够判断的信息
- 不用重格式化成人类报告
- 如果问题很多，优先合并成一个可决策的包
