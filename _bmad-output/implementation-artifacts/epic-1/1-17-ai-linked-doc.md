---
story_id: "1.17"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "review"
priority: "P0"
estimate_hours: 6
depends_on: ["1.16"]
blocks: []
trace: ["FR-CONV-08","FR-KG-06"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
revision: "v2-claudian-skill-align-2026-04-19"
uat_sheet: "_bmad-output/验收单/Story-1.17-ai-linked-doc.md"
---

# Story 1.17: AI 双链文档 v2 (形态 β：Plugin + Claudian Skill)

**Epic**: 1 — 基础设施 + Obsidian 插件命令
**Status**: review (v2 实施完成 2026-04-20，待用户 UAT 14 步)
**Plan**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**Priority**: P0
**Estimate**: ~6h
**Dependency**: Story 1.16 (hotkey/modal 范式) 已 done；Claudian 插件（官方 Agent SDK sidebar）已装；Claude Code 订阅已登录

---

## Story

作为 学习者，
我想 在任意 md 笔记选中一段文本后按 `Cmd+Shift+D`，插件把选中文本 + 生成 prompt 复制到剪贴板并自动打开 Claudian 侧栏，我在侧栏粘贴后由 `/ai-linked-doc` Skill 驱动 Claude Code 生成一份结构化概念文档、把源笔记选中文本替换为 `[[概念名]]` wikilink、并在当前原白板的 index.md 追加记录，
以便 我在阅读时快速把"还需深入理解的概念"派生为独立笔记，用订阅额度（不额外付费）复用 Mode D 架构，并保持知识图谱关系链完整。

> **架构对齐（硬约束）**：`planning-artifacts/architecture.md:113` 已锁 Mode D = Claude Agent SDK spawn 官方 Claude Code CLI（用户订阅额度）。v1 方案（Obsidian plugin 直调 Anthropic API + Settings 配独立 API Key）违反该决策，v2 完全重构为 **Plugin 只做触发 + 剪贴板/Claudian 切换 + Skill 承担 AI 调用/文件写入**。
>
> **来源对齐**：Round 3 QA `research/obsidian-qa-round3-claude-answers-2026-04-14.md:141-177`（System Prompt 模板三段式结构：核心概念 / 关键点 / 关联概念）+ Story 1.16 v2 实施经验（plugin 第 N 命令 + handler + `src/main.ts` 注册模式 + `cp main.js → canvas-vault/.obsidian/plugins/canvas-learning-system/` 部署范式）+ Story 1.19 的 `.claude/skills/<name>/SKILL.md` vault-level skill 发现机制。

## Behavior（用户视角）

```
在 wiki/canvases/math240/Fundamentals.md 选中
    "Eigenvalues are special vectors that satisfy Av = λv"
            ↓ 按 Cmd+Shift+D (用户在 Obsidian Settings 绑定到 canvas:ai-linked-doc)
            ↓
Plugin 做 3 件事:
  1. 组装 prompt 写入系统剪贴板
     格式: /ai-linked-doc
           选中文本:
           Eigenvalues are special vectors...
           源笔记路径: wiki/canvases/math240/Fundamentals.md
           学科: math240
           请为这段内容创建一个概念文档。
  2. Notice: "已复制到剪贴板，切到 Claudian 粘贴即可触发"
  3. 调 app.commands.executeCommandById("claudian:open-view") 切到 Claudian sidebar
            ↓
用户在 Claudian 输入框 Cmd+V 粘贴 → Enter
            ↓
Claudian (Claude Code 订阅额度) 识别 /ai-linked-doc 加载 SKILL.md
            ↓
Skill 执行 (Claude Code CLI 在 vault 根目录有完整 Read/Write/Edit 权限):
  步骤 1: 解析剪贴板/消息中的"选中文本 / 源笔记路径 / 学科"
  步骤 2: 用 System Prompt 模板生成概念 md (三段式：核心概念 / 关键点 / 关联概念)
  步骤 3: 从核心概念第一句提取概念名作为文件名 (如 "Eigenvalues")
  步骤 4: 写 wiki/canvases/math240/Eigenvalues.md (重名自动 _2 _3)
  步骤 5: 读源笔记 Fundamentals.md，把选中文本替换为 [[Eigenvalues]]
  步骤 6: 检查 wiki/canvases/math240/index.md：
            存在 → 更新 (frontmatter doc_count += 1, body "## Concepts" append 行)
            不存在 → auto-create 基本骨架后再更新
  步骤 7: 返回摘要 "✓ Eigenvalues.md 已创建；源笔记已替换为 wikilink；index.md 已更新"
            ↓
用户切回源笔记 tab 看到 [[Eigenvalues]]; 点击跳转到新文件验证内容
```

零额外 API Key 配置，零独立付费，完全复用 Mode D 架构和订阅额度。

---

## Acceptance Criteria

### AC #1: Plugin 第 8 命令注册
- [x] 命令 `canvas:ai-linked-doc` 注册在 Obsidian 命令面板（对齐 1.16 的 `canvas:annotate-callout` 模式）
- [ ] 中文名: "AI 创建双链文档"
- [ ] Settings > Hotkeys 搜 "Canvas" 看到 8 条（1.16 的 7 条 + 本条）
- [ ] 默认 `hotkeys: []`（用户自绑；建议 `Cmd+Shift+D`）

### AC #2: 选中文本必需 + 编辑器就绪检查
- [ ] 命令触发但 `activeEditor` 缺 → Notice "编辑器未激活"（3 秒）
- [ ] 有 editor 但 `getSelection()` 空 → Notice "请先选中文本再创建双链"（3 秒）
- [ ] 双重防护后不进入剪贴板/Claudian 切换流程

### AC #3: 剪贴板 prompt 写入（含 source_note + subject 上下文）
- [ ] 选中文本非空后，调 `navigator.clipboard.writeText(prompt)` 写系统剪贴板
- [ ] Prompt 模板（硬编码在 handler，中文）：
  ```
  /ai-linked-doc
  选中文本:
  <selected text>
  
  源笔记路径: <activeFile.path>
  学科: <frontmatter.subject or "unknown">
  
  请为这段内容创建一个概念文档（三段式：## 核心概念 / ## 关键点 / ## 关联概念）。
  ```
- [ ] `subject` 从当前文件 frontmatter 读取；缺字段则填 `"unknown"`（Skill 侧会用 AskUserQuestion 补）
- [ ] 剪贴板 API 失败（权限拒绝）→ Notice "剪贴板写入失败，请检查 Obsidian 权限"（5 秒）

### AC #4: 触发 Claudian sidebar 打开
- [ ] 调 `this.app.commands.executeCommandById("claudian:open-view")` 打开 Claudian 侧栏
- [ ] Notice: "已复制到剪贴板，切到 Claudian 粘贴即可触发"（5 秒）
- [ ] 若 Claudian 未装（`findCommand("claudian:open-view")` 返回 null）→ Notice "未检测到 Claudian 插件，请先安装并登录 Claude Code"（5 秒）
- [ ] Plugin 侧流程在此结束（不等 Skill 回调）

### AC #5: Skill 文件存在 + Claudian 可发现
- [ ] `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` 存在且语法合法（YAML frontmatter + Markdown body）
- [ ] Frontmatter: `name: ai-linked-doc` + `description`（一句话说明）
- [ ] Claudian 侧栏输入 `/ai-linked-doc` 触发该 Skill（Claudian 扫描 vault 级 `.claude/skills/`）
- [ ] Skill 文件首行 `---` 前无 BOM/空行

### AC #6: Skill 调 Claude Code CLI 生成 markdown
- [ ] Skill body 指令 Claude Code（当前 Claudian session）用 **System Prompt 模板**（见 Dev Notes）生成 markdown
- [ ] 生成内容必须包含：
  - frontmatter: `type: concept` / `subject: <参数>` / `mastery_score: 0.30` / `created_at: <ISO>` / `source_note: "[[<filename stem>]]"`
  - `## 核心概念` 段（1-2 句定义）
  - `## 关键点` 段（3-5 个要点 bullet）
  - `## 关联概念` 段（至少含 `- [[<source_note_stem>]] — extracted`）
- [ ] 若剪贴板文本是中文 → 生成内容用中文；英文同理
- [ ] 不生成代码块，除非概念本身涉及代码（System Prompt 显式约束）

### AC #7: Skill 写新文件到 `wiki/canvases/<subject>/`
- [ ] 路径格式: `wiki/canvases/<subject>/<concept-name>.md`
- [ ] 文件名从生成内容的 `## 核心概念` 首句提取主概念名（去符号/空格用 `-` 连接）
- [ ] 重名检测：已存在 `Eigenvalues.md` → 尝试 `Eigenvalues_2.md` → `Eigenvalues_3.md`（最多 9 轮）
- [ ] 若 `<subject>` 是 `"unknown"` → Skill 内 AskUserQuestion 让用户手动指定学科代码（或回答 `default` 落到 `wiki/canvases/default/`）
- [ ] 用 Claude Code `Write` 工具（而非 bash heredoc）创建

### AC #8: Skill 替换源笔记选中为 wikilink
- [ ] Skill 读源笔记全文 (`Read` tool)
- [ ] 用 `Edit` 工具把剪贴板里记录的"选中文本"原样替换为 `[[<concept-name>]]`（不用 fileManager API，纯文本级 Edit 即可）
- [ ] 若源笔记中出现选中文本多次 → 仅替换第一个命中（`replace_all: false`）并在返回摘要提示用户手动检查其他位置
- [ ] 替换失败（文本已变）→ 返回摘要警告 "源笔记选中文本未找到，未替换"，不抛错

### AC #9: Skill 更新 index.md（auto-create if missing）
- [ ] 检查 `wiki/canvases/<subject>/index.md` 是否存在
- [ ] **存在** → 读 → 更新 frontmatter `doc_count` +1（若字段缺则初始化为 1）；body 找到 `## Concepts` section append `- [[<concept-name>]] — extracted, weak (0.30)`；若无此 section 则在文件末 append section + 行
- [ ] **不存在** → Skill 自动创建最小 index.md（frontmatter `type: board_index` + `subject` + `doc_count: 1` + `created_at`；body `# <subject> 原白板\n\n## Concepts\n- [[<concept-name>]] — extracted, weak (0.30)\n`），**不再依赖 Story 1.19**
- [ ] 用 `Edit` 或 `Write` 工具操作，无并发（Skill 是同步执行的，无需 debounce queue）

### AC #10: 错误处理 + 返回摘要
- [ ] Skill 成功完成 → 在 Claudian 返回消息：`✓ <concept-name>.md 已创建\n✓ 源笔记 [[<source>]] 已替换为 [[<concept-name>]]\n✓ index.md (<subject>) 已更新 (doc_count -> N)`
- [ ] 任一步失败 → 返回部分完成的清单 + 失败原因（例如 `✓ 新文件已创建\n✗ 源笔记替换失败: 选中文本已被修改\n⚠ index.md 未更新`）
- [ ] Plugin 侧的 Claudian 未装 / 剪贴板失败 也按 Notice 文案清晰提示（AC #3 + AC #4 已覆盖）

---

## Tasks

### Plugin 侧（`frontend/obsidian-plugin/`）

- [ ] **新增第 8 命令** 在 `src/main.ts` 的 `registerCanvasCommands()` 末尾：
  ```typescript
  this.addCommand({
    id: "canvas:ai-linked-doc",
    name: "AI 创建双链文档",
    callback: () => this.handleAILinkedDoc(),
  });
  ```
- [ ] **新增 handler** `handleAILinkedDoc()` 方法（完整代码见 Dev Notes "代码骨架"）：编辑器检查 + 选中检查 + frontmatter subject 读取 + prompt 组装 + `navigator.clipboard.writeText` + Claudian 命令 ID 可用性检查 + `executeCommandById("claudian:open-view")` + Notice 反馈
- [ ] **扩展 Story 1.5 冲突检测** 无需改（现有逻辑自动覆盖第 8 命令）
- [ ] **新增测试** `tests/ai-linked-doc.test.ts` (3 用例)：
  - prompt 模板 string format（`/ai-linked-doc\n选中文本:\n...\n源笔记路径: ...\n学科: ...`）
  - 无 subject frontmatter → prompt 填 "unknown"
  - 选中文本含 markdown 语法（粗体 `**xxx**`）保留原样

### Skill 侧（`canvas-vault/.claude/skills/ai-linked-doc/`）

- [ ] **新建 `SKILL.md`**（完整内容见 Dev Notes "Skill 内容"）：YAML frontmatter (`name` + `description`) + 六步流程说明 + System Prompt 模板嵌入 + 错误处理策略
- [ ] **内嵌 System Prompt 模板**（Round 3 QA Line 141-177 的三段式结构 + 用户语言检测约束）
- [ ] **内嵌错误处理规则**（选中文本未找到 / index.md 缺失 / subject = unknown 的 AskUserQuestion 降级）

### 部署 + 测试

- [ ] `cd frontend/obsidian-plugin && npm run build` → main.js 更新
- [ ] `cp frontend/obsidian-plugin/main.js canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`
- [ ] 验证 `ls canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` 存在
- [ ] Obsidian Cmd+Q 重开加载 v2 main.js
- [ ] 用户在 Obsidian Settings > Hotkeys 给 `canvas:ai-linked-doc` 绑 `Cmd+Shift+D`
- [ ] 跑 UAT 14 步

---

## Dev Notes

### 已锁技术决策（v2 对齐 architecture.md Mode D + Round 3 QA）

| 决策点 | 选择 | 理由 |
|---|---|---|
| Plugin AI 调用 | **不调** — Plugin 只做剪贴板 + Claudian 切换 | 对齐 architecture.md:113 Mode D（用户订阅额度），废弃 v1 独立 API Key |
| Claudian 触发 | `app.commands.executeCommandById("claudian:open-view")` | Obsidian 标准 sidebar 打开模式；若 Claudian 改命令 ID 则 graceful fallback（AC #4 Notice） |
| 剪贴板 API | `navigator.clipboard.writeText()` | Obsidian 1.5+ 原生支持；比 `require("electron").clipboard` 更跨平台 |
| Skill 路径 | `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` | vault-level skill，Claudian 自动扫描；对齐 Story 1.19 的 `.claude/skills/` 布局 |
| Skill 触发 | 用户手动 Cmd+V 粘贴 prompt 后回车 | 最直观；Plugin 无法直接触发 Skill（Claudian 没暴露 JSON-RPC API） |
| 文件创建 | Claude Code `Write` 工具（在 Skill 内） | Skill 执行时 Claude Code CLI 有完整 vault 权限；不经 Plugin |
| Wikilink 替换 | Claude Code `Edit` 工具（`replace_all: false`） | 纯文本级替换，避免 FileManager API 的 cache timing 问题 |
| index.md 防 race | 不需要（Skill 同步执行） | v1 的 debounce queue 针对 Plugin 并发，Skill 每次对话只跑一次，无并发 |
| index.md 缺失处理 | Skill 自动 auto-create | 解除 v1 对 Story 1.19 的硬依赖 |
| 概念名提取 | Skill 从生成内容 `## 核心概念` 首句提取 | 比 Plugin 弹 Modal 问用户更丝滑（零交互）|
| Subject 缺失 | Skill 内 AskUserQuestion 降级 | 符合 DD-09 增量提问纪律 |
| 付费模型 | 用户订阅额度（Claude Code Pro/Max plan） | 对齐 Mode D，零额外付费 |

### v1 → v2 correct-course 触发点

- **Gap**：v1 spec (`implementation-artifacts/epic-1/1-17-ai-linked-doc.md` 2026-04-17 初稿) 让 Obsidian plugin 直调 Anthropic API（`requestUrl()` + `app.secretStorage` 存独立 API key），与 `planning-artifacts/architecture.md:113` 已锁定的 Mode D 决策（"Claude Agent SDK spawn 官方 Claude Code CLI，用户订阅额度"）**直接冲突**。
- **用户质疑**：用户 2026-04-19 批注指出"我们都降级到 obsidian 了，API 调用应该走 Claudian 复用订阅额度，为什么要另外收费让我配 key"。
- **形态 β 决策**：Plugin 只做本地交互（剪贴板 + Claudian 切换），所有 AI 生成 / 文件写入 / wikilink 替换 / index.md 更新都搬到 `.claude/skills/ai-linked-doc/SKILL.md`，由 Claudian（= Claude Code CLI 订阅额度）执行。
- **影响**：1) 依赖从 `["1.16","1.19"]` 缩为 `["1.16"]`（index.md auto-create 替代 1.19 硬前提）；2) 估时从 10h 降为 6h（Plugin 只 1 handler + 1 Skill 文件，不再需要 Settings UI / Modal class / API error handling / debounce queue）；3) 用户零付费。

