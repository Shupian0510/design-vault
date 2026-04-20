<%*
const today = tp.date.now("YYYY-MM-DD");
const title = tp.file.title;
const coreName = title.replace(/^概念 - /, "");
_%>
---
type: concept
status: draft
updated: <% today %>
managed_by: ai
keywords:
  - <% coreName %>
player_questions: []
code_refs: []
figma_refs: []
source_notes: []
related: []
---

# <% title %>

## 一句话定义
<% tp.file.cursor(1) %>

## 作用

## 触发条件

## 状态与数据

## 关键规则

## 边界与例外

## 当前实现线索

## 相关页面
