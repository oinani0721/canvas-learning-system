# Canvas Learning System — Obsidian Hybrid Development (BMAD scoped)

> **此文件 scope = `_bmad-output/` 目录及子目录。**
> **claudeMdExcludes 已阻断父级 canvas-learning-system/CLAUDE.md（含 Tauri v0 误导内容）。**

---

## R4 核心工作流（用户 + Claude Code 角色契约）

### 用户（非技术 PM）的责任
1. **PRD/EPIC**: 用产品行为 + UX 期望描述（plain English / 中文，无 pseudo-code）
2. **Story 验证**: 每个 Story 实现后，**上手感受**功能是否符合预期
3. **批注反馈**: 在 _bmad-output/review/ 文档加 `[!question]+ [!error]+ [!tip]+` callout
4. **不审技术**: 不评 API 设计、库选型、文件结构、状态管理 — 这些 Claude Code 自决

### Claude Code 的责任
1. **自决技术**: 启动并行 Explore agent 在社区 deep explore，自主决定:
   - API 选型（如 requestUrl vs fetch vs SDK）
   - 库版本 + 依赖
   - 文件路径 + 函数命名
   - 状态管理 + 缓存策略
2. **拿不定 → ChatGPT Deep Research 提示词**: 当 deep explore 后仍无法决定时，给用户一段提示词，用户复制给 ChatGPT Deep Research 拿第二意见
3. **每个 Story 给用户上手 demo**: 实施后让用户能在 Obsidian 操作验证（无技术介入）
4. **接受批注循环**: 用户批注 → 读 → 调整 → 重新 demo

### ChatGPT Deep Research 升级触发条件

仅当下列情况触发：
- Explore agent 找不到社区先例
- 两个对立技术方案各有论据，无明显胜方
- 决策影响后续 5+ Story

**升级提示词模板**:

```markdown
# Tech Decision: [Story-ID] - [Decision-Name]

## Context
- Project: Canvas Learning System (Obsidian Hybrid + FastAPI + Neo4j + LanceDB)
- Existing patterns: [reference file paths]
- Story behavior expectation: [user's plain English]

## Question
[What specific tech choice is blocking?]
- Option A: [tech 1] — would [impact]
- Option B: [tech 2] — would [impact]

## Constraints
- Obsidian plugin (TS) + Claudian Skill (Markdown)
- Backend Python FastAPI async
- Neo4j (KG) + LanceDB (vector) + MCP (14 tools)
- LLM: Claude API + Gemini (only for Graphiti)
- No mock/stub; must connect real services

## What we tried
- Explore agents searched [paths]
- Found patterns in [files]
- Still unclear because: [what's missing]

## Desired output
1. Recommended approach + why
2. Implementation sketch (2-3 steps)
3. Risk + fallback
```

---

## 项目定位

**当前架构**: Obsidian Hybrid（已从 Tauri v0 降级）
- UI: Obsidian Editor + Claudian 侧栏
- Skill 引擎: Claude Code Skill (官方集成)
- 后端: FastAPI + Neo4j + LanceDB + Ollama bge-m3
- LLM: Claude API（主）+ Gemini（仅 Graphiti，episode_worker.py:287-394 硬锁）

**开发聚焦**: 你（Claude Code）此 session 在 `_bmad-output/` 工作目录。
sibling 代码目录通过 `--add-dir` 接入：
- `../backend/` — FastAPI + 28 服务
- `../frontend/obsidian-plugin/` — Obsidian 插件 (TS)
- `../canvas-vault/` — 验收 vault

**禁读** (`claudeMdExcludes` 已排除):
- `../CLAUDE.md` (Tauri 时期遗留)
- `../docs/` (Tauri 时期文档，已迁移到 ../archive/legacy-docs/)
- `../_decisions/` (旧 MVP 计划)

---

## 开发文档（你改动的文件）

- `implementation-artifacts/` — Story spec + sprint-status.yaml
- `../backend/app/` — 后端代码
- `../frontend/obsidian-plugin/src/` — Obsidian plugin 代码
- `../canvas-vault/` — 验收 vault（真实数据）

---

## 真相源（你只读，不改）

按优先级递减：

