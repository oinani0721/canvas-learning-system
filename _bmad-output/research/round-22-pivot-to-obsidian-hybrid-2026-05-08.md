---
title: "Round-22 弃用 + 回归 Obsidian Hybrid 综合报告"
type: "pivot-decision-and-migration"
date: "2026-05-08"
trigger: "用户决定放弃 DeepTutor fork 路径，回归 Canvas + Obsidian Hybrid 开发 worktree"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
agents_used: 3
critical_findings:
  - "DeepTutor 第一次提及在 Round-15 line 99/155 (2026-05-05)"
  - "推荐回归锚点 Round-14（最后一次纯 Obsidian Hybrid 调研）"
  - "UAT v3.0 资产已迁移到 Obsidian Hybrid worktree（template + hook + DoD-3 + 范本）"
---

# Round-22 弃用 + 回归 Obsidian Hybrid 综合报告

> **触发**: 用户 2026-05-08 看完 fork 路径 A 对照测试 + 两次反思后明确决定："放弃把 Canvas learning system 加上 DeepTutor，把 worktree 切回原本的 Canvas learning system + Obsidian 开发 worktree"
>
> **方法**: 3 agent 并行 deep explore — Agent A 精确定位 DeepTutor 起源 round；Agent B 抽象 UAT v3.0 worktree-agnostic 标准；Agent C 切 worktree 操作 + 资产迁移清单。

## Executive Summary

1. **DeepTutor 起源**: 第一次提及在 `round-15-bkt-fsrs-multihop-tauri-prd-deep-explore-2026-05-05.md` line 99（学术对标发现）+ line 155（用户首次提议 fork 改造）。从 Round-15 → Round-22 的 8 轮调研构成"接受 → 调研 → 决定 fork → 启动 MVP" 完整 pivot 链
2. **回归锚点 Round-14**: `round-14-graphiti-retrieval-deep-explore-2026-05-05.md` 是**最后一次纯 Obsidian Hybrid 调研**（双链检索 + Graphiti 同步），未涉 fork 决策，含完整用户原话需求批注（line 31-54）
3. **UAT v3.0 资产已迁移**: template / hook / DoD-3 D3-A~D3-E 5 铁律 / 范本 Story-10.4 已 cp 到 Obsidian Hybrid worktree，settings.json 已注册 hook，CLAUDE.md DoD-3 段已升级
4. **Obsidian Hybrid worktree CURRENT_TASK.md 已创建** — 含 Round-22 弃用决策依据 + Round-14 锚点指引 + Epic-1/2 当前状态 + 下一步 5 件事
5. **保留 archive 不删**: DeepTutor worktree 整体作 archive（含 17 份 round-22 调研 + Story 10.x + Epic-10/11 + 决策批注 D17/D18/D19）。fork repo / vanilla repo / docker 容器留命令给用户手动执行

---

## 第 1 部分 · DeepTutor 起源 Timeline（Agent A 收敛）

### 1.1 第一次提及精确位置

**文件**: `_bmad-output/research/round-15-bkt-fsrs-multihop-tauri-prd-deep-explore-2026-05-05.md`

**Line 99**（学术对标 — DeepTutor 进入视野）:
```
| **D. 多段推理生成考察题** | 🔴 学术研究活跃，**教育场景生产 near-zero** |
...最接近的 DeepTutor (HKUDS, 2025) 和 KG-CQ (MDPI 2025) 都没有个人 mastery/error 元数据
```

**Line 155**（用户首次提议 fork — 态度转折点）:
```
**User：我们要不要直接 先在这个 https://github.com/HKUDS/DeepTutor 来改造，
我觉得额外我需要的能力是：
1，我学习是会以一个 vault 文件夹作为核心，那么我需要 ai 在给我解释讲解题目的时候，能精确返回我储存在笔记库里的笔记片段；
2，就是我对于知识点的掌握度分析...我在打批注然后双向链接来表示各个片段关系时，我是希望 agent 能充分理解我的拆解链条的；
3，最好还是用 FSRS 的配合，这样我就知道最佳复习时机...**
```

### 1.2 Round-15 → Round-22 完整 Timeline

