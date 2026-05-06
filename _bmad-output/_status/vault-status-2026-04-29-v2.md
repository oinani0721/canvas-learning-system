---
title: "Canvas Learning System _bmad-output Vault 验收清单 v2（含具体决策摘要 + wikilink 跳转）"
date: 2026-04-29
type: verification-checklist
total_annotations: 222
structure: "Layer 1 决策备忘录（含跳转）+ Layer 2 批注矩阵（6 列含摘要+wikilink）+ Layer 3 未决 action（含摘要+wikilink）+ Layer 4 5 句话总结"
parent_methodology: null
goal: "v1 → v2 升级 — 每个决策/批注/action 必带 30-60 字摘要 + [[wikilink]] 跳转，用户能 Cmd+Click 直跳原文"
status: draft
scope: canvas-bmad-output
generator: "verify-vault@v1.2 (wikilink+excerpt strict)"
version: v2
canvas_enhancement: enabled
prev_version: vault-status-2026-04-29-v1.md
upgrade_reason: "用户反馈 v1 决策主题太抽象（'Story 1.19 v4 UAT 跑/不跑'），不知道决策啥；v2 强制每行带具体内容摘要 + wikilink 跳转"
---

# Canvas Learning System 开发进度 + 关键决策验收清单 v2

## 使用说明（1 分钟）

1. **不要再拆新批注**。这份文档是"收敛"用的，不是"扩展"用的。
2. **扫读 AI 简答 + 批注摘要列** → 在"你的理解"列写 1 句话
3. **打状态**：✅ 同意 / ⏳ 部分同意 / ❌ 不同意或需要更多信息
4. **Cmd+Click wikilink** 直跳原文位置（无需再翻文件）
5. **完成时间**：3-5 分钟扫读 → 1-2 小时填写 → 一次性收敛

---

## Layer 1: 一页纸决策备忘录

### 你问的两个核心问题，一句话答

> **Q1：开发进度停哪？** Epic 1 v2: 5 done / 1 review / 1 blocked / 10 ready-for-dev。**关键卡点 = Story 1.19 v4 UAT 你还没跑** → 1.17 blocked + 1.18 数据源缺白板。Epic 2: 10/13 done。Epic 3-6: 全 backlog 等 Epic 1 主线。
>
> **Q2：什么决策待拍板？** 4 个 — D1🔥 / D2🔥 / D3⚠️ / D4⏳（详见下表，**点击 wikilink 看原文**）

### 4 个关键决策（含具体内容 + 跳转）

| ID | 决策具体内容（30-60 字） + 跳转 | 选项 ABC 具体含义 | 综合推荐 | Deadline |
|---|---|---|---|---|
| **D1** 🔥 | **Story 1.19 v4 UAT 跑/不跑** [[Story-1.19-configure-whiteboard\|📍 D1 @line101-242]]<br>用户跑完 12 步 UAT（含 P1-P4 前置 + 中文编码 QA + 场景 A 从零建 + 场景 B 从已有 md 派生），需回答：全通过 ✅ / 中文编码失败降级英文 / 其他诊断（A/C/D）❌。当前 1.17 等这个解锁。 | **A** 全通过 → 1.19 mark done → unblock 1.17<br>**B** 诊断 B（中文编码失败）→ 降级英文方案重跑<br>**C/D** 部分失败 → 针对诊断 fix | **A** ⭐⭐⭐⭐⭐<br>(解锁链最关键) | 越快越好 |
| **D2** 🔥 | **round-13 wikilink 双引擎 4 选项** [[round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29\|📍 D2 @line348-372]]<br>Q5 推荐架构 4 种工作量权衡：A=启动 Story 1.2+1.3 (~18h, wikilink-graph-build+context-assembly) / B=同时激活 Graphiti search_facts (+3h) / C=激活 entity_types (+2h) / D=接 wikilink 入 fusion (+4-6h)。决定 next 2-3 sprints 优先级。 | **A** 短期 18h: 1.2/1.3 wikilink<br>**B** +3h: Graphiti API 自动选<br>**C** +2h: entity_types 通电<br>**D** +4-6h: 第 6 通道 RRF 融合 | **A 或 D** ⭐⭐⭐⭐<br>(依实施偏好) | 配合 D1 同步 |
| **D3** ⚠️ | **retrieve_cross_canvas 砍/适配** [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 D3 @line38]]<br>round-11 扁平后跨白板含义已变。原 state_graph.py:540-671 第 4 通道（5-way fusion 中之一）要么砍掉降为 4-way，要么改成读 `原白板/<board>.md` 扁平结构。 | **A** 砍掉（删 state_graph.py:605-614）<br>**B** 适配（改读 `原白板/` 目录，~3h） | **B** ⭐⭐⭐⭐<br>(适配比砍稳) | 与 D2 同步 |
| **D4** ⏳ | **上轮 8 个 UX 决策** (见本文档底部 §UX 详单)<br>立即层 5 项（影响 1.17/1.18/1.19 实施）：①AI 派生跳转方式 ②派生失败提示 ③Dashboard confirm 弹窗 ④configure 派生原 md 处理 ⑤Dashboard metric 选哪些；未来层 3 项（影响 Phase 1-3）：⑥检索来源标注 ⑦同步状态提示 ⑧错误模式发现。 | 选 1-2 个先聊 / 全部按推荐 / 还要调整 | 先解 ③ + ④<br>(影响 D1 配套) | TBD |

