# DeepTutor CLI / Python SDK / Book Engine 深度调研报告

> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **调研日期**: 2026-05-07
> **调研方法**: 5 Agent 并行 Deep Explore（产品架构 + 入口能力 + 集成路径）
> **触发问题**: 用户批注 3 个核心问题
> 1. DeepTutor CLI 是否能满足 Web Chat 6 capability？
> 2. Python SDK + 本地文件交互（Claude Code Desktop 对标）支持力度？
> 3. Book Engine 能否把"原白板分析过程"整合为易读活书？

---

## Executive Summary（核心结论）

**🚨 重大发现：Guided Learning 已在 v1.2.0 完全删除（~5300 行代码移除），Book Engine 是其继任者。**用户截图的官方架构图是**过时营销描述**。

**3 个核心问题的明确答案**：

1. **CLI 完整覆盖 6 capability ✅** — `deeptutor run <capability>` 100% 支持，与 Web 共享 DeepTutorApp 执行引擎，资源管理（kb/session/notebook）甚至优于 Web
2. **本地文件交互对标 Claude Code Desktop** — 只有 **TutorBot via Python SDK** 是等价物（沙箱默认关闭 + ReadFile/WriteFile/Edit/List 完整工具）。Web Chat / CLI Chat **都不支持**直读 host 文件
3. **Book Engine 整合"分析过程→活书" ✅ 架构 100% 支持** — 但缺 5 个 vault 适配模块，工作量 5-7 day（与 Round-22 Story 10.4 一致）

---

## 一、5 Agent 整合发现矩阵

| Agent | 关键发现 | 对 Round-22 D2 影响 |
|---|---|---|
| **A** CLI 完整能力 | 6 capability 100% 通过 `deeptutor run` 执行 + CLI 资源管理 > Web | CLI 是 Web 的功能平级覆盖（不是子集） |
| **B** Python SDK 真实存在 | `DeepTutorApp` + `TurnRequest` + `CapabilityAvailability` 3 公开类 + 完整性 3/5 ⭐ | SDK 适合嵌入 Jupyter / 自己 FastAPI 项目 |
| **C** 三 Entry Point 文件访问 | Web/CLI Chat 都无文件工具；TutorBot via SDK 是唯一接近 Claude Code Desktop 的入口 | Day 2 Phase A 路径锁定为 TutorBot |
| **D** Book Engine 整合 | 5 阶段管道 + 14 BlockType + confirm-spine API 全就绪；缺 5 个 vault 适配模块（5-7d 工作量） | Round-22 Story 10.4 路径 B 验证一致 |
| **E** Guided Learning 新发现 | **v1.2.0 完全删除**，Book Engine 取代 | 架构图过时，Book 是用户期望落地点 |

---

## 二、Q1: CLI 是否覆盖 Chat 6 capability？

### 答案：✅ 100% 覆盖（CLI 与 Web 共享 DeepTutorApp facade）

```bash
# 6 capability 全部 CLI 可执行
deeptutor run chat "解释递归" -l zh -f json
deeptutor run deep_solve "证明 √2 是无理数" -t rag --kb math
deeptutor run deep_question "微积分" --config num_questions=10 --config difficulty=hard  # 别名: quiz
deeptutor run deep_research "Transformer 演进" --config mode=report
deeptutor run math_animator "正弦曲线变换" --config quality=high
deeptutor run visualize "递归树" -f json
```

### CLI 与 Web 双引擎架构

```
DeepTutor 统一核心
  Capabilities (6) + Tools (6+) + Services (LLM/Embedding/Memory/...)
            ▲
            │
    ┌───────┴────────┐
    │ DeepTutorApp   │  ← facade.py (207 行 stable application-layer)
    │ (start_turn,   │
    │  stream_turn)  │
    └───┬────────┬───┘
        │        │
    ┌───▼──┐ ┌──▼────┐ ┌──────┐
    │ CLI  │ │  Web  │ │ SDK  │  ← 3 Entry Points（架构图正确）
    └──────┘ └───────┘ └──────┘
```

### CLI 优于 Web 的功能（资源管理）