| Round | 文件 | 日期 | 用户态度 |
|---|---|---|---|
| **15** | bkt-fsrs-multihop-tauri-prd | 2026-05-05 | 🟢 学术对标 → 主动提议 fork |
| 16 | deeptutor-canvas-flow | 2026-05-06 | 🟢 确认改造方向 |
| 17 | deeptutor-technical-conflicts | 2026-05-06 | 🟡 技术冲突评估 |
| 18 | rag-validation-deployment | 2026-05-06 | 🟡 RAG 黑盒打开 |
| 19 | deeptutor-transformation-roadmap | 2026-05-06 | 🟡 改造路径 roadmap |
| 20 | deeptutor-clone-deep-analysis | 2026-05-06 | 🟡 实际代码分析 |
| 21 | canvas-five-core-deeptutor-integration | 2026-05-06 | 🟢 集成方案完成（92KB 最大调研） |
| **22** | 17 份 round-22-* + 决策批注 D17/D18/D19 | 2026-05-06~08 | 🔴 Fork 决策启动 → 2026-05-08 弃用 |

### 1.3 推荐回归锚点 — Round-14

**文件**: `round-14-graphiti-retrieval-deep-explore-2026-05-05.md`

**理由**:
1. 最后一次"双链检索 + Graphiti 同步"的纯 Obsidian Hybrid 调研，**未涉 fork 决策**
2. 含完整用户原话批注（line 31-54）— 4 个核心机制 + 2 大压力点的需求基准
3. Round-15 line 155 列的"3 项 Canvas 核心需求"在 **Obsidian Hybrid 路径**仍 100% 适用（vault 精确返回笔记片段 / 拆解链条理解 / FSRS 复习时机）
4. 切回 Round-14 等于**回到"用 Canvas 原生实现 4 大机制"的路径**，跳过 DeepTutor 集成的整段 detour

**Round-14 关键用户 Quote**:

| 主题 | 用户原话 |
|---|---|
| vault 设计 | "我在 obsidian 上是用 obsidian 的 md 文件 然后再加上了 自己定义双向链接 来规划各个节点之间联系" |
| Mastery 视角 | "节点的理解程度是如何批判的...我对 md 节点内容所打下批注的过程，这个批注则是我的核心的想法也是我后续需要聚焦考察的点" |
| FSRS 实证态度 | "Anki 的 FSRS 难道不是根据你对每个单词卡片回答记得还是不记得，从而推算出掌握程度...我的 Canvas learning system 的检验白板一开始也是根据我对原白板中各个节点的实际掌握情况，精确推算精确的复习时间" |
| 成熟度优先 | "我也不会局限于 BKT。我只是要找到最成熟最稳定的方案，因为没有人做过的东西，我很难验证" |

---

## 第 2 部分 · UAT v3.0 资产迁移（Agent B 收敛）

### 2.1 已迁移资产清单

| 文件 | 源 | 目标 | 升级内容 |
|---|---|---|---|
| `templates/uat-sheet-template.md` | DeepTutor v2 | Obsidian Hybrid（旧版备份 `.v1.backup`） | 双段强制 + 5-Second Test + 句型 + felt-sense + 5 题自检 + 方法论分层 |
| `.claude/CLAUDE.md` § DoD-3 | DeepTutor v3.0 | Obsidian Hybrid CLAUDE.md（旧版备份） | D3-A~D3-E 5 铁律 + 升级自检清单 |
| `.claude/hooks/uat-double-section-guard.js` | DeepTutor | Obsidian Hybrid `.claude/hooks/`（新文件） | PostToolUse 禁词 grep + felt-sense 软警告 + fail-open 容错 |
| `.claude/settings.json` | — | Obsidian Hybrid（追加配置） | PostToolUse 链追加 hook，不覆盖现有 router |
| `_bmad-output/验收单/_reference/范本-双段-Story-10.4.md` | DeepTutor Story-10.4 v2.0 | Obsidian Hybrid `_reference/` | 0% 违规范本作参考 |

### 2.2 worktree-agnostic 抽象（哪些通用 / 哪些 specific）

**通用（直接复用）**:
- 句型 "我做 X → 我看到 Y → 我感觉 Z"
- 通用禁词 17 项（curl/docker/HTTP/JSON/端口/.env/pytest/schema/容器/daemon/git/cd/mkdir/cp/rm/sudo/DevTools）
- 7 段结构骨架（目标 / Behavior / 交互流程 / 4-A 代验 / 4-B 用户验 / 结果 / 批注+trace）
- 5 题自检清单
- D3-A~D3-E 5 铁律语义不变
- Felt-sense 词典（流畅/困惑/信任/期待/失望等 18 词）
- 主观打分 4 项（流畅度 / 易学性 / NPS / 一句话原因）
- 状态机 5 标记（🔒 / 🟢 / ✅ / ❌ / ⏸️）
- 方法论分层（Phase A 5-Second / Phase B JTBD / Day 7+ NPS）

