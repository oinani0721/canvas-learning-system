---
title: "Canvas Learning System _bmad-output Vault 验收清单（3-5 分钟扫读版 / 用户自填）"
date: 2026-04-29
type: verification-checklist
total_annotations: 222
structure: "Layer 1 决策备忘录 + Layer 2 批注矩阵（按 Round 分组）+ Layer 3 未决 action + Layer 4 5 句话总结"
parent_methodology: null
goal: "回答用户'当前开发进度停在哪 + 什么关键决策需要拍板'两个核心问题，把 222 散落批注收敛成 4 个核心决策 + 4-6 个未决 action"
status: draft
scope: canvas-bmad-output
generator: "verify-vault@v1.1"
version: v1
canvas_enhancement: enabled (sprint-status.yaml + 验收单/ + 批注回复/ + research/round-N/ 全部启用)
---

# Canvas Learning System 开发进度 + 关键决策验收清单

## 使用说明（1 分钟）

1. **不要再拆新批注**。这份文档是"收敛"用的，不是"扩展"用的。
2. **扫读 AI 简答** → 在"你的理解"列写**1 句话**（强制自己用自己的话说一遍 = 主动学习）
3. **打状态**：✅ 同意 / ⏳ 部分同意 / ❌ 不同意或需要更多信息
4. **遇到想再拆的冲动**时，问自己：**"这和 D1-D4 4 个关键决策有关吗？"**——无关则直接 archive
5. **完成时间**：目标 3-5 分钟扫读 → 1-2 小时逐行填写 → **一次性收敛**

---

## Layer 1: 一页纸决策备忘录（top-level）

### 你问的两个核心问题，一句话答

> **Q1：开发进度停在哪？** Epic 1 v2 (Obsidian+Claudian 架构) 17 stories — 5 done / 1 review / 1 blocked / 10 ready-for-dev。**关键卡点 = Story 1.19 UAT 未跑**（导致 1.17 blocked 连锁）。Epic 2 (检索管道) 10/13 done 健康。Epic 3-6 全 backlog，等 Epic 1 主线打通。
>
> **Q2：什么关键决策要拍板？** 4 个 — D1 (🔥 Story 1.19 UAT 跑/不跑) / D2 (🔥 round-13 wikilink 架构 4 选 1) / D3 (⚠️ 跨白板关联功能砍/留) / D4 (⏳ 上轮 8 个 UX 决策选哪个先聊)。

### 4 个关键决策（你必须拍板）

| ID     | 决策主题                                                     | 选项                                                                              | 关键卡点                                            | 综合推荐                                                    | Deadline     |
| ------ | -------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------- | ------------ |
| **D1** | **Story 1.19 v4 配置白板 UAT 跑/不跑**                          | A 立即跑 10 步 UAT / B 先做别的                                                         | 🔥 1.17 blocked 等这个解锁；1.18 Dashboard 数据源也需要先有白板 | **A** ⭐⭐⭐⭐⭐ (解锁链上最关键)                                   | 越快越好         |
| **D2** | **round-13 wikilink 双引擎 4 选项**                           | A 启动 1.2/1.3 (~18h) / B 先 1.18 / C 细看某问 / D 跳过 spec 接 wikilink 入 fusion (~4-6h) | 🔥 决定 next 2-3 sprints 优先级                      | **A 或 D** ⭐⭐⭐⭐ (依实施偏好)                                  | 配合 D1 同步     |
| **D3** | **后端 retrieve_cross_canvas 砍/留** (round-12 line 38 你的批注) | A 砍掉（round-11 扁平后语义失效）/ B 适配新 `原白板/` 扁平结构 (~3h)                                 | round-11 之后跨白板关联含义已变                            | **B** ⭐⭐⭐⭐ (适配比砍掉更稳)                                    | 与 1.2/1.3 同步 |
| **D4** | **上轮 8 个 UX 决策**（5 立即层 + 3 未来层）                          | 选 1-2 个先聊 / 全部按推荐方案 / 还有调整                                                      | 影响 1.17/1.18/1.19 实施细节                          | 先解 #3 (Dashboard confirm 弹窗) + #4 (configure 派生原 md 处理) | TBD          |

### 4 个关键假设（多数已 ✅，1 个 🔥 待核实）

