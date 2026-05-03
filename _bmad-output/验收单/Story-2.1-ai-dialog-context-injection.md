---
story: "2.1"
title: "AI 对话 + 邻居上下文注入 v1.0（backend RAG 增强 / 路线 A 第 2 步）"
status: "review"
version: "v1.0"
date: "2026-05-02"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
unblocked_by: "Story 1.2/1.3 wikilink_graph_service 已 done (commit 4e0c27b)"
blocks: "2.2/2.3/2.4/2.5/2.6/2.7/2.8 (epics.md Epic 2 全部依赖 2.1)"
worktree_branch: "worktree-feature-obsidian-hybrid-dev"
backend_endpoint: "POST /api/v1/chat/enrich-context"
plugin_command: "canvas:chat-with-context (建议绑 Cmd+Shift+E)"
skill: "canvas-vault/.claude/skills/chat-with-context/SKILL.md"
---

# Story 2.1 验收单 v1.0 — AI 对话 + Backend RAG 上下文注入 ⭐

> [!success]+ 2026-05-02 v1.0 ship — Story 2.1 ready for review
> Epic 2 第 1 个 Story，完整端到端实施（plugin + Skill + backend service + endpoint + 50 backend tests）。
> 解锁 Epic 2 的剩余 7 个 Story（2.2-2.8 都依赖 2.1）。
>
> ## 主 ship
>
> | 资产 | 类型 | 行数 | 测试 |
> |---|---|---|---|
> | `wikilink_context_service.py` | new backend service | 180 | 19 ✅ |
> | `chat_context_assembler.py` | new backend service | 240 | 25 ✅ |
> | `chat.py` (endpoint) | new FastAPI endpoint | 110 | 6 ✅ |
> | `main.ts` (handleChatWithContext) | plugin handler | +131 | (集成待 5.4) |
> | `chat-with-context/SKILL.md` | new Claudian skill | 113 | — |
> | **main.js** (canvas-vault deploy) | plugin build | 83672→**88684**B (+5KB) | 98 ✅ |
>
> ## 5 AC 完成度
>
> | AC | 描述 | 状态 |
> |---|---|---|
> | #1 | 2-hop wikilink 遍历 + NeighborContext | ✅ 完成 |
> | #2 | LLM 上下文组装 + frontmatter/Tips/errors 注入 | ✅ 完成 |
> | #3 | token 预算压缩 + 公式/代码块保护（atomic 块算法）| ✅ 完成 |
> | #4 | LLM 首 token < 5s P95 | 🟡 待用户实测 / Task 5.4 性能测试推迟 |
> | #5 | 降级处理（graph_not_built / timeout / error）| ✅ 完成 + 通知文本 |

---

## 🎯 这个 Story 要做到什么

**一句话**：在节点页内按 `Cmd+Shift+E`，plugin 自动调 backend 拿到含 N-hop 邻居 + 你的学习历史（Tips/errors）的完整上下文，写剪贴板切到 Claudian，让 Claude 围绕笔记 + 邻居关系连贯回答你的问题。

---

## 📖 你的视角

**作为** 学习者，
**我想** 在 `节点/<concept>.md` 节点页内按 `Cmd+Shift+E`，plugin 把当前笔记 + N-hop 邻居（含 frontmatter / Tips / errors）打包发给 backend RAG 服务做 token 预算压缩 + LaTeX 公式保护，再切到 Claudian sidebar，
**以便** 我粘贴后 Claude 立即基于完整学习上下文回答，无需重复说明背景，比 Story 3.1 的纯本地 1-hop 更智能。

---

## 🖥️ 交互流程