| 层 | 文件 | 优先度 | 用途 |
|---|---|---|---|
| 1 | `planning-artifacts/epics.md` | 5 星 | BDD + AC + Story 详情 |
| 2 | `planning-artifacts/prd.md` | 4 星 | 需求文本 |
| 3 | `planning-artifacts/architecture.md` | 3 星 | 技术约束 |
| 4 | `planning-artifacts/ux-design-specification.md` | 3 星 | UX 需求 |
| 5 | `planning-artifacts/recovered/prd-tauri-original-2ae5897.md` | 2 星 | Tauri v0 历史 |
| 6 | `research/obsidian-qa-round2-*.md` | 2 星 | 13 轮决策追溯 |
| 7 | `review/*.md` | 1 星 | 审计 + 用户批注 + UAT |

**外部锚定 PRD**: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (只读，pretool-guard 阻断修改)

---

## ⛔⛔⛔ Vault 扁平架构（2026-04-20 round-11 固化 — 对齐 Nick Milo Ideaverse）

> **来源**：用户 2026-04-20 批注"白板是 index.md 本身 / 节点扁平池 / 一 vault 一学科"。3 并行 Agent deep explore 确诊 = Nick Milo Ideaverse 官方 Atlas/Maps+Atlas/Notes 结构的精确镜像（社区 70,000+ 下载）。见 `_bmad-output/验收单/批注回复/Round-10-架构重设计.md`。

### Canvas Vault 目录规范（单学科 vault）

```
canvas-vault-<subject>/                    # 一 vault 一学科（例 canvas-vault-cs61b）
├── .canvas-config.yaml                    # vault 级配置（subject / vault_id / active_board）
├── 原白板/                                # 所有原白板 md（=学习 MOC）— 扁平
│   ├── CS 61B 数据结构.md                 # 白板本身是 md 文件（= 以前 index.md 语义）
│   └── BST.md
├── 节点/                                  # 所有概念节点 md — 扁平池（一 vault 一学科零重名）
│   ├── base-case.md
│   ├── recursion.md
│   └── eigenvalue.md
├── 检验白板/                              # 所有检验白板 md — 扁平
│   └── CS 61B 期末.md
├── raw/                                   # 原始课件 / 视频转录 / 图片
├── outputs/
│   └── exam_boards/                       # 检验白板输出
├── templates/                             # Templater 模板
└── .obsidian/
    ├── plugins/
    │   ├── canvas-learning-system/
    │   └── claudian/
    └── .claude/skills/
        ├── configure-whiteboard/
        └── ai-linked-doc/
```

### 弃用的旧结构（不要再出现在任何 spec/code/skill）

```
❌ wiki/canvases/<subject>/index.md         # 嵌套目录，弃用
❌ wiki/canvases/<subject>/<concept>.md     # 同上
❌ wiki/concepts/                           # Claudian 自由发挥的历史遗留
```

### 资产归属规则（违反 = 错配）

| 资产 | 正确位置 | 禁止位置 |
|---|---|---|
| 原白板 md（白板本身） | `原白板/<board>.md` | ❌ `wiki/canvases/<subject>/index.md` |
| 节点 md（概念） | `节点/<concept>.md`（扁平） | ❌ `wiki/canvases/<subject>/<concept>.md` / `wiki/concepts/` |
| 检验白板 md | `检验白板/<exam>.md` | ❌ `outputs/exam_boards/` 作白板（只放输出） |
| subject 字段 | **vault 级** `.canvas-config.yaml` 单一值 | ❌ 每个 md frontmatter 重复（retain `board_name` 即可） |

### subject 字段处置（round-11 固化）

- **一 vault 一学科** → subject 固化为 vault 级值
- **存储位置**：`canvas-vault-<subject>/.canvas-config.yaml` 的 `subject:` 字段
- **md 文件 frontmatter**：保留 `board_name`、去掉 `subject`（vault 级透明读取）
- **后端 P0 工作量留待下轮**（mastery_store / subject_resolver / memory_service 等 ~14-18h MVP 阶段非阻塞）
- **Skill 侧立即固化**：configure-whiteboard 和 ai-linked-doc 都从 `.canvas-config.yaml` 读 subject，不再向用户问

### 节点可见性（round-11 固化 = a 侧栏折叠但可点）

