# BMad Orchestrator

全自动化 24/7 开发系统 - 基于 LangGraph StateGraph 的 SM→PO→Dev→QA 工作流编排器。

## 概述

BMad Orchestrator 提供完全自动化的 Epic 开发工作流：

```
SM → PO → Analysis → DEV → QA → MERGE → COMMIT → COMPLETE
                      ↓
                     FIX (CONCERNS 循环)
                      ↓
                    HALT (失败处理)
```

### 核心特性

- **9 个工作流节点** - SM、PO、Analysis、DEV、QA、Merge、Commit、Fix、Halt
- **自动依赖分析** - 检测文件冲突，生成并行批次
- **三种执行模式** - parallel（并行）、linear（串行）、hybrid（混合）自动选择
- **崩溃恢复** - SqliteSaver 检查点持久化
- **独立上下文** - 每个 Claude 会话 200K tokens 隔离
- **Git Worktree 隔离** - 无冲突的并行开发

## 安装

```bash
# 确保已安装 LangGraph
pip install langgraph

# 模块位于 src/bmad_orchestrator/
```

## 快速开始

### 1. 预览模式（分析依赖）

```bash
python -m bmad_orchestrator epic-develop 15 --stories 15.1 15.2 15.3 --dry-run
```

输出示例：
```
============================================================
BMad Dependency Analysis Report
============================================================

Stories Analyzed: 3
Conflicts Found: 1
Batches Generated: 2
Recommended Mode: HYBRID

Parallel Batches:
  Batch 1: 15.1, 15.2
  Batch 2: 15.3

Conflicts:
  15.1 ↔ 15.3: src/canvas_utils.py

============================================================
```

### 2. 启动全自动工作流

```bash
python -m bmad_orchestrator epic-develop 15 --stories 15.1 15.2 15.3
```

### 3. 监控进度

```bash
python -m bmad_orchestrator epic-status epic-15
```

### 4. 恢复中断的工作流

```bash
python -m bmad_orchestrator epic-resume epic-15
```

### 5. 停止工作流

```bash
python -m bmad_orchestrator epic-stop epic-15
```

## CLI 命令参考

### epic-develop

启动 Epic 全自动化工作流。

```bash
python -m bmad_orchestrator epic-develop <epic_id> \
    --stories <story_ids> \
    [--base-path <path>] \
    [--worktree-base <path>] \
    [--max-turns <num>] \
    [--mode parallel|linear|hybrid] \
    [--no-ultrathink] \
    [--dry-run]
```

**参数**:
- `epic_id`: Epic ID（如 "15"）
- `--stories`: Story IDs（空格分隔，如 "15.1 15.2 15.3"）
- `--base-path`: 项目根目录（默认: 当前目录）
- `--worktree-base`: Worktree 父目录（默认: base_path 父目录）
- `--max-turns`: 每个 Claude 会话最大轮数（默认: 200）
- `--mode`: 执行模式（默认: 自动检测）
- `--no-ultrathink`: 禁用 UltraThink
- `--dry-run`: 预览模式，只分析不执行

### epic-status

查看工作流状态。

```bash
python -m bmad_orchestrator epic-status <thread_id> [--db <path>]
```

**参数**:
- `thread_id`: 工作流线程 ID（如 "epic-15"）
- `--db`: 检查点数据库路径（默认: bmad_orchestrator.db）

### epic-resume

恢复中断的工作流。

```bash
python -m bmad_orchestrator epic-resume <thread_id> [--db <path>]
```

### epic-stop

停止运行中的工作流。

```bash
python -m bmad_orchestrator epic-stop <thread_id>
```

## 架构

### 模块结构

```
src/bmad_orchestrator/
├── __init__.py          # 包导出
├── __main__.py          # CLI 入口
├── cli.py               # CLI 命令实现
├── state.py             # State Schema 和 Reducers
├── nodes.py             # 9 个 StateGraph 节点
├── graph.py             # StateGraph 构建和编译
├── session_spawner.py   # Claude CLI 会话管理
├── dependency_analyzer.py  # 依赖分析和冲突检测
└── README.md            # 本文档
```

### StateGraph 工作流

