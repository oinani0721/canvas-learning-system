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

实施顺序: 1.16 → 1.17 → 1.18 → 3.X

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
2. **在 Obsidian 打开 `canvas-vault/验收单/Story-{id}-*.md`**（Claude dev 完会自动 ship）
3. 在 Obsidian 跑 UAT 清单，满意就勾 ✅，不满意就用 `Cmd+Shift+A` 批注 `❌ 错误` 或 `❓ 提问`
4. 说一句 "dev story X.Y" 推进下一步，或 "Story X.Y 通过" mark done

**所有技术细节（YAML frontmatter / checkbox / BMAD Skill 调用 / sprint-status edit）由 Claude 处理，你不用关心。**

---

## ⛔⛔⛔ R4 × BMAD Definition of Done (DoD) — 2026-04-18 round-6 固化

> **用户刚需**：R4 工作流中的"ship demo + 用户 hands-on"环节之前靠 Claude 记性，现固化为 **dev-story 完成的三项必要条件**。任一缺失 = 未完成。

### dev-story 的三项完成条件（AND 关系）

| # | 条件 | 验收信号 |
|---|---|---|
| **DoD-1 技术层** | Git commit + tests 通过 + sprint-status `review` | `git log` 最新 commit 含 Story ID + `npm test` / `pytest` green |
| **DoD-2 spec 层** | Story spec 的 Dev Agent Record / File List / Change Log / Tasks 全打勾 | `_bmad-output/implementation-artifacts/epic-N/X-Y-*.md` 所有 `- [ ]` 变 `- [x]`，新增 Change Log 条目 |
| **DoD-3 R4 层** | **`canvas-vault/验收单/Story-{id}-{kebab-title}.md` 已 ship** | `ls canvas-vault/验收单/` 能看到新增文件，且结构符合 `_bmad-output/templates/uat-sheet-template.md` |

### DoD-3 验收单强制结构（7 段）

每份 `canvas-vault/验收单/Story-*.md` **必须包含**以下 7 段，用模板复制后填充：

```
1. 🎯 一句话目标（非技术，你能看懂）
2. 📖 你的视角（Behavior，作为...我想...以便...）
3. 🖥️ 交互流程（step-by-step，带 ASCII 或表格图示）
4. ✅ UAT 清单（N 步 - [ ] checkbox，可勾选，前置+主流程+边界+Esc 取消）
5. 🚦 验收结果（通过/不通过的下一步指引）
6. 📝 批注区（[!question]+ 空 callout 供你写，+ 历史 [!error]+ 追溯）
7. 🔗 技术 spec 引用（Story spec 路径 / 源代码 / 测试 / commit — 给 Claude 读的）
```

### 模板位置

`_bmad-output/templates/uat-sheet-template.md` — Claude 每次 dev-story 完成后 **复制此模板**填充，ship 到 `canvas-vault/验收单/`。

### correct-course 触发的验收单行为

当 `bmad-bmm-correct-course` 调整 Story 后：
- **不新建**新验收单，**覆盖**原 `canvas-vault/验收单/Story-{id}-*.md`
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

### Claude Code 自检清单（dev-story 结束时必跑）

```
DoD-1 ☐ git log 最新 commit 含 "Story: X.Y" 或 "PLAN-NNN"
DoD-1 ☐ tests 命令跑完 0 fail
DoD-1 ☐ sprint-status.yaml 里对应 key 是 "review"

DoD-2 ☐ Story spec 的 Dev Tasks 全部 [x]
DoD-2 ☐ Dev Agent Record / File List / Change Log 已填
DoD-2 ☐ AC 列表每条对应实现有 trace

DoD-3 ☐ canvas-vault/验收单/Story-{id}-*.md 存在
DoD-3 ☐ 该文件含 7 段（目标/Behavior/交互/UAT/结果/批注/trace）
DoD-3 ☐ 对用户消息中通知该文件位置

3 × ☐ 全部 ✓ → 才能告诉用户 "Story X.Y ready for review"
任一 ✗ → HALT，补齐后才算完成
```
