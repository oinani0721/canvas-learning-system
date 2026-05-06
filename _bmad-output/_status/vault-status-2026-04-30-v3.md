---
title: "Canvas Learning System _bmad-output Vault 验收清单 v3（UX/TECH 分类 + AI 自决）"
date: 2026-04-30
type: verification-checklist
total_annotations: 222
structure: "Layer 1 决策备忘录（含 🎯 UX + 🔧 TECH 两区）+ Layer 2 批注矩阵（保留 v2）+ Layer 3 行动清单（分类） + Layer 4 总结"
parent_methodology: vault-status-2026-04-29-v2.md
goal: "v2 → v3 升级 — D1/D4 标记 🎯 UX 用户拍板项；D2/D3 标记 🔧 TECH 自决项（含自决结果 + 30-60 字理由）"
status: draft
scope: canvas-bmad-output
generator: "verify-vault@v1.3 (UX/TECH classification)"
version: v3
canvas_enhancement: enabled
prev_version: vault-status-2026-04-29-v2.md
upgrade_reason: "v2 4 决策未区分 UX/TECH 用户权限 → 用户立场：只决策 UX，TECH AI 自决。v3 明确分组 + AI 已自决 D2/D3 给结果"
---

# Canvas Learning System 开发进度 + 关键决策验收清单 v3

## 使用说明（1 分钟更新）

**v3 主要变化**：
1. **🎯 你必须决策的（UX）** — D1 + D4-1 到 D4-8 共 9 个，标记加粗 + 🎯 显著标记
2. **🔧 AI 已自决的（TECH）** — D2 + D3 共 2 个，标记 🔧 + ✅ done + 30-60 字理由
3. 其余 Layer 2-4 保留 v2 schema（每行含 wikilink + 30-60 字摘要）

**查阅流程**：
1. 扫 Layer 1 **🎯 UX 决策区** → 每个 3-5 秒判断是否同意推荐
2. 跳过 **🔧 TECH 自决区**（仅供参考，AI 已拍板）
3. 点 wikilink 看原文；在"你的理解"列写 1 句反馈
4. 打状态 ✅ / ⏳ / ❌

---

## Layer 1: 一页纸决策备忘录（分 🎯 UX + 🔧 TECH 两区）

### 你问的两个核心问题，一句话答

> **Q1：开发进度停哪？** Epic 1 v2: 5 done / 1 review / 1 blocked / 10 ready-for-dev。**关键卡点 = Story 1.19 v4 UAT 你还没跑** → 1.17 blocked + 1.18 数据源缺白板。Epic 2: 10/13 done。Epic 3-6: 全 backlog 等 Epic 1 主线。
>
> **Q2：什么决策待拍板？** 11 个 — **9 个 UX 决策**（D1 + D4-1~D4-8 你必须拍板）+ **2 个 TECH 决策**（D2 + D3 AI 已自决）。

### 🎯 你必须决策的 UX 决策（9 个）

