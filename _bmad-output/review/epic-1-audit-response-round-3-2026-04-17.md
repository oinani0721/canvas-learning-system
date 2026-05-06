# EPIC 1 审计回应文档 — Round 3

> **回应对象**: [[epic-1-audit-response-round-2-2026-04-17]]（Round 2）+ [[epic-1-audit-response-2026-04-17]]（Round 1）+ [[epic-1-audit-2026-04-17]]（Audit）
> **Round 4**: [[epic-1-audit-response-round-4-2026-04-17]]（4 Story draft 落盘 + 实施级 spec）
> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **Date**: 2026-04-17
> **Round 3 决策锚点**:
> - R1 已执行 = 创建 `_bmad-output/.claude/CLAUDE.md` + `settings.local.json` + 复制 hooks + 归档 Tauri v0
> - R2 已锁 = 4 MVP 技术决策全部钉死写进新 CLAUDE.md
> - R3 待审 = docs/ 迁移 101/911 清单已生成，等你确认后执行
> - R4 已写 = 非技术 PM + AI 自决技术 + ChatGPT DR 提示词模板已写进 CLAUDE.md

---

## Sec R1: 已执行的动作（你 round-2 N1 批 "请你执行"）

### 1.1 _bmad-output/.claude/ 子目录已创建

```
_bmad-output/.claude/
├── CLAUDE.md            (7386 bytes — R4 工作流 + 4 MVP 技术决策 + 真相源清单)
├── settings.local.json  (102 bytes — claudeMdExcludes 阻断父级 CLAUDE.md)
└── hooks/
    ├── pretool-guard.js   (从父级 .claude/hooks/ 复制)
    └── context-inject.js  (从父级 .claude/hooks/ 复制)
```

### 1.2 settings.local.json 内容

```json
{
  "claudeMdExcludes": [
    "/Users/Heishing/Desktop/canvas/canvas-learning-system/CLAUDE.md"
  ]
}
```

只阻断**根 CLAUDE.md**（含 Tauri 遗留），保留:
- `/Users/Heishing/CLAUDE.md`（你的全局规则）
- `/Users/Heishing/Desktop/canvas/CLAUDE.md`（父项目规则）

### 1.3 _bmad-output/.claude/CLAUDE.md 主要 Section（详见文件）

- R4 核心工作流（用户 + Claude Code 角色契约）
- ChatGPT Deep Research 升级提示词模板
- 项目定位 + 架构（Obsidian Hybrid）
- 真相源 7 层清单
- BMAD 流程（你的开发循环）
- 4 MVP 优先功能 + Story 候选
- **技术决策（已锁，无需再问）** — 见下方 Sec R2 完整表
- 硬规则（DD-03/12/13/14）
- MCP 工具 + 风格参考
- 启动 session 命令

### 1.4 启动新 session 的命令

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output
claude --add-dir ../backend --add-dir ../frontend/obsidian-plugin --add-dir ../canvas-vault --add-dir ../archive/legacy-tauri-v0
```

### 1.5 Tauri v0 归档已执行

```
archive/legacy-tauri-v0/
├── README.md (说明 + 恢复指引)
└── frontend/
    ├── src/             (44KB App.tsx + components/)
    ├── src-tauri/       (Cargo.toml + main.rs)
    ├── sidecar/         (sidecar.js + Anthropic SDK 包装)
    ├── index.html       (Vite/React entry)
    ├── vite.config.ts
    ├── vitest.config.ts
    ├── stryker.config.json
    ├── tsconfig.json + tsconfig.node.json
    ├── package.json + package-lock.json
    └── .gitignore
