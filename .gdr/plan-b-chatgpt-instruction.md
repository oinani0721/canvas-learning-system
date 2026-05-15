# Deep Research 对抗审查请求 — Plan B (Story 2.4) 架构独立第二意见

## 项目背景

Canvas Learning System (Obsidian Hybrid + FastAPI + Neo4j + LanceDB + Graphiti).

2026-05-13 ChatGPT 78% 置信确认 Claude 5-Agent "FAIL" 判定 (见 F. 历史报告).

2026-05-14 Canvas 团队基于该判定实施 Plan B (plugin debounce push + content_hash 幂等 + Graphiti EpisodicNode 真相源), 8 层根因 (P0-1~P0-8 + F1 visible prompt) 逐一修复, 用户实测端到端打通 (一次输入 = 8 sync = 3 EpisodicNode v1/v2/v3 + Gemini 抽取 LearningConcept).

但 5-14 自我做的 4 Agent 并行 deep explore 暴露 34 个对抗性问题 — 4 BLOCKER + 8 HIGH + 11 MEDIUM + 11 LOW (详见 agent_research_summary 段).

**核心担忧**: Plan B 看似成功 (端到端跑通) 但可能选错了根本架构方向. Story 2.4 原 spec 是 Plan A (frontmatter 真相源 + backend file watcher pull). 我们偏离 spec 走 Plan B 是否是 over-engineering?

## ChatGPT 的 4 个任务

### 任务 1: 验证 4 BLOCKER 是否真致命

| BLOCKER | Canvas 团队判断 | 你需要验证 |
|---|---|---|
| B1 数据链路死链 | context_enrichment_service.py:276 只读 frontmatter, 零处调 Graphiti | 看代码确认; 如真, Plan B 主对话链路接不上是不是致命? |
| B2 删除追踪 0 感知 | append-only + vault.on('modify') 看不到删除事件 | AC#5 在 Plan B 是否可实现? 给 3 个备选方案打分 |
| B3 Cmd+Q 100% 数据丢失 | plugin 0 处 onunload flush + 0 处 retry queue | 真实 Obsidian 用户行为下损失率? 必须先修这个再说? |
| B4 跨文件 hash prefix 碰撞 | Neo4j 查询缺 node_id 过滤 + 16 hex prefix | 实际碰撞概率? P0 漏洞还是 MVP 可推迟? |

### 任务 2: 评估 Plan B vs Plan A 决策

Canvas 选 Plan B 的 3 个理由:
1. 时序演化 (Graphiti valid_at)
2. 跨白板推理
3. P0 已接通

但 Agent C 给的反驳事实:
1. dedupe_nodes 源码无 temporal 逻辑 → LearningConcept 跨时间合并 → **演化只在 Episode 层不在 Entity 层** → 用户 5-13 报告 G7 担忧 **在 Plan B 下被放大**
2. 跨白板推理代价是 dedupe 合并 → 失去 canvas-A vs canvas-B 不同语境
3. P0 已接通但是"半成品" (plugin 部分功能 build 进 main.js 但部分还在 src/ 未接通)

**你的判断**: Plan B 解决了 G7 演化担忧吗? 还是放大了?

### 任务 3: 回答 Agent C 的 Q5 灵魂拷问 (DD-08 用户初衷)

DD-08 (Graphiti 用户初衷): 用户从未说"需要 AI 自动从批注里抽取实体边".

用户表达的是:
- 批注要落地到文件 → frontmatter 完美解决
- wikilink 要可追溯 → frontmatter 完美解决
- 跨白板要可发现 → Obsidian Graph View 原生

**ChatGPT 任务**: 给出 **一个具体的用户故事** — 一句用户的话 — 能且仅能用 Graphiti append-only 解决, frontmatter 无法解决. 如果给不出, Plan B 就是 over-engineering, 应该回退 Plan A 或推倒重来.

### 任务 4: 从 20 个对抗问题选 5-7 个最尖锐回答

Agent A/B/C/D 各 5 问 (共 20 问), 详见 agent_research_summary 段. 请挑选最有价值的 5-7 个深度回答, 特别关注:
- 是否有社区先例 (GitHub issues / 知名 plugin / Graphiti maintainer 表态)
- 修复 vs 重做的成本差
- 用户体验冲击的可观察性

## 期望输出格式

### 表 1: 4 BLOCKER 逐条审查
| BLOCKER | Canvas 判断 | ChatGPT 判断 | 证据 (file:line) | 修复优先级 |

### 表 2: Plan B vs Plan A vs Plan C(双写) 决策再评估
| 方案 | 时序演化 | 跨白板推理 | 离线弹性 | AC#5 删除 | LLM 成本 | 验收单友好 | ChatGPT 推荐 |

### 表 3: 5-7 个尖锐对抗问题深度回答
对每个问题:
- 引用代码或社区证据
- 给出修复方向 (PR-able 具体改动, 不是模糊建议)

### 分章节叙述
- **章节 A — Plan B 必修 BLOCKER 清单** (达到"可上线"标准的最低修复)
- **章节 B — Plan B vs Plan A 决策推荐** (停止前进 / 回退 spec / 双写过渡)
- **章节 C — DD-08 用户初衷验证** (用户故事能否找到)
- **章节 D — Canvas 团队未发现的盲点** (你看到我们没看到的问题)

## 关键证据文件路径 (按章节定位)

- **死链证据**: backend/app/services/context_enrichment_service.py + backend/app/services/learning_context_service.py
- **append-only 设计**: backend/app/api/v1/endpoints/tips.py + backend/app/services/memory_service.py
- **plugin 现状**: frontend/obsidian-plugin/src/callout.ts + callout-sync.ts + main.ts
- **Graphiti 内部约束**: graphiti_core/prompts/dedupe_nodes.py + models/nodes/node_db_queries.py
- **Plan A 原 spec**: worktree/_bmad-output/implementation-artifacts/epic-2/2-4-callout-annotation-tips.md
- **项目脉络**: worktree/CLAUDE.md + worktree/_bmad-output/.claude/CLAUDE.md

## 输出风格要求

- **零客气** — 这是对抗审查, 不是同行评议. 指出我们错了直接说.
- **引用证据** — file:line 或社区 issue/forum URL.
- **可执行** — 修复建议必须可 PR 化, 不要"应该考虑"等模糊语.
- **保护用户** — 最终决策权在用户 (非技术 PM), 帮我们替用户判断"Plan B 是不是把简单问题复杂化".
- **诚实承认** — 如果某个问题 ChatGPT 无法判断, 明确说"未能判断".
