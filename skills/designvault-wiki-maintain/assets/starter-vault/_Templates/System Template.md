<%*
const today = tp.date.now("YYYY-MM-DD");
const title = tp.file.title;
const coreName = title.replace(/^系统 - /, "");
_%>
---
type: system
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

## 玩家可见表现

## 核心规则

## 输入

## 输出

## 与其他系统关系

## 当前实现约束

## 当前实现线索

## 未决问题
