# Chat vs TutorBot 使用差异完整报告

> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **调研日期**: 2026-05-06
> **调研方法**: 5 Agent 并行 Deep Explore（产品 UX 维度）
> **触发问题**: 用户问 "chat 和 agent 在原本设计的使用上功能有什么区别？"

---

## Executive Summary（核心结论）

**Chat vs TutorBot 是 HKUDS 故意设计的两条互补路径**：

- **Chat = 瑞士军刀**（万能、快速、无记忆，6 capability 在单 thread 内自由切换）
- **TutorBot = 私人教练**（持久、自主、长期陪伴，N 个 bot 各自独立 + 共享 user-level memory）

**核心选择标准**：
- 时间周期 < 1 周 → **Chat**
- 时间周期 ≥ 1 周 + 跨 session 记忆 → **TutorBot**
- 多学科并行 + 跨域关联 → **TutorBot N bots + 共享 SUMMARY/PROFILE**
- 即时问答 + 临时需求 → **Chat**

**HKUDS 营销 vs 学术分层**：
- README 篇幅比 Chat:TutorBot = **3.4:1**（Chat 是营销前台 = 学生引流入口）
- arXiv 论文强调 "Agent-Native" 架构（TutorBot 是学术差异化 = 工程师/研究者深度）

---

## 一、5 Agent 整合发现矩阵

| Agent | 关键发现 | 对 Round-22 D2 的影响 |
|---|---|---|
| **A** Chat 6 capability 详解 | "One thread" = 共享 session_id + per-message capability 标记；6 capability 在 SQLite 同一 session 累积 | Chat 路径单 thread 灵活但跨 session 孤岛 |
| **B** TutorBot 实际工作流 | 创建 4 字段（Name/Desc/Soul/Model）+ 9 目录树 + 3 asyncio 任务 + Heartbeat 30min auto-tick + 12 渠道 | TutorBot 是 Round-22 M8（主动心跳）的精确落地 |
| **C** 5 学习场景对比 | 决策矩阵：考试突击 Chat / 长期备考 TutorBot / 错题追踪 TutorBot 必选 / 跨学科 N bots | Round-22 5 验证场景 应主推 TutorBot 路径 |
| **D** 用户旅程 3 时间尺度 | Chat URL 寻址 + TutorBot bot-centric；都缺 mastery dashboard | **Round-22 Canvas 5 大核心 = 填补共同缺口** |
| **E** README 官方卖点 | Chat 营销主导（3.4:1）+ TutorBot 学术差异化 + 13 能力官方化（6+7） | Day 2+ 引导用户用 TutorBot（fork README 教学引流） |

---

## 二、Chat 6 Capability 详解（Agent A 提取）

### "One Thread" 实现机制

```typescript
// 前端：切换 capability 不改 session_id
handleSelectCapability(value) {
  setCapability(value);           // 只改 activeCapability
  // sessionId 保持不变 ← one thread!
}

// 后端：capability 字段 per-message
session.messages = [
  {role: "user", content: "...", capability: "chat", seq: 1},
  {role: "user", content: "...", capability: "deep_solve", seq: 3},
  {role: "user", content: "...", capability: "visualize", seq: 5},
  // 同一 session_id，不同 capability 共存
]
```

### 6 Capability 完整对照（官方一句话 + 实际场景）