- 节点 md 物理位置 `节点/`，左栏文件树**默认折叠不展开**
- 用户主要通过"打开原白板 md → Cmd+Click 双链跳到节点"的路径工作
- **但** Cmd+Click 双链/命令面板搜索/wikilink 补全 **仍能打开节点 md**（兼容 PRD FR-CONV-01 + 未来 Story 3.x 节点对话）

### 中文目录名编码 QA（round-11 必跑）

中文目录 `原白板/节点/检验白板/` 有编码风险（Dataview / Bash mv / wikilink / Graph View filter）。实施必跑 **4 个编码边界测试**：

1. Bash: `mkdir "原白板"` 成功 + `ls "原白板"` 可查
2. Obsidian Graph View: Filters 输 `path:原白板/` 过滤生效
3. Wikilink: `[[原白板/CS 61B]]` 能自动补全 + 跳转
4. Dataview: `FROM "原白板"` query 无报错

任一失败 → 记入 Story 1.19 v4 的 deviation notes，降级到混合方案（目录英文 + frontmatter 中文）。

### Nick Milo 社区参考（设计一致性验证）

- Ideaverse Atlas/Maps = 原白板/
- Ideaverse Atlas/Notes = 节点/（扁平 atomic pool）
- 参考：https://www.linkingyourthinking.com/

---

## BMAD 流程（你的开发循环）

```
1. 用 bmad-bmm-create-story Skill 创建 Story (最小验收单位)
       下一步
2. 用户人工批注审核 Story spec
       下一步
3. 用 bmad-bmm-dev-story Skill 实施 AC（你 deep explore 自决技术）
       下一步
4. 你 ship 让用户能 hands-on 操作的 demo
       下一步
5. 用户用 UAT 矩阵验收（含"小白改进批注"列）
       下一步
6. 偏离时用对齐矩阵的"技术层 trace"诊断根因
       下一步
7. 用户批注 → 你 bmad-bmm-correct-course 调整 → 回 #3
```

---

## 4 MVP 优先功能

| # | 名称 | 类型 | Story | 优先级 | 工作量 |
|---|---|---|---|---|---|
| 1 | 批注 hotkey + 7 callout | Obsidian plugin | 1.16 | P0 | ~4h |
| 2 | AI 双链文档 + index.md 更新 | Obsidian plugin | 1.17 | P0 | ~10h |
| 3 | 原白板配置 | Claude Code Skill | 3.X | P1 | ~6h |
| 4 | Dashboard 一键考察 (MD MVP) | dashboard.md + Buttons URI | 1.18 | P1 | ~6h |

实施顺序: 1.16 (done) → **1.19 v4 (扁平架构 configure-whiteboard)** → 1.17 v4 (AI 双链 · 路径对齐) → 1.18 (Dashboard · Dataview FROM "原白板")

> **2026-04-20 round-8 顺序修正**：之前顺序 `1.16 → 1.17 → 1.18 → 3.X` 按工作量排序，但违反 Story 1.19 yaml `blocks: ["1.17","1.18"]` 和用户使用链路。3 并行 agent deep explore（2026-04-20）确诊：Story 1.19 是"用户打开 Canvas 第一件事"（onboarding 入口），没有白板 1.17 AI 双链 UAT 前置不成立、1.18 Dashboard 数据源为空。用户 2026-04-20 批注"双链提问节点的功能本身就是要在原白板里面使用的" + "我现在有一个在任意文件夹的 md 文件那么我想要从这个文件开始生成原白板" 精准命中此 bug。修正见 Round 4 Sec X4 正确依赖图（`review/epic-1-audit-response-round-4-2026-04-17.md:117-128`）。

---

## 技术决策（已锁，无需再问）

### Story 1.16 批注 hotkey
- Modal: `FuzzySuggestModal` (7 选项)
- Wrap: `editor.replaceSelection()` (cursor-aware)
- Callout 类型: 7 hardcoded (question/tip/error/hint/note/warning/info) + 可选 Callout Manager 检测
- Hotkey: `hotkeys: []` (用户自绑)

### Story 1.17 AI 双链
- Claude API: `requestUrl()` (Obsidian CORS bypass)
- API key: `app.secretStorage.get()` (Obsidian 1.5+)
- 文件创建: `vault.create()` (cache-aware)
- 新 tab: `workspace.openLinkText(name, '', true)`
- Wikilink: `app.fileManager.generateMarkdownLink()` (尊重用户偏好)
- index.md update: `setTimeout(200ms)` debounce 防 race