| 假设 | 当前证据 | 核实方式 | Deadline |
|---|---|---|---|
| **A1: round-11 扁平架构稳定** (`原白板/<board>.md` + `节点/<concept>.md` 扁平池 + vault 级 subject) | ✅ commit `d5c6a69` 固化 + `_bmad-output/.claude/CLAUDE.md` 已写规则 | 已核实 | ✅ done |
| **A2: Story 1.19 v4 用户能在 canvas-vault 跑通 10 步 UAT** | 🔥 ⏳ Story-1.19 spec status = review，UAT 文档已 ship 在 `验收单/Story-1.19-configure-whiteboard.md`，但用户尚未实际跑 | 你开 canvas-vault → Cmd+P → /configure-whiteboard 跑场景 A + 场景 B | TBD（D1 决定） |
| **A3: Wikilink 图 + Graphiti 双引擎共存可行** | ✅ round-12/13 论证（`research/round-12-graphiti-karpathy-5-conjectures-audit.md` + `research/round-13-wikilink-vs-graphiti-five-questions-answer.md`）+ 业界 12+ 案例 | 已论证 | ✅ done |
| **A4: subject 字段 vault 级固化（一 vault 一学科）** | ✅ round-11 决定 + `.canvas-config.yaml` schema 已定 | 已核实 | ✅ done |

### 里程碑 + 重新评估触发器

| 日期 | 里程碑 | 触发重新评估 |
|---|---|---|
| 2026-04-29 (今天) | round-13 答案 + verify-vault skill 双交付 | — |
| **TBD ↑ 关键** | **Story 1.19 v4 UAT 通过 → 解锁 1.17 → 1.18 Dashboard** | A2 假设核实 |
| TBD | 接受 round-13 推荐架构 → 启动 Story 1.2/1.3 wikilink 实施 (~18h) | D2 拍板 |
| TBD | Phase 1 完成（wikilink 接入 fusion + Graphiti search_facts 激活）| Story 1.2/1.3 done |

---

## Layer 2: 批注矩阵（按 Round 分组，仅保留待处理 + 关键已闭环代表，全量 222 中 ~180 已闭环 → Archive 候选）

**填写顺序建议**：先扫 Round-V（验收单当前热点 = 12 行）→ 再扫 Round-13（最新调研 = 4 行）→ 再扫 Round-Spec（Story spec 内嵌 = 6 行）→ 历史 Round-1~12 全部 ✅ 关闭，**直接跳过**

### Round-V 验收单（当前热点，12 行 — 你最该看的）

| ID | 批注主题 | AI 简答 | 你的理解（自填） | 状态 |
|---|---|---|---|---|
| **V-Q1** | **Story 1.19 v4 UAT 你对 v4 的批注**（line 303）| 1.19 v4 已 ship Skill + template，待你跑 10 步 UAT（场景 A 从零建 + 场景 B 从 md 派生）| ___________ | ⏳ 🔥 |
| **V-Q2** | Story 1.19 历史已修复（v3 → v4 round-9 subject/board_name 分工，line 322）| ✅ round-9 已通过 v3 修复 | ___________ | ✅ |
| **V-Q3** | Story 1.19 历史已修复（v2.1 → v3 round-8 Epic 1 顺序，line 325）| ✅ round-8 已通过顺序修正 | ___________ | ✅ |
| **V-Q4** | Story 1.17 暂挂起（line 14: 等 1.19 完成）| ✅ 已挂起（1.17 yaml status = blocked），等 D1 解锁 | ___________ | ⏳ |
| **V-Q5** | **Story 1.17 v2.1 你对 v2.1 的批注**（line 400）| 1.17 v2.1 已 correct-course，待你 D1 通过后重跑 UAT | ___________ | ⏳ 🔥 |
| **V-Q6** | Story 1.17 历史已修复（v2 → v2.1 round-9，line 408）| ✅ correct-course 已完成 | ___________ | ✅ |
| **V-Q7** | Story 1.17 历史已修复（v1 双重付费 + 双 Vault 错配，line 428/433）| ✅ v2 已修复架构偏离 | ___________ | ✅ |
| **V-Q8** | **Story 1.16 v2 你对 v2 的批注**（line 168）| Story 1.16 已 done，可关闭批注 | ___________ | ⏳ |
| **V-Q9** | Story 1.16 历史已修复（v1 严重 scope 偏离，line 176）| ✅ v2 已修复 | ___________ | ✅ |
| **V-Q10** | **Canvas 完整学习闭环 你对总验收单的批注**（line 379）| 总闭环验收单已 ship，待你跑总流程（依赖 D1 解锁）| ___________ | ⏳ |
| **V-Q11** | Canvas 完整闭环 提示快捷键（line 33 `[!tip]+`）| ✅ 文档自身指引，非批注 | — | ✅ |
| **V-Q12** | Canvas 完整闭环 类比家教（line 104 `[!tip]+`）| ✅ 文档自身比喻，非批注 | — | ✅ |

