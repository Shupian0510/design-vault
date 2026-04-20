<%*
const today = tp.date.now("YYYY-MM-DD");
const title = tp.file.title;
_%>
---
type: todo
status: open
updated: <% today %>
owner_role: personal
priority: rolling
links: []
---

# <% title %>

## 现在要做

- [ ] <% tp.file.cursor(1) %>

## 接下来

- [ ] 

## 等待确认

- [ ] 

## 随手记

- 

## 已完成

- [x] 新建页面
