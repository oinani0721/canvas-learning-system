# EPIC 1 审计回应文档（Round 1）

> **回应对象**: [[epic-1-audit-2026-04-17]]（2026-04-17 审计文档 + 你的 9 条批注）
> **Round 2**: [[epic-1-audit-response-round-2-2026-04-17]]（回应本文档 N1-N6 新批注）
> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **Date**: 2026-04-17
> **本次决策锚点**:
> - Q1 归档策略 = 当前仓库即新项目，Tauri v0 移 `archive/legacy-tauri-v0/`
> - Q2 Story 1.14 归属 = EPIC 1 末尾新增（已 deep explore 历史文档）
> - Q3 Graphiti LLM = 双 Provider（Graphiti 保 Gemini，其余切 Claude）
>
> **使用方式**: 每个 Sec 末尾有新的 `[!question]+` 占位符。和 audit 文档的旧批注区分开：
> - Audit 文档的旧批注 = 本次已回答（见本文各 Sec）
> - 本文档的新批注 = 下次 session 循环

---

## Sec 1: 偏差纠正回答（回应 audit 批注 #偏差纠正）

### 你的原批注
> "严肃强调以上那些都是参考文件，而不是我们实际开发的文件，请你进行 deep explore 告诉我你打算怎么归档"

### 我的理解

Audit 文档 9 项纠正里列的"真相源"（[[prd]]、[[epics]]、[[architecture]]、[[recovered/prd-tauri-original-2ae5897]] 等）确实是**参考文件** — 它们是设计规范、历史演进记录、决策锚点，**不是被开发/修改的代码产物**。

Deep explore 完整发现（5 个并行 agent 产出）：**Tauri v0 代码实际存在于仓库中**，不是归档状态 — 这推翻了 audit 文档"没有 Tauri / 没有 Sidecar"的误导说法。

| 项目 | 状态 | 证据 |
|---|---|---|
| `frontend/src/App.tsx` | ✅ 真实存在 (44 KB) | 2026-04-07 最后修改 |
| `frontend/src-tauri/` | ✅ 真实存在 | Cargo.toml + main.rs |
| `frontend/sidecar/sidecar.js` | ✅ 真实存在 | 仍 import `@anthropic-ai/claude-agent-sdk` |
| `frontend/obsidian-plugin/` | ✅ 真实存在（已部署到 vault） | main.ts + main.js |

### 归档方案（你在 Q1 选了此方案）

**分层归档结构**（全部在当前仓库内，不开新仓库）：

```
canvas-learning-system/                    ← 当前仓库 = 新项目
├── _bmad-output/                          ← 规划/设计真相源（⭐ 第 1 优先）
│   ├── planning-artifacts/                  BMAD 真相源 Layer 1-4 (prd/epics/arch/ux)
│   ├── implementation-artifacts/            Story spec（ready-for-dev + done）
│   ├── review/                              审计 + UAT 指南 + 本 response
│   └── research/                            13 轮 QA 决策追溯
├── backend/                               ← 真实开发代码
├── frontend/obsidian-plugin/              ← 真实开发代码（Obsidian 插件）
├── canvas-vault/                          ← 验收 vault（小白测试用）
├── archive/                               ← 新建归档目录
│   └── legacy-tauri-v0/                    （待执行）Tauri v0 归档目标
│       ├── App.tsx + src/
│       ├── src-tauri/
│       └── sidecar/
└── docs/                                  ← 历史开发笔记（已作废，仅供追溯）
```

**归档待执行动作清单**（本 response 不执行，等你单独批准）:
1. 创建 `archive/legacy-tauri-v0/` 目录
2. `git mv frontend/src/ archive/legacy-tauri-v0/` (44 KB + components/)
3. `git mv frontend/src-tauri/ archive/legacy-tauri-v0/`
4. `git mv frontend/sidecar/ archive/legacy-tauri-v0/`
5. 新建 `archive/legacy-tauri-v0/README.md`（说明为什么归档 + v1 对应哪些 commit）
6. 更新 `.gitignore`（若有 Tauri build 产物）
7. 更新 `CLAUDE.md` 第 100-117 行"风格参考文件"区 — 见 Sec 9

**为什么不在本 response 执行**: 归档是 git mv 多个目录的破坏性操作，按 `/Users/Heishing/Desktop/canvas/CLAUDE.md` 权限原则需单独确认。
	**User：请你启动并行 agent deep explore 找到社区成熟的解决方案，因为我们现在 Canvas learning systeam 是将降级部署到我们使用 obsidian 加 claudian 的方案，所以我觉得需要重新在一个新的文件夹写 claude.md 来强调，然后我们的整个新的 claude code 的开发仓库聚焦于/Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output  ；我们进入这一个文件夹来 claude code 开发**

> [!question]+ 用户批注 - Sec 1
> 归档方案是否完整？是否有 Tauri v0 相关文件我遗漏了？授权执行请写 "yes, archive"。
> （批注区）

---

## Sec 2: Layer 2 架构修正 — Hotkey + Callout 双入口（回应 audit #真实架构）

### 你的原批注
> "请你查看一下 Story 的 hotkey 的使用，我之前有批注过我们是用 hotkey 来进行快捷操作的"

### 调研结果

Agent 1 读取 [[1-4-hotkey-binding-config]] + [[1-5-hotkey-conflict-detection]] + `frontend/obsidian-plugin/src/main.ts:24-67` 后确认：

