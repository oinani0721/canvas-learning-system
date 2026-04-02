# Agent Team 工作流审计报告

> Date: 2026-03-31
> Scope: Phase 3 Pipeline Repair (10 commits, 4e09573..fb7efcd)
> Method: 3 parallel adversarial audit agents + local evidence analysis

---

## Executive Summary

Phase 3 的代码产出**质量可用**（73% 真实测试，80% 管道连通），但开发工作流**严重偏离设计**：

| 设计 | 现实 |
|------|------|
| Ralph Runner 外部循环自动迭代 | 只跑了 iteration 0 就停了，后续全手动 |
| Claude Code Native Agent Teams 多进程协作 | 从未启用，用的是普通 Agent subagent |
| Composite Oracle 变异测试验证每次编辑 | 从未运行（工具未安装/venv 路径断裂） |
| 13 条 DD 开发纪律 hook 强制执行 | DD-12/DD-13 声称有 hook，实际已被移除 |
| 每轮 Graphiti search_memory_facts | Phase 3 开发中未执行 |
| 独立 Agent 对抗性代码审查 | 10 commits 无任何 [Code-Review] 记录 |

**基础设施膨胀**：62% 的工作流基础设施是死代码/过时代码（11,446 / 18,374 行）。

---

## 1. 外部循环 + 内部循环：是否按设计运行？

### 1.1 外部循环（Ralph Runner）— 未运行

**设计**：`ralph-runner.sh` 循环最多 30 次，每次 `claude -p "/auto-epic"`，自动 commit `ralph-loop: iteration N`。

**现实**：
- `5d7fef9` (03-30 05:54): `ralph-loop: iteration 0` — 仅改 PROGRESS.md + ralph-runner.sh
- 后续 10 commits 全是 `feat(EpicN):` 格式，作者 `root@Frick.localdomain`（Mac）
- 时间跨度 13h（21:31→10:41），手动逐 Epic 执行
- Deep research 报告自述："Current gap: outer loop is manual"

**根因**：Ralph Runner 在 Mac 上首次执行遇到问题后未被修复。脚本依赖 `docker compose restart neo4j-test`，但 Mac 上 Docker 配置可能不同。

### 1.2 内部循环（Agent Teams）— 未使用原生功能