| Capability | 官方一句话 | 处理阶段 | 默认工具 | 输出格式 | 典型场景 |
|---|---|---|---|---|---|
| **Chat** | Fluid, tool-augmented conversation | 4 stage (T-A-O-R) | 用户勾选（6 工具） | Markdown 流式 | "解释光合作用"（30s 答） |
| **Deep Solve** | Multi-agent problem solving: plan, investigate, solve, verify | 3 stage (P-Re-W) | rag/web/code/reason | 分阶段 Markdown | 数学证明 / 编程 bug / 物理计算 |
| **Quiz Generation** | Generate assessments grounded in your knowledge base | 2 stage (Idea-Gen) | rag/web/code | JSON Q&A | 自动出题 / 模仿真题风格 |
| **Deep Research** | Decompose into subtopics, dispatch parallel research agents | 4 stage (Reph-Decomp-Res-Rep) | 用户选 sources(kb/web/papers) | Markdown 报告 + 引用 | 文献综述 / 跨源对比 |
| **Math Animator** | Turn math concepts into Manim visual animations | 6 stage | 无（LLM code-gen） | MP4/PNG/GIF | 微积分极限可视化 / 傅里叶变换演示 |
| **Visualize** | Generate SVG/Chart.js/Mermaid/HTML | 3 stage | 无（LLM code-gen） | SVG/Chart/HTML | 数据图表 / UML / 流程图 |
**User：我看到 deeptutor 是有CIL 界面，那么 CIL 可以满足 chat 所提供的这 6 种命令吗？**
**我拿 claude code desktop 举例，它背后运行 claude code cil session ，但是我们前端又有出色的交互界面，所以我是期望 deeptutor 最好也是可以原生和我的本地文件进行交互，请你查看一下官方源码和社区 issue。因为我看交互方式还有Python sdk 和 CIL；### Book Engine — 交互式「活书」 这一点我看重的是他能把我在原白板上的整个分析过程整合起来最终也是生成一个我易于阅读的活书，请你启动并行 agent deep explore 给我回复，关于这几点的明确支持力度**


### Chat 工具选择的三种模式

1. **Chat**：用户动态勾选（最灵活，6 工具任选）
2. **Deep Solve / Quiz / Research**：固定 manifest（预定义工作流）
3. **Math Animator / Visualize**：无工具（纯 LLM code-gen）

---

## 三、TutorBot 7 特性详解（Agent B + E 整合）

### TutorBot 创建表单（4 字段，2 分钟完成）

```yaml
Name: "CS 61B 期末考试导师"        # 必填，自动派生 bot_id (kebab-case)
Description: "帮助准备数据结构期末"  # 可选
Soul: |                            # 必填（5 模板：Default/Math/Coding/Research/Language）
  # Soul
  我是 CS 61B 期末考试导师...
Model: claude-opus-4               # 可选（系统默认 / 自定义 LLM）
```

点 "Create & Start" → 后端立即:
- 创建 9 个目录树（`data/tutorbot/{bot_id}/{config.yaml,workspace/{SOUL,USER,TOOLS,AGENTS,HEARTBEAT}.md,workspace/{sessions,memory,skills},cron,logs,media}`）
- 启动 3 个 asyncio 任务（agent loop / outbound router / heartbeat service）

### 7 特性完整对照（官方一句话 + 实际行为）

| 特性                         | 官方一句话                                                                                | 实际行为                                                                |
| -------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| **Soul Templates**         | Editable Soul files for personality / tone / teaching philosophy                     | 5 预设（Socratic/encouraging/rigorous）+ 自定义 Markdown，定义 system prompt  |
| **Independent Workspace**  | Each bot 有 own directory with separate memory, sessions, skills, configuration       | `data/tutorbot/{bot_id}/workspace/` 完全隔离                            |
| **Proactive Heartbeat**    | Bots don't just respond — they initiate. Recurring study check-ins, review reminders | 每 30min 自动 tick → LLM 决策 HEARTBEAT.md 任务 → 主动推送 WebSocket           |
| **Full Tool Access**       | RAG / code / web / paper / reasoning / brainstorm 全部                                 | 与 Chat 工具池共享，但 + ReadFileTool/WriteFileTool/Edit/List/Exec          |
| **Skill Learning**         | 加 SKILL.md 文件 → bot 学新能力                                                             | 12+ 内置 skills（github/weather/summarize/cron 等），workspace/skills/ 可加 |
| **Multi-Channel Presence** | Telegram / Discord / Slack / 飞书 / 企业微信 / 钉钉 / Email                                  | 12+ 渠道，schema-driven form 配置                                        |
| **Team & Sub-Agents**      | Spawn 后台 sub-agents 或 multi-agent teams                                              | TeamTool + sub-agent 协作（复杂长任务）                                      |

