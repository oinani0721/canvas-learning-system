---
story: "1.18"
title: "Dashboard MVP · v1.2（用户实测通过 · 4 MVP 闭环达成）"
status: "done"
version: "v1.2"
date: "2026-05-02"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
unblocked_by: "1.19 v4.1 已 done (2026-05-01)"
d4_decisions: "D4-3 confirm Modal + D4-5 三指标（mastery 平均 + 节点总数 + FSRS 到期 placeholder）"
uat_outcome: "用户截图证明 — 最近学习活动 bug 已修 + 4 节点表格正常渲染 + 24h 统计"
---

# Story 1.18 验收单 v1.2 — Dashboard MVP · 4 MVP 闭环达成 ⭐

> [!success]+ 2026-05-02 v1.2 用户实测通过 — Story 1.18 done
> 用户跑通 Dashboard.md（含 v1.1 引入的"最近学习活动"bug 修复 + 4 节点表格正常渲染 + 24h 统计），截图证明各 section 渲染正常。
>
> ## 闭环里程碑
>
> | Story | 状态 | 用户能力 |
> |---|---|---|
> | 1.16 批注 hotkey | ✅ done | Cmd+Shift+A 批注任意文本，7 callout 类型 |
> | 1.17 AI 双链 v4.1 | ✅ done | Cmd+Shift+D 派生节点 + 关系类型双写 + Hybrid 阶段 1 |
> | 1.18 Dashboard v1.2 | ✅ **本次 done** | Dashboard.md 三指标 + 活跃白板表 + 节点池分组 + confirm Modal + 交互按钮 |
> | 1.19 configure-whiteboard v4.1 | ✅ done | 4 命令体系（建空白板 / 建+种子 / 追加已有 / Skill fallback）|
>
> **=> 4 MVP 闭环 100% 达成**：用户可以从"PRD 行为期望 → 建白板 → 派生节点 → 批注 → 看 Dashboard 概况"全程在 Obsidian 内完成，无需技术介入。
>
> ## 下一步
>
> 路线 A · Epic 3.1 节点 AI 对话原型（Cmd+Shift+C → Claudian 弹出含 context 对话）— 见 `_bmad-output/验收单/Story-3.1-claude-code-cli-per-node-session.md`（待 ship）。

> [!success]+ 2026-05-02 v1.1 ship — B + A 双跑完成
> 基于 ChatGPT Deep Research（[DECISION-TECH-FINAL] 已归档 Graphiti）+ 3 agent 调研社区案例。
>
> ## v1.0 → v1.1 的 2 大改进
>
> ### B · 修 5 个 plugin 错误命令契约
>
> | 命令 | v1.0（错误） | v1.1（修复） |
> |---|---|---|
> | `canvas:start-examination` | GET /api/v1/exam/start（无 body）| **POST + ExamSessionCreate body**（source_canvas_id + exam_mode）|
> | `canvas:open-review-queue` | GET /api/v1/review/queue（不存在）| **GET /api/v1/review/schedule?days=7**（实际 endpoint）|
> | `canvas:open-dashboard` | GET /api/v1/system/health（假冒）| **打开 Dashboard.md launcher**（vault 根）|
> | `BACKEND_URL` | 写死 localhost:8001 | **plugin Settings 可配置**（Settings → Canvas Learning System）|
> | `callBackend()` | 只检查 resp.ok | **解析 JSON + 显示 detail/total_count**（Notice 友好）|
>
> ### A · plugin 暴露 3 公共方法 + Dashboard 交互按钮
>
> - `app.plugins.plugins["canvas-learning-system"].getMasteryBatch(boardName)` — 聚合该白板节点 mastery（含 2s 缓存）
> - `app.plugins.plugins["canvas-learning-system"].executeBoardCommand(boardName, "exam-start"|"open-board")` — 触发命令
> - `app.plugins.plugins["canvas-learning-system"].invalidateMasteryCache(boardName?)` — 强制刷新
> - **`metadataCache.on('changed')` 监听**：用户改任意节点 / 白板 frontmatter 后自动失效缓存
> - **Dashboard.md 表格**：每行加 📂 打开白板 + 🚀 考察 按钮 + 全局🔄 强制刷新缓存
>
> ## 主 ship
> - **plugin** main.js 65270B → **72731B**（+7461B = SettingsTab + 3 plugin API + handler 重写）
> - **`Dashboard.md`** 表格升级为 dv.el 渲染 + addEventListener 按钮
> - 11 plugin 命令（v1.0 时 11 个保持不变）



