---
story: "3.1"
title: "节点 AI 对话 v1.0 · Cmd+Shift+C → Claudian 自动注入节点上下文"
status: "review"
version: "v1.0"
date: "2026-05-02"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
unblocked_by: "1.18 v1.2 已 done (2026-05-02) — 4 MVP 闭环达成"
route: "路线 A · 节点 AI 对话原型（推迟 1.2 wikilink-graph-build / 推迟 Tauri Web UI）"
---

# Story 3.1 验收单 v1.0 — 节点 AI 对话 · 路线 A 起步 ⭐

> [!success]+ 2026-05-02 v1.0 ship — Story 3.1 ready for review
> 4 MVP 闭环达成后路线 A 第 1 个 Story。完全复用 Story 1.17 v3.0 已验证的 **Hybrid 范式**（plugin clipboard write + Claudian invoke），plugin 仅做 deterministic 工作（context 收集 + prompt 组装 + 切 Claudian），LLM 由 Mode D Claudian session 承担。
>
> ## 主 ship
>
> | 资产 | 类型 | 大小 |
> |---|---|---|
> | `main.js`（canvas-vault deploy） | plugin build | 72731 → **83672B**（+10.7KB） |
> | `main.ts: handleOpenNodeChat()` | new method | ~140 行 |
> | `main.ts: collectNodeNeighbors()` | new method | ~32 行 |
> | `src/node-chat-context.ts` | new module | 230 行（纯函数） |
> | `tests/node-chat-context.test.ts` | new tests | 17 cases，全 green |
> | `canvas-vault/.claude/skills/node-chat/SKILL.md` | new skill | 110 行 |
>
> ## 顺手修复（2026-05-02 一并）
>
> - **main.ts:990 closure bug**：`fm.doc_count = recountBoardConcepts(updated)` 中 `updated` 在 const 声明前引用（TDZ ReferenceError 风险）→ reorder 到 `vault.modify(updated)` 之后

---

## 🎯 这个 Story 要做到什么

**一句话**：在节点 md 内按 `Cmd+Shift+C`，立刻和 Claude 围绕本节点对话（不需要重复说背景，AI 已经"知道"你在哪个节点）。

---

## 📖 你的视角

**作为** 学习者，
**我想** 在 `节点/<concept>.md` 节点页内按 `Cmd+Shift+C`，plugin 自动收集本节点完整学习背景（frontmatter / 正文 / 选中文 / 1-hop 邻居）写入剪贴板并切到 Claudian sidebar，
**以便** 我粘贴后立即和 AI 围绕这个节点连贯对话，不用反复粘贴上下文 / 切窗口 / 解释背景。

---

## 🖥️ 交互流程

```
打开 节点/Eigenvalues.md（或任意 节点/ 下的概念页）
        ↓
（可选）选中某段重点文字
        ↓
按 Cmd+Shift+C（用户在 Settings → Hotkeys 自绑命令"节点对话（注入上下文 + 切 Claudian）"）
        ↓
Plugin 弹 Notice："已复制节点 'Eigenvalues' 上下文（4.2KB / 5 邻居）到剪贴板\n切到 Claudian 粘贴即可触发对话"
+ Claudian sidebar 自动打开
        ↓
Cmd+V 粘贴到 Claudian 输入框
        ↓
Claudian 识别 /node-chat 加载 SKILL.md
        ↓
Claude 开场："✓ 已加载节点 [Eigenvalues] 上下文（4.2KB / 5 邻居）。
              📖 节点速览：特征值是线性代数核心概念，给定方阵 A 若 Av = λv 则 λ 是特征值。
              🔗 关键邻居：[[Linear-Independence]] (refines)、[[Determinant]] (depends_on)
              💬 可问方向：定义 / 关系 / 例子 / 自测题"
        ↓
（用户问"什么是特征值的几何意义？"→ Claude 用节点上下文 + 邻居关系作答）
```

---

## ✅ 验收清单（10 步 UAT，约 8 分钟）

> [!tip]+ 怎么用这份清单
> 每跑完一步，**点击 `- [ ]` 切换为 `[x]`**。发现不对劲 → **选中那行 → `Cmd+Shift+A` → ❌ 错误 + ❌ 不懂**，把问题批到这个文档。

