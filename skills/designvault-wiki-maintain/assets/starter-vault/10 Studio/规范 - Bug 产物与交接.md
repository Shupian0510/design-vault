---
type: source_note
status: reference
updated: 2026-04-20
managed_by: ai
links:
  - "[[10 Studio/Workflow]]"
---

# 规范 - Bug 产物与交接

`/bug` 是独立通道，不是缩小版 `/execute`。

## 正常输出

- 修复结果
- 机器验证结果
- 必要的 wiki 更新建议
- execution log 中的追加记录

## 升级到 `/design`

如果确认不是实现 bug，而是设计不清楚或互相矛盾，就不要继续硬修。  
此时返回一个短的设计修正包，然后回到 `/design`。