> [!success]+ 2026-05-01 v1.0 ship — 4 MVP 闭环达成 ⭐
> Story 1.16 + 1.17 + 1.19 全 done 后，**1.18 是 4 MVP 最后一环**。本 v1.0 适配 v4 扁平架构（不依赖 Buttons plugin，纯 DataviewJS 自渲染）+ D4-3 confirm Modal + D4-5 三指标。
>
> ## 改 v3 spec 的关键差异
> | spec v3 | 实际 v1.0 |
> |---|---|
> | 数据源 `wiki/canvases/*/index.md` | **`原白板/*.md` + `节点/*.md`**（v4 扁平） |
> | Buttons plugin 触发 `obsidian://execute` | **DataviewJS 自渲染 + 命令面板触发**（vault 没装 Buttons） |
> | 表 1: 活跃原白板（doc_count / mastery） | ✅ 实现，含 🟢🟡🔴 颜色编码 |
> | 表 2: 准备中检验白板 | ⏭ 推迟到 Epic 6（exam_boards 数据源还没建） |
> | 一键考察按钮 | **plugin 新命令 `canvas:start-examination-confirm`** + Cmd+P 触发 |
>
> ## 主 ship
> - **`canvas-vault/Dashboard.md`** —— vault 根新 md，DataviewJS 实时聚合 frontmatter
> - **plugin 新命令** `canvas:start-examination-confirm`（D4-3 confirm Modal）
> - **plugin** main.js 62890B → **65270B**（+2380B = ConfirmExamModal + handler）

---

## 🎯 v1.1 UAT 12 步（约 8 分钟）

### 前置（P1-P3）

- [ ] **P1**：main.js 大小 = **72731B**（`stat -f "%z" canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`）
- [ ] **P2**：Cmd+Q 退出 Obsidian → 再开（让 v4.3 加载）
- [ ] **P3**：Settings → Community plugins → Canvas Learning System 已启用

### 核心 UAT

#### V1-1 · 打开 Dashboard.md
- [ ] vault 根有新文件 `Dashboard.md`
- [ ] 双击打开（或 Cmd+O 搜 Dashboard）
- [ ] 顶部标题"📊 Canvas 学习仪表盘"

#### V1-2 ⭐ · 三大核心指标（D4-5）
- [ ] **平均精通度**显示数字 + 颜色（如 `0.30 🔴 起步`）
- [ ] **节点总数**显示总数 + 按白板分组（如 `9（特征值与特征向量: 4 / cs-61b: 1 / ...）`）
- [ ] **FSRS 到期**：placeholder `0（Story 5/6 BKT+FSRS 实施后自动统计）`
- [ ] **原白板总数**：`4`

#### V1-3 ⭐ · 活跃原白板表
- [ ] 表头 4 列："白板 / 节点数 / 平均掌握度 / 状态"
- [ ] 4 行数据（4 个白板）
- [ ] 节点数 > 0 的白板（特征值与特征向量、CS 61B）排前面
- [ ] 平均掌握度含 🟢🟡🔴 颜色
- [ ] 状态描述：空白板提示 Cmd+Shift+D，进行中显示"📖 进行中"等

#### V1-4 · 节点池分组列表
- [ ] 按 source_board 分组
- [ ] 每组 header 含白板名 + 节点数
- [ ] 节点按 mastery_score 升序（最弱在前）
- [ ] 每行含颜色 + wikilink + mastery 数值

#### V1-5 · 待复习节点列表（v1 placeholder）
- [ ] callout 警告 v1 暂未实现 FSRS
- [ ] 兜底视图列出所有 mastery < 0.5 的节点（实际 9 个节点应大部分在）
- [ ] 节点行含 🔴 + wikilink + 白板名 + mastery

#### V1-6 ⭐ · D4-3 confirm Modal
- [ ] Cmd+P → 搜"启动考察（带 confirm 弹窗）"→ Enter
- [ ] **应弹 Modal**，标题"启动考察 · 确认"
- [ ] body 显示：`确认从 当前 vault 进入考察模式？` + `Plugin 将调用后端 /api/v1/exam/start 基于 mastery < 0.5 的节点生成 5 题。` + `⏰ 考察过程预计 5-15 分钟。`
- [ ] 2 个按钮：`❌ 取消 (Esc)` + `✅ 开始考察`（蓝色 mod-cta）

#### V1-7 · Modal 取消路径
- [ ] 点"❌ 取消"或按 Esc → Modal 关闭
- [ ] **不**调 backend / **不**报错
- [ ] 再次触发 → Modal 应正常弹出

#### V1-8 · 从白板内触发上下文显示
- [ ] 打开 `原白板/特征值与特征向量.md` 让它成为 active file
- [ ] Cmd+P → "启动考察（带 confirm 弹窗）"
- [ ] Modal body 应显示：`确认从 原白板"特征值与特征向量" 进入考察模式？`（带白板名上下文）

### v1.1 新增必测（V1-9 至 V1-12）

#### V1-9 ⭐ · plugin Settings 可配置 BACKEND_URL（B 修复）
- [ ] Settings → 滚动到底找"Canvas Learning System"
- [ ] 应见 "Backend URL" 输入框，默认 `http://localhost:8001`
- [ ] 改为别的 URL（如 `http://192.168.1.100:8001`）→ 关 Settings → 改回默认
- [ ] 再次触发 confirm Modal → 调用应使用新 URL（不再写死 localhost）