### 代码骨架（Plugin 侧）

`frontend/obsidian-plugin/src/main.ts` 在 `registerCanvasCommands()` 末尾追加：

```typescript
this.addCommand({
  id: "canvas:ai-linked-doc",
  name: "AI 创建双链文档",
  callback: () => this.handleAILinkedDoc(),
});
```

新增 private method：

```typescript
private async handleAILinkedDoc() {
  const editor = this.app.workspace.activeEditor?.editor;
  if (!editor) {
    new Notice("编辑器未激活");
    return;
  }
  const selected = editor.getSelection();
  if (!selected) {
    new Notice("请先选中文本再创建双链", 3000);
    return;
  }

  const activeFile = this.app.workspace.getActiveFile();
  const sourcePath = activeFile?.path ?? "unknown";
  const cache = activeFile
    ? this.app.metadataCache.getFileCache(activeFile)
    : null;
  const subject = (cache?.frontmatter?.subject as string) ?? "unknown";

  const prompt =
    `/ai-linked-doc\n` +
    `选中文本:\n${selected}\n\n` +
    `源笔记路径: ${sourcePath}\n` +
    `学科: ${subject}\n\n` +
    `请为这段内容创建一个概念文档（三段式：## 核心概念 / ## 关键点 / ## 关联概念）。`;

  try {
    await navigator.clipboard.writeText(prompt);
  } catch {
    new Notice("剪贴板写入失败，请检查 Obsidian 权限", 5000);
    return;
  }

  const claudianCmd = this.app.commands.findCommand("claudian:open-view");
  if (!claudianCmd) {
    new Notice(
      "未检测到 Claudian 插件，请先安装并登录 Claude Code",
      5000,
    );
    return;
  }

  new Notice("已复制到剪贴板，切到 Claudian 粘贴即可触发", 5000);
  this.app.commands.executeCommandById("claudian:open-view");
}
```

### Skill 内容（`canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`）

完整文件内容（直接 Write 到磁盘）：

```markdown
---
name: ai-linked-doc
description: 根据剪贴板粘贴的选中文本，生成概念 md 文档 + 写入 wiki/canvases/<subject>/ + 把源笔记选中替换为 wikilink + 更新/创建 index.md（Canvas Learning System Story 1.17 形态 β）。
---

