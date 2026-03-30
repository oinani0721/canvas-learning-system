---
name: S27 路径A确认 — 先打通管道再打磨体验
description: 用户确认开发路径A：Phase1启动验证→Phase2 Graphiti迁移→Phase3管道修复→Phase4 UI打磨（2026-03-25）
type: project
---

## [Decision] 开发路径 A — 先打通管道再打磨体验

Session: S27 | 日期: 2026-03-25

**选择**: 路径 A（自底向上）
**否决**: 路径 B（自顶向下/体验驱动）

**理由**: Agent 记忆系统是多项功能的根基（写入检索、RAG、笔记搜索都依赖它）。先修基础设施效率更高。

**执行顺序**:
1. Phase 1: 启动验证（docker + tauri dev，逐项验证 14 项）
2. Phase 2: 打通 Agent 记忆（照搬 Gemini API + 6Phase Graphiti 迁移）
3. Phase 3: 修复管道断裂（sidecar验证 + 笔记索引 + Dashboard + Profile闭环）
4. Phase 4: UI 对齐 + 体验打磨

**Why:** 基础设施先到位，后续功能自然串通。Gemini API 阻塞已解除（用户说照搬 Claude Code 的配置）。
**How to apply:** 后续 session 按 Phase 顺序执行，每个 Phase 完成后用户验收。

**决策状态: [Decision-Review] PENDING — 待验证: Phase划分合理性 + 预估工时准确性 + 依赖链正确性**
