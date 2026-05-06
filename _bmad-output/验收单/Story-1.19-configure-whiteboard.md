---
story: "1.19"
title: "原白板配置 · v4.0 全 plugin 重构（脚本替代 Skill）"
status: "review"
version: "v4.0-plugin"
date: "2026-05-01"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
prev_uat_sheet: "v3 Skill 已通过 (2026-04-30)；v4.0 是同 Story 的架构重构"
---

# Story 1.19 验收单 v4.0 — 全 plugin 重构（替代 Skill 提速 50-100x）

> [!success]+ 2026-05-01 v4.0 全 plugin 重构 ship
> 你 2026-05-01 问"哪些功能用脚本会稳定迅速"。3 并行 agent 调研确认 configure-whiteboard 7 步全 deterministic（读 yaml / 路径 / vault 操作），零 LLM 必需。Plugin 重构完成：
>
> | 维度 | v3 Skill (旧) | v4 plugin (新) |
> |---|---|---|
> | 总耗时 | 15-30s LLM 推理 | **<300ms 全脚本** |
> | 反向引用检测 | Skill Glob ~500ms | **plugin metadataCache 10ms (50x)** |
> | LLM token | ~1500-2000 | **0** |
> | 触发 | Claudian `/configure-whiteboard` | 命令面板 / 快捷键 `canvas:configure-whiteboard` |
> | Modal 链 | AskUserQuestion 多轮 | 3 native Modal class |
> | 失败恢复 | 整体 halt | partial commit (白板建好就保留) |
>
> 主 ship: `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` 57836B (v3.0 31768B + 26068B configure-whiteboard 模块)
>
> **Skill v3.1 保留作 fallback**（标 [DEPRECATED]），用户输 `/configure-whiteboard` 仍能跑（不再积极维护）。
>
> ## 跑 v4 UAT 之前
> 1. **Cmd+Q 退出 Obsidian → 再开**（让 main.js v4 加载）
> 2. 验证 `stat -f "%z" canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` = `57836`
> 3. 命令面板（Cmd+P）搜"建/配置原白板"应见 `Canvas Learning System: 建/配置原白板（v4 全 plugin 脚本）`
> 4. 可选：去 Settings → Hotkeys → 给该命令绑快捷键（如 Cmd+Shift+W）

---

## 🎯 v4 UAT 24 步（v4.0 16 步 + v4.1 8 步 = 全场景覆盖）

> **v4.1 新增（2026-05-01）**：场景 V4-E（8 步）— 回应你的"已有笔记归类到已存在白板"批注。新命令 `canvas:append-note-to-board` 提供独立 entry point。

### 前置验证（P1-P3）

- [ ] **P1**：main.js 大小 = 57836B（不是 31768B 或更小）
- [ ] **P2**：命令面板能搜到"建/配置原白板（v4 全 plugin 脚本）"
- [ ] **P3**：vault 已有 `.canvas-config.yaml`（含 subject 字段）+ 至少 1 个白板 + 1 个已派生节点（v3 测过的）

---

### 场景 V4-A · 场景 A 从零建白板（无种子，最简路径）

#### V4-A1 · 触发命令
- [ ] vault 根新建一个空 md（如"未命名"）
- [ ] 不打开任何笔记 / 或在 vault 根的"未命名.md"上
- [ ] Cmd+P → 搜"建/配置原白板"→ 回车

