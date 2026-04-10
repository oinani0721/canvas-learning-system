---
doc_type: feedback
fb_id: "FB-<% tp.file.cursor(1) %>"
source_plan: "PLAN-<% tp.file.cursor(2) %>"
source_ver: "VER-<% tp.file.cursor(3) %>"
severity: "<% tp.system.suggester(['critical', 'high', 'medium', 'low'], ['critical', 'high', 'medium', 'low']) %>"
status: open
created: <% tp.date.now("YYYY-MM-DD") %>
resolved_date: ""
---

# <% tp.frontmatter.fb_id %> · 问题反馈

> **来源**: [[<% tp.frontmatter.source_plan %>]] → [[<% tp.frontmatter.source_ver %>]]
> **严重程度**: <% tp.frontmatter.severity %> | **状态**: <% tp.frontmatter.status %>

## 问题描述

_具体描述用户在验收时发现的问题_

## 复现步骤

1. ___
2. ___
3. 预期: ___ / 实际: ___

## 追踪链

- **PRD §**: [[PRD14-§___]]
- **Plan**: [[<% tp.frontmatter.source_plan %>]]
- **验收**: [[<% tp.frontmatter.source_ver %>]]
- **修复 Commit**: ___
- **修复 Plan**: [[PLAN-___]]

## 解决方案

_待填写_

## 用户批注区

<!-- 用户在此添加批注 -->