### Heartbeat 真实使用例子（Agent B）

```markdown
# HEARTBEAT.md（用户编辑）
## Active Tasks
- 今天目标：完成红黑树 rotation 理解
- 生成 3 道红黑树 insertion 习题（中等难度）
- 检查我之前提交的 hw5.py，重点看树的 delete 逻辑

## Completed
- AVL 树讲解 ✓
```

**自动触发流程**:
1. 30 min 后 `_tick()` 读 HEARTBEAT.md
2. Phase 1: LLM 决策 `{"action": "run", "tasks": "..."}`
3. Phase 2: agent loop 执行 → 生成习题 + 代码 review
4. Phase 3: WebSocket 推送 + 可选转发 Telegram/Discord 群

---

## 四、"One Thread" vs "Multi-Bot" 数据架构对比

### Chat 数据架构（SQLite + URL 寻址）

```
浏览器 URL: /chat/unified_abc123
       ↓
SQLite chat_history.db
  ├── sessions 表（id, title, created_at, updated_at, mode, preferences_json）
  └── messages 表（session_id, role, content, capability, seq, events）

侧栏 = 最近 50 个 session（按 updated_at DESC）
关闭浏览器再打开 → URL 直达恢复 session
```

### TutorBot 数据架构（JSONL + bot-centric）

```
data/tutorbot/cs-61b-tutor/
  ├── config.yaml          (name, persona, model, channels)
  ├── workspace/
  │   ├── SOUL.md          (system prompt)
  │   ├── USER.md          (用户偏好 / profile)
  │   ├── TOOLS.md         (可用工具说明)
  │   ├── AGENTS.md        (sub-agents 配置)
  │   ├── HEARTBEAT.md     (定时任务)
  │   ├── sessions/
  │   │   ├── 2026-05-06.jsonl  (12 条消息)
  │   │   └── 2026-05-03.jsonl  (8 条消息)
  │   ├── memory/          (consolidated memory)
  │   └── skills/          (12+ 内置 + 自定义)
  └── logs/

侧栏 = 最近 3 个活跃 bot（按 sessions/*.jsonl mtime）
关闭浏览器再打开 → /agents → 选 bot → 加载最后 session
```

### 关键架构差异

| 维度 | Chat | TutorBot |
|---|---|---|
| 存储 | SQLite 集中 | JSONL 分布（per bot） |
| 寻址 | URL `/chat/{session_id}` | UI 导航 `/agents` → 选 bot |
| Memory 触发 | per-turn refresh（每条消息后异步） | per-consolidation（周期性批量） |
| 共享 memory | 用户级 SUMMARY/PROFILE 全局 | 每 bot 独立 + 共享 `data/memory/` |
| 跨 session 关联 | 同 session 内 4000 token 上下文 | 同 bot 跨 session JSONL 累积 |

---

## 五、5 学习场景决策矩阵（Agent C 提取）

