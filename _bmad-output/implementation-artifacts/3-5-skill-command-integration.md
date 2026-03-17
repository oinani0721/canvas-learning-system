# Story 3.5: /命令技能集成

Status: ready-for-dev

## Story

As a 用户,
I want 在对话框输入 `/` 时看到可用的学习技能列表（基础拆解、深度拆解等 11 个），选择后 Claude Code 原生执行,
so that 我能在对话中快速调用专业学习工具。

## Acceptance Criteria

1. **AC-1: / 命令触发技能列表**
   - **Given** 用户在对话输入框中
   - **When** 输入 `/` 字符
   - **Then** 弹出 SkillSelector 浮动面板，显示已注册技能列表
   - **And** 支持模糊搜索（输入 `/拆` 过滤到"基础拆解""深度拆解"）
   - **And** 每个技能显示名称 + 简短描述

2. **AC-2: 技能透传 Claude Code 原生处理**
   - **Given** 用户选择了一个技能（如"基础拆解"）
   - **When** 技能发送到 Claude Code
   - **Then** 透传 `/skill-name 参数` 给 Claude Code 原生 /command 系统
   - **And** Claude Code 加载 `.claude/commands/skill.md` → 读取 `.claude/agents/agent.md`（如存在） → 执行
   - **And** 技能执行结果显示在对话流中（与普通消息一样流式渲染）

3. **AC-3: 11 个预装学习技能**
   - **Given** 插件安装完成
   - **When** 用户首次输入 `/`
   - **Then** 11 个预装学习辅助技能开箱可用
   - **And** 技能覆盖：基础拆解、深度拆解、四级解释、概念对比、记忆锚点、变式练习、错题重访、关系追问、知识检验、学习计划、总结回顾
   - **And** 每个技能有对应的 `.claude/commands/{skill-name}.md` prompt 模板文件

4. **AC-4: 用户自定义技能**
   - **Given** 用户想添加新技能
   - **When** 在 `.claude/commands/` 目录添加新的 `.md` 文件
   - **Then** 下次输入 `/` 时新技能出现在列表中
   - **And** 无需重启插件（文件系统监听或每次触发时重新扫描）

5. **AC-5: 技能执行上下文注入**
   - **Given** 用户在节点 A 的对话中执行技能
   - **When** 技能命令发送给 Claude Code
   - **Then** 该节点的学习历史上下文通过 `--append-system-prompt` 注入（复用 Story 3.4）
   - **And** 技能执行结果个性化（基于用户的 Tips/错误/精通度）

6. **AC-6: 技能结果可拉出**
   - **Given** 技能执行完成，结果显示在对话中
   - **When** 用户选中技能结果文字
   - **Then** 可被选中拉出为白板节点（复用 Story 3.7 的拖拽机制）

## Tasks / Subtasks