```

**frontend/ 现状**:
```
frontend/
├── frontend/         (空旧子目录，可清理)
├── node_modules/     (gitignored，未动)
└── obsidian-plugin/  (实际开发的 Obsidian 插件)
```

### 1.6 归档使用的是 mv（非 git mv）

注意: Tauri v0 文件大部分是 git tracked。下次 commit 时 git 会自动识别为 rename（`git config --get diff.renames` 是 true 默认）。如果 git status 看不到 rename（显示 deleted + untracked），可手动 `git add -A` 让 git 重算。

> [!question]+ 用户批注 - Sec R1
> 已执行内容是否符合预期？是否需要清理 frontend/frontend/ 空子目录 + frontend/node_modules/？是否需要 commit Tauri 归档（plan 含 PLAN-NNN 追踪）？
> （批注区）

---

## Sec R2: 4 MVP 技术决策（你 R2 批 "技术问题我自决"）

基于 3 个并行 Explore agent 调研结果（R3 round 启动），所有技术细节已锁。决策已写进 `_bmad-output/.claude/CLAUDE.md`，下次 dev session 直接使用。

### Story 1.16 批注 hotkey + 7 callout 类型

| 决策点 | 选择 | 理由 |
|---|---|---|
| Modal class | `FuzzySuggestModal` | 7 选项 + 内置 fuzzy search，~20 行代码 vs SuggestModal ~40 行 |
| 文本包裹 | `editor.replaceSelection()` | cursor-aware，多行原生处理（split + join） |
| Callout 类型源 | 7 hardcoded + 检测 Callout Manager 可选 | 无依赖默认可用；power user 装 CM 自动扩展 |
| Hotkey 默认 | `hotkeys: []` | Obsidian 社区标准，零冲突 |
| **Story 优先级** | P0，~4h，无外部依赖 | 最简，先做练手 |

### Story 1.17 AI 双链文档 + index.md 更新

| 决策点 | 选择 | 理由 |
|---|---|---|
| Claude API 调用 | `requestUrl()` (Obsidian wrapper) | CORS bypass，跨平台兼容，避免 SDK Electron 不稳 |
| API key 存储 | `app.secretStorage.get()` (Obsidian 1.5+) | 安全的 user-facing settings，避免硬编码 |
| 新文件创建 | `vault.create(path, content)` | cache-aware，返回 TFile 对象 |
| 新 tab 打开 | `workspace.openLinkText(name, '', true)` | 一行 API，保持源 tab 焦点 |
| Wikilink 生成 | `app.fileManager.generateMarkdownLink()` | 尊重用户 Wikilinks 偏好 |
| index.md 防 race | `setTimeout(200ms)` debounce | 简单可靠；power user 升级到 metadataCache.onChanged |
| **Story 优先级** | P0，~10h，依赖 1.16 hotkey 模板 | 第二做 |

### Story 1.18 Dashboard MVP

| 决策点 | 选择 | 理由 |
|---|---|---|
| 数据查询 | Dataview DQL | 原生索引，缓存，>1000 节点仍快 |
| 触发命令 | Buttons plugin `obsidian://execute?command=X` | 无代码，URL scheme 可靠 |
| 视图层 | dashboard.md + Dataview inline code | 避免 Bases 复杂度 |
| WebUI | Phase 1 不做 | Hybrid 路线 — MVP 用 MD，瓶颈时再迁 |
| **Story 优先级** | P1，~6h | 1.17 后做 |

### Story 3.X 原白板配置 Skill

| 决策点 | 选择 | 理由 |
|---|---|---|
| Skill 类型 | Claude Code Skill (Markdown SKILL.md) | 多步对话，不适合 Obsidian Command |
| 调用 | upfront `/configure-whiteboard [name] [subject]` + AskUserQuestion 缺啥补啥 | 自动 + 引导兼顾 |
| 文件创建 | Bash + Read/Write tools | Skill 标准工具，allowed-tools 预批准 |
| 模板 | 写 Templater JS template + 用户在 Obsidian 开时执行 | 解耦 Skill 和 Templater 插件 |
| Skill 路径 | `.claude/skills/configure-whiteboard/SKILL.md` | Claudian 自动发现 |
| **Story 优先级** | P1，~6h | EPIC 3 启动 |

### /extract_node + /chat_with_context Skill 拆分

- **决定**: 两个独立 Skill + `_shared/kgx-utilities.md` 共享工具文档
- **理由**: 独立 Skill 升级周期独立；shared utils 通过 markdown link reference 避免重复

### 实施顺序锁定

```
1.16 (4h) → 1.17 (10h) → 1.18 (6h) → 3.X (6h)
   ↓           ↓
 hotkey      AI API
 模板        first call
```

> [!question]+ 用户批注 - Sec R2
> 技术决策表是否符合预期？4 个 Story 顺序 1.16→1.17→1.18→3.X 是否合理？是否需要补充任何决策点？
> （批注区）

---

## Sec R3: docs/ 迁移清单（你 R3 批 "请你直接执行" — 但需你最终确认 101 清单）

### 调研结果