### Story 1.18 Dashboard
- 数据: Dataview DQL (vs inline JS)
- 触发: Buttons plugin `obsidian://execute?command=X`
- Bases: Phase 1 不用 (overkill)

### Story 3.X 原白板配置 Skill
- 参数: upfront `[name] [subject]` + AskUserQuestion 缺啥补啥
- 模板: 写 Templater JS template (用户开 Obsidian 时自动跑)
- index.md MOC schema 见 review/epic-1-audit-response-round-2-2026-04-17.md Sec N4

---

## 硬规则（来自父项目 CLAUDE.md，仍生效）

- DD-03 禁 mock：不写 stub / fake API / 空函数
- DD-12 范围约束：frontend agent 改 `../frontend/`，backend agent 改 `../backend/`
- DD-13 名实一致：函数名匹配实际行为
- DD-14 追踪链：commit 含 PLAN-NNN（当前 EPIC1-BMAD-DEV-ASSESS-2026-04-17）

---

## ⛔⛔⛔ Graphiti Runtime 体系契约（2026-05-26 ChatGPT 体系审查固化）

> **背景**: ChatGPT Deep Research 判定 BMAD 体系健康度 4.5/10，根因是 G-FAKE-001（名字像 Graphiti 身体是 Neo4j）+ G-PIPE-006（桥有了但没单一主干）历史重演风险。多 session 并行开发 Graphiti runtime（`epic-5a-graphiti-runtime/`）前，必须先锁以下契约。
>
> **开发流程定调（用户 2026-05-26 确认）**: 保留 BMAD spec 格式（frontmatter `story_id/status/depends_on/blocks` + AC + Tasks checkbox，多 session 接续靠它）+ R4 循环手写实施。**不走** `bmad-bmm-dev-story` skill 自动实施（Graphiti 精确 schema 手写更稳）。

### 3 个接口契约（违反 = 体系撕裂，code review 必拦）

| # | 契约 | 唯一 owner / 路径 | 禁止 |
|---|---|---|---|
| **C-1 写入契约** | 所有学习事件（callout/wikilink/calibration/error）必须通过 `5-ge-1` 的 `CanvasGraphEpisodeV1` 统一 episode schema 入图 | `backend/app/graphiti/canvas_episode.py`（Session B 定义，唯一 owner） | ❌ 各 story 自造发散 payload；❌ Session E 反向定义 schema（只能消费） |
| **C-2 读取契约** | 所有 Graphiti 关系读取统一过 `5-ge-5` 的 `GraphitiRelationService` facade | `backend/app/services/graphiti_relation_service.py` | ❌ LITE-4-3 / LITE-5-7 直调底层 `search_facts`；❌ 新 story 私接 Neo4j-backed learning memory search |
| **C-3 隔离契约** | `group_id` 业务层统一 `build_vault_group_id()`，Graphiti 边界统一 `sanitize_group_id_for_graphiti()` | `backend/app/core/subject_config.py` + `backend/app/graphiti/group_id_compat.py` | ❌ 任何 writer/reader 拿 `DEFAULT_GROUP_ID` 走生产路径（跨 vault 污染） |

### 6 条多 session 协同硬规则

1. **每个 Session 必须绑定 `spec_path` + `changed_files`** — 没有 spec_path 的工作项不能直接进 live 分支
2. **任何 supersede 必须同 commit 改旧 spec 状态** — 新 spec 合并时旧 spec 不允许继续挂 `ready-for-dev`
3. **产品读写路径不允许双主干** — 写统一走 episode runtime（C-1），读统一走 relation facade（C-2）
4. **所有 group_id 相关改动必须同时过 `subject_config.py` 与 `group_id_compat.py`**（C-3）
5. **`dry_run=True` 只允许出现在恢复/批量重建工具，不允许默默成为生产默认** — 当前 `relationship_sync_service` + `/relationships/vault` endpoint 的 `dry_run=True` 默认必须由 `5-ge-4` 显式翻转为 `False`
6. **Session D（`5-ge-5` facade）不是与 B/C 并行，而是"等待依赖完成后的快速收口 Session"** — 必等 B（schema）+ C（belief/flush contract）定版