| ID | 决策具体内容（30-60 字）+ 跳转 | 选项 ABC | 推荐 | Deadline |
|---|---|---|---|---|
| **D1** 🎯 UX | ~~**Story 1.19 v4 UAT 跑/不跑**~~ ✅ **2026-04-30 用户亲自跑过通过** [[Story-1.19-configure-whiteboard\|📍 D1 @line101-242]]<br>已通过：场景 A + 场景 B + 中文编码 QA + D4-4 复制保留生效（截图 3 验证）+ wikilink 中文路径工作（截图 2）+ Graph View 孤立节点 toggle 解决（截图 1） | **A** 全通过 → unblock 1.17 + ship 1.18 patch | **A** ✅ **done** | ✅ 2026-04-30 |
| **D4-1** 🎯 UX | **AI 派生新节点后跳转方式**（影响 Story 1.17）<br>AI 派生新节点后体验：自动跳新 tab（中断阅读）vs toast 不打断 vs split view 并行显示 | **A** 自动跳 tab<br>**B** toast 不打断<br>**C** split view | **B** ⭐⭐⭐⭐ | 1.17 开工前 |
| **D4-2** 🎯 UX | **AI 派生失败提示方式**（影响 Story 1.17）<br>派生失败时 UI：红 toast + 重试按钮 vs 静默不提示 vs 在选中位置插 [!error]+ callout | **A** toast + 重试<br>**B** 静默<br>**C** callout | **A** ⭐⭐⭐ | 1.17 开工前 |
| **D4-3** 🎯 UX | **Story 1.18 Dashboard 一键考察 confirm 弹窗**<br>考察前是否弹"确认进入考察吗？" vs 直跳（少一次点击）vs 一秒倒计时可取消 | **A** 直跳<br>**B** confirm 弹窗<br>**C** 倒计时 | **B** ⭐⭐⭐⭐ | 1.18 开工前 |
| **D4-4** 🎯 UX | **Story 1.19 从已有 md 派生白板时原 md 处理**<br>用户选已有 md 派生白板，原 md 要：保留副本在原位 vs 移动到新位置（自动重定向 wikilink）vs 引用 | **A** 复制保留<br>**B** 移动<br>**C** 引用 | **A** ⭐⭐⭐⭐ | 1.19 UAT 前 |
| **D4-5** 🎯 UX | **Story 1.18 Dashboard 显示哪些指标**（multiSelect）<br>7 候选：mastery 平均分 / 节点总数 / 最近 7 天复习数 / 错误集中节点 / FSRS 到期数 / 上次考察成绩 / 孤儿节点数 | 7 候选挑 3-5 个 | mastery + 节点数 + FSRS 到期 (刚需) | 1.18 开工前 |
| **D4-6** 🎯 UX | **AI 检索结果是否标注引擎来源**（Phase 1，Story 3+）<br>检索结果是否显示来源：不标 vs 加 emoji 🔗wikilink/📊Graphiti/🔍LanceDB vs hover 才显 | **A** 不标<br>**B** 加 emoji<br>**C** hover | **C** ⭐⭐⭐ | Phase 1 后 |
| **D4-7** 🎯 UX | **md → Graphiti 同步状态提示**（Phase 2）<br>用户编辑 md 后是否看到同步状态：完全隐藏 vs 状态栏图标 ⏳/✓ vs 仅未同步时提示 | **A** 隐藏<br>**B** 状态栏图标<br>**C** 仅未同步提示 | **C** ⭐⭐⭐ | Phase 2 后 |
| **D4-8** 🎯 UX | **错误模式发现的提示方式**（Phase 3，Story 6）<br>AI 发现常错某概念后：立即 toast（打断）vs Dashboard 卡片（不打断）vs 静默写 Graphiti（下次考察用） | **A** 立即 toast<br>**B** Dashboard 卡片<br>**C** 静默 | **B** ⭐⭐⭐ | Phase 3 后 |

### 🔧 AI 已自决的 TECH 决策（2 个，仅告知）

| ID | 决策具体内容（30-60 字）+ 跳转 | AI 选择 | 自决理由（30-60 字） | 工作量 | 状态 |
|---|---|---|---|---|---|
| **D2** 🔧 TECH | **round-13 wikilink 双引擎 4 选项** [[round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29\|📍 D2 @line348-372]]<br>4 实施工作量权衡：A 启动 1.2/1.3 (~18h) / B Graphiti search_facts (+3h) / C entity_types (+2h) / D wikilink 入 fusion (+4-6h) | **✅ 选 A**<br>启动 Story 1.2+1.3 | Karpathy 第 1 层是骨架，零成本 + 90% 简单查询够用；短期最优先，B/C/D Phase 2-3 依序激活；Round-13 Q5 明确路线图 | ~18h | ✅ done |
| **D3** 🔧 TECH | **retrieve_cross_canvas 砍/适配** [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 D3 @line38]]<br>round-11 扁平后跨白板含义已变。state_graph.py:540-671 第 4 通道砍掉 vs 适配读 `原白板/` 扁平结构 | **✅ 选 B**<br>适配 (~3h) | 现有代码骨架完整，仅 find_related_canvases 是空实现；适配成本低（~3h 改读扁平目录），功能保留跨学科价值；砍的收益不如留 | ~3h | ✅ done |

