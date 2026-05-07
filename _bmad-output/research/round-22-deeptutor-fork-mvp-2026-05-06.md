---
title: "Round-22 主决策报告 — DeepTutor Fork MVP"
date: 2026-05-06
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
status: "decision-locked"
supersedes: ["round-15 architecture-A 双系统", "round-19 Unix CLI 拆分", "round-21 25-30d 集成方案"]
revised_by: "2026-05-07 Round-22 二轮（6 报告深度调研收敛）"
revised_by_2: "2026-05-07 对抗性设计审查（Claude 5 Agent + ChatGPT GPT-5 Pro 第二意见）"
---

# Round-22 主决策报告 — DeepTutor Fork MVP

> **状态**：补创于 2026-05-07（原文件 `round-22-deeptutor-fork-mvp-2026-05-06.md` 在 Epic-10/11 多处引用但缺失，本文档作为 Round-22 决策的 single source of truth 收口）
>
> **决策核心**：用户 2026-05-06 拍板 — fork DeepTutor + 嵌入 Canvas 5 大核心 + 舍弃 Obsidian + 10 天 MVP 验证

---

## 用户原话（D17 锚定，一字不改）

> "我是想要舍弃 obsidian，直接把我们 Canvas learning systeam 思想在 deeptutor 实现，我的批注有列出来哪些 deeptutor 和我们 Canvas learning systeam 的思想和功能相对应，缺少功能我们就参考我们的 Canvas learning systeam 的源码集成。**我先试一下集成的效果先**"

—— 来源：决策批注 `D17-round22-fork-mvp-2026-05-06.md` L28

---

## 决策路径（Round-15 → Round-22 收敛）

```
Round-15 (2026-05-05): 用户首次提议 "先在 DeepTutor 改造"（L155）
   ↓
Round-16/17/18: 双后端 / Unix CLI / vault 直读 三方案探讨
   ↓
Round-19 (2026-05-06): D1 锁定 — 功能需求优先（L59）
   ↓
Round-20 (2026-05-06): D3 锁定 — 5 大核心权威定义（L222）
                       clone DeepTutor 实地验证 → 发现 TutorBot 已具备 Claude Code Desktop 风格
   ↓
Round-21 (2026-05-06): D4 锁定 — Graphiti 闭环贯穿（L1085）
                       M1-M13 13 条映射对锁定
   ↓
Round-22 主决策 (2026-05-06): D17 拍板 — Fork + 5 大核心嵌入 + 10d MVP
   ↓
Round-22 二轮 (2026-05-07): F1-F6 收敛 + D18 桌面化 → Epic-11 派生
   ↓
对抗性设计审查 (2026-05-07): 5 Agent + ChatGPT 第二意见 → S1/S2/S3 修订
```

---

## Canvas 5 大核心（D3 权威定义）

来源：用户 Round-20 L222 / Round-21 L32 原话

```
1. 原白板（OriginWhiteboard + wikilink 双链）
2. 检验白板（ExamWhiteboard + AutoSCORE 4 维评分）
3. 个人记忆系统在原白板和检验白板的应用（BKT + FSRS + Graphiti episodic）
4. 笔记精确返回系统（4 路融合 RAG）
5. 推测使用检验白板复习的系统（FSRS + 8 通道 Heartbeat 推送）
```

---

## 集成必要性（Round-22 Deep Explore 10 Agent 调研收敛）

5 个独立维度调研，全部指向同一结论：**Canvas 5 大核心 100% 必要、0 冗余**。

| Canvas 核心 | DeepTutor 现状 | 集成必要性 |
|---|---|---|
| 原白板 + wikilink 双链 | AI 推断 ConceptGraph + book 内孤立 + 跨 book 不复用 | ⛔ 必要补全 |
| 检验白板 + AutoSCORE | `is_correct` 二值，无 4 维 SOLO 评分 | ⛔ 必要补全 |
| 个人记忆系统（BKT + FSRS） | Notebook 扁平 + Memory 覆盖式无版本 | ⛔ 必要补全（DeepTutor 自留 `services/canvas/client.py` hook） |
| ErrorCandidate 4 类错误归因 | 无错误归因 | ⛔ 必要补全 |
| Graphiti episodic 闭环 | 覆盖式 markdown 无版本 | ⛔ 必要补全 |
| Whiteboard UI 主入口 | 无以图为入口的浏览模式 | ⛔ 调研补全 |

**13 条映射对（M1-M13）锁定**：见 Epic-10 _README §"M 映射对"。
**最强映射 M4**：DeepTutor Math Animator + Visualize ↔ Canvas 原白板讲题方式（用户 Round-21 L1063 "十分在意"）。

---

## 实施架构（10 天 MVP）

### 部署模式

