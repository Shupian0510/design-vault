---
type: source_note
status: reference
updated: 2026-04-20
managed_by: ai
links:
  - "[[10 Studio/目标工作流 - 三入口自动执行工作流]]"
  - "[[10 Studio/Home]]"
---

# 规范 - Dashboard 信息架构

Dashboard 只放人类真正需要看的东西。

## 四块固定信息

### 1. 最近完成

- 做完了什么
- 对应哪个 plan / execution log

### 2. 待我试玩

- 功能
- 你该看什么
- 可能的风险

### 3. 待决策

- `decision packet`
- repair loop 选择点
- 需要人类拍板的 design mismatch

### 4. 最近回写

- 最近更新了哪些 wiki / 文档
- 这些改动来自哪个 feature 或 bug 修复

## 不该放什么

- 原始 phase handoff
- 大段执行过程
- 冗长测试输出
- 旧的 page-level verify 勾选
