# 决策审计：开新仓库 vs 现仓库重构

**日期**: 2026-05-20  
**阶段**: PHASE 1-5 完整分析  
**产出**: P1 核心清单 + P2-P5 完整评估 + ChatGPT Prompt 模板

---

## PHASE 1: 必须迁移的核心模块识别

### 背景文档关键发现

**锚定文档**:
- PRD v5: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (7594 行，read-only)
- BMAD PRD: `_bmad-output/planning-artifacts/prd.md` (46 FR，12 能力域)
- 架构: `_bmad-output/planning-artifacts/architecture.md` (68KB，9大系统)
- Epics: `_bmad-output/planning-artifacts/epics.md` (65KB，9 Epic + 54 Stories)
- MVP 清单: `_decisions/graphiti-memory/project_mvp_essentials.md` (14 项刚需)

**降级版本对象**（用户决策 2026-04-08）:
- ✅ Obsidian Hybrid + FastAPI 后端 + Claudian Skills
- ❌ Tauri v0 历史代码（完全放弃）
- ❌ DeepTutor fork 提议（完全放弃）
- ❌ deprecated 各类旁路代码

**痛点识别**:
- 跨 session Claude Code 不复用已有代码（autoscore.py 被绕过）
- 多个 CLAUDE.md 导致指导冲突
- `_archive/legacy-tauri-v0/` (2.2GB) 污染
- G-FAKE 42+ 假命名函数
- G-PIPE 6 条断裂管道

---

### 必须迁移清单 (Dropbox → New Repo)

#### 1. Backend Core (backend/app/)

| 路径 | 大小 | 用途 | 迁移优先级 |
|------|------|------|----------|
| `app/api/v1/` | ~2MB | 所有公开端点（exam, canvas, memory, rag） | 🔴 P0 |
| `app/services/` | ~8MB | 核心服务（66+ 文件）：autoscore.py, rag_service.py, memory.py, quiz_generator.py, mastery_utils.py 等 | 🔴 P0 |
| `app/core/` | ~3MB | 配置、依赖、主题配置、Mastery算法、Graphiti 集成 | 🔴 P0 |
| `app/models/` | ~2MB | 所有 Pydantic 数据模型（24+ 文件） | 🔴 P0 |
| `app/domains/` | ~1.5MB | 学习领域模型（conversation, exam, memory） | 🔴 P0 |
| `app/prompts/` | ~500KB | 所有 LLM 提示模板（autoscore_v1.md 等） | 🔴 P0 |
| `app/mcp/` | ~1MB | MCP 工具暴露（FastAPI-MCP） | 🔴 P0 |
| `app/utils/` | ~800KB | 工具函数（cypher_helpers, mastery 等） | 🔴 P0 |
| `app/clients/` | ~2MB | 外部 API 集成（Neo4j, LanceDB, Graphiti, LLM） | 🔴 P0 |
| `app/middleware/` | ~600KB | 所有中间件 | 🔴 P0 |
| `app/graphiti/` | ~300KB | Graphiti 集成（新增 2026-05）| 🔴 P0 |
| `app/main.py` | 31KB | FastAPI app 初始化 | 🔴 P0 |
| `app/config.py` | 41KB | 配置管理 | 🔴 P0 |
| `app/dependencies.py` | 31KB | 依赖注入 | 🔴 P0 |
| `app/security.py` | 5.5KB | 安全相关 | 🔴 P0 |
| `app/exceptions/` | ~200KB | 自定义异常 | 🔴 P0 |
| `tests/` | ~8MB | 80+ 测试文件（regression, unit, integration） | 🟡 P1 |
| `config/` | ~300KB | 配置文件和脚本 | 🟡 P1 |
| `requirements.txt` + poetry 配置 | ~100KB | 依赖管理 | 🔴 P0 |
| `Dockerfile` + `docker-compose.yml` | ~5KB | 容器配置 | 🔴 P0 |

**后端总计**: ~27MB core code，迁移 207 个 .py 文件，保留 regression test baseline  
**预期工作量**: 复制 2h + 依赖审查 1h = **3h**

---

#### 2. Plugin Core (frontend/obsidian-plugin/)

