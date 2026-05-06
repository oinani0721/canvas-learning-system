---
title: "Canvas Next Steps — 用户接受推荐后的 BMAD 工作流 + 个人验收清单"
date: 2026-04-30
type: action-plan
parent: vault-status-2026-04-30-v3.md
status: ready-for-execution
generator: "verify-vault@v1.3 + AI 回复用户批注"
---

# Next Steps · 2026-04-30 · 用户接受推荐后的执行路径

## Context

用户在 [[vault-status-2026-04-30-v3#Layer 3|v3 Layer 3]] 批注 line 131：
> "按照你的决策推动，这些决策我需要实际使用过才知道实际的效果。BMAD 开发是否需要编辑成 Story？个人需要验收什么？"

→ **9 个 UX 决策全部接受推荐方案**，AI 自动落地到 BMAD spec + 用户跑 UAT 验收。

---

## Q1 答 · "用过才知道效果" — 边跑边验顺序

**核心原则**：每跑完一个 Story 的 UAT，立刻能验下一组 UX 决策是否真好用。如果不好用，**用 `bmad-bmm-correct-course` 调整**（无成本）。

| 顺序 | Story | 验收的 UX 决策 | 你做啥 |
|---|---|---|---|
| **1** 🔥 | Story 1.19 v4（已 review，待跑 UAT） | **D1**（UAT 12 步通过）+ **D4-4**（派生原 md 复制保留 — 跑场景 B 时能感知）| 打开 canvas-vault → Cmd+P → /configure-whiteboard → 跑场景 A + B |
| **2** | Story 1.17 v2.1（D1 通过后解锁）| **D4-1**（toast 不打断阅读） + **D4-2**（toast + 重试按钮） | Cmd+Shift+D 派生节点 → 感受是 toast 还是跳 tab 体验更好 |
| **3** | Story 1.18 Dashboard（开工后） | **D4-3**（confirm 弹窗 vs 直跳）+ **D4-5**（mastery+节点数+FSRS 到期 3 指标够不够）| 打开 dashboard.md → 点一键考察按钮 → 看弹窗 / 看指标卡片 |
| **4-6** | Phase 1-3（未来 Story 3+/6+）| **D4-6**（hover 标来源）+ **D4-7**（仅未同步提示）+ **D4-8**（Dashboard 卡片不打断）| 远期决策，先记不动代码 |

**回退机制**：跑完 Step 1-3 任一发现不好 → 立刻说"D4-X 改成 B/C 选项" → AI 用 correct-course 调整 spec + 重新 ship。

---

## Q2 答 · BMAD 工作流 — 不需要新建 Story

### 现状：4 个 MVP Story 都已有 spec

| Story | 文件 | 当前 status | 关联 UX 决策 |
|---|---|---|---|
| **1.16** 批注 hotkey | [[1-16-annotate-callout-hotkey]] | ✅ done | — |
| **1.17** AI 双链 | [[1-17-ai-linked-doc]] | ⏸ blocked（等 1.19）| D4-1 / D4-2 |
| **1.18** Dashboard | [[1-18-dashboard-md-mvp]] | ⏳ ready-for-dev | D4-3 / D4-5 |
| **1.19** 配置白板 | [[1-19-configure-whiteboard-skill]] | ⏳ review（待跑 UAT）| D1 / D4-4 |

### 我（AI）会自动做

**第 1 步（用户跑 D1 UAT 之前 / 之后均可）**：
- 用 `bmad-bmm-correct-course` patch Story 1.17 spec：在 Tasks 段加 D4-1（toast 不打断 spec）+ D4-2（toast + 重试 spec）
- 用 `bmad-bmm-correct-course` patch Story 1.18 spec：加 D4-3 confirm 弹窗 + D4-5 三个指标
- Story 1.19 spec 已含 D4-4 复制保留（场景 B 步骤），不需改

**第 2 步（D2/D3 TECH 决策落地）**：
- D2 → 启动 Story 1.2 + 1.3 wikilink 实施（~18h）
- D3 → 改 `state_graph.py:540-671` 适配 `原白板/` 扁平 (~3h)
- 这两个**不需要你拍板**，等你说"启动 D2 / D3" 我开始

**第 3 步（远期 D4-6/7/8）**：
- 现在只**记录决策**到 [[vault-status-2026-04-30-v3]]，不动代码
- Phase 1-3 实际开工时（Story 3+ / 6+），spec 创建时 inherit 这些决策

### 你（用户）只需说

| 你说 | 我做 |
|---|---|
| "我跑完 1.19 UAT 通过了" | 1.19 mark done + unblock 1.17 + ship 1.18 spec patch（含 D4-3/5）|
| "1.19 UAT 第 X 步失败" | 用 correct-course 修 + ship v5 重跑 |
| "启动 1.17" | dev 1.17 v2.1 + 用 D4-1/D4-2 spec patch |
| "启动 D2 / D3" | dev Story 1.2/1.3 + patch state_graph.py |
| "D4-X 推荐方案不好，改 Y" | correct-course 调整决策 + 重新 ship 受影响 spec |

---

## Q3 答 · 个人验收清单 — 4 份 UAT Sheet 已 ship

### 当前最关键：D1 跑 Story 1.19 v4 UAT

**位置**：`_bmad-output/验收单/Story-1.19-configure-whiteboard.md`

**12 步 UAT 概览**（详细在 sheet 里）：
- **P1-P4 前置**：vault 配置 / Skill 加载 / 命令面板可见 / SKILL.md 触发词识别
- **场景 A 从零建** (步 1-6)：`/configure-whiteboard "测试白板"` → 检查 `原白板/测试白板.md` 创建 + frontmatter + ## Concepts section + .canvas-config.yaml subject
- **场景 B 从已有 md 派生** (步 7-12)：`/configure-whiteboard from <md-path>` → 检查派生白板 + 原 md 复制保留（**对应 D4-4**）+ wikilink 自动重定向
- **中文编码 QA**：4 个测试（Bash mkdir / Graph View filter `path:原白板/` / wikilink `[[原白板/...]]` / Dataview `FROM "原白板"`）

**通过判定**：12 步全 ✅ → mark done → 解锁 1.17 / 1.18

### 其他 UAT Sheet（按 Story 顺序跑）

| Sheet | 跑的时机 | 步骤数 |
|---|---|---|
| [[Story-1.19-configure-whiteboard]] 🔥 | **现在** | 12 步 |
| [[Story-1.17-ai-linked-doc]] | D1 通过后 | 14 步 |
| [[Story-1.18-dashboard-md-mvp]]（待 ship）| 1.18 开工后 | 5 步 |
| [[Canvas-完整学习闭环-验收总流程-2026-04-20]] | 1.16+1.17+1.19 都 done 后 | 端到端总流程 |

### 你跑 UAT 的方法（统一）

1. 在 obsidian 打开对应 sheet
2. 跑每一步操作（按 sheet 描述）
3. 勾 `- [x]` checkbox 通过 / 用 Cmd+Shift+A 加 `[!error]+` callout 标失败
4. 全 ✅ → 告诉我 "Story X.Y UAT 通过"
5. 任一 ❌ → 我用 correct-course 修

---

## 立即下一步（你只做这 1 件事）

**打开 obsidian** → 切到 canvas-vault → 按 `Cmd+P` 打开命令面板 → 输入 `/configure-whiteboard "我的第一个白板"` → 跑场景 A 的 6 步 → 然后跑场景 B 的 6 步 → 全 ✅ 告诉我 "1.19 UAT 通过"。

**预期时间**：30 分钟（含中文编码 QA 4 步）。

完成后我立即启动 Story 1.17 dev（含 D4-1/D4-2 patch）+ ship Story 1.18 spec（含 D4-3/D4-5 patch）。

---

**文档结束**。生成于 2026-04-30 · 关联 [[vault-status-2026-04-30-v3]] line 131 用户批注的 AI 回复