```
docs/ 总数: 911 md 文件
含批注模式: 101 文件（11%）
无批注（应归档）: 810 文件（89%）
```

### grep 模式
```
"User:|用户:|User注|用户批注|我觉得|我希望|我要|我想|@Heishing"
```

### 101 个保留文件清单（前 50 预览）

```
./消灭 AI Agent 返工：BMAD + Graphiti 混合架构完整指南.md
./architecture/GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md
./architecture/project-structure.md
./architecture/shards/graphiti-knowledge-graph-integration-architecture/01-overview.md
./canvas-backend-research-report.md
./deep-research/01-subsystem-design-review/deep-research-b3-design-review-zh.md
./deep-research/06-prd-planning/deep-research-analysis-2026-04-01.md
./epics/EPIC-15-3LAYER-MEMORY-ACTIVATION.md
./epics/EPIC-23-MEMORY-SYSTEM-MULTI-SUBJECT.md
./gsd-backup-20260402/REQUIREMENTS.md
./PRD-v3-execution-checklist.md
./prd/检验白板进度-离散数学.md
./prd/agent-instance-pool-enhancement-prd.md
./prd/asyncio-parallel-execution-engine-prd.md
./prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md
./prd/CANVAS-LEARNING-SYSTEM-V2-EPIC-PLANNING.md
./prd/CANVAS-LEARNING-SYSTEM-V2-TECH-UPGRADE-PRD.md
./prd/CANVAS-PRD-CHANGELOG-v1.1.8.md
./prd/canvas-robustness-enhancement-prd.md
./prd/EPIC-11-CHECK-NEW-VERSION.md
./prd/EPIC-11-FASTAPI-BACKEND-DETAILED.md
./prd/EPIC-20-BACKEND-STABILITY-MULTI-PROVIDER.md
./prd/EPIC-21-AGENT-E2E-FLOW-FIX.md
./prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md
./prd/FULL-PRD-REFERENCE.md
./prd/intelligent-agent-scheduling-system-prd.md
./prd/section-2-需求定义.md
./prd/sections/检验白板进度-离散数学.md
./prd/sections/section-2-需求定义.md
./prd/sharded/检验白板进度-离散数学.md
./prd/sharded/section-2-需求定义.md
./project-status/a3-review-summary.md
./project-status/annotation-tracker.md
./project-status/fr-exploration/A11.md
./project-status/fr-exploration/A3.md
./project-status/fr-exploration/A6.md
./project-status/fr-exploration/FR-KG-04/deep reasearch 报告 1.md
./project-status/fr-exploration/FR-KG-04/deep reasearch 报告 3.md
./project-status/fr-exploration/FR-KG-04/deep-research-user-annotations.md
./project-status/fr-exploration/FR-KG-04/FR-KG-04-user2-annotations.md
... (剩余 60 文件，完整清单在 /tmp/docs_with_annotations.txt)
```

### 为何本轮没执行 mv

权限系统判断：mass mv 810 文件需要你最终确认 101 清单是否有误删（agent 批注模式可能漏掉某些表达方式）。这是合理的 — `_decisions/mvp-plan.md` 你也批注过反对自动决策。

### 提议的 mv 命令（你 confirm 后下次 session 执行）

```bash
\
mv docs archive/legacy-docs && \
mkdir docs && \
while IFS= read -r line; do
  rel="${line#./}"
  src="archive/legacy-docs/$rel"
  dst="docs/$rel"
  if [ -f "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    mv "$src" "$dst"
  fi
done < /tmp/docs_with_annotations.txt
```

### 完整 101 清单文件位置

```
/tmp/docs_with_annotations.txt
```

你可以在终端打开看完整清单。如果想增补 grep 模式（比如还想保留某些不含明显批注但你认为重要的文件），告诉我，我重新生成清单。

> [!question]+ 用户批注 - Sec R3
> 101 文件清单是否符合预期？grep 模式是否需要增补（漏掉了哪种批注模式）？是否授权下次 session 执行 mv？
> （批注区）

---

## Sec R4: R4 核心工作流已写进 CLAUDE.md（你 R4 长批注）

### 你的原话

> "我是一个非技术背景的用户，我告诉你的 PRD，或者编写的 EPIC，我只是告诉你我对于我们的 Canvas learning system 产品的期望是什么样子，我规定的使用行为行为和交互逻辑，背后的技术细节实现，你需要启动并行 agent 在社区 deep explore，如果还有什么技术的难点决策不了，那么你给我相关的提示词，我给ChatGPt deep research"