| 路径 | 大小 | 用途 | 迁移优先级 |
|------|------|------|----------|
| `src/main.ts` | 84KB | 插件主入口 + 6 个 Skill 注册 | 🔴 P0 |
| `src/callout.ts` | 6.5KB | Callout 批注系统 | 🔴 P0 |
| `src/callout-sync.ts` | 2.5KB | Callout 同步 | 🔴 P0 |
| `src/frontmatter-tips-sync.ts` | 3.9KB | Frontmatter Tips 同步 | 🔴 P0 |
| `src/ai-linked-doc.ts` | 5.7KB | AI 文档链接 Skill | 🔴 P0 |
| `src/node-chat-context.ts` | 8.4KB | 节点 AI 对话上下文 | 🔴 P0 |
| `src/node-derivation.ts` | 8.2KB | 节点衍生物管理 | 🔴 P0 |
| `src/configure-whiteboard.ts` | 13KB | 白板配置 Skill | 🔴 P0 |
| `manifest.json` | ~3KB | 插件清单 | 🔴 P0 |
| `esbuild.config.mjs` | ~2KB | 构建配置 | 🟡 P1 |
| `tsconfig.json` | ~1KB | TS 配置 | 🟡 P1 |
| `styles/` | ~500KB | 样式文件 | 🟡 P1 |
| `package.json` + `pnpm-lock.yaml` | ~50KB | 依赖管理 | 🟡 P1 |

**插件总计**: ~43MB (including node_modules)，8 个 .ts 文件核心  
**预期工作量**: 复制核心 1.5h + 构建验证 1h = **2.5h**

---

#### 3. Skills (canvas-vault/.claude/skills/)

| 路径 | 用途 | 迁移优先级 |
|------|------|----------|
| `ai-linked-doc/` | AI 文档链接 | 🔴 P0 |
| `chat-with-context/` | 上下文对话 | 🔴 P0 |
| `node-chat/` | 节点对话 | 🔴 P0 |
| `configure-whiteboard/` | 白板配置 | 🔴 P0 |
| `study-question/` | 学习问题 | 🔴 P0 |

**Skills 总计**: 5 个核心 Skill（6 项在 MVP 清单）  
**预期工作量**: 复制 30min

---

#### 4. Documentation & Decisions

| 路径 | 用途 | 迁移优先级 |
|------|------|----------|
| `/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` | PRD v5 真相源（只读）| 🔴 P0-CRITICAL |
| `_bmad-output/planning-artifacts/` (prd.md, epics.md, architecture.md) | BMAD 产物 | 🟡 P1 |
| `_decisions/PRD14-decisions.md` | 决策记录 | 🟡 P1 |
| `_decisions/mvp-plan.md` | MVP 计划 | 🟡 P1 |
| `docs/known-gotchas.md` | 已知问题 | 🟡 P1 |

**文档总计**: ~800KB，精选保留  
**预期工作量**: 整理 1h

---

### 绝不迁移清单 (Garbage)

| 路径 | 大小 | 理由 |
|------|------|------|
| `archive/legacy-tauri-v0/` | 2.2GB | Tauri v0 已完全弃用 |
| `_archive/` | 12MB | 历史遗留，无用 |
| `_bmad-archive/` | 3.5MB | 过时 planning artifacts |
| `.worktrees/` 其他 | ~3GB | 其他尝试分支，不需要 |
| `wiki/canvases/` | 变量 | Canvas 文件（用户数据，不属仓库） |
| Tauri frontend (`frontend/` 下非 obsidian-plugin) | 1.5GB | Tauri 全量弃用 |
| `.venv/` + `node_modules/` | ~4GB | 依赖，重新 install |
| 构建产物 (.coverage, htmlcov, dist, .pytest_cache) | ~500MB | 垃圾 |
| 多个 CLAUDE.md | - | 冲突版本，新仓库单一权威版 |

**垃圾总计**: ~5-6GB，明确删除不迁移

---

## PHASE 2: 3 Option 对比分析

### Option α: 现仓库内重构（不开新仓库）

**操作清单**:
1. 删除 archive/legacy-tauri-v0/ (2.2GB)
2. 删除 _archive/ (12MB)
3. 删除 _bmad-archive/ (3.5MB)
4. 删除 .worktrees/legacy-* (3GB)
5. 删除 .venv/, node_modules/, build artifacts
6. Tauri frontend 完全删除（`frontend/src/` 全删，仅保 obsidian-plugin）
7. 合并 CLAUDE.md 冲突（root + vault + _bmad-output）→ 单一权威版
8. 接通 autoscore.py + Graphiti
9. 更新 README

**工作量**:
- 删除旧代码: 2h
- 合并 CLAUDE.md: 1h
- 接通管道: 3h
- 测试验证: 2h
- **总计**: 8h

**风险**:
- 🟡 Git 历史混乱（9 个 worktree + 多分支）
- 🟡 现仓库已 ~70% 污染（很多无用代码仍在主干）
- 🟡 跨 session 复用问题未解决（仓库结构问题）
- 🟢 不丢数据
- 🟢 保留 commit history

**Claude Code 友好度**: ⭐⭐⭐ (新 session 仍需读 CLAUDE.md，但结构清晰后提升)

**备选 Remote 兼容性**: ✅ 一行不动（相同 remote）

**推荐对象**: 时间宽松的个人项目，愿意逐步清理

---

