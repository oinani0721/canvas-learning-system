# Vault 切换方案 — 批注回复

> 日期：2026-04-17 | EPIC1-BMAD-DEV-ASSESS-2026-04-17
> 
> 回复 [[vault-switch-review-2026-04-17]] 中的用户批注。
> 新批注用 `> BMAD-ANNO:` 标记，已回复的用 `> REPLY:` 标记。

---

## 回复批注 1：注意力问题（第二节 line 27）

> **你的批注**: 肯定是我关于 claude code 的设置出了一些问题，所以请你仔细 deep explore 解决这个注意力的问题，归档处理掉过时的内容

### 根因分析

**问题**：Claude Code 搜 story 时找到了旧的 `_bmad-archive/legacy-stories/`（75 个文件，3月31日），没有去找新的 `_bmad-output/implementation-artifacts/epic-1/`（13 个文件，4月17日）。

**原因**：你的 CLAUDE.md 和 `.claude/rules/` 里**没有任何规则告诉 Claude Code 应该优先搜哪个目录**。

具体来说：
1. CLAUDE.md 的"项目文档"列表里列了 `docs/`、`_decisions/`、`openspec/`，但**完全没提 `_bmad-output/`**
2. `.claude/rules/` 里没有搜索策略规则
3. `context-inject.js` hook 只注入 `CURRENT_TASK.md` 和 `known-gotchas.md`，不注入 Story 目录位置
4. 两个目录按字母排序：`_bmad-archive` 排在 `_bmad-output` 前面，搜索时先命中旧内容

### 目录审计结果

| 目录 | 状态 | 内容 | 建议 |
|------|------|------|------|
| `_bmad-output/implementation-artifacts/epic-1/` | **当前** | 13 个 Story spec（1.1-1.13），4月17日最新 | **优先搜索** |
| `_bmad-output/planning-artifacts/` | **当前** | PRD、架构、UX 设计 | 优先搜索 |
| `_bmad-output/research/` | **当前** | 16 个调研报告（QA round 2-13） | 按需搜索 |
| `_bmad-archive/legacy-stories/` | **过时** | 75 个旧 Story（3月31日），已被 epic-1 完全替代 | **不要搜** |
| `_bmad-archive/test-artifacts/` | **过时** | 52 个测试产物 | 不要搜 |
| `_bmad-archive/archived-v2/` | **过时** | 45 个归档文件 | 不要搜 |
| `_bmad/` | **框架** | BMAD 框架代码（agent、workflow 定义） | 只读参考 |

### 修复方案

我建议创建一个 `.claude/rules/bmad-search-strategy.md`，内容大意是：

```
当 plan_kind=bmad-implementation 时，搜索优先级：
1. _bmad-output/implementation-artifacts/ — 当前 sprint 的 Story spec
2. _bmad-output/planning-artifacts/ — PRD、架构文档
3. _bmad-output/research/ — 调研报告
4. _bmad-archive/ — 已弃用，除非用户明确要求，否则不搜
```

同时在 CLAUDE.md 里加一段"BMAD 目录结构"说明。

> **需要你确认**：我可以现在就创建这个规则文件吗？还是你想先看看具体内容再批准？
> 
> 批注位置 ▼我希望我的 claude.md  变得干净，减少相关的幻觉，既不要锁死了注意力到一个文件上，但是也不要出现幻觉

---

## 回复批注 2：父目录方案（第四节 line 130）

> **你的批注**: 我觉得可行

收到，父目录挂载方案确认可行。

---

## 回复批注 3：父目录位置与部署（Q1 line 172）

> **你的批注**: 我只聚焦于一个问题，后面如果我新建其他学科的 vault，那么我的 Canvas learning system 如何部署，父目录的位置会影响这一点吗？

### 短回答

**不影响**。父目录放在哪里都行，只要 Docker 能挂载到它。

### 详细解释

你的 Canvas Learning System 有两大块：
- **系统**（代码 + Docker 容器）— 固定在 `canvas-learning-system/` 目录
- **笔记库**（vault 文件夹）— 可以放在任何地方

它们之间的关系就像"播放器"和"光盘"：
- 播放器（系统）装在一个固定位置
- 光盘（vault）可以放在任何抽屉里
- 你只需要告诉播放器"光盘在哪个抽屉"

具体来说：

**方案 A：vault 放在项目内（简单）**
```
canvas-learning-system/
├── vaults/               ← 所有 vault 在这里
│   ├── CS188/
│   ├── CS61B/
│   └── 线性代数/
├── backend/
├── frontend/
└── docker-compose.yml
```
- 优点：一个文件夹包含所有东西，备份简单
- 缺点：vault 和代码混在一起

**方案 B：vault 放在项目外（灵活）**
```
~/Documents/study-vaults/    ← vault 在这里
├── CS188/
├── CS61B/
└── 线性代数/

~/Desktop/canvas/canvas-learning-system/    ← 系统在这里
├── backend/
├── frontend/
└── docker-compose.yml
```
- 优点：笔记和代码分离，vault 可以放在 iCloud/Dropbox 同步
- 缺点：`.env` 里要写绝对路径