Audit 原说"用户在 Obsidian Markdown 里写 callout 触发 Claude Code Skill" **不完整** — Layer 2 实际有**两个互不重叠的入口**：

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Skill Trigger = 双入口                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 入口 A: HOTKEY（全局，键盘优先）                            │
│ ──────────────────────────────────────────────────────────  │
│ 键盘快捷键 (Obsidian Settings > Hotkeys 用户配置)          │
│    ↓                                                         │
│ 6 个 canvas:* 命令 (addCommand 注册)                       │
│    ↓ callback 执行                                          │
│ POST /api/v1/{endpoint}                                     │
│    ↓                                                         │
│ 后端 Skill Handler                                         │
│                                                              │
│ 注册点: frontend/obsidian-plugin/src/main.ts:24-67         │
│ 冲突检测: main.ts:72-105 (Story 1.5)                       │
│ 作用域: 全局（任何 Obsidian view）                         │
│ 主要用于: 快速操作（启动考察/打开仪表盘/提取概念）          │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 入口 B: CALLOUT（笔记内，上下文相关）                       │
│ ──────────────────────────────────────────────────────────  │
│ Markdown callout ([!question]+ / [!tip]+ / [!error]+)      │
│    ↓                                                         │
│ Claudian 侧栏                                               │
│    ↓                                                         │
│ 用户输入 /command (如 /chat_with_context)                  │
│    ↓                                                         │
│ Claudian 解析 callout + 笔记 context                       │
│    ↓                                                         │
│ Skill Handler (Claude Code via Claudian spawn)             │
│                                                              │
│ 作用域: 笔记级（读取当前笔记的 callouts）                   │
│ 主要用于: 上下文学习（针对批注精确对话）                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6 Hotkey 命令清单（Story 1.4 实现）

**User：请你先实现来两个核心 hotkey和两个核心 skill。1，批注 hotkey，我可以在 md 文档上的任意内容进行批注，批注的类型请你参考我的 prd ，这个 hotkey 我觉得不需要用到 ai。2，对于我选中的文本，通过 ai 来创建出新的双向链接文档来进行分析,然后我可以在新的文档上开新的 tab 进行分析，并且更新我的当前原白板的 index.md ；3， 一个是原白板配置 skill，我让 claudian 对于我当前的 md 文档进行创建原白板的配置也就是要配置相关的 index.md 配置，需要询问我这是什么原白板，对应什么学科类型，然后把 index.md 以及我的md 文件创建到相关的文件夹归类，并且配置好原白板的相关配置；4，在我们创建的 dashboard.md 的界面，我可以点击检索出相关的原白板然后直接开始启动检验白板检验。而且我这里多一个建议关于 dashboard 设计，是否换成 webUI 更好一点，通过 WebUI 更能清楚我当前的原白板和检验白板的学习情况，然后是否可以在 webui 的交互 来直接让到 claudian 创建相关原白板的检验白板，或者我还是用 skill 加原白板名字来创建检验白板，**

| Command ID | 中文名 | Backend Endpoint |
|---|---|---|
| `canvas:start-dialog` | 启动学习对话 | `POST /api/v1/agents/dialog` |
| `canvas:start-examination` | 启动考察 | `POST /api/v1/exam/start` |
| `canvas:extract-concept` | 提取概念 | `POST /api/v1/wikilink/build` |
| `canvas:quiz-from-callout` | 批注考察 | `POST /api/v1/exam/start` |
| `canvas:open-dashboard` | 打开仪表盘 | `POST /api/v1/system/health` |
| `canvas:open-review-queue` | 打开复习队列 | `POST /api/v1/review/queue` |

默认 `hotkeys: []`（符合 Obsidian 社区最佳实践）— 用户在 Settings > Hotkeys 自行绑定。Story 1.5 冲突检测用 8 秒 Notice 提示。

### 6 Claudian `/command` Skill 清单（EPIC 2/3/4 范围）

| `/command`           | 触发方式             | 所在 EPIC |
| -------------------- | ---------------- | ------- |
| `/chat_with_context` | 输入 `/` + 自动补全    | EPIC 2  |
| `/start_exam_board`  | 输入 `/`           | EPIC 4  |
| `/extract_node`      | 选中文本后输入 `/`      | EPIC 3  |
| `/edge_discuss`      | 在 edge 上输入 `/`   | EPIC 3  |
| `/quiz_from_callout` | 选中 callout 后 `/` | EPIC 4  |
| `/review_profile`    | 输入 `/`           | EPIC 5  |
		**User：1，我们强调过`/extract_node` 就是会让我说明，前后文档之间的联系,2，`/chat_with_context` 是用来告诉 claudian，我们当前使用的是原白板吗？这里我觉得让 claudian 意识到的事情只要是，知道我们当前的 md 文件归属于哪一个原白板，并且能找 index. md 阅读理解各个文档之间的关系；`/extract_node` 则是提取创建新的节点后，能关系原白板的 index.md**
### 为什么两组 6 命令分开？

- **Hotkey 的 6 个命令**（Obsidian plugin）= 全局快捷操作，不需要读笔记内容
- **Claudian 的 6 个 /command**（Claudian 插件）= 需要读当前笔记 + callout 上下文

功能上部分重叠（都有"启动考察"和"提取概念"），但触发模式不同。