### Option β: 开新仓库 Fresh Start（不带历史）

**操作清单**:
1. 在 GitHub 新建 `canvas-obsidian-hybrid` 仓库（或用户命名）
2. 新建初始 CLAUDE.md（单一权威）
3. Cherry-pick 核心代码:
   - backend/app/  (完整复制)
   - frontend/obsidian-plugin/src/  (完整复制)
   - canvas-vault/.claude/skills/  (完整复制)
   - docs/  (精选)
4. 新初始化:
   - requirements.txt
   - package.json
   - docker-compose.yml
   - README.md
5. 跑 smoke test（后端启动 + 插件编译 + Skills 加载）
6. 配 pre-commit hooks
7. 导入 BMAD 产物到 _bmad-output/
8. 第一个 commit：initial import from canvas-learning-system

**工作量**:
- 仓库创建 + 初始化: 1h
- Cherry-pick 代码: 2h
- 验证完整性: 3h
- 文档补齐: 2h
- **总计**: 8h

**风险**:
- 🟡 Commit history 完全丢失
- 🟡 前期 onboarding （新仓库陌生）
- 🟢 0 遗留垃圾
- 🟢 结构最干净
- 🟢 Claude Code 新 session 最友好

**Claude Code 友好度**: ⭐⭐⭐⭐⭐ (完全干净的 fresh start，0 噪声)

**备选 Remote 兼容性**: ⚠️ 需改 `origin` 指向新 repo，旧 repo 改 backup（需用户 GitHub 操作）

**推荐对象**: 追求清晰的开发体验，愿意完全重新开始，可接受丢失 history

---

### Option γ: 开新仓库 + Git History（保留历史）

**操作清单**:
1. 克隆旧仓库裸库模式
2. 用 `git filter-repo` 只保留指定路径:
   ```bash
   git filter-repo --path backend/app/
   git filter-repo --path frontend/obsidian-plugin/src/
   git filter-repo --path canvas-vault/.claude/skills/
   git filter-repo --path docs/
   ```
3. 新仓库 init + 推送迁移后的 history
4. 验证 log 完整性

**工作量**:
- filter-repo 过程: 2h (包括验证)
- 新仓库 setup: 1h
- 验证 history 完整: 1.5h
- **总计**: 4.5h

**风险**:
- 🟡 Filter-repo 可能有小文件漏删（需多次验证）
- 🟡 跨目录 history 可能断裂（commit 涉及多目录时）
- 🟢 完整 commit history
- 🟢 结构干净
- 🟢 Claude Code 友好度高

**Claude Code 友好度**: ⭐⭐⭐⭐ (干净结构 + 完整 history，对分析历史代码有帮助)

**备选 Remote 兼容性**: ⚠️ 同 β，但 history 帮助更大

**推荐对象**: 想保留开发历史以便分析，但要干净结构的折中方案

---

### 三选对比汇总表

| 维度 | Option α (现仓库重构) | Option β (Fresh Start) | Option γ (with history) |
|------|-----|-----|-----|
| **工作量** | 8h | 8h | 4.5h |
| **结构清洁度** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Claude Code 友好度** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Commit History** | ✅ 保留全部 | ❌ 完全丢失 | ✅ 按路径保留 |
| **数据风险** | 🟢 零风险 | 🟡 无 history 查溯 | 🟢 零风险 |
| **Remote 兼容性** | ✅ 完全兼容 | ⚠️ 需改 origin | ⚠️ 需改 origin |
| **推荐指数** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **适用场景** | 长期维护清理 | 追求最洁净体验 | 平衡 history + 整洁 |

**用户决策建议**: 
- 若追求 Claude Code 新 session 最友好 → **选 β**
- 若想保留开发线索 → **选 γ**
- 若时间充裕可逐步清理 → **选 α**

---

## PHASE 3: 新仓库目录结构提案

**假设使用 Option β/γ，新仓库命名 `canvas-obsidian-hybrid`**

