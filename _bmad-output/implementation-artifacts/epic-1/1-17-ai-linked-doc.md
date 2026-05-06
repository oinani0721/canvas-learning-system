---
story_id: "1.17"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "review"
priority: "P0"
estimate_hours: 10
depends_on: ["1.16"]
blocks: []
trace: ["FR-CONV-08","FR-KG-06"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
revision: "v3.0-hybrid-script-instant-async-llm-2026-04-30"
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

---

## D4 UX 决策落地 (2026-04-30 · Story 1.19 v4 UAT 通过后 unblock)

**前置**: 1.19 v4 UAT 已通过（用户亲自跑通），1.17 status 从 blocked → ready-for-dev。

### D4-1 🎯 UX：AI 派生新节点后跳转方式

**用户拍板**: ✅ **B toast 不打断**（推荐方案）

**实施细节**（dev 时落地）:
- AI 派生完成后，**留在原 md**（不切 active file）
- Obsidian 右下角弹 toast: `✓ 新节点 [[节点/<concept>]] 已建好` （3 秒自动消失）
- toast 含 wikilink 文本，用户**可点击跳转**（不强制）
- **不**自动 `workspace.openLinkText(name, '', true)` 开新 tab（v2 spec 默认行为是 `true` 即新 tab，本决策改为不开 tab）

**spec 影响**: AC #4「新节点已派生且 wikilink 已替换」→ 加子句"新节点不在新 tab 打开，仅 toast 提示"

### D4-2 🎯 UX：AI 派生失败提示方式

**用户拍板**: ✅ **A toast + 重试按钮**（推荐方案）

**实施细节**:
- 派生失败（API 超时 / 401 / 解析错误）→ Obsidian 右下角红色 toast: `❌ 派生失败：<原因>`
- toast 含「重试」按钮 → 用户点击后**复用之前的 prompt** 重新调用 Claudian Skill（不需要用户重新选文本）
- 失败原文**保留在剪贴板**直到重试成功 / 用户主动取消
- **不**在原 md 选中位置插 `[!error]+` callout（避免污染原 md）

**spec 影响**: 加新 AC「派生失败时 toast 显示原因 + 重试按钮，重试复用 prompt」

---

## v2.2 Dev 完成（2026-04-30）

**Status**: review → 待用户 UAT

**实施**：
- ✅ D4-1 plugin 天然实现（plugin handleAILinkedDoc 不调 workspace.openLinkText，用户留在源笔记；SKILL.md Step 8 加 D4-1 注释 + toast 文案"💡 你想看新节点 → Cmd+Click 跳转（不强制）"）
- ✅ D4-2 plugin 加 `showRetryNotice` helper（duration 10s，含「重试」mod-cta button），handleAILinkedDoc 的 2 个 catch 路径（剪贴板写入失败 / Claudian 未装）改用 retry notice

**File List (v2.2 增量)**：
- **MOD** `frontend/obsidian-plugin/src/main.ts` — 新增 `showRetryNotice` 方法 + handleAILinkedDoc 2 处 catch 改用 retry notice + 注释加 D4-1/D4-2 说明
- **MOD** `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` — Step 8 加 D4-1 决策注释 + 回执文案末加 wikilink 跳转提示
- **MOD** `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` — build 13432B（v2.1 是 10571B，+2861B = retry notice helper）

**Change Log (v2.2)**:
- 2026-04-30 v2.2 — D1 (Story 1.19 UAT) 通过后 unblock；落地 D4-1（plugin 天然不开 tab）+ D4-2（showRetryNotice 含重试按钮，10s sticky）UX 决策。Plugin TS edit + SKILL.md Step 8 patch + npm run build + cp main.js → canvas-vault。Plan: D4 UX 决策落地 2026-04-30。

---

## v2.4 Dev 完成（2026-04-30 · 关系类型双写）

**Status**: review → 待用户跑 v2.4 UAT（在 v2.2 14 步基础上 +3 步关系类型验收）

**触发**：用户在 v2.2 UAT 中明确批注："选择文本拉出作为新的节点的时候，没有向我询问节点和节点之间是什么关系，两者之间的联系应该也有相关的 callout 来进行标注的。"

**用户 D1 决策（2026-04-30）**：
- **D1-1 关系类型集**：✅ **C 混合 7 类**（Story 6-3 5 类 + 社区补 prerequisite + example_of）
- **D1-2 询问时机**：✅ **A 派生前立即弹**（Cmd+Shift+D 选完文字立即 modal）
- **D1-3 callout 位置**：✅ **C 双写**（源笔记 callout 视觉 + 新节点 frontmatter 数据）

### v2.4 Acceptance Criteria（追加 v2.2 之外的 5 条）

#### AC #11: Plugin 关系类型 Modal（D1-2 派生前立即弹）
- [x] `RelationTypeModal` 类继承 `FuzzySuggestModal<RelationTypeOption>`，placeholder："派生关系：新节点和当前源笔记是什么关系？(7 类，输入过滤)"
- [x] `getItems()` 返回 `RELATION_TYPES` 常量（7 项，readonly）
- [x] `getItemText()` 显示 `${label} — ${description}`
- [x] `handleAILinkedDoc()` 在选中文本检查通过后**立即** open modal（不进入剪贴板写入）
- [x] modal Esc 取消 → silent return（不写剪贴板，不报错）

#### AC #12: 7 类关系语义（D1-1 决策 C）
- [x] `RELATION_TYPES` 数组顺序固定：`prerequisite / depends_on / refines / extends / example_of / contradicts / related_to`
- [x] 每项 `{key, label, description}` 完整
- [x] `isValidRelationKey(key)` 严格匹配 7 类
- [x] `getRelationLabel(key)` 返回中文 + 英文 key（如 `先修 (prerequisite)`）；未知 key 兜底返回原值
- [x] `buildAIDocPrompt(...,relationType)` 注入 `关系类型: <key> (<label>)\n` 行（紧跟"活动白板:"行）
- [x] 非法 / 缺省 relationType → 自动回落 `related_to`（不抛错）

#### AC #13: Skill frontmatter 写 relationships[]（D1-3 机器可读半边）
- [ ] Skill Step 1 解析 prompt 的"关系类型"字段，提取 key
- [ ] Skill Step 3 frontmatter 模板含 `relationships:` 数组：`[{type: <key>, target: "[[<源笔记 stem>]]"}]`
- [ ] 非 7 类 key → Skill 回落 `related_to` + 回执标 `⚠ 关系类型回落`
- [ ] 自检清单含"frontmatter 含 relationships[]"项

#### AC #14: Skill 源笔记 callout 双写（D1-3 视觉半边）
- [ ] Skill Step 6 `Edit` 的 `new_string` 含 wikilink + 5 行 callout 模板：
  ```
  [[节点/{concept_name}]]

  > [!relation/{key}]+ 派生关系: {中文标签}
  > 上方 wikilink 节点派生自这段文本，关系类型为 **{key}**。
  ```
- [ ] 中文标签映射表：先修/依赖/细化/扩展/例子/反驳/相关
- [ ] `replace_all: false` 不变；选中文本未找到时不抛错（继续 Step 7）

#### AC #15: 白板 + 回执含关系类型
- [ ] Step 7 `## Concepts` append 行格式: `- [[节点/{name}]] — <key>, weak (0.30)`（替代 v2.2 的 `extracted, weak`）
- [ ] Step 7 `## Recent Activity` append 行末加 `（关系: <key>）`
- [ ] Step 8 回执 4 行格式（v2.2 是 3 行），第 4 行: `关系类型: <key> (<中文标签>)`

### File List (v2.4 增量)
- **MOD** `frontend/obsidian-plugin/src/ai-linked-doc.ts` — 新增 `RelationTypeOption` interface + `RELATION_TYPES` 7 项常量 + `getRelationLabel()` + `isValidRelationKey()` + `buildAIDocPrompt()` 增 `relationType` 第 4 参数
- **MOD** `frontend/obsidian-plugin/src/main.ts` — 新增 `RelationTypeModal` 类 + `handleAILinkedDoc()` 拆出 `continueAILinkedDoc()` 异步副流程，modal callback 触发；Notice 文案加 `关系: <key>` 提示
- **MOD** `frontend/obsidian-plugin/tests/ai-linked-doc.test.ts` — 新增 6 个 v2.4 测试用例（RELATION_TYPES 7 类 / isValidRelationKey / getRelationLabel / 注入合法 / 回落非法 / 行序校验）
- **MOD** `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` — title v4 → v4.4；frontmatter description 加"关系类型双写"；硬约束 6 → 8 条；Step 1 解析 4 字段（加关系类型）；Step 3 frontmatter 模板加 `relationships:` 数组；Step 6 模板从单行 wikilink 改 5 行 wikilink+callout；Step 7 append 含关系 key；Step 8 回执 4 行格式；自检清单从 7 项扩 10 项
- **MOD** `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` — build 16534B（v2.2 13432B，+3102B = RelationTypeModal + RELATION_TYPES + relationKey 线穿）

### Change Log (v2.4)
- 2026-04-30 v2.4 — 用户在 v2.2 UAT 中发现 gap "派生时未询问节点关系，需要 callout 标注"。3 并行 Explore agent 调研：项目内部（Story 6-3 5 类）+ 社区（7 类共识）。用户 D1 决策：C 混合 7 类 + A 派生前立即弹 + C 双写（callout + frontmatter）。Plugin v2.4：RelationTypeModal + RELATION_TYPES 常量 + buildAIDocPrompt 第 4 参数。Skill v4.4：8 步流程 + relationships[] + [!relation/<key>]+ callout 模板。31 单元测试 green（25 + v2.4 6 个）。main.js 13432B → 16534B。Plan: `/Users/Heishing/.claude/plans/swift-mapping-alpaca.md` D1 落地 2026-04-30。

---

## v2.5 Dev 完成（2026-04-30 · 派生描述三处落地）

**Status**: review → 待用户跑 v2.5 UAT

**触发**：用户在 v2.4 dev 完成后立即追加："按 Cmd+Shift+D 后先弹关系 modal，然后两者之间的关系，我也可以进行自定义描述我为什么要把这个节点给拉出来。"

**用户 D1-4/D1-5 决策（2026-04-30）**：
- **D1-4 描述必填性**：✅ **B 可选**（留空 / Esc 跳过，不阻断派生）
- **D1-5 描述落地位置**：✅ **C 三处都写**（源笔记 callout body + 新节点 frontmatter relationships[].description + AI prompt 注入）

### v2.5 Acceptance Criteria（追加 v2.4 之外的 4 条）

#### AC #16: Plugin 派生描述 Modal（D1-4 可选 + 链式 modal）
- [x] 新增 `DescriptionModal` 类继承 `Modal`，含 `<textarea>` + 「跳过 (Esc)」+「提交 (Cmd/Ctrl+Enter)」两按钮
- [x] `RelationTypeModal` onChooseItem 回调中链式 open `DescriptionModal`
- [x] textarea 留空 / Esc / 点「跳过」均触发 `onPicked("")`（不阻断派生）
- [x] textarea 含内容 + 点「提交」/ Cmd+Enter → `onPicked(value)`
- [x] modal title 显示已选关系类型 key（如 "派生描述（关系: refines）"）
- [x] textarea placeholder 给具体例子文本（提示用户怎么写）

#### AC #17: buildAIDocPrompt 第 5 参数 + 派生描述行（D1-5 落地点 3）
- [x] `buildAIDocPrompt(selected, sourcePath, activeBoard, relationType, description)` 第 5 参数
- [x] 描述 trim 处理：前后空白 / 末尾换行去掉，内部换行保留
- [x] 描述非空 → prompt 含 `派生描述: <trimmed>\n`
- [x] 描述为空 / undefined → prompt 含 `派生描述: (用户留空)\n` 占位行
- [x] 派生描述行紧跟关系类型行（Skill 解析依赖固定顺序：白板 → 关系 → 描述）

#### AC #18: Skill frontmatter 写 relationships[].description（D1-5 落地点 2）
- [ ] Skill Step 1 解析"派生描述"行，识别 `(用户留空)` 占位 vs 真实描述
- [ ] description 非空 → Step 3 frontmatter `relationships[0].description: "<原值>"`
- [ ] description 为空 → relationships[0] **不**写 description 字段（不要 description: ""）
- [ ] 自检清单含两条："非空 → 写 description" / "为空 → 不写 description 字段"

#### AC #19: Skill 源笔记 callout body 描述行（D1-5 落地点 1）
- [ ] Skill Step 6 模板有 2 条路径：
  - 路径 A（description 空）→ 5 行 callout（v2.4 原版）
  - 路径 B（description 非空）→ 6 行 callout（多 1 行 `> 你的派生意图: <description>`）

#### AC #20: Skill 注入用户意图到生成 prompt（D1-5 落地点 3）
- [ ] description 非空 → Step 3 System Prompt 含【用户派生意图】段，让生成器据此调整 `## 核心概念` 角度
- [ ] AI **不得**机械复读用户描述到正文（应理解意图后用自己的表述）
- [ ] description 为空 → 不注入【用户派生意图】段

### File List (v2.5 增量)
- **MOD** `frontend/obsidian-plugin/src/ai-linked-doc.ts` — `buildAIDocPrompt` 增 `description?: string` 第 5 参数；trim + `(用户留空)` 占位逻辑
- **MOD** `frontend/obsidian-plugin/src/main.ts` — 新增 `DescriptionModal` 类（基于 `Modal` + textarea + 2 按钮 + Cmd+Enter 提交）；`handleAILinkedDoc` 链式 modal（关系 → 描述 → continue）；Notice 文案加 `+描述` 标识
- **MOD** `frontend/obsidian-plugin/tests/ai-linked-doc.test.ts` — 新增 7 个 v2.5 测试（注入 / 行序 / 留空占位 / undefined 占位 / trim / 含换行 / 全 5 参数）
- **MOD** `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` — title v4.4 → v4.5；硬约束 8 → 9 条；Step 1 解析 4 字段 → 5 字段；Step 3 frontmatter 加 `description` 子字段（条件写）+ 用户意图段注入；Step 6 单路径 → 2 路径（A 5 行 / B 6 行）；Step 8 回执 4 行 → 5 行；自检清单 10 项扩 14 项
- **MOD** `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` — build 19159B（v2.4 16534B，+2625B = DescriptionModal + textarea + 5 个 v2.5 测试需要的 helper）

### Change Log (v2.5)
- 2026-04-30 v2.5 — 用户在 v2.4 dev 完成后追加 "可以自定义描述为什么要派生这个节点"。D1-4 决策 B 可选 + D1-5 决策 C 三处都写。Plugin v2.5：DescriptionModal（textarea + 2 按钮 + Cmd+Enter 快捷键）+ buildAIDocPrompt 第 5 参数 + 链式 modal（关系 → 描述 → continue）。Skill v4.5：5 字段解析 + 双路径 callout（5 行 / 6 行）+ frontmatter description 条件写 + AI prompt 注入用户意图段。32 单元测试 green（25 v2 base + 7 v2.5 新增）。main.js 16534B → 19159B。Plan: `/Users/Heishing/.claude/plans/swift-mapping-alpaca.md` D1 落地 2026-04-30。

---

## v2.6 Dev 完成（2026-04-30 · 节点派生节点继承白板归属）

**Status**: review → 待用户跑 v2.6 UAT（在 v2.5 19 步基础上 +1 步节点继承验收）

**触发**：用户截图（2026-04-30 22:22）发现 bug：在节点 md 上 Cmd+Shift+D 派生新节点时，Skill 没读源节点 frontmatter `source_board` 字段，反而弹 AskUserQuestion 让用户重选白板。用户原话："如果这个节点本身就是属于哪一个白板的话，那我本身从这个节点中拉出新的节点的话，本身应该还是属于一个白板的吧。"

**调研**：
- 2 并行 Explore agent：
  - **项目内部**：source_board 字段格式 `"[[原白板/<board>]]"` (Obsidian Link 类型)；Skill Step 2 规则 2 只覆盖 `原白板/` 路径，**没覆盖 `节点/`**；plugin 当前不读 metadataCache.frontmatter
  - **社区共识**：Andy Matuschak / Nick Milo / Zettelkasten 不主张"无条件继承"，但支持"smart default + 用户可改"
- **决策**：自动继承 + 不弹 AskUserQuestion = 用户期望 + 社区"smart default"共识对齐

### v2.6 Acceptance Criteria（追加 v2.5 之外的 3 条）

#### AC #21: Plugin 节点继承 source_board（无 modal 询问）
- [x] 新增 `extractSourceBoardFromFrontmatter(frontmatter)` helper：robust 处理 string / Link 对象 / 多种 wikilink 格式（含 .md 后缀 / alias `|`）
- [x] `handleAILinkedDoc` 增加：当 `sourcePath.startsWith("节点/")` 且 `extractBoardNameFromPath` 未命中（节点本身不是白板路径）→ 调 `metadataCache.getFileCache(activeFile)` 读 frontmatter → `extractSourceBoardFromFrontmatter` 提取 → 设 `activeBoard`
- [x] 提取成功 → 弹 Notice `继承源节点白板归属：<board>（v2.6 自动）` (3s)
- [x] 提取失败 / source_board 缺失 → 不报错，由 Skill fallback 处理（规则 3 → 4）

#### AC #22: extractSourceBoardFromFrontmatter robust 解析
- [x] 接受 string `"[[原白板/<board>]]"` → 提取 board name
- [x] 接受 string `"[[原白板/<board>.md]]"` → 提取 board name（去 `.md` 后缀）
- [x] 接受 string `"[[原白板/<board>|alias]]"` → 提取 board name（去 alias）
- [x] 接受 Obsidian Link 对象 `{link: "原白板/<board>"}` → 提取 board name
- [x] 接受 Link 对象 `{path: "原白板/<board>.md"}` → 提取 board name
- [x] 不在 `原白板/` 下（`节点/` / `wiki/canvases/` / 任意路径）→ null（不错位归属）
- [x] 缺失 / 空 / null / 数字 / 未知类型 → null（不抛错）
- [x] board name 含中英混合 + 空格（`CS 61B 数据结构`）→ 正常提取

#### AC #23: Skill Step 2 加规则 2.5 fallback（双保险）
- [ ] Skill Step 2 优先级列表加新规则 2.5：源笔记路径在 `节点/<concept>.md` → Read 源节点 frontmatter → 提取 source_board → 设 active_board
- [ ] 规则 2.5 命中 → 不弹 AskUserQuestion，直接进入 Step 3
- [ ] 规则 2.5 未命中（frontmatter 无 source_board）→ 走规则 3（.canvas-config.yaml）
- [ ] 该规则在 plugin 已注入 activeBoard 时不触发（规则 1 优先）

### File List (v2.6 增量)
- **MOD** `frontend/obsidian-plugin/src/ai-linked-doc.ts` — 新增 `extractSourceBoardFromFrontmatter()` helper（robust 处理 string / Link / 多 wikilink 格式）
- **MOD** `frontend/obsidian-plugin/src/main.ts` — handleAILinkedDoc 加节点继承逻辑（节点路径 + 不在原白板路径 → 读 metadataCache → 提取 source_board）；继承成功弹 3s Notice
- **MOD** `frontend/obsidian-plugin/tests/ai-linked-doc.test.ts` — 新增 9 个 v2.6 测试（缺失 / string / .md 后缀 / alias / Link.link / Link.path / 拒绝错位归属 / 类型异常 / 中英混合）
- **MOD** `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` — Step 2 优先级列表加规则 2.5 节点继承 fallback
- **MOD** `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` — build 20348B（v2.5 19159B，+1189B = extractSourceBoardFromFrontmatter + metadataCache 调用 + Notice）

### Change Log (v2.6)
- 2026-04-30 v2.6 — 用户截图发现 bug：在节点 md 派生新节点时 Skill 弹 AskUserQuestion 而非自动继承源节点的 source_board。2 并行 Explore agent 调研：项目内部确认 Skill Step 2 规则 2 不覆盖 `节点/` 路径，plugin 不读 metadataCache；社区共识 = "smart default + 用户可改"。Plugin v2.6：extractSourceBoardFromFrontmatter helper（robust 9 形态）+ handleAILinkedDoc 节点继承逻辑 + Notice 提示。Skill v4.6：Step 2 加规则 2.5 fallback。41 单元测试 green（32 base + 9 v2.6 新增）。main.js 19159B → 20348B。Plan: `/Users/Heishing/.claude/plans/swift-mapping-alpaca.md` 节点继承 2026-04-30。

---

## v3.0 Dev 完成（2026-04-30 · Hybrid 架构 · 脚本立即建骨架 + 异步 AI 填正文）

**Status**: review → 待用户跑 v3.0 UAT（替代 v2.6 19 步，新 22 步 hybrid UAT）

**触发**：用户截图（22:34）发现 Claudian 在做 `Step 2 · 确定 active_board` 这种纯 if-else 推理，耗时 15-45s。用户原话："从一个节点拉出一个新的节点生成是否使用相关的脚本程序就可以了，没必要用到相关的 skill。"

**调研**：3 并行 Explore agent
- **Agent 1（项目+架构）**：8 步 Skill 流程仅 Step 3（生成正文）必须 LLM，其余 7 步全 deterministic；Mode D 不被 hybrid 破坏（仍走 Claudian → CLI 订阅额度）
- **Agent 2（社区）**：Note Refactor (60K+) 100% 脚本，Templater 100% 脚本框架，Obsidian Copilot 是 hybrid（LLM 决策 + 脚本执行 8761 行工具最终调 OS CLI）→ 主流 = hybrid
- **Agent 3（失败恢复）**：Vercel/Cursor/Notion AI 均 partial commit + 无 atomic rollback；推荐保留 placeholder + per-step replay；复用 v2.2 showRetryNotice
- **Agent 4（vault API 验证）**：vault.create() 同步安全；processFrontMatter 是 atomic（避免 YAML 转义坑）；editor.replaceSelection 同步；renameFile 自动更新 backlink

**架构决策**：
- **阶段 1 · plugin 脚本，<100ms**：建节点 md（启发式 stub 名）+ frontmatter（含 status: ai_pending）+ wikilink + callout + 白板 ## Concepts + 白板 ## Recent Activity
- **阶段 2 · Skill v5.0 异步**：仅生成 3 段正文 + Edit 替换 placeholder + status: ai_pending → ai_complete

### v3.0 Acceptance Criteria（追加 v2.6 之外的 7 条）

#### AC #24: Plugin 阶段 1 deterministic 全流程
- [x] 新增 `frontend/obsidian-plugin/src/node-derivation.ts` 含 9 个纯函数（启发式提取 / 重名 / frontmatter 构造 / placeholder 正文 / wikilink+callout / 白板行 / Skill prompt）
- [x] `handleAILinkedDoc` 重写为 `runHybridDerivation`：阶段 1 全部 plugin script 完成
- [x] 所有 vault 写操作用 obsidian 官方 API：`vault.create()` / `processFrontMatter()` / `editor.replaceSelection()` / `vault.modify()`（避免 YAML 转义坑）
- [x] frontmatter 写入 status: ai_pending（白板 dataviewjs 用此过滤）

#### AC #25: 启发式概念名提取（无 LLM）
- [x] 中文：取前 2-40 个汉字，按句号 / 标点 / 换行截断
- [x] 英文：取前 1 句 → kebab-case
- [x] 非法字符 `/ \ : * ? " < > | # ^ [ ]` 自动清除
- [x] 全失败 → fallback `derived-<6 位 timestamp>`
- [x] 重名（节点池已有同名）→ 自动 `_2 / _3 / ... / _9`，9+ 抛错

#### AC #26: Skill v5.0 极简（仅 2 步）
- [x] 新建 `canvas-vault/.claude/skills/ai-linked-doc-fill/SKILL.md`
- [x] 触发命令：`/ai-linked-doc-fill`（与 v4.5 `/ai-linked-doc` 区分）
- [x] 8 条硬约束：不 Glob 白板 / 不读 yaml / 不用 AskUserQuestion / 不改源笔记 / 不改白板 / 不重写 frontmatter / 唯一替换 placeholder / 必返 2 行回执
- [x] Step 1: Read 节点 md + 验证 AI_BODY_PLACEHOLDER 标记存在
- [x] Step 2: 生成 3 段正文 + Edit 替换 placeholder + 改 status

#### AC #27: 失败恢复 (partial commit + 无 rollback)
- [ ] 阶段 1 任一步骤失败 → Notice 报错 + 不回滚（已 commit 的 artifact 保留）
- [ ] 阶段 2 失败 → 节点 md 保持 status: ai_pending + placeholder body + 用户可手动重跑 `/ai-linked-doc-fill <concept>`
- [ ] 复用 v2.2 `showRetryNotice` 处理剪贴板 / Claudian 失败的重试

#### AC #28: 白板 ## Concepts 行格式 + status 标记
- [x] 阶段 1 append: `- [[节点/<concept>]] — <relation_key>, weak (0.30) ⏳ ai_pending`
- [ ] 阶段 2 完成后**不**自动改这一行（用户后续看 dataviewjs 用 frontmatter status 过滤）
- [x] ## Recent Activity append 格式: `- <ISO>: Extracted [[节点/<concept>]] via /ai-linked-doc from [[<source>]]（关系: <key>, status: ai_pending）`

#### AC #29: 阶段 1 性能要求
- [ ] vault.create + processFrontMatter + editor.replaceSelection + 白板 modify 总耗时 < 200ms（实测打 Notice 显示用时）
- [ ] 失败时不阻塞超过 500ms（避免 UI freeze）

#### AC #30: 兼容性 — v4.5 ai-linked-doc 保留为 fallback
- [x] `.claude/skills/ai-linked-doc/SKILL.md` v4.5 不删，作 fallback
- [x] v3.0 plugin 写剪贴板触发 `/ai-linked-doc-fill`（v5.0），不再触发 `/ai-linked-doc`（v4.5）
- [x] 用户如手动调 `/ai-linked-doc` 仍能跑 v4.5 全流程

### File List (v3.0 增量)
- **NEW** `frontend/obsidian-plugin/src/node-derivation.ts` — 252 行，9 个纯函数 + 1 个常量
- **MOD** `frontend/obsidian-plugin/src/main.ts` — 重写 `handleAILinkedDoc` → `runHybridDerivation`；新增 `appendBoardLines` helper；新增 `retrySkillTrigger`；移除 v2.6 `continueAILinkedDoc` 的 `buildAIDocPrompt` 调用
- **NEW** `frontend/obsidian-plugin/tests/node-derivation.test.ts` — 34 个 v3.0 测试（启发式 / 重名 / 关系映射 / 模板构造 / Phase2 prompt）
- **MOD** `frontend/obsidian-plugin/package.json` — test 脚本加 node-derivation.test.ts
- **NEW** `canvas-vault/.claude/skills/ai-linked-doc-fill/SKILL.md` — v5.0 极简 Skill，2 步流程
- **MOD** `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` — build 31768B（v2.6 20348B，+11420B = node-derivation 模块）

### Change Log (v3.0)
- 2026-04-30 v3.0 — 用户在 v2.6 ship 后立即提出 hybrid 架构需求："脚本程序就可以，没必要用 skill"。3 并行 Explore agent + 1 技术验证 agent 调研：v3 完全可行，社区主流（Note Refactor / Templater / Obsidian Copilot）= hybrid 模式；plugin 用 vault.create + processFrontMatter + editor.replaceSelection 全脚本化；Skill 瘦身到 v5.0 仅 2 步（生成正文 + Edit 替换）。Plugin 节点派生 7 步 deterministic 全本地化，<100ms 见骨架；Skill 异步填正文，用户不再阻塞。75 单元测试 green（41 base + 34 v3.0 新增）。main.js 20348B → 31768B。Plan: `/Users/Heishing/.claude/plans/swift-mapping-alpaca.md` v3 hybrid 落地 2026-04-30。