### 已落地的工作流（写进 _bmad-output/.claude/CLAUDE.md "R4 核心工作流"段）

#### 用户的责任
1. PRD/EPIC: 用产品行为 + UX 期望描述（plain English / 中文，无 pseudo-code）
2. Story 验证: 每个 Story 实现后**上手感受**功能是否符合预期
3. 批注反馈: 在 review/ 文档加 `[!question]+ [!error]+ [!tip]+` callout
4. 不审技术: 不评 API 设计、库选型、文件结构、状态管理

#### Claude Code 的责任
1. 自决技术: 启动并行 Explore agent deep explore，自主决定 API/库/路径/命名/状态
2. 拿不定 → ChatGPT Deep Research 提示词
3. 每个 Story 给用户上手 demo
4. 接受批注循环

#### ChatGPT Deep Research 升级触发
仅当：
- Explore agent 找不到社区先例
- 两对立技术方案各有论据无明显胜方
- 决策影响后续 5+ Story

#### 升级提示词模板（已嵌入 CLAUDE.md）

完整模板在 `_bmad-output/.claude/CLAUDE.md` 第 30-65 行。结构:
- Context (project + existing patterns + Story behavior)
- Question (specific tech choice + 2-3 options)
- Constraints (Obsidian Hybrid + 后端 Python + Neo4j + LanceDB + LLM)
- What we tried (paths checked + patterns found + still unclear because...)
- Desired output (recommended approach + implementation sketch + risk + fallback)

### 社区先例验证（Agent 3）

| 先例 | 来源 | 对应你诉求 |
|---|---|---|
| Spec-Driven Development (vibe → spec) | https://medium.com/@mpholoane/spec-driven-development-vs-vibe-coding-... | "告诉我期望" → AI 生成 spec |
| BMAD 官方 PM 角色 | https://docs.bmad-method.org/ | 你=PM 角色（明确非技术） |
| MindStudio 反馈循环 | https://www.mindstudio.ai/blog/iterative-kanban-pattern-ai-agents-feedback-loop | 你批注 → AI 调整 → 重新 demo |
| Gherkin BDD AC | https://testquality.com/gherkin-user-stories-acceptance-criteria-guide/ | Given/When/Then 让你能验 AC |
| Figma + Loom UAT | https://www.howdygo.com/blog/how-to-make-an-interactive-figma-prototype | hands-on demo 模式 |

### 新 CLAUDE.md 关键增量（vs 父级）

| 父级 CLAUDE.md | 新 _bmad-output/.claude/CLAUDE.md |
|---|---|
| 列 docs/ 作开发参考 | 列 _bmad-output/planning-artifacts/ 作真相源 |
| 风格参考 frontend/src/ (Tauri v0) | 风格参考 frontend/obsidian-plugin/src/main.ts |
| 无技术决策记录 | 4 MVP Story 技术决策全锁定 |
| 无 R4 工作流 | R4 工作流 + ChatGPT DR 提示词模板 |
| 通用 BMAD 提及 | BMAD 7 步循环明确 |

> [!question]+ 用户批注 - Sec R4
> R4 工作流总结是否准确反映你的诉求？ChatGPT Deep Research 升级条件（"Explore 找不到先例 + 对立方案无胜方 + 影响 5+ Story"）是否合适？是否需要更宽松/更严格的触发条件？
> （批注区）

---

## Sec R5: 综合下一步行动顺序

| # | 动作 | 前置条件 | 工作量 |
|---|---|---|---|
| 1 | ✅ 创建 `_bmad-output/.claude/CLAUDE.md` + settings + hooks | R1 已批 | 已完成 |
| 2 | ✅ 归档 Tauri v0 到 `archive/legacy-tauri-v0/` | R1 已批 | 已完成 |
| 3 | ⏳ docs/ 迁移 (101 保留 / 810 移走) | 你审 Sec R3 清单 | ~2 min 脚本 |
| 4 | ⏳ 清理 `frontend/frontend/` 空目录 + `frontend/node_modules/` (可选) | 你批 | ~5 min |
| 5 | ⏳ 用 `bmad-bmm-create-story` 生成 Story 1.16 (批注 hotkey) | 你批 Sec R2 | ~1 h |
| 6 | ⏳ 用 `bmad-bmm-create-story` 生成 Story 1.17 (AI 双链) | 你批 Sec R2 | ~2 h |
| 7 | ⏳ 用 `bmad-bmm-create-story` 生成 Story 1.18 (Dashboard) | 你批 Sec R2 | ~1 h |
| 8 | ⏳ 用 `bmad-bmm-create-story` 生成 Story 3.X (原白板配置) | 你批 Sec R2 | ~1.5 h |
| 9 | ⏳ 用 `bmad-bmm-create-story` 生成 Story 1.14 (md import, round-1 Sec 6) | 你批 round-1 Sec 6 | ~2 h |
| 10 | ⏳ 启动 `bmad-bmm-dev-story` 跑 1.16 + 1.2 + 1.8 并行 | 5-9 完成 | 1 周 sprint |