| 场景                 | Chat    | TutorBot | 最终推荐                                         |
| ------------------ | ------- | -------- | -------------------------------------------- |
| **考试突击**（1-2 天）    | ✅ 首选    | ❌ 过载     | **Chat** — 简洁、快速出题                           |
| **长期备考**（2+ 周）     | ⚠️ 可用   | ✅ 首选     | **TutorBot** — 错题追踪 + Heartbeat 复习提醒         |
| **短论文**（1 周，3-5 页） | ✅ 首选    | ❌ 过载     | **Chat** — paper_search + Deep Research 一次完成 |
| **长论文**（3+ 周，8+ 页） | ⚠️ 可用   | ✅ 首选     | **TutorBot** — 进度追踪 + 已读论文记录 + Heartbeat 提醒  |
| **单次错题分析**         | ✅ 首选    | ❌ 过载     | **Chat** — Deep Solve 即时分析                   |
| **长期错题追踪**（1+ 月）   | ❌ 无法追踪  | ✅ 首选     | **TutorBot** — PROFILE.md 记弱点 + 自动生成变体题      |
| **快速学新概念**         | ✅ 首选    | ❌ 过载     | **Chat** — Math Animator + Visualize 直观      |
| **深度理解新概念**        | ❌ 表面化   | ✅ 首选     | **TutorBot** — Socratic persona 引导思考         |
| **单学科集中学**         | ✅ 首选    | ⚠️ 可用    | **Chat** — 单 thread 6 capability 切换          |
| **多学科并行学**         | ❌ 上下文混乱 | ✅ 首选     | **TutorBot** — N bots × 共享 PROFILE/SUMMARY   |

### 按学生类型推荐（Agent C）

- **普通大学生**: Chat 90% + TutorBot 10%（仅期末考前 1 周 / 论文截稿前 3 天）
- **研究生 / 准备考试**: TutorBot 60% + Chat 40%
- **K-12 / 自主学习者**: TutorBot 80%（Socratic persona）+ Chat 20%
- **跨学科学习者**: TutorBot × N（每学科一个）+ Chat 即时咨询

---

## 六、3 时间尺度用户旅程（Agent D 提取）

### 单次会话（30 分钟）

| 维度 | Chat | TutorBot |
|---|---|---|
| 默认入口 | `/chat`（自动 redirect） | `/agents`（bot 列表） |
| Session 创建 | WebSocket 自动（首条消息触发） | 手动选 bot → start_bot() |
| 关闭浏览器再打开 | URL 直达恢复 | 进 `/agents` → 选 bot → 加载最后 session |
| Chat history 列表 | 侧栏 50 个 session（搜索/重命名/删除） | 侧栏 3 个最近活跃 bot（无消息列表） |

### 一周连续学习（每天 30min × 7 天）

| 维度 | Chat | TutorBot |
|---|---|---|
| 数据积累 | 7 个独立 session（如每天新建）OR 同一 session（如点侧栏续） | 同一 bot → 单一 JSONL 持续追加 |
| Memory 更新 | per-turn refresh SUMMARY/PROFILE.md（成本高） | per-consolidation 批量（高效但可能丢细节） |
| 第 7 天能查到第 1 天 | ✅ 同 session 内 messages 表全部 | ✅ JSONL 追加，最近 100 条 `get_bot_history(limit=100)` |

### 一个月跨主题学习（CS + 数学 + 物理）

| 维度 | Chat | TutorBot |
|---|---|---|
| 多 thread 关联 | ❌ 无跨 session 引用机制 | ⚠️ 共享 `data/memory/` SUMMARY/PROFILE 间接关联 |
| 学科隔离 | 同 thread 学科混乱（4000 token 挤压） | N 个 bot 各管一学科，独立 SOUL.md |
| 跨学科提醒 | ❌ 无 | ✅ Heartbeat 综合 N bot 状态联动 |

---

## 七、HKUDS 设计哲学（Agent E 整合）

### 营销 vs 学术分层

```
                README.md（营销层）
              篇幅 Chat : TutorBot = 3.4:1
              Key Features 排序：Chat #1, TutorBot #6
              叙事重点："Six modes, one thread"
              目标用户：学生 / 一般学习者
                       ↓ 引流入口

                arXiv 2604.26962（学术层）
              "Agent-Native Architecture"
              叙事重点：autonomous agent loop + multi-instance
              目标用户：研究者 / 工程师
                       ↑ 深度差异化
```

### 6 个 Chat capability 名 + 7 个 TutorBot 特性 = 13 能力官方化

