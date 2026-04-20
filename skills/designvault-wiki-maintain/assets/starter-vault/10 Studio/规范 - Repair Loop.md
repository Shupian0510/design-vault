---
type: source_note
status: reference
updated: 2026-04-20
managed_by: ai
links:
  - "[[10 Studio/目标工作流 - 三入口自动执行工作流]]"
---

# 规范 - Repair Loop

`Repair Loop` 是 `/execute` 在 `Acceptance Phase` 之后的修正闭环。

## 基本规则

- 先做 `Acceptance Phase`
- 发现偏差时先生成 `decision packet`
- 人类确认后，只生成一个新的 `Repair Packet`
- 修正完成后，只重跑受影响的验收部分
- 如果修正再次暴露偏差，允许继续进入下一轮 `Repair Loop`

## Repair Packet

`Repair Packet` 不是新的大 plan。

它只说明：

- 要修什么偏差
- 受影响的 truth / code / asset 范围
- 需要补跑哪些验证
- 修完后回到哪一段 acceptance

## 什么时候不该继续 repair

- 问题已经升级成设计重构
- repair 范围已经接近一个新 feature
- 当前 plan 已不足以描述后续工作

这时应停下来，回到 `/design`。