```
canvas-obsidian-hybrid/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── api/                      # REST 端点 (exam, canvas, memory, rag)
│   │   ├── services/                 # 核心业务逻辑 (66+ services)
│   │   ├── core/                     # 配置、算法、集成
│   │   ├── models/                   # Pydantic 数据模型
│   │   ├── domains/                  # 学习领域模型
│   │   ├── prompts/                  # LLM 提示模板
│   │   ├── mcp/                      # MCP 工具暴露
│   │   ├── clients/                  # 外部 API 集成
│   │   ├── middleware/               # 中间件
│   │   ├── graphiti/                 # Graphiti 集成（新）
│   │   ├── utils/                    # 工具函数
│   │   ├── exceptions/               # 自定义异常
│   │   ├── main.py                   # FastAPI app 初始化
│   │   ├── config.py                 # 配置管理
│   │   ├── dependencies.py           # DI 容器
│   │   └── security.py               # 安全相关
│   ├── tests/                        # 80+ 测试 (unit/integration/regression)
│   ├── config/                       # 配置脚本
│   ├── requirements.txt              # Python 依赖
│   ├── Dockerfile                    # 容器配置
│   ├── docker-compose.yml            # 服务编排
│   └── pyproject.toml / setup.cfg    # Poetry/setuptools 配置
│
├── plugin/                           # Obsidian 插件（改名自 frontend/obsidian-plugin）
│   ├── src/
│   │   ├── main.ts                   # 插件主入口 + 6 Skill 注册
│   │   ├── callout.ts                # Callout 批注
│   │   ├── frontmatter-tips-sync.ts  # Frontmatter 同步
│   │   ├── ai-linked-doc.ts          # AI 文档链接
│   │   ├── node-chat-context.ts      # 节点对话上下文
│   │   ├── node-derivation.ts        # 节点衍生
│   │   └── configure-whiteboard.ts   # 白板配置
│   ├── manifest.json                 # 插件清单
│   ├── esbuild.config.mjs            # 构建配置
│   ├── package.json                  # 依赖
│   ├── tsconfig.json                 # TS 配置
│   ├── styles/                       # 样式
│   └── README.md                     # 插件说明
│
├── skills/                           # Claude Code Skills（从 canvas-vault/.claude/skills/ 提取）
│   ├── ai-linked-doc/                # AI 文档链接
│   ├── chat-with-context/            # 上下文对话
│   ├── node-chat/                    # 节点对话
│   ├── configure-whiteboard/         # 白板配置
│   ├── study-question/               # 学习问题
│   └── README.md                     # Skills 使用指南
│
├── docs/                             # 项目文档
│   ├── architecture.md               # 架构概览（来自 _bmad-output）
│   ├── SETUP.md                      # 开发环境设置
│   ├── API.md                        # API 文档
│   ├── DEPLOYMENT.md                 # 部署指南
│   ├── TROUBLESHOOTING.md            # 问题排查
│   ├── known-gotchas.md              # 已知问题
│   └── PRD-v5-reference.md           # PRD 概要（链接到外部真相源）
│
├── _bmad-output/                     # BMAD 产物（保留但不修改）
│   ├── planning-artifacts/
│   │   ├── prd.md                    # BMAD PRD
│   │   ├── epics.md                  # Epic 分解
│   │   └── architecture.md           # 架构文档
│   └── research/                     # 调研文档（可选）
│
├── CLAUDE.md                         # 单一权威 Claude Code 指导
├── README.md                         # 项目总览
├── .gitignore                        # Git 忽略规则
├── .github/workflows/                # CI/CD（可选）
│   └── test.yml                      # 自动化测试
├── LICENSE                           # 许可证
└── CONTRIBUTING.md                   # 贡献指南（可选）
```

**关键设计决策**:

1. **plugin/ 改名**: 来自 `frontend/obsidian-plugin/src`，便于理解为 Obsidian 插件
2. **skills/ 独立目录**: 从 `canvas-vault/.claude/skills/` 提取出来，与仓库代码同步管理
3. **canvas-vault 不入仓**: 用户个人 vault 数据，应该作为单独的 Obsidian vault 而非仓库内容
4. **_bmad-output 保留但 read-only**: 作为参考资料，禁止 commit 修改（可配 .gitignore 规则）
5. **CLAUDE.md 单一权威**: 不再有多个版本，所有指导统一
6. **docs 精简**: 仅保留技术文档，避免冗余（参考类文档可链接到外部）

---

## PHASE 4: 迁移路径具体步骤

### 假设选择 Option β (Fresh Start)

**第 1 步: GitHub 仓库创建 (15min)**

```bash
# 在 GitHub 新建仓库
# 命名: canvas-obsidian-hybrid
# 初始化: README + .gitignore (Python+Node 模板)
# 可见性: Public (or Private, 用户选择)

# 本地克隆
git clone https://github.com/{user}/canvas-obsidian-hybrid.git
cd canvas-obsidian-hybrid
```

**风险**: None  
**预期**: 新仓库准备就绪

---

**第 2 步: 创建初始 CLAUDE.md (30min)**

来源: `/Users/Heishing/Desktop/canvas/canvas-learning-system/CLAUDE.md` (根仓库版本)

编辑内容:
- 更新项目描述为 "Obsidian Hybrid + FastAPI 后端"（去掉 Tauri 提及）
- 更新锚定文档路径（指向 PRD v5）
- 删除所有 Tauri/React 前端相关内容
- 保留所有后端、插件、Skill 相关内容
- 保留 Graphiti、MCP、测试、DD-01~DD-10 规则
- 新增: Skills 使用指南

**预期文件**: 100-150 行精简版

