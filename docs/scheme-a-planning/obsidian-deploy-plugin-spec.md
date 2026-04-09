---
title: Obsidian 一键部署插件设计 Spec
subtitle: Canvas Learning System Scheme A · Phase 1 §10.1 实现目标
status: Draft · Plan v25 实现 target
author: Plan v24 Part C2
date: 2026-04-09
scope: γ · 完整 Scheme A vault 模板部署
prerequisite: Plan v24 Part C1 已修复 Spike 3 hook scope 错位
deliverable-type: 架构 spec · 不含 TypeScript 源码
next-plan: Plan v25 Phase 1 §10.1 task 1-7
---

# Obsidian 一键部署插件设计 Spec

> 本文档是**设计 spec**·不是实现代码。实际 TypeScript 源码、`manifest.json` 结构、模板文件内容全部留给 Plan v25。
> 本文档的价值是**锁定 Plan v25 的实现目标**·避免 Plan v25 启动时再做架构决策。

---

## 1. Why · 为什么要这个插件

### 1.1 Scheme A 本质是 runtime / vault 解耦

Scheme A（Claudian + Obsidian 降级架构）把系统拆成两层：

- **Canvas runtime**（不变层）：`canvas-learning-system/` 主 repo · 包含 backend 15 MCP 工具 + `frontend/sidecar/sidecar.js` + LanceDB + Neo4j + SQLite + cost_tracker 等。**部署一次·长期运行·所有 vault 共享**。
- **Obsidian vault**（可替换层）：一个独立的 Obsidian 目录 · 包含 `wiki/` 笔记 · `exam_boards/` 考察白板 · `discussions/` 讨论 · `.claude/` hook + skill 骨架 · `CLAUDE.md` 铁律等。**每个 vault 是一个独立"学习空间"**。

用户今天在 CS188 vault 学 AI · 明天起 CS189 vault 学 ML · 后天起 CS294 vault 学 quantum computing —— 三个 vault 各自独立 · 但都跑在**同一个** Canvas runtime 上 · 共用底层数据库和 MCP 工具。

这个架构的威力在于 **"加一个新学科就新起一个 vault · 不用动后端"**。但威力的前提是 vault 初始化必须**快、对、可复现**。

### 1.2 手动部署的痛点

PRD §4.7.4 Step 5 规定的 vault 初始化是 8 步手动操作：

1. 创建完整目录树（§3.1 的 `wiki/` · `exam_boards/` · `discussions/` · `edges/` · `scripts/` · `.claude/` · `.obsidian/`）
2. 写 `CLAUDE.md`（§4 的 6 条铁律）
3. 写 4 层 hook 脚本（§4.7.3 Layer 1-4 · Node.js + Bash 混合）
4. 写 `.claude/settings.json`（声明 4 层 hook）
5. 写 6 个 skill 骨架目录（§10.1 task 1-7）
6. 运行 `graphify install`（§6 可选）
7. 验证 backend 健康（§2.4 · `curl http://localhost:8000/docs`）
8. 触发初次 LanceDB 索引（§2.5 · `POST /api/v1/metadata/index/vault`）

**每次起新 vault 都跑一遍** = 重复劳动 + 高错误率。

### 1.3 Part C1 是插件必要性的反向证据

Plan v24 Part C1 手动修复了 Spike 3 的 hook 错位（把 UserPromptSubmit 从 global `~/.claude/` 搬到 vault-scoped `CS188/.claude/`）· 这只是**上面 8 步里 Step 4 的一小部分** · 但已经花了 6 个原子操作（rollback / mkdir / cp / edit / write / dry-run）+ 完整的验证清单。

按统计学 · 只要手动部署 · 就会有 L5-#8 这类 scope 错位事件。插件 = **把手动降到零** = 彻底消灭这类错误的唯一方法。**插件的成熟度 = Scheme A 架构的成熟度**。

---

## 2. What · 插件部署的 17 项 deliverable