```
打开 节点/Eigenvalues.md（或任意 节点/ 下的概念页）
        ↓
按 Cmd+Shift+E（用户在 Settings → Hotkeys 自绑命令"AI 对话 v2（backend RAG 上下文增强 + 切 Claudian）"）
        ↓
Plugin 检查 active file 是否在 节点/ 路径 → 通过
        ↓
Plugin 读取节点正文（剥 frontmatter）+ frontmatter
        ↓
POST http://localhost:8001/api/v1/chat/enrich-context
  Body: { node_path, current_note_content, current_note_frontmatter, max_hops: 2 }
        ↓
Backend wikilink_context_service.enrich_from_wikilink_graph (200ms 超时)
   → wikilink_graph_service.get_neighbors(node_path, hop=2)
   → NeighborNote × N → WikilinkNeighborContext × N (含 relationship_type 提取)
        ↓
Backend chat_context_assembler.assemble_context
   → Priority 1: 当前笔记全文
   → Priority 2: 1-hop frontmatter+Tips+errors
   → Priority 3: 1-hop content_summary
   → Priority 4: 2-hop frontmatter
   → Priority 5: 2-hop content_summary
   → tiktoken cl100k_base 计 token / 8192 budget / 公式 + 代码块 atomic 保护
        ↓
Plugin 收到 enriched_context (含降级通知 if any)
        ↓
Plugin 写剪贴板 (prompt = /chat-with-context + enriched_context + "请基于以上上下文回答..." 占位)
        ↓
Plugin Notice："已组装 backend RAG 上下文 X.XKB / Y 邻居 / Z/8192 tokens（XXms）切到 Claudian 粘贴"
+ 自动切 Claudian sidebar
        ↓
用户在 Claudian Cmd+V 粘贴
        ↓
Claudian 加载 chat-with-context Skill (canvas-vault/.claude/skills/chat-with-context/SKILL.md)
        ↓
Claude 解析 sections → 给开场白（节点速览 + 关键邻居 + 可问方向）
        ↓
（用户提问 → Claude 用注入的完整上下文 + 邻居关系作答）
```

---
**User：这里的上下文注入，你是学习 Karpathy 的 wiki 方式通过双向链接方式读取了链接的文档，然后同时 后端的 Graphiti 也是有把前端 md 文件之间联系构建了关系图谱然后读取，那么我要明确你这里用到了什么 RAG ，以及和 claude code 自己 Grap 文件来读 ，哪一个是更优的，我需要你在技术角度来 deep explore 这一点。**
## ✅ 验收清单（10 步 UAT，约 10 分钟）

> [!tip]+ 怎么用这份清单
> 每跑完一步，**点击 `- [ ]` 切换为 `[x]`**。
> 发现不对劲 → 选中那行 → `Cmd+Shift+A` 批 `❌ 错误`。

### 第 0 步：前置（必须）

- [ ] **P0**：Backend docker compose 已起：`cd backend && docker compose up -d`（应见 neo4j / ollama / fastapi 三容器健康）
- [ ] **P1**：Backend 健康：`curl http://localhost:8001/api/v1/chat/enrich-context -X POST -H "Content-Type: application/json" -d '{"node_path":"test","current_note_content":"test"}'` 应返回 JSON（含 degraded=true 因 graph 未 build，但 endpoint 工作）
- [ ] **P2**：Cmd+Q 完全退出 Obsidian → 重开（加载新 main.js）
- [ ] **P3**：main.js 大小 = **88684B**（`stat -f "%z" canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`）
- [ ] **P4**：Settings → Community plugins → Canvas Learning System 已启用 + Claudian 已装并登录

### 第 1 步：注册命令验证

- [ ] `Cmd+P` 命令面板搜 "canvas" → 应见 13 条命令（多 1 条："AI 对话 v2（backend RAG 上下文增强 + 切 Claudian）"）
- [ ] Settings → Hotkeys 搜 "AI 对话 v2" → 应找到对应条目
- [ ] 给它绑 `Cmd+Shift+E`（建议；其他键也行）

### 第 2 步：节点路径检查（边界测试）

- [ ] 打开任意**非节点**文件（如 `Dashboard.md` 或 `原白板/CS 61B.md`）
- [ ] 按 Cmd+Shift+E → 应弹 Notice"对话仅在 节点/ 下的概念页可用（当前 path: ...）"
- [ ] **不应**调 backend / **不应**写剪贴板 / **不应**切 Claudian

### 第 3 步：节点页 happy path（核心）

- [ ] 打开 `节点/Fundamentals.md`（或 vault 内任一节点）
- [ ] 按 Cmd+Shift+E
- [ ] 应见 Notice："已组装 backend RAG 上下文 X.XKB / Y 邻居 / Z/8192 tokens（XXms）切到 Claudian 粘贴"
- [ ] Claudian sidebar 自动打开