### 4 个关键假设

| 假设 | 当前证据 + 跳转 | 核实方式 | Deadline |
|---|---|---|---|
| **A1**: round-11 扁平架构稳定 | ✅ commit `d5c6a69` 固化 + [[CLAUDE\|📍 _bmad-output/.claude/CLAUDE.md vault 扁平架构段]] | 已核实 | ✅ done |
| **A2** 🔥: Story 1.19 v4 用户能跑通 12 步 UAT | ⏳ Story-1.19 status=review，UAT 文档已 ship，**用户尚未跑** | [[Story-1.19-configure-whiteboard\|📍 跑场景 A+B 12 步]] | **TBD（D1 决定）** |
| **A3**: Wikilink + Graphiti 双引擎共存可行 | ✅ [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 round-12]] + [[round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29\|📍 round-13]] 双调研 + 12+ 业界案例 | 已论证 | ✅ done |
| **A4**: subject 字段 vault 级固化 | ✅ round-11 决定 + `.canvas-config.yaml` schema | 已核实 | ✅ done |

### 里程碑

| 日期 | 里程碑 | 触发重新评估 |
|---|---|---|
| 2026-04-30 | v3 文档 ship + UX/TECH 分类落地 + verify-vault skill v1.3 | — |
| **TBD ↑ 关键** | **Story 1.19 v4 UAT 通过 → 解锁 1.17 → 1.18 Dashboard** | A2 假设核实 |
| TBD | D2 自决落地 → Story 1.2/1.3 wikilink 启动 (~18h) | D1 跑通后 |
| TBD | Phase 1 完成（wikilink 第 1 层 + Graphiti search_facts 激活）| Story 1.2/1.3 done |

---

## Layer 2: 批注矩阵（保留 v2 schema，6 列含摘要 + wikilink）

**填写顺序**：Round-V 验收单（12 行 — 你最该看的）→ Round-13 调研（4 行）→ Round-Spec spec 内嵌（6 行）→ 历史 ✅ 跳过

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
| **R13-Q1** | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q1 @line38]] · 跨白板关联功能砍/适配 | "现在我们白板都是 index.md 文件，已经不是之前的 Tarui 框架了，请你查看一下我们后端的跨白板关联的功能就是可以被砍掉了吧。或者来做其他的适配。" | ✅ Round-13 已答（**对应 D3 🔧 已选 B 适配**） | ___________ | ✅ |
| **R13-Q2** | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q2 @line116]] · 10 个 Graphiti 改善意见 | "请你提出 10 个成熟的关于我们后端目前 Graphti 使用功能改善的成熟的意见" | ✅ Round-13 已答（search_facts/communities/valid_at 三大未通电 + 路线图）| ___________ | ✅ |
| **R13-Q3** | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q3 @line212]] · graphify 检索精度 50% 大于吗 | "graphify 在管理 obsidian 文件检索的话，他的检索精度，使用场景是什么？管理节点关系的作用大于 50% 吗？请启动并行 agent deep explore" | ✅ Round-13 Q1 答：分工互补不是替代（**对应 D2 🔧 已选 A 启 1.2/1.3**）| ___________ | ✅ |
| **R13-Q4** | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q4 @line265]] · md 全送 Graphiti vs LanceDB 对比 | "md frontmatter+body+wikilinks 全送给 Graphiti 抽实体 和 LanceDB+专用 vector 管道，请多维度对比" | ✅ Round-13 Q3 答：只对会变化属性进 Graphiti（mastery_score / understanding / last_reviewed）| ___________ | ✅ |

### Round-Spec Story spec 内嵌（6 行）