按 PRD section 映射到可部署 artifact（γ scope）：

| # | PRD ref | 部署内容 | 类型 | 幂等策略 |
|---|---|---|---|---|
| 1 | §3.1 | 完整目录树（7 个一级子目录 + README 模板） | 目录 + md | 已存在跳过 |
| 2 | §3.2 | frontmatter schema 示例 `.md` 模板 | 每目录 1 个模板 | 已存在跳过 |
| 3 | §4 | `CLAUDE.md` 6 条铁律 | 单文件 | 备份后覆盖·用户可拒绝 |
| 4 | §4.7.3 L1 | `.claude/hooks/session-start-intent-rules.js` | Node.js hook | 备份后覆盖 |
| 5 | §4.7.3 L2 | `.claude/hooks/user-prompt-submit.js`（意图路由 → skill 建议） | Node.js hook | **替换** Part C1 的 bash logger |
| 6 | §4.7.3 L3 | `.claude/hooks/pretool-exam-board-isolation.js` | Node.js hook | 备份后覆盖 |
| 7 | §4.7.3 L4 | `.claude/hooks/stop-auto-archive-to-graphiti.sh` | Bash hook | 备份后覆盖 |
| 8 | §4.7.4 Step5 | `.claude/settings.json`（声明 4 层 hook 全部） | JSON | **merge** 不覆盖 `settings.local.json` |
| 9-14 | §10.1 t1-6 | `.claude/skills/{start_exam_board,ask_for_hint,report_mastery,review_error_log,generate_discussion,archive_session}/` | skill 骨架目录 | 已存在跳过 |
| 15 | §6 | Graphify CLI `graphify install`（可选） | CLI 调用 | CLI 不在 PATH 则跳过 |
| 16 | §2.4 | Canvas backend 健康检查（`GET /docs`） | HTTP GET | 失败则弹 notice 提示先启 backend |
| 17 | §2.5 | 初始 LanceDB 索引触发（`POST /api/v1/metadata/index/vault`） | HTTP POST | backend 不可达时跳过 |

**注意 #5**：Layer 2 hook 是 **真功能性替换** —— Part C1 的 bash logger 只是 wiring 验证 · 插件会用 PRD §4.7.3 Layer 2 的完整 Node.js intent router 把它覆盖。这是**正常演化**·不是浪费。

---

## 3. How · 插件 UX 设计

### 3.1 命令集（Obsidian Command Palette）

| 命令 | 作用 |
|---|---|
| `Canvas: Deploy Learning Infrastructure to This Vault` | 主命令·执行 17 项 deliverable |
| `Canvas: Verify Current Vault Setup` | 检测已装部分·报 missing items |
| `Canvas: Update Templates` | 把新版本模板 diff 到现有 vault（保留用户笔记） |
| `Canvas: Switch Active Vault` | 切换 `backend/.env` `CANVAS_BASE_PATH` 指向当前 Obsidian 打开的 vault |

### 3.2 交互式 vault 选择（Plan v24 用户明确要求的关键 UX）

主命令触发后弹 modal：

1. **候选来源**（3 层优先级）：
   - 层 1：当前打开的 vault（高亮 · 默认勾选 · `app.vault.adapter.getBasePath()`）
   - 层 2：Obsidian 其他已注册 vault（读 `~/Library/Application Support/obsidian/obsidian.json` 的 `vaults` 字段）
   - 层 3：磁盘扫描 `~/Desktop/` 递归深度 2 层·检测含 `.obsidian/` 子目录的路径
2. **UI 形式**：checkbox 列表 + 搜索框 + "Add custom path" 按钮（支持 vault 不在预期位置）
3. **选完后 → dry-run preview**：弹对话框列出将要创建 / 修改的完整文件树·每个文件标注 `[new]` / `[overwrite]` / `[merge]` / `[skip]`·用户 Confirm → 开始部署·Cancel → 回到 modal

### 3.3 幂等行为规则（保护用户数据）

