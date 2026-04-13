---
doc_type: story
story_id: "1.5"
aliases: ["1.5"]
epic_id: "EPIC-1"
prd_id: "PRD14"
status: ready-for-dev
priority: "P2"
estimate_hours: 2
depends_on: []
blocks: []
trace:
  decisions: []
  bugs: []
---
# Story 1.5: Obsidian Git 自动备份

## Story

As a 学习者,
I want 选择性启用 Obsidian Git 自动备份,
So that 我的学习数据可以自动同步到 Git 仓库，防止丢失。

## Acceptance Criteria

1. **Given** 学习者安装了 Obsidian Git 插件并在 Settings 中启用自动备份
   **When** 配置间隔到达（默认 30 分钟）
   **Then** Obsidian Git 自动执行 commit + push
   **And** 备份过程在后台异步执行，不打断学习者操作

2. **Given** 学习者未安装或未启用 Obsidian Git 插件
   **When** 系统正常运行（对话、出题、评分等所有功能）
   **Then** 系统不因缺少 Git 备份而报错、降级或弹出警告
   **And** 所有核心功能保持完整可用

## Tasks / Subtasks

- [ ] Task 1: 编写 Obsidian Git 配置指南文档 (AC: #1)
  - [ ] 1.1 在 `vault/_meta/obsidian-git-setup.md` 创建配置说明文件
  - [ ] 1.2 说明安装步骤：Obsidian → Settings → Community plugins → Browse → 搜索 "Obsidian Git" → Install → Enable
  - [ ] 1.3 说明推荐配置：Auto backup interval = 30 min，Disable notifications = true（避免打断学习），Commit message = "auto-backup: {{date}}"
  - [ ] 1.4 说明前置条件：vault 目录已是 git repo，已配置远端 remote（GitHub / Gitea 等），SSH key 或 HTTPS token 已就位

- [ ] Task 2: 验证系统对 Obsidian Git 缺失的容错行为 (AC: #2)
  - [ ] 2.1 确认后端所有 API endpoint 不依赖 Git 状态（grep backend/ 不含 git commit / git push 调用）
  - [ ] 2.2 确认前端 Skill 脚本不调用 git 相关命令
  - [ ] 2.3 确认 health check (`/api/v1/health`) 不将 Obsidian Git 列为必检服务
  - [ ] 2.4 在无 Obsidian Git 的干净 vault 环境下，手动验证核心旅程（对话/检验/Dashboard）可正常运行

- [ ] Task 3: 编写 .gitignore 推荐规则文档 (AC: #1)
  - [ ] 3.1 在配置指南中附上推荐的 vault `.gitignore` 内容
  - [ ] 3.2 排除项：`.obsidian/workspace.json`（含窗口状态，频繁变更无意义），`.trash/`，`*.tmp`
  - [ ] 3.3 保留项：`.obsidian/plugins/`（插件配置），`.obsidian/snippets/`，所有 `.md` 文件，`_templates/`

## Dev Notes

- **Canvas 不拥有 Obsidian Git 插件**：Obsidian Git 是由 Vinadon 维护的社区插件（GitHub: denolehov/obsidian-git），版本 2.x。Canvas 系统不打包、不修改该插件，只需要不与之冲突。
- **无代码实现**：这个 Story 主要是文档 + 验证容错行为。不需要写后端代码，不需要前端改动。
- **异步执行由插件保证**：Obsidian Git 2.x 的 auto backup 通过 Obsidian 的 `setTimeout` 事件循环执行，不阻塞编辑器主线程。Canvas 无需额外处理。
- **冲突风险**：Obsidian Git 在 commit 期间会短暂锁定 vault 文件系统（< 1 秒）。Canvas 的 LanceDB 增量索引（实时文件保存触发）可能在极低概率下与 git lock 碰撞。实测未观察到问题，暂不处理；如后续出现 `EBUSY` 错误则记录为 bug。
- **不在 MVP 核心路径上**：FR39 标注为 P2，可选功能。不影响旅程 1-5 的主链路。

### Project Structure Notes

- 新增文档：`vault/_meta/obsidian-git-setup.md`（在 vault 内，供学习者在 Obsidian 中直接阅读）
- 不涉及后端代码改动
- 不涉及前端代码改动
- 不需要新增测试文件（验证步骤为手动确认）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.5] — Story 原始 AC 和 FR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#Update-Strategy] — "Obsidian vault 数据: Obsidian Git 插件可选自动备份"
- [Source: _bmad-output/planning-artifacts/prd.md#FR39] — FR39: 学习者可以选择性启用 Obsidian Git 自动备份
- [External: https://github.com/denolehov/obsidian-git] — Obsidian Git 社区插件官方仓库

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证有 Obsidian Git 时的自动备份** (AC: #1)
   - 在 Obsidian 中打开 Settings → Community plugins → 确认 "Obsidian Git" 已启用
   - 打开 Obsidian Git 插件设置，将 "Auto backup interval (minutes)" 设为 1（测试用）
   - 在任意笔记中随意写几个字，然后等待约 1 分 30 秒
   - 打开命令面板（Ctrl/Cmd+P），搜索 "Obsidian Git: Open source control view"，点击
   - 在右侧 Source Control 面板中，应该看到最近有一条 commit 记录（包含 "auto-backup" 字样）
   - 验证完成后，将 Auto backup interval 改回 30 分钟
   - 如果没看到 commit 记录，记录 Story 1.5 和具体现象

2. **验证没有 Obsidian Git 时系统正常** (AC: #2)
   - 在 Obsidian Settings → Community plugins 中，临时**禁用** Obsidian Git（点击 toggle 关闭）
   - 正常使用系统：打开一个笔记，启动 Claudian 对话，说一句话并等待回复
   - 系统应该正常回复，不出现任何错误弹窗或"Git 不可用"提示
   - 测试完成后，重新启用 Obsidian Git
   - 如果看到任何 Git 相关错误，记录 Story 1.5 和错误弹窗内容

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.5.1 | grep | `grep -r "git commit\|git push\|subprocess.*git" backend/app/ --include="*.py"` | 0 matches（无 git 调用） |
| CP-1.5.2 | grep | `grep -r "git commit\|git push\|execSync.*git" frontend/src/ --include="*.ts" --include="*.tsx"` | 0 matches（无 git 调用） |
| CP-1.5.3 | manual | 禁用 Obsidian Git 后访问 `http://localhost:8001/api/v1/health` | 返回 200，无 git_backup 字段或字段非 required |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

- `vault/_meta/obsidian-git-setup.md` (new — configuration guide)

## Relations

- EPIC: [[EPIC-1]]
- PRD: [[PRD14]]