| ID | 主题 + 跳转 | 批注摘要（30-60 字） | AI 简答 | 你的理解（自填） | 状态 |
|---|---|---|---|---|---|
| **RS-Q1** | [[1-19-configure-whiteboard-skill\|📍 RS-Q1 @line317]] · Story 1.19 spec 用户批注占位 | 占位空白，等 1.19 v4 UAT 跑通后填 SKILL.md + template 是否符合预期 | 等 D1 跑通后填 | ___________ | ⏳ |
| **RS-Q2** | [[1-18-dashboard-md-mvp\|📍 RS-Q2 @line185]] · Story 1.18 spec 用户批注占位 | 占位空白，等 1.18 开工后填 dashboard.md 模板是否符合预期 + 4 AC + 5 步 UAT 是否够 | 1.18 ready-for-dev，等开工 | ___________ | ⏳ |
| **RS-Q3** | [[1-17-ai-linked-doc\|📍 RS-Q3 @line510]] · Story 1.17 spec v2 批注占位 | 占位等 1.17 解锁后填：10 AC + 14 步 UAT / 形态 β 是否对齐 Mode D / System Prompt 三段式是否够 | 等 D1 解锁后填 | ___________ | ⏳ |
| **RS-Q4** | [[1-16-annotate-callout-hotkey\|📍 RS-Q4 @line279]] · Story 1.16 spec 批注占位 | 1.16 已 done；占位可关闭，无 pending | ✅ 1.16 已 done | ___________ | ✅ |
| **RS-Q5** | [[1-4-hotkey-binding-config\|📍 RS-Q5 @line64]] · 原白板类型 + 检验白板检索 | 用户原话："md 文档为节点了，那么原白板的类型是什么？文件夹？index 文档？检验白板生成需检索批注+节点连接+解题错误，如何精准检索组装考察？" | ✅ round-11 扁平架构 + Story 1.2/1.3 wikilink（**对应 D2 🔧 选 A**）已规划 | ___________ | ✅ |
| **RS-Q6** | [[1-3-wikilink-context-assembly\|📍 RS-Q6 @line46-67]] · 检索定位 + Karpathy 启发 | 4 行用户深度提问：(46) 检索定位个人记忆 vs 笔记？/ (52) 2-hop 硬限必要性？/ (58) index.md 归纳啥？/ (67) tag 体系跨学科通用？| ✅ round-12/13 已答（Karpathy 第 1 层 + Graphiti 第 2 层 + LanceDB 第 3 层）| ___________ | ✅ |

---

## Layer 3: 未决开放问题 + 行动清单（按 UX/TECH 分组）

### 🎯 你必须拍板的 UX 决策（9 个）

**User：按照你的决策推动，这些决策我需要实际使用过才知道实际的效果，然后还有一点就是目前以上的决策内容启动 Bamd 的开发方式的话，请问是否需要编辑成相关的 story，来开始执行，然后你还要告诉我个人需要进行验收的内容。**

> **[AI 回复 2026-04-30 → 接受推荐 + BMAD + 验收]** ✅ 三问回答见 [[next-steps-2026-04-30\|📌 next-steps 完整路线 + UAT 清单]]。**核心 3 答**：
> 1. **"用过才知道效果"** ✅ 同意 — 决策推动顺序按"边跑边验"安排：D1 跑 1.19 UAT → D4-4 实际感知 → 1.17 解锁后跑 → D4-1/2 实际感知 → 1.18 开工 → D4-3/5 实际感知。每跑一个 Story 你立刻能验下一组 UX 决策。
> 2. **"BMAD 是否需要编辑成 Story"** — **不需要新建** Story，4 个 MVP Story (1.16/1.17/1.18/1.19) 都已有 spec。**需要做** = AI 用 `bmad-bmm-correct-course` 把 9 个 UX 决策 patch 到对应 spec 的 AC + Tasks 段（自动）。映射：D1→1.19 / D4-1,2→1.17 / D4-3,5→1.18 / D4-4→1.19 / D4-6,7,8→Phase 1-3 未来 Story（暂记决策，不动代码）。D2/D3 TECH → 写入 Story 1.2/1.3 spec Dev Notes。
> 3. **"个人验收清单"** — 已有 4 份 UAT sheet（按 Story 串），列在 next-steps 文档底部。当前**最关键 1 件事 = D1 跑 Story 1.19 v4 UAT 12 步**，UAT sheet 在 `验收单/Story-1.19-configure-whiteboard.md`，你打开 obsidian → 跑场景 A + B → 勾选 ✅。
>
> **9 个 UX 决策状态** ✅ **已接受推荐**：D1→A / D4-1→B / D4-2→A / D4-3→B / D4-4→A / D4-5→mastery+节点数+FSRS 到期 / D4-6→C / D4-7→C / D4-8→B