```
┌─────────────────────────────────────┐
│  浏览器 (用户) :3782                │
└──────────────┬──────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────┐
│  DeepTutor Next.js v16 + React 19   │
│  output: "standalone" mode          │
└──────────────┬──────────────────────┘
               │ HTTP (本地)
┌──────────────▼──────────────────────┐
│  DeepTutor FastAPI :8001            │
│  + wikilink_proxy_router            │
│  + exam_proxy_router                │
└──────────────┬──────────────────────┘
               │ host.docker.internal:8011
┌──────────────▼──────────────────────┐
│  Canvas FastAPI :8011               │
│  + wikilink_graph_service           │
│  + exam_service / autoscore         │
│  + mastery_engine (BKT+FSRS)        │
│  + notification_channels (8 通道)   │
└──────────────┬──────────────────────┘
               │
       ┌───────▼─────────┐
       │  Neo4j :7691    │
       │  LanceDB        │
       │  bge-m3 (Ollama)│
       │  Graphiti       │
       └─────────────────┘
```

### 端口矩阵

| 服务 | 端口 | 用途 |
|---|---|---|
| DeepTutor frontend | :3782 | Next.js standalone server |
| DeepTutor backend | :8001 | FastAPI（含 proxy router） |
| Canvas backend | :8011 | FastAPI 5 大核心服务 |
| Neo4j Bolt | :7691 | KG 存储 |
| Neo4j HTTP | :7478 | KG REST |

### Vault 路径

```
~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp/canvas-vault/
  ├── 原白板/      # 学习 MOC（白板本身是 md）
  ├── 节点/        # 概念节点扁平池
  ├── 检验白板/    # 检验白板 md
  └── .obsidian/   # obsidiantools 兼容（即使废弃 Obsidian 仍保留结构）
```

通过 docker bind mount 注入到容器 `/vault`。

---

## 5 验证场景（Day 10 UAT 通过 = MVP 成功）

| # | 场景 | 通过标准 | Day | Story |
|---|---|---|---|---|
| **S1** | DeepTutor 写 `[[recursion]]` → 自动完成 → 点击跳转 | wikilink 跳转 < 1s | Day 1-2 | 10.2 |
| **S2** | 右键 callout → "Generate Quiz via Canvas ACP" → mastery 更新 | 后端调 Canvas endpoint | Day 4 | 10.4 |
| **S3** | 答题 → AutoSCORE 4 维评分 → Dashboard 显示 | mastery.value 改变 | Day 7 | 10.6 |
| **S4** | Whiteboard 显示节点 + wikilink 边 | ≥10 节点 + 边渲染 | Day 5-6 | 10.5 |
| **S5** | 答错 → 错误日志 → Day 0/3/7 推送 | console 显示 `[REVIEW DUE]` | Day 8 | 10.7 |
| **S6**（新） | Graphiti 闭环：错误 → episode → 复习时多 hop 检索关联错题 | 复习推送显示历史关联错题 | Day 8 | 10.7 + 10.9 |

> **S6 新增依据**：用户 D4（Round-21 L1085）"整个闭环必须由 Graphiti 后端贯穿"。对抗性审查发现 D4 在 Epic-10 仅 Story 10.8 写入未读取，升 Epic 级 AC #6（详见 Epic-10 _README）。

---

## Round-22 二轮修订（6 项调研发现 F1-F6）

详见各子报告：
- **F1** Guided Learning v1.2.0 删除（Book Engine 继任）— `round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md`
- **F2** Math/Visualize 100% server-side 渲染 — `round-22-desktop-app-rendering-deep-explore-2026-05-07.md`
- **F3** Electron + AnythingLLM 模式选定（Tauri 淘汰）— 同上
- **F4** Day 2 Vault 工作量 4h → 1.5-2 day（Phase A/B 拆分）— `round-22-day2-vault-access-design-2026-05-06.md`
- **F5** Chat 6 cap + TutorBot 7 features 双轨 — `round-22-chat-vs-tutorbot-usage-comparison-2026-05-06.md`
- **F6** ReactFlow 选定（Cytoscape 闲置）— Day 0 实测 + CLI/SDK 报告

---

## 对抗性审查修订（2026-05-07 Claude 5 Agent + ChatGPT GPT-5 Pro 第二意见）

详见 `round-22-adversarial-design-review-epic-10-11-2026-05-07.md`。

### S1 决策（Canvas backend + Neo4j 在 Epic-11 怎么跑）

**ChatGPT 推荐 C+ 方案锁定**：保留 Docker compose 编排所有服务（Canvas + Neo4j + DeepTutor backend），Electron 仅做 GUI 包装 + 服务 supervisor，**不嵌入 Neo4j**。

**理由**：
- ChatGPT 实际查 fork next.config.js 验证 `output: "standalone"`（已是 SSR 模式）
- Canvas backend 200+ 行业务代码 + Neo4j Cypher 查询 + LanceDB + bge-m3 + Graphiti，用户 Day 0-10 已验证的链路不应推翻
- Neo4j 嵌入需要 JRE（包大 +200MB）或 sqlite 重写所有 Cypher（推翻 Story 10.2）