### Sprint 2 v3 三波次（ChatGPT 校正，非纯 5 并行）

```
波一: Session A (UX/UAT) ‖ Session B (5-ge-1 schema) ‖ Session E (1.16/2.10 scaffold, 不锁 payload)
波二: Session C (5-ge-2/3/4) ‖ Session E (对齐 5-ge-1 后完成 payload) ‖ Session A (1.18/1.19 收尾)
波三: Session D (5-ge-5 facade) → Consumer LITE-4-3 (等 2.10+facade) → LITE-5-7 AC#1 patch only
```

硬依赖：**B↔E 协议依赖**（E 不能在 B 的 schema 定版前合并 payload）；**C↔D 服务依赖**（D 读的 facade 依赖 C 立 belief/flush contract）。

### live / archive 治理（2026-05-26）

- `_bmad-output/implementation-artifacts/archive/` — 17 个归档旧 spec（13 高确定 supersede/deprecated + 4 候选 infra/多模态）。**只读参考，不在 live 开发队列**
- `epic-5a-graphiti-runtime/` — Graphiti runtime 主干（5-ge-1~5），**不是旧 epic-5 的替代品，是其上游 runtime**（旧 5.1/5.2/5.3 BKT/FSRS 是下游消费方，Sprint 3+ 激活）
- ⚠️ **1-4-hotkey-binding-config 不归档**（ChatGPT 误判为 Excalidraw 遗留，实证是 hotkey 核心 onboarding）

---

## MCP 工具

- **Sequential Thinking**: 复杂推理必调
- **Context7**: 查库/框架/API 文档
- **Graphiti**: `search_memory_facts(group_id="canvas-dev")` 每轮
- **Codebase Memory**: 项目记忆查询

---

## 风格参考

- 后端 service: `../backend/app/services/rag_service.py`
- 后端 router: `../backend/app/api/v1/endpoints/canvas.py`
- Obsidian plugin: `../frontend/obsidian-plugin/src/main.ts`

---