### 4 个关键假设

| 假设 | 当前证据 + 跳转 | 核实方式 | Deadline |
|---|---|---|---|
| **A1**: round-11 扁平架构稳定 | ✅ commit `d5c6a69` 固化 + [[CLAUDE\|📍 _bmad-output/.claude/CLAUDE.md vault 扁平架构段]] | 已核实 | ✅ done |
| **A2** 🔥: Story 1.19 v4 用户能跑通 10 步 UAT | ⏳ Story-1.19 status=review，UAT 文档已 ship，**用户尚未跑** | [[Story-1.19-configure-whiteboard\|📍 跑场景 A+B 12 步]] | TBD（D1 决定） |
| **A3**: Wikilink + Graphiti 双引擎共存可行 | ✅ [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 round-12]] + [[round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29\|📍 round-13]] 双调研 + 12+ 业界案例 | 已论证 | ✅ done |
| **A4**: subject 字段 vault 级固化 | ✅ round-11 决定 + `.canvas-config.yaml` schema | 已核实 | ✅ done |

### 里程碑

| 日期 | 里程碑 | 触发重新评估 |
|---|---|---|
| 2026-04-29 | round-13 答案 + verify-vault skill v1.2 + 本 v2 文档 | — |
| **TBD ↑ 关键** | **Story 1.19 v4 UAT 通过 → 解锁 1.17 → 1.18 Dashboard** | A2 假设核实 |
| TBD | 接受 round-13 推荐 → 启动 Story 1.2/1.3 wikilink (~18h) | D2 拍板 |
| TBD | Phase 1 完成（wikilink 接入 fusion + Graphiti search_facts 激活）| Story 1.2/1.3 done |

---

## Layer 2: 批注矩阵（6 列含摘要 + wikilink）

**填写顺序**：Round-V 验收单（12 行 — 你最该看的）→ Round-13 调研（4 行 — 你刚拍板的）→ Round-Spec spec 内嵌（6 行）→ 历史 Round-Audit/Round-1~12 全 ✅ 跳过

### Round-V 验收单（当前热点，12 行）

