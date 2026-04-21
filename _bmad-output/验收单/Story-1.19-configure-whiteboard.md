---
story: "1.19"
title: "原白板配置 Skill · v4 扁平架构（对齐 Nick Milo Ideaverse）"
status: "review"
version: "v4"
date: "2026-04-20"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
prev_uat_sheet: "v3 已覆盖；v1/v2/v2.1/v3 历史见本文底部"
---

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

- [ ] `Cmd+P` → "Reload app without saving"（让 Claudian 重扫 v4 Skill + plugin 重读 v4 main.js）
- [ ] canvas-vault 左下角显示 `canvas-vault`

### P3 · Obsidian 侧栏观察

- [ ] 打开 Obsidian 文件树，看到三个新顶层文件夹：`原白板/` / `节点/` / `检验白板/`
- [ ] **默认状态**：节点文件夹图标旁边是 `▸`（折叠）
- [ ] `原白板/CS 61B.md` 已存在（从 v2 迁移的）
- [ ] `节点/cs-61b-csm.md` + `节点/TestConceptA/B/C.md` + `节点/csm-tutoring-unit-credit.md` 5 个节点

### P4 · Claudian 可用

- [ ] Claudian sidebar 打开
- [ ] `/config` → dropdown 看到 `/configure-whiteboard` + `/ai-linked-doc`

---

## ✅ UAT 12 步（4 阶段）

## 阶段 1 · v4 识别（第 1-2 步）

### 第 1 步：打开 F12 Console

- [ ] `Cmd+Opt+I` → Console 标签 → 清屏

### 第 2 步：Skill dropdown 识别

- [ ] Claudian 输 `/config` → dropdown 显示 `/configure-whiteboard`
- [ ] 输 `/ai` → dropdown 显示 `/ai-linked-doc`

**失败** → 诊断 A

---

## 阶段 2 · 中文路径编码 QA（第 3-5 步 · 核心）

⚠️ 这是 round-10 决策 3（中文目录）的验证 — 必须跑！

### 第 3 步：Graph View `path:原白板/` filter

- [ ] 打开任意 md 后按 `Cmd+G` 打开 Graph View
- [ ] 左上角 `Filters` 面板 → 输入 `path:原白板/`
- [ ] 看到 **1 个节点 "CS 61B"**（从 `原白板/CS 61B.md` 迁移的）
- [ ] 输 `path:节点/` → 看到 **5 个节点**（cs-61b-csm + csm-tutoring-unit-credit + TestConceptA/B/C）

**失败**（filter 无效或无节点）→ **诊断 B · 中文编码 fail**（架构需降级英文）

### 第 4 步：Wikilink 中文路径

- [ ] 打开 `原白板/CS 61B.md`
- [ ] 看到 `- [[节点/cs-61b-csm]] — seed note (mastery: 0.30, migrated from v2)`
- [ ] Cmd+Click `[[节点/cs-61b-csm]]` → 能跳转到 `节点/cs-61b-csm.md`

**失败**（wikilink 红色无效）→ 诊断 B

### 第 5 步：Bash mv 中文路径幂等（验证 Skill 的 Step 5 能跑）

- [ ] 终端：
  ```bash
  cd canvas-vault
  echo "# 测试节点" > raw/test-node.md
  mv raw/test-node.md 节点/test-node.md
  ls 节点/test-node.md && rm 节点/test-node.md
  ```
- [ ] **成功** = 无报错 + `ls` 能看到文件 + `rm` 能删
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
- [ ] Skill Step 6 问 "种子笔记要 move 还是 copy？" → 选 `move`

### 第 12 步：场景 B 结果验证

- [ ] Claudian 返回 3 行 ✓：
  ```
  ✓ 原白板 "递归学习" 已建立（原白板/递归学习.md）
  ✓ 种子笔记 my-recursion-notes.md 已归入 节点/
  ✓ 白板 ## Concepts 已添加 [[节点/my-recursion-notes]]
  ```
- [ ] 验证物理结构：
  - `raw/my-recursion-notes.md` **已消失**（move 删源）
  - `节点/my-recursion-notes.md` **存在**
  - 打开它 → frontmatter 含 `type: concept`（Skill 加的）**无 subject 字段**
  - `原白板/递归学习.md` **存在**
  - 打开白板 md → `## Concepts` 有 `- [[节点/my-recursion-notes]] — seed note (mastery: 0.30)`
  - **wikilink 用完整路径 `节点/my-recursion-notes`**（验证 Skill 正确写完整路径，避免 Obsidian 歧义）

**失败** → 诊断 D

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