#### V1-10 ⭐ · 启动考察 POST 契约修复（B 修复 - 如 backend 没启会失败但**错误信息应有用**）
- [ ] 打开 `原白板/特征值与特征向量.md` 让它成为 active file
- [ ] Cmd+P → 搜"启动考察（直调，无 confirm）"→ Enter
- [ ] **预期 backend 没启时**：Notice `启动考察"特征值与特征向量" 失败: 后端未连接（fetch failed）请先 docker compose up...`（**不再**是没用的 HTTP 404）
- [ ] **如果 backend 启了**：Notice `✓ 考察会话已建：<UUID>`（说明 POST + ExamSessionCreate body 正确）

#### V1-11 ⭐ · Dashboard 交互按钮（A 升级）
- [ ] 打开 Dashboard.md
- [ ] "🗺️ 活跃原白板" 表格每行右侧应见 **📂 + 🚀 考察** 两个按钮
- [ ] 点 📂 按钮 → 应在新 tab 打开对应白板 md
- [ ] 点 🚀 考察 按钮 → **先打开白板** + **随后弹 D4-3 confirm Modal**（200ms 内）
- [ ] 节点数 = 0 的白板，🚀 按钮应灰色 disabled（鼠标 hover cursor 是 not-allowed）

#### V1-12 ⭐ · 强制刷新缓存（A 升级）
- [ ] Dashboard 底部应见 "🔄 强制刷新缓存" 按钮
- [ ] 在另一 tab 改某节点 frontmatter `mastery_score: 0.30 → 0.85`
- [ ] 切回 Dashboard → 表格应**自动**反映（plugin metadataCache 监听清缓存）
- [ ] 即使没自动刷新，点"🔄 强制刷新缓存"+ 按 F5 reload，应反映新值

### 已废弃（v1.0 占位）

- ~~V1-9 后端 connection refused~~ → 改为 V1-10 实际验证 POST 契约
- ~~V1-10 pin tab~~ → 移到 v1.0 行为，不必再测

---

## 🚦 v1.0 验收结果

### 全 8 步 ✅
→ 告诉我 "**Story 1.18 v1.0 通过**"
→ 我 mark done + **4 MVP 闭环达成 100%** ⭐
→ 启动 Story 1.2 wikilink-graph-build（后端基础）或 Epic 3 节点 AI 对话

### 部分失败
→ 告诉我哪步 ❌ + 截图
→ 针对性修

### Dashboard 完全空白 / DataviewJS 报错
→ 检查 vault 是否装 Dataview plugin（应已装）
→ Console (Cmd+Opt+I) 看 dataview 报错

---

## 🛠️ 实施细节

### 新增文件
- **`canvas-vault/Dashboard.md`** (~150 行，含 5 个 dataviewjs 块 + 静态 markdown)
  - Section 1: 三大核心指标
  - Section 2: 活跃原白板表
  - Section 3: 节点池分组
  - Section 4: 待复习（v1 placeholder）
  - Section 5: 一键考察说明（不依赖 Buttons）
  - Section 6: 4 命令速查
  - Section 7: 学习历史

### Plugin 改动
- **MOD** `frontend/obsidian-plugin/src/main.ts`：
  - 注册第 11 个 command `canvas:start-examination-confirm`
  - 新方法 `handleStartExaminationConfirm()` —— 检测 active file 是否在 `原白板/` 下，从中提取 sourceContext
  - 新 `ConfirmExamModal` 类（基于 obsidian Modal，title + 2 段说明 + 取消/开始 2 按钮）
- **MOD** main.js 62890B → **65270B**（+2380B for ConfirmExamModal + handler）

### 不依赖
- ❌ Buttons plugin（vault 没装）→ 用命令面板替代
- ❌ Bases plugin（v3 提到的复杂方案）
- ❌ obsidian-advanced-uri plugin

### 数据源（v4 扁平架构）
- `原白板/*.md` frontmatter: `type: whiteboard / board_name / created_at / doc_count / doc_mastery_avg`
- `节点/*.md` frontmatter: `type: concept / mastery_score / source_note / source_board / created_from / up / derived-from / relationships`

---

## 📝 你的批注区

> [!question]+ Dashboard MVP 实测批注（2026-05-01 起）
>
> 跑完 8 步任意写下：
> - DataviewJS 渲染速度（应 < 1s）
> - 三指标颜色编码是否好看
> - confirm Modal UX 是否合理（"考察 5-15 分钟"是否符合你预期）
> - 节点池分组是否过于密集（节点多时是否需要折叠）
>
> （空）

---

## 🔗 技术 spec 引用

- Story spec: `_bmad-output/implementation-artifacts/epic-1/1-18-dashboard-md-mvp.md`（v1.0 已 ship）
- v3 spec 段保留作历史（`wiki/canvases` 路径已废弃）
- D4-3 决策来源: `_bmad-output/验收单/Story-1.19-configure-whiteboard.md` v4 UAT 通过后的 D4 决策段
- D4-5 决策来源: 同上
- 主 commit（待 ship）: `feat(epic-1): story 1.18 v1.0 dashboard mvp + d4-3 confirm modal + d4-5 三指标`