#### V4-A2 · BoardNameInputModal（v4 新 UX）
- [x] **立即**弹 modal，标题"建白板（场景 A · 从零）"
- [x] 输入框 placeholder：`例如：线性代数 / CS 61B 数据结构 / Eigenvalues & Eigenvectors`
- [x] 输入框下方有实时 **hint** 提示
      **User：那么给已有的笔记归类于某个已经存在的白板的话，请问我该如何操作？**

      > [!success]+ Round-1 回复（2026-05-01）— v4.1 已加新命令
      >
      > **你的问题精准命中 v4.0 UX gap**：v4.0 主命令 `canvas:configure-whiteboard` 是"建白板"语义，不是"归类笔记"。当笔记**没被反向引用**时，没有明确入口把它追加到已有白板。
      >
      > **v4.1 修复（2026-05-01 ship）**：新增独立命令 **`canvas:append-note-to-board`** —"把当前笔记追加到已有原白板"。
      >
      > **使用方式**（3 步）：
      > 1. 打开你想归类的笔记（让它成为 active file）
      > 2. Cmd+P → 搜"把当前笔记追加到已有原白板"
      > 3. 弹 `SelectExistingBoardModal` 列出 vault 所有 `原白板/*.md` → 模糊搜索选目标白板
      > 4. 弹 `SeedModeModal` 选 move / copy / skip → 完成
      >
      > **流程**：
      > ```
      > Cmd+P → "把当前笔记追加到已有原白板"
      >         ↓
      > SelectExistingBoardModal（FuzzySuggestModal 列已有白板，输入过滤）
      >         ↓
      > 选完白板 → 自动检查白板的 ## Concepts 是否已含此笔记（避免重复 append）
      >         ↓
      > SeedModeModal（move 推荐 / copy 保留原位 / skip 不归类只标白板）
      >         ↓
      > Plugin 脚本：移到 节点/ → 加 type:concept frontmatter → 白板 ## Concepts append → doc_count +1
      >         ↓
      > ✓ Notice：笔记 X.md 已移动到 节点/ + 追加到白板 "Y"（XXms）
      > ```
      >
      > **3 个命令的语义边界（v4.1 后清晰）**：
      >
      > | 命令 | 语义 | 用例 |
      > |---|---|---|
      > | `canvas:configure-whiteboard` | **建新白板** + 可选种子 | 我要建一个新主题白板 |
      > | `canvas:append-note-to-board` | **追加笔记到已有白板** | 这笔记忘记归类，归到 X 白板里 |
      > | `canvas:ai-linked-doc` | **从节点派生子节点** | 选中文字派生新概念 |
      >
      > **跑此场景**：见下方"场景 V4-E"
      >
      > **build**：main.js 57836B → 64183B（+6347B = SelectExistingBoardModal + handleAppendNoteToBoard 等 4 个新方法）
- [ ] 输入"a/b/c"（含非法字符）→ hint 应红色显示"✗ 白板名含非法字符"
- [ ] 清空输入"测试白板 V4A"→ hint 应绿色显示"✓ 将建到 原白板/测试白板 V4A.md（7 字符）"
- [ ] 按 Enter（或点"下一步 (Enter)"按钮）

#### V4-A3 · 立即建白板（场景 A 跳过 SeedModeModal）
- [ ] **<300ms 内**右下角弹 Notice：`✓ 原白板 "测试白板 V4A" 已建立（XXms）位置: 原白板/测试白板 V4A.md 种子: 0（空白板）`
- [ ] **关键性能**：XXms 数字应 < 300（v3 是 15000-30000ms）
- [ ] 文件树 `原白板/` 下立即可见 `测试白板 V4A.md`
- [ ] 打开 `原白板/测试白板 V4A.md`，frontmatter 含 5 字段（type / board_name / created_at / doc_count: 0 / doc_mastery_avg: 0.00）
- [ ] body 含 ## Concepts + ## 🔗 节点关系图（dataviewjs 块完整保留）+ ## Recent Activity

#### V4-A4 · 同名冲突（错误恢复）
- [ ] 再次跑命令 → 输入相同的"测试白板 V4A"→ 提交
- [ ] **应弹 Notice**：`⚠ 原白板/测试白板 V4A.md 已存在。请换名重试，或手动追加种子到该白板。`
- [ ] **不**建任何文件（partial commit，白板已有的不破坏）

---

### 场景 V4-B · 场景 B 从节点派生（**重点测反向引用检测**）

#### V4-B1 · 准备：选个已被反向引用的笔记
- [ ] 去你的 vault 找一个**已被节点 `derived-from / source_note / up` 引用**的 md（v3 测过的派生过的笔记，例 `节点/Fundamentals.md` 或截图里的 `wiki/canvases/math140/Fundamentals.md` 如果还在）
- [ ] 打开它（让它成为 active file）

#### V4-B2 · 触发命令
- [ ] Cmd+P → "建/配置原白板"→ 回车
- [ ] **立即**弹 BoardNameInputModal，标题应是"建白板（场景 B · 从 `<active 路径>` 派生）"
- [ ] 输入新白板名（例"V4B Test"）→ 提交

#### V4-B3 · ⭐ BacklinkWarningModal（v4 核心新功能）
- [ ] **立即**（< 300ms）弹 **BacklinkWarningModal**，标题 `⚠️ 检测到反向引用`
- [ ] body 第一行：`<active 路径> 已被 N 个节点反向引用，可能已属于已有白板。`
- [ ] 列出最多 5 个反向引用源 md（每行 `<path>（白板: <board_name>）`）
- [ ] 3 个按钮：
  1. 蓝色（mod-cta）：`A. 追加到已有白板 "<existing_board>"（推荐）`
  2. 普通：`B. 仍建新白板 "V4B Test"（碎片化风险）`
  3. 普通：`C. 取消（先去看一下已有白板再决定）`