| 功能 | CLI | Web |
|---|---|---|
| KB 完整 CRUD | ✅ `kb create/add/search/delete` | ⚠️ UI 受限 |
| Session 操作 | ✅ `session show/rename/delete` JSON 输出 | ⚠️ 仅列表 |
| Notebook 文件 I/O | ✅ `notebook add-md/replace-md` | ⚠️ UI 输入 |
| 批量脚本化 | ✅ shell pipe / cron / CI/CD | ❌ |
| JSON 输出 | ✅ `-f json` agent-friendly | ❌ |

### Web 独占功能

- **Co-Writer** (`/co_writer` 路由) — 实时多文档协作编辑
- **Book 编译** (`/book` 完整 UI) — BookCreator + SpineEditor + PageReader
- **可视化渲染** — SVG/Chart.js/Mermaid 浏览器内即时展示
- **Skill 编辑器** — 可视化模板编辑

### 关键限制：CLI 不支持 `bot send`

```bash
deeptutor bot list / create / start / stop  # ✅ 生命周期支持
deeptutor bot send <bot_id> <message>        # ❌ 不存在
# 与 TutorBot 对话必须通过 Telegram/Discord/Slack 或 Web UI
```

---

## 三、Q2: Python SDK + 本地文件交互（Claude Code Desktop 对标）

### SDK 真实存在 ✅（但完整性 3/5 ⭐）

**3 个公开类**（`deeptutor/app/__init__.py`）:
- `DeepTutorApp` — 统一应用 facade
- `TurnRequest` — 单次对话参数封装
- `CapabilityAvailability` — 能力可用性元数据

**6 capability 程序化调用示例**:

```python
import asyncio
from deeptutor.app import DeepTutorApp, TurnRequest

async def main():
    app = DeepTutorApp()
    
    # Chat
    req = TurnRequest(content="解释递归", capability="chat", language="zh", tools=["rag"])
    session, turn = await app.start_turn(req)
    async for event in app.stream_turn(turn["id"]):
        print(event)
    
    # Deep Solve / Quiz / Research / Math Animator / Visualize 同模式

asyncio.run(main())
```

### SDK 集成场景（嵌入到自己项目）

| 场景 | 示例 |
|---|---|
| Jupyter Notebook | `from deeptutor.app import DeepTutorApp; app = DeepTutorApp()` |
| 自己 FastAPI | `@api.post("/tutor/chat")` 包装 `app.start_turn` |
| Agent 工具调用 | Claude/GPT 代理通过 TurnRequest 调用 DeepTutor |

### 三 Entry Point × 文件访问能力对比表

| 行为 | Web Chat | CLI Chat | TutorBot via SDK | Claude Code Desktop |
|---|---|---|---|---|
| 直接读本地文件 | ❌ | ❌ | ✅ | ✅（0 配置） |
| 直接写文件 | ❌ | ❌ | ✅ | ✅ |
| 编辑文件（edit_file） | ❌ | ❌ | ✅ | ✅ |
| 列目录（list_dir） | ❌ | ❌ | ✅ | ✅ |
| 沙箱默认状态 | N/A | N/A | **关闭**（manager.py:438） | 可选限制 |
| AI 主动 I/O | ❌ | ❌ | ✅ Agent loop | ✅ |
| 自动 cwd 上下文 | ❌ | ❌ | ❌（需显式 workspace） | ✅ |
| 用户 0 配置启动 | ✅ | ✅ | ❌（需创建 bot） | ✅ |

### 关键代码证据

**Web/CLI Chat 缺文件工具**（`deeptutor/agents/chat/agentic_pipeline.py:44`）:
```python
BUILTIN_TOOL_NAMES = ("brainstorm", "rag", "web_search", "code_execution", "reason", "paper_search")
# 6 个内置工具 — 无 ReadFile/WriteFile
```

**TutorBot 沙箱关闭**（`deeptutor/services/tutorbot/manager.py:438`）:
```python
restrict_to_workspace=False,  # 沙箱默认关闭
```

**TutorBot 文件工具完整**（`deeptutor/tutorbot/agent/tools/filesystem.py:42-122`）:
- ReadFileTool（offset/limit 分页 + 128K 字符上限）
- WriteFileTool / EditFileTool / ListDirTool