### Round-13 最新调研批注（4 行 — 你刚拍板的）

| ID | 批注主题 | AI 简答 | 你的理解（自填） | 状态 |
|---|---|---|---|---|
| R13-Q1 | round-12 line 38 你的批注："跨白板关联功能可砍掉" | round-11 扁平后跨白板含义已变；建议适配 `原白板/` 扁平不砍（**对应 D3**）| ___________ | ⏳ ⚠️ |
| R13-Q2 | round-12 line 116 你的批注："给我 10 个 Graphiti 改善意见" | ✅ Round-13 5 问回答已给 Graphiti 改善路线图（search_facts/communities/valid_at 三大未通电）| ___________ | ✅ |
| R13-Q3 | round-12 line 212 你的批注："graphify 检索精度 50% 大于吗？" | ✅ Round-13 Q1 答：分工互补不是替代；wikilink 90% 简单查询命中第 1 层 | ___________ | ✅ |
| R13-Q4 | round-12 line 265 你的批注："md+wikilink 全送 Graphiti vs LanceDB 对比" | ✅ Round-13 Q3 答：只对会变化属性进 Graphiti（mastery_score/understanding/last_reviewed）| ___________ | ✅ |

### Round-Spec Story spec 内嵌占位（6 行 — 多为待用户填的占位）

| ID | 批注主题 | AI 简答 | 你的理解（自填） | 状态 |
|---|---|---|---|---|
| RS-Q1 | Story 1.19 spec line 317 用户批注占位 | 占位符等 1.19 UAT 跑通后填 | ___________ | ⏳ |
| RS-Q2 | Story 1.18 spec line 185 用户批注占位 | 1.18 ready-for-dev，spec 占位等开工后填 | ___________ | ⏳ |
| RS-Q3 | Story 1.17 spec line 510 用户批注 v2 占位 | 等 1.17 解锁后填 | ___________ | ⏳ |
| RS-Q4 | Story 1.16 spec line 279 用户批注占位 | 1.16 已 done，可关闭 | ___________ | ✅ |
| RS-Q5 | Story 1.4 line 64 你的批注："原白板类型 + 检验白板生成精准检索" | ✅ round-11 扁平架构 + Story 1.2/1.3 wikilink 已规划 | ___________ | ✅ |
| RS-Q6 | Story 1.3 line 46 你的批注："检索定位 + Karpathy 启发" | ✅ round-12/13 已答（Karpathy 第 1 层 + Graphiti 第 2 层 + LanceDB 第 3 层）| ___________ | ✅ |

### Round-Audit + Round-1~12 (全量 ~180 行已闭环 → Archive 候选)

> 这一大段不在活跃矩阵，已通过 Round-N+1 response 文件闭环。详见 Archive 候选表。

---

## Layer 3: 未决开放问题 + 行动清单

**只列 ⏳/❌/🔥 的批注。本清单决定你"本周必须做什么"。**

| ID | 问题 | 状态 | 建议行动 | Deadline |
|---|---|---|---|---|
| **D1** | **Story 1.19 v4 UAT 跑/不跑（最关键卡点）** | 🔥 ⏳ 未跑 | **打开 canvas-vault → Cmd+P → /configure-whiteboard 跑场景 A 从零建 + 场景 B 从已有 md 派生 → 验收 10 步**（详见 `验收单/Story-1.19-configure-whiteboard.md`）| **越快越好** |
| **D2** | round-13 wikilink 双引擎 4 选项 | 🔥 ⏳ 未拍板 | 在 4 选项中选 1: A 启动 1.2/1.3 (~18h) / B 先 1.18 Dashboard / C 细看 Q1-Q5 某问 / D 跳过 spec 直接接 wikilink 入 fusion (~4-6h) | TBD（建议 D1 跑通后立即拍）|
| **D3** | retrieve_cross_canvas 砍/适配（round-12 line 38）| ⚠️ ⏳ 未决 | 拍板：A 砍（删后端代码）/ **B 适配 round-11 扁平**（推荐 ~3h 改 `state_graph.py:540-671`）| 与 D2 同步 |
| **D4** | 上轮 8 个 UX 决策选哪个先聊 | ⏳ 未挑 | 从立即层 5 项（AI 派生跳转 / 失败提示 / Dashboard confirm / 派生原 md 处理 / Dashboard metric）+ 未来层 3 项中选 1-3 个 | TBD |
| V-Q1 | Story 1.19 v4 你的批注 | ⏳ 待写 | UAT 跑通后写"通过 ✅"或具体问题 | 配合 D1 |
| V-Q5 | Story 1.17 v2.1 你的批注 | ⏳ 待 D1 解锁 | D1 通过后重跑 1.17 UAT | 配合 D1 |
| R13-Q1 | round-12 跨白板关联砍/留 | ⚠️ 待决 | 等同 D3 | 配合 D3 |

