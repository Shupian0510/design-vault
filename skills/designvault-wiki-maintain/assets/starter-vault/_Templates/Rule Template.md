<%*
const today = tp.date.now("YYYY-MM-DD");
const title = tp.file.title;
const coreName = title.replace(/^规则 - /, "");
_%>
---
type: rule
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

## 目的
<% tp.file.cursor(1) %>

## 触发条件

## 数据流

## 规则

## 例外

## 当前实现线索

## 相关页面
