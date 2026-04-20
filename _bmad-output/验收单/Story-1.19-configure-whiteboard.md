---
story: "1.19"
title: "原白板配置 Skill（场景 A 从零建 + 场景 B 从任意 md 派生）"
status: "review"
version: "v2"
date: "2026-04-20"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

# Story 1.19 验收单 — 原白板配置 Skill

> [!info]+ 这是什么
> 这是 Story 1.19 的用户验收文档。Story 1.19 是"**用户打开 Canvas 第一件事**" — 创建第一个原白板。之前 Story 1.17 UAT 卡住就是因为没有这个入口。
> 
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md`（Claude 读的）。

---

## 🎯 这个 Story 要做到什么

通过 **Claudian Skill `/configure-whiteboard`**，你可以：
- **场景 A**：从零建一个全新的学习主题原白板（例："Linear Algebra" + `math240`）
- **场景 B**：把你任意文件夹的现有 md 笔记**一键派生成一个新原白板**（回应你 2026-04-20 的"我现在有一个在任意文件夹的 md 文件那么我想要从这个文件开始生成原白板"诉求）

Skill 自动做 4 件事：
1. 建文件夹 `wiki/canvases/<subject>/`
2. 生成 `index.md`（含 frontmatter + Concepts/Theorems/Errors/Relationship/RecentActivity 5 段结构）
3. 把你的种子笔记 move（或 copy）到白板目录
4. 更新种子笔记 frontmatter + index.md wikilink 列表

---

## 📖 两种交互流程

### 场景 A · 从零建（你有学习主题想法但没笔记）

```
你在 Claudian 输: /configure-whiteboard "Linear Algebra" "math240"
        ↓
Skill Step 1-3: 解析参数 + 验证 subject 合法性
        ↓
Step 4: mkdir wiki/canvases/math240/ + 生成 index.md
        ↓
Step 5: 询问 "把当前打开的笔记作为种子迁入吗？"
        → 不 → 跳过 Step 5-6
        → 是 + 按 Step 5-6 流程
        ↓
Step 7: 返回 "✓ 原白板 Linear Algebra 已建立"
```

### 场景 B · 从任意 md 派生（你已有笔记想变成白板，2026-04-20 新增）

```
你有一个 wiki/raw/my-notes.md 或 vault 根的 未命名.md
        ↓
你在 Claudian 输: /configure-whiteboard from wiki/raw/my-notes.md
        或 /configure-whiteboard（如果笔记已 active）
        ↓
Skill Step 1: 识别场景 B (含 from <path> 或 active note 不在 canvases/)
        ↓
Step 2: AskUserQuestion "归属哪个学科？"
        → 列出已有 subject（math240, cs-61b, ...）+ "新建" 选项
        → 读源 md 的 subject frontmatter 预填（如有）
        ↓
Step 3: 检查 wiki/canvases/<subject>/ 是否已存在（已存在 → 问"重用/换代码"）
        ↓
Step 4: mkdir + 生成 index.md
        ↓
Step 5: AskUserQuestion "move（推荐）还是 copy？" → 执行
        ↓
Step 6: 更新种子笔记 frontmatter subject + index.md ## Concepts 加 wikilink
        ↓