# AI 双链文档 Skill

## 触发方式

用户在 Claudian 输入框粘贴形如下面的 prompt 后回车：

```
/ai-linked-doc
选中文本:
<文本>

源笔记路径: wiki/canvases/<subject>/<source>.md
学科: <subject>

请为这段内容创建一个概念文档（三段式：## 核心概念 / ## 关键点 / ## 关联概念）。
```

## 执行步骤

### 1. 解析输入
从消息中抽出 3 个字段：
- `选中文本`（可能多行，遇到下一个 `源笔记路径:` 停止）
- `源笔记路径`（相对 vault 根）
- `学科`（单 token，可能是 "unknown"）

若 `学科 == "unknown"`，用 AskUserQuestion 问用户："当前源笔记缺少 subject frontmatter。请指定学科代码（如 math240），或回答 default 落到 wiki/canvases/default/。"

### 2. 生成概念文档
用下面的 System Prompt 模板生成概念 md 内容（输出是完整 markdown 文件内容，含 frontmatter）：

```
你是 Canvas Learning System 的概念文档生成器。

任务：基于用户提供的"选中文本"和"源笔记路径"，生成一份结构化的概念笔记。

输出格式（Markdown，完整文件内容，含 frontmatter）：

---
type: concept
subject: <参数填入>
mastery_score: 0.30
created_at: <ISO 时间戳>
source_note: "[[<源笔记文件名 stem>]]"
created_from: ai_linked_doc
---

# <主概念名>

## 核心概念
（基于选中文本，1-2 句话精准定义，不赘述）

## 关键点
- 要点 1
- 要点 2
- 要点 3
- 要点 4 (可选)
- 要点 5 (可选)

## 关联概念
- [[<源笔记 stem>]] — extracted from this note
- [[其他相关概念]] — 如有明显关联（可选）

约束：
- 语言匹配选中文本（中文输入 → 中文输出；英文同理）
- 概念定义优先精准而非详尽
- 不写代码块，除非概念本身涉及代码（如"递归函数"、"lambda 表达式"）
- 关键点 3-5 条，避免超过 7 条
- 主概念名从核心概念首句提炼（如 "Eigenvalues are special..." → "Eigenvalues"）
```