- [ ] **Task 1: SkillSelector UI 组件** (AC: #1)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/components/chat/SkillSelector.svelte`
  - [ ] 1.2 浮动面板定位：InputBar 上方弹出，遮罩外点击关闭
  - [ ] 1.3 技能列表渲染：图标 + 名称 + 描述，支持键盘上下导航 + Enter 选择
  - [ ] 1.4 模糊搜索：根据输入的 `/xxx` 中 `xxx` 部分过滤技能名称和描述
  - [ ] 1.5 CSS 类名 `.cl-chat-skill-selector`，适配 Light/Dark 主题

- [ ] **Task 2: 技能注册表** (AC: #1, #4)
  - [ ] 2.1 创建 `obsidian-canvas-learning/src/services/skill-registry.ts`
  - [ ] 2.2 实现 `loadSkills()`: 扫描 `.claude/commands/` 目录获取所有 `.md` 文件
  - [ ] 2.3 解析每个 `.md` 文件的 frontmatter（name, description, icon）
  - [ ] 2.4 返回 `Skill[]` 列表供 SkillSelector 消费
  - [ ] 2.5 支持动态刷新（用户添加新文件后调用 `loadSkills()` 重新扫描）

- [ ] **Task 3: 技能命令透传** (AC: #2, #5)
  - [ ] 3.1 扩展 `chat-state.svelte.ts`：添加 `executeSkill(skillName, args)` 方法
  - [ ] 3.2 将 `/skill-name args` 作为消息内容发送给 ClaudeCodeEngine
  - [ ] 3.3 Claude Code 原生识别 `/command` 格式并加载对应 `.claude/commands/skill.md`
  - [ ] 3.4 技能执行结果通过 StreamEvent 流式返回，复用 ChatPanel 渲染

- [ ] **Task 4: 11 个预装技能 Prompt 模板** (AC: #3)
  - [ ] 4.1 创建 `.claude/commands/` 目录（项目根目录）
  - [ ] 4.2 编写 11 个技能 prompt 模板文件：
    - `basic-decompose.md` — 基础拆解：将复杂概念分解为可理解的子概念
    - `deep-decompose.md` — 深度拆解：递归分解到原子级知识点
    - `four-level-explain.md` — 四级解释：5岁/高中/大学/专家四个层次解释
    - `concept-compare.md` — 概念对比：对比两个容易混淆的概念
    - `memory-anchor.md` — 记忆锚点：为概念创建记忆术/类比/助记
    - `variation-practice.md` — 变式练习：生成同一知识点的不同变体练习
    - `error-revisit.md` — 错题重访：基于历史错误精准复习
    - `relation-probe.md` — 关系追问：深入探讨两个概念的关联
    - `knowledge-check.md` — 知识检验：快速检测对概念的理解程度
    - `study-plan.md` — 学习计划：基于精通度制定复习计划
    - `summary-review.md` — 总结回顾：概括当前对话的学习收获
  - [ ] 4.3 每个模板包含 frontmatter（name, description, icon）+ prompt 内容
  - [ ] 4.4 prompt 中引用 `$ARGUMENTS` 变量接收用户附加参数

- [ ] **Task 5: InputBar 集成 SkillSelector** (AC: #1, #2)
  - [ ] 5.1 扩展 `InputBar.svelte`（Story 3.3）：监听 `/` 字符输入
  - [ ] 5.2 `/` 触发时显示 SkillSelector 组件
  - [ ] 5.3 用户选择技能后：替换输入框内容为 `/skill-name ` 并保持焦点
  - [ ] 5.4 用户按 Enter 发送技能命令

## Dev Notes

### Claude Code /command 系统

Claude Code 原生支持 `/command` 系统：
- `.claude/commands/xxx.md` 文件定义技能 prompt
- 用户在对话中输入 `/xxx` 触发
- Claude Code 加载 prompt → 可选读取 `.claude/agents/agent.md` → 执行

本 Story 利用此原生机制，前端只做 UI 层面的技能列表展示和命令透传。

### 技能 Prompt 模板格式

```markdown
---
name: 基础拆解
description: 将复杂概念分解为可理解的子概念
icon: puzzle
---

请将以下概念进行基础拆解，分解为3-5个可理解的子概念：

$ARGUMENTS

要求：
1. 每个子概念用一句话解释
2. 标注子概念之间的关系
3. 基于学生当前的学习上下文个性化解释
```

### 模糊搜索实现

```typescript
function fuzzyMatch(query: string, text: string): boolean {
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  let qi = 0;
  for (let ti = 0; ti < t.length && qi < q.length; ti++) {
    if (t[ti] === q[qi]) qi++;
  }
  return qi === q.length;
}
```

### 关键约束

1. **原生 /command 透传**：不在前端重新实现技能执行逻辑，完全依赖 Claude Code 原生处理
2. **目录扫描**：`.claude/commands/` 在项目根目录（非 Obsidian vault 内）
3. **用户自定义**：直接添加 `.md` 文件即可，无需注册
4. **上下文注入**：复用 Story 3.4 的 `--append-system-prompt`，技能执行也带学习历史
5. **流式渲染**：技能结果与普通对话消息一样走 StreamEvent → ChatPanel 管道

### 不做的事项（防蔓延）

- 不实现技能执行状态 UI（"正在执行基础拆解..."）—— 与普通消息等待一致
- 不实现技能参数表单 UI —— 用户在 `/skill-name` 后直接输入参数
- 不实现技能执行历史/收藏
- 不实现 .claude/agents/ 的 Agent 定义文件创建（Claude Code 原生功能）
- 不实现技能市场/共享

### Project Structure Notes

- 前端新建：`obsidian-canvas-learning/src/components/chat/SkillSelector.svelte`
- 前端新建：`obsidian-canvas-learning/src/services/skill-registry.ts`
- 项目根目录新建：`.claude/commands/` 目录下 11 个 `.md` 文件
- 扩展：`InputBar.svelte`（Story 3.3）添加 `/` 触发
- 扩展：`chat-state.svelte.ts` 添加 `executeSkill` 方法

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.5] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] — 命令技能系统 5 FR
- [Source: _decisions/ADR-001-dialogue-engine.md] — /命令直接复用 Claude Code 原生 /skill 系统

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