### 第 4 步：粘贴 + Skill 触发

- [ ] 在 Claudian 输入框按 `Cmd+V` 粘贴
- [ ] 看到一大段含 `/chat-with-context` 起头的 prompt
- [ ] prompt 中应有 `# 当前笔记: 节点/Fundamentals.md`
- [ ] prompt 中应有节点正文
- [ ] 如有邻居，应有 `## 1-hop 邻居 (frontmatter / Tips / errors)` section
- [ ] 末尾有 `请基于以上上下文回答我的问题。问题：（在这里输入）`
- [ ] 替换"（在这里输入）"为"什么是这个概念的核心定义？"→ Enter

### 第 5 步：Skill 开场白质量

- [ ] Claudian 加载 `chat-with-context` Skill
- [ ] Claude 第一条回复应含：
  - [ ] "✓ 已加载 backend RAG 增强上下文（XKB / N 邻居 / X/Y tokens）"
  - [ ] **节点速览**（一句概括）
  - [ ] **关键邻居**（列 2-3 个最相关的，含关系类型 + mastery 颜色 🔴🟡🟢）
  - [ ] **可问方向**（4 类：定义/关系/例子/出题）

### 第 6 步：AI 对话连贯性

- [ ] 问 Claude "什么是 [当前节点概念]的核心定义"
- [ ] Claude 应**优先用节点正文中的定义**作答（不重复要求你提供背景）
- [ ] 追问"和 [[<某邻居节点>]] 是什么关系" → Claude 应基于注入的邻居 metadata 回答（不捏造）

### 第 7 步：纯对话约束（不污染 vault）

- [ ] 整个对话过程，**不应**有任何文件被创建 / 修改
- [ ] 检查 `节点/` 目录文件数 = 对话前数量
- [ ] 如果你说"帮我把这个写下来"→ Claude 应回"派生新概念请用 /ai-linked-doc，本对话不会动 vault 文件"

### 第 8 步：Backend 降级路径

- [ ] 终止 backend：`docker compose down`
- [ ] 在节点页按 Cmd+Shift+E
- [ ] 应弹 Notice"❌ backend 未连接（fetch failed）请先 docker compose up 启动 Canvas 后端"
- [ ] **不应** 切 Claudian / **不应** 写剪贴板
- [ ] 重启 backend：`docker compose up -d`

### 第 9 步：Backend graph 未 build 降级

- [ ] Backend 起来但 wikilink graph 未 build（首次启动）
- [ ] 触发 Cmd+Shift+E
- [ ] Notice 中应见"⚠ wikilink_graph_not_built — 仅当前笔记"
- [ ] Claudian 仍能弹出，prompt 中末尾追加"邻居上下文暂时不可用..."通知
- [ ] Claude 开场白应明确说"backend 邻居上下文暂时不可用，本回答仅基于当前笔记"

### 第 10 步：对比 Story 3.1（node-chat）vs Story 2.1（chat-with-context）

- [ ] 同一个节点页
- [ ] Cmd+Shift+C（Story 3.1 plugin 端 1-hop） vs Cmd+Shift+E（Story 2.1 backend RAG N-hop）
- [ ] 对比剪贴板 prompt 内容差异：
  - Story 3.1: plugin 端组装，prompt 含 metadataCache.resolvedLinks 1-hop
  - Story 2.1: backend 组装，prompt 含 wikilink_graph N-hop + frontmatter Tips/errors + token 预算压缩

---

## 🚦 验收结果

### 全 10 步 ✅
→ 告诉我 "**Story 2.1 通过**"
→ 我 mark done + commit + 启动 **Story 2.2 supplementary-material-search**（路线 A 第 3 步：补充学习材料 RAG 搜索）

### 部分失败
→ 告诉我哪步 ❌ + 截图（粘贴 prompt + Notice 内容给我看）
→ 针对性修

### Backend 不响应
→ 检查 `docker compose ps` 看容器状态
→ Console (Cmd+Opt+I) 看 fetch error 详情
→ 验证 plugin Settings → Backend URL 是 `http://localhost:8001`