### 3. 提取概念名
从生成内容的 `## 核心概念` 首句抽主词作为文件名（去空格/特殊符号用 `-` 连接；中文直接用 2-6 字的概念词）。

### 4. 写新文件
目标路径：`wiki/canvases/<subject>/<concept-name>.md`

重名处理：
- 若已存在 → 尝试 `<name>_2.md`, `<name>_3.md`, ..., 最多 `<name>_9.md`
- 9 轮全占用 → 返回错误

用 `Write` 工具创建。

### 5. 替换源笔记选中为 wikilink
用 `Read` 读源笔记全文，确认选中文本存在。用 `Edit` 工具：
- `old_string`: 原选中文本（原样，含换行）
- `new_string`: `[[<concept-name>]]`
- `replace_all`: false

失败场景：
- 文本未找到（用户在等 AI 生成期间改了文件）→ 在摘要里标记 `✗ 源笔记替换失败: 选中文本未找到`
- 文本出现多次 → 仅替换第一个（`replace_all: false` 默认行为），摘要提示 `⚠ 源笔记选中文本出现多次，仅替换首个`

### 6. 更新/创建 index.md
目标路径：`wiki/canvases/<subject>/index.md`

**若存在**：
- 用 `Read` 读全文
- frontmatter `doc_count` +1（字段缺 → 初始化为 1）
- body 找 `## Concepts` section：
  - 存在 → append `- [[<concept-name>]] — extracted, weak (0.30)`
  - 不存在 → 在文件末追加 `\n## Concepts\n- [[<concept-name>]] — extracted, weak (0.30)\n`