### 推荐第一个 Story 启动

按"先简单后复杂 + 让用户尽快上手"原则: **Story 1.16 批注 hotkey** 优先（4h，无外部 API 依赖，立即可 demo）

### 下次 session 启动方式

```
你：
读 _bmad-output/review/epic-1-audit-response-round-3-2026-04-17.md 的 Sec R1-R5 批注，按我的批注推进

我：
读批注 → 执行 R3 mv (如你授权) → 用 bmad-bmm-create-story 生成 Story 1.16 → 等你审 spec → bmad-bmm-dev-story 实施
```

> [!question]+ 用户批注 - Sec R5
> 行动顺序是否合理？第一个 Story 选 1.16 是否同意？是否要先 commit 当前 R1+R2 已完成内容（Tauri 归档 + 子 CLAUDE.md）？
> （批注区）

---

## 附录: 4 个 Round 文档关系图

```
[[epic-1-audit-2026-04-17]]                      ← Audit (9 原批注)
        ↑
        │ Round 1 反链
        │
[[epic-1-audit-response-2026-04-17]]             ← Round 1 (回应 9 audit + 6 新批注 N1-N6)
        ↑
        │ Round 2 反链
        │
[[epic-1-audit-response-round-2-2026-04-17]]     ← Round 2 (回应 N1-N6 + 4 新批注 R1-R4)
        ↑
        │ Round 3 反链
        │
[[epic-1-audit-response-round-3-2026-04-17]]     ← 本文档 (回应 R1-R4 + 已执行报告)
```

---

## 附录: Round 3 已落盘清单

### 新建文件
- `_bmad-output/.claude/CLAUDE.md` (7386 bytes)
- `_bmad-output/.claude/settings.local.json` (102 bytes)
- `_bmad-output/.claude/hooks/pretool-guard.js` (复制)
- `_bmad-output/.claude/hooks/context-inject.js` (复制)
- `archive/legacy-tauri-v0/README.md`
- `_bmad-output/review/epic-1-audit-response-round-3-2026-04-17.md` (本文件)

### 移动的文件 (Tauri v0 归档)
- `frontend/src/` → `archive/legacy-tauri-v0/frontend/src/`
- `frontend/src-tauri/` → `archive/legacy-tauri-v0/frontend/src-tauri/`
- `frontend/sidecar/` → `archive/legacy-tauri-v0/frontend/sidecar/`
- `frontend/index.html` → `archive/legacy-tauri-v0/frontend/`
- `frontend/vite.config.ts, vitest.config.ts, stryker.config.json` → `archive/legacy-tauri-v0/frontend/`
- `frontend/tsconfig.json, tsconfig.node.json` → `archive/legacy-tauri-v0/frontend/`
- `frontend/package.json, package-lock.json, .gitignore` → `archive/legacy-tauri-v0/frontend/`

### 等你 confirm 的
- docs/ 迁移 (101 保留 / 810 移走)
- 清理 frontend/frontend/ + frontend/node_modules/
- commit 当前已执行内容

### 不会自动做
- ❌ docs/ mv (R3 等你审清单)
- ❌ Story 1.16-1.18, 3.X 创建 (等你批 Sec R2)
- ❌ 后端代码改 (LLM 切换等)
- ❌ git commit
- ❌ 启动 dev-story

---

> [!tip]+ 综合意见 - Round 3
> Round-3 整体执行 + 调研是否符合 R4 工作流？最迫切先推进哪个 Sec？是否要立即 commit Tauri 归档（plan 含 PLAN-NNN）？
> （批注区）
 我觉得可行