> [!question]+ 用户批注 - Sec 2
> 两组命令是否应该命名合并（例如 Obsidian hotkey 也叫 `/start_exam_board` 不叫"启动考察"）？还是保留中文显示名 + `/command` 英文 ID 分离？影响 Story 1.4 AC 文案。
> （批注区）

---

## Sec 3: 归档 + 三文档分层方案（回应 audit #真实进度 + #元根因）

### 你的原批注（两处合并回答）
> "我们的代码和文档之间是有实现互相追踪的...我们需要一个新的文件夹来进行开发我们的降级版本的 Canvas learning system... 开发文档都在 bmad-output 这里；测试 vault 是 canvas-vault；开发流程用 BMAD... 每个 story 最小验收单位为基准..."
>
> "我们直接把当前的仓库作为新的项目文档，然后 claude code 进入这个文档进行开发，然后 canvas-vault 是我们实际检验我们开发效果的仓库"

### 三类文档正式定义

Q1 已答：当前仓库 = 新项目。所以分层是：

#### Type A: 开发文档（Claude Code 实际改动的文件）
- `_bmad-output/implementation-artifacts/` — Story spec + sprint-status
- `backend/` — 后端代码
- `frontend/obsidian-plugin/` — Obsidian 插件代码
- `canvas-vault/` — 验收用 vault（真实测试数据进来）

#### Type B: 参考文档（Claude Code 只读，不改）
- `_bmad-output/planning-artifacts/prd.md` — 项目内部 PRD（⭐ 最高优先）
- `_bmad-output/planning-artifacts/epics.md` — EPIC + Story BDD AC
- `_bmad-output/planning-artifacts/architecture.md` — 架构约束
- `_bmad-output/planning-artifacts/ux-design-specification.md` — UX 规范
- `_bmad-output/planning-artifacts/recovered/` — Tauri v0 设计历史
- `_bmad-output/research/` — 13 轮 QA 追溯
- `archive/legacy-tauri-v0/` — Tauri v0 归档代码（待归档后）
- 外部锚定 PRD `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` — 只读（pretool-guard 阻断修改）

#### Type C: 验收 vault
- `canvas-vault/` — 小白测试用，和 canvas-vault 里部署的 Obsidian plugin + Claudian 形成完整验收环境

#### Type D: 历史开发笔记（已作废，仅供追溯）
- `docs/` — 旧 architecture / gap-analysis / annotation-tracker
- `_decisions/mvp-plan.md` + `_decisions/CURRENT_TASK.md` — 旧 MVP 计划

### CLAUDE.md 修改建议（本 response 不执行）
U**ser：给项目开启一个新的 claude.md 就是为了不让 claude code 被之前 claude.md 中的过时内容所误导**
	

当前 `/Users/Heishing/Desktop/canvas/canvas-learning-system/CLAUDE.md` 第 100-117 行"风格参考文件"区：
- ❌ 列了 `docs/known-gotchas.md`、`docs/architecture.md` 作开发参考
- ❌ 未列 `_bmad-output/planning-artifacts/` 作真相源
- ❌ 把外部 PRD 和 implementation-artifacts 直连，跳过 planning-artifacts 中间层

建议重写为：
```markdown
## 开发文档（Claude Code 改动的文件）
- 后端: backend/
- Obsidian 插件: frontend/obsidian-plugin/
- Story spec: _bmad-output/implementation-artifacts/
- 验收 vault: canvas-vault/

## 参考文档（Claude Code 只读）
### BMAD 真相源（优先级递减）
1. `_bmad-output/planning-artifacts/epics.md` ⭐⭐⭐⭐⭐ (BDD + AC)
2. `_bmad-output/planning-artifacts/prd.md` ⭐⭐⭐⭐ (需求)
3. `_bmad-output/planning-artifacts/architecture.md` ⭐⭐⭐ (约束)
4. `_bmad-output/planning-artifacts/ux-design-specification.md` ⭐⭐⭐ (UX)
### 历史演进
5. `_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md` (Tauri v0)
6. `archive/legacy-tauri-v0/` (归档代码)
### 外部锚定 PRD
- `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (只读)