### Day 2 改造方案（让 Web/CLI Chat 也支持文件直读）

| 步骤 | 文件 | 改动 |
|---|---|---|
| P0 | `deeptutor/app/facade.py` | TurnRequest 加 `file_paths: list[str]` + `allowed_workspace: str` |
| P1 | `deeptutor/api/routers/chat.py` | Chat Router 检查 file_paths → 读取 + 注入 message context |
| P2 | `deeptutor/agents/chat/` | ChatAgent 可选注入 ReadFileTool（非默认） |
| P3 | 沙箱白名单 | 限制 `allowed_workspace` 路径（防系统文件泄漏） |
| P4 | Web UI | "Local Files" 面板 / `[file: /path]` markdown 语法 |

### 推荐方案

**用户期望"原生本地文件交互"** → **Phase A: TutorBot via SDK**（0 代码改动，已就绪）

```python
from deeptutor.services.tutorbot.manager import TutorBotManager

manager = TutorBotManager()
bot = await manager.create(
    bot_id="vault-reader",
    workspace="/Users/Heishing/Desktop/canvas/canvas-vault"  # 自动获得文件读写
)
# AI 现在可以 read_file/write_file/edit_file/list_dir
```

---

## 四、Q3: Book Engine 整合"分析过程→活书"支持力度

### 答案：✅ 架构 100% 支持，需 5-7 day 改造（与 Round-22 Story 10.4 一致）

### Book Engine 5 阶段管道（已实装）

```
Stage 1: IdeationAgent
  输入：BookInputs (4 源融合 = user_intent + chat_selections + notebook_refs + KBs)
  输出：BookProposal（title / scope / target_level / estimated_chapters）

Stage 2: SourceExplorer + SpineSynthesizer
  - SourceExplorer 并行多查询 RAG（每 KB 4-8 个查询）
  - SpineSynthesizer Draft → Critique → Revise 3 轮 LLM
  - 后处理：拓扑排序 + 环去除 + 覆盖率补齐
  输出：Spine（chapters[] + ConceptGraph）

Stage 2.5: Overview Chapter 自动注入
  - Intro 文本块 + CONCEPT_GRAPH block（Mermaid）+ Chapter 索引
  - 完全确定性渲染（无 LLM）

Stage 3-4: BookCompiler
  - SectionArchitect 规划 blocks
  - 14 BlockType 4 phases 编译：
    Phase 1: TEXT, CALLOUT, QUIZ, USER_NOTE, PLACEHOLDER
    Phase 2: FIGURE, INTERACTIVE, ANIMATION, CODE, TIMELINE, FLASH_CARDS
    Phase 3: DEEP_DIVE
    Phase 4: SECTION, CONCEPT_GRAPH

Stage 5: Progress Tracking
  Progress 模型: current_page / visited_pages / quiz_attempts / weak_chapters / score
```

### 3 条映射路径对比

| 路径 | 描述 | 工作量 | 用户期望符合度 |
|---|---|---|---|
| **X** KB-Only | vault → KB upload → AI 重生成 book | 2-3d | ❌ 丢失结构 |
| **Y** CanvasVaultAdapter ⭐ | vault → 转 Spine JSON → confirm-spine API → 编译 14 blocks | 5-7d | ✅ **100% 保留 + 原生整合** |
| **Z** Co-Writer→Book | Co-Writer 编辑 → 转 Book | 现状无 API | ❌ 偏离 |

### 路径 Y 5 个新模块清单（与 Round-22 Story 10.4 完全对应）

| 优先级 | 模块 | 工作量 | 职责 |
|---|---|---|---|
| **P0** | CanvasVaultAdapter | 2d | vault 解析 + 结构提取 → PreSpine JSON |
| **P1** | VaultBlockGenerator | 1d | 回源 vault 获取 block 内容 |
| **P2** | CalloutAnnotationParser | 1d | `[!question]+` 等 callout → USER_NOTE block |
| **P3** | WikilinkGraphBuilder | 1d | `[[xxx]]` → ConceptEdge |
| **P4** | UserProgressExtractor | 1d | 从批注提取理解度评分 |

### Book 输入 4 源（关键限制：无 vault 直接输入）