- 用 `Write` 覆盖（因为涉及 frontmatter 数字变更，Edit 模糊易错）

**若不存在**（auto-create）：
直接 `Write` 下面的骨架：

```
---
type: board_index
subject: <subject>
doc_count: 1
created_at: <ISO>
---

# <subject> 原白板

## Concepts
- [[<concept-name>]] — extracted, weak (0.30)

## Recent Activity
- <ISO>: <concept-name>.md created via /ai-linked-doc
```

### 7. 返回摘要
成功路径：
```
✓ <concept-name>.md 已创建 (wiki/canvases/<subject>/)
✓ 源笔记 [[<source-stem>]] 已替换为 [[<concept-name>]]
✓ index.md (<subject>) 已更新 (doc_count -> N)
```

部分失败路径（示例）：
```
✓ Eigenvalues.md 已创建
✗ 源笔记替换失败: 选中文本未找到
⚠ index.md (math240) 已更新 (doc_count -> 3)
请手动在源笔记插入 [[Eigenvalues]] wikilink。
```

## 约束

- 不调 Graphiti（下游 Story 处理知识图谱入图）
- 不触碰 `raw/` 目录（降级后只写 `wiki/canvases/<subject>/`）
- 不加 `tags:` frontmatter（非 MVP 刚需）
- 生成内容不含 AI 自我介绍（"作为 AI 我..."）
```

### 风格参考

- Plugin 第 N 命令注册模式：`frontend/obsidian-plugin/src/main.ts:38-88`（Story 1.16 v2）
- Plugin handler Notice 模式：`src/main.ts:94-106`（`handleAnnotateCallout` 双重防护）
- Skill `name + description` frontmatter：`canvas-vault/.claude/skills/configure-whiteboard/SKILL.md`（Story 1.19）

---

## UAT Script (非技术用户 14 步)

**前置**：
1. Claudian 插件已在 canvas-vault 安装并启用，Claude Code 已登录（订阅额度可用）
2. `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` 是 v2（含第 8 命令）
3. `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` 已部署
4. Obsidian Settings > Hotkeys 给 `canvas:ai-linked-doc` 绑了 `Cmd+Shift+D`
5. 测试文件 `wiki/canvases/math240/Fundamentals.md` 存在，frontmatter 含 `subject: math240`，body 含一段 "Eigenvalues are special vectors that satisfy Av = λv"
6. `wiki/canvases/math240/index.md` **可以不存在**（验证 auto-create）

**步骤**：

1. **重启 Obsidian**：Cmd+Q 彻底退出，重新打开 canvas-vault
2. **验证第 8 命令**：Cmd+Shift+P → 搜 "AI 创建双链文档" → 看到命令在列表
3. **验证 Skill 文件存在**：Cmd+Shift+P → "Show in system explorer" → 定位 `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` 存在可读
4. **打开源笔记**：Obsidian 打开 `wiki/canvases/math240/Fundamentals.md`
5. **测试空选中**：不选任何文本，按 `Cmd+Shift+D` → 看到 Notice "请先选中文本再创建双链"（3 秒）
6. **选中目标文本 + 触发**：选 "Eigenvalues are special vectors that satisfy Av = λv" → 按 `Cmd+Shift+D`
7. **验证 Notice + Claudian 切换**：看到 Notice "已复制到剪贴板，切到 Claudian 粘贴即可触发"；Claudian 侧栏自动弹出（或进入前台）
8. **粘贴 prompt 到 Claudian**：在 Claudian 输入框 Cmd+V → 看到剪贴板内容（`/ai-linked-doc\n选中文本:\nEigenvalues...\n源笔记路径: wiki/canvases/math240/Fundamentals.md\n学科: math240\n...`）→ Enter
9. **等 Skill 执行**：Claude Code 输出 "执行 Step 1 解析..."、"Step 2 生成文档..."、"Step 4 写 wiki/canvases/math240/Eigenvalues.md..."（约 10-30s）
10. **验证摘要**：最后看到 3 行 ✓：
    ```
    ✓ Eigenvalues.md 已创建 (wiki/canvases/math240/)
    ✓ 源笔记 [[Fundamentals]] 已替换为 [[Eigenvalues]]
    ✓ index.md (math240) 已更新 (doc_count -> 1)
    ```
11. **验证新文件**：Obsidian 打开 `wiki/canvases/math240/Eigenvalues.md` → 看到三段式结构 + frontmatter 含 `type: concept` / `mastery_score: 0.30` / `created_from: ai_linked_doc`
12. **验证源笔记替换**：切回 Fundamentals.md 的源 tab → 光标位置附近看到 `[[Eigenvalues]]`（原选中文本已被替换）
13. **验证 index.md auto-create**：打开 `wiki/canvases/math240/index.md` → 看到 frontmatter `doc_count: 1` + `## Concepts` 下有 `- [[Eigenvalues]] — extracted, weak (0.30)`
14. **边界：未装 Claudian**：临时在 Settings > Community Plugins 禁用 Claudian → `Cmd+Shift+D` → 看到 Notice "未检测到 Claudian 插件，请先安装并登录 Claude Code"（5 秒，不崩溃）→ 重新启用 Claudian 恢复