| ID | 主题 + 跳转 | 批注摘要（30-60 字） | AI 简答 | 你的理解（自填） | 状态 |
|---|---|---|---|---|---|
| **V-Q1** | [[Story-1.19-configure-whiteboard\|📍 V-Q1 @line303]] · 你对 Story 1.19 v4 的批注区 | 文档预留 `[!question]+` 空 callout，等你跑 UAT 后写疑问/通过/失败 | 1.19 v4 已 ship Skill + template，等你跑 12 步 UAT | ___________ | ⏳ 🔥 |
| **V-Q2** | [[Story-1.19-configure-whiteboard\|📍 V-Q2 @line322]] · v3 → v4 round-9 修复历史 | round-9 v2.1 subject/board_name 分工：v2.1 埋步骤里 → v3 提顶 → v4 被架构重设计替代 | ✅ round-9 已通过 v3 → v4 修复 | ___________ | ✅ |
| **V-Q3** | [[Story-1.19-configure-whiteboard\|📍 V-Q3 @line325]] · v2.1 → v3 round-8 修复历史 | round-8 Epic 1 顺序 correct-course：1.19 yaml blocks 声明被 CLAUDE.md 工作量排序覆盖；修正为 1.16→1.19→1.17→1.18 | ✅ round-8 顺序已修正 | ___________ | ✅ |
| **V-Q4** | [[Story-1.17-ai-linked-doc\|📍 V-Q4 @line14]] · Story 1.17 暂挂起 | `[!error]+ ⛔ 暂挂起`：1.19 yaml blocks 要求 1.19 先做，1.17 双链才能在白板内用 | ✅ 已挂起，等 D1 解锁 | ___________ | ⏳ |
| **V-Q5** | [[Story-1.17-ai-linked-doc\|📍 V-Q5 @line400]] · 你对 Story 1.17 v2.1 的批注区 | 空 `[!question]+` callout，等 D1 通过后重跑 1.17 UAT 时填 | 1.17 v2.1 已 correct-course，待 D1 解锁 | ___________ | ⏳ 🔥 |
| **V-Q6** | [[Story-1.17-ai-linked-doc\|📍 V-Q6 @line408]] · v2 → v2.1 critical correct-course | 用户原批注命中 4 bug：Cmd+Shift+D/V 无区别 / 复制不工作 / 双链错误创建 / 等；3 agent 深挖确诊修复 | ✅ correct-course 已完成 | ___________ | ✅ |
| **V-Q7** | [[Story-1.17-ai-linked-doc\|📍 V-Q7 @line428]] · v1 双重付费 + 双 Vault 错配修复 | v1 plugin 直调 Anthropic API 违反 Mode D；改为形态 β（Plugin+Claudian Skill），零额外付费 | ✅ v2 已修复 | ___________ | ✅ |
| **V-Q8** | [[Story-1.16-批注-hotkey\|📍 V-Q8 @line168]] · 你对 Story 1.16 v2 的批注区 | 空 `[!question]+` callout；1.16 已 done，无 pending 批注可关闭 | ✅ 1.16 已 done | ___________ | ⏳ |
| **V-Q9** | [[Story-1.16-批注-hotkey\|📍 V-Q9 @line176]] · v1 严重 scope 偏离修复 | 用户原批注：批注应标 3 态理解度（已懂/模糊/不懂），但 spec 降级为 7 个原生 callout；根因是审计违反 Round 3 QA 锁定方案 | ✅ v2 已修复 | ___________ | ✅ |
| **V-Q10** | [[Canvas-完整学习闭环-验收总流程-2026-04-20\|📍 V-Q10 @line33]] · 提取概念僵尸命令警告 | 旧 Tauri 按钮调不存在的 `/api/v1/wikilink/build`，按了无反应；Story 3.1 用 Skill 重写 | ✅ 文档自身指引 | — | ✅ |
| **V-Q11** | [[Canvas-完整学习闭环-验收总流程-2026-04-20\|📍 V-Q11 @line104]] · 双链场景类比 | 1.17 = 读书时荧光笔+问老师写卡片；3.1 = 对话时请 AI 建新卡；老"提取概念"是没电的坏按钮 | ✅ 文档自身比喻 | — | ✅ |
| **V-Q12** | [[Canvas-完整学习闭环-验收总流程-2026-04-20\|📍 V-Q12 @line379]] · 总验收单批注区 | 空 `[!question]+` callout，待你跑总流程后填（依赖 D1 解锁后才能跑全闭环） | 待 D1 后跑总流程 | ___________ | ⏳ |

### Round-13 最新调研批注（4 行 — 已闭环）