```
                    ┌─────────┐
                    │   SM    │ ← Scrum Master: 生成 Story 草稿
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │   PO    │ ← Product Owner: 审批 Story
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │Analysis │ ← 分析依赖、生成批次、选择模式
                    └────┬────┘
                         │
                    ┌────▼────┐
              ┌────►│   DEV   │ ← 开发（并行批次）
              │     └────┬────┘
              │          │
              │     ┌────▼────┐
              │     │   QA    │ ← 质量审查
              │     └────┬────┘
              │          │
              │          ├── PASS/WAIVED ─────┐
              │          │                    │
              │     ┌────▼────┐          ┌────▼────┐
              │     │   FIX   │          │  MERGE  │ ← Git 合并
              │     └────┬────┘          └────┬────┘
              │          │                    │
              │          │               ┌────▼────┐
              └──────────┘               │ COMMIT  │ ← 最终提交
                                         └────┬────┘
                                              │
                    ┌─────────┐          ┌────▼────┐
                    │  HALT   │          │COMPLETE │
                    └─────────┘          └─────────┘
                    ↑ 失败处理
```

### State Schema

```python
class BmadOrchestratorState(MessagesState):
    # 基础信息
    session_id: str
    epic_id: str
    story_ids: List[str]
    base_path: str
    worktree_base: str

    # 阶段状态
    current_phase: str  # SM, PO, Analysis, DEV, QA, Merge, Commit, Halt
    sm_status: str      # pending, in_progress, completed, failed
    po_status: str
    dev_status: str
    qa_status: str
    merge_status: str

    # 工作产出
    story_drafts: List[StoryDraft]
    approved_stories: List[str]
    dev_outcomes: Annotated[List[DevOutcome], merge_dev_outcomes]
    qa_outcomes: Annotated[List[QAOutcome], merge_qa_outcomes]
    blockers: Annotated[List[BlockerInfo], merge_blockers]
    commit_shas: Annotated[List[str], merge_commit_shas]

    # 执行控制
    execution_mode: str  # parallel, linear, hybrid
    parallel_batches: List[List[str]]
    current_batch_index: int
    fix_attempts: int
    max_turns: int

    # 最终结果
    final_status: str  # success, halted, failed
    completion_summary: str
```

## 依赖分析算法

### 文件冲突检测

从 Story 文件的 Dev Notes 中提取：
- 要创建的文件
- 要修改的文件
- API 端点引用
- Schema 引用

冲突类型：
- `CREATE_CONFLICT`: 两个 Story 创建同一文件
- `MODIFY_CONFLICT`: 两个 Story 修改同一文件
- `API_CONFLICT`: 两个 Story 修改同一 API 端点

### 批次生成（图着色算法）

使用贪心图着色算法将 Stories 分组：
1. 构建冲突图（节点=Story, 边=冲突）
2. 贪心着色：按顺序分配颜色，选择最小可用颜色
3. 同一颜色的 Stories 形成一个批次

### 模式推荐

| 条件 | 推荐模式 |
|------|---------|
| 无冲突 | `parallel` |
| 冲突率 ≥ 80% | `linear` |
| 部分冲突 & 批次效率 ≥ 2 | `hybrid` |
| 其他 | `linear` |

## 崩溃恢复

工作流状态通过 SqliteSaver 持久化到 SQLite 数据库。

### 恢复场景

| 场景 | 恢复方式 |
|------|---------|
| Claude 会话 compact | 检查点已保存，从当前阶段恢复 |
| 机器关机 | SQLite 检查点，重启后恢复 |
| 网络故障 | 检查点已保存，重试当前 Story |
| 手动停止 | 使用 `epic-resume` 继续 |
| HALT（阻塞） | 修复问题后 `epic-resume` |

## 与 BMad Agent 集成

通过 `/parallel` 命令激活 Parallel Dev Coordinator：

```bash
/parallel
*epic-develop 15 --stories "15.1,15.2,15.3"
```

任务文件位置：
- `.bmad-core/tasks/epic-develop.md`
- `.bmad-core/tasks/epic-status.md`
- `.bmad-core/tasks/epic-resume.md`
- `.bmad-core/tasks/epic-stop.md`

## 测试

```bash
# 运行测试
python -m pytest src/tests/test_bmad_orchestrator.py -v
```

## 版本历史

- **v1.0.0** (2025-11-30): 初始版本
  - 9 节点 StateGraph 工作流
  - 依赖分析和冲突检测
  - SqliteSaver 崩溃恢复
  - CLI 命令接口
  - BMad Agent 集成

## 作者

Canvas Learning System Team
