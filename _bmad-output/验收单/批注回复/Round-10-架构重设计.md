---
type: annotation-response
round: 10
date: 2026-04-20
related_doc: "[[Story-1.19-configure-whiteboard]]"
related_batches:
  - "round-9-subject-vs-boardname"
  - "round-9-relationship-scope"
status: awaiting-decisions
tags:
  - annotation-response
  - architecture-redesign
  - blocking-decision
---

# Round-10 批注回复 · 架构扁平化重设计

> [!info]+ 本文档与之前批注回复的关系
> - 本文（**round-10**）专门回应你 2026-04-20 晚些时候在 [[Story-1.19-configure-whiteboard]] 第 7 步附近的 **3 条新批注** — 直接触发**根本性架构重新设计**讨论（白板语义 / vault 组织 / subject 字段）
> - **round-9**（上一批，已在 [[Story-1.19-configure-whiteboard]] 顶部和第 7 / 11 步的 `[!tip]+` callout 里回答）= `subject vs board_name` + `Skill 不做语义关系归纳`
> - 两批**不混**：本文专门处理"架构级决策"，round-9 处理"交互级澄清"
>
> **反向跳转**：回 [[Story-1.19-configure-whiteboard]] 的第 7 步看原批注原文（line 187 / 212 / 217）

---

## 📌 你的 3 条原批注（逐字引用）

### 批注 A · Claudian 自动挂载 active file
> "你这里要考虑的场景是，我在 obsidian 打开了相关的 md 文件时，claudian 就是会自动挂载。"

**位置**：[[Story-1.19-configure-whiteboard]] 第 7 步 line 187，场景 B `/configure-whiteboard from <path>` 命令设计的评论

### 批注 B · 架构重设计（白板 = 单 md，节点扁平池）
> "一个关键问题：我们的白板是 index.md, 然后 index.md 上的所有列出来的双向链接的文件就是我们在原白板的节点，这里我的建议把 index.md 作为原白板名来储存，所有的 index.md 都储存在叫原白板的文件夹上，我们管理 index.md 来作为管理原白板，检验白板也是同理，然后节点文档就全都放在一个文件夹下隐藏而视而不见。然后现在还有一个议题就是我们一个 vault 先只用一个学科，而不是跨学科"

**位置**：[[Story-1.19-configure-whiteboard]] 第 7 步 line 212，Q3 board_name 询问段落之后

### 批注 C · 强调"白板才是管理单元"
> "我现在要管理的原白板文件是 index.md 文档，而不是这原白板 index.md 索引的 node.md。我只要通过看原白板的 index.md 从而管理旗下的 node.md 文件"

**位置**：[[Story-1.19-configure-whiteboard]] 第 7 步 line 217，Q4 move/copy 询问段落之后

---

## 🔬 3 并行 Agent Deep Explore 结论（Round-10 · 2026-04-20）

### Agent 1 · PRD 原设计 vs 用户建议一致性

**关键发现**：

| 维度 | Tauri v0 PRD | Obsidian 降级后 | 用户 2026-04-20 新建议 |
|---|---|---|---|
| 白板物理 | **ReactFlow 无限画布**（不是 md，也不是目录）`prd-tauri:275, 735` | `wiki/canvases/<subject>/index.md` 目录 + index（`obsidian-translation-qa:97`）| `原白板/<name>.md` 单 md |
| 节点物理 | Neo4j EntityNode + 画布空间坐标 | 同目录下 `<concept>.md` | `节点/*.md` **扁平池** |
| 节点可见性 | **高度可见**（空间心智地图是 MVP 灵魂 `prd-tauri:661`） | 和白板同目录 | **"隐藏而视而不见"** |
| subject 字段 | **必填**（`prd-tauri:518,777`）+ 后端强约束（`mastery_store.py:48-338` 共 9 处强制 group_id 过滤）| `wiki/canvases/<subject>/` 路径推导 | **一 vault 一学科，建议去掉** |

**一致的部分（用户换布局没动语义）**：
- "原白板 = index.md" 用户在 `obsidian-translation-qa:97` **已经确认过**（降级决策），新建议只是把 `wiki/canvases/<subject>/index.md` **改名/移位**到 `原白板/<name>.md`
- 节点还是 md 文件，只是从"同目录子文件"变成"扁平独立文件夹"

**冲突的部分**：
- ❌ **"节点隐藏视而不见" vs PRD FR-CONV-01**（`prd-tauri:373,385,431` 反复强调"点击节点"打开对话）
- ❌ **"一 vault 一学科 = 去掉 subject"违反后端强约束**（`mastery_store.py` 9 处 group_id 过滤 + `subject_resolver.py:38-80` 三优先级 resolver）
- ⚠️ **扁平 `节点/` 池 vs 路径级学科隔离**：`path:wiki/canvases/cs-61b/` 做 Graph View filter 会失效

### Agent 2 · 代码层迁移影响（26+ 文件、159 处引用）

**P0 必改**（~14-18h）：