**Chat 关键词**（README 原文）:
1. "Six distinct modes" / "Six modes, one thread"
2. "Fluid, tool-augmented conversation"
3. "Unified context management system"
4. "Tools are decoupled from workflows"
5. "Mix and match as needed"
6. "Start with quick chat, escalate to Deep Solve, visualize, generate quiz, launch Deep Research — all in one continuous thread"

**TutorBot 关键词**（README 原文）:
1. **"Not a chatbot"**（明确反差）
2. "Persistent, multi-instance agent"
3. "Each TutorBot runs its own agent loop"
4. **"Bots don't just respond — they initiate"**
5. "Proactive Heartbeat"
6. **"Your tutor shows up even when you don't"**

### 设计哲学一句话

- **Chat**: 工作流 + 工具解耦的"渐进深化对话引擎"
- **TutorBot**: 持久化人格 + 主动循环的"长期学习陪伴智能体"

---

## 八、共同缺口 + Round-22 Canvas 5 大核心如何补全

### Agent D 发现的共同缺口

| 缺口 | Chat 现状 | TutorBot 现状 |
|---|---|---|
| **学习进度可视化** | ❌ 无 mastery dashboard | ❌ 无（USER.md 纯文本） |
| **答错题汇总自动推荐** | ⚠️ notebook_entries 表但无推荐 | ❌ 默认无 quiz tracking schema |
| **概念忘了怎么复习** | ❌ SUMMARY.md 不可精确搜 | ✅ bot 可存知识图（需自维护） |
| **跨概念追溯**（"3 周前在 admissibility 上犯的错"） | ❌ session 孤岛 | ⚠️ 共享 SUMMARY 但无 graph |

### Round-22 Canvas 5 大核心 = 完美补全

| Canvas 核心 | 补全的共同缺口 | 落地 Story |
|---|---|---|
| **OriginWhiteboard + wikilink 双链** | 跨概念追溯（vault graph 可遍历） | Story 10.5 Whiteboard |
| **MasteryDashboard (BKT + FSRS)** | 学习进度可视化 | Story 10.6 Day 7 |
| **ExamWhiteboard + AutoSCORE** | 答错题汇总 + 4 维评分 | Story 10.7 Day 8 |
| **ErrorCandidate (4 类错误归因)** | 错误模式自动识别 | Story 10.7 Day 8 |
| **Graphiti episodic memory** | 跨时间错误重现（事件因果链） | Story 10.8 Day 9 |

**关键判断**: Round-22 不是"覆盖 DeepTutor"是"**补全 Chat + TutorBot 共同缺口**"。

---

## 九、Day 2 实施路径（基于 Chat vs TutorBot 真实使用差异）

### 推荐路径：Phase A + Phase B + Phase C

#### Phase A: 应用层启用（**0 代码改动**）
- TutorBot ReadFileTool 沙箱已默认关闭（`manager.py:438`）
- 配置 fork .env 让默认 TutorBot 指向 vault：
  ```
  CANVAS_VAULT_PATH=/vault
  TUTORBOT_DEFAULT_WORKSPACE_LINK=/vault
  ```
- **效果**: 用户进入 `/agents` → 创建 bot → bot 自动能 read_file vault 任意路径

#### Phase B: 入口层引导（**30 min - 1h**）
- 修 `web/app/(workspace)/page.tsx`：
  ```typescript
  // OLD: router.replace("/chat")  // 默认进 Chat
  // NEW: router.replace(hasVaultMounted ? "/agents" : "/chat")
  ```
- 或在 Chat 加 "Switch to TutorBot Mode" 按钮（顶部 banner）
- 在 onboarding 加 vault 检测：如果有 vault → 推荐用 TutorBot

#### Phase C: 架构层兼容（**1.5-2 day 可选**）
- DocumentAdder vault_mode 参数（Agent C 之前调研）
- VaultMonitor polling daemon（5s 增量索引）
- 让 Chat 路径也能自动索引 vault（KB 不再强制 upload）

