---
story_id: "1.19"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "in-progress"
priority: "P0"
estimate_hours: 8
depends_on: []
blocks: ["1.17","1.18"]
trace: ["FR-KG-08","FR-SYS-06","FR-DASH-01"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
revision: "v2-scope-extended-2026-04-20"
---

# Story 1.19: 原白板配置 Skill — 场景 A 新建 + 场景 B 从任意 md 派生

**Epic**: 1 — 基础设施 + Obsidian 插件命令
**Status**: in-progress (v2 scope 扩展 2026-04-20；因 1.17 UAT 批注暴露用户实际使用链路)
**Plan**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**Priority**: **P0**（提升：Epic 1 第 1 个用户 onboarding 入口，blocks 1.17/1.18）
**Estimate**: ~8h（原 6h + 场景 B 扩展 2h）
**Dependency**: 无（独立 Skill）

> **2026-04-20 scope 扩展触发**：用户 UAT Story 1.17 v2.1 时批注"我现在有一个在任意文件夹的 md 文件那么我想要从这个文件开始生成原白板，请问我该如何操作？" + "双链提问节点的功能本身就是要在原白板里面使用的"。3 并行 agent 调研（见 `_bmad-output/research/`）确诊：Story 1.19 是"用户打开 Canvas 第一件事"的 onboarding 入口，必须先于 1.17/1.18 完成。v1 scope 只覆盖场景 A（从零建），v2 扩展场景 B（从任意 md 派生）回应用户诉求。

---

## Story

作为 学习者，
我想 通过 Claudian Skill 一键建立一个新原白板 — **要么从零创建**（场景 A），**要么从任意文件夹的现有笔记派生**（场景 B），Skill 自动创建文件夹 / 生成 index.md / 归类笔记 / 加 wikilink，
以便 首次打开 Canvas 能立即开始学习一个新主题，无需手动建文件夹/写 frontmatter/拷笔记。

## 两种场景

### 场景 A · 从零建白板（v1 已覆盖）

```
用户在 Claudian: /configure-whiteboard "Linear Algebra" "math240"
        ↓
Skill 验证两参数（缺则 AskUserQuestion 补）
        ↓
mkdir wiki/canvases/math240/
        ↓
创建 wiki/canvases/math240/index.md（Templater 化 + frontmatter 完整 schema）
        ↓
若当前笔记不在 wiki/canvases/ → move 到 wiki/canvases/math240/<filename>.md
        ↓
更新 frontmatter + append index.md wikilink
        ↓
返回: "✓ 原白板已建立"
```

### 场景 B · 从任意 md 派生（v2 新增 — 2026-04-20 用户诉求）

```
用户打开任意路径 md（例：vault 根的 "未命名.md"、raw/notes.md、外部拖入的）
        ↓
用户在 Claudian: /configure-whiteboard from [path]  或无参
        ↓
Skill 确定"种子笔记"（参数 path / 当前 activeFile / AskUserQuestion 问路径）
        ↓
Skill AskUserQuestion: "这个笔记要归属哪个原白板？"
        → 若已有白板：列现有 subject 列表让用户选
        → 若无或用户选 "新建" → 问新 subject 代码 + 板名
        ↓
Skill AskUserQuestion: "种子笔记要 move 还是 copy 到白板？"
        → 默认 move（避免重复笔记）
        → copy 适合想保留原位置的场景
        ↓
mkdir wiki/canvases/<subject>/（若不存在）
        ↓
创建或更新 wiki/canvases/<subject>/index.md
        ↓
move/copy <path> → wiki/canvases/<subject>/<basename>.md
        ↓
更新种子笔记 frontmatter: 加 subject 字段（若无）
        ↓
append 到 index.md 的 ## Concepts section
        ↓
返回: "✓ 原白板已从 [path] 派生，种子笔记已归入 wiki/canvases/<subject>/"
```

---

## Acceptance Criteria

### AC #1: Skill 注册 + 调用
- [ ] `.claude/skills/configure-whiteboard/SKILL.md` 存在
- [ ] Claudian 自动发现（vault-level skill）
- [ ] 用户输入 `/configure-whiteboard` 触发
- [ ] 支持 upfront 参数 `[name] [subject]`

### AC #2: 缺参数 → AskUserQuestion
- [ ] 若无参数 → 弹问 "请输入白板名称:"
- [ ] 然后弹问 "请输入学科代码:"
- [ ] 用户答完继续

### AC #3: 文件夹创建
- [ ] `mkdir -p wiki/canvases/<subject>/`
- [ ] subject 验证: lowercase + 数字 + 连字符
- [ ] 已存在 → 弹问 "重用还是改名"

### AC #4: index.md 模板化
- [ ] 读 `templates/index.md.template`
- [ ] 替换 `{{board_name}}` `{{subject}}` `{{created_at}}`
- [ ] 写 `wiki/canvases/<subject>/index.md`

### AC #5: 种子笔记归类（场景 A + B 共用）
- [ ] 若当前笔记不在 `wiki/canvases/` → mv 到新文件夹（场景 A 默认）
- [ ] 场景 B 显式路径：`from <md-path>` 子命令走这条路径
- [ ] 更新笔记 frontmatter `subject: <subject>`（无则加，有则覆盖）
- [ ] 在 index.md 的 `## Concepts` section append `- [[<filename-stem>]]`

### AC #6: 完成回执
- [ ] 场景 A 返回 `"✓ 原白板 <board_name> 已建立. 位置: wiki/canvases/<subject>/"`
- [ ] 场景 B 返回 `"✓ 原白板 <board_name> 已从 <source-path> 派生. 种子笔记已归入 wiki/canvases/<subject>/<basename>.md"`

### AC #7 (v2 新增): 场景 B 显式 `from` 子命令
- [ ] 支持 `/configure-whiteboard from <md-path>`（相对 vault 根或绝对路径）
- [ ] Skill 自动读源 md frontmatter `subject` 字段作为默认 subject 候选
- [ ] 若源路径不存在 → Notice `✗ 源笔记 <path> 不存在`
- [ ] 若源路径已在 `wiki/canvases/<existing-subject>/` → Notice `⚠ 该笔记已属于 <existing-subject> 白板，不执行派生`

### AC #8 (v2 新增): move vs copy 选择
- [ ] 场景 B 默认 `move`（避免重复笔记）
- [ ] Skill 通过 AskUserQuestion 让用户选：move（推荐，原位置文件删除）/ copy（保留原位置副本）
- [ ] move 成功 → 源 md 被删除；copy 成功 → 源 md 保留，vault 多一份副本

### AC #9 (v2 新增): subject 智能候选
- [ ] Skill 启动时 `Glob wiki/canvases/*/index.md` 枚举已有 subject（读 frontmatter `subject` 字段）
- [ ] AskUserQuestion 列已有 subject 作为选项 + "新建" 选项
- [ ] 若源 md 有 `subject` frontmatter → 预填该值为默认
- [ ] 选 "新建" → 追问 board_name + subject-code

---

## Tasks

- [ ] 创建 `.claude/skills/configure-whiteboard/SKILL.md`
- [ ] 创建 `templates/index.md.template`
- [ ] 实现 Bash 步骤（mkdir + sed 替换 + mv + yq frontmatter 更新）
- [ ] 实现 AskUserQuestion fallback
- [ ] 边界测试: 重名 / 已存在 / Templater 缺
- [ ] UAT 7 步

---

## SKILL.md 完整模板（120 行）

```markdown
---
name: configure-whiteboard
description: 创建新原白板 + 文件夹 + Templater index.md
argument-hint: "[whiteboard-name] [subject-code]"
allowed-tools: [Bash, Read, Write, Glob, AskUserQuestion]
---

配置一个新的原白板。

## 输入

两个参数:
- `[whiteboard-name]` 显示名 (e.g., "Linear Algebra")
- `[subject-code]` 文件夹代码 (e.g., "math240")

如缺，会用 AskUserQuestion 询问。

## 步骤

### 1. 解析参数

如 $ARGUMENTS 提供两个参数 → 直接用
如缺 → AskUserQuestion("请输入白板名称:") + AskUserQuestion("请输入学科代码:")

### 2. 验证

- board_name: 至少 2 字符
- subject: lowercase + 字母数字 + 连字符 (e.g., "math240", "cs-61b")
- 检查 wiki/canvases/$subject/ 是否存在 → 如已存在弹问

### 3. 创建文件夹

\`\`\`bash
mkdir -p "wiki/canvases/$subject"
\`\`\`

### 4. 替换模板变量

\`\`\`bash
created_at=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
sed -e "s|{{board_name}}|$board_name|g" \
    -e "s|{{subject}}|$subject|g" \
    -e "s|{{created_at}}|$created_at|g" \
  < .claude/skills/configure-whiteboard/templates/index.md.template \
  > "wiki/canvases/$subject/index.md"
\`\`\`

### 5. 处理当前笔记（可选）

如当前笔记不在 wiki/canvases/：
\`\`\`bash
mv "$current_note" "wiki/canvases/$subject/$(basename $current_note)"
\`\`\`

### 6. 更新移动后笔记 frontmatter

\`\`\`bash
yq -i '.subject = "'$subject'"' "wiki/canvases/$subject/$(basename $current_note)"
\`\`\`

或用 sed (如 yq 不可用):
\`\`\`bash
sed -i '' '/^type: /a\
subject: "'$subject'"' "wiki/canvases/$subject/$(basename $current_note)"
\`\`\`

### 7. Append wikilink 到 index.md

\`\`\`bash
echo "" >> "wiki/canvases/$subject/index.md"
echo "[[$(basename $current_note .md)]]" >> "wiki/canvases/$subject/index.md"
\`\`\`

### 8. 回复用户

\`\`\`
✓ 原白板已配置

📍 位置: wiki/canvases/$subject/index.md
📋 板名: $board_name
🏷️ 代码: $subject
📝 已关联: 1 笔记 (如适用)

下一步: 打开 index.md (Templater 会自动填充 concept 列表)
\`\`\`

## 错误处理

- 文件夹已存在 → 弹问 "重用还是改名"
- Templater 未装 → 创建静态 md + 警告
- 当前笔记已在 canvases/ → 跳过 mv，只更 frontmatter
- yq 未装 → 用 sed fallback
```

## index.md.template 完整模板

```markdown
---
type: whiteboard_index
board_name: "{{board_name}}"
subject: "{{subject}}"
created_at: "{{created_at}}"
doc_count: 0
doc_mastery_avg: 0
---

# {{board_name}}

<%* tp.user.populate_concepts(tp.frontmatter.subject) %>

## Concepts

## Theorems & Proofs

## Common Errors

## Relationship Graph

## Recent Activity
- {{created_at}} — Whiteboard created
```

---

## UAT (7 步)

1. **带参调用**: Claudian 输入 `/configure-whiteboard "Linear Algebra" "math240"`
2. **看文件夹**: vault 里 wiki/canvases/math240/ 出现
3. **看 index.md**: frontmatter board_name/subject/created_at 正确
4. **测试归类**: 当前笔记 raw/notes.md → 跑 skill → 移到 wiki/canvases/math240/notes.md
5. **看 wikilink**: index.md 含 `[[notes]]`
6. **测试缺参**: 跑 `/configure-whiteboard` (无参) → AskUserQuestion 弹两次
7. **测试冲突**: 重跑 → 弹 "重用还是改名"

---

## Pitfalls

| 症状 | 原因 | 修 |
|---|---|---|
| frontmatter 解析挂 | sed 处理多行 YAML 错 | 装 yq 用 yq |
| Wikilink 路径错 | 相对路径计算错 | 用 basename 不用全路径 |
| Templater 不执行 | 用户未装 plugin | 警告 + 静态 fallback |
| Race (并发跑两次) | 两个 mkdir 同时 | mkdir -p 幂等无问题 |

---

> [!question]+ 用户批注 - Story 3.6 spec
> SKILL.md + 模板是否符合预期？7 步 UAT 是否够？
> （批注区）

---

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1 | build | `cd frontend/obsidian-plugin && npm run build` | exit 0, main.js updated |
| CP-2 | deploy | `cp main.js canvas-vault/.obsidian/plugins/canvas-learning-system/` | file copied |
| CP-3 | reload | Manual: Obsidian Cmd+Shift+P → "Reload app" | no console error (F12) |
| CP-4 | UAT | Run "## UAT Script" steps | all steps pass |

## User Feedback & Changes

### Feedback Log
<!-- 用户在 Obsidian 跑 UAT 后批注 -->

### Deviation Notes
<!-- Dev agent 偏离 spec 时记录原因 -->

## Dev Agent Record

### Agent Model Used
<!-- to be filled by dev-story Skill -->

### Debug Log References
<!-- placeholder -->

### Completion Notes List
<!-- placeholder -->

### File List

<!-- dev-story Skill 实施后填充, e.g.:
- NEW: frontend/obsidian-plugin/src/modals/CalloutTypeModal.ts
- MOD: frontend/obsidian-plugin/src/main.ts (added canvas:annotate-callout)
-->