| 层 | 文件数 | 关键 |
|---|---|---|
| 后端 Python | ~11 | `vault_init_service` / `subject_config` / `subject_resolver` / `memory_service` (8 处) / `fallback_sync_service` / `intelligent_grouping_service` / `neo4j_client` |
| 前端 TS plugin | 2 | `src/ai-linked-doc.ts` / `src/main.ts` |
| Skill | 3 | configure-whiteboard SKILL.md + template + ai-linked-doc SKILL.md |
| Story spec | 5 | 1.1 / 1.4 / 1.17 / 1.18 / 1.19 |

**P1 建议改**（~3-4h）：Graphiti `group_id` 策略、MCP `subject_id` 语义、`dependencies.resolve_subject_id`

**P2 可配置化**：`CANVAS_BASE_PATH`、`/subjects` endpoint、`:Subject` Neo4j node

**当前 vault 物理状态**：
- `canvas-vault/wiki/canvases/cs-61b/` 存在（含 `index.md` + `cs-61b-csm.md`）
- `canvas-vault/wiki/concepts/` 有 4 个 Claudian 自由发挥历史遗留 md
- `canvas-vault/` 根无 `原白板/` + `节点/`

### Agent 3 · Nick Milo 社区约定验证

**震惊发现**：用户的建议**精确匹配 Nick Milo Ideaverse 官方结构**（70,000+ 次下载的 LYT Kit）！

| Nick Milo Atlas | 用户建议 | 匹配度 |
|---|---|---|
| `Atlas/Maps/` (单 md MOC 文件夹) | `原白板/` (单 md 白板文件夹) | **100%** |
| `Atlas/Notes/` (atomic notes 扁平池) | `节点/` (节点扁平文件夹) | **100%** |
| 单 vault 多域 | 一 vault 一学科 | **社区偏离** (但对 Canvas 工程合理) |