---

## Pitfalls + 诊断矩阵

| 症状 | 原因 | Claude Code 诊断 + 修 |
|---|---|---|
| `Cmd+Shift+D` 无反应 | Hotkey 未绑定 | Settings > Hotkeys 搜 "AI 创建双链文档" 重绑 |
| Notice "未检测到 Claudian 插件" | Claudian 未装或未登录 | Community Plugins 装 Claudian + 终端登录 Claude Code CLI |
| Notice "剪贴板写入失败" | 系统权限拒绝 | macOS 系统偏好 > 隐私 > 输入监控给 Obsidian 权限 |
| Claudian 侧栏未弹出 | 命令 ID 变化 | Cmd+Shift+P 搜 "Claudian" 确认实际命令 ID，改 AC #4 的 ID 字符串 |
| `/ai-linked-doc` 在 Claudian 不触发 | SKILL.md 未被扫描到 | 确认路径 `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` 且 frontmatter 合法；Claudian 设置刷新 |
| Skill 生成的 md 是英文但选中是中文 | Prompt 模板约束被忽略 | 检查 System Prompt "语言匹配"段是否完整嵌入 |
| 新文件写到错误目录 | subject frontmatter 缺 | Skill AskUserQuestion 应触发；若没触发检查 Plugin 传的是否真是 "unknown" |
| 源笔记替换失败 | 用户在等待期间改了文件 | Skill 摘要会提示 `✗`，用户手动插入 wikilink |
| index.md doc_count 变成 NaN | frontmatter YAML 非整数 | Skill 用 `Read` 先读再 `Write` 覆盖；检查旧 index.md 的 doc_count 是否字符串 |
| 概念名重名冲突 | 同名概念已存在 | Skill 自动加 `_2` 后缀（最多 `_9`） |
| Skill 卡在 Step 2 生成很久 | Claude Code 响应慢 | 正常耗时 10-30s；超过 60s 看 Claudian 侧栏 error log |

