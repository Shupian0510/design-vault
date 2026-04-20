<%*
const today = tp.date.now("YYYY-MM-DD");
const title = tp.file.title;
_%>
---
type: idea
status: backlog
updated: <% today %>
priority: human-set
links: []
notes: ""
---

# <% title %>

## 核心想法
<% tp.file.cursor(1) %>

## 为什么值得考虑

## 与当前游戏的匹配度

## 可能问题

## 相关 wiki 页面