**用户层面影响**：装机时需装 Docker Desktop（一次性 600MB 下载），日常启动多 5-10s 但所有功能保留。

### S2 决策（Next.js mode）

**ChatGPT 推荐 standalone SSR 锁定**：Electron main 进程 spawn `node .next/standalone/server.js` + BrowserWindow 加载 `http://127.0.0.1:<port>`，**不走 SSG file://**。

**理由**：
- DeepTutor `web/next.config.js` 实际配置就是 `output: "standalone"`
- DeepTutor `web/package.json` 只有 `next build` / `next start`，无 `next export` 线路
- 走 SSG 会丢 Next.js API routes，与 D18 选 Electron 的根本理由对立

### S3 决策（MP4 URL 协议）

**ChatGPT 推荐继续 HTTP，不强制迁 file://**：需要本地文件用 `media://` / `app://` 自定义协议（Electron main 注册），不暴露裸 file://。

**理由**：DeepTutor 已有后端静态输出挂载机制 + `NEXT_PUBLIC_API_BASE` 构造 HTTP URL，天然适合 `http://127.0.0.1:<backend>` 的 MP4 URL。file:// 暴露绝对路径有隐私风险。

### H3+H4+M1（升 Epic 级 AC #6）

**ChatGPT 推荐升 AC**：Epic-10 加 Epic 级 AC #6 "Graphiti 闭环" — 错误产生 → episode → 出题 → 推送 → 复习时召回历史 mastery / 错因。详见 Epic-10 _README。

### H5（NEG-1 澄清）

**ChatGPT 推荐改文案 + 加 guardrail**：Story 10.5 路由改名（"全局学习地图"），加 NEG-1 guardrail — 只展示用户显式 wikilink / 用户创建边，**禁止 AI 自动新增跨白板边**。

---

## 用户主权约束（NEG 反对批注）

| NEG # | 反对内容 | 来源 |
|---|---|---|
| NEG-1 | 不做跨白板自动关联（AI 不自动建边） | Round-12 |
| NEG-2 | 不上传 vault 文件（直接访问指定文件夹） | Round-18 L805 |
| NEG-3 | MVP 期间不 git pull upstream | Round-22（DeepTutor 30 天 24 release） |
| NEG-4 | Graphiti 不替代 wikilink RAG（事件存储） | Round-12 |
| NEG-5 | 不要"集成 Canvas 模块"，是写新代码 | Round-19 L59 |
| NEG-6 | Desktop 不强制使用，Web 双轨并存 | D18 派生 |
| NEG-7 | 不绕过用户选 vault（首次必须 modal 选择） | D18 派生 |
| NEG-8 | 跨时间错误重现降级 P2（学术 near-zero） | Round-15 |

---

## Epic 派生

| Epic | 范围 | 触发 | 状态 |
|---|---|---|---|
| **Epic-10** | DeepTutor Fork + 5 大核心 MVP（Day 0-10） | 用户 D17 拍板 | in-progress（10.1/10.2 done） |
| **Epic-11** | Electron Desktop App（Day 11+） | Epic-10 Day 10 UAT 全 PASS + 用户 Path A 选定 | backlog |

---

## 关联文档

### 决策批注
- `_bmad-output/决策批注/D17-round22-fork-mvp-2026-05-06.md` — D17 主决策原文
- `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md` — D18 桌面化决策

### Round-22 6 子报告
- `round-22-deeptutor-deep-explore-2026-05-06.md` — 10 Agent 5 大核心可行性整合
- `round-22-day2-vault-access-design-2026-05-06.md` — Day 2 Phase A/B vault 设计
- `round-22-chat-vs-tutorbot-usage-comparison-2026-05-06.md` — Chat 6 vs TutorBot 7 决策矩阵
- `round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md` — Book Engine 继承 Guided Learning
- `round-22-desktop-app-rendering-deep-explore-2026-05-07.md` — Math/Visualize + Electron 决策

### 对抗性审查
- `round-22-adversarial-design-review-epic-10-11-2026-05-07.md` — Claude 5 Agent + ChatGPT 综合审查
- `chatgpt-prompt-epic-10-11-design-review-2026-05-07.md` — ChatGPT 第二意见提示词

### Epic 文档
- `_bmad-output/implementation-artifacts/epic-10/_README.md`
- `_bmad-output/implementation-artifacts/epic-11/_README.md`

### Memory
- `~/.claude/projects/-Users-Heishing-Desktop-canvas-canvas-learning-system/memory/decision_round22_fork_mvp.md`

---

*Round-22 主决策报告。所有 Epic-10/11 spec 必须引用本文件 + 对应 Round-22 子报告章节。*
*生成日期：2026-05-07（补创）/ 决策日期：2026-05-06（D17）/ 修订日期：2026-05-07（对抗性审查）*