## 启动 session 的命令

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output
claude --add-dir ../backend --add-dir ../frontend/obsidian-plugin --add-dir ../canvas-vault --add-dir ../archive/legacy-tauri-v0
```

---

## R4 ↔ BMAD 适配契约（2026-04-17 round-5 加入）

### 用户身份声明

**用户是非技术背景小白**，BMAD 复杂性必须**对用户透明**。BMAD 是 Claude Code 的内部工具链，不暴露给用户。

### R4 是核心，BMAD 是工具

| 维度 | R4 (核心) | BMAD (工具) | 冲突时 |
|---|---|---|---|
| 用户职责 | PRD 行为 + UX 期望 + 上手 UAT + 批注 | (用户不懂 BMAD 角色) | R4 胜 |
| Story spec 来源 | 用户行为期望 | bmad-bmm-create-story Skill 生成 | R4 + BMAD schema 兼容 |
| 技术决策 | Claude 自决 + 并行 explore + ChatGPT DR 兜底 | BMAD Architect 角色 | R4 胜（Architect 融入 explore） |
| Sprint 管理 | Claude autonomous edit sprint-status | BMAD SM 角色 | R4 胜（用户监督但不操作） |
| QA gate | 用户 hands-on UAT + 批注 | BMAD QA agent 测试矩阵 | R4 胜（边界用例 Claude 自检） |
| Story 创建顺序 | 可 batch（4 MVP 同时定义） | SM "N+1 only after N done" | 折衷: batch 定义但 dev 顺序执行 |

### BMAD 必须保留（避免工具链崩溃）

1. **Story spec YAML frontmatter** — story_id / epic_id / depends_on / blocks / trace 必填，否则 bmad-bmm-dev-story 解析崩溃
2. **Tasks 用 `- [ ]` checkbox** — 否则 dev-story 找不到任务列表
3. **Dev Agent Record / File List 段位** — dev-story 实施时填充
4. **sprint-status.yaml** — Claude edit 但 schema 严格遵守（status 枚举 backlog/ready-for-dev/in-progress/review/done）

### BMAD 简化（适配 R4）

1. **Architect 角色** → 融入 Claude 自决 + Explore agent deep explore
2. **SM 角色** → Claude autonomous (用户每周看 sprint-status 大概)
3. **PM/PO/QA 合并** → 用户一人（写 PRD + 验 UAT + 批注）
4. **Advanced elicitation** → R4 批注循环 (audit → response → annotation 多轮)
5. **Sequential story creation** → 允许 batch 定义 spec，但 dev-story 顺序执行（1.16 done 后 1.17）

### Claude Code 行动规则

实施 Story 时:
1. 先用 `bmad-bmm-dev-story` Skill 而非手写代码（保 BMAD 工具链）
2. 若 spec 缺 frontmatter/checkbox → **先 patch spec 再跑 Skill**
3. 跨 Story 架构选择 → **先看 architecture.md，无则自决并 update architecture.md**
4. dev 完成 → 更新 sprint-status `review` + **必 ship 小白验收单**（见下方 DoD）+ 通知用户 UAT
5. 用户 UAT 不通过 → 用 `bmad-bmm-correct-course` Skill 调整 + **更新已 ship 的验收单** v2/v3

### 用户视角（极简）

你只需 4 个动作:
1. 写产品行为期望（PRD/EPIC，plain English）
2. **在 Obsidian 打开 `_bmad-output/验收单/Story-{id}-*.md`**（Claude dev 完会自动 ship）
3. 在 Obsidian 跑 UAT 清单，满意就勾 ✅，不满意就用 `Cmd+Shift+A` 批注 `❌ 错误` 或 `❓ 提问`
4. 说一句 "dev story X.Y" 推进下一步，或 "Story X.Y 通过" mark done

**所有技术细节（YAML frontmatter / checkbox / BMAD Skill 调用 / sprint-status edit）由 Claude 处理，你不用关心。**

---

## ⛔⛔⛔ 双 Vault 架构（2026-04-19 round-7 固化）

> **用户 2026-04-19 明确**："开发相关的文档在 bmad output，然后测试相关的内容在 canvas vault"

| Vault | 存放 | 用户场景 |
|---|---|---|
| **`_bmad-output/`** | 开发文档：PRD / spec / review / 验收单 / 研究报告 / 模板 | 打开读文档、勾验收单 checkbox、在验收单批注 |
| **`canvas-vault/`** | 测试环境：插件 main.js / Claudian / Skills / 真实笔记 / hotkey 绑定 / 白板 / 实测 KG 数据 | 实际跑 UAT、Cmd+Shift+A 批注、Cmd+Shift+D 触发 AI 双链、日常学习使用 |

### 资产归属规则（违反 = 错配）

| 资产 | 正确位置 | 禁止位置 |
|---|---|---|
| Obsidian plugin `main.js`/`manifest.json` | `canvas-vault/.obsidian/plugins/<id>/` | ❌ _bmad-output/.obsidian/plugins/ |
| Claudian (Claude Code sidebar) | `canvas-vault/.obsidian/plugins/claudian/` | ❌ _bmad-output |
| Claudian Skills | `canvas-vault/.claude/skills/<name>/SKILL.md` | ❌ _bmad-output/.claude/skills/ |
| hotkeys.json（用户绑定） | `canvas-vault/.obsidian/hotkeys.json` | ❌ _bmad-output/.obsidian/ |
| community-plugins.json | `canvas-vault/.obsidian/community-plugins.json`（含真实 plugin 列表） | `_bmad-output/.obsidian/community-plugins.json` 保持 `[]` |
| Story spec / 验收单 / 模板 | `_bmad-output/...` | ❌ canvas-vault |
| frontend plugin 源码 | `frontend/obsidian-plugin/src/` (Git-tracked) | — |
| build 产物 main.js | `frontend/obsidian-plugin/main.js` (Git-ignored) + cp → canvas-vault | ❌ _bmad-output/.obsidian/plugins/ |

### Deploy 命令模板（未来所有 Story）

```bash
cd frontend/obsidian-plugin && npm run build
cp main.js ../../canvas-vault/.obsidian/plugins/canvas-learning-system/main.js
# (验收单单独 ship)
cp _bmad-output/templates/uat-sheet-template.md \
   _bmad-output/验收单/Story-{id}-{kebab-title}.md  # 然后填充