### 第 0 步：前置（必须）

- [ ] **P0**：`Cmd+Q` 完全退出 Obsidian → 重开（加载新 main.js）
- [ ] **P1**：main.js 大小 = **83672B**（`stat -f "%z" canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`）
- [ ] **P2**：Settings → Community plugins → Canvas Learning System 已启用
- [ ] **P3**：Claudian 插件已装并登录 Claude Code（订阅生效）

### 第 1 步：注册命令验证

- [ ] `Cmd+P` 命令面板搜 "canvas" → 应见 12 条命令（多 1 条："节点对话（注入上下文 + 切 Claudian）"）
- [ ] Settings → Hotkeys 搜 "节点对话" → 应找到对应条目
- [ ] 给它绑 `Cmd+Shift+C`（建议；其他键也行）

### 第 2 步：节点路径检查（边界测试）

- [ ] 打开任意**非节点**文件（如 `Dashboard.md` 或 `原白板/CS 61B.md`）
- [ ] 按 Cmd+Shift+C → 应弹 Notice"对话仅在 节点/ 下的概念页可用（当前 path: ...）"
- [ ] **不应**写剪贴板 / **不应**切 Claudian

### 第 3 步：节点页基本对话（核心 happy path）

- [ ] 打开 `节点/Fundamentals.md`（或 vault 内任一节点）
- [ ] 按 Cmd+Shift+C
- [ ] 应见 Notice："已复制节点 'Fundamentals' 上下文（X.XKB / Y 邻居）到剪贴板"
- [ ] Claudian sidebar 自动打开

### 第 4 步：粘贴 + Skill 触发

- [ ] 在 Claudian 输入框按 `Cmd+V` 粘贴
- [ ] 看到一大段含 `/node-chat` 起头的 prompt（含"## 当前节点 / ## 节点正文 / ## 1-hop 邻居 / ## 任务"等 sections）
- [ ] 按 Enter 提交
- [ ] Claudian 加载 `node-chat` Skill（看到识别提示或直接开始回复）

### 第 5 步：开场白质量

- [ ] Claude 第一条回复应含：
  - [ ] "✓ 已加载节点 [<节点名>] 上下文（XKB / N 邻居）"
  - [ ] **节点速览**（一句概括）
  - [ ] **关键邻居**（列 1-3 个最相关的）
  - [ ] **可问方向**（4 类）

### 第 6 步：选中文重点关注（可选 path）

- [ ] 节点页内**选中某段**（如某个公式或定义）
- [ ] 按 Cmd+Shift+C
- [ ] 粘贴后查 prompt → 应有"## 选中文（重点关注）" section 含选中的文字
- [ ] Claude 开场白应特别提到"我注意到你选中了 ..."

### 第 7 步：AI 对话连贯性

- [ ] 问 Claude "什么是 [当前节点概念]的核心定义"
- [ ] Claude 应**优先用节点正文中的定义**作答（不重复要求你提供背景）
- [ ] 追问"和 [[<某邻居节点>]] 是什么关系" → Claude 应用 frontmatter relationships[] 或 1-hop 邻居信息答

### 第 8 步：纯对话约束（不会污染 vault）

- [ ] 整个对话过程，**不应**有任何文件被创建 / 修改（区别于 ai-linked-doc 派生流程）
- [ ] 检查 `节点/` 目录文件数 = 对话前数量
- [ ] 如果你说"帮我把这个写下来"→ Claude 应回"派生新概念请用 /ai-linked-doc，本对话不会动 vault 文件"

### 第 9 步：孤立节点 / 邻居为空

- [ ] 找一个**孤立节点**（没有 wikilink 进出的，可手动建一个测试节点）
- [ ] Cmd+Shift+C
- [ ] prompt 中"## 1-hop 邻居（0 个 ...)" + "（无关联节点 — 这是孤立概念）"
- [ ] 对话仍能正常启动（Claude 不抛错）

### 第 10 步：Claudian 未装边界

