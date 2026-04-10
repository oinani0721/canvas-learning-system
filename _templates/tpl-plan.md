---
doc_type: plan
plan_id: "PLAN-<% tp.file.cursor(1) %>"
title: "<% tp.file.cursor(2) %>"
status: planned
prd_sections: ["<% tp.file.cursor(3) %>"]
frs: []
mvp_items: []
change_id: ""
created: <% tp.date.now("YYYY-MM-DD") %>
updated: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.frontmatter.plan_id %> · <% tp.frontmatter.title %>

> **PRD**: <% tp.frontmatter.prd_sections %> | **Status**: <% tp.frontmatter.status %>

## PRD 来源

> **From PRD**: §___ [标题] (line ___-___)

相关代理笔记: [[PRD14-§___]]

## 目标

_一句话描述此 Plan 要达成的用户可感知成果_

## 步骤

- [ ] Step 1: ___
- [ ] Step 2: ___
- [ ] Step 3: ___

## 验收标准（用户操作级别）

1. 打开应用 → ___
2. 操作 → ___
3. 看到 → ___

## 关联

- **OpenSpec Change**: `<% tp.frontmatter.change_id %>`
- **验收记录**: [[VER-<% tp.file.cursor(4) %>]]
- **反馈**: _待验收后补充_

## 用户批注区

<!-- 用户在此添加批注 -->
