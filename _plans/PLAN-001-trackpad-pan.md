---
doc_type: plan
plan_id: "PLAN-001"
title: "Trackpad 触控板双指平移"
status: planned
prd_sections: ["§1"]
frs: ["FR-KG-03"]
mvp_items: ["#1"]
change_id: "trackpad-pan-support"
created: 2026-04-10
updated: 2026-04-10
---

# PLAN-001 · Trackpad 触控板双指平移

> **PRD**: §1 (原白板前端设计) | **Status**: planned

## PRD 来源

> **From PRD**: §1 [12 个学习设计的"效应量 + 等价实现"] (line 116-904)
> FR-KG-03: 拖拽/缩放(10%-500%)/平移 <16ms

相关代理笔记: [[PRD14-S01]]

## 目标

macOS 触控板用户可以用双指滑动平移白板，Ctrl/Cmd+捏合缩放，同时不影响现有鼠标交互。

## 步骤

- [ ] Step 1: 修改 `frontend/src/App.tsx` 的 ReactFlow props — `panOnScroll={true}` + `zoomOnScroll={false}`
- [ ] Step 2: 验证触控板平移/缩放 + 鼠标中键拖拽 + Shift 框选均正常

## 验收标准（用户操作级别）

1. 打开应用 → 在白板上用触控板双指上下/左右滑动 → 白板跟随平移
2. Ctrl/Cmd + 触控板捏合 → 白板缩放
3. 鼠标中键/右键拖拽 → 仍然可以平移（不受影响）
4. Shift + 拖拽 → 仍然可以框选

## 关联

- **OpenSpec Change**: `trackpad-pan-support`
- **验收记录**: [[VER-001-trackpad-pan]]
- **反馈**: _待验收后补充_

## 用户批注区

<!-- 用户在此添加批注 -->