### Archive 候选（不删，但不计入当前框架，~180 行）

| 类别 | 数量 | 原因 |
|---|---|---|
| review/epic-1-audit-* + audit-response-round-2/3/4 系列 | ~50 行 `[!question]+` 占位 | Round-2/3/4 response 文档已闭环；批注占位为历史协作机制，非待决 |
| research/obsidian-qa-round1~12-* 系列 | ~80 行 `**User：**` 历史问答 | 每个 Round 都已通过 round-N+1 reply 闭环 |
| research/canvas-crossdiscipline-tags-v1.md + obsidian-translation-qa-* | ~25 行 | 已通过 round-7/8 重设计闭环 |
| planning-artifacts/prd.md + recovered/ | ~5 行 `[!question]+` 引用 | 是 PRD 设计参考，非用户批注 |
| templates/uat-sheet-template.md + .claude/CLAUDE.md 的 `[!question]+` | ~10 行 | 模板/约定文档，非批注 |
| Story-1.16/1.17/1.18/1.19 的历史 `[!error]+ v{N} → v{N+1} 修复` | ~10 行 | 已通过 correct-course 闭环（V-Q3/V-Q6/V-Q7/V-Q9）|

---

## Layer 4: 5 句话框架总结（用户自填 = 认知收敛）

**完成 Layer 2 + Layer 3 扫读后，用下面 5 句话总结。如果能脱口而出，说明 framework 已稳定。**

1. **核心决策**：我选择 ____________（D1 立即跑 1.19 UAT / D2 选哪个选项 / 其他），因为 ____________ （一句话理由）。

2. **关键约束**：我现在的瓶颈是 ____________（A2 1.19 UAT 没跑 → 1.17 连锁 blocked / D2 wikilink 路线没定 / 其他）。

3. **下一步行动**（本周内）：____________ （1 件最重要的事，写具体动作 — 例："打开 canvas-vault 跑 1.19 UAT 10 步"）。

4. **风险识别**：我最担心的是 ____________（1 个最大风险）；我的 plan B 是 ____________ 。

5. **时间截点**：我必须在 ________ 年 __ 月 __ 日前决定 ____________（具体决策内容 — 例："2026-05-05 前完成 D1 1.19 UAT + D2 wikilink 路线拍板"）。

---

## 你可能感觉到的认知变化（填完这份文档后）

- ✅ 3 分钟内讲清"Canvas 当前 17 stories 的进度 + 1 个连锁卡点（1.19 UAT）"
- ✅ 4 个关键决策 D1-D4 的优先级脱口而出（D1 🔥 解锁链最关键 / D2 🔥 next 2-3 sprints 优先级 / D3 ⚠️ 配套 / D4 ⏳ UX 细节）
- ✅ 遇到新批注，能快速判断"这是 D1-D4 决策关键还是支撑细节？"→ 后者直接 archive
- ✅ 对"222 个批注"的焦虑消失（已收敛到 12 + 4 + 6 = 22 行活跃 + ~180 外部存储）

---

## 遇到"想拆新批注"的冲动时（重要 anti-pattern）

**问自己 3 个问题**：

1. **这个新问题和 D1-D4 4 个关键决策直接相关吗？**
   - 有关 → 在现有 22 行内找最相关那行，**在该行深化**（不是新建批注）
   - 无关 → 直接 archive（写到 Archive 候选列表，不处理）

2. **这个问题可以在 Layer 3 action 里用"发 1 句指令给 Claude / 跑一次 UAT"解决吗？**
   - 可以 → 写到 Layer 3 行动清单，不写成批注
   - 不可以 → 才考虑新建批注（但 99% 情况可以）

3. **如果不回答这个问题，我还能做 D1-D4 决策吗？**
   - 能 → 不是 blocker，archive
   - 不能 → 它就是 A1-A4 关键假设之一，放到 Layer 1 假设表

---

**文档结束**。生成于 2026-04-29 23:26 · verify-vault@v1.1（首版 v1）· Canvas 增强模式 enabled · 总扫描 222 命中 / Layer 2 活跃 22 行 / Archive 候选 ~180 行