Step 7: 返回 "✓ 白板已从 my-notes.md 派生，种子笔记已归入"
```

---

## 🔧 前置条件

### P1 · 环境验证

- [ ] canvas-vault 的 Claudian 已启用 + CLI path 填对（Story 1.17 P1 完成后这里就 OK）
- [ ] 终端 `ls canvas-vault/.claude/skills/configure-whiteboard/SKILL.md` 存在
- [ ] 终端 `ls canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template` 存在

### P2 · 强制 Reload Obsidian

- [ ] `Cmd+P` → "Reload app without saving"（让 Claudian 重新扫描 Skills）

---

## ✅ UAT（10 步 — 场景 A + B 双路径）

### 第 1 步：F12 DevTools Console（用于诊断，可选）

- [ ] `Cmd+Opt+I` 打开 Console

### 第 2 步：Claudian slash 补全验证

- [ ] 打开 Claudian 侧栏
- [ ] 在输入框输 `/config`
- [ ] Slash dropdown 里应**看到 `/configure-whiteboard`**（如没有 → Skill 文件没被扫到，转诊断 A）

### 第 3 步：场景 A 测试（从零建）

- [ ] 在 Claudian 输入：
  ```
  /configure-whiteboard "Linear Algebra" "math240"
  ```
- [ ] 按 Enter
- [ ] Claudian 开始执行 Skill（约 5-20s）

### 第 4 步：场景 A · Skill 询问"种子笔记"

- [ ] Claude 应该 AskUserQuestion 问："把当前打开的笔记作为种子迁入吗？"
- [ ] 若你没打开任何笔记或选"不"→ 跳过迁入，只建空白板
- [ ] 若选"是" → Skill 进入 Step 5-6 流程

### 第 5 步：场景 A · 验证回执 + 结构

- [ ] Claudian 最终返回回执，含 `✓ 原白板 "Linear Algebra" 已建立`
- [ ] Obsidian 左侧文件树刷新看到 `wiki/canvases/math240/` 文件夹
- [ ] 里面有 `index.md`
- [ ] 打开 `index.md` 看到：
  - frontmatter 含 `type: whiteboard_index` / `board_name: "Linear Algebra"` / `subject: "math240"` / `doc_count: 0` / `doc_mastery_avg: 0.00`
  - `# Linear Algebra` 标题
  - 5 个 section：`## Concepts` / `## Theorems & Proofs` / `## Common Errors` / `## Relationship Graph` / `## Recent Activity`
  - Recent Activity 段有 1 条 "Whiteboard created" 记录

### 第 6 步：场景 B 测试（从任意 md 派生）

- [ ] 在 canvas-vault 任意位置（例 `wiki/raw/`）建测试文件 `my-recursion-notes.md`：
  ```markdown
  # 递归笔记
  
  递归是函数调用自身以解决规模更小的相同问题。
  
  基本模式：base case（边界）+ recursive case（自调用）。
  ```
- [ ] 在 Claudian 输：
  ```
  /configure-whiteboard from wiki/raw/my-recursion-notes.md
  ```
- [ ] 按 Enter

### 第 7 步：场景 B · Skill AskUserQuestion 流程

- [ ] Claudian 问 "归属哪个学科？"
- [ ] 选项列出已有的 `math240`（第 3-5 步建的）+ "新建"
- [ ] 选"新建" → 再问 subject 代码 → 输 `cs-61b` → 再问 board_name → 输 `CS 61B 数据结构`
- [ ] Claudian 问 "move 还是 copy？" → 选 move
- [ ] Skill 开始执行

### 第 8 步：场景 B · 验证派生结果

- [ ] Claudian 返回 3 行 ✓：
  ```
  ✓ 原白板 "CS 61B 数据结构" 已建立
  ✓ 种子笔记 my-recursion-notes.md 已归入 wiki/canvases/cs-61b/
  ✓ index.md 的 Concepts section 已添加 [[my-recursion-notes]]
  ```
- [ ] 验证：
  - `wiki/raw/my-recursion-notes.md` **已消失**（move 删了原文件）
  - `wiki/canvases/cs-61b/my-recursion-notes.md` **存在**
  - 打开它 → frontmatter 有 `subject: "cs-61b"`（Skill 加的）
  - `wiki/canvases/cs-61b/index.md` 的 `## Concepts` section 有 `- [[my-recursion-notes]] — seed note (mastery: 0.30)`

### 第 9 步：验证已有白板场景（copy 测试）