| ID | 决策（含摘要 + 跳转） | 当前状态 | 建议行动 | Deadline |
|---|---|---|---|---|
| **D1** 🎯 | [[Story-1.19-configure-whiteboard\|📌 D1 @line101-242]] **Story 1.19 v4 UAT 跑通 vs 降级**：12 步 UAT + 4 架构决策 + 中文编码 QA | ⏳ 未跑 | **打开 canvas-vault → Cmd+P → /configure-whiteboard 跑场景 A + 场景 B（12 步）** | 越快越好 |
| **D4-1** 🎯 | **AI 派生跳转方式**（影响 Story 1.17）：自动跳 vs toast vs split view | ⏳ 未拍 | 从 3 选项选 1（推荐 B toast） | 1.17 开工前 |
| **D4-2** 🎯 | **派生失败提示**（影响 Story 1.17）：toast + 重试 vs 静默 vs callout | ⏳ 未拍 | 从 3 选项选 1（推荐 A toast） | 1.17 开工前 |
| **D4-3** 🎯 | **Dashboard confirm 弹窗**（影响 Story 1.18）：直跳 vs 弹窗 vs 倒计时 | ⏳ 未拍 | 从 3 选项选 1（推荐 B 弹窗） | 1.18 开工前 |
| **D4-4** 🎯 | **派生原 md 处理**（影响 Story 1.19 场景 B）：复制 vs 移动 vs 引用 | ⏳ 未拍 | 从 3 选项选 1（推荐 A 复制） | 1.19 UAT 前 |
| **D4-5** 🎯 | **Dashboard 指标 multiSelect**（影响 1.18）：7 候选挑 3-5 | ⏳ 未拍 | 挑 3-5 个（推荐 mastery + 节点数 + FSRS 到期） | 1.18 开工前 |
| **D4-6** 🎯 | **检索来源标注**（Phase 1）：不标 vs emoji vs hover | ⏳ 未拍 | 从 3 选项选 1（推荐 C hover） | Phase 1 后 |
| **D4-7** 🎯 | **同步状态提示**（Phase 2）：隐藏 vs 状态栏 vs 仅未同步 | ⏳ 未拍 | 从 3 选项选 1（推荐 C 仅未同步） | Phase 2 后 |
| **D4-8** 🎯 | **错误模式提示**（Phase 3）：立即 toast vs Dashboard 卡片 vs 静默 | ⏳ 未拍 | 从 3 选项选 1（推荐 B Dashboard） | Phase 3 后 |

### 🔧 AI 已自决的 TECH 决策（2 个，仅供参考）

| ID | 决策（含摘要 + 跳转） | AI 选择 | 实施工作量 | Deadline |
|---|---|---|---|---|
| **D2** 🔧 | [[round-13-wikilink-vs-graphiti-five-questions-answer-2026-04-29\|📌 D2 @line348-372]] **wikilink 双引擎 4 选项** | ✅ **选 A**：启动 Story 1.2 + 1.3（Karpathy 第 1 层是骨架，零成本 + 90% 简单查询够） | ~18h | 配合 D1 |
| **D3** 🔧 | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📌 D3 @line38]] **retrieve_cross_canvas 砍/适配** | ✅ **选 B**：适配（现有代码完整，仅改 `find_related_canvases` 从 `原白板/` 读扁平目录，~3h 改造） | ~3h | 与 D2 同步 |