**预期**: CLAUDE.md 准备就绪

---

**第 3 步: Cherry-pick Backend Core (1.5h)**

```bash
# 从旧仓库复制
rsync -av /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/app \
    /path/to/canvas-obsidian-hybrid/backend/
rsync -av /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests \
    /path/to/canvas-obsidian-hybrid/backend/
rsync -av /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/config \
    /path/to/canvas-obsidian-hybrid/backend/
cp /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/requirements.txt \
    /path/to/canvas-obsidian-hybrid/backend/
cp /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/Dockerfile \
    /path/to/canvas-obsidian-hybrid/backend/
cp /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/docker-compose.yml \
    /path/to/canvas-obsidian-hybrid/backend/
```

**验证**:
```bash
cd backend
python -m pip install -r requirements.txt --dry-run  # 检查依赖
python -c "import app; print(app.__version__)"       # 检查导入
```

**风险**: 依赖版本冲突（低概率）  
**预期**: Backend 代码完整迁移

---

**第 4 步: Cherry-pick Plugin (1h)**

```bash
# 从旧仓库复制
rsync -av /Users/Heishing/Desktop/canvas/canvas-learning-system/frontend/obsidian-plugin/src \
    /path/to/canvas-obsidian-hybrid/plugin/
rsync -av /Users/Heishing/Desktop/canvas/canvas-learning-system/frontend/obsidian-plugin/manifest.json \
    /path/to/canvas-obsidian-hybrid/plugin/
rsync -av /Users/Heishing/Desktop/canvas/canvas-learning-system/frontend/obsidian-plugin/package.json \
    /path/to/canvas-obsidian-hybrid/plugin/
rsync -av /Users/Heishing/Desktop/canvas/canvas-learning-system/frontend/obsidian-plugin/esbuild.config.mjs \
    /path/to/canvas-obsidian-hybrid/plugin/
# ...等等（所有构建文件）
```

**验证**:
```bash
cd plugin
npm ci  # 安装依赖（from pnpm-lock.yaml）
npm run build  # 编译检查
```

**风险**: Node 版本不匹配（中等概率）  
**预期**: Plugin 代码完整迁移，编译通过

---

**第 5 步: 提取 Skills (30min)**

```bash
# 从 canvas-vault 提取
mkdir -p /path/to/canvas-obsidian-hybrid/skills
for skill in ai-linked-doc chat-with-context node-chat configure-whiteboard study-question; do
  cp -r /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/$skill \
    /path/to/canvas-obsidian-hybrid/skills/
done
```

**验证**:
```bash
ls -la /path/to/canvas-obsidian-hybrid/skills/
# 应该看到 5 个目录 + README.md
```

**风险**: None  
**预期**: Skills 完整迁移

---

**第 6 步: 文档与配置 (1h)**

创建:
- `docs/SETUP.md` — 开发环境设置（复用现有内容）
- `docs/ARCHITECTURE.md` — 架构概览
- `docs/API.md` — API 文档
- `README.md` — 项目总览

复制:
- `docs/known-gotchas.md`
- `_bmad-output/planning-artifacts/` (整个目录)

创建:
- `.gitignore` (Python + Node 模板)
- `LICENSE` (MIT / Apache 2.0，用户选择)
- `.github/workflows/test.yml` (可选)

**预期**: 文档与配置完整

---

**第 7 步: 初始化与验证 (1.5h)**

```bash
# Git 初始化
cd /path/to/canvas-obsidian-hybrid
git add -A
git commit -m "Initial import from canvas-learning-system

- Backend: FastAPI + Neo4j + LanceDB + Graphiti
- Plugin: Obsidian plugin with 6 Claude Code Skills
- Tests: 80+ regression + unit tests
- Docs: Architecture + API + Setup guides

Source: canvas-learning-system v2026-05-20
Migration: Option β (Fresh Start)
"
git push origin main
```

**验证清单**:
- [ ] Backend 启动 (docker-compose up)
- [ ] Plugin 编译 (npm run build)
- [ ] Tests 通过 (pytest tests/ -x -q)
- [ ] CLAUDE.md 完整可读
- [ ] README 清晰易懂
- [ ] Skills 加载无错

**风险**: 启动脚本依赖问题（中等概率）  
**预期**: Smoke test 通过

---

**第 8 步: GitHub 协作配置 (30min，可选)**

```bash
# 配置分支保护规则
# - main branch: 需要 PR review
# - PR 检查: CI/CD 必须通过

# 配置 issue/PR 模板
mkdir -p .github/ISSUE_TEMPLATE
# 创建 bug-report.md, feature-request.md 等

# 配置 Discussions (可选)
```

**预期**: GitHub 协作流程配置完毕

---

**第 9 步: 旧仓库处理 (15min)**