### Claudian 不识别 /chat-with-context
→ 检查 `canvas-vault/.claude/skills/chat-with-context/SKILL.md` 是否存在
→ Claudian 重启（Settings → Community plugins → 关再开 Claudian）

---

## 📝 你的批注区

> [!question]+ Story 2.1 v1.0 实测批注（2026-05-02 起）
>
> 跑完 10 步任意写下：
> - Backend RAG 上下文增强是否真"更智能"（vs Story 3.1 plugin 端 1-hop）
> - 邻居 metadata（Tips/errors/mastery）是否真注入了
> - token 预算是否合理（觉得 8192 够用 or 想调）
> - 公式 / 代码块保护是否生效（如果你的笔记含 LaTeX）
> - 降级提示是否清晰（backend 挂时用户能否理解）
> - Claudian Skill 开场白是否好用
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）

---

## 🔗 技术 spec 参考

- **Story spec**：`_bmad-output/implementation-artifacts/epic-2/2-1-ai-dialog-context-injection.md`
- **源代码**：
  - `backend/app/services/wikilink_context_service.py` (180 行 — Task 1+4 wikilink 遍历 + 降级)
  - `backend/app/services/chat_context_assembler.py` (240 行 — Task 2 token 预算 + 公式保护)
  - `backend/app/api/v1/endpoints/chat.py` (110 行 — Task 3 backend POST endpoint)
  - `backend/app/api/v1/router.py` (chat_router include)
  - `frontend/obsidian-plugin/src/main.ts` (handleChatWithContext +131 行 — Task 3 plugin handler)
  - `canvas-vault/.claude/skills/chat-with-context/SKILL.md` (113 行 — Task 3 Skill workflow)
- **单元测试**：
  - `backend/tests/unit/test_wikilink_context_service.py` (19 cases)
  - `backend/tests/unit/test_chat_context_assembler.py` (25 cases)
  - `backend/tests/unit/test_chat_endpoint.py` (6 cases)
  - 累计 **50 backend tests + 98 plugin tests = 148 tests all green**
- **Git commits**：
  - `fc27e44` Task 1+4 wikilink_context_service
  - `0d0c302` Task 2 chat_context_assembler
  - `0c45296` Task 3 backend chat endpoint
  - `06ecca5` Task 3 plugin + skill + 缺失源文件补齐
- **AC → 代码对应**：
  - AC #1 → wikilink_context_service.py:enrich_from_wikilink_graph
  - AC #2 → chat_context_assembler.py:assemble_context
  - AC #3 → chat_context_assembler.py:compress_content + _extract_atomic_blocks
  - AC #4 → 待 Task 5.4 性能测试 / 用户实测
  - AC #5 → wikilink_context_service.py:EnrichmentResult.degraded + chat.py:append notice

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "Story 2.1 通过" → mark done → 启动 **Story 2.2 supplementary-material-search**（~6h，补充学习材料 LanceDB RAG）
2. **部分 ❌** → 在批注区写清楚 + 截图，Claude 跑 `bmad-bmm-correct-course` 修
3. **想换路线** → 告诉 Claude 跳到 Epic 4 检验白板灵魂启动 / 或先做 Epic 5 BKT 算法心脏

---

## 🧭 Epic 2 全景 + Story 2.1 在闭环中的位置

```
Epic 1 done (17/17 + 4 MVP) ✅
   ↓
Story 1.2/1.3 wikilink_graph_service ✅ (commit 4e0c27b)
   ↓
Story 3.1 节点对话 v1 (plugin 端 1-hop) ⏳ review
   ↓
Story 2.1 AI 对话 v2 (backend RAG N-hop) ⏳ ← 本 Story
   ↓
Story 2.2 补充学习材料搜索 (LanceDB RAG)
   ↓
Story 2.3 历史误解提醒 (Graphiti 查询)
   ↓
Story 2.5 错误自动提取分类 (4 类双写 Graphiti + frontmatter)
   ↓
Story 2.6 对话归档三层 (Hot/Warm/Cold)
   ↓
（Epic 2 完成 → Epic 5 BKT/FSRS 算法心脏 + Epic 4 检验白板灵魂）
```