## 已作废（仅追溯）
- docs/* (Tauri 时期笔记)
- _decisions/mvp-plan.md (旧 MVP 计划)
```

### BMAD 开发流程（你的原批注明示）

1. 用 `bmad-bmm-create-story` Skill 创建 Story（每个 Story = 最小验收单位）
2. 人工批注审核（你在 Obsidian 里给 Story spec 加 callout）
3. 用 `bmad-bmm-dev-story` Skill 开发（实施 AC）
4. 小白用 UAT 指南验收（见 Sec 4 UAT 对齐矩阵）
5. 如果小白发现实现偏离 Story，Claude Code 用技术层诊断找根因（见 Sec 4）

> [!question]+ 用户批注 - Sec 3
> CLAUDE.md 修改建议方向对吗？Type D "历史开发笔记"是否彻底作废（`docs/` 全移到 `archive/legacy-docs/`）还是保留作追溯？
> （批注区）有我的批注的保留，其余的迁移

---

## Sec 4: UAT 小白 ↔ Story 对齐机制（回应 audit #UAT 指南）

### 你的原批注
> "我是要一个完全不懂代码的小白来进行测试，它的聚焦点在于，claude code 实现的功能是否符合它的规范... 而 claude code 要有能力找出当小白说实现功能和 story 上实现的功能不一致或者偏离，而 claude code 要找出来抽象之下的技术层面到底哪里出了问题。"

### 设计：UAT 对齐矩阵

**核心思想**: 每个 Story AC 旁配一列"小白验证语句"（小白视角的观察），再配一列"技术层诊断线索"（Claude Code 定位偏离的根因）。

#### 矩阵模板

| Story AC | 小白验证语句（行为-观察） | 期望结果 | 技术层诊断线索 |
|---|---|---|---|
| Story 1.4 AC #1 | "我在 Settings > Hotkeys 搜 'Canvas'" | 看到 6 行 `canvas:*` 命令 | 若 < 6 行 → 检查 `main.ts:addCommand` 注册数 |
| Story 1.4 AC #2 | "我给 canvas:start-examination 绑 Cmd+E" | 绑定保存后，按 Cmd+E 触发考察 | 若无反应 → 检查 plugin 是否 loaded + backend `/api/v1/exam/start` 是否返回 200 |
| Story 1.5 AC #1 | "我故意绑 Cmd+E 给两个命令，重启 Obsidian" | 屏幕出现 8 秒黄色 Notice 警告 | 若无 Notice → 检查 `main.ts:72-105` 的 `checkHotkeyConflicts` + `onLayoutReady` hook |

#### 偏离预警列

每个 Story 的 UAT 指南加"偏离预警"列，描述 3 种可能的偏离场景 + 诊断顺序：

**场景 1**: 小白说"我按了 Cmd+E 没反应"
- Claude Code 诊断顺序：
  1. 是否真绑定了快捷键？→ 读 `canvas-vault/.obsidian/hotkeys.json`
  2. Plugin 是否加载？→ 看 Obsidian console 有无 `Canvas Learning System: Loading`
  3. Backend 是否响应？→ `curl http://localhost:8001/api/v1/system/health`
  4. 若 backend 500 → 看 backend log 找异常栈
  5. 若 backend 200 但 plugin 无日志 → `main.ts` callback 里加 `console.log("[canvas:start-exam] triggered")` 再试

**场景 2**: 小白说"我做的和 Story 描述的不一样"
- Claude Code 行动：
  1. 读 [[1-4-hotkey-binding-config]] 的 AC 原文
  2. 对比小白描述的行为
  3. 如果 AC 模糊 → 标记"AC 待 clarify"
  4. 如果 AC 清晰但实现偏离 → 定位代码 commit 找什么时候改了

**场景 3**: 小白说"我看不懂"
- Claude Code 行动：
  1. 检查 UAT 指南是否用了技术术语（grep "component" "endpoint" "state"）
  2. 如果是 → 改写为"画面 / 动作 / 结果" 三段式
  3. 如果 UAT 本身没问题 → 小白可能缺少前置步骤（Docker 启动 / Claudian 未装）

### 对现有 [[epic-1-uat-guide-2026-04-17]] 的改造

现 UAT 指南是"Story → 验收方法 → 验收手段"3 列表。建议改造为 6 列：
- Story / AC
- 小白行为（"你做什么"）
- 小白观察（"你应该看到什么"）
- 通过/失败判据
- 偏离预警（3 场景速查）
- 技术层 trace（Claude Code 诊断起点）

**Open Q 给你**: 是否让我下次 session 改造 `epic-1-uat-guide-2026-04-17.md` 为这个矩阵形式？

> [!question]+ 用户批注 - Sec 4
> 对齐矩阵机制是否符合你的"小白 vs Story 对比 + Claude Code 技术层诊断"的诉求？是否授权下次 session 改造 UAT 指南？
> User：还要有小白觉得不满意的地方需要改进的点进行批注
> （批注区）

---

## Sec 5: 4 决策重解读确认（回应 audit #4 决策）

### 你的原批注
> "这是正确的"

### 回执

✓ 确认收到。4 条决策重解读已锁定：

| Q | 决策 | 下一步 trace |
|---|---|---|
| 粘贴语义 | callout 批注 + Claudian 触发（fallback 粘贴见 Story 1.14） | Story 1.14 Draft 在 Sec 6 |
| LLM 选型 | Claudian 是 UI 容器，后端 Claude API（Graphiti 例外） | 详见 Sec 7 dual-provider |
| EPIC 1 终点 | 按 [[epic-1-uat-guide-2026-04-17]] 执行 UAT | UAT 改造见 Sec 4 |
| 优先级 | 按 sprint-status.yaml + BMAD 方法 | 下 session 启动 1.2 + 1.8 |

> [!question]+ 用户批注 - Sec 5
> （无需批注除非有变更）
> （批注区）

---

## Sec 6: Story 1.14 Draft — 导入 md → 原白板分析（回应 audit #工作流 + #BMAD 下一步）

### 你的原批注
> "导入任意文本作为 md 文档，例如我导入题目，然后就开始启动原白板的分析，请你参考原 Canvas learning system 的 prd-tauri-original-2ae5897.md 设计，所以我们要把原白板的节点的启动和归类你要定义清楚"
>
> "写在 EPIC 1"

### 调研发现

Q2 已答 = EPIC 1 末尾新增 + "deep explore 历史文档"。经 2 个 Explore agent 搜 `_bmad-output/` 全域 + `docs/` + 外部 PRD + `_decisions/` 后确认：

#### 关键发现 F3 + F5 + F6

1. **Karpathy 三层架构已在外部 PRD L3287-3310 定义**:
   - `raw/` = 粘贴原始材料（**新文件夹** — 这就是你"新文件夹"诉求的落点）
   - `wiki/` = 加工后知识（现有 `wiki/concepts/`）
   - `exam_boards/` = 检验白板

2. **`created_from: import` 已在外部 PRD L3362 作为 frontmatter 合法枚举值**:
   ```yaml
   created_from: manual | extract_node | import | graphify
   ```
   不需要发明新架构，只需连起来。

3. **现有"提取"Story 不覆盖"导入"**:
   - [[3-1-concept-extraction-wikilink]] = 从对话/考察/edge 提取
   - [[2-7-concept-extraction-edge-inject]] = 概念 + edge 注入
   - Story 4.8 = 书签式考中提取
   - **这些都是"从已有内容提取"，非"从外部导入"** — Story 1.14 填补空白。

4. **你的历史批注** (`_decisions/mvp-plan.md:206`):
   > "这里新的疑问节点创建，我记得我们在 Graphiti 决策过不是你自动创建的，而是我来手动决定"

   ⇒ Story 1.14 必须"LLM 建议 + 用户确认"，不做 full-auto。

### 原白板节点体系映射（参考 [[recovered/prd-tauri-original-2ae5897]]）

| Tauri 节点 | Obsidian 映射 | frontmatter `type:` |
|---|---|---|
| 题目 | `wiki/<...>/question.md` 或 callout `[!question]+` | `question` |
| 概念 | `wiki/concepts/<slug>.md` | `concept` |
| 笔记 | `wiki/notes/*.md` 或 callout `[!note]+` | `note` |
| 答题板 | `exam_boards/<slug>-<ts>.md` | `exam_board` |
| 关系边 | concept.md 的 frontmatter `relationships[]` | (已废弃独立文件) |

### Story 1.14 AC Draft (8 条)

**Story 1.14: 外部 md 导入 → 自动归类 → 落入 raw/ 或 wiki/**

```
As a 学习者,
I want to paste/drop external markdown content into canvas-vault,
So that new knowledge can rapidly enter the system without manual file creation.

#### AC #1: 粘贴 md → raw/ 落盘
Given: 用户在 Claudian 粘贴 md 文本（或拖拽 .md 文件）
When: 检测到多行（>100 字符）或 .md 文件
Then: 创建 canvas-vault/raw/<timestamp>-<sanitized-title>.md
And: 写入 frontmatter:
  - created_from: import
  - imported_at: <ISO8601>
  - imported_from: (pasted | <file_path>)
  - needs_review: true

#### AC #2: LLM 建议 type（用户确认制）
Given: raw/ 落盘后
When: 触发 /extract_node 或手动打开 raw 文件
Then: LLM 分析内容，建议 type（concept / question / note）
And: 呈现给用户确认（不自动改 frontmatter）
And: 用户批准后，文件移到 wiki/concepts|notes/ 对应子目录 + type: 写入

**关键**: 默认不自动归类（用户历史批注明示反对 full-auto）

#### AC #3: 重名 slug 合并对话
Given: 导入内容的 title 和现有 wiki/concepts/<slug>.md 重名
When: slug 冲突检测
Then: 呈现 3 选项:
  - A: 合并（append 到现有 body + 更新 last_imported 字段）
  - B: 版本后缀（<slug>_v2, <slug>_v3 ...）
  - C: 取消导入

#### AC #4: 批量导入（--- 分隔）
Given: 粘贴的 md 包含多段 --- 分隔块
When: 解析识别分隔
Then: 每段创建独立 raw/ 文件
And: 自动建立 wikilink（如果段内容有引用）

#### AC #5: Wikilink 解析
Given: 导入内容含 [[concept-name]] 或 [link](anchor)
When: 解析 wikilink
Then: 尝试匹配 wiki/concepts/
And: 匹配失败的 → frontmatter unresolved_refs: ["concept-name"]

#### AC #6: Callout 作为导入触发（fallback）
Given: 用户在笔记里写 [!import]+ <粘贴的外部 md>
When: Claudian 解析到 [!import]+ callout
Then: 等价于 AC #1 的粘贴流程（fallback 入口）

#### AC #7: 解析失败降级
Given: 粘贴内容非 md（如二进制 / 乱码 / 超长）
When: 解析失败
Then: 降级为 raw note（保存原始文本 + WARNING）
And: frontmatter 加 parse_error: true
And: 通知用户："无法自动解析，已保存为 raw note，请手动清理"

#### AC #8: 追溯信息
Given: 任一 import 产出的文件
When: 用户通过 Dataview 查询 created_from: import
Then: 看到所有导入文件列表（imported_at, imported_from, type 建议, 是否已确认）
```

### 工作量 + 依赖

- 工作量: ~8h（MEDIUM effort — Agent B 评估）
- 依赖:
  - Story 1.1 vault init (✅ done) — `raw/` 目录需在 vault 结构里
  - Story 1.3 MCP 工具（ready-for-dev）— 用 `write_note` 写 raw/
  - `/extract_node` Skill（EPIC 3，未来）— 用于 AC #2 LLM 建议
- 不依赖: Story 1.14 可以在 EPIC 3 之前做（AC #2 的 LLM 建议可暂占位等 EPIC 3 接上）

### 正式 Story spec 创建时机

本 response 只是 **Draft**。正式 Story spec 需下 session 用 `bmad-bmm-create-story` Skill 生成，产出 `_bmad-output/implementation-artifacts/epic-1/1-14-md-import-auto-categorize.md`。

> [!question]+ 用户批注 - Sec 6
> 8 AC 是否符合你的"导入题目 → 原白板分析 + 节点启动和归类"预期？是否要增删？AC #2 的"用户确认制"是否你要的（反 auto-categorize）？
> （批注区）

---

## Sec 7: Graphiti dual-provider 方案（回应 audit #执行计划 内嵌批注）

### 你的原批注
> "你这里的后端所要求的大模型是因为 Graphiti 吗？"

### 调研真相（F2）

**答：部分是**。Agent 2 枚举 backend 7 个 LLM 使用点：

| 组件 | LLM 用途 | Provider 依赖 | 证据 |
|---|---|---|---|
| **Graphiti** | 实体抽取 + 图构建 | 🔴 **硬锁 Gemini** | `backend/app/services/episode_worker.py:287-394` 用 `graphiti_core.llm_client.gemini_client.GeminiClient` |
| Graphiti Embedder | 向量嵌入 | 🔴 硬锁 Gemini | `GeminiEmbedder` 1024d dense |
| autoscore | 评分 | 🟢 Soft (LiteLLM) | 可切 Claude |
| conversation_distiller | 对话蒸馏 | 🟢 Soft | 可切 |
| difficulty_matcher | 难度分类 | 🟢 Soft | 可切 |
| verification | AI 题生成 | 🟢 Soft | 可切 |
| agent_service | Agent workflow | 🟢 Soft | 可切 |
| rag_service | Agentic RAG | 🟢 Soft | 可切 |
| review_service | 验证 | 🟢 Soft | 可切 |

**结论**: Gemini 硬依赖**仅来自 Graphiti 一处** — graphiti-core 的 LLMConfig 不支持换 provider。其他 7 个组件都可切 Claude。

### Q3 选定方案: dual-provider

```
┌───────────────────────┐     ┌───────────────────────┐
│ Graphiti Pipeline     │────▶│  Gemini API          │
│ (episode_worker.py)   │     │  (GOOGLE_API_KEY)    │
└───────────────────────┘     └───────────────────────┘

┌───────────────────────┐     ┌───────────────────────┐
│ 其余 7 个组件          │────▶│  Claude API          │
│ (autoscore/rag/等)    │     │  (ANTHROPIC_API_KEY) │
└───────────────────────┘     └───────────────────────┘
```

### 改动清单

**文件清单**（本 response 不执行，只做设计）:

1. `backend/.env.example`:
   - 保留 `GOOGLE_API_KEY=xxx`（给 Graphiti）
   - 新增 `ANTHROPIC_API_KEY=xxx`（给其他）
   - 新增 `AI_PROVIDER=anthropic`（默认 switch）

2. `backend/app/clients/` 新增:
   - `anthropic_client.py`（仿 `gemini_client.py` 接口）
   - 支持 prompt caching（Claude 特性）

3. `backend/app/dependencies.py:64` 修改:
   - 按 `AI_PROVIDER` env 决定注入 `AnthropicClient` 或 `GeminiClient`
   - Graphiti 相关的 dependency 硬编码 `GeminiClient`（不走 env 切换）

4. 不改 `episode_worker.py:287-394`（保 Gemini）

### 新 Story 定位

这是 **Story 1.15** 候选（EPIC 1 末尾另一条）或 **Story 3.0**（EPIC 3 开头）。

- **1.15 优势**: 和 EPIC 1 的基础设施主题一致
- **3.0 优势**: EPIC 3 是对话 + 概念提取，正好是最大 LLM 消费者，这时切 provider 可以立刻验证效果

工作量: ~1 周

> [!question]+ 用户批注 - Sec 7
> dual-provider 方案理解对吗？Story 1.15 还是 3.0 更合适？需要先看 Anthropic prompt caching 怎么嵌入现有 rag_service 吗？
> （批注区）

---

## Sec 8: 两 PRD 对抗审查 — 12 项冲突（回应 audit #BMAD 下一步 内嵌要求 + audit #文件参考）

### 你的原批注
> "请你对抗性审查一下我们的 prd.md 和 14-scheme-a-implementation-prd.md，哪些内容不一致有冲突，请你向我增量提问。"
>
> "当前项目内部优先"

### 冲突规则

项目 `_bmad-output/planning-artifacts/prd.md` 胜出。外部 `14-scheme-a-implementation-prd.md` 为只读参考。

### 12 项冲突表

| # | 标签 | 维度 | prd.md（胜出） | 14-scheme PRD | Implication |
|---|---|---|---|---|---|
| 1 | 🔴 Block | 前端栈 | Obsidian Hybrid (L68) | Tauri 2 + React + ReactFlow (L269-279) | 所有 Tauri 代码作废，归档（Sec 1） |
| 2 | 🔴 Block | LLM 选型 | Claude + Gemini 双 (L76) | 开放多厂商可切 (L68) | Settings UI 里"模型切换"功能移除 |
| 3 | 🔴 Block | 节点创建 UX | callout + hotkey + Story 1.14 import (L142) | 5 种手动/对话/白板/导入/推荐 (L280-282) | 取消自动 OCR，改用 /extract_node Skill |
| 4 | 🔴 Block | 评分显示 | silent（frontmatter 更新） (L96) | 节点颜色动画反馈 (L387) | 无实时 node color feedback，只看 Dataview 查询 |
| 5 | 🟡 Attn | Dashboard | Dataview + QuickAdd + Meta Bind + Bases (L144) | 处方式 Dashboard (L147, LAK'24 ES=1.36) | Phase 1 只描述性，处方性延后 |
| 6 | 🟡 Attn | 关系存储 | frontmatter `relationships[]` (L142) | 独立 edge 对象 (L153) | 损失视觉 edge UI，wikilink + backlinks 补偿 |
| 7 | 🟡 Attn | Context 注入 | 本地 wikilink 图遍历 (L146) | RAG Tier 1 全量注入 (L314) | 上下文窗口变小但确定性强 |
| 8 | 🟡 Attn | 防递归考察 | `type: exam_board` frontmatter 启动前检查 (L160) | 切换节点时后台评分 (L385) | 启动阻止嵌套，非运行时 |
| 9 | 🟢 Cos | CLAUDE.md schema | 差异在行数 | 差异在行数 | 对齐 |
| 10 | 🟢 Cos | 6 Skill hotkey | Cmd+Option+{C,R,E,Q,X,P} (L144) | 6 核心 Skill 设计 (§4) | 命名一致 |
| 11 | 🟢 Cos | Graphify 集成 | L147 phase1 末 | 71x token 减 + Leiden 聚类 (§6) | 目标一致 |
| 12 | 🟢 Cos | Day 1 Spike | L145 已执行 | L112 "等待审核" | prd.md 推翻，14-scheme 历史化 |

### 🔴 Blocking 4 项详解

#### #1 前端栈
- **prd.md (L68)**: `Obsidian v1.5+ · Claudian plugin · 7 社区插件 + Bases`
- **14-scheme (L269-279)**: `Tauri 2 独立桌面 · React + ReactFlow 12.10.1 · Node.js Sidecar`
- **废弃的 14-scheme 条文**: 所有 Tauri 架构章节、ReactFlow 白板章节、Sidecar 状态机章节
- **影响的 Story**: Story 1.4 (hotkey) 改走 Obsidian addCommand 而非 Tauri IPC；Story 4.x 白板改走 Obsidian Canvas

#### #2 LLM 锁定
- **prd.md (L76)**: `Claude API + Graphiti 用 Gemini`
- **14-scheme (L68)**: `LLM 不锁定厂商，Settings 页面配置`
- **废弃的 14-scheme 条文**: Settings 里"选厂商"UI（等于 Sec 7 dual-provider 简化版）
- **影响的 Story**: Story 1.15（若定位 EPIC 1 末尾）

#### #3 节点创建 UX
- **prd.md (L142)**: `Templater + callout + /extract_node + Story 1.14 import`
- **14-scheme (L280-282)**: `5 种触发：手动 / 对话拉出 / 白板生成 / 导入 / 推荐`
- **部分继承**: 导入、推荐、对话拉出都保留（Story 1.14 + 2.7 + 3.1），手动改为 Templater 模板，白板生成由 /start_exam_board Skill 代替
- **废弃**: 粘贴自动 OCR
- **影响**: 不影响现有 Story；Story 1.14 的 AC 定稿要注意不和 3.1 / 2.7 重复

#### #4 评分显示
- **prd.md (L96)**: `silent 评分 + 书签式提取全部工作`
- **14-scheme (L387)**: `节点颜色变化感知精通度`
- **废弃**: Tauri 的 node color animation（Obsidian Canvas 不支持实时节点颜色逻辑）
- **替代**: Dataview 查询展示 mastery，或 Obsidian Bases 展示
- **影响的 Story**: Story 4.x (评分 + FSRS) 的 AC 文案要避免"节点颜色变化"描述

### 🟡 Attention 4 项是否需要逐条讨论？

5, 6, 7, 8 项都是"非阻塞但不一致"。建议下次 session 逐条小讨论（每项 10 分钟）。

> [!question]+ 用户批注 - Sec 8
> 🔴 Blocking 4 项全按 prd.md 胜出，你同意所有 "废弃" 和 "影响" 描述吗？🟡 Attention 4 项是否要下次 session 逐条讨论？还是全部默认 prd.md 胜出？
> （批注区）

---

## Sec 9: CLAUDE.md 修复方案 + bmad-search-strategy 更新（回应 audit #元根因）

### 你的原批注
> "我们直接把当前的仓库作为新的项目文档..."

5 项根因（audit 文档 Sec 九）+ Q1 选项 = 需要修改 4 个文件。

### 改动清单

本 response 不执行，列出建议:

#### 1. `canvas-learning-system/CLAUDE.md` 第 100-117 行

**现状** (Tauri 遗留):
```
## 风格参考文件
- 后端 service: backend/app/services/rag_service.py
- 前端 state: frontend/src/stores/chat-store.ts  ← Tauri 遗留
- 前端组件: frontend/src/components/ChatPanel.tsx  ← Tauri 遗留
```

**建议** (见 Sec 3 三类文档):
```
## 开发文档
...

## 参考文档
### BMAD 真相源（优先级递减）
1. _bmad-output/planning-artifacts/epics.md ⭐⭐⭐⭐⭐
...

## 已作废
- docs/*
- _decisions/*
```

#### 2. `.claude/rules/bmad-search-strategy.md`

**当前**: 搜索顺序 `implementation-artifacts → review → sprint-status → docs`

**建议添加 "阶段 0"**:
```
## 阶段 0: planning-artifacts 优先（BMAD 真相源 Layer 1-4）

开始 Story/Epic 实施前，**必须**先读:
- _bmad-output/planning-artifacts/epics.md (BDD + AC 真相源)
- _bmad-output/planning-artifacts/prd.md (需求文本)
- _bmad-output/planning-artifacts/architecture.md (技术约束)
- _bmad-output/planning-artifacts/ux-design-specification.md (UX 需求)
```

#### 3. 新建 `.claude/rules/bmad-truth-source.md`

```
# BMAD 7 层真相源（Claude Code 必读）

| 层 | 文件 | 优先度 | 用途 |
|---|---|---|---|
| 1 | planning-artifacts/epics.md | ⭐⭐⭐⭐⭐ | BDD + AC + Story 详情 |
| 2 | planning-artifacts/prd.md | ⭐⭐⭐⭐ | 需求文本 |
| 3 | planning-artifacts/architecture.md | ⭐⭐⭐ | 技术约束 |
| 4 | planning-artifacts/ux-design-specification.md | ⭐⭐⭐ | UX 需求 |
| 5 | implementation-artifacts/epic-N/*.md | ⭐⭐ | Story spec |
| 6 | implementation-artifacts/sprint-status.yaml | ⭐⭐ | Story 状态 |
| 7 | review/*.md | ⭐ | 审计 + UAT |
```

#### 4. `.claude/hooks/context-inject.js`

在 SessionStart 时注入 planning-artifacts/ 摘要（和 docs/known-gotchas.md 并列）。

### 执行时机

本 response 不执行。建议下次 session 优先做（工作量 ~70 min），降低未来"调研再偏"的概率。

> [!question]+ 用户批注 - Sec 9
> 4 个改动是否全授权下次 session 执行？还是挑选几个先做？
> （批注区）

---

## Sec 10: 下次 session 接管协议

### 你批注完 Sec 1-9 之后的动作

在新 session 里告诉我:
```
读 _bmad-output/review/epic-1-audit-response-2026-04-17.md 的 Sec 1-9 批注，按我的批注推进
```

### 执行优先级（基于默认推荐）

按你本次 audit 批注 + 3 个决策（Q1/Q2/Q3），下 session 默认执行顺序：

| # | 动作 | 前置条件 | 工作量 |
|---|---|---|---|
| 1 | 按 Sec 3 归档 Tauri v0 (git mv) | 你批注 "yes, archive" | ~15 min |
| 2 | 按 Sec 9 改 CLAUDE.md + bmad-search-strategy | 你批注 "yes, fix rules" | ~70 min |
| 3 | 按 Sec 6 用 `bmad-bmm-create-story` 生成 Story 1.14 正式 spec | 你批注 Sec 6 (AC 增删) | ~2 h |
| 4 | 按 Sec 7 决定 1.15 还是 3.0 处理 LLM 切换 | 你批注 Sec 7 (1.15 vs 3.0) | ~决策后 ~2 h 创建 Story spec |
| 5 | 按 Sec 4 改造 UAT 指南为对齐矩阵 | 你批注 Sec 4 (yes/no) | ~1 h |
| 6 | 启动 `bmad-bmm-dev-story` 跑 Story 1.2 + 1.8 并行 | 所有 Sec 批注完成 | 1 周 sprint |

### 不会自动做的事

- ❌ 归档 Tauri v0 代码（需你批 "yes"）
- ❌ 改 CLAUDE.md / hook / rules（需你批 "yes"）
- ❌ 创建正式 Story 1.14 spec（需通过 `bmad-bmm-create-story` Skill + 你批 AC）
- ❌ 修改后端代码（dependencies.py 等）
- ❌ 做 commit
- ❌ 修改外部 PRD（pretool-guard 阻断）
- ❌ 启动 `bmad-bmm-dev-story` 直到以上全部完成

### 本次 session 产出物清单

- ✅ 新建 `_bmad-output/review/epic-1-audit-response-2026-04-17.md`（本文件）
- ✅ 在 `epic-1-audit-2026-04-17.md` 头部加反链 `[[epic-1-audit-response-2026-04-17]]`
- ✅ Plan 文件保存在 `/Users/Heishing/.claude/plans/squishy-purring-hoare.md`
- ❌ 无 git commit

---

## 附录: 批注引用速查

本 response 按以下顺序回应 audit 的 9 条批注:

| Audit 批注 | 本文档 | 关键发现 |
|---|---|---|
| #偏差纠正 | Sec 1 | Tauri v0 真实存在，归档方案 |
| #真实架构 | Sec 2 | Layer 2 双入口（hotkey + callout） |
| #真实进度 | Sec 3 | 三类文档分层 |
| #UAT 指南 | Sec 4 | 对齐矩阵 + 偏离预警 |
| #4 决策 | Sec 5 | 确认回执 |
| #工作流 | Sec 6 | Story 1.14 Draft + Karpathy raw/ 层 |
| #执行计划 (内嵌) | Sec 7 | Graphiti dual-provider |
| #文件参考 | Sec 3 + Sec 9 | 项目内部优先 |
| #BMAD 下一步 | Sec 6 + Sec 8 | 1.14 EPIC 1 末尾 + 12 项冲突 |
| #元根因 | Sec 9 | CLAUDE.md + rules 修复 |

---

> [!tip]+ 综合意见 - 整份 response
> 对整份 response 有什么整体意见？最迫切先推进哪个 Sec？
> （批注区）