### 时间投入对比（基于 5 agent 调研）

| 工作量 | Round-22 主报告原估 | 5 agent 调研后真实估 |
|---|---|---|
| Day 2 总工作 | 0.5 day | **1.5-2 day**（含 Phase A+B+C） |
| Phase A only | — | **0.5h** |
| Phase A+B | — | **1.5h** |
| Phase A+B+C | — | **9-13h** |

---

## 十、关键决策点（用户需选）

### 决策 1: Day 2 实施范围

| 选项 | 描述 | 工作量 |
|---|---|---|
| A | 仅 Phase A（启用 TutorBot 直读 vault，用户主动用 TutorBot） | 0.5h |
| B | Phase A + Phase B（默认入口改 TutorBot 或加引导） | 1.5h |
| C | 完整 Phase A+B+C（含 KB 路径也支持 vault 直读） | 1.5-2 day |

### 决策 2: 用户主推哪条路径

| 选项 | DeepTutor 主路径 | Round-22 集成方向 |
|---|---|---|
| **TutorBot-first** | `/agents` 默认入口 + N 个 bot 协作 | Canvas 5 大核心 = TutorBot 工具集扩展 |
| **Chat-first** | `/chat` 默认入口 + 6 capability 切换 | Canvas 5 大核心 = Chat capability 加 2 个新模式（OriginWhiteboard / ExamWhiteboard） |
| **Hybrid** | 两者并存 + 用户自选 | Canvas 5 大核心 = 通用模块两端都能用 |

### 决策 3: Onboarding 引导

| 选项 | 用户首次看到 | 引流逻辑 |
|---|---|---|
| **保持现状** | `/chat` 空对话框 | 学生友好，但 D2 vault 直读优势不显 |
| **改 redirect** | `/agents` bot 列表 + "Create CS 61B Tutor" 按钮 | TutorBot 主推，符合 D2 用户初衷 |
| **首次引导向导** | "你是学生 (Chat) / 长期学习者 (TutorBot)?" | 用户自选，平衡 |

---

## 十一、关联文档

- **Round-22 主报告**: `_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
- **Round-22 Deep Explore**: `_bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md`
- **Day 2 设计文档（vault 访问）**: `_bmad-output/research/round-22-day2-vault-access-design-2026-05-06.md`
- **Round-20 双 Agent 架构**: `_bmad-output/research/round-20-deeptutor-clone-deep-analysis-2026-05-06.md`（在父 worktree）
- **Epic-10 总览**: `_bmad-output/implementation-artifacts/epic-10/_README.md`
- **决策批注 D17**: `_bmad-output/决策批注/D17-round22-fork-mvp-2026-05-06.md`

---

## 十二、5 Agent 调研产物索引

| Agent | 主题                                     | 输出文件                             |
| ----- | -------------------------------------- | -------------------------------- |
| **A** | Chat 6 capability 详解 + "one thread" 实现 | `tasks/a51b38b8fe4e4e828.output` |
| **B** | TutorBot 实际工作流 + 30min 用户旅程            | `tasks/af5850fe896dccbc2.output` |
| **C** | 5 学习场景对比 + 决策矩阵                        | `tasks/a6f9beab015d3c351.output` |
| **D** | 用户旅程 3 时间尺度 + 共同缺口                     | `tasks/a2869a00d2d97bd70.output` |
| **E** | README 官方卖点 + HKUDS 设计哲学               | `tasks/a704a2768f709e756.output` |

---

*报告完成。回答用户问题"chat 和 agent 在原本设计的使用上功能有什么区别"——核心答案：HKUDS 故意双轨设计，Chat = 即时多模式 / TutorBot = 长期持久化，Round-22 Canvas 5 大核心补全两者共同缺口（mastery dashboard / 错误归因 / 跨时间追溯）。*
