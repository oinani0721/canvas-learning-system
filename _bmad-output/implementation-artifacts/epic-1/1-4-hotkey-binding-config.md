---
story_id: "1.4"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["1.1"]
blocks: ["1.5"]
trace:
  - "FR-SYS-02"
---

# Story 1.4: Hotkey 绑定配置

Status: ready-for-dev

## Story

As a 学习者,
I want 为 6 个 Skill 配置自定义快捷键,
So that 我可以通过键盘快速触发学习操作而无需鼠标点击菜单。

## Acceptance Criteria

1. **Given** 学习者打开 Obsidian Hotkeys 设置面板
   **When** 搜索 "Canvas" 或 "学习"
   **Then** 显示核心 Hotkey 命令（中文名称）：
   - **批注插入类**（核心刚需 Hotkey）：
     - 插入 Tip 批注（insert-tip-callout）— 快速插入 `> [!tip]+ `
     - 插入 Question 批注（insert-question-callout）— 快速插入 `> [!question]+ `
     - 插入 Fail 批注（insert-fail-callout）— 快速插入 `> [!fail]+ `
   - **节点提取类**（核心刚需 Hotkey）：
     - 提取概念节点（extract-concept）— 选中文本 → 创建独立 concept.md + wikilink 回引
   - **Skill 命令类**（通过 Claudian `/` 命令调用，Hotkey 为可选快捷方式）：
     - /chat_with_context、/start_exam_board、/edge_discuss、/review_profile 等
   **And** 每个命令旁显示可绑定热键的空白位

2. **Given** 学习者为某个 Hotkey 命令绑定了快捷键
   **When** 在 Obsidian 任何 UI 区域按下该快捷键
   > User：我刚需 hotkey 是方便打批注和方便我提取节点（然后关于我自己构建的节点图谱以及我打的批注如何管理，这是 claudian 所要关注的重点）来然后用双向链接来连接；你这里提到的 skill 完全是我可以使用/命令来调出来对话的
   **Then** 对应命令被触发执行（批注插入类为纯前端操作，节点提取类调用后端）
   **And** 响应不限于特定面板（全局响应）
   **And** Claudian 负责管理用户的批注（Tips/Errors）和节点图谱（concept.md + relationships[]），这是其核心职责

**User：关于当前的一个问题，我的批注绝对是我使用原白板的过程中绝对的精华，但是有一个问题我们现在 md 文档为节点了，那么原白板的类型是什么？是文件夹，还是一个随时可以更新的 index 文档；第二，检验白板的生成需要阅读原白板的内容，其中特别重要的就是节点内容上的个人批注，各个节点之间为什么要链接起来，以及如果在原白板过程 中是解题的话，那么还有记录的解题错误以及混淆知识点，这里就有一个问题，那么在生成检验白板考察的时候，请问如何精准的检索这些，然后组装起来进行了一个有效的考察**
3. **Given** 插件首次安装
   **When** 查看 Hotkeys 设置
   **Then** 所有命令均无默认快捷键（用户自行绑定）
   **And** 命令说明文案清晰描述每个命令的功能，区分"批注 Hotkey"和"Skill /命令"

4. **Given** 学习者触发一个 Skill 命令
   **When** 后端未启动或不可用
   **Then** 显示友好错误提示（"后端未连接，请先启动 Canvas 后端"）
   **And** 不会导致 Obsidian 崩溃

## Tasks / Subtasks