| 现有状态 | 行为 |
|---|---|
| 整个 `.claude/` 不存在 | 全新创建 |
| `.claude/settings.local.json` 存在 | **强保护** · 不覆盖 · 新 `settings.json` 独立创建 |
| `.claude/settings.json` 存在·用户未改过 | 备份后覆盖（对比模板 md5 判断） |
| `.claude/settings.json` 存在·用户改过 | 三路 merge（弹 diff UI 让用户选 accept / reject / edit） |
| `CLAUDE.md` 存在 | 备份后覆盖·弹 notice 允许用户拒绝 |
| `wiki/*.md` 有用户笔记 | **极强保护**·完全不动用户 `.md`·只补 README 模板 |
| `.claude/hooks/*` 存在 | 备份后覆盖（插件是 hooks 的 source of truth） |
| `.claude/skills/*` 骨架存在 | 比较 timestamp·只更新骨架文件·不动用户自定义 |

### 3.4 进度显示 + 日志

- 17 项 deliverable 每完成 1 项 → Obsidian notice 显示进度（`[5/17] Installing CLAUDE.md...`）
- 全部写到 `<vault>/.canvas-deploy.log`（第一次 deployment 时才创建·可 gitignore）
- 错误显示 notice + 完整 stack trace 写到 log
- 完成后 notice：`✅ Deployment complete. Open Claudian tab to start.`

### 3.5 完成后 action

- 提示用户：`Please reload Claudian plugin to pick up new skills`
- 若 Claudian 已装 → 尝试调用其 `Claudian: Reload` 命令自动触发
- 若 Claudian 未装 → notice 提示 `Install Claudian from [YishenTu/claudian] first`

---

## 4. 插件技术栈

| 领域 | 选型 | 备注 |
|---|---|---|
| 语言 | TypeScript | 标准 Obsidian 插件栈 |
| API | `obsidian` npm 包 | `App` · `Plugin` · `Vault` · `Modal` · `Notice` · `Command` |
| 构建 | esbuild | 参考 `obsidian-sample-plugin` 模板 |
| 清单 | `manifest.json` | 标准 Obsidian 格式（id / name / version / minAppVersion） |
| 文件操作 | Node.js `fs/promises` + Obsidian `vault.adapter` | `adapter` 用于 vault 内·`fs` 用于 vault 外（扫磁盘） |
| HTTP | `fetch`（Node.js 内置） | 用于 backend 健康检查 + LanceDB 索引触发 |
| 模板 | 编译期嵌入（esbuild `loader: { '.md': 'text' }` 或 string literal） | 模板位于 `src/templates/`·构建时打包进 `main.js` |
| 安装方式 | 开发：BRAT plugin 加载本地·生产：Canvas repo `obsidian-plugins/` 子目录 | 不一定走 Obsidian community registry（Scheme A 是私有架构） |

---

## 5. 插件源码目录结构（Plan v25 实现 target）

```
canvas-learning-system/
└── obsidian-plugins/
    └── canvas-deployer/
        ├── manifest.json                # 插件元信息
        ├── package.json                 # 依赖声明（obsidian · esbuild）
        ├── tsconfig.json                # TypeScript 编译配置
        ├── esbuild.config.mjs           # 构建脚本
        ├── main.ts                      # 插件入口·registerCommands()
        ├── src/
        │   ├── commands/
        │   │   ├── deploy.ts             # `Canvas: Deploy ...`
        │   │   ├── verify.ts             # `Canvas: Verify ...`
        │   │   ├── update.ts             # `Canvas: Update ...`
        │   │   └── switch.ts             # `Canvas: Switch ...`
        │   ├── modals/
        │   │   ├── vault-picker.ts       # 3 层候选 + 磁盘扫描
        │   │   └── dry-run-preview.ts    # 文件树 + 标注 UI
        │   ├── installers/
        │   │   ├── directory-tree.ts     # §3.1 目录创建
        │   │   ├── claude-md.ts          # §4 CLAUDE.md
        │   │   ├── hooks.ts              # §4.7.3 Layer 1-4
        │   │   ├── settings-json.ts      # §4.7.4 Step 5（含 merge）
        │   │   ├── skills.ts             # §10.1 6 skill 骨架
        │   │   ├── graphify.ts           # §6 Graphify CLI
        │   │   ├── backend-check.ts      # §2.4 健康检查
        │   │   └── lancedb-index.ts      # §2.5 初始索引
        │   ├── templates/                # 编译期嵌入
        │   │   ├── CLAUDE.md
        │   │   ├── settings.json
        │   │   ├── hooks/ (4 files)
        │   │   ├── skills/ (6 dirs)
        │   │   └── wiki-readme.md
        │   ├── utils/
        │   │   ├── backup.ts             # 统一 .bak.<ts> 生成
        │   │   ├── merge.ts              # 三路 JSON merge
        │   │   └── disk-scan.ts          # 磁盘扫描 vault 候选
        │   └── types.ts                  # 插件内部类型
        └── README.md                     # 用户文档
```