```python
POST /books
{
  "user_intent": "...",          # 必填
  "knowledge_bases": [...],       # 可选
  "chat_selections": [...],       # 可选（最近 60 条 messages）
  "notebook_refs": [...],         # 可选
  "question_categories": [...],   # 可选
  "language": "zh"                # 可选
}
# ⚠️ 无 "vault_path" 字段——必须先转 4 源之一
```

**关键 API（路径 Y 通道）**:
```python
POST /books/confirm-spine
{
  "book_id": "...",
  "spine": <预构建的 Spine JSON>,  # CanvasVaultAdapter 输出
  "auto_compile": true
}
```

---

## 五、🚨 重大发现：Guided Learning 已在 v1.2.0 删除

### 历史轨迹

| 版本 | 日期 | Guided Learning 状态 |
|---|---|---|
| v1.0.0-beta.1 | 2026.04.04 | ✅ 存在（4 agents + 8 prompt YAMLs + Guide 页面） |
| v1.0.0-beta.3 | 2026.04.08 | ✅ 仍存在（KaTeX bug 修复） |
| v1.1.1 | 2026.04.17 | ✅ 仍存在（主题切换适配） |
| **v1.2.0** | **2026.04.20** | **❌ 完全移除（~5300 行代码删除）** |

### Release Notes 原文（一字不改）

> **Legacy Guided Learning Removed**
> The `deeptutor/agents/guide/` module (guide manager, 4 agents, 8 prompt YAMLs) and the entire `/guide` web UI (components, hooks, types, API router — ~5,300 lines) have been removed. **The Book Engine supersedes Guided Learning** with a richer, more extensible architecture.

### 为什么 Book Engine 优于 Guided Learning

| 维度 | Guided Learning（已删） | Book Engine（现） |
|---|---|---|
| 块类型 | 未记录 | 14 种（text/quiz/flashcard/animation/interactive/timeline/concept_graph 等） |
| 编译流水线 | 4 agents | 5 阶段（Ideation → Source → Spine → Planning → Compilation） |
| 用户控制 | 无 | 完整（proposal review / spine drag-drop / per-block edit） |
| KB 集成 | 基础 | 高级（health check + 增量 RAG + fingerprint tracking） |
| 与 Round-22 用户期望 | 50% 匹配 | **95%+ 匹配** |

### 当前 Sidebar 真实结构（v1.3.x）

```
1. Chat
2. TutorBot
3. Co-Writer
4. Book        ← 取代 Guided Learning（Library icon）
5. Knowledge
6. Space

无 Guided Learning 独立入口 ✓
```

### 营销话术与代码现实的差距

- 用户截图的官方架构图显示 4 Core Features 含 "Guided Learning"
- **代码现实只有 4 Core Features：Chat / Co-Writer / Book / TutorBot**
- 架构图保留 "Guided Learning" 命名是**营销话术过时遗留**
- **Book Engine 是 Guided Learning 的精确继任者**

---

## 六、3 Entry Points × 4 Core Features 完整能力矩阵

| Core Feature                      | Web                                      | CLI                                        | Python SDK           |
| --------------------------------- | ---------------------------------------- | ------------------------------------------ | -------------------- |
| **Chat Workspace** (6 capability) | ✅ 完整（实时流 + UI 渲染）                        | ✅ 6 capability 100% (`run`/`chat`)         | ✅ TurnRequest        |
| **Co-Writer**                     | ✅ 多文档协作编辑                                | ❌ 不支持                                      | ❌ 不支持                |
| **Book Engine**                   | ✅ BookCreator + SpineEditor + PageReader | ⚠️ 仅维护命令（list/health/refresh-fingerprints） | ❌ DeepTutorApp 未暴露   |
| **TutorBot**                      | ✅ UI 编辑 + Channels 配置 + Dashboard        | ⚠️ 仅生命周期（list/create/start/stop）           | ✅ TutorBotManager 完整 |
|                                   |                                          |                                            |                      |
**User：claude code desktop 是有 GUI 的，然后又操控后端的 claude code session 来对本地文件修改，我这里对于 web 的|   |   |**
**|---|---|**
**|数学动画|基于 Manim 将数学概念可视化为动画与分镜。|**
**|可视化|用自然语言描述生成交互式 SVG 图、Chart.js 图表、Mermaid 图或自包含 HTML 页面。|**
**这两点十分在意，我需要知道这两点能力在 CIL 和 SDK 是否有对应，然后如果没有这渲染的对应能力，那么是否可以把 Web 入口改造成本地的 app ，然后像 claude code desktop 既可以用相关的渲染，又可以操作后端的 CIL 操作文件**
### 用户场景 → Entry Point 推荐