- [ ] Task 1: 注册 6 个 Obsidian 命令 (AC: #1, #3)
  - [ ] 1.1: 在 Claudian 插件主文件中，`onload()` 方法里使用 `this.addCommand()` 注册 6 个命令
  - [ ] 1.2: 每个命令的 `id` 使用 kebab-case：`canvas:start-dialog` · `canvas:start-examination` · `canvas:extract-concept` · `canvas:quiz-from-callout` · `canvas:open-dashboard` · `canvas:open-review-queue`
  - [ ] 1.3: 每个命令的 `name` 使用中文：`Canvas: 启动学习对话` · `Canvas: 启动考察` · `Canvas: 提取概念` · `Canvas: 批注考察` · `Canvas: 打开仪表盘` · `Canvas: 打开复习队列`
  - [ ] 1.4: 不设置 `hotkeys` 属性（无默认绑定，由用户在 Settings > Hotkeys 自行配置）

- [ ] Task 2: 命令回调实现 (AC: #2)
  - [ ] 2.1: 每个命令的 `callback` 调用统一的 `executeSkill(skillName: string)` 方法
  - [ ] 2.2: `executeSkill` 向后端发送 `POST /api/v1/skills/{skill_name}/execute` 请求
  - [ ] 2.3: 传递当前活动文件路径（`this.app.workspace.getActiveFile()?.path`）作为上下文参数
  - [ ] 2.4: 命令使用 `editorCallback` 或 `callback` 确保全局响应（不仅限于 editor 模式）

- [ ] Task 3: 后端连接检测与错误处理 (AC: #4)
  - [ ] 3.1: `executeSkill` 执行前先 ping `GET /api/v1/ping`（已有 endpoint）
  - [ ] 3.2: ping 失败时显示 `new Notice("后端未连接，请先启动 Canvas 后端", 5000)`
  - [ ] 3.3: 请求超时（5s）或 HTTP 错误时显示具体错误信息
  - [ ] 3.4: 所有网络异常 catch 并显示 Notice，不抛未捕获异常

- [ ] Task 4: Skill 路由 endpoint (AC: #2)
  - [ ] 4.1: 在 `backend/app/api/v1/endpoints/skills.py` 中确认或新增 `POST /api/v1/skills/{skill_name}/execute`
  - [ ] 4.2: 请求体包含 `{active_file: str, vault_path: str}`
  - [ ] 4.3: 路由到 `backend/app/services/skill_registry.py` 的对应 handler
  - [ ] 4.4: 未实现的 Skill 返回 `501 Not Implemented` + 友好消息

- [ ] Task 5: 测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1: `backend/tests/unit/test_skill_routing.py` — 6 个 Skill 路由正确分发、未实现 Skill 返回 501
  - [ ] 5.2: 手动验证：Obsidian Settings > Hotkeys 中搜索 "Canvas" 能看到 6 条命令

## Dev Notes

- **Obsidian Plugin API**: `this.addCommand({ id, name, callback })` 是标准 API。`id` 必须唯一且稳定（不要改），`name` 是用户可见的显示名
- **全局 vs Editor**: 使用 `callback`（无条件全局触发）而非 `editorCallback`（仅编辑器焦点时触发），确保从任何面板都能响应
- **无默认 hotkey**: PRD 明确要求不设默认快捷键（FR-SYS-02），避免与用户已有绑定冲突
- **Claudian 插件**: 这是项目的 Obsidian 插件入口点，命令注册在 `onload()` 生命周期
- **后端 skill_registry**: `backend/app/services/skill_registry.py` 已有 Skill 注册框架，需确认 6 个 Skill 的 handler 映射
- **Notice API**: Obsidian 的 `new Notice(message, duration_ms)` 显示临时通知条
- **原白板类型定义**: 原白板 = `wiki/canvases/` 下的 **index .md 文档**，用 `[[wikilinks]]` 链接到 concept 节点。不是文件夹，而是一个随时可更新的 index 文档
- **考察精准检索流程**（FR-EXAM-03 三路融合）：
  1. 解析原白板 index.md 的所有 `[[wikilinks]]` → 找到关联的 concept.md
  2. 遍历每个 concept.md 读取：frontmatter（mastery/errors/tips）+ 正文 callout 批注（`[!tip]+` / `[!question]+` / `[!fail]+`）
  3. 查询 Graphiti 个人记忆（历史错误、混淆点、讨论记录）
  4. 查询 Graphify 概念关系（71x 压缩检索）
  5. 组装 ACP（Assessment Context Package）→ `generate_question` MCP 出题

### Project Structure Notes

- 修改文件：Claudian 插件主文件（`onload()` 中注册命令）
- 修改文件：`backend/app/api/v1/endpoints/skills.py`（确认路由）
- 修改文件：`backend/app/services/skill_registry.py`（确认 handler 映射）
- 测试文件：`backend/tests/unit/test_skill_routing.py`

### References

- [Source: _bmad-output/planning-artifacts/prd.md#FR-SYS-02] — 学习者可以自定义所有 Skill 的 hotkey 绑定
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.4] — AC 原文
- [Source: backend/app/services/skill_registry.py] — 现有 Skill 注册框架
- [Source: backend/app/api/v1/endpoints/skills.py] — 现有 Skills endpoint
- [Source: backend/app/api/v1/endpoints/ping.py] — 现有 ping endpoint

## UAT Script

> 非技术用户验收脚本

1. **验证命令注册** (AC: #1)
   - 打开 Obsidian，进入 Settings（齿轮图标）> Hotkeys
   - 在搜索框输入 "Canvas"
   - 应该看到 6 条命令，每条都有中文名称（启动学习对话、启动考察、提取概念、批注考察、打开仪表盘、打开复习队列）
   - 每条命令旁边应该有一个空白的快捷键位可以点击绑定

2. **验证快捷键绑定** (AC: #2)
   - 为 "启动学习对话" 绑定一个快捷键（如 Cmd+Option+C）
   - 在 Obsidian 任意页面按下该快捷键
   - 如果后端已启动，应该触发学习对话功能
   - 如果后端未启动，应该看到提示 "后端未连接"

3. **验证无默认绑定** (AC: #3)
   - 首次安装插件后，6 条命令都不应该有预设的快捷键

4. **验证错误处理** (AC: #4)
   - 关闭后端服务
   - 按已绑定的快捷键
   - 应该看到友好的错误提示，Obsidian 不会崩溃

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.4.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_skill_routing.py -x -q` | 0 failed |
| CP-1.4.2 | ruff | `ruff check backend/app/api/v1/endpoints/skills.py backend/app/services/skill_registry.py` | exit 0 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**批注处理记录 (2026-04-13)**
1. **Hotkey 聚焦** (User line 38): 用户刚需是批注（callout）+ 节点提取。Skill 通过 /命令调用。Claudian 重点是管理批注和节点图谱。已调整 AC 聚焦方向。
2. **N4: 原白板类型 + 考察检索** (User line 46): 原白板 = `wiki/canvases/` 下的 **index .md 文档**（用 wikilinks 链接 concept 节点，非文件夹）。考察检索采用 5 步三路融合流程（FR-EXAM-03）：(1) 解析 index.md 的 `[[wikilinks]]` → 找到关联 concept.md (2) 遍历每个 concept.md 读取 frontmatter（mastery/errors/tips）+ 正文 callout 批注 (3) 查询 Graphiti 个人记忆（历史错误、混淆点、讨论记录）(4) 查询 Graphify 概念关系（71x 压缩检索）(5) 组装 ACP（Assessment Context Package）→ `generate_question` MCP 出题。

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