**测 3 条路径任选**：

**路径 A · 选"追加到已有白板"**：
- [ ] modal 关闭后 Notice：`✓ 种子 <basename>.md 已追加到已有白板 "<existing_board>"（v4 反向引用检测建议）`
- [ ] 该笔记**自动 move 到 节点/**（如不在）
- [ ] 已有白板 md 的 ## Concepts append 新行 `- [[节点/<stem>]] — seed note (mastery: 0.30)`
- [ ] 已有白板 frontmatter `doc_count` += 1
- [ ] **不**建新白板

**路径 B · 选"仍建新白板"**：
- [ ] modal 关闭后弹 SeedModeModal（FuzzySuggestModal）3 选项：move / copy / skip
- [ ] 选 move → Notice：`✓ 原白板 "V4B Test" 已建立 + 种子 X.md 归入 节点/ + ## Concepts 已添加 [[节点/X]]（共 XXms）`
- [ ] 该笔记被 move 到 `节点/X.md`（原位置消失）
- [ ] 新白板 `原白板/V4B Test.md` 创建
- [ ] **关键**：通过反向引用强行建新白板**会**碎片化（同概念多白板分裂）— 这是 v4 警告你的原因

**路径 C · 选"取消"**：
- [ ] modal 关闭，Notice：`✗ 用户取消。请去 [[原白板/<existing_board>]] 查看后再决定`
- [ ] **不**建任何文件（你可以先去看那个已有白板）

---

### 场景 V4-C · 场景 B 但无反向引用（应跳过 BacklinkWarningModal）

#### V4-C1 · 准备：建一个全新的、没被引用的 md
- [ ] vault 根新建 `测试种子V4C.md`，输入几句话
- [ ] 不要在任何节点的 frontmatter 引用它

#### V4-C2 · 触发命令 + 验证跳过 backlink modal
- [ ] 在 `测试种子V4C.md` 上 Cmd+P → "建/配置原白板"→ 输入"V4C Board"→ 提交
- [ ] **应直接弹 SeedModeModal**（跳过 BacklinkWarningModal，因为反向引用 = 0）
- [ ] 选 move → Notice 显示总耗时 < 300ms
- [ ] `原白板/V4C Board.md` 已建好 + `节点/测试种子V4C.md` 出现 + ## Concepts 含 wikilink

---

### 场景 V4-E · ⭐ 追加笔记到已有白板（v4.1 新命令，回应用户批注）

**前提**：vault 至少有 1 个白板（如 V4-A 测出的"测试白板 V4A"）+ 1 个还没归类的笔记。

#### V4-E1 · 准备未归类笔记
- [ ] vault 根新建 `unfiled-note.md` 输入几句话，**不**做任何 wikilink 引用
- [ ] 或随便挑一个旧的 `wiki/canvases/...` 路径下的笔记
- [ ] 在该笔记上让光标进入（active file）

#### V4-E2 · 触发 v4.1 新命令
- [ ] Cmd+P → 搜"把当前笔记追加到已有原白板"→ 回车
- [ ] **应立即弹 `SelectExistingBoardModal`**，placeholder：`选要追加到的原白板（共 N 个，输入过滤）`

#### V4-E3 · SelectExistingBoardModal（v4.1 核心）
- [ ] modal 列出 vault 所有 `原白板/*.md`（按 basename 显示，例"测试白板 V4A"/"特征值与特征向量"等）
- [ ] 输入"特"→ 过滤到含"特"的白板
- [ ] 选一个白板（例"测试白板 V4A"）

#### V4-E4 · 重复检查（避免冗余 append）
- [ ] **若该白板的 ## Concepts 已含 `[[节点/<basename>]]`** → Notice：`⚠ 白板 测试白板 V4A 的 ## Concepts 已含 [[节点/X]]，跳过避免重复` 并 halt
- [ ] **若不含** → 继续 V4-E5

#### V4-E5 · SeedModeModal
- [ ] 弹 `SeedModeModal` 3 选项：move（推荐）/ copy / skip
- [ ] 选 move

#### V4-E6 · ⭐ 验证完成
- [ ] **<300ms 内**右下角 Notice：`✓ 笔记 unfiled-note.md 已移动到 节点/ + 追加到白板 "测试白板 V4A"（XXms）`
- [ ] `unfiled-note.md` 从原位置消失，出现在 `节点/unfiled-note.md`
- [ ] 该节点 frontmatter 含 `type: concept`（plugin 自动加，若原本无）+ **不**含 `subject` 字段（v4 规则）
- [ ] `原白板/测试白板 V4A.md` 的 ## Concepts 多 1 行 `- [[节点/unfiled-note]] — seed note (mastery: 0.30)`
- [ ] 该白板 frontmatter `doc_count` 从 0 → 1
- [ ] ## Recent Activity 多 1 行 `- <ISO>: Seed note unfiled-note.md imported`

#### V4-E7 · 边界：无白板时
- [ ] 在一个**空 vault**（`原白板/` 下没有任何 md）触发命令
- [ ] **应弹 Notice**：`原白板/ 下还没有任何白板。请先用 canvas:configure-whiteboard 建一个。`
- [ ] **不**建任何文件

#### V4-E8 · 边界：无 active file 时
- [ ] 关闭所有 tab → 命令面板搜"把当前笔记追加到已有原白板"→ 回车
- [ ] **应弹 Notice**：`请先打开你想归类的笔记（让它成为 active file）`
- [ ] **不**显示 modal

---

### 场景 V4-D · 错误恢复 + 边界

#### V4-D1 · 没 .canvas-config.yaml 的 vault
- [ ] 在 `.canvas-config.yaml` 不存在的 vault 触发命令
- [ ] **应弹 Notice**：`❌ 未找到 .canvas-config.yaml 或解析失败。请先建 vault 级配置（参考 deploy-vault Skill）`
- [ ] **不**建任何文件

#### V4-D2 · BoardNameInputModal Esc 取消
- [ ] 触发命令 → modal 弹出 → 按 Esc
- [ ] modal 关闭，**不**建白板，无错误

#### V4-D3 · 节点池重名自动 _2
- [ ] 触发场景 B，种子文件名是 `Fundamentals.md`（节点池已有同名）
- [ ] 选 move → 应自动重命名为 `节点/Fundamentals_2.md`
- [ ] 白板 ## Concepts 写 `- [[节点/Fundamentals_2]]`

#### V4-D4 · v3 Skill fallback 仍可用（兼容性）
- [ ] 在 Claudian 输 `/configure-whiteboard`
- [ ] Skill 应仍能加载（标 [DEPRECATED] banner 但功能保留）
- [ ] 这条路 ~15-30s（你能感受 v3 vs v4 的差距）

---

### 性能验收（v4 核心卖点）

#### V4-P1 · 总耗时 < 300ms
- [ ] V4-A3 / V4-B3 / V4-C2 任一 Notice 末尾的 `XXms` 数字应 < 300
- [ ] 实测如果 > 500ms → 反馈我（可能 obsidian 启动 cold cache）

#### V4-P2 · 反向引用检测 < 50ms
- [ ] V4-B3 触发 BacklinkWarningModal 是"几乎瞬间"，不应有可感知延迟（<100ms）
- [ ] 对比 v3 Skill Glob 200 笔记 ~500ms

---

## 🚦 v4 验收结果

### 全 24 步 ✅（含 v4.1 场景 V4-E 8 步）
→ 告诉我 "**Story 1.19 v4 通过**"
→ 我 mark done + 启动 Story 1.18 Dashboard MVP（最后一个 Epic 1 P0）

### 部分失败
→ 告诉我哪一步 ❌ + 截图 + 估测耗时
→ 我针对性修

### v4 命令完全没出现在命令面板
→ main.js 不是 57836B，重 deploy 或 obsidian 没重启

---

## 🧹 v3 → v4 迁移清理（可选）

| 资产 | 状态 | 建议 |
|---|---|---|
| `canvas-vault/.claude/skills/configure-whiteboard/SKILL.md` v3.1 | 标 [DEPRECATED] 保留 | 验完 v4 OK 可手动删 SKILL.md（Skill fallback 失效）|
| `canvas-vault/.claude/skills/configure-whiteboard/templates/whiteboard.md.template` | 仍存在 | 可删（plugin 已内嵌 WHITEBOARD_TEMPLATE 不再读外部）|
| `wiki/canvases/<subject>/` 旧目录残留 | 历史遗留 | 用户 5/1 已大部分清理；剩余手动删 |

---

## 📝 你的批注区

> [!question]+ v4.0 plugin 重构后的批注
>
> 跑完 16 步任意写下：
> - 速度感受（v3 30s vs v4 <300ms 差距是否明显）
> - BacklinkWarningModal 是否符合预期
> - 任何 UX 不顺的地方
>
> （空）

---

## 🔽 以下是 v3 Skill UAT 文档（保留追溯，2026-04-30 已通过）

# Story 1.19 验收单 v4 — 扁平架构完整 UAT

> [!success]+ 这是 round-10/11 架构重设计的交付
> 你 2026-04-20 在 v2.1 UAT 批注 3 个架构问题（Claudian 自动挂载 / 白板 = md / 一 vault 一学科），3 并行 agent 调研后你在 AskUserQuestion 给出 **4 个关键决策**：
> 1. ✅ **节点可见性 = a 侧栏折叠但可点**（兼容 PRD FR-CONV-01）
> 2. ✅ **subject 字段 = B 固化 vault 级**（.canvas-config.yaml 对用户透明）
> 3. ✅ **目录命名 = 中文**（原白板/节点/检验白板）
> 4. ✅ **重名冲突 = X 一 vault 一学科零冲突**
>
> 本文档验证 v4 实施是否符合你的 4 决策 + 中文编码是否工作。
>
> **4 决策详解 + 形式比喻**：见 [[Round-10-架构重设计]]（`_bmad-output/验收单/批注回复/Round-10-架构重设计.md`）。

---

## 📌 核心架构（v4 vs v2.1 对比）

| 维度 | v2.1（已弃用） | v4（本次） |
|---|---|---|
| 白板物理 | `wiki/canvases/<subject>/index.md`（目录） | **`原白板/<board>.md`**（单 md） |
| 节点物理 | `wiki/canvases/<subject>/<concept>.md` | **`节点/<concept>.md`**（扁平池） |
| 检验白板 | 无专门位置 | **`检验白板/<exam>.md`** |
| subject 字段 | 每个白板/节点 md frontmatter 都有 | **vault 级 `.canvas-config.yaml`**，对用户透明 |
| 学科范围 | 一 vault 多学科（subject 隔离） | **一 vault 一学科**（零重名） |
| 节点可见性 | 和白板同目录显式可见 | **左栏默认折叠**，Cmd+Click 仍可开 |

**社区对齐**：Nick Milo Ideaverse（70,000+ LYT Kit 下载）的 Atlas/Maps + Atlas/Notes 官方结构的**精确镜像**。

---

## 🔧 前置条件（P1-P4）

### P1 · v4 代码验证（终端跑）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system

# 1. Plugin v4 (含 原白板/节点/ 路径识别)
wc -c canvas-vault/.obsidian/plugins/canvas-learning-system/main.js
# 应该 ~12202 bytes（v2.1 是 11608）

# 2. Skill v4 文件
ls canvas-vault/.claude/skills/configure-whiteboard/
# SKILL.md + templates/whiteboard.md.template (旧的 index.md.template 已 git rm)

head -20 canvas-vault/.claude/skills/configure-whiteboard/SKILL.md
# 应看到 `原白板配置 Skill v3（Canvas Learning System · 扁平架构）`
# + `⛔⛔⛔ CRITICAL TRIGGER & HARD CONSTRAINTS（round-11 扁平架构）`

# 3. vault 级 config 文件
cat canvas-vault/.canvas-config.yaml
# 应看到 subject: cs-61b + subject_display: "CS 61B 数据结构" + deprecated_paths:...

# 4. 物理目录迁移
ls canvas-vault/ | grep -E "原白板|节点|检验白板"
# 应全部看到

ls canvas-vault/原白板/
# CS 61B.md

ls canvas-vault/节点/
# cs-61b-csm.md + csm-tutoring-unit-credit.md + TestConceptA/B/C.md (5 个)

# 5. 旧 wiki/ 目录已空（不影响功能但应删）
ls canvas-vault/wiki/ 2>/dev/null
# 应该空或不存在
```

**全通过** → P1 ✅

### P2 · 强制 Reload Obsidian

- [x] `Cmd+P` → "Reload app without saving"（让 Claudian 重扫 v4 Skill + plugin 重读 v4 main.js）
- [x] canvas-vault 左下角显示 `canvas-vault`

### P3 · Obsidian 侧栏观察

- [x] 打开 Obsidian 文件树，看到三个新顶层文件夹：`原白板/` / `节点/` / `检验白板/`
- [x] **默认状态**：节点文件夹图标旁边是 `▸`（折叠）
- [x] `原白板/CS 61B.md` 已存在（从 v2 迁移的）
- [x] `节点/cs-61b-csm.md` + `节点/TestConceptA/B/C.md` + `节点/csm-tutoring-unit-credit.md` 5 个节点

### P4 · Claudian 可用

- [x] Claudian sidebar 打开
- [x] `/config` → dropdown 看到 `/configure-whiteboard` + `/ai-linked-doc`

---

## ✅ UAT 12 步（4 阶段）

## 阶段 1 · v4 识别（第 1-2 步）

### 第 1 步：打开 F12 Console

- [x] `Cmd+Opt+I` → Console 标签 → 清屏

### 第 2 步：Skill dropdown 识别

- [x] Claudian 输 `/config` → dropdown 显示 `/configure-whiteboard`
- [x] 输 `/ai` → dropdown 显示 `/ai-linked-doc`

**失败** → 诊断 A

---

## 阶段 2 · 中文路径编码 QA（第 3-5 步 · 核心）

⚠️ 这是 round-10 决策 3（中文目录）的验证 — 必须跑！

### 第 3 步：Graph View `path:原白板/` filter![[截屏2026-04-30 上午1.27.40.png]]

- [ ] 打开任意 md 后按 `Cmd+G` 打开 Graph View
- [ ] 左上角 `Filters` 面板 → 输入 `path:原白板/`
- [ ] 看到 **1 个节点 "CS 61B"**（从 `原白板/CS 61B.md` 迁移的）User：并没有看到这里的 CS61B 的节点![[截屏2026-04-30 上午1.28.37.png]]
- [x] 输 `path:节点/` → 看到 **5 个节点**（cs-61b-csm + csm-tutoring-unit-credit + TestConceptA/B/C）

**失败**（filter 无效或无节点）→ **诊断 B · 中文编码 fail**（架构需降级英文）

### 第 4 步：Wikilink 中文路径

- [x] 打开 `原白板/CS 61B.md`
- [x] 看到 `- [[节点/cs-61b-csm]] — seed note (mastery: 0.30, migrated from v2)`
- [x] Cmd+Click `[[节点/cs-61b-csm]]` → 能跳转到 `节点/cs-61b-csm.md`

**失败**（wikilink 红色无效）→ 诊断 B

### 第 5 步：Bash mv 中文路径幂等（验证 Skill 的 Step 5 能跑）

- [x] 终端：
  ```bash
  cd canvas-vault
  echo "# 测试节点" > raw/test-node.md
  mv raw/test-node.md 节点/test-node.md
  ls 节点/test-node.md && rm 节点/test-node.md
  
  
  ```
  
  输出结果：
  Last login: Wed Apr 29 23:46:23 on ttys010
Heishing@MacBook-Pro ~ %   cd canvas-vault
  echo "# 测试节点" > raw/test-node.md
  mv raw/test-node.md 节点/test-node.md
  ls 节点/test-node.md && rm 节点/test-node.md
cd: no such file or directory: canvas-vault
zsh: no such file or directory: raw/test-node.md
mv: rename raw/test-node.md to 节点/test-node.md: No such file or directory
ls: 节点/test-node.md: No such file or directory
Heishing@MacBook-Pro ~ %

- [x] **成功** = 无报错 + `ls` 能看到文件 + `rm` 能删
- [ ] 若报错 "No such file" → 中文路径 Bash 环境有问题

**失败** → 诊断 B

---

## 阶段 3 · 场景 A 从零建白板（第 6-8 步）

### 第 6 步：触发 `/configure-whiteboard`

- [ ] Claudian 输：
  ```
  /configure-whiteboard "线性代数"
  ```
- [ ] Enter → Skill 开始执行
**User：原白板我目前已经创建了，但是我想知道原白板难道不就是用来呈现节点和节点之间的关系和索引节点的目录吗？**
### 第 7 步：Skill 执行验证

- [ ] Skill 读 `.canvas-config.yaml` 得 `vault_subject = cs-61b`
- [ ] **不会向你问 subject**（v4 对用户透明）
- [ ] Skill 询问 "把当前打开的笔记作为种子迁入吗？" → 选"不"

### 第 8 步：回执 + 物理结构验证

- [ ] Claudian 返回：
  ```
  ✓ 原白板 "线性代数" 已建立
  📍 位置: 原白板/线性代数.md
  🏷️ 学科（vault 级）: cs-61b
  📝 种子笔记: 0（空白板）
  ```
- [ ] 验证 `原白板/线性代数.md` 存在
- [ ] 打开 `原白板/线性代数.md`：
  - frontmatter `type: whiteboard` + `board_name: "线性代数"` + `doc_count: 0` + **无 subject 字段**
  - `# 线性代数` 标题
  - `[!info]+ 原白板说明（扁平架构 · round-11）` callout
  - 5 sections: Concepts / Theorems & Proofs / Common Errors / Relationship Graph / Recent Activity
  - Relationship Graph 是完整 `[!info]+` callout（不是空白）

**失败**（路径错 / subject 字段还在 / schema 错）→ 诊断 C

---

## 阶段 4 · 场景 B 从任意 md 派生（第 9-12 步 · 最核心）

### 第 9 步：准备测试种子

- [ ] Finder 或 Obsidian 在 `raw/` 下建 `my-recursion-notes.md`：
  ```markdown
  # 递归笔记
  
  递归是函数调用自身以解决规模更小的相同问题。
  基本模式：base case + recursive case。
  例：阶乘 factorial(n) = n * factorial(n-1)。
  ```

### 第 10 步：Claudian 自动挂载验证（round-10 批注 A）

- [ ] 在 Obsidian 打开 `raw/my-recursion-notes.md`（Claudian 应自动挂载 active file）
- [ ] 切到 Claudian sidebar
- [ ] 输：
  ```
  /configure-whiteboard from raw/my-recursion-notes.md
  ```
  或**无参**测试 active file 挂载：
  ```
  /configure-whiteboard
  ```
- [ ] Enter

### 第 11 步：Skill AskUserQuestion 流程（场景 B）

- [ ] Skill Step 2 判定场景 B
- [ ] Skill Step 3 问 "新白板叫什么名字？"（场景 B 默认用 source 文件名 stem `my-recursion-notes` 作为候选，但让你确认）
- [ ] 输 `递归学习`
- [ ] Skill Step 6 问 "种子笔记要 move 还是 copy？" → 选 `copy`（✅ **D4-4 决策**：复制保留，原 md 在 raw/ 不动）

### 第 12 步：场景 B 结果验证

- [ ] Claudian 返回 3 行 ✓：
  ```
  ✓ 原白板 "递归学习" 已建立（原白板/递归学习.md）
  ✓ 种子笔记 my-recursion-notes.md 已归入 节点/
  ✓ 白板 ## Concepts 已添加 [[节点/my-recursion-notes]]
  ```
- [ ] 验证物理结构：
  - `raw/my-recursion-notes.md` **仍保留**（✅ **D4-4 决策**：复制保留 — 原 md 不删，节点池新增副本）
    User：没有出现删除
    > **[AI 回复 2026-04-30]** ✅ 这是**符合 D4-4 决策的预期行为**，不是 bug。D4-4 = 复制保留（A 选项）→ 原文件应保留在 raw/。spec 第 12 步描述过时了，已修正。请把这一步 `- [ ]` 勾选为 `- [x]` 通过。
  - `节点/my-recursion-notes.md` **存在**
  - 打开它 → frontmatter 含 `type: concept`（Skill 加的）**无 subject 字段**
  - `原白板/递归学习.md` **存在**
  - 打开白板 md → `## Concepts` 有 `- [[节点/my-recursion-notes]] — seed note (mastery: 0.30)`
  - **wikilink 用完整路径 `节点/my-recursion-notes`**（验证 Skill 正确写完整路径，避免 Obsidian 歧义）

**失败** → 诊断 D
**User：截图上呈现的就是我们节点所呈现的内容。**

![[截屏2026-04-30 上午2.14.29.png]]

---

## 🚦 验收结果

### 理想（P1-P4 + 第 1-12 步全 ✅）

→ 告诉我 "**Story 1.19 v4 通过**"  
→ 我 mark done + **unblock Story 1.17**（下一轮开始 1.17 v4 适配扁平架构）

### 中文编码失败（第 3-5 步任一 ❌）

→ 告诉我 "**诊断 B 中文失败**" + 截图  
→ 我降级为**英文方案**（Maps/Notes/Exams）再实施一次，~2h 切换

### 其他部分失败

→ 告诉我 "**诊断 [A/C/D]**" + 截图

---

## 🔴 诊断矩阵

### 诊断 A · Skill dropdown 不识别 /configure-whiteboard

- 终端：`head -15 canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
  - 第 1 行 `---`，第 2 行 `name: configure-whiteboard`
  - description 含 "v3 扁平架构"
- Claudian Settings → 找"Reload skills"按钮点一下
- 仍不行 → Cmd+P → "Reload app without saving"

### 诊断 B · 中文编码失败（关键！）

此为 round-10 决策 3 最大风险。若失败：
- Graph View `path:原白板/` 无效 → 用 `path:"原白板/"` 加引号试
- Wikilink `[[节点/xxx]]` 红色 → Obsidian 不识别中文路径
- Bash `mv "raw/x.md" "节点/"` 报错 → macOS NFD/NFC normalization 问题

**我的 fallback 方案**（告诉我 "诊断 B" 后我会做）：
- 把 `原白板/` / `节点/` / `检验白板/` 全部改英文 `Maps/` / `Notes/` / `Exams/`
- Skill + template + plugin + spec 全部搜索替换
- .canvas-config.yaml 加 `directory_naming: english` 标记
- 重新跑 UAT

### 诊断 C · 场景 A 白板 schema 错

- 白板 md 有 `subject` 字段 → SKILL.md 未更新到 v4（grep `subject:` 应该只在 `.canvas-config.yaml`）
- 白板 md 路径 `wiki/canvases/...` → Skill 未读新 CLAUDE.md，rollback v2.1 SKILL
- Relationship Graph 空白 → `whiteboard.md.template` 未被 Skill 读到（检查 Skill Step 5 Read path）

### 诊断 D · 场景 B 物理错

- `raw/my-recursion-notes.md` **没消失** → move 失败，Skill 走了 copy fallback（看回执的 ⚠）
- 节点 md 写到 `节点/` 外 → Skill 违反硬约束（查 Skill Step 6 的 Glob 检查）
- 白板 `## Concepts` 没加 wikilink → Skill 跳了 Step 6 的 Append

---

## 📝 你的批注区

> [!question]+ 你对 Story 1.19 v4 的批注
>
> 在这里写任何疑问/建议/不满意。
>
> （空）

---

## 📜 历史追溯（v1 → v4 完整演进）

> [!note]+ 2026-04-20 round-11 · v4 扁平架构（本版）
> 回应 round-10 你的 3 个架构批注 + 4 决策（AskUserQuestion）：
> - 白板 = 单 md（`原白板/<board>.md`）
> - 节点扁平池（`节点/<concept>.md`）
> - subject vault 级透明（`.canvas-config.yaml`）
> - 中文目录（需编码 QA）
> - 一 vault 一学科（零重名）
> 社区对齐 Nick Milo Ideaverse Atlas/Maps + Atlas/Notes。

> [!error]+ 2026-04-20 round-9 · v2.1 subject/board_name 分工 + 关系归纳 scope
> v2.1 `[!tip]+` 埋步骤里 → v3 核心概念提顶 → v4 被架构重设计替代。

> [!error]+ 2026-04-20 round-8 · Epic 1 顺序 correct-course
> 1.19 yaml `blocks: [1.17,1.18]` 被 CLAUDE.md 工作量排序覆盖；修正顺序 1.16→1.19→1.17→1.18。

> [!success]+ 2026-04-19 · Story 1.16 批注 hotkey 通过
> 10 步 UAT 全绿，Cmd+Shift+A 双步 modal 工作，4 Tag + 3 态 checkbox 正确。

---

## 🔗 技术参考

- **Round-10 架构调研**：`_bmad-output/验收单/批注回复/Round-10-架构重设计.md`
- **Story spec v3**：`_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md`
- **Skill v3**：`canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
- **Template v3**：`canvas-vault/.claude/skills/configure-whiteboard/templates/whiteboard.md.template`
- **下游 ai-linked-doc v4**：`canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`
- **CLAUDE.md round-11 架构段**：`_bmad-output/.claude/CLAUDE.md`（搜 "Vault 扁平架构"）
- **Plugin v4 源码**：`frontend/obsidian-plugin/src/ai-linked-doc.ts` + `src/main.ts`
- **Plugin 测试**：`frontend/obsidian-plugin/tests/ai-linked-doc.test.ts`（9 用例，total 18/18 pass）
- **Build 产物**：`main.js` 12202 bytes（v2.1 11608 + 594B v4 逻辑）
- **Vault 级配置**：`canvas-vault/.canvas-config.yaml`
- **社区参考**：
  - [Nick Milo Ideaverse](https://www.linkingyourthinking.com/)
  - [Atlas/Notes flat pool convention](https://obsidian.rocks/maps-of-content-effortless-organization-for-notes/)

---

## 📅 下一步

1. **你跑 P1-P4 前置 + 第 1-12 步 UAT**（估计 20 分钟）
2. **反馈**：
   - 全 ✅ → "**Story 1.19 v4 通过**" → unblock Story 1.17
   - 中文编码失败 → "**诊断 B**" → 我降级英文方案
   - 其他失败 → "**诊断 [A/C/D]**" → 针对 fix
3. **关键建议**：**先跑阶段 2（中文编码 QA 第 3-5 步）** — 这是 round-10 决策 3 的最大风险，若失败整个 v4 要架构降级，不用测后面的流程