### 其他 action items

| ID | 问题（含摘要 + 跳转） | 状态 | 建议行动 | Deadline |
|---|---|---|---|---|
| V-Q1 | [[Story-1.19-configure-whiteboard\|📍 V-Q1 @line303]] Story 1.19 v4 UAT 跑完后写通过 ✅ 或具体失败步骤 | ⏳ | UAT 跑通后填 | 配合 D1 |
| V-Q5 | [[Story-1.17-ai-linked-doc\|📍 V-Q5 @line400]] Story 1.17 v2.1 批注（待 D1 解锁后重跑 14 步 UAT） | ⏳ | D1 通过后重跑 1.17 | 配合 D1 |
| R13-Q1 | [[round-12-graphiti-karpathy-5-conjectures-audit-2026-04-21\|📍 R13-Q1 @line38]] retrieve_cross_canvas（AI 已自决选 B） | ✅ done | 参考 D3 🔧 自决结果 | 与 D2 同步 |

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

## Layer 4: 5 句话框架总结（用户自填）

1. **核心决策**：我选择 ____________（D1 立即跑 1.19 UAT / D4-1~D4-8 各选项 / 接受 D2/D3 AI 自决），因为 ____________ 。

2. **关键约束**：我现在的瓶颈是 ____________（A2 1.19 UAT 没跑 → 1.17 连锁 blocked / 其他）。

3. **下一步行动**（本周内）：____________ （1 件最重要的事，写具体动作）。

4. **风险识别**：我最担心的是 ____________ ；我的 plan B 是 ____________ 。

5. **时间截点**：我必须在 ________ 年 __ 月 __ 日前决定 ____________ 。

---

## 你可能感觉到的认知变化（填完这份文档后）

- ✅ 3 分钟内讲清"Canvas 17 stories 进度 + 1 个连锁卡点 + 9 个 UX 拍板 + 2 个 TECH 已决"
- ✅ 9 个 UX 决策（D1 + D4-1~D4-8）的具体内容 + 推荐选项脱口而出
- ✅ 2 个 TECH 决策（D2 + D3）AI 已拍板，理由简洁（30-60 字）
- ✅ 遇到新问题，能快速判断"这是 UX（我拍板）还是 TECH（AI 自决）？"
- ✅ 对 222 批注的焦虑消失（已收敛到 22 行活跃 + 2 个 AI 自决 + 9 个 UX 拍板 + ~180 已闭环）

---

## 遇到"想拆新决策"的冲动时（反模式三问）

1. **这个新问题是 UX 决策还是 TECH 细节？**
   - UX → 拆成 D4-9 / D4-10 等（写到 Layer 1 + Layer 3 🎯 区）
   - TECH → AI 自决，不劳用户拍板（写到 🔧 区告知）

2. **这个决策影响哪些 Story 的 Deadline？**
   - 影响立即层 → 加到 D1 / D4-1~D4-5
   - 影响未来层 → 归到 D4-6~D4-8
   - 都不影响 → archive

3. **如果不拍板这个决策，我还能做 D1-D4 决策吗？**
   - 能 → archive（这是 TECH 细节，AI 可自决）
   - 不能 → 它是 UX 决策，加到 Layer 1 🎯 区

---

**文档结束**。生成于 2026-04-30 · verify-vault@v1.3 · v2 → v3 升级（UX/TECH 分类 + AI 自决 D2/D3）· prev: vault-status-2026-04-29-v2.md · 活跃决策 11 个（9 🎯 UX + 2 🔧 TECH 自决）/ 关键假设 4 个 / Layer 2 活跃 22 行 + Archive ~180 行