**设计**：`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 启用多进程 Agent Teams（Team Lead + Builder + Test Writer + Critic）。

**现实**：
- `.claude/settings.json` 无 `teammateMode` 配置
- 项目自己的稳定性报告结论：Windows in-process 模式致命
- 实际使用的是 Claude Code 的 `Agent()` 子 agent 工具（单 session 内串行/并行派生）
- 这不是 "Agent Teams"，而是普通的子 agent 调用

### 1.3 Composite Oracle（变异测试）— 未运行

**设计**：PostToolUse hook 每次编辑后运行 pytest + mutmut + vulture（后端）或 stryker + knip（前端）。

**现实**：
- `post-tool-router.sh` 存在但有两个致命问题：
  1. **venv 路径断裂**：脚本直接调用 `python -m pytest` / `mutmut run`，未激活 venv
  2. **180 秒超时**：每次文件编辑都跑变异测试，极其耗时
- `stop-test-runner.js` 同样有 venv 路径问题
- 没有任何 commit 消息提到变异测试结果

---

## 2. 开发成果是否有用？

### 2.1 代码质量：可用，但需补充审查

**Test Facade 审计结果**：

| 文件 | Epic | 断言数 | 真实% | 判定 |
|------|------|--------|-------|------|
| test_acp_prompt_externalization.py | 3 | 26 | 85% | **REAL** |
| test_group_id_dynamic_binding.py | 6 | 27 | 100% | **REAL** |
| test_cross_canvas_removal.py | 2.1 | 10 | 70% | **REAL** |
| test_epic36_gap_coverage.py | 36 | 28 | 79% | **REAL** |
| test_profile_source_ids.py | 1.2 | 30 | 73% | PARTIAL |
| test_textbook_removal.py | 2.2 | 12 | 75% | PARTIAL (含 1 个空测试) |
| test_hybrid_search_activation.py | 5 | 28 | 50% | PARTIAL (50% inspect.getsource) |
| test_neo4j_fulltext_index.py | 4 | 12 | 25% | PARTIAL (mock SUT 内部方法) |
| **合计** | | **173** | **73%** | **0 facade** |

**结论**：没有完全 facade 的测试，73% 的断言测试真实行为。最弱的是 `test_neo4j_fulltext_index.py`（mock 了 SUT 内部方法）。

### 2.2 管道打通性：80% 连通

| 函数 | 文件 | 判定 |
|------|------|------|
| `extract_canvas_name()` | subject_config.py | **CONNECTED** (6 调用点) |
| `ensure_fulltext_index()` | memory_service.py | **CONNECTED** (main.py lifespan) |
| `sanitize_subject_name()` | subject_config.py | **CONNECTED** (10+ 调用点) |
| `_load_prompt_file()` | question_generator.py | **CONNECTED** (5 层 prompt 加载) |
| `onNavigateToSource` | LearningProfile.tsx | **DEAD CODE** (App.tsx 从未传入此 prop) |

**关键缺陷**：Epic 1 的核心功能 "Profile Click-to-Jump" 在后端完整实现，但前端 `onNavigateToSource` callback 从未被 `App.tsx` 传入，导致导航按钮永远不会渲染。**用户不可见的功能 = 无效功能**。

### 2.3 重复代码

`subject_resolver.py` 有私有方法 `_extract_canvas_name()` 与 `subject_config.py` 中的 `extract_canvas_name()` 重复。

---

## 3. 严重问题清单

### CRITICAL

#### C1: Composite Oracle 从未运行
- **问题**：变异测试是代码质量的核心保障，但从未触发
- **影响**：77+ tests 中有 27% 的断言是 trivial，无法确认是否有漏洞
- **文件**：`.claude/hooks/post-tool-router.sh`
- **修复**：Mac 上安装 mutmut/vulture，修复脚本路径；考虑只在 commit 前运行而非每次编辑

#### C2: DD-12/DD-13 规则声称有 hook 执行，实际不存在
- **问题**：`CLAUDE.md` 和 `development-discipline.md` 声称 "PreToolUse hook exit 2 阻断"，但 `pretool-guard.js` v3 已移除这些检查
- **影响**：规则是"幽灵执行"——AI 以为有约束，实际无约束
- **修复**：要么恢复 hook 代码，要么移除虚假声称

#### C3: Epic 1 前端未接线
- **问题**：`onNavigateToSource` prop 定义了但 `App.tsx` 从未传入
- **影响**：Profile Click-to-Jump 功能在用户端完全不可见
- **修复**：在 `App.tsx:1164-1169` 渲染 `<LearningProfile>` 时传入导航回调

### HIGH

#### H1: 基础设施膨胀 62%
- **问题**：11,446 行死代码/过时代码
- **分布**：
  - 归档 Agent: 5,256 行（canvas-orchestrator 3,232 行）
  - WSL2 脚本: 799 行
  - 过时 Deep Research 文档: ~3,800 行
  - 断裂 Hook: 105 行
  - 规则冗余: ~200 行
- **修复**：删除归档 Agent + WSL2 脚本，归档过时文档

#### H2: 规则链过长导致 LLM "Lost in the Middle"
- **问题**：4 层 CLAUDE.md（489 行）+ 5 个 rules 文件（336 行）= 825 行规则
- **冗余**：DD-01~DD-10 在 3 个文件中重复定义，Graphiti 协议在 5 个文件中提及
- **影响**：LLM 实际执行率极低（Phase 3 开发中多条规则未执行）
- **修复**：合并为 2 个文件（1 个 CLAUDE.md + 1 个 rules 文件），去重

#### H3: 外部循环空壳
- **问题**：Ralph Runner 设计但不可用
- **影响**：没有自动化持续开发能力
- **修复**：Mac 上端到端验证 ralph-runner.sh + auto-epic

### MEDIUM

#### M1: 无对抗性代码审查记录
- Phase 3 的 10 commits 无 [Code-Review] Graphiti 记录

#### M2: Graphiti 每轮搜索协议未执行
- Phase 3 开发中 `search_memory_facts` 未被调用

#### M3: `test_textbook_removal.py` 含空测试
- `test_dependencies_imports_without_textbook` 删除 sys.modules 但不重新导入，永远通过

#### M4: `test_hybrid_search_activation.py` 50% 是 `inspect.getsource` 检查
- 检查源码文本而非运行时行为，重构后会误报

---

## 4. Mac 开发环境迁移指南

### 4.1 Docker Services

```bash
# docker-compose.yml 中已定义的服务
neo4j (7689)      # 开发用 Neo4j — Mac Docker Desktop 直接可用
neo4j-test (7692) # 测试用 Neo4j — 需验证 Docker 网络
ollama (11434)    # 本地 LLM — Mac 推荐原生安装：brew install ollama
```

### 4.2 Claude Code 配置

| 项目 | Windows | Mac | 备注 |
|------|---------|-----|------|
| `$CLAUDE_PROJECT_DIR` | 自动设置 | 自动设置 | Hook 脚本引用此变量，两端兼容 |
| Hook 脚本 (.sh) | Git Bash | 原生 bash | Mac 原生支持 |
| Hook 脚本 (.js) | Node.js | Node.js | 需确认 `node` 在 PATH 中 |
| Agent Teams tmux | 不支持（in-process fallback） | **支持** | Mac 可真正使用 Agent Teams |
| `PYTHONUTF8=1` | 必需 | 不需要 | Mac 默认 UTF-8 |

### 4.3 工具安装（启用 Composite Oracle）

```bash
# Python 工具
pip install mutmut vulture pytest hypothesis