- [ ] 再建一个测试文件 `wiki/raw/test-copy.md`（写几句话）
- [ ] 在 Claudian 输 `/configure-whiteboard from wiki/raw/test-copy.md`
- [ ] 归属选已有的 `math240`（不是新建）
- [ ] move vs copy 选 **copy**
- [ ] 验证：
  - `wiki/raw/test-copy.md` **仍然存在**（copy 保留原文件）
  - `wiki/canvases/math240/test-copy.md` 也存在
  - `wiki/canvases/math240/index.md` 的 `doc_count` 字段从 0 增加到 1（若 Skill 有实现），且 Concepts section 加了 `[[test-copy]]`

### 第 10 步：边界 — 冲突重试

- [ ] 重新输 `/configure-whiteboard "Linear Algebra" "math240"`（重名）
- [ ] Skill AskUserQuestion 问 "重用还是换代码？"
- [ ] 选"换代码" → 输新代码 → 确认建新白板

---

## 🚦 验收结果

### 理想（全 10 步 ✅）
→ 告诉我 "**Story 1.19 通过**"  
→ 我 mark done → 然后**自动回到 Story 1.17 UAT**（前置条件终于成立了）

### 部分失败
→ 告诉我哪步 ❌ + 截图  
→ 我 `bmad-bmm-correct-course` 到 v2.1

### 诊断 A · Skill 不在 Slash dropdown
- 验证文件：`head -15 canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
- 必须首行 `---` + `name: configure-whiteboard` + `description` 合法 YAML
- Reload Obsidian（Cmd+P → "Reload app"）让 Claudian 重扫

### 诊断 B · Skill 触发但不走 6 步流程
- 同 Story 1.17 的 Claudian 自由发挥问题
- 检查 SKILL.md 开头的 CRITICAL TRIGGER 是否完整
- 降级：在 Claudian 里明说 "请调用 configure-whiteboard Skill 严格按 Step 1-7 处理"

---

## 📝 你的批注区

> [!question]+ 你对 Story 1.19 的批注
>
> 在这里写任何疑问/建议/不满意。
>
> （空）

### 这个 Story 解决了什么历史问题

> [!error]+ 2026-04-20 — 用户 UAT Story 1.17 批注暴露 onboarding 入口缺失
> **你的批注**：
> 1. "双链提问节点的功能本身就是要在原白板里面使用的"
> 2. "我现在有一个在任意文件夹的 md 文件那么我想要从这个文件开始生成原白板，请问我该如何操作？"
>
> **根因**：Story 1.19 yaml 早就声明 `blocks: ["1.17","1.18"]`（数据层规定 1.19 先做），但 Claude 之前在 CLAUDE.md 按工作量排序成 `1.16→1.17→1.18→3.X` 覆盖了依赖。用户 Story 1.17 UAT 时没有白板可用 → 只能手动 mkdir + 建笔记，体验割裂。
>
> **已修复**：
> - 顺序修正 `1.16 → 1.19 → 1.17 → 1.18`
> - Story 1.19 scope 从 v1 的"场景 A"扩展为 v2 的"场景 A + 场景 B"（6h → 8h），回应"任意文件夹 md 派生"诉求
> - Story 1.17 暂 blocked，等 1.19 done 后回头测

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-1/1-19-configure-whiteboard-skill.md`（v2 2026-04-20）
- **Skill**：`canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`
- **Template**：`canvas-vault/.claude/skills/configure-whiteboard/templates/index.md.template`
- **3 并行 Agent 调研报告**：2026-04-20 round-8（story 依赖链 + 原白板定义 + 用户旅程）
- **Commit**：
  - `b660445`：round-8 顺序 correct-course + 1.17 blocked + 1.19 scope v2 扩展
  - 本次 commit：Skill + template 实施

---

## 📅 下一步（你批完这份单后）

1. **全 ✅** → 说 "Story 1.19 通过" → 我 mark 1.19 done → 自动启动 1.17 UAT（本身代码不变，只是前置成立了）
2. **部分 ❌** → 批注 → 我 correct-course 到 v2.1
3. **建议 UAT 顺序**：
   - 先跑场景 A 建个小白板看看整体流程
   - 再跑场景 B 从任意 md 派生（这是你最初 2026-04-20 的诉求）
   - 最后测边界（冲突 / move vs copy）