| ID | 主题 + 跳转 | 批注摘要（30-60 字 用户原话） | AI 简答 | 你的理解（自填） | 状态 |
|---|---|---|---|---|---|
| **R13-Q1** | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q1 @line38]] · 跨白板关联功能砍/适配 | "现在我们白板都是 index.md 文件，已经不是之前的 Tarui 框架了，请你查看一下我们后端的跨白板关联的功能就是可以被砍掉了吧。或者来做其他的适配。" | round-11 扁平后含义变；建议适配（**对应 D3**） | ___________ | ⏳ ⚠️ |
| **R13-Q2** | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q2 @line116]] · 10 个 Graphiti 改善意见 | "请你提出 10 个成熟的关于我们后端目前 Graphti 使用功能改善的成熟的意见" | ✅ Round-13 已答（search_facts/communities/valid_at 三大未通电 + 路线图）| ___________ | ✅ |
| **R13-Q3** | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q3 @line212]] · graphify 检索精度 50% 大于吗 | "graphify 在管理 obsidian 文件检索的话，他的检索精度，使用场景是什么？管理节点关系的作用大于 50% 吗？请启动并行 agent deep explore" | ✅ Round-13 Q1 答：分工互补不是替代；wikilink 90% 简单查询命中第 1 层 | ___________ | ✅ |
| **R13-Q4** | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q4 @line265]] · md 全送 Graphiti vs LanceDB 对比 | "md frontmatter+body+wikilinks 全送给 Graphiti 抽实体 和 LanceDB+专用 vector 管道，请多维度对比" | ✅ Round-13 Q3 答：只对会变化属性进 Graphiti（mastery_score / understanding / last_reviewed）| ___________ | ✅ |

### Round-Spec Story spec 内嵌（6 行）

| ID | 主题 + 跳转 | 批注摘要（30-60 字） | AI 简答 | 你的理解（自填） | 状态 |
|---|---|---|---|---|---|
| **RS-Q1** | [[1-19-configure-whiteboard-skill\|📍 RS-Q1 @line317]] · Story 1.19 spec 用户批注占位 | 占位空白，等 1.19 v4 UAT 跑通后填 SKILL.md + template 是否符合预期 | 等 D1 跑通后填 | ___________ | ⏳ |
| **RS-Q2** | [[1-18-dashboard-md-mvp\|📍 RS-Q2 @line185]] · Story 1.18 spec 用户批注占位 | 占位空白，等 1.18 开工后填 dashboard.md 模板是否符合预期 + 4 AC + 5 步 UAT 是否够 | 1.18 ready-for-dev，等开工 | ___________ | ⏳ |
| **RS-Q3** | [[1-17-ai-linked-doc\|📍 RS-Q3 @line510]] · Story 1.17 spec v2 批注占位 | 占位等 1.17 解锁后填：10 AC + 14 步 UAT / 形态 β 是否对齐 Mode D / System Prompt 三段式是否够 | 等 D1 解锁后填 | ___________ | ⏳ |
| **RS-Q4** | [[1-16-annotate-callout-hotkey\|📍 RS-Q4 @line279]] · Story 1.16 spec 批注占位 | 1.16 已 done；占位可关闭，无 pending | ✅ 1.16 已 done | ___________ | ✅ |
| **RS-Q5** | [[1-4-hotkey-binding-config\|📍 RS-Q5 @line64]] · 原白板类型 + 检验白板检索 | 用户原话："md 文档为节点了，那么原白板的类型是什么？文件夹？index 文档？检验白板生成需检索批注+节点连接+解题错误，如何精准检索组装考察？" | ✅ round-11 扁平架构 + Story 1.2/1.3 wikilink 已规划 | ___________ | ✅ |
| **RS-Q6** | [[1-3-wikilink-context-assembly\|📍 RS-Q6 @line46-67]] · 检索定位 + Karpathy 启发 | 4 行用户深度提问：(46) 检索定位个人记忆 vs 笔记？/ (52) 2-hop 硬限必要性？/ (58) index.md 归纳啥？/ (67) tag 体系跨学科通用？| ✅ round-12/13 已答（Karpathy 第 1 层 + Graphiti 第 2 层 + LanceDB 第 3 层）| ___________ | ✅ |

### Round-Audit + Round-1~12 (~180 行已闭环 → Archive 候选 见 Layer 3 末)

> 已通过 Round-N+1 response 文件闭环，详见 Archive 候选表。

---

## Layer 3: 未决开放问题 + 行动清单（含摘要 + wikilink）

**只列 ⏳/❌/🔥 的批注。本清单决定你"本周必须做什么"。**