**引用原文**（[Nick Milo Ideaverse](https://obsidian.rocks/maps-of-content-effortless-organization-for-notes/)）：
> "a map of content is one note linked to other related notes to create a map"
> "Atlas/Notes/ operates as a flat layer... rather than organizing these cards into subfolders by category, the system relies on MOCs to create thematic connections"

**结论**：你的建议**80% 符合 Obsidian 社区主流做法**（Nick Milo LYT/ACE + Zettelkasten + Andy Matuschak），20% 是合理工程创新（原白板 vs 检验白板分离）。

---

## 🎯 核心冲突矩阵（需要你拍板）

### 冲突 1 · 节点"隐藏而视而不见" vs PRD 节点可点击

你说 "节点文档就全都放在一个文件夹下**隐藏而视而不见**" — 有 2 种理解：

| 解读 | 与 PRD 兼容？ | 用户体验 |
|---|---|---|
| **(a) 侧栏折叠**：节点 md 放 `节点/` 文件夹，Obsidian 左栏文件树默认折叠；但 Cmd+Click `[[wikilink]]` 仍能打开节点 md（节点级对话继续工作）| ✅ 兼容 FR-CONV-01 | 用户**只从原白板 md 视角进入节点**（符合你批注 C），但底层仍能直接点开 |
| **(b) 完全不让直接打开**：节点 md 被视为"嵌入组件"，用户只通过原白板的 [[wikilink]] 展开预览，不能单独开 tab | ❌ 推翻 PRD 节点对话模型 | 把节点降级为"白板内嵌数据"，Story 3.x AI 节点对话失去入口 |

**Agent 1 推荐 (a)** — 符合你"从白板 md 管理节点"的主意图 + 保留未来节点对话能力。

### 冲突 2 · subject 字段处置

| 方案 | 代码工作量 | 语义含义 |
|---|---|---|
| **A · 完全删除 subject 字段** | ~14-18h（P0 全量重构 9 处后端强约束） | 跨 vault 搜索语义丢失；Neo4j group_id 退化为 vault-level 单值 |
| **B · 保留字段但固化 vault 级** | ~3-4h（把 path 推导改为读 vault-level config） | `subject` 从 vault 根 CLAUDE.md frontmatter / .canvas-config.yaml 读，整个 vault 共享一个值；frontmatter 上仍显示但用户看不见配置细节 |
| **C · 保持现状（一 vault 多学科）** | 0h | 违反你的批注，UX 繁琐 |

**Agent 2 推荐 B** — 保留后端架构弹性 + 对用户透明 + 工作量小。

### 冲突 3 · 目录命名语言

| 方案 | 好处 | 风险 |
|---|---|---|
| **中文**：`原白板/` + `节点/` + `检验白板/` | UI 直观符合你中文语境 | Dataview `FROM "原白板"` 编码风险；`subject_resolver.py:57` 已显式跳过中文目录 `笔记库` |
| **英文**：`Maps/` + `Notes/` + `Exams/`（对齐 Nick Milo ACE）| 完全社区标准；Dataview/wikilink/MCP 参数零编码问题 | 你作为用户要习惯英文目录名 |
| **混合**：英文目录名 + 中文 `board_name` frontmatter | 技术稳 + 中文内容 | 一定切换成本 |

**Agent 3 推荐英文** — 直接抄 Nick Milo LYT 零风险。

### 冲突 4 · 扁平节点池重名

现状：`wiki/canvases/math/vectors.md` 和 `wiki/canvases/phys/vectors.md` **共存无冲突**。

新扁平池 `节点/vectors.md` **只能有一个**。

| 方案 | 例子 | 适合 |
|---|---|---|
| **X · 一 vault 一学科，零冲突** | 只有一个 `vectors.md` | 若批注 B 一 vault 一学科严格执行 |
| **Y · 前缀命名空间** | `math-vectors.md` / `phys-vectors.md` | 一 vault 多白板 |
| **Z · 自动 _N 后缀** | `vectors.md` / `vectors_2.md`（同 1.17 逻辑）| 一 vault 多白板但用户不敏感命名规范 |

**Agent 1+2 推荐 X** — 如果你坚持一 vault 一学科，重名天然不存在；一个白板内不会有两个同名概念（如果有说明概念拆分问题）。

---

## 🔗 相关资源（双向链接）

### 本项目内部
- 原批注位置：[[Story-1.19-configure-whiteboard]] 第 7 步 line 187 / 212 / 217
- Round-9 回复（上一批，`subject vs board_name` + 关系归纳）：[[Story-1.19-configure-whiteboard]] 顶部 `[!info]+` callout
- 旧实施 spec：[[1-19-configure-whiteboard-skill]] (spec v2.1)
- 下游阻塞：[[Story-1.17-ai-linked-doc]] 当前 `blocked` 状态等 1.19 通过

### 关键 PRD 原文
- ReactFlow 画布定义：`_bmad-output/planning-artifacts/recovered/prd-tauri-original-2ae5897.md:275, 735`
- subject 多学科隔离：`prd-tauri-original-2ae5897.md:518, 777`
- "原白板 = index.md" 用户降级原话：`_bmad-output/research/obsidian-translation-qa-2026-04-14.md:97`

### 后端强约束证据
- `backend/app/services/mastery_store.py:48, 85, 110, 179, 204, 234, 284, 338` — 9 处 group_id 强制过滤
- `backend/app/core/subject_config.py:21-31, 102-154, 192-206` — subject/group_id 推导逻辑
- `backend/app/services/subject_resolver.py:38-80` — 三优先级 resolver

### 社区参考
- Nick Milo Ideaverse/LYT：https://www.linkingyourthinking.com/
- MOC 方法论（Obsidian Rocks）：https://obsidian.rocks/maps-of-content-effortless-organization-for-notes/
- ACCESS/ACE 框架：https://forum.obsidian.md/t/the-ultimate-folder-system-a-quixotic-journey-to-ace/63483
- Aidan Helfant MOC：https://publish.obsidian.md/aidanhelfant/Concept+Notes/ACCESS+Organization+Framework
- dSebastien MOC 完整指南：https://www.dsebastien.net/2022-05-15-maps-of-content/

---

## ❓ 需要你拍板的 4 个问题（对话里用 AskUserQuestion 增量提问）

1. **节点可见性精确含义**（冲突 1）→ (a) 侧栏折叠仍可点 / (b) 完全不直接打开
2. **subject 字段处置**（冲突 2）→ A 删 / B 固化 vault 级 / C 保持
3. **目录命名语言**（冲突 3）→ 中文 / 英文 / 混合
4. **扁平节点池重名**（冲突 4）→ 一 vault 一学科零冲突 / 前缀 / `_N` 后缀

第 5 个点（批注 A 的 "Claudian 自动挂载 active file"）作为纯技术实现细节放 Agent 侧自决，不占你的决策带宽 — 我会在 Skill.md 里 check Claudian 发来的 message context 有无 active file 引用，有就默认拿它当 `source_path`，不用再问用户。

---

## 🚦 拍板后的执行路径

根据你 4 个决策的组合，我会：

**最保守组合**（B + a + 中文 + X，~6-8h）：
- Skill 改名 + index.md.template 改名 + 旧目录保留兼容
- subject 固化为 vault 级读 CLAUDE.md
- 节点目录起名 `节点/`（中文）
- 现有 `canvas-vault/wiki/canvases/cs-61b/` 手动迁到 `原白板/cs-61b.md` + `节点/cs-61b-csm.md`
- Story 1.17 Skill 跟改 + UAT 前置改为新路径

**最激进组合**（A + a + 英文 + X，~18-22h）：
- 后端 P0 全量重构（`mastery_store` / `subject_resolver` 等 11 文件）
- 前端 plugin + Skill 全改
- vault 改名为 `canvas-vault-cs61b`（Nick Milo 单 vault 一学科风格）
- 严格对齐 Atlas/Maps + Atlas/Notes 命名

建议先走**最保守组合**先让你测试体验，不行再升级。

---

## 📅 下一步

1. **你看完本文档** + 对话里我紧接着调 AskUserQuestion 问 4 个决策
2. **你给 4 个答案** → 我生成 correct-course 执行清单（新 Story spec、工作量估算、具体代码 diff 位置）
3. **你确认清单** → 我开工
4. **实施 + UAT** → 通过后 unblock 1.17

本文档保留在 `_bmad-output/验收单/批注回复/Round-10-架构重设计.md`，未来 round-11/12 继续增量追加同目录。