```

---

## ⛔⛔⛔ R4 × BMAD Definition of Done (DoD) — 2026-04-18 round-6 固化 + 2026-04-19 round-7 修正

> **用户刚需**：R4 工作流中的"ship demo + 用户 hands-on"环节之前靠 Claude 记性，现固化为 **dev-story 完成的三项必要条件**。任一缺失 = 未完成。

### dev-story 的三项完成条件（AND 关系）

| # | 条件 | 验收信号 |
|---|---|---|
| **DoD-1 技术层** | Git commit + tests 通过 + sprint-status `review` + **插件 deploy 到 `canvas-vault/.obsidian/plugins/`** | `git log` 最新 commit 含 Story ID + `npm test` green + `ls canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` |
| **DoD-2 spec 层** | Story spec 的 Dev Agent Record / File List / Change Log / Tasks 全打勾 | `_bmad-output/implementation-artifacts/epic-N/X-Y-*.md` 所有 `- [ ]` 变 `- [x]`，新增 Change Log 条目 |
| **DoD-3 R4 层** | **`_bmad-output/验收单/Story-{id}-{kebab-title}.md` 已 ship** | `ls _bmad-output/验收单/` 能看到新增文件，且结构符合 `_bmad-output/templates/uat-sheet-template.md` |

### DoD-3 验收单强制结构（7 段 + 第 4 段双段铁律 — 2026-05-08 v3.0 升级）

> **升级背景**：从 `feature-deeptutor-canvas-mvp` worktree 5-agent UAT methodology deep explore 收敛产物（Moments of Truth + JTBD + Nielsen + 5-Second Test）+ 现有 Story 验收单审计（Story 10.1=68% / 10.2=50% / 10.3=45% / 10.4=0% 违规率）。固化 D3-A~D3-E 5 铁律。

每份 `_bmad-output/验收单/Story-*.md` **必须包含**以下结构：

```
1. 🎯 一句话目标（非技术，你能看懂）
2. 📖 你的视角（Behavior，作为...我想...以便...）
3. 🖥️ 交互流程（用户屏幕变化，禁后端架构流）
4-A. 🤖 Claude 已代验（技术 assert 全归这段：API status / docker / JSON / schema / pytest / cost）
4-B. 👤 你来验（产品体验，禁出现技术词，句型"我做 X → 我看到 Y → 我感觉 Z"）
5. 🚦 验收结果（通过/不通过的下一步指引）
6. 📝 批注区（[!question]+ 空 callout 供你写，+ 历史 [!error]+ 追溯）
7. 🔗 技术 spec 引用（Story spec 路径 / 源代码 / 测试 / commit — 给 Claude 读的）
```

### DoD-3 双段铁律 D3-A ~ D3-E（违反 = 验收单作废重写）

| # | 规则 | 违反信号（grep 可检测） |
|---|---|---|
| **D3-A** | 段 4-B "👤 你来验"中 **0 出现** 以下技术词：`curl` / `docker` / `:端口号`（如 `:8001`）/ `HTTP` / `JSON` / `.env` / `endpoint` / `pytest` / `schema` / `容器` / `daemon` / `requestUrl` / `vault.create()` / `obsidiantools` 等（项目相关禁词配 `.claude/hooks/uat-forbidden-words.json`） | grep 命中 = ❌ |
| **D3-B** | 段 4-B 每条 checkbox 必须能被"60 岁不会编程的人在 Obsidian / 浏览器一次照做" — 工具白名单：Obsidian 主界面 / 浏览器主窗口 / macOS Finder（仅 vault 内） | 含"终端"/"命令行"/"`cd `"/"`mkdir`"/"`git`"/"DevTools" = ❌ |
| **D3-C** | 段 4-A 必须 Claude 自己跑完贴 ✅ + 证据，不能让用户跑 | 段内出现"请你跑" / "你执行" / "你打开终端" = ❌ |
| **D3-D** | 段 3 "🖥️ 交互流程"画的是用户屏幕变化，不是后端架构 | 出现 `→ backend` / `→ endpoint` / `→ 容器` / `daemon` = ❌ |
| **D3-E** | 段 4-B 每条 checkbox 用"我做 X → 我看到 Y → 我感觉 Z"句型 + felt-sense（每 3 条至少 1 处） | 全文 0 felt-sense（流畅/困惑/信任/期待）= ❌ |

### DoD-3 方法论分层（不同 Phase 用不同重点）

- **Phase A（产品骨架）**：5-Second Test + Moments of Truth (Carlzon 1987) — 测"你愿不愿意明天再打开它"
- **Phase B（功能可用）**：JTBD (Ulwick) + Nielsen Heuristic-Lite — 测"你能否完成想做的 job"
- **Day 7+（产品成熟）**：NPS + Sean Ellis 40% PMF test — 测"明天消失你会非常失望吗"

### Hook 自动化保护

`/.claude/hooks/uat-double-section-guard.js` PostToolUse 自动检测段 4-B 禁词 + felt-sense。fail-open 容错（hook 错误不阻断 Claude）。

### 模板位置

`_bmad-output/templates/uat-sheet-template.md` — Claude 每次 dev-story 完成后 **复制此模板**填充，ship 到 `_bmad-output/验收单/`。

### correct-course 触发的验收单行为

当 `bmad-bmm-correct-course` 调整 Story 后：
- **不新建**新验收单，**覆盖**原 `_bmad-output/验收单/Story-{id}-*.md`
- 在批注区"已知的已批注问题（历史追溯）"小节加 `[!error]+ v{N} → v{N+1} 修复` callout 记录变更
- 在"v{N} → v{N+1} 你将看到的变化"表格里列出 diff

### R4 6 环节 × DoD 对应关系

| R4 环节 | DoD 强制 | 备注 |
|---|---|---|
| 1. 用户写 PRD/EPIC | — | `planning-artifacts/prd.md` 用户 own |
| 2. Claude 自决技术 | — | Explore agent + Context7 + Graphiti 自动 |
| 3. Deep Research 兜底 | — | `[DECISION-TECH]` + Stop hook 守护 |
| **4. ship hands-on demo** | **DoD-3** | 验收单位置固定 + 结构固定 |
| **5. 用户 UAT + 批注** | **DoD-3 批注区** | 用户用 Cmd+Shift+A 批注到验收单自身 |
| **6. 技术层 trace 诊断** | **DoD-2 Dev Agent Record** | Story spec `## Pitfalls + 诊断矩阵` 段对应 |
| **7. correct-course 闭环** | **DoD-3 覆盖更新** | 验收单 v2/v3 + Change Log 记录 |