# 前端工具（已在 node_modules 中）
npx stryker run  # 需要 stryker.conf.js
npx knip          # 需要 knip.json
```

### 4.4 WSL2 文件处理

以下文件在 Mac 上不需要，建议移至 `_archive/windows/`：
- `wsl2-setup.sh` (188 行)
- `wsl2-verify.sh` (209 行)
- `wsl2-migrate-claude.sh` (353 行)

### 4.5 Agent Teams on Mac

Mac 有原生 tmux 支持，Agent Teams 在 tmux 模式下比 Windows in-process 模式**稳定得多**：
- Teammates 是独立 OS 进程，有自己的上下文压缩
- 不会出现 Windows 的 "in-process 上下文耗尽无法恢复" 问题
- 设置：`export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

---

## 5. 改进建议优先级

| # | 行动 | 影响 | 工作量 |
|---|------|------|--------|
| 1 | 修复 Epic 1 前端接线 (onNavigateToSource) | 恢复用户可见功能 | 小 |
| 2 | 删除归档 Agent + WSL2 脚本 (6,055 行) | 减少上下文噪音 | 小 |
| 3 | 合并/去重 CLAUDE.md 规则链 | 提高 LLM 规则执行率 | 中 |
| 4 | 修复 post-tool-router.sh venv 路径 | 启用变异测试 | 中 |
| 5 | 移除 DD-12/DD-13 虚假 hook 声称 | 消除"幽灵规则" | 小 |
| 6 | 归档 15 篇过时 Deep Research 文档 | 减少仓库噪音 | 小 |
| 7 | Mac 端到端验证 Ralph Runner + auto-epic | 启用自动化开发 | 大 |

---

## Appendix: 审计方法

- **Agent A (Test Facade)**：逐文件读取 8 个测试文件，分类每个 assert 为 REAL/TRIVIAL
- **Agent B (Pipeline)**：Grep 追踪 5 个新函数的调用链到 API 入口
- **Agent C (Dead Infra)**：审计 hooks/agents/docs/scripts/rules 的引用关系
- **Gemini Deep Research**：全面工作流审计（pending，Store 同步中）
