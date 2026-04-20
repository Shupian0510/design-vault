---
type: source_note
status: reference
updated: 2026-04-20
managed_by: ai
links:
  - "[[10 Studio/Workflow]]"
---

# 规范 - Wiki 回写与状态建议

## 核心原则

- wiki 负责设计真相
- execution log 负责执行状态
- change review 负责实现偏差与收口说明

## 回写规则

- 改动真的改变了设计真相，就更新 wiki
- 只是实现细节调整而 truth 没变，可以不改 wiki
- 代码改动后，应自动建议可能受影响的 wiki 页面