### Claude Code 自检清单（dev-story 结束时必跑 — 2026-05-08 v3.0 升级版）

```
DoD-1 ☐ git log 最新 commit 含 "Story: X.Y" 或 "PLAN-NNN"
DoD-1 ☐ tests 命令跑完 0 fail
DoD-1 ☐ sprint-status.yaml 里对应 key 是 "review"
DoD-1 ☐ canvas-vault/.obsidian/plugins/<id>/main.js 已更新（不是 _bmad-output）

DoD-2 ☐ Story spec 的 Dev Tasks 全部 [x]
DoD-2 ☐ Dev Agent Record / File List / Change Log 已填
DoD-2 ☐ AC 列表每条对应实现有 trace

DoD-3 ☐ _bmad-output/验收单/Story-{id}-*.md 存在
DoD-3 ☐ 含 7 段（含 4-A + 4-B 双段拆分）
DoD-3 ☐ 段 4-B 跑禁词 grep（curl|docker|HTTP|JSON|端口|.env|endpoint|pytest|容器|daemon|git|DevTools|requestUrl|vault.create|obsidiantools）= 0 命中 [D3-A]
DoD-3 ☐ 段 4-B 每 checkbox 通过"60 岁照做 Obsidian/浏览器"测试 [D3-B]
DoD-3 ☐ 段 4-A 全部 ✅ 已带证据（Claude 自跑，非"请你跑"） [D3-C]
DoD-3 ☐ 段 3 交互流程画用户屏幕变化，不是后端架构 [D3-D]
DoD-3 ☐ 段 4-B 用"我做 X → 我看到 Y → 我感觉 Z"句型 + felt-sense ≥ 1 处 [D3-E]
DoD-3 ☐ 5 题自检全过（见 templates/uat-sheet-template.md 末尾注释）
DoD-3 ☐ 通知用户验收单文件位置 + 提醒"全在 Obsidian/浏览器里完成，3-5 分钟"

3 × ☐ 全部 ✓ → 才能告诉用户 "Story X.Y ready for review"
任一 ✗ → HALT，补齐后才算完成
```