| ID | 问题（含摘要 + 跳转） | 状态 | 建议行动 | Deadline |
|---|---|---|---|---|
| **D1** 🔥 | [[Story-1.19-configure-whiteboard\|📌 D1 @line101-242]] **跑 12 步 UAT 验收 4 架构决策**：(1) 节点扁平池 = 侧栏折叠但 Cmd+Click 可点 / (2) subject 固化 vault 级 / (3) 中文目录 (原白板/节点/检验白板) 编码 QA / (4) 场景 A 从零建 + 场景 B 从 md 派生。**核心卡点**：中文 4 编码测试（Bash mkdir / Graph View filter / wikilink / Dataview FROM "原白板"）任一失败降级英文。 | ⏳ 未跑 | **打开 canvas-vault → Cmd+P → /configure-whiteboard 跑场景 A + 场景 B** | 越快越好 |
| **D2** 🔥 | [[round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29\|📌 D2 @line348-372]] **wikilink 双引擎 4 选项决策**：A 启动 1.2/1.3 wikilink 第 1 层 (~18h) / B 同时激活 Graphiti search_facts (+3h) / C 激活 entity_types (+2h) / D 接 wikilink 入 fusion (+4-6h)。决定 next 2-3 sprints 优先级。 | ⏳ 未拍板 | **从 4 选项中选 1-2 个**，告诉 Claude 启动实施 | TBD（D1 后拍） |
| **D3** ⚠️ | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📌 D3 @line38]] **retrieve_cross_canvas 砍/适配**：你的批注"白板已迁移扁平 md，跨白板关联可砍或适配"。后端 state_graph.py:540-671 第 4 通道现状是读老 `wiki/canvases/` 嵌套结构，round-11 扁平后语义失效。**砍**=删 line 605-614 5-way 降 4-way；**适配**=改读 `原白板/<board>.md` (~3h)。 | ⏳ 未决 | **拍板**：A 砍 / B 适配（推荐 B 改 `state_graph.py:540-671`）| 与 D2 同步 |
| **D4** ⏳ | (见本文档末尾 §UX 详单) **上轮 8 UX 决策**：立即层 5 影响 1.17/1.18/1.19；未来层 3 影响 Phase 1-3。 | ⏳ 未挑 | **从 8 个中选 1-3 个先聊**（推荐 ③ Dashboard confirm + ④ configure 派生原 md 处理）| TBD |
| V-Q1 | [[Story-1.19-configure-whiteboard\|📍 V-Q1 @line303]] Story 1.19 v4 UAT 跑完后写通过 ✅ 或具体失败步骤 | ⏳ | UAT 跑通后填 | 配合 D1 |
| V-Q5 | [[Story-1.17-ai-linked-doc\|📍 V-Q5 @line400]] Story 1.17 v2.1 批注（待 D1 解锁后重跑 14 步 UAT） | ⏳ | D1 通过后重跑 1.17 | 配合 D1 |
| R13-Q1 | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q1 @line38]] retrieve_cross_canvas 砍/适配（等同 D3） | ⚠️ | 等同 D3 | 配合 D3 |

### Archive 候选（不删，~180 行已闭环）

| 类别 | 数量 | 闭环证据 |
|---|---|---|
| review/epic-1-audit-* + audit-response-round-2/3/4 | ~50 行 [!question]+ | 通过 round-2/3/4 response 文件闭环 |
| research/obsidian-qa-round1~12-* | ~80 行 **User：** 历史问答 | 每 Round 通过 round-N+1 reply 闭环 |
| research/canvas-crossdiscipline-tags + obsidian-translation-qa | ~25 行 | 通过 round-7/8 重设计闭环 |
| planning-artifacts/prd.md + recovered/ | ~5 行 | PRD 引用，非批注 |
| templates/uat-sheet-template.md + .claude/CLAUDE.md `[!question]+` | ~10 行 | 模板/约定文档，非批注 |
| Story 验收单历史 `[!error]+ v{N} → v{N+1} 修复` | ~10 行 | 已通过 correct-course 闭环 |

---

## §UX 详单 — D4 的 8 个具体 UX 决策（来自上轮 assistant 列表）

### 立即层（4 MVP Story 实施前要拍板）

**① AI 派生新节点后跳转方式**（影响 Story 1.17）
- A 自动跳新 tab（中断当前阅读）
- B 留原 md + toast "✓ 新节点已建好"（不打断阅读流）
- C 左右 split view 同时显示