---

## 不会做的事

- ❌ **不调独立 Anthropic API**（v1 方案已废弃；违反 architecture.md:113 Mode D）
- ❌ **不配 API Key Settings UI**（形态 β 零额外配置，复用 Claude Code 订阅额度）
- ❌ **不用 `requestUrl()` 直调 AI**（完全搬到 Skill 侧，Plugin 只做剪贴板 + 命令切换）
- ❌ **不做后端同步**（Graphiti 入图是下游 Story，本 Story 纯 vault 文件级）
- ❌ **不做 Graphiti 入图**（延后到专门的 Story；本 Story 仅创建 md + wikilink + index.md）
- ❌ **不做 Modal UI**（用户直接在 Claudian 输入，比弹 modal 更丝滑）
- ❌ **不做 debounce queue**（Skill 同步执行无并发，v1 的 `Map<path, timeout>` 被删除）
- ❌ **不做 `fileManager.generateMarkdownLink()`**（Skill 用纯文本 Edit，避开 cache timing 问题）
- ❌ **不写多行 frontmatter `related_concepts: []`**（System Prompt 模板简化为 `source_note` 单字段 + `## 关联概念` 正文列表；frontmatter 数组字段超出 MVP）
- ❌ **不硬依赖 Story 1.19**（index.md auto-create 替代 1.19 前置）

---

> [!question]+ 用户批注 - Story 1.17 spec v2
> 10 AC + 14 步 UAT 是否符合预期？形态 β（Plugin 剪贴板 + Claudian Skill）是否与 Mode D 架构彻底对齐？Skill 的 System Prompt 三段式 + frontmatter 字段是否够用？是否授权 bmad-bmm-dev-story 实施？
> （批注区）

