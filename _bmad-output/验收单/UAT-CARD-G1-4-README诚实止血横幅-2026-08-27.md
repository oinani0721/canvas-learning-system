# 验收单 · CARD-G1-4 README 诚实止血横幅

> **批次**: BATCH-2026-08-27-第四批 · 车道 4 第一卡
> **分支**: `card/n4-readme`（不 push，等你验收）
> **日期**: 2026-08-27
> **计划书锚点**: §12.7:617（执行早期先加诚实提示；不得润色旧文案成新承诺）· 总账硬约束：根 README 改动须用户过目 diff 批准

---

## ⛔⛔⛔ 醒目声明（总账硬约束）

**本卡改的是根 README.md。commit 已按流水线惯例打到车道分支 `card/n4-readme`，但在合并进开发分支（feature-obsidian-hybrid-dev / main）之前，必须由你亲自过目下方「三、待用户批准」节的完整 diff 并明确说「批准」。你不点头，这个 diff 不进开发分支。**

---

## 一、你需要做什么（用户产品体验）

只有一件事：**看一遍「三、待用户批准」节的 diff，说批准或提修改意见**。

效果预览：以后任何人（包括你自己）打开这份 README，第一眼看到的是一个黄色 WARNING 框，明说「这是历史文档，有 5 类已知失实，别照着做，Docker 段相对可信」；往下读到 5 个具体失实位置时，紧贴着各有一行「⚠️ 漂移标注」现场提醒。旧文案一个字没动。

## 二、技术判据（Claude 已代跑）

| 裁判 | 命令 | 结果 |
|---|---|---|
| 只加不改铁律 | `git diff --numstat README.md` | **19 insertions / 0 deletions** ✅ |
| diff 无任何删除行 | `git diff README.md \| grep -E '^-' \| grep -v '^---' \| wc -l` | **0** ✅ |
| 行数 | `wc -l README.md` | 308 → **327**（+19，全部为新增提示行）✅ |
| 主仓 README 不碰 | 本卡只改 worktree 副本 | 主仓 301 行旧副本零接触 ✅ |
| 横幅漂移点数 | 要求 ≥3 | **5 条** + Docker 段可信入口指向 ✅ |
| 就地标注数 | 要求 5 处 | **5 处**（Overview Agent 数 / FSRS 未验证 / 旧插件目录 / 端口与 0.0.0.0 / Quick Start）✅ |

### 零新能力承诺自检（对照计划书 §12.7 L633 的 11 类禁夸大清单，逐条人工核对新增 19 行）

| # | 禁夸大声明 | 新增文本命中 |
|---|---|---|
| 1 | production-ready | 0 ✅ |
| 2 | 任意 vault 一键可用 | 0 ✅ |
| 3 | 完整 multi-vault safe | 0 ✅ |
| 4 | Graphiti 永久且全量可重建 | 0 ✅ |
| 5 | full multi-source RAG 是默认主链 | 0 ✅ |
| 6 | 把 hit@k 写成 recall | 0 ✅ |
| 7 | FSRS/UI 已完全一致 | 0 ✅ |
| 8 | Canvas↔Excalidraw 无损双向 | 0 ✅ |
| 9 | 14 个 Agent 协同 | 0 ✅（新增行只陈述「数字互相矛盾」，未宣称任何数量的 Agent 协同）|
| 10 | 移动端可用 | 0 ✅ |
| 11 | skipped/degraded 等同成功 | 0 ✅ |

> 唯一的正面措辞是卡片明令要求的指向：「Docker Deployment 一节经 2026-08-27 勘探实测**相对可信**，可作为部署起点」——带 hedge、不承诺能力，且勘探（第四批档案 §二 G1-4）已实测该段相对可信。

除人工自检外，已用 CARD-G1-5 的机械 lint 复核（实跑记录）：
- `check_readme_claims.py --report` 对含横幅的 README 全文：**TOTAL=3 effective=0**，命中全部是旧文案行（新行号 35/50/68 的 14-Agent 旧声明，打 `[legacy]` 标），本卡新增 19 行 **0 误伤**
- `check_readme_claims.py --staged-diff` 对 staged 的 G1-4 diff（+19 行）：**TOTAL=0**，横幅按新门语义可正常 commit

### Codex 对抗审查（重点：零改写零新承诺）

- 一轮（ultra）：`codex exec --sandbox read-only -m gpt-5.6-sol -c model_reasoning_effort="ultra"`，全文存档 `_bmad-output/审查/codex-review-CARD-G1-4.md` — **0 BLOCKER + 0 HIGH** + 3 MEDIUM，「BLOCKER/HIGH 清零: 是」。零改写/零新承诺（L633 十一条逐条核对表）/横幅完整性/Markdown 结构四项硬门全部「通过」；`.canvas` 右键无事件挂载、正文 11 个 Agent、0.0.0.0 撞 P0-0 等事实断言抽查坐实。
- 3 条 MEDIUM（均为横幅自身的事实精度）处置——**全部按建议修复**：
  - M1「后端枚举 13 个」口径不准（AgentType 实为 15 值含 2 兼容别名，另有 14 项清单）→ 改为如实陈述多口径互不一致
  - M2「8011」自指成真（README 原文只有 8000/8001，8011 是横幅自己引入的）→ 改为「本文 8000/8001，仓库 `.env.example` 当前 8011」
  - M3「不会被现行插件读取」过度绝对 → 改为「可能导致插件无法正常加载」hedge