- [ ] （**仅在 Claudian 暂时禁用时测**）Settings → Community plugins → Disable Claudian
- [ ] Cmd+Shift+C
- [ ] Notice：写剪贴板成功 + "未检测到 Claudian 插件，请先安装并登录 Claude Code"
- [ ] 重新启用 Claudian

---

## 🚦 验收结果

### 全 10 步 ✅

→ 告诉我 "**Story 3.1 通过**"
→ 我 mark done + commit + 启动**路线 B Story 1.2 wikilink-graph-build**（NetworkX BFS 升级 1-hop 到 multi-hop，对话上下文质量再 ~5x）

### 部分失败

→ 告诉我哪步 ❌ + 截图（粘贴 prompt 给我看）
→ 针对性修

### Claudian 不识别 /node-chat

→ 检查 `canvas-vault/.claude/skills/node-chat/SKILL.md` 是否存在 + frontmatter 合法
→ Claudian 重启（卸载 + 重装 Skill 索引）

---

## 📝 你的批注区

> [!question]+ Story 3.1 v1.0 实测批注（2026-05-02 起）
>
> 跑完 10 步任意写下：
> - 上下文注入是否真"省心"（不用反复说背景）
> - 邻居摘要是否相关（5 个里有几个是真的相关）
> - Claude 开场白是否好用
> - 对话过程有没有 AI"不知道当前 vault 状态"的感觉
> - 选中文重点关注是否真的让 AI 聚焦
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）

---

## 🔗 技术 spec 参考

- **Story spec**：`_bmad-output/implementation-artifacts/epic-3/3-1-claude-code-cli-per-node-session.md`（v1.0 已 ship）
- **源代码**：
  - `frontend/obsidian-plugin/src/main.ts`（handleOpenNodeChat + collectNodeNeighbors + 第 12 命令注册 + line 990 closure bug 修复）
  - `frontend/obsidian-plugin/src/node-chat-context.ts`（纯函数模块：extractBodyWithoutFrontmatter / formatFrontmatterLines / buildNodeChatPrompt / byteLength / unicodeFirstN / isNodePath / extractFrontmatterType）
  - `canvas-vault/.claude/skills/node-chat/SKILL.md`（纯对话 Skill，allowed-tools 仅 Read/Glob/Grep）
- **单元测试**：`frontend/obsidian-plugin/tests/node-chat-context.test.ts`（17 cases / 121 total green）
- **AC → 代码对应**：
  - AC #1（plugin 12 命令）→ `main.ts:262-265`
  - AC #2（active file 检查）→ `main.ts:handleOpenNodeChat` 开头 if 链
  - AC #3（context 收集）→ `main.ts:collectNodeNeighbors` + `node-chat-context.ts:extractBodyWithoutFrontmatter / formatFrontmatterLines`
  - AC #4（prompt 组装 + 截断）→ `node-chat-context.ts:buildNodeChatPrompt`
  - AC #5（Claudian invoke）→ `main.ts:handleOpenNodeChat` 末段
  - AC #6（Skill 文件）→ `canvas-vault/.claude/skills/node-chat/SKILL.md`
  - AC #7（孤立节点）→ `node-chat-context.ts:formatNeighborLines` "（无关联节点 — 这是孤立概念）"
  - AC #8（端到端）→ UAT 第 3-7 步覆盖

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "通过" → mark done → 启动 **Story 1.2 wikilink-graph-build**（路线 B 升级 1-hop 到 multi-hop，~16-20h）
2. **部分 ❌** → 在批注区写清楚 + 截图，Claude 跑 `bmad-bmm-correct-course` 修
3. **想换路线** → 告诉 Claude "切到路线 C Tauri Web UI"或其他方向

---

## 🧭 4 MVP + 路线 A 闭环全景

```
Story 1.16 批注 hotkey ✅
Story 1.17 AI 双链 ✅  ─┐
Story 1.18 Dashboard ✅ ─┼─→ 4 MVP 闭环达成 (2026-05-02)
Story 1.19 配置白板 ✅  ─┘                    ↓
                                            Story 3.1 节点对话 ⏳ ← (本 Story)
                                                            ↓
                                            Story 1.2 wikilink graph (路线 B 启动)
                                                            ↓
                                            Story 1.3 + 多 Epic 3 子 Story
```
