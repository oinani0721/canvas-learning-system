---
doc_type: verification
ver_id: "VER-<% tp.file.cursor(1) %>"
plan_id: "PLAN-<% tp.file.cursor(2) %>"
status: pending
tester: ""
date: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.frontmatter.ver_id %> · 验收记录

> **Plan**: [[<% tp.frontmatter.plan_id %>]] | **Status**: <% tp.frontmatter.status %>

## 操作步骤

| # | 操作 | 预期结果 | 实际结果 | 通过 |
|---|------|---------|---------|------|
| 1 | ___ | ___ | ___ | [ ] |
| 2 | ___ | ___ | ___ | [ ] |
| 3 | ___ | ___ | ___ | [ ] |

## 环境

- OS: ___
- 启动方式: `npm run tauri dev` / 其他
- 后端: `docker compose up -d` + `uvicorn`

## 发现的问题

_无 / 链接到 [[FB-NNN]]_

## 结论

- [ ] **全部通过** → Plan 标记 `verified`
- [ ] **部分通过** → 记录问题，Plan 保持 `in-progress`
- [ ] **未通过** → 创建反馈 [[FB-___]]，Plan 回退

## 用户批注区

<!-- 用户在此添加批注 -->