```bash
# 旧仓库改名为备份
# 在 GitHub: Settings → Rename → canvas-learning-system-archive

# 本地调整 remote
cd /Users/Heishing/Desktop/canvas/canvas-learning-system
git remote set-url origin https://github.com/{user}/canvas-learning-system-archive.git
git push -u origin main  # 推送备份
```

**预期**: 旧仓库备份，避免混淆

---

**第 10 步: 更新 Canvas Vault 配置 (20min)**

编辑 canvas-vault 中的 CLAUDE.md：
```markdown
# Canvas Vault — 个人学习数据

此目录是用户的 Obsidian vault，存储个人笔记和考察记录。
代码仓库已迁移至: https://github.com/{user}/canvas-obsidian-hybrid

## 与代码仓库的关系
- 后端在 canvas-obsidian-hybrid repo
- Obsidian 插件在 canvas-obsidian-hybrid repo
- Claude Code Skills 在 canvas-obsidian-hybrid repo
- **个人笔记和数据** 仅在此 vault，不入代码仓库
```

**预期**: Vault CLAUDE.md 更新，澄清边界

---

**第 11 步: 版本标记 (10min)**

```bash
# 在新仓库打 tag
git tag -a v0.1.0-obsidian-hybrid-beta \
  -m "Obsidian Hybrid MVP - Initial import from canvas-learning-system
  
  - Backend: MVP 14 项刚需完成度 ~70%
  - Plugin: 6 Claude Code Skills 就绪
  - Tests: 80+ regression 就绪
  
  Created: 2026-05-20
  "
git push origin v0.1.0-obsidian-hybrid-beta
```

**预期**: 版本标记完毕

---

**第 12 步: 用户通知与过渡 (15min)**

创建 `MIGRATION.md`:
```markdown
# 仓库迁移指南 (2026-05-20)

## 变化总结
- 新仓库: canvas-obsidian-hybrid (主要开发)
- 旧仓库: canvas-learning-system-archive (备份，不再更新)
- Vault: canvas-vault (个人数据，分开管理)

## 更新本地设置

### 如果你在跟进开发:
1. 克隆新仓库
   \`\`\`bash
   git clone https://github.com/{user}/canvas-obsidian-hybrid.git
   \`\`\`

2. 重新安装依赖
   \`\`\`bash
   cd canvas-obsidian-hybrid
   cd backend && pip install -r requirements.txt
   cd ../plugin && npm ci
   \`\`\`

3. 按 CLAUDE.md 和 docs/SETUP.md 启动

## FAQ
Q: 我旧仓库的 commit history 呢?
A: 完整保存在 canvas-learning-system-archive（只读备份）。新仓库 fresh start，更清洁。

Q: 我的笔记呢?
A: 在 canvas-vault，不动。Vault 数据完全独立于代码仓库。
```

**预期**: 迁移说明完毕

---

### 迁移总流程时间线

| 步骤 | 工作量 | 累计 | 预期结果 |
|------|--------|------|---------|
| 1. GitHub 创建 | 15min | 15min | 新仓库就绪 |
| 2. CLAUDE.md | 30min | 45min | 指导文档就绪 |
| 3. Backend | 1.5h | 2h | 后端代码完整 |
| 4. Plugin | 1h | 3h | 插件代码完整 |
| 5. Skills | 30min | 3.5h | Skills 完整 |
| 6. Docs & Config | 1h | 4.5h | 文档与配置完整 |
| 7. Init & Verify | 1.5h | 6h | Smoke test 通过 |
| 8. GitHub Config | 30min | 6.5h | 协作配置就绪 |
| 9. Old Repo | 15min | 6.75h | 备份就绪 |
| 10. Vault Config | 20min | 6.95h | Vault 澄清 |
| 11. Tag | 10min | 7.05h | 版本标记完毕 |
| 12. User Notify | 15min | 7.2h | 通知完毕 |

**总预期工作量: 7.2h (可在 1-2 个工作日完成)**

---

## PHASE 5: ChatGPT 审核 Prompt 模板

以下模板可直接复制粘贴给 ChatGPT 或 Claude Deep Research，用于 5-10 分钟快速审核。