**两种方案对部署的影响**：

| 操作 | 方案 A（项目内） | 方案 B（项目外） |
|------|-----------------|-----------------|
| 新建 vault | `vaults/` 下直接创建 | 任意位置创建，改 `.env` 指向 |
| Docker 挂载 | `.env` 里 `VAULTS_ROOT=./vaults` | `.env` 里 `VAULTS_ROOT=~/Documents/study-vaults` |
| 备份 | 只备份一个目录 | 需要分别备份系统和 vault |
| 换电脑 | 整个项目复制过去 | 系统和 vault 分别复制 |
| 给别人用 | 对方 clone 项目就行 | 对方需要额外配置路径 |

> **需要你选择**：A（项目内）还是 B（项目外）？或者你有其他偏好？
> 
> 批注位置 ▼ 项目外

---

## 回复批注 4：实施顺序（Q2 line 185）

> **你的批注**: B

收到。一步到位做 Story 1.8（切换 API）+ Story 1.9（数据隔离）。

---

## 回复批注 5：一键部署脚本（Q3 line 195）

> **你的批注**: 一个问题，我开新的 vault 的话，你最好以插件或者相关脚本的方式，然后我给 claude code 阅读来帮我一键部署 Canvas learning system 到我当前所学习学科的路径

### 我的理解

你想要的流程是：
1. 你开了一门新课（比如"操作系统"）
2. 你告诉 Claude Code："帮我部署一个新的学习 vault 给操作系统课"
3. Claude Code 读取一个脚本/配置文件
4. 自动执行：创建 vault 目录 → 初始化模板 → 注册到后端 → 切换过去
5. 你在 Obsidian 里打开新 vault 就能直接用

### 现有基础

好消息是，后端的"零件"已经有了：

| 零件 | 状态 | 位置 |
|------|------|------|
| VaultInitService（创建目录+模板+CLAUDE.md） | ✅ 已实现 | `backend/app/services/vault_init_service.py` |
| setup-wizard 端点（创建+验证+健康检查） | ✅ 已实现 | `backend/app/api/v1/system.py:287` |
| 插件检测 | ✅ 已实现 | `vault_init_service.py:105-150` |
| vault 切换 API | 📋 Story 1.8 待实现 | — |
| LanceDB 隔离 | 📋 Story 1.9 待实现 | — |

缺的是**编排层**——把这些零件串起来的脚本。

### 方案设计

我建议创建一个 `scripts/deploy-vault.sh`（或者 Python 脚本），Claude Code 可以读取和执行：

```
用法：scripts/deploy-vault.sh <课程名> [vault路径]

示例：
  scripts/deploy-vault.sh 操作系统
  → 在 vaults/操作系统/ 下创建完整 vault
  → 调用 setup-wizard 初始化
  → 调用 vault/switch 切换过去
  → 输出 Obsidian 打开链接
```

脚本做的事情：
1. 在 `VAULTS_ROOT` 下创建以课程名命名的目录
2. 调用 `POST /api/v1/system/setup-wizard` 初始化 vault 结构
3. 调用 `POST /api/v1/vault/switch` 切换后端到新 vault（Story 1.8 实现后）
4. 打印 Obsidian URI 让你一键打开：`obsidian://open?vault=操作系统`

### 一个需要你确认的问题

> 你说"以插件或者相关脚本的方式" — 你更偏向哪种？
> 
> - **A: Shell 脚本**（`scripts/deploy-vault.sh`）— 你给 Claude Code 说"帮我跑 deploy-vault.sh 操作系统"
> - **B: Claude Code Skill**（`.claude/skills/deploy-vault.md`）— 你直接说 `/deploy-vault 操作系统`，Claude Code 自动执行
> - **C: 后端 API**（`POST /api/v1/vaults/create`）— 纯 API，前端或 Claude Code 都能调用
> 
> 建议：三个可以共存（C 是基础，A 包装 C，B 包装 A）。但优先做哪个？
> 
> 批注位置 ▼ B

---

## 附录：一键部署需要的完整"包裹"

根据 4 个 Agent 的调研，一个 CLS 兼容的 vault 需要包含：

```
<课程名>/
├── .obsidian/
│   ├── templates/
│   │   ├── concept.md          ← 概念笔记模板（含 mastery_score、FSRS 字段）
│   │   └── exam-board.md       ← 考察板模板
│   ├── community-plugins.json  ← 4 个必装插件列表
│   └── core-plugins.json       ← Bases 核心插件
├── raw/                        ← 原始笔记（导入用）
├── wiki/
│   ├── concepts/               ← 概念笔记（Templater 生成）
│   └── canvases/               ← Canvas 画布文件
├── outputs/
│   └── exam_boards/            ← 考察板
└── CLAUDE.md                   ← AI 使用指南（自动生成）
```

这些**全部由 `VaultInitService` 自动创建**，不需要手动操作。