- 二轮复核（high，同文件末尾附录）：M1/M2/M3 **全部 RESOLVED**，修复后 diff 仍 19/0 纯新增、零新承诺，「**BLOCKER/HIGH 清零: 是**」+「**MEDIUM 处置复核: 通过**」。
- 本 session Graphiti MCP 未接入（工具清单无 graphiti-canvas），决策与审查记录以本验收单 + 审查存档为准，不补记 Graphiti。

## 三、待用户批准（完整 diff 原文）

**⛔ 合并进开发分支前须你过目此 diff 并明确批准（总账硬约束）。**

```diff
diff --git a/README.md b/README.md
index a2f72e2b..060344c8 100644
--- a/README.md
+++ b/README.md
@@ -1,5 +1,15 @@
 # Canvas Learning System
 
+> [!WARNING]
+> **诚实止血横幅（2026-08-27 · CARD-G1-4）** — 本 README 为历史介绍文档，内容跨越两个架构时代，尚未按当前系统状态重新验证。已知漂移点：
+> 1. **Agent 数量前后矛盾** — 下文三处分别写 12-14（Overview）与 14（Our Solution 要点、Features 标题），正文实际列出 11 个；后端 `AgentType` 枚举 15 个值（含 2 个兼容别名）、另一处后端清单 14 项，各处口径互不一致。
+> 2. **旧插件目录名** — 安装步骤中的 `.obsidian/plugins/canvas-review-system/` 是旧目录名，与当前插件目录不一致。
+> 3. **旧 Quick Start 流程** — 「右键调用 Agent」的 `.canvas` 操作流程在当前插件代码（main.ts）中没有对应事件挂载，按此操作无法复现。
+> 4. **端口与监听地址漂移** — 本文写有 8000 与 8001 两种端口；仓库当前 `.env.example` 实际使用宿主端口 8011，与本文不一致；`--host 0.0.0.0` 与 2026-07-31 的 P0-0 安全决策相抵触，请勿照抄。
+> 5. **未验证描述** — 「Auto-generated review Canvas」等 Review System 描述未在当前架构下重新验证。
+>
+> 相对可信的入口：下方 **Docker Deployment** 一节经 2026-08-27 勘探实测相对可信，可作为部署起点；其余章节请以仓库内代码、测试与验收单为准。
+
 <p align="center">
   <strong>AI-Powered Learning Platform for Obsidian Canvas</strong><br/>
   Transform passive learning into active understanding using the Feynman Technique
@@ -24,6 +34,8 @@
 
 Canvas Learning System transforms **passive learning** into an **active learning process**. With 12-14 specialized AI Agents collaborating, it guides you from confusion to mastery through the Feynman Learning Method.
 
+> ⚠️ 漂移标注（2026-08-27）：本段 Agent 数量与下文不一致——此处写 12-14，下文 Our Solution 要点与 Features 标题写 14，正文实际列出 11 个；后端多处枚举（15 值含 2 别名 / 14 项清单）口径也互不一致，数字待重新核定。
+
 ### Problems We Solve
 
 - **Passive Consumption** - Reading/watching without active engagement
@@ -78,6 +90,8 @@ Canvas Learning System transforms **passive learning** into an **active learning
 - Auto-generated review Canvas
 - Progress tracking dashboard
 
+> ⚠️ 漂移标注（2026-08-27）：本节「Auto-generated review Canvas」等描述未在当前架构下重新验证，实际行为以仓库内代码与测试为准。
+
 ---
 
 ## Installation
@@ -95,6 +109,7 @@ Canvas Learning System transforms **passive learning** into an **active learning
 1. Download the latest [Release](https://github.com/oinani0721/canvas-learning-system/releases)
 2. Extract `main.js` and `manifest.json`
 3. Create folder `.obsidian/plugins/canvas-review-system/` in your Vault
+   > ⚠️ 漂移标注（2026-08-27）：`canvas-review-system` 是旧插件目录名，与当前插件 manifest ID 及部署目录（`canvas-learning-system`）不一致，按本行操作可能导致插件无法正常加载。
 4. Copy the files to that folder
 5. Enable the plugin in Obsidian Settings > Community Plugins
 
@@ -129,6 +144,8 @@ cp .env.example .env
 uvicorn app.main:app --host 0.0.0.0 --port 8000
 ```
 
+> ⚠️ 漂移标注（2026-08-27）：上方 `--host 0.0.0.0 --port 8000` 与本文 Docker 段的 8001、仓库 `.env.example` 当前的 8011 端口配置互相矛盾；`0.0.0.0` 监听与 2026-07-31 的 P0-0 安全决策相抵触，请勿照抄。
+
 ### Docker Deployment (Neo4j + Memory System)
 
 #### Prerequisites
@@ -188,6 +205,8 @@ curl http://localhost:8001/api/v1/health
 
 ## Quick Start
 
+> ⚠️ 漂移标注（2026-08-27）：以下「右键调用 Agent」流程在当前插件代码（main.ts）中没有对应事件挂载，按此步骤操作无法复现；本节属旧架构时代文案。
+
 1. **Create a new Canvas** - Create a `.canvas` file in Obsidian
 2. **Add red nodes** - Write concepts you don't understand
 3. **Right-click to invoke Agent** - Select appropriate Agent for decomposition/explanation
```

## 四、改动清单

- `README.md` — +19 行纯新增（1 横幅 + 5 就地标注），0 删除 0 改写
- `_bmad-output/审查/codex-review-CARD-G1-4.md` — Codex ultra 对抗审查存档
- `_bmad-output/验收单/UAT-CARD-G1-4-README诚实止血横幅-2026-08-27.md` — 本验收单