**注意**：这只是目录结构 + 文件命名·不含 TypeScript 实现。每个 `.ts` 文件是 Plan v25 的独立实现任务。

---

## 6. 与 Plan v24 Part C1 的演化关系

### 6.1 Part C1 的定位（手动、一次性）

Part C1 手动把 Spike 3 的 bash logger 从 `~/.claude/` 搬到 `CS188/.claude/hooks/user-prompt-hook.sh` · 保持脚本语义不变（仍是 wiring 验证 · 往日志追加一行）· 仅修 scope。

### 6.2 Part C2（本 spec）的定位（可复用、自动化）

Part C2 定义的插件是**可复用的自动化工具** · 一次实现后可以装到任何 vault（CS188 / CS189 / 未来新建的 CS294 等）· 不再需要任何手动操作。

### 6.3 演化路径（Plan v25 启动后的第一次运行）

1. 用户在 Obsidian 打开 CS188 vault · 运行 `Canvas: Deploy Learning Infrastructure`
2. 插件 verify 检测到：
   - ✅ `.claude/hooks/user-prompt-hook.sh` 已存在（Part C1 的 bash logger · 1 层 hook）
   - ✅ `.claude/settings.json` 已存在（Part C1 的 minimal config · 只声明 1 层）
   - ✅ `.claude/settings.local.json` 已存在（用户原本的 permissions + outputStyle）
   - ❌ 其他 15 项 deliverable 全部 missing（目录树 · CLAUDE.md · 3 层其他 hook · 6 skill 骨架 · 等）
3. 插件弹 dry-run preview：
   - `[overwrite]` `.claude/hooks/user-prompt-hook.sh` → 替换为 PRD §4.7.3 Layer 2 的 `user-prompt-submit.js`（Node.js intent router · 功能远超 bash logger）
   - `[merge]` `.claude/settings.json` → 从 1 层 hook 扩展到 4 层 hook
   - `[skip]` `.claude/settings.local.json` → 保持不动（强保护规则）
   - `[new]` 其余 15 项
4. 用户 Confirm → 插件执行 17 项部署
5. 结果：CS188 vault 从"部分装好（Part C1 · 1 层 hook wiring）"升级到"完整 Scheme A（Part C2 插件 · 4 层 hook + 6 skill + 8 目录 + CLAUDE.md + Graphify 等）"

### 6.4 为什么演化路径不是浪费

- Part C1 让 Spike 3 **立即闭合** · 不阻塞 Plan v25 启动 · 给了时间空间先写 spec
- Part C2 的 spec **锁定 Plan v25 实现目标** · Plan v25 启动时不需要再做架构决策
- 两者 handoff 清晰：Part C1 的 bash logger 被插件**合法覆盖** · 等效于把 Spike 3 的 wiring 验证"转正"成真 feature
- Part C1 的 `CS188/.claude/hooks/user-prompt-hook.sh` 会留在 git history 作为**L5-#8 错位事件的物证** · 未来 post-mortem 查看