**Worktree-specific（需参数化）**:
- `{EPIC_ID}` / `{STORY_ID}` / `{PLAN_ID}` / `{APP_ENTRY}`
- 项目相关禁词（DeepTutor: endpoint/adapter/pydantic / Obsidian Hybrid: requestUrl/vault.create/obsidiantools/Templater）
- 部署路径（DeepTutor: fork/adapter/ / Obsidian: canvas-vault/.obsidian/plugins/）

---

## 第 3 部分 · 用户手动执行清单（Agent C 收敛）

> Auto Mode 不做的破坏性操作 — 留命令给用户验证执行。

### Step 1 · DeepTutor worktree 收尾 commit（保 archive）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp
git status
git add -A
git commit -m "$(cat <<'EOF'
docs(round-22): final state before Obsidian Hybrid pivot

Round-22 DeepTutor fork MVP 路径已弃用，归档保留作 reference。
弃用决策依据：60KB vault 喂 RAG 是 over-engineering + DEAD-WRITE bug + RAG noise (Liu 2023 / Cuconasu SIGIR 2024 / Chroma 2025).

archive trace: this branch + worktree
回归路径: worktree-feature-obsidian-hybrid-dev @ Round-14 anchor

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push backup worktree-feature-deeptutor-canvas-mvp 2>&1 | tail -3
```

### Step 2 · 切到 Obsidian Hybrid worktree

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev
pwd                                  # → .../feature-obsidian-hybrid-dev
git branch --show-current            # → worktree-feature-obsidian-hybrid-dev
git status
git log --oneline -5                 # → e6b43dc 是最新
cat CURRENT_TASK.md | head -25       # 验证恢复锚点已就位
```

### Step 3 · 处理 Obsidian Hybrid 现存 dirty 状态

```bash
# 删除 Round-22 残留 staging（已在 DeepTutor worktree 备份）
rm -rf _bmad-output/staging-deeptutor-fork/
rm -f _bmad-output/Story-2.1-ai-dialog-context-injection.md.empty-stale.bak
rm -f _bmad-output/111.md
rm -f _bmad-output/round-22-deeptutor-deep-explore-2026-05-06.md
rm -f _bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md
rm -f _bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md

# 截屏文件（看是否要保留）
ls _bmad-output/截屏*.png 2>&1 | head
# 决定后:  rm -f _bmad-output/截屏*.png  或  mv 到 archive

git status
```

### Step 4 · docker / 进程清理

```bash
# 停 DeepTutor + vanilla + pocketbase 容器
cd /Users/Heishing/Desktop/canvas/deeptutor-fork && docker compose down 2>/dev/null
cd /Users/Heishing/Desktop/canvas/deeptutor-vanilla && docker compose -p vanilla down 2>/dev/null

# 兜底（如果 compose down 没找到）
docker stop deeptutor deeptutor-vanilla pocketbase 2>/dev/null
docker rm deeptutor deeptutor-vanilla pocketbase 2>/dev/null

# 验证保留容器仍 healthy
docker ps --filter "name=canvas-learning-system"
# 期望看到 canvas-learning-system-backend (8011) + canvas-learning-system-neo4j (7691) 仍 Up

# Meridian / Ollama 不动（用户其他场景可能用）
```

### Step 5 · 删 fork / vanilla repo（释放 ~144MB）

```bash
# 用户确认后执行：
rm -rf /Users/Heishing/Desktop/canvas/deeptutor-fork
rm -rf /Users/Heishing/Desktop/canvas/deeptutor-vanilla
du -sh ~/Desktop/canvas/  # 验证空间释放
```

### Step 6 · 切回后立即 5 件事

| # | 操作 | 时长 |
|---|---|---|
| 1 | 状态确认 (`git status` + `sprint-status.yaml` head) | 5 min |
| 2 | 读 `_bmad-output/research/round-21-canvas-five-core-deeptutor-integration-2026-05-06.md`（92KB 最后一次 Obsidian Hybrid 思路）+ Round-14/15 用户原话批注 | 30 min |
| 3 | 决定下一步 Epic / Story（候选：Epic-3 / Story 2.1 / Story 3.1） | — |
| 4 | UAT v3.0 验证 — 在新模板上 dry-run 创建 1 个测试验收单 | 10 min |
| 5 | sprint-status.yaml 状态评估 + 选定下一个 Story 的 PRD | 30 min |

---

## 第 4 部分 · Round-14 用户原话核心 Quote（继续讨论的需求基准）

> 这些 Quote 在 Obsidian Hybrid 路径仍 100% 适用 — 不依赖 DeepTutor。