| 场景 | 推荐入口 | 理由 |
|---|---|---|
| 即时问答 / 一次性研究 | Web Chat | 6 capability 切换 + 实时渲染 |
| 自动化批量任务 | CLI | shell pipe / cron / JSON 输出 |
| 嵌入 Jupyter / FastAPI | Python SDK | 程序化控制 + dict 输出 |
| 长期学习陪伴 | Web TutorBot | UI 编辑 Soul + Channels |
| 让 AI 直读 vault | **TutorBot via SDK** | **唯一 Claude Code Desktop 等价物** |
| 把分析过程→书 | **Book Engine via Web + Round-22 Story 10.4** | 架构 100% 就绪，需 5-7d 适配模块 |

---

## 七、Day 2 实施路径修订（基于本次调研）

### 修订要点

1. **Phase A 0 改动启用 TutorBot via SDK**（已就绪）：
   ```python
   bot = await manager.create(workspace=vault_path)
   # AI 立即能 read_file/write_file vault
   ```

2. **架构图 Guided Learning 是过时营销描述**——你的"vault → 易读活书"需求落地于 **Book Engine** 而非 Guided Learning

3. **Book Engine vault 整合 = Story 10.4 路径 B**：
   - CanvasVaultAdapter (P0, 2d)
   - VaultBlockGenerator (P1, 1d)
   - CalloutAnnotationParser (P2, 1d)
   - WikilinkGraphBuilder (P3, 1d)
   - UserProgressExtractor (P4, 1d)
   - 总计 5-7 day（与 Story 10.4 一致）

4. **SDK 完整性 3/5 ⭐ 暗示限制**：
   - 核心 capability 调用 ✅
   - 文件 I/O 通过 attachments 间接 ⚠️
   - Co-Writer / Book Engine 编译 API 未暴露 ❌
   - 没有官方 examples/sdk/ 文档

---

## 八、关联文档

- **Round-22 主报告**: `_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
- **Round-22 Deep Explore**: `_bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md`
- **Day 2 Vault 设计**: `_bmad-output/research/round-22-day2-vault-access-design-2026-05-06.md`
- **Chat vs TutorBot**: `_bmad-output/research/round-22-chat-vs-tutorbot-usage-comparison-2026-05-06.md`
- **本报告**: `_bmad-output/research/round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md`
- **Epic-10 Story 10.4** (CanvasVaultAdapter): `_bmad-output/implementation-artifacts/epic-10/10-4-day3-4-canvas-vault-adapter.md`

---

## 九、5 Agent 调研产物索引

| Agent | 主题 | 输出文件 |
|---|---|---|
| **A** | CLI 完整能力 + 6 capability × CLI 矩阵 | `tasks/a3489690f7e3cd43f.output` |
| **B** | Python SDK 真实存在性 + 完整性 3/5 ⭐ | `tasks/a8efc19336400e432.output` |
| **C** | 三 Entry Point × 文件访问能力 | `tasks/a04b5906410c22004.output` |
| **D** | Book Engine 5 阶段 + 14 BlockType + 路径 Y 5 模块 | `tasks/a704e07f6e8a82642.output` |
| **E** | **🚨 Guided Learning v1.2.0 删除** + Book 是继任者 | `tasks/a64875e3e39ae8e22.output` |

---

*报告完成。回答用户 3 核心问题：(Q1) CLI 100% 覆盖 6 capability；(Q2) TutorBot via SDK 是 Claude Code Desktop 唯一等价物，Web/CLI Chat 都缺文件工具；(Q3) Book Engine 架构 100% 支持"分析过程→活书"，需 5-7d 适配模块（= Round-22 Story 10.4）。**重大发现：Guided Learning 已删除，架构图过时，Book Engine 是用户期望的真实落地点。***