---

## 7. Plan v25 kickoff 参考（spec 的终点）

### 7.1 Plan v25 启动前置

- 完整读一遍本 spec + `phase-1-day-1-spike-results.md` 的 L5-#8 条目
- 准备 Obsidian 插件开发环境（`pnpm create obsidian-plugin` 或手动初始化）
- 在 Canvas repo 新分支 `git checkout -b plan-v25-obsidian-deployer`
- 阅读 PRD §3.1 / §4 / §4.7.3 / §4.7.4 / §10.1 对应章节确认 deliverable

### 7.2 MVP 分阶段实施策略

| Step | 范围 | deliverable | 验收标准 |
|---|---|---|---|
| 1 | 最小可运行命令 + 1 层 hook | `manifest.json` + `main.ts` + `commands/deploy.ts` + `templates/CLAUDE.md` + `templates/settings.json` + `templates/hooks/user-prompt-submit.js` | 能在 CS188 跑 `Canvas: Deploy` · 替换 Part C1 的 bash logger · 不破坏 `settings.local.json` |
| 2 | 目录树 + skill 骨架 | `installers/directory-tree.ts` + `installers/skills.ts` + 6 个 skill 模板 | `exam_boards/` `wiki/` `discussions/` 创建成功 · 6 个 skill 目录就位 |
| 3 | 剩余 3 层 hook | `installers/hooks.ts` + 3 个 hook 模板 | `settings.json` 4 层 hook 全部声明 · 每层 dry-run 通过 |
| 4 | Backend 健康检查 + LanceDB 索引 | `installers/backend-check.ts` + `installers/lancedb-index.ts` | backend 不可达时正确 fallback · 可达时触发初次索引 |
| 5 | 辅助命令 | `commands/verify.ts` + `commands/update.ts` + `commands/switch.ts` | 能 verify 现有 vault · update template 保留用户数据 |

### 7.3 第一个 integration test target

**CS188 vault**（Plan v24 Part C1 已部分初始化 · 是**完美的 incremental deploy test case**）

验证要点：
- 插件能在"已有 1 层 hook（bash logger）"的状态下正确扩展到 4 层 hook
- `settings.local.json` 的 permissions + `outputStyle: "Learning"` 在部署过程中 **md5 不变**
- `~/.claude/` 下零新增 / 修改（验证 scope 隔离 · 不再重演 L5-#8）
- 部署前后跑同一个 `Cmd+P` 命令列表对比 · 确认没有丢命令
- 备份文件（`.bak.<ts>`）生成正确 · 可回滚

### 7.4 验收清单

- [ ] 能在 CS188 跑 `Canvas: Deploy Learning Infrastructure` · 无 error
- [ ] 所有 17 项 deliverable 检查通过（`Canvas: Verify` 报 0 missing）
- [ ] `CS188/.claude/settings.local.json` md5 保持不变
- [ ] `~/.claude/` 整个目录 md5 保持不变（scope 隔离验证）
- [ ] 从 `Canvas: Deploy` 启动到完成 · 总耗时 < 30 秒
- [ ] 能在一个新 vault（如 CS189）从零初始化 · 全绿
- [ ] 所有备份文件可 rollback 恢复到部署前状态

---

## 附录 · 与其他文档的关系

- **主 PRD**: `14-scheme-a-implementation-prd.md` §3 / §4 / §6 / §10 是本 spec 的 upstream
- **L5 证据**: `phase-1-day-1-spike-results.md` L5-#8 是为什么需要插件的反向证据
- **方法论**: `16-triangulated-review-report.md` §1.5.9 的四层 nested errata pattern 为本 spec 提供理论基础
- **Plan 链路**: Plan v15→v23（PRD 演化）→ Plan v24 Part C1（手动修 L5-#8）→ **本 spec**（Part C2）→ Plan v25（实现）→ Phase 2（学习闭环）

---

**END OF SPEC**