### Quote 1 — vault 设计（Round-14 line 31-32）

> "我在 obsidian 上是用 obsidian 的 md 文件 然后再加上了 自己定义双向链接 来规划各个节点之间联系。"

### Quote 2 — Mastery 批注视角（Round-14 line 44）

> "节点的理解程度是如何批判的，我个人更倾向于，我对 md 节点内容所打下批注的过程，这个批注则是我的核心的想法也是我后续需要聚焦考察的点"

### Quote 3 — Canvas 5 大核心（Round-14 line 91 / Round-21）

> "我的 Canvas learning system 的检验白板一开始也是根据我对原白板中各个节点的实际掌握情况，精确推算精确的复习时间，然后生成精确的检验白板来最大限度的回顾起我原白板的一切内容"

### Quote 4 — 三大需求（Round-15 line 155，Obsidian Hybrid 路径仍适用）

> "1，我学习是会以一个 vault 文件夹作为核心，那么我需要 ai 在给我解释讲解题目的时候，能精确返回我储存在笔记库里的笔记片段；
> 2，就是我对于知识点的掌握度分析... agent 能充分理解我的拆解链条的，所以才可以更加合理出闪卡和题目来考察我；
> 3，最好还是用 FSRS 的配合，这样我就知道最佳复习时机"

### Quote 5 — 成熟度优先（Round-15 line 92）

> "我也不会局限于 BKT。我只是要找到最成熟最稳定的方案，因为没有人做过的东西，我很难验证"

---

## 第 5 部分 · 关键决策追溯（按时间倒序）

| 日期 | 决策 | 关键事件 |
|---|---|---|
| **2026-05-08** | 弃用 Round-22 fork 路径，回归 Obsidian Hybrid | 用户看 fork 路径 A 对照测试 + RAG vs Karpathy 调研后决策 |
| 2026-05-07 | D19 Epic-11 锁定 Docker Compose Supervisor | Round-22 桌面化决策 |
| 2026-05-07 | D18 Epic-11 桌面化 Electron | Round-22 桌面化决策 |
| 2026-05-06 | D17 Round-22 fork MVP 启动 | Round-22 fork 路径决策 |
| 2026-05-05 | Round-15 用户首次提议 fork DeepTutor | DeepTutor 起源点 |
| 2026-05-05 | Round-14 最后一次纯 Obsidian Hybrid 调研 | **回归锚点** |
| 2026-05-04 | D15/D16 Story 2.5.X/2.5.Y 用户主权与隔离 | Obsidian Hybrid 最后里程碑 |

---

## 关键文件路径速查

| 资产 | 路径 |
|---|---|
| **回归锚点** | `_bmad-output/research/round-14-graphiti-retrieval-deep-explore-2026-05-05.md` (Obsidian Hybrid worktree) |
| **DeepTutor 起源** | `_bmad-output/research/round-15-bkt-fsrs-multihop-tauri-prd-deep-explore-2026-05-05.md:99,155` (DeepTutor worktree archive) |
| **Round-21 92KB 最大调研** | `_bmad-output/research/round-21-canvas-five-core-deeptutor-integration-2026-05-06.md` |
| **Round-22 弃用证据** | `_bmad-output/research/round-22-rag-degradation-and-paradigm-report-2026-05-08.md` |
| **Obsidian Hybrid CURRENT_TASK** | `worktrees/feature-obsidian-hybrid-dev/CURRENT_TASK.md` (新建) |
| **archive worktree branch** | `worktree-feature-deeptutor-canvas-mvp` @ `d4295f3` |
| **UAT v3.0 模板** | `worktrees/feature-obsidian-hybrid-dev/_bmad-output/templates/uat-sheet-template.md` (已迁移) |
| **UAT hook** | `worktrees/feature-obsidian-hybrid-dev/.claude/hooks/uat-double-section-guard.js` (已迁移) |

---

## 风险红线

- ✅ 不删 fork commit history（保留 trace）
- ✅ 不删 worktree 物理目录（DeepTutor worktree 当 archive）
- ✅ 不动 main branch
- ✅ Canvas backend (8011) / Neo4j (7691) 不停（其他 worktree 用）
- ✅ Meridian / Ollama 不动（用户其他场景）
- ⚠️ DeepTutor fork repo / vanilla repo / docker 容器 — 用户决定是否删（命令已给）

---

*Round-22 弃用 + Obsidian Hybrid 回归综合报告。3 agent 收敛。Auto Mode 已完成低风险迁移，破坏性操作命令留用户执行。*
