<%*
const today = tp.date.now("YYYY-MM-DD");
const title = tp.file.title;
_%>
---
type: todo
status: open
updated: <% today %>
owner_role: design
priority: human-set
links: []
---

# <% title %>

## 目标
<% tp.file.cursor(1) %>

## 输入材料

## 需求说明

## 验收标准

## 相关 wiki 页面