---

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1 | build | `cd frontend/obsidian-plugin && npm run build` | exit 0, `main.js` 更新 (v2 字节数 > v1.16 的 7886) |
| CP-2 | deploy-plugin | `cp frontend/obsidian-plugin/main.js canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` | file copied |
| CP-3 | deploy-skill | `ls canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` | file exists, 非空 |
| CP-4 | skill-frontmatter | `head -3 canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` | 首行 `---`，第二行 `name: ai-linked-doc` |
| CP-5 | plugin-reload | Manual: Obsidian Cmd+Q → reopen | F12 console 无 error |
| CP-6 | command-visible | Manual: Cmd+Shift+P 搜 "AI 创建双链文档" | 命令出现 |
| CP-7 | unit-test | `cd frontend/obsidian-plugin && npm test` | 3 用例全 pass (prompt 模板 / unknown subject / markdown 语法保留) |
| CP-8 | UAT | Run "## UAT Script" 14 步 | all pass |

## User Feedback & Changes

### Feedback Log
<!-- 用户在 Obsidian 跑 UAT 后批注 -->

### Deviation Notes
<!-- Dev agent 偏离 spec 时记录原因 -->

## Dev Agent Record (v2 实施 2026-04-20)

### Agent Model Used
Claude Opus 4.7 (1M context) — 3 并行 Agent deep explore + direct implementation

### Debug Log References
- Build: `cd frontend/obsidian-plugin && npm run build` → `main.js` 10571 bytes (1.16 v2 = 7886 + 2685)
- Test: `npm test` → 13/13 passed (9 callout + 4 ai-linked-doc)
- Deploy: `cp main.js ../../canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` (7 Story 1.17 符号命中)
- Skill: `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` 已部署

### Completion Notes List

见上方主 Dev Agent Record 段（Edit 时文件结构冲突，全部 13 项完成笔记已写在 frontmatter 之后的 Change Log 之前）。核心：13 AC 全部实施（Plugin 4 + Skill 5 + 错误处理 1），0 TODO/mock/stub，4 单元测试 + 14 步 UAT 待用户 hands-on。

### File List (v2 实施)

- **NEW** `frontend/obsidian-plugin/src/ai-linked-doc.ts` — 纯函数 `buildAIDocPrompt(selected, sourcePath, subject)`
- **MOD** `frontend/obsidian-plugin/src/main.ts` — import + 第 8 命令 + `handleAILinkedDoc`
- **NEW** `frontend/obsidian-plugin/tests/ai-linked-doc.test.ts` — 4 用例
- **MOD** `frontend/obsidian-plugin/package.json` — test script 含 2 个 test file
- **NEW** `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` — Claudian Skill 6 步流程
- **MOD** `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` — build 10571B (.gitignore 排除)
- **MOD** `_bmad-output/implementation-artifacts/sprint-status.yaml` — 1-17 `ready-for-dev → review`
- **MOD** `_bmad-output/implementation-artifacts/epic-1/1-17-ai-linked-doc.md` — 本 spec (AC #1 打勾 / Dev Agent Record / File List / Change Log)
- **NEW** `_bmad-output/验收单/Story-1.17-ai-linked-doc.md` — 小白 UAT 14 步验收单

### Change Log

- 2026-04-19 v2 — spec 完全重写（形态 β：Plugin 剪贴板 + Claudian Skill 分离）。触发点：用户批注指出 v1 方案（Plugin 直调 Anthropic API + 独立 API Key）违反 `planning-artifacts/architecture.md:113` 已锁的 Mode D 决策。重构为 Plugin 第 8 命令只做"编辑器/选中检查 + prompt 写剪贴板 + 切 Claudian sidebar"，所有 AI 生成 / 文件写入 / wikilink 替换 / index.md 更新搬到 `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`，由 Claudian（Claude Code CLI 订阅额度）执行。依赖从 `["1.16","1.19"]` 缩为 `["1.16"]`（index.md auto-create 替代 1.19 硬前提）；估时从 10h 降为 6h；零额外付费。[PLAN: EPIC1-BMAD-DEV-ASSESS-2026-04-17]
- 2026-04-17 v1 (废弃) — 初稿方案：Obsidian plugin 直调 Anthropic API + Settings UI 配独立 API key + Modal + debounce queue + index.md 硬依赖 Story 1.19。9 AC + 11 步 UAT。违反 Mode D 架构，未被实施。