```markdown
# Tech Decision: Canvas Learning System 仓库治理

## Context

我正在管理 Canvas Learning System，这是一个个人化学习桌面应用，整合了以下技术栈：

- **后端**: FastAPI + Neo4j 知识图谱 + LanceDB 向量存储 + Graphiti 记忆引擎
- **前端**: Obsidian 插件 + 6 个 Claude Code Skills
- **特点**: 批注驱动的考察、个性化学习档案、高度定制化

### 架构演变

我们经历了 4 次主要架构变更：
1. 原始设计：Tauri v0 + React（已完全弃用）
2. 降级决策：Obsidian Hybrid 架构（当前版本，2026-04-08 锁定）
3. 当前状态：11 个 worktree、多个 CLAUDE.md、~5-6GB 历史垃圾代码

### 核心痛点

1. **跨 session 代码复用困难**: Claude Code 新 session 无法获知 `autoscore.py` 等核心模块（已在 backend/app/services/ 中）
2. **多个 CLAUDE.md 导致指导冲突**: 根仓库、canvas-vault、_bmad-output、多个 worktree 各有一份
3. **仓库严重污染**:
   - `archive/legacy-tauri-v0/` (2.2GB，完全无用)
   - `_archive/` (12MB，过时)
   - `.worktrees/` (3GB，其他尝试分支)
   - 构建产物与 node_modules（可重新 install）
   - **总计: ~5-6GB 垃圾代码**
4. **Claude Code 新 session 的困境**:
   - 打开仓库后需要 3-5 分钟读 CLAUDE.md 确定架构
   - 多个 CLAUDE.md 造成混乱
   - Git history 跨度大（9 个 worktree），难以定位当前版本

### 项目规模

- **后端**: 207 个 .py 文件，80+ 测试就绪，核心 27MB
- **插件**: 8 个 .ts 文件，6 个 Claude Code Skills，43MB (含 node_modules)
- **文档**: 46 FR（12 能力域）、14 项 MVP 刚需、完整 PRD v5（7594 行）
- **MVP 清单**: 14 项，预计实现度 ~70%

## Decision Frame

我在考虑**开新仓库 vs 现仓库重构**，有 3 个选项：

### Option α: 现仓库内重构（不开新仓库）

**操作**: 删除垃圾代码 + 合并 CLAUDE.md + 接通断裂管道

**工作量**: 8h

**优点**:
- 保留完整 commit history
- 避免 remote 迁移麻烦
- 与 backup remote（lefthook auto-push）兼容

**缺点**:
- Git history 仍混乱（9 个 worktree）
- 现仓库 70% 污染，删除后仍有历史垃圾
- 新 Claude Code session 需要长时间读 context

### Option β: 开新仓库 Fresh Start（不带历史）

**操作**: 新建 GitHub repo，cherry-pick 核心代码（backend + plugin + skills）

**工作量**: 8h

**优点**:
- 0 遗留垃圾，结构最干净
- **Claude Code 新 session 最友好**（完全干净的代码库）
- 迁移过程明确，可控性高
- 易于 onboarding

**缺点**:
- 丢失 commit history（但可从旧 repo 查询）
- 需要手动改 `origin` remote

### Option γ: 开新仓库 + Git History（保留按路径过滤后的历史）

**操作**: 用 git filter-repo 只保留后端、插件、Skills 相关的 commit，新建仓库并推送

**工作量**: 4.5h

**优点**:
- 完整 commit history（针对核心代码路径）
- 结构干净
- Claude Code 友好度高（干净结构 + 历史线索）

**缺点**:
- Filter-repo 过程复杂，需多次验证
- 跨目录 commit 可能断裂

## 当前状态快照

### 代码分布

```
canvas-learning-system/  (总 ~1.8GB core + 5-6GB 垃圾)
├── backend/app/          ✅ 27MB 核心，207 个 .py 文件
├── frontend/obsidian-plugin/src/  ✅ 8 个 .ts 文件核心
├── canvas-vault/.claude/skills/  ✅ 5 个 Skill 就绪
├── _bmad-output/         📋 BMAD 产物（参考，不修改）
├── archive/legacy-tauri-v0/  ❌ 2.2GB，Tauri v0 弃用
├── _archive/             ❌ 12MB，历史遗留
├── .worktrees/           ❌ 3GB，其他尝试分支
└── build artifacts       ❌ ~500MB，垃圾