**② AI 派生失败提示**（影响 Story 1.17）
- A 红色 toast + "重试" 按钮
- B 静默不提示
- C 在原文选中位置插入 `[!error]+ AI 派生失败：原因 XX` callout

**③ Story 1.18 Dashboard 一键考察 confirm vs 直跳**
- A 直跳（少一次点击）
- B confirm 弹窗 "确认进入考察吗？"
- C 一秒倒计时按钮可取消

**④ Story 1.19 从已有 md 派生白板时原 md 处理**（影响 Story 1.19 场景 B）
- A 复制保留（原位置仍在）
- B 移动（原位置消失，wikilink 自动重定向）
- C 引用（建新文件含 [[原 md]] wikilink）

**⑤ Story 1.18 Dashboard 显示哪些指标（multiSelect 候选）**
- mastery 平均分 / 节点总数 / 最近 7 天复习数 / 错误集中节点 / FSRS 到期数 / 上次考察成绩 / 孤儿节点数（建议挑 3-5 个）

### 未来层（Phase 1-3 路线图相关）

**⑥ AI 检索结果是否标注引擎来源**（Phase 1）
- A 不标注，统一展示
- B 加 emoji 🔗wikilink / 📊Graphiti / 🔍LanceDB
- C 默认隐藏，hover 才显

**⑦ md → Graphiti 同步状态**（Phase 2）
- A 完全隐藏（用户感觉不到延迟）
- B 状态栏小图标 ⏳同步中 / ✓已同步
- C 仅未同步时提示 "正在 lazy sync 你最新的编辑..."

**⑧ 错误模式发现（Phase 3）的提示方式**
- A 立即 toast "AI 发现你常错 X"（打断）
- B Dashboard 加 "待查看的洞察" 卡片（不打断）
- C 静默写 Graphiti，下次考察时自动用

---

## Layer 4: 5 句话框架总结（用户自填）

1. **核心决策**：我选择 ____________（D1 立即跑 1.19 UAT / D2 选哪个选项 / 其他），因为 ____________ 。

2. **关键约束**：我现在的瓶颈是 ____________（A2 1.19 UAT 没跑 → 1.17 连锁 blocked / D2 wikilink 路线没定 / 其他）。

3. **下一步行动**（本周内）：____________ （1 件最重要的事，写具体动作）。

4. **风险识别**：我最担心的是 ____________ ；我的 plan B 是 ____________ 。

5. **时间截点**：我必须在 ________ 年 __ 月 __ 日前决定 ____________ 。

---

## 你可能感觉到的认知变化（填完这份文档后）

- ✅ 3 分钟内讲清"Canvas 17 stories 进度 + 1 个连锁卡点（1.19 UAT）"
- ✅ 4 个关键决策 D1-D4 的具体内容 + 优先级脱口而出
- ✅ 遇到新批注，能快速判断"这是 D1-D4 决策关键还是支撑细节？"
- ✅ 对 222 批注的焦虑消失（已收敛到 22 行活跃 + ~180 已闭环）
- ✅ 任何一行决策 / 批注 / action 都能 Cmd+Click 跳到原文（v2 升级）

---

## 遇到"想拆新批注"的冲动时（反模式三问）

1. **这个新问题和 D1-D4 4 个关键决策直接相关吗？**
   - 有关 → 在现有 22 行内深化（不新建）
   - 无关 → 直接 archive

2. **这个问题可以在 Layer 3 action 里用"发 1 句指令给 Claude / 跑一次 UAT"解决吗？**
   - 可以 → 写到 Layer 3，不写成批注
   - 不可以 → 才考虑新建（99% 情况不需要）

3. **如果不回答这个问题，我还能做 D1-D4 决策吗？**
   - 能 → archive
   - 不能 → 它就是 A1-A4 关键假设之一，放 Layer 1 假设表

---

**文档结束**。生成于 2026-04-29 23:35 · verify-vault@v1.2 · v1 → v2 升级（每行加摘要 + wikilink） · prev: vault-status-2026-04-29-v1.md · 总扫描 222 命中 / Layer 2 活跃 22 行 + 4 决策 + 4 假设
