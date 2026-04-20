<%*
const today = tp.date.now("YYYY-MM-DD");
const title = tp.file.title;
_%>
---
type: change_review
status: open
updated: <% today %>
managed_by: ai
links: []
code_refs: []
figma_refs: []
---

# <% title %>

## 本次改动
<% tp.file.cursor(1) %>

## 影响到的 wiki 页面

## 机器证据

## 验收方式

## 试玩关注点

## 后续问题 / 待决策