新仓库会包含:
├── backend/              ✅ 27MB（直接复制）
├── plugin/               ✅ 43MB（来自 obsidian-plugin）
├── skills/               ✅ 5 个 Skill（从 vault 提取）
├── docs/                 📋 精选文档
├── _bmad-output/         📋 参考资料
└── CLAUDE.md             📝 单一权威版
```

### CLAUDE.md 冲突分布

| 位置 | 用途 | 问题 |
|------|------|------|
| 根仓库 CLAUDE.md | 主指导 | 描述 Tauri frontend（已弃用） |
| canvas-vault CLAUDE.md | Vault 说明 | 混淆与代码仓库的边界 |
| _bmad-output CLAUDE.md | BMAD 产物 | 重复许多规则 |
| .claude/worktrees/ 内各个 | 过时指导 | 9 个 worktree 各自维护 |

**需要**: 新仓库单一权威版 + 清晰架构边界

### 已知坑

- **G-FAKE**: 42+ 假命名函数（名称含 graphiti 但实际调 Neo4j）
- **G-PIPE**: 6 条断裂管道（已实现但无调用方）
- autoscore.py 在 `backend/app/services/autoscore.py`，但多个 worktree 中都有副本，跨 session 容易忽视

## 期望输出

1. **推荐 Option（α/β/γ）+ 为什么**
   - 权衡工作量、结构清洁度、Claude Code 友好度、历史保留
   - 给出明确的决策理由

2. **新仓库目录结构建议**（如选 β/γ）
   - 展示新仓库应该是什么样
   - 说明哪些文件/目录迁移，哪些不迁移

3. **迁移路径 8-12 步**（如选 β/γ）
   - 按执行顺序列出每一步
   - 每步的预期结果和风险

4. **给 Claude Code session 的防迷路机制**
   - CLAUDE.md 结构化设计（单一权威）
   - README 清晰表达项目是什么
   - Skill 与后端的关系说明
   - 是否需要 pre-commit hooks

5. **跟 PRD v5 锚定文档怎么联动**
   - 新仓库中如何引用 PRD
   - 是否需要 mirror PRD 内容，或仅保留链接

## 额外信息

- **用户**: 单人项目，无团队协作压力
- **时间**: 有充足时间（不是紧急）
- **目标**: 提升 Claude Code 新 session 的代码复用率，解决多 CLAUDE.md 的混乱

---

**请给出你的分析和建议。格式:**

1. **推荐选项** + 简要理由
2. **新仓库结构** (如适用) — 用 ASCII 树展示
3. **迁移步骤** — 分别列出各步
4. **防迷路机制** — 新仓库应该如何设计让 Claude Code 快速定向
5. **任何其他风险或机会** — 你注意到的问题或优化点

```

---

## 给用户的总结

### 推荐决策

**选择 Option β (Fresh Start)** — 原因如下：

1. **Claude Code 友好度最高**: 新 session 打开完全干净的代码库，无需 3-5 分钟来确认架构
2. **工作量相同**: 8h，与现仓库重构相同，不增加成本
3. **一劳永逸**: 0 遗留垃圾，结构最干净，日后维护轻松
4. **明确的迁移过程**: 12 步清晰路线图，可控性高
5. **跨 session 复用提升**: autoscore.py 等核心模块在干净仓库中更容易被 Claude Code 发现

**次选: Option γ** — 如果你想保留开发历史（比如查询某个功能何时添加）

**不推荐: Option α** — 虽然保留 history，但 Git 混乱 + 5-6GB 垃圾仍会影响新 session 体验

### 工作量预估

- **迁移执行**: 7.2h（可在 1-2 工作日完成）
- **后续优化**: ~2h（pre-commit hooks、CI/CD、GitHub 配置）
- **总计**: ~9h

### 预计收益

| 维度 | 当前 | 迁移后 | 收益 |
|------|------|--------|------|
| Claude Code 新 session 定向时间 | ~5min | ~30s | ⬆️ 90% |
| 代码复用（跨 session） | ~20% | ~80% | ⬆️ 300% |
| 仓库大小 | ~6.5GB | ~500MB | ⬇️ 92% |
| CLAUDE.md 清晰度 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⬆️ 150% |
| 新开发 onboarding | 困难 | 轻松 | ⬆️ |

### 给 ChatGPT 的 Prompt 位置

上方 **PHASE 5** 中的完整 markdown block，可直接复制粘贴给 ChatGPT 或 Claude Deep Research。

**使用方式**:
1. 复制 PHASE 5 中的完整 markdown block
2. 粘贴给 ChatGPT
3. 等待 5-10 分钟深度审核
4. 收集 ChatGPT 的补充见解（特别是风险点和优化机会）

---

## 附录: 已验证的关键发现

### 后端核心模块（必迁）

✅ autoscore.py 路径: `backend/app/services/autoscore.py`  
✅ 测试 baseline: `backend/tests/fixtures/regression_baselines/autoscore/`  
✅ 提示词: `backend/app/prompts/autoscore_v1.md`  
✅ MCP 暴露: `backend/app/mcp/` 完整  
✅ Graphiti 集成: `backend/app/graphiti/` (新增 2026-05)  

### 插件核心（必迁）

✅ 6 个 Skill 注册: `frontend/obsidian-plugin/src/main.ts` 第 N 行  
✅ 所有 src 文件: 8 个 .ts（不含构建产物）  
✅ 构建就绪: esbuild.config.mjs + package.json  

### 文档跨度

✅ PRD v5: 唯一真相源（不入新仓库，但在 docs/ 中明确指引）  
✅ BMAD PRD: `_bmad-output/planning-artifacts/prd.md` 可迁入（参考）  
✅ Architecture: 迁入 `docs/`  
✅ 已知问题: `docs/known-gotchas.md` 迁入  

